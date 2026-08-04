# Journal de bord — M2

Module 2 — auditer et préparer les données DiagOps. Session du 03/08/2026.

Deux volets : le **présentiel** (auditer, préparer, décider) et le **distanciel**
(statistiques descriptives avec Pandas et Seaborn). Le second est autonome — il
repart des fichiers reçus, pas des tables préparées.

## Reprise M0–M1

- **Référence commune M1 consultée** :
  `data_pack/2026-S1/reference_runs/m1_for_m2/` — matrice d'erreurs (80 cas),
  prédictions baseline et LoRA, métriques, `decision_m1.md`. Le dossier garantit
  un point de départ identique pour tous, indépendamment des productions M1
  personnelles.

- **Comparaison avec ma production M1** : non effectuée. Le module 1 a été clos
  sans les phases A7 (revue contradictoire) et C. Le brief M2 prévoit ce cas :
  les analyses s'appuient sur la référence commune. Aucune dépendance à mes
  résultats M1.

- **Décisions structurantes** :
  - registre de règles **écrit avant toute mesure**, gelé par commit ;
  - contrôles génériques paramétrés plutôt qu'une fonction par règle ;
  - séparation stricte mesure / correction : l'audit ne transforme rien ;
  - toute révision de règle postérieure à une mesure est datée et justifiée
    (`rules.REVISIONS`).

- **Preuves conservées** : `output/check_results.csv`, `output/quarantine.csv`,
  `output/transformation_log.csv`, `output/processed/`, le registre versionné,
  58 tests, et l'historique git.

- **Limites encore ouvertes** : 3 références orphelines, 595 coûts de pièces
  sans pièce déclarée, 12 lignes en quarantaine, 41 équipements sans activité.

## Hypothèses formulées avant analyse

| Date | Hypothèse | Mesure prévue | Résultat | Décision |
|---|---|---|---|---|
| 03/08 | Les identifiants dupliqués porteront des contenus divergents et exigeront un arbitrage | Croiser `KEY-002` (clé dupliquée) et `KEY-003` (ligne entière dupliquée) | **Réfutée** — les 26 clés dupliquées sont toutes des lignes intégralement identiques | Déduplication automatique, aucun arbitrage |
| 03/08 | Un coût de pièces sans pièce remplacée est une incohérence métier (`MNT-VAL-007`) | Compter les cas et les répartir par `intervention_type` | **Réfutée** — 595 cas sur 1 800, répartis uniformément sur les 5 types | Règle passée en signalement, question au métier |
| 03/08 | Les valeurs hors énumération sont des anomalies de saisie isolées (`EVT-CAT-001`) | Compter par valeur | **Partiellement réfutée** — 49 `alert` réguliers contre 1 `Incident ` isolé | Règle scindée en trois : isolée / récurrente / casse |
| 03/08 | Les erreurs M1 se concentrent sur certaines catégories d'équipement | Taux d'erreur par site, type, criticité, sévérité | **Non concluant** — un seul groupe dépasse 30 observations par découpage | Aucune conclusion ; hypothèse reportée |
| 03/08 | La détection de données personnelles par motifs laissera passer des cas | Énumérer toutes les valeurs distinctes du champ | **Confirmée** — `Nadia B.` échappe à tout motif | Masquage du champ entier, pas par fragment |
| 03/08 | *(distanciel)* La durée d'arrêt n'est corrélée à aucune autre variable — corrélation max 0,043 | Recalculer la matrice de Pearson après retrait des valeurs impossibles | **Réfutée** — la corrélation avec `labor_hours` passe de −0,002 à **0,848** | Deux lignes sur 1 800 masquaient la relation la plus forte du jeu ; conclusion précédente annulée |
| 03/08 | *(distanciel)* La règle des 3 écarts-types et l'IQR signaleront les mêmes valeurs | Appliquer les deux méthodes à `downtime_minutes` | **Réfutée** — 5 valeurs pour l'IQR, **1 seule** pour les 3σ | L'IQR retenu comme méthode de détection ; la règle des 3σ documentée comme inopérante ici |

## Activités et preuves produites

