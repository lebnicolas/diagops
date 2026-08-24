---
module: M3
etat: axe 6 terminé
maj: 2026-08-24
---

# Flux de traitement et cycle de vie du jeu de données — M3

## Destinataires

Ce document est écrit pour trois lecteurs qui n'ont pas les mêmes questions.

| Destinataire | Ce qu'il doit pouvoir en tirer |
|---|---|
| **L'équipe technique** qui reprendra la pipeline (M4 et au-delà) | Suivre une ligne de la source à la sortie, savoir où elle peut être écartée et par quelle règle, rejouer l'ensemble par une commande |
| **Le métier maintenance** qui exploitera les résultats | Savoir ce que le jeu couvre et ce qu'il ne couvre pas, à quelle fréquence il se rafraîchit, et à partir de quand une conclusion cesse d'être valable |
| **La personne chargée de la conformité** | Savoir d'où viennent les données, ce qu'elles permettent de reconstituer indirectement, combien de temps elles sont conservées et sous quelle forme |

Ces documents sont **périssables**. Ils décrivent l'état au 24/08/2026 et doivent
être remis à jour à chaque nouvelle source ou nouvelle livraison — pas écrits une
fois pour toutes.

## Flux de traitement

```text
data_pack/2026-S1/                          (lecture seule, jamais modifié)
│
├── sensors/sensor_readings.csv ────────────┐  50 401 lignes
├── reference_runs/m2_for_m3/processed/     │
│     ├── equipment.csv ───────────┐        │     416
│     ├── events.csv ──────────────┤        │     514
│     └── maintenance_history.csv ─┤        │   1 788
└── reference_runs/m2_for_m3/               │
      quarantine/quarantine_m2.csv ─┐       │      35
                                    │       │
        ┌───────────────────────────┴───────┴──────────────────┐
        │                                                       │
   [1] run_cadrage_m3.py                    [2] run_audit_temporel_m3.py
   décrit — ne décide rien                  décrit — ne décide rien
        │                                                       │
   output/cadrage/                          output/audit/
   7 CSV + cadrage.json                     5 CSV + audit_temporel.json
        │                                                       │
        └──────────────────────┬────────────────────────────────┘
                               │  (les constats alimentent les règles)
                               ▼
                  [3] run_pipeline_m3.py   ← SEUL script qui décide
                      34 règles appliquées
                               │
        ┌──────────────────────┼───────────────────────┬────────────────┐
        ▼                      ▼                       ▼                ▼
output/processed/       output/quarantine.csv   output/registre_    contrôle de
  equipment.csv    416     1 833 lignes           regles.csv        NON-RÉGRESSION
  events.csv       514     (4 sources)            34 règles         (bloquant)
  maintenance…   1 788
  sensor_readings…      50 277
        │
        ▼
   [4] run_rapprochement_m3.py
       fenêtre 48 h / 24 h
        │
        ├──► output/alignment/mesures_evenements.csv        2 610 lignes
        ├──► output/alignment/evenements_sans_mesure.csv       425
        └──► output/aggregates/agregats_par_evenement.csv      175
```

### Où une ligne peut être écartée, et par quelle règle

| Étape | Entrée | Sortie | Ligne écartée ? | Règle |
|---|---|---|---|---|
| Normalisation du nom de capteur | `sensor_name` reçu | nom normalisé | non — corrigée et tracée | `R-SEN-005` |
| Capteur hors domaine | nom normalisé | — | **oui** | `R-SEN-005` |
| Horodatage | `timestamp` reçu | instant UTC | **oui** si illisible (0 cas) | `R-SEN-002` |
| Unités | `value` + `unit` | valeur en unité de référence | **oui** si non convertible (0 cas) | `R-SEN-006` |
| Sentinelles | valeur numérique | valeur ou vide | non — champ neutralisé, ligne gardée | `R-SEN-008` |
| Valeur manquante | valeur | vide tracé | non | `R-SEN-007` |
| Étiquette de période | `period` | `2026-S1` | non | `R-SEN-015` |
| Hors période | instant UTC | — | non — conservée et signalée | `R-SEN-014` |
| Grille horaire | instant UTC | — | non — signalée au niveau série | `R-SEN-003` |
| Équipement hors parc | `equipment_id` | — | **oui** (30 lignes) | `R-SEN-013` |
| Clé dupliquée, doublon strict | clé logique | 1 ligne sur 2 | **oui** (6 lignes) | `R-SEN-001` |
| Clé dupliquée, valeurs divergentes | clé logique | — | **oui, les deux** (8 lignes) | `R-SEN-001` |
| Capteur figé | série | — | **oui** (80 lignes) | `R-SEN-010` |
| Plage, dérive, saut, continuité | série | — | non — signalés | `R-SEN-009/011/012/004` |

