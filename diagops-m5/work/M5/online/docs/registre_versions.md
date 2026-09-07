# Registre de versions — service de scoring

> État au **07/09/2026**. Étape 3 du brief online : relier code, modèle, données et résultats, et
> dire **ce qui déclenche une nouvelle version** et ce qui peut rester inchangé.

## Les unités

| Unité | Version | Empreinte | Source |
|---|---|---|---|
| **Code du service** | commit du dépôt `lebnicolas/diagops` | commit git (40 hex) | `online/src/` |
| **Modèle** | `detecteur-provenance-m4`, gelé le 31/08/2026 | `164d05b129ce5e41…` | `artefact/candidat_m4.joblib` |
| **Manifeste de gel** | `gel.json` | `7af52b98fc32d321…` | `artefact/gel.json` |
| **Extraction de features** | reprise de M4, chemin d'inférence | équivalence vérifiée à 10⁻⁹ | `src/features.py` |
| **Jeu d'évaluation** | `sensor_calibration.csv`, 30 fenêtres / 900 lignes | data pack `2026-S1` | `data_pack/2026-S1/model_eval/` |
| **Résultats de référence** | F1 hors pli 0,694 ± 0,068 | `gel.json` → `performance_attendue_calibration` | M4 |
| **Dépendances** | `requirements.lock`, scikit-learn 1.7.1 | fichier versionné | `online/requirements.lock` |
| **Image d'exécution** | `deploy-scoring` | `sha256:8d8ffaef4e5ebdb5ca9b725…` | build local du 07/09 |
| **Image de base** | `python:3.12.11-slim-bookworm` | `sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7` | Docker Hub |
| **Image Prometheus** | `prom/prometheus:v3.5.0` | `sha256:63805ebb8d2b3920190daf1cb14a60871b16fd38bed42b857a3182bc621f4996` | Docker Hub |

## Ce qui déclenche une nouvelle version

| Événement | Unités qui changent | Ce qui ne bouge pas | Réévaluation nécessaire ? |
|---|---|---|---|
| Correctif dans `src/app.py` | code, image | modèle, features, résultats | non — le contrat d'API est testé |
| Modification de `src/features.py` | code, **extraction**, image | modèle, jeu d'évaluation | **oui, impérativement** — l'équivalence avec M4 doit être reprouvée |
| Nouvel artefact `.joblib` | **modèle**, image, résultats de référence | code, features, jeu d'évaluation | **oui** — nouveau gel, nouvelles métriques de référence |
| Montée de scikit-learn | dépendances, image | modèle *(le fichier)*, code | **oui** — le comportement du même artefact peut changer |
| Montée de l'image de base | image | tout le reste | non, si les tests passent |
| Nouveau jeu d'évaluation | jeu d'évaluation, résultats | code, modèle | oui, pour recalculer la référence |

**Le cas qui piège** : monter scikit-learn ne change ni le modèle ni le code, et pourtant change
potentiellement les prédictions. C'est pourquoi la version de scikit-learn est traitée comme une
unité versionnée à part entière, vérifiée au démarrage et exposée en métrique — et non comme une
ligne parmi d'autres dans un fichier de dépendances.

**Le cas symétrique** : un correctif de l'API ne touche pas au modèle. Le réévaluer à chaque
commit userait la chaîne pour rien et finirait par faire ignorer ses résultats.

## Ce qui relie une prédiction à ses versions

Toute réponse de `/predict` porte `modele_checksum`. `/version` rend l'ensemble : date de gel,
commit du gel, algorithme, seuil, graine, checksum, nombre de features, version de scikit-learn
attendue **et** exécutée, et les résultats de référence.

Une trace de prédiction permet donc de retrouver l'artefact exact. C'est ce que le contrat de
versions du brief présentiel exige du service RAG, appliqué ici au modèle.

## Ce que ce registre ne couvre pas

L'artefact est **figé dans l'image**, pas monté en volume. Conséquence : il n'y a pas de « version
d'artefact » indépendante de la version d'image, et c'est délibéré — les séparer permettrait de
servir un autre modèle sous le même tag, ce qui est exactement l'attribution qu'on cherche à
rendre impossible.

Corollaire à assumer : **tout changement de modèle est un redéploiement**. Il n'y a pas de
rechargement à chaud, et il n'en est pas prévu.
