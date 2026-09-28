#!/usr/bin/env python3
"""Banc local JSON → SQLite, sans réseau ni modèle à télécharger (Python 3.11+)."""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time

ROLES = {"public", "technicien", "superviseur", "auditeur"}
TOKEN = re.compile(r"[\wÀ-ÿ-]+", re.UNICODE)

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def read_export(path):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if value.get("schema_version") != 1 or not value.get("documents"):
        raise ValueError("export vide ou version inconnue")
    seen = set()
    for row in value["documents"]:
        if row["document_id"] in seen:
            raise ValueError("identifiant dupliqué")
        seen.add(row["document_id"])
        if not row["allowed_roles"] or not set(row["allowed_roles"]) <= ROLES:
            raise ValueError("droits absents ou inconnus")
        if row["status"] != "active" or not row["revision"]:
            raise ValueError("révision non active ou absente")
        if hashlib.sha256(row["text"].encode()).hexdigest() != row["checksum_sha256"]:
            raise ValueError("contenu altéré")
    return value

def export_corpus(pack, destination):
    root = Path(pack) / "2026-S1" / "knowledge"
    manifest = root / "manifest.csv"
    with manifest.open(encoding="utf-8", newline="") as handle:
        source = list(csv.DictReader(handle))
    documents = []
    for row in source:
        asset = (root / "documents" / row["asset_path"]).resolve()
        if (root / "documents").resolve() not in asset.parents:
            raise ValueError("document hors corpus")
        if digest(asset) != row["checksum_sha256"]:
            raise ValueError("checksum source invalide")
        if row["status"] == "active":
            documents.append({**row, "allowed_roles": sorted(row["allowed_roles"].split(";")),
                              "text": asset.read_text(encoding="utf-8")})
    save(destination, {"schema_version": 1, "manifest_sha256": digest(manifest), "documents": documents})
    return read_export(destination)

def migrate(export, database):
    value = read_export(export)
    database = Path(database)
    if database.exists():
        raise FileExistsError("refus d'écraser un index existant")
    with sqlite3.connect(database) as conn:
        conn.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.executemany("INSERT INTO metadata VALUES (?, ?)",
                         [("schema_version", "1"), ("source_export_sha256", digest(export))])
        conn.execute("CREATE TABLE documents (id TEXT PRIMARY KEY, body TEXT NOT NULL)")
        conn.execute("CREATE TABLE roles (document_id TEXT, role TEXT, PRIMARY KEY(document_id, role))")
        for row in value["documents"]:
            conn.execute("INSERT INTO documents VALUES (?, ?)", (row["document_id"], json.dumps(row, ensure_ascii=False)))
            conn.executemany("INSERT INTO roles VALUES (?, ?)", [(row["document_id"], role) for role in row["allowed_roles"]])

def score(query, text):
    q = Counter(token.lower() for token in TOKEN.findall(query))
    d = Counter(token.lower() for token in TOKEN.findall(text))
    return sum(min(count, d[token]) for token, count in q.items())

def search(path, backend, query, role, *, scorer=score):
    if role not in ROLES:
        raise ValueError("rôle inconnu")
    if backend == "json":
        rows = [row for row in read_export(path)["documents"] if role in row["allowed_roles"]]
    elif backend == "sqlite":
        # mode=ro refuse un index absent ; pas de création silencieuse d'une base vide.
        with sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True) as conn:
            if conn.execute("SELECT value FROM metadata WHERE key='schema_version'").fetchone() != ("1",):
                raise ValueError("version d'index inconnue")
            rows = [json.loads(item[0]) for item in conn.execute(
                "SELECT d.body FROM documents d JOIN roles r ON d.id=r.document_id WHERE r.role=?", (role,))]
        if any(role not in row["allowed_roles"] for row in rows):
            raise ValueError("ACL incohérentes")
    else:
        raise ValueError("backend inconnu")
    # Filtrage avant scoring : le test espion contrôle les textes réellement classés.
    ranked = sorted(((scorer(query, row["text"]), row["document_id"]) for row in rows), reverse=True)
    return [identifier for value, identifier in ranked if value > 0][:3]

