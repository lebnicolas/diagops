"""Chargement et interpretation de la politique de qualification.

La politique vit dans `config/quality_rules.yaml`. Ce module la lit, la valide
et repond a une seule question : etant donne le resultat mesure d'une regle,
quel niveau cela vaut-il — `error`, `warning` ou `info` ?

Il ne mesure rien lui-meme. La separation est volontaire : `data_pipeline`
constate, la politique juge. Changer d'avis sur un seuil ne doit jamais obliger
a rouvrir le code qui compte.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import yaml


LEVELS = ("info", "warning", "error")
LEVEL_ORDER = {level: rank for rank, level in enumerate(LEVELS)}

STATUS_ACCEPTED = "ACCEPTED"
STATUS_ACCEPTED_WITH_WARNINGS = "ACCEPTED_WITH_WARNINGS"
STATUS_REJECTED = "REJECTED"


class PolicyError(ValueError):
    """Politique illisible, incomplete ou incoherente."""


@dataclass(frozen=True)
class RuleVerdict:
    """Ce que la politique conclut d'une regle mesuree."""

    rule_id: str
    level: str
    escalated: bool = False
    reason: str = ""


@dataclass(frozen=True)
class Policy:
    """Politique de qualification chargee depuis un fichier YAML."""

    version: str
    checksum: str
    path: Path
    decision_levels: dict[str, str]
    rules: dict[str, dict] = field(default_factory=dict)
    incremental_rules: dict[str, dict] = field(default_factory=dict)
    thresholds: dict = field(default_factory=dict)
    watched_open_categories: dict[str, list[str]] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Seuils
    # ------------------------------------------------------------------

    @property
    def recurrence_share(self) -> float:
        return float(self.thresholds.get("recurrence_share", 0.05))

    @property
    def recurrence_minimum(self) -> int:
        return int(self.thresholds.get("recurrence_minimum", 10))

    @property
    def recurrence_population(self) -> str:
        return str(self.thresholds.get("recurrence_population", "context"))

    @property
    def expected_periods(self) -> tuple[str, ...]:
        return tuple(self.thresholds.get("expected_periods", ("2026-S1",)))

    # ------------------------------------------------------------------
    # Jugement
    # ------------------------------------------------------------------

    def level_for(self, rule_id: str, decision: str, failure_rate: float = 0.0) -> RuleVerdict:
        """Niveau d'une regle du registre M2 au vu de son taux d'echec.

        `decision` est la decision M2 (`quarantaine_rejet`, `signalement`...).
        Elle fournit le niveau par defaut ; une entree dans `rules` la
        remplace. Le taux d'echec peut ensuite faire monter le niveau : c'est
        la difference entre une ligne fausse et une livraison fausse.
        """
        override = self.rules.get(rule_id, {})
        level = override.get("level") or self.decision_levels.get(decision)
        if level is None:
            raise PolicyError(
                f"Aucun niveau pour {rule_id} : decision '{decision}' absente de decision_levels"
            )
        _require_level(level, f"rules.{rule_id}.level")

        ceiling = override.get("max_failure_rate")
        if ceiling is not None and failure_rate > float(ceiling):
            escalated = override.get("escalate_to", "error")
            _require_level(escalated, f"rules.{rule_id}.escalate_to")
            if LEVEL_ORDER[escalated] > LEVEL_ORDER[level]:
                return RuleVerdict(
                    rule_id=rule_id,
                    level=escalated,
                    escalated=True,
                    reason=(
                        f"taux d'echec {failure_rate:.2%} au-dela du plafond "
                        f"{float(ceiling):.2%} — regression globale, pas anomalie de ligne"
                    ),
                )
        return RuleVerdict(rule_id=rule_id, level=level, reason=override.get("note", ""))

    def level_for_incremental(self, rule_id: str) -> str:
        """Niveau d'une regle propre aux livraisons incrementales."""
        entry = self.incremental_rules.get(rule_id)
        if entry is None:
            raise PolicyError(f"Regle incrementale inconnue de la politique : {rule_id}")
        level = entry.get("level")
        _require_level(level, f"incremental_rules.{rule_id}.level")
        return level

    def describe_incremental(self, rule_id: str) -> str:
        return self.incremental_rules.get(rule_id, {}).get("description", "")

    def status_for(self, levels: list[str]) -> str:
        """Statut global du lot a partir des niveaux constates."""
        if "error" in levels:
            return STATUS_REJECTED
        if "warning" in levels:
            return STATUS_ACCEPTED_WITH_WARNINGS
        return STATUS_ACCEPTED


