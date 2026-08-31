"""Brief 2, étape 2 — augmenter des séries existantes et mesurer le coût.

Cinq techniques sont appliquées aux 72 séries préparées au brief 1. Pour
chacune, le script ne se contente pas de produire la variante : il mesure ce
que la transformation a préservé et ce qu'elle a détruit, puis confronte ce
résultat à l'effet attendu déclaré dans le code.

Le brief sanctionne toute technique décrite sans ce qu'elle détruit. Les seuils
de verdict sont explicites et figurent dans la sortie : « préservé » est ici une
mesure, pas une appréciation.

Usage :
    python run_augmentation_b2.py [--output ./output/augmentation]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

from src.brief2.augmentation import LAGS_AUTOCORR, LAGS_STRUCTURE, TECHNIQUES, mesurer
from src.brief2.seed import SEED, rng
from src.brief2.sources import load_prepared


# Fenêtre d'observation d'un événement, reprise du brief 1.
FENETRE_AVANT_H = 48
FENETRE_APRES_H = 24

# Longueur minimale d'une série pour être augmentée. En dessous, les mesures
# d'autocorrélation et de plage robuste n'ont pas de sens.
LONGUEUR_MINIMALE = 100

# Seuils de verdict. Ils sont arbitraires mais déclarés : sans eux, « préservé »
# resterait une appréciation.
SEUILS = {
    "ordre_de_grandeur_pct": 1.0,
    "autocorrelation_absolue": 0.05,
    "pas_nominal_pct": 1.0,
    "fidelite_correlation": 0.99,
    "lien_evenements_ratio": 0.95,
    "signal_fenetre_ratio": 0.01,
}


def fenetres_par_equipement(events: pd.DataFrame) -> dict[str, list[tuple]]:
    """Fenêtres d'observation, par équipement."""
    debut = pd.to_datetime(events["start_at"], errors="coerce", utc=True)
    fin = pd.to_datetime(events["end_at"], errors="coerce", utc=True)
    frame = pd.DataFrame(
        {
            "equipment_id": events["equipment_id"],
            "debut": debut - pd.Timedelta(hours=FENETRE_AVANT_H),
            "fin": fin + pd.Timedelta(hours=FENETRE_APRES_H),
        }
    ).dropna()

    fenetres: dict[str, list[tuple]] = {}
    for equipement, groupe in frame.groupby("equipment_id", observed=True):
        fenetres[equipement] = list(zip(groupe["debut"], groupe["fin"]))
    return fenetres


def series_preparees(sensors: pd.DataFrame) -> list[tuple[tuple[str, str], pd.DataFrame]]:
    """Découpe la table de mesures en séries exploitables, triées par temps.

    Les valeurs neutralisées au brief 1 (`R-SEN-007`, `R-SEN-008`) sont écartées
    ici : une augmentation ne peut pas déformer une valeur absente, et les
    conserver fausserait toutes les mesures de dispersion.
    """
    frame = sensors.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    frame = frame.dropna(subset=["timestamp", "value"])

    series = []
    for cle, groupe in frame.groupby(["equipment_id", "sensor_name"], observed=True):
        if len(groupe) < LONGUEUR_MINIMALE:
            continue
        series.append((cle, groupe.sort_values("timestamp").reset_index(drop=True)))
    return series


def verdicts(mesure: dict) -> dict:
    """Traduit les mesures en propriétés préservées ou détruites."""
    delta_moyenne = abs(mesure["delta_moyenne_pct"] or 0.0)
    delta_ecart = abs(mesure["delta_ecart_type_pct"] or 0.0)
    # La structure est jugée sur les rangs qui la portent (12 h et 24 h), pas
    # sur le rang 1 où le cycle journalier est en quadrature et invisible.
    ecarts_autocorr = [
        abs(mesure[f"autocorr_lag{lag}_apres"] - mesure[f"autocorr_lag{lag}_avant"])
        for lag in LAGS_STRUCTURE
        if mesure[f"autocorr_lag{lag}_apres"] is not None
        and mesure[f"autocorr_lag{lag}_avant"] is not None
    ]
    ecart_autocorr = max(ecarts_autocorr) if ecarts_autocorr else 0.0
    perte_pas = mesure["part_pas_nominal_avant_pct"] - mesure["part_pas_nominal_apres_pct"]

    avant = mesure["en_fenetre_evenement_avant"]
    apres = mesure["en_fenetre_evenement_apres"]
    lien = (apres / avant) if avant else None

    # Le lien aux événements se juge sur deux plans : les mesures sont-elles
    # toujours dans la fenêtre, et portent-elles toujours le même signal.
    signal_avant = mesure["signal_en_fenetre_avant"]
    signal_apres = mesure["signal_en_fenetre_apres"]
    signal_conserve = (
        (abs(signal_apres - signal_avant) / abs(signal_avant) <= SEUILS["signal_fenetre_ratio"])
        if signal_avant not in (None, 0) and signal_apres is not None
        else None
    )

    correlation = mesure["correlation_point_a_point"]

    return {
        "ordre_de_grandeur": bool(
            delta_moyenne <= SEUILS["ordre_de_grandeur_pct"]
            and delta_ecart <= SEUILS["ordre_de_grandeur_pct"]
        ),
        "fidelite_point_a_point": (
            bool(correlation >= SEUILS["fidelite_correlation"])
            if correlation is not None
            else None
        ),
        "structure_temporelle": bool(ecart_autocorr <= SEUILS["autocorrelation_absolue"]),
        "regularite_du_pas": bool(perte_pas <= SEUILS["pas_nominal_pct"]),
        "plausibilite_physique": bool(
            mesure["hors_plage_robuste_apres"] <= mesure["hors_plage_robuste_avant"]
        ),
        "lien_aux_evenements": (
            bool(lien >= SEUILS["lien_evenements_ratio"]) if lien is not None else None
        ),
        "signal_aux_evenements": (None if signal_conserve is None else bool(signal_conserve)),
        "cle_logique_libre": bool(mesure["collisions_cle_logique"] == 0),
    }


