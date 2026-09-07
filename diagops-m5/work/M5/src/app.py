"""API minimale M5 : santé, attribution de version et métriques techniques."""

from __future__ import annotations

import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import BaseModel, Field

from .observability import METRICS
from .retrieval import TOP_K, rank, tokenize, visible_to
from .versioning import load_json, validate_release


DEFAULT_REFERENCE = (
    Path(__file__).resolve().parents[3]
    / "data_pack/2026-S1/reference_runs/m4_for_m5/release_manifest.json"
)
app = FastAPI(title="DiagOps M5 starter", version="1.0.0")


def reference_manifest() -> Path:
    configured = os.environ.get("DIAGOPS_REFERENCE_MANIFEST")
    return Path(configured) if configured else DEFAULT_REFERENCE


def fault_file() -> Path:
    configured = os.environ.get("DIAGOPS_FAULT_FILE")
    return Path(configured) if configured else Path("artifacts/runtime/faults.json")


def active_index_file() -> Path | None:
    """Index réellement servi. Non configuré = pas de vérification (comportement du starter)."""
    configured = os.environ.get("DIAGOPS_ACTIVE_INDEX")
    return Path(configured) if configured else None


def index_integrity() -> tuple[bool, str]:
    """Vérifie l'index actif au lieu de croire un interrupteur d'incident.

    Le starter faisait porter `diagops_index_valid` par `faults.json` : la métrique ne pouvait
    passer à 0 que si quelqu'un écrivait le fichier. Un index réellement corrompu restait vert.
    Ici la lecture porte sur l'artefact servi — un index absent, illisible, vide ou dont les
    postings ont disparu fait tomber la readiness.
    """
    path = active_index_file()
    if path is None:
        return True, "non configuré"
    if not path.is_file():
        return False, f"index actif absent : {path}"
    try:
        index = load_json(path)
    except (OSError, ValueError) as exc:
        return False, f"index actif illisible : {exc}"
    documents = index.get("documents")
    if not isinstance(documents, list) or not documents:
        return False, "index actif sans document"
    if index.get("document_count") != len(documents):
        return False, "document_count incohérent avec le contenu"
    if any(not document.get("terms") for document in documents):
        return False, "index actif sans postings exploitables"
    return True, str(index.get("index_version", "inconnue"))


def active_fault() -> dict:
    path = fault_file()
    return load_json(path) if path.is_file() else {}


def current_release() -> dict:
    release = load_json(reference_manifest())
    validate_release(release)
    return release


def active_index() -> dict | None:
    path = active_index_file()
    if path is None or not path.is_file():
        return None
    try:
        return load_json(path)
    except (OSError, ValueError):
        return None


# -- Plan « service » : toute requête est comptée et chronométrée -----------------

@app.middleware("http")
async def observe_requests(request: Request, call_next):
    started = time.perf_counter()
    try:
        response = await call_next(request)
        status = response.status_code
    except Exception:
        # Une exception non gérée est un échec de service : elle doit apparaître dans les
        # compteurs avant d'être propagée, sinon le taux d'erreur ne voit que les 5xx polis.
        METRICS.increment("diagops_http_requests_total",
                          {"path": _route_of(request), "method": request.method, "status": "500"})
        raise
    elapsed = time.perf_counter() - started
    route = _route_of(request)
    # Le chemin est réduit au motif de route : une URL brute ferait exploser la cardinalité
    # et pourrait transporter une donnée métier dans un label.
    METRICS.increment("diagops_http_requests_total",
                      {"path": route, "method": request.method, "status": str(status)})
    METRICS.observe("diagops_http_request_duration_seconds", elapsed, {"path": route})
    return response


def _route_of(request: Request) -> str:
    path = request.url.path
    return path if path in KNOWN_ROUTES else "other"


KNOWN_ROUTES = {"/health/live", "/health/ready", "/version", "/metrics", "/search"}


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "live"}


@app.get("/health/ready")
def ready() -> dict[str, str]:
    fault = active_fault()
    delay_ms = min(int(fault.get("readiness_delay_ms", 0)), 2000)
    if delay_ms:
        time.sleep(delay_ms / 1000)
    if fault.get("dependency_available") is False or fault.get("index_valid") is False:
        raise HTTPException(status_code=503, detail="Incident de laboratoire actif")
    valid, detail = index_integrity()
    if not valid:
        raise HTTPException(status_code=503, detail=detail)
    try:
        release = current_release()
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"status": "ready", "release_id": str(release["release_id"]), "index": detail}


