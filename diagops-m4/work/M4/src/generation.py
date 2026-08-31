"""Génération citée et abstention — brief 1 M4, étape 5.

**Arbitrage : génération extractive, pas de LLM.**

Rien dans le brief n'impose un modèle génératif, et le contrat de sortie du
starter (`GroundedAnswer`) n'en suppose aucun. Trois raisons de s'en passer :

1. **la fidélité aux extraits devient une propriété, pas une mesure.** Une
   réponse composée de passages copiés du document *est* fidèle par
   construction. Avec un LLM, la fidélité s'évalue après coup, sur des
   reformulations, et le brief la compte parmi les critères ;
2. **la reproductibilité est exacte.** Deux exécutions rendent les mêmes octets,
   sans température ni graine à fixer ;
3. **le coût par réponse est nul**, ce que la matrice de décision doit chiffrer.

Ce que cela coûte, et qui est assumé : les réponses sont brutes — des extraits
juxtaposés, pas de la prose. Sur un assistant réel destiné à des techniciens, un
modèle génératif contraint aux extraits serait le prolongement naturel, et
c'est **le premier écart à combler** si DiagOps va plus loin.

**Arbitrage A5 — la politique d'abstention.**

Elle ne repose **pas** sur un seuil de similarité, et c'est mesuré : sur les 12
questions de calibration, le meilleur score va de 0,811 à 0,909 pour les
questions répondables, et vaut 0,801 et 0,804 pour les deux qui ne le sont pas.
L'écart entre la pire répondable et la meilleure non-répondable est de **0,007**.
Un seuil placé dans cet intervalle séparerait parfaitement les douze — en étant
calé sur **deux** exemples négatifs. C'est du surajustement, et `DOC-RAG-OPS-001`
l'écrit lui-même : « une similarité élevée ne constitue pas une preuve de
vérité ».

L'abstention repose donc sur trois règles nommées, portant sur des faits
vérifiables plutôt que sur un score.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from src.corpus import Document, admissible_comme_preuve
from src.grounded_answer import Citation, GroundedAnswer, abstain


#: Mots vides français — écartés du calcul de recouvrement. Liste courte et
#: explicite plutôt qu'une dépendance : elle doit être lisible et discutable.
MOTS_VIDES = frozenset(
    """
    a au aux avec ce ces dans de des du elle en et eux il ils je la le les leur
    lui ma mais me meme mes moi mon ne nos notre nous on ou par pas pour qu que
    qui sa se ses son sur ta te tes toi ton tu un une vos votre vous c d j l m n
    s t y est sont etre ete a ont avoir faut il-y-a quel quelle quels quelles
    quoi comment pourquoi combien lorsque quand si dont donc or ni car plus
    moins tres peut peuvent doit doivent faire fait
    est-il est-elle sont-ils sont-elles y-a-t-il faut-il peut-on doit-on
    qu-est-ce est-ce
    """.split()
)

#: Un terme de la question est « porteur » s'il n'est pas vide et fait au moins
#: cette longueur. Les sigles courts du domaine (kPa, bar) passent par la
#: recherche exacte, pas par ce filtre.
LONGUEUR_MINIMALE = 3

#: Longueur de la racine utilisée pour apparier deux formes fléchies.
#:
#: Sans elle, « choisir » ne retrouve pas « choisit » et « autorisé » ne retrouve
#: pas « autorise » : l'appariement exact échoue sur la conjugaison, ce qui est
#: un défaut de principe et non une particularité d'une question. Cinq caractères
#: suffisent pour les formes verbales et les accords du corpus.
#:
#: Ce que cela coûte : deux mots partageant leurs cinq premières lettres sans
#: être de la même famille sont appariés à tort. Sur un corpus plus large, une
#: vraie racinisation (Snowball) remplacerait cette approximation.
LONGUEUR_RACINE = 5

#: Part minimale des termes porteurs de la question qui doit se retrouver dans le
#: document pour qu'il soit considéré comme portant une preuve.
#:
#: Mesuré sur les 12 questions de calibration :
#:
#: | | Couverture maximale |
#: |---|---|
#: | 10 questions répondables | 0,500 à 1,000 |
#: | 2 questions sans réponse | 0,143 et 0,200 |
#:
#: Les deux groupes sont séparés par un intervalle de 0,300. Le seuil est placé
#: **au milieu** de cet intervalle, et non juste au-dessus du dernier négatif :
#: un seuil posé au bord se transporte mal sur des questions non vues.
#:
#: **La limite est déclarée** : deux questions négatives ne suffisent pas à caler
#: un seuil. La marge est confortable sur ce jeu, elle ne dit rien de sa
#: stabilité ailleurs.
COUVERTURE_MINIMALE = 0.35

#: Formulations par lesquelles le corpus exclut explicitement la prédiction.
#: Elles viennent des documents eux-mêmes, pas d'une intuition.
MARQUEURS_NON_PREDICTION = (
    "ne prédit pas",
    "ne constitue pas une preuve",
)

#: Termes qui font d'une question une demande de prédiction.
TERMES_PREDICTION = frozenset(
    "prochaine future futur prédire prediction prévoir prevision surviendra".split()
)


def normaliser(texte: str) -> str:
    """Minuscules sans accents — pour que « révision » et « revision » matchent."""
    decompose = unicodedata.normalize("NFD", texte.lower())
    return "".join(c for c in decompose if unicodedata.category(c) != "Mn")


def termes_porteurs(texte: str) -> set[str]:
    """Termes signifiants d'une question, mots vides écartés."""
    mots = re.findall(r"[\w-]+", normaliser(texte))
    return {
        mot
        for mot in mots
        if len(mot) >= LONGUEUR_MINIMALE and mot not in MOTS_VIDES and not mot.isdigit()
    }


