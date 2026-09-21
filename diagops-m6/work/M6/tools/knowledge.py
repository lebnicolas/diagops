"""Outil `search_knowledge` : recherche documentaire bornée, en lecture seule."""

from __future__ import annotations

import re
from collections import Counter

from . import PERTINENCE_MINIMUM, ToolResult, knowledge_documents, termes_significatifs


SPEC = {
    "name": "search_knowledge",
    "purpose": "Retrouver les passages de procédure ou de politique qui fondent une réponse.",
    "arguments": [
        {
            "name": "query",
            "type": "string",
            "required": True,
            "min_length": 3,
            "max_length": 200,
            "description": "question ou termes de recherche, en clair",
        },
        {
            "name": "top_k",
            "type": "integer",
            "required": False,
            "minimum": 1,
            "maximum": 3,
            "default": 3,
            "description": "nombre de documents retournés",
        },
    ],
    "result_fields": ["document_id", "title", "revision", "excerpt", "score"],
    "source_of_truth": "data_pack/2026-S1/knowledge/ (documents actifs du manifeste)",
    "authorized_roles": ["technicien", "superviseur", "auditeur", "public"],
    "timeout_ms": 1500,
    "max_results": 3,
    "sensitive_data": "extraits de documents internes ou restreints, filtrés par rôle",
    "errors": ["checksum invalide", "corpus indisponible"],
    "degraded_mode": (
        "résultat vide et motif explicite ; mais le vide est rare — le score lexical "
        "rend presque toujours des documents, y compris hors sujet. Le champ `withheld` "
        "compte les documents écartés par le filtre de rôle, sans les nommer."
    ),
    "side_effects": False,
}

TOKEN = re.compile(r"[\wÀ-ÿ-]+", re.UNICODE)
EXCERPT_WINDOW = 240


def _tokens(text: str) -> list[str]:
    return [item.lower() for item in TOKEN.findall(text)]


def _score(query: str, text: str) -> float:
    """Termes significatifs partages entre la question et le document.

    Candidat `m6-retrieval-r2`. La version de reference comptait TOUS les tokens
    communs, mots vides inclus : « de », « la », « aux », « est » sont presents
    dans les sept documents, rapprochaient n'importe quelle question de n'importe
    quel document, et noyaient le signal des termes metier. Mesure de reference :
    separation de -3.0 entre domaine et hors-domaine, et zero silence sur cinq
    questions hors sujet.

    Le comptage porte desormais sur les termes significatifs — mots vides
    retires, accents normalises, mots de trois lettres ou moins ecartes — via la
    meme couche lexicale que l'ancrage de l'agent. Un terme compte une fois,
    qu'il apparaisse une ou dix fois : ce qui distingue un document, c'est de
    porter le sujet, pas de le repeter.
    """
    return float(len(termes_significatifs(query) & termes_significatifs(text)))


def _excerpt(query: str, text: str) -> str:
    terms = [token for token in _tokens(query) if len(token) > 3]
    lowered = text.lower()
    position = next((lowered.find(term) for term in terms if lowered.find(term) >= 0), -1)
    if position < 0:
        return text[:EXCERPT_WINDOW].strip()
    start = max(0, position - EXCERPT_WINDOW // 3)
    return text[start:start + EXCERPT_WINDOW].strip()


def run(arguments: dict, *, role: str) -> ToolResult:
    query = arguments["query"]
    top_k = int(arguments.get("top_k", SPEC["max_results"]))
    documents = [
        document for document in knowledge_documents()
        if role in document["allowed_roles"]
    ]
    # Documents que le rôle ne peut pas lire mais qui auraient répondu. On compte,
    # on ne nomme pas : l'agent apprend qu'il lui manque quelque chose, la réponse
    # rendue reste identique à celle d'un corpus qui n'aurait rien eu à offrir.
    termes = termes_significatifs(query)
    withheld = sum(
        1 for document in knowledge_documents()
        if role not in document["allowed_roles"]
        and len(termes & termes_significatifs(document["text"])) >= PERTINENCE_MINIMUM
    )
    scored = [
        (document, _score(query, document["text"])) for document in documents
    ]
    ranked = sorted(
        (item for item in scored if item[1] > 0),
        key=lambda item: (item[1], item[0]["document_id"]),
        reverse=True,
    )
    selected = ranked[:top_k]
    rows = tuple(
        {
            "document_id": document["document_id"],
            "title": document["title"],
            "revision": document["revision"],
            "excerpt": _excerpt(query, document["text"]),
            "score": score,
        }
        for document, score in selected
    )
    return ToolResult(
        tool=SPEC["name"],
        rows=rows,
        source="knowledge/manifest.csv",
        truncated=len(ranked) > len(selected),
        reason="" if rows else "aucun document actif admissible pour ce rôle et cette requête",
        withheld=withheld,
    )
