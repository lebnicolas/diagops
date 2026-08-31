"""Protocole d'évaluation M4 — splits groupés, gel et baseline comparable.

Ce module est écrit **avant** toute modélisation. Il fixe ce qui ne devra plus
bouger : l'unité de décision, la partition, la règle d'agrégation de la baseline
et les empreintes du point de départ. Toute modification après consultation du
test invalide la comparaison, et la règle de changement est écrite dans
`docs/protocole_evaluation.md`.

Le test (`sensor_test.csv`) n'est jamais chargé ici. Il est scellé jusqu'au gel
du candidat, et le formateur calcule les métriques finales sur son oracle.
"""

from __future__ import annotations

import hashlib
import platform
import subprocess
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold


#: Graine du module, reprise de `configs/model.yaml` — pas une des nôtres.
SEED = 20260831

#: Cible et classe positive, reprises de `configs/model.yaml`.
CIBLE = "provenance"
CLASSE_POSITIVE = "fabriquée"
CLASSE_NEGATIVE = "réelle"

#: `window_id` est le groupe indivisible imposé par le brief. `equipment_id` est
#: le groupe **de partition** retenu (arbitrage A2) : 20 des 22 équipements de
#: calibration réapparaissent dans le test, et 4 portent les deux provenances.
#: Partitionner sur `window_id` seul laisserait un même équipement des deux
#: côtés d'un pli, ce que le brief demande explicitement de vérifier.
COLONNE_GROUPE = "equipment_id"
COLONNE_FENETRE = "window_id"

#: Validation croisée : 5 plis stratifiés répétés 5 fois. Sur 30 fenêtres dont
#: 11 positives, un tirage unique donne des plis de 6 fenêtres avec 1 à 3
#: positifs — trop instable pour départager deux modèles. La répétition ne crée
#: pas d'information, elle rend la dispersion mesurable.
N_PLIS = 5
N_REPETITIONS = 5

PACK = Path("../../data_pack/2026-S1")
CALIBRATION = PACK / "model_eval" / "sensor_calibration.csv"
TEST_SCELLE = PACK / "model_eval" / "sensor_test.csv"
BASELINE_DIR = PACK / "reference_runs" / "m3_for_m4"


def sha256(chemin: Path) -> str:
    empreinte = hashlib.sha256()
    with chemin.open("rb") as handle:
        for bloc in iter(lambda: handle.read(1024 * 1024), b""):
            empreinte.update(bloc)
    return empreinte.hexdigest()


# --- point de départ -------------------------------------------------------


def charger_calibration() -> pd.DataFrame:
    """Les 900 lignes étiquetées. Le test n'est pas chargé par ce module."""
    return pd.read_csv(CALIBRATION)


def table_fenetres(lignes: pd.DataFrame) -> pd.DataFrame:
    """Une ligne par fenêtre — l'unité à laquelle l'étiquette existe.

    L'étiquette `provenance` est constante à l'intérieur d'une fenêtre : c'est
    vérifié ici plutôt que supposé, parce que toute la partition en dépend.
    """
    par_fenetre = lignes.groupby(COLONNE_FENETRE)[CIBLE].nunique()
    incoherentes = par_fenetre[par_fenetre > 1]
    if len(incoherentes):
        raise ValueError(
            "fenêtres à provenance non unique : " + ", ".join(incoherentes.index)
        )

    table = (
        lignes.groupby(COLONNE_FENETRE)
        .agg(
            equipment_id=("equipment_id", "first"),
            sensor_name=("sensor_name", "first"),
            unit=("unit", "first"),
            lignes=("value", "size"),
            provenance=(CIBLE, "first"),
        )
        .reset_index()
    )
    table["y"] = (table["provenance"] == CLASSE_POSITIVE).astype(int)
    return table


# --- partition -------------------------------------------------------------


@dataclass(frozen=True)
class Pli:
    repetition: int
    pli: int
    entrainement: tuple[str, ...]
    validation: tuple[str, ...]


