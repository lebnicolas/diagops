"""Contrats de l'API et instrumentation du service de scoring."""

import json
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.observability import METRICS
from src.scoring import fenetres_depuis_csv


RACINE = Path(__file__).resolve().parents[4]
CALIBRATION = RACINE / "data_pack/2026-S1/model_eval/sensor_calibration.csv"


def fenetre() -> list[dict]:
    mesures = next(iter(fenetres_depuis_csv(CALIBRATION).values()))
    return [
        {k: str(mesure[k]) for k in ("timestamp", "value", "sensor_name", "unit")}
        for mesure in mesures
    ]


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("DIAGOPS_FAULT_FILE", str(tmp_path / "absent.json"))
    METRICS.reset()
    return TestClient(app)


def test_la_vivacite_ne_depend_pas_de_l_artefact(client) -> None:
    """`live` doit répondre même si le modèle est cassé — sinon l'orchestrateur redémarre en boucle."""
    assert client.get("/health/live").json() == {"status": "live"}


def test_l_aptitude_expose_l_identite_du_modele(client) -> None:
    corps = client.get("/health/ready").json()
    assert corps["status"] == "ready"
    assert corps["checksum"] == "164d05b129ce5e41"
    assert corps["sklearn_conforme"] is True


def test_une_faute_injectee_coupe_l_aptitude(client, monkeypatch, tmp_path) -> None:
    faute = tmp_path / "faults.json"
    faute.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("DIAGOPS_FAULT_FILE", str(faute))
    assert client.get("/health/ready").status_code == 503
    # La vivacité, elle, ne bouge pas : le processus est toujours là.
    assert client.get("/health/live").status_code == 200


def test_la_version_porte_tout_ce_qui_identifie_la_prediction(client) -> None:
    corps = client.get("/version").json()
    for champ in ("date_de_gel", "commit_du_gel", "algorithme", "seuil_de_decision",
                  "graine", "checksum_sha256", "sklearn_du_gel", "performance_de_reference"):
        assert champ in corps, champ


def test_une_prediction_est_attribuable_a_un_artefact(client) -> None:
    corps = client.post("/predict", json={"mesures": fenetre()}).json()
    assert corps["modele_checksum"] == "164d05b129ce5e41"
    assert corps["provenance_predite"] in {"réelle", "fabriquée"}
    assert 0.0 <= corps["probabilite_fabriquee"] <= 1.0
    assert corps["mesures_recues"] == 30


def test_une_fenetre_trop_courte_est_refusee_avant_le_modele(client) -> None:
    assert client.post("/predict", json={"mesures": fenetre()[:2]}).status_code == 422


def test_un_champ_inconnu_est_refuse(client) -> None:
    assert client.post("/predict", json={"mesures": fenetre(), "seuil": 0.9}).status_code == 422


def test_les_predictions_sont_comptees_par_classe(client) -> None:
    client.post("/predict", json={"mesures": fenetre()})
    corps = client.get("/metrics").text
    assert "diagops_predictions_total{" in corps
    assert "diagops_model_probability_bucket" in corps
    assert "diagops_model_loaded 1" in corps
    assert "diagops_model_sklearn_conforme 1" in corps


def test_une_fenetre_hors_specification_est_signalee(client) -> None:
    """29 mesures au lieu de 30 : la prédiction sort, mais le décalage est compté."""
    client.post("/predict", json={"mesures": fenetre()[:29]})
    assert "diagops_windows_off_spec_total 1" in client.get("/metrics").text


def test_aucune_mesure_ne_finit_dans_un_label(client) -> None:
    """Les valeurs capteur sont des données métier : elles n'ont rien à faire dans une métrique."""
    mesures = fenetre()
    mesures[0]["value"] = "424242.42"
    client.post("/predict", json={"mesures": mesures})
    assert "424242" not in client.get("/metrics").text
