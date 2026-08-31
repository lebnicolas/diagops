"""Agent à une étape — brief 1 M4, étape 6.

L'agent choisit **une seule action** parmi trois, et l'exécute. Ni mémoire
longue, ni boucle, ni outil d'écriture. `bounded_agent.validate_decision` du
starter est le garde-fou, et il n'est pas contourné.

## La question qui a demandé d'être tranchée

Si l'agent choisit `search_knowledge` et que la consultation ne rend aucune
preuve admissible, s'abstenir est-il une **seconde** action ?

**Non, et la distinction porte tout le reste.** `search_knowledge` est une
action de *consultation* : elle englobe son propre résultat, qui peut être « le
corpus admissible ne répond pas ». Un système qui enchaînerait `search_knowledge`
puis `abstain` exécuterait deux actions et ouvrirait la porte à une troisième —
c'est le début d'une boucle, précisément ce que le brief interdit.

Concrètement : l'agent décide **une fois**, avant toute consultation, puis
l'action choisie s'exécute jusqu'à son terme. Le rendu d'une consultation est
soit une réponse citée, soit une abstention motivée — dans les deux cas, une
seule décision a été prise.

## Quand chaque action est choisie

| Action | Condition, évaluée **avant** toute consultation |
|---|---|
| `abstain` | aucune recherche ne peut aider : hors périmètre déclaré (prédiction que le corpus exclut) ou aucun document admissible pour ce rôle |
| `answer_without_tool` | la question porte sur les limites de l'agent lui-même, répondables par son contrat sans consulter le corpus |
| `search_knowledge` | tout le reste — et la consultation peut aboutir à une abstention pour preuve insuffisante |

La décision `abstain` sans consultation n'est pas un raccourci : chercher dans un
corpus dont on sait qu'il exclut explicitement ce type de question consommerait
du calcul pour un résultat connu d'avance, et donnerait l'illusion d'avoir
cherché.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.bounded_agent import ALLOWED_ACTIONS, decide, validate_decision
from src.contracts import AgentDecision
from src.corpus import Document, corpus_admissible
from src.generation import (
    MARQUEURS_NON_PREDICTION,
    TERMES_PREDICTION,
    normaliser,
    repondre,
    termes_porteurs,
)
from src.grounded_answer import GroundedAnswer, abstain


#: Questions auxquelles l'agent répond par son propre contrat, sans consulter le
#: corpus : elles portent sur ce qu'il a le droit de faire, pas sur la
#: maintenance. La réponse est fixe et vérifiable.
TERMES_METACOGNITIFS = frozenset(
    "agent assistant systeme tu vous peux pouvez droit limites bornes".split()
)

#: Réponse contractuelle de l'agent sur ses propres limites.
CONTRAT_AGENT = (
    "Je choisis une seule action par question, parmi : répondre sans consulter "
    "de document, consulter la base documentaire, ou m'abstenir. Je n'ai ni "
    "mémoire d'une question à l'autre, ni boucle, ni moyen d'écrire ou d'agir "
    "sur un système."
)


@dataclass(frozen=True)
class Execution:
    """Une décision, son exécution, et de quoi la vérifier après coup."""

    decision: AgentDecision
    reponse: GroundedAnswer
    regle: str
    motif: str
    signalements: tuple[str, ...]
    documents_consultes: tuple[str, ...]
    actions_executees: int

    def trace(self, question: str, role: str) -> dict:
        """Schéma structuré exposant le choix, sa justification et son résultat."""
        return {
            "question": question,
            "role": role,
            "action": self.decision.action,
            "justification": self.decision.rationale,
            "requete_retrieval": self.decision.retrieval_query,
            "regle": self.regle,
            "motif": self.motif,
            "documents_consultes": list(self.documents_consultes),
            "abstenu": self.reponse.abstained,
            "reponse": self.reponse.answer,
            "interpretation": self.reponse.interpretation,
            "citations": [
                {"document_id": c.document_id, "extrait": c.excerpt}
                for c in self.reponse.citations
            ],
            "signalements": list(self.signalements),
            "actions_executees": self.actions_executees,
            "outils_a_effet_appeles": 0,
        }


def hors_perimetre(question: str, corpus: dict[str, Document]) -> bool:
    """La question demande-t-elle une prédiction que le corpus exclut ?

    Évalué sur la question et sur les exclusions écrites dans les documents —
    pas sur une intuition, et sans consulter le classement.
    """
    if not termes_porteurs(question) & TERMES_PREDICTION:
        return False
    marqueurs = [normaliser(m) for m in MARQUEURS_NON_PREDICTION]
    return any(
        any(marqueur in normaliser(document.texte) for marqueur in marqueurs)
        for document in corpus.values()
    )


def porte_sur_l_agent(question: str) -> bool:
    """La question porte-t-elle sur les limites de l'agent lui-même ?

    Exige au moins deux termes métacognitifs : un seul suffirait à capter « quelles
    actions l'agent M4 est-il autorisé à choisir ? », dont la réponse est dans le
    corpus et doit donc passer par une consultation.
    """
    return len(termes_porteurs(question) & TERMES_METACOGNITIFS) >= 2


def agir(
    question: str,
    role: str,
    corpus: dict[str, Document],
    classement_admissible,
    substitutions: dict[str, str],
) -> Execution:
    """Décide une fois, exécute une fois.

    `classement_admissible` est une fonction paresseuse : elle n'est appelée que
    si l'action retenue est `search_knowledge`. Un agent qui consulterait le
    corpus pour décider s'il doit le consulter aurait déjà agi.
    """
    admissibles = corpus_admissible(corpus, role)

    # --- la décision, prise avant toute consultation ------------------------
    aucune_source = not admissibles
    hors_champ = hors_perimetre(question, corpus)
    repondable_sans_outil = porte_sur_l_agent(question) and not hors_champ

    decision = decide(
        needs_documents=not (aucune_source or hors_champ),
        answerable_without_tool=repondable_sans_outil,
        query=question,
    )
    validate_decision(decision)

    # --- l'exécution, unique ------------------------------------------------
    if decision.action == "answer_without_tool":
        return Execution(
            decision=decision,
            reponse=GroundedAnswer(
                answer=CONTRAT_AGENT,
                citations=(),
                abstained=False,
                interpretation=(
                    "Réponse contractuelle sur les limites de l'agent. Aucun "
                    "document consulté, donc aucune citation — la question ne "
                    "porte pas sur le corpus."
                ),
            ),
            regle="AGT-001",
            motif="question sur les limites de l'agent, répondable sans consultation",
            signalements=(),
            documents_consultes=(),
            actions_executees=1,
        )

    if decision.action == "abstain":
        motif = (
            "aucun document admissible pour ce rôle"
            if aucune_source
            else "la question demande une prédiction que le corpus exclut"
        )
        return Execution(
            decision=decision,
            reponse=abstain(
                "Je m'abstiens sans consulter la base : " + motif + "."
            ),
            regle="AGT-002" if aucune_source else "AGT-003",
            motif=motif,
            signalements=(),
            documents_consultes=(),
            actions_executees=1,
        )

    # `search_knowledge` — la consultation englobe son propre résultat, qui peut
    # être une abstention. Ce n'est pas une seconde action.
    classement = classement_admissible(question, admissibles)
    resultat = repondre(question, role, corpus, classement, substitutions)
    return Execution(
        decision=decision,
        reponse=resultat.reponse,
        regle=resultat.regle,
        motif=resultat.motif,
        signalements=resultat.signalements,
        documents_consultes=tuple(classement[:3]),
        actions_executees=1,
    )


def actions_disponibles() -> frozenset[str]:
    """Les seules actions que l'agent peut exécuter — aucun outil à effet."""
    return ALLOWED_ACTIONS