def plis(table: pd.DataFrame) -> list[Pli]:
    """Plis stratifiés, groupés par équipement, répétés.

    `StratifiedGroupKFold` conserve le ratio de positifs dans chaque pli tout
    en gardant chaque équipement entier d'un seul côté. Sur cet effectif, la
    stratification n'est pas un raffinement : sans elle, un pli peut ne
    contenir aucun positif et rendre le F1 indéfini.
    """
    resultat: list[Pli] = []
    for repetition in range(N_REPETITIONS):
        decoupage = StratifiedGroupKFold(
            n_splits=N_PLIS, shuffle=True, random_state=SEED + repetition
        )
        for index, (apprentissage, validation) in enumerate(
            decoupage.split(table, table["y"], groups=table[COLONNE_GROUPE])
        ):
            resultat.append(
                Pli(
                    repetition=repetition,
                    pli=index,
                    entrainement=tuple(table.iloc[apprentissage][COLONNE_FENETRE]),
                    validation=tuple(table.iloc[validation][COLONNE_FENETRE]),
                )
            )
    return resultat


def verifier_absence_de_fuite(table: pd.DataFrame, decoupes: list[Pli]) -> dict[str, object]:
    """Contrôle bloquant : aucun équipement des deux côtés d'un même pli.

    Un contrôle qui s'arrête à la première faute ne dit pas combien il y en a :
    on compte, on nomme, et on rend un rapport.
    """
    equipements = table.set_index(COLONNE_FENETRE)[COLONNE_GROUPE].to_dict()
    fautes: list[str] = []
    plis_sans_positif = 0
    y = table.set_index(COLONNE_FENETRE)["y"].to_dict()

    for decoupe in decoupes:
        gauche = {equipements[f] for f in decoupe.entrainement}
        droite = {equipements[f] for f in decoupe.validation}
        commun = gauche & droite
        if commun:
            fautes.append(
                f"r{decoupe.repetition}p{decoupe.pli} : " + ", ".join(sorted(commun))
            )
        if sum(y[f] for f in decoupe.validation) == 0:
            plis_sans_positif += 1

    tailles = [len(d.validation) for d in decoupes]
    positifs = [sum(y[f] for f in d.validation) for d in decoupes]
    return {
        "plis": len(decoupes),
        "equipements_traversant_un_pli": fautes,
        "sans_fuite": not fautes,
        "plis_de_validation_sans_positif": plis_sans_positif,
        "taille_validation_min": min(tailles),
        "taille_validation_max": max(tailles),
        "positifs_validation_min": min(positifs),
        "positifs_validation_max": max(positifs),
    }


# --- baseline comparable ---------------------------------------------------


def scores(vrais: pd.Series, predits: pd.Series) -> dict[str, float | int]:
    """Comptages et métriques sur la classe positive `fabriquée`.

    Écrit à la main plutôt qu'emprunté à scikit-learn : la baseline de référence
    calcule ses métriques ainsi, et les deux chiffres doivent se retrouver au
    millième près pour que la comparaison soit défendable.
    """
    vp = int(((vrais == CLASSE_POSITIVE) & (predits == CLASSE_POSITIVE)).sum())
    fp = int(((vrais == CLASSE_NEGATIVE) & (predits == CLASSE_POSITIVE)).sum())
    fn = int(((vrais == CLASSE_POSITIVE) & (predits == CLASSE_NEGATIVE)).sum())
    vn = int(((vrais == CLASSE_NEGATIVE) & (predits == CLASSE_NEGATIVE)).sum())
    precision = vp / (vp + fp) if vp + fp else 0.0
    rappel = vp / (vp + fn) if vp + fn else 0.0
    f1 = 2 * precision * rappel / (precision + rappel) if precision + rappel else 0.0
    return {
        "n": vp + fp + fn + vn,
        "vrai_positif": vp,
        "faux_positif": fp,
        "faux_negatif": fn,
        "vrai_negatif": vn,
        "precision": round(precision, 6),
        "rappel": round(rappel, 6),
        "f1": round(f1, 6),
        "exactitude": round((vp + vn) / (vp + fp + fn + vn), 6),
    }


