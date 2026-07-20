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
import time
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
        f"**Seuil de revision humaine** : {CONFIDENCE_THRESHOLD:.2f}",
        "",
        "> Il ne s'agit pas de prouver que le modele est parfait, mais de",
        "> montrer qu'on sait l'integrer, observer son comportement et",
        "> documenter ses limites.",
        "",
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
