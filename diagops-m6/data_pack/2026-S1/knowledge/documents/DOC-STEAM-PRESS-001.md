# Triage pédagogique — pression du réseau vapeur

Statut : active, révision 1.

Ce document sert exclusivement au cas synthétique DiagOps.

## Règles de triage

Une baisse de pression supérieure à `0,8 bar` par rapport à la médiane des
vingt-quatre heures précédentes déclenche une vérification de fuite et de
capteur. La comparaison n’est valable que si l’unité est `bar` et si au moins
80 % des mesures attendues sont présentes.

Si les mesures sont exprimées en `kPa`, elles doivent être normalisées avant la
comparaison. En cas de couverture insuffisante ou d’unité incertaine, le
système refuse de conclure.
