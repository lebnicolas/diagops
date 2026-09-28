#!/usr/bin/env python3
"""Applique les contrôles de référence M2 et M3 à un fichier de mesures.

Cet outil est un détecteur de référence, pas un oracle. Il retourne des
**comptages par famille de règle** et ne désigne jamais les lignes concernées :
il indique qu'une population est irrégulière, pas laquelle.

Son périmètre est celui des contrôles établis en M2 et M3 : schéma, format
d'horodatage, grille d'échantillonnage, plage physique, cohérence entre le nom
du capteur et son unité, unicité de la clé logique, intégrité référentielle,
convention de précision et conformité des distributions marginales à la
livraison de référence.

Il ne contrôle ni la structure temporelle des séries, ni leur cohérence avec
`events.csv` et `maintenance_history.csv`. Ces deux angles sont hors de son
périmètre et sont rappelés à chaque exécution.

Usage :

    python tools/verify_synthetic.py --input <fichier_de_mesures.csv>
    python tools/verify_synthetic.py --input <fichier.csv> --json
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "data_pack" / "2026-S1"
REFERENCE = PACK / "sensors" / "sensor_readings.csv"
EQUIPMENT = PACK / "equipment" / "equipment.csv"

REQUIRED_COLUMNS = ["equipment_id", "timestamp", "sensor_name", "value", "unit", "period"]
OPTIONAL_COLUMNS = ["provenance", "procedure_id"]

PERIOD = "2026-S1"
STEP_HOURS = 6
PERIOD_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
PERIOD_END = datetime(2026, 7, 1, tzinfo=timezone.utc)
DECIMALS = 2

SENSOR_RANGE = {
    "vibration_mm_s": (0.0, 12.0),
    "temperature_c": (-20.0, 140.0),
    "pressure_bar": (0.0, 25.0),
    "current_a": (0.0, 120.0),
    "rpm": (0.0, 3000.0),
}
EXPECTED_UNIT = {
    "vibration_mm_s": "mm/s",
    "temperature_c": "°C",
    "pressure_bar": "bar",
    "current_a": "A",
    "rpm": "rpm",
}
SENTINELS = {"-999", "-9999", "9999", "999999"}

RULES = [
    ("R-SCHEMA", "colonne absente, capteur inconnu ou valeur non numérique"),
    ("R-FORMAT", "horodatage non ISO-UTC, hors grille de 6 h ou hors période"),
    ("R-RANGE", "valeur absente, sentinelle ou hors plage physique"),
    ("R-UNIT", "unité incohérente avec le nom du capteur"),
    ("R-KEY", "clé logique équipement + horodatage + capteur non unique"),
    ("R-FK", "équipement absent de equipment.csv"),
    ("R-PRECISION", "précision décimale hors convention de la livraison"),
]

# R-DISTRIB ne se compte pas en lignes : une marginale s'apprécie sur une
# population entière. La règle est évaluée capteur par capteur.
DISTRIB_RULE = ("R-DISTRIB", "distribution marginale éloignée de la référence")

OUT_OF_SCOPE = [
    "structure temporelle des séries : autocorrélation, cycle journalier, "
    "distribution des écarts successifs",
    "cohérence avec events.csv et maintenance_history.csv : présence ou absence "
    "de signature capteur en regard des événements sévères",
]


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def parse_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def numeric(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def decimals_of(value: str) -> int:
    return len(value.split(".", 1)[1]) if "." in value else 0


def reference_profile(path: Path) -> dict[str, dict[str, float]]:
    """Moyenne et écart-type par capteur, calculés sur les lignes régulières."""
    values: dict[str, list[float]] = defaultdict(list)
    for row in read_csv(path):
        sensor = row["sensor_name"].strip().lower()
        if sensor not in SENSOR_RANGE:
            continue
        if row["unit"] != EXPECTED_UNIT[sensor]:
            continue
        parsed = numeric(row["value"])
        low, high = SENSOR_RANGE[sensor]
        if parsed is None or not low <= parsed <= high:
            continue
        values[sensor].append(parsed)
    return {
        sensor: {
            "mean": statistics.fmean(series),
            "stdev": statistics.pstdev(series),
            "count": len(series),
        }
        for sensor, series in sorted(values.items())
        if len(series) >= 30
    }


def analyse(rows: list[dict], columns: list[str], profile: dict, park: set[str]) -> dict:
    flags: dict[str, int] = {rule: 0 for rule, _ in RULES}
    flagged_sensors: list[str] = []
    missing_columns = [name for name in REQUIRED_COLUMNS if name not in columns]
    extra_columns = [
        name
        for name in columns
        if name not in REQUIRED_COLUMNS and name not in OPTIONAL_COLUMNS
    ]

    seen: Counter[tuple[str, str, str]] = Counter()
    by_sensor: dict[str, list[float]] = defaultdict(list)
    sensors = Counter()
    periods = Counter()
    moments: list[datetime] = []

    for row in rows:
        sensor_raw = row.get("sensor_name", "")
        sensor = sensor_raw.strip().lower()
        sensors[sensor_raw] += 1
        periods[row.get("period", "")] += 1
        value_raw = row.get("value", "")
        parsed_value = numeric(value_raw)

        if missing_columns or sensor not in SENSOR_RANGE or (
            value_raw not in ("",) and parsed_value is None
        ):
            flags["R-SCHEMA"] += 1

        moment = parse_timestamp(row.get("timestamp", ""))
        if moment is None:
            flags["R-FORMAT"] += 1
        else:
            moments.append(moment)
            off_grid = moment.hour % STEP_HOURS or moment.minute or moment.second
            outside = not PERIOD_START <= moment < PERIOD_END
            if off_grid or outside:
                flags["R-FORMAT"] += 1

        if value_raw == "" or value_raw in SENTINELS:
            flags["R-RANGE"] += 1
        elif parsed_value is not None and sensor in SENSOR_RANGE:
            low, high = SENSOR_RANGE[sensor]
            if not low <= parsed_value <= high:
                flags["R-RANGE"] += 1
            else:
                by_sensor[sensor].append(parsed_value)

        if sensor in EXPECTED_UNIT and row.get("unit", "") != EXPECTED_UNIT[sensor]:
            flags["R-UNIT"] += 1

        seen[
            (row.get("equipment_id", ""), row.get("timestamp", ""), sensor_raw)
        ] += 1

        if park and row.get("equipment_id", "") not in park:
            flags["R-FK"] += 1

        if value_raw and parsed_value is not None and decimals_of(value_raw) > DECIMALS + 1:
            flags["R-PRECISION"] += 1

    flags["R-KEY"] = sum(count - 1 for count in seen.values() if count > 1)

    # R-DISTRIB : un capteur est signalé en bloc si sa marginale s'écarte de la
    # livraison de référence. Le comptage porte sur les lignes du capteur.
    distribution: list[dict] = []
    for sensor, series in sorted(by_sensor.items()):
        expected = profile.get(sensor)
        if expected is None or len(series) < 30:
            continue
        mean = statistics.fmean(series)
        stdev = statistics.pstdev(series)
        mean_gap = abs(mean - expected["mean"]) / (expected["stdev"] or 1.0)
        ratio = stdev / expected["stdev"] if expected["stdev"] else 1.0
        flagged = mean_gap > 0.8 or not 0.7 <= ratio <= 1.45
        if flagged:
            flagged_sensors.append(sensor)
        distribution.append(
            {
                "sensor_name": sensor,
                "rows": len(series),
                "mean": round(mean, 3),
                "reference_mean": round(expected["mean"], 3),
                "mean_gap_in_reference_stdev": round(mean_gap, 3),
                "stdev_ratio": round(ratio, 3),
                "flagged": flagged,
            }
        )

    return {
        "rows": len(rows),
        "columns": columns,
        "missing_columns": missing_columns,
        "unexpected_columns": extra_columns,
        "declares_provenance": "provenance" in columns,
        "distinct_series": len(
            {(row.get("equipment_id", ""), row.get("sensor_name", "")) for row in rows}
        ),
        "sensor_names": dict(sensors),
        "periods": dict(periods),
        "timestamp_span": [
            min(moments).strftime("%Y-%m-%dT%H:%M:%SZ") if moments else None,
            max(moments).strftime("%Y-%m-%dT%H:%M:%SZ") if moments else None,
        ],
        "flagged_rows_by_rule": flags,
        "flagged_rows_total": sum(flags.values()),
        "flagged_sensors_by_distribution": flagged_sensors,
        "distribution": distribution,
        "out_of_scope": OUT_OF_SCOPE,
    }


def render(report: dict, source: Path) -> str:
    lines = [
        f"Détecteur de référence M2/M3 — {source.name}",
        "",
        f"Lignes analysées      : {report['rows']}",
        f"Séries distinctes     : {report['distinct_series']}",
        f"Fenêtre d'horodatage  : {report['timestamp_span'][0]} → {report['timestamp_span'][1]}",
        f"Colonne provenance    : {'présente' if report['declares_provenance'] else 'absente'}",
    ]
    if report["missing_columns"]:
        lines.append(f"Colonnes absentes     : {', '.join(report['missing_columns'])}")
    if report["unexpected_columns"]:
        lines.append(f"Colonnes inattendues  : {', '.join(report['unexpected_columns'])}")

    lines += ["", "Lignes signalées par famille de règle", ""]
    width = max(len(rule) for rule, _ in RULES)
    for rule, label in RULES:
        count = report["flagged_rows_by_rule"][rule]
        share = count / report["rows"] if report["rows"] else 0.0
        lines.append(f"  {rule:<{width}}  {count:>7}  {share:6.2%}  {label}")

    flagged = report["flagged_sensors_by_distribution"]
    lines += [
        "",
        f"Total                 : {report['flagged_rows_total']} signalements "
        f"(une ligne peut l'être par plusieurs règles)",
        "",
        f"{DISTRIB_RULE[0]} — {DISTRIB_RULE[1]} : "
        f"{len(flagged)} capteur(s) sur {len(report['distribution'])} signalé(s)",
        "",
        f"  {'capteur':<16} {'lignes':>7} {'moyenne':>10} {'référence':>10} "
        f"{'écart/σ':>8} {'ratio σ':>8}  état",
    ]
    for item in report["distribution"]:
        state = "signalé" if item["flagged"] else "conforme"
        lines.append(
            f"  {item['sensor_name']:<16} {item['rows']:>7} {item['mean']:>10.2f} "
            f"{item['reference_mean']:>10.2f} "
            f"{item['mean_gap_in_reference_stdev']:>8.2f} "
            f"{item['stdev_ratio']:>8.2f}  {state}"
        )

    lines += ["", "Hors périmètre de ce détecteur", ""]
    for item in OUT_OF_SCOPE:
        lines.append(f"  - {item}")
    lines += [
        "",
        "Un fichier qui ne déclenche aucune règle n'est pas pour autant réaliste :",
        "il est seulement conforme aux contrôles ci-dessus.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Contrôles de référence M2 et M3 sur un fichier de mesures."
    )
    parser.add_argument("--input", required=True, type=Path, help="fichier CSV à contrôler")
    parser.add_argument(
        "--reference",
        type=Path,
        default=REFERENCE,
        help="livraison de référence pour les distributions marginales",
    )
    parser.add_argument("--json", action="store_true", help="sortie machine")
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"Fichier introuvable : {args.input}", file=sys.stderr)
        return 2

    with args.input.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        columns = list(reader.fieldnames or [])
        rows = list(reader)

    if not rows:
        print("Fichier vide : aucun contrôle applicable.", file=sys.stderr)
        return 2

    profile = reference_profile(args.reference) if args.reference.is_file() else {}
    park = (
        {row["equipment_id"] for row in read_csv(EQUIPMENT)}
        if EQUIPMENT.is_file()
        else set()
    )

    report = analyse(rows, columns, profile, park)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(render(report, args.input))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
