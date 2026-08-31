"""Étape 3 du brief 1 M4 — comparer des modèles simples à la baseline M3.

Le protocole est gelé (`run_protocole.py`) : partition, métrique et seuil
d'acceptation ne sont pas renégociés ici. Ce script mesure, il ne décide pas.

Le test scellé n'est jamais chargé.

Usage :
    python run_modele.py [--output ./results/modele]
"""

from __future__ import annotations

import argparse
import json
import time
import tracemalloc
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

from src.modele import NOMS_FEATURES, candidats, etiquettes, table_features
from src.protocole import (
    CLASSE_NEGATIVE,
    CLASSE_POSITIVE,
    COLONNE_FENETRE,
    baseline_deux_niveaux,
    charger_calibration,
    plis,
    scores,
    table_fenetres,
)


def evaluer(nom: str, pipeline, table: pd.DataFrame, y: pd.Series, decoupes) -> dict:
    """Validation croisée répétée — un résultat par pli, jamais un chiffre unique."""
    index = {identifiant: i for i, identifiant in enumerate(table[COLONNE_FENETRE])}
    features = table[NOMS_FEATURES].to_numpy()
    cible = y.to_numpy()

    par_pli: list[dict] = []
    # Une grille de prédictions par répétition : dans une répétition, les plis
    # de validation partitionnent les 30 fenêtres, donc chaque fenêtre est
    # prédite une fois et une seule. Le F1 qui en découle porte sur les 30
    # fenêtres — directement comparable à celui de la baseline.
    repetitions = sorted({d.repetition for d in decoupes})
    predictions_par_repetition = {
        r: np.full(len(table), -1) for r in repetitions
    }
    scores_par_repetition = {
        r: np.full(len(table), np.nan) for r in repetitions
    }
    latences: list[float] = []

    for decoupe in decoupes:
        entrainement = [index[f] for f in decoupe.entrainement]
        validation = [index[f] for f in decoupe.validation]

        modele = pipeline.__class__(**pipeline.get_params(deep=False))
        modele.fit(features[entrainement], cible[entrainement])

        debut = time.perf_counter()
        predits = modele.predict(features[validation])
        latences.append((time.perf_counter() - debut) / len(validation) * 1000)
        probabilites = modele.predict_proba(features[validation])[:, 1]

        vrais = pd.Series(
            [CLASSE_POSITIVE if v else CLASSE_NEGATIVE for v in cible[validation]]
        )
        estimes = pd.Series(
            [CLASSE_POSITIVE if v else CLASSE_NEGATIVE for v in predits]
        )
        mesure = scores(vrais, estimes)
        positifs = int(cible[validation].sum())
        par_pli.append(
            {
                "repetition": decoupe.repetition,
                "pli": decoupe.pli,
                "taille": len(validation),
                "positifs": positifs,
                "f1": mesure["f1"] if positifs else None,
                "precision": mesure["precision"],
                "rappel": mesure["rappel"],
                "vrai_positif": mesure["vrai_positif"],
                "faux_positif": mesure["faux_positif"],
                "faux_negatif": mesure["faux_negatif"],
                "vrai_negatif": mesure["vrai_negatif"],
            }
        )

        predictions_par_repetition[decoupe.repetition][validation] = predits
        scores_par_repetition[decoupe.repetition][validation] = probabilites

    f1_valides = [p["f1"] for p in par_pli if p["f1"] is not None]

    vrais_complets = pd.Series(
        [CLASSE_POSITIVE if v else CLASSE_NEGATIVE for v in cible]
    )
    hors_pli_par_repetition = []
    for repetition in repetitions:
        estimes = pd.Series(
            [
                CLASSE_POSITIVE if v == 1 else CLASSE_NEGATIVE
                for v in predictions_par_repetition[repetition]
            ]
        )
        mesure = scores(vrais_complets, estimes)
        hors_pli_par_repetition.append(
            {
                "repetition": repetition,
                "f1": mesure["f1"],
                "precision": mesure["precision"],
                "rappel": mesure["rappel"],
                "vrai_positif": mesure["vrai_positif"],
                "faux_positif": mesure["faux_positif"],
                "faux_negatif": mesure["faux_negatif"],
                "roc_auc": round(
                    float(roc_auc_score(cible, scores_par_repetition[repetition])), 4
                ),
            }
        )

    predictions_cumulees = predictions_par_repetition[repetitions[0]]
    scores_cumules = scores_par_repetition[repetitions[0]]
    estimes_complets = pd.Series(
        [CLASSE_POSITIVE if v == 1 else CLASSE_NEGATIVE for v in predictions_cumulees]
    )
    hors_pli = pd.Series(scores(vrais_complets, estimes_complets))
    f1_hors_pli = [h["f1"] for h in hors_pli_par_repetition]
    auc_hors_pli = [h["roc_auc"] for h in hors_pli_par_repetition]

    # Empreinte mémoire du modèle ajusté sur la totalité de la calibration.
    tracemalloc.start()
    final = pipeline.__class__(**pipeline.get_params(deep=False))
    final.fit(features, cible)
    _, memoire_pic = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "candidat": nom,
        "plis_evalues": len(par_pli),
        "plis_sans_positif": len(par_pli) - len(f1_valides),
        "f1_moyen": round(float(np.mean(f1_valides)), 4),
        "f1_ecart_type": round(float(np.std(f1_valides)), 4),
        "f1_min": round(float(np.min(f1_valides)), 4),
        "f1_max": round(float(np.max(f1_valides)), 4),
        "precision_moyenne": round(float(np.mean([p["precision"] for p in par_pli])), 4),
        "rappel_moyen": round(float(np.mean([p["rappel"] for p in par_pli])), 4),
        "f1_hors_pli_moyen": round(float(np.mean(f1_hors_pli)), 4),
        "f1_hors_pli_ecart_type": round(float(np.std(f1_hors_pli)), 4),
        "f1_hors_pli_min": round(float(np.min(f1_hors_pli)), 4),
        "f1_hors_pli_max": round(float(np.max(f1_hors_pli)), 4),
        "roc_auc_hors_pli": round(float(np.mean(auc_hors_pli)), 4),
        "hors_pli_par_repetition": hors_pli_par_repetition,
        "matrice_hors_pli": hors_pli.to_dict(),
        "latence_ms_par_fenetre": round(float(np.mean(latences)), 4),
        "memoire_ajustement_ko": round(memoire_pic / 1024, 1),
        "par_pli": par_pli,
        "predictions_premiere_repetition": predictions_cumulees.tolist(),
        "scores_premiere_repetition": scores_cumules.tolist(),
    }


