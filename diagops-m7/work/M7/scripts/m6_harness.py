"""Outillage commun aux campagnes M7 : copies du data pack et agent M6 de référence.

Toutes les injections portent sur une **copie** du data pack placée dans le
dossier de résultat. Le data pack commun et le code M6 ne sont jamais modifiés :
l'agent est importé depuis `M6/starter` et pointé sur la copie par
`DIAGOPS_DATA_PACK`, variable prévue par le starter M6.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import time

WORK = Path(__file__).resolve().parents[1]
ROOT = WORK.parents[1]
PACK = ROOT / "data_pack"
M6 = ROOT / "M6" / "starter"
sys.path.insert(0, str(M6))
sys.path.insert(0, str(M6 / "eval"))

import run_agent_eval as rae  # noqa: E402
from agent.registry import default_registry  # noqa: E402
from agent.runner import BoundedAgent, load_policy  # noqa: E402
import tools as m6tools  # noqa: E402

# Seules les sources lues par les outils M6 et le banc sont copiées.
PACK_PARTS = [
    "2026-S1/knowledge", "2026-S1/equipment", "2026-S1/events", "2026-S1/maintenance",
    "2026-S1/reports", "2026-S1/rag_eval", "2027-S1/reports", "2027-S1/feedback",
]
NOMINAL = M6 / "eval" / "scenarios.jsonl"
ADVERSARIAL = M6 / "adversarial" / "campaign.jsonl"


def copy_pack(destination: Path) -> Path:
    destination = Path(destination)
    for part in PACK_PARTS:
        shutil.copytree(PACK / part, destination / part)
    return destination


def use_pack(path: Path) -> None:
    """Pointe les outils M6 sur un data pack et vide leurs caches."""
    os.environ["DIAGOPS_DATA_PACK"] = str(Path(path).resolve())
    m6tools.reset_caches()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# -- manifeste documentaire ----------------------------------------------------
def read_manifest(pack: Path) -> tuple[list[str], list[dict]]:
    path = Path(pack) / "2026-S1/knowledge/manifest.csv"
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames), list(reader)


def write_manifest(pack: Path, header: list[str], rows: list[dict]) -> None:
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    (Path(pack) / "2026-S1/knowledge/manifest.csv").write_text(buffer.getvalue(), encoding="utf-8", newline="")


def add_document(pack: Path, row: dict, text: str, *, sign: bool = True) -> None:
    """Ajoute un document au corpus copié ; `sign=False` laisse le checksum faux."""
    document = Path(pack) / "2026-S1/knowledge/documents" / row["asset_path"]
    document.write_text(text, encoding="utf-8", newline="\n")
    header, rows = read_manifest(pack)
    full = {key: "" for key in header}
    full.update(row)
    full["checksum_sha256"] = sha256_file(document) if sign else "0" * 64
    rows.append(full)
    write_manifest(pack, header, rows)


def update_document(pack: Path, document_id: str, **changes) -> None:
    header, rows = read_manifest(pack)
    for row in rows:
        if row["document_id"] == document_id:
            row.update(changes)
    write_manifest(pack, header, rows)


# -- agent ------------------------------------------------------------------------
def agent(role: str = "technicien", **policy_changes) -> BoundedAgent:
    from dataclasses import replace
    policy = replace(load_policy(), role=role, **policy_changes)
    return BoundedAgent(default_registry(), policy)


def ask(question: str, *, role: str = "technicien", faults: dict | None = None, bot: BoundedAgent | None = None) -> dict:
    bot = bot or agent(role)
    started = time.perf_counter()
    run = bot.run(question, faults=faults)
    trace = run.as_trace()
    trace["wall_ms"] = round((time.perf_counter() - started) * 1000, 1)
    trace["answer"] = run.answer
    trace["instruction_like"] = any(step.instruction_like_content for step in run.steps)
    return trace


def load_scenarios(path: Path) -> list[dict]:
    return rae.load_scenarios(Path(path))


def evaluate(path: Path, faults: dict | None = None) -> dict:
    """Rejoue un jeu de scénarios M6 sur le data pack courant."""
    bot = agent()
    rows = [rae.evaluate_scenario(bot, scenario, faults or {}) for scenario in load_scenarios(path)]
    return {
        "success": sum(row["success"] for row in rows), "count": len(rows),
        "answered": sum(row["answered"] for row in rows),
        "refused": sum(row["refused"] for row in rows),
        "stop_reasons": _count(row["stop_reason"] for row in rows),
        "failed": [row["scenario_id"] for row in rows if not row["success"]],
        "rows": [{key: row[key] for key in ("scenario_id", "success", "answered", "refused", "stop_reason", "tools_used")}
                 for row in rows],
    }


def _count(values) -> dict:
    counts: dict = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def save_json(path: Path, value) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                          encoding="utf-8", newline="\n")
