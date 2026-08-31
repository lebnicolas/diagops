---
module: M3
maj: 2026-08-25
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

*(briefs 1 terminés — présentiel et online ; le brief 2 rouvre le module, voir plus bas)*

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

---

# Brief 2 — Capacité du jeu de données et transition vers M4

Le module rouvre : le brief 2 est publié le 25/08/2026 (commit amont `e4b0efc`),
online, obligatoire, **strictement individuel**.

## Reprise — ce que la publication change

- **Les techniques de génération et d'augmentation remontent du M6 au M3.**
  `acquis_m3.md` est révisé et donne le motif : ces techniques répondent à « que
  permet ce jeu de données », question qui précède la modélisation.
- **Un contrat de provenance entre au `SCHEMA.md`** : toute table de mesures
  transmise déclare `provenance` et `procedure_id`. Le pack passe en
  `diagops-2026-S1-m3-v2`.
- **Le régime d'échange change** : revues collectives possibles sur les briefs 1,
  travail strictement individuel sur le brief 2 — le lot de contrôle est
  identique pour les trois apprenants et son oracle n'est pas distribué.
- **Le bilan du brief 1 n'est pas invalidé, il est requalifié** : il portait sur
  la *qualité* des données. Le brief 2 pose la question de leur *capacité*.

## Activités du 25/08

| Activité | Preuve | Statut |
|---|---|---|
| Synchronisation du module avec l'amont `e4b0efc` | brief 2, lot de contrôle, `verify_synthetic.py`, `SCHEMA.md`, `DATA_CARD.md`, `MANIFEST.yaml` | fait |
| Vérification d'intégrité du lot de contrôle | `sha256sum -c checksums.sha256` → 3 fichiers OK | fait |
| Vérification de l'environnement | `work/M3/.venv` — numpy 2.3.2, pandas 2.3.1, scikit-learn 1.7.1, matplotlib 3.10.3, scipy 1.16.0 | fait |
| Cadrage du travail | `docs/plan_brief2.md` | fait |
| Étape 1 — capacité du jeu de données | `run_capacite_b2.py`, `output/capacite/` (13 CSV + 5 figures + `capacite.json`), `docs/capacite_jeu_donnees.md` | fait |
| Reproductibilité vérifiée | deux exécutions successives, sorties identiques à l'octet près (graine `25082026`) | fait |
| Étape 2 — augmentation de séries | `run_augmentation_b2.py`, `output/augmentation/` (8 CSV + 2 figures + `augmentation.json`), `docs/augmentation_techniques.md` | fait |
| Arbitrage A2 — périmètre à générer | `docs/plan_brief2.md` §7 | **tranché** : `SITE-OUEST` ∩ `SEG-2`, 8 équipements, 2 capteurs, janvier 2026 |
| Étape 3 — génération et comparaison | `run_generation_b2.py`, `output/generation/` (8 CSV + 2 figures + `generation.json`), `docs/comparaison_reel_fabrique.md` | fait |
| Arbitrage A1 — préparation de départ | `docs/plan_brief2.md` §7 | **tranché** : notre préparation du brief 1 (`output/processed/`) |
| Arbitrage A3 — variables de segmentation | `docs/plan_brief2.md` §7 | **tranché** : référentiel + activité, couverture instrumentale exclue |

## Constat porté au dossier avant toute exécution

Les 15 règles capteurs du brief 1 contrôlent la **qualité**, pas
l'**authenticité**. Le lot de contrôle est construit pour punir cette confusion :
ses lignes réelles proviennent de la livraison M3 et portent donc ses anomalies.
Réutiliser le registre du brief 1 comme détecteur de fabrication produira des
faux positifs — c'est une prédiction, elle sera vérifiée au calibrage sur
`control_sample.csv`.

## Hypothèses formulées avant analyse — brief 2

| Date | Hypothèse | Mesure prévue | Résultat | Décision |
|---|---|---|---|---|
| 25/08 | Les règles de qualité du brief 1 accusent à tort des lignes réelles du lot | Appliquer le registre `R-SEN-*` à `control_sample.csv` et compter les réelles signalées | *(à mesurer)* | *(à décider)* |
| 25/08 | Une segmentation du parc sur référentiel + activité fait apparaître un groupe mal couvert que les comptages par site ne montraient pas | K-means, `k` par silhouette, croisement a posteriori avec l'instrumentation | **Vraie, mais pas au premier essai** — voir l'étape 1 ci-dessous | Stratifier avant de segmenter |
| 25/08 | La couverture d'un événement dépend de sa sévérité — les cas graves seraient les moins observés | Taux par catégorie, puis test du χ² sur le tableau de contingence | **Fausse** — χ² = 2,46, p = 0,483 sur `severity` ; p = 0,389 sur `event_type` | Écrire que la couverture est uniformément faible (~17 %), et non corrélée à la gravité |
| 25/08 | Les séries capteurs n'ont pas de structure temporelle exploitable (autocorrélation de rang 1 : +0,079) | Reprendre l'autocorrélation aux rangs 2, 3, 4, 8 et 28 | **Fausse** — cycle journalier marqué : rang 2 (12 h) −0,585, rang 4 (24 h) +0,694 | Juger la structure aux rangs 2 et 4 ; le rang 1 est en quadrature, nul par construction |
| 25/08 | Un décalage temporel de 18 h détruit le lien aux événements | Compter les mesures encore présentes dans une fenêtre après décalage | **Fausse** — 2 553 sur 2 560 y sont encore, lien tenu sur 97,1 % des séries | Constat reporté sur le brief 1 : la fenêtre −48 h / +24 h est peu sélective |
| 25/08 | Compter les mesures présentes dans une fenêtre suffit à établir le lien aux événements | Appliquer la métrique à une permutation de valeurs, qui ne déplace aucun horodatage | **Fausse** — verdict « lien préservé à 100 % » sur une série dont les valeurs ont été mélangées | Ajouter le niveau moyen en fenêtre ; la permutation tombe alors à 31,4 % |
| 25/08 | Les mesures réelles réagissent aux événements de `events.csv` | Mann-Whitney sur le niveau en fenêtre contre hors fenêtre, par capteur | **Vraie sur 2 des 5 capteurs** — vibration +7,42 % (p < 0,0001), température +2,69 % (p < 0,0001) ; courant, pression et régime non significatifs | Générer sur ces deux capteurs ; la réaction devient un test discriminant |
| 25/08 | Le test de réaction aux événements peut se mener sur le mois généré | Rejouer le test du réel restreint à janvier | **Fausse** — sur janvier, même le réel ne réagit pas de façon détectable (p = 0,18 et p = 0,97) | Produire une génération de contrôle sur tout le semestre pour cette seule question ; le livrable reste borné à janvier |

