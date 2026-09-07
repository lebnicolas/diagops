"""Extraction des features du détecteur de provenance M4 — chemin d'inférence uniquement.

Repris de `diagops-m4/work/M4/src/modele.py` (empreinte `7cce88a5f36e7218…`), **sans le code
d'entraînement**. Une image d'inférence n'a pas à embarquer `candidats()`, `RandomForestClassifier`
ni la logique de partition : c'est du code qui ne s'exécutera jamais en service, et chaque ligne
transportée est une ligne à maintenir, à auditer et à faire figurer dans un SBOM.

Le module d'origine dépendait de `src.protocole` pour trois constantes ; elles sont reprises ici
en clair plutôt que de tirer un module entier pour trois valeurs.

**L'équivalence n'est pas supposée** : `tests/test_features.py` recalcule les 19 features des
30 fenêtres de calibration et les compare à `results/modele/features.csv` produit en M4. Une
dérive d'extraction rendrait le modèle gelé silencieusement faux — il prédirait bien, sur les
mauvaises entrées.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# Reprises de `diagops-m4/work/M4/src/protocole.py`
SEED = 20260831
CLASSE_POSITIVE = "fabriquée"
COLONNE_FENETRE = "window_id"


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
