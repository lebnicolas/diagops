#!/usr/bin/env python3
"""Initialise sans écrasement l'espace de travail d'un module."""

from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATTERN = re.compile(r"M\d+")


def module_name(value: str) -> str:
    normalized = value.upper()
    if not MODULE_PATTERN.fullmatch(normalized):
        raise argparse.ArgumentTypeError("module attendu sous la forme M2")
    return normalized


def init_module(module: str) -> Path:
    source = ROOT / module / "starter"
    destination = ROOT / "work" / module

    if not source.is_dir():
        raise FileNotFoundError(f"Starter indisponible : {source.relative_to(ROOT)}")
    if destination.exists():
        raise FileExistsError(
            f"Refus d'écraser le travail existant : {destination.relative_to(ROOT)}"
        )

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        source,
        destination,
        ignore=shutil.ignore_patterns(
            ".venv",
            "__pycache__",
            ".pytest_cache",
            ".ipynb_checkpoints",
            ".DS_Store",
        ),
    )
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Copier le starter d'un module dans work/ sans écrasement."
    )
    parser.add_argument("module", type=module_name, help="module à initialiser, ex. M2")
    args = parser.parse_args()

    try:
        destination = init_module(args.module)
    except (FileNotFoundError, FileExistsError) as exc:
        parser.error(str(exc))

    print(f"Espace créé : {destination.relative_to(ROOT)}")
    print("Travaillez et committez ce dossier sur main dans votre dépôt privé.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