## Étape 1 — ce que le jeu de données ne permet pas

Détail complet dans `docs/capacite_jeu_donnees.md`. Deux ratés méritent d'être
consignés ici, parce que le résultat corrigé en dépend.

**Raté 1 — la première segmentation ne segmentait rien.** Sur le parc entier,
`k = 2` sortait avec une silhouette de 0,454, chiffre flatteur. Le groupe isolé
était en réalité le critère booléen `n_interventions == 0` : pureté 100 %,
rappel 100 %. Ces 50 équipements ont tous leurs compteurs d'activité nuls et
occupent un point unique de l'espace ; K-means les sépare en premier, la
silhouette récompense cette séparation, et les 366 autres restent non
structurés. Signes qui auraient dû alerter plus tôt : silhouette qui s'effondre
à 0,215 dès `k = 3`, et plus petit groupe bloqué à 50 pour `k = 2, 3, 4`.
**Correction** : sortir ces 50 équipements en strate déclarée (`SEG-INACTIF`),
puis segmenter les 366 actifs séparément.

**Raté 2 — le diagnostic qui devait attraper le raté 1 ne l'attrapait pas.**
Écrit d'abord comme `max(activité) == 0` sur chaque groupe, il ne détectait
rien : certains équipements sans intervention ont malgré tout un événement
enregistré, donc le maximum du groupe n'est pas nul. Le bon test est le
**recouvrement** entre le groupe et le critère, mesuré dans les deux sens
(pureté et rappel). Une règle de contrôle peut être juste dans son intention et
inopérante dans sa formulation — c'est exactement ce que le lot de contrôle du
brief 2 va sanctionner à la partie 4.

**Ce que l'étape établit.** À criticité, site, type, âge et puissance
comparables, le taux d'instrumentation varie d'un facteur **15** entre `SEG-1`
(33/192, 17,19 %) et `SEG-2` (2/174, 1,15 %). 92 % de l'instrumentation est
concentrée dans un segment qui pèse 46 % du parc. C'est un second biais de
couverture, **indépendant** du biais de criticité établi au brief 1. Son sens
causal n'est pas déterminé : la date de pose des capteurs est absente du jeu.

**Limite énoncée** : la silhouette retenue vaut 0,193 et ne dépasse 0,175 pour
aucun `k` de 2 à 10. Le parc est un gradient continu d'intensité de maintenance,
pas une collection de familles distinctes. Le facteur 15 tient ; la lecture
« deux populations de nature différente » ne tient pas.

## Étape 2 — ce que chaque augmentation détruit

Détail complet dans `docs/augmentation_techniques.md`. Cinq techniques,
70 séries, 50 225 mesures. Trois enseignements dépassent l'étape.

**La saisonnalité journalière était invisible à l'endroit où je la cherchais.**
Mesurée au rang 1, l'autocorrélation vaut +0,079 — j'en avais conclu que les
séries n'avaient pas de structure temporelle. Aux rangs 2 et 4, elle vaut −0,585
et +0,694 : le cycle est journalier, quatre mesures par jour, et le rang 1 est
en quadrature de phase donc nul **par construction**. Deux conséquences pour la
suite : c'est la relation que le tirage marginal détruira à la partie 3, et
c'est le levier de détection de la famille de fabrications n° 2 à la partie 4.

**Une métrique peut dire « préservé » sur une propriété détruite.** Le lien aux
événements était mesuré par le nombre de mesures présentes dans une fenêtre. Une
permutation de valeurs ne déplace aucun horodatage : verdict « préservé à
100 % » sur une série entièrement mélangée. La métrique comptait la présence,
pas la pertinence. Corrigée par le niveau moyen en fenêtre, la permutation tombe
à 31,4 %. C'est la deuxième fois dans la journée qu'un contrôle juste dans
l'intention se révèle inopérant dans sa formulation.

**Un attendu démenti, qui en dit plus sur le brief 1 que sur la technique.** Le
décalage de 18 h devait casser le lien aux événements ; 2 553 mesures sur 2 560
restent dans leur fenêtre. La fenêtre d'observation du brief 1 (−48 h / +24 h)
est si large qu'elle absorbe un désalignement de trois quarts de journée. Le
rapprochement temporel est peu sélectif — à reprendre au registre.

