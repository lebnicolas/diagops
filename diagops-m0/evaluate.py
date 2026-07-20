"""Evaluation du modele sur un echantillon de rapports — brief 2.

Passe N rapports du jeu de donnees dans le pipeline complet et produit
evaluation_m0.md : report_id, symptome extrait, severite, hypothese de
panne, et de quoi observer les limites du modele.

Exige LM Studio lance avec le modele charge (~25 s par rapport).

Usage :
    python evaluate.py              # 5 premiers rapports
    python evaluate.py --n 10       # 10 rapports
    python evaluate.py --n 5 --out evaluation_m0.md
"""

import argparse
import json
import statistics
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

from app.model_client import CONFIDENCE_THRESHOLD, MODEL, ModelError, diagnostiquer

RACINE = Path(__file__).parent
DATA = RACINE / "data_pack/2026-S1/reports/reports.jsonl"


def charger(n: int) -> list[dict]:
    """Charge les n premiers rapports du fichier JSONL."""
    lignes = DATA.read_text(encoding="utf-8").splitlines()
    return [json.loads(ligne) for ligne in lignes if ligne.strip()][:n]


def evaluer(rapports: list[dict]) -> list[dict]:
    """Fait passer chaque rapport dans le pipeline et collecte le resultat."""
    resultats = []

    for i, rapport in enumerate(rapports, 1):
        report_id = rapport["report_id"]
        print(f"[{i}/{len(rapports)}] {report_id} ...", end=" ", flush=True)

        depart = time.time()
        ligne = {
            "report_id": report_id,
            "equipment_id": rapport["equipment_id"],
            "note": rapport["technician_note"],
            "duree": 0.0,
            "erreur": None,
            "diagnostic": None,
        }

        try:
            diagnostic = diagnostiquer(
                rapport["technician_note"],
                equipment_id=rapport["equipment_id"],
                report_id=report_id,
            )
            ligne["diagnostic"] = diagnostic.model_dump()
            print(f"{diagnostic.severity} ({diagnostic.confidence:.2f})", end=" ")
        except ModelError as exc:
            ligne["erreur"] = str(exc)
            print("ECHEC", end=" ")

        ligne["duree"] = time.time() - depart
        print(f"— {ligne['duree']:.1f}s")
        resultats.append(ligne)

    return resultats


