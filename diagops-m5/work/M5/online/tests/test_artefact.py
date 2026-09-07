"""L'artefact déployé doit être celui qui a été gelé, et se comporter comme lui.

Trois façons de servir un modèle faux sans qu'aucune erreur ne se lève :
un autre fichier `.joblib`, une extraction de features qui a dérivé, un ordre de colonnes
différent. Aucune ne plante — les trois donnent des prédictions plausibles et fausses.
Ces tests ferment les trois portes.
"""

from pathlib import Path

import pandas as pd
import pytest

from src.features import COLONNE_FENETRE, NOMS_FEATURES, features_fenetre
from src.scoring import CHECKSUM_ATTENDU, SKLEARN_DU_GEL, charger, fenetres_depuis_csv


RACINE = Path(__file__).resolve().parents[4]
CALIBRATION = RACINE / "data_pack/2026-S1/model_eval/sensor_calibration.csv"
# Features recalculées en M4, conservées comme oracle d'équivalence.
FEATURES_M4 = RACINE.parent / "diagops-m4/work/M4/results/modele/features.csv"


@pytest.fixture(scope="module")
def modele():
    return charger()


def test_l_artefact_est_celui_du_gel(modele) -> None:
    assert modele.checksum.startswith(CHECKSUM_ATTENDU)


def test_le_gel_declare_dix_neuf_features(modele) -> None:
    assert len(modele.features) == 19
    assert modele.features == NOMS_FEATURES


def test_le_seuil_de_decision_vient_du_gel(modele) -> None:
    assert modele.seuil == 0.5


def test_la_version_de_sklearn_est_celle_du_gel(modele) -> None:
    """Un joblib chargé par une autre version est au mieux bruyant, au pire différent."""
    assert modele.sklearn_version == SKLEARN_DU_GEL
    assert modele.sklearn_conforme is True


@pytest.mark.skipif(not FEATURES_M4.is_file(), reason="features de référence M4 indisponibles")
def test_l_extraction_reproduit_exactement_celle_de_m4() -> None:
    """30 fenêtres × 19 features, comparées aux valeurs produites en M4.

    C'est le test qui compte le plus de ce fichier : une dérive d'extraction rendrait le modèle
    gelé silencieusement faux. Il prédirait correctement — sur les mauvaises entrées.
    """
    reference = pd.read_csv(FEATURES_M4)
    lignes = pd.read_csv(CALIBRATION)
    lignes["timestamp"] = pd.to_datetime(lignes["timestamp"], utc=True, format="mixed")
    noms = [c for c in reference.columns if c not in ("window_id", "provenance")]

    ecarts = []
    for identifiant, groupe in lignes.groupby(COLONNE_FENETRE):
        calculees = features_fenetre(groupe)
        attendues = reference[reference.window_id == identifiant].iloc[0]
        for nom in noms:
            if abs(calculees[nom] - attendues[nom]) > 1e-9:
                ecarts.append((identifiant, nom))
    assert ecarts == [], f"{len(ecarts)} écarts d'extraction"


def test_l_ordre_des_features_change_le_resultat(modele) -> None:
    """Garde-fou : prouve que l'ordre n'est pas cosmétique.

    Si ce test échouait — si l'ordre était sans effet — la protection du module de scoring serait
    inutile, et il faudrait se demander pourquoi.
    """
    fenetres = fenetres_depuis_csv(CALIBRATION)
    mesures = next(iter(fenetres.values()))
    cadre = pd.DataFrame(mesures)
    cadre["timestamp"] = pd.to_datetime(cadre["timestamp"], utc=True, format="mixed")
    calculees = features_fenetre(cadre)

    droit = [[calculees[nom] for nom in modele.features]]
    inverse = [[calculees[nom] for nom in reversed(modele.features)]]
    assert modele.pipeline.predict_proba(droit)[0][1] != modele.pipeline.predict_proba(inverse)[0][1]


def test_le_modele_reproduit_son_comportement_sur_la_calibration(modele) -> None:
    """Non-régression de bout en bout : mêmes entrées, mêmes décisions qu'en M4.

    Le F1 obtenu ici (0,952) est **in-sample** : ces 30 fenêtres ont servi à ajuster le modèle.
    Il ne se compare pas au F1 hors pli de 0,694 déclaré au gel, et ne dit rien de la performance
    attendue en service. Ce qu'il vérifie, c'est que la chaîne déployée rend les mêmes décisions
    que la chaîne d'entraînement — pas qu'elle est bonne.
    """
    fenetres = fenetres_depuis_csv(CALIBRATION)
    verite = pd.read_csv(CALIBRATION).groupby(COLONNE_FENETRE)["provenance"].first()

    vrais_positifs = faux_positifs = faux_negatifs = 0
    for identifiant, mesures in fenetres.items():
        predite = modele.predire_fenetre(mesures)["provenance_predite"]
        attendue = verite[identifiant]
        if predite == "fabriquée" and attendue == "fabriquée":
            vrais_positifs += 1
        elif predite == "fabriquée":
            faux_positifs += 1
        elif attendue == "fabriquée":
            faux_negatifs += 1

    assert (vrais_positifs, faux_positifs, faux_negatifs) == (10, 0, 1)


def test_une_fenetre_trop_courte_est_refusee(modele) -> None:
    with pytest.raises((ValueError, KeyError, IndexError)):
        modele.predire_fenetre([])
