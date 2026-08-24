"""Cas de verification de la pipeline M3.

Chaque regle a au moins un cas **valide** (la ligne passe) et un cas
**invalide** (la ligne est rejetee avec la bonne decision). Les cas sont
construits a la main : ils ne dependent pas du contenu du data_pack, donc ils
restent valables si la livraison change.

Trois exigences explicites du brief sont couvertes ici :
- au moins un cas temporel (grille, continuite, fuseau) ;
- la non-regression sur les trois tables M2 ;
- la distinction doublon strict / valeur divergente.
"""

from __future__ import annotations

import pandas as pd
import pytest

from src.data_pipeline.rules import Rule, RuleRegistry
from src.pipeline_m3 import build_registry, check_no_regression, prepare_sensors

PARK = {"EQ-PUMP-001", "EQ-FAN-002"}


def measurements(rows: list[dict]) -> pd.DataFrame:
    """Construit une table de mesures au format recu."""
    defaults = {
        "equipment_id": "EQ-PUMP-001",
        "timestamp": "2026-03-01T00:00:00Z",
        "sensor_name": "vibration_mm_s",
        "value": "2.80",
        "unit": "mm/s",
        "period": "2026-S1",
    }
    return pd.DataFrame([{**defaults, **row} for row in rows])


def quarantine_for(quarantine: pd.DataFrame, rule_id: str) -> pd.DataFrame:
    return quarantine[quarantine["rule_id"] == rule_id]


# --------------------------------------------------------------------------- #
# Cas valides
# --------------------------------------------------------------------------- #

def test_mesure_conforme_traverse_sans_rejet():
    prepared, quarantine, stats = prepare_sensors(measurements([{}]), PARK)
    assert len(prepared) == 1
    assert quarantine.empty
    assert stats["lignes_preparees"] == 1


def test_les_cinq_capteurs_du_domaine_sont_acceptes():
    rows = [
        {"sensor_name": "vibration_mm_s", "unit": "mm/s", "value": "2.80"},
        {"sensor_name": "temperature_c", "unit": "°C", "value": "57.0"},
        {"sensor_name": "pressure_bar", "unit": "bar", "value": "6.30"},
        {"sensor_name": "current_a", "unit": "A", "value": "23.0"},
        {"sensor_name": "rpm", "unit": "rpm", "value": "1440"},
    ]
    prepared, quarantine, _ = prepare_sensors(measurements(rows), PARK)
    assert len(prepared) == 5
    assert quarantine.empty


# --------------------------------------------------------------------------- #
# Cas invalides — une regle par bloc
# --------------------------------------------------------------------------- #

def test_r_sen_005_nom_de_capteur_normalise():
    frame = measurements([{"sensor_name": "VIBRATION_MM_S "}])
    prepared, quarantine, _ = prepare_sensors(frame, PARK)
    rejets = quarantine_for(quarantine, "R-SEN-005")
    assert len(rejets) == 1
    assert rejets.iloc[0]["decision"] == "valeur_normalisee"
    # La ligne est conservee, avec le nom corrige.
    assert prepared.iloc[0]["sensor_name"] == "vibration_mm_s"
    # L'identifiant garde la valeur RECUE : il doit pointer le fichier d'origine.
    assert "VIBRATION_MM_S " in rejets.iloc[0]["row_identifier"]


def test_r_sen_006_conversion_kpa_vers_bar():
    frame = measurements(
        [{"sensor_name": "pressure_bar", "unit": "kPa", "value": "630.0"}]
    )
    prepared, quarantine, _ = prepare_sensors(frame, PARK)
    assert len(quarantine_for(quarantine, "R-SEN-006")) == 1
    assert prepared.iloc[0]["value"] == pytest.approx(6.30)
    assert prepared.iloc[0]["unit"] == "bar"


def test_r_sen_006_conversion_kelvin_vers_celsius():
    frame = measurements(
        [{"sensor_name": "temperature_c", "unit": "K", "value": "330.15"}]
    )
    prepared, _, _ = prepare_sensors(frame, PARK)
    assert prepared.iloc[0]["value"] == pytest.approx(57.0)


