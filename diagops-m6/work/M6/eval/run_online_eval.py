#!/usr/bin/env python3
"""Évaluation du brief online — la version en service, contre le gate M5.

Le brief 1 présentiel a mesuré un candidat sur un jeu que j'ai écrit moi-même.
Celui-ci le confronte au **jeu de calibration du formateur** (12 questions,
`data_pack/2026-S1/rag_eval/`) et aux **gates gelés de la référence M5**
(`reference_runs/m5_for_m6/gates/gates.json`).

La référence n'est pas réimplémentée : la fonction de score d'origine est
importée du dossier de référence livré par le formateur. Comparer à une copie de
mémoire, c'est comparer à ce dont on se souvient.

Les 12 questions du split `test` restent scellées et ne sont pas lues.

    python eval/run_online_eval.py
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.registry import default_registry
from agent.runner import BoundedAgent, load_policy
from tools import data_pack, knowledge as knowledge_tool, knowledge_documents

REFERENCE = data_pack() / "2026-S1" / "reference_runs" / "m5_for_m6"
QUESTIONS = data_pack() / "2026-S1" / "rag_eval" / "questions.jsonl"
GATES = REFERENCE / "gates" / "gates.json"
METRIQUES_M5 = REFERENCE / "evaluation" / "metrics_calibration.json"


def score_de_reference():
    """La fonction de score livrée par le formateur, chargée telle quelle."""
    chemin = REFERENCE / "baseline" / "retrieval.py"
    spec = importlib.util.spec_from_file_location("baseline_retrieval", chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.lexical_score


def calibration() -> list[dict]:
    cas = [
        json.loads(ligne)
        for ligne in QUESTIONS.read_text(encoding="utf-8").splitlines()
        if ligne.strip()
    ]
    # Le split `test` est scellé : on ne le lit pas, on ne le compte pas.
    return [c for c in cas if c["split"] == "calibration"]


def mesurer(cas: list[dict], libelle: str) -> dict:
    agent = BoundedAgent(default_registry(), load_policy(ROOT / "agent" / "policy.yaml"))
    connus = {d["document_id"] for d in knowledge_documents()}
    lignes = []
    for item in cas:
        import dataclasses

        courant = agent
        if item["role"] != agent.policy.role:
            courant = BoundedAgent(
                agent.registry, dataclasses.replace(agent.policy, role=item["role"])
            )
        run = courant.run(item["question"])
        cites = [e["reference"] for e in run.evidence if e["type"] == "document"]
        attendus = set(item["expected_document_ids"])
        lignes.append({
            "eval_id": item["eval_id"],
            "answerable": item["answerable"],
            "risk_tags": item["risk_tags"] or ["aucun"],
            "role": item["role"],
            "cites": cites,
            "hit_at_3": bool(attendus) and bool(attendus & set(cites)),
            "resolvable": all(ref in connus for ref in cites),
            "abstention": run.refused,
            "documents_rendus": len(cites),
        })

    repondables = [l for l in lignes if l["answerable"]]
    non_repondables = [l for l in lignes if not l["answerable"]]
    return {
        "libelle": libelle,
        "questions": len(lignes),
        "expected_document_hit_at_3": round(
            sum(l["hit_at_3"] for l in repondables) / len(repondables), 3
        ),
        "citation_resolvable_rate": round(
            sum(l["resolvable"] for l in lignes) / len(lignes), 3
        ),
        "correct_abstention_rate": round(
            sum(l["abstention"] for l in non_repondables) / len(non_repondables), 3
        ) if non_repondables else 1.0,
        "abstentions_incorrectes": sum(1 for l in repondables if l["abstention"]),
        "mean_retrieved_documents": round(
            sum(l["documents_rendus"] for l in lignes) / len(lignes), 3
        ),
        "detail": lignes,
    }


def par_segment(mesure: dict) -> dict:
    """Une moyenne qui monte peut cacher un segment qui tombe."""
    segments: dict[str, list] = defaultdict(list)
    for ligne in mesure["detail"]:
        if ligne["answerable"]:
            for tag in ligne["risk_tags"]:
                segments[f"risk:{tag}"].append(ligne["hit_at_3"])
            segments[f"role:{ligne['role']}"].append(ligne["hit_at_3"])
    return {
        nom: {"questions": len(valeurs), "hit_at_3": round(sum(valeurs) / len(valeurs), 3)}
        for nom, valeurs in sorted(segments.items())
    }


def verdict_du_gate(mesure: dict) -> dict:
    seuils = json.loads(GATES.read_text(encoding="utf-8"))
    controles = {
        "expected_document_hit_at_3": (
            mesure["expected_document_hit_at_3"], seuils["minimum_expected_document_hit_at_3"]
        ),
        "citation_resolvable_rate": (
            mesure["citation_resolvable_rate"], seuils["minimum_citation_resolvable_rate"]
        ),
        "correct_abstention_rate": (
            mesure["correct_abstention_rate"], seuils["minimum_correct_abstention_rate"]
        ),
        "document_count": (len(knowledge_documents()), seuils["minimum_document_count"]),
    }
    detail = {
        nom: {"obtenu": obtenu, "seuil": seuil, "verdict": "PASS" if obtenu >= seuil else "FAIL"}
        for nom, (obtenu, seuil) in controles.items()
    }
    return {
        "verdict": "PASS" if all(c["verdict"] == "PASS" for c in detail.values()) else "FAIL",
        "controles": detail,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "online_eval.json")
    args = parser.parse_args()

    cas = calibration()
    original = knowledge_tool._score

    try:
        knowledge_tool._score = score_de_reference()
        reference = mesurer(cas, "retrieval de référence (score du formateur)")
    finally:
        knowledge_tool._score = original
    candidat = mesurer(cas, "candidat m6-retrieval-r2 (termes significatifs)")

    rapport = {
        "jeu": "rag_eval calibration (12 questions, split test non lu)",
        "metriques_m5_annoncees": json.loads(METRIQUES_M5.read_text(encoding="utf-8")),
        "reference": {**reference, "gate": verdict_du_gate(reference),
                      "segments": par_segment(reference)},
        "candidat": {**candidat, "gate": verdict_du_gate(candidat),
                     "segments": par_segment(candidat)},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8", newline="",
    )

    for cle in ("reference", "candidat"):
        bloc = rapport[cle]
        print(f"\n{bloc['libelle']}")
        print(f"  hit@3 {bloc['expected_document_hit_at_3']} | "
              f"citations résolubles {bloc['citation_resolvable_rate']} | "
              f"abstention correcte {bloc['correct_abstention_rate']} | "
              f"abstentions incorrectes {bloc['abstentions_incorrectes']} | "
              f"documents rendus {bloc['mean_retrieved_documents']}")
        print(f"  gate M5 : {bloc['gate']['verdict']}")
        for nom, valeurs in bloc["segments"].items():
            print(f"    {nom:<22} {valeurs['hit_at_3']}  ({valeurs['questions']} q.)")
    print(f"\n-> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
