# Registre des règles de référence M2

Chaque règle porte un identifiant stable, une table, une condition et une
décision. M3 réutilise ce registre, le complète pour les mesures capteurs et
documente toute modification.

| Règle | Table | Condition contrôlée | Décision appliquée |
|---|---|---|---|
| `R-EQ-001` | equipment | `equipment_id` unique | doublon exact supprimé, conflit exclu |
| `R-EQ-002` | equipment | `criticality` dans le domaine fermé | ligne exclue |
| `R-EQ-003` | equipment | `equipment_type` normalisé | valeur normalisée |
| `R-EQ-004` | equipment | `rated_power_kw` strictement positive | champ neutralisé |
| `R-EQ-005` | equipment | `commissioning_date` antérieure à la fin de période | champ neutralisé |
| `R-EQ-006` | equipment | champs descriptifs renseignés | ligne conservée et signalée |
| `R-EVT-001` | events | `event_id` unique | doublon exact supprimé, conflit exclu |
| `R-EVT-002` | events | `severity` dans le domaine fermé | ligne exclue |
| `R-EVT-003` | events | `event_type` normalisé et dans le domaine | normalisation puis exclusion |
| `R-EVT-004` | events | `end_at` postérieure à `start_at` | champ neutralisé |
| `R-EVT-005` | events | `equipment_id` présent dans la table préparée | ligne exclue |
| `R-MNT-001` | maintenance | `maintenance_id` unique | doublon exact supprimé, conflit exclu |
| `R-MNT-002` | maintenance | `event_id` présent dans la table préparée | ligne exclue |
| `R-MNT-003` | maintenance | `equipment_id` présent dans la table préparée | ligne exclue |
| `R-MNT-004` | maintenance | `closed_at` postérieure à `opened_at` | champ neutralisé |
| `R-MNT-005` | maintenance | `downtime_minutes` positive et plausible | exclusion ou signalement |
| `R-MNT-006` | maintenance | `parts_cost_eur` positive | champ neutralisé |
| `R-MNT-007` | maintenance | `intervention_type` normalisé et dans le domaine | normalisation puis exclusion |
| `R-MNT-008` | maintenance | absence d'information personnelle directe dans les notes | pseudonymisation |

## Vocabulaire des décisions

| Décision | Sens |
|---|---|
| `doublon_supprime` | ligne strictement identique retirée, trace conservée |
| `exclue` | ligne retirée de la table préparée |
| `champ_neutralise` | ligne conservée, champ vidé et tracé |
| `valeur_normalisee` | valeur corrigée de façon déterministe |
| `conserve_signale` | ligne conservée, anomalie signalée pour expertise |
| `pseudonymise` | information directe remplacée par un marqueur stable |

## Limites connues

- la cascade est volontairement ordonnée équipements → événements →
  interventions : une exclusion amont retire des lignes aval ;
- aucune règle ne porte encore sur une série temporelle ;
- la détection d'information personnelle repose sur des motifs et peut manquer
  une formulation inhabituelle.
