from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path
from typing import Any, Iterable


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            if "input_text" not in row or "expected_output" not in row:
                raise ValueError(f"{path}:{line_number}: annotation incomplete")
            rows.append(row)
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(
                json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
            )


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_split(
    rows: list[dict[str, Any]], seed: int, validation_size: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if validation_size <= 0 or validation_size >= len(rows):
        raise ValueError("validation_size doit etre compris entre 1 et n-1")
    ordered = sorted(rows, key=lambda row: row["annotation_id"])
    random.Random(seed).shuffle(ordered)
    validation = ordered[:validation_size]
    train = ordered[validation_size:]
    return train, validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--validation-size", type=int, default=80)
    args = parser.parse_args()

    rows = load_jsonl(args.input)
    train, validation = stable_split(rows, args.seed, args.validation_size)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    train_path = args.output_dir / "train.jsonl"
    validation_path = args.output_dir / "validation.jsonl"
    write_jsonl(train_path, train)
    write_jsonl(validation_path, validation)

    manifest = {
        "source": str(args.input),
        "source_sha256": file_sha256(args.input),
        "seed": args.seed,
        "train_rows": len(train),
        "validation_rows": len(validation),
        "train_sha256": file_sha256(train_path),
        "validation_sha256": file_sha256(validation_path),
    }
    (args.output_dir / "split_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
