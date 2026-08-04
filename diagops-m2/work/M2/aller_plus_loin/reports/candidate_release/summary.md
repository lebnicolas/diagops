# Qualification — Livraison candidate M2 — lot 02

- **Lot** : `diagops-2026-S1-m2-candidate-r2`
- **Version des regles** : `1.0.0`
- **Statut** : **REJECTED**
- **Constats** : 4 erreur(s), 22 avertissement(s), 5 information(s)

## Erreurs bloquantes

| Regle | Source | Colonne | Echecs | Taux | Constat |
|---|---|---|---:|---:|---|
| `MNT-TMP-003` ⬆ | maintenance | opened_at | 86 | 39.09% | taux d'echec 39.09% au-dela du plafond 5.00% — regression globale, pas anomalie de ligne |
| `EQP-KEY-001` | equipment | equipment_id | 1 | 3.33% | equipment_id est renseigne sur toutes les lignes. |
| `INC-KEY-003` | events | event_id | 1 | 1.25% | 1 cle(s) deja presente(s) dans le publie — aucune collision attendue sur un lot d'ajouts |
| `INC-KEY-004` | maintenance | maintenance_id | 1 | 0.45% | 1 cle(s) deja presente(s) dans le publie — aucune collision attendue sur un lot d'ajouts |

## Avertissements

| Regle | Source | Colonne | Echecs | Taux | Constat |
|---|---|---|---:|---:|---|
| `MNT-REF-003` | maintenance | equipment_id | 4 | 1.82% | Contradiction interne entre l'equipement porte par l'intervention et celui porte par son evenement. Systematique, c'est un defaut de construction de l'export, p |
| `MNT-REF-002` | maintenance | equipment_id | 3 | 1.36% | Meme raisonnement que EVT-REF-002. |
| `EQP-KEY-002` | equipment | equipment_id | 2 | 6.67% | equipment_id est unique. |
| `EVT-KEY-002` | events | event_id | 2 | 2.50% | event_id est unique. |
| `MNT-KEY-002` | maintenance | maintenance_id | 2 | 0.91% | maintenance_id est unique. |
| `MNT-PII-001` | maintenance | work_order_note | 2 | 0.91% | Donnees personnelles dans le texte libre. Quelques occurrences se traitent au cas par cas. Au-dela de 10 %, le champ est utilise comme main courante nominative  |
| `EQP-SCH-002` | equipment | commissioning_date | 1 | 3.33% | Chaque valeur non nulle se lit comme une date. |
| `EQP-KEY-003` | equipment | * | 1 | 3.33% | Aucune ligne n'est un doublon exact d'une autre sur toutes ses colonnes. |
| `EQP-CAT-001` | equipment | criticality | 1 | 3.33% | criticality inconnue de ('critical', 'high', 'low', 'medium') et marginale. |
| `EQP-VAL-001` | equipment | rated_power_kw | 1 | 3.33% | La puissance nominale renseignee est strictement positive. |
| `EVT-REF-002` | events | equipment_id | 1 | 1.25% | Un evenement rattache a un equipement inconnu du parc. Isole, c'est une ligne fausse. Au-dela de 2 %, le lot ne parle pas du meme parc. |
| `EVT-CAT-001` | events | event_type | 1 | 1.25% | event_type inconnu de ('alert', 'incident', 'intervention', 'observation') et marginal. |
| `EVT-CAS-002` | events | severity | 1 | 1.25% | severity dont seule la casse ou l'espacement devie d'une valeur connue. |
| `EVT-TMP-001` | events | end_at | 1 | 1.25% | Si end_at est renseigne, start_at lui est anterieur ou egal. |
| `MNT-SCH-003` | maintenance | downtime_minutes, labor_hours, parts_cost_eur, parts_replaced_count | 1 | 0.45% | Chaque valeur non nulle se lit comme un nombre ; downtime_minutes et parts_replaced_count sont entiers. |
| `MNT-REF-001` | maintenance | event_id | 1 | 0.45% | Meme raisonnement que EVT-REF-002, sur le rattachement a l'evenement. |
| `MNT-CAT-004` | maintenance | intervention_type | 1 | 0.45% | intervention_type inconnu de ('calibration', 'corrective', 'inspection', 'preventive', 'replacement') et marginal. |
| `MNT-CAT-005` | maintenance | outcome | 1 | 0.45% | outcome inconnu de ('follow_up_required', 'monitoring', 'no_fault_found', 'parts_ordered', 'resolved') et marginal. |
| `MNT-TMP-001` | maintenance | closed_at | 1 | 0.45% | Si closed_at est renseigne, opened_at lui est anterieur ou egal. |
| `MNT-VAL-001` | maintenance | downtime_minutes | 1 | 0.45% | downtime_minutes est superieur ou egal a zero. |
| `MNT-VAL-003` | maintenance | downtime_minutes | 1 | 0.45% | Si les deux horodatages sont renseignes, downtime_minutes ne depasse pas l'ecart closed_at - opened_at. |
| `MNT-VAL-006` | maintenance | parts_replaced_count | 1 | 0.45% | parts_replaced_count est un entier superieur ou egal a zero. |

## Informations

| Regle | Source | Colonne | Echecs | Taux | Constat |
|---|---|---|---:|---:|---|
| `MNT-VAL-007` | maintenance | parts_cost_eur | 45 | 20.45% | Interventions facturant des pieces sans en declarer. Mesure le 03/08/2026 a 595 lignes sur 1 800, reparties uniformement sur les cinq types d'intervention : mot |
| `INC-KEY-002` | equipment | equipment_id | 4 | 13.33% | 4 cle(s) deja presente(s) dans le publie — operation de mise a jour annoncee |
| `INC-CAT-001` | equipment | equipment_type | 1 | 3.33% | valeurs inedites : hydraulic_unit |
| `INC-CAT-001` | equipment | site_id | 1 | 3.33% | valeurs inedites : SITE-CENTRE |
| `INC-SCH-001` | maintenance | source_system | 1 | 0.45% | colonnes : source_system |

> ⬆ signale une regle passee au niveau superieur parce que son taux
> d'echec depasse le plafond de la politique : le constat ne decrit
> plus des lignes fausses mais une livraison fausse.
