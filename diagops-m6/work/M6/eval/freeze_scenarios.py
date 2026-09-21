#!/usr/bin/env python3
"""Validation et gel du jeu de scénarios — étape 3 du brief 1.

Un jeu de scénarios se gèle avant toute mesure comparative. Avant de geler, il
se valide : un scénario qui attend un outil inexistant, un argument que le
contrat refuse ou une preuve absente du data pack ne mesure rien — il produit un
échec permanent qu'on finit par prendre pour une propriété de l'agent.

Ce script contrôle les deux fichiers sources, les concatène dans le jeu gelé et
écrit le manifeste de gel avec les empreintes.

    python eval/freeze_scenarios.py [--check]

`--check` valide et compare aux empreintes du manifeste sans rien réécrire :
c'est la forme utilisable en intégration continue.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.registry import ArgumentError, default_registry
from tools import equipment_table, events_table, knowledge_documents, maintenance_table, reports_table

SOURCES = (ROOT / "eval" / "scenarios.jsonl", ROOT / "eval" / "scenarios_extension.jsonl")
GELE = ROOT / "eval" / "scenarios_v2.jsonl"
MANIFESTE = ROOT / "eval" / "GEL.md"

CHAMPS_REQUIS = {
    "scenario_id", "category", "question", "role", "expected_tools",
    "forbidden_tools", "minimal_arguments", "expected_evidence", "expectation",
}
ROLES = {"technicien", "superviseur", "auditeur", "public"}
ATTENTES = {"answer", "refuse"}


def empreinte(chemin: Path) -> str:
    return hashlib.sha256(chemin.read_bytes()).hexdigest()


def references_connues() -> set[str]:
    """Tout identifiant citable comme preuve, lu dans le data pack."""
    connues = {document["document_id"] for document in knowledge_documents()}
    connues |= set(equipment_table())
    connues |= {ligne["event_id"] for ligne in events_table()}
    connues |= {ligne["maintenance_id"] for ligne in maintenance_table()}
    connues |= set(reports_table())
    return connues


def valider(scenarios: list[dict]) -> tuple[list[str], list[str]]:
    registre = default_registry()
    outils = set(registre.names())
    connues = references_connues()
    erreurs: list[str] = []
    avertissements: list[str] = []
    vus: set[str] = set()

    for scenario in scenarios:
        identifiant = scenario.get("scenario_id", "<sans id>")

        manquants = CHAMPS_REQUIS - set(scenario)
        if manquants:
            erreurs.append(f"{identifiant} : champs manquants {sorted(manquants)}")
            continue
        if identifiant in vus:
            erreurs.append(f"{identifiant} : identifiant en double")
        vus.add(identifiant)

        if scenario["role"] not in ROLES:
            erreurs.append(f"{identifiant} : rôle inconnu {scenario['role']}")
        if scenario["expectation"] not in ATTENTES:
            erreurs.append(f"{identifiant} : attente inconnue {scenario['expectation']}")

        attendus = set(scenario["expected_tools"])
        interdits = set(scenario["forbidden_tools"])
        for nom in attendus | interdits:
            if nom not in outils:
                erreurs.append(f"{identifiant} : outil absent du registre {nom}")
        if attendus & interdits:
            erreurs.append(
                f"{identifiant} : outil à la fois attendu et interdit {sorted(attendus & interdits)}"
            )

        # Les arguments minimaux doivent passer le contrat : un scénario ne peut
        # pas exiger un appel que le registre refuserait.
        for nom, arguments in scenario["minimal_arguments"].items():
            if nom not in attendus:
                erreurs.append(f"{identifiant} : arguments déclarés pour {nom}, qui n'est pas attendu")
                continue
            try:
                registre.validate(nom, arguments)
            except ArgumentError as exc:
                erreurs.append(f"{identifiant} : arguments refusés par le contrat — {exc}")

        for reference in scenario["expected_evidence"]:
            if reference not in connues:
                erreurs.append(f"{identifiant} : preuve absente du data pack {reference}")

        if scenario["expectation"] == "answer" and not scenario["expected_evidence"]:
            avertissements.append(
                f"{identifiant} : réponse attendue sans preuve exigée — le scénario ne "
                "contrôle que le fait de répondre"
            )
        if scenario["expectation"] == "refuse" and scenario["expected_evidence"]:
            erreurs.append(f"{identifiant} : refus attendu, mais des preuves sont exigées")
        if not scenario.get("notes"):
            avertissements.append(f"{identifiant} : sans note — la règle de jugement n'est pas écrite")

    return erreurs, avertissements


def charger(chemin: Path) -> list[dict]:
    return [
        json.loads(ligne)
        for ligne in chemin.read_text(encoding="utf-8").splitlines()
        if ligne.strip()
    ]


def manifeste(scenarios: list[dict], parties: dict[str, int]) -> str:
    categories: dict[str, int] = {}
    for scenario in scenarios:
        categories[scenario["category"]] = categories.get(scenario["category"], 0) + 1
    lignes = [
        "# Gel du jeu de scénarios — M6",
        "",
        "> Un jeu de scénarios se gèle **avant** toute mesure comparative. Après le gel,",
        "> une modification impose une nouvelle version : les chiffres obtenus sur deux",
        "> jeux différents ne se comparent pas.",
        "",
        f"**Version `m6-scenarios-v2`, gelée le {date.today().strftime('%d/%m/%Y')}.**",
        "",
        "## Composition",
        "",
        "| Source | Scénarios | Empreinte SHA-256 |",
        "|---|---:|---|",
    ]
    for chemin, compte in parties.items():
        lignes.append(f"| `{chemin}` | {compte} | `{empreinte(ROOT / chemin)}` |")
    lignes += [
        f"| **`eval/scenarios_v2.jsonl`** | **{len(scenarios)}** | `{empreinte(GELE)}` |",
        "",
        "## Couverture",
        "",
        "| Catégorie | Scénarios |",
        "|---|---:|",
    ]
    for categorie, compte in sorted(categories.items()):
        lignes.append(f"| `{categorie}` | {compte} |")
    attendus = sum(1 for item in scenarios if item["expectation"] == "answer")
    lignes += [
        "",
        f"**{attendus} réponses attendues, {len(scenarios) - attendus} refus attendus.**",
        "",
        "## Ce que la validation contrôle",
        "",
        "- champs requis, identifiants uniques, rôle et attente connus ;",
        "- outils attendus et interdits présents au registre, et disjoints ;",
        "- arguments minimaux **acceptés par le contrat de l'outil** — un scénario ne peut",
        "  pas exiger un appel que le registre refuserait ;",
        "- preuves attendues présentes dans le data pack ;",
        "- un refus attendu n'exige pas de preuve, et réciproquement une réponse sans preuve",
        "  exigée est signalée.",
        "",
        "```bash",
        "python eval/freeze_scenarios.py --check   # valide et vérifie les empreintes",
        "```",
        "",
        "## Règle de modification",
        "",
        "Après gel, un scénario ne se corrige pas en place. Toute modification produit",
        "`m6-scenarios-v3`, et les mesures antérieures restent attachées à la version sur",
        "laquelle elles ont été obtenues.",
        "",
    ]
    return "\n".join(lignes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="valider et vérifier les empreintes sans réécrire")
    args = parser.parse_args()

    parties = {}
    scenarios: list[dict] = []
    for chemin in SOURCES:
        lot = charger(chemin)
        parties[str(chemin.relative_to(ROOT)).replace("\\", "/")] = len(lot)
        scenarios.extend(lot)

    erreurs, avertissements = valider(scenarios)
    for message in avertissements:
        print(f"  avertissement : {message}")
    if erreurs:
        for message in erreurs:
            print(f"  ERREUR : {message}")
        print(f"\n{len(erreurs)} erreur(s) — jeu non gelé.")
        return 1

    contenu = "".join(
        json.dumps(scenario, ensure_ascii=False, sort_keys=True) + "\n" for scenario in scenarios
    )
    if args.check:
        if not GELE.is_file():
            print("Jeu gelé absent : lancer sans --check.")
            return 1
        # Comparaison sur les octets, jamais sur le texte relu : `read_text` ne
        # prend `newline` qu'à partir de Python 3.13, et surtout un checksum doit
        # porter sur le fichier tel qu'il est stocké.
        attendu = hashlib.sha256(contenu.encode("utf-8")).hexdigest()
        obtenu = empreinte(GELE)
        if attendu != obtenu:
            print(f"ECART : les sources ne correspondent plus au jeu gelé.\n"
                  f"  attendu {attendu}\n  obtenu  {obtenu}")
            return 1
        print(f"Jeu gelé conforme — {len(scenarios)} scénarios, empreinte {empreinte(GELE)[:16]}…")
        return 0

    # newline="" : le checksum doit porter sur le fichier tel qu'il sera lu,
    # après git, après une copie entre systèmes (piège paye quatre fois en M5).
    GELE.write_text(contenu, encoding="utf-8", newline="")
    MANIFESTE.write_text(manifeste(scenarios, parties), encoding="utf-8", newline="")
    print(f"Jeu gelé : {len(scenarios)} scénarios -> {GELE.relative_to(ROOT)}")
    print(f"Empreinte : {empreinte(GELE)}")
    print(f"Manifeste : {MANIFESTE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
