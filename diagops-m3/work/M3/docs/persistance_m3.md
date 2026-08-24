---
module: M3
brief: online — persister les données DiagOps avec SQLAlchemy et Alembic
etat: terminé
maj: 2026-08-24
---

# Persistance DiagOps — brief online M3

> Tous les chiffres viennent de `output/db/` : `chargement_m2.json`,
> `import_mesures.json`, `effet_index.json`, `requetes.json` et
> `requete_*.json`. Le fichier de base **n'est pas un livrable** : il se
> reconstruit entièrement par la séquence donnée plus bas.

## Séquence complète

```bash
cd work/M3
rm -f output/diagops.db

alembic upgrade 92d73464d6d3        # migration 1 — schéma initial
python run_persistance_m3.py load          # 2 718 lignes M2

alembic upgrade head                # migrations 2 et 3, sur base CHARGÉE
python run_persistance_m3.py measurements  # import idempotent, joué 2 fois

python run_persistance_m3.py queries       # 6 requêtes, résultats conservés
python run_persistance_m3.py index         # effet mesuré des index

pytest tests/test_persistance_m3.py -q     # 16 cas de vérification
```

Base reconstruite : **9,2 Mo** (12,1 Mo après les index et l'usage).

## 1. Justification du modèle de stockage — Q1

Deux familles de données, deux questions différentes.

**Les trois tables M2** ne posent pas de débat : identifiants stables, relations
obligatoires, volumétrie faible (2 718 lignes), intégrité référentielle à faire
respecter. Le relationnel est le choix évident.

**Les mesures capteurs** sont le cas discutable. Comparaison sur des critères
explicites :

| Critère | Relationnel (SQLite / PostgreSQL) | Fichiers colonnes (Parquet) | Base séries temporelles (TimescaleDB, InfluxDB) |
|---|---|---|---|
| **Requêtes attendues** — filtre par équipement et plage de temps, jointure avec `events` | Bon. La jointure est native | Médiocre. La jointure avec un référentiel demande un moteur externe | Bon sur le temps, mais la jointure référentielle reste à faire ailleurs |
| **Contraintes d'intégrité** — clé logique unique, référence vers `equipment` | **Décisif.** Unicité et clé étrangère appliquées par le moteur | Aucune. L'unicité serait une convention de code | Partiel. L'unicité existe, la clé étrangère vers un référentiel rarement |
| **Volumétrie et croissance** — 50 401 lignes / semestre, ×11,6 si tout le parc | Confortable jusqu'à ~10⁷ lignes | Excellent au-delà, compression forte | Conçu exactement pour ça |
| **Coût d'exploitation** | Nul en SQLite : un fichier, zéro installation | Nul, mais pas de serveur de requêtes | Élevé : un service à installer, configurer, sauvegarder |
| **Écritures en lot** | Bon | Excellent | Excellent |

**Retenu : relationnel, pour les deux familles.**

Le critère qui tranche n'est pas la performance — c'est l'**intégrité**. Tout ce
module a montré que la source contredit ses propres règles : clé logique non
unique dans le fichier reçu, équipement absent du référentiel, unités
incohérentes. Un stockage qui n'applique aucune contrainte reporterait ces
contrôles sur chaque programme qui lit les données, et il suffirait d'un import
écrit par quelqu'un d'autre pour les contourner. Une contrainte déclarée en base
tient quel que soit l'auteur du code.

À la volumétrie actuelle, le relationnel n'a aucun désavantage. **Le seuil qui
changerait ce choix est identifié** : au pas de la minute sur le parc entier —
13,1 Go par semestre — la question se rouvrirait, et un stockage hybride
deviendrait défendable (mesures brutes en colonnes, référentiel et agrégats en
relationnel). Le brief admet explicitement deux modèles pour deux familles à
condition de le dire ; ce n'est pas nécessaire aujourd'hui.

## 2. Modèle relationnel — Q2, Q3, Q4

### Ce que représente une ligne, et sa clé primaire — Q2

| Table | Une ligne = | Clé primaire | Lignes |
|---|---|---|---:|
| `equipment` | un équipement du parc | `equipment_id` | 416 |
| `events` | un événement d'exploitation | `event_id` | 514 |
| `maintenance_history` | une intervention de maintenance | `maintenance_id` | 1 788 |
| `sensor_readings` | **une mesure unitaire** : un capteur, un équipement, un instant | `reading_id` *(substitution)* | 50 277 |

**Pourquoi une clé de substitution sur les mesures**, alors que la clé logique
existe. Deux raisons, la seconde décisive :

1. une clé primaire composite de trois colonnes — dont une chaîne de 32
   caractères et un horodatage — serait recopiée dans chaque index secondaire ;
2. surtout, **la clé logique n'est pas unique dans le fichier reçu** (10 clés
   dupliquées, cf. brief présentiel). La promouvoir en clé primaire rendrait
   l'import impossible avant nettoyage. Une contrainte d'unicité permet au
   contraire de **constater** le rejet et de le compter.

