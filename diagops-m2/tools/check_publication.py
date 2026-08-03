#!/usr/bin/env python3
"""Bloque les contenus privés, dupliqués ou trop lourds avant publication."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_SIZE = 25 * 1024 * 1024
MODULE_PATTERN = re.compile(r"M\d+")
FORBIDDEN_PARTS = {
    "_conception",
    ".venv",
    "venv",
    "__pycache__",
    ".pytest_cache",
    ".ipynb_checkpoints",
    "checkpoints",
}
FORBIDDEN_NAMES = {
    ".DS_Store",
    "anomaly_oracle.csv",
    "validation_reference.json",
}
FORBIDDEN_SUFFIXES = {".safetensors", ".pt", ".pth", ".ckpt", ".onnx"}


def publication_candidates() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / item.decode() for item in result.stdout.split(b"\0") if item]


def reasons(path: Path) -> list[str]:
    relative = path.relative_to(ROOT)
    parts = relative.parts
    found: list[str] = []

    if FORBIDDEN_PARTS.intersection(parts):
        found.append("dossier privé, cache ou artefact interdit")
    if path.name in FORBIDDEN_NAMES or path.suffix.lower() in FORBIDDEN_SUFFIXES:
        found.append("type de fichier non distribuable")
    if len(parts) >= 2 and MODULE_PATTERN.fullmatch(parts[0]) and parts[1] == "data":
        found.append("copie de données dans un module : utiliser data_pack/")
    if path.is_file() and path.stat().st_size > MAX_FILE_SIZE:
        found.append(f"fichier supérieur à {MAX_FILE_SIZE // (1024 * 1024)} MiB")
    return found


def main() -> int:
    failures = [
        (path.relative_to(ROOT), issue)
        for path in publication_candidates()
        for issue in reasons(path)
    ]
    if failures:
        print("Publication refusée :")
        for path, issue in failures:
            print(f"- {path}: {issue}")
        return 1

    print("Contrôle de publication réussi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
