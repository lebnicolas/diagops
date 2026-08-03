"""Registre des regles de qualite M2.

Ecrit AVANT toute mesure sur les donnees, a partir de `data_pack/SCHEMA.md`
et des axes du brief. Chaque regle porte un identifiant stable, une
justification et la decision prevue en cas d'echec.

Convention d'identifiant : <SOURCE>-<FAMILLE>-<NNN>

    SOURCE   EQP = equipment, EVT = events, MNT = maintenance_history
    FAMILLE  SCH = structure et types      KEY = identifiants
             REF = references entre tables CAT = categories
             TMP = coherence temporelle    VAL = valeurs impossibles
             NUL = valeurs manquantes      PII = donnees personnelles

Severites : bloquante, majeure, mineure.

Decisions en cas d'echec :

    arret_audit               la source n'est pas exploitable, on ne poursuit pas
    correction_certaine       correction reproductible et non ambigue, tracee
    quarantaine_rejet         la ligne est ecartee du jeu transmis a M3
    quarantaine_examen_metier la ligne est isolee, un humain doit trancher
    signalement               constat chiffre, aucune ligne ecartee
"""

from __future__ import annotations

import pandas as pd


REGISTER_COLUMNS = [
    "rule_id",
    "source",
    "column",
    "description",
    "justification",
    "severity",
    "decision_if_failed",
]

# Valeurs de reference issues de data_pack/SCHEMA.md
CRITICALITY_VALUES = ("low", "medium", "high", "critical")
SEVERITY_VALUES = ("low", "medium", "high", "critical")
EVENT_TYPE_VALUES = ("incident", "intervention", "observation", "alerte")
EXPECTED_PERIOD = "2026-S1"

# Part a partir de laquelle une valeur inconnue cesse d'etre une anomalie pour
# devenir un ecart de nomenclature — voir REVISIONS et docs/regles_qualite_m2.md
RECURRENCE_THRESHOLD = 0.05
RECURRENCE_MINIMUM = 10

# Bornes ajoutees, absentes du schema — voir docs/regles_qualite_m2.md
MIN_COMMISSIONING_DATE = "1950-01-01"
MAX_RATED_POWER_KW = 10_000
MAX_DOWNTIME_MINUTES = 43_200  # 30 jours
MAX_LABOR_HOURS = 2_000

EQUIPMENT_REQUIRED_COLUMNS = (
    "equipment_id",
    "equipment_type",
    "site_id",
    "commissioning_date",
    "criticality",
    "manufacturer",
    "rated_power_kw",
)

EVENTS_REQUIRED_COLUMNS = (
    "event_id",
    "equipment_id",
    "start_at",
    "end_at",
    "event_type",
    "severity",
    "period",
)

MAINTENANCE_REQUIRED_COLUMNS = (
    "maintenance_id",
    "event_id",
    "equipment_id",
    "opened_at",
    "closed_at",
    "intervention_type",
    "outcome",
    "downtime_minutes",
    "labor_hours",
    "parts_cost_eur",
    "parts_replaced_count",
    "work_order_note",
    "period",
)


