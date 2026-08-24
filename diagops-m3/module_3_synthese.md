# Module 3 — Faire évoluer la pipeline DiagOps pour une nouvelle source

**Durée : 20 h — 14 h pour le brief présentiel et 6 h pour le brief online**  
**Présentiel : 7 h encadrées + 7 h de prolongement autonome**  
**Online : 3 h en classe virtuelle + 3 h de travail autonome**

## Positionnement

M3 ouvre la première source temporelle du corpus DiagOps et aborde son
intégration avec deux approches complémentaires. Le module couvre les trois
objectifs terminaux du programme : ajouter une source à la pipeline et lui
appliquer les traitements, faire évoluer la base de données pour l'accueillir,
et documenter le flux et le cycle de vie qui en résultent. L'analyse d'un
nouveau besoin métier sur un projet existant est reprise en M4, avec le cadrage
du choix de modèle.

- le présentiel traite l'ingestion multi-source comme une situation
  professionnelle : cadrer une source inconnue, ajouter des règles temporelles
  sans casser l'acquis de M2, relier les mesures aux événements et décider ;
- l'online couvre le programme Atlas en persistant les données dans une base
  relationnelle et en faisant évoluer son schéma par migration.

Les deux briefs traitent la même question — comment accueillir une nouvelle
source sans repartir de zéro — par deux moyens différents : le registre de
règles d'un côté, la migration de schéma de l'autre.

Un état préparé de référence M2 est fourni dans
`data_pack/2026-S1/reference_runs/m2_for_m3/`. M3 peut donc commencer même si
toutes les productions personnelles de M2 ne sont pas achevées.

## Architecture pédagogique

| Document | Finalité | Charge |
|---|---|---:|
| `brief1_module3.md` | intégrer la source capteurs, faire évoluer les règles et décider | **14 h** |
| `brief1_module3_online.md` | modéliser, migrer et importer avec SQLAlchemy et Alembic | **6 h** |

Les deux briefs sont autonomes. Les cinq apprenants reçoivent le même sujet et
les mêmes ressources, puis travaillent chacun dans leur propre environnement.

Aucun complément facultatif n'est publié pour M3 : la charge du module est de
20 h.

## Compétences travaillées

| Compétence | Résultat attendu | Niveau | Preuves principales |
|---|---|---:|---|
| **C1** | Cadrer une source inconnue : grain, clé, période, couverture et limites | **N1 consolidé** | inventaire des séries, période et pas mesurés, chiffrage de la couverture instrumentale |
| **C2** | Identifier les risques introduits par une source temporelle et y répondre de manière proportionnée | **N2** | note de couverture et de risques, règle de conservation, périmètre de validité annoncé |
| **C3** | Faire évoluer une préparation de données sans rupture | **N2** | registre de règles versionné, règles temporelles, non-régression M2, quarantaine unifiée, migration réversible |

M2 laissait les trois compétences au niveau 1. M3 consolide C1 sur une source
d'un type nouveau, et porte C2 et C3 au niveau 2. M4 amènera C1 au niveau 2 avec
la constitution de jeux d'évaluation, et C2 au niveau 3 avec l'analyse consolidée
des risques.

## Matrice de couverture

| Attendu | Programme Atlas | Mise à jour 2026 | Compétence | Preuve attendue |
|---|---|---|---|---|
| Modèle relationnel et clés | modèles SQLAlchemy, types, clés primaires et étrangères | contrainte exprimant une clé logique non fournie par la source | C1, C3 | modèles exécutables et contraintes déclarées |
| Évolution de schéma | migrations Alembic, `upgrade` et `downgrade` | évolution tracée d'un registre de règles en parallèle du schéma | C3 | deux migrations réversibles et registre versionné |
| Ingestion d'un nouveau jeu de données | import en base, lignes rejetées comptées | idempotence démontrée et coût de rejeu mesuré | C3 | import rejouable et comptages avant/après |
| Qualité d'une série temporelle | valeurs manquantes et doublons | clé logique, régularité d'échantillonnage, capteur figé, dérive, unité incohérente | C3 | contrôles quantifiés et quarantaine unifiée |
| Rapprochement de sources | jointures et cardinalités | rapprochement par fenêtre temporelle, lignes non appariées | C1, C3 | table de rapprochement et contrôle de cardinalité |
| Disponibilité des sources | identification de sources pertinentes et accessibles | conditions de livraison, couverture partielle et solution de remplacement | C1 | vérification d'existence, d'accès et alternatives examinées |
| Documentation | datasheet, flux de traitement, cycle de vie de la donnée | mise à jour à chaque source ajoutée et destinataires nommés | C1, C3 | flux documenté et cycle de vie renseigné |
| Couverture et représentativité | comparaison de populations | couverture instrumentale partielle et périmètre de validité | C1, C2 | comptages par site, type et criticité |
| Risques et minimisation | données personnelles dans les champs libres | traçabilité indirecte de l'activité humaine, règle de conservation du volume | C2 | note de risques et décision argumentée |
| Décision | recommandation de variables | décision de transmission à M4 avec conditions et coût | C1, C2, C3 | diagnostic conclu et daté |

