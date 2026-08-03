"""Execution du registre de regles M2 sur les trois sources.

Ce module **mesure**, il ne corrige rien et n'ecrit rien sur le disque. Il
produit deux tableaux :

- `check_results` : une ligne par regle, avec le nombre d'echecs ;
- `quarantine`   : une ligne par anomalie, au format impose par le brief.

Les corrections eventuelles se decident apres lecture de ces tableaux, jamais
pendant l'audit.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from . import checks
from .checks import CheckOutcome
from .rules import (
    CRITICALITY_VALUES,
    DECLARED_LABEL_EQUIVALENCES,
    EQUIPMENT_REQUIRED_COLUMNS,
    EVENT_TYPE_VALUES,
    EVENTS_REQUIRED_COLUMNS,
    EXPECTED_PERIOD,
    INTERVENTION_TYPE_VALUES,
    MAINTENANCE_REQUIRED_COLUMNS,
    MAX_DOWNTIME_MINUTES,
    MAX_LABOR_HOURS,
    MAX_RATED_POWER_KW,
    MIN_COMMISSIONING_DATE,
    OUTCOME_VALUES,
    RECURRENCE_MINIMUM,
    RECURRENCE_THRESHOLD,
    SEVERITY_VALUES,
    rule_register,
)


SOURCE_FILES = {
    "equipment": "equipment.csv",
    "events": "events.csv",
    "maintenance": "maintenance_history.csv",
}

ROW_IDENTIFIER = {
    "equipment": "equipment_id",
    "events": "event_id",
    "maintenance": "maintenance_id",
}

REQUIRED_COLUMNS = {
    "equipment": EQUIPMENT_REQUIRED_COLUMNS,
    "events": EVENTS_REQUIRED_COLUMNS,
    "maintenance": MAINTENANCE_REQUIRED_COLUMNS,
}

CHECK_RESULT_COLUMNS = [
    "rule_id",
    "source",
    "column",
    "severity",
    "rows_checked",
    "failures",
    "failure_rate",
    "sample_row_identifiers",
    "comment",
]

QUARANTINE_COLUMNS = [
    "source_file",
    "row_identifier",
    "rule_id",
    "column",
    "observed_value",
    "reason",
    "decision",
]

# Decisions qui ne produisent aucune ligne de quarantaine : soit le controle
# est structurel, soit il ne fait que mesurer.
NON_QUARANTINE_DECISIONS = {"arret_audit", "signalement"}

# Nombre d'identifiants affiches dans check_results. La quarantaine, elle,
# contient toujours la totalite des lignes en echec.
SAMPLE_SIZE = 10


@dataclass
class AuditResult:
    """Sortie complete d'un passage d'audit."""

    check_results: pd.DataFrame
    quarantine: pd.DataFrame
    outcomes: list[CheckOutcome]
    reference_date: pd.Timestamp
    inventories: dict[str, pd.DataFrame]

    def failed_rules(self) -> pd.DataFrame:
        """Regles ayant au moins un echec, les plus graves d'abord."""
        order = {"bloquante": 0, "majeure": 1, "mineure": 2}
        failed = self.check_results.loc[self.check_results["failures"] > 0].copy()
        failed["_rank"] = failed["severity"].map(order).fillna(9)
        return (
            failed.sort_values(["_rank", "failures"], ascending=[True, False])
            .drop(columns="_rank")
            .reset_index(drop=True)
        )


# ----------------------------------------------------------------------
# Specification : quelle regle utilise quel controle
# ----------------------------------------------------------------------


