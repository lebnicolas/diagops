"""Alternative d'index : SQLite FTS5 (BM25), sans dépendance ni téléchargement.

Le banc du starter (`lab.py`) change le stockage mais garde le score lexical.
Ce module change réellement le moteur de classement : FTS5 tokenise avec
`unicode61` (casse et accents neutralisés) et classe par BM25, qui normalise par
la longueur des documents. Il reprend l'export de `lab.py` et ses contrôles
(`read_export`) : même contrat d'entrée, droits et révisions vérifiés.

Deux manières d'appliquer les droits, comparées par le banc :

- `shared` : une table FTS unique, filtrée par rôle dans la même requête. Aucun
  document interdit n'est renvoyé, mais les statistiques BM25 (fréquence des
  termes, longueur moyenne) sont calculées sur tout le corpus, documents
  restreints compris ;
- `per_role` : une table FTS par rôle, qui ne contient que les documents
  visibles. Les statistiques ne voient que le périmètre du rôle.

Deux manières de passer la requête :

- `naive` : la question brute passée à MATCH, comme on le ferait en premier ;
- `quoted` : la question tokenisée comme dans `lab.py`, chaque terme entre
  guillemets et reliés par OR.
"""
from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import sqlite3

from lab import ROLES, TOKEN, digest, read_export

SCHEMA_VERSION = "fts5-1"


def migrate_fts5(export, database, *, layout: str = "shared") -> None:
    if layout not in {"shared", "per_role"}:
        raise ValueError("disposition inconnue")
    value = read_export(export)
    database = Path(database)
    if database.exists():
        raise FileExistsError("refus d'écraser un index existant")
    with closing(sqlite3.connect(database)) as conn, conn:
        conn.execute("CREATE TABLE metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        conn.executemany("INSERT INTO metadata VALUES (?, ?)", [
            ("schema_version", SCHEMA_VERSION), ("layout", layout),
            ("source_export_sha256", digest(export)),
        ])
        conn.execute("CREATE TABLE documents (id TEXT PRIMARY KEY, body TEXT NOT NULL)")
        conn.execute("CREATE TABLE roles (document_id TEXT, role TEXT, PRIMARY KEY(document_id, role))")
        for row in value["documents"]:
            conn.execute("INSERT INTO documents VALUES (?, ?)",
                         (row["document_id"], json.dumps(row, ensure_ascii=False)))
            conn.executemany("INSERT INTO roles VALUES (?, ?)",
                             [(row["document_id"], role) for role in row["allowed_roles"]])
        tables = ["fts_shared"] if layout == "shared" else [f"fts_{role}" for role in sorted(ROLES)]
        for table in tables:
            conn.execute(f"CREATE VIRTUAL TABLE {table} USING fts5(document_id UNINDEXED, text)")
        for row in value["documents"]:
            if layout == "shared":
                conn.execute("INSERT INTO fts_shared VALUES (?, ?)", (row["document_id"], row["text"]))
            else:
                for role in row["allowed_roles"]:
                    conn.execute(f"INSERT INTO fts_{role} VALUES (?, ?)", (row["document_id"], row["text"]))


def quote_query(query: str) -> str:
    """Termes de la question, entre guillemets, reliés par OR.

    Les guillemets neutralisent la syntaxe FTS5 (`-`, `:`, `*`, `NEAR`, `AND`…) :
    un terme reste un terme, jamais un opérateur ou un nom de colonne.
    """
    terms = []
    for token in TOKEN.findall(query):
        term = token.lower().replace('"', '""')
        if term not in terms:
            terms.append(term)
    return " OR ".join(f'"{term}"' for term in terms)


def search_fts5(path, query, role, *, mode: str = "quoted", limit: int = 3):
    if role not in ROLES:
        raise ValueError("rôle inconnu")
    match = query if mode == "naive" else quote_query(query)
    if not match:
        return []
    with closing(sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)) as conn:
        meta = dict(conn.execute("SELECT key, value FROM metadata"))
        if meta.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("version d'index inconnue")
        if meta["layout"] == "shared":
            # Le filtre de rôle est dans la même requête que MATCH : un document
            # interdit n'est jamais classé en sortie. Ses statistiques, si.
            rows = conn.execute(
                "SELECT f.document_id, bm25(fts_shared) AS s FROM fts_shared f "
                "JOIN roles r ON r.document_id = f.document_id AND r.role = ? "
                "WHERE fts_shared MATCH ? ORDER BY s, f.document_id LIMIT ?",
                (role, match, limit)).fetchall()
        else:
            table = f"fts_{role}"
            rows = conn.execute(
                f"SELECT document_id, bm25({table}) AS s FROM {table} "
                f"WHERE {table} MATCH ? ORDER BY s, document_id LIMIT ?",
                (match, limit)).fetchall()
        allowed = {item[0] for item in conn.execute(
            "SELECT document_id FROM roles WHERE role = ?", (role,))}
    if any(identifier not in allowed for identifier, _ in rows):
        raise ValueError("ACL incohérentes")
    return [identifier for identifier, _ in rows]


def scores_fts5(path, query, role):
    """Scores BM25 bruts des documents visibles, pour mesurer l'effet du corpus."""
    with closing(sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)) as conn:
        layout = dict(conn.execute("SELECT key, value FROM metadata"))["layout"]
        table = "fts_shared" if layout == "shared" else f"fts_{role}"
        rows = conn.execute(
            f"SELECT f.document_id, bm25({table}) FROM {table} f "
            "JOIN roles r ON r.document_id = f.document_id AND r.role = ? "
            f"WHERE {table} MATCH ?", (role, quote_query(query))).fetchall()
    return {identifier: round(value, 6) for identifier, value in rows}
