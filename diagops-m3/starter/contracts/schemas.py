"""Point de départ des contrats M3.

Les domaines fermés et les identifiants de règles héritées sont fournis pour
éviter la ressaisie. Les schémas, les plages physiques et le rapprochement
temporel restent à définir et à justifier pendant le brief.
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

# Nom de capteur attendu et unité annoncée par ce nom. Le fichier reçu ne
# garantit pas la cohérence entre les deux : c'est un contrôle à écrire.
SENSOR_UNITS = {
    "vibration_mm_s": "mm/s",
    "temperature_c": "°C",
    "pressure_bar": "bar",
    "current_a": "A",
    "rpm": "rpm",
}

MEASUREMENT_KEY = ("equipment_id", "timestamp", "sensor_name")

# Pas d'échantillonnage annoncé dans SCHEMA.md pour la livraison 2026-S1.
# Le pas réellement observé doit être mesuré, pas supposé.
ANNOUNCED_STEP_HOURS = 6
ANNOUNCED_PERIOD = "2026-S1"

# Règles de la préparation de référence M2, à reprendre avec un statut explicite.
# Source : data_pack/2026-S1/reference_runs/m2_for_m3/regles_m2.md
M2_RULE_IDS = (
    "R-EQ-001",
    "R-EQ-002",
    "R-EQ-003",
    "R-EQ-004",
    "R-EQ-005",
    "R-EQ-006",
    "R-EVT-001",
    "R-EVT-002",
    "R-EVT-003",
    "R-EVT-004",
    "R-EVT-005",
    "R-MNT-001",
    "R-MNT-002",
    "R-MNT-003",
    "R-MNT-004",
    "R-MNT-005",
    "R-MNT-006",
    "R-MNT-007",
    "R-MNT-008",
)


def sensor_value_ranges():
    """Retourner les plages physiques plausibles par capteur.

    Le format attendu est ``{sensor_name: (minimum, maximum)}``. Les bornes ne
    sont pas fournies : elles se déduisent de l'observation des séries, du type
    d'équipement mesuré et de ce qui est physiquement possible. Toute borne
    retenue doit être justifiée dans le registre de règles.
    """
    raise NotImplementedError("À compléter et justifier pendant le brief")


def sensor_schema():
    """Retourner le schéma de validation de ``sensor_readings.csv``."""
    raise NotImplementedError("À compléter et justifier pendant le brief")


def align_measures_to_events(measures, events, before_hours, after_hours):
    """Rapprocher les mesures des événements par fenêtre temporelle.

    Contrat attendu :

    - une ligne par couple (mesure, événement) réellement apparié ;
    - les colonnes de clé des deux sources sont conservées, sans les écraser ;
    - la fenêtre retenue est portée par le résultat, pour rester lisible ;
    - le nombre de mesures non appariées et le nombre d'événements sans mesure
      sont calculables à partir du résultat et des entrées.

    Une mesure peut appartenir aux fenêtres de deux événements : le
    rapprochement duplique alors la mesure. C'est acceptable si c'est dit et
    contrôlé, pas si cela passe inaperçu dans un comptage.
    """
    raise NotImplementedError("À compléter et justifier pendant le brief")
