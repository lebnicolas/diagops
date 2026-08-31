"""Index vectoriel — brief 1 M4, étape 4.

**Arbitrage A4 — le modèle d'embeddings.** `configs/retrieval.yaml` livre
`embedding_model: TO_DOCUMENT_BEFORE_RUN` : le choix est libre, la documentation
obligatoire.

Retenu : **`intfloat/multilingual-e5-small`**.

| Critère | Valeur | Pourquoi ça décide |
|---|---|---|
| Langue | 100+ langues, dont le français | le corpus est **entièrement en français** — un modèle anglophone est disqualifié d'office |
| Tâche | entraîné pour le *retrieval* | les modèles `paraphrase-*` optimisent la similarité de paraphrases, pas la correspondance question → passage |
| Dimensions | 384 | index minuscule sur 8 documents |
| Contexte | 512 tokens | le plus long document fait moins de 900 octets — aucun document n'est tronqué |
| Poids | ~470 Mo, 118 M paramètres | tient sur un poste sans GPU ; l'inférence tourne en CPU |
| Licence | MIT | réutilisable sans contrainte |

Écarté : `paraphrase-multilingual-MiniLM-L12-v2` (même taille, mais objectif
d'entraînement inadapté au retrieval) et `multilingual-e5-base` (278 M
paramètres pour 6 Ko de corpus — l'éco-conception que le brief demande de
mesurer interdit de payer ce prix sans gain établi).

**Le piège des préfixes.** La famille E5 est entraînée avec `query: ` devant les
requêtes et `passage: ` devant les documents. Les omettre dégrade nettement le
classement sans produire la moindre erreur : c'est le genre de défaut qui reste
invisible tant qu'on ne le mesure pas. Les deux variantes sont donc évaluées, et
l'écart est rapporté.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np

warnings.filterwarnings("ignore", category=FutureWarning)


MODELE = "intfloat/multilingual-e5-small"
PREFIXE_REQUETE = "query: "
PREFIXE_DOCUMENT = "passage: "


@dataclass
class IndexVectoriel:
    """Index dense en mémoire — 8 documents ne justifient aucune base dédiée.

    Le brief l'autorise explicitement : « une base vectorielle dédiée n'est pas
    obligatoire ; un index local reproductible suffit ». Sur ce volume, une base
    ajouterait une dépendance, un service et une latence réseau pour indexer
    6 Ko de texte.
    """

    identifiants: list[str]
    vecteurs: np.ndarray
    prefixes: bool

    @property
    def taille_octets(self) -> int:
        return int(self.vecteurs.nbytes)

    @property
    def dimensions(self) -> int:
        return int(self.vecteurs.shape[1])


def charger_modele(nom: str = MODELE):
    """Charge le modèle d'embeddings. Import différé : il coûte plusieurs secondes."""
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(nom)


def _normaliser(vecteurs: np.ndarray) -> np.ndarray:
    normes = np.linalg.norm(vecteurs, axis=1, keepdims=True)
    return vecteurs / np.maximum(normes, 1e-12)


def construire_index(
    modele, documents: dict[str, str], prefixes: bool = True
) -> IndexVectoriel:
    """Encode les documents. `prefixes=False` sert à mesurer le coût de l'oubli."""
    identifiants = sorted(documents)
    textes = [
        (PREFIXE_DOCUMENT if prefixes else "") + documents[identifiant]
        for identifiant in identifiants
    ]
    vecteurs = _normaliser(np.asarray(modele.encode(textes, show_progress_bar=False)))
    return IndexVectoriel(identifiants=identifiants, vecteurs=vecteurs, prefixes=prefixes)


def rechercher(
    modele, index: IndexVectoriel, requete: str, top_k: int = 3
) -> list[tuple[str, float]]:
    """Documents les plus proches, par similarité cosinus décroissante.

    Les vecteurs étant normalisés, le produit scalaire **est** la similarité
    cosinus. Le départage se fait sur le `document_id` pour que deux exécutions
    rendent le même ordre à score égal.
    """
    texte = (PREFIXE_REQUETE if index.prefixes else "") + requete
    vecteur = _normaliser(np.asarray(modele.encode([texte], show_progress_bar=False)))[0]
    scores = index.vecteurs @ vecteur
    ordre = sorted(
        range(len(index.identifiants)),
        key=lambda i: (-float(scores[i]), index.identifiants[i]),
    )
    return [(index.identifiants[i], float(scores[i])) for i in ordre[:top_k]]
