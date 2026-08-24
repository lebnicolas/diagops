"""Commande de départ à compléter pendant le brief M3.

La commande charge les quatre sources, calcule leur empreinte, décrit les séries
temporelles et crée la structure de sortie. Elle n'applique volontairement
aucune règle métier, ne rapproche rien et ne présente pas les fichiers reçus
comme des données validées.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .io import load_sources, source_checksums
from .quarantine import empty_quarantine
from .rules import RuleRegistry
from .timeseries import series_overview


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Contrôler les sources DiagOps M3")
    parser.add_argument("--input", type=Path, required=True, help="dossier des sources reçues")
    parser.add_argument("--output", type=Path, required=True, help="dossier des sorties")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    sources = load_sources(args.input)
    checksums = source_checksums(args.input)

    for name in ("processed", "aggregates", "alignment"):
        (args.output / name).mkdir(parents=True, exist_ok=True)
    empty_quarantine().to_csv(args.output / "quarantine.csv", index=False)

    overview = series_overview(sources["sensors"])
    overview.to_csv(args.output / "series_overview.csv", index=False)

    registry = RuleRegistry()
    registry.to_frame().to_csv(args.output / "registre_regles.csv", index=False)

    report = {
        "status": "starter_to_complete",
        "message": (
            "Ajoutez le registre de règles, les contrôles temporels, le "
            "rapprochement, la quarantaine et la décision du brief."
        ),
        "sources": {
            name: {"rows": len(frame), "sha256": checksums[name]}
            for name, frame in sources.items()
        },
        "series": {
            "count": int(len(overview)),
            "equipment_with_measurements": int(overview["equipment_id"].nunique()),
            "median_step_hours": float(overview["median_step_hours"].median()),
        },
        "checks": [],
        "rules": {"declared": 0, "active": 0},
        "summary": {"passed": 0, "failed": 0, "quarantined_rows": 0},
        "decision": None,
    }
    (args.output / "validation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0
