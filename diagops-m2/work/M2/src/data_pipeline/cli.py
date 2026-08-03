"""Commande de départ à compléter pendant le brief M2.

La commande charge les sources, calcule leur empreinte et crée la structure de
sortie. Elle n'applique volontairement aucune règle métier et ne présente pas
les fichiers bruts comme des données validées.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .io import load_sources, source_checksums
from .quarantine import empty_quarantine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Contrôler les données DiagOps M2")
    parser.add_argument("--input", type=Path, required=True, help="dossier des CSV reçus")
    parser.add_argument("--output", type=Path, required=True, help="dossier des sorties")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    sources = load_sources(args.input)

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "processed").mkdir(exist_ok=True)
    empty_quarantine().to_csv(args.output / "quarantine.csv", index=False)

    report = {
        "status": "starter_to_complete",
        "message": "Ajoutez les règles, la quarantaine et la décision du brief.",
        "sources": {
            name: {"rows": len(frame), "sha256": source_checksums(args.input)[name]}
            for name, frame in sources.items()
        },
        "checks": [],
        "summary": {"passed": 0, "failed": 0, "quarantined_rows": 0},
        "decision": None,
    }
    (args.output / "validation_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return 0

