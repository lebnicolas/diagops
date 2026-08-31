"""Brief 2, étape 4, sens 2 — qualifier le lot de contrôle.

Le sens 1 a soumis nos fabrications au détecteur du module. Ce script fait
l'inverse : il applique **nos** règles à un lot dont la provenance est cachée.

La démarche tient en trois temps, dans cet ordre et jamais dans l'autre :

1. **calibrage** sur `control_sample.csv`, 720 lignes à provenance déclarée.
   Chaque règle y est mesurée dans les deux sens — ce qu'elle attrape et ce
   qu'elle accuse à tort ;
2. **verdict** sur `control_batch.csv`, 6 000 lignes, un verdict et une règle
   nommée par ligne ;
3. **contre-épreuve** : les règles de qualité du brief 1 sont appliquées au
   lot, pour établir combien de lignes authentiques elles accusent.

Le point de méthode central est la séparation des deux registres. `R-SEN-*`
répond à « cette ligne est-elle conforme au contrat », `R-DET-*` à « cette ligne
a-t-elle été fabriquée ». Les lignes authentiques du lot proviennent de la
livraison M3 et en portent les défauts : une règle de qualité qui signale une
mesure réelle ne se trompe pas sur la qualité, elle se trompe de question.

Usage :
    python run_verdicts_b2.py [--output ./output/detection]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.brief2.detection import (
    LOT_BATCH,
    LOT_SAMPLE,
    REGISTRE_DET,
    SEUIL_AC4,
    SEUIL_COINCIDENCE,
    SEUIL_GRILLE,
    SEUIL_NIVEAU_SIGMA,
    BORNES_DISPERSION,
    TAILLE_BLOC,
    _normaliser,
    charger_livraison,
    controles_qualite_par_ligne,
    correspondance,
    decouper_en_blocs,
    profil_equipements,
    signatures_par_bloc,
    verdicts_par_bloc,
)
from src.brief2.seed import SEED
from src.brief2.sources import load_prepared


WORK_ROOT = Path(__file__).resolve().parent


def qualifier(chemin: Path, livraison: pd.DataFrame, profil: pd.DataFrame) -> pd.DataFrame:
    """Chaîne complète appliquée à un lot : rapprochement, blocs, signatures, verdicts."""
    lot = _normaliser(pd.read_csv(chemin))
    lot = correspondance(lot, livraison)
    lot = decouper_en_blocs(lot)
    signatures = signatures_par_bloc(lot, profil)
    return lot, verdicts_par_bloc(signatures)


def calibrer(sortie: Path, livraison: pd.DataFrame, profil: pd.DataFrame) -> dict:
    """Mesure chaque règle sur l'échantillon à provenance déclarée."""
    lot, verdicts = qualifier(LOT_SAMPLE, livraison, profil)
    verite = (
        lot.groupby("bloc_id")["provenance"]
        .agg(lambda valeurs: valeurs.mode().iat[0])
        .rename("provenance_declaree")
    )
    table = verdicts.merge(verite, left_on="bloc_id", right_index=True)
    table["juste"] = table["verdict"] == table["provenance_declaree"]

    # Chaque règle de corroboration, mesurée dans les deux sens.
    mesures = []
    for code, libelle, portee in REGISTRE_DET:
        if portee != "corroboration":
            continue
        active = table["corroborations"].str.contains(code)
        fabriquees = table["provenance_declaree"] == "fabriquée"
        mesures.append(
            {
                "regle": code,
                "libelle": libelle,
                "blocs_signales": int(active.sum()),
                "dont_fabriques": int((active & fabriquees).sum()),
                "dont_reels_accuses": int((active & ~fabriquees).sum()),
                "blocs_fabriques_manques": int((~active & fabriquees).sum()),
            }
        )
    mesures = pd.DataFrame(mesures)
    mesures.to_csv(sortie / "calibrage_regles.csv", index=False, encoding="utf-8")
    table.to_csv(sortie / "calibrage_blocs.csv", index=False, encoding="utf-8")

    lignes = int(len(lot))
    justes = int(table.loc[table["juste"], "lignes"].sum())
    return {
        "lignes": lignes,
        "blocs": int(len(table)),
        "lignes_justes": justes,
        "part_juste": round(justes / lignes, 4),
        "blocs_faux": table.loc[~table["juste"], "bloc_id"].tolist(),
        "matrice": [
            {"provenance_declaree": declaree, "verdict": rendu, "lignes": int(nombre)}
            for (declaree, rendu), nombre in table.groupby(
                ["provenance_declaree", "verdict"]
            )["lignes"]
            .sum()
            .items()
        ],
        "regles": mesures.to_dict(orient="records"),
    }


