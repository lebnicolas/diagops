"""Cas de vérification du contrat de provenance — brief 2, étape 6.

Le contrat est le seul rempart entre « transmettre du fabriqué étiqueté » et
« transmettre du fabriqué », qui est un critère bloquant du brief. Ces cas sont
construits à la main : ils ne dépendent ni du `data_pack` ni des sorties des
scripts, et restent donc valables si la livraison change.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.brief2.provenance import (
    COLONNES_TRANSMISES,
    DECIMALES,
    REGISTRE,
    etiqueter,
    normaliser_precision,
    procedes_transmis,
    verifier_contrat,
)


def mesures(**surcharges) -> pd.DataFrame:
    """Deux lignes de mesures conformes au schéma de la livraison."""
    base = {
        "equipment_id": ["EQ-PUMP-001", "EQ-PUMP-001"],
        "timestamp": ["2026-01-01 00:00:00+00:00", "2026-01-01 06:00:00+00:00"],
        "sensor_name": ["vibration_mm_s", "vibration_mm_s"],
        "value": [2.45, 3.43],
        "unit": ["mm/s", "mm/s"],
        "period": ["2026-S1", "2026-S1"],
    }
    base.update(surcharges)
    return pd.DataFrame(base)


# --- étiquetage ------------------------------------------------------------


def test_etiquetage_pose_les_deux_colonnes_du_contrat():
    etiquete = etiqueter(mesures(), "synthétique", "PROC-GEN-SMOTE-V2")

    assert list(etiquete.columns) == list(COLONNES_TRANSMISES)
    assert (etiquete["provenance"] == "synthétique").all()
    assert (etiquete["procedure_id"] == "PROC-GEN-SMOTE-V2").all()


def test_etiquetage_retire_les_colonnes_de_travail():
    """`row_identifier` est signalée comme colonne inattendue par le détecteur."""
    avec_travail = mesures()
    avec_travail["row_identifier"] = ["EQ-PUMP-001|…|vibration_mm_s"] * 2

    etiquete = etiqueter(avec_travail, "réelle", "")

    assert "row_identifier" not in etiquete.columns


def test_etiquetage_refuse_une_provenance_hors_domaine():
    with pytest.raises(ValueError, match="provenance hors domaine"):
        etiqueter(mesures(), "inventée", "PROC-X")


def test_etiquetage_refuse_une_table_incomplete():
    incomplete = mesures().drop(columns=["unit"])

    with pytest.raises(ValueError, match="colonnes absentes du contrat"):
        etiqueter(incomplete, "réelle", "")


# --- vérification du contrat ----------------------------------------------


def test_contrat_respecte_sur_un_jeu_bien_forme():
    jeu = pd.concat(
        [
            etiqueter(mesures(), "réelle", ""),
            etiqueter(mesures(), "synthétique", "PROC-GEN-SMOTE-V2"),
        ],
        ignore_index=True,
    )

    rapport = verifier_contrat(jeu)

    assert rapport["conforme"]
    assert rapport["lignes"] == 4
    assert rapport["fabriquees_sans_procede"] == 0


def test_contrat_rejette_une_ligne_fabriquee_sans_procede():
    jeu = etiqueter(mesures(), "synthétique", "PROC-GEN-SMOTE-V2")
    jeu.loc[0, "procedure_id"] = ""

    rapport = verifier_contrat(jeu)

    assert not rapport["conforme"]
    assert rapport["fabriquees_sans_procede"] == 1


def test_contrat_rejette_un_procede_absent_du_registre():
    jeu = etiqueter(mesures(), "synthétique", "PROC-INCONNU-V9")

    rapport = verifier_contrat(jeu)

    assert not rapport["conforme"]
    assert rapport["procedes_inconnus"] == ["PROC-INCONNU-V9"]


def test_contrat_rejette_une_ligne_reelle_portant_un_procede():
    """Une mesure réelle n'a pas été produite : lui coller un procédé est faux."""
    jeu = etiqueter(mesures(), "réelle", "")
    jeu.loc[0, "procedure_id"] = "PROC-GEN-SMOTE-V2"

    rapport = verifier_contrat(jeu)

    assert not rapport["conforme"]
    assert rapport["reelles_portant_un_procede"] == 1


def test_contrat_rejette_une_colonne_surnumeraire():
    jeu = etiqueter(mesures(), "réelle", "")
    jeu["commentaire"] = "note libre"

    rapport = verifier_contrat(jeu)

    assert not rapport["conforme"]
    assert not rapport["colonnes_conformes"]


# --- R-TRA-001 -------------------------------------------------------------


def test_r_tra_001_ramene_la_precision_a_la_convention():
    """Le cas réel : conversion kelvin → °C écrite sans arrondi."""
    brut = mesures(value=[56.85000000000002, 64.49000000000001])

    corrige, modifiees = normaliser_precision(brut)

    assert modifiees == 2
    assert corrige["value"].tolist() == [56.85, 64.49]


def test_r_tra_001_ne_touche_pas_une_valeur_deja_conforme():
    corrige, modifiees = normaliser_precision(mesures())

    assert modifiees == 0
    assert corrige["value"].tolist() == [2.45, 3.43]


def test_r_tra_001_preserve_les_valeurs_absentes():
    """Les 52 valeurs vides du jeu transmis ne doivent pas devenir des zéros."""
    avec_trou = mesures(value=[None, 3.43])

    corrige, _ = normaliser_precision(avec_trou)

    assert corrige["value"].isna().sum() == 1
    assert corrige["value"].iloc[1] == 3.43


def test_convention_de_precision_alignee_sur_la_livraison():
    assert DECIMALES == 2


# --- registre des procédés -------------------------------------------------


def test_tout_procede_transmis_declare_sa_validite_et_son_motif():
    transmis = procedes_transmis()

    assert transmis, "au moins un procédé doit être transmis"
    for procede in transmis:
        assert procede.provenance != "réelle"
        assert procede.validite.strip()
        assert procede.motif_transmission.strip()
        assert procede.parametres.strip()


def test_les_procedes_ont_des_identifiants_uniques():
    identifiants = [procede.procedure_id for procede in REGISTRE]

    assert len(identifiants) == len(set(identifiants))


def test_tout_procede_ecarte_porte_le_motif_de_son_exclusion():
    """Un rejet sans motif écrit est un rejet qu'on ne peut pas défendre."""
    for procede in REGISTRE:
        if not procede.transmis:
            assert len(procede.motif_transmission) > 30
