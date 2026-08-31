"""Brief 2, étape 1 — chiffrer ce que le jeu de données ne permet pas.

Le brief 1 a conclu sur la qualité des données. Cette étape mesure leur
capacité : effectifs et déséquilibres, couverture réelle des événements,
segmentation du parc, et le croisement de cette segmentation avec
l'instrumentation.

Rien n'est transformé ni rejeté ici : on décrit un état avant toute
fabrication. Les sorties vont dans `output/capacite/`, les figures dans
`output/capacite/figures/`.

Usage :
    python run_capacite_b2.py [--output ./output/capacite] [--k-max 10]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from src.brief2.capacite import (
    FEATURES_LOG,
    STRATE_INACTIVE,
    construire_features,
    composition_segments,
    couverture_evenements,
    croiser_couverture,
    diagnostiquer_partition,
    effectifs,
    explorer_k,
    matrice_normalisee,
    nommer_segments,
    profil_segments,
    ratio_desequilibre,
    segmenter,
    tester_independance_couverture,
)
from src.brief2.seed import SEED
from src.brief2.sources import load_alignment, load_prepared, prepared_checksums


AXES_PARC = ["site_id", "equipment_type", "criticality"]
AXES_EVENEMENTS = ["event_type", "severity"]


def tracer_effectifs(tables: dict[str, pd.DataFrame], titre: str, chemin: Path) -> None:
    """Effectifs par modalité — une barre horizontale par catégorie."""
    figure, axes = plt.subplots(1, len(tables), figsize=(5 * len(tables), 5))
    axes = axes if len(tables) > 1 else [axes]
    for ax, (axe, table) in zip(axes, tables.items()):
        donnees = table.sort_values("effectif")
        ax.barh(donnees[axe].astype(str), donnees["effectif"], color="#4c72b0")
        ax.set_title(axe)
        ax.set_xlabel("effectif")
        ax.tick_params(axis="y", labelsize=8)
    figure.suptitle(titre)
    figure.tight_layout()
    figure.savefig(chemin, dpi=120)
    plt.close(figure)


def tracer_distributions(features: pd.DataFrame, chemin: Path) -> None:
    """Distributions d'activité, avant toute transformation.

    Le brief 1 a montré qu'une poignée de valeurs extrêmes peut effacer un
    résultat sans que rien ne le signale. Ces histogrammes sont tracés avant
    le passage en logarithme, pour que l'asymétrie soit visible et non déduite.
    """
    figure, axes = plt.subplots(1, len(FEATURES_LOG), figsize=(4 * len(FEATURES_LOG), 4))
    for ax, colonne in zip(axes, FEATURES_LOG):
        ax.hist(features[colonne], bins=30, color="#c44e52")
        ax.set_title(colonne, fontsize=10)
        ax.set_yscale("log")
        ax.set_ylabel("équipements (échelle log)", fontsize=8)
    figure.suptitle("Activité par équipement — distributions brutes")
    figure.tight_layout()
    figure.savefig(chemin, dpi=120)
    plt.close(figure)


def tracer_choix_k(exploration: pd.DataFrame, k_retenu: int, chemin: Path) -> None:
    """Coude de l'inertie et silhouette, côte à côte."""
    figure, (gauche, droite) = plt.subplots(1, 2, figsize=(11, 4.5))

    gauche.plot(exploration["k"], exploration["inertie"], marker="o", color="#4c72b0")
    gauche.axvline(k_retenu, color="#c44e52", linestyle="--", label=f"k = {k_retenu}")
    gauche.set_title("Inertie intra-groupe (coude)")
    gauche.set_xlabel("k")
    gauche.legend()

    droite.plot(exploration["k"], exploration["silhouette"], marker="o", color="#55a868")
    droite.axvline(k_retenu, color="#c44e52", linestyle="--", label=f"k = {k_retenu}")
    droite.set_title("Silhouette moyenne")
    droite.set_xlabel("k")
    droite.legend()

    figure.tight_layout()
    figure.savefig(chemin, dpi=120)
    plt.close(figure)


