#!/usr/bin/env python3
"""Restaure un index archivé, explicitement nommé.

Pas de « dernière version connue » implicite : sous incident, l'automatisme qui choisit tout seul
est celui qui restaure la version qui vient de casser. La version cible est un argument, et
`--list` sert à la choisir en connaissance de cause.

La restauration revérifie l'intégrité de l'archive avant de la remettre en service — une archive
corrompue restaurée sous incident transforme une panne en deux pannes.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.versioning import atomic_write_json, load_json  # noqa: E402


def available(history: Path) -> list[str]:
    return sorted(path.stem.replace("index-", "") for path in history.glob("index-*.json"))


def rollback_index(active: Path, history: Path, index_version: str) -> dict:
    archive = history / f"index-{index_version}.json"
    if not archive.is_file():
        raise SystemExit(
            f"Version absente de l'historique : {index_version}. "
            f"Disponibles : {', '.join(available(history)) or 'aucune'}"
        )

    index = load_json(archive)
    documents = index.get("documents")
    if not isinstance(documents, list) or not documents:
        raise SystemExit(f"Archive inexploitable : {archive.name} ne contient aucun document.")
    if any(not document.get("terms") for document in documents):
        raise SystemExit(f"Archive inexploitable : {archive.name} est sans postings.")
    if index.get("document_count") != len(documents):
        raise SystemExit(f"Archive incohérente : {archive.name}.")

    replaced = None
    if active.is_file():
        courant = load_json(active)
        replaced = str(courant.get("index_version", "inconnue"))
        # Archiver AVANT de restaurer, y compris — et surtout — une version fautive.
        # Constaté le 07/09 en enchaînant une promotion et un retour : le rollback écrasait la
        # version qu'il remplaçait sans en garder trace. Deux conséquences, chacune suffisante :
        # on ne peut plus revenir sur un rollback pris à tort, et le post-incident perd la pièce
        # à conviction. Le brief 2 l'exige d'ailleurs — « n'efface ni traces ni état initial ».
        archive = history / f"index-{replaced}.json"
        if not archive.exists():
            shutil.copy2(active, archive)

    atomic_write_json(active, index)
    return {"restored": str(index.get("index_version")), "replaced": replaced}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("index_version", nargs="?")
    parser.add_argument("--active", type=Path, required=True)
    parser.add_argument("--history", type=Path, required=True)
    parser.add_argument("--list", action="store_true", help="lister les versions restaurables")
    args = parser.parse_args()

    if args.list or not args.index_version:
        versions = available(args.history)
        print("Versions restaurables :")
        for version in versions:
            print(f"  {version}")
        if not versions:
            print("  aucune")
        return 0 if args.list else 1

    result = rollback_index(args.active, args.history, args.index_version)
    print(f"Index restaure : {result['replaced']} -> {result['restored']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
