"""Verifications de la qualification.

Chaque test repond a une exigence du brief, dans l'ordre ou elles y figurent :
une rupture de schema, une relation absente et une regle bloquante sont
detectees ; un avertissement ne se comporte pas comme une erreur ; deux
executions sur les memes entrees et les memes regles donnent la meme decision.

Les lots sont fabriques en memoire. Un test qui dependrait du contenu exact du
data pack ne prouverait pas que le controle fonctionne, seulement qu'il a
trouve ce qu'on savait deja y etre.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from qualification.batch import Batch, build_context
from qualification.policy import (
    STATUS_ACCEPTED,
    STATUS_ACCEPTED_WITH_WARNINGS,
    STATUS_REJECTED,
    PolicyError,
    conforms,
    load_policy,
)
from qualification.qualify import qualify


POLICY_PATH = Path(__file__).resolve().parents[1] / "config" / "quality_rules.yaml"
REFERENCE_DATE = pd.Timestamp("2026-08-04")

# Les lots de test sont volontairement larges. Ecrits d'abord a trois lignes,
# ils faisaient echouer deux tests pour une raison qui n'avait rien a voir avec
# ce qu'ils verifiaient : une anomalie unique pesait 33 % et franchissait tous
# les plafonds de la politique. C'est exactement le biais de taille de lot
# releve dans le code M2 — il revient ici, sur les donnees de test cette fois.
# Un lot de soixante lignes laisse une anomalie isolee peser 1,7 %, sous tous
# les seuils, et l'escalade redevient une chose qu'on declenche exprès.
BASELINE_ROWS = 80
CANDIDATE_ROWS = 60


# ----------------------------------------------------------------------
# Fabriques
# ----------------------------------------------------------------------


def equipment_rows(count: int = 3, start: int = 1) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "equipment_id": [f"EQ-T-{index:03d}" for index in range(start, start + count)],
            "equipment_type": ["pump"] * count,
            "site_id": ["SITE-A"] * count,
            "commissioning_date": ["2020-01-15"] * count,
            "criticality": ["high"] * count,
            "manufacturer": ["ACME"] * count,
            "rated_power_kw": [110.0] * count,
        }
    )


def event_rows(equipment: pd.DataFrame, prefix: str = "EVT-T") -> pd.DataFrame:
    ids = equipment["equipment_id"].tolist()
    return pd.DataFrame(
        {
            "event_id": [f"{prefix}-{index:03d}" for index in range(1, len(ids) + 1)],
            "equipment_id": ids,
            "start_at": ["2026-03-01T08:00:00Z"] * len(ids),
            "end_at": ["2026-03-01T10:00:00Z"] * len(ids),
            "event_type": ["incident"] * len(ids),
            "severity": ["medium"] * len(ids),
            "period": ["2026-S1"] * len(ids),
        }
    )


def maintenance_rows(events: pd.DataFrame, prefix: str = "MNT-T") -> pd.DataFrame:
    count = len(events)
    return pd.DataFrame(
        {
            "maintenance_id": [f"{prefix}-{index:03d}" for index in range(1, count + 1)],
            "event_id": events["event_id"].tolist(),
            "equipment_id": events["equipment_id"].tolist(),
            "opened_at": ["2026-03-01T09:00:00Z"] * count,
            "closed_at": ["2026-03-01T11:00:00Z"] * count,
            "intervention_type": ["corrective"] * count,
            "outcome": ["resolved"] * count,
            "downtime_minutes": [60] * count,
            "labor_hours": [2.0] * count,
            "parts_cost_eur": [0.0] * count,
            "parts_replaced_count": [0] * count,
            "work_order_note": ["remplacement joint"] * count,
            "period": ["2026-S1"] * count,
        }
    )


def make_batch(frames: dict[str, pd.DataFrame], batch_id: str = "lot-test", **extra) -> Batch:
    return Batch(
        batch_id=batch_id,
        label=batch_id,
        root=Path("."),
        paths={},
        frames=frames,
        checksums={},
        announced_rows=extra.get("announced_rows", {}),
        announced_columns=extra.get("announced_columns", {}),
        update_by_key=extra.get("update_by_key", {}),
    )


def clean_baseline() -> Batch:
    equipment = equipment_rows(BASELINE_ROWS)
    events = event_rows(equipment)
    return make_batch(
        {"equipment": equipment, "events": events, "maintenance": maintenance_rows(events)},
        batch_id="baseline-test",
    )


def clean_candidate(**extra) -> Batch:
    equipment = equipment_rows(CANDIDATE_ROWS, start=1000)
    events = event_rows(equipment, prefix="EVT-C")
    return make_batch(
        {
            "equipment": equipment,
            "events": events,
            "maintenance": maintenance_rows(events, prefix="MNT-C"),
        },
        batch_id="candidat-test",
        **extra,
    )


def rename_equipment(batch: Batch, position: int, new_id: str) -> None:
    """Renomme un equipement dans les trois tables du lot.

    Changer l'identifiant dans la seule table `equipment` laisserait les
    evenements et les interventions pointer vers une machine disparue : le test
    echouerait sur une reference orpheline, pas sur ce qu'il verifie.
    """
    old_id = batch.frames["equipment"].loc[position, "equipment_id"]
    batch.frames["equipment"].loc[position, "equipment_id"] = new_id
    for source in ("events", "maintenance"):
        frame = batch.frames[source]
        frame.loc[frame["equipment_id"] == old_id, "equipment_id"] = new_id


@pytest.fixture(scope="module")
def policy():
    return load_policy(POLICY_PATH)


def run(candidate: Batch, baseline: Batch, policy):
    return qualify(candidate, baseline, policy, REFERENCE_DATE)


# ----------------------------------------------------------------------
# Point de depart : un lot propre passe
# ----------------------------------------------------------------------


def test_un_lot_propre_est_accepte(policy):
    """Sans ce test, tous les autres pourraient passer pour de mauvaises raisons.

    Un controle qui rejette tout detecte aussi toutes les anomalies.
    """
    result = run(clean_candidate(), clean_baseline(), policy)
    assert result.status == STATUS_ACCEPTED, result.findings.to_string()


# ----------------------------------------------------------------------
# Exigence : une rupture de schema est detectee
# ----------------------------------------------------------------------


def test_colonne_manquante_est_bloquante(policy):
    candidate = clean_candidate()
    candidate.frames["events"] = candidate.frames["events"].drop(columns=["severity"])
    result = run(candidate, clean_baseline(), policy)

    assert result.status == STATUS_REJECTED
    assert "EVT-SCH-001" in set(result.blocking()["rule_id"])


def test_colonne_supplementaire_non_annoncee_avertit(policy):
    candidate = clean_candidate()
    candidate.frames["maintenance"]["source_system"] = "GMAO-X"
    result = run(candidate, clean_baseline(), policy)

    assert result.status == STATUS_ACCEPTED_WITH_WARNINGS
    assert "INC-SCH-002" in set(result.warnings()["rule_id"])


def test_colonne_supplementaire_annoncee_ne_bloque_pas(policy):
    """Meme colonne que le test precedent, mais declaree dans les notes."""
    candidate = clean_candidate(announced_columns={"maintenance": ["source_system"]})
    candidate.frames["maintenance"]["source_system"] = "GMAO-X"
    result = run(candidate, clean_baseline(), policy)

    assert result.status == STATUS_ACCEPTED
    assert "INC-SCH-002" not in set(result.findings["rule_id"])


# ----------------------------------------------------------------------
# Exigence : une relation absente est detectee
# ----------------------------------------------------------------------


def test_reference_orpheline_isolee_avertit(policy):
    candidate = clean_candidate()
    candidate.frames["events"].loc[0, "equipment_id"] = "EQ-INCONNU-999"
    result = run(candidate, clean_baseline(), policy)

    assert result.status == STATUS_ACCEPTED_WITH_WARNINGS
    assert "EVT-REF-002" in set(result.warnings()["rule_id"])


def test_references_orphelines_massives_bloquent(policy):
    """Le meme controle, a une autre echelle, ne dit plus la meme chose.

    Une ligne orpheline est une ligne fausse. Toutes les lignes orphelines,
    c'est un lot construit sur un autre referentiel.
    """
    candidate = clean_candidate()
    candidate.frames["events"]["equipment_id"] = "EQ-INCONNU-999"
    result = run(candidate, clean_baseline(), policy)

    assert result.status == STATUS_REJECTED
    blocking = result.blocking()
    assert "EVT-REF-002" in set(blocking["rule_id"])
    assert bool(blocking.loc[blocking["rule_id"] == "EVT-REF-002", "escalated"].iloc[0])


def test_reference_resolue_dans_le_contexte_et_non_dans_le_lot(policy):
    """Un evenement candidat peut porter sur une machine deja au catalogue.

    C'est le piege central du passage a l'incremental : sans le contexte, ces
    references seraient toutes declarees orphelines.
    """
    baseline = clean_baseline()
    candidate = clean_candidate()
    candidate.frames["equipment"] = candidate.frames["equipment"].iloc[0:0]
    candidate.frames["events"]["equipment_id"] = baseline.frames["equipment"]["equipment_id"].iloc[0]
    candidate.frames["maintenance"]["equipment_id"] = (
        baseline.frames["equipment"]["equipment_id"].iloc[0]
    )
    result = run(candidate, baseline, policy)

    assert "EVT-REF-002" not in set(result.findings["rule_id"])
    assert "MNT-REF-002" not in set(result.findings["rule_id"])


# ----------------------------------------------------------------------
# Exigence : une regle bloquante est detectee
# ----------------------------------------------------------------------


def test_identifiant_absent_est_bloquant(policy):
    candidate = clean_candidate()
    candidate.frames["equipment"].loc[0, "equipment_id"] = None
    result = run(candidate, clean_baseline(), policy)

    assert result.status == STATUS_REJECTED
    assert "EQP-KEY-001" in set(result.blocking()["rule_id"])


def test_collision_de_cle_avec_l_historique_est_bloquante(policy):
    """Les notes de livraison annoncent des ajouts, sans collision attendue."""
    baseline = clean_baseline()
    candidate = clean_candidate()
    candidate.frames["events"].loc[0, "event_id"] = baseline.frames["events"]["event_id"].iloc[0]
    result = run(candidate, baseline, policy)

    assert result.status == STATUS_REJECTED
    assert "INC-KEY-003" in set(result.blocking()["rule_id"])


def test_recouvrement_de_cle_declare_comme_mise_a_jour_ne_bloque_pas(policy):
    """Meme situation que le test precedent, sur une table declaree en mise a jour.

    La cle qui revient n'est alors plus une collision : c'est l'operation
    annoncee. Ce couple de tests fixe la distinction que M2 ne faisait pas.
    """
    baseline = clean_baseline()
    candidate = clean_candidate(update_by_key={"equipment": "equipment_id"})
    rename_equipment(candidate, 0, baseline.frames["equipment"]["equipment_id"].iloc[0])
    result = run(candidate, baseline, policy)

    assert result.status == STATUS_ACCEPTED
    assert "INC-KEY-002" in set(result.findings["rule_id"])
    assert result.findings.loc[result.findings["rule_id"] == "INC-KEY-002", "level"].iloc[0] == "info"


# ----------------------------------------------------------------------
# Exigence : un avertissement ne se comporte pas comme une erreur
# ----------------------------------------------------------------------


def test_avertissement_et_erreur_ne_produisent_pas_le_meme_statut(policy):
    warned = clean_candidate()
    warned.frames["maintenance"].loc[0, "work_order_note"] = "appeler jean.dupont@example.com"

    failed = clean_candidate()
    failed.frames["equipment"].loc[0, "equipment_id"] = None

    baseline = clean_baseline()
    assert run(warned, baseline, policy).status == STATUS_ACCEPTED_WITH_WARNINGS
    assert run(failed, baseline, policy).status == STATUS_REJECTED


def test_un_avertissement_seul_ne_produit_aucune_erreur(policy):
    candidate = clean_candidate(announced_rows={"equipment": 999})
    result = run(candidate, clean_baseline(), policy)

    assert result.counts["error"] == 0
    assert "INC-VOL-001" in set(result.warnings()["rule_id"])


# ----------------------------------------------------------------------
# Exigence : reproductibilite
# ----------------------------------------------------------------------


def test_deux_executions_donnent_la_meme_decision(policy):
    baseline, candidate = clean_baseline(), clean_candidate()
    first = run(candidate, baseline, policy)
    second = run(candidate, baseline, policy)

    assert first.status == second.status
    assert first.counts == second.counts
    pd.testing.assert_frame_equal(first.findings, second.findings)


def test_la_qualification_ne_modifie_pas_les_donnees_recues(policy):
    baseline, candidate = clean_baseline(), clean_candidate()
    before = {name: frame.copy(deep=True) for name, frame in candidate.frames.items()}
    run(candidate, baseline, policy)

    for name, frame in candidate.frames.items():
        pd.testing.assert_frame_equal(frame, before[name])


def test_le_contexte_ne_retourne_jamais_dans_les_lots(policy):
    """Le contexte est un artefact de calcul, pas une integration."""
    baseline, candidate = clean_baseline(), clean_candidate()
    context = build_context(baseline, candidate)
    context["equipment"].loc[0, "site_id"] = "MODIFIE-EN-MEMOIRE"

    assert "MODIFIE-EN-MEMOIRE" not in set(baseline.frames["equipment"]["site_id"])
    assert "MODIFIE-EN-MEMOIRE" not in set(candidate.frames["equipment"]["site_id"])


# ----------------------------------------------------------------------
# La politique elle-meme
# ----------------------------------------------------------------------


def test_la_politique_porte_une_version(policy):
    assert policy.version
    assert policy.checksum


def test_une_politique_sans_version_est_refusee(tmp_path):
    path = tmp_path / "sans_version.yaml"
    path.write_text("decision_levels:\n  signalement: info\n", encoding="utf-8")
    with pytest.raises(PolicyError, match="policy_version"):
        load_policy(path)


def test_un_niveau_inconnu_est_refuse(tmp_path):
    path = tmp_path / "niveau_faux.yaml"
    path.write_text(
        'policy_version: "0.1"\ndecision_levels:\n  signalement: critique\n', encoding="utf-8"
    )
    with pytest.raises(PolicyError, match="Niveau invalide"):
        load_policy(path)


# ----------------------------------------------------------------------
# Conformite d'un lot a la decision deja prise sur lui
# ----------------------------------------------------------------------


def test_une_livraison_neuve_rejetee_fait_echouer_la_chaine():
    ok, explanation = conforms(STATUS_REJECTED, None)
    assert not ok
    assert "neuve" in explanation


@pytest.mark.parametrize("status", [STATUS_ACCEPTED, STATUS_ACCEPTED_WITH_WARNINGS])
def test_une_livraison_neuve_qui_passe_est_conforme(status):
    ok, _ = conforms(status, None)
    assert ok


def test_un_rejet_acte_et_declare_ne_fait_plus_echouer_la_chaine():
    ok, explanation = conforms(STATUS_REJECTED, STATUS_REJECTED)
    assert ok
    assert "decision actee" in explanation


def test_un_lot_qui_cesse_d_etre_rejete_fait_echouer_la_chaine():
    """La verification est symetrique, et c'est le point.

    Un lot qui redevient acceptable sans que personne ne l'ait decide est
    aussi anormal qu'un lot qui se met a echouer : dans les deux cas la
    decision inscrite ne correspond plus a ce que les donnees disent.
    """
    ok, explanation = conforms(STATUS_ACCEPTED, STATUS_REJECTED)
    assert not ok
    assert "a change" in explanation


def test_un_statut_attendu_invalide_est_refuse():
    with pytest.raises(PolicyError, match="expected_status invalide"):
        conforms(STATUS_ACCEPTED, "PEUT-ETRE")


def test_la_politique_reste_applicable_au_socle_publie(policy):
    """Exigence du brief : le lot historique est controle par la meme politique.

    Une politique qui rejette ce qui a deja ete accepte ne sert a rien pour
    juger une livraison. Ce test a echoue a la premiere ecriture — voir la note
    sur EQP-KEY-002 dans quality_rules.yaml.
    """
    baseline = clean_baseline()
    result = qualify(baseline, baseline, policy, REFERENCE_DATE, is_baseline=True)
    assert result.status != STATUS_REJECTED