def _specs(reference_date: pd.Timestamp) -> list[dict]:
    """Branche chaque rule_id du registre sur un controle de `checks.py`.

    `reference_date` est passee explicitement pour que deux executions du meme
    audit au meme instant donnent le meme resultat.
    """
    today = reference_date.isoformat()

    return [
        # -------------------------------------------------- equipment
        {"rule_id": "EQP-SCH-001", "source": "equipment", "kind": "required_columns"},
        {"rule_id": "EQP-SCH-002", "source": "equipment", "kind": "convertible",
         "column": "commissioning_date", "type": "datetime"},
        {"rule_id": "EQP-SCH-003", "source": "equipment", "kind": "convertible",
         "column": "rated_power_kw", "type": "number"},
        {"rule_id": "EQP-KEY-001", "source": "equipment", "kind": "not_null",
         "column": "equipment_id"},
        {"rule_id": "EQP-KEY-002", "source": "equipment", "kind": "unique",
         "column": "equipment_id"},
        {"rule_id": "EQP-KEY-003", "source": "equipment", "kind": "duplicated_rows"},
        {"rule_id": "EQP-CAT-001", "source": "equipment", "kind": "closed_set",
         "column": "criticality", "allowed": CRITICALITY_VALUES, "bucket": "isolated"},
        {"rule_id": "EQP-NOM-001", "source": "equipment", "kind": "closed_set",
         "column": "criticality", "allowed": CRITICALITY_VALUES, "bucket": "recurrent"},
        {"rule_id": "EQP-CAS-001", "source": "equipment", "kind": "closed_set",
         "column": "criticality", "allowed": CRITICALITY_VALUES, "bucket": "case_variant"},
        {"rule_id": "EQP-CAT-002", "source": "equipment", "kind": "inventory",
         "column": "site_id"},
        {"rule_id": "EQP-CAT-003", "source": "equipment", "kind": "inventory",
         "column": "equipment_type"},
        {"rule_id": "EQP-CAS-002", "source": "equipment", "kind": "declared_label",
         "column": "equipment_type"},
        {"rule_id": "EQP-TMP-001", "source": "equipment", "kind": "date_bounds",
         "column": "commissioning_date", "maximum": today},
        {"rule_id": "EQP-TMP-002", "source": "equipment", "kind": "date_bounds",
         "column": "commissioning_date", "minimum": MIN_COMMISSIONING_DATE},
        {"rule_id": "EQP-VAL-001", "source": "equipment", "kind": "numeric_bounds",
         "column": "rated_power_kw", "minimum": 0, "strict_minimum": True},
        {"rule_id": "EQP-VAL-002", "source": "equipment", "kind": "numeric_bounds",
         "column": "rated_power_kw", "maximum": MAX_RATED_POWER_KW},
        {"rule_id": "EQP-NUL-001", "source": "equipment", "kind": "missing_rate",
         "column": "manufacturer"},
        {"rule_id": "EQP-NUL-002", "source": "equipment", "kind": "missing_rate",
         "column": "rated_power_kw"},
        # -------------------------------------------------- events
        {"rule_id": "EVT-SCH-001", "source": "events", "kind": "required_columns"},
        {"rule_id": "EVT-SCH-002", "source": "events", "kind": "convertible",
         "column": "start_at", "type": "iso_datetime", "also": ["end_at"]},
        {"rule_id": "EVT-KEY-001", "source": "events", "kind": "not_null",
         "column": "event_id"},
        {"rule_id": "EVT-KEY-002", "source": "events", "kind": "unique",
         "column": "event_id"},
        {"rule_id": "EVT-KEY-003", "source": "events", "kind": "duplicated_rows"},
        {"rule_id": "EVT-REF-001", "source": "events", "kind": "not_null",
         "column": "equipment_id"},
        {"rule_id": "EVT-REF-002", "source": "events", "kind": "foreign_key",
         "column": "equipment_id", "reference": "equipment",
         "reference_column": "equipment_id"},
        {"rule_id": "EVT-CAT-001", "source": "events", "kind": "closed_set",
         "column": "event_type", "allowed": EVENT_TYPE_VALUES, "bucket": "isolated"},
        {"rule_id": "EVT-NOM-001", "source": "events", "kind": "closed_set",
         "column": "event_type", "allowed": EVENT_TYPE_VALUES, "bucket": "recurrent"},
        {"rule_id": "EVT-CAS-001", "source": "events", "kind": "closed_set",
         "column": "event_type", "allowed": EVENT_TYPE_VALUES, "bucket": "case_variant"},
        {"rule_id": "EVT-CAT-002", "source": "events", "kind": "closed_set",
         "column": "severity", "allowed": SEVERITY_VALUES, "bucket": "isolated"},
        {"rule_id": "EVT-NOM-002", "source": "events", "kind": "closed_set",
         "column": "severity", "allowed": SEVERITY_VALUES, "bucket": "recurrent"},
        {"rule_id": "EVT-CAS-002", "source": "events", "kind": "closed_set",
         "column": "severity", "allowed": SEVERITY_VALUES, "bucket": "case_variant"},
        {"rule_id": "EVT-CAT-003", "source": "events", "kind": "in_set",
         "column": "period", "allowed": (EXPECTED_PERIOD,)},
        {"rule_id": "EVT-TMP-001", "source": "events", "kind": "date_order",
         "earlier": "start_at", "later": "end_at", "column": "end_at"},
        {"rule_id": "EVT-TMP-002", "source": "events", "kind": "date_bounds",
         "column": "start_at", "maximum": today},
        {"rule_id": "EVT-TMP-003", "source": "events", "kind": "custom",
         "column": "start_at", "function": _event_before_commissioning},
        {"rule_id": "EVT-NUL-001", "source": "events", "kind": "missing_rate",
         "column": "end_at"},
        # -------------------------------------------------- maintenance
        {"rule_id": "MNT-SCH-001", "source": "maintenance", "kind": "required_columns"},
        {"rule_id": "MNT-SCH-002", "source": "maintenance", "kind": "convertible",
         "column": "opened_at", "type": "iso_datetime", "also": ["closed_at"]},
        {"rule_id": "MNT-SCH-003", "source": "maintenance", "kind": "convertible",
         "column": "downtime_minutes", "type": "integer",
         "also_typed": [("labor_hours", "number"), ("parts_cost_eur", "number"),
                        ("parts_replaced_count", "integer")]},
        {"rule_id": "MNT-KEY-001", "source": "maintenance", "kind": "not_null",
         "column": "maintenance_id"},
        {"rule_id": "MNT-KEY-002", "source": "maintenance", "kind": "unique",
         "column": "maintenance_id"},
        {"rule_id": "MNT-KEY-003", "source": "maintenance", "kind": "duplicated_rows"},
        {"rule_id": "MNT-REF-001", "source": "maintenance", "kind": "foreign_key",
         "column": "event_id", "reference": "events", "reference_column": "event_id"},
        {"rule_id": "MNT-REF-002", "source": "maintenance", "kind": "foreign_key",
         "column": "equipment_id", "reference": "equipment",
         "reference_column": "equipment_id"},
        {"rule_id": "MNT-REF-003", "source": "maintenance", "kind": "custom",
         "column": "equipment_id", "function": _maintenance_equipment_mismatch},
        {"rule_id": "MNT-CAT-001", "source": "maintenance", "kind": "inventory",
         "column": "intervention_type"},
        {"rule_id": "MNT-CAS-001", "source": "maintenance", "kind": "declared_label",
         "column": "intervention_type"},
        {"rule_id": "MNT-CAT-004", "source": "maintenance", "kind": "closed_set",
         "column": "intervention_type", "allowed": INTERVENTION_TYPE_VALUES, "bucket": "isolated"},
        {"rule_id": "MNT-NOM-001", "source": "maintenance", "kind": "closed_set",
         "column": "intervention_type", "allowed": INTERVENTION_TYPE_VALUES, "bucket": "recurrent"},
        {"rule_id": "MNT-CAS-002", "source": "maintenance", "kind": "closed_set",
         "column": "intervention_type", "allowed": INTERVENTION_TYPE_VALUES, "bucket": "case_variant"},
        {"rule_id": "MNT-CAT-005", "source": "maintenance", "kind": "closed_set",
         "column": "outcome", "allowed": OUTCOME_VALUES, "bucket": "isolated"},
        {"rule_id": "MNT-NOM-002", "source": "maintenance", "kind": "closed_set",
         "column": "outcome", "allowed": OUTCOME_VALUES, "bucket": "recurrent"},
        {"rule_id": "MNT-CAS-003", "source": "maintenance", "kind": "closed_set",
         "column": "outcome", "allowed": OUTCOME_VALUES, "bucket": "case_variant"},
        {"rule_id": "MNT-CAT-002", "source": "maintenance", "kind": "inventory",
         "column": "outcome"},
        {"rule_id": "MNT-CAT-003", "source": "maintenance", "kind": "in_set",
         "column": "period", "allowed": (EXPECTED_PERIOD,)},
        {"rule_id": "MNT-TMP-001", "source": "maintenance", "kind": "date_order",
         "earlier": "opened_at", "later": "closed_at", "column": "closed_at"},
        {"rule_id": "MNT-TMP-002", "source": "maintenance", "kind": "date_bounds",
         "column": "opened_at", "maximum": today},
        {"rule_id": "MNT-TMP-003", "source": "maintenance", "kind": "custom",
         "column": "opened_at", "function": _maintenance_before_event},
        {"rule_id": "MNT-VAL-001", "source": "maintenance", "kind": "numeric_bounds",
         "column": "downtime_minutes", "minimum": 0},
        {"rule_id": "MNT-VAL-002", "source": "maintenance", "kind": "numeric_bounds",
         "column": "downtime_minutes", "maximum": MAX_DOWNTIME_MINUTES},
        {"rule_id": "MNT-VAL-003", "source": "maintenance", "kind": "gap",
         "column": "downtime_minutes", "start": "opened_at", "end": "closed_at"},
        {"rule_id": "MNT-VAL-004", "source": "maintenance", "kind": "numeric_bounds",
         "column": "labor_hours", "minimum": 0, "maximum": MAX_LABOR_HOURS},
        {"rule_id": "MNT-VAL-005", "source": "maintenance", "kind": "numeric_bounds",
         "column": "parts_cost_eur", "minimum": 0},
        {"rule_id": "MNT-VAL-006", "source": "maintenance", "kind": "numeric_bounds",
         "column": "parts_replaced_count", "minimum": 0},
        {"rule_id": "MNT-VAL-007", "source": "maintenance", "kind": "pair",
         "column": "parts_cost_eur", "driver": "parts_cost_eur",
         "dependent": "parts_replaced_count"},
        {"rule_id": "MNT-NUL-001", "source": "maintenance", "kind": "missing_rate",
         "column": "closed_at"},
        {"rule_id": "MNT-NUL-002", "source": "maintenance", "kind": "missing_rate",
         "column": "labor_hours", "also": ["parts_cost_eur"]},
        {"rule_id": "MNT-PII-001", "source": "maintenance", "kind": "pii",
         "column": "work_order_note"},
    ]


