"""Client du modele IA — transforme un rapport technicien en diagnostic DiagOps.

Choix retenu : modele local servi par LM Studio via son API compatible OpenAI.
Voir la section "Choix du modele" du README pour la justification.

Le modele produit du TEXTE. Ce module a la charge de le ramener au contrat
DiagOps (app/schemas.py) : extraction du JSON, validation Pydantic, erreur
explicite en cas d'echec. Aucune sortie non conforme ne franchit ce module.
"""

import json
import logging
import os
import re

import httpx
from pydantic import ValidationError

from app.schemas import DiagnosisResponse

logger = logging.getLogger(__name__)

# --- Configuration (surchargeable par variables d'environnement) ----------
API_URL = os.getenv("DIAGOPS_API_URL", "http://localhost:1234/v1")
# ministral-3-3b : ~25 s par diagnostic. qwen3.5-9b donne de meilleures
# reponses mais depasse 120 s a cause de son raisonnement — inutilisable
# derriere une interface. Compromis assume, a documenter dans le README.
MODEL = os.getenv("DIAGOPS_MODEL", "mistralai/ministral-3-3b")
TIMEOUT = float(os.getenv("DIAGOPS_TIMEOUT", "120"))
MAX_TOKENS = int(os.getenv("DIAGOPS_MAX_TOKENS", "1200"))

# Regle metier : sous ce seuil de confiance, la revision humaine est imposee
# quel que soit l avis du modele. Un LLM peut se declarer sur de lui sur un
# rapport sommaire — en maintenance industrielle, un faux "pas besoin de
# verifier" est le pire type d erreur.
CONFIDENCE_THRESHOLD = float(os.getenv("DIAGOPS_CONFIDENCE_THRESHOLD", "0.85"))


class ModelError(RuntimeError):
    """Le modele est injoignable, ou sa reponse est inexploitable."""


SYSTEM_PROMPT = """Tu es un assistant de diagnostic de maintenance industrielle.

A partir d'un rapport technicien, tu produis UN SEUL objet JSON, sans texte
autour, sans bloc de code, respectant exactement ce format :

{
  "equipment_id": "identifiant de l'equipement",
  "symptom": "symptome principal observe",
  "severity": "low | medium | high | critical",
  "failure_hypothesis": "hypothese de panne la plus probable",
  "recommended_action": "action de maintenance recommandee",
  "confidence": 0.0,
  "evidence": ["element du rapport ayant motive le diagnostic"],
  "requires_human_review": true
}

Regles :
- severity vaut obligatoirement low, medium, high ou critical.
- confidence est un nombre entre 0 et 1.
- evidence cite des elements reellement presents dans le rapport.
- requires_human_review vaut true si le rapport est ambigu ou incomplet.
- Ecris en francais sans accents, comme les rapports d'entree.
- Si l'equipement n'est pas identifiable, mets "UNKNOWN" dans equipment_id.
"""


def _extraire_json(texte: str) -> dict:
    """Recupere le premier objet JSON present dans la reponse du modele.

    Un LLM ajoute souvent du texte autour, ou encadre sa reponse d'un bloc
    ```json. On tente d'abord le parsing direct, puis on cherche le premier
    objet accolade-a-accolade.
    """
    texte = texte.strip()

    try:
        return json.loads(texte)
    except json.JSONDecodeError:
        pass

    # Bloc de code markdown eventuel
    bloc = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", texte, re.DOTALL)
    if bloc:
        try:
            return json.loads(bloc.group(1))
        except json.JSONDecodeError:
            pass

    # Dernier recours : du premier { au dernier }
    debut, fin = texte.find("{"), texte.rfind("}")
    if debut != -1 and fin > debut:
        try:
            return json.loads(texte[debut : fin + 1])
        except json.JSONDecodeError:
            pass

    raise ModelError(f"Aucun JSON exploitable dans la reponse : {texte[:200]!r}")


def _appeler_modele(note: str) -> str:
    """Envoie le rapport au modele et renvoie le texte brut de sa reponse."""
    charge = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": note},
        ],
        "max_tokens": MAX_TOKENS,
        "temperature": 0.2,  # bas : on veut de la stabilite, pas de la creativite
    }

    try:
        reponse = httpx.post(
            f"{API_URL}/chat/completions", json=charge, timeout=TIMEOUT
        )
        reponse.raise_for_status()
    except httpx.HTTPError as exc:
        raise ModelError(f"Modele injoignable sur {API_URL} : {exc}") from exc

    donnees = reponse.json()
    try:
        message = donnees["choices"][0]["message"]
    except (KeyError, IndexError) as exc:
        raise ModelError(f"Reponse inattendue du modele : {donnees}") from exc

    contenu = (message.get("content") or "").strip()

    # Certains modeles a raisonnement remplissent reasoning_content et laissent
    # content vide quand max_tokens est atteint trop tot.
    if not contenu:
        raise ModelError(
            "Le modele a renvoye un contenu vide "
            "(raisonnement tronque ? augmenter DIAGOPS_MAX_TOKENS)"
        )
    return contenu


def diagnostiquer(
    note: str, equipment_id: str | None = None, report_id: str | None = None
) -> DiagnosisResponse:
    """Produit un diagnostic conforme au contrat DiagOps.

    Args:
        note: texte libre du rapport technicien.
        equipment_id: equipement, s'il est connu de l'appelant.
        report_id: rapport source, s'il est connu.

    Returns:
        Un DiagnosisResponse valide.

    Raises:
        ModelError: modele injoignable, reponse illisible ou non conforme.
    """
    brut = _appeler_modele(note)
    donnees = _extraire_json(brut)

    # L'appelant fait autorite sur l'identite de l'equipement : s'il la
    # connait, on ne laisse pas le modele la reinventer.
    if equipment_id:
        donnees["equipment_id"] = equipment_id

    # Tracabilite : le rapport source devient une piece justificative.
    if report_id:
        evidence = donnees.get("evidence") or []
        reference = f"rapport {report_id}"
        if reference not in evidence:
            donnees["evidence"] = [reference, *evidence]

    try:
        diagnostic = DiagnosisResponse(**donnees)
    except ValidationError as exc:
        logger.warning("Sortie modele non conforme au contrat : %s", donnees)
        raise ModelError(f"Sortie non conforme au contrat DiagOps : {exc}") from exc

    # Garde-fou metier applique APRES validation : le modele n a pas le
    # dernier mot sur la necessite d une revision humaine.
    if diagnostic.confidence < CONFIDENCE_THRESHOLD and not diagnostic.requires_human_review:
        logger.info(
            "Revision humaine imposee : confiance %.2f < seuil %.2f",
            diagnostic.confidence,
            CONFIDENCE_THRESHOLD,
        )
        diagnostic = diagnostic.model_copy(update={"requires_human_review": True})

    return diagnostic
