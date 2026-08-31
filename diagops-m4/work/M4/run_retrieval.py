"""Étape 4 du brief 1 M4 — trois baselines de retrieval, mesurées.

Sans retrieval, lexical, vectoriel. L'hybride n'est construit que si les deux
précédents sont stables — le brief le subordonne explicitement.

**Ce que ce script mesure, et ce qu'il ne mesure pas.** Il évalue la
**récupération** : les bons documents remontent-ils, les documents inadmissibles
restent-ils dehors. La génération citée et l'abstention sont l'étape 5.

L'évaluation porte sur les **12 questions de calibration**. Les 12 questions du
split `test` sont scellées (`answerable: null`) et ne sont pas ouvrables.

Usage :
    python run_retrieval.py [--output ./results/retrieval]
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

from src.corpus import (
    admissible_comme_preuve,
    charger_corpus,
    corpus_admissible,
    remplacants,
)
from src.io_contracts import load_questions
from src.retrieval import rank_lexical
from src.vectoriel import MODELE, charger_modele, construire_index, rechercher

QUESTIONS = Path("../../data_pack/2026-S1/rag_eval/questions.jsonl")
TOP_K = 3


REFORMULATIONS = Path("data/questions_reformulees.json")


def questions_reformulees(questions: list[dict]) -> list[dict]:
    """Les mêmes questions, reformulées sans le vocabulaire des documents.

    Le Recall@k sature à 1,000 dès k = 1 sur les questions d'origine : chaque
    document traite un sujet distinct et la question en reprend les termes. La
    mesure ne peut donc pas départager lexical et vectoriel — elle ne mesure pas
    le retrieval, elle mesure la facilité du corpus.

    Cette épreuve remplace chaque terme technique par un synonyme ou une
    périphrase. Un appariement par recouvrement de mots doit y perdre ce qu'un
    appariement sémantique conserve. Les documents attendus sont inchangés.
    """
    contenu = json.loads(REFORMULATIONS.read_text(encoding="utf-8"))
    table = contenu["reformulations"]
    reformulees = []
    for question in questions:
        if question["eval_id"] not in table:
            continue
        copie = dict(question)
        copie["question_origine"] = question["question"]
        copie["question"] = table[question["eval_id"]]
        reformulees.append(copie)
    return reformulees


def questions_calibration() -> list[dict]:
    return [q for q in load_questions(QUESTIONS) if q["split"] == "calibration"]


def attendus_par_statut(question: dict, corpus, role: str) -> dict[str, list[str]]:
    """Sépare les documents attendus selon qu'ils sont citables ou non.

    Deux questions attendent un document que le contrat exclut — l'une un
    document restreint au rôle, l'autre une révision `superseded`. Mesurer le
    rappel sans cette distinction **pénaliserait le comportement correct** : un
    système qui refuse de citer une note interdite serait compté en échec.
    """
    citables, non_citables = [], []
    for identifiant in question["expected_document_ids"]:
        document = corpus.get(identifiant)
        if document is None:
            continue
        (citables if admissible_comme_preuve(document, role)[0] else non_citables).append(
            identifiant
        )
    return {"citables": citables, "non_citables": non_citables}


def evaluer(nom: str, recherche, questions, corpus, top_k: int = TOP_K) -> dict:
    """Applique une stratégie de récupération aux 12 questions.

    `recherche` reçoit (requête, documents admissibles) et rend une liste
    ordonnée de `document_id`. L'admission est appliquée **avant** l'appel :
    aucune stratégie ne voit un document qu'elle n'a pas le droit de proposer.
    """
    substitutions = remplacants(corpus)
    detail, latences = [], []

    for question in questions:
        role = question["role"]
        admissibles = corpus_admissible(corpus, role)
        attendus = attendus_par_statut(question, corpus, role)

        debut = time.perf_counter()
        recuperes = recherche(question["question"], admissibles)[:top_k]
        latences.append((time.perf_counter() - debut) * 1000)

        citables = set(attendus["citables"])
        trouves = citables & set(recuperes)
        inadmissibles_recuperes = [
            identifiant
            for identifiant in recuperes
            if not admissible_comme_preuve(corpus[identifiant], role)[0]
        ]
        signalables = [
            f"{identifiant} → remplacé par {substitutions[identifiant]}"
            for identifiant in attendus["non_citables"]
            if identifiant in substitutions
        ]

        detail.append(
            {
                "strategie": nom,
                "eval_id": question["eval_id"],
                "role": role,
                "answerable": question["answerable"],
                "attendus_citables": ";".join(attendus["citables"]) or "",
                "attendus_non_citables": ";".join(attendus["non_citables"]) or "",
                "recuperes": ";".join(recuperes),
                "rappel": len(trouves) / len(citables) if citables else None,
                "premier_juste": bool(recuperes and recuperes[0] in citables),
                "rang_premier_attendu": next(
                    (i + 1 for i, d in enumerate(recuperes) if d in citables), None
                ),
                "documents_inadmissibles_recuperes": len(inadmissibles_recuperes),
                "signalement_possible": ";".join(signalables) or "",
                "risk_tags": ";".join(question["risk_tags"]),
            }
        )

    table = pd.DataFrame(detail)
    avec_attendu = table[table["rappel"].notna()]
    sans_preuve = table[table["rappel"].isna()]
    # `rang_premier_attendu` porte des None, que pandas convertit en NaN.
    # NaN est *truthy* : un filtre `if r` les laisse passer et 1/NaN pollue
    # la moyenne. Le filtre porte donc sur pd.notna, pas sur la vérité.
    rangs = [r for r in table["rang_premier_attendu"] if pd.notna(r)]

    return {
        "strategie": nom,
        "top_k": top_k,
        "questions": len(table),
        "questions_avec_preuve_citable": len(avec_attendu),
        "rappel_moyen": round(float(avec_attendu["rappel"].mean()), 4),
        "rappel_parfait": int((avec_attendu["rappel"] == 1.0).sum()),
        "hit_rate": round(float((avec_attendu["rappel"] > 0).mean()), 4),
        "precision_premier": round(float(avec_attendu["premier_juste"].mean()), 4),
        "mrr": round(float(np.mean([1 / r for r in rangs])), 4) if rangs else 0.0,
        "documents_inadmissibles_recuperes": int(
            table["documents_inadmissibles_recuperes"].sum()
        ),
        "questions_sans_preuve_citable": len(sans_preuve),
        "bruit_sur_questions_sans_preuve": int(
            sum(len(r.split(";")) if r else 0 for r in sans_preuve["recuperes"])
        ),
        "latence_ms_mediane": round(float(np.median(latences)), 3),
        "detail": detail,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="./results/retrieval", type=Path)
    arguments = parser.parse_args()
    sortie: Path = arguments.output
    sortie.mkdir(parents=True, exist_ok=True)

    corpus = charger_corpus()
    questions = questions_calibration()
    print(f"Corpus : {len(corpus)} documents, {sum(len(d.texte) for d in corpus.values())} octets")
    print(f"Questions de calibration : {len(questions)} (les 12 du split test sont scellées)\n")

    # --- baseline 1 : sans retrieval ---------------------------------------
    def sans_retrieval(requete, admissibles):
        return []

    # --- baseline 2 : lexical (fourni par le starter) ----------------------
    def lexical(requete, admissibles):
        documents = [
            {"document_id": identifiant, "text": document.texte}
            for identifiant, document in admissibles.items()
        ]
        return [item["document_id"] for item in rank_lexical(requete, documents, TOP_K)]

    # --- baseline 3 : vectoriel --------------------------------------------
    print(f"Chargement du modèle d'embeddings — {MODELE}")
    debut = time.perf_counter()
    modele = charger_modele()
    cout_chargement = time.perf_counter() - debut
    print(f"  chargé en {cout_chargement:.1f}s\n")

    textes = {identifiant: document.texte for identifiant, document in corpus.items()}
    index_complet = construire_index(modele, textes, prefixes=True)
    index_sans_prefixe = construire_index(modele, textes, prefixes=False)

    def vectoriel_avec(index):
        def recherche(requete, admissibles):
            resultats = rechercher(modele, index, requete, top_k=len(index.identifiants))
            return [
                identifiant
                for identifiant, _ in resultats
                if identifiant in admissibles
            ][:TOP_K]
        return recherche

    strategies = {
        "sans_retrieval": sans_retrieval,
        "lexical": lexical,
        "vectoriel": vectoriel_avec(index_complet),
        "vectoriel_sans_prefixe": vectoriel_avec(index_sans_prefixe),
    }

    resultats = [evaluer(nom, fn, questions, corpus) for nom, fn in strategies.items()]
    balayage = [
        evaluer(nom, fn, questions, corpus, top_k=k)
        for k in (1, 2, 3)
        for nom, fn in strategies.items()
        if nom != "sans_retrieval"
    ]

    print("Récupération — 12 questions, top_k = 3")
    print(
        f"  {'stratégie':<24} {'rappel':>8} {'hit rate':>9} {'1er juste':>10} "
        f"{'MRR':>7} {'inadmissibles':>14} {'latence ms':>11}"
    )
    for r in resultats:
        print(
            f"  {r['strategie']:<24} {r['rappel_moyen']:>8.4f} {r['hit_rate']:>9.4f} "
            f"{r['precision_premier']:>10.4f} {r['mrr']:>7.4f} "
            f"{r['documents_inadmissibles_recuperes']:>14} {r['latence_ms_mediane']:>11.3f}"
        )

    print("\nRecall@k — à k = 3 la mesure sature et ne discrimine plus rien")
    print(f"  {'stratégie':<24} {'k=1':>22} {'k=2':>22} {'k=3':>22}")
    for nom in ("lexical", "vectoriel", "vectoriel_sans_prefixe"):
        cellules = []
        for k in (1, 2, 3):
            r = next(x for x in balayage if x["strategie"] == nom and x["top_k"] == k)
            cellules.append(f"{r['rappel_moyen']:.3f}  (MRR {r['mrr']:.3f})")
        print(f"  {nom:<24} " + " ".join(f"{c:>22}" for c in cellules))

    print("\nCoût de l'index")
    print(f"  {'index vectoriel':<24} {index_complet.taille_octets} octets, "
          f"{index_complet.dimensions} dimensions, {len(index_complet.identifiants)} documents")
    print(f"  {'chargement du modèle':<24} {cout_chargement:.1f}s (une fois)")
    print(f"  {'index lexical':<24} 0 octet — construit à la volée")

    print("\nLes deux questions sans preuve citable")
    for r in resultats:
        print(
            f"  {r['strategie']:<24} {r['bruit_sur_questions_sans_preuve']} document(s) "
            f"proposé(s) sur {r['questions_sans_preuve_citable']} question(s)"
        )

    print("\nÉpreuve de robustesse lexicale — questions reformulées sans le")
    print("vocabulaire des documents (protocole figé dans data/questions_reformulees.json)")
    reformulees = questions_reformulees(questions)
    epreuve = [
        evaluer(f"{nom}_reformule", fn, reformulees, corpus, top_k=1)
        for nom, fn in strategies.items()
        if nom != "sans_retrieval"
    ]
    print(f"  {'stratégie':<24} {'Recall@1 origine':>18} {'Recall@1 reformulé':>20} {'écart':>9}")
    for r in epreuve:
        nom = r["strategie"].replace("_reformule", "")
        origine = next(
            x for x in balayage if x["strategie"] == nom and x["top_k"] == 1
        )["rappel_moyen"]
        print(
            f"  {nom:<24} {origine:>18.3f} {r['rappel_moyen']:>20.3f} "
            f"{r['rappel_moyen'] - origine:>+9.3f}"
        )
    resultats.extend(epreuve)

    detail = pd.concat([pd.DataFrame(r["detail"]) for r in resultats], ignore_index=True)
    detail.to_csv(sortie / "detail_questions.csv", index=False, encoding="utf-8")
    pd.DataFrame(
        [{k: v for k, v in r.items() if k != "detail"} for r in resultats]
    ).to_csv(sortie / "comparaison.csv", index=False, encoding="utf-8")
    (sortie / "retrieval.json").write_text(
        json.dumps(
            {
                "modele_embeddings": MODELE,
                "top_k": TOP_K,
                "index": {
                    "octets": index_complet.taille_octets,
                    "dimensions": index_complet.dimensions,
                    "documents": len(index_complet.identifiants),
                    "chargement_modele_s": round(cout_chargement, 2),
                },
                "resultats": resultats,
                "balayage_k": [
                    {k: v for k, v in r.items() if k != "detail"} for r in balayage
                ],
            },
            ensure_ascii=False, indent=2, default=str,
        ),
        encoding="utf-8",
    )
    print(f"\nSorties écrites dans {sortie}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
