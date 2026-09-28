#!/usr/bin/env python3
"""Rejoue diagops-m6-reference-r1 sur ce poste et la compare à l'état gelé.

Reprend la logique de tools/check_m7_release.py sans la modifier : même
inventaire des sources, même rejeu des deux campagnes, même normalisation des
durées. Deux différences, toutes deux liées à Windows :

- l'inventaire est comparé sur des chemins POSIX (le contrôle formateur compare
  `M6\\starter\\...` à `M6/starter/...` et refuse une référence intacte) ;
- la partie « checkout isolé » du contrôle formateur (lien symbolique vers le
  data pack) n'est pas reprise : elle exige un privilège Windows et ne porte que
  sur le kit M7, déjà couvert par `python -m unittest discover -s tests`.

Usage, depuis work/M7 avec le venv (PyYAML requis par l'agent M6) :
    .venv/Scripts/python scripts/replay_reference.py --output results/replay-reference-r1
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path, PurePath

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
from build_m7_reference import REFERENCE, replay, source_inventory  # noqa: E402


def posix_inventory() -> dict[str, str]:
    return {PurePath(path).as_posix(): digest for path, digest in source_inventory().items()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output
    output.mkdir(parents=True, exist_ok=False)

    release = json.loads((REFERENCE / "release_manifest.json").read_text(encoding="utf-8"))
    expected = release["source_sha256"]
    observed = posix_inventory()
    inventory = {
        "files": len(expected),
        "missing": sorted(set(expected) - set(observed)),
        "extra": sorted(set(observed) - set(expected)),
        "changed": sorted(k for k in expected if k in observed and expected[k] != observed[k]),
        "raw_windows_paths_equal": source_inventory() == expected,
    }
    inventory["equal"] = not (inventory["missing"] or inventory["extra"] or inventory["changed"])

    started = time.perf_counter()
    # Chemin absolu : le rejeu lance ses sous-processus depuis la racine S04.
    replayed = replay((output / "raw").resolve())
    replay_ms = round((time.perf_counter() - started) * 1000, 1)

    comparisons = {}
    for name, value in replayed.items():
        frozen = json.loads((REFERENCE / "evaluation" / f"{name}.json").read_text(encoding="utf-8"))
        comparisons[name] = value == frozen
    failed = {
        name: [row["scenario_id"] for row in replayed[name]["scenarios"] if not row["success"]]
        for name in ("nominal", "adversarial")
    }
    report = {
        "release_id": release["release_id"],
        "inventory": inventory,
        "replay_equal_to_frozen": comparisons,
        "failed_scenarios": failed,
        "known_failures_match": failed == release["known_failed_scenarios"],
        "summaries": {name: replayed[name]["summary"] for name in ("nominal", "adversarial")},
        "replay_ms_local": replay_ms,
        "python": sys.version.split()[0],
        "platform": sys.platform,
    }
    report["status"] = "reproduced" if inventory["equal"] and all(comparisons.values()) \
        and report["known_failures_match"] else "diverged"
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8", newline="\n")
    print(json.dumps({k: report[k] for k in ("status", "failed_scenarios", "replay_equal_to_frozen")},
                     ensure_ascii=False))
    print(json.dumps({"inventory_equal": inventory["equal"],
                      "raw_windows_paths_equal": inventory["raw_windows_paths_equal"]}))
    return 0 if report["status"] == "reproduced" else 1


if __name__ == "__main__":
    raise SystemExit(main())
