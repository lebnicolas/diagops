# Synthèse initiale des erreurs M1

## Périmètre

La référence porte sur **80 exemples de validation déjà consultés**,
représentant **80 rapports**,
**69 équipements renseignés**
et **74 événements renseignés**.
**7 lignes sans `equipment_id`** et
**6 sans `event_id`** font partie des cas
à examiner. La référence ne doit pas être présentée comme le test final inédit
de M1.

## Constats initiaux

- sorties LoRA conformes au schéma : **98.75%** ;
- macro-F1 `severity` : **0.795** ;
- erreurs exactes de sévérité : **12 cas** ;
- erreurs `requires_human_review` : **1 cas** ;
- dérive de latence p95 observée : **34.5%** par rapport à la baseline.

La confusion dominante est `critical → high` (7
cas). Ce constat motive une analyse de couverture, mais ne démontre pas que la
composition du corpus cause les erreurs.

## Limites à conserver dans M2

- run réalisé sur MPS en `float32`, et non sur le GPU CUDA commun ;
- baseline structurellement non conforme, donc comparaison de latence peu
  homogène ;
- validation déjà observée : aucune sélection de configuration ne doit être
  validée à nouveau sur ces mêmes exemples ;
- effectifs de sous-groupes à contrôler avant toute conclusion.
