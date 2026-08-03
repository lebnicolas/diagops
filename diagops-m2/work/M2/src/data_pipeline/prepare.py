"""Transformations justifiees appliquees aux copies de travail.

Aucune fonction de ce module ne touche aux fichiers recus : elles operent sur
des copies en memoire et rendent, avec la table transformee, le journal de ce
qui a ete change. Une transformation sans trace n'existe pas.

Colonnes du journal, alignees sur le canevas du notebook :
`source`, `rule_id`, `transformation`, `rows_affected`, `before`, `after`,
`justification`.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from . import checks
from .rules import (
    CRITICALITY_VALUES,
    DECLARED_LABEL_EQUIVALENCES,
    EVENT_TYPE_VALUES,
    INTERVENTION_TYPE_VALUES,
    OUTCOME_VALUES,
    SEVERITY_VALUES,
)


TRANSFORMATION_LOG_COLUMNS = [
    "source",
    "rule_id",
    "transformation",
    "rows_affected",
    "before",
    "after",
    "justification",
]

PERSONAL_DATA_PLACEHOLDER = "[NOTE MASQUEE — DONNEE PERSONNELLE]"


def empty_transformation_log() -> pd.DataFrame:
    return pd.DataFrame(columns=TRANSFORMATION_LOG_COLUMNS)


def mask_personal_notes(
    frame: pd.DataFrame,
    column: str = "work_order_note",
    identifier_column: str = "maintenance_id",
    rule_id: str = "MNT-PII-001",
    source: str = "maintenance",
    placeholder: str = PERSONAL_DATA_PLACEHOLDER,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Remplace **integralement** le texte libre des notes contenant une donnee personnelle.

    Pourquoi masquer tout le champ et non les seuls fragments detectes : le
    masquage par motif donne une fausse assurance. Sur ce jeu, la note
    `Rappeler Nadia B. au 06 12 34 56 78.` illustre exactement le probleme —
    le numero est detecte et masque, mais `Nadia B.` ne declenche aucun motif
    (pas de civilite qui la precede) et resterait en clair. Un masquage partiel
    laisserait croire la ligne assainie alors qu'elle porte encore un nom.

    La ligne est conservee : les dates, la duree, le cout et le type
    d'intervention sont valides et utiles a M3. Rien ne justifie de perdre une
    intervention saine a cause d'un champ de commentaire.

    Retourne la table transformee et le journal correspondant.
    """
    prepared = frame.copy(deep=True)
    mask = checks.contains_personal_data(prepared, column)

    if not mask.any():
        return prepared, empty_transformation_log()

    kinds = checks.personal_data_kinds(prepared, column)
    identifiers = (
        prepared.loc[mask, identifier_column].astype(str).tolist()
        if identifier_column in prepared.columns
        else [f"index:{value}" for value in prepared.index[mask]]
    )

    records = [
        {
            "source": source,
            "rule_id": rule_id,
            "transformation": f"{column} -> {placeholder}",
            "rows_affected": 1,
            # L'etat initial est conserve en clair : le brief l'exige pour toute
            # transformation, et sans lui la correction n'est ni verifiable ni
            # reversible. Le journal est un artefact d'audit, pas une sortie
            # destinee a M3 — c'est la table preparee qui porte le masquage.
            "before": f"[{identifier}] {frame.at[index, column]}",
            "after": placeholder,
            "justification": (
                "Minimisation : un diagnostic de panne n'a besoin ni d'un numero "
                "de telephone ni d'une adresse electronique. Champ masque en "
                "entier car la detection par motif ne garantit pas d'avoir vu "
                "tous les elements identifiants du texte."
            ),
        }
        for identifier, index in zip(identifiers, prepared.index[mask])
    ]

    prepared.loc[mask, column] = placeholder
    return prepared, pd.DataFrame(records, columns=TRANSFORMATION_LOG_COLUMNS)


