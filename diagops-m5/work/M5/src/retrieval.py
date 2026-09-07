"""Retrieval lexical de référence, partagé entre l'API servie et le pipeline de mesure.

La baseline M4 vivait dans `data_pack/.../baseline/retrieval.py`, qui est en lecture seule et
travaille sur le texte intégral. L'index servi ne porte que des postings : même score, même
ordre, mais le document n'est pas reconstituable depuis l'artefact.

Un seul endroit pour cette logique — sinon l'API et le gate mesurent deux choses différentes,
et le gate cesse de dire quoi que ce soit sur ce qui est réellement servi.
"""

from __future__ import annotations

import hashlib
import re
from collections import Counter
from pathlib import Path


TOKEN = re.compile(r"[\wÀ-ÿ-]+", re.UNICODE)
TOP_K = 3
TERM_DIGEST_LENGTH = 16
CHUNKING_STRATEGY = "document-entier-r1"


def build_version() -> str:
    """Empreinte de la STRATEGIE de construction, distincte du contenu indexé.

    `index_version` identifie les documents ; celle-ci identifie la façon de les indexer. Les deux
    sont nécessaires, et pour une raison démontrée le 07/09 : un index dont les postings avaient
    été produits par une version antérieure de ce module donnait **zéro résultat à toutes les
    requêtes**, avec un `index_version` identique — et le service se déclarait `ready`.

    Une panne totale et silencieuse. C'est pourquoi l'API compare désormais cette empreinte à
    celle de l'index servi, au lieu de se contenter de constater que des postings existent.
    """
    empreinte = hashlib.sha256(
        f"{CHUNKING_STRATEGY}:{TOKEN.pattern}:{TERM_DIGEST_LENGTH}:"
        f"{hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}".encode()
    ).hexdigest()
    return f"build-{empreinte[:12]}"


def term_key(token: str) -> str:
    """Empreinte d'un terme. L'index stocke ceci, jamais le mot lui-même.

    Les postings en clair rendaient l'artefact publié équivalent au vocabulaire du corpus — y
    compris celui des documents **restreints**, dont chaque mot devenait lisible par quiconque
    accède à `index.json`. Un test de la CI l'a attrapé le 07/09, sur un secret d'un seul mot.

    Ce que la mesure protège : la lecture. Ce qu'elle ne protège pas : la confirmation — qui
    connaît un mot peut en calculer l'empreinte et vérifier sa présence. C'est un compromis
    assumé, le score lexical exigeant une clé stable. Un index reste un artefact interne : le
    hachage réduit l'exposition, il ne remplace pas le contrôle d'accès au fichier.

    64 bits sur un vocabulaire de quelques milliers de termes : la collision est négligeable.
    """
    return hashlib.sha256(token.encode("utf-8")).hexdigest()[:TERM_DIGEST_LENGTH]


def tokenize(text: str) -> Counter:
    """Termes de la requête, sous la même forme que les postings de l'index."""
    return Counter(term_key(token.lower()) for token in TOKEN.findall(text))


def postings(text: str) -> dict[str, int]:
    """Postings d'un document : empreinte de terme → occurrences, triés pour la reproductibilité."""
    return dict(sorted(tokenize(text).items()))


def lexical_score(query_terms: Counter, document_terms: dict[str, int]) -> float:
    """Score de la baseline M4 : recouvrement borné par les comptes de la requête."""
    return float(
        sum(min(count, document_terms.get(token, 0)) for token, count in query_terms.items())
    )


def visible_to(documents: list[dict], role: str) -> list[dict]:
    """Un rôle ne voit que ce qu'il a le droit de voir — le filtre précède le classement.

    Filtrer après le classement laisserait un document restreint occuper une place du top-k,
    puis disparaître : le rôle public verrait un trou là où un document existe. Filtrer avant
    donne un classement complet sur le périmètre autorisé.
    """
    return [item for item in documents if role in item.get("allowed_roles", [])]


def rank(query_terms: Counter, documents: list[dict], top_k: int = TOP_K) -> list[dict]:
    """Ordre de la baseline M4 : score décroissant, puis document_id décroissant."""
    scored = [
        (lexical_score(query_terms, item.get("terms", {})), item["document_id"], item)
        for item in documents
    ]
    scored.sort(key=lambda entry: (entry[0], entry[1]), reverse=True)
    return [item for score, _, item in scored if score > 0][:top_k]
