#!/usr/bin/env python3
"""Migration exercée du brief 2 : lexical JSON -> FTS5 par rôle.

Mesure les 24 cas gelés (`migration_exercise/cases.jsonl`, SHA-256 vérifié
avant toute mesure), puis joue les six scénarios du contrat sur des copies du
corpus. Aucune dépendance, aucun réseau.

    python scripts/migration_run.py --output results/migration-r1
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import time

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import lab  # noqa: E402
import migration as mg  # noqa: E402
from fts5 import migrate_fts5, scores_fts5  # noqa: E402

PACK = HERE.parents[1] / "data_pack"
CASES = HERE / "migration_exercise" / "cases.jsonl"
FROZEN_SHA256 = "2ed61a27b32efc136652e1d81376c1fbc9b3c923ced31d84367de03f36d6f590"
RESTRICTED = "DOC-DATA-ACCESS-001"
MANUAL = []  # opérations qu'un exploitant ferait à la main, comptées


def manual(step):
    MANUAL.append(step)


def ms(started):
    return round((time.perf_counter() - started) * 1000, 2)


def copy_corpus(destination):
    for part in ("2026-S1/knowledge", "2026-S1/rag_eval"):
        shutil.copytree(PACK / part, Path(destination) / part)
    return Path(destination)


def edit_manifest(pack, change):
    path = mg.manifest_path(pack)
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        header, rows = reader.fieldnames, list(reader)
    rows = change(rows) or rows
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=header, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    path.write_text(buffer.getvalue(), encoding="utf-8", newline="")


def add_revision(pack, *, forget_old):
    documents = Path(pack) / "2026-S1/knowledge/documents"
    text = (documents / "DOC-CONV-CURRENT-001.md").read_text(encoding="utf-8")
    text = text.replace("révision 1", "révision 2").replace("`110 %`", "`120 %`")
    (documents / "DOC-CONV-CURRENT-002.md").write_text(text, encoding="utf-8", newline="\n")
    checksum = hashlib.sha256((documents / "DOC-CONV-CURRENT-002.md").read_bytes()).hexdigest()

    def change(rows):
        base = next(r for r in rows if r["document_id"] == "DOC-CONV-CURRENT-001")
        if not forget_old:
            base["status"] = "superseded"
        rows.append({**base, "document_id": "DOC-CONV-CURRENT-002", "revision": "2",
                     "title": "Triage pédagogique — courant des convoyeurs (rév. 2)", "effective_at": "2026-09-28",
                     "asset_path": "DOC-CONV-CURRENT-002.md", "status": "active",
                     "supersedes_document_id": "DOC-CONV-CURRENT-001", "checksum_sha256": checksum})
        return rows
    edit_manifest(pack, change)


def deploy(directory, pack):
    """État « après migration » : FTS5 actif, JSON conservé en repli."""
    directory.mkdir(parents=True)
    export = directory / "corpus.json"
    mg.export_v2(pack, export, events_dir=directory)
    mg.build_candidate(export, directory / "fts5.sqlite")
    mg.activate_v2(directory, "corpus.json", "json", pack=pack, slot="fallback")
    mg.activate_v2(directory, "fts5.sqlite", "fts5", pack=pack, slot="active")
    return export


def rebuild(directory, pack, suffix):
    manual(f"reconstruction {suffix} : export_v2 + build_candidate + activate_v2 (x2)")
    export = directory / f"corpus_{suffix}.json"
    mg.export_v2(pack, export, events_dir=directory)
    mg.build_candidate(export, directory / f"fts5_{suffix}.sqlite")
    mg.activate_v2(directory, export.name, "json", pack=pack, slot="fallback")
    mg.activate_v2(directory, f"fts5_{suffix}.sqlite", "fts5", pack=pack, slot="active")


def quality(cases, results):
    answerable = [(c, r) for c, r in zip(cases, results) if c["expected"]]

    def hit(k, subset):
        return round(sum(bool(set(c["expected"]) & set(r[:k])) for c, r in subset) / len(subset), 3) if subset else None

    def mrr(subset):
        total = 0.0
        for c, r in subset:
            rank = next((i + 1 for i, d in enumerate(r) if d in c["expected"]), None)
            total += 1 / rank if rank else 0
        return round(total / len(subset), 3)
    groups = {g: [(c, r) for c, r in answerable if c["group"] == g] for g in ("vocabulaire", "reformule")}
    return {
        "hit_at_1": hit(1, answerable), "hit_at_3": hit(3, answerable), "mrr": mrr(answerable),
        "hit_at_1_vocabulaire": hit(1, groups["vocabulaire"]), "hit_at_1_reformule": hit(1, groups["reformule"]),
        "hit_at_3_reformule": hit(3, groups["reformule"]),
        "sans_reponse_avec_resultats": sum(bool(r) for c, r in zip(cases, results) if not c["expected"]),
        "forbidden_renvoyes": sum(len(set(c.get("forbidden", [])) & set(r)) for c, r in zip(cases, results)),
        "echecs_hit3": [c["case_id"] for c, r in answerable if not set(c["expected"]) & set(r[:3])],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=False)
    if hashlib.sha256(CASES.read_bytes()).hexdigest() != FROZEN_SHA256:
        raise SystemExit("cases.jsonl a changé depuis le gel du contrat : mesure refusée")
    cases = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line.strip()]
    work = out / "copies"
    report = {"contract_cases_sha256": FROZEN_SHA256, "scenarios": {}}

    # --- avant / candidat sur le corpus nominal ------------------------------------------
    pack = copy_corpus(work / "nominal")
    bench = work / "nominal" / "banc"
    started = time.perf_counter()
    manual("migration : export_v2 + build_candidate + activate_v2 (fallback, active)")
    export = deploy(bench, pack)
    migration_ms = ms(started)
    before = [lab.search(export, "json", c["question"], c["role"]) for c in cases]
    started = time.perf_counter()
    after_serve = [mg.serve(bench, c["question"], c["role"], pack=pack) for c in cases]
    after_ms = ms(started)
    after = [r["results"] for r in after_serve]
    started = time.perf_counter()
    for c in cases:
        lab.search(export, "json", c["question"], c["role"])
    before_ms = ms(started)
    report["avant"] = {**quality(cases, before), "duree_24_cas_ms": before_ms}
    report["candidat"] = {**quality(cases, after), "duree_24_cas_ms": after_ms,
                          "modes": sorted({r["mode"] for r in after_serve}), "migration_ms": migration_ms,
                          "octets": {"export": export.stat().st_size, "fts5": (bench / "fts5.sqlite").stat().st_size}}
    report["comparaison_cas"] = [{"case_id": c["case_id"], "group": c["group"], "role": c["role"],
                                  "expected": c["expected"], "avant": b, "candidat": a}
                                 for c, b, a in zip(cases, before, after)]

    # Métadonnées champ par champ.
    exported = {d["document_id"]: d for d in lab.read_export(export)["documents"]}
    indexed = {d["document_id"]: d for d in mg.index_documents(bench / "fts5.sqlite", "fts5")}
    report["metadonnees_identiques"] = exported == indexed and len(indexed) == 7

    # Fuites : 11 sondes du document restreint, deux rôles.
    restricted = next(d["text"] for d in exported.values() if d["document_id"] == RESTRICTED)
    probes = [line.strip("#-* ").strip() for line in restricted.splitlines() if len(line.strip()) > 20]
    leaks = 0
    for role in ("public", "technicien"):
        for probe in probes:
            leaks += RESTRICTED in mg.serve(bench, probe, role, pack=pack)["results"]
    report["fuites"] = {"sondes": len(probes) * 2, "renvois": leaks}

    # Statistiques isolées : pour chaque rôle, index par rôle = index du seul périmètre visible.
    isolation = {}
    for role in sorted(lab.ROLES):
        visible = [d for d in exported.values() if role in d["allowed_roles"]]
        if not visible:
            continue
        subset = bench / f"perimetre_{role}.json"
        lab.save(subset, {"schema_version": 1, "documents": visible})
        alone = bench / f"perimetre_{role}.sqlite"
        migrate_fts5(subset, alone, layout="shared")
        isolation[role] = all(scores_fts5(bench / "fts5.sqlite", c["question"], role) == scores_fts5(alone, c["question"], role)
                              for c in cases)
    report["statistiques_isolees"] = isolation

    # --- scénarios -------------------------------------------------------------------------
    # M-REV-A : ancienne révision oubliée.
    pack_a = copy_corpus(work / "rev-a")
    add_revision(pack_a, forget_old=True)
    try:
        mg.export_v2(pack_a, work / "rev-a" / "corpus.json")
        outcome = "export accepté"
    except mg.AdmissionError as exc:
        outcome = f"export refusé : {exc}"
    report["scenarios"]["M-REV-A"] = {"resultat": outcome, "conforme": outcome.startswith("export refusé")}

    # M-REV-B : nouvelle révision correcte, index d'avant périmé.
    pack_b = copy_corpus(work / "rev-b")
    bench_b = work / "rev-b" / "banc"
    deploy(bench_b, pack_b)
    b201 = next(c for c in cases if c["case_id"] == "B2-01")
    old = mg.serve(bench_b, b201["question"], "technicien", pack=pack_b)
    add_revision(pack_b, forget_old=False)
    stale = mg.serve(bench_b, b201["question"], "technicien", pack=pack_b)
    started = time.perf_counter()
    rebuild(bench_b, pack_b, "rev2")
    rebuild_ms = ms(started)
    new = mg.serve(bench_b, b201["question"], "technicien", pack=pack_b)
    report["scenarios"]["M-REV-B"] = {
        "avant_changement": old, "index_perime": stale, "apres_reconstruction": new, "reconstruction_ms": rebuild_ms,
        "conforme": stale["mode"] == "refus" and "DOC-CONV-CURRENT-002" in new["results"]
                    and "DOC-CONV-CURRENT-001" not in new["results"]}

    # M-REVOC : révocation, puis tentative de retour arrière.
    pack_r = copy_corpus(work / "revoc")
    bench_r = work / "revoc" / "banc"
    deploy(bench_r, pack_r)
    b203 = next(c for c in cases if c["case_id"] == "B2-03")
    before_revoc = mg.serve(bench_r, b203["question"], "technicien", pack=pack_r)
    old_fts = mg.index_documents  # référence gardée pour lisibilité du rapport
    old_sha = lab.digest(bench_r / "fts5.sqlite")
    # Comportement du code actuel du banc (prédiction P5) : index lab.py construit avant.
    lab_bench = work / "revoc" / "banc_lab"
    lab_bench.mkdir()
    lab.export_corpus(pack_r, lab_bench / "corpus.json")
    lab.migrate(lab_bench / "corpus.json", lab_bench / "index.sqlite")
    lab.activate(lab_bench, "index.sqlite", "sqlite")
    edit_manifest(pack_r, lambda rows: [
        {**r, "allowed_roles": "superviseur;auditeur"} if r["document_id"] == "DOC-STEAM-PRESS-001" else r for r in rows])
    lab_after = lab.search_active(lab_bench, b203["question"], "technicien")
    stale_r = mg.serve(bench_r, b203["question"], "technicien", pack=pack_r)
    started = time.perf_counter()
    rebuild(bench_r, pack_r, "revoc")
    rebuild_r_ms = ms(started)
    tech = mg.serve(bench_r, b203["question"], "technicien", pack=pack_r)
    sup = mg.serve(bench_r, b203["question"], "superviseur", pack=pack_r)
    manual("tentative de retour arrière vers l'index d'avant la révocation")
    try:
        mg.activate_v2(bench_r, "fts5.sqlite", "fts5", pack=pack_r, expected_sha256=old_sha)
        rollback = "accepté"
    except mg.RightRestored as exc:
        rollback = f"refusé : {exc}"
    report["scenarios"]["M-REVOC"] = {
        "avant": before_revoc, "code_actuel_du_banc_apres_revocation": lab_after,
        "candidat_index_perime": stale_r, "reconstruction_ms": rebuild_r_ms,
        "technicien_apres": tech, "superviseur_apres": sup, "retour_arriere_vers_avant": rollback,
        "prediction_P5_code_actuel_sert_encore": "DOC-STEAM-PRESS-001" in lab_after,
        "conforme": stale_r["mode"] == "refus" and "DOC-STEAM-PRESS-001" not in tech["results"]
                    and "DOC-STEAM-PRESS-001" in sup["results"] and rollback.startswith("refusé")}

    # M-QUAR : document altéré.
    pack_q = copy_corpus(work / "quar")
    target = pack_q / "2026-S1/knowledge/documents/DOC-CHILL-TEMP-001.md"
    target.write_text(target.read_text(encoding="utf-8") + "\nLigne ajoutée hors processus.\n", encoding="utf-8", newline="\n")
    bench_q = work / "quar" / "banc"
    deploy(bench_q, pack_q)
    value = json.loads((bench_q / "corpus.json").read_text(encoding="utf-8"))
    b205 = next(c for c in cases if c["case_id"] == "B2-05")
    served = mg.serve(bench_q, b205["question"], "technicien", pack=pack_q)
    events = [json.loads(line) for line in (bench_q / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    report["scenarios"]["M-QUAR"] = {
        "quarantaine": value["quarantine"], "documents_servis": len(value["documents"]), "reponse_B2_05": served,
        "alerte_tracee": any(e["event"] == "quarantaine" for e in events),
        "conforme": len(value["documents"]) == 6 and "DOC-CHILL-TEMP-001" not in served["results"]
                    and any(e["event"] == "quarantaine" for e in events)}

    # M-PANNE : candidat supprimé, puis corrompu.
    pack_p = copy_corpus(work / "panne")
    bench_p = work / "panne" / "banc"
    deploy(bench_p, pack_p)
    b207 = next(c for c in cases if c["case_id"] == "B2-07")
    nominal = mg.serve(bench_p, b207["question"], "technicien", pack=pack_p)
    original = (bench_p / "fts5.sqlite").read_bytes()
    (bench_p / "fts5.sqlite").unlink()
    started = time.perf_counter()
    missing = mg.serve(bench_p, b207["question"], "technicien", pack=pack_p)
    failover_ms = ms(started)
    (bench_p / "fts5.sqlite").write_bytes(b"index corrompu pour exercice local")
    corrupted = mg.serve(bench_p, b207["question"], "technicien", pack=pack_p)
    (bench_p / "corpus.json").write_text("{}", encoding="utf-8")
    both = mg.serve(bench_p, b207["question"], "technicien", pack=pack_p)
    events_p = [json.loads(line) for line in (bench_p / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    served_events = [e for e in events_p if e["event"] in ("reponse", "refus")]
    report["scenarios"]["M-PANNE"] = {
        "nominal": nominal, "candidat_absent": missing, "bascule_ms": failover_ms, "candidat_corrompu": corrupted,
        "candidat_et_repli_hors_service": both,
        "traces_coherentes": len(served_events) == 4 and [e.get("mode", "refus") for e in served_events] == ["nominal", "degrade", "degrade", "refus"],
        "texte_de_question_dans_les_traces": any(b207["question"] in json.dumps(e, ensure_ascii=False) for e in events_p),
        "conforme": missing["mode"] == "degrade" and corrupted["mode"] == "degrade" and both["mode"] == "refus"
                    and missing["results"] == nominal["results"][:0] + missing["results"]}
    report["scenarios"]["M-PANNE"]["conforme"] = (missing["mode"] == "degrade" and corrupted["mode"] == "degrade"
                                                  and both["mode"] == "refus" and report["scenarios"]["M-PANNE"]["traces_coherentes"])
    (bench_p / "fts5.sqlite").write_bytes(original)

    # M-ROLLBACK : retour nominal au JSON par empreinte.
    bench_n = bench
    sha_json = lab.digest(bench_n / "corpus.json")
    manual("retour arrière : activate_v2(corpus.json, json, expected_sha256)")
    started = time.perf_counter()
    mg.activate_v2(bench_n, "corpus.json", "json", pack=pack, slot="active", expected_sha256=sha_json)
    rolled = [mg.serve(bench_n, c["question"], c["role"], pack=pack)["results"] for c in cases]
    rollback_ms = ms(started)
    report["scenarios"]["M-ROLLBACK"] = {"identique_a_avant": rolled == before, "duree_ms": rollback_ms,
                                         "conforme": rolled == before}

    # --- gates du contrat --------------------------------------------------------------------
    a, c = report["avant"], report["candidat"]
    s = report["scenarios"]
    report["gates"] = {
        "fuite": {"seuil": "0", "valeur": report["fuites"]["renvois"] + c["forbidden_renvoyes"],
                  "passe": report["fuites"]["renvois"] + c["forbidden_renvoyes"] == 0, "type": "bloquant"},
        "statistiques_isolees": {"valeur": isolation, "passe": all(isolation.values()), "type": "bloquant"},
        "metadonnees": {"passe": report["metadonnees_identiques"], "type": "bloquant"},
        "scenarios_4": {"valeur": {k: s[k]["conforme"] for k in ("M-REV-A", "M-REV-B", "M-REVOC", "M-QUAR")},
                        "passe": all(s[k]["conforme"] for k in ("M-REV-A", "M-REV-B", "M-REVOC", "M-QUAR")), "type": "bloquant"},
        "retour_arriere": {"passe": s["M-ROLLBACK"]["conforme"] and s["M-REVOC"]["retour_arriere_vers_avant"].startswith("refusé"),
                           "type": "bloquant"},
        "qualite_hit3": {"seuil": f">= {a['hit_at_3']} - 0.05", "valeur": c["hit_at_3"],
                         "passe": c["hit_at_3"] >= a["hit_at_3"] - 0.05, "type": "majeur"},
        "qualite_hit1": {"seuil": f">= {a['hit_at_1']} - 0.10", "valeur": c["hit_at_1"],
                         "passe": c["hit_at_1"] >= a["hit_at_1"] - 0.10, "type": "majeur"},
        "reprise": {"seuil": "< 15 min", "valeur_ms": s["M-PANNE"]["bascule_ms"], "passe": s["M-PANNE"]["bascule_ms"] < 900000,
                    "type": "majeur"},
    }
    report["operations_manuelles"] = MANUAL
    report["predictions"] = {
        "P1_hit3_ge_0_90": {"avant": a["hit_at_3"], "candidat": c["hit_at_3"], "tenue": a["hit_at_3"] >= .9 and c["hit_at_3"] >= .9},
        "P2_fts5_meilleur_hit1_reformule": {"avant": a["hit_at_1_reformule"], "candidat": c["hit_at_1_reformule"],
                                            "tenue": c["hit_at_1_reformule"] > a["hit_at_1_reformule"]},
        "P3_sans_abstention": {"avant": a["sans_reponse_avec_resultats"], "candidat": c["sans_reponse_avec_resultats"],
                               "tenue": a["sans_reponse_avec_resultats"] == 4 and c["sans_reponse_avec_resultats"] == 4},
        "P4_zero_fuite": {"tenue": report["gates"]["fuite"]["passe"]},
        "P5_code_actuel_echoue_revocation": {"tenue": s["M-REVOC"]["prediction_P5_code_actuel_sert_encore"]},
        "P6_reconstruction_sous_1s": {"valeurs_ms": [s["M-REV-B"]["reconstruction_ms"], s["M-REVOC"]["reconstruction_ms"]],
                                      "tenue": max(s["M-REV-B"]["reconstruction_ms"], s["M-REVOC"]["reconstruction_ms"]) < 1000},
    }
    lab.save(out / "report.json", report)
    shutil.rmtree(work)
    print(json.dumps({"avant": a, "candidat": {k: v for k, v in c.items()}}, ensure_ascii=False, indent=1))
    print(json.dumps({k: v["passe"] for k, v in report["gates"].items()}, ensure_ascii=False))
    print(json.dumps({k: v["tenue"] for k, v in report["predictions"].items()}, ensure_ascii=False))
    print(json.dumps({k: v["conforme"] for k, v in s.items()}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