**Constat transversal** : aucune des cinq techniques ne produit une ligne
transmissible telle quelle. Quatre sur cinq entrent en collision de clé logique
avec la mesure réelle sur 99,5 à 100 % des lignes (`R-SEN-001`). Une table
transmise à M4 mêlant réel et augmenté devra porter un identifiant distinct ou
étendre sa clé par `procedure_id`.

## Étape 3 — génération, et ce que chaque voie perd

Détail complet dans `docs/comparaison_reel_fabrique.md`. Périmètre : les 8
équipements de `SITE-OUEST` ∩ `SEG-2`, 2 capteurs, janvier 2026.

**Le résultat central du brief, mesuré.** Le tirage marginal reproduit les
marginales à 1,5 % près — écart-type 4,882 contre 4,958, quantiles alignés — et
produit des séries dont **l'autocorrélation est nulle** : +0,02 au rang 2 et
−0,02 au rang 4, là où le réel donne −0,759 et +0,803. Le cycle journalier a
entièrement disparu. Sur un histogramme, la fabrication est indétectable ; sur
l'autocorrélation, elle saute aux yeux. L'interpolation entre voisins en
conserve 48 à 75 %, mais **contracte la dispersion de 15 à 22 %** — effet
structurel de SMOTE, tout point interpolé étant intérieur au segment de ses deux
parents. Les extrêmes partent les premiers : maximum de vibration 4,47 → 4,22.

**Aucune des deux voies ne reproduit la réaction aux événements.** Le réel monte
de 7,42 % en vibration pendant les fenêtres (p < 0,0001) ; les fabriqués ne
bougent pas. Pour l'interpolation, c'est instructif : elle copie des séries
réelles qui portent cette réaction, mais les événements du donneur ne tombent
pas aux dates de la cible. **Copier une série réelle ne transporte pas son
calendrier.**

**Une précaution qui a changé la conclusion.** Le test a d'abord été mené sur le
seul mois de janvier : il ne détectait rien, y compris sur le réel (p = 0,18 et
p = 0,97). Conclure « les fabriqués ne réagissent pas » à partir d'un test
incapable de voir la réaction du réel aurait été une faute. D'où la génération
de contrôle sur tout le semestre, dédiée à cette question.

**Le contraste qui compte pour l'étape 4.** Nos contrôles de qualité ne relèvent
que **2 lignes en faute sur 3 783** — et valident donc presque intégralement
1 984 lignes de structure temporelle nulle. Ils regardent chaque ligne isolément.
C'est exactement la cécité que le lot de contrôle est construit pour sanctionner.

**Limite structurelle énoncée.** Chaque série a sa propre phase de cycle
journalier. Pour un équipement sans capteur, cette phase est une information
absente : aucune méthode ne la crée. On reproduit l'existence d'un cycle, jamais
sa phase.

**Cas limite documenté.** `EQ-DRYER-264` est un `dryer` et aucun `dryer` du parc
n'est instrumenté : ses cinq voisins sont d'autres types, la pénalité de type ne
peut pas être satisfaite. Et `EQ-OVEN-203 / vibration_mm_s` n'a produit aucune
ligne — aucun de ses voisins ne porte ce capteur. 185 points sans donneur au
total, tracés dans `generation.json`.

## Étape 4, tour 1 — ce que le détecteur voit, et ce qu'il attribue à tort

Neuf soumissions, dont **deux témoins authentiques** placés en tête : la
livraison de référence du module telle qu'elle est publiée, et un extrait de
notre préparation du brief 1 sur le périmètre exact des fabrications. Les deux
signalent — 6,24 % des lignes pour la livraison, 3,04 % pour notre préparation.
Le zéro n'est donc pas la normale du détecteur, et « zéro signalement » ne peut
pas se lire comme « authentique ».

**Les deux générateurs passent intégralement.** `PROC-GEN-MARG-V1` et
`PROC-GEN-SMOTE-V1` sortent à **0 signalement sur 1 984 et 1 799 lignes**, alors
que les témoins réels, eux, sont signalés. Le tirage marginal produit des séries
d'autocorrélation nulle — +0,02 au rang 2 contre −0,759 sur le réel, mesuré à
l'étape 3 — et le détecteur ne peut pas le voir : il déclare cet angle mort.
**Nos fabrications sont plus « propres » que le réel qu'elles imitent, et c'est
exactement ce qui devrait alerter.**

**Le défaut mesuré de SMOTE est visible dans le détail et sous le seuil.** Le
ratio d'écart-type ressort à **0,783** en température et **0,810** en vibration —
la contraction de 15 à 22 % annoncée à l'étape 3, retrouvée à l'identique par un
outil qui n'est pas le nôtre. Le seuil de signalement étant 0,70, elle passe.
Le chiffre est juste, la conclusion serait fausse.

**Un défaut d'étalonnage de 5 % passe aussi.** `PROC-AUG-ECHELLE` déplace la
moyenne de **0,391 écart-type** de référence, pour un seuil à 0,8. La fiche de
l'étape 2 classe pourtant ce procédé comme destructeur de l'ordre de grandeur.
Un contrôle de marginale ne rattrape pas un biais multiplicatif modéré.