# ----------------------------------------------------------------------
# Controles croises, hors moule generique
# ----------------------------------------------------------------------


def _event_before_commissioning(frames: dict[str, pd.DataFrame]) -> pd.Series:
    """EVT-TMP-003 — evenement anterieur a la mise en service de l'equipement."""
    events, equipment = frames["events"], frames["equipment"]
    if "equipment_id" not in events.columns or "commissioning_date" not in equipment.columns:
        return pd.Series(False, index=events.index, dtype=bool)
    mapping = equipment.drop_duplicates("equipment_id").set_index("equipment_id")[
        "commissioning_date"
    ]
    commissioning = pd.to_datetime(
        events["equipment_id"].map(mapping), errors="coerce", utc=True
    )
    start = pd.to_datetime(events["start_at"], errors="coerce", utc=True)
    return commissioning.notna() & start.notna() & (start < commissioning)


def _maintenance_before_event(frames: dict[str, pd.DataFrame]) -> pd.Series:
    """MNT-TMP-003 — intervention ouverte avant le debut de son evenement."""
    maintenance, events = frames["maintenance"], frames["events"]
    if "event_id" not in maintenance.columns or "start_at" not in events.columns:
        return pd.Series(False, index=maintenance.index, dtype=bool)
    mapping = events.drop_duplicates("event_id").set_index("event_id")["start_at"]
    event_start = pd.to_datetime(
        maintenance["event_id"].map(mapping), errors="coerce", utc=True
    )
    opened = pd.to_datetime(maintenance["opened_at"], errors="coerce", utc=True)
    return event_start.notna() & opened.notna() & (opened < event_start)


