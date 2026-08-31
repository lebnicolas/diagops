"""Features et candidats de modélisation — brief 1 M4, étape 3.

Le starter fournit trois features par fenêtre (moyenne, écart-type, taux de
valeurs absentes) et se déclare volontairement incomplet. Ce module les étend.

**Arbitrage A3 — les familles retenues et le motif de chacune :**

1. *structure temporelle* — le brief 2 du M3 a établi que c'est ce qui distingue
   une série fabriquée : un tirage marginal conserve tous les histogrammes et
   fait tomber l'autocorrélation de rang 4 de 0,80 à −0,02. S'en priver
   reviendrait à ignorer notre propre résultat ;
2. *régularité de la grille* — le pas nominal est de 6 h, et les procédés qui
   déforment l'axe des temps le cassent ;
3. *forme de la distribution* — asymétrie, aplatissement, valeurs répétées ;
4. *contrat capteur* — les signaux que la baseline M3 regarde déjà, inclus pour
   que la comparaison porte sur la méthode et non sur l'information disponible.

**Ce qui est délibérément exclu, et pourquoi :**

- **`sensor_name`**, sous quelque forme que ce soit. La répartition par capteur
  est très déséquilibrée — `temperature_c` compte 1 fenêtre fabriquée pour 8
  réelles. Sur 30 fenêtres, un modèle apprendrait « température ⇒ réelle », un
  raccourci qui marcherait en calibration et ne prouverait rien ;
- **`equipment_id`**, pour la même raison, aggravée : c'est la colonne de groupe
  de la partition ;
- **toute statistique calculée sur l'ensemble du lot** (moyenne du capteur, écart
  au profil de l'équipement). Elle ferait entrer dans une fenêtre une information
  venue des autres, y compris celles du pli de validation — une fuite discrète et
  invisible sur les résultats.

Toutes les features sont donc **intrinsèques à la fenêtre** et, quand elles
portent une échelle, **sans dimension** (rapports plutôt que valeurs brutes) :
c'est ce qui les rend comparables d'un capteur à l'autre sans nommer le capteur.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from src.protocole import CLASSE_POSITIVE, COLONNE_FENETRE, SEED


#: Pas nominal d'échantillonnage, en heures — contrat de la livraison.
PAS_NOMINAL_H = 6.0

#: Heures de la grille attendue.
GRILLE = {0, 6, 12, 18}

#: Plages physiques, reprises de la baseline M3 figée.
PLAGES = {
    "vibration_mm_s": (0.0, 12.0),
    "temperature_c": (-20.0, 140.0),
    "pressure_bar": (0.0, 25.0),
    "current_a": (0.0, 120.0),
    "rpm": (0.0, 3000.0),
}

SENTINELLES = {-999.0, -9999.0, 9999.0, 999999.0}


def _autocorrelation(valeurs: np.ndarray, decalage: int) -> float:
    """Autocorrélation à un décalage donné, 0.0 si elle n'est pas définie."""
    if len(valeurs) <= decalage + 1:
        return 0.0
    debut, fin = valeurs[:-decalage], valeurs[decalage:]
    if np.std(debut) < 1e-12 or np.std(fin) < 1e-12:
        return 0.0
    return float(np.corrcoef(debut, fin)[0, 1])


def _plus_longue_repetition(valeurs: np.ndarray) -> int:
    """Plus longue suite de valeurs identiques — signature d'un capteur figé."""
    if len(valeurs) == 0:
        return 0
    record = courant = 1
    for precedent, suivant in zip(valeurs[:-1], valeurs[1:], strict=True):
        courant = courant + 1 if suivant == precedent else 1
        record = max(record, courant)
    return record


