#!/usr/bin/env python3
"""Publie un index candidat en archivant d'abord celui qu'il remplace.

Le compose faisait `cp candidat actif` : la publication était atomique, mais l'index sain
disparaissait au moment même où il devenait le seul recours. Une procédure de retour arrière
suppose qu'il reste quelque chose vers quoi revenir.

Deux garanties tenues ici :

- **archiver avant de publier** — l'index remplacé est copié dans l'historique, nommé par sa
  version, avant que le nouveau ne prenne sa place ;
- **publier atomiquement** — écriture dans un fichier temporaire puis `replace()`, pour qu'aucun
  lecteur ne voie un index à moitié écrit.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.versioning import atomic_write_json, load_json  # noqa: E402


def promote_index(candidate: Path, active: Path, history: Path, gate: Path | None = None) -> dict:
    if gate is not None:
        report = load_json(gate)
        if report.get("status") != "passed":
            raise SystemExit("Publication refusée : le gate n'est pas passé.")

    index = load_json(candidate)
    if not index.get("documents"):
        raise SystemExit("Publication refusée : index candidat sans document.")

    history.mkdir(parents=True, exist_ok=True)
    archived = None
    if active.is_file():
        previous = load_json(active)
        version = str(previous.get("index_version", "inconnue"))
        archive = history / f"index-{version}.json"
        # Ne jamais réécrire une archive : une version archivée est un point de retour, pas un
        # cache. L'écraser reviendrait à perdre l'état vers lequel on comptait revenir.
        if not archive.exists():
            shutil.copy2(active, archive)
        archived = version

    atomic_write_json(active, index)
    return {
        "published": str(index.get("index_version")),
        "archived": archived,
        "history": sorted(path.name for path in history.glob("index-*.json")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--active", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--gate", type=Path, default=None)
    args = parser.parse_args()

    result = promote_index(args.candidate, args.active, args.history, args.gate)
    if result["archived"]:
        print(f"Index archive : {result['archived']}")
    print(f"Index publie : {result['published']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