### Clés étrangères, et ce qui se passe en cas de violation — Q3

| Table | Colonne | Référence | `ON DELETE` |
|---|---|---|---|
| `events` | `equipment_id` | `equipment.equipment_id` | `RESTRICT` |
| `maintenance_history` | `equipment_id` | `equipment.equipment_id` | `RESTRICT` |
| `maintenance_history` | `event_id` | `events.event_id` | `RESTRICT` |
| `sensor_readings` | `equipment_id` | `equipment.equipment_id` | `RESTRICT` |

**En cas de violation, l'insertion est refusée** — `IntegrityError`, la ligne
n'entre pas. `RESTRICT` plutôt que `CASCADE` : supprimer un équipement ne doit
pas effacer silencieusement son historique et ses mesures. Si cette suppression
est voulue, elle doit être explicite.

**Piège vérifié, pas supposé.** SQLite **n'applique pas** les clés étrangères par
défaut : sans `PRAGMA foreign_keys=ON`, une contrainte déclarée dans le modèle
n'a aucun effet à l'exécution. `build_engine()` l'active. Contrôlé par mutation :
sur un moteur sans le PRAGMA, une mesure rattachée à `EQ-ORPHAN-777` **est
acceptée**. Le test `test_les_cles_etrangeres_sont_reellement_actives` est donc
discriminant — il échouerait si le réglage disparaissait.

### Types retenus, et pourquoi — Q4

| Nature | Type | Justification |
|---|---|---|
| Identifiants | `String(32)` | Courts, stables, jamais calculés. Longueur bornée pour que le schéma documente la donnée attendue |
| Horodatages | `DateTime(timezone=True)` | Tout le module raisonne en UTC ; perdre le fuseau au stockage réintroduirait l'ambiguïté que l'axe 2 a coûté du travail à lever |
| Date de mise en service | `Date` | Aucune heure signifiante : un `DateTime` inventerait une précision |
| **Montants** (`parts_cost_eur`) | **`Numeric(12, 2)`** | **Pas `Float`.** Le binaire flottant ne représente pas exactement 0,10 € : sur 1 788 lignes l'écart est invisible, sur un cumul annuel il ne l'est plus. Un montant se compare et s'additionne, il exige l'exactitude décimale |
| Grandeurs physiques (`value`, `labor_hours`, `rated_power_kw`) | `Float` | Une mesure de capteur est **déjà** approchée ; la précision décimale n'apporterait rien et coûterait en place |
| Compteurs (`downtime_minutes`, `parts_replaced_count`) | `Integer` | Entiers par nature |
| Catégories fermées | `String(16..24)` **+ `CheckConstraint`** | Voir ci-dessous |
| Note libre | `Text` | Longueur non bornée par nature |

**Les domaines fermés sont exprimés en base, pas seulement en code.** Cinq
`CHECK` portent `criticality`, `severity`, `event_type`, `intervention_type`,
`outcome` et `sensor_name`. Motif : le M2 avait montré que `SCHEMA.md` décrivait
`intervention_type` et `outcome` comme des chaînes libres alors que les données
ferment ces domaines à cinq valeurs. Une contrainte en base résiste à un import
écrit par quelqu'un d'autre ; un contrôle applicatif non.

