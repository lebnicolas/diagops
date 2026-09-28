# Évaluation du modèle simple — M4

Ces deux fichiers constituent le jeu capteur gelé de M4. Ils sont disjoints des
lots de contrôle utilisés en M3.

| Fichier | Fenêtres | Lignes | Étiquette |
|---|---:|---:|---|
| `sensor_calibration.csv` | 30 | 900 | `provenance` visible |
| `sensor_test.csv` | 60 | 1 800 | oracle scellé côté formateur |

Une fenêtre contient 30 mesures consécutives. `window_id` doit être utilisé
pour empêcher qu’une même fenêtre soit répartie entre apprentissage et
évaluation. La cible distingue uniquement `réelle` et `fabriquée` ; elle ne
qualifie ni la qualité de la mesure, ni une anomalie métier, ni une panne future.

Le fichier de test peut être chargé et prédit après le gel du candidat. Il ne
sert jamais à régler les features, les seuils ou les hyperparamètres. Le
formateur restitue les métriques à partir de l’oracle non distribué.

Graine de génération : `20260831`. Les données sont synthétiques et réservées à
la formation.
