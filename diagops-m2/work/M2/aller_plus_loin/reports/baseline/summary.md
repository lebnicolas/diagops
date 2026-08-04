# Qualification — Socle M2 publie

- **Lot** : `diagops-2026-S1-m2-published`
- **Version des regles** : `1.0.0`
- **Statut** : **ACCEPTED_WITH_WARNINGS**
- **Constats** : 0 erreur(s), 25 avertissement(s), 1 information(s)

## Avertissements

| Regle | Source | Colonne | Echecs | Taux | Constat |
|---|---|---|---:|---:|---|
| `MNT-KEY-002` | maintenance | maintenance_id | 10 | 0.56% | maintenance_id est unique. |
| `EQP-KEY-002` | equipment | equipment_id | 8 | 1.90% | equipment_id est unique. |
| `EVT-KEY-002` | events | event_id | 8 | 1.54% | event_id est unique. |
| `MNT-KEY-003` | maintenance | * | 5 | 0.28% | Aucune ligne n'est un doublon exact d'une autre. |
| `EQP-KEY-003` | equipment | * | 4 | 0.95% | Aucune ligne n'est un doublon exact d'une autre sur toutes ses colonnes. |
| `EVT-KEY-003` | events | * | 4 | 0.77% | Aucune ligne n'est un doublon exact d'une autre. |
| `MNT-VAL-003` | maintenance | downtime_minutes | 2 | 0.11% | Si les deux horodatages sont renseignes, downtime_minutes ne depasse pas l'ecart closed_at - opened_at. |
| `MNT-PII-001` | maintenance | work_order_note | 2 | 0.11% | Donnees personnelles dans le texte libre. Quelques occurrences se traitent au cas par cas. Au-dela de 10 %, le champ est utilise comme main courante nominative  |
| `EQP-CAS-002` | equipment | equipment_type | 1 | 0.24% | Libelles declares equivalents sur une categorie ouverte : 'Pump ' -> 'pump'. |
| `EQP-TMP-001` | equipment | commissioning_date | 1 | 0.24% | La mise en service n'est pas posterieure a la date du jour. |
| `EQP-VAL-001` | equipment | rated_power_kw | 1 | 0.24% | La puissance nominale renseignee est strictement positive. |
| `EVT-REF-002` | events | equipment_id | 1 | 0.19% | Un evenement rattache a un equipement inconnu du parc. Isole, c'est une ligne fausse. Au-dela de 2 %, le lot ne parle pas du meme parc. |
| `EVT-CAS-001` | events | event_type | 1 | 0.19% | event_type dont seule la casse ou l'espacement devie d'une valeur connue. |
| `EVT-CAT-002` | events | severity | 1 | 0.19% | severity inconnue de ('critical', 'high', 'low', 'medium') et marginale. |
| `EVT-TMP-001` | events | end_at | 1 | 0.19% | Si end_at est renseigne, start_at lui est anterieur ou egal. |
| `EVT-TMP-003` | events | start_at | 1 | 0.19% | Meme plafond par coherence : une regle ne change pas de forme selon la table ou elle a trouve quelque chose. |
| `MNT-REF-001` | maintenance | event_id | 1 | 0.06% | Meme raisonnement que EVT-REF-002, sur le rattachement a l'evenement. |
| `MNT-REF-002` | maintenance | equipment_id | 1 | 0.06% | Meme raisonnement que EVT-REF-002. |
| `MNT-REF-003` | maintenance | equipment_id | 1 | 0.06% | Contradiction interne entre l'equipement porte par l'intervention et celui porte par son evenement. Systematique, c'est un defaut de construction de l'export, p |
| `MNT-CAS-001` | maintenance | intervention_type | 1 | 0.06% | Libelles declares equivalents sur une categorie ouverte : 'Correctif' -> 'corrective'. |
| `MNT-CAT-004` | maintenance | intervention_type | 1 | 0.06% | intervention_type inconnu de ('calibration', 'corrective', 'inspection', 'preventive', 'replacement') et marginal. |
| `MNT-TMP-001` | maintenance | closed_at | 1 | 0.06% | Si closed_at est renseigne, opened_at lui est anterieur ou egal. |
| `MNT-VAL-001` | maintenance | downtime_minutes | 1 | 0.06% | downtime_minutes est superieur ou egal a zero. |
| `MNT-VAL-002` | maintenance | downtime_minutes | 1 | 0.06% | downtime_minutes ne depasse pas 43200 minutes. |
| `MNT-VAL-005` | maintenance | parts_cost_eur | 1 | 0.06% | parts_cost_eur renseigne est superieur ou egal a zero. |

## Informations

| Regle | Source | Colonne | Echecs | Taux | Constat |
|---|---|---|---:|---:|---|
| `MNT-VAL-007` | maintenance | parts_cost_eur | 595 | 33.06% | Interventions facturant des pieces sans en declarer. Mesure le 03/08/2026 a 595 lignes sur 1 800, reparties uniformement sur les cinq types d'intervention : mot |

> ⬆ signale une regle passee au niveau superieur parce que son taux
> d'echec depasse le plafond de la politique : le constat ne decrit
> plus des lignes fausses mais une livraison fausse.
