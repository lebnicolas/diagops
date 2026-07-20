"""Tests de l API DiagOps.

Les tests rapides remplacent le modele par un double (mock) : ils sont
deterministes, s executent en millisecondes et ne demandent pas que
LM Studio tourne. Un test d integration reel est disponible mais desactive
par defaut.

Lancement :
    pytest                          # tests rapides uniquement
    pytest -m integration           # test reel, exige LM Studio + le modele
    pytest -v                       # detail
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.model_client import ModelError
from app.schemas import DiagnosisResponse

client = TestClient(app)


DIAGNOSTIC_FICTIF = DiagnosisResponse(
    equipment_id="EQ-PUMP-001",
    symptom="vibration anormale au demarrage",
    severity="high",
    failure_hypothesis="roulement use ou desalignement",
    recommended_action="planifier une inspection prioritaire du palier",
    confidence=0.72,
    evidence=["rapport RPT-0001"],
    requires_human_review=True,
)

NOTE_VALIDE = (
    "Pompe P-204 en zone A. Vibration plus forte que d habitude depuis la "
    "prise de poste. Bruit metallique au demarrage. Temperature carter 71 C."
)


# --- Technique -----------------------------------------------------------
def test_health_repond():
    """GET /health confirme que le service est debout."""
    reponse = client.get("/health")
    assert reponse.status_code == 200
    assert reponse.json()["status"] == "ok"


# --- Cas nominal ---------------------------------------------------------
def test_diagnose_cas_nominal(monkeypatch):
    """Un rapport valide produit un diagnostic conforme au contrat DiagOps.

    Note : on remplace app.main.diagnostiquer, pas app.model_client.
    diagnostiquer — main.py a importe la fonction dans son propre espace de
    noms, c est donc cette reference-la qui est appelee.
    """
    monkeypatch.setattr("app.main.diagnostiquer", lambda *a, **k: DIAGNOSTIC_FICTIF)

    reponse = client.post("/diagnose", json={"technician_note": NOTE_VALIDE})

    assert reponse.status_code == 200
    corps = reponse.json()

    # Tous les champs du contrat sont presents
    attendus = {
        "equipment_id",
        "symptom",
        "severity",
        "failure_hypothesis",
        "recommended_action",
        "confidence",
        "evidence",
        "requires_human_review",
    }
    assert set(corps) == attendus

    assert corps["severity"] in {"low", "medium", "high", "critical"}
    assert 0.0 <= corps["confidence"] <= 1.0
    assert isinstance(corps["evidence"], list)
    assert isinstance(corps["requires_human_review"], bool)


def test_diagnose_transmet_les_identifiants(monkeypatch):
    """equipment_id et report_id fournis par l appelant atteignent le client."""
    recus = {}

    def espion(note, equipment_id=None, report_id=None):
        recus.update(note=note, equipment_id=equipment_id, report_id=report_id)
        return DIAGNOSTIC_FICTIF

    monkeypatch.setattr("app.main.diagnostiquer", espion)

    client.post(
        "/diagnose",
        json={
            "technician_note": NOTE_VALIDE,
            "equipment_id": "EQ-PUMP-001",
            "report_id": "RPT-2026S1-0001",
        },
    )

    assert recus["equipment_id"] == "EQ-PUMP-001"
    assert recus["report_id"] == "RPT-2026S1-0001"


# --- Cas d erreur --------------------------------------------------------
@pytest.mark.parametrize(
    "note, cas",
    [
        ("court", "note trop courte"),
        ("             ", "note faite d espaces"),
        ("", "note vide"),
    ],
)
def test_diagnose_entrees_invalides(note, cas):
    """Une entree non conforme est refusee par Pydantic avec un 422."""
    reponse = client.post("/diagnose", json={"technician_note": note})
    assert reponse.status_code == 422, cas


def test_diagnose_champ_manquant():
    """technician_note est obligatoire."""
    assert client.post("/diagnose", json={}).status_code == 422


def test_diagnose_modele_indisponible(monkeypatch):
    """Si le modele echoue, l API renvoie 502 et non une erreur 500 brute."""

    def echoue(*a, **k):
        raise ModelError("modele injoignable")

    monkeypatch.setattr("app.main.diagnostiquer", echoue)

    reponse = client.post("/diagnose", json={"technician_note": NOTE_VALIDE})

    assert reponse.status_code == 502
    assert "Diagnostic indisponible" in reponse.json()["detail"]


# --- Integration (modele reel) -------------------------------------------
@pytest.mark.integration
def test_diagnose_modele_reel():
    """Test de bout en bout avec le vrai modele.

    Exige LM Studio lance avec le modele charge. Lent (~25 s) et non
    deterministe : on verifie le respect du contrat, pas le contenu.
    """
    reponse = client.post(
        "/diagnose",
        json={"technician_note": NOTE_VALIDE, "equipment_id": "EQ-PUMP-001"},
    )

    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    assert corps["severity"] in {"low", "medium", "high", "critical"}
    assert 0.0 <= corps["confidence"] <= 1.0
    assert corps["symptom"].strip()
