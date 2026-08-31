# État du projet DiagOps — fin du module 3

## Résumé

DiagOps ne dépend plus d'un traitement table par table. La préparation des
données est devenue une pipeline multi-source dont l'évolution est tracée, et
les données sont désormais persistables dans une base dont le schéma se fait
migrer plutôt que recréer.

La décision sur l'ensemble multi-source prend l'un des statuts suivants :

- **utilisable** ;
- **utilisable sous conditions** ;
- **non utilisable en l'état**.

Cette décision, ses conditions et le coût de rejeu de la pipeline sont conservés
dans le diagnostic M3.

## Sources comprises

Le projet connaît le rôle, la clé et les relations de :

- `equipment.csv` ;
- `events.csv` ;
- `maintenance_history.csv` ;
- `sensor_readings.csv`.

Pour la source capteurs, le projet sait que la clé d'une mesure est le triplet
`equipment_id + timestamp + sensor_name`, qu'aucun identifiant de ligne n'est
fourni, que la période et le pas d'échantillonnage doivent être mesurés plutôt
que supposés, et que le parc instrumenté ne couvre qu'une partie du parc décrit
par `equipment.csv`.

## Contrôles disponibles

Aux contrôles hérités de M2 s'ajoutent des contrôles propres à une série
temporelle. Ils vérifient au minimum :

- l'unicité de la clé logique d'une mesure ;
- la distinction entre doublon strict et doublon de clé à valeur divergente ;
- l'homogénéité du format d'horodatage et l'hypothèse de fuseau retenue ;
- la position des mesures dans la période annoncée ;
- la régularité du pas d'échantillonnage et la localisation des interruptions ;
- la cohérence entre nom de capteur, unité et ordre de grandeur ;
- les plages physiques plausibles et les valeurs sentinelles ;
- les comportements de capteur : valeur figée, dérive lente, saut brutal ;
- l'existence de l'équipement mesuré.

Les fichiers bruts restent inchangés.

## Évolution tracée des règles

Un registre de règles indique, pour chaque règle, son identifiant, sa source —
M2 ou M3 —, son statut — conservée, modifiée, étendue ou abandonnée — et sa
justification.

Une non-régression sur les trois tables ouvertes en M2 est démontrée : leurs
résultats de préparation n'ont pas changé sans raison énoncée.

La quarantaine est unifiée. Les rejets des quatre sources partagent le même
format et le même vocabulaire de décision.

## Documentation disponible

Le projet dispose d'une description du flux de traitement, de la source reçue
jusqu'à la sortie exploitable, indiquant les étapes, ce qui est écrit à chacune,
les points où une ligne peut être écartée et la commande qui rejoue l'ensemble.

Le cycle de vie du jeu de données est renseigné : origine, fréquence de
livraison, format et mode d'accès, durée et forme de conservation, accès aux
données préparées, comportement à l'arrivée d'une nouvelle période et condition
de fin d'utilisabilité.

La description du jeu de données a été mise à jour après l'ajout de la source :
ce qu'il contient, ce qu'il ne contient pas, ce qu'il permet de conclure. Les
destinataires de ces documents sont nommés.

L'existence, la disponibilité et les conditions d'accès de la source capteurs
sont vérifiées. Les équipements qu'elle ne couvre pas font l'objet d'une solution
de remplacement examinée, retenue ou écartée avec sa raison.

## Sorties disponibles

Le travail M3 produit :

- une table de mesures préparée ;
- au moins une table d'agrégats à un grain documenté ;
- une table de rapprochement entre mesures et événements, avec sa fenêtre, son
  sens et sa cardinalité ;
- une quarantaine unifiée ;
- un registre de règles versionné ;
- un diagnostic multi-source répondant aux questions du brief ;
- une note de couverture et de risques.

Les mêmes entrées et les mêmes règles permettent de reproduire ces sorties.

## Couverture et périmètre de validité

