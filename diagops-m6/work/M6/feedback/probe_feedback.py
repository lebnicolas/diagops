#!/usr/bin/env python3
"""Éprouver les seuils de qualification du feedback — étape 6 du brief 1.

Le starter le dit lui-même : « les seuils sont volontairement explicites : ils
doivent être justifiés, corrigés et défendus, pas acceptés tels quels ». Ce banc
les déplace et mesure ce qui bascule, cherche ce que les règles ne voient pas, et
vérifie si les thèmes remontés par les utilisateurs recoupent ce que l'évaluation
a mesuré de son côté.

    python feedback/probe_feedback.py
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import feedback.qualify_feedback as qf
from tools import data_pack, reports_table

FEEDBACK = data_pack() / "2027-S1" / "feedback" / "feedback.csv"


def qualifier(rows: list[dict], known: set[str]) -> list[dict]:
    sortie = []
    for signal in qf.signals(rows, known):
        classe, motif = qf.classify(signal)
        sortie.append({**signal, "classe": classe, "motif": motif})
    return sortie


def sensibilite(rows: list[dict], known: set[str]) -> dict:
    """Ce qui bascule quand chaque seuil se déplace, les autres restant fixes."""
    mesures: dict[str, dict] = {}
    origine = (qf.NEAR_DUPLICATE_JACCARD, qf.MINIMUM_ACTIONABLE_LENGTH,
               qf.AUTHOR_CONCENTRATION_LIMIT)

    for valeur in (0.60, 0.70, 0.85, 0.95):
        qf.NEAR_DUPLICATE_JACCARD = valeur
        resultat = qualifier(rows, known)
        mesures[f"jaccard={valeur}"] = {
            "doublons": sum(
                1 for r in resultat if r["exact_duplicate_of"] or r["near_duplicate_of"]
            ),
            "actionnables": sum(1 for r in resultat if r["classe"] == "actionnable"),
        }
    qf.NEAR_DUPLICATE_JACCARD = origine[0]

    for valeur in (20, 30, 40, 60, 80):
        qf.MINIMUM_ACTIONABLE_LENGTH = valeur
        resultat = qualifier(rows, known)
        mesures[f"longueur={valeur}"] = {
            "actionnables": sum(1 for r in resultat if r["classe"] == "actionnable"),
            "non_actionnables": sum(1 for r in resultat if r["classe"] == "non_actionnable"),
        }
    qf.MINIMUM_ACTIONABLE_LENGTH = origine[1]

    for valeur in (0.05, 0.08, 0.10, 0.15, 0.25):
        qf.AUTHOR_CONCENTRATION_LIMIT = valeur
        resultat = qualifier(rows, known)
        mesures[f"concentration={valeur}"] = {
            "a_investiguer": sum(1 for r in resultat if r["classe"] == "a_investiguer"),
            "declenchements": sum(1 for r in resultat if r["author_over_represented"]),
        }
    qf.AUTHOR_CONCENTRATION_LIMIT = origine[2]

    return mesures


def doublons_inter_rapports(rows: list[dict]) -> list[dict]:
    """Commentaires identiques sur des rapports différents.

    Le starter ne cherche les doublons qu'à l'intérieur d'un même rapport. Un
    retour répété sur plusieurs rapports lui échappe — or c'est la forme que
    prend une campagne.
    """
    par_texte: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        par_texte[qf.normalize(row["comment"])].append(row)
    return [
        {
            "commentaire": texte[:90],
            "occurrences": len(lot),
            "rapports": sorted({r["report_id"] for r in lot}),
            "auteurs": sorted({r["submitted_by_id"] for r in lot}),
        }
        for texte, lot in par_texte.items()
        if len({r["report_id"] for r in lot}) > 1
    ]


def profil_des_risques(qualifie: list[dict], rows: list[dict]) -> dict:
    brut = {r["feedback_id"]: r for r in rows}
    risques = [r for r in qualifie if r["classe"] == "risque"]
    return {
        "total": len(risques),
        "par_motif": dict(Counter(r["motif"] for r in risques)),
        "auteurs": dict(Counter(r["author"] for r in risques)),
        "roles": dict(Counter(r["role"] for r in risques)),
        "part_des_auteurs_concernes": round(
            len({r["author"] for r in risques}) / len({r["author"] for r in qualifie}), 3
        ),
        "textes_distincts": len({qf.normalize(brut[r["feedback_id"]]["comment"]) for r in risques}),
    }


def couverture(qualifie: list[dict]) -> dict:
    rapports_connus = set(reports_table())
    couverts = {r["report_id"] for r in qualifie}
    periode_2027 = {r for r in rapports_connus if "2027" in r}
    return {
        "rapports_2027_S1": len(periode_2027),
        "rapports_avec_retour": len(couverts & periode_2027),
        "rapports_sans_retour": len(periode_2027 - couverts),
        "retours_sur_rapport_inconnu": sorted(
            r["report_id"] for r in qualifie if not r["known_report"]
        ),
    }


def themes_actionnables(qualifie: list[dict], rows: list[dict]) -> list[dict]:
    """Les sujets qui reviennent, avec un exemple lisible de chacun."""
    brut = {r["feedback_id"]: r["comment"] for r in rows}
    groupes: dict[str, list[str]] = defaultdict(list)
    for ligne in qualifie:
        if ligne["classe"] == "actionnable":
            groupes[ligne["theme"]].append(ligne["feedback_id"])
    classes = sorted(groupes.items(), key=lambda item: len(item[1]), reverse=True)
    return [
        {
            "theme": theme,
            "occurrences": len(identifiants),
            "exemple": brut[identifiants[0]][:120],
        }
        for theme, identifiants in classes[:8]
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "sondes_feedback.json")
    args = parser.parse_args()

    rows = qf.load_feedback(FEEDBACK, "all")
    known = set(reports_table())
    qualifie = qualifier(rows, known)

    rapport = {
        "lot": "b1 + b2",
        "retours": len(rows),
        "classes": dict(Counter(r["classe"] for r in qualifie)),
        "motifs": dict(Counter(r["motif"] for r in qualifie)),
        "profil_des_risques": profil_des_risques(qualifie, rows),
        "doublons_inter_rapports": doublons_inter_rapports(rows),
        "couverture": couverture(qualifie),
        "sensibilite_des_seuils": sensibilite(rows, known),
        "themes_actionnables": themes_actionnables(qualifie, rows),
        "concentration_auteurs": dict(
            Counter(r["author"] for r in qualifie).most_common(5)
        ),
        "roles": dict(Counter(r["role"] for r in qualifie)),
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(rapport, ensure_ascii=False, indent=2), encoding="utf-8", newline="",
    )

    print(f"{rapport['retours']} retours — {rapport['classes']}")
    print("\nmotifs de classement")
    for motif, compte in sorted(rapport["motifs"].items(), key=lambda i: -i[1]):
        print(f"  {compte:>3}  {motif}")
    print("\nsensibilité des seuils")
    for libelle, valeurs in rapport["sensibilite_des_seuils"].items():
        print(f"  {libelle:<22} {valeurs}")
    print("\ndoublons inter-rapports (invisibles pour le starter)")
    for item in rapport["doublons_inter_rapports"]:
        print(f"  ×{item['occurrences']} sur {len(item['rapports'])} rapports, "
              f"{len(item['auteurs'])} auteur(s) : {item['commentaire']}")
    print(f"\nRapport complet : {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
