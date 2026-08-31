"""Brief 2, étape 3 — générer des mesures pour un périmètre non couvert.

Périmètre retenu (arbitrage A2, tranché le 25/08) : les **8 équipements de
`SITE-OUEST` appartenant à `SEG-2`**. `SITE-OUEST` est le périmètre non
instrumenté que le brief désigne ; `SEG-2` est le segment que l'étape 1 a
identifié comme le moins couvert (2 équipements instrumentés sur 174). Leur
intersection satisfait les deux, et présente une répartition de criticité
parfaitement équilibrée — 2 `critical`, 2 `high`, 2 `medium`, 2 `low`.

Deux voies de génération sont produites et comparées au réel : le tirage
marginal et l'interpolation entre voisins. La comparaison porte sur les
marginales **et** sur les relations — entre colonnes et entre sources — comme
l'exige le brief : une comparaison limitée aux moyennes est un critère bloquant.

Usage :
    python run_generation_b2.py [--output ./output/generation]
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
from scipy.stats import mannwhitneyu

from src.brief2.augmentation import LAGS_STRUCTURE, profil_autocorrelation
from src.brief2.generation import (
    K_VOISINS,
    PENALITE_TYPE,
    contexte_generation,
    controles_metier,
    descripteurs_equipements,
    generer_par_interpolation,
    generer_par_tirage_marginal,
    grille_horaire,
    voisins_par_cible,
)
from src.brief2.seed import SEED, rng
from src.brief2.sources import load_prepared


SITE_CIBLE = "SITE-OUEST"
SEGMENT_CIBLE = "SEG-2"
CAPTEURS = ("vibration_mm_s", "temperature_c")

# Période courte, comme le brief l'autorise : un mois au pas nominal de 6 h.
DEBUT = pd.Timestamp("2026-01-01T00:00:00Z")
FIN = pd.Timestamp("2026-01-31T18:00:00Z")

FENETRE_AVANT_H = 48
FENETRE_APRES_H = 24

# Le livrable est borné à un mois, comme le brief l'autorise. Mais sur un mois,
# le test de réaction aux événements n'a pas la puissance de trancher : sur le
# réel lui-même, restreint à janvier, il ne détecte rien (p = 0,18 et p = 0,97)
# alors que la réaction est franche sur le semestre. Une génération de contrôle
# couvrant tout 2026-S1 est donc produite pour cette seule question, et
# identifiée comme telle : sans elle, « les fabriqués ne réagissent pas » serait
# une conclusion tirée d'un test incapable de voir la réaction du réel.
FIN_CONTROLE = pd.Timestamp("2026-06-30T18:00:00Z")


def marginales(frame: pd.DataFrame, origine: str) -> pd.DataFrame:
    """Statistiques de distribution par capteur."""
    lignes = []
    for capteur, groupe in frame.groupby("sensor_name", observed=True):
        valeurs = groupe["value"]
        lignes.append(
            {
                "origine": origine,
                "sensor_name": capteur,
                "lignes": int(len(valeurs)),
                "moyenne": round(float(valeurs.mean()), 4),
                "mediane": round(float(valeurs.median()), 4),
                "ecart_type": round(float(valeurs.std(ddof=0)), 4),
                "q25": round(float(valeurs.quantile(0.25)), 4),
                "q75": round(float(valeurs.quantile(0.75)), 4),
                "min": round(float(valeurs.min()), 4),
                "max": round(float(valeurs.max()), 4),
            }
        )
    return pd.DataFrame(lignes)


def structure_temporelle(frame: pd.DataFrame, origine: str) -> pd.DataFrame:
    """Autocorrélation médiane par capteur, aux rangs qui portent le cycle."""
    lignes = []
    for (capteur,), groupe in frame.groupby(["sensor_name"], observed=True):
        profils = []
        for _, serie in groupe.groupby("equipment_id", observed=True):
            serie = serie.sort_values("timestamp")
            if len(serie) < 20:
                continue
            profils.append(profil_autocorrelation(serie["value"]))
        if not profils:
            continue
        ligne = {"origine": origine, "sensor_name": capteur, "series": len(profils)}
        for lag in LAGS_STRUCTURE:
            valeurs = [p[lag] for p in profils if p[lag] is not None]
            ligne[f"autocorr_lag{lag}_mediane"] = (
                round(float(np.median(valeurs)), 4) if valeurs else None
            )
        lignes.append(ligne)
    return pd.DataFrame(lignes)


def correlation_entre_capteurs(frame: pd.DataFrame, origine: str) -> dict:
    """Corrélation entre les deux capteurs d'un même équipement, au même instant.

    C'est une relation *entre colonnes* : elle ne se voit sur aucun histogramme
    et le tirage marginal ne peut pas la produire.
    """
    pivot = frame.pivot_table(
        index=["equipment_id", "timestamp"], columns="sensor_name", values="value"
    ).dropna()
    if pivot.shape[0] < 20 or pivot.shape[1] < 2:
        return {"origine": origine, "couples": int(pivot.shape[0]), "correlation": None}

    correlations = []
    for _, groupe in pivot.groupby(level="equipment_id"):
        if len(groupe) < 20:
            continue
        valeur = groupe.iloc[:, 0].corr(groupe.iloc[:, 1])
        if pd.notna(valeur):
            correlations.append(float(valeur))
    return {
        "origine": origine,
        "couples": int(pivot.shape[0]),
        "equipements": len(correlations),
        "correlation_mediane": round(float(np.median(correlations)), 4) if correlations else None,
    }


def reaction_aux_evenements(
    frame: pd.DataFrame, events: pd.DataFrame, origine: str
) -> pd.DataFrame:
    """Niveau moyen pendant les fenêtres d'événement, comparé au reste.

    C'est une relation *entre sources* : elle met en jeu `events.csv`, que ni le
    tirage marginal ni l'interpolation ne consultent.
    """
    debut = pd.to_datetime(events["start_at"], errors="coerce", utc=True) - pd.Timedelta(
        hours=FENETRE_AVANT_H
    )
    fin = pd.to_datetime(events["end_at"], errors="coerce", utc=True) + pd.Timedelta(
        hours=FENETRE_APRES_H
    )
    # Un événement sans date de fin garde une fenêtre ouverte à droite de la
    # durée d'après : sans cela, ses mesures seraient comptées comme hors
    # fenêtre alors que l'événement est simplement en cours.
    fin = fin.fillna(
        pd.to_datetime(events["start_at"], errors="coerce", utc=True)
        + pd.Timedelta(hours=FENETRE_APRES_H)
    )
    fenetres = pd.DataFrame(
        {"equipment_id": events["equipment_id"], "debut": debut, "fin": fin}
    ).dropna()

    frame = frame.copy()
    frame["en_fenetre"] = False
    for ligne in fenetres.itertuples(index=False):
        frame.loc[
            (frame["equipment_id"] == ligne.equipment_id)
            & (frame["timestamp"] >= ligne.debut)
            & (frame["timestamp"] <= ligne.fin),
            "en_fenetre",
        ] = True

    lignes = []
    for capteur, groupe in frame.groupby("sensor_name", observed=True):
        dedans = groupe.loc[groupe["en_fenetre"], "value"]
        dehors = groupe.loc[~groupe["en_fenetre"], "value"]
        # Un écart de moyenne ne suffit pas à établir une réaction : il faut
        # savoir s'il se distingue du hasard, d'autant que les effectifs en
        # fenêtre sont dix à trente fois plus petits qu'en dehors.
        p_value = None
        if len(dedans) >= 10 and len(dehors) >= 10:
            _, p_value = mannwhitneyu(dedans, dehors)
            p_value = round(float(p_value), 6)

        lignes.append(
            {
                "origine": origine,
                "sensor_name": capteur,
                "mesures_en_fenetre": int(len(dedans)),
                "mesures_hors_fenetre": int(len(dehors)),
                "moyenne_en_fenetre": round(float(dedans.mean()), 4) if len(dedans) else None,
                "moyenne_hors_fenetre": round(float(dehors.mean()), 4) if len(dehors) else None,
                "ecart_pct": (
                    round(100 * (dedans.mean() - dehors.mean()) / dehors.mean(), 2)
                    if len(dedans) and len(dehors) and dehors.mean()
                    else None
                ),
                "p_value_mann_whitney": p_value,
                "reaction_significative": (
                    None if p_value is None else bool(p_value < 0.05)
                ),
            }
        )
    return pd.DataFrame(lignes)


def tracer_series(
    reelle: pd.DataFrame, produits: dict[str, pd.DataFrame], capteur: str, chemin: Path
) -> None:
    """Une série réelle et les deux séries fabriquées, même capteur."""
    figure, axes = plt.subplots(len(produits) + 1, 1, figsize=(11, 2.4 * (len(produits) + 1)))
    reference = reelle[reelle["sensor_name"] == capteur].sort_values("timestamp").head(80)
    axes[0].plot(reference["timestamp"], reference["value"], color="#4c72b0", linewidth=1.3)
    axes[0].set_title(
        f"réelle — {reference['equipment_id'].iat[0]} / {capteur}", fontsize=9, loc="left"
    )

    for ax, (procedure_id, produit) in zip(axes[1:], produits.items()):
        extrait = produit[produit["sensor_name"] == capteur]
        premier = extrait["equipment_id"].iat[0]
        extrait = extrait[extrait["equipment_id"] == premier].sort_values("timestamp").head(80)
        ax.plot(extrait["timestamp"], extrait["value"], color="#c44e52", linewidth=1.3)
        ax.set_title(f"{procedure_id} — {premier} / {capteur}", fontsize=9, loc="left")

    for ax in axes:
        ax.tick_params(labelsize=7)
    figure.suptitle("Réel contre fabriqué — 80 premières mesures")
    figure.tight_layout()
    figure.savefig(chemin, dpi=120)
    plt.close(figure)


def tracer_distributions(
    reelle: pd.DataFrame, produits: dict[str, pd.DataFrame], chemin: Path
) -> None:
    """Histogrammes comparés — là où le tirage marginal est irréprochable."""
    figure, axes = plt.subplots(1, len(CAPTEURS), figsize=(5.5 * len(CAPTEURS), 4))
    for ax, capteur in zip(axes, CAPTEURS):
        ax.hist(
            reelle.loc[reelle["sensor_name"] == capteur, "value"],
            bins=30,
            density=True,
            alpha=0.5,
            color="#4c72b0",
            label="réel",
        )
        for couleur, (procedure_id, produit) in zip(
            ("#c44e52", "#55a868"), produits.items()
        ):
            ax.hist(
                produit.loc[produit["sensor_name"] == capteur, "value"],
                bins=30,
                density=True,
                histtype="step",
                linewidth=1.6,
                color=couleur,
                label=procedure_id,
            )
        ax.set_title(capteur, fontsize=10)
        ax.legend(fontsize=7)
    figure.suptitle("Distributions comparées")
    figure.tight_layout()
    figure.savefig(chemin, dpi=120)
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/generation"))
    args = parser.parse_args()

    out = args.output
    figures = out / "figures"
    figures.mkdir(parents=True, exist_ok=True)

    prepared = load_prepared()
    parc_segmente = pd.read_csv("output/capacite/parc_segmente.csv")

    contexte = contexte_generation(
        CAPTEURS, SITE_CIBLE, SEGMENT_CIBLE, parc_segmente, prepared, K_VOISINS
    )
    reelles = contexte["reelles"]
    cibles = contexte["cibles"]
    donneurs = contexte["donneurs"]
    voisins = contexte["voisins"]

    horodatages = grille_horaire(DEBUT, FIN)

    marginal = generer_par_tirage_marginal(
        cibles, reelles, CAPTEURS, horodatages, rng(offset=101)
    )
    marginal["provenance"] = "synthétique"
    marginal["procedure_id"] = "PROC-GEN-MARG-V1"

    interpole, journal = generer_par_interpolation(
        cibles, reelles, CAPTEURS, horodatages, voisins, rng(offset=102)
    )
    interpole["provenance"] = "synthétique"
    interpole["procedure_id"] = "PROC-GEN-SMOTE-V1"

    produits = {"PROC-GEN-MARG-V1": marginal, "PROC-GEN-SMOTE-V1": interpole}
    for procedure_id, produit in produits.items():
        produit.to_csv(out / f"mesures_{procedure_id}.csv", index=False)

    # --- comparaison réel / fabriqué ----------------------------------------
    reference = reelles[
        (reelles["timestamp"] >= DEBUT) & (reelles["timestamp"] <= FIN)
    ]

    table_marginales = pd.concat(
        [marginales(reference, "réel")]
        + [marginales(produit, procedure_id) for procedure_id, produit in produits.items()],
        ignore_index=True,
    )
    table_marginales.to_csv(out / "comparaison_marginales.csv", index=False)

    table_structure = pd.concat(
        [structure_temporelle(reference, "réel")]
        + [
            structure_temporelle(produit, procedure_id)
            for procedure_id, produit in produits.items()
        ],
        ignore_index=True,
    )
    table_structure.to_csv(out / "comparaison_structure.csv", index=False)

    correlations = [correlation_entre_capteurs(reference, "réel")] + [
        correlation_entre_capteurs(produit, procedure_id)
        for procedure_id, produit in produits.items()
    ]
    pd.DataFrame(correlations).to_csv(out / "comparaison_correlation_capteurs.csv", index=False)

    evenements = prepared["events"]

    # --- génération de contrôle, sur tout le semestre -----------------------
    horodatages_longs = grille_horaire(DEBUT, FIN_CONTROLE)
    marginal_long = generer_par_tirage_marginal(
        cibles, reelles, CAPTEURS, horodatages_longs, rng(offset=201)
    )
    interpole_long, _ = generer_par_interpolation(
        cibles, reelles, CAPTEURS, horodatages_longs, voisins, rng(offset=202)
    )
    controle_puissance = pd.concat(
        [
            reaction_aux_evenements(reelles, evenements, "réel — 2026-S1"),
            reaction_aux_evenements(
                marginal_long, evenements, "PROC-GEN-MARG-V1 — 2026-S1"
            ),
            reaction_aux_evenements(
                interpole_long, evenements, "PROC-GEN-SMOTE-V1 — 2026-S1"
            ),
        ],
        ignore_index=True,
    )
    controle_puissance.to_csv(out / "comparaison_evenements_puissance.csv", index=False)

    table_evenements = pd.concat(
        [
            reaction_aux_evenements(reference, evenements, "réel — janvier"),
            # La référence sur tout le semestre sert de témoin : sur un seul
            # mois, les effectifs en fenêtre sont trop faibles pour trancher.
            reaction_aux_evenements(reelles, evenements, "réel — 2026-S1"),
        ]
        + [
            reaction_aux_evenements(produit, evenements, procedure_id)
            for procedure_id, produit in produits.items()
        ],
        ignore_index=True,
    )
    table_evenements.to_csv(out / "comparaison_evenements.csv", index=False)

    parc = set(parc_segmente["equipment_id"])
    controles = pd.concat(
        [
            controles_metier(produit, reelles, parc).assign(procedure_id=procedure_id)
            for procedure_id, produit in produits.items()
        ],
        ignore_index=True,
    )
    controles.to_csv(out / "controles_metier.csv", index=False)

    tracer_series(reference, produits, CAPTEURS[0], figures / "generation_series.png")
    tracer_distributions(reference, produits, figures / "generation_distributions.png")

    resultat = {
        "graine": SEED,
        "perimetre": {
            "arbitrage": "A2 — SITE-OUEST ∩ SEG-2",
            "site": SITE_CIBLE,
            "segment": SEGMENT_CIBLE,
            "equipements": cibles["equipment_id"].tolist(),
            "types": cibles["equipment_type"].value_counts().to_dict(),
            "criticites": cibles["criticality"].value_counts().to_dict(),
            "capteurs": list(CAPTEURS),
            "periode": {"debut": str(DEBUT), "fin": str(FIN)},
            "horodatages_par_serie": len(horodatages),
        },
        "voisinage": {
            "k": K_VOISINS,
            "penalite_type_different": PENALITE_TYPE,
            "descripteurs": ["criticite_ordinale", "puissance_log", "age_annees"],
            "donneurs_disponibles": int(len(donneurs)),
            "voisins_retenus": voisins,
            "journal_interpolation": journal,
        },
        "volumes": {
            procedure_id: int(len(produit)) for procedure_id, produit in produits.items()
        },
        "marginales": table_marginales.to_dict(orient="records"),
        "structure_temporelle": table_structure.to_dict(orient="records"),
        "correlation_entre_capteurs": correlations,
        "reaction_aux_evenements": table_evenements.to_dict(orient="records"),
        "reaction_aux_evenements_controle_semestre": controle_puissance.to_dict(
            orient="records"
        ),
        "controles_metier": controles.to_dict(orient="records"),
    }
    (out / "generation.json").write_text(
        json.dumps(resultat, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )

    print(table_marginales.to_string(index=False))
    print()
    print(table_structure.to_string(index=False))
    print()
    print(pd.DataFrame(correlations).to_string(index=False))
    print()
    print(table_evenements.to_string(index=False))
    print()
    print(controle_puissance.to_string(index=False))
    print(f"\nSorties écrites dans {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
