# Brief 1 — Module 3 — Online

## Persister les données DiagOps avec SQLAlchemy et Alembic

**Charge apprenant : 6 h — 3 h en classe virtuelle + 3 h de travail autonome**

## Situation

Les données DiagOps circulent aujourd'hui sous forme de fichiers. Chaque module
les relit, les contrôle et les recharge. L'arrivée des mesures capteurs rend
cette organisation coûteuse : le fichier est volumineux, les jointures sont
refaites à chaque exécution et rien ne garantit qu'une même mesure ne soit pas
chargée deux fois.

Vous devez modéliser les données DiagOps dans une base relationnelle, y charger
les tables déjà préparées, puis **faire évoluer le schéma par migration** pour
accueillir la nouvelle source, sans détruire ce qui existe.

Ce brief couvre le socle Atlas du module 3 : choix et documentation du modèle de
stockage, modèle relationnel, ORM SQLAlchemy, migrations Alembic et import d'un
nouveau jeu de données. Il est autonome et ne
dépend pas des productions du brief présentiel.

## Données disponibles

Le dossier `data_pack/` à la racine du dépôt contient :

- `2026-S1/reference_runs/m2_for_m3/processed/equipment.csv`,
  `events.csv` et `maintenance_history.csv` : tables préparées de référence,
  utilisées comme chargement initial ;
- `2026-S1/sensors/sensor_readings.csv` : nouvelle source à intégrer par
  migration ;
- `SCHEMA.md` : description des entités, des champs et des identifiants.

Vous pouvez utiliser vos propres tables préparées si elles sont disponibles, à
condition d'indiquer lesquelles vous chargez.

Le moteur par défaut est **SQLite**, suffisant pour ce brief et sans
installation. PostgreSQL est possible si votre environnement le permet ; le
travail attendu et les livrables sont identiques.

## Organisation du travail

Les cinq apprenants travaillent sur le même brief, chacun dans son propre
environnement. La classe virtuelle sert à clarifier le modèle relationnel,
vérifier les migrations et comparer les stratégies d'import.

## Travail attendu

Le rendu doit comporter cinq parties clairement identifiables.

### 1. Justifier le modèle de stockage

Avant de déclarer un modèle, dites pourquoi une base relationnelle convient à ces
données, et pourquoi une autre forme de stockage conviendrait moins bien.

Les mesures capteurs sont un cas discutable : volumétrie élevée, schéma stable,
écritures en lot, lectures par plage de temps et par équipement. Une base
documentaire, un stockage en fichiers colonnes ou une base orientée séries
temporelles sont des alternatives défendables. Les trois tables héritées de M2 ne
posent pas la même question : identifiants stables, relations obligatoires,
volumétrie faible.

Il n'est pas demandé d'installer une seconde base. Il est demandé de **comparer
au moins deux modèles de stockage sur des critères explicites** — requêtes
attendues, contraintes d'intégrité à faire respecter, volumétrie et croissance,
coût d'exploitation — puis de justifier celui que vous retenez. Un même projet
peut retenir deux modèles différents pour deux familles de données, à condition
de le dire.

### 2. Modéliser et créer la base

- déclarer les modèles SQLAlchemy des trois entités déjà connues :
  `equipment`, `events` et `maintenance_history` ;
- choisir et justifier les types de colonnes : identifiants, dates, montants,
  catégories, valeurs facultatives ;
- déclarer les clés primaires, les clés étrangères et les colonnes obligatoires ;
- créer la base à partir d'une première migration Alembic, et non par une
  création directe des tables.

### 3. Charger les tables préparées

- écrire un import qui lit les CSV préparés et insère les lignes ;
- respecter l'ordre imposé par les clés étrangères ;
- traiter explicitement les lignes refusées par la base plutôt que de les perdre ;
- compter les lignes lues, insérées et rejetées, et expliquer l'écart.

### 4. Faire évoluer le schéma pour les mesures capteurs

- écrire une migration qui ajoute la table des mesures **sans recréer la base** ;
- exprimer la clé logique `equipment_id + timestamp + sensor_name` par une
  contrainte d'unicité ;
- déclarer la clé étrangère vers `equipment` et décider du sort des mesures
  orphelines ;
- ajouter au moins un index justifié par une requête que vous exécutez
  réellement ;
- vérifier que `upgrade` puis `downgrade` fonctionnent tous les deux et
  documenter ce que `downgrade` détruit ;