Trois `CHECK` supplémentaires portent la cohérence : chronologie
(`end_at >= start_at`, `closed_at >= opened_at`), positivité
(`rated_power_kw > 0`, `downtime_minutes >= 0`, `parts_cost_eur >= 0`) et
**`value >= 0`** — cette dernière interdit à la sentinelle `-999` d'entrer en
base, même par un import qui contournerait la pipeline.

`value` est **nullable** : « le capteur n'a rien renvoyé » est une information
d'exploitation, la ligne ne doit pas disparaître.

## 3. Chargement des tables préparées — Q5, Q6

**Ordre imposé par les clés étrangères** : `equipment` → `events` →
`maintenance_history`. `maintenance_history` référence les deux autres, elle
vient nécessairement en dernier.

| Table | Lues | Insérées | Rejetées |
|---|---:|---:|---:|
| `equipment` | 416 | 416 | 0 |
| `events` | 514 | 514 | 0 |
| `maintenance_history` | 1 788 | 1 788 | 0 |
| **Total** | **2 718** | **2 718** | **0** |

Durée : 4,7 s.

**L'écart s'explique-t-il entièrement ? Oui — il est nul, et c'est attendu.** Les
tables chargées sont l'état **préparé** de référence, déjà passé par les 19
règles M2. Un rejet à ce stade aurait signalé une incohérence entre la
préparation M2 et le schéma, ce qui aurait été un résultat en soi.

**Ce zéro ne prouve donc rien sur les contraintes.** C'est pourquoi elles sont
vérifiées séparément, par 16 cas qui les franchissent volontairement — sans
quoi on ne saurait pas distinguer « les données sont propres » de « la base
n'applique rien ».

**Traitement des lignes rejetées — Q6.** Chaque ligne est insérée dans son
propre point de sauvegarde (`session.begin_nested()`) : une ligne refusée
n'annule pas les précédentes, et sa raison est comptée par type d'erreur dans
`ImportReport.reasons`. Une ligne rejetée est **comptée et catégorisée**, jamais
perdue en silence.

## 4. Migrations — Q7, Q8, Q9

**Trois migrations**, appliquées dans l'ordre :

| Révision | Objet | Destructeur au `downgrade` ? |
|---|---|---|
| `92d73464d6d3` | Schéma initial : `equipment`, `events`, `maintenance_history` | **Oui — détruit les 2 718 lignes M2** |
| `d94729f4ef24` | Ajout de `sensor_readings`, sa contrainte d'unicité, sa clé étrangère et son index | **Oui — détruit les 50 277 mesures** |
| `92c3364b9519` | Remplace l'index redondant par l'index mesuré utile | **Non — index seulement, aucune donnée touchée** |

La base est **créée par migration**, jamais par `create_all()`.

**Comment `sensor_readings` a été tenue hors de la première migration.** Les
quatre modèles vivent dans le même `models.py` : un `--autogenerate` naïf aurait
produit les quatre tables d'un coup. `alembic/env.py` expose un
`include_object` piloté par `DIAGOPS_ALEMBIC_STAGE=initial`, qui exclut la table
de mesures le temps de générer la première révision. Sans la variable, aucun
filtre — c'est l'état normal du dépôt.

Deux autres réglages de `env.py` ne sont pas ceux du modèle généré :
`render_as_batch=True`, sans quoi toute migration modifiant une colonne échoue
sous SQLite ; et l'URL lue depuis `src/db/session.py` plutôt que dupliquée dans
`alembic.ini`.

### Ce que fait exactement chaque `downgrade` — Q7

Les trois ont été exécutés, l'un après l'autre, en comptant les lignes à chaque
étape :

| Étape | Révision | `equipment` | `events` | `maintenance` | `sensor_readings` |
|---|---|---:|---:|---:|---:|
| départ | `92c3364b9519` | 416 | 514 | 1 788 | **50 277** |
| `downgrade -1` | `d94729f4ef24` | 416 | 514 | 1 788 | **50 277** |
| `downgrade -1` | `92d73464d6d3` | 416 | 514 | 1 788 | **table absente** |
| `downgrade base` | *(aucune)* | absente | absente | absente | absente |

