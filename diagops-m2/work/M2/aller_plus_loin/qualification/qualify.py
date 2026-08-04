"""Qualification d'un lot : mesure, classement, decision.

Trois etapes, dans cet ordre et jamais melangees :

1. le registre M2 est rejoue sur le lot, dans le contexte du publie ;
2. les controles propres a une livraison incrementale sont ajoutes ;
3. la politique traduit chaque constat en `error`, `warning` ou `info`, et le
   statut du lot se deduit des niveaux rencontres.

Aucune donnee source n'est modifiee, aucune livraison n'est integree. La
decision finale reste explicite et humaine : ce module produit un statut, pas
un acte.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from src.data_pipeline.audit import (
    REQUIRED_COLUMNS,
    SOURCE_FILES,
    AuditOptions,
    run_audit,
)
from src.data_pipeline.checks import CheckOutcome
from src.data_pipeline.rules import rule_register

from . import incremental
from .batch import Batch, build_context
from .policy import Policy


FINDING_COLUMNS = [
    "rule_id",
    "source",
    "column",
    "level",
    "rows_checked",
    "failures",
    "failure_rate",
    "escalated",
    "comment",
    "sample_row_identifiers",
]

SAMPLE_SIZE = 10

# Colonnes dont la modification lors d'une mise a jour demande un avis humain.
STRUCTURAL_COLUMNS = {
    "equipment": ("site_id", "commissioning_date"),
}


@dataclass
class Qualification:
    """Resultat complet de la qualification d'un lot."""

    batch_id: str
    label: str
    policy_version: str
    status: str
    findings: pd.DataFrame
    quarantine: pd.DataFrame
    counts: dict[str, int] = field(default_factory=dict)
    details: dict[str, object] = field(default_factory=dict)

    def blocking(self) -> pd.DataFrame:
        return self.findings.loc[self.findings["level"] == "error"]

    def warnings(self) -> pd.DataFrame:
        return self.findings.loc[self.findings["level"] == "warning"]


def qualify(
    batch: Batch,
    baseline: Batch,
    policy: Policy,
    reference_date: pd.Timestamp,
    is_baseline: bool = False,
) -> Qualification:
    """Qualifie un lot au regard d'une politique.

    `is_baseline=True` qualifie le socle publie contre lui-meme : c'est le
    controle de non-regression. Il verifie que la politique reste applicable a
    ce qui a deja ete accepte — une politique qui rejette le passe ne sert a
    rien pour juger l'avenir.
    """
    context = build_context(baseline, None if is_baseline else batch)
    options = AuditOptions(
        # Les references se resolvent toujours dans le contexte : un evenement
        # candidat porte sur une machine du catalogue, pas sur une machine de
        # son propre fichier. Sans cela, un mur de faux orphelins bloquants.
        context_frames=context,
        # La population de comptage, elle, suit la politique.
        population_frames=context if policy.recurrence_population == "context" else None,
        expected_periods=policy.expected_periods,
        recurrence_threshold=policy.recurrence_share,
        recurrence_minimum=policy.recurrence_minimum,
    )

    audit = run_audit(batch.frames, reference_date=reference_date, options=options)
    register = rule_register().set_index("rule_id")

    records: list[dict] = []
    levels: list[str] = []

    # ------------------------------------------------------------------
    # 1. Registre M2
    # ------------------------------------------------------------------
    for _, row in audit.check_results.iterrows():
        decision = register.at[row["rule_id"], "decision_if_failed"]
        if row["failures"] == 0:
            continue
        verdict = policy.level_for(row["rule_id"], decision, float(row["failure_rate"]))
        levels.append(verdict.level)
        records.append(
            {
                "rule_id": row["rule_id"],
                "source": row["source"],
                "column": row["column"],
                "level": verdict.level,
                "rows_checked": int(row["rows_checked"]),
                "failures": int(row["failures"]),
                "failure_rate": float(row["failure_rate"]),
                "escalated": bool(verdict.escalated),
                # Une regle sans note de politique laissait une case vide : un
                # rejet illisible sans ouvrir le code. On retombe sur ce que la
                # regle verifie, le rapport se suffit alors a lui-meme.
                "comment": _first_text(
                    verdict.reason, row["comment"], register.at[row["rule_id"], "description"]
                ),
                "sample_row_identifiers": row["sample_row_identifiers"],
            }
        )

    # ------------------------------------------------------------------
    # 2. Controles incrementaux
    # ------------------------------------------------------------------
    details: dict[str, object] = {}
    if not is_baseline:
        for outcome, rule_id in _incremental_outcomes(batch, baseline, policy, details):
            level = policy.level_for_incremental(rule_id)
            if outcome.failures == 0:
                continue
            levels.append(level)
            records.append(
                {
                    "rule_id": rule_id,
                    "source": outcome.source,
                    "column": outcome.column,
                    "level": level,
                    "rows_checked": outcome.rows_checked,
                    "failures": outcome.failures,
                    "failure_rate": round(outcome.failure_rate, 4),
                    "escalated": False,
                    "comment": outcome.comment,
                    "sample_row_identifiers": ", ".join(
                        outcome.failing_identifiers[:SAMPLE_SIZE]
                    ),
                }
            )

    findings = pd.DataFrame(records, columns=FINDING_COLUMNS)
    if not findings.empty:
        order = {"error": 0, "warning": 1, "info": 2}
        findings = (
            findings.assign(_rank=findings["level"].map(order).fillna(9))
            .sort_values(["_rank", "failures"], ascending=[True, False])
            .drop(columns="_rank")
            .reset_index(drop=True)
        )

    return Qualification(
        batch_id=batch.batch_id,
        label=batch.label,
        policy_version=policy.version,
        status=policy.status_for(levels),
        findings=findings,
        quarantine=audit.quarantine,
        counts={
            "error": levels.count("error"),
            "warning": levels.count("warning"),
            "info": levels.count("info"),
        },
        details=details,
    )


