"""Axe 5 du brief M3 — relier les mesures aux evenements.

Une mesure et un evenement ne partagent aucune cle : seul le couple
« equipement + temps » les rapproche. Le rapprochement repose donc entierement
sur une **fenetre d'observation**, qui est un choix a justifier et non un
parametre technique.

Ce script :
- construit le rapprochement sur la fenetre retenue ;
- controle sa cardinalite dans les deux sens, et mesure la duplication ;
- produit des agregats a un grain documente ;
- eprouve la sensibilite du resultat a la largeur de la fenetre.

Il ne construit ni modele ni relation de cause a effet — hors perimetre du brief.

Usage :
    python run_rapprochement_m3.py [--output ./output]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.data_pipeline.io import load_reference
from src.data_pipeline.timeseries import window_bounds

# Fenetre retenue, en heures. Justification detaillee dans
# docs/diagnostic_multisource.md — resume :
#
# - AVANT (48 h) : les trois episodes de vibration identifies a l'axe 3 montent
#   pendant 18 a 30 h avant l'incident declare. 48 h couvre les trois avec de la
#   marge, soit 8 releves au pas de 6 h.
# - APRES (24 h) : ces memes episodes retombent au niveau nominal en 12 a 24 h.
#
# La fenetre part du DEBUT de l'evenement et se termine apres sa FIN : un
# evenement dure 19 h en mediane, l'ignorer amputerait la moitie des cas.
BEFORE_HOURS = 48.0
AFTER_HOURS = 24.0

# Fenetres comparees pour eprouver la sensibilite du resultat.
SENSITIVITY_WINDOWS = [(12.0, 6.0), (24.0, 12.0), (48.0, 24.0), (72.0, 48.0), (168.0, 72.0)]


def load_measurements(output: Path) -> pd.DataFrame:
    """Mesures preparees par l'axe 4, pas les mesures brutes."""
    frame = pd.read_csv(output / "processed" / "sensor_readings.csv")
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True)
    return frame


def match(
    measurements: pd.DataFrame, events: pd.DataFrame, before: float, after: float
) -> pd.DataFrame:
    """Rapproche chaque mesure des evenements dont la fenetre la contient.

    Jointure par equipement puis filtre temporel. Une mesure peut tomber dans
    plusieurs fenetres — c'est un fait a mesurer, pas a masquer.
    """
    bounded = window_bounds(events, before, after)
    columns = [
        "event_id",
        "equipment_id",
        "event_type",
        "severity",
        "window_start",
        "window_end",
    ]
    joined = measurements.merge(
        bounded.loc[:, columns], on="equipment_id", how="inner", suffixes=("", "_event")
    )
    inside = joined[
        (joined["timestamp"] >= joined["window_start"])
        & (joined["timestamp"] <= joined["window_end"])
    ]
    return inside.copy()


def cardinality(
    measurements: pd.DataFrame, events: pd.DataFrame, matched: pd.DataFrame
) -> dict:
    """Controle la cardinalite dans les deux sens et la duplication."""
    instrumented = set(measurements["equipment_id"])
    events_on_instrumented = events[events["equipment_id"].isin(instrumented)]

    per_event = matched.groupby("event_id", observed=True).size()
    matched_events = set(matched["event_id"])

    # Une mesure est identifiee par son `row_identifier` : c'est ce qui permet
    # de savoir si elle a ete comptee plusieurs fois.
    distinct_measures = matched["row_identifier"].nunique()
    duplication = len(matched) / distinct_measures if distinct_measures else 0.0
    per_measure = matched.groupby("row_identifier", observed=True).size()

    return {
        "fenetre_heures": {"avant": BEFORE_HOURS, "apres": AFTER_HOURS},
        "evenements": {
            "total": int(len(events)),
            "sur_equipement_instrumente": int(len(events_on_instrumented)),
            "sur_equipement_non_instrumente": int(len(events) - len(events_on_instrumented)),
            "avec_au_moins_une_mesure": int(len(matched_events)),
            "sans_aucune_mesure": int(len(events) - len(matched_events)),
            "sans_mesure_bien_qu_instrumente": int(
                len(set(events_on_instrumented["event_id"]) - matched_events)
            ),
        },
        "mesures_par_evenement": {
            "min": int(per_event.min()) if not per_event.empty else 0,
            "mediane": int(per_event.median()) if not per_event.empty else 0,
            "moyenne": round(float(per_event.mean()), 1) if not per_event.empty else 0.0,
            "max": int(per_event.max()) if not per_event.empty else 0,
        },
        "mesures": {
            "preparees": int(len(measurements)),
            "dans_au_moins_une_fenetre": int(distinct_measures),
            "hors_de_toute_fenetre": int(len(measurements) - distinct_measures),
            "part_appariee_pct": round(100 * distinct_measures / len(measurements), 2),
        },
        "duplication": {
            "lignes_de_rapprochement": int(len(matched)),
            "mesures_distinctes": int(distinct_measures),
            "facteur": round(float(duplication), 4),
            "mesures_dans_plusieurs_fenetres": int((per_measure > 1).sum()),
            "appartenance_maximale": int(per_measure.max()) if not per_measure.empty else 0,
        },
    }