def search_active(directory, query, role):
    active = json.loads((Path(directory) / "active.json").read_text(encoding="utf-8"))
    target = (Path(directory) / active["path"]).resolve()
    if Path(directory).resolve() not in target.parents or digest(target) != active["sha256"]:
        raise ValueError("index actif absent, hors périmètre ou altéré")
    return search(target, active["backend"], query, role)

def activate(directory, name, backend, *, expected_sha256=None):
    target = (Path(directory) / name).resolve()
    if Path(directory).resolve() not in target.parents:
        raise ValueError("index hors répertoire de travail")
    actual = digest(target)
    if expected_sha256 is not None and actual != expected_sha256:
        raise ValueError("source de reprise altérée")
    save(Path(directory) / "active.json", {"path": name, "backend": backend, "sha256": actual})

def exercise(pack, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    export = output / "corpus.json"
    database = output / "index.sqlite"
    value = export_corpus(pack, export)
    original_export_hash = digest(export)
    activate(output, export.name, "json")
    questions = [json.loads(line) for line in (Path(pack) / "2026-S1/rag_eval/questions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    questions = [q for q in questions if q["split"] == "calibration"]
    def replay():
        started = time.perf_counter()
        result = [search_active(output, q["question"], q["role"]) for q in questions]
        return result, round((time.perf_counter() - started) * 1000, 3)
    before, before_ms = replay()
    started = time.perf_counter()
    migrate(export, database)
    sqlite_bytes = database.stat().st_size
    migration_ms = round((time.perf_counter() - started) * 1000, 3)
    activate(output, database.name, "sqlite")
    after, after_ms = replay()
    # Panne réelle et bornée du fichier candidat, puis retour à la source conservée.
    database.write_bytes(b"index corrompu pour exercice local")
    detected = False
    try:
        search_active(output, questions[0]["question"], questions[0]["role"])
    except ValueError:
        detected = True
    started = time.perf_counter()
    activate(output, export.name, "json", expected_sha256=original_export_hash)
    rollback, rollback_ms = replay()
    recovery_ms = round((time.perf_counter() - started) * 1000, 3)
    def hit_at_3(results):
        pairs = [(q, r) for q, r in zip(questions, results) if q["answerable"]]
        return sum(bool(set(q["expected_document_ids"]) & set(r)) for q, r in pairs) / len(pairs)
    report = {
        "scope": "local_storage_migration_only", "documents": len(value["documents"]),
        "calibration_questions": len(questions), "test_split_used": False,
        "ranking_equal": before == after, "rollback_equal": before == rollback,
        "corruption_detected": detected, "hit_at_3_before": hit_at_3(before),
        "hit_at_3_after": hit_at_3(after), "migration_ms": migration_ms,
        "recovery_ms": recovery_ms, "replay_ms": {"json": before_ms, "sqlite": after_ms, "rollback": rollback_ms},
        "source_export_sha256": original_export_hash,
        "export_bytes": export.stat().st_size, "sqlite_bytes_before_corruption": sqlite_bytes,
        "cost_eur": None, "energy_wh": None,
        "limitations": ["corpus pédagogique réduit", "pas de génération LLM", "pas de concurrence ni de fournisseur distant", "latences locales non extrapolables"],
        "observations": [{"eval_id": q["eval_id"], "before": b, "after": a, "rollback": r} for q,b,a,r in zip(questions,before,after,rollback)],
    }
    report["status"] = "passed" if before == after == rollback and detected else "failed"
    save(output / "report.json", report)
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-pack", type=Path, default=Path(__file__).resolve().parents[2] / "data_pack")
    parser.add_argument("--output", type=Path, default=Path("results/migration-r1"))
    args = parser.parse_args()
    result = exercise(args.data_pack, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result["status"] == "passed" else 1)
