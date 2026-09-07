"""L'ingestion doit dire ce qui a changé, et refuser ce qui n'est pas attribuable.

`build_index.py` reconstruit sans comparer : le résultat est déterministe, mais rien n'empêche
un document d'être modifié à révision constante — auquel cas deux contenus différents portent la
même identité dans toutes les traces. Ces tests figent la détection et les refus d'admission.
"""

import csv

import pytest

from pipelines.build_index import build_index
from pipelines.ingest import decide, diff_against, validate_admission
from src.versioning import sha256


FIELDS = [
    "document_id", "title", "revision", "effective_at", "source_type", "asset_path",
    "license", "sensitivity", "status", "supersedes_document_id", "allowed_roles",
    "checksum_sha256",
]


def row(document_id, path, **overrides) -> dict:
    base = {
        "document_id": document_id, "title": f"Doc {document_id}", "revision": "1",
        "effective_at": "2026-01-15", "source_type": "procedure", "asset_path": path.name,
        "license": "formation_interne", "sensitivity": "interne", "status": "active",
        "supersedes_document_id": "", "allowed_roles": "technicien;auditeur",
        "checksum_sha256": sha256(path),
    }
    base.update(overrides)
    return base


@pytest.fixture
def corpus(tmp_path):
    documents = tmp_path / "documents"
    documents.mkdir()

    def make(name, text):
        asset = documents / name
        asset.write_text(text, encoding="utf-8")
        return asset

    def manifest(rows, name="manifest.csv"):
        path = tmp_path / name
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        return path

    return documents, make, manifest


def test_un_corpus_inchange_ne_produit_aucun_changement(corpus) -> None:
    documents, make, manifest = corpus
    asset = make("a.md", "vibration de la pompe")
    path = manifest([row("DOC-A", asset)])
    index = build_index(path, documents)
    changes = diff_against(index, build_index(path, documents))
    assert changes["unchanged"] == ["DOC-A"]
    assert decide(changes, [])[0] == "unchanged"


def test_un_ajout_est_detecte(corpus) -> None:
    documents, make, manifest = corpus
    a = make("a.md", "pompe")
    avant = build_index(manifest([row("DOC-A", a)]), documents)
    b = make("b.md", "convoyeur")
    apres = build_index(manifest([row("DOC-A", a), row("DOC-B", b)], "m2.csv"), documents)
    changes = diff_against(avant, apres)
    assert changes["added"] == ["DOC-B"]
    assert decide(changes, [])[0] == "rebuild"


def test_un_retrait_est_detecte(corpus) -> None:
    documents, make, manifest = corpus
    a, b = make("a.md", "pompe"), make("b.md", "convoyeur")
    avant = build_index(manifest([row("DOC-A", a), row("DOC-B", b)]), documents)
    apres = build_index(manifest([row("DOC-A", a)], "m2.csv"), documents)
    changes = diff_against(avant, apres)
    assert changes["removed"] == ["DOC-B"]


def test_une_modification_avec_nouvelle_revision_passe(corpus) -> None:
    documents, make, manifest = corpus
    a = make("a.md", "pompe")
    avant = build_index(manifest([row("DOC-A", a)]), documents)
    a.write_text("pompe et vibration", encoding="utf-8")
    apres = build_index(manifest([row("DOC-A", a, revision="2")], "m2.csv"), documents)
    changes = diff_against(avant, apres)
    assert changes["modified"] == ["DOC-A"]
    assert changes["revision_conflicts"] == []
    assert decide(changes, [])[0] == "rebuild"


def test_une_modification_a_revision_constante_est_refusee(corpus) -> None:
    documents, make, manifest = corpus
    a = make("a.md", "pompe")
    avant = build_index(manifest([row("DOC-A", a)]), documents)
    a.write_text("contenu remplacé en douce", encoding="utf-8")
    apres = build_index(manifest([row("DOC-A", a)], "m2.csv"), documents)
    changes = diff_against(avant, apres)
    assert changes["revision_conflicts"] == ["DOC-A"]
    decision, reason = decide(changes, [])
    assert decision == "rejected"
    assert "révision constante" in reason


def test_une_revision_sans_changement_de_contenu_est_signalee(corpus) -> None:
    documents, make, manifest = corpus
    a = make("a.md", "pompe")
    avant = build_index(manifest([row("DOC-A", a)]), documents)
    apres = build_index(manifest([row("DOC-A", a, revision="2")], "m2.csv"), documents)
    changes = diff_against(avant, apres)
    assert changes["revisions_without_content_change"] == ["DOC-A"]


def test_un_document_restreint_ouvert_au_public_est_refuse(corpus) -> None:
    documents, make, manifest = corpus
    a = make("a.md", "secret")
    rows = [row("DOC-A", a, sensitivity="restreint", allowed_roles="public;auditeur")]
    refusals = validate_admission(rows, documents)
    assert any("restreint ouvert au rôle public" in refusal for refusal in refusals)
    assert decide({"revision_conflicts": [], "added": [], "removed": [], "modified": [],
                   "candidate_build_version": None, "previous_build_version": None},
                  refusals)[0] == "rejected"


def test_un_checksum_qui_ne_correspond_pas_est_refuse(corpus) -> None:
    documents, make, manifest = corpus
    a = make("a.md", "pompe")
    refusals = validate_admission([row("DOC-A", a, checksum_sha256="0" * 64)], documents)
    assert any("checksum" in refusal for refusal in refusals)


def test_un_remplacement_dont_le_predecesseur_reste_actif_est_refuse(corpus) -> None:
    documents, make, manifest = corpus
    a, b = make("a.md", "v1"), make("b.md", "v2")
    rows = [row("DOC-A", a), row("DOC-B", b, revision="2", supersedes_document_id="DOC-A")]
    refusals = validate_admission(rows, documents)
    assert any("toujours actif" in refusal for refusal in refusals)


def test_un_role_inconnu_est_refuse(corpus) -> None:
    documents, make, manifest = corpus
    a = make("a.md", "pompe")
    refusals = validate_admission([row("DOC-A", a, allowed_roles="technicien;stagiaire")], documents)
    assert any("rôles inconnus" in refusal for refusal in refusals)


def test_le_corpus_de_reference_passe_l_admission() -> None:
    """Garde-fou : les règles ci-dessus ne doivent pas recaler le corpus livré."""
    from pathlib import Path

    from pipelines.ingest import read_manifest

    root = Path(__file__).resolve().parents[3] / "data_pack/2026-S1/knowledge"
    refusals = validate_admission(read_manifest(root / "manifest.csv"), root / "documents")
    assert refusals == []