#: Règle d'agrégation de la baseline vers la fenêtre (arbitrage A1).
#:
#: La baseline est **presque** tout ou rien : sur les 30 fenêtres, 24 n'ont
#: aucune ligne signalée, 5 en ont 30 — et une seule fait exception,
#: `M4-CAL-019`, avec **exactement 1 ligne** signalée. C'est la sentinelle
#: `-999` isolée du lot, sur une fenêtre `pressure_bar` authentique.
#:
#: Cette unique ligne décide du seuil. À 1, elle transforme une fenêtre réelle
#: en faux positif et fait tomber le F1 de la baseline à 0,353 ; à partir de 2,
#: la baseline rend 0,375. Le seuil retenu est donc **2**, et le motif n'est pas
#: qu'il nous arrange : c'est qu'on ne bat pas une baseline qu'on a soi-même
#: handicapée par un choix d'agrégation. Une valeur aberrante isolée sur 30
#: mesures signale un défaut de qualité, pas une fenêtre fabriquée — c'est
#: exactement la distinction établie au brief 2 M3.
#:
#: La sensibilité au seuil est rapportée dans `protocole.json` pour que ce choix
#: soit vérifiable et non pas simplement affirmé.
SEUIL_AGREGATION = 2


def baseline_predictions() -> pd.DataFrame:
    """Prédictions M3 figées, telles que livrées — jamais recalculées."""
    return pd.read_csv(BASELINE_DIR / "baseline_predictions_calibration.csv")


def baseline_deux_niveaux() -> dict[str, dict]:
    """La baseline mesurée à la ligne **et** à la fenêtre.

    Le brief exige des baselines comparables. Notre modèle décidera par fenêtre,
    la baseline décide par ligne : sans cette agrégation, la comparaison
    opposerait deux unités de décision différentes.
    """
    predictions = baseline_predictions()
    par_ligne = scores(predictions[CIBLE], predictions["prediction"])

    agrege = predictions.groupby(COLONNE_FENETRE).agg(
        provenance=(CIBLE, "first"),
        signalees=("prediction", lambda serie: int((serie == CLASSE_POSITIVE).sum())),
    )
    predits = pd.Series(
        [
            CLASSE_POSITIVE if n >= SEUIL_AGREGATION else CLASSE_NEGATIVE
            for n in agrege["signalees"]
        ],
        index=agrege.index,
    )
    par_fenetre = scores(agrege["provenance"], predits)

    sensibilite = {}
    for seuil in (1, 5, 10, 15, 20, 25, 30):
        p = pd.Series(
            [
                CLASSE_POSITIVE if n >= seuil else CLASSE_NEGATIVE
                for n in agrege["signalees"]
            ],
            index=agrege.index,
        )
        sensibilite[seuil] = scores(agrege["provenance"], p)["f1"]

    return {
        "par_ligne": par_ligne,
        "par_fenetre": par_fenetre,
        "seuil_agregation": SEUIL_AGREGATION,
        "f1_par_seuil_agregation": sensibilite,
        "lignes_signalees_par_fenetre": agrege["signalees"].to_dict(),
    }


# --- gel -------------------------------------------------------------------


def environnement() -> dict[str, str]:
    """Versions et plateforme, pour qu'un rejeu puisse être comparé."""
    import numpy
    import sklearn

    return {
        "python": platform.python_version(),
        "plateforme": platform.platform(),
        "numpy": numpy.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
    }


def commit_courant() -> str:
    """Empreinte git du dépôt, si disponible — sinon `inconnu`."""
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True, timeout=10,
        ).stdout.strip()
    except Exception:
        return "inconnu"


def empreintes() -> dict[str, str]:
    """Empreintes des entrées, y compris celle du test **sans l'ouvrir**.

    Lire les octets d'un fichier pour en calculer l'empreinte n'est pas
    consulter ses étiquettes : le test ne porte pas de colonne `provenance`.
    L'empreinte sert à prouver, après coup, que le fichier évalué est bien celui
    qui était scellé au moment du gel.
    """
    fichiers = {
        "sensor_calibration.csv": CALIBRATION,
        "sensor_test.csv": TEST_SCELLE,
        "baseline_predictions_calibration.csv": BASELINE_DIR / "baseline_predictions_calibration.csv",
        "baseline_metrics_calibration.json": BASELINE_DIR / "baseline_metrics_calibration.json",
        "baseline_rules.py": BASELINE_DIR / "baseline_rules.py",
    }
    return {nom: sha256(chemin) for nom, chemin in fichiers.items()}
