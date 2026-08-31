"""Brief 2, étape 4 — se confronter au détecteur de référence.

L'étape se joue dans deux sens. Ce module porte les outils communs aux deux.

**Sens 1** — nos productions sont soumises à `tools/verify_synthetic.py`. Le
détecteur ne retourne que des comptages par famille de règle : il indique qu'une
population est irrégulière, jamais quelle ligne l'est. Il déclare lui-même son
angle mort — ni structure temporelle, ni cohérence inter-sources — et c'est
précisément là que se logent les fabrications les plus fidèles. Un fichier qui
ne déclenche rien n'est donc pas un fichier réaliste : il est conforme aux
contrôles, ce qui est une propriété beaucoup plus faible.

**Sens 2** — nos règles sont appliquées au lot de contrôle. Elles vivent dans un
registre distinct (`R-DET-*`), séparé des règles de qualité du brief 1 : les
lignes authentiques du lot portent les anomalies de la livraison M3, donc une
ligne signalée par un contrôle de qualité n'est pas une ligne fabriquée.
Confondre les deux registres est ce que le lot est construit pour sanctionner.

Le témoin réel est la précaution centrale de l'étape. Avant de lire le moindre
comptage sur une fabrication, on soumet des lignes dont on sait qu'elles sont
authentiques. Si le détecteur les signale — et il le fait — alors « zéro
signalement » ne peut pas se lire comme « authentique », et l'écart entre les
deux devient la seule mesure interprétable.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd


WORK_ROOT = Path(__file__).resolve().parents[2]
MODULE_ROOT = WORK_ROOT.parents[1]
DETECTEUR = MODULE_ROOT / "tools" / "verify_synthetic.py"

# Colonnes attendues par le détecteur. `provenance` et `procedure_id` sont
# facultatives pour lui, mais obligatoires au contrat de transmission du M3 :
# une table de mesures transmise sans provenance est bloquante.
COLONNES_DETECTEUR = [
    "equipment_id",
    "timestamp",
    "sensor_name",
    "value",
    "unit",
    "period",
]
COLONNES_PROVENANCE = ["provenance", "procedure_id"]

FAMILLES = [
    "R-SCHEMA",
    "R-FORMAT",
    "R-RANGE",
    "R-UNIT",
    "R-KEY",
    "R-FK",
    "R-PRECISION",
]


def soumettre(chemin: Path) -> dict:
    """Exécute le détecteur de référence sur un fichier et retourne son rapport.

    Le détecteur est appelé en sous-processus plutôt qu'importé : c'est un
    artefact fourni par le module, pas une dépendance de notre code. L'appeler
    comme le ferait un correcteur garantit qu'on ne lit pas nos propres
    fonctions à sa place.
    """
    if not chemin.exists():
        raise FileNotFoundError(chemin)
    resultat = subprocess.run(
        [sys.executable, str(DETECTEUR), "--input", str(chemin), "--json"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=str(MODULE_ROOT),
    )
    if resultat.returncode not in (0, 1):
        raise RuntimeError(
            f"détecteur en échec sur {chemin.name} "
            f"(code {resultat.returncode}) : {resultat.stderr.strip()[:400]}"
        )
    return json.loads(resultat.stdout)


def preparer_pour_detecteur(
    frame: pd.DataFrame, destination: Path, garder_provenance: bool = True
) -> Path:
    """Écrit une table au format attendu par le détecteur.

    Les colonnes de travail internes — `row_identifier` en particulier — sont
    retirées : le détecteur les signale comme inattendues, ce qui est correct de
    sa part mais parasite la lecture des familles de règles.
    """
    colonnes = list(COLONNES_DETECTEUR)
    if garder_provenance:
        colonnes += [c for c in COLONNES_PROVENANCE if c in frame.columns]
    manquantes = [c for c in COLONNES_DETECTEUR if c not in frame.columns]
    if manquantes:
        raise KeyError(f"colonnes absentes de la table : {manquantes}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame[colonnes].to_csv(destination, index=False, encoding="utf-8")
    return destination


def resume_soumission(identifiant: str, hypothese: str, rapport: dict) -> dict:
    """Aplatit un rapport du détecteur en une ligne de table."""
    familles = rapport["flagged_rows_by_rule"]
    lignes = rapport["rows"] or 1
    return {
        "soumission": identifiant,
        "hypothese": hypothese,
        "lignes": rapport["rows"],
        "series": rapport["distinct_series"],
        "provenance_declaree": rapport["declares_provenance"],
        "colonnes_absentes": ";".join(rapport["missing_columns"]),
        "colonnes_inattendues": ";".join(rapport["unexpected_columns"]),
        **{famille: familles.get(famille, 0) for famille in FAMILLES},
        "total_signalements": rapport["flagged_rows_total"],
        "part_lignes_signalees": round(rapport["flagged_rows_total"] / lignes, 4),
        "capteurs_signales_distribution": ";".join(
            rapport["flagged_sensors_by_distribution"]
        ),
        "debut": rapport["timestamp_span"][0],
        "fin": rapport["timestamp_span"][1],
    }


def table_distributions(identifiant: str, rapport: dict) -> pd.DataFrame:
    """Détail capteur par capteur de la règle `R-DISTRIB`."""
    detail = pd.DataFrame(rapport["distribution"])
    if detail.empty:
        return detail
    detail.insert(0, "soumission", identifiant)
    return detail


# --------------------------------------------------------------------------
# Sens 2 — qualifier le lot de contrôle
# --------------------------------------------------------------------------

PACK = MODULE_ROOT / "data_pack" / "2026-S1"
LIVRAISON = PACK / "sensors" / "sensor_readings.csv"
LOT_BATCH = PACK / "sensors_control" / "control_batch.csv"
LOT_SAMPLE = PACK / "sensors_control" / "control_sample.csv"

PLAGES_PHYSIQUES = {
    "vibration_mm_s": (0.0, 12.0),
    "temperature_c": (-20.0, 140.0),
    "pressure_bar": (0.0, 25.0),
    "current_a": (0.0, 120.0),
    "rpm": (0.0, 3000.0),
}
UNITES_ATTENDUES = {
    "vibration_mm_s": "mm/s",
    "temperature_c": "°C",
    "pressure_bar": "bar",
    "current_a": "A",
    "rpm": "rpm",
}
SENTINELLES = {-999.0, -9999.0, 9999.0, 999999.0}
HEURES_GRILLE = {0, 6, 12, 18}
PAS_NOMINAL_H = 6.0
PERIODE_DEBUT = pd.Timestamp("2026-01-01T00:00:00Z")
PERIODE_FIN = pd.Timestamp("2026-07-01T00:00:00Z")

# Taille du bloc de fabrication, constatée et non supposée : les 720 lignes de
# l'échantillon se répartissent en 24 blocs de 30 dont la provenance est
# homogène, et les 6 000 lignes du lot en 200 blocs de 30 exactement.
TAILLE_BLOC = 30

# Seuils issus du calibrage sur `control_sample.csv`. Chacun est mesuré dans les
# deux sens — détections et fausses accusations — dans `run_verdicts_b2.py`.
SEUIL_AC4 = 0.50
SEUIL_GRILLE = 0.20
SEUIL_NIVEAU_SIGMA = 3.0
BORNES_DISPERSION = (0.70, 1.60)
SEUIL_COINCIDENCE = 0.10

# Rang de l'autocorrélation retenu : au pas de 6 h, le rang 4 porte le cycle de
# 24 heures. C'est la structure que le rééchantillonnage détruit et que le rang 2
# (12 h, anti-phase) rend moins nettement.
RANG_CYCLE_JOUR = 4

REGISTRE_DET = [
    ("R-DET-001", "bloc intégralement retrouvé dans la livraison M3, même équipement", "réelle"),
    ("R-DET-002", "bloc absent de la livraison M3", "fabriquée"),
    ("R-DET-003", "correspondance résiduelle, sous le seuil de coïncidence numérique", "fabriquée"),
    ("R-DET-004", "correspondance partielle intermédiaire — aucune règle ne conclut", "indécidable"),
    ("R-DET-010", f"autocorrélation de rang {RANG_CYCLE_JOUR} effondrée : cycle journalier absent", "corroboration"),
    ("R-DET-011", "grille d'échantillonnage irrégulière", "corroboration"),
    ("R-DET-012", "niveau incompatible avec le profil de l'équipement", "corroboration"),
    ("R-DET-013", "dispersion incompatible avec le profil de l'équipement", "corroboration"),
    ("R-DET-014", "valeurs retrouvées chez un autre équipement — greffe", "corroboration"),
]


def _normaliser(frame: pd.DataFrame) -> pd.DataFrame:
    """Colonnes de travail communes : capteur normalisé, valeur numérique, instant."""
    sortie = frame.copy()
    sortie["capteur"] = sortie["sensor_name"].astype(str).str.strip().str.lower()
    sortie["valeur"] = pd.to_numeric(sortie["value"], errors="coerce")
    sortie["instant"] = pd.to_datetime(
        sortie["timestamp"], utc=True, format="mixed", errors="coerce"
    )
    return sortie


def charger_livraison() -> pd.DataFrame:
    """Livraison M3 publiée, normalisée. C'est la source des lignes authentiques.

    Les notes de version du lot déclarent que « les mesures réelles proviennent
    de la livraison M3 ». Rapprocher le lot de cette livraison n'est donc pas
    consulter un oracle : c'est utiliser une source publique du pack, au même
    titre que `equipment.csv`.
    """
    return _normaliser(pd.read_csv(LIVRAISON))


def profil_equipements(livraison: pd.DataFrame) -> pd.DataFrame:
    """Moyenne et écart-type par équipement et capteur, sur les valeurs valides.

    Le filtrage n'est pas une commodité : calculé sur les valeurs brutes, le
    profil de `EQ-MIX-379` sort à 1,46 de moyenne pour un capteur qui tourne
    à 2,9 — les sentinelles de la livraison écrasent la statistique et rendent
    toute comparaison illisible.
    """
    valide = livraison[
        livraison.apply(
            lambda ligne: (
                ligne["capteur"] in PLAGES_PHYSIQUES
                and pd.notna(ligne["valeur"])
                and ligne["valeur"] not in SENTINELLES
                and PLAGES_PHYSIQUES[ligne["capteur"]][0]
                <= ligne["valeur"]
                <= PLAGES_PHYSIQUES[ligne["capteur"]][1]
            ),
            axis=1,
        )
    ]
    return valide.groupby(["equipment_id", "capteur"])["valeur"].agg(
        ["mean", "std", "count"]
    )


def correspondance(lot: pd.DataFrame, livraison: pd.DataFrame) -> pd.DataFrame:
    """Rapproche chaque ligne du lot de la livraison, à l'arrondi du contrat près.

    Deux correspondances distinctes, et la distinction porte tout le sens 2 :
    la ligne est retrouvée **sur son propre équipement** — elle est alors
    authentique — ou seulement **chez un autre** — le contenu est réel mais il a
    changé de porteur, ce qui est une fabrication par greffe.
    """
    exact = set(
        zip(
            livraison["equipment_id"],
            livraison["capteur"],
            livraison["timestamp"],
            livraison["valeur"].round(2),
        )
    )
    ailleurs: dict[tuple, set[str]] = {}
    for equipement, capteur, instant, valeur in zip(
        livraison["equipment_id"],
        livraison["capteur"],
        livraison["timestamp"],
        livraison["valeur"].round(2),
    ):
        ailleurs.setdefault((capteur, instant, valeur), set()).add(equipement)

    sortie = lot.copy()
    cles = list(
        zip(
            sortie["equipment_id"],
            sortie["capteur"],
            sortie["timestamp"],
            sortie["valeur"].round(2),
        )
    )
    sortie["retrouvee_meme_equipement"] = [cle in exact for cle in cles]
    sortie["retrouvee_autre_equipement"] = [
        bool(ailleurs.get((capteur, instant, valeur), set()) - {equipement})
        for equipement, capteur, instant, valeur in cles
    ]
    return sortie


def decouper_en_blocs(lot: pd.DataFrame, taille: int = TAILLE_BLOC) -> pd.DataFrame:
    """Numérote les blocs de fabrication, par série et par ordre chronologique."""
    sortie = lot.sort_values(["equipment_id", "capteur", "instant"]).copy()
    rang = sortie.groupby(["equipment_id", "capteur"]).cumcount()
    sortie["bloc"] = rang // taille
    sortie["bloc_id"] = (
        sortie["equipment_id"] + "|" + sortie["capteur"] + "|" + sortie["bloc"].astype(str)
    )
    return sortie


def signatures_par_bloc(lot: pd.DataFrame, profil: pd.DataFrame) -> pd.DataFrame:
    """Calcule, pour chaque bloc, les indicateurs des règles de corroboration.

    Ces indicateurs ne décident pas du verdict — ils l'appuient ou le
    contredisent. Les confondre avec la décision reviendrait à faire du contrôle
    de qualité un test d'authenticité, ce que le lot est construit pour punir.
    """
    lignes = []
    for bloc_id, bloc in lot.groupby("bloc_id"):
        bloc = bloc.sort_values("instant")
        valeurs = bloc["valeur"].reset_index(drop=True)
        capteur = bloc["capteur"].iloc[0]
        equipement = bloc["equipment_id"].iloc[0]
        ecarts = bloc["instant"].diff().dropna().dt.total_seconds() / 3600

        cle = (equipement, capteur)
        reference = profil.loc[cle] if cle in profil.index else None
        ecart_type = float(valeurs.std(ddof=0))

        autocorrelation = (
            float(valeurs.autocorr(RANG_CYCLE_JOUR))
            if len(valeurs) > RANG_CYCLE_JOUR + 1
            else float("nan")
        )
        lignes.append(
            {
                "bloc_id": bloc_id,
                "equipment_id": equipement,
                "capteur": capteur,
                "lignes": int(len(bloc)),
                "debut": bloc["instant"].min(),
                "fin": bloc["instant"].max(),
                "part_retrouvee": round(
                    float(bloc["retrouvee_meme_equipement"].mean()), 4
                ),
                "lignes_greffees": int(bloc["retrouvee_autre_equipement"].sum()),
                "autocorrelation_cycle": (
                    None if pd.isna(autocorrelation) else round(autocorrelation, 4)
                ),
                "part_pas_irregulier": (
                    round(float((ecarts != PAS_NOMINAL_H).mean()), 4)
                    if len(ecarts)
                    else 0.0
                ),
                "ecart_niveau_sigma": (
                    round(abs(float(valeurs.mean()) - reference["mean"]) / reference["std"], 3)
                    if reference is not None and reference["std"]
                    else None
                ),
                "ratio_dispersion": (
                    round(ecart_type / reference["std"], 3)
                    if reference is not None and reference["std"]
                    else None
                ),
            }
        )
    return pd.DataFrame(lignes)


def _corroborations(bloc: pd.Series) -> list[str]:
    """Règles de corroboration déclenchées par un bloc."""
    actives = []
    autocorrelation = bloc["autocorrelation_cycle"]
    if autocorrelation is not None and not pd.isna(autocorrelation):
        if autocorrelation < SEUIL_AC4:
            actives.append("R-DET-010")
    if bloc["part_pas_irregulier"] > SEUIL_GRILLE:
        actives.append("R-DET-011")
    niveau = bloc["ecart_niveau_sigma"]
    if niveau is not None and not pd.isna(niveau) and niveau > SEUIL_NIVEAU_SIGMA:
        actives.append("R-DET-012")
    dispersion = bloc["ratio_dispersion"]
    if dispersion is not None and not pd.isna(dispersion):
        if not BORNES_DISPERSION[0] <= dispersion <= BORNES_DISPERSION[1]:
            actives.append("R-DET-013")
    if bloc["lignes_greffees"] > 0 and bloc["part_retrouvee"] < 1.0:
        actives.append("R-DET-014")
    return actives


def verdicts_par_bloc(signatures: pd.DataFrame) -> pd.DataFrame:
    """Applique la politique de verdict retenue (arbitrage A5).

    Le verdict se prend **au bloc**, unité constatée de la fabrication, et il
    découle d'une seule règle décisive — la correspondance à la livraison. Les
    règles de corroboration sont reportées à côté du verdict : elles disent si
    le bloc porte aussi une signature interne, et leur silence sur un bloc
    déclaré fabriqué est un résultat en soi.

    `indécidable` est réservé à la correspondance partielle intermédiaire : le
    bloc n'est ni entièrement retrouvé ni absent, et aucun élément ne tranche.
    """
    sortie = signatures.copy()
    verdict, regle = [], []
    for _, bloc in sortie.iterrows():
        part = bloc["part_retrouvee"]
        if part >= 1.0:
            verdict.append("réelle")
            regle.append("R-DET-001")
        elif part == 0.0:
            verdict.append("fabriquée")
            regle.append("R-DET-002")
        elif part <= SEUIL_COINCIDENCE:
            verdict.append("fabriquée")
            regle.append("R-DET-003")
        else:
            verdict.append("indécidable")
            regle.append("R-DET-004")
    sortie["verdict"] = verdict
    sortie["regle_decisive"] = regle
    sortie["corroborations"] = [
        ";".join(_corroborations(bloc)) for _, bloc in sortie.iterrows()
    ]
    return sortie


def controles_qualite_par_ligne(lot: pd.DataFrame, parc: set[str]) -> pd.DataFrame:
    """Applique les règles capteurs du brief 1, ligne à ligne.

    Elles servent ici à répondre à une question du brief : lesquelles de nos
    règles de qualité ont attrapé des lignes fabriquées, lesquelles n'ont rien
    vu, et lesquelles ont accusé une mesure authentique. Ce ne sont **pas** des
    règles d'authenticité, et le résultat attendu est qu'elles se trompent.
    """
    valeurs = lot["valeur"]
    instants = lot["instant"]
    cle = (
        lot["equipment_id"].astype(str)
        + "|"
        + lot["timestamp"].astype(str)
        + "|"
        + lot["capteur"].astype(str)
    )
    plages_basses = lot["capteur"].map(
        lambda c: PLAGES_PHYSIQUES.get(c, (-np.inf, np.inf))[0]
    )
    plages_hautes = lot["capteur"].map(
        lambda c: PLAGES_PHYSIQUES.get(c, (-np.inf, np.inf))[1]
    )
    return pd.DataFrame(
        {
            "R-SEN-001 clé logique unique": cle.duplicated(keep=False),
            "R-SEN-003 horodatage sur la grille": ~(
                instants.dt.hour.isin(HEURES_GRILLE) & (instants.dt.minute == 0)
            ),
            "R-SEN-005 nom de capteur normalisé": lot["sensor_name"].astype(str)
            != lot["capteur"],
            "R-SEN-006 unité conforme": lot["unit"].astype(str)
            != lot["capteur"].map(UNITES_ATTENDUES).fillna(""),
            "R-SEN-007 valeur numérique": valeurs.isna(),
            "R-SEN-008 valeur non sentinelle": valeurs.isin(SENTINELLES),
            "R-SEN-009 valeur dans la plage physique": (valeurs < plages_basses)
            | (valeurs > plages_hautes),
            "R-SEN-013 équipement présent au parc": ~lot["equipment_id"].isin(parc),
            "R-SEN-014 mesure dans la période": (instants < PERIODE_DEBUT)
            | (instants >= PERIODE_FIN),
            "R-SEN-015 étiquette period cohérente": lot["period"].astype(str) != "2026-S1",
        },
        index=lot.index,
    )
