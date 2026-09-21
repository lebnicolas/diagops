# Synthèse de la préparation de référence M2

## Volumes

| Table | Lignes reçues | Lignes préparées | Écart |
|---|---:|---:|---:|
| `equipment.csv` | 420 | 416 | -4 |
| `events.csv` | 520 | 514 | -6 |
| `maintenance_history.csv` | 1800 | 1788 | -12 |

La quarantaine contient **35 lignes** réparties sur
**18 couples règle/table**. Chaque entrée porte une règle, une valeur
observée, une raison et une décision.

## Couverture du parc préparé

- sites : SITE-EST = 91, SITE-NORD = 173, SITE-OUEST = 16, SITE-SUD = 136 ;
- criticités : critical = 46, high = 122, low = 75, medium = 173 ;
- sévérités des événements : critical = 73, high = 213, low = 71, medium = 157.

## Ce que cette référence ne fait pas

- elle ne rejoue pas les analyses statistiques du brief online M2 ;
- elle n'impute aucune valeur manquante ;
- elle ne tranche pas les valeurs extrêmes plausibles : les durées d'arrêt très
  longues sont conservées et signalées, pas supprimées ;
- elle ne constitue pas la seule préparation acceptable.

## Points ouverts transmis à M3

- les valeurs manquantes de `parts_cost_eur` restent concentrées sur un site ;
- les catégories peu représentées n'ont pas été regroupées ;
- la pseudonymisation des notes est appliquée par motif : elle ne garantit pas
  l'absence de toute information indirecte ;
- aucune règle temporelle n'existe encore : M3 doit les créer pour les capteurs.