def _maintenance_equipment_mismatch(frames: dict[str, pd.DataFrame]) -> pd.Series:
    """MNT-REF-003 — equipement de l'intervention different de celui de l'evenement."""
    maintenance, events = frames["maintenance"], frames["events"]
    if "event_id" not in events.columns:
        return pd.Series(False, index=maintenance.index, dtype=bool)
    return checks.inconsistent_join(
        maintenance,
        column="equipment_id",
        reference=events.drop_duplicates("event_id"),
        reference_key="event_id",
        reference_column="equipment_id",
    )


# ----------------------------------------------------------------------
# Execution
# ----------------------------------------------------------------------


def _run_spec(
    spec: dict, frames: dict[str, pd.DataFrame], inventories: dict[str, pd.DataFrame]
) -> CheckOutcome:
    source = spec["source"]
    frame = frames[source]
    identifier = ROW_IDENTIFIER[source]
    rule_id = spec["rule_id"]
    kind = spec["kind"]
    column = spec.get("column", "*")

    if kind == "required_columns":
        missing = checks.missing_columns(frame, REQUIRED_COLUMNS[source])
        return CheckOutcome(
            rule_id=rule_id,
            source=source,
            column="*",
            rows_checked=len(frame),
            failures=len(missing),
            failing_identifiers=missing,
            observed_values=[],
            comment="colonnes absentes : " + (", ".join(missing) if missing else "aucune"),
        )

    if kind == "missing_rate":
        columns = [column, *spec.get("also", [])]
        parts = [f"{name} : {checks.missing_rate(frame, name):.1%}" for name in columns]
        return CheckOutcome(
            rule_id=rule_id,
            source=source,
            column=", ".join(columns),
            rows_checked=len(frame),
            failures=0,
            comment="taux de valeurs absentes — " + " ; ".join(parts),
        )

    if kind == "inventory":
        inventory = checks.category_inventory(frame, column)
        inventories[f"{source}.{column}"] = inventory
        near = checks.near_duplicate_labels(frame, column)
        rare = inventory.loc[inventory["count"] <= 2, "value"].tolist()
        comment = f"{len(inventory)} valeurs distinctes"
        if rare:
            comment += f" ; effectif <= 2 : {', '.join(rare[:5])}"
        if near:
            comment += f" ; libelles voisins : {near[:3]}"
        return CheckOutcome(
            rule_id=rule_id,
            source=source,
            column=column,
            rows_checked=len(frame),
            failures=0,
            comment=comment,
        )

    if kind == "convertible":
        mask = checks.not_convertible(frame, column, spec["type"])
        columns = [column]
        for name in spec.get("also", []):
            mask = mask | checks.not_convertible(frame, name, spec["type"])
            columns.append(name)
        for name, typed in spec.get("also_typed", []):
            mask = mask | checks.not_convertible(frame, name, typed)
            columns.append(name)
        column = ", ".join(columns)
    elif kind == "not_null":
        mask = checks.is_null(frame, column)
    elif kind == "unique":
        mask = checks.duplicated_key(frame, column)
    elif kind == "duplicated_rows":
        mask = checks.duplicated_rows(frame)
    elif kind == "in_set":
        mask = checks.not_in_set(frame, column, spec["allowed"])
    elif kind == "declared_label":
        mask = checks.has_declared_label(
            frame, column, DECLARED_LABEL_EQUIVALENCES.get(column, {})
        )
    elif kind == "closed_set":
        mask = checks.unknown_value_masks(
            frame, column, spec["allowed"], RECURRENCE_THRESHOLD, RECURRENCE_MINIMUM
        )[spec["bucket"]]
    elif kind == "foreign_key":
        reference = frames[spec["reference"]]
        values = (
            reference[spec["reference_column"]]
            if spec["reference_column"] in reference.columns
            else pd.Series(dtype=object)
        )
        mask = checks.unresolved_reference(frame, column, values.dropna())
    elif kind == "date_order":
        mask = checks.out_of_order_dates(frame, spec["earlier"], spec["later"])
    elif kind == "date_bounds":
        mask = checks.date_out_of_bounds(
            frame, column, minimum=spec.get("minimum"), maximum=spec.get("maximum")
        )
    elif kind == "gap":
        mask = checks.date_gap_exceeded(frame, spec["start"], spec["end"], column)
    elif kind == "numeric_bounds":
        mask = checks.numeric_out_of_bounds(
            frame,
            column,
            minimum=spec.get("minimum"),
            maximum=spec.get("maximum"),
            strict_minimum=spec.get("strict_minimum", False),
        )
    elif kind == "pair":
        mask = checks.inconsistent_pair(frame, spec["driver"], spec["dependent"])
    elif kind == "pii":
        mask = checks.contains_personal_data(frame, column)
    elif kind == "custom":
        mask = spec["function"](frames)
    else:
        raise ValueError(f"Controle inconnu : {kind}")

    outcome = checks.outcome_from_mask(
        rule_id=rule_id,
        source=source,
        column=column,
        frame=frame,
        mask=mask,
        identifier_column=identifier,
        observed_column=spec.get("column") if spec.get("column") in frame.columns else None,
    )

    if kind == "pii" and outcome.failures:
        kinds = checks.personal_data_kinds(frame, spec["column"])
        detected = sorted({value for value in kinds[mask].tolist() if value})
        # La valeur observee reste le texte brut. La quarantaine est un artefact
        # d'audit destine a un relecteur humain : sans le texte, impossible de
        # distinguer un vrai numero d'une reference technique mal detectee, donc
        # impossible de trancher. Le brief exige d'ailleurs de conserver la
        # valeur observee. La protection porte sur les tables preparees
        # transmises a M3, ou la note est masquee (voir prepare.py).
        return CheckOutcome(
            rule_id=outcome.rule_id,
            source=outcome.source,
            column=outcome.column,
            rows_checked=outcome.rows_checked,
            failures=outcome.failures,
            failing_identifiers=outcome.failing_identifiers,
            observed_values=outcome.observed_values,
            comment="motifs declenches : " + ", ".join(detected) + " — verification humaine requise",
        )

    return outcome


