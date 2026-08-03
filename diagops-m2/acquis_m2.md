# État du projet DiagOps — fin du module 2

## Résumé

DiagOps dispose désormais d'un diagnostic documenté et de traitements
reproductibles pour contrôler et préparer les trois tables ouvertes en M2.

La décision sur les données prend l'un des statuts suivants :

- **utilisable** ;
- **utilisable sous conditions** ;
- **non utilisable en l'état**.

Cette décision et ses raisons sont conservées dans le diagnostic M2.

## Sources comprises

Le projet connaît le rôle, la clé principale et les relations de :

- `equipment.csv` ;
- `events.csv` ;
- `maintenance_history.csv`.

Les relations entre `equipment_id` et `event_id` ont été contrôlées. Les
mesures capteurs ne sont pas encore ouvertes.

## Contrôles disponibles

Les contrôles retenus vérifient au minimum :

- la présence et la lisibilité des fichiers ;
- les colonnes obligatoires ;
- les types et catégories attendus ;
- l'unicité des identifiants ;
- les références entre les tables ;
- plusieurs règles métier sur les dates, durées, coûts et quantités ;
- la présence éventuelle d'informations personnelles dans les notes.

Les fichiers bruts restent inchangés.

## Sorties disponibles

Le travail M2 produit :

- trois tables préparées ;
- un fichier de quarantaine indiquant la règle, la valeur observée, la raison
  et la décision pour chaque anomalie ;
- un diagnostic répondant aux questions du brief ;
- des cas de vérification valides et invalides.

Les mêmes entrées et les mêmes règles permettent de reproduire les sorties.

## Couverture et erreurs M1

Le rapport présente des comptages par site, type d'équipement, criticité et
sévérité. Il examine également si les erreurs historiques de la référence M1
semblent plus fréquentes dans certaines catégories, sans affirmer de causalité
et sans conclure lorsque les effectifs sont trop faibles.

La référence M1 reste un historique déjà consulté ; elle n'est pas réutilisée
comme test inédit.

## Socle Atlas

Le notebook online atteste la capacité à :

- charger, inspecter et joindre des tables avec Pandas ;
- calculer mode, moyenne, médiane, quantiles, variance et écart-type ;
- examiner valeurs manquantes, doublons et valeurs atypiques ;
- produire et interpréter des graphiques Seaborn ;
- calculer une corrélation sans la confondre avec une causalité ;
- comparer normalisation et standardisation ;
- recommander des variables en indiquant leurs limites.

## Compétences acquises

- **C1 — niveau 1** : comprendre les données nécessaires, leurs clés, leurs
  relations et leurs limites ;
- **C2 — niveau 1** : repérer les informations personnelles, les défauts de
  couverture et les risques simples ;
- **C3 — niveau 1** : préparer les données avec des traitements vérifiés,
  reproductibles et documentés.

## Entrées pour le module 3

M3 repart de :

- le support d'audit et le diagnostic ;
- les contrôles, transformations et vérifications ;
- les données préparées et la quarantaine ;
- la décision sur l'état de préparation ;
- le notebook statistique et ses recommandations ;
- le journal de bord.

M3 ouvre les mesures capteurs et ajoute la dimension temporelle et
multi-source. Les règles M2 sont réutilisées ou modifiées de manière explicite.
