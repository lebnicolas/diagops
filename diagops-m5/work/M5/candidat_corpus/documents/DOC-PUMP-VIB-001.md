# Triage pédagogique — vibration des pompes

Statut : active, révision 2.

Les valeurs ci-dessous sont construites pour la formation DiagOps et ne sont
pas des seuils industriels.

## Règles de triage

- Une vibration supérieure ou égale à `4,0 mm/s` sur trois mesures consécutives
  déclenche une revue humaine prioritaire.
- Une valeur isolée ne suffit pas à conclure : vérifier l’unité, la régularité
  temporelle et les mesures voisines.
- À partir de `7,1 mm/s`, l’assistant recommande une inspection du palier et
  signale que la décision d’arrêt appartient au responsable habilité.
- Si le capteur est figé, si l’unité est incohérente ou si la série comporte un
  trou de plus de 24 heures, l’assistant refuse le diagnostic automatique.

- Une dérive lente de plus de `0,5 mm/s` sur quatorze jours est signalée même si
  aucune valeur individuelle ne dépasse le seuil.

Le système ne prédit pas une panne future à partir de ces seuls seuils.
