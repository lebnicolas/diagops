#!/usr/bin/env python3
"""Gate de capacité du contrat : le candidat **tel qu'il est servi**, contrôles compris.

`scripts/capacity_scale.py` (brief 1) mesurait le moteur FTS5 nu. Le service du
candidat (`migration.serve`) ajoute à chaque requête l'empreinte du fichier
d'index et celle du manifeste. Ce script mesure les deux, sur des corpus
agrandis dont le manifeste est réécrit (7 × facteur documents), sur les 24 cas
gelés.

    python scripts/migration_capacity.py --output results/migration-capacite-r1
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import statistics
import sys
import time

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import lab  # noqa: E402
import migration as mg  # noqa: E402
from fts5 import search_fts5  # noqa: E402

PACK = HERE.parents[1] / "data_pack"
CASES = HERE / "migration_exercise" / "cases.jsonl"
FROZEN_SHA256 = "2ed61a27b32efc136652e1d81376c1fbc9b3c923ced31d84367de03f36d6f590"


def enlarged_pack(destination, factor):
    knowledge = Path(destination) / "2026-S1" / "knowledge"
    shutil.copytree(PACK / "2026-S1/knowledge", knowledge)
    path = knowledge / "manifest.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header, rows = reader.fieldnames, list(reader)
    extra = []
    for copy in range(1, factor):
        for row in rows:
            if row["status"] != "active":
                continue
            identifier = f"{row['document_id']}-X{copy:04d}"
            text = (knowledge / "documents" / row["asset_path"]).read_text(encoding="utf-8") + f"\nexemplaire {copy:04d}\n"
            (knowledge / "documents" / f"{identifier}.md").write_text(text, encoding="utf-8", newline="\n")
            extra.append({**row, "document_id": identifier, "asset_path": f"{identifier}.md", "supersedes_document_id": "",
                          "checksum_sha256": hashlib.sha256(text.encode()).hexdigest()})
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows + extra)
    path.write_text(buffer.getvalue(), encoding="utf-8", newline="")
    return Path(destination)


def p50(function, cases, repeat):
    samples = []
    for _ in range(repeat):
        for case in cases:
            started = time.perf_counter()
            function(case)
            samples.append((time.perf_counter() - started) * 1000)
    return round(statistics.median(samples), 3)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--factors", default="1,100,1000")
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    if hashlib.sha256(CASES.read_bytes()).hexdigest() != FROZEN_SHA256:
        raise SystemExit("cases.jsonl a changé depuis le gel : mesure refusée")
    cases = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line.strip()]
    rows = []
    for factor in [int(x) for x in args.factors.split(",")]:
        pack = enlarged_pack(out / f"x{factor}" / "pack", factor)
        bench = out / f"x{factor}" / "banc"
        bench.mkdir(parents=True)
        started = time.perf_counter()
        mg.export_v2(pack, bench / "corpus.json")
        mg.build_candidate(bench / "corpus.json", bench / "fts5.sqlite")
        mg.activate_v2(bench, "corpus.json", "json", pack=pack, slot="fallback")
        mg.activate_v2(bench, "fts5.sqlite", "fts5", pack=pack, slot="active")
        build_ms = round((time.perf_counter() - started) * 1000, 1)
        repeat = 3 if factor < 1000 else 1
        export = bench / "corpus.json"
        rows.append({
            "factor": factor, "documents": len(lab.read_export(export)["documents"]),
            "index_bytes": (bench / "fts5.sqlite").stat().st_size, "manifest_bytes": mg.manifest_path(pack).stat().st_size,
            "build_and_activate_ms": build_ms,
            "p50_existant_json_ms": p50(lambda c: lab.search(export, "json", c["question"], c["role"]), cases, repeat),
            "p50_fts5_nu_ms": p50(lambda c: search_fts5(bench / "fts5.sqlite", c["question"], c["role"]), cases, repeat),
            "p50_candidat_servi_ms": p50(lambda c: mg.serve(bench, c["question"], c["role"], pack=pack), cases, repeat),
            "p50_empreinte_index_seule_ms": p50(lambda c: lab.digest(bench / "fts5.sqlite"), cases[:5], repeat),
        })
        print(json.dumps(rows[-1]))
        shutil.rmtree(out / f"x{factor}")
    gate = [r for r in rows if r["factor"] >= 100]
    lab.save(out / "report.json", {
        "rows": rows,
        "gate_capacite": {"seuil": "p50 candidat servi <= p50 existant, à 700 documents et au-delà",
                          "passe": all(r["p50_candidat_servi_ms"] <= r["p50_existant_json_ms"] for r in gate)},
        "limitations": ["corpus dupliqué", "un processus", "poste de développement"]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