def racine(mot: str) -> str:
    """Préfixe servant à apparier deux formes fléchies du même mot."""
    return mot[:LONGUEUR_RACINE]


def mots_de(texte_normalise: str) -> set[str]:
    """Mots du texte, pour un appariement qui respecte les frontières de mot."""
    return set(re.findall(r"[\w-]+", texte_normalise))


def present(terme: str, texte_normalise: str) -> bool:
    """Le terme, ou une de ses formes fléchies, apparaît-il dans le texte ?

    L'appariement par racine porte sur le **début d'un mot**, jamais sur une
    sous-chaîne quelconque. La première version cherchait `racine(terme) in
    texte` : « commander » y devenait « comma », qui se retrouve au milieu de
    « recommandé », et la question sur la marque de lubrifiant — sans réponse
    dans le corpus — recevait une réponse. Une recherche de sous-chaîne n'est
    pas une racinisation.
    """
    if terme in texte_normalise:
        return True
    if len(terme) <= LONGUEUR_RACINE:
        return False
    prefixe = racine(terme)
    return any(mot.startswith(prefixe) for mot in mots_de(texte_normalise))


def couverture(question: str, document: Document) -> float:
    """Part des termes porteurs de la question retrouvés dans le document."""
    termes = termes_porteurs(question)
    if not termes:
        return 0.0
    texte = normaliser(document.texte)
    return sum(1 for terme in termes if present(terme, texte)) / len(termes)


def phrases(document: Document) -> list[str]:
    """Découpe le document en phrases exploitables comme extraits."""
    lignes = [ligne.strip(" -•\t") for ligne in document.texte.splitlines()]
    morceaux: list[str] = []
    for ligne in lignes:
        if not ligne or ligne.startswith("#"):
            continue
        for phrase in re.split(r"(?<=[.:])\s+", ligne):
            phrase = phrase.strip()
            if len(phrase) > 25:
                morceaux.append(phrase)
    return morceaux


def meilleur_extrait(question: str, document: Document) -> str:
    """Phrase du document recouvrant le mieux les termes de la question.

    Extraction et non reformulation : l'extrait rendu est un fragment exact du
    document, ce qui rend la fidélité vérifiable par comparaison de chaînes.
    """
    termes = termes_porteurs(question)
    candidats = phrases(document)
    if not candidats:
        return document.texte.strip()[:200]

    def score(phrase: str) -> tuple[float, int]:
        normalisee = normaliser(phrase)
        recouvrement = sum(1 for terme in termes if present(terme, normalisee))
        return (recouvrement / max(len(termes), 1), -len(phrase))

    return max(candidats, key=score)


@dataclass(frozen=True)
class Reponse:
    """Réponse produite, avec la règle qui l'a décidée."""

    reponse: GroundedAnswer
    regle: str
    motif: str
    signalements: tuple[str, ...] = ()


