"""Primitives de features ; les choix de modélisation restent à justifier."""

from __future__ import annotations

from collections import defaultdict
from statistics import mean, pstdev


def group_windows(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["window_id"]].append(row)
    return dict(grouped)


def numeric_summary(rows: list[dict[str, str]]) -> dict[str, float]:
    values: list[float] = []
    missing = 0
    for row in rows:
        try:
            values.append(float(row["value"]))
        except ValueError:
            missing += 1
    return {
        "value_mean": mean(values) if values else 0.0,
        "value_std": pstdev(values) if len(values) > 1 else 0.0,
        "missing_share": missing / len(rows) if rows else 0.0,
    }


def build_feature_table(rows: list[dict[str, str]]) -> list[dict[str, float | str]]:
    """Point de départ volontairement incomplet, agrégé par fenêtre."""
    return [
        {"window_id": window_id, **numeric_summary(window_rows)}
        for window_id, window_rows in sorted(group_windows(rows).items())
    ]