def run_audit(
    frames: dict[str, pd.DataFrame], reference_date: pd.Timestamp | None = None
) -> AuditResult:
    """Execute toutes les regles du registre sans modifier les donnees."""
    reference_date = reference_date or pd.Timestamp.utcnow().normalize().tz_localize(None)
    register = rule_register().set_index("rule_id")
    inventories: dict[str, pd.DataFrame] = {}
    outcomes: list[CheckOutcome] = []

    for spec in _specs(reference_date):
        outcomes.append(_run_spec(spec, frames, inventories))

    results = pd.DataFrame(
        [
            {
                "rule_id": outcome.rule_id,
                "source": outcome.source,
                "column": outcome.column,
                "severity": register.at[outcome.rule_id, "severity"],
                "rows_checked": outcome.rows_checked,
                "failures": outcome.failures,
                "failure_rate": round(outcome.failure_rate, 4),
                "sample_row_identifiers": ", ".join(
                    outcome.failing_identifiers[:SAMPLE_SIZE]
                ),
                "comment": outcome.comment,
            }
            for outcome in outcomes
        ],
        columns=CHECK_RESULT_COLUMNS,
    )

    return AuditResult(
        check_results=results,
        quarantine=build_quarantine(outcomes, frames, register),
        outcomes=outcomes,
        reference_date=reference_date,
        inventories=inventories,
    )


def build_quarantine(
    outcomes: list[CheckOutcome],
    frames: dict[str, pd.DataFrame],
    register: pd.DataFrame,
) -> pd.DataFrame:
    """Construit la quarantaine au format impose par le brief.

    Une meme ligne peut apparaitre plusieurs fois si elle enfreint plusieurs
    regles : chaque anomalie garde sa propre trace.
    """
    records: list[dict[str, str]] = []

    for outcome in outcomes:
        decision = register.at[outcome.rule_id, "decision_if_failed"]
        if decision in NON_QUARANTINE_DECISIONS or outcome.failures == 0:
            continue
        reason = register.at[outcome.rule_id, "description"]
        observed = outcome.observed_values or [""] * len(outcome.failing_identifiers)
        for identifier, value in zip(outcome.failing_identifiers, observed):
            records.append(
                {
                    "source_file": SOURCE_FILES[outcome.source],
                    "row_identifier": identifier,
                    "rule_id": outcome.rule_id,
                    "column": outcome.column,
                    "observed_value": value,
                    "reason": reason,
                    "decision": decision,
                }
            )

    return pd.DataFrame(records, columns=QUARANTINE_COLUMNS)
