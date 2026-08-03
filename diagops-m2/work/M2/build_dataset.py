"""Construit le jeu supervise a partir des tables preparees M2.

    python build_dataset.py [--input output/processed] [--output output/training]

A lancer APRES `run_audit_m2.py` : il consomme les tables preparees, jamais
les fichiers recus.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.data_pipeline.dataset import FEATURES, TARGET, build_training_set


HERE = Path(__file__).resolve().parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Jeu supervise DiagOps — cible severity.")
    parser.add_argument("--input", type=Path, default=HERE / "output" / "processed")
    parser.add_argument("--output", type=Path, default=HERE / "output" / "training")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    frames = {
        "equipment": pd.read_csv(args.input / "equipment.csv"),
        "events": pd.read_csv(args.input / "events.csv"),
        "maintenance": pd.read_csv(args.input / "maintenance_history.csv"),
    }
    print(f"Tables preparees lues depuis {args.input}")

    resultat = build_training_set(frames, seed=args.seed)

    args.output.mkdir(parents=True, exist_ok=True)
    for name, frame in resultat.splits.items():
        path = args.output / f"{name}.csv"
        frame.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")
        print(f"  {name:12s} {len(frame):4d} lignes  {len(frame['equipment_id'].unique()):4d} equipements  -> {path.name}")

    if len(resultat.excluded_rows):
        path = args.output / "exclusions.csv"
        resultat.excluded_rows.to_csv(path, index=False, encoding="utf-8", lineterminator="\n")
        print(f"  exclusions   {len(resultat.excluded_rows):4d} lignes  -> {path.name}")

    print(f"\nVariables ({len(FEATURES)}) : {', '.join(FEATURES)}")
    print(f"Cible : {TARGET}")

    print("\nRepartition de la cible par paquet :")
    for name, frame in resultat.splits.items():
        parts = (frame[TARGET].value_counts(normalize=True) * 100).round(1)
        print(f"  {name:12s} " + " · ".join(f"{k} {v}%" for k, v in parts.items()))

    print("\nScores de reference a battre (mesures sur le test) :")
    for nom, score in resultat.baselines.items():
        print(f"  {nom:24s} {score:.4f}")

    # Garde-fou : aucun equipement partage entre les paquets.
    ids = {name: set(f["equipment_id"]) for name, f in resultat.splits.items()}
    chevauchement = (
        (ids["train"] & ids["test"]) | (ids["train"] & ids["validation"]) | (ids["validation"] & ids["test"])
    )
    if chevauchement:
        raise SystemExit(f"ECHEC : equipements partages entre paquets — {sorted(chevauchement)[:5]}")
    print("\nAucun equipement partage entre les paquets : controle reussi.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