## Entrées

- `data_pack/2026-S1/sensors/sensor_readings.csv` : nouvelle source ouverte ;
- les trois tables M2 dans `data_pack/2026-S1/` ;
- l'état préparé de référence dans
  `data_pack/2026-S1/reference_runs/m2_for_m3/` : tables préparées, quarantaine,
  registre des règles et décision ;
- schéma, manifeste et data card à la racine de `data_pack/` ;
- starter de code et notebooks dans `starter/` ;
- ressources M0–M2 déjà distribuées, lorsqu'elles sont utiles.

## Brief présentiel — pratique moderne

### Mission

Intégrer la source capteurs à la pipeline DiagOps, la relier aux événements
existants, faire évoluer les règles sans casser l'acquis de M2, et décider ce qui
peut être transmis à M4.

### Sorties attendues

- registre de règles versionné, distinguant règles héritées et règles nouvelles ;
- pipeline multi-source rejouable ;
- table de mesures préparée ;
- table d'agrégats et table de rapprochement mesures ↔ événements ;
- quarantaine unifiée sur les quatre sources ;
- cas de vérification valides et invalides, dont une non-régression M2 ;
- documentation du flux de traitement et du cycle de vie du jeu de données ;
- diagnostic répondant à douze questions et concluant par une décision :
  `utilisable`, `utilisable sous conditions` ou `non utilisable en l'état` ;
- note de couverture et de risques.

La difficulté principale n'est pas le volume mais l'absence de garanties : la
source n'a pas d'identifiant de ligne, son horodatage n'est pas homogène et ses
unités ne sont pas fiables. Il n'est demandé ni détection automatique d'anomalie,
ni modèle prédictif, ni infrastructure de données.

## Brief online — couverture Atlas

### Mission

Modéliser les données DiagOps dans une base relationnelle, y charger les tables
préparées, puis faire évoluer le schéma par migration pour accueillir les mesures
capteurs et les importer sans duplication.

### Contenus couverts

- choix et justification du modèle de stockage face à une alternative ;
- modèle relationnel : entités, clés primaires, clés étrangères, contraintes ;
- déclaration ORM avec SQLAlchemy et choix de types ;
- session, transaction et traitement des erreurs d'insertion ;
- migrations Alembic : révision initiale, révision d'ajout, `downgrade` ;
- contrainte d'unicité exprimant une clé logique ;
- index et effet observé sur une requête ;
- import d'un nouveau jeu de données et idempotence ;
- requêtes d'agrégation et de contrôle ;
- comparaison entre lecture de fichiers et base de données.

### Sorties attendues

- modèles, migrations et import exécutables ;
- démonstration de la séquence complète ;
- résultats de cinq requêtes au moins ;
- entrée dans le journal de bord.

## Complémentarité des briefs

| Attendu | Présentiel moderne | Online Atlas |
|---|---|---|
| Accueillir une source nouvelle | cadrage, règles temporelles et quarantaine | migration de schéma et contrainte d'unicité |
| Ne pas casser l'existant | non-régression sur les tables M2 | `downgrade` exécutable et données préservées |
| Éviter les doublons | arbitrage des doublons de clé divergents | import idempotent |
| Relier les sources | rapprochement par fenêtre temporelle | clés étrangères et jointures SQL |
| Volumétrie | coût de rejeu de la pipeline | index et effet mesuré |
| Documenter | flux de traitement et cycle de vie de la donnée | modèle de stockage justifié |
| Décision | transmission à M4 sous conditions | apport et coût de la persistance |

## Évaluation

- brief présentiel : **70 %** ;
- brief online : **30 %**.

| Dimension | Poids |
|---|---:|
| **C1 — cadrage de la source et couverture** | 20 % |
| **C2 — risques, minimisation et périmètre de validité** | 20 % |
| **C3 — évolution de la pipeline sans rupture** | 35 % |
| **Reproductibilité et qualité des sorties** | 15 % |
| **Journal de bord et argumentation** | 10 % |

## Données ouvertes en M3

| Fichier | Volume | Rôle |
|---|---:|---|
| `sensor_readings.csv` | 50 401 lignes | mesures temporelles de 36 équipements instrumentés |

La table couvre le 2 janvier au 30 juin 2026 au pas nominal de six heures. Elle
contient des anomalies contrôlées et des variations réelles. L'oracle formateur
reste hors du dossier distribué.

Les tables M2 restent ouvertes et inchangées. Aucune donnée de la période
`2026-S2` n'est ouverte en M3.

## Résultat de fin de module

À la fin de M3, DiagOps dispose d'une pipeline multi-source dont l'évolution est
tracée, d'une table de mesures préparée, d'un rapprochement documenté entre
mesures et événements, d'une quarantaine unifiée et d'une décision de
transmission. La base relationnelle construite en online fournit un support
persistant réutilisable pour les modules suivants.

M4 pourra constituer des jeux d'évaluation et travailler le choix de modèle en
s'appuyant sur ces sources rapprochées, à condition de reprendre les conditions
et les limites énoncées ici.
