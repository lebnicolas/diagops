"""Étape 3 du brief 2 — générer des mesures pour un périmètre non couvert.

Deux voies imposées par le brief, volontairement inégales :

- **le tirage marginal** (`PROC-GEN-MARG-V1`) reproduit indépendamment la
  distribution de chaque colonne. C'est la méthode naïve, et elle sert de
  contre-exemple : elle préserve tous les histogrammes et détruit toutes les
  relations ;
- **l'interpolation entre voisins** (`PROC-GEN-SMOTE-V1`) suit le principe de
  SMOTE — choisir une observation, l'un de ses plus proches voisins, tirer un
  point entre les deux. Écrite à la main avec `NearestNeighbors`, comme le
  brief l'exige, avec traitement explicite des colonnes catégorielles.

## Ce que la génération ne peut pas faire, et pourquoi

Les séries DiagOps portent un cycle journalier, mais **chaque série a sa propre
phase** : `EQ-CAB-134` culmine en température à minuit, `EQ-CHILL-001` à midi.
Moyennées sur le parc, ces phases se compensent et le profil horaire global est
plat — ce qui avait d'abord fait croire à l'absence de cycle.

Pour un équipement dépourvu de tout capteur, la phase de son cycle est une
information **absente du jeu de données**. Aucune méthode ne la crée. Une
génération peut reproduire l'existence d'un cycle et son amplitude ; elle ne
peut pas reproduire sa phase, et prétendre le contraire serait inventer une
information.

C'est la limite structurelle de l'étape, et elle vaut pour les deux voies.

## Traitement des colonnes catégorielles

Interpoler numériquement une catégorie n'a aucun sens : à mi-chemin entre
`vibration_mm_s` et `temperature_c` il n'y a rien. Les colonnes catégorielles
sont donc traitées séparément, selon le principe de SMOTE-NC :

- dans la **distance**, une différence de `equipment_type` ajoute une pénalité
  fixe, calibrée sur la dispersion des variables numériques ;
- dans la **génération**, la valeur catégorielle est obtenue par **vote
  majoritaire** parmi les voisins retenus, jamais par interpolation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


# Grille nominale de la livraison : quatre mesures par jour.
HEURES_GRILLE = (0, 6, 12, 18)
PAS_NOMINAL_H = 6

# Nombre de voisins considérés. Cinq est le choix usuel de SMOTE ; en dessous le
# tirage devient dégénéré, au-dessus les voisins cessent d'être proches.
K_VOISINS = 5

# Pénalité de distance appliquée quand deux équipements n'ont pas le même type.
# Elle vaut un écart-type des variables numériques standardisées : un type
# différent coûte donc autant qu'un écart d'un écart-type sur une variable
# continue. C'est un choix, déclaré ici et discutable.
PENALITE_TYPE = 1.0

# Descripteurs d'équipement servant au voisinage. La couverture instrumentale en
# est absente : tous les équipements cibles ont zéro capteur, elle ne
# discriminerait rien.
DESCRIPTEURS = ["criticite_ordinale", "puissance_log", "age_annees"]


def grille_horaire(debut: pd.Timestamp, fin: pd.Timestamp) -> pd.DatetimeIndex:
    """Horodatages attendus par le contrat entre deux bornes, pas de 6 h."""
    return pd.date_range(start=debut, end=fin, freq=f"{PAS_NOMINAL_H}h", tz="UTC")


def descripteurs_equipements(parc: pd.DataFrame) -> pd.DataFrame:
    """Table des descripteurs numériques, une ligne par équipement."""
    frame = parc[["equipment_id", "equipment_type", "criticite_ordinale", "age_annees"]].copy()
    frame["puissance_log"] = np.log1p(parc["puissance_kw"])
    return frame


def voisins_par_cible(
    cibles: pd.DataFrame, donneurs: pd.DataFrame, k: int = K_VOISINS
) -> dict[str, list[str]]:
    """Les `k` équipements donneurs les plus proches de chaque cible.

    La distance est euclidienne sur les descripteurs numériques standardisés,
    augmentée d'une pénalité quand le type d'équipement diffère. `NearestNeighbors`
    ne sait pas gérer cette pénalité : on récupère donc un voisinage large, puis
    on réordonne à la main sur la distance corrigée.
    """
    echelle = StandardScaler().fit(donneurs[DESCRIPTEURS].to_numpy(dtype=float))
    matrice_donneurs = echelle.transform(donneurs[DESCRIPTEURS].to_numpy(dtype=float))
    matrice_cibles = echelle.transform(cibles[DESCRIPTEURS].to_numpy(dtype=float))

    large = min(len(donneurs), max(k * 3, k))
    modele = NearestNeighbors(n_neighbors=large).fit(matrice_donneurs)
    distances, indices = modele.kneighbors(matrice_cibles)

    resultat: dict[str, list[str]] = {}
    for rang, cible in enumerate(cibles.itertuples(index=False)):
        candidats = []
        for distance, indice in zip(distances[rang], indices[rang]):
            donneur = donneurs.iloc[indice]
            penalite = 0.0 if donneur["equipment_type"] == cible.equipment_type else PENALITE_TYPE
            candidats.append((distance + penalite, donneur["equipment_id"]))
        candidats.sort()
        resultat[cible.equipment_id] = [identifiant for _, identifiant in candidats[:k]]
    return resultat


def vote_majoritaire(valeurs: pd.Series) -> str:
    """Modalité la plus fréquente — traitement des catégories, pas d'interpolation."""
    return str(valeurs.mode().iat[0])