def features_fenetre(fenetre: pd.DataFrame) -> dict[str, float]:
    """Features d'une fenêtre — intrinsèques, sans dimension quand c'est possible."""
    brut = fenetre["value"]
    valeurs = pd.to_numeric(brut, errors="coerce")
    manquantes = int(valeurs.isna().sum())
    propres = valeurs.dropna().to_numpy()

    horodatages = pd.to_datetime(fenetre["timestamp"], utc=True, errors="coerce")
    horodatages = horodatages.sort_values()
    ecarts_h = horodatages.diff().dropna().dt.total_seconds().to_numpy() / 3600.0

    capteur = fenetre["sensor_name"].iloc[0]
    borne_basse, borne_haute = PLAGES.get(capteur, (-np.inf, np.inf))

    # Précision décimale : la règle qui nous a rattrapés au brief 2 du M3.
    decimales = brut.astype(str).str.partition(".")[2].str.len()

    moyenne = float(np.mean(propres)) if len(propres) else 0.0
    ecart_type = float(np.std(propres)) if len(propres) > 1 else 0.0
    etendue = float(np.ptp(propres)) if len(propres) else 0.0
    echelle = abs(moyenne) if abs(moyenne) > 1e-9 else 1.0

    if len(propres) > 2 and ecart_type > 1e-12:
        centre = (propres - moyenne) / ecart_type
        asymetrie = float(np.mean(centre**3))
        aplatissement = float(np.mean(centre**4))
    else:
        asymetrie = aplatissement = 0.0

    differences = np.diff(propres) if len(propres) > 1 else np.array([0.0])

    return {
        # dispersion, sans dimension
        "coefficient_variation": ecart_type / echelle,
        "etendue_relative": etendue / echelle,
        "ecart_type_differences_relatif": float(np.std(differences)) / echelle,
        # structure temporelle — le cœur de l'arbitrage A3
        "autocorr_lag1": _autocorrelation(propres, 1),
        "autocorr_lag2": _autocorrelation(propres, 2),
        "autocorr_lag4": _autocorrelation(propres, 4),
        "part_changements_de_signe": float(np.mean(np.diff(np.sign(differences)) != 0))
        if len(differences) > 1 else 0.0,
        # forme
        "asymetrie": asymetrie,
        "aplatissement": aplatissement,
        "part_valeurs_distinctes": len(np.unique(propres)) / len(propres) if len(propres) else 0.0,
        "plus_longue_repetition": float(_plus_longue_repetition(propres)),
        # régularité de la grille
        "part_pas_non_nominal": float(np.mean(np.abs(ecarts_h - PAS_NOMINAL_H) > 1e-6))
        if len(ecarts_h) else 0.0,
        "ecart_type_pas": float(np.std(ecarts_h)) if len(ecarts_h) > 1 else 0.0,
        "part_hors_grille": float(np.mean([h not in GRILLE for h in horodatages.dt.hour])),
        # contrat capteur — ce que la baseline regarde
        "part_manquantes": manquantes / len(fenetre),
        "part_sentinelles": float(np.mean([v in SENTINELLES for v in propres])) if len(propres) else 0.0,
        "part_hors_plage": float(np.mean((propres < borne_basse) | (propres > borne_haute)))
        if len(propres) else 0.0,
        "part_precision_excessive": float((decimales > 2).mean()),
        "unite_conforme": float(fenetre["unit"].nunique() == 1),
    }


def table_features(lignes: pd.DataFrame, fenetres: pd.DataFrame) -> pd.DataFrame:
    """Table de features, une ligne par fenêtre, alignée sur la table du protocole."""
    calculees = pd.DataFrame(
        [
            {COLONNE_FENETRE: identifiant, **features_fenetre(groupe)}
            for identifiant, groupe in lignes.groupby(COLONNE_FENETRE, sort=True)
        ]
    )
    fusion = fenetres.merge(calculees, on=COLONNE_FENETRE, how="left", validate="one_to_one")
    if fusion[NOMS_FEATURES].isna().any().any():
        raise ValueError("features manquantes après jointure")
    return fusion


#: Ordre stable des colonnes de features — nécessaire pour que l'importance des
#: variables et les coefficients restent lisibles d'un run à l'autre.
NOMS_FEATURES = list(
    features_fenetre(
        pd.DataFrame(
            {
                "value": ["1.0"] * 5,
                "timestamp": pd.date_range("2026-01-01", periods=5, freq="6h", tz="UTC"),
                "sensor_name": ["vibration_mm_s"] * 5,
                "unit": ["mm/s"] * 5,
            }
        )
    )
)


def candidats() -> dict[str, Pipeline]:
    """Les deux candidats du `configs/model.yaml`, chacun contre l'autre.

    La régression logistique exige une mise à l'échelle : elle est dans le
    pipeline, donc ajustée **sur le pli d'entraînement seul**. Placer un
    `StandardScaler` avant la validation croisée ferait entrer les statistiques
    du pli de validation dans l'apprentissage — une fuite discrète, et invisible
    sur les résultats.

    `class_weight="balanced"` dans les deux cas : 11 positifs sur 30, et le coût
    des deux erreurs est traité à égalité par la métrique de décision.
    """
    return {
        "regression_logistique": Pipeline(
            [
                ("echelle", StandardScaler()),
                (
                    "modele",
                    LogisticRegression(
                        max_iter=5000,
                        class_weight="balanced",
                        random_state=SEED,
                    ),
                ),
            ]
        ),
        "foret_aleatoire": Pipeline(
            [
                (
                    "modele",
                    RandomForestClassifier(
                        n_estimators=300,
                        min_samples_leaf=2,
                        class_weight="balanced",
                        random_state=SEED,
                        n_jobs=1,
                    ),
                )
            ]
        ),
    }


def etiquettes(table: pd.DataFrame) -> pd.Series:
    """Vecteur cible : 1 pour `fabriquée`."""
    return (table["provenance"] == CLASSE_POSITIVE).astype(int)
