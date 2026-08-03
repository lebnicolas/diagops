"""Construction d'un jeu supervise a partir des tables preparees M2.

**Tache** : predire la `severity` d'un evenement au moment ou il est signale,
pour trier les interventions.

**Unite d'observation** : un evenement. Une ligne du jeu = une ligne de
`events.csv`, enrichie des caracteristiques de son equipement.

Deux garde-fous structurent tout le module.

*Fuite temporelle* — seules les variables **connues au debut de l'evenement**
entrent dans le jeu. Tout ce qui vient de `maintenance_history` (duree
d'arret, cout, resultat) decrit ce qui s'est passe **apres**, et apres
l'evaluation de gravite elle-meme. `end_at` et la duree de l'evenement sont
exclus pour la meme raison : au moment de trier, l'evenement n'est pas fini.

*Fuite par groupe* — le decoupage se fait **par equipement**, pas par ligne.
Un equipement present a la fois dans l'entrainement et dans le test
permettrait de memoriser son comportement propre au lieu d'apprendre une
regle generalisable.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .rules import SEVERITY_VALUES


TARGET = "severity"

# Variables disponibles au moment ou l'evenement est signale.
EQUIPMENT_FEATURES = [
    "equipment_type",
    "site_id",
    "criticality",
    "manufacturer",
    "rated_power_kw",
]
EVENT_FEATURES = ["event_type"]
DERIVED_FEATURES = [
    "equipment_age_days",
    "start_month",
    "start_weekday",
    "start_hour",
]
FEATURES = EQUIPMENT_FEATURES + EVENT_FEATURES + DERIVED_FEATURES

# Colonnes explicitement ecartees, avec la raison. Documenter ce qu'on
# n'utilise PAS vaut autant que documenter ce qu'on utilise.
EXCLUDED = {
    "end_at": "inconnu au moment du tri — l'evenement n'est pas termine",
    "duration": "derive de end_at, meme fuite",
    "downtime_minutes": "vient de l'intervention, posterieure a l'evaluation",
    "labor_hours": "idem",
    "parts_cost_eur": "idem",
    "parts_replaced_count": "idem",
    "outcome": "idem, et sans signal mesurable",
    "intervention_type": "idem",
    "work_order_note": "idem, et champ gabarit a 7 valeurs",
    "equipment_id": "identifiant — servirait a memoriser un equipement precis",
    "event_id": "identifiant sans valeur predictive",
    "period": "constante sur la livraison",
}

SPLIT_SIZES = {"train": 0.70, "validation": 0.15, "test": 0.15}
SPLIT_SEED = 42


@dataclass
class TrainingSet:
    """Jeu supervise decoupe, plus ce qu'il faut pour le juger."""

    splits: dict[str, pd.DataFrame]
    baselines: dict[str, float]
    excluded_rows: pd.DataFrame
    seed: int

    def sizes(self) -> dict[str, int]:
        return {name: len(frame) for name, frame in self.splits.items()}


def build_features(frames: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Assemble le jeu au niveau evenement, sans decoupage.

    Retourne le jeu exploitable et les lignes ecartees, avec leur motif — une
    ligne retiree sans trace serait la meme faute qu'a l'audit.
    """
    events, equipment = frames["events"], frames["equipment"]

    joined = events.merge(
        equipment[["equipment_id", *EQUIPMENT_FEATURES]], on="equipment_id", how="left"
    )

    start = pd.to_datetime(joined["start_at"], errors="coerce", utc=True)
    commissioning = pd.to_datetime(
        joined["commissioning_date"], errors="coerce", utc=True
    ) if "commissioning_date" in joined.columns else pd.Series(pd.NaT, index=joined.index)

    if "commissioning_date" not in joined.columns:
        commissioning = pd.to_datetime(
            joined["equipment_id"].map(
                equipment.drop_duplicates("equipment_id")
                .set_index("equipment_id")["commissioning_date"]
            ),
            errors="coerce",
            utc=True,
        )

    joined["equipment_age_days"] = (start - commissioning).dt.days
    joined["start_month"] = start.dt.month
    joined["start_weekday"] = start.dt.weekday
    joined["start_hour"] = start.dt.hour

    motifs = pd.Series("", index=joined.index, dtype=str)
    motifs[~joined[TARGET].isin(SEVERITY_VALUES)] = "severite hors enumeration"
    motifs[joined["equipment_type"].isna()] = "equipement non joignable"
    motifs[start.isna()] = "horodatage illisible"

    excluded = joined.loc[motifs != ""].copy()
    excluded["motif_exclusion"] = motifs[motifs != ""]

    usable = joined.loc[motifs == "", ["equipment_id", *FEATURES, TARGET]].reset_index(drop=True)
    return usable, excluded[["event_id", "equipment_id", TARGET, "motif_exclusion"]]


def split_by_equipment(
    frame: pd.DataFrame, seed: int = SPLIT_SEED, sizes: dict[str, float] | None = None
) -> dict[str, pd.DataFrame]:
    """Decoupe par equipement : un equipement n'apparait que dans un seul paquet.

    Un decoupage ligne a ligne laisserait le meme equipement des deux cotes.
    Le modele pourrait alors retenir son comportement propre et afficher un
    score qui ne se reproduirait sur aucun equipement nouveau.
    """
    sizes = sizes or SPLIT_SIZES
    groups = frame["equipment_id"].dropna().unique()
    rng = np.random.default_rng(seed)
    shuffled = rng.permutation(groups)

    n = len(shuffled)
    n_train = int(round(n * sizes["train"]))
    n_validation = int(round(n * sizes["validation"]))

    assignment = {
        "train": set(shuffled[:n_train]),
        "validation": set(shuffled[n_train : n_train + n_validation]),
        "test": set(shuffled[n_train + n_validation :]),
    }

    return {
        name: frame.loc[frame["equipment_id"].isin(ids)].reset_index(drop=True)
        for name, ids in assignment.items()
    }


def baselines(train: pd.DataFrame, test: pd.DataFrame) -> dict[str, float]:
    """Les deux scores qu'un modele doit battre pour valoir quelque chose.

    - `classe_majoritaire` : repondre toujours la classe la plus frequente.
    - `table_equipment_type` : une correspondance type d'equipement -> severite
      majoritaire, apprise sur l'entrainement seul.

    Publier le second est ce qui empeche de presenter comme un resultat un
    modele qui n'a fait que reconstituer un tableau de 18 lignes.
    """
    majoritaire = train[TARGET].value_counts().idxmax()
    score_majoritaire = float((test[TARGET] == majoritaire).mean())

    table = train.groupby("equipment_type")[TARGET].agg(
        lambda serie: serie.value_counts().idxmax()
    )
    predite = test["equipment_type"].map(table).fillna(majoritaire)
    score_table = float((predite == test[TARGET]).mean())

    return {
        "classe_majoritaire": round(score_majoritaire, 4),
        "table_equipment_type": round(score_table, 4),
    }


def build_training_set(
    frames: dict[str, pd.DataFrame], seed: int = SPLIT_SEED
) -> TrainingSet:
    """Chaine complete : assemblage, decoupage par equipement, references."""
    usable, excluded = build_features(frames)
    splits = split_by_equipment(usable, seed=seed)
    return TrainingSet(
        splits=splits,
        baselines=baselines(splits["train"], splits["test"]),
        excluded_rows=excluded,
        seed=seed,
    )