| Date | Activité | Artefact ou commit | Revue reçue |
|---|---|---|---|
| 03/08 | Espace de travail, venv, correctif du test `test_io.py` (CRLF sous Windows) | `dbff8e4` | — |
| 03/08 | Cartographie des sources, clés et relations | `diagnostic_donnees.md` §1 | — |
| 03/08 | Registre de 54 règles écrit **avant** mesure | `rules.py`, `regles_qualite_m2.md`, `dbff8e4` | — |
| 03/08 | 18 contrôles génériques + 35 tests | `checks.py`, `audit.py`, `dbff8e4` | — |
| 03/08 | Première mesure — 26 règles en échec | `check_results.csv` | — |
| 03/08 | Révision 1 : `MNT-VAL-007` et scission `EVT-CAT-001` | `rules.REVISIONS`, `dbff8e4` | — |
| 03/08 | Axe 3 — données personnelles, masquage | `prepare.py`, `8d03ff8` | validation utilisateur du traitement |
| 03/08 | Axe 3 — couverture et concentration des erreurs M1 | `coverage.py`, `8d03ff8` | — |
| 03/08 | Révision 2 : équivalences déclarées `Pump `, `Correctif` | `rules.REVISIONS` | décision utilisateur |
| 03/08 | Corrections certaines, export, pipeline rejouable | `run_audit_m2.py`, `output/`, `8d03ff8` | — |
| 03/08 | Révision 3 : import des domaines depuis `contracts/schemas.py` | `rules.REVISIONS` | — |
| 03/08 | Diagnostic, note de décision, journal | `docs/` | — |
| 03/08 | Site didactique — 13 étapes | `docs/web/` | — |
| 03/08 | Jeu supervisé pour la prédiction de gravité | `dataset.py`, `output/training/`, `fcb87be` | — |
| 03/08 | **Distanciel** — notebook statistiques Atlas | `notebooks/m2_statistiques_atlas.ipynb` + export HTML | — |

**Revue contradictoire externe : non obtenue.** Le brief prévoit des échanges en
séance sans constitution de groupes. Les objections consignées ici proviennent
de mes propres contrôles ; c'est une limite de valeur probante à assumer, une
auto-revue n'ayant pas le poids d'un relecteur tiers.

## Décisions

### Décision 1 — traitement des données personnelles

- **Options considérées** : conserver en signalant · masquer le champ et garder
  la ligne · écarter les lignes.
- **Preuve déterminante** : le champ ne porte que 7 valeurs distinctes sur
  1 800 lignes, donc la vérification humaine est **exhaustive** et non
  échantillonnée. Et `Nadia B.`, sans civilité, n'est détecté par aucun motif —
  un masquage partiel aurait laissé un nom en clair dans une ligne paraissant
  assainie.
- **Choix retenu** : masquer le champ **entier**, conserver les 1 800 lignes.
  La valeur d'origine reste dans la quarantaine et le journal, qui sont des
  artefacts d'audit.
- **Limites et réversibilité** : entièrement réversible, l'état initial est
  tracé. L'exhaustivité de la vérification tient à la nature gabarit du champ ;
  elle ne serait pas transposable à du texte libre réel.

### Décision 2 — traitement des valeurs extrêmes (distanciel)

- **Options considérées** : tout conserver · écarter les 5 valeurs signalées par
  l'IQR · n'écarter que celles dont l'impossibilité est démontrée.
- **Preuve déterminante** : la confrontation aux horodatages. `MNT-2026S1-0206`
  déclare 99 999 minutes alors que `opened_at` et `closed_at` sont séparés de
  69 minutes ; `MNT-2026S1-0041` déclare une durée négative. Les 3 autres
  valeurs signalées (380 à 480 min) n'ont **aucune** contradiction interne : ce
  sont des interventions longues, pas des erreurs.
- **Choix retenu** : écarter **2 lignes sur 1 800**, conserver les 3 autres.
  Effet mesuré et publié — moyenne −26 %, écart-type −97 %, médiane inchangée.
- **Limites et réversibilité** : réversible, le retrait est un filtre appliqué à
  une copie. Le seuil de Tukey (1,5 × IQR) est une convention, pas une preuve :
  il **signale**, il ne qualifie pas. C'est la confrontation à une autre colonne
  qui a tranché, pas la statistique.

### Décision 3 — statut des données pour M3

- **Options considérées** : utilisables · utilisables sous conditions · non
  utilisables en l'état.
- **Preuve déterminante** : les 26 identifiants dupliqués sont tous des lignes
  intégralement dupliquées. Après préparation, 3 anomalies bloquantes
  subsistent sur 2 727 lignes.
- **Choix retenu** : **utilisables sous conditions**, quatre conditions
  détaillées dans `decision_preparation.md`.
- **Limites et réversibilité** : les fichiers reçus sont intacts, la chaîne se
  rejoue par une commande. La décision porte sur l'état des données, pas sur le
  modèle M1.

## Bilan M2

### Ce que je sais démontrer

- **Les fichiers reçus n'ont pas été modifiés** — empreintes SHA-256 comparées
  avant et après par le script lui-même.
- **Chaque anomalie retenue est chiffrée et localisée** — règle, colonne,
  identifiants, valeur observée.
- **Chaque correction est justifiée, tracée et réversible** — 18 lignes sur
  2 740, aucune suppression silencieuse.
- **Les contrôles se rejouent** — une commande, 68 règles, 58 tests dont des
  cas valides et invalides.
- **Les règles ont été écrites avant les mesures**, et chaque révision
  ultérieure est datée avec ce qui l'a déclenchée.
