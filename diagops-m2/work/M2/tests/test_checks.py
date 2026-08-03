"""Cas valides et invalides pour chaque controle generique.

Chaque test construit un jeu minimal ou l'on sait a l'avance quelles lignes
doivent echouer. Un controle qui ne signale rien sur un cas valide est aussi
important qu'un controle qui detecte l'anomalie : c'est ce qui garantit
l'absence de faux positif en masse.
"""

from __future__ import annotations

import pandas as pd

from src.data_pipeline import checks


# ----------------------------------------------------------------------
# Structure et types
# ----------------------------------------------------------------------


def test_missing_columns_detecte_les_absences():
    frame = pd.DataFrame({"a": [1], "b": [2]})
    assert checks.missing_columns(frame, ["a", "b"]) == []
    assert checks.missing_columns(frame, ["a", "c", "b"]) == ["c"]


def test_not_convertible_number_ignore_les_valeurs_absentes():
    frame = pd.DataFrame({"puissance": ["12.5", None, "abc", "", "0"]})
    mask = checks.not_convertible(frame, "puissance", "number")
    assert mask.tolist() == [False, False, True, False, False]


def test_not_convertible_integer_refuse_un_decimal():
    frame = pd.DataFrame({"pieces": ["3", "2.5", None]})
    mask = checks.not_convertible(frame, "pieces", "integer")
    assert mask.tolist() == [False, True, False]


def test_not_convertible_iso_datetime_refuse_un_format_local():
    frame = pd.DataFrame({"start_at": ["2026-03-01T08:00:00", "01/03/2026 08:00", None]})
    mask = checks.not_convertible(frame, "start_at", "iso_datetime")
    assert mask.tolist() == [False, True, False]


def test_colonne_absente_ne_produit_aucun_echec():
    frame = pd.DataFrame({"a": [1, 2]})
    assert checks.not_convertible(frame, "inexistante", "number").sum() == 0
    assert checks.is_null(frame, "inexistante").sum() == 0
    assert checks.duplicated_key(frame, "inexistante").sum() == 0


# ----------------------------------------------------------------------
# Identifiants
# ----------------------------------------------------------------------


def test_is_null_compte_la_chaine_vide():
    frame = pd.DataFrame({"id": ["EQ-1", None, "   ", "EQ-2"]})
    assert checks.is_null(frame, "id").tolist() == [False, True, True, False]


def test_duplicated_key_marque_les_deux_exemplaires():
    frame = pd.DataFrame({"id": ["EQ-1", "EQ-2", "EQ-1", "EQ-3"]})
    assert checks.duplicated_key(frame, "id").tolist() == [True, False, True, False]


def test_duplicated_key_ignore_les_valeurs_absentes():
    frame = pd.DataFrame({"id": [None, None, "EQ-1"]})
    assert checks.duplicated_key(frame, "id").sum() == 0


def test_duplicated_rows_ne_marque_que_les_copies():
    frame = pd.DataFrame({"a": [1, 1, 2], "b": ["x", "x", "y"]})
    assert checks.duplicated_rows(frame).tolist() == [False, True, False]


# ----------------------------------------------------------------------
# Categories
# ----------------------------------------------------------------------


def test_not_in_set_respecte_l_enumeration():
    frame = pd.DataFrame({"severity": ["low", "urgent", None, "critical"]})
    mask = checks.not_in_set(frame, "severity", ("low", "medium", "high", "critical"))
    assert mask.tolist() == [False, True, False, False]


def test_category_inventory_trie_du_plus_rare_au_plus_frequent():
    frame = pd.DataFrame({"site": ["A", "A", "A", "B"]})
    inventory = checks.category_inventory(frame, "site")
    assert inventory["value"].tolist() == ["B", "A"]
    assert inventory["count"].tolist() == [1, 3]
    assert inventory["share"].tolist() == [0.25, 0.75]


def test_near_duplicate_labels_reunit_les_variantes_de_casse():
    frame = pd.DataFrame({"type": ["pompe", "Pompe", "moteur", "pompe "]})
    variants = checks.near_duplicate_labels(frame, "type")
    assert variants == [("Pompe", "pompe", "pompe ")]


# ----------------------------------------------------------------------
# References
# ----------------------------------------------------------------------


def test_unresolved_reference_detecte_l_orphelin():
    frame = pd.DataFrame({"equipment_id": ["EQ-1", "EQ-9", None]})
    mask = checks.unresolved_reference(frame, "equipment_id", ["EQ-1", "EQ-2"])
    assert mask.tolist() == [False, True, False]