**L'erreur du tour, et c'est la plus instructive.** J'attendais des comptages
contrastés sur les cinq procédés d'augmentation : rien pour le bruit et la
permutation, un peu pour le décalage, la totalité pour la déformation de l'axe
temporel. **Les cinq sortent à 721 signalements sur 721**, identiques au
signalement près. La cause n'est dans aucun procédé : la série support choisie à
l'étape 2, `EQ-PUMP-001`, est échantillonnée aux heures 2, 8, 14 et 20 — décalée
de deux heures par rapport à la grille attendue. C'est **le seul équipement du
parc dans ce cas**, et il porte à lui seul les 720 lignes hors grille de la
livraison. Nos cinq fabrications héritaient d'un défaut du réel, et je l'ai
attribué à nos procédés.

C'est le piège central du brief 2, rencontré sur nos propres productions avant
même de toucher au lot de contrôle : **une ligne signalée par un contrôle de
qualité n'est pas une ligne fabriquée.** Ici le détecteur ne distingue plus
`PROC-AUG-BRUIT`, inoffensif, de `PROC-AUG-DEFORM`, qui détruit la grille : les
deux rendent 721/721. Le signal utile est noyé sous le bruit de fond du support.

Le témoin manquant était évident après coup : `exemple_serie_reelle.csv`, la
série non augmentée. Soumise, elle aurait rendu 721/721 elle aussi et l'erreur
d'attribution n'aurait pas eu lieu. Un témoin par population comparée, pas un
témoin par étape.

## Étape 4, tour 2 — un générateur meilleur, le même verdict

Deux corrections, décidées à partir des comptages du tour 1.

**Le témoin manquant, d'abord.** `exemple_serie_reelle.csv` — la série support
sans aucune augmentation — rend **721 signalements sur 721**, exactement les
comptages des cinq procédés. L'erreur d'attribution du tour 1 est démontrée en
une soumission, et la règle qui s'en déduit est simple : un témoin par population
comparée, soumis avant d'ouvrir le moindre comptage.

**Le second état du générateur, ensuite.** `PROC-GEN-SMOTE-V2` reprend
exactement le contexte du premier — mêmes cibles, mêmes donneurs, même voisinage,
même flux aléatoire — et ne change qu'une chose : le coefficient d'interpolation
est tiré dans `[−0,25 ; 1,25]` au lieu de `[0 ; 1]`. Les points fabriqués ne sont
plus contraints à l'intérieur du segment joignant leurs deux parents, ce qui
s'attaque à la cause de la contraction et non à son symptôme. **614 points sur
1 799 sont extrapolés**, soit 34 %.

La dispersion remonte : le ratio d'écart-type passe de **0,783 à 0,858** en
température et de **0,810 à 0,897** en vibration. En valeur absolue, l'écart-type
de la température passe de 3,847 à 4,218 pour un réel à 4,958 — un tiers du
déficit récupéré, pas davantage.

**Deux prévisions démenties, dans deux directions opposées.**

Le coût annoncé ne s'est pas matérialisé : **aucun point ne franchit la plage
physique**. Les valeurs fabriquées se tiennent loin des bornes du capteur, et
extrapoler d'un quart de segment ne suffit pas à les en approcher. Le risque
était réel en principe, nul sur ce périmètre.

En sens inverse, l'argument qui avait fait retenir cette option est faux.
L'extrapolation devait préserver l'autocorrélation héritée des donneurs ; elle la
**dégrade** — rang 2 en température : −0,450 au premier état, **−0,383** au
second, pour un réel à −0,746. Le mécanisme se comprend après coup : la paire de
donneurs est retirée à chaque point, donc amplifier l'écart entre eux amplifie
une quantité qui change d'un instant à l'autre. C'est du bruit indépendant — le
défaut même qu'on reprochait à la correction par bruit résiduel. On a échangé un
tiers de dispersion contre 15 % d'autocorrélation, et il faut le dire ainsi.

**Le résultat qui compte est ailleurs.** Le premier état rendait 0 signalement.
Le second, mesurablement meilleur sur la dispersion et mesurablement moins bon
sur la structure, rend **0 signalement**. Le détecteur de référence est
incapable de classer deux états successifs du même générateur — non par défaut de
réglage, mais parce que ce qui les sépare est hors de son périmètre déclaré. Un
outil qui rend le même verdict à des objets différents ne peut pas guider une
amélioration. C'est ce qui rend le sens 2 nécessaire : sans règles à nous, il n'y
a aucun instrument pour arbitrer.

## Étape 4, sens 2 — nos règles sur le lot de contrôle

Détail complet dans `docs/detection_lot_controle.md`.

**La structure d'abord, les règles ensuite.** Avant d'écrire quoi que ce soit :
l'échantillon se répartit en 24 blocs de 30 lignes à provenance homogène, le lot
en 200 blocs de 30 exactement. La fabrication est par segment, pas par ligne.
Décider ligne à ligne aurait été travailler contre la structure du problème — un
verdict au bloc s'appuie sur trente observations au lieu d'une.

**La règle qui décide est un rapprochement, pas une statistique.** Un bloc dont
les trente lignes se retrouvent à l'identique dans la livraison M3, sur le même
équipement, est authentique. Les notes de version du lot déclarent que les
mesures réelles en proviennent : ce n'est pas consulter un oracle, c'est utiliser
une source publique du pack. La séparation est nette — **127 blocs retrouvés à
100 %, 66 à 0 %**, six à une ou deux coïncidences numériques, et **un seul
entre les deux**.

**Verdict sur le lot** : 3 810 lignes `réelle` (63,5 %), 2 160 `fabriquée`
(36,0 %), 30 `indécidable` (0,5 %). La proportion fabriquée tombe à 1,5 point des
37,5 % de l'échantillon — seul contrôle externe disponible, et il est cohérent.

