"""Contrats de l'alternative FTS5 : syntaxe neutralisée, droits, statistiques."""
from contextlib import closing
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab import save
from fts5 import migrate_fts5, quote_query, scores_fts5, search_fts5

PACK = Path(__file__).resolve().parents[3] / "data_pack"


def document(identifier, roles, text):
    return {"document_id": identifier, "allowed_roles": roles, "text": text,
            "checksum_sha256": hashlib.sha256(text.encode()).hexdigest(), "revision": "1", "status": "active"}


class Fts5Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.documents = [
            document("PUBLIC", ["public", "technicien"], "procédure publique de consignation"),
            document("TECH", ["technicien"], "procédure de consignation pompe vibration"),
            document("SECRET", ["superviseur"], "procédure consignation consignation consignation réservée"),
        ]
        self.export = self.root / "corpus.json"
        save(self.export, {"schema_version": 1, "documents": self.documents})

    def build(self, name, layout, documents=None):
        export = self.export
        if documents is not None:
            export = self.root / f"{name}.json"
            save(export, {"schema_version": 1, "documents": documents})
        path = self.root / f"{name}.sqlite"
        migrate_fts5(export, path, layout=layout)
        return path

    def test_raw_question_breaks_fts5_and_quoted_query_does_not(self):
        index = self.build("shared", "shared")
        with self.assertRaises(sqlite3.OperationalError):
            search_fts5(index, "Faut-il consigner la pompe ?", "technicien", mode="naive")
        self.assertIn("TECH", search_fts5(index, "Faut-il consigner la pompe ?", "technicien"))

    def test_every_calibration_question_is_a_valid_quoted_query(self):
        rows = [json.loads(line) for line in (PACK / "2026-S1/rag_eval/questions.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
        index = self.build("shared", "shared")
        for row in rows:
            if row["split"] == "calibration":
                search_fts5(index, row["question"], row["role"])
        self.assertEqual(quote_query('a"b OR c NEAR d'), '"a" OR "b" OR "or" OR "c" OR "near" OR "d"')

    def test_restricted_document_never_returned_in_both_layouts(self):
        for layout in ("shared", "per_role"):
            index = self.build(layout, layout)
            for role in ("public", "technicien"):
                self.assertNotIn("SECRET", search_fts5(index, "procédure consignation réservée", role))
            self.assertEqual(search_fts5(index, "réservée", "superviseur"), ["SECRET"])

    def test_shared_statistics_see_restricted_documents_per_role_do_not(self):
        without = [row for row in self.documents if row["document_id"] != "SECRET"]
        shared = self.build("shared", "shared")
        shared_without = self.build("shared_without", "shared", without)
        per_role = self.build("per_role", "per_role")
        # Terme discriminant : un terme présent partout a un IDF quasi nul et
        # masquerait l'effet du document restreint sur les statistiques.
        query = "pompe vibration"
        self.assertNotEqual(scores_fts5(shared, query, "technicien"), scores_fts5(shared_without, query, "technicien"))
        self.assertEqual(scores_fts5(per_role, query, "technicien"), scores_fts5(shared_without, query, "technicien"))

    def test_existing_index_preserved_and_unknown_version_rejected(self):
        index = self.build("shared", "shared")
        original = index.read_bytes()
        with self.assertRaises(FileExistsError):
            migrate_fts5(self.export, index)
        self.assertEqual(index.read_bytes(), original)
        with closing(sqlite3.connect(index)) as conn, conn:
            conn.execute("UPDATE metadata SET value='0' WHERE key='schema_version'")
        with self.assertRaises(ValueError):
            search_fts5(index, "procédure", "technicien")


if __name__ == "__main__":
    unittest.main()
