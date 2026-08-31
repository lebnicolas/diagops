"""Brief 2, étape 5 — protéger un agrégat trop peu fourni.

Agrégat retenu (arbitrage A4) : le **coût moyen des pièces par site et par
criticité**, seize cellules, effectifs de 4 à 319 interventions.

Le script produit trois choses, dans cet ordre :

1. le **tableau vrai**, avec pour chaque cellule son effectif, sa moyenne, et le
   biais introduit par le bornage des coûts ;
2. l'effet de **cinq budgets** `ε` sur chaque cellule, mesuré sur 2 000 tirages —
   un tirage unique ne dit rien d'un mécanisme aléatoire ;
3. l'effet de **trois plafonds de bornage**, qui montre que la sensibilité n'est
   pas une donnée du problème mais une décision de conception.

La conclusion attendue porte sur les deux bornes : à partir de quel budget le
chiffre publié cesse d'être exploitable, et à partir duquel il cesse de protéger.

Usage :
    python run_confidentialite_b2.py [--output ./output/confidentialite]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.brief2.privacy import (
    EPSILONS,
    PART_SOMME,
    PLAFOND_RETENU,
    PLAFONDS,
    TIRAGES,
    TOLERANCE_ATTAQUE_EUR,
    attaque_par_differenciation,
    agregat_reference,
    mesurer,
    publier_moyenne,
    sensibilites,
)
from src.brief2.seed import SEED, rng
from src.brief2.sources import load_prepared


WORK_ROOT = Path(__file__).resolve().parent


def interventions_situees() -> pd.DataFrame:
    """Interventions enrichies du site et de la criticité de leur équipement."""
    tables = load_prepared()
    maintenance = tables["maintenance"].copy()
    maintenance["parts_cost_eur"] = pd.to_numeric(
        maintenance["parts_cost_eur"], errors="coerce"
    )
    return maintenance.merge(
        tables["equipment"][["equipment_id", "site_id", "criticality"]],
        on="equipment_id",
        how="left",
    )


def balayer_budgets(
    interventions: pd.DataFrame, reference: pd.DataFrame, plafond: float
) -> pd.DataFrame:
    """Mesure chaque cellule sous chaque budget."""
    globale = float(
        np.clip(interventions["parts_cost_eur"].dropna(), 0.0, plafond).mean()
    )
    lignes = []
    for rang, (_, cellule) in enumerate(reference.iterrows()):
        valeurs = (
            interventions.loc[
                (interventions["site_id"] == cellule["site_id"])
                & (interventions["criticality"] == cellule["criticality"]),
                "parts_cost_eur",
            ]
            .dropna()
            .to_numpy(dtype=float)
        )
        for index, epsilon in enumerate(EPSILONS):
            publiees = publier_moyenne(
                valeurs,
                epsilon,
                plafond,
                rng(offset=500 + rang * len(EPSILONS) + index),
            )
            mesures = mesurer(publiees, cellule["cout_moyen_borne"], plafond, globale)
            lignes.append(
                {
                    "site_id": cellule["site_id"],
                    "criticality": cellule["criticality"],
                    "effectif": cellule["effectif"],
                    "cout_moyen_borne": cellule["cout_moyen_borne"],
                    "epsilon": epsilon,
                    "echelle_bruit_somme": round(
                        sensibilites(plafond)["somme"] / (epsilon * PART_SOMME), 1
                    ),
                    **mesures,
                }
            )
    return pd.DataFrame(lignes)


def comparer_plafonds(interventions: pd.DataFrame, epsilon: float) -> pd.DataFrame:
    """Effet du plafond de bornage, à budget fixé.

    Le plafond joue dans les deux sens : il réduit le bruit — la sensibilité lui
    est proportionnelle — et il introduit un biais en tronquant les coûts
    élevés. Le comparer revient à choisir entre une erreur qu'on subit et une
    erreur qu'on décide.
    """
    lignes = []
    for plafond in PLAFONDS:
        reference = agregat_reference(interventions, plafond)
        globale = float(
            np.clip(interventions["parts_cost_eur"].dropna(), 0.0, plafond).mean()
        )
        for rang, (_, cellule) in enumerate(reference.iterrows()):
            valeurs = (
                interventions.loc[
                    (interventions["site_id"] == cellule["site_id"])
                    & (interventions["criticality"] == cellule["criticality"]),
                    "parts_cost_eur",
                ]
                .dropna()
                .to_numpy(dtype=float)
            )
            publiees = publier_moyenne(
                valeurs, epsilon, plafond, rng(offset=900 + rang)
            )
            mesures = mesurer(publiees, cellule["cout_moyen_borne"], plafond, globale)
            lignes.append(
                {
                    "plafond": plafond,
                    "site_id": cellule["site_id"],
                    "criticality": cellule["criticality"],
                    "effectif": cellule["effectif"],
                    "biais_troncature": cellule["biais_troncature"],
                    "erreur_absolue_mediane": mesures["erreur_absolue_mediane"],
                    "erreur_totale": round(
                        abs(cellule["biais_troncature"])
                        + mesures["erreur_absolue_mediane"],
                        2,
                    ),
                    "part_conclusion_conservee": mesures["part_conclusion_conservee"],
                }
            )
    return pd.DataFrame(lignes)


def balayer_granularite(interventions: pd.DataFrame, plafond: float) -> pd.DataFrame:
    """Compare la publication à deux granularités, à budgets identiques.

    Si aucun budget ne convient au tableau croisé, la question à poser n'est plus
    « quel `ε` », mais « quelle maille ». Regrouper les sites fait passer les
    effectifs de 4 à plusieurs centaines sans changer la sensibilité : le bruit
    reste le même en euros et devient négligeable devant la masse.
    """
    globale = float(
        np.clip(interventions["parts_cost_eur"].dropna(), 0.0, plafond).mean()
    )
    lignes = []
    mailles = {
        "site × criticité": ["site_id", "criticality"],
        "criticité seule": ["criticality"],
    }
    for nom, colonnes in mailles.items():
        for rang, (cle, groupe) in enumerate(interventions.groupby(colonnes)):
            valeurs = groupe["parts_cost_eur"].dropna().to_numpy(dtype=float)
            if not len(valeurs):
                continue
            vraie = float(np.clip(valeurs, 0.0, plafond).mean())
            for index, epsilon in enumerate(EPSILONS):
                publiees = publier_moyenne(
                    valeurs,
                    epsilon,
                    plafond,
                    rng(offset=1300 + rang * len(EPSILONS) + index),
                )
                mesures = mesurer(publiees, vraie, plafond, globale)
                lignes.append(
                    {
                        "maille": nom,
                        "cellule": cle if isinstance(cle, str) else " / ".join(cle),
                        "effectif": int(len(valeurs)),
                        "epsilon": epsilon,
                        "erreur_absolue_mediane": mesures["erreur_absolue_mediane"],
                        "part_conclusion_conservee": mesures["part_conclusion_conservee"],
                    }
                )
    return pd.DataFrame(lignes)


def figure_budgets(balayage: pd.DataFrame, chemin: Path) -> None:
    """Erreur et conclusion conservée, en fonction du budget et de l'effectif."""
    figure, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    petites = balayage[balayage["effectif"] < 30]
    grandes = balayage[balayage["effectif"] >= 100]

    for axe, indicateur, titre, echelle in (
        (axes[0], "erreur_relative_mediane", "Erreur relative médiane", "log"),
        (
            axes[1],
            "part_conclusion_conservee",
            "Conclusion conservée (au-dessus / en dessous\nde la moyenne générale)",
            "linear",
        ),
    ):
        for groupe, libelle, style in (
            (petites, "cellules < 30 interventions", "o-"),
            (grandes, "cellules ≥ 100 interventions", "s--"),
        ):
            moyennes = groupe.groupby("epsilon")[indicateur].median()
            axe.plot(moyennes.index, moyennes.values, style, label=libelle)
        axe.set_xscale("log")
        axe.set_yscale(echelle)
        axe.set_xlabel("budget ε")
        axe.set_title(titre, fontsize=10)
        axe.grid(alpha=0.3)
    axes[1].axhline(0.5, color="crimson", lw=1, ls=":", label="hasard")
    axes[0].legend(fontsize=8)
    axes[1].legend(fontsize=8)
    figure.suptitle(
        "Coût moyen des pièces par site × criticité — effet du budget de confidentialité"
    )
    figure.tight_layout()
    figure.savefig(chemin, dpi=120)
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=WORK_ROOT / "output" / "confidentialite"
    )
    args = parser.parse_args()
    sortie = args.output
    (sortie / "figures").mkdir(parents=True, exist_ok=True)

    interventions = interventions_situees()
    reference = agregat_reference(interventions, PLAFOND_RETENU)
    reference.to_csv(sortie / "agregat_reference.csv", index=False, encoding="utf-8")

    print(f"Agrégat protégé — coût moyen des pièces, site × criticité")
    print(f"  plafond de bornage retenu : {PLAFOND_RETENU:.0f} €")
    print(
        f"  sensibilité de la somme : {PLAFOND_RETENU:.0f} € · "
        f"sensibilité de l'effectif : 1 · budget partagé {PART_SOMME:.0%}/"
        f"{1 - PART_SOMME:.0%}"
    )
    print(f"  {len(reference)} cellules, effectifs {reference.effectif.min()} → "
          f"{reference.effectif.max()}, {TIRAGES} tirages par cellule et par budget\n")

    balayage = balayer_budgets(interventions, reference, PLAFOND_RETENU)
    balayage.to_csv(sortie / "balayage_epsilon.csv", index=False, encoding="utf-8")

    print("  ε      cellule la plus petite (n=4)      cellule la plus grande (n=319)")
    print("         erreur méd.   conclusion          erreur méd.   conclusion")
    petite = balayage.loc[balayage["effectif"].idxmin(), ["site_id", "criticality"]]
    grande = balayage.loc[balayage["effectif"].idxmax(), ["site_id", "criticality"]]
    for epsilon in EPSILONS:
        ligne = balayage[balayage["epsilon"] == epsilon]
        p = ligne[
            (ligne["site_id"] == petite["site_id"])
            & (ligne["criticality"] == petite["criticality"])
        ].iloc[0]
        g = ligne[
            (ligne["site_id"] == grande["site_id"])
            & (ligne["criticality"] == grande["criticality"])
        ].iloc[0]
        print(
            f"  {epsilon:<5}  {p['erreur_absolue_mediane']:>10.0f} €  "
            f"{p['part_conclusion_conservee']:>8.0%}   "
            f"    {g['erreur_absolue_mediane']:>9.1f} €  "
            f"{g['part_conclusion_conservee']:>8.0%}"
        )

    # Budget fixé pour l'étude du plafond : le seul degré de liberté examiné ici
    # est le bornage, donc ε reste constant.
    epsilon_comparaison = 1.0
    plafonds = comparer_plafonds(interventions, epsilon_comparaison)
    plafonds.to_csv(sortie / "comparaison_plafonds.csv", index=False, encoding="utf-8")
    print(
        f"\n  Effet du plafond de bornage, à ε = {epsilon_comparaison:g} "
        f"(médiane sur les 16 cellules)"
    )
    resume_plafonds = plafonds.groupby("plafond").agg(
        biais_median=("biais_troncature", lambda x: round(float(np.median(np.abs(x))), 2)),
        erreur_bruit_mediane=("erreur_absolue_mediane", "median"),
        erreur_totale_mediane=("erreur_totale", "median"),
        conclusion_conservee=("part_conclusion_conservee", "median"),
    )
    print(resume_plafonds.to_string())

    attaques = pd.DataFrame(
        [
            {
                "epsilon": epsilon,
                **attaque_par_differenciation(
                    epsilon, PLAFOND_RETENU, rng(offset=1700 + index)
                ),
            }
            for index, epsilon in enumerate(EPSILONS)
        ]
    )
    attaques.to_csv(sortie / "attaque_differenciation.csv", index=False, encoding="utf-8")

    granularite = balayer_granularite(interventions, PLAFOND_RETENU)
    granularite.to_csv(sortie / "granularite.csv", index=False, encoding="utf-8")

    print("\n  Les deux bornes")
    print("  ε       exploitables    erreur de l'adversaire   cible retrouvée à ±50 €")
    for _, attaque in attaques.iterrows():
        epsilon = attaque["epsilon"]
        ligne = balayage[balayage["epsilon"] == epsilon]
        exploitables = int((ligne["part_conclusion_conservee"] > 0.90).sum())
        print(
            f"  {epsilon:<6}  {exploitables:>6} / 16    "
            f"{attaque['erreur_estimation_mediane']:>15.0f} €   "
            f"{attaque['part_cible_retrouvee']:>16.1%}"
        )

    print("\n  Cellules exploitables selon la maille de publication")
    print("  ε       site × criticité      criticité seule")
    for epsilon in EPSILONS:
        fine = balayage[balayage["epsilon"] == epsilon]
        grossiere = granularite[
            (granularite["maille"] == "criticité seule")
            & (granularite["epsilon"] == epsilon)
        ]
        print(
            f"  {epsilon:<6}  {int((fine['part_conclusion_conservee'] > 0.90).sum()):>8} / 16  "
            f"{int((grossiere['part_conclusion_conservee'] > 0.90).sum()):>14} / 4"
        )

    figure_budgets(balayage, sortie / "figures" / "budgets_epsilon.png")

    synthese = {
        "graine": SEED,
        "agregat": "coût moyen des pièces par site × criticité",
        "plafond_retenu": PLAFOND_RETENU,
        "plafonds_compares": list(PLAFONDS),
        "epsilons": list(EPSILONS),
        "tirages": TIRAGES,
        "part_budget_somme": PART_SOMME,
        "tolerance_attaque_eur": TOLERANCE_ATTAQUE_EUR,
        "cellules": reference.to_dict(orient="records"),
        "balayage": balayage.to_dict(orient="records"),
        "plafonds": resume_plafonds.reset_index().to_dict(orient="records"),
        "granularite": granularite.to_dict(orient="records"),
        "attaque": attaques.to_dict(orient="records"),
    }
    (sortie / "confidentialite.json").write_text(
        json.dumps(synthese, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nSorties écrites dans {sortie}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