@app.get("/version")
def version() -> dict:
    try:
        return current_release()
    except (OSError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


class SearchRequest(BaseModel):
    """Contrat d'entrée. Le rôle est explicite : aucune recherche « sans rôle » n'est servie."""

    model_config = {"extra": "forbid"}

    question: str = Field(min_length=1, max_length=500)
    role: str = Field(min_length=1, max_length=32)


@app.post("/search")
def search(payload: SearchRequest) -> dict:
    """Retrieval cité de l'état M4, servi sur l'index actif.

    Pas de génération : il n'y a pas de modèle dans ce périmètre. La réponse respecte le contrat
    `DiagOpsGroundedAnswer` — `answer`, `citations`, `abstained` — et s'abstient quand aucun
    document autorisé ne ressort. C'est l'abstention *du retrieval*, pas celle de la génération :
    la distinction est mesurée dans `measure_release.py` et tenue dans le contrat de versions.
    """
    index = active_index()
    if index is None:
        METRICS.increment("diagops_search_errors_total", {"reason": "no_active_index"})
        raise HTTPException(status_code=503, detail="Aucun index actif")

    documents = index.get("documents", [])
    allowed = visible_to(documents, payload.role)
    METRICS.increment("diagops_retrieval_queries_total", {"role": payload.role})
    # Combien de documents le rôle n'a PAS le droit de voir : le filtre est un fait observable,
    # pas une intention écrite dans le runbook.
    METRICS.increment("diagops_retrieval_filtered_documents_total",
                      {"role": payload.role}, len(documents) - len(allowed))

    started = time.perf_counter()
    retrieved = rank(tokenize(payload.question), allowed, TOP_K)
    METRICS.observe("diagops_retrieval_duration_seconds", time.perf_counter() - started)
    METRICS.observe("diagops_retrieval_results", float(len(retrieved)))

    if not retrieved:
        # « Documents sans résultat » du plan retrieval, et refus du plan réponse : c'est le
        # même événement vu de deux côtés, et il doit être compté des deux.
        METRICS.increment("diagops_retrieval_empty_total", {"role": payload.role})
        METRICS.increment("diagops_refusals_total", {"reason": "no_evidence"})
        return {
            "answer": "Aucun document autorisé ne permet de répondre.",
            "citations": [],
            "abstained": True,
        }

    known = {item["document_id"] for item in documents}
    citations = []
    for item in retrieved:
        resolvable = item["document_id"] in known
        METRICS.increment("diagops_citations_total",
                          {"resolvable": "true" if resolvable else "false"})
        if not resolvable:
            continue
        citations.append({
            "document_id": item["document_id"],
            # L'extrait est une référence, pas un contenu : l'index ne porte pas le texte, et
            # une réponse d'API n'a pas à recopier un document interne.
            "excerpt": f"révision {item['revision']}, {item['token_count']} tokens indexés",
        })

    leaked = [
        item for item in retrieved
        if item.get("sensitivity") == "restreint" and payload.role not in item.get("allowed_roles", [])
    ]
    if leaked:
        # Ne devrait jamais arriver — `visible_to` filtre en amont. Si le compteur bouge, c'est
        # le filtre qui a cassé, et c'est une alerte de sécurité, pas une dégradation de qualité.
        METRICS.increment("diagops_restricted_citations_total", {"role": payload.role}, len(leaked))

    return {
        "answer": f"{len(citations)} document(s) pertinent(s) trouvé(s).",
        "citations": citations,
        "abstained": False,
        "interpretation": f"retrieval lexical, index {index.get('index_version', 'inconnue')}",
    }


METRIC_HELP = {
    "diagops_ready": ("gauge", "Whether the reference release is valid."),
    "diagops_dependency_up": ("gauge", "Whether the generation dependency is available."),
    "diagops_index_valid": ("gauge", "Whether the active index passed integrity checks."),
    "diagops_index_documents": ("gauge", "Documents in the active index."),
    "diagops_http_requests_total": ("counter", "HTTP requests by route, method and status."),
    "diagops_http_request_duration_seconds": ("histogram", "HTTP request latency in seconds."),
    "diagops_retrieval_queries_total": ("counter", "Retrieval queries by role."),
    "diagops_retrieval_empty_total": ("counter", "Queries returning no authorised document."),
    "diagops_retrieval_filtered_documents_total": ("counter", "Documents withheld by role filtering."),
    "diagops_retrieval_results": ("histogram", "Documents returned per query."),
    "diagops_retrieval_duration_seconds": ("histogram", "Retrieval latency in seconds."),
    "diagops_search_errors_total": ("counter", "Search failures by reason."),
    "diagops_refusals_total": ("counter", "Refusals to answer, by reason."),
    "diagops_citations_total": ("counter", "Citations emitted, by resolvability."),
    "diagops_restricted_citations_total": ("counter", "Restricted documents cited to an unauthorised role."),
}


@app.get("/metrics")
def metrics() -> Response:
    try:
        current_release()
        ready_value = 1
    except (OSError, ValueError):
        ready_value = 0
    fault = active_fault()
    dependency_up = int(fault.get("dependency_available", True))
    # L'intégrité observée prime : l'interrupteur d'incident ne peut que la dégrader, jamais
    # la faire remonter à vert. Une panne réelle est visible même sans injection de faute.
    observed_valid, _ = index_integrity()
    index_valid = int(observed_valid and fault.get("index_valid", True))

    index = active_index()
    METRICS.set_gauge("diagops_ready", ready_value)
    METRICS.set_gauge("diagops_dependency_up", dependency_up)
    METRICS.set_gauge("diagops_index_valid", index_valid)
    METRICS.set_gauge("diagops_index_documents", float((index or {}).get("document_count", 0)))

    return Response(content=METRICS.render(METRIC_HELP), media_type="text/plain; version=0.0.4")
