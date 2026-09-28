#!/usr/bin/env python3
"""Contrôle de diffusion M7 ; replay local isolé, sans validation des acquis."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import yaml
from build_m7_reference import ROOT, REFERENCE, RELEASE_ID, replay, sha256, source_inventory

def require(condition, message):
    if not condition:
        raise ValueError(message)

def inventory_check(directory):
    checksum = directory / "checksums.sha256"
    listed = {}
    for line in checksum.read_text(encoding="utf-8").splitlines():
        expected, relative = line.split("  ", 1)
        path = (directory / relative).resolve()
        require(directory.resolve() in path.parents, f"Chemin hors paquet : {relative}")
        require(relative not in listed, f"Checksum dupliqué : {relative}")
        listed[relative] = expected
        require(path.is_file() and sha256(path) == expected, f"Fichier absent/altéré : {relative}")
    actual = {str(p.relative_to(directory)) for p in directory.rglob("*") if p.is_file()
              and p != checksum and p.name != ".DS_Store" and "__pycache__" not in p.parts}
    require(set(listed) == actual, "Inventaire de checksums incomplet")
    return len(listed)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trainer", action="store_true")
    args = parser.parse_args()
    module = ROOT / "M7"
    for name in ("brief1_module7.md", "brief2_module7.md", "brief1_module7_online.md",
                 "module_7_synthese.md", "acquis_m7.md", "RESOURCES.md", "DIFFUSION.md"):
        require((module / name).is_file(), f"Document absent : {name}")
    required = ["README.md", "lab.py", "tests/test_portability.py", "architecture/current.md", "architecture/target.md",
                "architecture/adr/0001-modele.md", "security/data_policy.md", "security/threat_model.md",
                "security/red_team_cases.yaml", "security/residual_risks.md", "portability/alternatives.md",
                "portability/exercise.md", "resilience/scenarios.md", "resilience/recovery.md",
                "simulated_action/contract.json", "simulated_action/approval_flow.md", "migration_exercise/contract.md",
                "migration_exercise/execution_log.md", "migration_exercise/independent_review.md",
                "migration_exercise/remediation.md", "online/dossier.md", "veille_diagops/journal.md", "handoff_m8.md", "journal_bord.md"]
    for name in required:
        require((module / "starter" / name).is_file(), f"Starter incomplet : {name}")
    action = json.loads((module / "starter/simulated_action/contract.json").read_text(encoding="utf-8"))
    require(action["executable"] is False and action["real_side_effects"] is False and action["network_client"] is None,
            "L'outil doit rester un contrat fictif")
    pack = ROOT / "data_pack"
    manifest = yaml.safe_load((pack / "MANIFEST.yaml").read_text(encoding="utf-8"))
    # Le paquet M7 est additif : préserver l'identité du socle M6 et ses contrôles.
    require(manifest["current_release"] == "diagops-2026-S1-m6-v1", "Le socle M6 doit rester compatible")
    require(manifest["module_extensions"]["M7"] == "diagops-2026-S1-m7-v1", "Extension M7 absente")
    entries = {entry["path"]: entry for entry in manifest["files"]}
    entry = entries["2026-S1/reference_runs/m6_for_m7/"]
    require(entry["delivery_status"] == "ready_for_distribution" and entry["release_id"] == RELEASE_ID,
            "La référence M7 n'est pas annoncée comme distribuable")
    require(entries["images/manifest.csv"]["required"] is False, "Le corpus image doit rester facultatif")
    release = json.loads((REFERENCE / "release_manifest.json").read_text(encoding="utf-8"))
    require(release["release_id"] == RELEASE_ID and release["production_approved"] is False, "Référence M7 incorrecte")
    require(release["source_sha256"] == source_inventory(), "Les sources M6 ont changé : requalifier avant reconstruction")
    counts = {"reference_files": inventory_check(REFERENCE), "data_pack_files": inventory_check(pack)}
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "DIAGOPS_DATA_PACK": str(pack)}
    with tempfile.TemporaryDirectory(prefix="cisia-m7-check-") as temporary:
        tmp = Path(temporary)
        observed = replay(tmp)
        for name, value in observed.items():
            require(value == json.loads((REFERENCE / "evaluation" / f"{name}.json").read_text(encoding="utf-8")),
                    f"Replay M6 différent : {name}")
        failed = {name: [row["scenario_id"] for row in observed[name]["scenarios"] if not row["success"]]
                  for name in ("nominal", "adversarial")}
        require(failed == release["known_failed_scenarios"], "Échecs connus non documentés")
        # Reproduire la commande apprenant dans une racine isolée, sans modifier work/.
        isolated = tmp / "checkout"
        shutil.copytree(module / "starter", isolated / "M7/starter", ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        (isolated / "data_pack").symlink_to(pack, target_is_directory=True)
        (isolated / "tools").mkdir()
        shutil.copy2(ROOT / "tools/init_module.py", isolated / "tools/init_module.py")
        subprocess.run([sys.executable, "tools/init_module.py", "M7"], cwd=isolated, env=environment, check=True, capture_output=True)
        work = isolated / "work/M7"
        second = subprocess.run([sys.executable, "tools/init_module.py", "M7"], cwd=isolated, env=environment, capture_output=True)
        require(second.returncode != 0, "L'initialisation doit refuser l'écrasement")
        tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"], cwd=work,
                               env=environment, check=True, capture_output=True, text=True)
        print(tests.stderr.strip())
        subprocess.run([sys.executable, "lab.py", "--output", "results/qualification"],
                       cwd=work, env=environment, check=True, capture_output=True)
        report = json.loads((work / "results/qualification/report.json").read_text(encoding="utf-8"))
        require(report["status"] == "passed" and report["calibration_questions"] == 12, "Migration locale non qualifiée")
        require(report["hit_at_3_after"] == report["hit_at_3_before"], "Régression de retrieval")
        again = subprocess.run([sys.executable, "lab.py", "--data-pack", str(pack), "--output", "results/qualification"],
                               cwd=work, env=environment, capture_output=True)
        require(again.returncode != 0, "Le banc doit préserver un résultat existant")
    if args.trainer:
        require((ROOT / "_conception/M7/README.md").is_file(), "Consignes formateur absentes")
    print(json.dumps({"status": "ready_for_local_distribution", "release_id": RELEASE_ID,
                      "learner_completion": "not_assessed", "known_m6_failures": failed,
                      "m7_tests": "passed", "migration": report["status"],
                      "ranking_equal": report["ranking_equal"], "rollback_equal": report["rollback_equal"], **counts},
                     ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
