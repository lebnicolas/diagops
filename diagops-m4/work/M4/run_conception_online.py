"""Brief 1 online M4 — sondages de faisabilité pour le dossier de conception.

Ce script **n'entraîne pas un système** : il produit les mesures qui étayent
`docs/dossier_conception_m4.md`. Trois questions, dans cet ordre :

1. quelle est la vraie unité d'observation du corpus d'annotations ?
2. que valent les familles de modèles candidates ?
3. l'exactitude est-elle une métrique acceptable pour ce besoin ?

**Tout est mesuré sur le seul jeu d'entraînement.** `diagops_test.jsonl` porte
ses étiquettes — ce n'est pas un oracle scellé — mais la discipline du brief
présentiel est conservée : il n'est pas ouvert ici.

Usage :
    python run_conception_online.py [--output ./results/conception]
"""

from __future__ import annotations

import argparse
import json
import re
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, f1_score
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import (
    StratifiedGroupKFold,
    StratifiedKFold,
    cross_val_predict,
)
from sklearn.pipeline import Pipeline

ANNOTATIONS = Path("../../data_pack/2026-S1/annotations")
RAPPORTS = Path("../../data_pack/2026-S1/reports/reports.jsonl")
SEED = 20260831
CLASSES = ("critical", "high", "medium", "low")

#: Mots-clés d'une baseline à règles. Écrits à la main, sans regarder les
#: résultats — c'est ce qui en fait une baseline et non un modèle ajusté.
MOTS_CLES = {
    "critical": ["arret immediat", "securite", "fumee", "incendie", "urgence"],
    "high": ["fuite", "bruit metallique", "vibration forte", "surchauffe"],
    "low": ["leger", "mineur", "rien a signaler", "normal", "sans anomalie"],
}


def charger(nom: str) -> list[dict]:
    chemin = ANNOTATIONS / f"diagops_{nom}.jsonl"
    return [json.loads(l) for l in chemin.read_text(encoding="utf-8").splitlines() if l.strip()]


def patron(texte: str) -> str:
    """Squelette d'un rapport : identifiants et nombres neutralisés.

    Deux rapports qui ne diffèrent que par « Equipement-1 » / « Equipement-3 »
    partagent le même patron. C'est l'unité qui compte : les 400 textes du train
    n'en comptent que 80.
    """
    corps = texte.split("Rapport technicien:")[-1].lower()
    corps = re.sub(r"[a-z]{2,}-?\d+", "#", corps)   # EQ-PUMP-001, Equipement-3
    corps = re.sub(r"\d+([.,]\d+)?", "#", corps)     # nombres
    corps = re.sub(r"[^a-z# ]", " ", corps)
    return " ".join(corps.split())[:80]


def regle(texte: str) -> str:
    """Baseline à règles — mots-clés, `medium` par défaut."""
    minuscule = texte.lower()
    for gravite in ("critical", "high", "low"):
        if any(mot in minuscule for mot in MOTS_CLES[gravite]):
            return gravite
    return "medium"


def pipeline_supervise() -> Pipeline:
    return Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
            (
                "clf",
                LogisticRegression(
                    max_iter=2000, class_weight="balanced", random_state=SEED
                ),
            ),
        ]
    )