**Bilan : 50 401 reçues → 50 277 préparées.** 124 lignes écartées, soit 0,25 %.
Toutes sont retrouvables en quarantaine par leur `row_identifier`.

### Suivre une ligne d'un bout à l'autre

Exemple concret, une ligne réellement écartée :

1. Le fichier reçu contient `EQ-CHILL-115 | 2026-03-13T18:00:00Z | temperature_c | 66.45 | °C | 2026-S1`.
2. `R-SEN-005` : le nom est déjà normalisé, rien à faire.
3. `R-SEN-002` : l'horodatage porte un `Z`, converti sans hypothèse.
4. `R-SEN-006` : l'unité `°C` est conforme au contrat.
5. `R-SEN-001` : **une autre ligne porte la même clé avec la valeur 55,72**. Les
   deux sont exclues.
6. La ligne apparaît dans `output/quarantine.csv` avec
   `row_identifier = EQ-CHILL-115|2026-03-13T18:00:00Z|temperature_c`,
   `rule_id = R-SEN-001`, `decision = exclue`.
7. Elle n'apparaît pas dans `output/processed/sensor_readings.csv`.
8. Effet de bord tracé : `R-SEN-004` signale ensuite une reprise
   d'échantillonnage le 14/03 à 00:00 — le trou créé par cette exclusion.

### Commande qui rejoue l'ensemble

```bash
cd work/M3
python -m venv .venv && .venv/Scripts/activate    # Windows
python -m pip install -r requirements.lock

python run_cadrage_m3.py
python run_audit_temporel_m3.py
python run_pipeline_m3.py          # code de sortie ≠ 0 si la non-régression échoue
python run_rapprochement_m3.py

python -m pytest -q                # 56 tests
```

**Coût de rejeu : 9,4 s** pour la chaîne complète (4,4 + 1,4 + 2,9 + 0,7 s,
médianes sur 3 exécutions, dont environ 2 s de démarrage de l'interpréteur et de
pandas par script). L'installation de l'environnement prend environ 2 minutes.

## Cycle de vie du jeu de données

| Question | Réponse |
|---|---|
| **Origine : qui produit ces données ?** | L'export de la supervision d'exploitation pour les mesures capteurs ; la GMAO pour les événements et les interventions ; le référentiel technique pour le parc. **Non vérifié directement** — voir la réserve ci-dessous. |
| **Fréquence de livraison** | Une livraison par semestre (`2026-S1`), au pas d'échantillonnage de 6 h. Le `MANIFEST.yaml` annonce `2026-S2` pour M5 et `2027-S1` pour M6 : la cadence semestrielle est donc la seule confirmée. |
| **Format et mode d'accès** | CSV UTF-8, une ligne par mesure, sans identifiant de ligne. Reçu par dépôt de fichier dans `data_pack/`, accompagné d'un `MANIFEST.yaml`, d'un `SCHEMA.md`, d'une `DATA_CARD.md` et de `checksums.sha256`. |
| **Durée et forme de conservation** | Voir la règle de conservation ci-dessous et `couverture_et_risques.md`. |
| **Qui accède aux données préparées ?** | L'équipe technique et le métier maintenance via le dépôt. Les sorties `output/` sont versionnées avec le code — elles sont donc aussi lisibles que le dépôt lui-même. |
| **Nouvelle période** | La pipeline est rejouable telle quelle : `DIAGOPS_DATA_DIR` désigne le dossier de données. Trois points sont à revalider à chaque livraison, ils ne sont **pas** garantis stables (voir « Points à revoir »). |
| **À partir de quand ces données cessent d'être utilisables ?** | Deux échéances distinctes : le **parc** évolue (mises en service, retraits), donc un rapprochement mesure ↔ équipement vieillit dès qu'un équipement change ; et la **dérive** identifiée sur `EQ-CHILL-248` est encore en cours à la fin de la période, ce qui signifie qu'une conclusion tirée de ce semestre sur cet équipement est déjà périmée au semestre suivant. |