def aggregate(matched: pd.DataFrame) -> pd.DataFrame:
    """Agregats au grain (evenement x equipement x capteur).

    Grain retenu parce que c'est le plus fin qui reste exploitable en aval : un
    enregistrement par capteur et par evenement. Ce que ce grain fait perdre est
    documente dans le diagnostic.
    """
    grouped = matched.groupby(
        ["event_id", "equipment_id", "sensor_name", "event_type", "severity"],
        observed=True,
    )
    aggregates = grouped.agg(
        mesures=("value", "size"),
        mesures_renseignees=("value", "count"),
        minimum=("value", "min"),
        maximum=("value", "max"),
        moyenne=("value", "mean"),
        ecart_type=("value", "std"),
        premiere_mesure=("timestamp", "min"),
        derniere_mesure=("timestamp", "max"),
    ).reset_index()
    aggregates["completude_pct"] = (
        100 * aggregates["mesures_renseignees"] / aggregates["mesures"]
    ).round(2)
    numeric = ["minimum", "maximum", "moyenne", "ecart_type"]
    aggregates[numeric] = aggregates[numeric].round(3)
    return aggregates


def sensitivity(measurements: pd.DataFrame, events: pd.DataFrame) -> list[dict]:
    """Effet de la largeur de fenetre sur le resultat.

    Une fenetre est un choix : montrer comment le resultat bouge quand elle
    change est la seule facon de dire si ce choix est determinant ou non.
    """
    rows = []
    for before, after in SENSITIVITY_WINDOWS:
        matched = match(measurements, events, before, after)
        distinct = matched["row_identifier"].nunique()
        per_event = matched.groupby("event_id", observed=True).size()
        rows.append(
            {
                "avant_h": before,
                "apres_h": after,
                "evenements_apparies": int(matched["event_id"].nunique()),
                "mesures_appariees": int(distinct),
                "part_mesures_pct": round(100 * distinct / len(measurements), 2),
                "mediane_mesures_par_evenement": int(per_event.median())
                if not per_event.empty
                else 0,
                "facteur_duplication": round(len(matched) / distinct, 3) if distinct else 0.0,
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output"))
    args = parser.parse_args()
    out = args.output
    (out / "alignment").mkdir(parents=True, exist_ok=True)
    (out / "aggregates").mkdir(parents=True, exist_ok=True)

    measurements = load_measurements(out)
    events = load_reference()["events"]

    matched = match(measurements, events, BEFORE_HOURS, AFTER_HOURS)
    report = cardinality(measurements, events, matched)
    aggregates = aggregate(matched)
    report["agregats"] = {
        "grain": "event_id x equipment_id x sensor_name",
        "lignes": int(len(aggregates)),
        "completude_mediane_pct": float(aggregates["completude_pct"].median()),
        "evenements_couverts": int(aggregates["event_id"].nunique()),
    }
    report["sensibilite_fenetre"] = sensitivity(measurements, events)

    matched.loc[
        :,
        [
            "event_id",
            "equipment_id",
            "sensor_name",
            "timestamp",
            "value",
            "unit",
            "row_identifier",
            "event_type",
            "severity",
            "window_start",
            "window_end",
        ],
    ].to_csv(out / "alignment" / "mesures_evenements.csv", index=False)
    aggregates.to_csv(out / "aggregates" / "agregats_par_evenement.csv", index=False)

    # Les evenements sans aucune mesure sont un livrable en soi : ils bornent ce
    # qu'un apprentissage supervise pourra voir.
    unmatched = events[~events["event_id"].isin(set(matched["event_id"]))]
    unmatched = unmatched.assign(
        equipement_instrumente=unmatched["equipment_id"].isin(set(measurements["equipment_id"]))
    )
    unmatched.to_csv(out / "alignment" / "evenements_sans_mesure.csv", index=False)

    (out / "rapprochement_m3.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"\nSorties ecrites dans {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
