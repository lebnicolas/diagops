---
module: M3
maj: 2026-08-24
---

# Journal de bord — M3

## Reprise M2

- **Point de départ utilisé** : la **référence commune**
  `data_pack/2026-S1/reference_runs/m2_for_m3/`, pas notre préparation M2
  personnelle. Motifs : comparabilité entre apprenants, découplage des
  arbitrages M2 encore ouverts, et autorisation explicite du brief.
- **Constat qui relativise ce choix** : sur `equipment`, la référence préparée et
  le fichier brut sont identiques (416 lignes de part et d'autre, aucun écart).
  Le point de départ n'a donc aucun effet sur les taux de couverture. L'écart ne
  pourra apparaître que sur `events` et `maintenance_history`, au rapprochement.
- **Règles héritées relues** : pas encore. Le registre M2
  (`reference_runs/m2_for_m3/regles_m2.md`) sera repris règle par règle à l'axe 4,
  chacune recevant un statut `conservee` / `modifiee` / `etendue` / `abandonnee`.
- **Décisions M2 remises en cause** : aucune à ce stade.
- **Preuves conservées** : `output/cadrage/` (7 CSV + `cadrage.json`), rejouable
  par `python run_cadrage_m3.py`.
- **Limites encore ouvertes, héritées de M2** : les deux arbitrages métier non
  tranchés (12 lignes en quarantaine, 595 interventions facturant des pièces sans
  en déclarer) restent en attente. Ils ne bloquent pas M3 du fait du choix de
  point de départ ci-dessus. Et toujours pas de revue contradictoire externe :
  toutes les objections viennent de nos propres contrôles.

## Hypothèses formulées avant analyse

| Date | Hypothèse | Mesure prévue | Résultat | Décision |
|---|---|---|---|---|
| 24/08 | La clé `equipment_id + timestamp + sensor_name` est unique | Compter les clés portant plusieurs lignes | **Fausse** — 10 clés / 20 lignes, dont 4 clés à valeurs divergentes | Arbitrage reporté à l'axe 4, tracé obligatoire |
| 24/08 | Le pas de 6 h annoncé est respecté | Distribution des écarts entre mesures consécutives | **Vraie à 99,97 %** (50 313 / 50 329) | Le pas devient une règle contrôlable, les 16 écarts sont instruits un par un |
| 24/08 | La période couverte est `2026-S1` | Comparer min/max réels aux bornes annoncées | **Presque** — 5 lignes débordent (2 en déc. 2025, 3 en juil. 2026) | Règle « mesure hors période » à écrire à l'axe 4 |
| 24/08 | Le fichier a un problème d'encodage (`°C` illisible) | Décoder les octets et localiser la séquence du degré | **Fausse** — UTF-8 valide, `C2 B0` ; l'artefact venait de la console Windows | Aucune règle. Fausse anomalie évitée |
| 24/08 | Les lots de 720 et de 40 lignes sont les mêmes comptés deux fois | Croiser les masques deux à deux | **Fausse** — toutes les intersections sont nulles, 6 lots indépendants | Le diagnostic ne double-compte pas |
| 24/08 | Il y a 6 interruptions d'échantillonnage | Vérifier ce qui borde chaque trou | **Fausse** — 5 sont des artefacts de mesures isolées, **1 seule est réelle** | Critère de détection corrigé (tester les deux bornes du trou) |
| 24/08 | Les valeurs aberrantes se repèrent par répétition anormale | Compter les valeurs revenant ≥ 20 fois par capteur | **Fausse** — `vibration_mm_s` varie de 2 à 4 à deux décimales, chaque valeur revient ~100 fois naturellement. Des dizaines de faux positifs, aucun vrai | Critère abandonné, remplacé par un critère **physique** : valeur négative impossible |
| 24/08 | Les 12 sentinelles sont marginales (0,02 % du fichier) | Comparer les écarts-types avec et sans | **Fausse** — σ de `vibration_mm_s` : 14,65 → **0,405** (÷ 36) | Sentinelles retirées **avant** tous les autres contrôles |
| 24/08 | Une dérive lente se détecte à une corrélation ≥ 0,7 | Régresser valeur sur temps, série par série | **Fausse** — 0 candidat, alors que la `DATA_CARD` en annonce une | Seuil refixé à 0,30 **d'après la distribution** (médiane 0,022, 2ᵉ max 0,103) → 1 candidat |
| 24/08 | La dérive de `EQ-CHILL-248` est linéaire sur 6 mois | Moyenne mensuelle | **Fausse** — stable à ~52,5 °C de janvier à avril, puis 55,1 en mai et 60,6 en juin | La régression signalait la bonne série pour la mauvaise raison ; c'est une rampe tardive, encore en cours |
| 24/08 | Un remplacement recalerait une dérive d'origine capteur | Comparer les 7 j avant / après `MNT-2026S1-0147` (15/03) | **Non concluant** — écart −1,20 °C, dans le bruit ; l'intervention précède le début de la dérive | Cas classé **indécidable**, et l'incertitude est documentée |
| 24/08 | La largeur de la fenêtre de rapprochement conditionne ce qui est observable | Rejouer le rapprochement sur 5 fenêtres, de 12/6 h à 168/72 h | **Fausse** — 89 événements appariés dans les 5 cas ; seul le volume de mesures change (1 045 → 7 024) | Fenêtre 48/24 h retenue ; le choix n'est pas déterminant, l'instrumentation l'est |
| 24/08 | Les épisodes de vibration les plus forts sont captés par le rapprochement | Compter les mesures > 5 mm/s appariées | **Fausse** — 8 au total, **2 appariées, 6 non** ; les 6 sont l'épisode `EQ-FAN-304`, pic 9,76 compris | Porté à la décision comme limite structurelle, non corrigeable par la fenêtre |

## Activités et preuves produites

| Date | Activité | Artefact ou commit | Revue reçue |
|---|---|---|---|
| 24/08 | Mise en place de `diagops-m3` : supports M3, `data_pack` à jour, `work/M3` initialisé depuis le starter, `.venv` dédié | `projets/diagops-m3/` | — |
| 24/08 | Vérification du starter fourni : **20 tests sur 21 passent** | — | — |
| 24/08 | Échec du 21e test identifié comme un **défaut du test, pas du code** : `Path.write_text` traduit `\n` en `\r\n` sous Windows, le SHA-256 attendu est celui du contenu en LF | à remonter au formateur | — |
| 24/08 | Axe 1 — cadrage de la source capteurs, script rejouable | `run_cadrage_m3.py`, `output/cadrage/` | — |
| 24/08 | Rédaction du diagnostic, partie cadrage | `docs/diagnostic_multisource.md` | — |
| 24/08 | Axe 2 — audit temporel : normalisation des unités, sentinelles, plages, capteur figé, dérive, sauts | `run_audit_temporel_m3.py`, `output/audit/` | — |
| 24/08 | Axe 3 — quatre observations atypiques instruites et croisées avec `events` / `maintenance_history` | `docs/diagnostic_multisource.md` | — |
| 24/08 | Les 11 familles d'anomalies annoncées par la `DATA_CARD` sont toutes retrouvées | tableau de recoupement dans le diagnostic | — |
| 24/08 | Axe 4 — pipeline multi-source : 34 règles, quarantaine unifiée, non-régression bloquante | `src/pipeline_m3.py`, `run_pipeline_m3.py`, `docs/registre_regles.md` | — |
| 24/08 | 36 cas de vérification écrits pour la pipeline — un valide et un invalide par règle, 4 cas temporels, la non-régression | `tests/test_pipeline_m3.py` — **56 tests au vert** | — |
| 24/08 | Deux épisodes de vibration inédits révélés par le critère de plage robuste, tous deux corrélés à un incident `critical` | `docs/diagnostic_multisource.md`, cas 3 bis | — |
| 24/08 | Axe 5 — rapprochement mesures ↔ événements : fenêtre justifiée, cardinalité, duplication, agrégats, sensibilité | `run_rapprochement_m3.py`, `output/alignment/`, `output/aggregates/` | — |
| 24/08 | Vérifié que la contradiction `SCHEMA.md` signalée en M2 persiste dans le M3 publié le 24/08 | à remonter au formateur | — |

## Décisions

### Décision 1 — Point de départ : référence commune plutôt que préparation M2 personnelle

- **Options considérées** : (a) notre préparation M2, terminée et disponible ;
  (b) la référence commune `m2_for_m3/`.
- **Preuve déterminante** : les deux parcs `equipment` sont identiques (416
  lignes, aucun écart) — le choix est donc sans conséquence sur toute la partie
  couverture, ce qui retire l'essentiel du risque de l'option (b).
- **Choix retenu** : (b), la référence commune.
- **Limites et réversibilité** : entièrement réversible — `load_reference()` et
  `load_sources()` sont deux appels distincts, et rien de ce qui est écrit ne
  dépend du contenu de la référence au-delà de `equipment`. À reconsidérer à
  l'axe 5, où `events` et `maintenance_history` peuvent différer.

### Décision 2 — Hypothèse de fuseau sur les 720 horodatages sans indication

- **Options considérées** : (a) interpréter en UTC ; (b) écarter ces 720 lignes ;
  (c) chercher le fuseau réel par recoupement avec `events`.
- **Preuve déterminante** : les 49 681 autres lignes sont en UTC explicite, et la
  série concernée s'aligne sur la même grille 00/06/12/18 que les autres.
- **Choix retenu** : (a), **et l'hypothèse est inscrite comme telle**, pas comme
  un fait. Elle ira au registre de règles.
- **Limites et réversibilité** : hypothèse **faible**. Elle ne distingue pas UTC
  d'un fuseau décalé d'un multiple exact de 6 h. Un décalage d'une heure
  fausserait le rapprochement mesure ↔ événement sur `EQ-COMP-233`. L'option (c)
  reste ouverte à l'axe 5 et pourrait la confirmer ou l'infirmer.

### Décision 3 — Traitement des quatre observations atypiques (axe 3)

Décidées ensemble, parce que leur cohérence est le vrai enjeu : quatre
observations de nature différente ne peuvent pas recevoir le même traitement.

| Cas | Nature | Décision | Traitement proposé |
|---|---|---|---|
| 12 lignes à `-999` | code d'absence, pas une mesure | **erreur** | `champ_neutralise` — valeur mise à manquant, ligne conservée et signalée |
| `EQ-PUMP-171 / vibration_mm_s` figé 474 h | capteur gelé | **erreur** | `exclue` des agrégats, en quarantaine avec son motif |
| `EQ-FAN-304 / vibration_mm_s` 10-11/05, pic 9,76 | rampe physique sur 36 h | **mesure réelle** | `conserve_signale` — jamais supprimée |
| `EQ-CHILL-248 / temperature_c` +8,9 °C | dérive réelle, origine inconnue | **indécidable** | `conserve_signale` + incertitude documentée |

- **Preuve déterminante, cas par cas** : pour `-999`, l'impossibilité physique
  d'une valeur négative sur les cinq grandeurs ; pour le figé, un σ nul sur 20
  jours quand le parc est à 0,405 ; pour `EQ-FAN-304`, la **forme** du signal —
  une rampe de six relevés consécutifs, pas un point isolé ; pour `EQ-CHILL-248`,
  l'échec assumé du test de recalage par intervention.
- **Limites et réversibilité** : aucune ligne n'est supprimée, dans aucun des
  quatre cas. Toutes restent retrouvables et les décisions sont réversibles.
- **Point à ne pas perdre** : l'épisode de `EQ-FAN-304` n'a **aucun événement ni
  intervention associés**. Le seul signal de dégradation exploitable du corpus
  est donc invisible pour un rapprochement mesures ↔ événements — ce qui borne
  directement ce qu'un modèle supervisé pourra apprendre en M4.

### Décision 4 — Clés à valeurs divergentes : aucune des deux valeurs retenue

- **Options considérées** : (a) exclure les deux et tracer ; (b) garder la
  première occurrence ; (c) arbitrer sur le voisinage ; (d) moyenne des deux.
- **Preuve déterminante** : sur `EQ-COMP-396`, l'option (c) est motivée — 8,12 bar
  est hors du voisinage immédiat et constitue le maximum global du capteur. Mais
  sur les trois autres clés, les deux valeurs candidates tombent dans la plage
  d'oscillation normale de la série : (c) y redevient arbitraire **sous une
  apparence de méthode**, ce qui est pire qu'un arbitraire assumé.
- **Choix retenu** : (a). 8 lignes exclues, tracées avec leur motif.
- **Coût mesuré** : 4 mesures perdues sur des séries de 720 points (0,008 %), et
  4 trous de 6 h — que `R-SEN-004` remonte ensuite. La pipeline signale la
  discontinuité que notre propre décision vient de créer : c'est le comportement
  attendu, et la traçabilité le prouve.
- **Limites et réversibilité** : entièrement réversible, les 8 lignes restent
  identifiables en quarantaine par leur `row_identifier`.

### Décision 5 — Estimateurs robustes pour tous les contrôles de valeurs extrêmes

- **Options considérées** : (a) seuils fondés sur moyenne/écart-type/centiles ;
  (b) seuils fondés sur médiane et MAD.
- **Preuve déterminante** : trois détecteurs ont produit des résultats faux avec
  (a). Le seuil au 99ᵉ centile rejetait exactement 1 % des lignes par
  construction. Le seuil à 8 écarts-types ne voyait pas un saut isolé, parce que
  le saut gonfle l'écart-type qui le mesure. C'est la mécanique des sentinelles
  transposée : **la valeur cherchée fausse l'estimateur censé la trouver**.
- **Choix retenu** : (b) partout, plus un garde-fou d'amplitude sur le saut.
- **Limites** : le MAD seul s'est révélé trop sensible sur une série très stable
  (38 faux sauts sur 40 points en test). D'où le second critère. Un détecteur
  robuste n'est pas un détecteur juste — il demande toujours d'être éprouvé.

## Brief online

Terminé. Détail complet dans `docs/persistance_m3.md`.

- **Modèle et types retenus** : relationnel pour les deux familles de données,
  contre Parquet et base séries temporelles. Le critère décisif n'est pas la
  performance — à 50 000 lignes pandas suffirait — mais l'**intégrité** : ce
  module a montré que la source contredit ses propres règles, et une contrainte
  en base résiste à un import écrit par quelqu'un d'autre. Types notables :
  `Numeric(12,2)` et non `Float` pour les montants ; `DateTime(timezone=True)`
  partout, pour ne pas reperdre le fuseau que l'axe 2 a coûté du travail à
  fixer ; six `CHECK` portant les domaines fermés, dont `value >= 0` qui
  interdit à la sentinelle `-999` d'entrer en base.
- **Migrations écrites et testées** : trois. Schéma initial, ajout de
  `sensor_readings` sur base **chargée**, puis remplacement de l'index. Les trois
  `downgrade` exécutés et leur effet destructeur mesuré par comptage : le 3→2 est
  sans perte, le 2→1 détruit les 50 277 mesures, le 1→base détruit les 2 718
  lignes M2. Base entièrement reconstruite depuis zéro pour vérifier.
- **Stratégie d'idempotence et coût observé** : `INSERT ... ON CONFLICT DO
  NOTHING` sur la clé logique, par lots de 1 000. Deux passages : 50 277 insérées
  puis **0**, table inchangée. Coût assumé — le second passage ne coûte pas moins
  cher (4,1 s contre 3,3 s), il faut relire tout le fichier pour découvrir que
  rien n'est nouveau. Un import réellement incrémental exigerait un marqueur de
  progression que la source ne fournit pas.
- **Index ajouté et effet mesuré** : `(sensor_name, value)`, **gain ×79,7**
  (4,30 → 0,054 ms), le tri temporaire disparaît du plan.

### Décision 6 — Un index retiré après mesure

- **Options considérées** : (a) garder `(equipment_id, timestamp)`, déclaré en
  premier pour le motif « un équipement sur une plage de temps » ; (b) le
  retirer.
- **Preuve déterminante** : gain mesuré **×1,00 — aucun**. La contrainte
  d'unicité crée `sqlite_autoindex_sensor_readings_1` sur
  `(equipment_id, timestamp, sensor_name)`, dont les deux premières colonnes
  couvrent exactement ce motif. L'indexation elle-même vaut ×48, mais cet
  index-là n'y contribuait pas.
- **Choix retenu** : (b), par une troisième migration, et remplacement par
  `(sensor_name, value)` justifié par une requête réellement exécutée.
- **Ce que ça apprend** : un index n'est pas justifié par le raisonnement qui
  l'a inspiré, seulement par la mesure. Celui-là paraissait évident.

### Hypothèses du brief online

| Date | Hypothèse | Mesure prévue | Résultat | Décision |
|---|---|---|---|---|
| 24/08 | Les clés étrangères déclarées s'appliquent | Insérer une mesure orpheline sur un moteur sans `PRAGMA foreign_keys=ON` | **Fausse sans le PRAGMA** — la ligne est acceptée | `build_engine()` l'active ; le test est discriminant, il échouerait si le réglage disparaissait |
| 24/08 | Un index sur `(equipment_id, timestamp)` accélère l'accès par série | Comparer les plans et les temps avec, sans, et sans aucun index | **Fausse** — ×1,00 ; l'index de la contrainte d'unicité fait déjà le travail | Index retiré et remplacé (décision 6) |
| 24/08 | Les mesures de temps d'index sont fiables | Vérifier le plan annoncé après `DROP INDEX` | **Fausse deux fois** — le pool réutilise la connexion SQLite et son cache de plans ; l'`EXPLAIN` renvoyait le plan d'avant | `engine.dispose()` avant chaque mesure |
| 24/08 | 0 rejet au chargement prouve que les contraintes fonctionnent | Écrire des cas qui les franchissent | **Fausse** — un zéro ne distingue pas « données propres » de « base qui n'applique rien » | 16 cas de vérification dédiés |

## Bilan M3

*(module terminé — brief présentiel et brief online)*

- **Ce que je sais démontrer** : le grain, la clé logique et sa non-unicité
  chiffrée ; la période réelle contre la période annoncée ; le pas d'échantillonnage
  et l'unique interruption réelle ; l'inventaire des défauts de forme et leur
  indépendance ; la couverture instrumentale ventilée par site, type et criticité ;
  l'effet mesuré des sentinelles sur la dispersion ; les trois comportements de
  capteur, chacun avec son seuil justifié ; et pour quatre observations atypiques,
  ce qui fait conclure à l'erreur, au phénomène réel ou à l'indécidable.
  Le tout rejouable en deux commandes, 5,8 s au total.
- **Ce qui reste incertain** : l'hypothèse de fuseau ; l'origine de la dérive de
  `EQ-CHILL-248` ; le sort des 4 clés à valeurs divergentes et celui de
  `EQ-ORPHAN-777` ; et l'exhaustivité des détecteurs — les seuils retenus
  laissent passer par construction les anomalies plus discrètes.
- **Ce que M4 doit reprendre** : le biais de sélection du parc instrumenté. La
  couverture est corrélée à la criticité (30,4 % des équipements `critical`
  contre 1,3 % des `low`), un site entier est sans capteur (SITE-OUEST) et 7
  types d'équipement n'ont aucune mesure, dont `press` (34) et `valve` (21).
  Tout modèle construit sur ces mesures décrira les équipements critiques de
  trois sites, pas le parc.
