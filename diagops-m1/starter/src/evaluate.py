from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .config import load_config
from .dataset import file_sha256, load_jsonl, write_jsonl
from .metrics import calculate_metrics, parse_raw_json, validate_output
from .model_provider import ModelProvider


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--adapter", type=str)
    parser.add_argument("--allow-test", action="store_true")
    args = parser.parse_args()

    if "test" in args.data.name.lower() and not args.allow_test:
        raise RuntimeError(
            "Test final bloque. Utilisez --allow-test uniquement dans le Brief 2."
        )

    config = load_config(args.config)
    rows = load_jsonl(args.data)
    provider = ModelProvider(config=config, adapter_path=args.adapter)
    records: list[dict[str, Any]] = []

    for row in rows:
        generated = provider.generate(row["input_text"], row.get("report_id"))
        parsed = parse_raw_json(generated.text)
        records.append(
            {
                "annotation_id": row["annotation_id"],
                "report_id": row["report_id"],
                "expected_output": row["expected_output"],
                "raw_output": generated.text,
                "parsed_output": parsed,
                "schema_valid": validate_output(parsed),
                "latency_seconds": generated.latency_seconds,
                "accelerator_memory_bytes": generated.accelerator_memory_bytes,
            }
        )

    metrics = calculate_metrics(records)
    memories = [
        record["accelerator_memory_bytes"]
        for record in records
        if record["accelerator_memory_bytes"] is not None
    ]
    metrics["accelerator_memory_max_bytes"] = max(memories) if memories else None
    metrics["model_id"] = config["model"]["id"]
    metrics["model_revision"] = config["model"]["revision"]
    metrics["adapter"] = args.adapter
    metrics["data_sha256"] = file_sha256(args.data)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(args.output_dir / "predictions.jsonl", records)
    (args.output_dir / "metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(metrics, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
