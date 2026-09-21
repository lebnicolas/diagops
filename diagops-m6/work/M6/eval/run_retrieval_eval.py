#!/usr/bin/env python3
"""Évaluation du retrieval seul — étape 7 du brief 1.

Le harness agentique mesure le système complet : il ne dit pas si un échec vient
du choix d'outil, de l'enchaînement ou du document rendu. Ce banc isole la
recherche documentaire, sur un jeu gelé avant toute modification du score.

Trois familles de questions, et elles ne se lisent pas ensemble :

- `vocabulaire_du_corpus` — la question emploie les mots du document ;
- `vocabulaire_utilisateur` — l'épreuve : la question emploie les mots des
  techniciens, qui ne sont pas toujours ceux du corpus ;
- `hors_domaine` — aucun document ne devrait être tenu pour pertinent.

    python eval/run_retrieval_eval.py [--label reference]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools import knowledge as knowledge_tool

JEU = ROOT / "eval" / "retrieval_eval.jsonl"


def charger() -> list[dict]:
    return [
        json.loads(ligne)
        for ligne in JEU.read_text(encoding="utf-8").splitlines()
        if ligne.strip()
    ]


def interroger(question: str, role: str) -> list[dict]:
    resultat = knowledge_tool.run({"query": question, "top_k": 3}, role=role)
    return [
        {"document_id": row["document_id"], "score": row["score"]}
        for row in resultat.rows
    ]


def evaluer(cas: list[dict]) -> dict:
    lignes = []
    for item in cas:
        rendus = interroger(item["question"], item["role"])
        attendus = set(item["expected_documents"])
        top1 = rendus[0]["document_id"] if rendus else None
        lignes.append({
            "id": item["id"],
            "categorie": item["categorie"],
            "top1": top1,
            "score_top1": rendus[0]["score"] if rendus else 0.0,
            "rendus": [r["document_id"] for r in rendus],
            "attendus": sorted(attendus),
            "hit_at_1": bool(attendus) and top1 in attendus,
            "hit_at_3": bool(attendus) and bool(attendus & {r["document_id"] for r in rendus}),
            "silence": not rendus,
        })

    def part(famille: str, cle: str) -> float:
        lot = [l for l in lignes if l["categorie"] == famille]
        return round(sum(l[cle] for l in lot) / len(lot), 3) if lot else 0.0

    domaine = [l for l in lignes if l["categorie"] != "hors_domaine"]
    hors = [l for l in lignes if l["categorie"] == "hors_domaine"]

    return {
        "recall_at_1": {
            famille: part(famille, "hit_at_1")
            for famille in ("vocabulaire_du_corpus", "vocabulaire_utilisateur", "ambigu")
        },
        "recall_at_3": {
            famille: part(famille, "hit_at_3")
            for famille in ("vocabulaire_du_corpus", "vocabulaire_utilisateur", "ambigu")
        },
        "recall_at_1_global": round(sum(l["hit_at_1"] for l in domaine) / len(domaine), 3),
        # La séparation est le vrai enjeu : tant que le pire score du domaine
        # reste sous le meilleur score hors domaine, aucun seuil ne peut trier.
        "score_min_domaine": min((l["score_top1"] for l in domaine), default=0.0),
        "score_max_hors_domaine": max((l["score_top1"] for l in hors), default=0.0),
        "silences_hors_domaine": sum(l["silence"] for l in hors),
        "separation": round(
            min((l["score_top1"] for l in domaine), default=0.0)
            - max((l["score_top1"] for l in hors), default=0.0), 3,
        ),
        "detail": lignes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--label", default="reference", help="nom de la mesure")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    cas = charger()
    empreinte = hashlib.sha256(JEU.read_bytes()).hexdigest()
    rapport = {"label": args.label, "jeu": JEU.name, "empreinte": empreinte,
               "cas": len(cas), **evaluer(cas)}

    sortie = args.output or ROOT / "results" / f"retrieval_{args.label}.json"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(
        json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8", newline="",
    )

    print(f"[{args.label}]  jeu {JEU.name} — empreinte {empreinte[:16]}…")
    print(f"  Recall@1 global (hors « hors domaine ») : {rapport['recall_at_1_global']}")
    for famille, valeur in rapport["recall_at_1"].items():
        print(f"    {famille:<24} @1 {valeur}   @3 {rapport['recall_at_3'][famille]}")
    print(f"  score min domaine {rapport['score_min_domaine']} | "
          f"max hors domaine {rapport['score_max_hors_domaine']} | "
          f"séparation {rapport['separation']}")
    print(f"  silences sur hors domaine : {rapport['silences_hors_domaine']} / 5")
    print(f"  -> {sortie}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