def mesures(vrais, predits) -> dict[str, float]:
    return {
        "exactitude": round(accuracy_score(vrais, predits), 4),
        "f1_macro": round(f1_score(vrais, predits, average="macro", zero_division=0), 4),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="./results/conception", type=Path)
    sortie: Path = parser.parse_args().output
    sortie.mkdir(parents=True, exist_ok=True)

    train, test = charger("train"), charger("test")
    X = [a["input_text"] for a in train]
    y = np.array([a["expected_output"]["severity"] for a in train])
    groupes = np.array([patron(t) for t in X])

    # --- 1. la cible dérivée ------------------------------------------------
    croisement = Counter(
        (a["expected_output"]["severity"], a["expected_output"]["requires_human_review"])
        for a in train + test
    )
    print("1. `requires_human_review` est-il une cible ou une conséquence ?")
    print(f"   {'gravité':<10} {'revue':>6} {'sans':>6}")
    for gravite in CLASSES:
        print(
            f"   {gravite:<10} {croisement[(gravite, True)]:>6} "
            f"{croisement[(gravite, False)]:>6}"
        )
    deductible = all(croisement[(g, False)] == 0 for g in ("critical", "high", "medium"))
    print(f"   → déductible de la gravité au-dessus de `low` : {deductible}")

    # --- 2. l'unité d'observation ------------------------------------------
    print(f"\n2. Unité d'observation — {len(set(groupes))} patrons pour {len(X)} textes")
    matrice = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True).fit_transform(X)
    similarites = cosine_similarity(matrice)
    np.fill_diagonal(similarites, 0)
    voisin = similarites.argmax(axis=1)
    print(f"   similarité moyenne au plus proche voisin : {similarites.max(axis=1).mean():.3f}")
    print(f"   paires au-dessus de 0,8 : {int((similarites > 0.8).sum() // 2)}")
    print(f"   plus proche voisin de même gravité : {(y[voisin] == y).mean():.1%}")
    purs = sum(
        1 for g in set(groupes) if len(set(y[groupes == g])) == 1
    )
    print(f"   patrons à gravité unique : {purs} / {len(set(groupes))}")

    # --- 3. les familles ----------------------------------------------------
    print("\n3. Familles de modèles — validation croisée sur le train")
    resultats = []

    predits_regles = [regle(t) for t in X]
    resultats.append({"famille": "F1 — règles", "decoupage": "sans objet", **mesures(y, predits_regles)})

    trivial = DummyClassifier(strategy="most_frequent").fit(X, y).predict(X)
    resultats.append({"famille": "baseline triviale", "decoupage": "sans objet", **mesures(y, trivial)})

    par_ligne = cross_val_predict(
        pipeline_supervise(), X, y,
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED),
    )
    resultats.append({"famille": "F2 — supervisé", "decoupage": "par ligne", **mesures(y, par_ligne)})

    par_patron = cross_val_predict(
        pipeline_supervise(), X, y,
        cv=StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEED),
        groups=groupes,
    )
    resultats.append({"famille": "F2 — supervisé", "decoupage": "groupé par patron", **mesures(y, par_patron)})

    table = pd.DataFrame(resultats)
    print(f"   {'famille':<20} {'découpage':<20} {'exactitude':>11} {'F1 macro':>10}")
    for _, r in table.iterrows():
        print(f"   {r['famille']:<20} {r['decoupage']:<20} {r['exactitude']:>11.4f} {r['f1_macro']:>10.4f}")

    ecart_exact = table.iloc[3]["exactitude"] - table.iloc[2]["exactitude"]
    ecart_f1 = table.iloc[3]["f1_macro"] - table.iloc[2]["f1_macro"]
    print(f"\n   Coût de la fuite par découpage : {ecart_exact:+.3f} d'exactitude, {ecart_f1:+.3f} de F1 macro")

    # --- 4. l'exactitude est-elle acceptable ? -----------------------------
    print("\n4. L'exactitude peut-elle servir de métrique de décision ?")
    regles_m, trivial_m = mesures(y, predits_regles), mesures(y, trivial)
    print(f"   règles          : exactitude {regles_m['exactitude']:.3f} | F1 macro {regles_m['f1_macro']:.3f}")
    print(f"   classe majoritaire : exactitude {trivial_m['exactitude']:.3f} | F1 macro {trivial_m['f1_macro']:.3f}")
    print("   → exactitude identique, F1 macro dans un rapport de 3 : non, l'exactitude ne convient pas")

    print("\n5. Rapport détaillé — F2 en découpage groupé")
    print(classification_report(y, par_patron, digits=3, zero_division=0))

    # --- 5. intégrité et décalage -----------------------------------------
    rapports = [json.loads(l) for l in RAPPORTS.read_text(encoding="utf-8").splitlines() if l.strip()]
    ids_rapports = {r["report_id"] for r in rapports}
    ids_cites = {a["report_id"] for a in train + test}
    orphelins = ids_cites - ids_rapports

    part_train = {g: sum(y == g) / len(y) for g in CLASSES}
    y_test = [a["expected_output"]["severity"] for a in test]
    part_test = {g: y_test.count(g) / len(y_test) for g in CLASSES}
    variation = 0.5 * sum(abs(part_train[g] - part_test[g]) for g in CLASSES)

    print("\n6. Défauts de données")
    print(f"   report_id cités sans rapport correspondant : {len(orphelins)} / {len(ids_cites)}")
    print(f"   distance de variation totale train/test    : {variation:.3f}")
    for gravite in CLASSES:
        print(f"     {gravite:<10} train {part_train[gravite]:>6.1%}  test {part_test[gravite]:>6.1%}")

    table.to_csv(sortie / "familles.csv", index=False, encoding="utf-8")
    (sortie / "conception.json").write_text(
        json.dumps(
            {
                "besoin": "qualifier la gravité d'un rapport technicien en texte libre",
                "cible": "severity",
                "cible_derivee": {
                    "champ": "requires_human_review",
                    "deductible_au_dessus_de_low": deductible,
                },
                "unite_observation": {
                    "textes": len(X),
                    "patrons": len(set(groupes)),
                    "patrons_a_gravite_unique": purs,
                    "similarite_moyenne_plus_proche_voisin": round(
                        float(similarites.max(axis=1).mean()), 4
                    ),
                },
                "familles": resultats,
                "cout_fuite_decoupage": {
                    "exactitude": round(float(ecart_exact), 4),
                    "f1_macro": round(float(ecart_f1), 4),
                },
                "defauts_donnees": {
                    "report_id_orphelins": len(orphelins),
                    "report_id_cites": len(ids_cites),
                    "distance_variation_train_test": round(variation, 4),
                    "distribution_train": {k: round(v, 4) for k, v in part_train.items()},
                    "distribution_test": {k: round(v, 4) for k, v in part_test.items()},
                },
                "test_ouvert": False,
            },
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nSorties écrites dans {sortie}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