def test_r_sen_008_sentinelle_neutralisee_et_ligne_conservee():
    frame = measurements([{"value": "-999"}])
    prepared, quarantine, _ = prepare_sensors(frame, PARK)
    rejets = quarantine_for(quarantine, "R-SEN-008")
    assert len(rejets) == 1
    assert rejets.iloc[0]["decision"] == "champ_neutralise"
    # La ligne reste : « le capteur n'a rien renvoye » est une information.
    assert len(prepared) == 1
    assert pd.isna(prepared.iloc[0]["value"])


def test_r_sen_007_valeur_vide_neutralisee():
    frame = measurements([{"value": ""}])
    prepared, quarantine, _ = prepare_sensors(frame, PARK)
    assert len(quarantine_for(quarantine, "R-SEN-007")) == 1
    assert len(prepared) == 1


def test_r_sen_013_equipement_hors_parc_exclu():
    frame = measurements([{"equipment_id": "EQ-ORPHAN-777"}])
    prepared, quarantine, _ = prepare_sensors(frame, PARK)
    rejets = quarantine_for(quarantine, "R-SEN-013")
    assert len(rejets) == 1
    assert rejets.iloc[0]["decision"] == "exclue"
    assert prepared.empty


def test_r_sen_015_etiquette_de_periode_normalisee():
    frame = measurements([{"period": "2026-S2"}])
    prepared, quarantine, _ = prepare_sensors(frame, PARK)
    assert len(quarantine_for(quarantine, "R-SEN-015")) == 1
    assert prepared.iloc[0]["period"] == "2026-S1"


# --------------------------------------------------------------------------- #
# Cle logique — la distinction qui compte
# --------------------------------------------------------------------------- #

def test_r_sen_001_doublon_strict_une_seule_ligne_conservee():
    frame = measurements([{}, {}])  # deux lignes rigoureusement identiques
    prepared, quarantine, _ = prepare_sensors(frame, PARK)
    rejets = quarantine_for(quarantine, "R-SEN-001")
    assert len(prepared) == 1
    assert len(rejets) == 1
    assert rejets.iloc[0]["decision"] == "doublon_supprime"


def test_r_sen_001_valeur_divergente_les_deux_lignes_exclues():
    """Arbitrage acte : sur une contradiction, aucune des deux valeurs n'est retenue."""
    frame = measurements([{"value": "2.80"}, {"value": "6.40"}])
    prepared, quarantine, _ = prepare_sensors(frame, PARK)
    rejets = quarantine_for(quarantine, "R-SEN-001")
    assert prepared.empty, "aucune des deux valeurs contradictoires ne doit passer"
    assert len(rejets) == 2
    assert set(rejets["decision"]) == {"exclue"}


def test_doublon_strict_et_divergent_ne_sont_pas_confondus():
    """Trois lignes sur deux cles : une paire stricte, une paire divergente."""
    frame = measurements(
        [
            {"timestamp": "2026-03-01T00:00:00Z", "value": "2.80"},
            {"timestamp": "2026-03-01T00:00:00Z", "value": "2.80"},
            {"timestamp": "2026-03-01T06:00:00Z", "value": "2.90"},
            {"timestamp": "2026-03-01T06:00:00Z", "value": "3.50"},
        ]
    )
    prepared, quarantine, stats = prepare_sensors(frame, PARK)
    assert stats["doublons_stricts_supprimes"] == 1
    assert stats["lignes_cle_divergente_exclues"] == 2
    assert len(prepared) == 1  # seul le doublon strict laisse une ligne


# --------------------------------------------------------------------------- #
# Cas temporels
# --------------------------------------------------------------------------- #

def test_r_sen_002_horodatage_sans_fuseau_signale_et_interprete_utc():
    frame = measurements([{"timestamp": "2026-03-01 00:00:00"}])
    prepared, quarantine, _ = prepare_sensors(frame, PARK)
    rejets = quarantine_for(quarantine, "R-SEN-002")
    assert len(rejets) == 1
    assert rejets.iloc[0]["decision"] == "valeur_normalisee"
    assert prepared.iloc[0]["timestamp"] == pd.Timestamp("2026-03-01T00:00:00Z")