def contre_epreuve(lot: pd.DataFrame, verdicts: pd.DataFrame, parc: set[str]) -> pd.DataFrame:
    """Confronte les règles de qualité du brief 1 aux verdicts d'authenticité."""
    controles = controles_qualite_par_ligne(lot, parc)
    verdict_par_ligne = lot["bloc_id"].map(
        verdicts.set_index("bloc_id")["verdict"]
    )
    lignes = []
    for regle in controles.columns:
        touchees = controles[regle]
        lignes.append(
            {
                "controle": regle,
                "lignes_signalees": int(touchees.sum()),
                "sur_lignes_reelles": int((touchees & (verdict_par_ligne == "réelle")).sum()),
                "sur_lignes_fabriquees": int(
                    (touchees & (verdict_par_ligne == "fabriquée")).sum()
                ),
                "sur_lignes_indecidables": int(
                    (touchees & (verdict_par_ligne == "indécidable")).sum()
                ),
            }
        )
    return pd.DataFrame(lignes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=WORK_ROOT / "output" / "detection"
    )
    args = parser.parse_args()
    sortie = args.output
    sortie.mkdir(parents=True, exist_ok=True)

    livraison = charger_livraison()
    profil = profil_equipements(livraison)
    parc = set(load_prepared()["equipment"]["equipment_id"])

    print("Calibrage sur control_sample.csv (720 lignes, provenance déclarée)")
    calibrage = calibrer(sortie, livraison, profil)
    print(
        f"  {calibrage['lignes_justes']}/{calibrage['lignes']} lignes correctement "
        f"classées ({calibrage['part_juste']:.1%}) sur {calibrage['blocs']} blocs"
    )
    for bloc in calibrage["blocs_faux"]:
        print(f"  bloc mal classé : {bloc}")
    print("\n  règles de corroboration — signalés / fabriqués / réels accusés / manqués")
    for mesure in calibrage["regles"]:
        print(
            f"    {mesure['regle']}  {mesure['blocs_signales']:>3} "
            f"{mesure['dont_fabriques']:>3} {mesure['dont_reels_accuses']:>3} "
            f"{mesure['blocs_fabriques_manques']:>3}   {mesure['libelle']}"
        )

    print("\nVerdicts sur control_batch.csv (6 000 lignes, provenance cachée)")
    lot, verdicts = qualifier(LOT_BATCH, livraison, profil)
    verdicts.to_csv(sortie / "verdicts_blocs.csv", index=False, encoding="utf-8")

    detail = lot[
        ["equipment_id", "timestamp", "sensor_name", "value", "unit", "period", "bloc_id"]
    ].copy()
    cle = verdicts.set_index("bloc_id")
    detail["verdict"] = detail["bloc_id"].map(cle["verdict"])
    detail["regle"] = detail["bloc_id"].map(cle["regle_decisive"])
    detail["corroborations"] = detail["bloc_id"].map(cle["corroborations"])
    detail.sort_values(["equipment_id", "sensor_name", "timestamp"]).to_csv(
        sortie / "verdicts_control_batch.csv", index=False, encoding="utf-8"
    )

    repartition = detail["verdict"].value_counts().to_dict()
    for verdict, nombre in sorted(repartition.items()):
        print(f"  {verdict:<12} {nombre:>5} lignes ({nombre / len(detail):.1%})")

    sans_signature = verdicts[
        (verdicts["verdict"] == "fabriquée") & (verdicts["corroborations"] == "")
    ]
    print(
        f"  blocs déclarés fabriqués sans aucune signature interne : "
        f"{len(sans_signature)} sur {(verdicts['verdict'] == 'fabriquée').sum()}"
    )

    print("\nContre-épreuve — règles de qualité du brief 1 appliquées au lot")
    epreuve = contre_epreuve(lot, verdicts, parc)
    epreuve.to_csv(sortie / "contre_epreuve_qualite.csv", index=False, encoding="utf-8")
    for _, ligne in epreuve.iterrows():
        if ligne["lignes_signalees"]:
            print(
                f"    {ligne['controle']:<42} {ligne['lignes_signalees']:>5} signalées, "
                f"dont {ligne['sur_lignes_reelles']:>4} authentiques"
            )

    synthese = {
        "graine": SEED,
        "taille_bloc": TAILLE_BLOC,
        "seuils": {
            "autocorrelation_cycle": SEUIL_AC4,
            "part_pas_irregulier": SEUIL_GRILLE,
            "ecart_niveau_sigma": SEUIL_NIVEAU_SIGMA,
            "bornes_dispersion": list(BORNES_DISPERSION),
            "coincidence": SEUIL_COINCIDENCE,
        },
        "registre": [
            {"regle": code, "libelle": libelle, "portee": portee}
            for code, libelle, portee in REGISTRE_DET
        ],
        "calibrage": calibrage,
        "lot": {
            "lignes": int(len(detail)),
            "blocs": int(len(verdicts)),
            "repartition": repartition,
            "blocs_fabriques_sans_signature": int(len(sans_signature)),
        },
        "contre_epreuve": epreuve.to_dict(orient="records"),
    }
    (sortie / "verdicts.json").write_text(
        json.dumps(synthese, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nSorties écrites dans {sortie}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
