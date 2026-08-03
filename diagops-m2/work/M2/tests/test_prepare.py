"""Cas valides et invalides du masquage des donnees personnelles."""

from __future__ import annotations

import pandas as pd

from src.data_pipeline.prepare import (
    PERSONAL_DATA_PLACEHOLDER,
    TRANSFORMATION_LOG_COLUMNS,
    drop_duplicate_rows,
    export_prepared,
    mask_personal_notes,
    normalize_case_variants,
    normalize_declared_labels,
    prepare_all,
)
from src.data_pipeline.rules import EVENT_TYPE_VALUES, SEVERITY_VALUES


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"maintenance_id": "MT-1", "work_order_note": "Controle visuel realise.",
             "parts_cost_eur": 120.0},
            {"maintenance_id": "MT-2", "work_order_note": "Rappeler Nadia B. au 06 12 34 56 78.",
             "parts_cost_eur": 80.0},
            {"maintenance_id": "MT-3", "work_order_note": "Compte rendu transmis a leo.martin@example.test.",
             "parts_cost_eur": 0.0},
        ]
    )


def test_seules_les_notes_concernees_sont_masquees():
    prepared, _ = mask_personal_notes(_frame())
    assert prepared.at[0, "work_order_note"] == "Controle visuel realise."
    assert prepared.at[1, "work_order_note"] == PERSONAL_DATA_PLACEHOLDER
    assert prepared.at[2, "work_order_note"] == PERSONAL_DATA_PLACEHOLDER


def test_les_lignes_sont_conservees_avec_leurs_autres_colonnes():
    original = _frame()
    prepared, _ = mask_personal_notes(original)
    assert len(prepared) == len(original)
    pd.testing.assert_series_equal(prepared["parts_cost_eur"], original["parts_cost_eur"])
    assert prepared["maintenance_id"].tolist() == ["MT-1", "MT-2", "MT-3"]


def test_la_table_source_n_est_pas_modifiee():
    original = _frame()
    avant = original.copy(deep=True)
    mask_personal_notes(original)
    pd.testing.assert_frame_equal(original, avant)


def test_le_journal_est_au_format_attendu():
    _, log = mask_personal_notes(_frame())
    assert list(log.columns) == TRANSFORMATION_LOG_COLUMNS
    assert len(log) == 2
    assert set(log["rule_id"]) == {"MNT-PII-001"}


def test_le_journal_conserve_l_etat_initial():
    """Le brief exige de conserver l'etat initial de toute transformation.

    Sans la valeur d'origine, la correction n'est ni verifiable par un
    relecteur ni reversible. Le journal est un artefact d'audit ; c'est la
    table preparee, elle, qui ne doit plus porter la donnee personnelle.
    """
    _, log = mask_personal_notes(_frame())
    avant = " ".join(log["before"].tolist())
    assert "Nadia B. au 06 12 34 56 78" in avant
    assert "leo.martin@example.test" in avant
    assert set(log["after"]) == {PERSONAL_DATA_PLACEHOLDER}


def test_le_masquage_est_idempotent():
    prepared, _ = mask_personal_notes(_frame())
    reprepared, log = mask_personal_notes(prepared)
    assert log.empty
    pd.testing.assert_frame_equal(prepared, reprepared)


def test_aucune_donnee_personnelle_ne_subsiste_apres_masquage():
    prepared, _ = mask_personal_notes(_frame())
    texte = " ".join(prepared["work_order_note"].tolist())
    for fragment in ("Nadia", "06 12", "leo.martin"):
        assert fragment not in texte


# ----------------------------------------------------------------------
# Deduplication
# ----------------------------------------------------------------------


def test_drop_duplicate_rows_ne_retire_que_les_copies():
    frame = pd.DataFrame(
        [
            {"event_id": "EV-1", "severity": "high"},
            {"event_id": "EV-1", "severity": "high"},
            {"event_id": "EV-2", "severity": "low"},
        ]
    )
    prepared, log = drop_duplicate_rows(frame, source="events", rule_id="EVT-KEY-003")
    assert len(prepared) == 2
    assert log.at[0, "rows_affected"] == 1


def test_drop_duplicate_rows_epargne_un_identifiant_duplique_sur_lignes_differentes():
    """Meme cle mais colonnes differentes : rien ne dit laquelle garder."""
    frame = pd.DataFrame(
        [
            {"event_id": "EV-1", "severity": "high"},
            {"event_id": "EV-1", "severity": "low"},
        ]
    )
    prepared, log = drop_duplicate_rows(frame, source="events", rule_id="EVT-KEY-003")
    assert len(prepared) == 2
    assert log.empty


# ----------------------------------------------------------------------
# Normalisation de casse
# ----------------------------------------------------------------------


def test_normalize_case_variants_corrige_la_casse_connue():
    frame = pd.DataFrame({"event_type": ["Incident", "incident", "observation"]})
    prepared, log = normalize_case_variants(
        frame, "event_type", EVENT_TYPE_VALUES, source="events", rule_id="EVT-CAS-001"
    )
    assert prepared["event_type"].tolist() == ["incident", "incident", "observation"]
    assert log.at[0, "rows_affected"] == 1


def test_normalize_case_variants_ne_touche_pas_une_valeur_inconnue():
    """URGENT et alert ne sont pas des fautes de casse : les corriger serait deviner."""
    frame = pd.DataFrame({"severity": ["URGENT", "high"]})
    prepared, log = normalize_case_variants(
        frame, "severity", SEVERITY_VALUES, source="events", rule_id="EVT-CAS-002"
    )
    assert prepared["severity"].tolist() == ["URGENT", "high"]
    assert log.empty