#: Registre des règles d'abstention et de signalement.
REGLES = {
    "ABS-001": "aucun document admissible pour ce rôle",
    "ABS-002": "aucun document ne couvre assez les termes de la question",
    "ABS-003": "la question demande une prédiction que le corpus exclut",
    "REP-001": "réponse fondée sur un document admissible",
    "SIG-001": "révision remplacée signalée sans être citée",
    "SIG-002": "document restreint mentionné sans divulgation de contenu",
}


def repondre(
    question: str,
    role: str,
    corpus: dict[str, Document],
    classement: list[str],
    substitutions: dict[str, str],
) -> Reponse:
    """Compose une réponse citée, ou s'abstient — avec la règle qui décide.

    `classement` est la liste ordonnée des documents **déjà filtrés par
    l'admission** : cette fonction ne voit jamais un document qu'elle n'a pas le
    droit de citer.
    """
    signalements: list[str] = []

    # Une révision remplacée qui concerne la question est signalée par ses
    # métadonnées — jamais par son contenu. C'est ce que le contrat appelle
    # « signaler les conflits de révision au lieu de les masquer ».
    termes = termes_porteurs(question)
    for remplace, remplacant in substitutions.items():
        document_remplacant = corpus.get(remplacant)
        if document_remplacant is None:
            continue
        if couverture(question, document_remplacant) >= COUVERTURE_MINIMALE:
            signalements.append(
                f"{remplace} est remplacé par {remplacant} "
                f"(révision {document_remplacant.revision}) — SIG-001"
            )

    # Un document restreint que le rôle ne peut pas lire est mentionné comme
    # existant, sans divulgation. Le taire reviendrait à répondre « je ne sais
    # pas » à la place de « vous n'y avez pas accès ».
    for identifiant, document in corpus.items():
        admis, motif = admissible_comme_preuve(document, role)
        if not admis and "rôle" in motif and couverture(question, document) >= COUVERTURE_MINIMALE:
            signalements.append(
                f"{identifiant} existe mais n'est pas accessible au rôle {role} "
                f"({document.sensibilite}) — SIG-002"
            )

    if not classement:
        return Reponse(
            abstain(
                "Aucun document accessible à ce rôle ne peut fonder une réponse."
            ),
            "ABS-001",
            REGLES["ABS-001"],
            tuple(signalements),
        )

    demande_prediction = bool(termes & TERMES_PREDICTION)
    couvertures = {
        identifiant: couverture(question, corpus[identifiant])
        for identifiant in classement
    }
    meilleur = max(couvertures, key=lambda i: couvertures[i])

    if demande_prediction:
        exclusion = [
            identifiant
            for identifiant in classement
            if any(m in normaliser(corpus[identifiant].texte) for m in map(normaliser, MARQUEURS_NON_PREDICTION))
        ]
        if exclusion:
            document = corpus[exclusion[0]]
            return Reponse(
                abstain(
                    "Le corpus exclut explicitement ce type de prédiction : "
                    + meilleur_extrait("ne prédit pas une panne future", document)
                ),
                "ABS-003",
                REGLES["ABS-003"],
                tuple(signalements),
            )

    if couvertures[meilleur] < COUVERTURE_MINIMALE:
        return Reponse(
            abstain(
                "Aucun document admissible ne traite cette question "
                f"(couverture maximale {couvertures[meilleur]:.0%}, "
                f"minimum requis {COUVERTURE_MINIMALE:.0%})."
            ),
            "ABS-002",
            REGLES["ABS-002"],
            tuple(signalements),
        )

    retenus = [i for i in classement if couvertures[i] >= COUVERTURE_MINIMALE][:2]
    citations = tuple(
        Citation(document_id=i, excerpt=meilleur_extrait(question, corpus[i]))
        for i in retenus
    )
    return Reponse(
        GroundedAnswer(
            answer=" ".join(c.excerpt for c in citations),
            citations=citations,
            abstained=False,
            interpretation=(
                "Réponse composée d'extraits littéraux des documents cités. "
                "Aucune reformulation : ce qui n'est pas dans les extraits n'est "
                "pas affirmé."
            ),
        ),
        "REP-001",
        REGLES["REP-001"],
        tuple(signalements),
    )
