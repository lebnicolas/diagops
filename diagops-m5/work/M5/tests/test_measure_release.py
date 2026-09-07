"""Le gate doit mesurer le candidat, pas relire des métriques figées.

Le starter livrait trois contrôles sur quatre branchés sur `metrics_calibration.json` : un index
vidé de ses postings passait le gate. Ces tests figent le comportement corrigé.
"""

from pipelines.evaluate_release import evaluate
from pipelines.measure_release import measure, rank, visible_to
from src.retrieval import postings, tokenize


GATES = {
    "minimum_document_count": 2,
    "minimum_expected_document_hit_at_3": 0.8,
    "minimum_citation_resolvable_rate": 1.0,
    "minimum_correct_abstention_rate": 1.0,
}


def index_of(documents: list[dict], version: str = "lexical-test") -> dict:
    return {
        "document_count": len(documents),
        "index_version": version,
        "build_version": "build-test",
        "documents": documents,
    }


DOCUMENTS = [
    {
        "document_id": "DOC-POMPE", "revision": "1", "sensitivity": "interne",
        "allowed_roles": ["technicien"], "token_count": 3,
        "terms": postings("vibration vibration pompe"),
    },
    {
        "document_id": "DOC-RESTREINT", "revision": "1", "sensitivity": "restreint",
        "allowed_roles": ["auditeur"], "token_count": 2,
        "terms": postings("acces pompe"),
    },
]

QUESTIONS = [
    {
        "eval_id": "Q1", "question": "vibration de la pompe", "role": "technicien",
        "expected_document_ids": ["DOC-POMPE"], "answerable": True, "split": "calibration",
    },
    {
        "eval_id": "Q2", "question": "aucune trace ici", "role": "technicien",
        "expected_document_ids": [], "answerable": False, "split": "calibration",
    },
]


def test_le_role_filtre_avant_le_classement() -> None:
    query = tokenize("pompe")
    visible = visible_to(DOCUMENTS, "technicien")
    assert [item["document_id"] for item in rank(query, visible)] == ["DOC-POMPE"]


def test_la_mesure_reflete_un_index_sain() -> None:
    metrics = measure(index_of(DOCUMENTS), QUESTIONS)
    assert metrics["expected_document_hit_at_3"] == 1.0
    assert metrics["citation_resolvable_rate"] == 1.0
    assert metrics["restricted_citation_count"] == 0
    assert metrics["metrics_provenance"]["expected_document_hit_at_3"] == "measured"


def test_un_index_vide_de_ses_postings_fait_chuter_la_mesure() -> None:
    degraded = [{**item, "terms": {}} for item in DOCUMENTS]
    metrics = measure(index_of(degraded), QUESTIONS)
    assert metrics["expected_document_hit_at_3"] == 0.0


def test_le_gate_bloque_l_index_degrade() -> None:
    degraded = [{**item, "terms": {}} for item in DOCUMENTS]
    index = index_of(degraded)
    metrics = measure(index, QUESTIONS)
    metrics["correct_abstention_rate"] = 1.0
    report = evaluate(index, metrics, GATES)
    assert report["status"] == "failed"
    assert report["checks"]["expected_document_hit_at_3"] is False


def test_le_gate_refuse_une_mesure_faite_sur_un_autre_index() -> None:
    index = index_of(DOCUMENTS)
    metrics = measure(index, QUESTIONS)
    metrics["correct_abstention_rate"] = 1.0
    report = evaluate(index_of(DOCUMENTS, version="lexical-autre"), metrics, GATES)
    assert report["status"] == "failed"
    assert report["checks"]["metrics_match_index"] is False


def test_la_provenance_distingue_mesure_et_heritage() -> None:
    index = index_of(DOCUMENTS)
    metrics = measure(index, QUESTIONS)
    metrics["correct_abstention_rate"] = 1.0
    metrics["metrics_provenance"]["correct_abstention_rate"] = "inherited:reference.json"
    report = evaluate(index, metrics, GATES)
    assert report["checks_provenance"]["expected_document_hit_at_3"] == "measured"
    assert report["checks_provenance"]["correct_abstention_rate"].startswith("inherited:")