# ----------------------------------------------------------------------
# Enchainement complet
# ----------------------------------------------------------------------


def _pipeline_frames() -> dict[str, pd.DataFrame]:
    equipment = pd.DataFrame(
        [
            {"equipment_id": "EQ-1", "criticality": "High"},
            {"equipment_id": "EQ-2", "criticality": "low"},
            {"equipment_id": "EQ-2", "criticality": "low"},
        ]
    )
    events = pd.DataFrame(
        [
            {"event_id": "EV-1", "event_type": "Incident", "severity": "high"},
            {"event_id": "EV-2", "event_type": "alert", "severity": "URGENT"},
        ]
    )
    maintenance = pd.DataFrame(
        [
            {"maintenance_id": "MT-1", "work_order_note": "Controle realise."},
            {"maintenance_id": "MT-2", "work_order_note": "Ecrire a a@b.fr"},
        ]
    )
    return {"equipment": equipment, "events": events, "maintenance": maintenance}


def test_normalize_declared_labels_applique_les_equivalences_declarees():
    frame = pd.DataFrame({"equipment_type": ["Pump ", "pump", "fan"]})
    prepared, log = normalize_declared_labels(
        frame, "equipment_type", {"Pump ": "pump"}, source="equipment", rule_id="EQP-CAS-002"
    )
    assert prepared["equipment_type"].tolist() == ["pump", "pump", "fan"]
    assert log.at[0, "rows_affected"] == 1


def test_normalize_declared_labels_ne_touche_pas_aux_libelles_non_declares():
    """Rien n'est deduit : un libelle absent de la table reste tel quel."""
    frame = pd.DataFrame({"intervention_type": ["Preventif", "corrective"]})
    prepared, log = normalize_declared_labels(
        frame,
        "intervention_type",
        {"Correctif": "corrective"},
        source="maintenance",
        rule_id="MNT-CAS-001",
    )
    assert prepared["intervention_type"].tolist() == ["Preventif", "corrective"]
    assert log.empty


def test_prepare_all_applique_les_trois_familles():
    prepared, log = prepare_all(_pipeline_frames())
    assert len(prepared["equipment"]) == 2  # doublon integral retire
    assert prepared["equipment"]["criticality"].tolist() == ["high", "low"]
    assert prepared["events"]["event_type"].tolist() == ["incident", "alert"]
    assert prepared["events"]["severity"].tolist() == ["high", "URGENT"]
    assert prepared["maintenance"].at[1, "work_order_note"] == PERSONAL_DATA_PLACEHOLDER
    assert list(log.columns) == TRANSFORMATION_LOG_COLUMNS
    assert set(log["rule_id"]) == {"EQP-KEY-003", "EQP-CAS-001", "EVT-CAS-001", "MNT-PII-001"}


def test_prepare_all_ne_touche_pas_aux_tables_recues():
    frames = _pipeline_frames()
    avant = {name: frame.copy(deep=True) for name, frame in frames.items()}
    prepare_all(frames)
    for name, frame in frames.items():
        pd.testing.assert_frame_equal(frame, avant[name])


def test_export_ecrit_les_livrables_sans_toucher_aux_sources(tmp_path):
    frames = _pipeline_frames()
    prepared, log = prepare_all(frames)
    written = export_prepared(
        prepared=prepared,
        quarantine=pd.DataFrame(columns=["source_file", "row_identifier"]),
        transformation_log=log,
        check_results=pd.DataFrame(columns=["rule_id", "failures"]),
        output_dir=tmp_path,
    )
    attendus = {
        "processed/equipment.csv",
        "processed/events.csv",
        "processed/maintenance_history.csv",
        "quarantine.csv",
        "transformation_log.csv",
        "check_results.csv",
    }
    assert set(written) == attendus
    assert all(path.is_file() for path in written.values())
    # relecture : ce qui est ecrit doit se relire a l'identique
    relu = pd.read_csv(tmp_path / "processed" / "events.csv")
    pd.testing.assert_frame_equal(relu, prepared["events"])


def test_export_ecrit_en_lf_et_utf8(tmp_path):
    """Une sortie dont les octets changent selon la machine n'est pas reproductible."""
    prepared, log = prepare_all(_pipeline_frames())
    export_prepared(
        prepared=prepared,
        quarantine=pd.DataFrame(columns=["a"]),
        transformation_log=log,
        check_results=pd.DataFrame(columns=["a"]),
        output_dir=tmp_path,
    )
    octets = (tmp_path / "processed" / "events.csv").read_bytes()
    assert b"\r\n" not in octets


def test_la_deduplication_precede_la_normalisation():
    """La normalisation ne doit jamais fabriquer un doublon ensuite supprime.

    Les deux lignes ne different que par la casse : elles ne sont PAS des
    doublons a la source. Apres normalisation elles deviennent identiques, et
    les deux doivent survivre — sinon on aurait efface une ligne reelle.
    """
    frames = {
        "equipment": pd.DataFrame([{"equipment_id": "EQ-1", "criticality": "high"}]),
        "events": pd.DataFrame(
            [
                {"event_id": "EV-1", "event_type": "Incident", "severity": "high"},
                {"event_id": "EV-1", "event_type": "incident", "severity": "high"},
            ]
        ),
        "maintenance": pd.DataFrame([{"maintenance_id": "MT-1", "work_order_note": "RAS"}]),
    }
    prepared, _ = prepare_all(frames)
    assert len(prepared["events"]) == 2
    assert prepared["events"]["event_type"].tolist() == ["incident", "incident"]
