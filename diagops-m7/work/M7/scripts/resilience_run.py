#!/usr/bin/env python3
"""Huit scénarios de résilience M7, injectés sur des copies locales.

Chaque scénario consigne ce qui a été réellement exécuté (`execution`) et ce
qui ne l'a pas été (`non_teste`). Un composant absent de la référence — modèle
génératif, fournisseur distant — n'est jamais déclaré testé : il est simulé sur
table, et un proxy local éventuel est nommé comme tel.

    .venv/Scripts/python scripts/resilience_run.py --output results/resilience-r1
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
from pathlib import Path
import shutil
import statistics
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parent))
import m6_harness as h  # noqa: E402

sys.path.insert(0, str(h.WORK))
import lab  # noqa: E402

PUMP_QUESTION = "Quel seuil de vibration déclenche une revue humaine prioritaire pour une pompe ?"


def ms(started: float) -> float:
    return round((time.perf_counter() - started) * 1000, 1)


def fresh(base: Path, name: str) -> Path:
    pack = h.copy_pack(base / name / "data_pack")
    h.use_pack(pack)
    return pack


def res01(base: Path) -> dict:
    pack = fresh(base, "res01")
    reference = h.evaluate(h.NOMINAL)
    manifest = pack / "2026-S1/knowledge/manifest.csv"
    saved = manifest.read_bytes()
    manifest.unlink()
    h.use_pack(pack)
    degraded = h.evaluate(h.NOMINAL)
    # Reprise : la source déclarée est restaurée, les caches vidés, le jeu rejoué.
    started = time.perf_counter()
    manifest.write_bytes(saved)
    h.use_pack(pack)
    restored = h.evaluate(h.NOMINAL)
    recovery_ms = ms(started)

    # Index actif du banc supprimé pendant l'exploitation.
    bench = base / "res01" / "banc"
    bench.mkdir()
    export = bench / "corpus.json"
    lab.export_corpus(pack, export)
    lab.migrate(export, bench / "index.sqlite")
    lab.activate(bench, "index.sqlite", "sqlite")
    (bench / "index.sqlite").unlink()
    try:
        lab.search_active(bench, PUMP_QUESTION, "technicien")
        lost = "aucune erreur"
    except Exception as exc:  # le type d'erreur est l'observation
        lost = type(exc).__name__
    return {
        "execution": "injection locale : manifeste du corpus supprimé sur la copie ; index actif du banc supprimé",
        "reference": {k: reference[k] for k in ("success", "count", "failed")},
        "degrade": {k: degraded[k] for k in ("success", "answered", "refused", "stop_reasons", "failed")},
        "apres_reprise": {k: restored[k] for k in ("success", "failed")},
        "reprise_ms": recovery_ms,
        "index_actif_supprime": lost,
        "non_teste": "modèle génératif : la référence n'en contient pas (réponse extractive déterministe)",
    }


def res02(base: Path) -> dict:
    fresh(base, "res02")
    faults = {"search_knowledge": {"error": "unavailable"}}
    degraded = h.evaluate(h.NOMINAL, faults)
    return {
        "execution": "simulation sur table + proxy local : panne 'unavailable' injectée sur search_knowledge par le registre M6",
        "proxy": {k: degraded[k] for k in ("success", "answered", "refused", "stop_reasons", "failed")},
        "non_teste": "aucun fournisseur distant dans la référence : latence réseau, quotas, réponses partielles, "
                     "changement de version côté fournisseur et coupure en cours de réponse ne sont pas exercés",
    }


def res03(base: Path) -> dict:
    pack = fresh(base, "res03")
    # État du banc construit AVANT la mise à jour documentaire.
    bench = base / "res03" / "banc"
    bench.mkdir()
    export = bench / "corpus.json"
    lab.export_corpus(pack, export)
    lab.migrate(export, bench / "index.sqlite")
    lab.activate(bench, "index.sqlite", "sqlite")

    old = (pack / "2026-S1/knowledge/documents/DOC-PUMP-VIB-001.md").read_text(encoding="utf-8")
    new = old.replace("révision 1", "révision 2").replace("`4,5 mm/s`", "`3,5 mm/s`")
    h.add_document(pack, {
        "document_id": "DOC-PUMP-VIB-002", "title": "Triage pédagogique — vibration des pompes (rév. 2)",
        "revision": "2", "effective_at": "2026-09-01", "source_type": "procedure",
        "asset_path": "DOC-PUMP-VIB-002.md", "license": "formation_interne", "sensitivity": "interne",
        "status": "active", "supersedes_document_id": "DOC-PUMP-VIB-001",
        "allowed_roles": "technicien;superviseur;auditeur"}, new)
    # Oubli volontaire : DOC-PUMP-VIB-001 reste « active ».
    h.use_pack(pack)
    served = sorted({e["reference"] for e in h.ask(PUMP_QUESTION)["evidence"]})
    try:
        lab.export_corpus(pack, bench / "corpus_v2.json")
        export_v2 = "acceptée"
    except ValueError as exc:
        export_v2 = f"refusée : {exc}"
    stale = lab.search_active(bench, PUMP_QUESTION, "technicien")
    return {
        "execution": "injection locale : révision 2 ajoutée au manifeste copié, révision 1 laissée active ; "
                     "index du banc construit avant la mise à jour et resté actif",
        "agent_m6_cite": served,
        "deux_revisions_actives_servies": {"DOC-PUMP-VIB-001", "DOC-PUMP-VIB-002"} <= set(served),
        "export_banc_v2": export_v2,
        "index_actif_perime_sert": stale,
        "index_actif_signale_peremption": False,
        "non_teste": "date d'effet future ou révision retirée sans remplaçante",
    }


def res04(base: Path) -> dict:
    fresh(base, "res04")
    scenarios = h.load_scenarios(h.NOMINAL)
    bot = h.agent()

    def one(scenario):
        started = time.perf_counter()
        bot.run(scenario["question"])
        return (time.perf_counter() - started) * 1000

    sequential = [one(s) for s in scenarios * 20]
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=8) as pool:
        concurrent = list(pool.map(one, scenarios * 20))
    concurrent_total = ms(started)
    sequential.sort()
    concurrent.sort()

    # Budget de durée plus court que le travail d'un outil ralenti.
    policy = h.load_policy()
    tight = h.BoundedAgent(h.default_registry(), replace(policy, budget=replace(policy.budget, max_duration_ms=100)))
    started = time.perf_counter()
    run = tight.run(PUMP_QUESTION, faults={"search_knowledge": {"delay_ms": 400}})
    return {
        "execution": "exécution locale : 360 exécutions séquentielles puis 360 sur 8 fils ; "
                     "budget de durée ramené à 100 ms sur une copie de la politique, outil ralenti de 400 ms",
        "sequentiel_ms": {"p50": round(statistics.median(sequential), 3), "p95": round(sequential[int(len(sequential) * .95)], 3),
                          "total": round(sum(sequential), 1)},
        "concurrent_8_fils_ms": {"p50": round(statistics.median(concurrent), 3), "p95": round(concurrent[int(len(concurrent) * .95)], 3),
                                 "total_mur": concurrent_total},
        "budget_depasse": {"stop_reason": run.stop_reason, "refused": run.refused, "steps": len(run.steps),
                           "wall_ms": ms(started), "budget_ms": 100},
        "non_teste": "coût facturé (aucun appel payant), charge multi-processus, mémoire sous charge",
    }


def res05(base: Path) -> dict:
    fresh(base, "res05")
    started = time.perf_counter()
    slow = h.ask(PUMP_QUESTION, faults={"search_knowledge": {"delay_ms": 3000}})
    slow_wall = ms(started)
    empty = h.ask(PUMP_QUESTION, faults={"search_knowledge": {"empty": True}})
    adv = [s for s in h.load_scenarios(h.ADVERSARIAL) if s["scenario_id"] == "ADV-006"][0]
    conflict = h.ask(adv["question"])
    return {
        "execution": "injection locale par le registre M6 : délai 3000 ms (timeout outil 1500 ms), résultat vide ; "
                     "scénario ADV-006 rejoué pour l'incohérence fiche/document",
        "outil_lent": {"stop_reason": slow["stop_reason"], "outcome": slow["steps"][0]["outcome"] if slow["steps"] else None,
                       "wall_ms": slow_wall, "timeout_outil_ms": 1500},
        "outil_vide": {"stop_reason": empty["stop_reason"], "refused": empty["refused"]},
        "incoherence": {"stop_reason": conflict["stop_reason"], "tools_used": conflict["tools_used"],
                        "conflit_expose": "conflit" in conflict["answer"].lower(), "answer": conflict["answer"]},
        "non_teste": "outil qui renvoie des données fausses mais bien formées sans signal de contradiction",
    }


def res06(base: Path) -> dict:
    pack = fresh(base, "res06")
    target = pack / "2026-S1/knowledge/documents/DOC-CHILL-TEMP-001.md"
    target.write_text(target.read_text(encoding="utf-8") + "\nLigne ajoutée hors processus.\n",
                      encoding="utf-8", newline="\n")
    h.use_pack(pack)
    degraded = h.evaluate(h.NOMINAL)
    try:
        lab.export_corpus(pack, base / "res06" / "corpus.json")
        export = "acceptée"
    except ValueError as exc:
        export = f"refusée : {exc}"
    uses_knowledge = [r["scenario_id"] for r in degraded["rows"] if "search_knowledge" in r["tools_used"]]
    return {
        "execution": "injection locale : une ligne ajoutée à DOC-CHILL-TEMP-001 sans mise à jour du manifeste",
        "agent_m6": {k: degraded[k] for k in ("success", "answered", "refused", "stop_reasons", "failed")},
        "scenarios_documentaires_touches": uses_knowledge,
        "export_banc": export,
        "granularite": "corpus entier : un seul document altéré rend toute la recherche documentaire indisponible",
        "non_teste": "document altéré ET manifeste mis à jour (voir RT-03, empoisonnement accepté)",
    }


def res07(base: Path) -> dict:
    pack = fresh(base, "res07")
    bot = h.agent()
    before = sorted({e["reference"] for e in bot.run(PUMP_QUESTION).as_trace()["evidence"]})
    bench = base / "res07" / "banc"
    bench.mkdir()
    export = bench / "corpus.json"
    lab.export_corpus(pack, export)
    lab.migrate(export, bench / "index.sqlite")
    lab.activate(bench, "index.sqlite", "sqlite")

    h.update_document(pack, "DOC-PUMP-VIB-001", allowed_roles="superviseur;auditeur")
    # Même processus, caches non vidés : c'est l'état d'une API qui tourne.
    same_process = sorted({e["reference"] for e in bot.run(PUMP_QUESTION).as_trace()["evidence"]})
    stale_index = lab.search_active(bench, PUMP_QUESTION, "technicien")
    h.use_pack(pack)
    after_reload = sorted({e["reference"] for e in h.agent().run(PUMP_QUESTION).as_trace()["evidence"]})
    started = time.perf_counter()
    export2 = bench / "corpus_revocation.json"
    lab.export_corpus(pack, export2)
    lab.migrate(export2, bench / "index_revocation.sqlite")
    lab.activate(bench, "index_revocation.sqlite", "sqlite")
    rebuilt = lab.search_active(bench, PUMP_QUESTION, "technicien")
    return {
        "execution": "injection locale : rôle technicien retiré de DOC-PUMP-VIB-001 dans le manifeste copié",
        "avant": before,
        "meme_processus_sans_rechargement": same_process,
        "index_banc_construit_avant": stale_index,
        "apres_rechargement_des_caches": after_reload,
        "apres_reconstruction_index": rebuilt,
        "reconstruction_ms": ms(started),
        "revocation_effective_sans_action": "DOC-PUMP-VIB-001" not in same_process and "DOC-PUMP-VIB-001" not in stale_index,
        "non_teste": "révocation propagée à des copies distantes ou à des traces déjà émises",
    }


def res08(base: Path) -> dict:
    pack = fresh(base, "res08")
    report = lab.exercise(pack, base / "res08" / "banc")
    bench = base / "res08" / "banc"
    # Source de reprise altérée : le retour arrière doit être refusé.
    export = bench / "corpus.json"
    original = export.read_bytes()
    export.write_text("{}", encoding="utf-8")
    try:
        lab.activate(bench, "corpus.json", "json", expected_sha256=report["source_export_sha256"])
        altered = "acceptée"
    except ValueError as exc:
        altered = f"refusée : {exc}"
    # Dernier recours : reconstruction complète depuis le manifeste.
    started = time.perf_counter()
    rebuilt = bench / "reconstruit"
    rebuilt.mkdir()
    lab.export_corpus(pack, rebuilt / "corpus.json")
    lab.migrate(rebuilt / "corpus.json", rebuilt / "index.sqlite")
    rebuild_ms = ms(started)
    export.write_bytes(original)
    return {
        "execution": "exécution réelle du banc : corruption du candidat SQLite, détection, retour au JSON ; "
                     "puis source de reprise altérée et reconstruction complète depuis le manifeste",
        "banc": {k: report[k] for k in ("status", "corruption_detected", "ranking_equal", "rollback_equal", "recovery_ms")},
        "reprise_depuis_source_alteree": altered,
        "reconstruction_complete_ms": rebuild_ms,
        "reconstruction_identique": h.sha256_file(rebuilt / "corpus.json") == report["source_export_sha256"],
        "non_teste": "perte simultanée du manifeste et de l'export (aucune sauvegarde hors poste)",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    base = args.output
    base.mkdir(parents=True, exist_ok=False)
    work = base / "copies"
    results = {}
    for name, function in [("RES-01", res01), ("RES-02", res02), ("RES-03", res03), ("RES-04", res04),
                           ("RES-05", res05), ("RES-06", res06), ("RES-07", res07), ("RES-08", res08)]:
        started = time.perf_counter()
        results[name] = function(work)
        results[name]["duree_scenario_ms"] = ms(started)
        print(name, json.dumps({k: v for k, v in results[name].items() if k not in ("execution", "non_teste")},
                               ensure_ascii=False)[:900])
    h.save_json(base / "report.json", {"scenarios": results, "python": sys.version.split()[0]})
    # Les copies du data pack sont reconstructibles : seules les preuves restent.
    shutil.rmtree(work)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