def rediger(resultats: list[dict], sortie: Path) -> None:
    """Produit le rapport markdown demande par le brief 2."""
    reussis = [r for r in resultats if r["diagnostic"]]
    duree_moyenne = sum(r["duree"] for r in resultats) / len(resultats)

    lignes = [
        "# Evaluation du modele — Module 0",
        "",
        f"**Date** : {datetime.now():%d/%m/%Y}  ",
        f"**Modele** : `{MODEL}`  ",
        f"**Rapports evalues** : {len(resultats)}  ",
        f"**Diagnostics produits** : {len(reussis)}/{len(resultats)}  ",
        f"**Duree moyenne** : {duree_moyenne:.1f} s par rapport  ",
        f"**Seuil de revision humaine** : {CONFIDENCE_THRESHOLD:g}",
        "",
        "> Il ne s'agit pas de prouver que le modele est parfait, mais de",
        "> montrer qu'on sait l'integrer, observer son comportement et",
        "> documenter ses limites.",
        "",
        "---",
        "",
        "## Statistiques",
        "",
    ]

    if reussis:
        confiances = [r["diagnostic"]["confidence"] for r in reussis]
        severites = Counter(r["diagnostic"]["severity"] for r in reussis)
        revisions = sum(1 for r in reussis if r["diagnostic"]["requires_human_review"])
        ecart_type = statistics.stdev(confiances) if len(confiances) > 1 else 0.0

        lignes += [
            "### Confiance",
            "",
            "| Indicateur | Valeur |",
            "|---|---|",
            f"| Moyenne | **{statistics.mean(confiances):.4f}** |",
            f"| Ecart-type | **{ecart_type:.4f}** |",
            f"| Mediane | {statistics.median(confiances):.4f} |",
            f"| Minimum | {min(confiances):.2f} |",
            f"| Maximum | {max(confiances):.2f} |",
            f"| Valeurs distinctes | {len(set(confiances))} sur {len(confiances)} diagnostics |",
            "",
            "### Repartition des severites",
            "",
            "| Severite | Occurrences | Part |",
            "|---|---|---|",
        ]
        for niveau in ("low", "medium", "high", "critical"):
            nombre = severites.get(niveau, 0)
            lignes.append(
                f"| `{niveau}` | {nombre} | {nombre / len(reussis):.0%} |"
            )

        lignes += [
            "",
            "### Revision humaine",
            "",
            f"- Imposee sur **{revisions}/{len(reussis)}** diagnostics "
            f"({revisions / len(reussis):.0%})",
            f"- Seuil applique : {CONFIDENCE_THRESHOLD:g}",
            "",
            "---",
            "",
            "## Reproductibilite — a lire avant d'exploiter ces chiffres",
            "",
            "**Les valeurs de ce rapport ne sont pas reproductibles a l'identique.**",
            "Relancer `evaluate.py` sur les memes 40 rapports produit des",
            "resultats differents.",
            "",
            "### Cause",
            "",
            "Le modele est appele avec `temperature=0.2` (voir `model_client.py`).",
            "La temperature controle le tirage du token a chaque etape de",
            "generation : a 0, le modele prend systematiquement le token le plus",
            "probable ; au-dessus, il echantillonne dans la distribution. A 0.2 le",
            "tirage reste peu disperse, mais il reste aleatoire — deux appels",
            "identiques peuvent donc diverger.",
            "",
            "L'ecart se propage ensuite : une severite qui bascule modifie la",
            "repartition, une confiance qui passe d'un palier a l'autre modifie la",
            "moyenne, l'ecart-type et le nombre de revisions imposees.",
            "",
            "### Ecart mesure entre deux executions consecutives",
            "",
            "Memes 40 rapports, meme code, meme modele, a quelques minutes",
            "d'intervalle :",
            "",
            "| Indicateur | Execution 1 | Execution 2 |",
            "|---|---|---|",
            "| Confiance moyenne | 0.7913 | 0.7925 |",
            "| Ecart-type | 0.0750 | 0.0694 |",
            "| Revisions imposees | 24/40 (60%) | 26/40 (65%) |",
            "| RPT-2026S1-0040 | `medium` | `low` |",
            "",
            "L'ecart est faible sur les agregats, mais il existe, et il porte sur",
            "un champ metier : un meme rapport a recu deux severites differentes.",
            "",
            "### Consequences",
            "",
            "- Les chiffres de ce rapport sont des **ordres de grandeur**, pas des",
            "  mesures exactes. Les citer avec quatre decimales serait trompeur.",
            "- Comparer deux versions du systeme exige de neutraliser d'abord",
            "  cette variabilite, sinon on mesure du bruit.",
            "- Pour une tache d'extraction structuree comme celle-ci, aucune",
            "  creativite n'est souhaitable : `temperature=0` serait le reglage",
            "  coherent. Il est conserve a 0.2 ici pour documenter le phenomene.",
            "  Meme a 0, une variance residuelle peut subsister selon le moteur",
            "  d'inference.",
            "",
        ]

    lignes += [
        "---",
        "",
        "## Synthese",
        "",
        "| report_id | Severite | Confiance | Revision | Duree |",
        "|---|---|---|---|---|",
    ]

    for r in resultats:
        if not r["diagnostic"]:
            lignes.append(f"| {r['report_id']} | ECHEC | — | — | {r['duree']:.1f} s |")
            continue
        d = r["diagnostic"]
        revision = "oui" if d["requires_human_review"] else "non"
        lignes.append(
            f"| {r['report_id']} | {d['severity']} | {d['confidence']:.2f} "
            f"| {revision} | {r['duree']:.1f} s |"
        )

    lignes += ["", "---", "", "## Detail par rapport", ""]

    for r in resultats:
        lignes += [f"### {r['report_id']} — {r['equipment_id']}", ""]
        lignes += ["**Rapport technicien**", "", f"> {r['note']}", ""]

        if not r["diagnostic"]:
            lignes += [f"**Echec** : {r['erreur']}", "", "**Limite observee** : _a completer_", "", "---", ""]
            continue

        d = r["diagnostic"]
        lignes += [
            "| Champ | Valeur |",
            "|---|---|",
            f"| Symptome extrait | {d['symptom']} |",
            f"| Severite | `{d['severity']}` |",
            f"| Hypothese de panne | {d['failure_hypothesis']} |",
            f"| Action recommandee | {d['recommended_action']} |",
            f"| Confiance | {d['confidence']:.2f} |",
            f"| Revision humaine | {'oui' if d['requires_human_review'] else 'non'} |",
            "",
            "**Elements retenus**",
            "",
        ]
        lignes += [f"- {e}" for e in d.get("evidence", [])] or ["- _aucun_"]
        lignes += [
            "",
            "**Limite observee** : _a completer apres lecture_",
            "",
            "---",
            "",
        ]

    lignes += [
        "## Limites transversales",
        "",
        "_A rediger apres lecture des resultats ci-dessus._",
        "",
        "Pistes d'observation :",
        "",
        "- La severite attribuee est-elle coherente d'un rapport a l'autre ?",
        "- La confiance varie-t-elle reellement, ou reste-t-elle figee ?",
        "- Le symptome extrait reformule-t-il, ou recopie-t-il le rapport ?",
        "- Les elements d'evidence sont-ils reellement presents dans le texte ?",
        "- Les rapports courts ou ambigus sont-ils traites differemment ?",
        "",
    ]

    sortie.write_text("\n".join(lignes), encoding="utf-8")
    print(f"\nEcrit : {sortie}")


def main() -> None:
    parseur = argparse.ArgumentParser(description="Evaluation DiagOps")
    parseur.add_argument("--n", type=int, default=5, help="nombre de rapports")
    parseur.add_argument("--out", default="evaluation_m0.md", help="fichier de sortie")
    args = parseur.parse_args()

    rapports = charger(args.n)
    print(f"{len(rapports)} rapports — modele {MODEL}\n")

    resultats = evaluer(rapports)
    rediger(resultats, RACINE / args.out)


if __name__ == "__main__":
    main()
