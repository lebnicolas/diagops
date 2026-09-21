#!/usr/bin/env python3
"""Comparaison des trois systèmes — étape 5 du brief 1.

Le brief impose de comparer l'agent « à une baseline sans agent et à la tranche
M4 à une étape ». Les trois sont rejoués ici sur les mêmes jeux, avec les huit
mesures demandées — dont la latence et le coût, que le harness ne décomposait pas.

Le coût se lit sur deux colonnes qu'on oublie souvent : le nombre d'appels
d'outils, et surtout **le nombre de lignes lues**. Un système qui répond aussi
bien en lisant deux fois moins de données n'est pas équivalent.

    python eval/compare_systems.py [--output results/comparaison.json]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.registry import default_registry
from agent.runner import BoundedAgent, load_policy
from eval.baseline_m4 import TrancheM4
from eval.run_agent_eval import baseline_without_agent, evaluate_scenario, load_scenarios

JEUX = {
    "jeu gelé v3 (29)": ROOT / "eval" / "scenarios_v3.jsonl",
    "jeu du starter (18)": ROOT / "eval" / "scenarios.jsonl",
    "campagne adversariale (6)": ROOT / "adversarial" / "campaign.jsonl",
}


def centile(valeurs: list[float], part: float) -> float:
    if not valeurs:
        return 0.0
    ordonnees = sorted(valeurs)
    rang = min(int(part * len(ordonnees)), len(ordonnees) - 1)
    return round(ordonnees[rang], 3)


def mesurer(agent: BoundedAgent, scenarios: list[dict]) -> dict:
    resultats = [evaluate_scenario(agent, scenario, {}) for scenario in scenarios]
    attentes = {"answer": [], "refuse": []}
    for ligne in resultats:
        attentes[ligne["expectation"]].append(ligne["success"])

    durees = [ligne["elapsed_ms"] for ligne in resultats]
    lignes_lues = sum(
        etape["row_count"] for ligne in resultats for etape in ligne["trace"]["steps"]
    )
    avec_arguments = [
        ligne["arguments_exact"] for ligne in resultats if ligne["arguments_exact"] is not None
    ]
    appels = sum(len(ligne["tools_used"]) for ligne in resultats)

    return {
        # --- les huit mesures exigées par le brief ---
        "reussite": round(sum(l["success"] for l in resultats) / len(resultats), 3),
        "choix_outil_exact": round(
            sum(l["tool_selection_exact"] for l in resultats if l["tools_expected"])
            / max(1, sum(1 for l in resultats if l["tools_expected"])), 3,
        ),
        "arguments_exacts": round(sum(avec_arguments) / len(avec_arguments), 3) if avec_arguments else None,
        "appels_inutiles": round(sum(l["useless_calls"] for l in resultats) / max(1, appels), 3),
        "preuves_completes": round(
            sum(l["evidence_complete"] for l in resultats if l["expectation"] == "answer")
            / max(1, sum(1 for l in resultats if l["expectation"] == "answer")), 3,
        ),
        "refus_corrects": sum(
            1 for l in resultats if l["expectation"] == "refuse" and l["refused"]
        ),
        "refus_incorrects": sum(
            1 for l in resultats if l["expectation"] == "answer" and l["refused"]
        ),
        "depassements_budget": sum(l["budget_overrun"] for l in resultats),
        # --- latence et coût, décomposés ---
        "latence_p50_ms": centile(durees, 0.5),
        "latence_p95_ms": centile(durees, 0.95),
        "latence_max_ms": round(max(durees), 3),
        "appels_outils": appels,
        "lignes_lues": lignes_lues,
        "etapes_moyennes": round(statistics.mean(l["steps"] for l in resultats), 2),
        # --- décomposition par attente : un refus systématique se verrait ici ---
        "reussite_sur_reponses": round(
            sum(attentes["answer"]) / len(attentes["answer"]), 3
        ) if attentes["answer"] else None,
        "reussite_sur_refus": round(
            sum(attentes["refuse"]) / len(attentes["refuse"]), 3
        ) if attentes["refuse"] else None,
        "echecs": [l["scenario_id"] for l in resultats if not l["success"]],
    }


def mesurer_sans_agent(scenarios: list[dict]) -> dict:
    """Une seule recherche documentaire, sans planification ni vérification."""
    resultats = [baseline_without_agent(scenario) for scenario in scenarios]
    return {
        "reussite": round(sum(l["success"] for l in resultats) / len(resultats), 3),
        "appels_outils": len(scenarios),
        "echecs": [l["scenario_id"] for l in resultats if not l["success"]],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "comparaison.json")
    args = parser.parse_args()

    registre = default_registry()
    politique = load_policy(ROOT / "agent" / "policy.yaml")
    systemes = {
        "tranche M4 (1 étape)": TrancheM4(registre, politique),
        "agent M6 (m6-r2)": BoundedAgent(registre, politique),
    }

    rapport: dict = {}
    for nom_jeu, chemin in JEUX.items():
        scenarios = load_scenarios(chemin)
        rapport[nom_jeu] = {"sans agent": mesurer_sans_agent(scenarios)}
        for nom, agent in systemes.items():
            rapport[nom_jeu][nom] = mesurer(agent, scenarios)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8", newline="",
    )

    colonnes = ("reussite", "reussite_sur_reponses", "reussite_sur_refus",
                "choix_outil_exact", "appels_inutiles", "refus_incorrects",
                "latence_p95_ms", "appels_outils", "lignes_lues")
    for nom_jeu, mesures in rapport.items():
        print(f"\n{nom_jeu}")
        print(f"  {'':<24}" + "".join(f"{col[:13]:>15}" for col in colonnes))
        for nom, valeurs in mesures.items():
            cellules = "".join(
                f"{('—' if valeurs.get(col) is None else valeurs.get(col)):>15}"
                for col in colonnes
            )
            print(f"  {nom:<24}{cellules}")
    print(f"\nRapport complet : {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
