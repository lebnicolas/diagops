"""Metriques stratifiees vu / nouveau a partir d'un fichier de predictions.

Motivation
----------
La stratification des exemples de validation selon leur proximite avec
l'entrainement — 65 exemples "vu" possedant un quasi-jumeau, 15 "nouveau" sans
equivalent — est ce qui a demasque la memorisation de `variation_2` : composite
100.00 sur les exemples vus, aucun gain sur les inedits.

Cette analyse avait ete conduite a la main lors du Brief 1. Aucun script n'en
avait ete conserve, ce qui la rendait non reproductible et exposait chaque
nouvelle experience a une methode de calcul legerement differente. Ce fichier
la fige.

Le groupe de chaque `annotation_id` est LU dans
`work/evidence/validation_proximite_train.json`, produit avant la decision
intermediaire et non recalcule ici : la partition reste celle qui a servi a
tous les systemes deja mesures. Les metriques sont calculees par
`src.metrics.calculate_metrics`, la fonction meme qu'utilise `src/evaluate.py`,
appliquee au sous-ensemble des enregistrements. Aucune reimplementation.

Ce fichier est un AJOUT au starter. Aucun fichier de `src/` n'est modifie.

Verification
------------
L'option `--verify` recalcule les groupes d'un systeme deja publie et compare
aux valeurs consignees dans `work/metrics_m1.csv`. Un ecart signale que la
methode de calcul a devie de celle du Brief 1.

Usage
-----
    python -m tools.stratified_metrics \
        --predictions work/variation_4_validation/predictions.jsonl \
        --systeme variation_4 \
        --output work/variation_4_validation/stratified.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from src.metrics import SEVERITIES, calculate_metrics

GROUPS_PATH = Path("work/evidence/validation_proximite_train.json")


def read_predictions(path: Path) -> list[dict[str, Any]]:
    """Lecture brute du fichier de predictions.

    `src.dataset.load_jsonl` valide le schema des ANNOTATIONS (input_text,
    expected_output...) et rejette donc un fichier de predictions, qui porte
    d'autres champs. On lit ici sans validation de schema.
    """
    records: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def load_groups(path: Path) -> dict[str, str]:
    entries = json.loads(path.read_text(encoding="utf-8"))
    return {entry["annotation_id"]: entry["groupe"] for entry in entries}


def per_class_f1(records: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """F1 et effectifs par niveau de gravite.

    Le macro-F1 moyenne les quatre niveaux et masque la classe faible. Sur un
    outil de maintenance, rater `critical` ne coute pas le meme prix que rater
    `low` : le detail par classe est publie a part.
    """
    parsed = [record.get("parsed_output") for record in records]
    expected = [record["expected_output"] for record in records]
    predicted = [
        value.get("severity") if isinstance(value, dict) else None
        for value in parsed
    ]
    references = [ref["severity"] for ref in expected]

    detail: dict[str, dict[str, float]] = {}
    for label in SEVERITIES:
        tp = sum(p == label and r == label for p, r in zip(predicted, references))
        fp = sum(p == label and r != label for p, r in zip(predicted, references))
        fn = sum(p != label and r == label for p, r in zip(predicted, references))
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0.0
        )
        detail[label] = {
            "f1": f1,
            "precision": precision,
            "rappel": recall,
            "attendus": tp + fn,
            "detectes": tp,
        }
    return detail


def stratify(
    records: list[dict[str, Any]], groups: dict[str, str]
) -> dict[str, dict[str, Any]]:
    buckets: dict[str, list[dict[str, Any]]] = {"vu": [], "nouveau": [], "tous": []}
    manquants: list[str] = []
    for record in records:
        annotation_id = record["annotation_id"]
        groupe = groups.get(annotation_id)
        if groupe is None:
            manquants.append(annotation_id)
            continue
        buckets[groupe].append(record)
        buckets["tous"].append(record)

    if manquants:
        raise SystemExit(
            "Ces annotations n'ont pas de groupe dans "
            f"{GROUPS_PATH} : {', '.join(manquants)}. La partition doit couvrir "
            "exactement le fichier de validation evalue."
        )

    resultats: dict[str, dict[str, Any]] = {}
    for groupe, subset in buckets.items():
        metriques = dict(calculate_metrics(subset))
        metriques["severity_par_classe"] = per_class_f1(subset)
        resultats[groupe] = metriques
    return resultats


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--predictions", required=True, type=Path)
    parser.add_argument("--systeme", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--groups",
        type=Path,
        default=GROUPS_PATH,
        help="partition vu/nouveau gelee avant la decision intermediaire",
    )
    parser.add_argument(
        "--verify",
        nargs=2,
        metavar=("COMPOSITE_VU", "COMPOSITE_NOUVEAU"),
        type=float,
        help="valeurs publiees a retrouver, pour controler la methode de calcul",
    )
    args = parser.parse_args()

    records = read_predictions(args.predictions)
    groups = load_groups(args.groups)
    resultats = stratify(records, groups)

    charge = {
        "systeme": args.systeme,
        "predictions": str(args.predictions),
        "partition": str(args.groups),
        "groupes": resultats,
    }

    for groupe in ("vu", "nouveau", "tous"):
        bloc = resultats[groupe]
        print(
            f"{groupe:8s} n={bloc['examples']:3d} "
            f"composite={bloc['composite_score']:7.4f} "
            f"macro_f1={bloc['severity_macro_f1']:.4f} "
            f"schema={bloc['schema_valid_rate']:.4f} "
            f"lexical={bloc['text_lexical_f1']:.4f}"
        )
    ecart = resultats["vu"]["composite_score"] - resultats["nouveau"]["composite_score"]
    print(f"ecart vu-nouveau = {ecart:.4f}")
    charge["ecart_vu_nouveau"] = ecart

    if args.verify:
        attendu_vu, attendu_nouveau = args.verify
        obtenu_vu = resultats["vu"]["composite_score"]
        obtenu_nouveau = resultats["nouveau"]["composite_score"]
        derive_vu = abs(obtenu_vu - attendu_vu)
        derive_nouveau = abs(obtenu_nouveau - attendu_nouveau)
        print(
            f"controle : vu {obtenu_vu:.4f} vs {attendu_vu:.4f} "
            f"(ecart {derive_vu:.4f}) | nouveau {obtenu_nouveau:.4f} vs "
            f"{attendu_nouveau:.4f} (ecart {derive_nouveau:.4f})"
        )
        if max(derive_vu, derive_nouveau) > 0.01:
            raise SystemExit(
                "ECHEC DU CONTROLE : la methode de calcul a devie de celle du "
                "Brief 1. Ne pas publier les metriques stratifiees tant que "
                "l'ecart n'est pas explique."
            )
        print("controle OK : methode de calcul identique a celle du Brief 1")

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(charge, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"ecrit : {args.output}")


if __name__ == "__main__":
    main()