- écrire un import de mesures **idempotent** : deux exécutions successives ne
  doivent pas doubler le contenu de la table.

### 5. Interroger et vérifier

Écrire et exécuter des requêtes qui répondent aux questions du brief, puis
conserver leurs résultats. Les requêtes peuvent être écrites en SQL ou avec
l'API SQLAlchemy, au choix, à condition d'être exécutables.

## Questions auxquelles votre rendu doit répondre

### Stockage et modèle

1. Quel modèle de stockage retenez-vous pour ces données, contre quelle
   alternative, et sur quels critères ?
2. Que représente une ligne dans chaque table, et quelle colonne en est la clé
   primaire ?
3. Quelles clés étrangères avez-vous déclarées et que se passe-t-il lorsqu'une
   ligne les viole ?
4. Quels types avez-vous retenus pour les dates, les montants et les catégories,
   et pourquoi ?

### Chargement

5. Combien de lignes sont lues, insérées et rejetées par table ? L'écart
   s'explique-t-il entièrement ?
6. Comment avez-vous traité les lignes rejetées à l'insertion ?

### Migration

7. Quelle migration crée la table des mesures, et que fait exactement son
   `downgrade` ?
8. Comment démontrez-vous que la migration ne détruit pas les données déjà
   chargées ?
9. Quelle contrainte exprime la clé logique des mesures, et qu'observe-t-on
   lorsqu'une ligne la viole ?

### Import incrémental

10. Que se passe-t-il exactement si vous relancez l'import des mesures ? Quelle
    stratégie assure l'idempotence, et quel en est le coût ?
11. Combien de mesures ont été refusées faute d'équipement correspondant ?

### Exploitation

12. Combien de mesures la base contient-elle par équipement et par capteur ?
13. Quelle est la première et la dernière mesure de chaque série ?
14. Quels équipements de `equipment` n'ont aucune mesure associée ?
15. Quel index avez-vous ajouté, pour quelle requête, et quel effet observez-vous
    sur son temps d'exécution ?
16. Qu'apporte la base par rapport à la lecture directe des CSV, et que
    coûte-t-elle ?

## Exigences minimales

Le rendu doit contenir au moins :

- une comparaison écrite d'au moins deux modèles de stockage, avec les critères
  retenus ;
- un fichier de configuration Alembic et un dossier de versions ;
- **deux migrations** : le schéma initial, puis l'ajout des mesures ;
- une contrainte d'unicité et au moins un index explicites ;
- un import rejouable des mesures ;
- cinq requêtes exécutées dont les résultats sont conservés.

## Livrables attendus

- la justification du modèle de stockage retenu, comparée à une alternative ;
- le code des modèles et de la session ;
- les migrations Alembic, `upgrade` et `downgrade` exécutables ;
- le ou les scripts d'import ;
- un notebook ou un `README` de démonstration montrant la séquence complète :
  migration, chargement, migration, import, requêtes ;
- les résultats des requêtes, sous forme de tableau ou d'export ;
- l'entrée M3 du journal de bord.

Le fichier de base de données lui-même n'est pas un livrable : il doit pouvoir
être reconstruit à partir de votre code.

## Critères de réussite

- le choix du modèle de stockage est justifié contre au moins une alternative,
  sur des critères explicites ;
- le modèle reprend les entités, leurs clés et leurs relations ;
- les types choisis sont justifiés ;
- la base est créée et modifiée par migration, jamais par recréation ;
- `upgrade` et `downgrade` sont tous les deux exécutables ;
- la clé logique des mesures est exprimée par une contrainte ;
- l'import est idempotent et le démontre ;
- les lignes rejetées sont comptées et expliquées ;
- l'index ajouté répond à une requête réelle et son effet est observé ;
- les requêtes répondent aux questions posées et sont reproductibles ;
- l'apport et le coût de la base sont discutés avec des éléments concrets.

## Critères bloquants

- base recréée à chaque exécution ou tables créées hors migration ;
- migration sans `downgrade` exécutable ;
- import non idempotent présenté comme incrémental ;
- modèle de stockage retenu sans comparaison ni critère ;
- clés étrangères absentes du modèle ;
- lignes rejetées silencieusement ;
- requêtes non exécutables ou résultats non reproductibles ;
- conclusion sur l'apport de la base sans mesure ni observation.
