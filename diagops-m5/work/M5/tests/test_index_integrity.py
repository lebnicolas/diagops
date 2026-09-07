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


def test_le_plan_qualite_se_degrade_pendant_que_le_service_reste_vert(monkeypatch, tmp_path) -> None:
    """Le scénario que nos propres compteurs ne pouvaient pas produire.

    Ajouté au starter par le formateur le 07/09. Trois des six scénarios de game day laissent le
    service répondre : sans ces jauges, l'incident n'aurait pu être *signalé par l'animateur*, ce
    que le brief 2 refuse — « l'incident est détecté par le système ».

    Ces trois valeurs sont des **leviers d'injection**, pas des mesures du trafic. Nos compteurs
    (`refusals_total`, `citations_total`) mesurent le réel ; celles-ci permettent de dégrader le
    plan réponse à volonté.
    """
    faute = tmp_path / "faults.json"
    faute.write_text(json.dumps({
        "dependency_available": True, "index_valid": True, "readiness_delay_ms": 0,
        "citation_resolvable_rate": 0.5, "correct_abstention_rate": 0.6,
        "expected_document_hit_at_3": 0.7,
    }), encoding="utf-8")
    monkeypatch.setenv("DIAGOPS_FAULT_FILE", str(faute))
    client = client_with(monkeypatch, tmp_path)
    monkeypatch.setenv("DIAGOPS_FAULT_FILE", str(faute))

    assert client.get("/health/ready").status_code == 200
    corps = client.get("/metrics").text
    assert "diagops_ready 1" in corps
    assert "diagops_index_valid 1" in corps
    assert "diagops_citation_resolvable_rate 0.5" in corps
    assert "diagops_correct_abstention_rate 0.6" in corps
    assert "diagops_expected_document_hit_at_3 0.7" in corps


def test_une_release_incompatible_n_est_pas_un_index_incoherent(monkeypatch, tmp_path) -> None:
    """Deux causes voisines, deux remédiations : la signature les distingue.

    `diagops_ready = 0` avec `diagops_index_valid = 1` désigne la configuration de release.
    L'inverse désignerait l'index. Sans cette distinction, le diagnostic part dans la mauvaise
    direction — et sous incident, une minute perdue à restaurer le mauvais artefact compte.
    """
    faute = tmp_path / "faults.json"
    faute.write_text(json.dumps({
        "dependency_available": True, "index_valid": True,
        "readiness_delay_ms": 0, "release_valid": False,
    }), encoding="utf-8")
    monkeypatch.setenv("DIAGOPS_FAULT_FILE", str(faute))
    client = client_with(monkeypatch, tmp_path)
    monkeypatch.setenv("DIAGOPS_FAULT_FILE", str(faute))

    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 503
    corps = client.get("/metrics").text
    assert "diagops_ready 0" in corps
    assert "diagops_dependency_up 1" in corps
    assert "diagops_index_valid 1" in corps