def importance_features(pipeline, table: pd.DataFrame, y: pd.Series, decoupes) -> pd.DataFrame:
    """Poids des features, moyennés sur les plis.

    Pour la régression logistique, le coefficient standardisé — le pipeline
    contient le `StandardScaler`, donc les coefficients sont comparables entre
    eux. Pour la forêt, l'importance de Gini.

    Les deux mesures ne sont pas de même nature et ne se comparent pas d'un
    candidat à l'autre : elles servent à voir **quelles familles de features
    portent le signal**, ce qui valide ou invalide l'arbitrage A3.
    """
    index = {identifiant: i for i, identifiant in enumerate(table[COLONNE_FENETRE])}
    features = table[NOMS_FEATURES].to_numpy()
    cible = y.to_numpy()

    poids = []
    for decoupe in decoupes:
        entrainement = [index[f] for f in decoupe.entrainement]
        modele = pipeline.__class__(**pipeline.get_params(deep=False))
        modele.fit(features[entrainement], cible[entrainement])
        estimateur = modele.named_steps["modele"]
        if hasattr(estimateur, "coef_"):
            poids.append(np.abs(estimateur.coef_[0]))
        else:
            poids.append(estimateur.feature_importances_)

    moyennes = np.mean(poids, axis=0)
    return (
        pd.DataFrame({"feature": NOMS_FEATURES, "poids": moyennes})
        .sort_values("poids", ascending=False)
        .reset_index(drop=True)
    )


