#!/usr/bin/env python3
"""Mesure un index candidat sur le jeu d'évaluation, au lieu de relire des métriques figées.

Le starter livrait un gate dont trois contrôles sur quatre lisaient `metrics_calibration.json`,
un fichier du data pack qui ne dépend pas du candidat évalué : un index dégradé passait le gate.
Ce pipeline produit les mêmes quatre métriques, mais *à partir de l'index fourni*, en rejouant le
retrieval lexical de référence transmis par M4.

La séparation est volontaire : ici on **mesure**, `evaluate_release.py` **décide**. Les seuils
restent dans `configs/gates.json`.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.versioning import atomic_write_json, load_json  # noqa: E402
# Le scoring vit dans src/retrieval.py : l'API servie et cette mesure doivent partager
# exactement le même classement, sinon le gate ne dit plus rien sur ce qui est servi.
from src.retrieval import TOP_K, lexical_score, rank, tokenize, visible_to  # noqa: E402,F401


def measure(index: dict, questions: list[dict], split: str = "calibration") -> dict:
    documents = index["documents"]
    known_ids = {item["document_id"] for item in documents}

    selected = [q for q in questions if q.get("split") == split]
    answerable = [q for q in selected if q.get("answerable")]
    unanswerable = [q for q in selected if not q.get("answerable")]

    hits = 0
    citations_total = 0
    citations_resolvable = 0
    restricted_leaks = 0
    correct_abstentions = 0
    per_question: list[dict] = []

    for question in selected:
        role = question.get("role", "technicien")
        terms = tokenize(question["question"])
        retrieved = rank(terms, visible_to(documents, role))
        retrieved_ids = [item["document_id"] for item in retrieved]

        citations_total += len(retrieved_ids)
        citations_resolvable += sum(1 for did in retrieved_ids if did in known_ids)
        restricted_leaks += sum(
            1 for item in retrieved
            if item.get("sensitivity") == "restreint" and role not in item["allowed_roles"]
        )

        if question.get("answerable"):
            hit = bool(set(question["expected_document_ids"]) & set(retrieved_ids))
            hits += int(hit)
        else:
            # L'abstention ne se déduit PAS du retrieval : mesuré le 07/09, les deux questions
            # sans réponse ramènent des documents avec un score non nul, et aucun seuil ne les
            # sépare des questions répondables — RAG-CAL-008 (répondable) score 0,33 quand
            # RAG-CAL-012 (sans réponse) score 0,36. C'est une propriété de la couche de
            # génération, absente de ce périmètre. Voir `correct_abstention_rate` ci-dessous.
            hit = None
            correct_abstentions += int(not retrieved_ids)

        per_question.append({
            "eval_id": question["eval_id"],
            "role": role,
            "answerable": question.get("answerable"),
            "expected_document_ids": question.get("expected_document_ids", []),
            "retrieved_document_ids": retrieved_ids,
            "expected_document_hit_at_3": hit,
        })

    return {
        "calibration_questions": len(selected),
        "answerable_questions": len(answerable),
        "unanswerable_questions": len(unanswerable),
        "expected_document_hit_at_3": round(hits / len(answerable), 6) if answerable else 0.0,
        "citation_resolvable_rate": (
            round(citations_resolvable / citations_total, 6) if citations_total else 1.0
        ),
        "restricted_citation_count": restricted_leaks,
        "retrieval_only_abstention_rate": (
            round(correct_abstentions / len(unanswerable), 6) if unanswerable else 1.0
        ),
        "measured_index_version": index.get("index_version"),
        "measured_build_version": index.get("build_version"),
        "test_split_used": split == "test",
        "metrics_provenance": {
            "expected_document_hit_at_3": "measured",
            "citation_resolvable_rate": "measured",
            "restricted_citation_count": "measured",
            "correct_abstention_rate": "unmeasurable_here",
        },
        "per_question": per_question,
    }


def inherit(metrics: dict, source: Path, keys: tuple[str, ...]) -> dict:
    """Importe explicitement une métrique qu'on ne sait pas mesurer, en gardant sa provenance.

    Une métrique héritée n'est pas une métrique mesurée : elle ne dit rien du candidat. La tracer
    comme telle est le minimum pour que le rapport de gate ne mente pas sur ce qu'il a vérifié.
    """
    reference = load_json(source)
    for key in keys:
        if key not in reference:
            raise ValueError(f"Métrique absente de la référence : {key}")
        metrics[key] = reference[key]
        metrics["metrics_provenance"][key] = f"inherited:{source.name}"
    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--questions", type=Path, required=True)
    parser.add_argument("--split", default="calibration")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--inherit-abstention-from", type=Path, default=None,
        help="métriques de référence d'où importer correct_abstention_rate, faute de couche de génération",
    )
    args = parser.parse_args()

    if args.split == "test":
        raise SystemExit("Refus : le split test est scellé côté formateur.")

    questions = [
        json.loads(line)
        for line in args.questions.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    metrics = measure(load_json(args.index), questions, args.split)
    if args.inherit_abstention_from:
        metrics = inherit(metrics, args.inherit_abstention_from, ("correct_abstention_rate",))
    atomic_write_json(args.output, metrics)
    print(
        f"Mesure écrite : {args.output} "
        f"(hit@3={metrics['expected_document_hit_at_3']}, "
        f"citations={metrics['citation_resolvable_rate']}, "
        f"restreint={metrics['restricted_citation_count']}, "
        f"abstention={metrics.get('correct_abstention_rate', 'non mesurée')})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