Le rapport chiffre la part du parc instrumentée, les sites, types et criticités
absents ou sous-représentés, et la part des événements réellement rapprochables
de mesures.

Toute conclusion tirée des capteurs est accompagnée de son périmètre de
validité. Une observation faite sur le parc instrumenté n'est pas présentée
comme valable pour l'ensemble du parc.

## Risques examinés

- une mesure horodatée décrit aussi le rythme de travail autour d'un
  équipement : le croisement avec un site, un horaire et un bon de travail peut
  rendre une personne identifiable ;
- le volume conservé résulte d'un choix : une règle de conservation
  proportionnée au besoin est formulée, entre mesures brutes et agrégats ;
- une variation atypique n'est pas supprimée sans examen : erreur, mesure réelle
  et cas indécidable sont distingués.

## Socle Atlas

Le rendu online atteste la capacité à :

- déclarer un modèle relationnel avec SQLAlchemy : entités, types, clés
  primaires, clés étrangères et contraintes ;
- créer et faire évoluer un schéma avec Alembic, `upgrade` et `downgrade`
  compris ;
- exprimer par une contrainte une clé logique non fournie par la source ;
- importer un nouveau jeu de données de manière idempotente ;
- compter et expliquer les lignes rejetées à l'insertion ;
- justifier un index par une requête réellement exécutée ;
- écrire des requêtes d'agrégation et de contrôle ;
- comparer la lecture de fichiers et la persistance en base, apport et coût
  compris.

## Compétences acquises

- **C1 — niveau 1 consolidé** : cadrer une source d'un type nouveau, en mesurer
  la couverture et en énoncer les limites ;
- **C2 — niveau 2** : identifier les risques introduits par une source
  temporelle, appliquer la minimisation au volume conservé et annoncer un
  périmètre de validité ;
- **C3 — niveau 2** : faire évoluer une préparation de données et un schéma sans
  rupture, avec traçabilité et non-régression.

## Entrées pour le module 4

M4 repart de :

- la pipeline multi-source et son registre de règles ;
- la table de mesures préparée, les agrégats et le rapprochement temporel ;
- la quarantaine unifiée et le diagnostic ;
- la décision de transmission et ses conditions ;
- la base relationnelle et ses migrations ;
- le journal de bord.

M4 constitue des jeux d'évaluation, compare des approches de modélisation et
consolide l'analyse des risques. Les conditions et limites énoncées en M3 sont
reprises telles quelles ou explicitement levées.

Un sujet est explicitement reporté :

- **l'analyse d'un nouveau besoin métier** sur le jeu de données d'un projet
  existant, traitée en M4 avec le cadrage du choix de modèle.

**Les techniques de génération et d'augmentation de données** — données
synthétiques, augmentation, confidentialité différentielle, biais et risques
résiduels — étaient initialement reportées en M6. Elles sont traitées en M3, au
brief 2. La raison est de portée : ces techniques répondent à la question « que
permet ce jeu de données, et que faut-il fabriquer pour la suite », qui se pose
avant la modélisation, pas après. Les reporter à la boucle d'amélioration
continue revenait à faire entrer M4 sans savoir ce que le jeu de données
autorise.

Ce que M3 transmet donc à M4, en plus des livrables ci-dessus :

- un jeu de données étiqueté en provenance — `réelle`, `synthétique`,
  `augmentée` — avec le procédé qui a produit chaque ligne ;
- une capacité chiffrée par segment, et la liste des questions que le jeu de
  données ne permet pas de trancher ;
- trois biais nommés, chiffrés, avec leur risque résiduel ;
- une **base de comparaison par règles** : les comptages de détection obtenus
  sans modèle. C'est le point de départ que le modèle de M4 doit battre, et la
  raison pour laquelle sa performance devra être analysée, pas seulement
  affichée.

Le corpus DiagOps est lui-même synthétique : sa data card indique ce que cela
interdit de conclure.