PASSING_STATUSES = (STATUS_ACCEPTED, STATUS_ACCEPTED_WITH_WARNINGS)


def conforms(observed: str, expected: str | None) -> tuple[bool, str]:
    """Le statut obtenu correspond-il a ce qui etait attendu de ce lot ?

    Sans attente declaree, un lot doit passer : c'est le cas d'une livraison
    neuve, et un rejet doit alors faire echouer la chaine.

    Avec une attente declaree, la comparaison est stricte et **symetrique**.
    Un lot dont la decision de rejet est actee ne fait plus echouer la chaine
    tant que rien ne bouge — mais s'il cessait d'etre rejete, la chaine
    echouerait aussi. Un changement de statut oblige a relire la decision, dans
    les deux sens.
    """
    if expected is None:
        if observed in PASSING_STATUSES:
            return True, f"{observed} — aucune decision anterieure, le lot passe"
        return False, f"{observed} — livraison neuve non conforme"

    _require_status(expected)
    if observed == expected:
        return True, f"{observed} — conforme a la decision actee"
    return False, f"{observed} — attendu {expected}, le statut a change depuis la decision actee"


def _require_status(status: object) -> None:
    valid = (STATUS_ACCEPTED, STATUS_ACCEPTED_WITH_WARNINGS, STATUS_REJECTED)
    if status not in valid:
        raise PolicyError(f"expected_status invalide : {status!r} — attendu parmi {valid}")


def _require_level(level: object, where: str) -> None:
    if level not in LEVELS:
        raise PolicyError(f"Niveau invalide en {where} : {level!r} — attendu parmi {LEVELS}")


def load_policy(path: Path) -> Policy:
    """Lit la politique et refuse de continuer si elle est incoherente.

    Une politique fausse est pire qu'une politique absente : elle produit une
    decision qui a l'air fondee. Le chargement est donc strict.
    """
    if not path.is_file():
        raise PolicyError(f"Politique introuvable : {path}")

    raw = path.read_bytes()
    document = yaml.safe_load(raw.decode("utf-8"))
    if not isinstance(document, dict):
        raise PolicyError(f"Politique illisible : {path}")

    version = document.get("policy_version")
    if not version:
        raise PolicyError("policy_version est obligatoire — un resultat sans version n'est pas rejouable")

    decision_levels = document.get("decision_levels") or {}
    if not decision_levels:
        raise PolicyError("decision_levels est obligatoire")
    for decision, level in decision_levels.items():
        _require_level(level, f"decision_levels.{decision}")

    thresholds = document.get("thresholds") or {}
    population = thresholds.get("recurrence_population", "context")
    if population not in ("context", "batch"):
        raise PolicyError(
            f"thresholds.recurrence_population invalide : {population!r} — attendu 'context' ou 'batch'"
        )

    incremental = document.get("incremental_rules") or {}
    for rule_id, entry in incremental.items():
        _require_level((entry or {}).get("level"), f"incremental_rules.{rule_id}.level")

    return Policy(
        version=str(version),
        checksum=hashlib.sha256(raw).hexdigest(),
        path=path,
        decision_levels=decision_levels,
        rules=document.get("rules") or {},
        incremental_rules=incremental,
        thresholds=thresholds,
        watched_open_categories=document.get("watched_open_categories") or {},
    )


def load_batches(path: Path) -> dict:
    """Lit le catalogue des lots."""
    if not path.is_file():
        raise PolicyError(f"Catalogue de lots introuvable : {path}")
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or "baseline" not in document:
        raise PolicyError(f"Catalogue de lots invalide : {path}")
    return document