def generer_par_tirage_marginal(
    cibles: pd.DataFrame,
    reelles: pd.DataFrame,
    capteurs: tuple[str, ...],
    horodatages: pd.DatetimeIndex,
    generateur: np.random.Generator,
) -> pd.DataFrame:
    """Reproduit indépendamment la distribution de chaque colonne.

    Chaque valeur est tirée dans la distribution empirique du capteur, sans
    aucun égard pour l'instant, l'équipement ou la valeur précédente. Toutes les
    marginales sont donc respectées par construction, et rien d'autre.
    """
    lignes = []
    for capteur in capteurs:
        population = reelles.loc[reelles["sensor_name"] == capteur, "value"].to_numpy()
        unite = vote_majoritaire(reelles.loc[reelles["sensor_name"] == capteur, "unit"])
        for equipement in cibles["equipment_id"]:
            tirage = generateur.choice(population, size=len(horodatages), replace=True)
            lignes.append(
                pd.DataFrame(
                    {
                        "equipment_id": equipement,
                        "timestamp": horodatages,
                        "sensor_name": capteur,
                        "value": np.round(tirage, 2),
                        "unit": unite,
                        "period": "2026-S1",
                    }
                )
            )
    return pd.concat(lignes, ignore_index=True)


def contexte_generation(
    capteurs: tuple[str, ...],
    site_cible: str,
    segment_cible: str,
    parc_segmente: pd.DataFrame,
    prepared: dict[str, pd.DataFrame],
    k: int,
) -> dict:
    """Reconstitue le point de départ commun aux deux voies de génération.

    Cibles, donneurs, voisinage et mesures réelles ne dépendent d'aucun tirage :
    les extraire ici permet au tour 2 de l'étape 4 de régénérer sur **exactement**
    le même périmètre que l'étape 3, sans dupliquer la préparation ni risquer de
    comparer deux états successifs du générateur sur des bases différentes.
    """
    sensors = prepared["sensors"].copy()
    sensors["timestamp"] = pd.to_datetime(sensors["timestamp"], errors="coerce", utc=True)
    sensors["value"] = pd.to_numeric(sensors["value"], errors="coerce")
    reelles = sensors.dropna(subset=["timestamp", "value"])
    reelles = reelles[reelles["sensor_name"].isin(capteurs)]

    cibles = parc_segmente[
        (parc_segmente["site_id"] == site_cible)
        & (parc_segmente["segment"] == segment_cible)
    ]
    instrumentes = set(reelles["equipment_id"])
    donneurs = parc_segmente[parc_segmente["equipment_id"].isin(instrumentes)]

    voisins = voisins_par_cible(
        descripteurs_equipements(cibles), descripteurs_equipements(donneurs), k=k
    )
    return {
        "reelles": reelles,
        "cibles": cibles,
        "donneurs": donneurs,
        "voisins": voisins,
    }


