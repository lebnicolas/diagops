"""Audit de bout en bout sur un jeu synthetique aux anomalies connues.

Le jeu est volontairement minuscule : chaque anomalie y est plantee
deliberement, ce qui permet de verifier que la regle attendue la remonte — et
qu'aucune autre ne se declenche a tort.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.data_pipeline.audit import QUARANTINE_COLUMNS, run_audit
from src.data_pipeline.rules import rule_register


REFERENCE_DATE = pd.Timestamp("2026-08-03")


@pytest.fixture
def frames() -> dict[str, pd.DataFrame]:
    equipment = pd.DataFrame(
        [
            # ligne saine
            {"equipment_id": "EQ-1", "equipment_type": "pompe", "site_id": "S1",
             "commissioning_date": "2020-01-15", "criticality": "high",
             "manufacturer": "ACME", "rated_power_kw": 75.0},
            # criticite hors enumeration + puissance negative
            {"equipment_id": "EQ-2", "equipment_type": "moteur", "site_id": "S1",
             "commissioning_date": "2019-06-01", "criticality": "urgent",
             "manufacturer": None, "rated_power_kw": -5.0},
            # identifiant duplique + date sentinelle
            {"equipment_id": "EQ-1", "equipment_type": "vanne", "site_id": "S2",
             "commissioning_date": "1900-01-01", "criticality": "low",
             "manufacturer": "ACME", "rated_power_kw": 10.0},
        ]
    )

    events = pd.DataFrame(
        [
            {"event_id": "EV-1", "equipment_id": "EQ-1", "start_at": "2026-03-01T08:00:00",
             "end_at": "2026-03-01T10:00:00", "event_type": "incident",
             "severity": "high", "period": "2026-S1"},
            # reference orpheline + fin avant debut
            {"event_id": "EV-2", "equipment_id": "EQ-404", "start_at": "2026-03-02T08:00:00",
             "end_at": "2026-03-02T07:00:00", "event_type": "alerte",
             "severity": "low", "period": "2026-S1"},
            # periode inattendue + evenement en cours
            {"event_id": "EV-3", "equipment_id": "EQ-2", "start_at": "2026-03-03T08:00:00",
             "end_at": None, "event_type": "observation",
             "severity": "medium", "period": "2026-S2"},
        ]
    )

    maintenance = pd.DataFrame(
        [
            {"maintenance_id": "MT-1", "event_id": "EV-1", "equipment_id": "EQ-1",
             "opened_at": "2026-03-01T09:00:00", "closed_at": "2026-03-01T11:00:00",
             "intervention_type": "corrective", "outcome": "resolu",
             "downtime_minutes": 60, "labor_hours": 2.0, "parts_cost_eur": 150.0,
             "parts_replaced_count": 2, "work_order_note": "Remplacement du palier",
             "period": "2026-S1"},
            # equipement contredit par l'evenement + cout sans piece + note avec email
            {"maintenance_id": "MT-2", "event_id": "EV-1", "equipment_id": "EQ-2",
             "opened_at": "2026-03-01T09:30:00", "closed_at": "2026-03-01T10:30:00",
             "intervention_type": "preventive", "outcome": "resolu",
             "downtime_minutes": 30, "labor_hours": 1.0, "parts_cost_eur": 80.0,
             "parts_replaced_count": 0,
             "work_order_note": "Voir avec jean.dupont@example.com", "period": "2026-S1"},
            # duree declaree superieure a l'ecart reel + intervention avant l'evenement
            {"maintenance_id": "MT-3", "event_id": "EV-3", "equipment_id": "EQ-2",
             "opened_at": "2026-03-03T07:00:00", "closed_at": "2026-03-03T08:00:00",
             "intervention_type": "corrective", "outcome": "en cours",
             "downtime_minutes": 600, "labor_hours": None, "parts_cost_eur": None,
             "parts_replaced_count": 0, "work_order_note": "RAS", "period": "2026-S1"},
        ]
    )

    return {"equipment": equipment, "events": events, "maintenance": maintenance}


def _failures(result, rule_id: str) -> int:
    row = result.check_results.loc[result.check_results["rule_id"] == rule_id]
    assert not row.empty, f"regle absente du resultat : {rule_id}"
    return int(row["failures"].iloc[0])


def test_toutes_les_regles_du_registre_sont_executees(frames):
    result = run_audit(frames, reference_date=REFERENCE_DATE)
    declarees = set(rule_register()["rule_id"])
    executees = set(result.check_results["rule_id"])
    assert declarees == executees


def test_structure_complete_ne_leve_rien(frames):
    result = run_audit(frames, reference_date=REFERENCE_DATE)
    assert _failures(result, "EQP-SCH-001") == 0
    assert _failures(result, "EVT-SCH-001") == 0
    assert _failures(result, "MNT-SCH-001") == 0


def test_anomalies_plantees_sont_detectees(frames):
    result = run_audit(frames, reference_date=REFERENCE_DATE)

    assert _failures(result, "EQP-KEY-002") == 2  # les deux EQ-1
    assert _failures(result, "EQP-CAT-001") == 1  # criticality "urgent"
    assert _failures(result, "EQP-TMP-002") == 1  # 1900-01-01
    assert _failures(result, "EQP-VAL-001") == 1  # puissance negative

    assert _failures(result, "EVT-REF-002") == 1  # EQ-404
    assert _failures(result, "EVT-TMP-001") == 1  # fin avant debut
    assert _failures(result, "EVT-CAT-003") == 1  # periode 2026-S2

    assert _failures(result, "MNT-REF-003") == 1  # MT-2 contredit EV-1
    assert _failures(result, "MNT-VAL-003") == 1  # 600 min sur 60 min d'ecart
    assert _failures(result, "MNT-VAL-007") == 1  # cout sans piece
    assert _failures(result, "MNT-TMP-003") == 1  # MT-3 ouverte avant EV-3
    assert _failures(result, "MNT-PII-001") == 1  # adresse dans la note


def test_lignes_saines_ne_declenchent_rien(frames):
    result = run_audit(frames, reference_date=REFERENCE_DATE)
    assert _failures(result, "EQP-KEY-001") == 0
    assert _failures(result, "EQP-KEY-003") == 0
    assert _failures(result, "EVT-KEY-002") == 0
    assert _failures(result, "MNT-KEY-002") == 0
    assert _failures(result, "MNT-VAL-001") == 0


def test_quarantaine_au_format_du_brief(frames):
    result = run_audit(frames, reference_date=REFERENCE_DATE)
    assert list(result.quarantine.columns) == QUARANTINE_COLUMNS
    assert not result.quarantine.empty
    # aucune regle de simple signalement ne remplit la quarantaine
    signalements = set(
        rule_register()
        .loc[rule_register()["decision_if_failed"] == "signalement", "rule_id"]
    )
    assert not (set(result.quarantine["rule_id"]) & signalements)


def test_une_ligne_peut_apparaitre_plusieurs_fois_en_quarantaine(frames):
    result = run_audit(frames, reference_date=REFERENCE_DATE)
    occurrences = result.quarantine["row_identifier"].value_counts()
    assert occurrences.max() >= 2


def test_audit_ne_modifie_pas_les_donnees(frames):
    avant = {name: frame.copy(deep=True) for name, frame in frames.items()}
    run_audit(frames, reference_date=REFERENCE_DATE)
    for name, frame in frames.items():
        pd.testing.assert_frame_equal(frame, avant[name])
