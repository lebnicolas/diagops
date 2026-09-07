"""La readiness doit observer l'index servi, pas croire un interrupteur d'incident.

Dans le starter, `diagops_index_valid` était porté par `faults.json` : la métrique ne passait à 0
que si quelqu'un écrivait ce fichier. Un index réellement corrompu restait vert — le scénario
« index partiellement corrompu » du game day n'aurait été « détecté » que parce qu'on l'avait
annoncé. Ces tests figent la détection réelle.
"""

import json

from fastapi.testclient import TestClient

from src.app import app
from src.retrieval import build_version, postings


SAIN = {
    "index_version": "lexical-test",
    "document_count": 1,
    "build_version": build_version(),
    "documents": [{"document_id": "DOC-1", "terms": postings("pompe pompe"), "allowed_roles": ["technicien"]}],
}


def write_index(path, payload) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def client_with(monkeypatch, tmp_path, payload=None, write=True) -> TestClient:
    monkeypatch.delenv("DIAGOPS_REFERENCE_MANIFEST", raising=False)
    monkeypatch.delenv("DIAGOPS_FAULT_FILE", raising=False)
    index = tmp_path / "index.json"
    if write:
        write_index(index, payload if payload is not None else SAIN)
    monkeypatch.setenv("DIAGOPS_ACTIVE_INDEX", str(index))
    return TestClient(app)


def test_un_index_sain_est_pret(monkeypatch, tmp_path) -> None:
    response = client_with(monkeypatch, tmp_path).get("/health/ready")
    assert response.status_code == 200
    assert response.json()["index"] == "lexical-test"


def test_un_index_absent_bloque_la_readiness(monkeypatch, tmp_path) -> None:
    response = client_with(monkeypatch, tmp_path, write=False).get("/health/ready")
    assert response.status_code == 503
    assert "absent" in response.json()["detail"]


def test_un_index_sans_postings_bloque_la_readiness(monkeypatch, tmp_path) -> None:
    vide = {**SAIN, "documents": [{"document_id": "DOC-1", "terms": {}, "allowed_roles": []}]}
    response = client_with(monkeypatch, tmp_path, vide).get("/health/ready")
    assert response.status_code == 503
    assert "postings" in response.json()["detail"]


def test_un_compte_incoherent_bloque_la_readiness(monkeypatch, tmp_path) -> None:
    faux = {**SAIN, "document_count": 7}
    response = client_with(monkeypatch, tmp_path, faux).get("/health/ready")
    assert response.status_code == 503


def test_la_metrique_tombe_sans_injection_de_faute(monkeypatch, tmp_path) -> None:
    vide = {**SAIN, "documents": [{"document_id": "DOC-1", "terms": {}, "allowed_roles": []}]}
    body = client_with(monkeypatch, tmp_path, vide).get("/metrics").text
    assert "diagops_index_valid 0" in body


def test_sans_index_configure_le_comportement_du_starter_est_conserve(monkeypatch) -> None:
    monkeypatch.delenv("DIAGOPS_ACTIVE_INDEX", raising=False)
    monkeypatch.delenv("DIAGOPS_REFERENCE_MANIFEST", raising=False)
    monkeypatch.delenv("DIAGOPS_FAULT_FILE", raising=False)
    response = TestClient(app).get("/health/ready")
    assert response.status_code == 200


def test_un_index_construit_par_une_autre_strategie_bloque_la_readiness(monkeypatch, tmp_path) -> None:
    """La panne la plus silencieuse trouvée en phase 1 du brief 2.

    Un index dont les postings viennent d'une version antérieure du module de retrieval passe
    tous les autres contrôles — documents présents, comptes cohérents, postings non vides — et
    rend **zéro résultat à chaque requête**. Le service se déclarait `ready`.
    """
    perime = {**SAIN, "build_version": "build-000000000000"}
    response = client_with(monkeypatch, tmp_path, perime).get("/health/ready")
    assert response.status_code == 503
    assert "autre stratégie" in response.json()["detail"]


def test_un_index_sans_build_version_bloque_la_readiness(monkeypatch, tmp_path) -> None:
    """Un index d'un schéma antérieur ne porte pas l'empreinte : il est refusé, pas toléré."""
    sans = {k: v for k, v in SAIN.items() if k != "build_version"}
    assert client_with(monkeypatch, tmp_path, sans).get("/health/ready").status_code == 503