- **Le notebook du distanciel s'exécute de bout en bout** — 42 cellules,
  0 erreur, 5 graphiques, chacun rattaché à une question et interprété. Vérifié
  par exécution réelle (`nbconvert --execute`), pas par relecture.

### Ce qui reste incertain

- Les 3 références orphelines : aucun moyen de deviner la bonne cible.
- Les 595 coûts sans pièce : motif structurel inexpliqué, réponse métier
  attendue.
- Les 12 lignes en quarantaine : deux valeurs se contredisent, aucune n'est
  identifiable comme fausse.
- La concentration apparente des erreurs M1 sur `critical` : 13 observations,
  et un biais de sélection — les cas écartés par la jointure affichent 0 %
  d'erreur contre 16,4 % pour les autres.
- Les seuils que j'ai posés (30 observations, bornes numériques, 5 % et 10
  occurrences) sont des conventions, pas des résultats.

### Ce que M3 doit reprendre

1. Les quatre conditions de `decision_preparation.md` avant toute exploitation.
2. Les limites de couverture : `SITE-OUEST` (16 équipements), 12 types sous le
   seuil, **41 équipements sans aucune activité dont 3 `critical` et 12
   `high`**. Un modèle entraîné sur ce jeu ne peut rien prétendre sur eux.
3. Le fait que le modèle M1 **sous-évalue `critical`** — 9 erreurs sur 12 sont
   des `critical` rétrogradés. Sur un outil de maintenance c'est la direction
   dangereuse. Hypothèse à retester sur un échantillon plus large.
4. La divergence entre `SCHEMA.md` et `contracts/schemas.py`, à faire corriger
   en amont.

### Ce que j'ai appris de mes erreurs

Cinq erreurs commises et corrigées, toutes détectées par un contrôle que
j'avais écrit moi-même — aucune par une relecture après coup.

| Erreur | Ce qu'elle a appris |
|---|---|
| Test du starter cassé sous Windows (CRLF) | Un octet de fin de ligne suffit à invalider une empreinte. Le même problème est réapparu deux fois : `.gitattributes` du dépôt, puis encodage de l'export. |
| Quarantaine tronquée à 10 lignes par règle | Plafonner l'affichage et plafonner la donnée sont deux choses différentes. 76 entrées au lieu de 701. |
| `MNT-VAL-007` rejetant un tiers de la table | Une règle métier inventée depuis un schéma ne peut pas mettre 33 % d'un jeu en quarantaine. La régularité de la répartition est le signal. |
| Valeur observée rédigée dans la quarantaine | Sur-appliquer un principe de protection au point de détruire la preuve. La protection porte sur ce qui part en aval, pas sur la traçabilité de l'audit. |
| Registre bâti sur `SCHEMA.md` sans ouvrir le contrat | Une méthode rigoureuse appliquée à la mauvaise source de vérité produit des résultats faux avec beaucoup d'assurance. 49 fausses anomalies, et une colonne — `outcome` — que rien ne contrôlait. |
| « La durée d'arrêt n'a aucun signal » — conclusion tirée d'une matrice de corrélation calculée sans avoir regardé les distributions | **Regarder les distributions avant les corrélations.** Une matrice calculée sur des données non vérifiées ne mesure pas les relations entre variables : elle mesure l'influence des valeurs aberrantes. Deux lignes sur 1 800 avaient effacé un r de 0,85. |

Deux d'entre elles se répondent, et c'est la leçon que je retiens de la journée.

L'erreur sur le contrat : j'ai bâti un audit rigoureux **sur la mauvaise source
de vérité**. L'erreur sur la corrélation : j'ai tiré une conclusion d'une mesure
juste **sans avoir regardé les données derrière**.

Dans les deux cas la méthode était bonne et le résultat faux, pour la même
raison — une étape de vérification sautée en amont. Et dans les deux cas
l'erreur était **invisible dans le résultat** : une matrice de corrélation à
−0,002 a exactement la même allure qu'une absence réelle de relation, et une
colonne non contrôlée ressemble trait pour trait à une colonne sans anomalie.

C'est ce que je changerais si je recommençais : lire **tout** ce que le module
fournit avant d'écrire la première règle, et tracer **toutes** les distributions
avant de calculer la première corrélation.

---

# Complément « Pour aller plus loin » — 04/08/2026

Publié en amont le 04/08 au matin. Vingt heures annoncées : quatorze de
qualification, six de GitHub Actions. Facultatif, et sans effet sur l'accès au
M3 — qui n'est toujours pas publié.

L'exercice change la question posée. En M2, un lot unique était à lui seul tout
l'univers : on l'auditait, on le préparait, on décidait. Ici une deuxième
livraison arrive, et il faut décider si elle peut rejoindre la première.

## Ce qui a résisté et ce qui a cédé