Le `downgrade` de la troisième migration est **sans perte** : il rétablit l'index
précédent. Celui de la deuxième **détruit la table des mesures et ses 50 277
lignes** — c'est un `DROP TABLE`, il n'y a pas de version non destructrice de ce
retour arrière. Celui de la première détruit les trois tables M2.

### Comment il est démontré que la migration ne détruit pas les données — Q8

Par comptage **avant et après**, sur la base réellement chargée :

```
AVANT  migration 2 : {"revision":"92d73464d6d3",
                      "equipment":416, "events":514, "maintenance_history":1788,
                      "sensor_readings":"table absente"}
APRÈS  migration 2 : {"revision":"d94729f4ef24",
                      "equipment":416, "events":514, "maintenance_history":1788,
                      "sensor_readings":0}
```

Les trois tables héritées sont **inchangées** ; `sensor_readings` passe
d'inexistante à créée et vide. La migration s'applique bien sur une base
chargée, sans recréation.

`run_persistance_m3.py counts` est volontairement tolérant à l'absence de
`sensor_readings` : c'est ce qui permet d'exécuter le même contrôle des deux
côtés de la migration.

### La contrainte de clé logique, et ce qu'on observe quand elle est violée — Q9

```python
UniqueConstraint("equipment_id", "timestamp", "sensor_name",
                 name="uq_sensor_readings_logical_key")
```

À la violation : `IntegrityError (sqlite3.IntegrityError) UNIQUE constraint
failed` — l'insertion est refusée, la transaction doit être annulée. Vérifié par
`test_la_cle_logique_refuse_un_doublon`, avec deux lignes de même clé portant des
valeurs différentes, exactement le cas des 4 clés divergentes du brief
présentiel.

Vérifié aussi dans l'autre sens : changer **le capteur** ou **l'instant** suffit
à distinguer deux mesures — la clé porte bien les trois colonnes.

## 5. Import incrémental — Q10, Q11

### Que se passe-t-il si on relance l'import — Q10

Il a été relancé, et le résultat est conservé :

| Passage | Lues | Insérées | En base après | Durée |
|---|---:|---:|---:|---:|
| 1 | 50 277 | **50 277** | 50 277 | 3,3 s |
| 2 | 50 277 | **0** | **50 277** | 4,1 s |

Le second passage lit tout, n'insère rien, et compte 50 277 lignes
`deja_presente`. **La table est dans le même état.**

**Stratégie : `INSERT ... ON CONFLICT DO NOTHING`** sur la contrainte d'unicité,
par lots de 1 000 lignes. Choisie contre deux alternatives :

- *relire les clés existantes et filtrer en mémoire* — il faudrait charger 50 000
  clés avant d'écrire, et la fenêtre entre lecture et écriture n'est pas
  protégée : l'unicité serait garantie par le code, pas par la base ;
- *insérer ligne à ligne dans un point de sauvegarde et rattraper
  l'`IntegrityError`* — c'est ce que font les trois imports M2, acceptable sur
  1 788 lignes ; sur 50 000, le coût des points de sauvegarde devient l'essentiel
  du temps ;
- **`ON CONFLICT DO NOTHING`** délègue l'unicité à la base, ne demande aucune
  lecture préalable, tient en une instruction par lot. Le coût est celui de
  l'index unique, qui existe de toute façon.

**Coût observé** : le second passage ne coûte **pas moins cher** que le premier
(4,1 s contre 3,3 s). C'est la contrepartie de cette stratégie — il faut relire
le fichier entier et proposer les 50 277 lignes à la base pour découvrir
qu'aucune n'est nouvelle. Un import réellement incrémental exigerait un marqueur
de progression côté source (numéro de livraison, horodatage de dernier import),
que le fichier ne fournit pas.

Seconde contrepartie, assumée : l'instruction dit **combien** de lignes ont été
ignorées, pas lesquelles. C'est suffisant ici — la trace ligne à ligne est déjà
portée par la quarantaine du brief présentiel.

### Mesures refusées faute d'équipement correspondant — Q11

**0** sur cet import.

