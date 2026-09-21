#!/usr/bin/env python3
"""Banc de sensibilité de la politique d'exécution — étape 2 du brief 1.

Le brief demande une politique « défendue valeur par valeur ». Défendre une
valeur, ce n'est pas écrire pourquoi elle paraît raisonnable : c'est montrer ce
qui change quand on la déplace. Ce banc rejoue le jeu gelé sous des politiques
dérivées, une valeur modifiée à la fois, et mesure l'effet.

Il mesure aussi ce que les bornes dures refusent, ce que les traces contiennent
réellement, et ce que coûte chaque autorisation de la liste blanche.

    python eval/probe_policy.py [--output results/sensibilite_politique.json]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.registry import default_registry
from agent.runner import BoundedAgent, load_policy
from eval.run_agent_eval import baseline_without_agent, evaluate_scenario, load_scenarios, summarize

SCENARIOS = ROOT / "eval" / "scenarios_v3.jsonl"
POLICY = ROOT / "agent" / "policy.yaml"


def mesure(policy, scenarios: list[dict]) -> dict:
    """Rejoue le jeu gelé sous une politique donnée."""
    agent = BoundedAgent(default_registry(), policy)
    results = [evaluate_scenario(agent, scenario, {}) for scenario in scenarios]
    baseline = [baseline_without_agent(scenario) for scenario in scenarios]
    resume = summarize(results, baseline)
    return {
        "reussite": resume["scenario_success_rate"],
        "choix_outil": resume["tool_selection_exact_rate"],
        "refus_corrects": resume["correct_refusals"],
        "refus_incorrects": resume["incorrect_refusals"],
        "depassements_budget": resume["budget_overruns"],
        # Ce que l'agent a effectivement lu : une politique se juge aussi à la
        # donnée qu'elle expose, pas seulement au score qu'elle obtient.
        "lignes_rendues": sum(
            etape["row_count"] for row in results for etape in row["trace"]["steps"]
        ),
        "echecs": [row["scenario_id"] for row in results if not row["success"]],
    }


def plancher_du_jeu(scenarios: list[dict]) -> dict:
    """Combien d'outils le jeu gelé exige-t-il, au maximum et en moyenne ?"""
    attendus = {
        scenario["scenario_id"]: len(scenario["expected_tools"])
        for scenario in scenarios
    }
    repartition: dict[int, int] = {}
    for compte in attendus.values():
        repartition[compte] = repartition.get(compte, 0) + 1
    maximum = max(attendus.values())
    return {
        "repartition": dict(sorted(repartition.items())),
        "maximum": maximum,
        "scenarios_au_maximum": sorted(
            identifiant for identifiant, compte in attendus.items() if compte == maximum
        ),
        "plancher_max_steps": maximum + 1,
    }


def sensibilite_etapes(base, scenarios: list[dict]) -> dict:
    return {
        str(valeur): mesure(
            replace(base, budget=replace(base.budget, max_steps=valeur, max_tool_calls=valeur)),
            scenarios,
        )
        for valeur in (1, 2, 3, 4, 8)
    }


def sensibilite_lignes(base, scenarios: list[dict]) -> dict:
    return {
        str(valeur): mesure(
            replace(base, budget=replace(base.budget, max_result_rows=valeur)), scenarios,
        )
        for valeur in (1, 3, 5, 10)
    }


def sensibilite_drapeaux(base, scenarios: list[dict]) -> dict:
    return {
        "require_evidence=False": mesure(replace(base, require_evidence=False), scenarios),
        "stop_on_tool_error=False": mesure(replace(base, stop_on_tool_error=False), scenarios),
    }


def cout_de_chaque_autorisation(base, scenarios: list[dict]) -> dict:
    """Ce que coûte le retrait d'un outil de la liste blanche."""
    mesures = {}
    for outil in sorted(base.allowlist):
        reduite = frozenset(base.allowlist - {outil})
        mesures[f"sans {outil}"] = mesure(replace(base, allowlist=reduite), scenarios)
    return mesures


POLITIQUES_REFUSEES = {
    "max_steps au-dela de la borne dure (8)": {"budget": {"max_steps": 9}},
    "max_duration_ms au-dela de la borne dure (30000)": {"budget": {"max_duration_ms": 40000}},
    "ajout dynamique d'outils": {"execution": {"allow_dynamic_tools": True}},
    "liste blanche vide": {"allowlist": []},
}


def bornes_dures() -> dict:
    """Ce qu'une politique ne peut pas se donner, même en editant le YAML."""
    import yaml

    brut = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    constats = {}
    for libelle, patch in POLITIQUES_REFUSEES.items():
        candidat = json.loads(json.dumps(brut))
        for section, valeurs in patch.items():
            if isinstance(valeurs, dict):
                candidat[section].update(valeurs)
            else:
                candidat[section] = valeurs
        with tempfile.NamedTemporaryFile(
            "w", suffix=".yaml", delete=False, encoding="utf-8", newline="",
        ) as fichier:
            yaml.safe_dump(candidat, fichier, allow_unicode=True)
            chemin = Path(fichier.name)
        try:
            load_policy(chemin)
            constats[libelle] = "ACCEPTEE"
        except ValueError as exc:
            constats[libelle] = f"refusee — {exc}"
        finally:
            chemin.unlink(missing_ok=True)
    return constats