def test_inconsistent_join_detecte_la_contradiction():
    maintenance = pd.DataFrame(
        {"event_id": ["EV-1", "EV-2", "EV-9"], "equipment_id": ["EQ-1", "EQ-7", "EQ-1"]}
    )
    events = pd.DataFrame(
        {"event_id": ["EV-1", "EV-2"], "equipment_id": ["EQ-1", "EQ-2"]}
    )
    mask = checks.inconsistent_join(
        maintenance, "equipment_id", events, "event_id", "equipment_id"
    )
    # EV-2 contredit ; EV-9 n'est pas joignable, ce n'est pas cette regle qui le voit
    assert mask.tolist() == [False, True, False]


# ----------------------------------------------------------------------
# Temporel
# ----------------------------------------------------------------------


def test_out_of_order_dates_ignore_les_lignes_incompletes():
    frame = pd.DataFrame(
        {
            "start_at": ["2026-03-01T08:00:00", "2026-03-02T08:00:00", "2026-03-03T08:00:00"],
            "end_at": ["2026-03-01T09:00:00", "2026-03-01T08:00:00", None],
        }
    )
    assert checks.out_of_order_dates(frame, "start_at", "end_at").tolist() == [
        False,
        True,
        False,
    ]


def test_date_out_of_bounds_encadre_des_deux_cotes():
    frame = pd.DataFrame({"d": ["1900-01-01", "2026-01-01", "2099-01-01"]})
    mask = checks.date_out_of_bounds(frame, "d", minimum="1950-01-01", maximum="2026-08-03")
    assert mask.tolist() == [True, False, True]


def test_date_gap_exceeded_compare_duree_declaree_et_ecart_reel():
    frame = pd.DataFrame(
        {
            "opened_at": ["2026-03-01T08:00:00", "2026-03-01T08:00:00"],
            "closed_at": ["2026-03-01T10:00:00", "2026-03-01T10:00:00"],
            "downtime_minutes": [90, 240],
        }
    )
    # 2 heures d'ecart : 90 min passe, 240 min est impossible
    assert checks.date_gap_exceeded(
        frame, "opened_at", "closed_at", "downtime_minutes"
    ).tolist() == [False, True]


# ----------------------------------------------------------------------
# Valeurs numeriques
# ----------------------------------------------------------------------


def test_numeric_out_of_bounds_gere_le_minimum_strict():
    frame = pd.DataFrame({"p": [0, 5, -3, None]})
    souple = checks.numeric_out_of_bounds(frame, "p", minimum=0)
    strict = checks.numeric_out_of_bounds(frame, "p", minimum=0, strict_minimum=True)
    assert souple.tolist() == [False, False, True, False]
    assert strict.tolist() == [True, False, True, False]


def test_numeric_out_of_bounds_ignore_le_non_convertible():
    frame = pd.DataFrame({"p": ["abc", "12"]})
    assert checks.numeric_out_of_bounds(frame, "p", minimum=0, maximum=100).sum() == 0


def test_inconsistent_pair_detecte_un_cout_sans_piece():
    frame = pd.DataFrame(
        {"parts_cost_eur": [120.0, 0.0, 90.0], "parts_replaced_count": [0, 0, 2]}
    )
    mask = checks.inconsistent_pair(frame, "parts_cost_eur", "parts_replaced_count")
    assert mask.tolist() == [True, False, False]


# ----------------------------------------------------------------------
# Manquants et donnees personnelles
# ----------------------------------------------------------------------


def test_missing_rate_compte_la_chaine_vide():
    frame = pd.DataFrame({"c": ["a", None, "", "d"]})
    assert checks.missing_rate(frame, "c") == 0.5


def test_contains_personal_data_detecte_email_telephone_et_civilite():
    frame = pd.DataFrame(
        {
            "note": [
                "Intervention standard sur EQ-PUMP-001",
                "Contacter jean.dupont@example.com pour la suite",
                "Rappeler le 06 12 34 56 78",
                "Valide par M. Martin",
                "Reference bon de travail 0612345678901234",
            ]
        }
    )
    mask = checks.contains_personal_data(frame, "note")
    assert mask.tolist()[:4] == [False, True, True, True]


def test_personal_data_kinds_nomme_les_motifs():
    frame = pd.DataFrame({"note": ["ecrire a a@b.fr", "rien a signaler"]})
    kinds = checks.personal_data_kinds(frame, "note")
    assert kinds.tolist() == ["email", ""]