Elles ne manquent pas : les 30 mesures de `EQ-ORPHAN-777` ont déjà été écartées
en amont par `R-SEN-013`, et l'import travaille sur les mesures **préparées**.
Le comptage est fait avant insertion plutôt que laissé échouer sur la clé
étrangère : sinon un lot entier échouerait à cause d'une seule ligne, et la
raison de rejet serait perdue.

Que la barrière fonctionne quand même est vérifié séparément :
`test_import_compte_les_mesures_d_equipement_inconnu` sur un fichier contenant
une ligne orpheline → 2 lues, 1 insérée, **1 rejetée** pour
`equipement_inconnu`.

## 6. Exploitation — Q12 à Q16

Six requêtes exécutées, résultats conservés dans `output/db/requete_*.json`.

| Code | Question | Lignes | Durée |
|---|---|---:|---:|
| `Q12` | Mesures par équipement et par capteur | 70 | 24,0 ms |
| `Q13` | Première et dernière mesure de chaque série | 70 | 29,6 ms |
| `Q14` | Équipements sans aucune mesure | **380** | 5,0 ms |
| `Q-COUV` | Taux d'instrumentation par criticité | 4 | 6,7 ms |
| `Q-VIB` | Vibrations au-delà de 5 mm/s, avec contexte équipement | 8 | **0,3 ms** |
| `Q-EVT` | Événements `critical` et mesures dans les 48 h précédentes | 9 | 0,4 ms |

**Q12** — 70 séries en base (72 dans le fichier reçu : la série figée de
`EQ-PUMP-171` et les mesures orphelines ont été écartées en amont).
**Q14** — 380 équipements sans mesure, cohérent avec les 36 instrumentés sur 416.
**Q-COUV** — retrouve en SQL les taux du brief présentiel : `critical` 30,43 %,
`high` 11,48 %, `medium` 4,05 %, `low` 1,33 %.

### L'index : celui qui sert, et celui qui ne servait pas — Q15

**Index retenu : `ix_sensor_readings_sensor_value` sur `(sensor_name, value)`**,
justifié par `Q-VIB`, réellement exécutée.

| État | Plan d'exécution | Durée médiane |
|---|---|---:|
| Avec l'index | `SEARCH … USING INDEX ix_sensor_readings_sensor_value` | **0,054 ms** |
| Sans aucun index (`NOT INDEXED`) | `SCAN sensor_readings` + `USE TEMP B-TREE FOR ORDER BY` | 4,303 ms |

**Gain observé : ×79,7.** L'index supprime aussi le tri temporaire, puisqu'il
porte déjà `value`.

**Un premier index avait été déclaré, puis retiré après mesure.**
`ix_sensor_readings_equipment_time` sur `(equipment_id, timestamp)` semblait
évident : c'est le motif d'accès attendu sur une série temporelle. Mesuré sur la
requête qui le motivait :

| État | Plan | Durée médiane |
|---|---|---:|
| Avec l'index dédié | `SEARCH … USING INDEX ix_sensor_readings_equipment_time` | 0,0834 ms |
| Index dédié retiré | `SEARCH … USING INDEX sqlite_autoindex_sensor_readings_1` | 0,0836 ms |
| Sans aucun index | `SCAN sensor_readings` | 4,014 ms |

**Gain de l'index dédié : ×1,00 — aucun.** La contrainte d'unicité crée
automatiquement `sqlite_autoindex_sensor_readings_1` sur
`(equipment_id, timestamp, sensor_name)`, dont les deux premières colonnes
couvrent exactement ce motif. L'index dédié était **redondant**, et il coûtait de
l'espace et du temps d'écriture pour rien.

Il a été retiré par la troisième migration, et remplacé par celui qui sert. Ce
que cela apprend : **l'indexation vaut ×48**, mais un index n'est pas justifié
par le raisonnement qui l'a inspiré — seulement par la mesure.

*Note de méthode* : les deux premières versions de cette mesure étaient fausses,
annonçant le même plan dans tous les états. Cause — le pool de SQLAlchemy
réutilise la connexion SQLite, qui garde son cache de plans ; un `EXPLAIN`
exécuté après un `DROP INDEX` renvoyait le plan d'avant. `engine.dispose()` avant
chaque mesure corrige.