def agreger(detail: pd.DataFrame) -> pd.DataFrame:
    """Résume les mesures série par série en une ligne par technique."""
    numeriques = [
        "delta_moyenne_pct",
        "delta_ecart_type_pct",
        "correlation_point_a_point",
        *[f"autocorr_lag{lag}_avant" for lag in LAGS_AUTOCORR],
        *[f"autocorr_lag{lag}_apres" for lag in LAGS_AUTOCORR],
        "part_pas_nominal_apres_pct",
    ]
    compteurs = [
        "lignes",
        "hors_plage_robuste_avant",
        "hors_plage_robuste_apres",
        "en_fenetre_evenement_avant",
        "en_fenetre_evenement_apres",
        "collisions_cle_logique",
    ]
    booleens = [
        "ordre_de_grandeur",
        "fidelite_point_a_point",
        "structure_temporelle",
        "regularite_du_pas",
        "plausibilite_physique",
        "lien_aux_evenements",
        "signal_aux_evenements",
        "cle_logique_libre",
    ]

    # Deux propriétés ne sont pas mesurables sur toutes les séries : la fidélité
    # point à point n'a pas de sens quand l'axe temporel a bougé, et le lien aux
    # événements n'existe pas pour un équipement sans événement. Ces cas valent
    # `None` et doivent être exclus du dénominateur, pas comptés comme des
    # échecs — d'où le type booléen nullable plutôt qu'un `fillna(False)`.
    detail = detail.copy()
    for colonne in booleens:
        detail[colonne] = detail[colonne].astype("boolean")

    groupes = detail.groupby("procedure_id", observed=True)
    resume = groupes[numeriques].mean().round(4)
    resume = resume.join(groupes[compteurs].sum())
    resume["series"] = groupes.size()
    for colonne in booleens:
        # Part des séries pour lesquelles la propriété tient. `None` (propriété
        # non mesurable sur cette série) est exclu du dénominateur.
        resume[f"{colonne}_pct"] = (100 * groupes[colonne].mean()).round(1)
    return resume.reset_index()


def tracer_comparaison(
    exemple: pd.DataFrame, variantes: dict[str, pd.DataFrame], chemin: Path, points: int = 60
) -> None:
    """Série de référence, avant et après chaque technique."""
    figure, axes = plt.subplots(len(variantes), 1, figsize=(11, 2.4 * len(variantes)), sharey=True)
    tete = exemple.head(points)
    for ax, (procedure_id, variante) in zip(axes, variantes.items()):
        ax.plot(tete["timestamp"], tete["value"], color="#4c72b0", label="réelle", linewidth=1.4)
        ax.plot(
            variante.head(points)["timestamp"],
            variante.head(points)["value"],
            color="#c44e52",
            label="augmentée",
            linewidth=1.0,
            linestyle="--",
            marker=".",
            markersize=3,
        )
        ax.set_title(procedure_id, fontsize=9, loc="left")
        ax.tick_params(labelsize=7)
        ax.legend(fontsize=7, loc="upper right")
    figure.suptitle(
        f"{exemple['equipment_id'].iat[0]} / {exemple['sensor_name'].iat[0]} — "
        f"{points} premières mesures"
    )
    figure.tight_layout()
    figure.savefig(chemin, dpi=120)
    plt.close(figure)


