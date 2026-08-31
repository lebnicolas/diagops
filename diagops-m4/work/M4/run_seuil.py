"""Étape 3 bis — régler le seuil de décision avant de geler le candidat.

Toutes les métriques du benchmark sont calculées au seuil **0,5**, celui que
`predict()` applique par défaut. Ce n'est pas une décision, c'est un héritage de
bibliothèque : le F1 dépend du seuil, et la ROC-AUC de 0,737 indique que le
modèle ordonne les fenêtres nettement mieux que son F1 au seuil par défaut ne le
laisse croire.

Régler ce seuil est légitime — c'est de la calibration, pas du test. Mais le
régler **et** le mesurer sur les mêmes données donne un chiffre optimiste. Ce
script produit donc trois estimations, dont deux honnêtes et une volontairement
biaisée, pour rendre l'écart visible :

1. **seuil 0,5** — la référence du benchmark ;
2. **seuil réglé en validation imbriquée** — dans chaque pli externe, le seuil
   est choisi sur une validation interne du seul jeu d'entraînement, puis
   appliqué au pli de validation qu'il n'a jamais vu. C'est l'estimation
   défendable ;
3. **seuil optimisé sur l'ensemble** — borne haute, affichée pour montrer de
   combien la version 2 s'en écarte. **Ce chiffre ne doit jamais être rapporté
   comme une performance.**

Le test scellé n'est pas chargé.

Usage :
    python run_seuil.py [--output ./results/seuil]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from src.modele import NOMS_FEATURES, candidats, etiquettes, table_features
from src.protocole import (
    CLASSE_NEGATIVE,
    CLASSE_POSITIVE,
    COLONNE_FENETRE,
    COLONNE_GROUPE,
    SEED,
    baseline_deux_niveaux,
    charger_calibration,
    plis,
    scores,
    table_fenetres,
)


#: Grille de seuils explorée. Pas de 0,01 : sur 30 fenêtres, un pas plus fin
#: ferait croire à une précision que l'effectif ne porte pas.
SEUILS = np.round(np.arange(0.05, 0.96, 0.01), 2)

#: Plis de la validation interne, dans chaque pli externe. Trois plutôt que cinq :
#: le jeu d'entraînement d'un pli externe compte environ 24 fenêtres.
PLIS_INTERNES = 3


def f1_au_seuil(cible: np.ndarray, probabilites: np.ndarray, seuil: float) -> float:
    vrais = pd.Series([CLASSE_POSITIVE if v else CLASSE_NEGATIVE for v in cible])
    predits = pd.Series(
        [CLASSE_POSITIVE if p >= seuil else CLASSE_NEGATIVE for p in probabilites]
    )
    return scores(vrais, predits)["f1"]


def meilleur_seuil(cible: np.ndarray, probabilites: np.ndarray) -> tuple[float, float]:
    """Seuil maximisant le F1. À égalité, le plus proche de 0,5 l'emporte.

    Le départage n'est pas cosmétique : plusieurs seuils donnent souvent le même
    F1 sur 24 observations, et prendre le plus extrême de la plage reviendrait à
    régler sur du bruit.
    """
    resultats = [(f1_au_seuil(cible, probabilites, s), -abs(s - 0.5), s) for s in SEUILS]
    f1, _, seuil = max(resultats)
    return float(seuil), float(f1)


def seuil_imbrique(pipeline, features, cible, groupes, entrainement) -> float:
    """Règle le seuil sur le seul jeu d'entraînement du pli externe."""
    sous_features = features[entrainement]
    sous_cible = cible[entrainement]
    sous_groupes = groupes[entrainement]

    probabilites = np.full(len(entrainement), np.nan)
    decoupage = StratifiedGroupKFold(
        n_splits=PLIS_INTERNES, shuffle=True, random_state=SEED
    )
    for apprentissage, validation in decoupage.split(
        sous_features, sous_cible, groups=sous_groupes
    ):
        modele = pipeline.__class__(**pipeline.get_params(deep=False))
        modele.fit(sous_features[apprentissage], sous_cible[apprentissage])
        probabilites[validation] = modele.predict_proba(sous_features[validation])[:, 1]

    seuil, _ = meilleur_seuil(sous_cible, probabilites)
    return seuil


