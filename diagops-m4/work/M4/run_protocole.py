"""Étape 2 du brief 1 M4 — geler le protocole avant toute modélisation.

Produit la partition, le contrôle de fuite, la baseline mesurée aux deux
niveaux et les empreintes du point de départ. Rien de ce qui est écrit ici ne
doit changer après consultation du test : c'est l'objet du gel.

Usage :
    python run_protocole.py [--output ./results/protocole]
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.protocole import (
    CLASSE_POSITIVE,
    COLONNE_GROUPE,
    N_PLIS,
    N_REPETITIONS,
    SEED,
    baseline_deux_niveaux,
    charger_calibration,
    commit_courant,
    empreintes,
    environnement,
    plis,
    table_fenetres,
    verifier_absence_de_fuite,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="./results/protocole", type=Path)
    arguments = parser.parse_args()

    sortie: Path = arguments.output
    sortie.mkdir(parents=True, exist_ok=True)

    lignes = charger_calibration()
    fenetres = table_fenetres(lignes)

    print("Point de départ")
    print(f"  lignes de calibration      {len(lignes)}")
    print(f"  fenêtres                   {len(fenetres)}")
    print(f"  dont fabriquées            {int(fenetres['y'].sum())}")
    print(f"  équipements                {fenetres[COLONNE_GROUPE].nunique()}")
    melanges = (
        fenetres.groupby(COLONNE_GROUPE)["provenance"].nunique().gt(1).sum()
    )
    print(f"  équipements aux 2 provenances  {melanges}")

    print("\nRépartition par capteur")
    croisement = pd.crosstab(fenetres["sensor_name"], fenetres["provenance"])
    print(croisement.to_string())

    decoupes = plis(fenetres)
    fuite = verifier_absence_de_fuite(fenetres, decoupes)

    print(f"\nPartition — {N_PLIS} plis stratifiés × {N_REPETITIONS} répétitions")
    print(f"  plis produits              {fuite['plis']}")
    print(f"  groupés sur                {COLONNE_GROUPE}")
    print(f"  taille de validation       {fuite['taille_validation_min']} à {fuite['taille_validation_max']}")
    print(f"  positifs en validation     {fuite['positifs_validation_min']} à {fuite['positifs_validation_max']}")
    print(f"  plis sans aucun positif    {fuite['plis_de_validation_sans_positif']}")
    print(f"  sans fuite d'équipement    {fuite['sans_fuite']}")
    if not fuite["sans_fuite"]:
        for faute in fuite["equipements_traversant_un_pli"]:
            print(f"    {faute}")
        raise SystemExit("fuite détectée — protocole non gelable")

    baseline = baseline_deux_niveaux()
    print("\nBaseline M3 figée — la barre à battre")
    entete = f"  {'niveau':<10} {'n':>5} {'VP':>4} {'FP':>4} {'FN':>4} {'précision':>10} {'rappel':>8} {'F1':>8}"
    print(entete)
    for niveau in ("par_ligne", "par_fenetre"):
        s = baseline[niveau]
        print(
            f"  {niveau.replace('par_', ''):<10} {s['n']:>5} {s['vrai_positif']:>4} "
            f"{s['faux_positif']:>4} {s['faux_negatif']:>4} {s['precision']:>10.3f} "
            f"{s['rappel']:>8.3f} {s['f1']:>8.3f}"
        )
    print("\n  F1 par seuil d'agrégation :", baseline["f1_par_seuil_agregation"])

    reference = json.loads(
        (
            Path("../../data_pack/2026-S1/reference_runs/m3_for_m4")
            / "baseline_metrics_calibration.json"
        ).read_text(encoding="utf-8")
    )
    ecart = abs(reference["f1_fabricated"] - baseline["par_ligne"]["f1"])
    print(f"\n  F1 officiel {reference['f1_fabricated']} — reproduit {baseline['par_ligne']['f1']} — écart {ecart:.6f}")
    if ecart > 1e-6:
        raise SystemExit("la baseline reproduite diverge de la référence — gel refusé")

    gel = {
        "date_de_gel": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "commit": commit_courant(),
        "graine": SEED,
        "cible": "provenance",
        "classe_positive": CLASSE_POSITIVE,
        "unite_de_decision": "fenêtre (window_id), avec report au niveau ligne",
        "metrique_de_decision": "F1 sur la classe fabriquée",
        "metriques_rapportees": [
            "precision", "rappel", "f1", "roc_auc", "matrice de confusion",
            "stabilite par segment", "latence", "memoire",
        ],
        "partition": {
            "methode": "StratifiedGroupKFold",
            "groupe": COLONNE_GROUPE,
            "plis": N_PLIS,
            "repetitions": N_REPETITIONS,
            "controle_de_fuite": fuite,
        },
        "baseline": baseline,
        "environnement": environnement(),
        "empreintes": empreintes(),
        "fenetres": fenetres.to_dict(orient="records"),
    }
    (sortie / "protocole.json").write_text(
        json.dumps(gel, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )

    partition = pd.DataFrame(
        [
            {
                "repetition": d.repetition,
                "pli": d.pli,
                "window_id": fenetre,
                "role": role,
            }
            for d in decoupes
            for role, fenetres_du_role in (
                ("entrainement", d.entrainement), ("validation", d.validation)
            )
            for fenetre in fenetres_du_role
        ]
    )
    partition.to_csv(sortie / "partition.csv", index=False, encoding="utf-8")
    fenetres.to_csv(sortie / "fenetres.csv", index=False, encoding="utf-8")

    print(f"\nProtocole gelé — sorties dans {sortie}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
