"""Point de départ des contrats M2.

Les domaines fermés sont fournis pour éviter la ressaisie. Les apprenants
doivent définir et justifier les schémas Pandera/Pydantic et les règles métier.
"""

SEVERITIES = {"low", "medium", "high", "critical"}
CRITICALITIES = {"low", "medium", "high", "critical"}
EVENT_TYPES = {"incident", "intervention", "observation", "alert"}
INTERVENTION_TYPES = {
    "inspection",
    "corrective",
    "preventive",
    "calibration",
    "replacement",
}
OUTCOMES = {
    "resolved",
    "monitoring",
    "parts_ordered",
    "no_fault_found",
    "follow_up_required",
}


def equipment_schema():
    """Retourner le DataFrameSchema Pandera de ``equipment.csv``."""
    raise NotImplementedError("À compléter et justifier pendant le brief")


def events_schema():
    """Retourner le DataFrameSchema Pandera de ``events.csv``."""
    raise NotImplementedError("À compléter et justifier pendant le brief")


def maintenance_schema():
    """Retourner le DataFrameSchema Pandera de ``maintenance_history.csv``."""
    raise NotImplementedError("À compléter et justifier pendant le brief")