def tracer_histogrammes(
    exemple: pd.DataFrame, variantes: dict[str, pd.DataFrame], chemin: Path
) -> None:
    """Distributions comparées — ce que l'histogramme ne montre pas.

    Deux techniques laissent l'histogramme rigoureusement inchangé alors
    qu'elles ont détruit la série : le décalage temporel et la permutation de
    segments. La figure existe pour rendre cette cécité visible.
    """
    figure, axes = plt.subplots(1, len(variantes), figsize=(3.2 * len(variantes), 3.4), sharey=True)
    for ax, (procedure_id, variante) in zip(axes, variantes.items()):
        ax.hist(exemple["value"], bins=25, alpha=0.6, color="#4c72b0", label="réelle")
        ax.hist(variante["value"], bins=25, alpha=0.6, color="#c44e52", label="augmentée")
        ax.set_title(procedure_id, fontsize=8)
        ax.tick_params(labelsize=7)
    axes[0].legend(fontsize=7)
    figure.suptitle("Distributions comparées — deux techniques ne laissent aucune trace ici")
    figure.tight_layout()
    figure.savefig(chemin, dpi=120)
    plt.close(figure)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/augmentation"))
    args = parser.parse_args()

    out = args.output
    figures = out / "figures"
    figures.mkdir(parents=True, exist_ok=True)

    prepared = load_prepared()
    fenetres = fenetres_par_equipement(prepared["events"])
    series = series_preparees(prepared["sensors"])

    lignes = []
    variantes_exemple: dict[str, pd.DataFrame] = {}

    # Série de référence pour les figures : la plus longue parmi celles dont
    # l'équipement porte au moins un événement, pour que le lien aux événements
    # soit observable et non nul.
    candidates = [(cle, serie) for cle, serie in series if fenetres.get(cle[0])]
    cle_exemple, exemple = max(candidates, key=lambda item: len(item[1]))

    for index, technique in enumerate(TECHNIQUES):
        generateur = rng(offset=index + 1)
        for (equipement, capteur), serie in series:
            augmentee = technique.applique(serie, generateur)
            mesure = mesurer(serie, augmentee, fenetres.get(equipement, []))
            lignes.append(
                {
                    "procedure_id": technique.procedure_id,
                    "equipment_id": equipement,
                    "sensor_name": capteur,
                    **mesure,
                    **verdicts(mesure),
                }
            )
            if (equipement, capteur) == cle_exemple:
                variantes_exemple[technique.procedure_id] = augmentee
                augmentee.to_csv(
                    out / f"exemple_{technique.procedure_id}.csv", index=False
                )

    detail = pd.DataFrame(lignes)
    detail.to_csv(out / "mesures_par_serie.csv", index=False)

    resume = agreger(detail)
    resume.to_csv(out / "mesures_par_technique.csv", index=False)

    exemple.to_csv(out / "exemple_serie_reelle.csv", index=False)
    tracer_comparaison(exemple, variantes_exemple, figures / "augmentation_series.png")
    tracer_histogrammes(exemple, variantes_exemple, figures / "augmentation_distributions.png")

    # Confrontation entre l'effet attendu, déclaré avant exécution, et l'effet
    # mesuré. Un écart est un résultat, pas une erreur à corriger en silence.
    fiche = []
    for technique in TECHNIQUES:
        ligne = resume[resume["procedure_id"] == technique.procedure_id].iloc[0]
        preserve_mesure = [
            propriete
            for propriete in (
                "ordre_de_grandeur",
                "fidelite_point_a_point",
                "structure_temporelle",
                "regularite_du_pas",
                "plausibilite_physique",
                "lien_aux_evenements",
                "signal_aux_evenements",
            )
            if pd.notna(ligne[f"{propriete}_pct"]) and ligne[f"{propriete}_pct"] >= 95.0
        ]
        detruit_mesure = [
            propriete
            for propriete in (
                "ordre_de_grandeur",
                "fidelite_point_a_point",
                "structure_temporelle",
                "regularite_du_pas",
                "plausibilite_physique",
                "lien_aux_evenements",
                "signal_aux_evenements",
            )
            if pd.notna(ligne[f"{propriete}_pct"]) and ligne[f"{propriete}_pct"] < 5.0
        ]
        fiche.append(
            {
                "procedure_id": technique.procedure_id,
                "nom": technique.nom,
                "famille": technique.famille,
                "parametres": json.dumps(technique.parametres, ensure_ascii=False),
                "intention": technique.intention,
                "attendu_preserve": " ; ".join(technique.attendu_preserve),
                "attendu_detruit": " ; ".join(technique.attendu_detruit),
                "mesure_preserve": " ; ".join(preserve_mesure),
                "mesure_detruit": " ; ".join(detruit_mesure),
                "collisions_cle_logique": int(ligne["collisions_cle_logique"]),
            }
        )
    pd.DataFrame(fiche).to_csv(out / "fiche_techniques.csv", index=False)

    resultat = {
        "graine": SEED,
        "series_augmentees": len(series),
        "mesures_par_serie_moyenne": int(detail["lignes"].mean()),
        "fenetre_evenement_heures": {"avant": FENETRE_AVANT_H, "apres": FENETRE_APRES_H},
        "seuils_de_verdict": SEUILS,
        "serie_exemple": {
            "equipment_id": cle_exemple[0],
            "sensor_name": cle_exemple[1],
            "mesures": int(len(exemple)),
            "fenetres_evenement": len(fenetres.get(cle_exemple[0], [])),
        },
        "par_technique": resume.to_dict(orient="records"),
        "fiche": fiche,
    }
    (out / "augmentation.json").write_text(
        json.dumps(resultat, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )

    print(resume.to_string(index=False))
    print(f"\nSorties écrites dans {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
