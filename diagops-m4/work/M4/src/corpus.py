"""Corpus documentaire, admission et index — brief 1 M4, étape 4.

Le manifeste est le **contrat d'admission**, et il s'applique *avant* le
classement : un document qui échoue au contrôle n'est pas récupérable, quel que
soit son score de similarité. Le starter fournit `admissible()` sur le statut et
le rôle ; ce module y ajoute la vérification du checksum, et surtout une
distinction que les questions d'évaluation rendent nécessaire.

**Admissible comme preuve ≠ connu du manifeste.**

Deux questions de calibration attendent un document que le contrat exclut :

- `RAG-CAL-008` (rôle `public`) attend `DOC-DATA-ACCESS-001`, qui est
  `restreint` aux rôles `superviseur` et `auditeur` ;
- `RAG-CAL-010` attend `DOC-LOTO-001`, dont le statut est `superseded`.

Dans les deux cas, la bonne réponse **porte sur l'inadmissibilité elle-même** :
« cette note ne vous est pas accessible », « cette révision est remplacée par la
révision 2 ». Un système qui se contenterait de filtrer serait incapable de le
dire, et un système qui citerait ces documents comme preuve violerait le contrat.

D'où deux niveaux :

| Niveau | Ce qu'il autorise | Contrôles |
|---|---|---|
| **preuve** | citer le contenu du document | statut `active`, rôle autorisé, checksum valide |
| **métadonnée** | dire qu'il existe, son statut, sa révision, ce qui le remplace | présence au manifeste |

Le contenu d'un document non admissible n'est jamais lu ni cité. Ses métadonnées
le sont — c'est ce que `DOC-RAG-OPS-001` appelle « signaler les conflits de
révision au lieu de les masquer ».
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from src.io_contracts import load_manifest


PACK = Path("../../data_pack/2026-S1")
MANIFESTE = PACK / "knowledge" / "manifest.csv"
DOCUMENTS = PACK / "knowledge" / "documents"


@dataclass(frozen=True)
class Document:
    document_id: str
    titre: str
    revision: str
    statut: str
    sensibilite: str
    roles: frozenset[str]
    remplace: str
    texte: str
    checksum_valide: bool

    @property
    def actif(self) -> bool:
        return self.statut == "active"


def charger_corpus() -> dict[str, Document]:
    """Charge le corpus en vérifiant chaque checksum.

    `load_manifest` du starter lève déjà sur un checksum invalide ; le contrôle
    est refait ici pour porter le résultat dans l'objet plutôt que dans une
    exception — un document au checksum faux doit pouvoir être *signalé* comme
    tel, pas seulement faire échouer le chargement.
    """
    lignes = load_manifest(MANIFESTE, DOCUMENTS)
    corpus: dict[str, Document] = {}
    for ligne in lignes:
        chemin = DOCUMENTS / ligne["asset_path"]
        octets = chemin.read_bytes()
        corpus[ligne["document_id"]] = Document(
            document_id=ligne["document_id"],
            titre=ligne["title"],
            revision=ligne["revision"],
            statut=ligne["status"],
            sensibilite=ligne["sensitivity"],
            roles=frozenset(r for r in ligne["allowed_roles"].split(";") if r),
            remplace=ligne["supersedes_document_id"],
            texte=octets.decode("utf-8"),
            checksum_valide=hashlib.sha256(octets).hexdigest() == ligne["checksum_sha256"],
        )
    return corpus


def admissible_comme_preuve(document: Document, role: str) -> tuple[bool, str]:
    """Le document peut-il être cité comme preuve pour ce rôle ?

    Rend aussi le motif du refus : sans lui, le système ne peut pas expliquer
    son abstention, et une abstention non motivée est un critère bloquant.
    """
    if not document.checksum_valide:
        return False, "checksum invalide"
    if not document.actif:
        return False, f"statut {document.statut}"
    if role not in document.roles:
        return False, f"rôle {role} non autorisé ({document.sensibilite})"
    return True, ""


def corpus_admissible(corpus: dict[str, Document], role: str) -> dict[str, Document]:
    """Sous-ensemble citable par ce rôle — appliqué **avant** tout classement."""
    return {
        identifiant: document
        for identifiant, document in corpus.items()
        if admissible_comme_preuve(document, role)[0]
    }


def remplacants(corpus: dict[str, Document]) -> dict[str, str]:
    """`document_id` remplacé → `document_id` qui le remplace.

    Permet de répondre « la révision 1 est remplacée par la révision 2 » sans
    jamais lire le contenu de la révision périmée.
    """
    return {
        document.remplace: identifiant
        for identifiant, document in corpus.items()
        if document.remplace
    }