# Plages physiques des capteurs, reprises **à l'identique** de la règle R-RANGE
# du détecteur de référence (`tools/verify_synthetic.py`). Elles ne servent ici
# qu'à compter les dépassements produits par l'extrapolation : rien n'est
# écrêté, et le comptage anticipe simplement ce que le détecteur signalera.
PLAGES_PHYSIQUES = {
    "vibration_mm_s": (0.0, 12.0),
    "temperature_c": (-20.0, 140.0),
    "pressure_bar": (0.0, 25.0),
    "current_a": (0.0, 120.0),
    "rpm": (0.0, 3000.0),
}


def generer_par_interpolation(
    cibles: pd.DataFrame,
    reelles: pd.DataFrame,
    capteurs: tuple[str, ...],
    horodatages: pd.DatetimeIndex,
    voisins: dict[str, list[str]],
    generateur: np.random.Generator,
    lambda_par_serie: bool = False,
    lambda_bornes: tuple[float, float] = (0.0, 1.0),
) -> tuple[pd.DataFrame, dict]:
    """Interpole entre deux séries réelles voisines, point par point.

    Pour chaque horodatage, deux donneurs sont tirés parmi les `k` voisins de la
    cible et leurs valeurs au même instant sont interpolées :
    `v = v_i + λ (v_j - v_i)`, avec `λ` tiré uniformément.

    `lambda_par_serie` change ce que le générateur préserve. Tiré à chaque point
    — le principe canonique de SMOTE — `λ` introduit un mélange indépendant d'un
    instant à l'autre et abîme la structure temporelle. Tiré une fois par série,
    il produit une combinaison fixe de deux séries réelles et préserve leur
    forme. Le premier état est produit d'abord ; le second n'est justifié que si
    la confrontation le demande.

    `lambda_bornes` porte la correction décidée après le tour 1 de l'étape 4.
    Avec les bornes canoniques `(0, 1)`, tout point fabriqué est **intérieur** au
    segment qui joint ses deux parents : la dispersion produite est mécaniquement
    inférieure à celle du réel, et le tour 1 l'a mesurée à 0,783 et 0,810 fois
    l'écart-type de référence. Élargir les bornes au-delà de `[0, 1]` autorise
    l'extrapolation de part et d'autre du segment et corrige la cause plutôt que
    le symptôme. Le prix est explicite : une valeur extrapolée peut franchir la
    plage physique du capteur. Ces dépassements ne sont **pas écrêtés** — ils
    sont comptés dans le journal et laissés dans la sortie, pour que le détecteur
    les signale et que le coût de la correction reste visible.
    """
    index_reel = reelles.set_index(["equipment_id", "sensor_name", "timestamp"])["value"]
    borne_basse, borne_haute = lambda_bornes
    journal = {
        "points_sans_donneur": 0,
        "donneurs_utilises": {},
        "lambda_bornes": [borne_basse, borne_haute],
        "points_extrapoles": 0,
        "points_hors_plage": 0,
    }

    lignes = []
    for capteur in capteurs:
        unite = vote_majoritaire(reelles.loc[reelles["sensor_name"] == capteur, "unit"])
        porteurs = set(
            reelles.loc[reelles["sensor_name"] == capteur, "equipment_id"].unique()
        )
        for equipement in cibles["equipment_id"]:
            # Un voisin ne sert que s'il porte effectivement le capteur demandé.
            disponibles = [v for v in voisins[equipement] if v in porteurs]
            journal["donneurs_utilises"][f"{equipement}/{capteur}"] = disponibles
            if not disponibles:
                journal["points_sans_donneur"] += len(horodatages)
                continue

            # Tiré une fois ici quand le coefficient est fixé par série, sinon
            # renouvelé à chaque point dans la boucle.
            coefficient_serie = (
                float(generateur.uniform(borne_basse, borne_haute))
                if lambda_par_serie
                else None
            )
            basse_physique, haute_physique = PLAGES_PHYSIQUES.get(
                capteur, (-np.inf, np.inf)
            )
            valeurs = np.empty(len(horodatages))
            for rang, instant in enumerate(horodatages):
                paire = generateur.choice(
                    disponibles, size=2, replace=len(disponibles) < 2
                )
                premier = index_reel.get((paire[0], capteur, instant), np.nan)
                second = index_reel.get((paire[1], capteur, instant), np.nan)
                if np.isnan(premier) and np.isnan(second):
                    journal["points_sans_donneur"] += 1
                    valeurs[rang] = np.nan
                    continue
                if np.isnan(premier):
                    premier = second
                if np.isnan(second):
                    second = premier
                coefficient = (
                    coefficient_serie
                    if coefficient_serie is not None
                    else generateur.uniform(borne_basse, borne_haute)
                )
                valeur = premier + coefficient * (second - premier)
                if coefficient < 0.0 or coefficient > 1.0:
                    journal["points_extrapoles"] += 1
                if not basse_physique <= valeur <= haute_physique:
                    journal["points_hors_plage"] += 1
                valeurs[rang] = valeur

            lignes.append(
                pd.DataFrame(
                    {
                        "equipment_id": equipement,
                        "timestamp": horodatages,
                        "sensor_name": capteur,
                        "value": np.round(valeurs, 2),
                        "unit": unite,
                        "period": "2026-S1",
                    }
                )
            )

    produit = pd.concat(lignes, ignore_index=True) if lignes else pd.DataFrame()
    return produit.dropna(subset=["value"]).reset_index(drop=True), journal