def evaluer_seuils(nom: str, pipeline, table, y, decoupes) -> dict:
    index = {identifiant: i for i, identifiant in enumerate(table[COLONNE_FENETRE])}
    features = table[NOMS_FEATURES].to_numpy()
    cible = y.to_numpy()
    groupes = table[COLONNE_GROUPE].to_numpy()

    repetitions = sorted({d.repetition for d in decoupes})
    probabilites = {r: np.full(len(table), np.nan) for r in repetitions}
    predits_imbrique = {r: np.full(len(table), -1) for r in repetitions}
    seuils_retenus: list[float] = []

    for decoupe in decoupes:
        entrainement = np.array([index[f] for f in decoupe.entrainement])
        validation = np.array([index[f] for f in decoupe.validation])

        modele = pipeline.__class__(**pipeline.get_params(deep=False))
        modele.fit(features[entrainement], cible[entrainement])
        probas = modele.predict_proba(features[validation])[:, 1]
        probabilites[decoupe.repetition][validation] = probas

        seuil = seuil_imbrique(pipeline, features, cible, groupes, entrainement)
        seuils_retenus.append(seuil)
        predits_imbrique[decoupe.repetition][validation] = (probas >= seuil).astype(int)

    par_repetition = []
    for repetition in repetitions:
        probas = probabilites[repetition]
        f1_defaut = f1_au_seuil(cible, probas, 0.5)
        seuil_oracle, f1_oracle = meilleur_seuil(cible, probas)

        vrais = pd.Series([CLASSE_POSITIVE if v else CLASSE_NEGATIVE for v in cible])
        estimes = pd.Series(
            [
                CLASSE_POSITIVE if v == 1 else CLASSE_NEGATIVE
                for v in predits_imbrique[repetition]
            ]
        )
        mesure_imbrique = scores(vrais, estimes)

        par_repetition.append(
            {
                "repetition": repetition,
                "f1_seuil_defaut": f1_defaut,
                "f1_seuil_imbrique": mesure_imbrique["f1"],
                "precision_imbrique": mesure_imbrique["precision"],
                "rappel_imbrique": mesure_imbrique["rappel"],
                "vrai_positif": mesure_imbrique["vrai_positif"],
                "faux_positif": mesure_imbrique["faux_positif"],
                "faux_negatif": mesure_imbrique["faux_negatif"],
                "f1_seuil_optimise_sur_tout": f1_oracle,
                "seuil_optimise_sur_tout": seuil_oracle,
            }
        )

    def resume(cle: str) -> dict[str, float]:
        valeurs = [r[cle] for r in par_repetition]
        return {
            "moyenne": round(float(np.mean(valeurs)), 4),
            "ecart_type": round(float(np.std(valeurs)), 4),
            "min": round(float(np.min(valeurs)), 4),
            "max": round(float(np.max(valeurs)), 4),
        }

    return {
        "candidat": nom,
        "seuil_defaut": 0.5,
        "seuils_imbriques": {
            "median": float(np.median(seuils_retenus)),
            "min": float(np.min(seuils_retenus)),
            "max": float(np.max(seuils_retenus)),
            "valeurs": seuils_retenus,
        },
        "f1_seuil_defaut": resume("f1_seuil_defaut"),
        "f1_seuil_imbrique": resume("f1_seuil_imbrique"),
        "f1_seuil_optimise_sur_tout": resume("f1_seuil_optimise_sur_tout"),
        "rappel_imbrique": resume("rappel_imbrique"),
        "precision_imbrique": resume("precision_imbrique"),
        "par_repetition": par_repetition,
    }