**Le plafond, et il n'est pas déplaçable.** `EQ-PUMP-171 / vibration_mm_s` est
étiqueté fabriqué et ses trente lignes sont identiques à la livraison — mêmes
horodatages, mêmes valeurs à la deuxième décimale. Rien d'interne ne peut le
distinguer d'une mesure réelle, parce qu'il n'en diffère par rien. C'est la seule
erreur du calibrage (30 lignes sur 720, 95,8 % de justes) et elle est
structurelle. La question part à la remontée formateur : le lot ne dit pas si
« fabriqué » qualifie le procédé appliqué ou le contenu obtenu, et la différence
décide de ce qui est détectable.

**Pourquoi les signatures internes ne décident pas.** Autocorrélation, grille,
niveau, dispersion, greffe : ces cinq règles corroborent. Portées à la décision,
elles auraient déclaré fabriqués **21 blocs authentiques sur 127**.
`R-DET-010` est la plus productive — 45 blocs fabriqués attrapés — et la plus
dangereuse : 14 blocs réels accusés. Seules la grille irrégulière et la greffe
inter-équipements n'accusent jamais à tort, et ce sont les deux qui reposent sur
un fait vérifiable plutôt que sur un seuil.

**Onze blocs fabriqués sur 72 ne portent aucune signature interne** — 330 lignes
dont l'autocorrélation, la dispersion, la grille et le niveau sont conformes à ce
qu'on attend du réel. Sans le rapprochement, elles passaient. C'est la même
conclusion que le sens 1, prise par l'autre bout.

**La contre-épreuve, et c'est le chiffre à retenir.** Nos dix règles capteurs du
brief 1, employées comme test d'authenticité sur les 6 000 lignes : **rappel
15,3 %, 343 lignes authentiques accusées, précision 49,0 %.** Une pièce lancée en
l'air fait 50 %. Cinq des règles qui signalent — unité, nom de capteur, étiquette
de période, clé logique, sentinelle — **n'attrapent que des lignes authentiques**.
Les quarante lignes du capteur `TEMPERATURE_C ` (majuscules et espace parasite)
sont toutes retrouvées dans la livraison : signalées à juste titre par la qualité,
authentiques sans discussion.

Ces règles ne sont pas mauvaises. Elles répondent à une autre question, et hors
de leur objet elles ne produisent que des fausses accusations.

## Étape 5 — protéger le coût moyen des pièces

Détail complet dans `docs/confidentialite_agregats.md`. Agrégat choisi
(arbitrage A4) : coût moyen des pièces par site × criticité — seize cellules,
effectifs de 4 à 319 interventions. Le choix d'une **moyenne** plutôt que d'un
comptage rend la sensibilité intéressante : elle dépend de l'amplitude des
valeurs, et le tableau met une cellule à 4 interventions à côté d'une à 319.

**Deux décisions prises avant tout calcul.** Borner les coûts, parce que sans
plafond déclaré la sensibilité serait le maximum observé — 1 127,58 € — qui est
lui-même une donnée du jeu : le prendre comme paramètre revient à le publier en
creux. Et partager le budget entre la somme et l'effectif, parce qu'une moyenne
est un quotient et qu'un effectif exact publié à côté d'une somme bruitée laisse
fuiter l'effectif, information sensible sur une cellule à quatre lignes.

**Le plafond n'est pas une donnée du problème, c'est un arbitrage.** À `ε = 1` :
tronquer à 500 € donne 13,18 € de biais pour 9,08 € de bruit — 23,60 € d'erreur
totale ; ne pas tronquer donne 0 de biais pour 18,19 € de bruit. Le minimum est
au milieu : **750 €, 13,64 € d'erreur totale**, 0,89 % de la masse coupée.
Contre-intuition utile relevée au passage : à 500 € la conclusion est mieux
conservée (83 %) qu'à 750 € (79 %) malgré une erreur double, parce qu'un biais de
troncature est systématique — il déplace tout le tableau du même côté — tandis
que le bruit déplace chaque cellule indépendamment. **Deux erreurs de même taille
n'ont pas le même effet sur ce qu'on veut lire.**

**Les deux bornes ne se rejoignent pas.** À `ε = 0,1`, aucune des seize cellules
n'est exploitable. À `ε = 20`, quinze le sont — mais l'adversaire retrouve le coût
de l'intervention qu'il cible une fois sur deux. La zone de compromis est étroite,
entre 2 et 5 : la moitié aux deux tiers des cellules lisibles, un adversaire qui
réussit dans 8 à 15 % des cas. **Un `ε` unique pour tout le tableau est
indéfendable**, et c'est le résultat de l'étape.

**Deux corrections à l'intuition.** L'effectif ne décide pas seul :
`SITE-OUEST / high`, 14 interventions, reste lisible à 99,8 % parce que son coût
moyen (81,90 €) s'écarte massivement de la moyenne générale (217,49 €). Ce qui
compte est le rapport entre l'écart à mesurer et le bruit. Et une conclusion peut
échouer sans que le mécanisme y soit pour rien : `SITE-OUEST / low` vaut
219,18 € contre 217,49 € de moyenne — **1,69 € d'écart**. À `ε = 50`, la
conclusion n'est encore juste que 59 % du temps. La question n'a pas de réponse
robuste pour cette cellule, et dépenser du budget dessus serait du gaspillage.

