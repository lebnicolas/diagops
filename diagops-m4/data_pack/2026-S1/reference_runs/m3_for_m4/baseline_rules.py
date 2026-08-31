#!/usr/bin/env python3
"""Baseline M3 figée pour la cible de provenance utilisée en M4."""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


EXPECTED_UNIT = {
    "vibration_mm_s": "mm/s",
    "temperature_c": "°C",
    "pressure_bar": "bar",
    "current_a": "A",
    "rpm": "rpm",
}
RANGES = {
    "vibration_mm_s": (0.0, 12.0),
    "temperature_c": (-20.0, 140.0),
    "pressure_bar": (0.0, 25.0),
    "current_a": (0.0, 120.0),
    "rpm": (0.0, 3000.0),
}


def parse_timestamp(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def rule_hits(row: dict[str, str]) -> list[str]:
    hits: list[str] = []
    sensor = row.get("sensor_name", "")
    value = row.get("value", "")
    timestamp = row.get("timestamp", "")

    if row.get("period") != "2026-S1":
        hits.append("M3-PERIOD")
    if sensor not in EXPECTED_UNIT:
        hits.append("M3-SENSOR")
    elif row.get("unit") != EXPECTED_UNIT[sensor]:
        hits.append("M3-UNIT")

    moment = parse_timestamp(timestamp)
    if moment is None or not timestamp.endswith("Z"):
        hits.append("M3-TIMESTAMP")
    elif moment.minute != 0 or moment.second != 0 or moment.hour % 6:
        hits.append("M3-GRID")

    try:
        numeric = float(value)
    except ValueError:
        hits.append("M3-MISSING")
    else:
        if numeric == -999.0:
            hits.append("M3-SENTINEL")
        if sensor in RANGES:
            low, high = RANGES[sensor]
            if numeric < low or numeric > high:
                hits.append("M3-RANGE")
        decimals = value.partition(".")[2]
        if len(decimals) > 2:
            hits.append("M3-PRECISION")
    return hits


def predict(row: dict[str, str]) -> tuple[str, str]:
    hits = rule_hits(row)
    return ("fabriquée" if hits else "réelle", ";".join(hits) or "none")


def metrics(rows: list[dict[str, str]]) -> dict[str, float | int]:
    labelled = [row for row in rows if row.get("provenance")]
    counts = Counter(
        (row["provenance"], row["prediction"])
        for row in labelled
    )
    tp = counts[("fabriquée", "fabriquée")]
    fp = counts[("réelle", "fabriquée")]
    fn = counts[("fabriquée", "réelle")]
    tn = counts[("réelle", "réelle")]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    return {
        "rows": len(labelled),
        "true_positive": tp,
        "false_positive": fp,
        "false_negative": fn,
        "true_negative": tn,
        "precision_fabricated": round(precision, 6),
        "recall_fabricated": round(recall, 6),
        "f1_fabricated": round(
            2 * precision * recall / (precision + recall)
            if precision + recall else 0.0,
            6,
        ),
        "accuracy": round((tp + tn) / len(labelled), 6) if labelled else 0.0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--metrics", type=Path)
    args = parser.parse_args()

    with args.input.open(encoding="utf-8", newline="") as handle:
        source = list(csv.DictReader(handle))
    output: list[dict[str, str]] = []
    for row in source:
        prediction, reasons = predict(row)
        output.append({**row, "prediction": prediction, "rule_hits": reasons})

    args.predictions.parent.mkdir(parents=True, exist_ok=True)
    with args.predictions.open("w", encoding="utf-8", newline="") as handle:
        fields = list(output[0]) if output else ["prediction", "rule_hits"]
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(output)

    if args.metrics:
        result = metrics(output)
        args.metrics.parent.mkdir(parents=True, exist_ok=True)
        args.metrics.write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
