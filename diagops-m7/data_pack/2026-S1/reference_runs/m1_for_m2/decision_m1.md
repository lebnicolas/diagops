# Décision de référence M1

**Décision : ne pas promouvoir en l'état.**

Le candidat améliore fortement le score composite et respecte plusieurs
garde-fous, mais il ne satisfait pas tous les seuils annoncés : conformité au
schéma inférieure à 100 %, macro-F1 `severity` inférieure à 0,80 et dérive de
latence p95 supérieure à 20 %. Le pilote n'a par ailleurs pas été exécuté sur
le backend CUDA commun prévu.

Cette décision sert uniquement à assurer la continuité pédagogique. M2 doit
examiner l'état des données et les associations possibles avec les erreurs ;
il ne doit ni réentraîner ni promouvoir le modèle à partir de cette validation
déjà consultée.
