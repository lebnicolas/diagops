#!/usr/bin/env python3
"""Applique les gates minimaux à un index et aux métriques M4 gelées."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.versioning import atomic_write_json, load_json  # noqa: E402


def evaluate(index: dict, metrics: dict, gates: dict) -> dict:
    checks = {
        "document_count": index.get("document_count", 0) >= gates["minimum_document_count"],
        "expected_document_hit_at_3": metrics.get("expected_document_hit_at_3", 0.0)
        >= gates["minimum_expected_document_hit_at_3"],
        "citation_resolvable_rate": metrics.get("citation_resolvable_rate", 0.0)
        >= gates["minimum_citation_resolvable_rate"],
        "correct_abstention_rate": metrics.get("correct_abstention_rate", 0.0)
        >= gates["minimum_correct_abstention_rate"],
    }
    # Provenance : un rapport de gate doit dire ce qu'il a réellement vérifié. Une métrique
    # absente du fichier mesuré vaut 0.0 ci-dessus, donc elle bloque — l'échec est le défaut sûr.
    # `document_count` est lu directement sur l'index présenté : il est mesuré par construction.
    provenance = {"document_count": "measured", **metrics.get("metrics_provenance", {})}
    report = {
        "status": "passed" if all(checks.values()) else "failed",
        "checks": checks,
        "checks_provenance": {key: provenance.get(key, "unknown") for key in checks},
        "measured_index_version": metrics.get("measured_index_version"),
        "measured_build_version": metrics.get("measured_build_version"),
        "evaluated_index_version": index.get("index_version"),
        "evaluated_build_version": index.get("build_version"),
    }
    # Une mesure faite sur un autre index que celui présenté ne vaut rien.
    if report["measured_index_version"] and report["measured_index_version"] != report["evaluated_index_version"]:
        report["status"] = "failed"
        report["checks"]["metrics_match_index"] = False
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--metrics", type=Path, required=True)
    parser.add_argument("--gates", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(load_json(args.index), load_json(args.metrics), load_json(args.gates))
    atomic_write_json(args.output, report)
    print(f"Gate {report['status']} : {args.output}")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