def comparaison_appariee(
    table: pd.DataFrame, resultat: dict, baseline: dict, decoupes
) -> dict:
    """Compare candidat et baseline **sur les mêmes plis**, pli par pli.

    Comparer deux moyennes de F1 et leurs écarts-types est trop grossier ici :
    l'écart-type entre plis mesure surtout la difficulté inégale des plis, pas
    l'incertitude sur la différence. Un pli de 3 fenêtres dont 1 positive donne
    un F1 de 0 ou de 1 selon une seule prédiction — pour les **deux** méthodes.

    L'appariement annule cette difficulté commune : sur chaque pli, on mesure le
    F1 du candidat et celui de la baseline sur **les mêmes fenêtres**, et on
    regarde la distribution des différences. C'est la comparaison que le brief
    appelle « équitable ».

    Le nombre de plis où chacun gagne est rapporté en plus de la moyenne : sur
    25 plis dont beaucoup sont dégénérés, une moyenne de différences se laisse
    tirer par deux ou trois plis extrêmes.
    """
    index = {identifiant: i for i, identifiant in enumerate(table[COLONNE_FENETRE])}

    # Verdicts de la baseline, par fenêtre — figés, jamais recalculés.
    signalees = baseline["lignes_signalees_par_fenetre"]
    verdict_baseline = {
        fenetre: CLASSE_POSITIVE if n >= 2 else CLASSE_NEGATIVE
        for fenetre, n in signalees.items()
    }

    differences: list[dict] = []
    for pli, decoupe in zip(resultat["par_pli"], decoupes, strict=True):
        if pli["f1"] is None:
            continue
        fenetres_validation = list(decoupe.validation)
        vrais = pd.Series(
            [table.iloc[index[f]]["provenance"] for f in fenetres_validation]
        )
        estimes_baseline = pd.Series(
            [verdict_baseline[f] for f in fenetres_validation]
        )
        f1_baseline = scores(vrais, estimes_baseline)["f1"]
        differences.append(
            {
                "repetition": pli["repetition"],
                "pli": pli["pli"],
                "taille": pli["taille"],
                "f1_candidat": pli["f1"],
                "f1_baseline": f1_baseline,
                "difference": round(pli["f1"] - f1_baseline, 6),
            }
        )

    ecarts = np.array([d["difference"] for d in differences])
    gagnes = int((ecarts > 0).sum())
    perdus = int((ecarts < 0).sum())
    return {
        "plis_compares": len(differences),
        "plis_gagnes": gagnes,
        "plis_perdus": perdus,
        "plis_egaux": len(differences) - gagnes - perdus,
        "difference_moyenne": round(float(np.mean(ecarts)), 4),
        "difference_mediane": round(float(np.median(ecarts)), 4),
        "difference_ecart_type": round(float(np.std(ecarts)), 4),
        "difference_min": round(float(np.min(ecarts)), 4),
        "difference_max": round(float(np.max(ecarts)), 4),
        "par_pli": differences,
    }