RULES: list[dict[str, str]] = [
    # ------------------------------------------------------------------
    # equipment — structure
    # ------------------------------------------------------------------
    {
        "rule_id": "EQP-SCH-001",
        "source": "equipment",
        "column": "*",
        "description": "Les 7 colonnes annoncees par SCHEMA.md sont presentes.",
        "justification": "Une colonne absente rend la table inexploitable pour DiagOps et invalide toutes les regles qui en dependent.",
        "severity": "bloquante",
        "decision_if_failed": "arret_audit",
    },
    {
        "rule_id": "EQP-SCH-002",
        "source": "equipment",
        "column": "commissioning_date",
        "description": "Chaque valeur non nulle se lit comme une date.",
        "justification": "Une date non analysable interdit tout controle de coherence temporelle en aval.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "EQP-SCH-003",
        "source": "equipment",
        "column": "rated_power_kw",
        "description": "Chaque valeur non nulle se lit comme un nombre.",
        "justification": "Le schema annonce un numerique ; du texte dans cette colonne signale une saisie libre non controlee.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    # equipment — identifiants
    {
        "rule_id": "EQP-KEY-001",
        "source": "equipment",
        "column": "equipment_id",
        "description": "equipment_id est renseigne sur toutes les lignes.",
        "justification": "Sans identifiant, l'equipement ne peut etre rattache a aucun evenement ni a aucune intervention.",
        "severity": "bloquante",
        "decision_if_failed": "quarantaine_rejet",
    },
    {
        "rule_id": "EQP-KEY-002",
        "source": "equipment",
        "column": "equipment_id",
        "description": "equipment_id est unique.",
        "justification": "C'est la cle primaire annoncee. Un doublon rend ambigu tout rapprochement depuis events et maintenance_history.",
        "severity": "bloquante",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "EQP-KEY-003",
        "source": "equipment",
        "column": "*",
        "description": "Aucune ligne n'est un doublon exact d'une autre sur toutes ses colonnes.",
        "justification": "Un doublon integral n'apporte aucune information et fausse les effectifs par site ou par criticite.",
        "severity": "majeure",
        "decision_if_failed": "correction_certaine",
    },
    # equipment — categories
    {
        "rule_id": "EQP-CAT-001",
        "source": "equipment",
        "column": "criticality",
        "description": f"criticality inconnue de {CRITICALITY_VALUES} et marginale.",
        "justification": "Enumeration fermee par SCHEMA.md. Une valeur inconnue et isolee est une anomalie de saisie : elle ne peut etre interpretee et fausserait toute priorisation.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "EQP-NOM-001",
        "source": "equipment",
        "column": "criticality",
        "description": f"criticality inconnue de {CRITICALITY_VALUES} mais portee par au moins {RECURRENCE_THRESHOLD:.0%} des lignes.",
        "justification": f"AJOUTEE le 03/08/2026. Une valeur inconnue presente sur plus de {RECURRENCE_THRESHOLD:.0%} d'une table de facon reguliere n'est pas une anomalie : c'est un ecart entre la nomenclature du schema et celle de la livraison. Rejeter serait ecarter une part massive de donnees saines pour un defaut de documentation.",
        "severity": "majeure",
        "decision_if_failed": "signalement",
    },
    {
        "rule_id": "EQP-CAS-001",
        "source": "equipment",
        "column": "criticality",
        "description": "criticality dont seule la casse ou l'espacement devie d'une valeur connue.",
        "justification": "AJOUTEE le 03/08/2026. `High` pour `high` designe sans ambiguite la meme classe : la normalisation est sure et reproductible, elle ne perd aucune information.",
        "severity": "mineure",
        "decision_if_failed": "correction_certaine",
    },
    {
        "rule_id": "EQP-CAT-002",
        "source": "equipment",
        "column": "site_id",
        "description": "Inventaire des sites et de leurs effectifs ; les sites a effectif tres faible sont signales.",
        "justification": "Le schema ne fixe pas de liste fermee. Un effectif de une ou deux lignes interdit toute conclusion sur ce site.",
        "severity": "mineure",
        "decision_if_failed": "signalement",
    },
    {
        "rule_id": "EQP-CAT-003",
        "source": "equipment",
        "column": "equipment_type",
        "description": "Inventaire des familles d'equipement et de leurs effectifs ; les variantes proches sont signalees.",
        "justification": "Liste ouverte. Deux libelles voisins peuvent designer la meme famille et eclater artificiellement les effectifs.",
        "severity": "mineure",
        "decision_if_failed": "signalement",
    },
    # equipment — temporel
    {
        "rule_id": "EQP-TMP-001",
        "source": "equipment",
        "column": "commissioning_date",
        "description": "La mise en service n'est pas posterieure a la date du jour.",
        "justification": "Un equipement mis en service dans le futur ne peut avoir ni evenement ni intervention : la donnee est fausse.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "EQP-TMP-002",
        "source": "equipment",
        "column": "commissioning_date",
        "description": f"La mise en service n'est pas anterieure au {MIN_COMMISSIONING_DATE}.",
        "justification": "Borne ajoutee : un parc industriel suivi par capteurs ne contient pas d'equipement anterieur a cette date. Sert a detecter les dates par defaut du type 1900-01-01.",
        "severity": "mineure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    # equipment — valeurs
    {
        "rule_id": "EQP-VAL-001",
        "source": "equipment",
        "column": "rated_power_kw",
        "description": "La puissance nominale renseignee est strictement positive.",
        "justification": "Une puissance nulle ou negative n'a pas de sens physique pour un equipement en service.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "EQP-VAL-002",
        "source": "equipment",
        "column": "rated_power_kw",
        "description": f"La puissance nominale renseignee ne depasse pas {MAX_RATED_POWER_KW} kW.",
        "justification": "Borne ajoutee : au-dela on quitte l'echelle d'un equipement d'atelier. Detecte surtout les erreurs d'unite (W saisis en kW).",
        "severity": "mineure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    # equipment — manquants
    {
        "rule_id": "EQP-NUL-001",
        "source": "equipment",
        "column": "manufacturer",
        "description": "Mesure du taux de valeurs absentes.",
        "justification": "Le schema autorise le nul. Le taux doit etre connu : un champ vide a plus de la moitie n'est pas exploitable en analyse.",
        "severity": "mineure",
        "decision_if_failed": "signalement",
    },
    {
        "rule_id": "EQP-NUL-002",
        "source": "equipment",
        "column": "rated_power_kw",
        "description": "Mesure du taux de valeurs absentes.",
        "justification": "Le schema autorise le nul. Meme raisonnement que EQP-NUL-001.",
        "severity": "mineure",
        "decision_if_failed": "signalement",
    },
    # ------------------------------------------------------------------
    # events — structure
    # ------------------------------------------------------------------
    {
        "rule_id": "EVT-SCH-001",
        "source": "events",
        "column": "*",
        "description": "Les 7 colonnes annoncees par SCHEMA.md sont presentes.",
        "justification": "Meme raisonnement que EQP-SCH-001.",
        "severity": "bloquante",
        "decision_if_failed": "arret_audit",
    },
    {
        "rule_id": "EVT-SCH-002",
        "source": "events",
        "column": "start_at, end_at",
        "description": "Chaque horodatage non nul se lit comme une date-heure ISO 8601.",
        "justification": "Le schema annonce de l'ISO 8601. Un format melange empeche tout tri et tout calcul de duree.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    # events — identifiants
    {
        "rule_id": "EVT-KEY-001",
        "source": "events",
        "column": "event_id",
        "description": "event_id est renseigne sur toutes les lignes.",
        "justification": "Sans identifiant, l'evenement ne peut etre rattache a ses interventions.",
        "severity": "bloquante",
        "decision_if_failed": "quarantaine_rejet",
    },
    {
        "rule_id": "EVT-KEY-002",
        "source": "events",
        "column": "event_id",
        "description": "event_id est unique.",
        "justification": "Cle primaire annoncee. Un doublon dedouble mecaniquement les interventions rattachees lors d'une jointure.",
        "severity": "bloquante",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "EVT-KEY-003",
        "source": "events",
        "column": "*",
        "description": "Aucune ligne n'est un doublon exact d'une autre.",
        "justification": "Meme raisonnement que EQP-KEY-003.",
        "severity": "majeure",
        "decision_if_failed": "correction_certaine",
    },
    # events — references
    {
        "rule_id": "EVT-REF-001",
        "source": "events",
        "column": "equipment_id",
        "description": "equipment_id est renseigne.",
        "justification": "Un evenement sans equipement ne peut alimenter aucun diagnostic DiagOps.",
        "severity": "bloquante",
        "decision_if_failed": "quarantaine_rejet",
    },
    {
        "rule_id": "EVT-REF-002",
        "source": "events",
        "column": "equipment_id",
        "description": "equipment_id existe dans equipment.equipment_id.",
        "justification": "Relation annoncee par le brief. Une reference orpheline signale un parc incomplet ou un identifiant errone ; dans les deux cas l'evenement n'est pas interpretable.",
        "severity": "bloquante",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    # events — categories
    {
        "rule_id": "EVT-CAT-001",
        "source": "events",
        "column": "event_type",
        "description": f"event_type inconnu de {EVENT_TYPE_VALUES} et marginal.",
        "justification": "REVISEE le 03/08/2026. La regle initiale echouait sur 50 lignes melangeant deux causes sans rapport : 49 `alert` (nomenclature) et 1 `Incident` (casse). L'anomalie reelle se noyait dans l'ecart documentaire. Ne retient desormais que les valeurs inconnues et isolees.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "EVT-NOM-001",
        "source": "events",
        "column": "event_type",
        "description": f"event_type inconnu de {EVENT_TYPE_VALUES} mais porte par au moins {RECURRENCE_THRESHOLD:.0%} des lignes.",
        "justification": "AJOUTEE le 03/08/2026. Cible l'ecart constate entre `alerte` annonce par SCHEMA.md et `alert` livre dans les donnees. Le schema et la livraison ne parlent pas la meme langue sur cette valeur ; c'est au metier de dire laquelle fait foi, pas a l'audit de rejeter 9 % de la table.",
        "severity": "majeure",
        "decision_if_failed": "signalement",
    },
    {
        "rule_id": "EVT-CAS-001",
        "source": "events",
        "column": "event_type",
        "description": "event_type dont seule la casse ou l'espacement devie d'une valeur connue.",
        "justification": "AJOUTEE le 03/08/2026. Isole le cas `Incident` de la masse des `alert`. Normalisation sure.",
        "severity": "mineure",
        "decision_if_failed": "correction_certaine",
    },
    {
        "rule_id": "EVT-CAT-002",
        "source": "events",
        "column": "severity",
        "description": f"severity inconnue de {SEVERITY_VALUES} et marginale.",
        "justification": "Enumeration fermee par SCHEMA.md, et champ present dans le contrat de sortie DiagOps. Meme decoupage que EVT-CAT-001, applique par coherence a toutes les enumerations fermees.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "EVT-NOM-002",
        "source": "events",
        "column": "severity",
        "description": f"severity inconnue de {SEVERITY_VALUES} mais portee par au moins {RECURRENCE_THRESHOLD:.0%} des lignes.",
        "justification": "AJOUTEE le 03/08/2026 par coherence avec EVT-NOM-001. Aucun cas attendu sur cette colonne, la regle sert de garde-fou si la nomenclature derive dans une livraison ulterieure.",
        "severity": "majeure",
        "decision_if_failed": "signalement",
    },
    {
        "rule_id": "EVT-CAS-002",
        "source": "events",
        "column": "severity",
        "description": "severity dont seule la casse ou l'espacement devie d'une valeur connue.",
        "justification": "AJOUTEE le 03/08/2026 par coherence avec EVT-CAS-001.",
        "severity": "mineure",
        "decision_if_failed": "correction_certaine",
    },
    {
        "rule_id": "EVT-CAT-003",
        "source": "events",
        "column": "period",
        "description": f"period vaut {EXPECTED_PERIOD}.",
        "justification": "La livraison porte sur une seule periode. Une autre valeur signale un melange de livraisons, qui fausserait toute analyse temporelle.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    # events — temporel
    {
        "rule_id": "EVT-TMP-001",
        "source": "events",
        "column": "start_at, end_at",
        "description": "Si end_at est renseigne, start_at lui est anterieur ou egal.",
        "justification": "Un evenement qui se termine avant d'avoir commence est impossible et produirait une duree negative.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "EVT-TMP-002",
        "source": "events",
        "column": "start_at",
        "description": "start_at n'est pas posterieur a la date du jour.",
        "justification": "Un evenement futur ne peut pas avoir ete observe.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "EVT-TMP-003",
        "source": "events",
        "column": "start_at",
        "description": "start_at est posterieur ou egal a la commissioning_date de l'equipement concerne.",
        "justification": "Controle croise : un evenement anterieur a la mise en service revele une incoherence entre les deux tables. On ne sait pas laquelle des deux dates est fausse.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    # events — manquants
    {
        "rule_id": "EVT-NUL-001",
        "source": "events",
        "column": "end_at",
        "description": "Mesure du taux de end_at absents.",
        "justification": "Le schema annonce une fin 'si applicable' : un nul signifie evenement en cours, ce n'est pas une anomalie. Le taux doit neanmoins etre connu et rester plausible.",
        "severity": "mineure",
        "decision_if_failed": "signalement",
    },
    # ------------------------------------------------------------------
    # maintenance_history — structure
    # ------------------------------------------------------------------
    {
        "rule_id": "MNT-SCH-001",
        "source": "maintenance",
        "column": "*",
        "description": "Les 13 colonnes annoncees par SCHEMA.md sont presentes.",
        "justification": "Meme raisonnement que EQP-SCH-001.",
        "severity": "bloquante",
        "decision_if_failed": "arret_audit",
    },
    {
        "rule_id": "MNT-SCH-002",
        "source": "maintenance",
        "column": "opened_at, closed_at",
        "description": "Chaque horodatage non nul se lit comme une date-heure ISO 8601.",
        "justification": "Meme raisonnement que EVT-SCH-002.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "MNT-SCH-003",
        "source": "maintenance",
        "column": "downtime_minutes, labor_hours, parts_cost_eur, parts_replaced_count",
        "description": "Chaque valeur non nulle se lit comme un nombre ; downtime_minutes et parts_replaced_count sont entiers.",
        "justification": "Types annonces par le schema. Un decimal sur un compteur de pieces signale une saisie ou un export defectueux.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    # maintenance — identifiants
    {
        "rule_id": "MNT-KEY-001",
        "source": "maintenance",
        "column": "maintenance_id",
        "description": "maintenance_id est renseigne sur toutes les lignes.",
        "justification": "Sans identifiant, l'intervention n'est ni tracable ni citable en quarantaine.",
        "severity": "bloquante",
        "decision_if_failed": "quarantaine_rejet",
    },
    {
        "rule_id": "MNT-KEY-002",
        "source": "maintenance",
        "column": "maintenance_id",
        "description": "maintenance_id est unique.",
        "justification": "Cle primaire annoncee. Un doublon gonfle artificiellement les couts et les temps d'arret cumules.",
        "severity": "bloquante",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "MNT-KEY-003",
        "source": "maintenance",
        "column": "*",
        "description": "Aucune ligne n'est un doublon exact d'une autre.",
        "justification": "Meme raisonnement que EQP-KEY-003, avec un enjeu chiffre : les couts et durees se cumulent.",
        "severity": "majeure",
        "decision_if_failed": "correction_certaine",
    },
    # maintenance — references
    {
        "rule_id": "MNT-REF-001",
        "source": "maintenance",
        "column": "event_id",
        "description": "event_id existe dans events.event_id.",
        "justification": "Relation annoncee par le brief. Une intervention rattachee a un evenement inexistant ne peut etre replacee dans son contexte.",
        "severity": "bloquante",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "MNT-REF-002",
        "source": "maintenance",
        "column": "equipment_id",
        "description": "equipment_id existe dans equipment.equipment_id.",
        "justification": "Relation annoncee par le brief. Meme raisonnement que EVT-REF-002.",
        "severity": "bloquante",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "MNT-REF-003",
        "source": "maintenance",
        "column": "equipment_id, event_id",
        "description": "equipment_id est identique a l'equipment_id de l'evenement designe par event_id.",
        "justification": "L'equipement est porte deux fois : directement et via l'evenement. Une divergence est une contradiction interne, et rien ne dit laquelle des deux valeurs est la bonne.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    # maintenance — categories
    {
        "rule_id": "MNT-CAT-001",
        "source": "maintenance",
        "column": "intervention_type",
        "description": "Inventaire des types d'intervention et de leurs effectifs ; les libelles rares ou voisins sont signales.",
        "justification": "Le schema annonce une chaine libre, sans liste fermee : on ne peut pas rejeter une valeur, seulement documenter ce qui existe.",
        "severity": "mineure",
        "decision_if_failed": "signalement",
    },
    {
        "rule_id": "MNT-CAT-002",
        "source": "maintenance",
        "column": "outcome",
        "description": "Inventaire des resultats d'intervention et de leurs effectifs.",
        "justification": "Meme raisonnement que MNT-CAT-001.",
        "severity": "mineure",
        "decision_if_failed": "signalement",
    },
    {
        "rule_id": "MNT-CAT-003",
        "source": "maintenance",
        "column": "period",
        "description": f"period vaut {EXPECTED_PERIOD}.",
        "justification": "Meme raisonnement que EVT-CAT-003.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    # maintenance — temporel
    {
        "rule_id": "MNT-TMP-001",
        "source": "maintenance",
        "column": "opened_at, closed_at",
        "description": "Si closed_at est renseigne, opened_at lui est anterieur ou egal.",
        "justification": "Une intervention cloturee avant son ouverture est impossible et produit une duree negative.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "MNT-TMP-002",
        "source": "maintenance",
        "column": "opened_at",
        "description": "opened_at n'est pas posterieur a la date du jour.",
        "justification": "Une intervention ouverte dans le futur est une erreur de saisie ou d'export.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "MNT-TMP-003",
        "source": "maintenance",
        "column": "opened_at",
        "description": "opened_at est posterieur ou egal au start_at de l'evenement designe.",
        "justification": "Controle croise : on n'intervient pas avant que l'evenement declencheur ait commence. Revele une incoherence entre les deux tables sans dire laquelle est fausse.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    # maintenance — valeurs impossibles
    {
        "rule_id": "MNT-VAL-001",
        "source": "maintenance",
        "column": "downtime_minutes",
        "description": "downtime_minutes est superieur ou egal a zero.",
        "justification": "Une indisponibilite negative n'a pas de sens et fausserait tout cumul.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "MNT-VAL-002",
        "source": "maintenance",
        "column": "downtime_minutes",
        "description": f"downtime_minutes ne depasse pas {MAX_DOWNTIME_MINUTES} minutes.",
        "justification": "Borne ajoutee : 30 jours d'arret continu sur un equipement suivi releve de la mise au rebut, pas de la maintenance courante. Detecte les erreurs d'unite (minutes saisies en secondes).",
        "severity": "mineure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "MNT-VAL-003",
        "source": "maintenance",
        "column": "downtime_minutes, opened_at, closed_at",
        "description": "Si les deux horodatages sont renseignes, downtime_minutes ne depasse pas l'ecart closed_at - opened_at.",
        "justification": "L'indisponibilite est incluse dans la duree d'intervention. Un depassement signale que les deux informations proviennent de sources qui ne se parlent pas.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "MNT-VAL-004",
        "source": "maintenance",
        "column": "labor_hours",
        "description": f"labor_hours renseigne est compris entre zero et {MAX_LABOR_HOURS} heures.",
        "justification": "Negatif impossible ; borne haute ajoutee, au-dela on depasse une annee-homme sur une seule intervention.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "MNT-VAL-005",
        "source": "maintenance",
        "column": "parts_cost_eur",
        "description": "parts_cost_eur renseigne est superieur ou egal a zero.",
        "justification": "Un cout de pieces negatif n'est pas un cout : c'est un avoir ou une erreur de signe, a examiner.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "MNT-VAL-006",
        "source": "maintenance",
        "column": "parts_replaced_count",
        "description": "parts_replaced_count est un entier superieur ou egal a zero.",
        "justification": "Un compteur de pieces negatif ou fractionnaire est impossible.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
    {
        "rule_id": "MNT-VAL-007",
        "source": "maintenance",
        "column": "parts_cost_eur, parts_replaced_count",
        "description": "Mesure de la part d'interventions facturant des pieces sans en declarer aucune.",
        "justification": "REVISEE le 03/08/2026 apres mesure. Ecrite comme regle de rejet, elle echouait sur 595 lignes sur 1800 reparties uniformement sur les cinq types d'intervention : ce n'est pas une anomalie mais un motif structurel du jeu. Une regle metier inventee depuis un schema ne peut pas mettre un tiers d'une table en quarantaine. Devient un constat chiffre, a soumettre au metier.",
        "severity": "mineure",
        "decision_if_failed": "signalement",
    },
    # maintenance — manquants
    {
        "rule_id": "MNT-NUL-001",
        "source": "maintenance",
        "column": "closed_at",
        "description": "Mesure du taux de closed_at absents.",
        "justification": "Le schema annonce une cloture 'si applicable' : un nul signifie intervention en cours. Le taux doit rester plausible au regard de la periode livree.",
        "severity": "mineure",
        "decision_if_failed": "signalement",
    },
    {
        "rule_id": "MNT-NUL-002",
        "source": "maintenance",
        "column": "labor_hours, parts_cost_eur",
        "description": "Mesure du taux de valeurs absentes sur les deux colonnes nullables.",
        "justification": "Le schema autorise le nul. Un taux eleve rend la colonne inutilisable pour une analyse de cout en M3.",
        "severity": "mineure",
        "decision_if_failed": "signalement",
    },
    # maintenance — donnees personnelles
    {
        "rule_id": "MNT-PII-001",
        "source": "maintenance",
        "column": "work_order_note",
        "description": "Recherche d'adresses electroniques, de numeros de telephone et de noms de personnes dans le texte libre.",
        "justification": "Champ de saisie libre : c'est la ou des donnees personnelles arrivent sans avoir ete prevues. Axe 3 du brief ; a distinguer des identifiants techniques necessaires a DiagOps.",
        "severity": "majeure",
        "decision_if_failed": "quarantaine_examen_metier",
    },
]


REVISIONS: list[dict[str, str]] = [
    {
        "date": "2026-08-03",
        "rule_id": "MNT-VAL-007",
        "change": "rejet -> signalement, severite majeure -> mineure",
        "trigger": "595 echecs sur 1800 lignes, repartis uniformement sur les cinq intervention_type",
        "reason": "Une regle metier inventee depuis le schema, qui echoue sur un tiers de la table de facon reguliere, decrit un motif structurel du jeu et non une anomalie. Le constat reste publie ; le rejet est retire.",
    },
    {
        "date": "2026-08-03",
        "rule_id": "EVT-CAT-001",
        "change": "scindee en EVT-CAT-001 (inconnue isolee), EVT-NOM-001 (inconnue recurrente), EVT-CAS-001 (variante de casse)",
        "trigger": "50 echecs melangeant 49 `alert` et 1 `Incident`",
        "reason": "Deux causes sans rapport sous une meme regle : un ecart de nomenclature entre SCHEMA.md (`alerte`) et la livraison (`alert`), et une anomalie de casse isolee. La seconde etait invisible derriere la premiere.",
    },
    {
        "date": "2026-08-03",
        "rule_id": "EQP-CAT-001, EVT-CAT-002",
        "change": "meme scission appliquee aux deux autres enumerations fermees",
        "trigger": "coherence de traitement",
        "reason": "Une regle ne peut pas changer de forme selon la colonne ou elle a trouve quelque chose. Le decoupage vaut pour toutes les enumerations fermees, y compris celles ou aucun ecart n'a ete constate.",
    },
]


def revisions() -> pd.DataFrame:
    """Journal des revisions du registre, posterieures a la premiere mesure."""
    return pd.DataFrame(REVISIONS, columns=["date", "rule_id", "change", "trigger", "reason"])


def rule_register() -> pd.DataFrame:
    """Retourne le registre des regles au format attendu par le notebook."""
    return pd.DataFrame(RULES, columns=REGISTER_COLUMNS)


def rules_for(source: str) -> pd.DataFrame:
    """Filtre le registre sur une source."""
    register = rule_register()
    return register.loc[register["source"] == source].reset_index(drop=True)
