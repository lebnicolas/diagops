# Journal de bord — M2

Module 2 — auditer et préparer les données DiagOps. Session du 03/08/2026.

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

### Décision 2 — statut des données pour M3

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

La dernière est la plus instructive : les 49 fausses anomalies se voyaient,
`outcome` non contrôlé ne se voyait pas. Un audit ne peut pas dire qu'une
colonne est bonne s'il ne l'a pas regardée — il peut seulement dire qu'il n'a
rien vu.