def drop_duplicate_rows(
    frame: pd.DataFrame,
    source: str,
    rule_id: str,
    identifier_column: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Supprime les exemplaires surnumeraires d'une ligne integralement identique.

    `keep='first'` : le premier exemplaire reste, les copies partent. La
    suppression ne perd aucune information puisque toutes les colonnes sont
    egales — c'est ce qui rend la correction certaine, et non un arbitrage.

    A ne pas confondre avec un identifiant duplique sur des lignes differentes :
    la, rien ne dit laquelle garder, et le cas va en examen metier.
    """
    duplicates = frame.duplicated(keep="first")
    prepared = frame.loc[~duplicates].copy(deep=True)

    if not duplicates.any():
        return prepared, empty_transformation_log()

    if identifier_column and identifier_column in frame.columns:
        identifiers = frame.loc[duplicates, identifier_column].astype(str).tolist()
    else:
        identifiers = [f"index:{value}" for value in frame.index[duplicates]]

    record = {
        "source": source,
        "rule_id": rule_id,
        "transformation": "suppression des lignes integralement dupliquees",
        "rows_affected": int(duplicates.sum()),
        "before": f"{len(frame)} lignes, dont doublons : {', '.join(identifiers)}",
        "after": f"{len(prepared)} lignes",
        "justification": (
            "Toutes les colonnes sont egales : la copie n apporte aucune "
            "information et fausse les effectifs et les cumuls. Le premier "
            "exemplaire est conserve."
        ),
    }
    return prepared.reset_index(drop=True), pd.DataFrame([record], columns=TRANSFORMATION_LOG_COLUMNS)


def normalize_case_variants(
    frame: pd.DataFrame,
    column: str,
    allowed: tuple[str, ...],
    source: str,
    rule_id: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Ramene une valeur a la forme canonique de l'enumeration quand seule la casse devie.

    `Incident` devient `incident` parce que la forme normalisee correspond a une
    valeur du schema. Une valeur dont la forme normalisee reste inconnue —
    `URGENT`, `alert` — n'est **pas** touchee : ce n'est pas une erreur de
    frappe, et la corriger serait deviner.
    """
    prepared = frame.copy(deep=True)
    if column not in prepared.columns:
        return prepared, empty_transformation_log()

    canonical = {str(value).strip().casefold(): value for value in allowed}
    values = prepared[column]
    normalized = values.astype(str).str.strip().str.casefold()
    target = normalized.map(canonical)
    to_fix = values.notna() & target.notna() & (values != target)

    if not to_fix.any():
        return prepared, empty_transformation_log()

    records = [
        {
            "source": source,
            "rule_id": rule_id,
            "transformation": f"{column} : {before} -> {after}",
            "rows_affected": int(count),
            "before": f"{before} ({count} lignes)",
            "after": str(after),
            "justification": (
                "La forme normalisee correspond a une valeur du schema : les deux "
                "ecritures designent la meme classe, la correction ne perd rien."
            ),
        }
        for (before, after), count in (
            pd.DataFrame({"before": values[to_fix], "after": target[to_fix]})
            .value_counts()
            .items()
        )
    ]

    prepared.loc[to_fix, column] = target[to_fix]
    return prepared, pd.DataFrame(records, columns=TRANSFORMATION_LOG_COLUMNS)


def normalize_declared_labels(
    frame: pd.DataFrame,
    column: str,
    equivalences: dict[str, str],
    source: str,
    rule_id: str,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Applique des equivalences de libelles **declarees** sur une categorie ouverte.

    Une categorie ouverte n'a pas d'enumeration de reference : on ne peut donc
    pas deduire qu'un libelle en vaut un autre, il faut le decider. La table
    d'equivalences vit dans `rules.DECLARED_LABEL_EQUIVALENCES` pour qu'un
    relecteur puisse la contester sans relire le code.
    """
    prepared = frame.copy(deep=True)
    if column not in prepared.columns:
        return prepared, empty_transformation_log()

    records = []
    for before, after in equivalences.items():
        matches = prepared[column] == before
        if not matches.any():
            continue
        records.append(
            {
                "source": source,
                "rule_id": rule_id,
                "transformation": f"{column} : {before!r} -> {after!r}",
                "rows_affected": int(matches.sum()),
                "before": f"{before!r} ({int(matches.sum())} lignes)",
                "after": after,
                "justification": (
                    "Equivalence declaree sur une categorie ouverte : la "
                    "correspondance ne se deduit pas du schema, elle est decidee "
                    "et tracee dans rules.DECLARED_LABEL_EQUIVALENCES."
                ),
            }
        )
        prepared.loc[matches, column] = after

    if not records:
        return prepared, empty_transformation_log()
    return prepared, pd.DataFrame(records, columns=TRANSFORMATION_LOG_COLUMNS)


def prepare_all(
    frames: dict[str, pd.DataFrame]
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Applique les 6 regles `correction_certaine` et le masquage, dans cet ordre.

    **L'ordre n'est pas neutre.** La deduplication passe AVANT la normalisation
    de casse. Dans l'autre sens, normaliser `Incident` en `incident` pourrait
    rendre deux lignes strictement identiques et la deduplication en
    supprimerait une — on aurait fabrique un doublon puis efface une ligne qui
    n'existait pas en double a la source. La deduplication ne doit retirer que
    ce qui etait deja duplique dans les fichiers recus.

    Les fichiers d'origine ne sont pas touches : tout se fait sur des copies.
    """
    prepared = {name: frame.copy(deep=True) for name, frame in frames.items()}
    logs: list[pd.DataFrame] = []

    # 1. Deduplication — d'abord, pour les raisons ci-dessus.
    for source, rule_id, identifier in (
        ("equipment", "EQP-KEY-003", "equipment_id"),
        ("events", "EVT-KEY-003", "event_id"),
        ("maintenance", "MNT-KEY-003", "maintenance_id"),
    ):
        prepared[source], log = drop_duplicate_rows(
            prepared[source], source=source, rule_id=rule_id, identifier_column=identifier
        )
        logs.append(log)

    # 2. Normalisation de casse sur les enumerations fermees par le contrat.
    for source, column, allowed, rule_id in (
        ("equipment", "criticality", CRITICALITY_VALUES, "EQP-CAS-001"),
        ("events", "event_type", EVENT_TYPE_VALUES, "EVT-CAS-001"),
        ("events", "severity", SEVERITY_VALUES, "EVT-CAS-002"),
        ("maintenance", "intervention_type", INTERVENTION_TYPE_VALUES, "MNT-CAS-002"),
        ("maintenance", "outcome", OUTCOME_VALUES, "MNT-CAS-003"),
    ):
        prepared[source], log = normalize_case_variants(
            prepared[source], column=column, allowed=allowed, source=source, rule_id=rule_id
        )
        logs.append(log)

    # 3. Equivalences declarees sur les categories ouvertes.
    for source, column, rule_id in (
        ("equipment", "equipment_type", "EQP-CAS-002"),
        ("maintenance", "intervention_type", "MNT-CAS-001"),
    ):
        prepared[source], log = normalize_declared_labels(
            prepared[source],
            column=column,
            equivalences=DECLARED_LABEL_EQUIVALENCES.get(column, {}),
            source=source,
            rule_id=rule_id,
        )
        logs.append(log)

    # 4. Masquage des donnees personnelles.
    prepared["maintenance"], log = mask_personal_notes(prepared["maintenance"])
    logs.append(log)

    combined = pd.concat(logs, ignore_index=True) if logs else empty_transformation_log()
    return prepared, combined.reindex(columns=TRANSFORMATION_LOG_COLUMNS)


OUTPUT_FILENAMES = {
    "equipment": "equipment.csv",
    "events": "events.csv",
    "maintenance": "maintenance_history.csv",
}


def export_prepared(
    prepared: dict[str, pd.DataFrame],
    quarantine: pd.DataFrame,
    transformation_log: pd.DataFrame,
    check_results: pd.DataFrame,
    output_dir: Path,
) -> dict[str, Path]:
    """Ecrit les livrables dans un dossier de sortie **distinct des sources**.

    Rien n'est jamais ecrit dans `data_pack/` : les fichiers recus restent
    inchangees, c'est un critere bloquant du brief. Tout part dans `output/`.

    Encodage `utf-8` et fins de ligne `\\n` explicites : les valeurs contiennent
    des accents, et une sortie dont les octets changent selon la machine ne
    serait pas reproductible.
    """
    output_dir = Path(output_dir)
    processed_dir = output_dir / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    written: dict[str, Path] = {}

    for name, frame in prepared.items():
        path = processed_dir / OUTPUT_FILENAMES[name]
        frame.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")
        written[f"processed/{OUTPUT_FILENAMES[name]}"] = path

    for name, frame in (
        ("quarantine.csv", quarantine),
        ("transformation_log.csv", transformation_log),
        ("check_results.csv", check_results),
    ):
        path = output_dir / name
        frame.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")
        written[name] = path

    return written
