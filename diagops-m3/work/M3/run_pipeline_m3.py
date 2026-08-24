"""Axe 4 du brief M3 — pipeline multi-source rejouable.

Applique les regles capteurs, produit les tables preparees des quatre sources,
assemble la quarantaine unifiee, ecrit le registre des regles et controle la
non-regression sur les trois tables heritees de M2.

Usage :
    python run_pipeline_m3.py [--output ./output]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.data_pipeline.io import load_reference, load_sources
from src.data_pipeline.quarantine import merge_quarantines
from src.pipeline_m3 import build_registry, check_no_regression, prepare_sensors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output"))
    args = parser.parse_args()
    out = args.output
    (out / "processed").mkdir(parents=True, exist_ok=True)

    sources = load_sources()
    reference = load_reference()

    # Les trois tables M2 sont reprises telles quelles depuis la reference : le
    # point de depart acte est l'etat prepare, pas les fichiers bruts.
    inherited = {
        name: reference[name] for name in ("equipment", "events", "maintenance")
    }
    park = set(inherited["equipment"]["equipment_id"])

    prepared, sensor_quarantine, stats = prepare_sensors(sources["sensors"], park)

    # Ecriture des quatre tables preparees.
    inherited["equipment"].to_csv(out / "processed" / "equipment.csv", index=False)
    inherited["events"].to_csv(out / "processed" / "events.csv", index=False)
    inherited["maintenance"].to_csv(
        out / "processed" / "maintenance_history.csv", index=False
    )
    prepared.to_csv(out / "processed" / "sensor_readings.csv", index=False)

    # Quarantaine unifiee : les rejets M2 de la reference et ceux des mesures
    # partagent le meme format et le meme vocabulaire de decision.
    m2_quarantine = reference["quarantine"]
    unified = merge_quarantines(m2_quarantine, sensor_quarantine)
    unified.to_csv(out / "quarantine.csv", index=False)

    # Non-regression : on relit ce qui vient d'etre ecrit, on le compare a
    # l'entree. Relire plutot que comparer en memoire fait passer le controle
    # par le meme aller-retour CSV que les consommateurs en aval.
    produced = {
        "equipment": pd.read_csv(out / "processed" / "equipment.csv"),
        "events": pd.read_csv(out / "processed" / "events.csv"),
        "maintenance": pd.read_csv(out / "processed" / "maintenance_history.csv"),
    }
    regression = check_no_regression(inherited, produced)

    registry = build_registry()
    registry_frame = registry.to_frame()
    registry_frame.to_csv(out / "registre_regles.csv", index=False)

    resume = {
        "sources": {
            "sensors_recues": int(len(sources["sensors"])),
            "equipment": int(len(inherited["equipment"])),
            "events": int(len(inherited["events"])),
            "maintenance": int(len(inherited["maintenance"])),
        },
        "regles": {
            "total": int(len(registry.rules)),
            "heritees_M2": int(sum(1 for r in registry.rules if r.origin == "M2")),
            "ajoutees_M3": int(sum(1 for r in registry.rules if r.origin == "M3")),
            "par_statut": {
                statut: int(sum(1 for r in registry.rules if r.status == statut))
                for statut in sorted({r.status for r in registry.rules})
            },
            "actives": int(len(registry.active())),
        },
        "mesures": stats,
        "quarantaine_unifiee": {
            "total": int(len(unified)),
            "heritee_M2": int(len(m2_quarantine)),
            "ajoutee_M3": int(len(sensor_quarantine)),
            "par_decision": {
                str(k): int(v) for k, v in unified["decision"].value_counts().items()
            },
            "par_source": {
                str(k): int(v) for k, v in unified["source_file"].value_counts().items()
            },
        },
        "non_regression": regression,
    }
    (out / "pipeline_m3.json").write_text(
        json.dumps(resume, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(resume, indent=2, ensure_ascii=False))

    if not regression["non_regression"]:
        print("\nECHEC : les tables M2 ne sont pas restituees a l'identique.")
        return 1
    print(f"\nSorties ecrites dans {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