# --------------------------------------------------------------------------
# Contrôles métier appliqués aux lignes fabriquées
# --------------------------------------------------------------------------

UNITES_ATTENDUES = {
    "vibration_mm_s": "mm/s",
    "temperature_c": "°C",
    "pressure_bar": "bar",
    "current_a": "A",
    "rpm": "rpm",
}

PERIODE_DEBUT = pd.Timestamp("2026-01-01T00:00:00Z")
PERIODE_FIN = pd.Timestamp("2026-07-01T00:00:00Z")


def controles_metier(
    produit: pd.DataFrame, reelles: pd.DataFrame, parc: set[str]
) -> pd.DataFrame:
    """Applique aux lignes fabriquées les règles établies aux briefs 1 et 2.

    Ce sont nos règles de qualité, pas un détecteur d'authenticité : elles
    disent si une ligne fabriquée est conforme au contrat, pas si elle est
    reconnaissable comme fabriquée. La distinction est celle que le lot de
    contrôle sanctionne à l'étape suivante.
    """
    horodatages = produit["timestamp"]
    valeurs = produit["value"]

    plages = {}
    for capteur, groupe in reelles.groupby("sensor_name", observed=True):
        mediane = float(groupe["value"].median())
        mad = float((groupe["value"] - mediane).abs().median())
        plages[capteur] = (mediane - 8 * mad, mediane + 8 * mad)

    borne_basse = produit["sensor_name"].map(lambda c: plages.get(c, (-np.inf, np.inf))[0])
    borne_haute = produit["sensor_name"].map(lambda c: plages.get(c, (-np.inf, np.inf))[1])

    cle = produit[["equipment_id", "timestamp", "sensor_name"]].astype(str).agg("|".join, axis=1)
    cles_reelles = set(
        reelles[["equipment_id", "timestamp", "sensor_name"]]
        .astype(str)
        .agg("|".join, axis=1)
    )

    controles = {
        "R-SEN-001 clé logique unique dans le lot": int(cle.duplicated().sum()),
        "R-SEN-001 clé en collision avec le réel": int(cle.isin(cles_reelles).sum()),
        "R-SEN-003 horodatage sur la grille de 6 h": int(
            (~horodatages.dt.hour.isin(HEURES_GRILLE)).sum()
            + (horodatages.dt.minute != 0).sum()
        ),
        "R-SEN-006 unité cohérente avec le capteur": int(
            (produit["unit"] != produit["sensor_name"].map(UNITES_ATTENDUES)).sum()
        ),
        "R-SEN-007 valeur renseignée et numérique": int(valeurs.isna().sum()),
        "R-SEN-008 valeur non négative": int((valeurs < 0).sum()),
        "R-SEN-009 valeur dans la plage robuste (8 MAD)": int(
            ((valeurs < borne_basse) | (valeurs > borne_haute)).sum()
        ),
        "R-SEN-013 équipement présent dans le parc": int(
            (~produit["equipment_id"].isin(parc)).sum()
        ),
        "R-SEN-014 mesure dans la période annoncée": int(
            ((horodatages < PERIODE_DEBUT) | (horodatages >= PERIODE_FIN)).sum()
        ),
        "R-SEN-015 étiquette period cohérente": int((produit["period"] != "2026-S1").sum()),
        "Précision à deux décimales": int(
            (valeurs.round(2) != valeurs).sum()
        ),
    }
    return pd.DataFrame(
        [{"controle": nom, "lignes_en_faute": nombre} for nom, nombre in controles.items()]
    )
