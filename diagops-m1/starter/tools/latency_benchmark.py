"""Banc de mesure de latence controle : baseline contre candidat, en alternance.

Motivation
----------
Les latences relevees par `src/evaluate.py` se sont revelees instables : sur un
meme run, en donnees homogenes, la latence des 20 dernieres generations variait
de 0.44x a 2.33x celle des 20 premieres (GPU portable limite en enveloppe
thermique, frequences variables). Chaque systeme ayant ete mesure dans une
session distincte, les latences ne sont pas comparables entre elles.

Ce banc corrige la methode de mesure sans toucher aux seuils ni a la regle de
decision du protocole gele :

- les deux systemes sont charges simultanement et mesures dans la MEME session ;
- les generations alternent exemple par exemple, et l'ordre s'inverse a chaque
  tour, de sorte qu'une derive thermique frappe les deux systemes egalement ;
- un prechauffage precede les mesures, pour ecarter le cout de premiere passe ;
- la derive interne (premier tiers contre dernier tiers) est reportee, pour que
  la stabilite de la mesure soit verifiable et non supposee.

Le candidat est evalue adaptateur FUSIONNE (`merge_and_unload`), c'est-a-dire
dans l'etat ou il serait mis en service.

Usage
-----
    python -m tools.latency_benchmark \
        --config configs/baseline.yaml \
        --adapter work/runs/variation_1/adapter \
        --data work/splits/validation.jsonl \
        --examples 30 \
        --output work/evidence/latence_controlee.json
"""

from __future__ import annotations

import argparse
import json
import statistics as st
from pathlib import Path

from src.config import load_config
from src.dataset import load_jsonl
from src.metrics import percentile
from src.model_provider import ModelProvider


def resume(latences: list[float]) -> dict[str, float]:
    tiers = max(1, len(latences) // 3)
    debut, fin = st.mean(latences[:tiers]), st.mean(latences[-tiers:])
    return {
        "n": len(latences),
        "mediane_s": round(st.median(latences), 4),
        "moyenne_s": round(st.mean(latences), 4),
        "p95_s": round(percentile(latences, 0.95), 4),
        "min_s": round(min(latences), 4),
        "max_s": round(max(latences), 4),
        "premier_tiers_s": round(debut, 4),
        "dernier_tiers_s": round(fin, 4),
        "derive": round(fin / debut, 3),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--adapter", required=True, type=str)
    parser.add_argument("--data", required=True, type=Path)
    parser.add_argument("--examples", type=int, default=30)
    parser.add_argument("--warmup", type=int, default=3)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    config = load_config(args.config)
    rows = load_jsonl(args.data)[: args.examples]

    print("Chargement baseline (sans adaptateur)...", flush=True)
    base = ModelProvider(config=config, adapter_path=None)

    print("Chargement candidat (adaptateur fusionne)...", flush=True)
    cand = ModelProvider(config=config, adapter_path=args.adapter)
    merged = cand.model.merge_and_unload()
    merged.eval()
    cand.model = merged

    print(f"Prechauffage ({args.warmup} generations par systeme)...", flush=True)
    for row in rows[: args.warmup]:
        base.generate(row["input_text"], row.get("report_id"))
        cand.generate(row["input_text"], row.get("report_id"))

    lat_base: list[float] = []
    lat_cand: list[float] = []
    print(f"Mesure alternee sur {len(rows)} exemples...", flush=True)
    for index, row in enumerate(rows):
        # L'ordre s'inverse a chaque exemple : aucun systeme n'est
        # systematiquement mesure en premier.
        if index % 2 == 0:
            lat_base.append(base.generate(row["input_text"], row.get("report_id")).latency_seconds)
            lat_cand.append(cand.generate(row["input_text"], row.get("report_id")).latency_seconds)
        else:
            lat_cand.append(cand.generate(row["input_text"], row.get("report_id")).latency_seconds)
            lat_base.append(base.generate(row["input_text"], row.get("report_id")).latency_seconds)
        if (index + 1) % 10 == 0:
            print(f"  {index + 1}/{len(rows)}", flush=True)

    rb, rc = resume(lat_base), resume(lat_cand)
    rapport = {
        "methode": "mesure alternee, ordre inverse a chaque exemple, meme session",
        "model_id": config["model"]["id"],
        "model_revision": config["model"]["revision"],
        "adapter": args.adapter,
        "adapter_merged": True,
        "examples": len(rows),
        "warmup": args.warmup,
        "baseline": rb,
        "candidat": rc,
        "ratio_p95_candidat_sur_baseline": round(rc["p95_s"] / rb["p95_s"], 3),
        "ratio_mediane_candidat_sur_baseline": round(rc["mediane_s"] / rb["mediane_s"], 3),
        "latences_brutes": {"baseline": lat_base, "candidat": lat_cand},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(rapport, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print()
    print(f"{'':18s}{'baseline':>12s}{'candidat':>12s}")
    for cle in ("mediane_s", "p95_s", "premier_tiers_s", "dernier_tiers_s", "derive"):
        print(f"{cle:18s}{rb[cle]:12.3f}{rc[cle]:12.3f}")
    print()
    print(f"ratio p95 candidat/baseline : {rapport['ratio_p95_candidat_sur_baseline']}")
    print("seuils du protocole : retenue <= 1.20, rejet > 1.50")


if __name__ == "__main__":
    main()
