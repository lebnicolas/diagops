#!/usr/bin/env python3
"""Vérifie les contrats du paquet apprenant M4 et, en option, les actifs formateur."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "data_pack" / "2026-S1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify_model_eval() -> dict[str, int]:
    calibration = csv_rows(PACK / "model_eval" / "sensor_calibration.csv")
    test = csv_rows(PACK / "model_eval" / "sensor_test.csv")
    require(len(calibration) == 900, "Calibration M4 : 900 lignes attendues")
    require(len(test) == 1800, "Test M4 : 1 800 lignes attendues")
    require(all(row.get("provenance") in {"réelle", "fabriquée"} for row in calibration),
            "Calibration M4 : étiquette de provenance invalide")
    require(all("provenance" not in row for row in test), "Test M4 : oracle exposé")
    calibration_groups = Counter(row["window_id"] for row in calibration)
    test_groups = Counter(row["window_id"] for row in test)
    require(set(calibration_groups.values()) == {30}, "Calibration : fenêtres non atomiques")
    require(set(test_groups.values()) == {30}, "Test : fenêtres non atomiques")
    require(not (set(calibration_groups) & set(test_groups)), "Fenêtre commune calibration/test")
    m3_rows = (
        csv_rows(PACK / "sensors_control" / "control_sample.csv")
        + csv_rows(PACK / "sensors_control" / "control_batch.csv")
    )
    key = lambda row: (row["equipment_id"], row["timestamp"], row["sensor_name"])
    m3_keys = {key(row) for row in m3_rows}
    require(not ({key(row) for row in calibration} & m3_keys),
            "Calibration M4 : recouvrement avec le lot M3")
    require(not ({key(row) for row in test} & m3_keys),
            "Test M4 : recouvrement avec le lot M3")
    return {"calibration_rows": len(calibration), "test_rows": len(test)}


def verify_knowledge() -> dict[str, int]:
    manifest = csv_rows(PACK / "knowledge" / "manifest.csv")
    require(len(manifest) == 8, "Corpus M4 : huit documents attendus")
    ids = [row["document_id"] for row in manifest]
    require(len(ids) == len(set(ids)), "Corpus M4 : document_id dupliqué")
    for row in manifest:
        asset = PACK / "knowledge" / "documents" / row["asset_path"]
        require(asset.is_file(), f"Document absent : {asset.name}")
        require(sha256(asset) == row["checksum_sha256"],
                f"Checksum invalide : {row['document_id']}")
        require(bool(row["license"] and row["sensitivity"] and row["revision"]),
                f"Métadonnées incomplètes : {row['document_id']}")
    return {"documents": len(manifest)}


def verify_rag_eval() -> dict[str, int]:
    path = PACK / "rag_eval" / "questions.jsonl"
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    calibration = [row for row in rows if row["split"] == "calibration"]
    test = [row for row in rows if row["split"] == "test"]
    require(len(calibration) == 12 and len(test) == 12,
            "RAG M4 : douze questions par split attendues")
    require(all(row["label_visibility"] == "visible" for row in calibration),
            "RAG calibration : labels non visibles")
    require(all(row["label_visibility"] == "sealed" for row in test),
            "RAG test : labels non scellés")
    require(all(row["expected_document_ids"] is None and row["answerable"] is None for row in test),
            "RAG test : oracle exposé")
    return {"rag_calibration": len(calibration), "rag_test": len(test)}


def verify_reference() -> dict[str, int | float]:
    root = PACK / "reference_runs" / "m3_for_m4"
    predictions = csv_rows(root / "baseline_predictions_calibration.csv")
    metrics = json.loads((root / "baseline_metrics_calibration.json").read_text(encoding="utf-8"))
    require(len(predictions) == 900, "Baseline M3 : 900 prédictions attendues")
    require(metrics["rows"] == 900, "Baseline M3 : métriques incomplètes")
    return {"baseline_rows": metrics["rows"], "baseline_f1": metrics["f1_fabricated"]}


def verify_trainer() -> dict[str, int]:
    root = ROOT / "_conception" / "M4"
    required = [
        root / "oracles" / "sensor_test_oracle.csv",
        root / "oracles" / "sensor_challenge_oracle.csv",
        root / "oracles" / "rag_test_oracle.jsonl",
        root / "oracles" / "rag_challenge_oracle.jsonl",
        root / "reveal" / "sensor_challenge.csv",
        root / "reveal" / "knowledge_revision" / "manifest.csv",
        root / "reveal" / "rag_challenge_questions.jsonl",
    ]
    missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
    require(not missing, f"Actifs formateur absents : {missing}")
    test_oracle = csv_rows(root / "oracles" / "sensor_test_oracle.csv")
    challenge = csv_rows(root / "reveal" / "sensor_challenge.csv")
    challenge_oracle = csv_rows(root / "oracles" / "sensor_challenge_oracle.csv")
    require(len(test_oracle) == 1800, "Oracle capteur test : 1 800 lignes attendues")
    require(len(challenge) == 1500 and len(challenge_oracle) == 1500,
            "Lot de contradiction capteur : 1 500 lignes attendues")
    rag_test = [json.loads(line) for line in
                (root / "oracles" / "rag_test_oracle.jsonl").read_text(encoding="utf-8").splitlines()]
    rag_challenge = [json.loads(line) for line in
                     (root / "oracles" / "rag_challenge_oracle.jsonl").read_text(encoding="utf-8").splitlines()]
    require(len(rag_test) == 12 and len(rag_challenge) == 6,
            "Oracles RAG incomplets")
    reveal_manifest = csv_rows(root / "reveal" / "knowledge_revision" / "manifest.csv")
    for row in reveal_manifest:
        asset = root / "reveal" / "knowledge_revision" / row["asset_path"]
        require(sha256(asset) == row["checksum_sha256"],
                f"Checksum challenge invalide : {row['document_id']}")
    return {"trainer_assets": len(required)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trainer", action="store_true", help="vérifier aussi _conception/M4")
    args = parser.parse_args()
    result: dict[str, int | float] = {}
    for check in (verify_model_eval, verify_knowledge, verify_rag_eval, verify_reference):
        result.update(check())
    if args.trainer:
        result.update(verify_trainer())
    print(json.dumps({"status": "ready", **result}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
