# Module 2 — Contrôler et préparer les données DiagOps

**Durée : 20 h — 14 h pour le brief présentiel et 6 h pour le brief online**  
**Présentiel : 7 h encadrées + 7 h de prolongement autonome**  
**Online : 3 h en classe virtuelle + 3 h de travail autonome**

## Positionnement

M2 aborde les données avec deux approches complémentaires :

- le présentiel propose une situation professionnelle ouverte : auditer les
  données, préparer une version exploitable et défendre une décision ;
- l'online couvre le programme Atlas avec un notebook d'exploration
  statistique.

Un état de référence M1 est fourni dans
`data_pack/2026-S1/reference_runs/m1_for_m2/`. M2 peut donc commencer même si
toutes les productions personnelles de M1 ne sont pas achevées.

## Architecture pédagogique

| Document | Finalité | Charge |
|---|---|---:|
| `brief1_module2.md` | auditer et préparer les données, puis rendre une décision argumentée | **14 h** |
| `brief1_module2_online.md` | explorer les données avec Pandas, Seaborn et les statistiques descriptives Atlas | **6 h** |
| `pour_aller_plus_loin_module2.md` | qualifier une nouvelle livraison et industrialiser ses contrôles avec GitHub Actions | **20 h facultatives** |

Les deux briefs sont autonomes. Les cinq apprenants reçoivent le même sujet et
les mêmes ressources, puis travaillent chacun dans leur propre environnement.

Le complément « Pour aller plus loin » s'adresse aux apprenants ayant terminé
les activités principales. Il approfondit C1 à C3 par la gestion d'une nouvelle
livraison, puis par son intégration dans le dépôt GitHub privé, sans ouvrir les
données capteurs ni modifier les prérequis de M3. La charge obligatoire du
module reste de 20 h ; la charge maximale avec ce complément est de 40 h.

## Compétences travaillées

| Compétence | Résultat attendu | Niveau | Preuves principales |
|---|---|---:|---|
| **C1** | Comprendre les fichiers, leurs clés, leurs relations et leurs limites | **N1** | contrôles de chargement, jointures, comptages et rapport |
| **C2** | Repérer les informations personnelles et les problèmes de couverture | **N1** | détection dans les notes, décisions de traitement, comptages par catégorie |
| **C3** | Préparer les données avec des traitements reproductibles et vérifiés | **N1** | notebook ou code, vérifications, données préparées et quarantaine |

## Entrées

- trois nouvelles tables dans `data_pack/2026-S1/` ;
- schéma, manifeste et data card à la racine de `data_pack/` ;
- référence commune M1 dans `data_pack/2026-S1/reference_runs/m1_for_m2/` ;
- starter de code et notebook dans `starter/` ;
- ressources M0–M1 déjà distribuées, lorsqu'elles sont utiles.

## Brief présentiel — pratique moderne

### Mission

Auditer les fichiers DiagOps, comprendre leurs limites, préparer une version
exploitable et décider s'ils peuvent être transmis à M3. Des contrôles
exécutables apportent la preuve des traitements, sans imposer une architecture
logicielle unique.

### Sorties attendues

- support d'audit : notebook, rapport ou combinaison des deux ;
- contrôles et transformations rejouables ;
- cas de vérification valides et invalides ;
- trois tables préparées ;
- quarantaine expliquant chaque rejet ;
- diagnostic répondant à dix questions et concluant par une décision :
  `utilisable`, `utilisable sous conditions` ou `non utilisable en l'état`.

L'analyse de la référence M1 utilise seulement des comptages et taux simples.
Il n'est demandé ni expertise statistique avancée, ni réentraînement du modèle,
ni documentation juridique exhaustive.

## Brief online — couverture Atlas

### Mission

Décrire le parc et les interventions dans un notebook, contrôler les jointures,
examiner la qualité des valeurs et recommander les variables utilisables pour
une future étude.

### Contenus couverts

- effectifs et fréquences ;
- mode, moyenne et médiane ;
- quartiles, déciles et centiles ;
- variance, écart-type et IQR ;
- valeurs manquantes, doublons et valeurs atypiques ;
- histogramme, boxplot, graphique catégoriel et nuage de points ;
- corrélation de Pearson ;
- encodage, normalisation et standardisation ;
- interprétation et recommandation métier.

### Sorties attendues

- notebook exécutable ;
- export HTML ;
- conclusion intégrée au notebook ;
- entrée dans le journal de bord.

## Complémentarité des briefs

| Attendu | Présentiel moderne | Online Atlas |
|---|---|---|
| Comprendre les sources | schémas, clés et relations expliqués et contrôlés | tables et unités d'observation expliquées |
| Qualité des données | diagnostic et contrôles rejouables | statistiques et visualisations |
| Valeurs incorrectes | quarantaine traçable | effet sur les résultats analysé |
| Données personnelles | détection et décision proportionnée | repérage éventuel dans l'exploration |
| Couverture | comptages simples et comparaison aux erreurs M1 | comparaison de populations |
| Reproductibilité | contrôles et transformations rejouables | notebook exécutable |
| Décision | utilisabilité pour M3 | variables recommandées ou écartées |

## Évaluation

- brief présentiel : **70 %** ;
- brief online : **30 %**.

| Dimension | Poids |
|---|---:|
| **C1 — compréhension des données et des relations** | 20 % |
| **C2 — informations personnelles, couverture et risques** | 20 % |
| **C3 — préparation reproductible et vérifications** | 35 % |
| **Reproductibilité et qualité des sorties** | 15 % |
| **Journal de bord et argumentation** | 10 % |

## Données ouvertes en M2

| Fichier | Volume | Rôle |
|---|---:|---|
| `equipment.csv` | 420 lignes | parc industriel |
| `events.csv` | 520 lignes | événements et sévérités |
| `maintenance_history.csv` | 1 800 lignes | interventions, durées et coûts |

Les fichiers contiennent des anomalies contrôlées. L'oracle formateur reste
hors du dossier distribué. Les mesures capteurs seront ouvertes en M3.

## Résultat de fin de module

À la fin de M2, DiagOps dispose d'un diagnostic, de contrôles et transformations
rejouables, de données préparées, d'une quarantaine et d'une décision
documentée. Le notebook Atlas apporte en parallèle une compréhension
statistique des variables et de leurs limites.

M3 pourra ajouter les mesures capteurs en réutilisant les contrôles établis ou
en documentant leur évolution.

## Approfondissement facultatif

Le lot `data_pack/2026-S1/m2_candidate_release/` permet de confronter les
contrôles M2 à une nouvelle livraison. L'apprenant compare les versions,
distingue erreur et évolution légitime, rend les règles configurables, vérifie
les non-régressions et produit une décision d'intégration reproductible. Un
laboratoire GitHub Actions permet ensuite d'exécuter les tests et la
qualification dans le dépôt privé, de publier un résumé et de conserver les
rapports comme artefacts.

Ce travail n'est pas utilisé pour établir la référence commune M2 vers M3.
