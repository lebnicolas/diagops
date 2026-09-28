#!/usr/bin/env python3
"""Capacité des trois backends quand le corpus grossit (×1, ×10, ×100, ×1000).

Le corpus agrandi est synthétique : chaque document actif est dupliqué avec un
identifiant et un jeton propres, ses droits inchangés, son checksum recalculé.
Il ne dit rien de la qualité ; il mesure seulement le coût d'une requête et
d'une construction quand le nombre de documents augmente.

    python scripts/capacity_scale.py --output results/capacite-r1
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import statistics
import sys
import time

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
from lab import export_corpus, migrate, read_export, save, search  # noqa: E402
from fts5 import migrate_fts5, search_fts5  # noqa: E402


def enlarge(export: Path, factor: int, destination: Path) -> int:
    documents = read_export(export)["documents"]
    rows = []
    for copy in range(factor):
        for row in documents:
            if copy == 0:
                rows.append(row)
                continue
            text = f"{row['text']}\nexemplaire {row['document_id'].lower()}-{copy:04d}\n"
            rows.append({**row, "document_id": f"{row['document_id']}-X{copy:04d}", "text": text,
                         "checksum_sha256": hashlib.sha256(text.encode()).hexdigest()})
    save(destination, {"schema_version": 1, "documents": rows})
    return len(rows)


def per_query(function, questions, repeat):
    samples = []
    for _ in range(repeat):
        for q in questions:
            started = time.perf_counter()
            function(q)
            samples.append((time.perf_counter() - started) * 1000)
    samples.sort()
    return {"p50_ms": round(statistics.median(samples), 3), "p95_ms": round(samples[int(len(samples) * .95) - 1], 3)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-pack", type=Path, default=HERE.parents[1] / "data_pack")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--factors", default="1,10,100,1000")
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    base = out / "corpus.json"
    export_corpus(args.data_pack, base)
    questions = [json.loads(line) for line in (args.data_pack / "2026-S1/rag_eval/questions.jsonl").read_text(encoding="utf-8").splitlines()
                 if line.strip()]
    questions = [q for q in questions if q["split"] == "calibration"]
    rows = []
    for factor in [int(x) for x in args.factors.split(",")]:
        export = out / f"corpus_x{factor}.json"
        count = enlarge(base, factor, export)
        timings = {}
        started = time.perf_counter()
        migrate(export, out / f"lexical_x{factor}.sqlite")
        timings["build_sqlite_ms"] = round((time.perf_counter() - started) * 1000, 1)
        started = time.perf_counter()
        migrate_fts5(export, out / f"fts5_x{factor}.sqlite", layout="per_role")
        timings["build_fts5_per_role_ms"] = round((time.perf_counter() - started) * 1000, 1)
        repeat = 5 if factor <= 100 else 1
        rows.append({
            "factor": factor, "documents": count, "export_bytes": export.stat().st_size,
            "sqlite_bytes": (out / f"lexical_x{factor}.sqlite").stat().st_size,
            "fts5_per_role_bytes": (out / f"fts5_x{factor}.sqlite").stat().st_size,
            **timings,
            "query_json_lexical": per_query(lambda q: search(export, "json", q["question"], q["role"]), questions, repeat),
            "query_sqlite_lexical": per_query(lambda q: search(out / f"lexical_x{factor}.sqlite", "sqlite", q["question"], q["role"]), questions, repeat),
            "query_fts5_per_role": per_query(lambda q: search_fts5(out / f"fts5_x{factor}.sqlite", q["question"], q["role"]), questions, repeat),
        })
        print(json.dumps(rows[-1], ensure_ascii=False))
    save(out / "report.json", {"scope": "capacity_only_synthetic_duplicates_no_quality", "rows": rows,
                               "limitations": ["documents dupliqués : distribution des termes irréaliste",
                                               "un seul processus, sans concurrence", "poste de développement"]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
