"""Les trois plans doivent être observables séparément, et sans fuite dans les labels.

Le starter exposait trois gauges statiques : un service à 100 % de disponibilité qui cite des
documents inexistants y était vert. Ces tests figent la séparation service / retrieval / réponse
et la règle « aucune donnée métier dans un label ».
"""

import json

import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.observability import METRICS, Metrics


INDEX = {
    "index_version": "lexical-test",
    "document_count": 2,
    "documents": [
        {"document_id": "DOC-PUB", "revision": "1", "token_count": 3, "sensitivity": "public",
         "allowed_roles": ["public", "technicien"], "terms": {"pompe": 1, "vibration": 2}},
        {"document_id": "DOC-RESTREINT", "revision": "1", "token_count": 2, "sensitivity": "restreint",
         "allowed_roles": ["auditeur"], "terms": {"pompe": 1, "acces": 3}},
    ],
}


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.delenv("DIAGOPS_REFERENCE_MANIFEST", raising=False)
    monkeypatch.delenv("DIAGOPS_FAULT_FILE", raising=False)
    index = tmp_path / "index.json"
    index.write_text(json.dumps(INDEX), encoding="utf-8")
    monkeypatch.setenv("DIAGOPS_ACTIVE_INDEX", str(index))
    METRICS.reset()
    return TestClient(app)


def test_le_plan_service_compte_les_requetes_et_leur_latence(client) -> None:
    client.get("/health/live")
    body = client.get("/metrics").text
    assert 'diagops_http_requests_total{method="GET",path="/health/live",status="200"} 1' in body
    assert "diagops_http_request_duration_seconds_count" in body


def test_le_plan_retrieval_compte_les_requetes_vides(client) -> None:
    client.post("/search", json={"question": "terme absent du corpus", "role": "technicien"})
    body = client.get("/metrics").text
    assert 'diagops_retrieval_empty_total{role="technicien"} 1' in body


def test_le_plan_reponse_compte_refus_et_citations(client) -> None:
    client.post("/search", json={"question": "vibration", "role": "technicien"})
    client.post("/search", json={"question": "zzz", "role": "technicien"})
    body = client.get("/metrics").text
    assert 'diagops_refusals_total{reason="no_evidence"} 1' in body
    assert 'diagops_citations_total{resolvable="true"} 1' in body


def test_le_filtrage_par_role_est_compte(client) -> None:
    client.post("/search", json={"question": "acces", "role": "public"})
    body = client.get("/metrics").text
    # Un seul des deux documents est visible au rôle public : l'autre est retenu par le filtre.
    assert 'diagops_retrieval_filtered_documents_total{role="public"} 1' in body


def test_un_document_restreint_n_est_jamais_cite_a_un_role_non_autorise(client) -> None:
    payload = client.post("/search", json={"question": "acces", "role": "public"}).json()
    cited = {citation["document_id"] for citation in payload["citations"]}
    assert "DOC-RESTREINT" not in cited
    assert "diagops_restricted_citations_total" not in client.get("/metrics").text


def test_la_reponse_respecte_le_contrat_de_reponse(client) -> None:
    payload = client.post("/search", json={"question": "vibration", "role": "technicien"}).json()
    assert set(payload) >= {"answer", "citations", "abstained"}
    assert payload["abstained"] is False
    for citation in payload["citations"]:
        assert set(citation) == {"document_id", "excerpt"}


def test_l_abstention_est_explicite_quand_rien_ne_ressort(client) -> None:
    payload = client.post("/search", json={"question": "zzz", "role": "technicien"}).json()
    assert payload["abstained"] is True
    assert payload["citations"] == []


def test_aucune_donnee_metier_ne_finit_dans_un_label(client) -> None:
    """La question posée ne doit apparaître nulle part dans l'exposition."""
    secret = "numero de serie 4815162342 du patient"
    client.post("/search", json={"question": secret, "role": "technicien"})
    body = client.get("/metrics").text
    assert "4815162342" not in body
    assert "patient" not in body


def test_une_route_inconnue_est_agregee_sous_other(client) -> None:
    client.get("/chemin/qui/n/existe/pas")
    assert 'path="other"' in client.get("/metrics").text


def test_les_buckets_de_comptage_ne_sont_pas_sur_une_echelle_de_secondes() -> None:
    registry = Metrics()
    registry.observe("diagops_retrieval_results", 3.0)
    body = registry.render({"diagops_retrieval_results": ("histogram", "documents")})
    assert 'le="3.0"' in body
    assert 'le="0.005"' not in body


def test_les_buckets_sont_cumulatifs() -> None:
    registry = Metrics()
    for value in (0.001, 0.03, 0.4):
        registry.observe("diagops_http_request_duration_seconds", value)
    body = registry.render({"diagops_http_request_duration_seconds": ("histogram", "latence")})
    assert 'le="0.005"} 1' in body
    assert 'le="0.05"} 2' in body
    assert 'le="+Inf"} 3' in body
    assert "_count 3" in body
