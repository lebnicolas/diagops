# Brief 1 — Module 2 — Online

## Explorer les données de maintenance avec Pandas et Seaborn

**Charge apprenant : 6 h — 3 h en classe virtuelle + 3 h de travail autonome**

## Situation

Le responsable maintenance souhaite comprendre les données disponibles avant
de lancer une étude prédictive. Vous devez produire un notebook qui décrit le
parc, les événements et les interventions, puis recommander les variables qui
semblent utilisables.

Ce brief couvre le socle Atlas du module 2 : statistiques descriptives,
valeurs atypiques, corrélations, transformations usuelles, Pandas et Seaborn.
Il est autonome et ne dépend pas des productions du brief présentiel.

## Données disponibles

Le dossier `data_pack/` à la racine du dépôt contient :

- `2026-S1/equipment/equipment.csv` : équipements et caractéristiques du parc ;
- `2026-S1/events/events.csv` : incidents, observations et alertes ;
- `2026-S1/maintenance/maintenance_history.csv` : interventions, durées
  d'arrêt, temps de travail et coûts de pièces.

Ces fichiers contiennent volontairement des valeurs manquantes, des doublons
et des valeurs atypiques. Il faut d'abord les observer et les interpréter
avant de décider d'un traitement.

## Organisation du travail

Les cinq apprenants travaillent sur le même brief et le même notebook de
départ, chacun dans son propre environnement. La classe virtuelle permet de
clarifier les notions, vérifier les jointures et comparer les interprétations.
L'ordre des analyses n'est pas imposé.

## Travail attendu

Le notebook doit comporter quatre parties clairement identifiables.

### 1. Chargement et compréhension

- charger et inspecter les trois tables ;
- expliquer ce que représente une ligne dans chaque fichier ;
- identifier les colonnes, types et clés ;
- réaliser les jointures utiles ;
- contrôler le nombre de lignes avant et après chaque jointure.

### 2. Description statistique

- calculer les effectifs et fréquences utiles ;
- calculer mode, moyenne et médiane ;
- calculer quartiles, déciles et centiles pertinents ;
- mesurer variance, écart-type et distance interquartile ;
- comparer au moins deux populations, par exemple deux sites ou deux types
  d'équipement.

### 3. Qualité et relations entre variables

- mesurer les valeurs manquantes et rechercher les doublons ;
- repérer les valeurs atypiques avec l'IQR et l'écart à la moyenne ;
- expliquer si elles paraissent erronées, rares ou incertaines ;
- produire une matrice de corrélation de Pearson ;
- vérifier visuellement certaines relations ;
- montrer l'effet d'une valeur extrême sur au moins un résultat ;
- comparer normalisation et standardisation sur deux variables numériques ;
- encoder une variable catégorielle avec une méthode justifiée.

### 4. Recommandation

Classez les variables en trois catégories :

- utilisables en l'état ;
- à nettoyer ou à mieux documenter ;
- à écarter provisoirement.

Justifiez ce classement à partir des calculs et graphiques du notebook.

## Questions auxquelles le notebook doit répondre

### Comprendre les fichiers

1. Que représente une ligne dans chaque fichier ?
2. Quelles colonnes permettent de relier les fichiers ?
3. Combien de lignes obtient-on après chaque jointure ? Une jointure a-t-elle
   créé des doublons ou écarté des observations ?

### Décrire le parc et les interventions

4. Combien d'équipements existe-t-il par site, type et niveau de criticité ?
5. Quel est l'âge approximatif des équipements ? Certaines catégories sont-elles
   très peu représentées ?
6. Quelle est la durée d'arrêt habituelle ? La moyenne et la médiane donnent-elles
   la même image ?
7. Que montrent les quartiles et les déciles sur les interventions les plus
   longues ?
8. Comment varient le temps de travail et le coût des pièces selon le type
   d'intervention ?

### Examiner la qualité

9. Quelles colonnes contiennent des valeurs manquantes ?
10. Quelles valeurs paraissent impossibles ou inhabituelles ?
11. Faut-il les supprimer, les corriger ou les conserver ? Quel effet le choix
    retenu a-t-il sur les statistiques ?

### Étudier les relations

12. La durée d'arrêt semble-t-elle liée au temps de travail ou au coût des
    pièces ?
13. Cette relation reste-t-elle visible après le traitement justifié d'une
    valeur extrême ?
14. Une corrélation observée suffit-elle à expliquer la durée d'arrêt ?

### Préparer une utilisation future

15. Quel est l'effet de la normalisation et de la standardisation sur les
    variables numériques choisies ?
16. Quelles variables recommandez-vous, écartez-vous ou placez-vous sous
    surveillance pour une future modélisation ?

## Graphiques minimums

Le notebook doit contenir au moins :

- un histogramme ;
- un boxplot ;
- un graphique comparant des catégories ;
- un nuage de points ;
- une matrice de corrélation.

Chaque graphique doit répondre à une question, avoir un titre et être suivi
d'une courte interprétation.

## Livrables attendus

- notebook `m2_statistiques_atlas.ipynb` complété ;
- export HTML du notebook ;
- entrée M2 dans le journal de bord.

La conclusion se trouve dans le notebook : aucun rapport séparé n'est demandé.
Le notebook doit être exécutable de bout en bout depuis les fichiers reçus et
utiliser des chemins relatifs ou configurables.

## Critères de réussite

- les trois tables et leurs clés sont comprises ;
- les jointures sont contrôlées ;
- les notions Atlas demandées sont calculées correctement ;
- les graphiques sont lisibles et interprétés ;
- les valeurs manquantes, doublons et valeurs atypiques font l'objet d'une
  décision argumentée ;
- corrélation et causalité ne sont pas confondues ;
- normalisation et standardisation sont comparées ;
- la recommandation finale est reliée aux résultats obtenus ;
- le notebook est lisible et exécutable.

## Critères bloquants

- notebook non exécutable ;
- suppression de lignes sans justification ni état avant/après ;
- jointure dont l'effet sur le nombre de lignes n'est pas contrôlé ;
- corrélation présentée comme une causalité ;
- graphique sans interprétation ;
- conclusion sans lien avec les calculs.