def tracer_couverture_segments(croisement: pd.DataFrame, chemin: Path) -> None:
    """Taux d'instrumentation par segment — le résultat de l'étape."""
    figure, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(croisement["segment"].astype(str), croisement["taux_pct"], color="#4c72b0")
    for x, (taux, instrumentes, total) in enumerate(
        zip(croisement["taux_pct"], croisement["instrumentes"], croisement["equipements"])
    ):
        ax.text(x, taux + 0.6, f"{instrumentes}/{total}", ha="center", fontsize=9)
    ax.set_ylabel("taux d'instrumentation (%)")
    ax.set_title("Couverture instrumentale par segment du parc")
    figure.tight_layout()
    figure.savefig(chemin, dpi=120)
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/capacite"))
    parser.add_argument("--k-max", type=int, default=10)
    args = parser.parse_args()

    out = args.output
    figures = out / "figures"
    figures.mkdir(parents=True, exist_ok=True)

    prepared = load_prepared()
    alignment = load_alignment()
    equipment = prepared["equipment"]
    events = prepared["events"]
    maintenance = prepared["maintenance"]
    sensors = prepared["sensors"]

    # --- 1. effectifs et fréquences -----------------------------------------
    tables_parc = {axe: effectifs(equipment, axe) for axe in AXES_PARC}
    tables_evenements = {axe: effectifs(events, axe) for axe in AXES_EVENEMENTS}
    for axe, table in {**tables_parc, **tables_evenements}.items():
        table.to_csv(out / f"effectifs_{axe}.csv", index=False)

    tracer_effectifs(tables_parc, "Parc — effectifs", figures / "effectifs_parc.png")
    tracer_effectifs(
        tables_evenements, "Événements — effectifs", figures / "effectifs_evenements.png"
    )

    # --- 2. rapports de déséquilibre ----------------------------------------
    ratios = pd.DataFrame(
        [ratio_desequilibre(table, axe) for axe, table in tables_parc.items()]
        + [ratio_desequilibre(table, axe) for axe, table in tables_evenements.items()]
    ).sort_values("ratio", ascending=False)
    ratios.to_csv(out / "ratios_desequilibre.csv", index=False)

    # --- 3. couverture des événements ---------------------------------------
    couverture = couverture_evenements(events, alignment["sans_mesure"])
    couverture.to_csv(out / "couverture_evenements.csv", index=False)

    independance = tester_independance_couverture(events, alignment["sans_mesure"])
    independance.to_csv(out / "couverture_evenements_test.csv", index=False)

    # --- 4. segmentation ----------------------------------------------------
    features, rapport = construire_features(equipment, events, maintenance)
    instrumentes = set(sensors["equipment_id"])
    features["instrumente"] = features["equipment_id"].isin(instrumentes)

    tracer_distributions(features, figures / "distributions_activite.png")

    # État 1 — segmentation du parc entier. Conservé pour la démarche : c'est
    # lui qui révèle le groupe dégénéré, et sa correction est un résultat.
    matrice_totale, colonnes = matrice_normalisee(features)
    exploration_totale = explorer_k(matrice_totale, range(2, args.k_max + 1))
    exploration_totale.to_csv(out / "choix_k_etat1.csv", index=False)

    meilleur_totale = exploration_totale.loc[exploration_totale["silhouette"].idxmax()]
    k_totale = int(meilleur_totale["k"])
    labels_totale = segmenter(matrice_totale, k_totale)
    diagnostic = diagnostiquer_partition(features, labels_totale)

    # État 2 — la strate sans activité est déclarée, pas découverte ; le parc
    # actif est segmenté séparément et standardisé sur sa propre population.
    actifs = features["n_interventions"] > 0
    matrice_actifs, _ = matrice_normalisee(features[actifs])
    exploration = explorer_k(matrice_actifs, range(2, args.k_max + 1))
    exploration.to_csv(out / "choix_k.csv", index=False)

    meilleur = exploration.loc[exploration["silhouette"].idxmax()]
    k_retenu = int(meilleur["k"])
    features["segment"] = STRATE_INACTIVE
    features.loc[actifs, "segment"] = nommer_segments(segmenter(matrice_actifs, k_retenu))

    tracer_choix_k(exploration, k_retenu, figures / "choix_k.png")

    profil = profil_segments(features)
    profil.to_csv(out / "segments_profil.csv", index=False)

    composition = composition_segments(features)
    composition.to_csv(out / "segments_composition.csv", index=False)

    croisement = croiser_couverture(features)
    croisement.to_csv(out / "segments_croisement_couverture.csv", index=False)
    tracer_couverture_segments(croisement, figures / "segments_couverture.png")

    features.to_csv(out / "parc_segmente.csv", index=False)

    # --- résumé -------------------------------------------------------------
    resume = {
        "point_de_depart": {
            "arbitrage": "A1 — préparation issue du brief 1 (output/processed/)",
            "empreintes": prepared_checksums(),
            "parc": int(len(equipment)),
            "evenements": int(len(events)),
            "interventions": int(len(maintenance)),
            "mesures": int(len(sensors)),
        },
        "graine": SEED,
        "desequilibres": ratios.to_dict(orient="records"),
        "couverture_evenements": {
            "fenetre_heures": {"avant": 48.0, "apres": 24.0},
            "evenements_total": int(len(events)),
            "evenements_documentes": int(
                len(events) - events["event_id"].isin(alignment["sans_mesure"]["event_id"]).sum()
            ),
            "par_categorie": couverture.to_dict(orient="records"),
            "test_independance": independance.to_dict(orient="records"),
        },
        "segmentation": {
            "variables": colonnes,
            "variables_en_log": FEATURES_LOG,
            "exclues_volontairement": {
                "instrumente": "sinon la conclusion sur la couverture serait tautologique",
                "site_id": "déjà décrit par les comptages du brief 1",
                "equipment_type": "la segmentation doit dépasser la partition par type",
            },
            "rapport_preparation": rapport,
            "etat_1_parc_entier": {
                "exploration_k": exploration_totale.to_dict(orient="records"),
                "k_retenu": k_totale,
                "silhouette": float(meilleur_totale["silhouette"]),
                "diagnostic": diagnostic,
                "conclusion": (
                    "partition rejetée — le groupe majoritairement isolé est défini "
                    "par des compteurs d'activité tous nuls, la silhouette récompense "
                    "une séparation triviale et le parc actif reste non structuré"
                ),
            },
            "etat_2_strate_puis_segments": {
                "strate_declaree": STRATE_INACTIVE,
                "equipements_strate": int((~actifs).sum()),
                "equipements_segmentes": int(actifs.sum()),
                "exploration_k": exploration.to_dict(orient="records"),
                "k_retenu": k_retenu,
                "silhouette_retenue": float(meilleur["silhouette"]),
            },
            "profil": profil.to_dict(orient="records"),
            "composition": composition.to_dict(orient="records"),
            "croisement_couverture": croisement.to_dict(orient="records"),
        },
    }
    (out / "capacite.json").write_text(
        json.dumps(resume, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )

    print(json.dumps(resume, indent=2, ensure_ascii=False, default=str))
    print(f"\nSorties écrites dans {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