### Réserve sur l'existence, la disponibilité et l'accès

Le brief demande de **vérifier** l'existence, la disponibilité et les conditions
d'accès de la source. Ce qui précède est une **reconstitution à partir des
documents livrés** (`MANIFEST.yaml`, `DATA_CARD.md`, `SCHEMA.md`), pas une
vérification auprès du producteur.

Ce qui est réellement vérifié : le fichier existe, son volume est conforme à
l'annonce (50 401 lignes), son empreinte SHA-256 est stable
(`455b85fe…`), il est encodé en UTF-8 valide, et son contenu est cohérent avec le
`MANIFEST` sur le pas nominal et le nombre d'équipements instrumentés.

Ce qui ne l'est pas : l'identité du système producteur, le procédé d'export, la
conduite à tenir si une livraison manque, et l'existence d'un engagement de
service. Dans un contexte réel, ces points se règlent par un échange avec
l'exploitation — pas par l'analyse du fichier. **Ils sont donc énoncés comme
hypothèses, pas comme faits.**

### Ce qui reste disponible pour les 380 équipements non couverts

La source capteurs n'atteint que 36 équipements sur 416. Pour les autres, ce qui
reste dans le corpus :

| Ressource | Ce qu'elle apporte | Ce qu'elle ne remplace pas |
|---|---|---|
| `events.csv` | 425 événements sur équipements non instrumentés : type, sévérité, début, fin | Aucun signal **continu** — on sait qu'il s'est passé quelque chose, pas ce qui montait avant |
| `maintenance_history.csv` | Interventions, durées d'indisponibilité, pièces, résultat | Idem — de l'événementiel, pas de la mesure |
| `equipment.csv` | Type, site, criticité, puissance nominale, date de mise en service | Descriptif statique |

**Solution de remplacement retenue : aucune.** Il n'existe pas, dans le corpus,
de substitut à une mesure continue. Un relevé porté par les interventions serait
ponctuel, non calibré et biaisé par construction — on ne relève que lorsqu'on
intervient. Prétendre reconstituer une série temporelle à partir de là
produirait un signal faux avec une apparence de complétude, ce qui est pire que
l'absence.

**L'absence est donc assumée et documentée**, ce que le brief admet
explicitement comme réponse recevable. La conséquence pratique est portée dans
`couverture_et_risques.md` et dans la décision : tout travail fondé sur les
mesures ne vaut que pour 8,65 % du parc.

## Règle de conservation retenue

Mesurée sur la livraison réelle, puis extrapolée :

| Forme | Volume | Lignes | Rapport |
|---|---:|---:|---:|
| Brut reçu (1 semestre, 36 équipements) | **3,16 Mo** | 50 401 | référence |
| Préparé | **5,71 Mo** | 50 277 | × 1,8 |
| Agrégats par événement | **0,026 Mo** | 175 | **÷ 122** |

Extrapolations :

| Scénario | Volume brut |
|---|---:|
| Parc entier instrumenté (× 11,6), un semestre | 36,5 Mo |
| Parc entier, 5 ans (10 semestres) | **365 Mo** |
| Parc entier, pas de 1 min au lieu de 6 h (× 360) | **13,1 Go / semestre** |

**Règle retenue : conserver le brut ET les agrégats, avec des durées
différentes.**

- **Brut : conservé intégralement**, sans expiration décidée à ce stade. À
  l'échelle actuelle et même extrapolée au parc entier sur cinq ans, 365 Mo ne
  justifient aucun arbitrage : le coût de stockage est négligeable devant le coût
  d'une donnée détruite qu'on ne peut pas régénérer. Les mesures brutes sont la
  seule source qui permette de rejouer un audit avec des règles différentes — et
  ce module a montré trois fois que les règles changent.
- **Agrégats : recalculés, jamais archivés seuls.** Ils sont 122 fois plus petits
  mais ils perdent l'ordre et la forme (voir axe 5). Les conserver sans le brut
  reviendrait à figer définitivement un choix de fenêtre et de grain.
- **Rien n'est écarté** pour raison de volume.