**La sortie n'est pas le budget, c'est la maille.** À `ε = 5`, la publication par
criticité seule est exploitable sur ses 4 cellules quand la maille croisée en
laisse 5 sur 16 inutilisables. Protéger un agrégat trop peu fourni ne s'achète
pas en budget : on renonce à la finesse.

**Erreur commise et corrigée en cours d'étape.** La première version mesurait la
protection par la part des tirages où la moyenne vraie était retrouvée à 10 %
près. Résultats absurdes — 98 % de « réidentification » sur la cellule à 319
interventions dès `ε = 1`, et la conclusion que les grandes cellules seraient les
moins protégées. L'erreur est de raisonnement : la confidentialité différentielle
ne promet pas de cacher un agrégat, elle borne ce que la publication révèle d'une
observation isolée. L'indicateur mesurait la précision et l'appelait
vulnérabilité. Remplacé par l'attaque par différenciation, qui suit le modèle de
menace annoncé — et qui redonne le résultat théorique attendu : **la protection ne
dépend pas de l'effectif**.

**Trouvaille pour l'étape 6.** Sur 28 coûts de pièces non renseignés dans les
1 788 interventions, **27 sont sur `SITE-OUEST`** — 35 % de ses interventions. Le
site le moins instrumenté est aussi le moins renseigné : les lacunes se cumulent
au lieu de se compenser.

## Étape 6 — transmettre, et ce que la transmission a révélé

**Hypothèses formulées avant exécution.** Trois, écrites avant d'écrire
`run_transmission_b2.py` :

1. la génération améliorera la couverture du parc de façon **négligeable** —
   8 équipements sur 416, soit environ 2 points ;
2. le gain en documentation d'événements sera **nul ou presque** : le périmètre
   généré est petit et la période courte ;
3. le jeu transmis passera le détecteur de référence **sans manquement au
   contrat**, les colonnes de provenance étant appliquées en un seul endroit.

La première est vérifiée (8,65 % → 10,58 %). La deuxième est vérifiée sur le
parc et **fausse sur le périmètre** : le gain est de 3 événements sur 514 au
global, mais de **3 sur 3** dans la période générée — la génération documente
tout ce qu'elle pouvait documenter. C'est une distinction qui compte : « le gain
est négligeable » et « la méthode a échoué » sont deux énoncés différents, et
seul le premier est vrai. La troisième est **fausse**, et c'est le résultat
principal de l'étape.

### Décision de composition

Arbitrage tranché le 31/08 : **une partie sous conditions**. Le réel complet plus
les 1 799 lignes de `PROC-GEN-SMOTE-V2`, soit 3,45 % de fabriqué. Sont exclus le
tirage marginal, l'état 1 du générateur et les cinq augmentations — motifs au
registre des procédés.

Ce qui a porté la décision n'est pas une préférence de principe mais un résultat
du tour 2 : **le détecteur a rendu le même zéro sur deux états successifs du
générateur dont l'un était mesurablement moins bon** (T2-01). Nous transmettons
donc un procédé sans instrument capable de confirmer qu'il est le meilleur.
D'où l'étiquetage, le cloisonnement, et l'interdiction d'usage en évaluation
plutôt qu'une transmission franche ou un refus.

### Ce que la couverture devient — et le piège qu'elle tend

| | Réel | Après transmission |
|---|---|---|
| parc couvert | 36 / 416 — 8,65 % | 44 / 416 — 10,58 % |
| `SITE-OUEST` | 0 / 16 | 8 / 16 — **100 % fabriqué** |
| taux `critical` / taux `low` | 30,43 % / 1,33 % — **×22,9** | 34,78 % / 4,00 % — **×8,7** |

Le rapport de couverture entre équipements critiques et non critiques est divisé
par 2,6 **sans qu'un seul équipement supplémentaire ait été instrumenté**. C'est
l'observation la plus utile de l'étape : une atténuation par fabrication corrige
l'indicateur et pas le phénomène. Elle a produit la condition C7 — ne jamais
compter la couverture sans filtrer sur la provenance.

### Un défaut de notre chaîne, resté invisible tout le brief 1

La soumission T3-00 a signalé **68 lignes en `R-PRECISION`**, famille de règle
qu'aucune soumission des tours 1 et 2 n'avait déclenchée. Toutes réelles, toutes
sur `EQ-SENSOR-305` : ce capteur livre 84 mesures en kelvins, que `R-SEN-006`
convertit par `v − 273,15` et écrit telles quelles — `56.85000000000002`.

La conversion est juste. C'est l'écriture qui est fautive, et **aucune des 34
règles du brief 1 ne contrôlait la sortie de ses propres transformations**. Le
défaut a traversé le module entier, la note de décision, la persistance en base,
et n'est apparu que le jour où le fichier a été soumis à un contrôle extérieur.

Deux enseignements, notés pour la suite :

- **un contrôle qui ne s'applique qu'aux données reçues laisse un angle mort de
  la taille de tout ce qu'on produit soi-même** ;
- **c'est la soumission du livrable, et non des cas de démonstration, qui l'a
  trouvé.** Les quinze soumissions des tours 1 et 2 portaient sur des extraits
  fabriqués ou des témoins ; aucune ne portait sur le fichier réellement destiné
  à sortir.

Corrigé par `R-TRA-001` au point de transmission — pas dans `prepare_sensors`,
pour ne pas invalider les empreintes des deux briefs rendus. La dette est
inscrite au registre des règles.

