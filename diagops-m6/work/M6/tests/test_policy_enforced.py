"""Chaque valeur de la politique borne-t-elle réellement quelque chose ?

Le banc de sensibilité de l'étape 2 a montré que cinq paramètres étaient chargés
puis jamais appliqués : `max_result_rows`, `treat_tool_output_as_data`,
`record_fields`, `forbidden_fields` et `retention_days`. Les quatre premiers sont
désormais appliqués ; ces tests échouent si l'un d'eux redevient décoratif.

`retention_days` reste une dette assumée : rien ne purge les traces, et un agent
sans stockage ne peut pas le faire seul — c'est au pipeline qui écrit
`results/*.jsonl` de porter la purge.
"""

from __future__ import annotations

import dataclasses

import pytest
import yaml

from agent.registry import default_registry
from agent.runner import AgentRun, BoundedAgent, Step, load_policy

POLICY_PATH = "agent/policy.yaml"
QUESTION_DOCUMENTAIRE = "Quelle procédure de consignation faut-il appliquer ?"


@pytest.fixture(scope="module")
def policy():
    return load_policy(POLICY_PATH)


def test_max_result_rows_coupe_le_resultat(policy):
    """La politique peut être plus restrictive que le contrat de l'outil."""
    large = BoundedAgent(default_registry(), policy)
    serree = BoundedAgent(
        default_registry(),
        dataclasses.replace(policy, budget=dataclasses.replace(policy.budget, max_result_rows=1)),
    )
    lignes_large = sum(step.row_count for step in large.run(QUESTION_DOCUMENTAIRE).steps)
    lignes_serree = sum(step.row_count for step in serree.run(QUESTION_DOCUMENTAIRE).steps)
    assert lignes_large > 1, "le cas de référence doit rendre plusieurs lignes"
    assert lignes_serree == 1


def test_trace_projetee_sur_les_champs_declares(policy):
    """La trace porte les champs du contrat, sous leur nom contractuel."""
    agent = BoundedAgent(default_registry(), policy)
    trace = agent.run("Quelle est la criticité de EQ-PUMP-001 ?").as_trace()
    etape = trace["steps"][0]
    assert set(etape) <= set(policy.trace_record_fields)
    assert "step" in etape and "index" not in etape
    assert etape["step"] == 1


def test_champ_trace_non_declare_absent_de_la_trace(policy):
    """Un champ retiré du contrat disparaît de la trace, sans toucher au code."""
    ampute = dataclasses.replace(
        policy,
        trace_record_fields=tuple(
            champ for champ in policy.trace_record_fields if champ != "elapsed_ms"
        ),
    )
    agent = BoundedAgent(default_registry(), ampute)
    trace = agent.run("Quelle est la criticité de EQ-PUMP-001 ?").as_trace()
    assert "elapsed_ms" not in trace["steps"][0]


def test_champ_interdit_dans_la_trace_leve(policy):
    """Le garde-fou est actif, pas déclaratif : une trace fautive ne sort pas."""
    run = AgentRun(
        question="", role=policy.role, policy_id=policy.policy_id,
        trace_fields=("step", "tool", "source"),
        trace_forbidden_fields=("source",),
    )
    run.steps.append(Step(
        index=1, tool="get_equipment", argument_keys=("equipment_id",),
        argument_fingerprint="0" * 12, row_count=1, source="equipment.csv",
        elapsed_ms=0.0, outcome="ok",
    ))
    with pytest.raises(ValueError, match="champs interdits"):
        run.as_trace()


def test_politique_traitant_un_resultat_comme_instruction_refusee(tmp_path):
    """`treat_tool_output_as_data: false` ne se charge pas : INV-08 en dépend."""
    raw = yaml.safe_load(open(POLICY_PATH, encoding="utf-8"))
    raw["execution"]["treat_tool_output_as_data"] = False
    chemin = tmp_path / "policy.yaml"
    chemin.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
    with pytest.raises(ValueError, match="donnée"):
        load_policy(chemin)


def test_marqueur_d_instruction_declare_au_contrat(policy):
    """Ce qui est tracé est déclaré : l'inverse laissait INV-08 hors contrat."""
    assert "instruction_like_content" in policy.trace_record_fields
