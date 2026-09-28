"""Contrats du candidat de migration : admission, fraîcheur, quarantaine, retour arrière."""
import csv
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import migration as mg

PACK = Path(__file__).resolve().parents[3] / "data_pack"


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.pack = self.root / "pack"
        shutil.copytree(PACK / "2026-S1/knowledge", self.pack / "2026-S1/knowledge")
        self.bench = self.root / "banc"
        self.bench.mkdir()
        mg.export_v2(self.pack, self.bench / "corpus.json", events_dir=self.bench)
        mg.build_candidate(self.bench / "corpus.json", self.bench / "fts5.sqlite")
        mg.activate_v2(self.bench, "corpus.json", "json", pack=self.pack, slot="fallback")
        mg.activate_v2(self.bench, "fts5.sqlite", "fts5", pack=self.pack, slot="active")

    def edit(self, change):
        path = mg.manifest_path(self.pack)
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            header, rows = reader.fieldnames, list(reader)
        buffer = io.StringIO(newline="")
        writer = csv.DictWriter(buffer, fieldnames=header, lineterminator="\n")
        writer.writeheader()
        writer.writerows(change(rows))
        path.write_text(buffer.getvalue(), encoding="utf-8", newline="")

    def test_nominal_service_and_export_is_lf(self):
        served = mg.serve(self.bench, "vibration pompe palier", "technicien", pack=self.pack)
        self.assertEqual(served["mode"], "nominal")
        self.assertIn("DOC-PUMP-VIB-001", served["results"])
        self.assertNotIn(b"\r", (self.bench / "corpus.json").read_bytes())

    def test_two_active_revisions_refused(self):
        def change(rows):
            base = next(r for r in rows if r["document_id"] == "DOC-LOTO-001")
            base["status"] = "active"
            return rows
        self.edit(change)
        with self.assertRaises(mg.AdmissionError):
            mg.export_v2(self.pack, self.root / "x.json")

    def test_revocation_makes_both_indexes_stale_and_rollback_refused(self):
        old_sha = mg.digest(self.bench / "fts5.sqlite")
        self.edit(lambda rows: [{**r, "allowed_roles": "superviseur;auditeur"} if r["document_id"] == "DOC-PUMP-VIB-001" else r
                                for r in rows])
        served = mg.serve(self.bench, "vibration pompe palier", "technicien", pack=self.pack)
        self.assertEqual((served["mode"], served["results"]), ("refus", []))
        with self.assertRaises(mg.RightRestored):
            mg.activate_v2(self.bench, "fts5.sqlite", "fts5", pack=self.pack, expected_sha256=old_sha)

    def test_altered_document_quarantined_others_served(self):
        target = self.pack / "2026-S1/knowledge/documents/DOC-CHILL-TEMP-001.md"
        target.write_text(target.read_text(encoding="utf-8") + "\najout\n", encoding="utf-8", newline="\n")
        value = mg.export_v2(self.pack, self.root / "q.json", events_dir=self.bench)
        self.assertEqual(len(value["documents"]), 6)
        quarantined = json.loads((self.root / "q.json").read_text(encoding="utf-8"))["quarantine"]
        self.assertEqual([q["document_id"] for q in quarantined], ["DOC-CHILL-TEMP-001"])

    def test_missing_candidate_falls_back_and_traces_hold_no_question(self):
        (self.bench / "fts5.sqlite").unlink()
        question = "vibration pompe palier"
        served = mg.serve(self.bench, question, "technicien", pack=self.pack)
        self.assertEqual(served["mode"], "degrade")
        self.assertIn("DOC-PUMP-VIB-001", served["results"])
        self.assertNotIn(question, (self.bench / "events.jsonl").read_text(encoding="utf-8"))

    def test_candidate_metadata_equal_to_export(self):
        exported = {d["document_id"]: d for d in mg.read_export(self.bench / "corpus.json")["documents"]}
        indexed = {d["document_id"]: d for d in mg.index_documents(self.bench / "fts5.sqlite", "fts5")}
        self.assertEqual(exported, indexed)


if __name__ == "__main__":
    unittest.main()
