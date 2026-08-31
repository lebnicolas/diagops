"""Étape 5 du brief 1 M4 — génération citée, abstention et signalements.

Mesure trois choses que le retrieval seul ne dit pas :

- **l'exactitude des citations** — chaque `document_id` cité se résout-il vers un
  document admissible du manifeste, et l'extrait est-il un fragment **littéral**
  du document ;
- **la qualité des refus** — les questions sans réponse déclenchent-elles une
  abstention, et les questions répondables sont-elles bien répondues ;
- **les signalements** — un conflit de révision ou un document restreint est-il
  annoncé plutôt que masqué.

Le test scellé n'est pas ouvert : évaluation sur les 12 questions de calibration.

Usage :
    python run_generation.py [--output ./results/generation]
"""

from __future__ import annotations

import argparse
import json
import warnings
from pathlib import Path

import pandas as pd

warnings.filterwarnings("ignore")

from src.corpus import charger_corpus, corpus_admissible, remplacants
from src.generation import COUVERTURE_MINIMALE, REGLES, couverture, repondre
from src.grounded_answer import validate_citations
from src.io_contracts import load_questions
from src.vectoriel import MODELE, charger_modele, construire_index, rechercher

QUESTIONS = Path("../../data_pack/2026-S1/rag_eval/questions.jsonl")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="./results/generation", type=Path)
    arguments = parser.parse_args()
    sortie: Path = arguments.output
    sortie.mkdir(parents=True, exist_ok=True)

    corpus = charger_corpus()
    substitutions = remplacants(corpus)
    questions = [
        q for q in load_questions(QUESTIONS) if q["split"] == "calibration"
    ]

    modele = charger_modele()
    index = construire_index(modele, {i: d.texte for i, d in corpus.items()})

    lignes, traces = [], []
    for question in questions:
        role = question["role"]
        admissibles = corpus_admissible(corpus, role)
        classement = [
            identifiant
            for identifiant, _ in rechercher(
                modele, index, question["question"], top_k=len(corpus)
            )
            if identifiant in admissibles
        ]

        resultat = repondre(
            question["question"], role, corpus, classement, substitutions
        )
        reponse = resultat.reponse

        # Contrat du starter : une abstention ne cite rien, une réponse cite au
        # moins une source admissible.
        erreurs_contrat = validate_citations(reponse, set(admissibles))

        # Fidélité : chaque extrait doit être un fragment littéral du document.
        infidelites = [
            citation.document_id
            for citation in reponse.citations
            if citation.excerpt not in corpus[citation.document_id].texte
        ]

        attendu_abstention = question["answerable"] is False
        lignes.append(
            {
                "eval_id": question["eval_id"],
                "role": role,
                "answerable": question["answerable"],
                "regle": resultat.regle,
                "abstenu": reponse.abstained,
                "abstention_correcte": reponse.abstained == attendu_abstention,
                "citations": ";".join(c.document_id for c in reponse.citations),
                "citations_valides": not erreurs_contrat,
                "extraits_litteraux": not infidelites,
                "signalements": len(resultat.signalements),
                "erreurs_contrat": ";".join(erreurs_contrat),
                "risk_tags": ";".join(question["risk_tags"]),
            }
        )
        traces.append(
            {
                "eval_id": question["eval_id"],
                "question": question["question"],
                "role": role,
                "regle": resultat.regle,
                "motif": resultat.motif,
                "abstenu": reponse.abstained,
                "reponse": reponse.answer,
                "interpretation": reponse.interpretation,
                "citations": [
                    {"document_id": c.document_id, "extrait": c.excerpt}
                    for c in reponse.citations
                ],
                "signalements": list(resultat.signalements),
                "couvertures": {
                    identifiant: round(couverture(question["question"], corpus[identifiant]), 3)
                    for identifiant in classement[:3]
                },
            }
        )

    table = pd.DataFrame(lignes)

    print(f"Génération extractive — {len(table)} questions de calibration")
    print(f"Seuil de couverture : {COUVERTURE_MINIMALE:.0%} des termes porteurs\n")

    print(f"  {'eval_id':<14} {'ans':<6} {'règle':<9} {'abstenu':<8} {'juste':<6} {'citations':<40} sig.")
    for _, r in table.iterrows():
        print(
            f"  {r['eval_id']:<14} {str(r['answerable']):<6} {r['regle']:<9} "
            f"{str(r['abstenu']):<8} {'oui' if r['abstention_correcte'] else 'NON':<6} "
            f"{r['citations'][:38]:<40} {r['signalements']}"
        )

    repondables = table[table["answerable"] == True]  # noqa: E712
    non_repondables = table[table["answerable"] == False]  # noqa: E712

    print("\nQualité des refus")
    print(f"  questions répondables      {len(repondables):>2} — répondues : "
          f"{int((~repondables['abstenu']).sum())}, abstenues à tort : "
          f"{int(repondables['abstenu'].sum())}")
    print(f"  questions sans réponse     {len(non_repondables):>2} — abstenues : "
          f"{int(non_repondables['abstenu'].sum())}, répondues à tort : "
          f"{int((~non_repondables['abstenu']).sum())}")
    print(f"  décisions correctes        {int(table['abstention_correcte'].sum())} / {len(table)}")

    print("\nContrat de citation")
    print(f"  citations valides          {int(table['citations_valides'].sum())} / {len(table)}")
    print(f"  extraits littéraux         {int(table['extraits_litteraux'].sum())} / {len(table)}")
    print(f"  signalements produits      {int(table['signalements'].sum())}")

    print("\nRègles déclenchées")
    for regle, nombre in table["regle"].value_counts().items():
        print(f"  {regle}  {nombre:>2}  {REGLES[regle]}")

    table.to_csv(sortie / "evaluation.csv", index=False, encoding="utf-8")
    with (sortie / "traces.jsonl").open("w", encoding="utf-8") as handle:
        for trace in traces:
            handle.write(json.dumps(trace, ensure_ascii=False) + "\n")
    (sortie / "generation.json").write_text(
        json.dumps(
            {
                "modele_embeddings": MODELE,
                "generation": "extractive — aucun modèle génératif",
                "seuil_couverture": COUVERTURE_MINIMALE,
                "regles": REGLES,
                "decisions_correctes": int(table["abstention_correcte"].sum()),
                "questions": len(table),
                "citations_valides": int(table["citations_valides"].sum()),
                "extraits_litteraux": int(table["extraits_litteraux"].sum()),
                "signalements": int(table["signalements"].sum()),
            },
            ensure_ascii=False, indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\nSorties écrites dans {sortie}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