### Ce que la base apporte, et ce qu'elle coûte — Q16

Mesuré, à traitement identique :

| Opération | Base | Lecture CSV avec pandas | Rapport |
|---|---:|---:|---:|
| Requête ciblée (`Q-VIB`) | **0,62 ms** | 53,21 ms | **×85** |
| Jointure mesures × équipements avec regroupement | **21,64 ms** | 60,57 ms | **×3** |

| Coût | Base | CSV |
|---|---:|---:|
| Espace disque | **12,1 Mo** | 6,1 Mo |

**Ce qu'elle apporte :**

1. **L'intégrité, qui est le vrai gain.** Unicité de la clé logique, clés
   étrangères, domaines fermés et cohérence chronologique sont appliqués par le
   moteur. Aucun programme lisant ces données ne peut les contourner. Sur des
   CSV, chaque lecteur doit refaire ces contrôles — ou les oublier.
2. **Le coût d'accès ne dépend plus du volume total.** Une requête ciblée coûte
   85 fois moins qu'une lecture CSV, parce que la base ne lit que ce qu'elle
   doit. L'écart croît avec le volume : c'est 85 aujourd'hui, ce serait bien
   davantage sur le parc entier.
3. **L'incrémental devient possible.** `ON CONFLICT DO NOTHING` rend l'import
   rejouable ; sur des fichiers, il faudrait tout relire et tout réécrire.

**Ce qu'elle coûte :**

1. **Le double d'espace** — 12,1 Mo contre 6,1 Mo. Les index représentent
   l'essentiel de l'écart, c'est le prix des ×85.
2. **Une étape de plus dans la chaîne.** Le fichier était directement lisible ;
   la base demande un schéma, des migrations et un import. C'est du code à
   maintenir, et une possibilité de divergence entre modèles et migrations — d'où
   le test `test_les_migrations_produisent_le_schema_des_modeles`.
3. **Un gain modeste sur les jointures** — ×3 seulement. À cette volumétrie,
   pandas s'en tire honorablement ; l'écart se creusera avec le volume, pas
   avant.

**Conclusion honnête** : à 50 000 lignes, la base n'est **pas** justifiée par la
performance — pandas suffirait. Elle l'est par l'**intégrité** et par ce qui
vient ensuite : le parc entier, les livraisons successives, et des lecteurs qui
ne connaîtront pas les règles de ce module.

## Vérifications

**16 cas de vérification** dans `tests/test_persistance_m3.py` :

- clés étrangères réellement actives — vérifié par mutation : sur un moteur sans
  `PRAGMA foreign_keys=ON`, la mesure orpheline **est acceptée** ;
- clé logique refusant un doublon, et acceptant deux capteurs au même instant ou
  deux instants pour le même capteur ;
- domaines fermés : capteur inconnu refusé, criticité hors domaine refusée ;
- cohérence : valeur négative refusée, valeur absente acceptée, événement
  finissant avant de commencer refusé, événement sans fin accepté ;
- import idempotent, comptage des équipements inconnus, valeur vide acceptée ;
- **cohérence migrations / modèles** : une base montée par `alembic upgrade head`
  a exactement les tables et colonnes des modèles.

## Limites

- **SQLite**, pas PostgreSQL. `ON CONFLICT DO NOTHING` existe dans les deux, mais
  la syntaxe est importée depuis `sqlalchemy.dialects.sqlite` : un passage à
  PostgreSQL demande de changer cet import. `DIAGOPS_DATABASE_URL` permet le
  changement de moteur, il n'a pas été **testé** sur PostgreSQL.
- Le comportement des index a été mesuré **sur SQLite**. La conclusion sur la
  redondance devrait s'y transposer — PostgreSQL crée aussi un index btree pour
  une contrainte d'unicité — mais elle n'a pas été vérifiée ailleurs.
- L'import n'est **rejouable** mais pas **incrémental** : il relit tout à chaque
  fois. Le fichier source ne fournit aucun marqueur de progression.
- Aucune stratégie de sauvegarde ni de reprise n'est définie. La base étant
  entièrement reconstructible en moins d'une minute, la question ne se pose pas à
  cette échelle.
