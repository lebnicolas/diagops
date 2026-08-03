"""Analyse de couverture et concentration des erreurs M1.

Repond aux questions 8 et 9 du diagnostic. Ce module ne juge pas : il compte,
et il **marque explicitement les effectifs trop faibles pour conclure**. C'est
la partie la plus facile a rater du brief — sortir un taux sur six lignes et le
presenter comme un resultat.

Aucune fonction n'ecrit sur le disque ni ne modifie les tables recues.
"""

from __future__ import annotations

import pandas as pd


# En deca de ce nombre d'observations dans une categorie, aucun taux n'est
# interpretable. Seuil conventionnel, a assumer et non a demontrer : il sert a
# forcer la mention de l'incertitude, pas a fixer une verite statistique.
MIN_EFFECTIF = 30


def category_counts(
    frame: pd.DataFrame, column: str, min_effectif: int = MIN_EFFECTIF
) -> pd.DataFrame:
    """Effectifs et parts d'une categorie, du plus rare au plus frequent."""
    if column not in frame.columns:
        return pd.DataFrame(columns=["categorie", "effectif", "part", "interpretable"])
    counts = frame[column].value_counts(dropna=False)
    return pd.DataFrame(
        {
            "categorie": counts.index.astype(str),
            "effectif": counts.to_numpy(),
            "part": (counts / len(frame)).round(4).to_numpy(),
            "interpretable": (counts >= min_effectif).to_numpy(),
        }
    ).sort_values("effectif").reset_index(drop=True)


def coverage_report(
    frames: dict[str, pd.DataFrame], min_effectif: int = MIN_EFFECTIF
) -> dict[str, pd.DataFrame]:
    """Effectifs sur les quatre axes demandes par le brief."""
    equipment, events = frames["equipment"], frames["events"]
    return {
        "equipment.site_id": category_counts(equipment, "site_id", min_effectif),
        "equipment.equipment_type": category_counts(equipment, "equipment_type", min_effectif),
        "equipment.criticality": category_counts(equipment, "criticality", min_effectif),
        "events.severity": category_counts(events, "severity", min_effectif),
        "events.event_type": category_counts(events, "event_type", min_effectif),
    }


def orphan_equipment(frames: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Equipements sans aucun evenement et sans aucune intervention.

    Ce n'est pas une anomalie de qualite : un equipement peut n'avoir rien
    connu sur la periode. C'est une question de **couverture** — un parc dont
    une partie n'est jamais observee limite ce que M3 pourra apprendre.
    """
    equipment, events, maintenance = (
        frames["equipment"],
        frames["events"],
        frames["maintenance"],
    )
    with_events = set(events["equipment_id"].dropna())
    with_maintenance = set(maintenance["equipment_id"].dropna())

    summary = equipment[["equipment_id", "equipment_type", "site_id", "criticality"]].copy()
    summary["a_des_evenements"] = summary["equipment_id"].isin(with_events)
    summary["a_des_interventions"] = summary["equipment_id"].isin(with_maintenance)
    return summary


def error_concentration(
    matrix: pd.DataFrame,
    frames: dict[str, pd.DataFrame],
    dimension: str,
    source: str = "equipment",
    join_key: str = "equipment_id",
    min_effectif: int = MIN_EFFECTIF,
) -> tuple[pd.DataFrame, dict[str, int]]:
    """Taux d'erreur M1 par categorie, avec le compte des lignes non appariees.

    Retourne le tableau **et** un diagnostic de jointure. Une jointure dont on
    ne verifie pas le taux d'appariement peut produire un tableau parfaitement
    presentable calcule sur la moitie des lignes.

    Le taux mesure une **co-occurrence**, jamais une cause : le brief compte la
    conclusion causale parmi ses criteres bloquants.
    """
    reference = frames[source]
    if join_key not in matrix.columns or join_key not in reference.columns:
        return pd.DataFrame(), {"lignes_matrice": len(matrix), "appariees": 0, "orphelines": len(matrix)}

    mapping = reference.drop_duplicates(join_key).set_index(join_key)[dimension]
    joined = matrix.copy()
    joined[dimension] = joined[join_key].map(mapping)

    diagnostic = {
        "lignes_matrice": len(matrix),
        "appariees": int(joined[dimension].notna().sum()),
        "orphelines": int(joined[dimension].isna().sum()),
    }

    usable = joined.loc[joined[dimension].notna()]
    if usable.empty:
        return pd.DataFrame(), diagnostic

    grouped = usable.groupby(dimension, dropna=False).agg(
        effectif=("severity_correct", "size"),
        severite_correcte=("severity_correct", "sum"),
        revue_correcte=("human_review_correct", "sum"),
    )
    grouped["taux_erreur_severite"] = (
        1 - grouped["severite_correcte"] / grouped["effectif"]
    ).round(4)
    grouped["taux_erreur_revue"] = (
        1 - grouped["revue_correcte"] / grouped["effectif"]
    ).round(4)
    grouped["interpretable"] = grouped["effectif"] >= min_effectif

    return (
        grouped.reset_index()[
            [
                dimension,
                "effectif",
                "taux_erreur_severite",
                "taux_erreur_revue",
                "interpretable",
            ]
        ].sort_values("effectif", ascending=False).reset_index(drop=True),
        diagnostic,
    )
