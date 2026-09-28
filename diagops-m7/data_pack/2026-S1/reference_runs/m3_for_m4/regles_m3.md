# Registre figé des règles M3

| Identifiant | Contrôle | Limite connue |
|---|---|---|
| `M3-PERIOD` | période différente de `2026-S1` | ne détecte pas une fabrication conforme |
| `M3-SENSOR` | capteur hors contrat | un nom valide peut porter une valeur fabriquée |
| `M3-UNIT` | unité incohérente avec le capteur | une unité correcte ne garantit pas la provenance |
| `M3-TIMESTAMP` | horodatage invalide ou sans UTC | ne mesure pas la cohérence temporelle globale |
| `M3-GRID` | mesure hors de la grille de six heures | une mesure réelle tardive peut être signalée |
| `M3-MISSING` | valeur absente ou non numérique | une absence peut provenir d’un défaut réel |
| `M3-SENTINEL` | sentinelle `-999` | contrôle de qualité, pas de provenance |
| `M3-RANGE` | valeur hors plage pédagogique | les plages ne sont pas industrielles |
| `M3-PRECISION` | plus de deux décimales | une précision atypique reste un indice faible |

La prédiction `fabriquée` est émise dès qu’une règle est touchée. Cette
agrégation volontairement simple fournit le point de comparaison que les
modèles M4 doivent battre sans confondre qualité et provenance.
