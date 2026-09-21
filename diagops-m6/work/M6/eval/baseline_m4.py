#!/usr/bin/env python3
"""La tranche M4 à une étape, conservée pour la comparaison.

Le brief exige de comparer l'agent « à une baseline sans agent **et** à la
tranche M4 à une étape ». Cette tranche était le planificateur livré par le
starter ; l'étape 4 l'a remplacée. Le point de comparaison ne peut pas être un
souvenir : il est réimplémenté ici, à l'identique, et rejoué à chaque mesure.

Ce n'est pas une copie décorative — c'est la référence contre laquelle le gain de
l'étape 4 se démontre. Elle ne bouge plus.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.runner import (
    EVENT_TERMS,
    FICHE_TERMS,
    HISTORY_TERMS,
    PROCEDURE_TERMS,
    BoundedAgent,
)


class TrancheM4(BoundedAgent):
    """Un outil choisi sur des mots-clés, appelé une fois, puis conclusion.

    Reproduction fidèle du planificateur distribué avec le starter M6 :
    - aucune vérification avant appel ;
    - aucun enchaînement : `if used: return None` dès la deuxième étape ;
    - aucune vérification de ce que le résultat porte réellement ;
    - `limit` figée à 5, quelle que soit la demande.
    """

    def plan_next(self, question: str, state: dict) -> tuple[str, dict] | None:
        lowered = question.lower()
        used: set[str] = set(state["tools_used"])
        if used:
            return None
        report_id = state.get("report_id")
        equipment_id = state.get("equipment_id")

        if report_id and "diagnose_report" not in used:
            return "diagnose_report", {"report_id": report_id}
        if equipment_id and any(term in lowered for term in HISTORY_TERMS) \
                and "get_maintenance_history" not in used:
            return "get_maintenance_history", {"equipment_id": equipment_id, "limit": 5}
        if equipment_id and any(term in lowered for term in EVENT_TERMS) \
                and "list_events" not in used:
            return "list_events", {"equipment_id": equipment_id, "limit": 5}
        if equipment_id and any(term in lowered for term in FICHE_TERMS) \
                and "get_equipment" not in used:
            return "get_equipment", {"equipment_id": equipment_id}
        if any(term in lowered for term in PROCEDURE_TERMS) and "search_knowledge" not in used:
            return "search_knowledge", {"query": question, "top_k": 3}
        return None

    def _collect_evidence(self, tool, result, run, state) -> None:
        """Collecte d'origine : tout ce qui est rendu devient une preuve.

        Ni vérification d'ancrage, ni prise en compte de la troncature — c'est
        précisément ce que l'étape 4 a ajouté, et ce que la comparaison mesure.
        """
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