Sur les 68 contrôles du registre, **45 se rejouent tels quels**. Ils ont un
point commun : ils jugent une ligne, ou une colonne, sans rien avoir besoin de
savoir du reste du monde. Types, bornes, ordre des dates, valeurs absentes,
doublons exacts, données personnelles.

**Dix-huit dépendaient du contexte ou d'une constante**, et c'est là que le
travail était.

Le plus instructif n'est pas la référence orpheline — celui-là se voit tout de
suite, un lot candidat dont les 80 événements portent sur des machines du
catalogue publié produirait 80 faux orphelins bloquants, impossible à manquer.

Le plus instructif, ce sont les trois contrôles croisés entre tables. Eux ne
produisaient **pas** de faux positifs : quand le rapprochement échouait, la
date de référence sortait absente et la règle passait. Ils ne se seraient pas
plaints, ils se seraient **éteints**. Un contrôle qui ne trouve rien parce
qu'il ne cherche plus ressemble exactement à un contrôle qui ne trouve rien
parce qu'il n'y a rien.

C'est la même famille d'erreur que le `SCHEMA.md` du 03/08 et que la matrice de
corrélation : **invisible dans le résultat**.

## Le biais de taille de lot

Le registre M2 classait une valeur hors énumération en « écart de nomenclature »
plutôt qu'en anomalie si elle pesait au moins 5 % des lignes **et** apparaissait
au moins 10 fois. Les deux conditions se calculaient sur la taille du lot
examiné.

| Population | Occurrences nécessaires |
|---|---:|
| Historique maintenance, 1 800 lignes | 90 |
| Lot candidat maintenance, 220 lignes | 11 |
| Lot candidat équipements, 30 lignes | 10, soit 33 % — hors d'atteinte |

La même valeur, dans le même fichier, changeait de classe selon le périmètre
qu'on lui donnait. Retenu : la récurrence se compte sur **publié + candidat**,
parce que la question « cette valeur est-elle une nomenclature légitime ? »
porte sur le corpus et non sur l'échantillon reçu. Contrepartie assumée et
tracée : la qualification d'un lot dépend alors de l'état du publié, donc le
manifeste enregistre les empreintes des deux.

## Deux erreurs de la journée

**La politique rejetait le socle publié.** J'avais écrit l'unicité de la clé
primaire en règle bloquante, au motif qu'elle est absolue. Mesure ensuite : le
socle porte 4 doublons d'`equipment_id`, connus, en quarantaine depuis le
03/08, arbitrage métier toujours en attente. Ma politique rejetait donc ce qui
avait déjà été accepté — et une politique qui rejette le passé ne peut rien
dire de l'avenir.

Le réflexe a été de chercher un plafond. Il se serait situé entre 1,9 % (le
publié) et 6,7 % (le candidat) : un seuil calé sur les deux seules valeurs
observées, donc sans portée au-delà d'elles. J'ai renoncé et gardé le niveau
par défaut. C'est exactement le piège que le brief nomme — écrire des contrôles
« spécifiques aux anomalies déjà observées ».

**Mes propres tests sont tombés dans le biais que je venais de corriger.** Lots
de test à trois lignes : une anomalie unique pesait 33 % et franchissait tous
les plafonds de la politique. Deux tests échouaient pour une raison qui n'avait
rien à voir avec ce qu'ils vérifiaient. Passés à soixante lignes, une anomalie
isolée pèse 1,7 % et l'escalade redevient quelque chose qu'on déclenche exprès.

## Ce que la livraison a donné

| Lot | Statut | Erreurs | Avertissements | Informations |
|---|---|---:|---:|---:|
| Socle publié | `ACCEPTED_WITH_WARNINGS` | 0 | 25 | 1 |
| Livraison candidate | `REJECTED` | 4 | 22 | 5 |

Quatre constats bloquants : 86 interventions sur 220 ouvertes **avant** leur
propre événement (0 sur 1 814 dans le publié), deux clés déjà publiées
réutilisées pour des contenus entièrement différents, un équipement sans
identifiant. Densité d'anomalies quatre fois supérieure au socle : 9,4 % du
volume contre 2,2 %.

**Décision : rejet, relivraison demandée.** Aucune des quatre erreurs ne se
corrige sans inventer de la donnée. Détail dans
`aller_plus_loin/decision_livraison.md`.

## Ce qui reste ouvert

- Toujours aucune revue contradictoire externe, en M1, en M2, et ici.
- Les seuils de plafond (2 %, 5 %, 10 %) sont des choix argumentés, pas des
  mesures. Ils sont dans le YAML pour être contestés.
- La politique n'a été éprouvée que sur une seule livraison candidate.
- Les 595 interventions du socle facturant des pièces sans en déclarer
  attendent toujours un arbitrage métier. Le lot candidat en ajoute 45.