**Le seuil qui changerait cette règle est identifié** : un passage à un pas de la
minute ferait franchir les 13 Go par semestre, soit 260 Go sur cinq ans pour le
parc entier. À cette échelle, l'arbitrage devient réel : conserver le brut sur
une fenêtre glissante (par exemple 18 mois) et des agrégats horaires au-delà.
Cette règle-là n'a pas lieu d'être appliquée aujourd'hui, mais elle est le point
de bascule à surveiller.

### Une inefficacité constatée, à corriger

Le fichier **préparé est 1,8 fois plus gros que le brut** (5,71 Mo contre 3,16),
pour 124 lignes de **moins**. Deux causes : la colonne `row_identifier`, qui
duplique les trois colonnes de la clé logique, et les horodatages réécrits en
ISO complet avec fuseau.

`row_identifier` est utile — il fait le lien avec la quarantaine — mais il est
recalculable à tout moment à partir des trois colonnes qui restent dans le
fichier. À l'échelle actuelle c'est sans conséquence ; extrapolé au parc entier
au pas de la minute, cela représenterait plusieurs gigaoctets de redondance pure.
**Point à traiter avant toute montée en volume**, pas maintenant.

## Description du jeu de données, mise à jour

L'ajout de la source capteurs change trois choses.

**Ce que le jeu contient désormais** : une dimension **temporelle continue**, qui
n'existait pas en M2. Les trois tables M2 décrivaient un parc, des événements et
des interventions — c'est-à-dire des faits ponctuels et leur contexte. La source
capteurs décrit ce qui se passe **entre** deux interventions, pour une partie du
parc. C'est la première source du corpus dont la valeur tient à sa continuité et
non à ses lignes prises isolément.

**Ce qu'il ne contient toujours pas** :

- de mesure pour 380 équipements sur 416 — dont l'intégralité de `SITE-OUEST` et
  sept types d'équipement, `press` (34) et `valve` (21) compris ;
- de signal continu antérieur au 28/12/2025 ni postérieur au 04/07/2026 ;
- d'étiquette de défaillance : les événements sont des **déclarations**
  d'exploitation, pas une vérité terrain, et l'axe 5 a montré qu'ils manquent
  précisément l'épisode le plus sévère ;
- de seconde mesure indépendante de la même grandeur, ce qui rend indécidable la
  question capteur/procédé sur la dérive de `EQ-CHILL-248`.

**Ce qu'il permet de conclure — et ce qu'il ne permet pas** :

| Permet | Ne permet pas |
|---|---|
| Décrire le comportement des 36 équipements instrumentés sur un semestre | Généraliser au parc — l'échantillon est biaisé vers les équipements critiques |
| Détecter des comportements anormaux de capteur (figé, dérive, saut, sentinelle) | Distinguer une dérive de capteur d'une dérive de procédé |
| Rapprocher 89 événements de mesures qui les précèdent et les suivent | Établir une relation de cause à effet |
| Construire des agrégats par événement | Dire si une variation précède ou suit l'événement — l'agrégat perd l'ordre |
| Constituer une base d'apprentissage pour M4 | Prétendre qu'elle couvre les cas sévères : le pic à 9,76 mm/s n'est apparié à aucun événement |

## Points à revoir

À la **prochaine livraison** (`2026-S2`, ouverte en M5) :

| Point | Pourquoi il n'est pas acquis |
|---|---|
| Le parc instrumenté | Rien ne garantit qu'il reste le même. Les taux de couverture doivent être recalculés, pas repris. |
| Les unités | Deux capteurs sur cinq ont été livrés dans une unité non conforme ce semestre. Le contrôle doit rester actif. |
| L'hypothèse de fuseau | Elle porte sur une série entière. Si le format d'horodatage se stabilise, l'hypothèse disparaît ; s'il change encore, elle doit être réexaminée. |
| Les seuils de détection | Quatre ont dû être corrigés en M3 après avoir produit des résultats faux. Ils sont calibrés sur **ce** semestre. |
| La dérive de `EQ-CHILL-248` | Elle est en cours à la fin de la période. Le semestre suivant dira si elle se poursuit, se stabilise ou a été traitée — c'est le test qui manque aujourd'hui. |
| L'épisode `EQ-FAN-304` | Vérifier si un événement a fini par être déclaré rétroactivement, ou si l'absence est définitive. |

À l'occasion de **M4** : ce document doit être relu avant toute construction de
modèle, en particulier la ligne « ne permet pas » du tableau ci-dessus.