def _first_text(*candidates: object) -> str:
    """Premier texte non vide parmi les candidats."""
    for value in candidates:
        text = "" if value is None or pd.isna(value) else str(value).strip()
        if text:
            return text
    return ""


def _incremental_outcomes(
    batch: Batch, baseline: Batch, policy: Policy, details: dict[str, object]
) -> list[tuple[CheckOutcome, str]]:
    """Produit les constats propres a un lot incremental."""
    outcomes: list[tuple[CheckOutcome, str]] = []
    new_values: dict[str, list[str]] = {}
    structural_changes: dict[str, list[str]] = {}

    for source, frame in batch.frames.items():
        published = baseline.frames.get(source)
        if published is None:
            continue

        # -- structure
        declared, undeclared = incremental.extra_columns(
            frame, REQUIRED_COLUMNS[source], batch.announced_columns.get(source, [])
        )
        outcomes.append(
            (incremental.column_outcome("INC-SCH-001", source, declared, frame), "INC-SCH-001")
        )
        outcomes.append(
            (incremental.column_outcome("INC-SCH-002", source, undeclared, frame), "INC-SCH-002")
        )

        # -- volumes
        outcomes.append(
            (
                incremental.row_count_outcome(
                    source, frame, batch.announced_rows.get(source)
                ),
                "INC-VOL-001",
            )
        )

        # -- cles
        update_key = batch.update_by_key.get(source)
        primary = incremental.ROW_IDENTIFIER[source]
        if update_key:
            outcomes.append(
                (
                    incremental.key_overlap_outcome(
                        "INC-KEY-002", source, frame, published, update_key,
                        "operation de mise a jour annoncee",
                    ),
                    "INC-KEY-002",
                )
            )
            watched = STRUCTURAL_COLUMNS.get(source, ())
            if watched:
                mask, changes = incremental.updates_changing_columns(
                    frame, published, update_key, watched
                )
                structural_changes.update(changes)
                outcomes.append(
                    (
                        CheckOutcome(
                            rule_id="INC-UPD-001",
                            source=source,
                            column=", ".join(watched),
                            rows_checked=len(frame),
                            failures=int(mask.sum()),
                            failing_identifiers=list(changes),
                            observed_values=[", ".join(v) for v in changes.values()],
                            comment=(
                                f"{len(changes)} mise(s) a jour modifiant "
                                f"{', '.join(watched)}"
                            ),
                        ),
                        "INC-UPD-001",
                    )
                )
        else:
            rule_id = "INC-KEY-003" if source == "events" else "INC-KEY-004"
            outcomes.append(
                (
                    incremental.key_overlap_outcome(
                        rule_id, source, frame, published, primary,
                        "aucune collision attendue sur un lot d'ajouts",
                    ),
                    rule_id,
                )
            )

        # -- categories ouvertes
        for column in policy.watched_open_categories.get(source, []):
            mask, values = incremental.new_category_values(frame, published, column)
            if values:
                new_values[f"{source}.{column}"] = values
            outcomes.append(
                (
                    CheckOutcome(
                        rule_id="INC-CAT-001",
                        source=source,
                        column=column,
                        rows_checked=len(frame),
                        failures=int(mask.sum()),
                        failing_identifiers=(
                            frame.loc[mask, primary].astype(str).tolist()
                            if primary in frame.columns
                            else []
                        ),
                        observed_values=frame.loc[mask, column].astype(str).tolist(),
                        comment=(
                            f"valeurs inedites : {', '.join(values)}" if values else "aucune"
                        ),
                    ),
                    "INC-CAT-001",
                )
            )

    details["new_category_values"] = new_values
    details["structural_updates"] = structural_changes
    details["source_files"] = SOURCE_FILES
    return outcomes
