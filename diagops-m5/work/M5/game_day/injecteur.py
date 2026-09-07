#!/usr/bin/env python3
"""Injecteur de scénario pour la répétition à blanc.

Le game day réel est contradictoire : un tiers injecte. Faute de tiers disponible, ce script tire
un scénario au sort et **scelle sa réponse** — celui qui diagnostique ne sait pas ce qui a été
injecté tant qu'il n'a pas rendu son verdict.

Ce que cela reproduit fidèlement : dans le brief, la **liste** des scénarios est connue d'avance
(« le formateur injecte un scénario parmi : … »). Seule l'identité du scénario tiré est inconnue.
La répétition place donc dans la même condition.

Ce que cela ne reproduit pas : un tiers peut inventer hors liste, se tromper, ou combiner deux
pannes. Cette répétition est un banc de chronologie et de rôles, **pas un game day**.

Le scénario `aucun_incident` est dans l'urne à dessein. Sans témoin, on cherche jusqu'à trouver —
et on finit toujours par trouver quelque chose. Savoir s'arrêter sur « rien à signaler » est une
compétence de l'exercice, pas une échappatoire.

    python game_day/injecteur.py --injecter     # tire, applique, scelle
    python game_day/injecteur.py --reveler      # après le diagnostic, jamais avant
    python game_day/injecteur.py --restaurer    # remet la stack d'aplomb
"""

from __future__ import annotations

import argparse
import json
import random
import secrets
import subprocess
from datetime import datetime, timezone
from pathlib import Path


RACINE = Path(__file__).resolve().parents[1]
SCELLE = RACINE / "game_day" / "_scelle.json"
COMPOSE = ["docker", "compose", "-f", str(RACINE / "deploy" / "compose.yaml")]

SCENARIOS = [
    "index_corrompu",          # postings vidés dans l'index servi
    "index_perime",            # build_version d'une autre stratégie
    "index_ampute",            # des documents disparaissent de l'index
    "dependance_indisponible", # faults.json : dependency_available = false
    "readiness_lente",         # faults.json : délai de readiness
    "aucun_incident",          # témoin — rien n'est injecté
]


def dans_le_volume(script: str) -> str:
    """Exécute un script Python dans un conteneur jetable monté sur le volume d'artefacts."""
    resultat = subprocess.run(
        [*COMPOSE, "run", "--rm", "--entrypoint", "python", "gate", "-c", script],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return (resultat.stdout or "") + (resultat.stderr or "")


INJECTIONS = {
    "index_corrompu": """
import json
p = '/artifacts/runtime/index.json'
d = json.load(open(p, encoding='utf-8'))
for doc in d['documents']:
    doc['terms'] = {}
json.dump(d, open(p, 'w', encoding='utf-8'))
""",
    "index_perime": """
import json
p = '/artifacts/runtime/index.json'
d = json.load(open(p, encoding='utf-8'))
d['build_version'] = 'build-000000000000'
json.dump(d, open(p, 'w', encoding='utf-8'))
""",
    "index_ampute": """
import json
p = '/artifacts/runtime/index.json'
d = json.load(open(p, encoding='utf-8'))
d['documents'] = d['documents'][:3]
d['document_count'] = 3
json.dump(d, open(p, 'w', encoding='utf-8'))
""",
    "dependance_indisponible": """
import json, os
os.makedirs('/artifacts/runtime', exist_ok=True)
json.dump({'dependency_available': False}, open('/artifacts/runtime/faults.json', 'w'))
""",
    "readiness_lente": """
import json, os
os.makedirs('/artifacts/runtime', exist_ok=True)
json.dump({'readiness_delay_ms': 1500}, open('/artifacts/runtime/faults.json', 'w'))
""",
    "aucun_incident": "print('temoin : rien n a ete injecte')",
}


def injecter() -> int:
    # Graine cryptographique : ni l'heure ni un compteur, pour qu'aucune reconstitution a
    # posteriori ne permette de deviner le tirage.
    scenario = random.Random(secrets.randbits(128)).choice(SCENARIOS)
    sortie = dans_le_volume(INJECTIONS[scenario])

    SCELLE.write_text(json.dumps({
        "scenario": scenario,
        "injecte_a": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sortie": sortie.strip()[-400:],
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print("Scénario injecté et scellé.")
    print("Ne pas ouvrir game_day/_scelle.json avant d'avoir rendu le diagnostic.")
    print(f"Urne : {len(SCENARIOS)} scénarios, dont un témoin sans incident.")
    return 0


def reveler() -> int:
    if not SCELLE.is_file():
        print("Aucun scellé : rien n'a été injecté.")
        return 1
    contenu = json.loads(SCELLE.read_text(encoding="utf-8"))
    print(f"Scénario réellement injecté : {contenu['scenario']}")
    print(f"Injecté à : {contenu['injecte_a']}")
    return 0


def restaurer() -> int:
    sortie = dans_le_volume("""
import os
for f in ('/artifacts/runtime/faults.json',):
    if os.path.exists(f):
        os.remove(f)
        print('faute retiree :', f)
print('faults.json absent')
""")
    print(sortie.strip())
    print("L'index, lui, se restaure par rollback_index.py — pas par ce script.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    groupe = parser.add_mutually_exclusive_group(required=True)
    groupe.add_argument("--injecter", action="store_true")
    groupe.add_argument("--reveler", action="store_true")
    groupe.add_argument("--restaurer", action="store_true")
    args = parser.parse_args()

    if args.injecter:
        return injecter()
    if args.reveler:
        return reveler()
    return restaurer()


if __name__ == "__main__":
    raise SystemExit(main())
