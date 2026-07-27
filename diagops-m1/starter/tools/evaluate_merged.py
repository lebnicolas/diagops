"""Evaluation avec l'adaptateur LoRA FUSIONNE dans le modele de base.

Motivation
----------
`src/evaluate.py` charge l'adaptateur via `PeftModel.from_pretrained` sans le
fusionner : les matrices LoRA restent des couches separees, recalculees a chaque
token genere, sur q_proj/k_proj/v_proj/o_proj des 28 couches. La latence mesuree
inclut donc un surcout propre au format d'entrainement, que la mise en service
supprimerait.

`merge_and_unload()` replie W + BA dans les poids du modele de base. L'operation
est mathematiquement equivalente : les sorties doivent etre identiques, aux
erreurs d'arrondi bfloat16 pres. Ce script permet de le verifier et de mesurer
la latence reelle du candidat.

Ce fichier est un AJOUT au starter. Aucun fichier de `src/` n'est modifie, et
les parametres de generation restent ceux de la configuration passee en
argument, pour rester comparable a la baseline.

Usage
-----
    python -m tools.evaluate_merged \
        --config configs/baseline.yaml \
        --adapter work/runs/lora_reference/adapter \
        --data work/splits/validation.jsonl \
        --output-dir work/lora_reference_validation_merged
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.config import load_config
from src.dataset import file_sha256, load_jsonl, write_jsonl
from src.metrics import calculate_metrics, parse_raw_json, validate_output
from src.model_provider import ModelProvider


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--adapter", required=True, type=str)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--allow-test", action="store_true")
    args = parser.parse_args()

    if "test" in args.data.name.lower() and not args.allow_test:
        raise RuntimeError(
            "Test final bloque. Utilisez --allow-test uniquement dans le Brief 2."
        )

    config = load_config(args.config)
    rows = load_jsonl(args.data)

    provider = ModelProvider(config=config, adapter_path=args.adapter)

    # Seule difference avec src/evaluate.py : les poids LoRA sont replies dans
    # le modele de base avant toute generation.
    merged = provider.model.merge_and_unload()
    merged.eval()
    provider.model = merged
    print("Adaptateur fusionne dans le modele de base.", flush=True)

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
    metrics["adapter_merged"] = True
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
