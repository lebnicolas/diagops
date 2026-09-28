#!/usr/bin/env python3
"""Fige l'état M6 réellement distribué, avec ses limites, pour la revue M7."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from build_m6_reference import refresh_checksums, refresh_data_pack_checksums

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / "data_pack/2026-S1/reference_runs/m6_for_m7"
RELEASE_ID = "diagops-m6-reference-r1"

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def normalized(value):
    # Les mesures temporelles sont rejouées sur le poste ; elles ne sont pas gelées.
    if isinstance(value, dict):
        return {k: normalized(v) for k, v in value.items() if not k.endswith("elapsed_ms")}
    if isinstance(value, list):
        return [normalized(v) for v in value]
    return value

def source_inventory():
    roots = [ROOT / "M6/starter"] + [ROOT / "data_pack" / path for path in (
        "2026-S1/equipment", "2026-S1/events", "2026-S1/maintenance", "2026-S1/knowledge",
        "2026-S1/reports", "2027-S1/reports")]
    paths = [path for root in roots for path in root.rglob("*") if path.is_file()
             and not {"__pycache__", ".pytest_cache", ".venv", "results"}.intersection(path.parts)
             and path.name not in {".DS_Store", ".gitkeep"}]
    paths += [ROOT / "data_pack/2026-S1/reference_runs/m5_for_m6/release_manifest.json"]
    return {str(path.relative_to(ROOT)): sha256(path) for path in sorted(paths)}

def replay(destination):
    destination = Path(destination)
    environment = {**os.environ, "DIAGOPS_DATA_PACK": str(ROOT / "data_pack"), "PYTHONDONTWRITEBYTECODE": "1"}
    outputs = {}
    for name, scenarios in [("nominal", "eval/scenarios.jsonl"), ("adversarial", "adversarial/campaign.jsonl")]:
        report, traces = destination / f"{name}.json", destination / f"{name}_traces.jsonl"
        completed = subprocess.run([sys.executable, str(ROOT / "M6/starter/eval/run_agent_eval.py"),
                        "--scenarios", str(ROOT / "M6/starter" / scenarios),
                        "--output", str(report), "--traces", str(traces)],
                       cwd=ROOT, env=environment, capture_output=True, text=True)
        if completed.returncode:
            raise RuntimeError(f"Replay M6 {name} impossible :\n{completed.stderr}")
        outputs[name] = normalized(json.loads(report.read_text(encoding="utf-8")))
        outputs[name + "_traces"] = [normalized(json.loads(line)) for line in traces.read_text(encoding="utf-8").splitlines()]
    return outputs

def main():
    # Reconstruction explicite d'artefacts dérivés seulement, jamais de work/M6.
    with tempfile.TemporaryDirectory(prefix="cisia-m7-reference-") as temporary:
        outputs = replay(temporary)
    for name, value in outputs.items():
        save(REFERENCE / "evaluation" / f"{name}.json", value)
    failed = {name: [row["scenario_id"] for row in outputs[name]["scenarios"] if not row["success"]]
              for name in ("nominal", "adversarial")}
    save(REFERENCE / "release_manifest.json", {
        "schema_version": 1, "release_id": RELEASE_ID,
        "source_release_id": "diagops-m5-reference-r1",
        "scope": "frozen_m6_starter_for_architecture_audit",
        "production_approved": False, "student_completion_proven": False,
        "known_failed_scenarios": failed, "source_sha256": source_inventory(),
        "timings": "not_frozen_replay_on_target_machine",
    })
    REFERENCE.mkdir(parents=True, exist_ok=True)
    (REFERENCE / "README.md").write_text(
        "# Référence M6 pour M7 — diagops-m6-reference-r1\n\n"
        "Cette référence gèle le starter M6 réellement distribué et ses campagnes. "
        "Elle n'est ni un corrigé M6 ni une preuve de réalisation par les apprenants. "
        "Le code reste dans M6/starter ; release_manifest.json en fixe les hashes, "
        "ainsi que ceux des données utilisées. Aucun modèle ni fournisseur distant n'est invoqué.\n\n"
        "## Résultats et risques connus\n\n"
        + "\n".join(f"- {name} : échecs {', '.join(ids)}." for name, ids in failed.items())
        + "\n\nLe planificateur reste à une étape. Les cas multi-étapes, l'instruction directe "
        "et le filtrage du rôle avant appel présentent des limites. Lire les résultats cas par cas. "
        "Aucune promotion globale n'est autorisée par cette référence ; M7 doit conserver, traiter "
        "ou bloquer ces risques explicitement. Le banc JSON/SQLite porte uniquement sur le retrieval documentaire.\n\n"
        "## Reproduction\n\n"
        "Depuis S04, avec les dépendances M6 : `python tools/check_m7_release.py`. "
        "Le contrôle rejoue les deux campagnes et compare résultats et traces hors durées, "
        "sans toucher aux travaux apprenants. Les durées locales ne sont pas des garanties.\n\n"
        "## Handoff réglementaire et opérationnel\n\n"
        "Reprendre les politiques et runbooks de m5_for_m6, la politique agent/policy.yaml, "
        "le registre docs/registre_outils.md et les invariants adversarial/invariants.md de M6. "
        "Aucune veille M6 ni revue indépendante n'est inventée pour cette référence. "
        "Compléter en M7 les décisions, sources officielles datées, propriétaires, RTO/RPO "
        "et risques résiduels dans les gabarits ; joindre son propre handoff M6 s'il existe.\n",
        encoding="utf-8")
    count = refresh_checksums(REFERENCE)
    pack_count = refresh_data_pack_checksums()
    print(json.dumps({"status": "built", "release_id": RELEASE_ID, "reference_files": count,
                      "data_pack_files": pack_count, "known_failed_scenarios": failed}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