def courbe_seuil(pipeline, table, y, decoupes) -> pd.DataFrame:
    """F1, précision et rappel en fonction du seuil, hors pli — pour le document."""
    index = {identifiant: i for i, identifiant in enumerate(table[COLONNE_FENETRE])}
    features = table[NOMS_FEATURES].to_numpy()
    cible = y.to_numpy()

    premiere = [d for d in decoupes if d.repetition == 0]
    probas = np.full(len(table), np.nan)
    for decoupe in premiere:
        entrainement = [index[f] for f in decoupe.entrainement]
        validation = [index[f] for f in decoupe.validation]
        modele = pipeline.__class__(**pipeline.get_params(deep=False))
        modele.fit(features[entrainement], cible[entrainement])
        probas[validation] = modele.predict_proba(features[validation])[:, 1]

    lignes = []
    for seuil in SEUILS:
        vrais = pd.Series([CLASSE_POSITIVE if v else CLASSE_NEGATIVE for v in cible])
        predits = pd.Series(
            [CLASSE_POSITIVE if p >= seuil else CLASSE_NEGATIVE for p in probas]
        )
        mesure = scores(vrais, predits)
        lignes.append({"seuil": seuil, **{k: mesure[k] for k in ("precision", "rappel", "f1")}})
    return pd.DataFrame(lignes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="./results/seuil", type=Path)
    arguments = parser.parse_args()
    sortie: Path = arguments.output
    sortie.mkdir(parents=True, exist_ok=True)

    lignes = charger_calibration()
    fenetres = table_fenetres(lignes)
    table = table_features(lignes, fenetres)
    y = etiquettes(table)
    decoupes = plis(fenetres)
    reference = baseline_deux_niveaux()["par_fenetre"]["f1"]

    resultats = []
    for nom, pipeline in candidats().items():
        print(f"réglage du seuil — {nom} …")
        resultats.append(evaluer_seuils(nom, pipeline, table, y, decoupes))

    print(f"\nBaseline M3 : F1 = {reference}\n")
    print("F1 hors pli selon le traitement du seuil (5 partitions)")
    print(
        f"  {'candidat':<24} {'seuil 0,5':>18} {'seuil réglé (imbriqué)':>24} "
        f"{'optimisé sur tout':>20}"
    )
    for r in resultats:
        d, i, o = r["f1_seuil_defaut"], r["f1_seuil_imbrique"], r["f1_seuil_optimise_sur_tout"]
        print(
            f"  {r['candidat']:<24} {d['moyenne']:>10.4f} ±{d['ecart_type']:<6.4f} "
            f"{i['moyenne']:>16.4f} ±{i['ecart_type']:<6.4f} "
            f"{o['moyenne']:>12.4f} ±{o['ecart_type']:<6.4f}"
        )
    print("\n  (la dernière colonne est une borne haute, réglée et mesurée sur les mêmes")
    print("   données — elle n'est PAS une performance et ne sera jamais rapportée seule)")

    print("\nEffet sur le compromis précision / rappel — seuil réglé")
    print(f"  {'candidat':<24} {'précision':>10} {'rappel':>10} {'seuils retenus (médiane)':>26}")
    for r in resultats:
        print(
            f"  {r['candidat']:<24} {r['precision_imbrique']['moyenne']:>10.4f} "
            f"{r['rappel_imbrique']['moyenne']:>10.4f} "
            f"{r['seuils_imbriques']['median']:>26.2f}"
        )

    retenu = max(resultats, key=lambda r: r["f1_seuil_imbrique"]["moyenne"])
    print(f"\nCandidat en tête : {retenu['candidat']}")
    print(
        f"  seuils choisis par les 25 plis : de {retenu['seuils_imbriques']['min']:.2f} "
        f"à {retenu['seuils_imbriques']['max']:.2f}, médiane "
        f"{retenu['seuils_imbriques']['median']:.2f}"
    )

    pipeline_retenu = candidats()[retenu["candidat"]]
    courbe = courbe_seuil(pipeline_retenu, table, y, decoupes)
    courbe.to_csv(sortie / "courbe_seuil.csv", index=False, encoding="utf-8")
    meilleur = courbe.loc[courbe["f1"].idxmax()]
    print(
        f"  courbe hors pli (répétition 0) : F1 maximal {meilleur['f1']:.4f} "
        f"au seuil {meilleur['seuil']:.2f}"
    )

    pd.DataFrame(
        [
            {"candidat": r["candidat"], **p}
            for r in resultats
            for p in r["par_repetition"]
        ]
    ).to_csv(sortie / "par_repetition.csv", index=False, encoding="utf-8")
    (sortie / "seuil.json").write_text(
        json.dumps(
            {"baseline_par_fenetre": reference, "grille": SEUILS.tolist(), "resultats": resultats},
            ensure_ascii=False, indent=2, default=str,
        ),
        encoding="utf-8",
    )
    print(f"\nSorties écrites dans {sortie}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
