"""Cas valides et invalides de la construction du jeu supervise."""

from __future__ import annotations

import pandas as pd

from src.data_pipeline.dataset import (
    EXCLUDED,
    FEATURES,
    TARGET,
    baselines,
    build_features,
    build_training_set,
    split_by_equipment,
)


def _frames() -> dict[str, pd.DataFrame]:
    equipment = pd.DataFrame(
        [
            {"equipment_id": f"EQ-{i}", "equipment_type": "pump" if i % 2 else "fan",
             "site_id": "S1", "criticality": "high", "manufacturer": "ACME",
             "rated_power_kw": 50.0, "commissioning_date": "2020-01-01"}
            for i in range(1, 21)
        ]
    )
    events = pd.DataFrame(
        [
            {"event_id": f"EV-{i}", "equipment_id": f"EQ-{i}",
             "start_at": "2026-03-01T08:00:00Z", "end_at": "2026-03-01T10:00:00Z",
             "event_type": "incident",
             "severity": "high" if i % 2 else "low", "period": "2026-S1"}
            for i in range(1, 21)
        ]
    )
    return {"equipment": equipment, "events": events, "maintenance": pd.DataFrame()}


def test_les_variables_de_maintenance_sont_absentes():
    """Aucune colonne posterieure a l'evaluation ne doit entrer dans le jeu."""
    usable, _ = build_features(_frames())
    for interdite in ("downtime_minutes", "parts_cost_eur", "outcome", "intervention_type"):
        assert interdite not in usable.columns
        assert interdite in EXCLUDED


def test_end_at_est_exclu():
    """La duree de l'evenement n'est pas connue au moment du tri."""
    usable, _ = build_features(_frames())
    assert "end_at" not in usable.columns
    assert "duration" not in usable.columns


def test_les_variables_derivees_sont_calculees():
    usable, _ = build_features(_frames())
    assert set(FEATURES).issubset(usable.columns)
    assert usable["equipment_age_days"].notna().all()
    assert usable["start_hour"].between(0, 23).all()


def test_les_lignes_ecartees_portent_un_motif():
    frames = _frames()
    frames["events"].loc[0, TARGET] = "URGENT"
    frames["events"].loc[1, "equipment_id"] = "EQ-INEXISTANT"
    usable, excluded = build_features(frames)
    assert len(usable) == 18
    assert set(excluded["motif_exclusion"]) == {
        "severite hors enumeration",
        "equipement non joignable",
    }


def test_un_equipement_n_apparait_que_dans_un_paquet():
    """Le garde-fou central : pas de fuite par groupe."""
    usable, _ = build_features(_frames())
    splits = split_by_equipment(usable, seed=42)
    ids = {name: set(frame["equipment_id"]) for name, frame in splits.items()}
    assert not (ids["train"] & ids["test"])
    assert not (ids["train"] & ids["validation"])
    assert not (ids["validation"] & ids["test"])


def test_le_decoupage_est_reproductible():
    usable, _ = build_features(_frames())
    a = split_by_equipment(usable, seed=42)
    b = split_by_equipment(usable, seed=42)
    for name in a:
        pd.testing.assert_frame_equal(a[name], b[name])


def test_un_autre_seed_donne_un_autre_decoupage():
    usable, _ = build_features(_frames())
    a = split_by_equipment(usable, seed=42)["train"]
    b = split_by_equipment(usable, seed=7)["train"]
    assert set(a["equipment_id"]) != set(b["equipment_id"])


def test_toutes_les_lignes_sont_reparties():
    usable, _ = build_features(_frames())
    splits = split_by_equipment(usable, seed=42)
    assert sum(len(f) for f in splits.values()) == len(usable)


def test_les_references_sont_calculees_sur_le_train_seul():
    """La table de correspondance ne doit rien apprendre du test."""
    train = pd.DataFrame(
        {"equipment_type": ["pump"] * 8 + ["fan"] * 2, TARGET: ["high"] * 8 + ["low"] * 2}
    )
    test = pd.DataFrame({"equipment_type": ["pump", "fan"], TARGET: ["high", "low"]})
    scores = baselines(train, test)
    assert scores["classe_majoritaire"] == 0.5   # "high" sur 1 des 2 lignes
    assert scores["table_equipment_type"] == 1.0  # pump->high, fan->low


def test_un_type_inconnu_du_train_retombe_sur_la_classe_majoritaire():
    train = pd.DataFrame({"equipment_type": ["pump"] * 3, TARGET: ["high"] * 3})
    test = pd.DataFrame({"equipment_type": ["oven"], TARGET: ["high"]})
    assert baselines(train, test)["table_equipment_type"] == 1.0


def test_build_training_set_rend_un_ensemble_coherent():
    resultat = build_training_set(_frames())
    assert set(resultat.splits) == {"train", "validation", "test"}
    assert sum(resultat.sizes().values()) == 20
    assert set(resultat.baselines) == {"classe_majoritaire", "table_equipment_type"}
    assert resultat.seed == 42
