"""Service de scoring du détecteur de provenance DiagOps — brief online M5.

Déploie l'artefact gelé en M4 derrière une API instrumentée. Autonome du service RAG : son propre
artefact, ses propres dépendances, sa propre chaîne de livraison.

Le modèle est chargé **une fois au démarrage**, pas à chaque requête. Conséquence assumée : un
artefact absent ou non conforme empêche le service de devenir `ready`, au lieu de produire des
500 à la première prédiction. Échouer au démarrage est le bon moment pour échouer.
"""

from __future__ import annotations

import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field

from .observability import METRICS
from .scoring import Detecteur, charger


app = FastAPI(title="DiagOps — détecteur de provenance", version="1.0.0")

_detecteur: Detecteur | None = None
_erreur_de_chargement: str | None = None


def detecteur() -> Detecteur:
    """Chargement paresseux mais unique. L'échec est mémorisé, pas retenté en boucle."""
    global _detecteur, _erreur_de_chargement
    if _detecteur is None and _erreur_de_chargement is None:
        try:
            _detecteur = charger()
        except (OSError, ValueError, KeyError) as exc:
            _erreur_de_chargement = str(exc)
    if _detecteur is None:
        raise HTTPException(status_code=503, detail=_erreur_de_chargement or "modèle non chargé")
    return _detecteur


def fault_file() -> Path:
    return Path(os.environ.get("DIAGOPS_FAULT_FILE", "artifacts/faults.json"))


KNOWN_ROUTES = {"/health/live", "/health/ready", "/version", "/metrics", "/predict"}


@app.middleware("http")
async def observe_requests(request: Request, call_next):
    started = time.perf_counter()
    route = request.url.path if request.url.path in KNOWN_ROUTES else "other"
    try:
        response = await call_next(request)
        status = response.status_code
    except Exception:
        METRICS.increment("diagops_http_requests_total",
                          {"path": route, "method": request.method, "status": "500"})
        raise
    METRICS.increment("diagops_http_requests_total",
                      {"path": route, "method": request.method, "status": str(status)})
    METRICS.observe("diagops_http_request_duration_seconds", time.perf_counter() - started,
                    {"path": route})
    return response


class Mesure(BaseModel):
    """Une mesure capteur. Les champs sont ceux du contrat capteur M3, inchangés."""

    model_config = {"extra": "ignore"}

    timestamp: str
    value: str | float
    sensor_name: str
    unit: str


class RequetePrediction(BaseModel):
    model_config = {"extra": "forbid"}

    # Une fenêtre M4 fait 30 mesures. La borne basse à 5 laisse passer une fenêtre courte en
    # rendant un résultat que l'appelant doit interpréter avec prudence — la borne haute évite
    # qu'une requête unique n'occupe le service.
    mesures: list[Mesure] = Field(min_length=5, max_length=200)


@app.get("/health/live")
def live() -> dict[str, str]:
    """Vivacité : le processus répond. Ne dépend d'aucune dépendance, artefact compris."""
    return {"status": "live"}


@app.get("/health/ready")
def ready() -> dict:
    """Aptitude à servir : le modèle est chargé, identifié et conforme."""
    fault = fault_file()
    if fault.is_file():
        raise HTTPException(status_code=503, detail="Incident de laboratoire actif")
    modele = detecteur()
    return {
        "status": "ready",
        "modele": "detecteur-provenance-m4",
        "checksum": modele.checksum[:16],
        "sklearn_conforme": modele.sklearn_conforme,
    }


@app.get("/version")
def version() -> dict:
    return detecteur().version()


@app.post("/predict")
def predict(requete: RequetePrediction) -> dict:
    modele = detecteur()
    started = time.perf_counter()
    try:
        resultat = modele.predire_fenetre([m.model_dump() for m in requete.mesures])
    except (ValueError, KeyError) as exc:
        METRICS.increment("diagops_prediction_errors_total", {"reason": "features"})
        raise HTTPException(status_code=422, detail=f"Fenêtre inexploitable : {exc}") from exc

    METRICS.observe("diagops_prediction_duration_seconds", time.perf_counter() - started)
    METRICS.observe("diagops_model_probability", resultat["probabilite_fabriquee"])
    METRICS.increment("diagops_predictions_total", {"classe": resultat["provenance_predite"]})
    # Fenêtre plus courte que les 30 mesures du gel : la prédiction est rendue, mais le fait est
    # compté. Une dérive de format en amont se voit ici avant de se voir dans les résultats.
    if resultat["mesures_recues"] != 30:
        METRICS.increment("diagops_windows_off_spec_total")

    return resultat | {"modele_checksum": modele.checksum[:16]}


METRIC_HELP = {
    "diagops_model_loaded": ("gauge", "Whether the frozen model is loaded and verified."),
    "diagops_model_sklearn_conforme": ("gauge", "Whether the running sklearn matches the freeze."),
    "diagops_http_requests_total": ("counter", "HTTP requests by route, method and status."),
    "diagops_http_request_duration_seconds": ("histogram", "HTTP request latency in seconds."),
    "diagops_predictions_total": ("counter", "Predictions by predicted class."),
    "diagops_prediction_duration_seconds": ("histogram", "Model inference latency in seconds."),
    "diagops_model_probability": ("histogram", "Predicted probability of the positive class."),
    "diagops_prediction_errors_total": ("counter", "Predictions refused, by reason."),
    "diagops_windows_off_spec_total": ("counter", "Windows received with a size other than 30."),
}


@app.get("/metrics")
def metrics() -> Response:
    charge, conforme = 0, 0
    try:
        modele = detecteur()
        charge = 1
        conforme = int(modele.sklearn_conforme)
    except HTTPException:
        pass
    METRICS.set_gauge("diagops_model_loaded", charge)
    METRICS.set_gauge("diagops_model_sklearn_conforme", conforme)
    return Response(content=METRICS.render(METRIC_HELP), media_type="text/plain; version=0.0.4")