def repetition_est_par_empreinte(base) -> dict:
    """`max_repeated_calls` compte-t-il l'outil, ou l'outil et ses arguments ?"""
    from agent.runner import _fingerprint

    meme = _fingerprint({"tool": "list_events", "equipment_id": "EQ-PUMP-001", "limit": 5})
    autre = _fingerprint({"tool": "list_events", "equipment_id": "EQ-PUMP-002", "limit": 5})
    return {
        "empreinte_appel_identique": meme,
        "empreinte_argument_different": autre,
        "portee": "outil + arguments" if meme != autre else "outil seul",
        "consequence": (
            "deux appels du meme outil sur des arguments differents ne comptent pas "
            "comme une repetition"
            if meme != autre else
            "tout second appel du meme outil est compte comme une repetition"
        ),
    }


def contenu_des_traces(base, scenarios: list[dict]) -> dict:
    """Ce que les traces contiennent réellement, comparé à ce qu'elles déclarent."""
    agent = BoundedAgent(default_registry(), base)
    etapes = []
    durees = []
    for scenario in scenarios:
        resultat = evaluate_scenario(agent, scenario, {})
        trace = resultat["trace"]
        durees.append(trace["elapsed_ms"])
        etapes.extend(trace["steps"])
    champs_vus = sorted({cle for etape in etapes for cle in etape})
    serialise = json.dumps(etapes, ensure_ascii=False)
    return {
        "etapes_tracees": len(etapes),
        "champs_declares": list(base.trace_record_fields),
        "champs_observes": champs_vus,
        "champs_declares_absents": sorted(set(base.trace_record_fields) - set(champs_vus)),
        "champs_observes_non_declares": sorted(set(champs_vus) - set(base.trace_record_fields)),
        "champs_interdits_presents": [
            champ for champ in base.trace_forbidden_fields if champ in serialise
        ],
        "longueur_empreinte": len({
            len(etape["argument_fingerprint"]) for etape in etapes if etape["argument_fingerprint"]
        } or {0}),
        "empreinte_exemple": next(
            (etape["argument_fingerprint"] for etape in etapes if etape["argument_fingerprint"]), "",
        ),
        "duree_par_scenario_ms": {
            "mediane": round(statistics.median(durees), 3),
            "maximum": round(max(durees), 3),
            "total": round(sum(durees), 3),
        },
        "budget_duree_ms": base.budget.max_duration_ms,
        "marge_sur_le_pire": round(base.budget.max_duration_ms / max(durees), 1),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "results" / "sensibilite_politique.json")
    args = parser.parse_args()

    scenarios = load_scenarios(SCENARIOS)
    base = load_policy(POLICY)

    rapport = {
        "politique": base.policy_id,
        "reference": mesure(base, scenarios),
        "plancher_du_jeu": plancher_du_jeu(scenarios),
        "sensibilite_max_steps": sensibilite_etapes(base, scenarios),
        "sensibilite_max_result_rows": sensibilite_lignes(base, scenarios),
        "sensibilite_drapeaux": sensibilite_drapeaux(base, scenarios),
        "sensibilite_max_repeated_calls": {
            str(valeur): mesure(
                replace(base, budget=replace(base.budget, max_repeated_calls=valeur)), scenarios,
            )
            for valeur in (1, 2)
        },
        "sensibilite_max_tool_calls": {
            str(valeur): mesure(
                replace(base, budget=replace(base.budget, max_tool_calls=valeur)), scenarios,
            )
            for valeur in (1, 2, 3, 4)
        },
        "cout_des_autorisations": cout_de_chaque_autorisation(base, scenarios),
        "bornes_dures": bornes_dures(),
        "portee_de_la_repetition": repetition_est_par_empreinte(base),
        "traces": contenu_des_traces(base, scenarios),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8", newline="",
    )

    def ligne(libelle: str, valeurs: dict) -> None:
        print(f"  {libelle:<34} reussite {valeurs['reussite']:<6} "
              f"refus incorrects {valeurs['refus_incorrects']:<3} "
              f"depassements {valeurs['depassements_budget']}")

    print("REFERENCE")
    ligne(base.policy_id, rapport["reference"])
    print("\nmax_steps (et max_tool_calls)")
    for valeur, valeurs in rapport["sensibilite_max_steps"].items():
        ligne(f"max_steps = {valeur}", valeurs)
    print("\nmax_result_rows")
    for valeur, valeurs in rapport["sensibilite_max_result_rows"].items():
        ligne(f"max_result_rows = {valeur}", valeurs)
    print("\ndrapeaux d'execution")
    for libelle, valeurs in rapport["sensibilite_drapeaux"].items():
        ligne(libelle, valeurs)
    print("\nliste blanche — cout du retrait")
    for libelle, valeurs in rapport["cout_des_autorisations"].items():
        ligne(libelle, valeurs)
    print("\nbornes dures")
    for libelle, constat in rapport["bornes_dures"].items():
        print(f"  {libelle:<48} {constat}")
    print(f"\nRapport complet : {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