def test_r_sen_003_serie_hors_grille_signalee_une_seule_fois():
    """Le decalage porte sur la serie : une ligne de quarantaine, pas quatre."""
    frame = measurements(
        [{"timestamp": f"2026-03-0{d}T02:00:00Z"} for d in range(1, 5)]
    )
    prepared, quarantine, stats = prepare_sensors(frame, PARK)
    assert stats["lignes_hors_grille"] == 4
    assert len(quarantine_for(quarantine, "R-SEN-003")) == 1
    assert "4 mesures concernees" in quarantine_for(quarantine, "R-SEN-003").iloc[0]["reason"]
    assert len(prepared) == 4, "une serie decalee reste exploitable"


def test_r_sen_004_interruption_detectee_sur_la_trame_temporelle():
    """Un trou est signale une fois, a la reprise."""
    frame = measurements(
        [
            {"timestamp": "2026-03-01T00:00:00Z"},
            {"timestamp": "2026-03-01T06:00:00Z"},
            # 48 h sans mesure
            {"timestamp": "2026-03-03T06:00:00Z"},
        ]
    )
    _, quarantine, stats = prepare_sensors(frame, PARK)
    assert stats["reprises_apres_interruption"] == 1
    assert len(quarantine_for(quarantine, "R-SEN-004")) == 1


def test_r_sen_004_valeur_vide_ne_cree_pas_de_fausse_interruption():
    """Un releve sans valeur reste un releve : la trame temporelle est continue.

    Regression : mesurer la continuite apres avoir retire les lignes sans valeur
    fabriquait 57 fausses interruptions sur les 63 detectees.
    """
    frame = measurements(
        [
            {"timestamp": "2026-03-01T00:00:00Z", "value": "2.80"},
            {"timestamp": "2026-03-01T06:00:00Z", "value": ""},
            {"timestamp": "2026-03-01T12:00:00Z", "value": "2.90"},
        ]
    )
    _, _, stats = prepare_sensors(frame, PARK)
    assert stats["reprises_apres_interruption"] == 0


def test_r_sen_014_mesure_hors_periode_conservee_et_signalee():
    frame = measurements([{"timestamp": "2025-12-28T06:00:00Z"}])
    prepared, quarantine, _ = prepare_sensors(frame, PARK)
    rejets = quarantine_for(quarantine, "R-SEN-014")
    assert len(rejets) == 1
    assert rejets.iloc[0]["decision"] == "conserve_signale"
    assert len(prepared) == 1, "hors periode ne veut pas dire fausse"


def test_r_sen_010_capteur_fige_exclu():
    frame = measurements(
        [
            {"timestamp": f"2026-03-{d:02d}T00:00:00Z", "value": "2.59"}
            for d in range(1, 11)
        ]
    )
    prepared, quarantine, stats = prepare_sensors(frame, PARK)
    assert stats["lignes_figees_exclues"] == 10
    assert len(quarantine_for(quarantine, "R-SEN-010")) == 10
    assert prepared.empty


def test_une_serie_qui_varie_n_est_pas_declaree_figee():
    frame = measurements(
        [
            {"timestamp": f"2026-03-{d:02d}T00:00:00Z", "value": f"2.{50 + d}"}
            for d in range(1, 11)
        ]
    )
    _, quarantine, stats = prepare_sensors(frame, PARK)
    assert stats["lignes_figees_exclues"] == 0
    assert quarantine_for(quarantine, "R-SEN-010").empty


# --------------------------------------------------------------------------- #
# Comportements de serie : plage, derive, saut
# --------------------------------------------------------------------------- #