## Exécutions du détecteur de référence

Chaque exécution de `tools/verify_synthetic.py` est consignée ici, avec
l'hypothèse formulée **avant** le lancement. Les hypothèses du tour 1 sont
inscrites dans `run_detection_b2.py`, figées à l'écriture du script et non
rédigées après lecture des comptages. Une série d'essais sans hypothèse n'est
pas une démarche, et l'omission est un critère bloquant du brief.

| # | Date | Fichier soumis | Hypothèse formulée avant | Comptages retournés | Ce que ça apprend | Changement effectué |
|---|---|---|---|---|---|---|
| T1-00 | 26/08 | `data_pack/…/sensors/sensor_readings.csv` (témoin, livraison publiée) | la livraison n'est pas exempte de défauts ; comptages non nuls attendus sur R-FORMAT et R-RANGE ; R-DISTRIB trivialement conforme puisque ce fichier sert à calculer le profil | 50 401 l. — **3 145 signalements (6,24 %)** : R-FORMAT 1 445, R-RANGE 856, R-UNIT 804, R-FK 30, R-KEY 10 ; 0 capteur signalé en distribution | **hypothèse vérifiée.** Le seuil de lecture n'est pas zéro : le réel publié est signalé une ligne sur seize | témoin de référence retenu pour tout le tour |
| T1-01 | 26/08 | `output/detection/temoin_reel.csv` (témoin, notre préparation, janvier, 2 capteurs) | taux faible mais non nul, porté par R-FORMAT (5 lignes hors période et 720 hors grille sur 50 277 avant filtrage) | 4 080 l., 30 équipements — **124 signalements (3,04 %)** : R-FORMAT 120, R-RANGE 4 ; distribution conforme (écarts 0,011 et 0,029 σ) | **vérifiée.** Sur le périmètre exact des fabrications, l'authentique se signale à 3 % | seuil de comparaison fixé à 3,04 % |
| T1-02 | 26/08 | `mesures_PROC-GEN-MARG-V1.csv` | zéro ligne signalée et distribution conforme, alors que l'autocorrélation est nulle ; si vérifié, la démonstration que le silence ne prouve rien | 1 984 l. — **0 signalement**, aucune famille déclenchée ; ratios σ 0,956 et 0,994 | **vérifiée exactement.** Une série sans aucune structure temporelle est déclarée conforme, et plus propre que les deux témoins réels | aucun — le résultat *est* le livrable |
| T1-03 | 26/08 | `mesures_PROC-GEN-SMOTE-V1.csv` | zéro ligne signalée ; ratio σ inférieur à 1 sous l'effet de la contraction mesurée (15 à 22 %), mais au-dessus du seuil de 0,70 | 1 799 l. — **0 signalement** ; ratios σ **0,783** (temp.) et **0,810** (vib.), non signalés | **vérifiée au chiffre près.** Le défaut est présent dans la sortie du détecteur, sous son seuil : un contrôle par seuil ne remplace pas la lecture du détail | corriger la dispersion au tour 2 et resoumettre |
| T1-04 | 26/08 | `exemple_PROC-AUG-BRUIT.csv` | zéro ligne signalée (σ = 2 %) ; provenance absente et colonne `row_identifier` inattendue signalées comme manquement au contrat | 721 l. — **721 signalements**, tous R-FORMAT ; provenance absente, `row_identifier` inattendue | **fausse sur le comptage.** La cause n'est pas le procédé : la série support est hors grille. Le volet colonnes est confirmé | ajouter `provenance`/`procedure_id`, retirer `row_identifier` |
| T1-05 | 26/08 | `exemple_PROC-AUG-ECHELLE.csv` | aucun signalement de distribution : ×1,05 déplace la moyenne d'environ 0,05 σ pour un seuil à 0,8 — un défaut documenté par nous devrait passer | 721 l. — **721 R-FORMAT** (support) ; distribution **non signalée**, écart **0,391 σ**, ratio 0,894 | **vérifiée sur R-DISTRIB, fausse sur le total.** L'écart réel est huit fois ma prévision et reste sous le seuil : le procédé est bien invisible, mais moins loin du seuil que je ne le pensais | conserver comme cas de biais non détecté |
| T1-06 | 26/08 | `exemple_PROC-AUG-DECALAGE.csv` | R-FORMAT faible et non nul (18 h est un multiple du pas, seules les lignes sorties de la période sont fautives) | 721 l. — **721 R-FORMAT** | **fausse.** Le décalage préserve bien la grille — mais la grille de départ était déjà fausse. Le comptage ne mesure pas ce que le procédé fait | soumettre la série support non augmentée au tour 2 |
| T1-07 | 26/08 | `exemple_PROC-AUG-PERMUT.csv` | zéro signalement sur une série dont la structure temporelle est entièrement détruite — le cas d'aveuglement le plus net | 721 l. — **721 R-FORMAT**, marginales identiques au réel (moyenne 2,863, ratio 0,852) | **fausse sur le comptage, vraie sur le fond** : la permutation rend exactement les mêmes chiffres que le bruit, la destruction est invisible | démonstration reportée sur T1-02, non affectée par le support |
| T1-08 | 26/08 | `exemple_PROC-AUG-DEFORM.csv` | R-FORMAT proche de la totalité des lignes : la grille est détruite dès la première déformation ; seul procédé franchement attrapé | 721 l. — **721 R-FORMAT**, identique aux quatre autres | **juste pour une mauvaise raison.** Le comptage était déjà à 721 avant toute déformation : la prédiction est confirmée par un chiffre qui ne la teste pas | isoler la contribution du procédé au tour 2 |
| T2-00 | 26/08 | `exemple_serie_reelle.csv` (témoin manquant du tour 1) | 721 signalements sur 721 en R-FORMAT **avant toute augmentation** ; si vérifié, aucune conclusion du tour 1 ne peut être attribuée à nos procédés | 721 l. — **721 R-FORMAT**, exactement les comptages des cinq augmentations | **vérifiée.** L'attribution du tour 1 était fausse, et la preuve tient en une soumission | témoin systématique avant toute lecture de comptage |
| T2-01 | 26/08 | `mesures_PROC-GEN-SMOTE-V2.csv` (λ ∈ [−0,25 ; 1,25]) | dispersion restaurée, ratio σ nettement plus proche de 1 ; R-RANGE non nul attendu, les extrapolations pouvant franchir la plage ; **et un verdict du détecteur égal ou pire que le premier état** | 1 799 l. — **0 signalement** ; ratios σ **0,858** et **0,897** (contre 0,783 et 0,810) ; 614 points extrapolés, **0 hors plage physique** | **vérifiée sur le classement, fausse sur le coût.** Le générateur s'améliore, le détecteur rend le même zéro : il ne peut pas arbitrer entre deux états. Le franchissement de plage annoncé n'a pas eu lieu | nos propres règles deviennent nécessaires — passage au sens 2 |
| T2-02 | 26/08 | `PROC-AUG-BRUIT.csv` (normalisé) | provenance déclarée et colonne de travail retirée ; R-FORMAT inchangé à 721, le défaut venant du support | 721 l. — **721 R-FORMAT**, provenance présente, aucune colonne inattendue | **vérifiée.** Le manquement au contrat est corrigé, le signalement de fond ne bouge pas : deux problèmes distincts | correction de contrat à reporter dans le générateur d'exemples |
| T2-03 | 26/08 | `PROC-AUG-DECALAGE.csv` (normalisé) | mêmes 721 R-FORMAT : le décalage de 18 h préserve le pas, la grille était déjà fausse | 721 l. — **721 R-FORMAT** | **vérifiée** | — |
| T2-04 | 26/08 | `PROC-AUG-DEFORM.csv` (normalisé) | 721 R-FORMAT, indiscernable des autres : la destruction de la grille ne peut pas s'ajouter à un comptage saturé | 721 l. — **721 R-FORMAT** | **vérifiée.** Un comptage saturé ne mesure plus rien — il faut changer de support, pas de règle | support conforme exigé pour toute mesure de procédé |
| T2-05 | 26/08 | `PROC-AUG-ECHELLE.csv` (normalisé) | écart de distribution inchangé à 0,391 σ, sous le seuil de 0,8 | 721 l. — **721 R-FORMAT**, écart **0,391 σ**, non signalé | **vérifiée** | conservé comme cas de biais non détecté |
| T2-06 | 26/08 | `PROC-AUG-PERMUT.csv` (normalisé) | 721 R-FORMAT et marginales identiques au réel ; destruction de la structure invisible | 721 l. — **721 R-FORMAT**, moyenne et ratio σ identiques au bruit | **vérifiée** | — |
| T3-00 | 31/08 | `output/transmission/sensor_readings_m4.csv` — **le livrable**, 52 076 l. | contrat respecté (provenance présente, `row_identifier` retirée) ; R-FORMAT ≈ 725 soit 1,4 %, porté par les 720 horodatages hors grille et les 5 lignes hors période du brief 1 ; R-DISTRIB conforme, 3,45 % de fabriqué ne déplaçant aucune marginale ; R-FK et R-KEY nuls. Hypothèse figée dans `output/transmission/hypothese_T3.md` | 52 076 l. — R-FORMAT **725 (1,39 %)**, R-RANGE **52**, **R-PRECISION 68**, R-SCHEMA/R-UNIT/R-KEY/R-FK 0 ; R-DISTRIB 0 capteur sur 5 | **vérifiée sur le contrat et le format, incomplète sur deux familles.** R-RANGE 52 = 40 valeurs vides à la livraison + 12 sentinelles `-999` volontairement neutralisées : attendu, non anticipé. **R-PRECISION 68 est un défaut de notre chaîne** — conversion K → °C de `R-SEN-006` écrivant `56.85000000000002`, invisible pendant tout le brief 1 | création de `R-TRA-001`, arrondi à la convention de la livraison au point de transmission |
| T3-01 | 31/08 | le même jeu, après `R-TRA-001` (68 valeurs arrondies) | R-PRECISION passe à **0**, tous les autres compteurs strictement inchangés ; si un autre bouge, l'arrondi a touché autre chose que la précision d'écriture | 52 076 l. — **R-PRECISION 0**, R-FORMAT 725, R-RANGE 52, reste à 0 ; R-DISTRIB conforme, ratios σ 0,99 à 1,00 | **vérifiée exactement.** Le correctif est ciblé : il supprime le défaut sans effet de bord mesurable | jeu transmis figé ; dette du correctif amont inscrite au registre |

## Point ouvert repris du brief 1

La remontée formateur (`docs/remontee_formateur.md`) reste **non envoyée**. La
contradiction `SCHEMA.md` / `contracts/schemas.py` sur `event_type` — `alerte`
annoncé contre `alert` livré — est **toujours présente** dans la publication du
25/08, désormais ligne 184. Elle traverse deux publications successives.
