from __future__ import annotations

import json
import math
import re
from collections import Counter
from statistics import mean
from typing import Any, Iterable

from pydantic import ValidationError

from .schemas import DiagOpsOutput


TEXT_FIELDS = ["symptom", "failure_hypothesis", "recommended_action"]
SEVERITIES = ["low", "medium", "high", "critical"]


def parse_raw_json(text: str) -> dict[str, Any] | None:
    try:
        value = json.loads(text.strip())
    except (json.JSONDecodeError, TypeError):
        return None
    return value if isinstance(value, dict) else None


def validate_output(value: dict[str, Any] | None) -> bool:
    if value is None:
        return False
    try:
        DiagOpsOutput.model_validate(value)
    except ValidationError:
        return False
    return True


def tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


def token_f1(prediction: str, expected: str) -> float:
    pred = Counter(tokens(prediction))
    ref = Counter(tokens(expected))
    if not pred and not ref:
        return 1.0
    overlap = sum((pred & ref).values())
    if overlap == 0:
        return 0.0
    precision = overlap / sum(pred.values())
    recall = overlap / sum(ref.values())
    return 2 * precision * recall / (precision + recall)


def macro_f1(
    predicted: Iterable[str | None], expected: Iterable[str]
) -> float:
    predicted_list = list(predicted)
    expected_list = list(expected)
    scores: list[float] = []
    for label in SEVERITIES:
        tp = sum(
            pred == label and ref == label
            for pred, ref in zip(predicted_list, expected_list)
        )
        fp = sum(
            pred == label and ref != label
            for pred, ref in zip(predicted_list, expected_list)
        )
        fn = sum(
            pred != label and ref == label
            for pred, ref in zip(predicted_list, expected_list)
        )
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        score = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        scores.append(score)
    return mean(scores)


def percentile(values: list[float], quantile: float) -> float:
    if not values:
        return math.nan
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(quantile * len(ordered)) - 1))
    return ordered[index]


def calculate_metrics(records: list[dict[str, Any]]) -> dict[str, float | int]:
    if not records:
        raise ValueError("Aucune prediction a evaluer")

    parsed = [record.get("parsed_output") for record in records]
    expected = [record["expected_output"] for record in records]
    equipment_accuracy = mean(
        float(
            isinstance(pred, dict)
            and pred.get("equipment_id") == ref.get("equipment_id")
        )
        for pred, ref in zip(parsed, expected)
    )

    review_accuracy = mean(
        float(
            isinstance(pred, dict)
            and pred.get("requires_human_review")
            == ref.get("requires_human_review")
        )
        for pred, ref in zip(parsed, expected)
    )

    severity_score = macro_f1(
        [
            pred.get("severity") if isinstance(pred, dict) else None
            for pred in parsed
        ],
        [ref["severity"] for ref in expected],
    )

    text_scores = [
        (
            token_f1(str(pred.get(field, "")), str(ref.get(field, "")))
            if isinstance(pred, dict)
            else 0.0
        )
        for pred, ref in zip(parsed, expected)
        for field in TEXT_FIELDS
    ]
    lexical_score = mean(text_scores)
    latencies = [float(record["latency_seconds"]) for record in records]
    count = len(records)
    parseable = sum(isinstance(value, dict) for value in parsed) / count
    schema_valid = sum(bool(record.get("schema_valid")) for record in records) / count

    composite = 100 * mean(
        [parseable, schema_valid, equipment_accuracy, severity_score, review_accuracy, lexical_score]
    )
    return {
        "examples": count,
        "json_parseable_rate": parseable,
        "schema_valid_rate": schema_valid,
        "equipment_id_accuracy": equipment_accuracy,
        "severity_macro_f1": severity_score,
        "requires_human_review_accuracy": review_accuracy,
        "text_lexical_f1": lexical_score,
        "latency_median_seconds": percentile(latencies, 0.50),
        "latency_p95_seconds": percentile(latencies, 0.95),
        "throughput_examples_per_second": count / sum(latencies),
        "composite_score": composite,
    }