def stabilite_par_segment(table: pd.DataFrame, resultat: dict) -> pd.DataFrame:
    """Comportement par capteur — exigé par le brief, et révélateur ici."""
    detail = table.copy()
    detail["predit"] = [
        CLASSE_POSITIVE if v == 1 else CLASSE_NEGATIVE
        for v in resultat["predictions_premiere_repetition"]
    ]
    lignes = []
    for capteur, groupe in detail.groupby("sensor_name", observed=True):
        mesure = scores(groupe["provenance"], groupe["predit"])
        lignes.append(
            {
                "candidat": resultat["candidat"],
                "segment": capteur,
                "fenetres": len(groupe),
                "fabriquees": int((groupe["provenance"] == CLASSE_POSITIVE).sum()),
                **{
                    cle: mesure[cle]
                    for cle in ("vrai_positif", "faux_positif", "faux_negatif", "f1")
                },
            }
        )
    return pd.DataFrame(lignes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="./results/modele", type=Path)
    arguments = parser.parse_args()
    sortie: Path = arguments.output
    sortie.mkdir(parents=True, exist_ok=True)

    lignes = charger_calibration()
    fenetres = table_fenetres(lignes)
    table = table_features(lignes, fenetres)
    y = etiquettes(table)
    decoupes = plis(fenetres)

    baseline = baseline_deux_niveaux()
    reference = baseline["par_fenetre"]["f1"]

    print(f"Features : {len(NOMS_FEATURES)} par fenêtre, aucune n'utilise le capteur ni l'équipement")
    print(f"Baseline M3 par fenêtre : F1 = {reference}\n")

    resultats = []
    segments = []
    for nom, pipeline in candidats().items():
        resultat = evaluer(nom, pipeline, table, y, decoupes)
        resultat["comparaison_appariee"] = comparaison_appariee(
            table, resultat, baseline, decoupes
        )
        resultat["importances"] = importance_features(
            pipeline, table, y, decoupes
        ).to_dict(orient="records")
        resultats.append(resultat)
        segments.append(stabilite_par_segment(table, resultat))

    entete = f"  {'candidat':<24} {'F1 moyen':>10} {'écart-type':>11} {'min':>7} {'max':>7} {'ROC-AUC':>9} {'lat. ms':>9}"
    print("Validation croisée — 5 plis × 5 répétitions")
    print(entete)
    for r in resultats:
        print(
            f"  {r['candidat']:<24} {r['f1_moyen']:>10.4f} {r['f1_ecart_type']:>11.4f} "
            f"{r['f1_min']:>7.4f} {r['f1_max']:>7.4f} {r['roc_auc_hors_pli']:>9.4f} "
            f"{r['latence_ms_par_fenetre']:>9.4f}"
        )

    print("\nComparaison de moyennes — lecture grossière")
    for r in resultats:
        ecart = r["f1_moyen"] - reference
        print(
            f"  {r['candidat']:<24} F1 {r['f1_moyen']:.4f} contre {reference:.4f} "
            f"— écart {ecart:+.4f}, dispersion entre plis {r['f1_ecart_type']:.4f}"
        )
    print("  → la dispersion entre plis mesure surtout leur difficulté inégale,")
    print("    qui pèse identiquement sur la baseline. Comparaison appariée ci-dessous.")

    print("\nComparaison appariée — candidat et baseline sur les mêmes plis")
    print(
        f"  {'candidat':<24} {'gagnés':>7} {'perdus':>7} {'égaux':>6} "
        f"{'diff. moy.':>11} {'écart-type':>11} {'min':>8} {'max':>8}"
    )
    for r in resultats:
        c = r["comparaison_appariee"]
        print(
            f"  {r['candidat']:<24} {c['plis_gagnes']:>7} {c['plis_perdus']:>7} "
            f"{c['plis_egaux']:>6} {c['difference_moyenne']:>11.4f} "
            f"{c['difference_ecart_type']:>11.4f} {c['difference_min']:>8.4f} "
            f"{c['difference_max']:>8.4f}"
        )

    print("\nF1 hors pli sur les 30 fenêtres — une prédiction par fenêtre, 5 partitions")
    print(
        f"  {'candidat':<24} {'F1 moyen':>10} {'écart-type':>11} {'min':>7} "
        f"{'max':>7} {'écart':>9}  verdict"
    )
    for r in resultats:
        ecart = r["f1_hors_pli_moyen"] - reference
        verdict = (
            "gain sur les 5 partitions" if r["f1_hors_pli_min"] > reference
            else "gain non systématique" if ecart > 0
            else "aucun gain"
        )
        print(
            f"  {r['candidat']:<24} {r['f1_hors_pli_moyen']:>10.4f} "
            f"{r['f1_hors_pli_ecart_type']:>11.4f} {r['f1_hors_pli_min']:>7.4f} "
            f"{r['f1_hors_pli_max']:>7.4f} {ecart:>+9.4f}  {verdict}"
        )
    print(f"  {'baseline M3':<24} {reference:>10.4f}")

    print("\nMatrice de confusion hors pli (30 fenêtres, première répétition)")
    print(f"  {'candidat':<24} {'VP':>4} {'FP':>4} {'FN':>4} {'VN':>4} {'F1':>8}")
    for r in resultats:
        m = r["matrice_hors_pli"]
        print(
            f"  {r['candidat']:<24} {m['vrai_positif']:>4} {m['faux_positif']:>4} "
            f"{m['faux_negatif']:>4} {m['vrai_negatif']:>4} {m['f1']:>8.4f}"
        )
    b = baseline["par_fenetre"]
    print(
        f"  {'baseline M3 (référence)':<24} {b['vrai_positif']:>4} {b['faux_positif']:>4} "
        f"{b['faux_negatif']:>4} {b['vrai_negatif']:>4} {b['f1']:>8.4f}"
    )

    segments_table = pd.concat(segments, ignore_index=True)
    print("\nStabilité par capteur (première répétition)")
    print(segments_table.to_string(index=False))

    pd.DataFrame(
        [{k: v for k, v in r.items() if not isinstance(v, (list, dict))} for r in resultats]
    ).to_csv(sortie / "comparaison.csv", index=False, encoding="utf-8")
    pd.concat(
        [pd.DataFrame(r["par_pli"]).assign(candidat=r["candidat"]) for r in resultats],
        ignore_index=True,
    ).to_csv(sortie / "par_pli.csv", index=False, encoding="utf-8")
    pd.concat(
        [
            pd.DataFrame(r["comparaison_appariee"]["par_pli"]).assign(candidat=r["candidat"])
            for r in resultats
        ],
        ignore_index=True,
    ).to_csv(sortie / "comparaison_appariee.csv", index=False, encoding="utf-8")
    segments_table.to_csv(sortie / "stabilite_segments.csv", index=False, encoding="utf-8")
    table[[COLONNE_FENETRE, "provenance", *NOMS_FEATURES]].to_csv(
        sortie / "features.csv", index=False, encoding="utf-8"
    )
    (sortie / "modele.json").write_text(
        json.dumps(
            {
                "features": NOMS_FEATURES,
                "baseline_par_fenetre": baseline["par_fenetre"],
                "seuil_acceptation": "F1 > baseline d'un écart supérieur à la dispersion entre plis",
                "resultats": resultats,
            },
            ensure_ascii=False, indent=2, default=str,
        ),
        encoding="utf-8",
    )
    print(f"\nSorties écrites dans {sortie}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
