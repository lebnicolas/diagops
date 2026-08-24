# DiagOps Data Pack — data card

Statut : support apprenant.

## Description

Le DiagOps Data Pack est un corpus synthetique fourni pour un parcours de
formation a la conception et l'implementation de solutions d'intelligence
artificielle appliquees a la maintenance industrielle.

Il contient des rapports techniciens, des donnees d'equipements, des mesures
capteurs, des historiques d'interventions, des evenements de maintenance, des
retours utilisateurs et un corpus image externe pour le travail multimodal.

## Origine

Les donnees textuelles, tabulaires et temporelles sont synthetiques.
Elles ont ete creees pour exercer des competences de cadrage, preparation,
entrainement, evaluation, integration, deploiement et amelioration continue.

Le corpus image M7 provient d'une source externe qui doit etre documentee dans
le manifeste avant distribution.

## Usages autorises

- Travaux de formation.
- Prototypage pedagogique.
- Evaluation de livrables dans le cadre du parcours.
- Demonstration de pipelines d'IA sur donnees controlees.

## Usages exclus

- Analyse metier reelle de maintenance industrielle.
- Entrainement d'un systeme de production.
- Comparaison scientifique entre modeles.
- Decision operationnelle ou de securite.

## Limites

Ce corpus ne constitue pas une source de connaissance metier. Les distributions,
formulations, incidents et relations entre sources sont construits pour le
parcours de formation.

Les resultats obtenus sur ce corpus ne doivent pas etre generalises a un site
industriel reel sans donnees reelles, expertise metier et validation dediee.

## Donnees annotees M1

Le pack inclut un sous-ensemble annote pour M1 :

- environ 400 exemples d'entrainement ;
- environ 100 exemples de test ;
- tache : transformer un rapport technicien en JSON DiagOps conforme.

Ces annotations servent d'intrants pedagogiques pour entrainer et evaluer le
modele M1.

## Tables ouvertes en M2

La revision `diagops-2026-S1-m2-v1` ajoute :

- 420 lignes d'inventaire d'equipements ;
- 520 lignes d'evenements ;
- 1 800 lignes d'historique de maintenance.

Ces tables couvrent les identifiants d'equipement et d'evenement references
par le corpus M1 et ajoutent des equipements sans annotation afin de travailler
la couverture.

Elles contiennent des anomalies pedagogiques controlees : doublons, valeurs
manquantes, categories heterogenes, incoherences temporelles, ruptures de
jointure, valeurs extremes et informations personnelles synthetiques dans
quelques notes libres. L'inventaire exact des anomalies n'est pas distribue aux
apprenants.

Les donnees capteurs ne sont pas ouvertes en M2. Elles restent reservees au
travail temporel et multi-source de M3.

## Table ouverte en M3

La révision `diagops-2026-S1-m3-v1` ajoute `2026-S1/sensors/sensor_readings.csv` :
50 401 mesures issues de 36 équipements instrumentés, au pas nominal de six
heures, du 2 janvier au 30 juin 2026.

Cette table est la première source temporelle du corpus. Elle n'a pas
d'identifiant de ligne : la clé logique est le triplet
`equipment_id + timestamp + sensor_name`.

Elle contient des anomalies pédagogiques contrôlées : doublons stricts,
doublons de clé à valeur divergente, horodatages hétérogènes, série décalée
dans le temps, changements d'unité, capteur figé, dérive lente, trou
d'échantillonnage, valeurs sentinelles, mesures hors période et mesures
rattachées à un équipement inconnu. Certaines variations sont réelles et ne
doivent pas être supprimées. L'inventaire exact des anomalies n'est pas
distribué aux apprenants.

Le parc instrumenté est volontairement partiel : 36 équipements sur 416, avec
une couverture inégale selon le site, le type d'équipement et la criticité.
Toute statistique calculée sur les capteurs porte donc sur une partie du parc.
La composition exacte du parc instrumenté n'est pas décrite ici : elle se
mesure à partir des données.

## Référence de continuité M2 vers M3

Le dossier `2026-S1/reference_runs/m2_for_m3/` fournit un état préparé commun
des trois tables ouvertes en M2 : tables préparées, quarantaine, registre des
règles appliquées, rapport de validation et décision de référence. Il permet de
démarrer M3 sans dépendre de l'achèvement des productions personnelles de M2.

Ce dossier n'est pas une correction du brief M2. Le registre est partiel,
plusieurs décisions restent discutables et aucune règle temporelle n'y figure.

## Livraison candidate facultative M2

La révision `diagops-2026-S1-m2-v2` ajoute le dossier
`2026-S1/m2_candidate_release/` pour le complément « Pour aller plus loin ».
Il contient un lot incrémental d'équipements, d'événements et d'interventions à
qualifier avant toute intégration.

Ce lot est volontairement distinct des tables publiées : il peut contenir des
erreurs, des évolutions de schéma, des catégories nouvelles et des changements
de qualité globale. Sa présence dans le data pack ne signifie pas qu'il est
accepté. Les notes de livraison décrivent uniquement les évolutions annoncées ;
l'inventaire formateur des écarts n'est pas distribué.

Ce complément ne contient aucune donnée capteur et n'anticipe pas le périmètre
temporel de M3.

## Référence de continuité M1 vers M2

Le dossier `2026-S1/reference_runs/m1_for_m2/` fournit un run M1 commun :
prédictions, métriques, matrice d'erreurs, limites et décision de référence.
Il permet de démarrer M2 sans dépendre de l'achèvement des productions
personnelles de M1. Il ne contient ni poids, ni checkpoint, ni correction de
M2.

## Precautions d'interpretation

Les effectifs et correlations sont construits a des fins pedagogiques. Ils ne
representent pas un parc industriel reel. Une relation observee ne doit pas
etre interpretee comme une causalite ni generalisee hors de ce corpus.
