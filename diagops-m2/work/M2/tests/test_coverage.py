"""Cas valides et invalides de l'analyse de couverture."""

from __future__ import annotations

import pandas as pd

from src.data_pipeline.coverage import (
    category_counts,
    error_concentration,
    orphan_equipment,
)


def _frames() -> dict[str, pd.DataFrame]:
    equipment = pd.DataFrame(
        [
            {"equipment_id": "EQ-1", "equipment_type": "pump", "site_id": "S1", "criticality": "high"},
            {"equipment_id": "EQ-2", "equipment_type": "pump", "site_id": "S1", "criticality": "low"},
            {"equipment_id": "EQ-3", "equipment_type": "fan", "site_id": "S2", "criticality": "high"},
        ]
    )
    events = pd.DataFrame(
        [
            {"event_id": "EV-1", "equipment_id": "EQ-1", "severity": "high"},
            {"event_id": "EV-2", "equipment_id": "EQ-1", "severity": "low"},
        ]
    )
    maintenance = pd.DataFrame([{"maintenance_id": "MT-1", "equipment_id": "EQ-2", "event_id": "EV-1"}])
    return {"equipment": equipment, "events": events, "maintenance": maintenance}


def test_category_counts_marque_les_effectifs_insuffisants():
    table = category_counts(_frames()["equipment"], "equipment_type", min_effectif=2)
    assert table["categorie"].tolist() == ["fan", "pump"]
    assert table["effectif"].tolist() == [1, 2]
    assert table["interpretable"].tolist() == [False, True]


def test_orphan_equipment_distingue_evenements_et_interventions():
    report = orphan_equipment(_frames()).set_index("equipment_id")
    assert report.at["EQ-1", "a_des_evenements"] and not report.at["EQ-1", "a_des_interventions"]
    assert not report.at["EQ-2", "a_des_evenements"] and report.at["EQ-2", "a_des_interventions"]
    assert not report.at["EQ-3", "a_des_evenements"]
    assert not report.at["EQ-3", "a_des_interventions"]


def _matrix() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"equipment_id": "EQ-1", "event_id": "EV-1", "severity_correct": True, "human_review_correct": True},
            {"equipment_id": "EQ-1", "event_id": "EV-2", "severity_correct": False, "human_review_correct": True},
            {"equipment_id": "EQ-3", "event_id": "EV-9", "severity_correct": False, "human_review_correct": False},
            # cle absente : ni rattachable, ni comptee dans les taux
            {"equipment_id": None, "event_id": None, "severity_correct": True, "human_review_correct": True},
        ]
    )


def test_error_concentration_calcule_les_taux_par_categorie():
    table, _ = error_concentration(_matrix(), _frames(), "criticality", min_effectif=2)
    taux = dict(zip(table["criticality"], table["taux_erreur_severite"]))
    assert taux["high"] == 0.6667  # 2 erreurs sur 3 cas rattaches a un equipement high


def test_error_concentration_rend_compte_des_lignes_non_rattachees():
    _, diagnostic = error_concentration(_matrix(), _frames(), "criticality")
    assert diagnostic == {"lignes_matrice": 4, "appariees": 3, "orphelines": 1}


def test_error_concentration_ne_conclut_pas_sur_un_petit_effectif():
    table, _ = error_concentration(_matrix(), _frames(), "criticality", min_effectif=30)
    assert not table["interpretable"].any()
