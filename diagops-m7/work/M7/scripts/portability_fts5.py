#!/usr/bin/env python3
"""Essai de portabilité du brief 1 : score lexical (référence) contre SQLite FTS5.

Porte uniquement sur la calibration (12 questions) et sur des requêtes écrites
ici. Le split `test` n'est jamais lu : ses étiquettes sont scellées côté
formateur. Tout est local, déterministe, sans modèle ni réseau.

    python scripts/portability_fts5.py --output results/portabilite-fts5-r1
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sqlite3
import statistics
import sys
import time

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from lab import export_corpus, migrate, read_export, save, search  # noqa: E402
from fts5 import migrate_fts5, scores_fts5, search_fts5  # noqa: E402

RESTRICTED = "DOC-DATA-ACCESS-001"


def calibration(pack):
    rows = [json.loads(line) for line in
            (Path(pack) / "2026-S1/rag_eval/questions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    return [row for row in rows if row["split"] == "calibration"]


def hit_at_3(questions, results):
    pairs = [(q, r) for q, r in zip(questions, results) if q["answerable"]]
    return round(sum(bool(set(q["expected_document_ids"]) & set(r)) for q, r in pairs) / len(pairs), 3)


def timed(function, repeat=30):
    samples = []
    for _ in range(repeat):
        started = time.perf_counter()
        function()
        samples.append((time.perf_counter() - started) * 1000)
    samples.sort()
    return {"p50_ms": round(statistics.median(samples), 3),
            "p95_ms": round(samples[int(len(samples) * 0.95) - 1], 3)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-pack", type=Path, default=HERE.parents[1] / "data_pack")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    questions = calibration(args.data_pack)

    export = out / "corpus.json"
    export_corpus(args.data_pack, export)
    documents = read_export(export)["documents"]
    restricted_text = next(row["text"] for row in documents if row["document_id"] == RESTRICTED)

    indexes = {}
    build = {}
    for name, builder in [("sqlite_lexical", lambda p: migrate(export, p)),
                          ("fts5_shared", lambda p: migrate_fts5(export, p, layout="shared")),
                          ("fts5_per_role", lambda p: migrate_fts5(export, p, layout="per_role"))]:
        path = out / f"{name}.sqlite"
        started = time.perf_counter()
        builder(path)
        build[name] = {"build_ms": round((time.perf_counter() - started) * 1000, 3),
                       "bytes": path.stat().st_size}
        indexes[name] = path

    # 1. Requête brute : ce qu'on écrirait en premier.
    naive = []
    for q in questions:
        try:
            result = search_fts5(indexes["fts5_shared"], q["question"], q["role"], mode="naive")
            naive.append({"eval_id": q["eval_id"], "ok": True, "result": result})
        except sqlite3.OperationalError as exc:
            naive.append({"eval_id": q["eval_id"], "ok": False, "error": str(exc)})

    # 2. Requête tokenisée et citée, deux dispositions des droits.
    runs = {
        "lexical_json": [search(export, "json", q["question"], q["role"]) for q in questions],
        "lexical_sqlite": [search(indexes["sqlite_lexical"], "sqlite", q["question"], q["role"]) for q in questions],
        "fts5_shared": [search_fts5(indexes["fts5_shared"], q["question"], q["role"]) for q in questions],
        "fts5_per_role": [search_fts5(indexes["fts5_per_role"], q["question"], q["role"]) for q in questions],
    }
    reference = runs["lexical_json"]
    comparison = {}
    for name, results in runs.items():
        comparison[name] = {
            "hit_at_3": hit_at_3(questions, results),
            "top3_identical_to_reference": sum(a == b for a, b in zip(results, reference)),
            "top1_identical_to_reference": sum(a[:1] == b[:1] for a, b in zip(results, reference)),
            "unanswerable_with_results": sum(bool(r) for q, r in zip(questions, results) if not q["answerable"]),
            "latency": timed(lambda n=name: [
                (search(export, "json", q["question"], q["role"]) if n == "lexical_json" else
                 search(indexes["sqlite_lexical"], "sqlite", q["question"], q["role"]) if n == "lexical_sqlite" else
                 search_fts5(indexes[n], q["question"], q["role"])) for q in questions]),
        }

    # 3. Fuite inter-périmètres : chaque phrase du document restreint comme requête.
    probes = [line.strip("#-* ").strip() for line in restricted_text.splitlines() if len(line.strip()) > 20]
    leaks = {}
    for role in ("public", "technicien"):
        for name in runs:
            found = 0
            for probe in probes:
                if name == "lexical_json":
                    result = search(export, "json", probe, role)
                elif name == "lexical_sqlite":
                    result = search(indexes["sqlite_lexical"], "sqlite", probe, role)
                else:
                    result = search_fts5(indexes[name], probe, role)
                found += RESTRICTED in result
            leaks[f"{role}/{name}"] = found

    # 4. Canal auxiliaire : le document restreint influence-t-il les scores visibles ?
    without = out / "corpus_sans_restreint.json"
    value = json.loads(export.read_text(encoding="utf-8"))
    value["documents"] = [row for row in value["documents"] if row["document_id"] != RESTRICTED]
    save(without, value)
    shared_without = out / "fts5_shared_sans_restreint.sqlite"
    migrate_fts5(without, shared_without, layout="shared")
    side = []
    for q in questions:
        if q["role"] == "technicien":
            a = scores_fts5(indexes["fts5_shared"], q["question"], "technicien")
            b = scores_fts5(shared_without, q["question"], "technicien")
            per_role = scores_fts5(indexes["fts5_per_role"], q["question"], "technicien")
            side.append({"eval_id": q["eval_id"], "scores_changed": a != b,
                         "ranking_changed": sorted(a, key=lambda k: (a[k], k)) != sorted(b, key=lambda k: (b[k], k)),
                         "per_role_equals_without_restricted": per_role == b})

    report = {
        "scope": "calibration_only_retrieval_ranking_no_generation",
        "documents": len(documents), "calibration_questions": len(questions),
        "sqlite_version": sqlite3.sqlite_version,
        "build": build, "export_bytes": export.stat().st_size,
        "naive_query": {"errors": sum(not r["ok"] for r in naive), "cases": naive},
        "comparison": comparison,
        "observations": [{"eval_id": q["eval_id"], "role": q["role"], "answerable": q["answerable"],
                          "expected": q["expected_document_ids"],
                          **{name: runs[name][i] for name in runs}} for i, q in enumerate(questions)],
        "restricted_probes": len(probes), "restricted_leaks": leaks,
        "side_channel": {"queries": len(side),
                         "scores_changed": sum(s["scores_changed"] for s in side),
                         "ranking_changed": sum(s["ranking_changed"] for s in side),
                         "per_role_matches_corpus_without_restricted": sum(s["per_role_equals_without_restricted"] for s in side),
                         "cases": side},
        "limitations": ["7 documents actifs : hit@3 sature vite et départage mal",
                        "pas de génération : un meilleur classement ne prouve pas une meilleure réponse",
                        "latences d'un poste, sans concurrence"],
    }
    save(out / "report.json", report)
    print(json.dumps({k: report[k] for k in ("naive_query",)}["naive_query"]["errors"]), "erreurs de requête brute")
    for name, value in comparison.items():
        print(name, {k: v for k, v in value.items()})
    print("fuites", leaks)
    print("canal auxiliaire", {k: v for k, v in report["side_channel"].items() if k != "cases"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
