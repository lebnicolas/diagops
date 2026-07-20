"""API DiagOps — assistance au diagnostic de maintenance industrielle.

Expose POST /diagnose : un rapport technicien en texte libre entre,
un diagnostic structure conforme au contrat DiagOps sort.

Lancement :
    uvicorn app.main:app --reload
Documentation interactive :
    http://localhost:8000/docs
"""

import logging

from fastapi import FastAPI, HTTPException, status

from app.model_client import MODEL, ModelError, diagnostiquer
from app.schemas import DiagnoseRequest, DiagnosisResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s : %(message)s",
)
logger = logging.getLogger("diagops")

app = FastAPI(
    title="DiagOps",
    version="0.1.0",
    description=(
        "Assistance au diagnostic de maintenance industrielle. "
        "Transforme un rapport technicien en diagnostic structure."
    ),
)


@app.get("/health", tags=["technique"], summary="Etat du service")
def health() -> dict:
    """Verifie que l'API repond et indique le modele configure.

    Ne teste pas la disponibilite du modele : cet appel doit rester
    instantane. Utiliser /diagnose pour un test de bout en bout.
    """
    return {"status": "ok", "model": MODEL}


@app.post(
    "/diagnose",
    response_model=DiagnosisResponse,
    tags=["diagnostic"],
    summary="Diagnostiquer un rapport technicien",
    responses={
        422: {"description": "Rapport invalide (vide, trop court, trop long)."},
        502: {"description": "Le modele est injoignable ou sa sortie est non conforme."},
    },
)
def diagnose(requete: DiagnoseRequest) -> DiagnosisResponse:
    """Produit un diagnostic structure a partir d'un rapport technicien.

    La validation de l'entree est assuree par Pydantic (422 automatique).
    La sortie est validee contre le contrat DiagOps avant d'etre renvoyee :
    aucune reponse non conforme ne peut sortir de cette route.
    """
    apercu = requete.technician_note[:80]
    logger.info("Diagnostic demande (equipment_id=%s) : %s...", requete.equipment_id, apercu)

    try:
        diagnostic = diagnostiquer(
            requete.technician_note,
            equipment_id=requete.equipment_id,
            report_id=requete.report_id,
        )
    except ModelError as exc:
        logger.error("Echec du diagnostic : %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Diagnostic indisponible : {exc}",
        ) from exc

    logger.info(
        "Diagnostic produit : severity=%s confidence=%.2f",
        diagnostic.severity,
        diagnostic.confidence,
    )
    return diagnostic
