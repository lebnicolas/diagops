"""Candidat de migration du brief 2 : FTS5 par rôle, lié à son manifeste.

Trois décisions d'architecture deviennent du code :

- ADR-0003 : l'export refuse deux révisions actives d'une même chaîne ; l'index
  enregistre l'empreinte du manifeste dont il vient, et un index dont
  l'empreinte ne correspond plus au manifeste courant est **refusé** ;
- ADR-0004 : un document dont le checksum ne correspond pas est mis en
  quarantaine avec son motif, les autres sont exportés ;
- migration_plan.md : un retour arrière qui rétablirait un droit retiré est
  refusé, quelle que soit l'empreinte du fichier.

Le mode dégradé bascule sur un index de repli (le JSON conservé), soumis aux
mêmes contrôles. Chaque décision est écrite dans un journal d'événements, sans
le texte des questions (seulement leur empreinte).
"""
from __future__ import annotations

from contextlib import closing
import csv
import hashlib
import json
from pathlib import Path
import sqlite3
import time

from lab import ROLES, digest, read_export, save, search as lexical_search
from fts5 import migrate_fts5, search_fts5

EXPORT_FIELDS = ("document_id", "title", "revision", "effective_at", "source_type", "license",
                 "sensitivity", "status", "supersedes_document_id", "checksum_sha256")


class AdmissionError(ValueError):
    """Le manifeste viole une règle d'admission : aucun export n'est produit."""


class StaleIndex(ValueError):
    """L'index ne correspond plus au manifeste courant."""


class RightRestored(ValueError):
    """Le retour arrière rétablirait un droit retiré."""


# -- journal ---------------------------------------------------------------------
def log(directory, event, **detail):
    path = Path(directory) / "events.jsonl"
    entry = {"t": round(time.time(), 3), "event": event, **detail}
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")


def fingerprint(text):
    return hashlib.sha256(text.encode()).hexdigest()[:12]


# -- export ----------------------------------------------------------------------
def manifest_path(pack):
    return Path(pack) / "2026-S1" / "knowledge" / "manifest.csv"


def manifest_acl(pack):
    """Couples (document, rôle) autorisés par le manifeste courant, documents actifs."""
    with manifest_path(pack).open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {(row["document_id"], role) for row in rows if row["status"] == "active"
            for role in row["allowed_roles"].split(";") if role}


def export_v2(pack, destination, *, events_dir=None):
    root = Path(pack) / "2026-S1" / "knowledge"
    with manifest_path(pack).open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    active = {row["document_id"] for row in rows if row["status"] == "active"}
    for row in rows:
        previous = row.get("supersedes_document_id")
        if row["status"] == "active" and previous and previous in active:
            if events_dir:
                log(events_dir, "export_refuse", motif="deux_revisions_actives",
                    documents=[previous, row["document_id"]])
            raise AdmissionError(f"deux révisions actives : {previous} et {row['document_id']}")
    documents, quarantine = [], []
    for row in rows:
        asset = (root / "documents" / row["asset_path"]).resolve()
        if (root / "documents").resolve() not in asset.parents:
            raise AdmissionError("document hors corpus")
        if row["status"] != "active":
            continue
        if not asset.is_file() or digest(asset) != row["checksum_sha256"]:
            quarantine.append({"document_id": row["document_id"], "motif": "checksum invalide ou fichier absent"})
            if events_dir:
                log(events_dir, "quarantaine", document_id=row["document_id"])
            continue
        documents.append({**{key: row[key] for key in EXPORT_FIELDS},
                          "allowed_roles": sorted(role for role in row["allowed_roles"].split(";") if role),
                          "text": asset.read_text(encoding="utf-8")})
    save(destination, {"schema_version": 1, "manifest_sha256": digest(manifest_path(pack)),
                       "documents": documents, "quarantine": quarantine})
    return read_export(destination)


# -- index -----------------------------------------------------------------------
def build_candidate(export, database):
    migrate_fts5(export, database, layout="per_role")
    manifest = json.loads(Path(export).read_text(encoding="utf-8"))["manifest_sha256"]
    with closing(sqlite3.connect(database)) as conn, conn:
        conn.execute("INSERT INTO metadata VALUES ('manifest_sha256', ?)", (manifest,))


def index_manifest(path, backend):
    if backend == "json":
        return json.loads(Path(path).read_text(encoding="utf-8")).get("manifest_sha256")
    with closing(sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)) as conn:
        row = conn.execute("SELECT value FROM metadata WHERE key='manifest_sha256'").fetchone()
    return row[0] if row else None


def index_documents(path, backend):
    if backend == "json":
        return read_export(path)["documents"]
    with closing(sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)) as conn:
        return [json.loads(item[0]) for item in conn.execute("SELECT body FROM documents ORDER BY id")]


def index_acl(path, backend):
    return {(row["document_id"], role) for row in index_documents(path, backend) for role in row["allowed_roles"]}


# -- activation et service -------------------------------------------------------
def activate_v2(directory, name, backend, *, pack, slot="active", expected_sha256=None):
    directory = Path(directory)
    target = (directory / name).resolve()
    if directory.resolve() not in target.parents:
        raise ValueError("index hors répertoire de travail")
    actual = digest(target)
    if expected_sha256 is not None and actual != expected_sha256:
        log(directory, "activation_refusee", slot=slot, index=name, motif="empreinte")
        raise ValueError("source de reprise altérée")
    restored = index_acl(target, backend) - manifest_acl(pack)
    if restored:
        log(directory, "activation_refusee", slot=slot, index=name, motif="droit_retire",
            couples=sorted(f"{d}/{r}" for d, r in restored))
        raise RightRestored(f"rétablirait {len(restored)} droit(s) retiré(s)")
    save(directory / f"{slot}.json", {"path": name, "backend": backend, "sha256": actual,
                                      "manifest_sha256": index_manifest(target, backend)})
    log(directory, "activation", slot=slot, index=name, backend=backend)


def _search_slot(directory, slot, query, role, pack):
    pointer = json.loads((Path(directory) / f"{slot}.json").read_text(encoding="utf-8"))
    target = (Path(directory) / pointer["path"]).resolve()
    if Path(directory).resolve() not in target.parents or not target.is_file():
        raise FileNotFoundError(f"index {slot} absent")
    if digest(target) != pointer["sha256"]:
        raise ValueError(f"index {slot} altéré")
    if pointer["manifest_sha256"] != digest(manifest_path(pack)):
        raise StaleIndex(f"index {slot} périmé")
    if pointer["backend"] == "json":
        return lexical_search(target, "json", query, role)
    return search_fts5(target, query, role)


def serve(directory, query, role, *, pack):
    """Recherche avec repli : actif, puis repli, puis refus explicite."""
    if role not in ROLES:
        raise ValueError("rôle inconnu")
    question = fingerprint(query)
    try:
        results = _search_slot(directory, "active", query, role, pack)
        log(directory, "reponse", mode="nominal", role=role, question=question, n=len(results))
        return {"mode": "nominal", "results": results}
    except (FileNotFoundError, ValueError, sqlite3.DatabaseError) as exc:
        reason = f"{type(exc).__name__}: {exc}"
    try:
        results = _search_slot(directory, "fallback", query, role, pack)
        log(directory, "reponse", mode="degrade", role=role, question=question, n=len(results), motif=reason)
        return {"mode": "degrade", "results": results, "motif": reason}
    except (FileNotFoundError, ValueError, sqlite3.DatabaseError) as exc:
        log(directory, "refus", role=role, question=question, motif=reason,
            repli=f"{type(exc).__name__}: {exc}")
        return {"mode": "refus", "results": [], "motif": reason}
