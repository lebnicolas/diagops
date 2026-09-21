"""Agent mono-agent borné : planification courte, un outil à la fois, arrêt.

L'agent ne modifie pas sa politique, n'élargit pas sa liste d'outils et ne
traite jamais le contenu récupéré comme une instruction. Le planificateur
fourni est une base à améliorer : il couvre les cas nominaux du jeu de
scénarios distribué, pas l'ensemble des situations demandées par le brief.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

from tools import PERTINENCE_MINIMUM, ToolError, ToolResult, normaliser, termes_significatifs
from .registry import ArgumentError, AuthorizationError, ToolRegistry, UnknownTool, default_registry


HARD_MAX_STEPS = 8
HARD_MAX_DURATION_MS = 30000

EQUIPMENT_PATTERN = re.compile(r"EQ-[A-Z]+-\d+")
REPORT_PATTERN = re.compile(r"RPT-\d{4}S\d-\d{4}")

# Marqueurs d'instruction rencontrés dans un contenu récupéré. Ils ne sont
# jamais exécutés : ils sont signalés dans la trace et la réponse reste bornée.
INSTRUCTION_MARKERS = (
    "ignore les consignes", "ignore les instructions", "nouvelle consigne",
    "tu peux desormais", "tu peux désormais", "ajoute l outil", "ajoute l'outil",
    "consigne systeme", "consigne système", "reponds sans citer", "réponds sans citer",
)

HISTORY_TERMS = ("historique", "intervention", "recidive", "récidive", "deja", "déjà", "precedent", "précédent")
EVENT_TERMS = ("evenement", "événement", "incident", "alerte", "panne", "arret", "arrêt")
FICHE_TERMS = ("criticite", "criticité", "site", "fiche", "equipement", "équipement", "puissance", "fabricant")
PROCEDURE_TERMS = ("procedure", "procédure", "consigne", "consignation", "seuil", "revision", "révision",
                   "politique", "regle", "règle", "etape", "étape", "autorise", "autorisé")

# --- Périmètre, ancrage et ambiguïté ---------------------------------------
#
# Ces listes sont des heuristiques lexicales, et elles en ont les défauts : une
# question formulée autrement passe à travers. Elles tiennent lieu de contrat de
# périmètre tant qu'aucune classification n'est mesurée — voir
# docs/agent_borne.md §6, « ce qui reste fragile ».

# Un terme d'ici disqualifie la question même si le reste parle du parc : « le
# prix d'une pompe » est une question d'achat, pas de maintenance.
HORS_DOMAINE = (
    "prix", "cout", "coût", "tarif", "achat", "acheter", "devis", "facture",
    "chiffre d'affaires", "budget", "marge", "salaire", "effectif", "recrutement",
    "meteo", "météo", "recette", "traduis", "traduction", "actualite", "actualité",
)

# Vocabulaire du parc et de son exploitation. La question doit en porter au moins
# un terme, ou un identifiant connu, pour être dans le périmètre.
DOMAINE = HISTORY_TERMS + EVENT_TERMS + FICHE_TERMS + PROCEDURE_TERMS + (
    "vibration", "temperature", "température", "pression", "courant", "givre",
    "capteur", "pompe", "convoyeur", "groupe froid", "vapeur", "moteur", "palier",
    "maintenance", "diagnostic", "defaut", "défaut", "triage", "mesure", "rapport",
    "severite", "sévérité", "symptome", "symptôme", "anomalie", "inspection",
)

# Un nom d'usage : « P-416 », « GF-426 ». Cherché seulement après retrait des
# identifiants d'inventaire, sans quoi « RPT-2027S1-0005 » en produirait un.
USAGE_NAME_PATTERN = re.compile(r"\b[A-Z]{1,3}-\d{2,5}\b")

# Deux familles de questions d'ensemble, et elles ne se traitent pas pareil.
#
# Une EXISTENCE se prouve sur un échantillon : deux interventions du même type
# dans les lignes visibles suffisent à établir une récidive. Une propriété
# EXHAUSTIVE ne le peut pas — « combien au total » sur un historique tronqué n'a
# aucune réponse défendable, et « jamais » est une négation universelle.
#
# La distinction est logique, pas cosmétique : ∃ se démontre sur un sous-ensemble,
# ∀ ne s'y démontre pas.
EXISTENCE_TERMS = ("recidive", "récidive", "deja", "déjà", "systematiquement",
                   "systématiquement", "a plusieurs reprises")
EXHAUSTIF_TERMS = ("toutes", "tous les", "combien", "au total", "l'ensemble",
                   "jamais", "exhaustif", "exhaustive", "la totalite", "la totalité")


# Nombre de termes significatifs de la question qu'un extrait cité doit porter
# pour que la réponse soit considérée comme fondée. Un seul terme laisse passer
# un document qui partage un mot de vocabulaire général ; trois refusait des cas
# nominaux courts. Même valeur que la pertinence appliquée aux documents écartés
# par le filtre de rôle — à re-mesurer avec le retrieval corrigé (étape 7).
ANCRAGE_MINIMUM = PERTINENCE_MINIMUM


@dataclass(frozen=True)
class Budget:
    max_steps: int
    max_tool_calls: int
    max_duration_ms: int
    max_repeated_calls: int
    max_result_rows: int


@dataclass(frozen=True)
class Policy:
    policy_id: str
    role: str
    allowlist: frozenset[str]
    budget: Budget
    stop_on_tool_error: bool
    require_evidence: bool
    treat_tool_output_as_data: bool
    allow_dynamic_tools: bool
    trace_record_fields: tuple[str, ...]
    trace_forbidden_fields: tuple[str, ...]
    retention_days: int


@dataclass(frozen=True)
class Step:
    index: int
    tool: str
    argument_keys: tuple[str, ...]
    argument_fingerprint: str
    row_count: int
    source: str
    elapsed_ms: float
    outcome: str
    instruction_like_content: bool = False


@dataclass
class AgentRun:
    question: str
    role: str
    policy_id: str
    steps: list[Step] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)
    evidence: list[dict] = field(default_factory=list)
    answered: bool = False
    refused: bool = False
    stop_reason: str = ""
    elapsed_ms: float = 0.0
    answer: str = ""
    # Motif fin d'un refus, pour la trace et l'audit. La réponse rendue ne le
    # reprend pas : deux refus de causes différentes se formulent pareil.
    refusal_detail: str = ""
    # Champs de trace imposés par la politique. Vides, la trace expose la
    # structure interne de Step — c'était le comportement d'origine, et il
    # divergeait de ce que la politique déclarait.
    trace_fields: tuple[str, ...] = ()
    trace_forbidden_fields: tuple[str, ...] = ()

    def _step_as_trace(self, step: Step) -> dict:
        brut = asdict(step)
        if not self.trace_fields:
            return brut
        # `step` est le nom contractuel du numéro d'étape ; la dataclass l'appelle
        # `index`. Sans cette projection, la politique déclare un champ que la
        # trace ne porte pas, et en porte deux qu'elle ne déclare pas.
        brut["step"] = brut.pop("index")
        projete = {champ: brut[champ] for champ in self.trace_fields if champ in brut}
        interdits = [champ for champ in self.trace_forbidden_fields if champ in projete]
        if interdits:
            raise ValueError(f"Trace refusée : champs interdits présents {interdits}")
        return projete

    def as_trace(self) -> dict:
        return {
            "policy_id": self.policy_id,
            "role": self.role,
            "steps": [self._step_as_trace(step) for step in self.steps],
            "tools_used": self.tools_used,
            "evidence": self.evidence,
            "answered": self.answered,
            "refused": self.refused,
            "stop_reason": self.stop_reason,
            "refusal_detail": self.refusal_detail,
            "elapsed_ms": round(self.elapsed_ms, 2),
        }


def load_policy(path: Path | str = Path(__file__).with_name("policy.yaml")) -> Policy:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    execution = raw["execution"]
    budget = raw["budget"]
    if execution.get("allow_dynamic_tools", False):
        raise ValueError("Politique refusée : l'ajout dynamique d'outils est interdit en M6.")
    if not execution.get("treat_tool_output_as_data", True):
        # Sans ce refus, le drapeau est une déclaration : le mettre à false ne
        # changeait rien au comportement, et l'invariant INV-08 reposait sur un
        # paramètre inerte.
        raise ValueError(
            "Politique refusée : un résultat d'outil est une donnée, "
            "treat_tool_output_as_data ne peut pas valoir false."
        )
    if budget["max_steps"] > HARD_MAX_STEPS:
        raise ValueError(f"Politique refusée : max_steps au-delà de {HARD_MAX_STEPS}.")
    if budget["max_duration_ms"] > HARD_MAX_DURATION_MS:
        raise ValueError(f"Politique refusée : max_duration_ms au-delà de {HARD_MAX_DURATION_MS}.")
    if not raw["allowlist"]:
        raise ValueError("Politique refusée : liste blanche vide.")
    trace = raw["trace"]
    return Policy(
        policy_id=raw["policy_id"],
        role=raw["role"],
        allowlist=frozenset(raw["allowlist"]),
        budget=Budget(
            max_steps=int(budget["max_steps"]),
            max_tool_calls=int(budget["max_tool_calls"]),
            max_duration_ms=int(budget["max_duration_ms"]),
            max_repeated_calls=int(budget["max_repeated_calls"]),
            max_result_rows=int(budget["max_result_rows"]),
        ),
        stop_on_tool_error=bool(execution["stop_on_tool_error"]),
        require_evidence=bool(execution["require_evidence"]),
        treat_tool_output_as_data=bool(execution["treat_tool_output_as_data"]),
        allow_dynamic_tools=False,
        trace_record_fields=tuple(trace["record_fields"]),
        trace_forbidden_fields=tuple(trace["forbidden_fields"]),
        retention_days=int(trace["retention_days"]),
    )


def _fingerprint(arguments: dict) -> str:
    payload = json.dumps(arguments, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:12]


def _looks_like_instruction(result: ToolResult) -> bool:
    joined = " ".join(
        str(value) for row in result.rows for value in row.values()
    ).lower()
    return any(marker in joined for marker in INSTRUCTION_MARKERS)


def _normaliser(texte: str) -> str:
    return normaliser(texte)


def _limite_demandee(question: str, defaut: int = 5, maximum: int = 10) -> int:
    """Le nombre de lignes demandé par la question, plafonné au contrat.

    Relayer « les 50 derniers » ferait rejeter l'appel avant exécution et
    arrêterait l'agent sur une erreur d'argument. Le plafond appartient au
    contrat de l'outil : l'agent s'y conforme et le signale, il ne transmet pas
    une demande qu'il sait irrecevable.
    """
    nombres = [int(valeur) for valeur in re.findall(r"(\d{1,3})", question)]
    demandes = [valeur for valeur in nombres if valeur > 0]
    if not demandes:
        return defaut
    return min(max(demandes), maximum)


def _termes_significatifs(question: str) -> set[str]:
    """Les mots de la question qui portent son sujet, accents mis de côté."""
    return termes_significatifs(question)


def _porte_sur_un_ensemble(question: str) -> str | None:
    """La question vise-t-elle une existence, une exhaustivite, ou ni l'une ni l'autre ?"""
    normalisee = _normaliser(question)
    if any(_normaliser(terme) in normalisee for terme in EXHAUSTIF_TERMS):
        return "exhaustif"
    if any(_normaliser(terme) in normalisee for terme in EXISTENCE_TERMS):
        return "existence"
    return None


def _repetition_visible(rows: tuple[dict, ...]) -> bool:
    """Deux lignes de meme nature dans ce qui est visible : l'existence est etablie."""
    types = [row.get("intervention_type") or row.get("event_type") for row in rows]
    presents = [valeur for valeur in types if valeur]
    return len(presents) != len(set(presents))