def _serie(values: list[str], sensor: str = "vibration_mm_s", unit: str = "mm/s") -> pd.DataFrame:
    """Serie reguliere au pas de 6 h, longue assez pour les detecteurs."""
    start = pd.Timestamp("2026-03-01T00:00:00Z")
    return measurements(
        [
            {
                "timestamp": (start + pd.Timedelta(hours=6 * i)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "value": value,
                "sensor_name": sensor,
                "unit": unit,
            }
            for i, value in enumerate(values)
        ]
    )


def test_r_sen_009_valeur_tres_ecartee_de_la_mediane_signalee():
    """Une valeur hors du corps de la distribution est signalee, pas supprimee."""
    valeurs = [f"2.{80 + (i % 7)}" for i in range(60)]
    valeurs[30] = "9.76"
    prepared, quarantine, stats = prepare_sensors(_serie(valeurs), PARK)
    rejets = quarantine_for(quarantine, "R-SEN-009")
    assert stats["depassements_plage"] >= 1
    assert rejets.iloc[0]["decision"] == "conserve_signale"
    assert len(prepared) == 60, "une valeur atypique reste dans les mesures preparees"


def test_r_sen_009_une_serie_reguliere_ne_declenche_aucun_depassement():
    """Garde-fou contre un seuil tautologique.

    Un critere fonde sur un centile signalerait mecaniquement 1 % des lignes,
    meme ici ou aucune valeur ne sort du lot. Le critere robuste ne doit rien
    trouver.
    """
    valeurs = [f"2.{80 + (i % 7)}" for i in range(60)]
    _, _, stats = prepare_sensors(_serie(valeurs), PARK)
    assert stats["depassements_plage"] == 0


def test_r_sen_011_derive_monotone_signalee_une_fois_par_serie():
    valeurs = [f"{50 + i * 0.2:.2f}" for i in range(60)]
    prepared, quarantine, stats = prepare_sensors(
        _serie(valeurs, sensor="temperature_c", unit="°C"), PARK
    )
    assert stats["series_en_derive_signalees"] == 1
    rejets = quarantine_for(quarantine, "R-SEN-011")
    assert len(rejets) == 1, "une derive porte sur la serie, pas sur chaque mesure"
    assert "correlation" in rejets.iloc[0]["reason"]
    assert len(prepared) == 60, "une serie en derive reste exploitable"


def test_r_sen_011_serie_stable_non_declaree_en_derive():
    valeurs = [f"{57 + (i % 5) * 0.1:.2f}" for i in range(60)]
    _, _, stats = prepare_sensors(_serie(valeurs, sensor="temperature_c", unit="°C"), PARK)
    assert stats["series_en_derive_signalees"] == 0


def test_r_sen_012_saut_brutal_signale():
    valeurs = [f"2.{80 + (i % 5)}" for i in range(40)]
    valeurs[20] = "25.00"
    _, quarantine, stats = prepare_sensors(_serie(valeurs), PARK)
    assert stats["sauts_signales"] >= 1
    assert quarantine_for(quarantine, "R-SEN-012").iloc[0]["decision"] == "conserve_signale"


def test_r_sen_012_serie_bruitee_sans_saut():
    valeurs = [f"2.{80 + (i % 9)}" for i in range(40)]
    _, _, stats = prepare_sensors(_serie(valeurs), PARK)
    assert stats["sauts_signales"] == 0


def test_les_sentinelles_ne_fabriquent_pas_de_faux_saut():
    """Regression : un `-999` non neutralise cree un saut geant artificiel."""
    valeurs = [f"2.{80 + (i % 5)}" for i in range(40)]
    valeurs[20] = "-999"
    _, _, stats = prepare_sensors(_serie(valeurs), PARK)
    assert stats["sentinelles_neutralisees"] == 1
    assert stats["sauts_signales"] == 0, "la sentinelle est neutralisee avant le controle"


# --------------------------------------------------------------------------- #
# Format de quarantaine
# --------------------------------------------------------------------------- #

def test_la_quarantaine_respecte_le_format_m2():
    frame = measurements([{"value": "-999"}, {"equipment_id": "EQ-ORPHAN-777"}])
    _, quarantine, _ = prepare_sensors(frame, PARK)
    assert list(quarantine.columns) == [
        "source_file",
        "row_identifier",
        "rule_id",
        "column",
        "observed_value",
        "reason",
        "decision",
    ]
    assert set(quarantine["source_file"]) == {"sensor_readings.csv"}


def test_toutes_les_decisions_appartiennent_au_vocabulaire_m2():
    from src.data_pipeline.quarantine import DECISIONS

    frame = measurements(
        [
            {"value": "-999"},
            {"value": ""},
            {"equipment_id": "EQ-ORPHAN-777"},
            {"sensor_name": "TEMPERATURE_C ", "unit": "°C", "value": "57.0"},
            {"period": "2026-S2"},
            {"timestamp": "2025-12-28T06:00:00Z"},
        ]
    )
    _, quarantine, _ = prepare_sensors(frame, PARK)
    assert set(quarantine["decision"]) <= DECISIONS


# --------------------------------------------------------------------------- #
# Registre
# --------------------------------------------------------------------------- #

def test_le_registre_couvre_les_dix_neuf_regles_m2():
    registry = build_registry()
    inherited = [rule for rule in registry.rules if rule.origin == "M2"]
    assert len(inherited) == 19
    assert all(
        rule.status in {"conservee", "modifiee", "etendue", "abandonnee"}
        for rule in inherited
    )


def test_le_registre_declare_quinze_regles_capteurs():
    registry = build_registry()
    added = [rule for rule in registry.rules if rule.origin == "M3"]
    assert len(added) == 15
    assert {rule.table for rule in added} == {"sensors"}


def test_un_identifiant_de_regle_en_double_est_refuse():
    registry = RuleRegistry()
    registry.add(Rule("R-SEN-001", "sensors", "nouvelle", "controle"))
    with pytest.raises(ValueError):
        registry.add(Rule("R-SEN-001", "sensors", "nouvelle", "doublon"))


def test_une_regle_abandonnee_exige_une_justification():
    with pytest.raises(ValueError):
        Rule("R-EQ-001", "equipment", "abandonnee", "controle", origin="M2")


# --------------------------------------------------------------------------- #
# Non-regression M2
# --------------------------------------------------------------------------- #

def test_non_regression_detecte_une_table_identique():
    table = pd.DataFrame({"equipment_id": ["EQ-1", "EQ-2"], "site_id": ["S1", "S2"]})
    tables = {"equipment": table, "events": table, "maintenance": table}
    report = check_no_regression(tables, {k: v.copy() for k, v in tables.items()})
    assert report["non_regression"] is True


def test_non_regression_echoue_si_une_ligne_disparait():
    table = pd.DataFrame({"equipment_id": ["EQ-1", "EQ-2"], "site_id": ["S1", "S2"]})
    tables = {"equipment": table, "events": table, "maintenance": table}
    produced = {k: v.copy() for k, v in tables.items()}
    produced["events"] = produced["events"].iloc[:1]
    report = check_no_regression(tables, produced)
    assert report["non_regression"] is False
    assert report["events"]["lignes_apres"] == 1


def test_non_regression_echoue_si_une_valeur_change():
    table = pd.DataFrame({"equipment_id": ["EQ-1", "EQ-2"], "site_id": ["S1", "S2"]})
    tables = {"equipment": table, "events": table, "maintenance": table}
    produced = {k: v.copy() for k, v in tables.items()}
    produced["equipment"].loc[0, "site_id"] = "S9"
    report = check_no_regression(tables, produced)
    assert report["non_regression"] is False
    assert report["equipment"]["lignes_apres"] == 2, "meme volume, contenu different"


def test_la_pipeline_ne_touche_pas_aux_mesures_recues():
    """Le fichier recu ne doit jamais etre modifie en place."""
    frame = measurements([{"sensor_name": "TEMPERATURE_C ", "unit": "K", "value": "330.15"}])
    original = frame.copy()
    prepare_sensors(frame, PARK)
    pd.testing.assert_frame_equal(frame, original)