def _ancrage(question: str, rows: tuple[dict, ...]) -> int:
    """Combien de termes de la question le meilleur extrait cité porte-t-il ?

    L'agent ne voit que ce que l'outil lui rend — titre et extrait, pas le
    document entier. La vérification porte donc sur la preuve telle qu'elle sera
    citée, ce qui est exactement ce qu'on demande à une réponse fondée.
    """
    termes = _termes_significatifs(question)
    if not termes:
        return 0
    return max(
        (
            len(termes & _termes_significatifs(f"{row.get('title', '')} {row.get('excerpt', '')}"))
            for row in rows
        ),
        default=0,
    )


class BoundedAgent:
    """Agent à étapes bornées, sans mémoire persistante ni effet externe."""

    def __init__(self, registry: ToolRegistry | None = None, policy: Policy | None = None) -> None:
        self.registry = registry or default_registry()
        self.policy = policy or load_policy()
        unknown = sorted(self.policy.allowlist - set(self.registry.names()))
        if unknown:
            raise ValueError(f"Liste blanche incohérente avec le registre : {unknown}")

    # -- planification ----------------------------------------------------
    def plan_next(self, question: str, state: dict) -> tuple[str, dict] | None:
        """Choisit l'outil suivant, ou None pour conclure.

        Trois différences avec la tranche à une étape fournie par le starter :

        - un **plan** est arrêté au premier tour, puis déroulé un outil à la fois,
          ce qui permet d'enchaîner sans jamais dépasser le budget ;
        - les refus qui doivent tomber **avant** tout appel sont décidés ici,
          avant que le premier outil ne soit choisi ;
        - une intention dont les arguments ne sont pas disponibles est abandonnée
          plutôt que devinée.

        Les vérifications vivent dans le planificateur, pas dans `run()` : une
        sous-classe qui remplace `plan_next` garde ainsi le contrôle complet de
        ce qu'elle appelle.
        """
        if not state["tools_used"] and "plan" not in state:
            refus = self._refus_avant_appel(question, state)
            if refus:
                state["refus"] = refus
                return None
            state["plan"] = self._planifier(question, state)

        if state.get("refus"):
            return None

        while state.get("plan"):
            outil = state["plan"].pop(0)
            if outil in state["tools_used"]:
                continue
            arguments = self._arguments(outil, question, state)
            if arguments is None:
                # L'information manque encore — un rapport qui n'a pas livré son
                # équipement, par exemple. On abandonne l'intention ; on n'invente
                # pas l'argument.
                continue
            return outil, arguments
        return None

    def _refus_avant_appel(self, question: str, state: dict) -> str | None:
        """Ce qui se refuse sans rien lire.

        Refuser après lecture, c'est avoir déjà lu : pour une question hors
        périmètre ou porteuse d'une instruction, l'appel lui-même est la faute.
        """
        normalisee = _normaliser(question)

        if any(_normaliser(marqueur) in normalisee for marqueur in INSTRUCTION_MARKERS):
            return "instruction_dans_la_question"

        if any(_normaliser(terme) in normalisee for terme in HORS_DOMAINE):
            return "hors_perimetre"

        connu = bool(state.get("equipment_id") or state.get("report_id"))
        if not connu and not any(_normaliser(terme) in normalisee for terme in DOMAINE):
            return "hors_perimetre"

        if not connu:
            # Un nom d'usage n'est pas un identifiant : le contrat des outils
            # l'écrit, et deviner l'équipement visé est précisément la faute que
            # les retours d'usage signalent.
            reste = REPORT_PATTERN.sub(" ", EQUIPMENT_PATTERN.sub(" ", question))
            if USAGE_NAME_PATTERN.search(reste):
                return "identifiant_ambigu"

        return None

    def _planifier(self, question: str, state: dict) -> list[str]:
        """Les outils que la question appelle, dans l'ordre où ils se lisent.

        Le rapport vient en premier : il porte l'identifiant d'équipement dont
        les lectures suivantes ont besoin. La recherche documentaire vient en
        dernier : la règle applicable dépend de ce qui a été relevé.
        """
        normalisee = _normaliser(question)

        def demande(termes: tuple[str, ...]) -> bool:
            return any(_normaliser(terme) in normalisee for terme in termes)

        plan: list[str] = []
        if state.get("report_id"):
            plan.append("diagnose_report")
        if demande(FICHE_TERMS):
            plan.append("get_equipment")
        if demande(EVENT_TERMS):
            plan.append("list_events")
        if demande(HISTORY_TERMS):
            plan.append("get_maintenance_history")
        if demande(PROCEDURE_TERMS):
            plan.append("search_knowledge")

        if not plan:
            # Question du domaine sans intention structurée reconnue : le corpus
            # est le seul recours, et l'ancrage dira si la réponse tient.
            plan = ["search_knowledge"]
        # Le plan n'est PAS filtre par la liste blanche : c'est la boucle
        # d'execution qui refuse un outil hors liste, avec son motif. Filtrer ici
        # rendrait INV-02 inobservable — un controle qui ne peut plus echouer ne
        # prouve plus rien (meme defaut qu'au §3 de la politique d'execution).
        return list(dict.fromkeys(plan))

    def _arguments(self, outil: str, question: str, state: dict) -> dict | None:
        """Arguments d'un appel, ou None si la question ne les fournit pas."""
        equipement = state.get("equipment_id")
        limite = _limite_demandee(question)

        if outil == "diagnose_report":
            rapport = state.get("report_id")
            return {"report_id": rapport} if rapport else None
        if outil == "get_equipment":
            return {"equipment_id": equipement} if equipement else None
        if outil == "list_events":
            return {"equipment_id": equipement, "limit": limite} if equipement else None
        if outil == "get_maintenance_history":
            return {"equipment_id": equipement, "limit": limite} if equipement else None
        if outil == "search_knowledge":
            return {"query": question, "top_k": 3}
        return None

    # -- exécution --------------------------------------------------------
    def run(self, question: str, *, faults: dict | None = None) -> AgentRun:
        run = AgentRun(
            question=question, role=self.policy.role, policy_id=self.policy.policy_id,
            trace_fields=self.policy.trace_record_fields,
            trace_forbidden_fields=self.policy.trace_forbidden_fields,
        )
        state: dict[str, Any] = {
            "tools_used": [],
            "equipment_id": _first(EQUIPMENT_PATTERN, question),
            "report_id": _first(REPORT_PATTERN, question),
            "calls": {},
        }
        started = time.perf_counter()
        budget = self.policy.budget

        while True:
            elapsed = (time.perf_counter() - started) * 1000
            if elapsed > budget.max_duration_ms:
                run.stop_reason = "budget_duree_depasse"
                break
            if len(run.steps) >= budget.max_steps or len(run.steps) >= budget.max_tool_calls:
                run.stop_reason = "budget_etapes_depasse"
                break

            plan = self.plan_next(question, state)
            if plan is None:
                break
            tool, arguments = plan
            if tool not in self.policy.allowlist:
                run.stop_reason = "outil_hors_liste"
                break

            fingerprint = _fingerprint({"tool": tool, **arguments})
            state["calls"][fingerprint] = state["calls"].get(fingerprint, 0) + 1
            if state["calls"][fingerprint] > budget.max_repeated_calls:
                run.stop_reason = "appel_repete"
                break

            try:
                result, elapsed_ms = self.registry.call(
                    tool, arguments, role=self.policy.role, faults=faults
                )
            except (ToolError, ArgumentError, AuthorizationError, UnknownTool) as exc:
                run.steps.append(Step(
                    index=len(run.steps) + 1, tool=tool,
                    argument_keys=tuple(sorted(arguments)),
                    argument_fingerprint=fingerprint,
                    row_count=0, source="", elapsed_ms=0.0,
                    outcome=type(exc).__name__,
                ))
                state["tools_used"].append(tool)
                run.tools_used.append(tool)
                if self.policy.stop_on_tool_error:
                    run.stop_reason = "erreur_outil"
                    break
                continue

            if len(result.rows) > budget.max_result_rows:
                # La politique peut être plus restrictive que le contrat de
                # l'outil ; sans cette coupe, `max_result_rows` était chargé,
                # stocké, et jamais appliqué.
                result = ToolResult(
                    tool=result.tool,
                    rows=result.rows[:budget.max_result_rows],
                    source=result.source,
                    truncated=True,
                    reason=result.reason,
                    withheld=result.withheld,
                )

            instruction_like = _looks_like_instruction(result)
            run.steps.append(Step(
                index=len(run.steps) + 1, tool=tool,
                argument_keys=tuple(sorted(arguments)),
                argument_fingerprint=fingerprint,
                row_count=len(result.rows), source=result.source,
                elapsed_ms=round(elapsed_ms, 2),
                outcome="vide" if result.empty else "ok",
                instruction_like_content=instruction_like,
            ))
            state["tools_used"].append(tool)
            run.tools_used.append(tool)
            self._collect_evidence(tool, result, run, state)

        run.elapsed_ms = (time.perf_counter() - started) * 1000
        self._conclude(run, state)
        return run

    def _collect_evidence(self, tool: str, result: ToolResult, run: AgentRun, state: dict) -> None:
        if tool == "search_knowledge" and _ancrage(run.question, result.rows) < ANCRAGE_MINIMUM:
            # Un document rendu n'est pas une preuve. Le score du corpus place un
            # document en tête de n'importe quelle question, y compris hors sujet :
            # ce qui décide, c'est ce que l'extrait cité porte réellement de la
            # question. Rien d'ancré, rien de cité.
            #
            # Mais une question composite — « la procédure ET la criticité » — se
            # répond en partie par les sources structurées. Quand elles ont déjà
            # fourni des preuves, le document faible est écarté de la citation ;
            # il ne fait pas tomber la réponse entière.
            if run.evidence:
                return
            state["refus"] = "filtre_de_role" if result.withheld else "ancrage_insuffisant"
            return

        portee = _porte_sur_un_ensemble(run.question)
        if result.truncated and portee:
            # Le résultat est incomplet. Une existence peut malgré tout être
            # établie si la répétition est déjà visible ; une propriété
            # exhaustive, jamais.
            if portee == "exhaustif" or not _repetition_visible(result.rows):
                state["refus"] = "preuve_tronquee"

        for row in result.rows:
            if tool == "search_knowledge":
                run.evidence.append({
                    "type": "document",
                    "reference": row["document_id"],
                    "revision": row["revision"],
                })
            elif tool == "diagnose_report":
                if row.get("equipment_id"):
                    state["equipment_id"] = row["equipment_id"]
                run.evidence.append({"type": "rapport", "reference": row["report_id"]})
            else:
                key = next(
                    (name for name in ("event_id", "maintenance_id", "equipment_id") if name in row),
                    None,
                )
                run.evidence.append({
                    "type": "enregistrement",
                    "reference": row.get(key, tool),
                    "source": result.source,
                })

    def _conclude(self, run: AgentRun, state: dict | None = None) -> None:
        if run.stop_reason:
            run.refused = True
            run.answer = f"Refus : {run.stop_reason}."
            return

        motif = (state or {}).get("refus")
        if motif:
            run.refused = True
            run.refusal_detail = motif
            # Le motif fin vit dans la trace, pas dans la réponse. Dire « un
            # document existe mais votre rôle ne l'autorise pas » révélerait par
            # canal auxiliaire ce que le filtre protège : la formulation rendue
            # est donc la même que lorsque rien n'a été trouvé.
            if run.evidence:
                run.stop_reason = motif
                run.answer = "Refus : les preuves obtenues ne permettent pas de conclure."
            else:
                run.stop_reason = "preuve_insuffisante"
                run.answer = "Refus : aucune preuve admissible n'a été obtenue."
            return

        if self.policy.require_evidence and not run.evidence:
            run.refused = True
            run.stop_reason = "preuve_insuffisante"
            run.answer = "Refus : aucune preuve admissible n'a été obtenue."
            return
        run.answered = True
        run.stop_reason = "reponse_produite"
        references = ", ".join(sorted({item["reference"] for item in run.evidence}))
        run.answer = f"Réponse fondée sur : {references}."


def _first(pattern: re.Pattern[str], text: str) -> str | None:
    found = pattern.search(text)
    return found.group(0) if found else None
