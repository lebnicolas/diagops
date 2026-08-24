---
module: M3
brief: présentiel — étendre la pipeline DiagOps aux mesures capteurs
etat: brief présentiel terminé — axes 1 à 8, douze questions traitées
maj: 2026-08-24
---

# Diagnostic multi-source DiagOps — M3

> État de ce document : **les huit axes du brief présentiel sont traités**, et
> les douze questions du diagnostic reçoivent une réponse. Les axes 6, 7 et 8
> ont leur document dédié, listé en fin de page.
> Aucun chiffre de ce document n'est saisi à la main : tous proviennent de
> `output/cadrage/cadrage.json`, `output/audit/audit_temporel.json`,
> `output/pipeline_m3.json` et `output/rapprochement_m3.json`, produits par les
> quatre scripts `run_*.py`.

## Point de départ retenu

Nous repartons de la **référence commune** `data_pack/2026-S1/reference_runs/m2_for_m3/`,
et non de notre propre préparation M2 — qui est pourtant disponible et terminée.

Trois raisons :

1. **Comparabilité.** Les cinq apprenants travaillent sur les mêmes briefs. Partir
   du même état préparé rend les écarts constatés en M3 attribuables au travail
   M3, pas à des divergences héritées du M2 de chacun.
2. **Découplage des arbitrages M2 encore ouverts.** Notre préparation M2 laisse
   deux décisions métier en attente : 12 lignes en quarantaine et 595
   interventions facturant des pièces sans en déclarer. Les faire porter au M3
   mélangerait deux dettes distinctes.
3. **Le brief l'admet explicitement** et demande seulement de dire lequel est
   utilisé et pourquoi.

**Vérification faite, et elle change la portée de ce choix** : sur la table
`equipment`, la référence préparée et le fichier brut sont **identiques** — 416
équipements de part et d'autre, aucun retiré, aucun ajouté. Le choix du point de
départ n'a donc **aucun effet** sur tout ce qui concerne le parc, y compris les
taux de couverture de ce document. L'écart entre les deux points de départ ne
pourra se manifester que sur `events` et `maintenance_history`, au moment du
rapprochement temporel (axe 5).

## Méthode utilisée

| | |
|---|---|
| Environnement | Python 3.12.10, `.venv` dédié dans `work/M3/`, `requirements.lock` du starter |
| Bibliothèques | pandas 2.3.1 ; primitives temporelles du starter (`src/data_pipeline/timeseries.py`) |
| Commandes de rejeu | `run_cadrage_m3.py`, `run_audit_temporel_m3.py`, `run_pipeline_m3.py`, `run_rapprochement_m3.py`, depuis `work/M3/` |
| Temps d'exécution | 4,4 + 1,4 + 2,9 + 0,7 = **9,4 s** pour la chaîne complète, médianes sur 3 exécutions (dont ~2 s de démarrage par script) |
| Sorties | `output/cadrage/`, `output/audit/`, `output/processed/`, `output/alignment/`, `output/aggregates/`, `output/quarantine.csv`, `output/registre_regles.csv` |
| Données | lues en lecture seule ; aucun fichier de `data_pack/` n'est modifié |

La séparation entre les scripts est volontaire. `run_cadrage_m3.py` et
`run_audit_temporel_m3.py` **décrivent et ne décident rien** : aucune ligne n'est
corrigée ni écartée, ils produisent des constats et des candidats.
`run_pipeline_m3.py` est le seul à **décider** — il applique les règles, écarte,
normalise et trace. On peut donc rejouer le diagnostic sans rien transformer, et
relire ce qui a été décidé sans avoir à démêler les deux.

Nous réutilisons les primitives du starter (`to_utc`, `naive_timestamps`,
`observed_steps`, `series_overview`) plutôt que de les réécrire, et le contrat
`contracts/schemas.py` (`SENSOR_UNITS`, `ANNOUNCED_STEP_HOURS`) comme référence
des unités et du pas attendus. Leçon reprise du M2 : le contrat livré avec le
module n'avait pas été ouvert, ce qui avait produit 49 fausses anomalies.

## Cadrage de la source capteurs

### Identité du fichier

| | |
|---|---|
| Chemin | `data_pack/2026-S1/sensors/sensor_readings.csv` |
| Empreinte SHA-256 | `455b85fe1c1514c90ae33db92337c0dae2958f1f7dbbd155140827a7fd2b1e1d` |
| Taille | 3 156 683 octets (3,0 Mio) |
| Lignes | **50 401** — conforme au volume annoncé |
| Colonnes | `equipment_id`, `timestamp`, `sensor_name`, `value`, `unit`, `period` |

L'encodage est **UTF-8 valide** : le `°` de `°C` est bien la séquence `C2 B0`.
Un premier passage l'avait affiché comme un caractère de remplacement — c'était
un artefact de la console Windows (cp1252), pas un défaut du fichier. Contrôle
fait avant de conclure, précisément pour ne pas écrire une fausse anomalie.

### Question 1 — Que représente une ligne, et quelle clé identifie une mesure ?

**Une ligne est une mesure unitaire** : la valeur relevée par un capteur donné,
sur un équipement donné, à un instant donné. Elle ne représente ni un
équipement, ni un événement, ni un intervalle — c'est un point.

Le fichier ne porte **aucun identifiant de ligne**. La clé logique est le
triplet `equipment_id + timestamp + sensor_name`, comme annoncé dans `SCHEMA.md`
— mais annoncé n'est pas vérifié, et le contrôle montre qu'elle **n'est pas
unique dans les données reçues** :

| | Clés | Lignes |
|---|---:|---:|
| Clés portant plusieurs lignes | **10** | **20** |
| dont doublons **stricts** (toutes colonnes identiques) | 6 | 12 |
| dont **valeurs divergentes** sur la même clé | **4** | **8** |

La distinction est structurante et ne peut pas être traitée par la même règle :

- un **doublon strict** peut être dédoublonné sans perte d'information ;
- une **valeur divergente** est une contradiction du fichier sur lui-même.
  Exemple : `EQ-CHILL-115`, 13/03/2026 18:00, `temperature_c` → **55,72 °C**
  *et* **66,45 °C**. Garder la première, la dernière, la moyenne, ou placer les
  deux en quarantaine sont quatre décisions différentes, aucune n'est neutre.

Ces 4 clés demandent un **arbitrage explicite et tracé** — « doublon de clé
résolu sans arbitrage tracé » est un critère bloquant du brief. L'arbitrage est
porté à l'axe 4, pas ici. Détail des 20 lignes : `output/cadrage/cles_dupliquees.csv`.

Conséquence pour la quarantaine : `row_identifier` est reconstruit comme la
concaténation du triplet, **avec les valeurs telles que reçues**, y compris
lorsqu'elles sont incohérentes. Un identifiant sert à retrouver la ligne
d'origine dans le fichier, pas à la corriger.

### Séries présentes

**72 séries** (couple équipement × capteur), sur 37 identifiants d'équipement et
5 capteurs distincts après normalisation des noms.

| | |
|---|---|
| Longueur médiane | **720** mesures = 180 jours × 4 mesures/jour |
| Longueur minimale | 30 |
| Longueur maximale | 722 |
| Capteurs par équipement | 2 pour 30 équipements, 1 pour 5, 3 pour 1, 4 pour 1 |

Les capteurs et leur unité attendue, d'après le contrat : `vibration_mm_s` (mm/s),
`temperature_c` (°C), `pressure_bar` (bar), `current_a` (A), `rpm` (rpm).

Détail par série : `output/cadrage/series_overview.csv`.

### Question 2 — Période et pas réellement couverts, contre ce qui est annoncé

**Annoncé** : livraison `2026-S1`, pas nominal de 6 h ; la `DATA_CARD` précise
« du 2 janvier au 30 juin 2026 ».

**Mesuré** : du **28/12/2025 06:00 UTC** au **04/07/2026 12:00 UTC**, soit
188,25 jours.

| Mois | Mesures |
|---|---:|
| 2025-12 | **2** |
| 2026-01 | 8 400 |
| 2026-02 | 7 874 |
| 2026-03 | 8 638 |
| 2026-04 | 8 402 |
| 2026-05 | 8 681 |
| 2026-06 | 8 401 |
| 2026-07 | **3** |

Le débordement tient à **5 lignes** : 2 avant le semestre (28 et 29/12/2025), 3
après (2, 3 et 4/07/2026). Toutes portent pourtant l'étiquette `period = 2026-S1`.
Détail : `output/cadrage/mesures_hors_bornes.csv`.

**Le pas nominal est massivement respecté** : sur 50 329 écarts entre mesures
consécutives d'une même série, **50 313 valent exactement 6 h — 99,97 %**. Les 16
écarts déviants se décomposent ainsi :

| Écart | Occurrences | Interprétation |
|---|---:|---|
| 0 h | 10 | doublons de clé (deux lignes au même instant) |
| 30, 60, 86, 90, 114 h | 5 | trous **bordés par une mesure hors bornes** |
| 270 h | 1 | **la seule interruption réelle** |

**Ce point a demandé une correction en cours de route, et il est instructif.**
Un décompte naïf annonce « 6 interruptions d'échantillonnage ». C'est faux : une
mesure isolée le 28/12 crée mécaniquement un vide de 114 h jusqu'au démarrage
réel de la série, alors qu'aucun capteur n'est tombé en panne. Notre premier
critère (« le trou est un artefact si la mesure qui le précède est hors bornes »)
n'attrapait que les mesures isolées de **début** de série et laissait passer
celles de **fin** — pour les trois lignes de juillet, c'est la ligne de *reprise*
qui est l'anomalie, pas la précédente. Le critère corrigé teste les **deux**
bornes du trou.

Après correction :

| | |
|---|---:|
| Trous détectés | 6 |
| dont artefacts de mesures isolées | **5** |
| **dont interruptions réelles** | **1** |

L'unique interruption réelle est `EQ-MIX-159 / current_a` : **270 h** (11 j 6 h)
sans mesure, du 17/03 18:00 au 29/03 00:00, soit **44 mesures manquantes**.

Compter 6 pannes de capteur là où il y en a une aurait faussé la note de
couverture, puis la décision finale. Détail : `output/cadrage/interruptions.csv`.

### Un défaut que le contrôle du pas ne peut pas voir

**720 lignes sont hors de la grille horaire nominale.** La série
`EQ-PUMP-001 / vibration_mm_s` échantillonne à **02:00, 08:00, 14:00, 20:00** au
lieu de 00/06/12/18 — la série entière est décalée de 2 h.

Son pas reste parfaitement de 6 h. Un contrôle d'écart entre mesures consécutives
ne la signale donc **jamais** : seul l'alignement sur une grille temporelle
commune la révèle. C'est l'argument concret pour lequel le brief demande les deux
contrôles et pas un seul. Détail : `output/cadrage/horodatages_hors_grille.csv`.

### Horodatage : deux formats, une hypothèse à assumer

| Forme | Lignes |
|---|---:|
| `9999-99-99T99:99:99Z` (ISO 8601, UTC explicite) | 49 681 |
| `9999-99-99 99:99:99` (**sans indication de fuseau**) | **720** |

Aucun horodatage illisible : les 50 401 lignes se convertissent.

Les 720 lignes sans fuseau forment une série entière :
`EQ-COMP-233 / temperature_c`. Le starter les interprète en UTC — et le dit
explicitement comme une hypothèse à confirmer ou à écarter.

**Hypothèse retenue à ce stade : UTC.** Justification : les 49 681 autres lignes
sont en UTC explicite, et cette série s'aligne sur la même grille 00/06/12/18 que
les autres, ce qui serait improbable sous un fuseau décalé d'un nombre non
entier d'heures. **Cette hypothèse est faible** : elle ne distingue pas UTC d'un
fuseau décalé d'un multiple exact de 6 h, et un décalage d'une heure fausserait
tout rapprochement mesure ↔ événement sur cet équipement. Elle est donc inscrite
comme hypothèse à porter au registre de règles, pas comme un fait.
« Horodatages normalisés sans indiquer l'hypothèse de fuseau retenue » est un
critère bloquant du brief.

### Cohérence `sensor_name` / `unit` / ordre de grandeur

| Constat | Lignes |
|---|---:|
| Noms de capteurs bruts / après normalisation | 6 / **5** |
| Nom non normalisé : `'TEMPERATURE_C '` (majuscules + espace final) | 40 |
| Unités distinctes | **7** pour 5 capteurs |
| Lignes dont l'unité contredit le contrat | **804** |
| — `pressure_bar` exprimé en `kPa` (attendu `bar`) | 720 |
| — `temperature_c` exprimé en `K` (attendu `°C`) | 84 |
| `value` vide | 40 |

Les 84 lignes en Kelvin (`EQ-SENSOR-305`) affichent des valeurs autour de 330 —
cohérent avec ~57 °C, donc une vraie mesure exprimée dans la mauvaise unité, pas
une valeur aberrante. Même logique pour les 720 lignes en kPa (facteur 100).
Ces conversions sont des **normalisations tracées**, pas des corrections
silencieuses : elles iront au registre avec la décision `valeur_normalisee`.

Détail des couples : `output/cadrage/couples_capteur_unite.csv`.

### Les six lots de défauts de forme sont indépendants

Vérification faite parce que les volumes se ressemblaient dangereusement — 720 et
720, 40 et 40 — et qu'un même lot compté deux fois aurait gonflé le diagnostic.
**Aucun recouvrement** : les intersections sont toutes nulles.

| Lot | Volume | Portée |
|---|---:|---|
| Horodatage sans fuseau | 720 | `EQ-COMP-233 / temperature_c` |
| Pression en `kPa` | 720 | lot distinct du précédent |
| Série décalée de 2 h sur la grille | 720 | `EQ-PUMP-001 / vibration_mm_s` |
| Température en `K` | 84 | `EQ-SENSOR-305` |
| `value` vide | 40 | — |
| `sensor_name` = `TEMPERATURE_C ` | 40 | lot distinct du précédent |
| `period` = `2026-S2` | 30 | `EQ-OVEN-123` |

Sur les 30 lignes étiquetées `2026-S2` : elles sont datées du **1er au 8 juin
2026**, donc **dans** le premier semestre. C'est l'**étiquette** qui est fausse,
pas la date — à ne pas confondre avec les 5 mesures réellement hors bornes. Deux
défauts de nature différente, deux règles différentes.

### Question 3 — Quelle part du parc est instrumentée, et qui est dans l'angle mort ?

**36 équipements instrumentés sur 416, soit 8,65 %.** 380 équipements n'ont
aucune mesure.

Le fichier contient **37** identifiants d'équipement : les 36 du parc, plus
`EQ-ORPHAN-777`, **absent du référentiel**. Ses mesures ne peuvent être
rattachées à aucun équipement connu — sort à décider à l'axe 4.

Mais le taux global de 8,65 % masque l'essentiel : **la couverture n'est pas
homogène**, et son inhomogénéité est structurée.

**Par site** — un site entier n'a aucun capteur :

| Site | Instrumentés / parc | Taux |
|---|---:|---:|
| SITE-NORD | 21 / 173 | 12,14 % |
| SITE-SUD | 10 / 136 | 7,35 % |
| SITE-EST | 5 / 91 | 5,49 % |
| **SITE-OUEST** | **0 / 16** | **0,00 %** |

**Par type d'équipement** — 7 types sur 18 n'ont aucune mesure :

`dryer` (8), `gearbox` (8), `lift` (5), `motor` (7), `packaging_machine` (7),
**`press` (34)**, **`valve` (21)**. Soit **90 équipements** dont aucun n'est
mesuré. `press` et `valve` ne sont pas des types marginaux.

À l'opposé : `steam_unit` 40,00 % (2/5), `chiller` 21,74 % (5/23), `fan` 14,71 %
(5/34).

**Par criticité — c'est le constat le plus lourd :**

| Criticité | Instrumentés / parc | Taux |
|---|---:|---:|
| `critical` | 14 / 46 | **30,43 %** |
| `high` | 14 / 122 | 11,48 % |
| `medium` | 7 / 173 | 4,05 % |
| `low` | 1 / 75 | **1,33 %** |

L'instrumentation est **fortement corrélée à la criticité** : un équipement
critique a environ **23 fois** plus de chances d'être mesuré qu'un équipement de
criticité basse. C'est parfaitement rationnel du point de vue de l'exploitation —
on instrumente ce qui coûte cher à perdre — mais c'est un **biais de sélection**
de première grandeur pour tout ce qui suivra.

Conséquence directe, à porter jusqu'à la décision : le parc instrumenté n'est pas
un échantillon représentatif du parc. Toute statistique calculée sur les mesures
décrit **les équipements critiques des trois sites instrumentés**, et rien
d'autre. « Conclusion tirée du parc instrumenté et présentée comme valable pour
tout le parc » est un critère bloquant du brief ; le périmètre de validité est
donc énoncé ici et sera répété dans la décision.

Détail par équipement : `output/cadrage/couverture_parc.csv`.

### Recoupement avec les familles d'anomalies annoncées

La `DATA_CARD` annonce les familles d'anomalies pédagogiques injectées, sans en
donner l'inventaire. Elle sert donc de liste de contrôle. État après l'axe 1 :

| Famille annoncée | État |
|---|---|
| Doublons stricts | trouvé — 12 lignes / 6 clés |
| Doublons de clé à valeur divergente | trouvé — 8 lignes / 4 clés |
| Horodatages hétérogènes | trouvé — 720 sans fuseau |
| Série décalée dans le temps | trouvé — 720, `EQ-PUMP-001 / vibration_mm_s` |
| Changements d'unité | trouvé — 720 en kPa, 84 en K |
| Trou d'échantillonnage | trouvé — 1 réel, 270 h |
| Mesures hors période | trouvé — 5 hors bornes (+ 30 mal étiquetées) |
| Équipement inconnu | trouvé — `EQ-ORPHAN-777` |
| Capteur figé | trouvé — `EQ-PUMP-171 / vibration_mm_s`, 80 relevés à 2,59 |
| Dérive lente | trouvé — `EQ-CHILL-248 / temperature_c`, +8,9 °C |
| Valeurs sentinelles | trouvé — 12 lignes à `-999` |

Les onze familles annoncées sont retrouvées. La `DATA_CARD` prévient aussi que
« certaines variations sont réelles et ne doivent pas être supprimées » : c'est
l'objet de l'axe 3, traité plus bas.

---

# Audit temporel (axe 2)

Produit par `run_audit_temporel_m3.py` — **1,4 s**, sorties dans `output/audit/`.
Comme le cadrage, ce script **décrit et ne décide rien** : il produit des
candidats, que l'axe 3 instruit.

## Normalisation préalable des unités

Les valeurs ne sont comparables qu'une fois ramenées à l'unité de référence du
capteur. Deux conversions, tracées ligne à ligne :

| Conversion | Lignes | Avant | Après |
|---|---:|---|---|
| `pressure_bar` : kPa → bar (÷ 100) | 720 | 506 – 650 | 5,06 – 6,50 |
| `temperature_c` : K → °C (− 273,15) | 84 | 321,28 – 337,64 | 48,13 – 64,49 |

Les deux se replacent exactement dans la plage des autres séries du même
capteur : ce sont bien des **mesures réelles mal exprimées**, pas des valeurs
aberrantes. Ces lignes seront traitées avec la décision `valeur_normalisee`, pas
écartées.

Le nom de capteur est normalisé (casse et espaces) **avant** conversion. Sans
cela, les 40 lignes `TEMPERATURE_C ` seraient passées à travers tout contrôle de
plage, faute d'être reconnues comme des températures.

## Les sentinelles d'abord — et pourquoi l'ordre compte

**12 lignes portent la valeur `-999`**, sur 5 capteurs et 10 équipements. Le
critère de détection est **physique** et non deviné : *une valeur négative est
impossible* pour ces cinq grandeurs. Aucun autre code usuel (`0`, `-1`, `9999`)
n'est présent.

Douze lignes sur 50 401 — 0,02 % du fichier. Et pourtant :

| Capteur | Écart-type **avec** les 12 sentinelles | **sans** | Facteur |
|---|---:|---:|---:|
| `vibration_mm_s` | 14,653 | **0,405** | ÷ 36 |
| `pressure_bar` | 14,708 | **0,573** | ÷ 26 |
| `temperature_c` | 17,861 | 4,909 | ÷ 3,6 |
| `current_a` | 14,196 | 2,669 | ÷ 5,3 |
| `rpm` | 137,668 | 130,024 | ÷ 1,06 |

Laissées en place, ces douze lignes rendent inutilisable **tout** contrôle qui
s'appuie sur la dispersion : plages physiques écrasées, seuils de saut calibrés
sur un écart-type faux, et un faux saut brutal fabriqué à chaque occurrence. Les
sentinelles sont donc retirées **en premier**, et les 50 389 lignes restantes
servent de base à tous les contrôles de comportement.

C'est la même mécanique qu'en M2, où deux lignes sur 1 800 avaient effacé un
coefficient de corrélation de 0,85 : peu de lignes, effet massif, et invisible
dans le résultat final si on ne le cherche pas.

## Plages physiques observées

Après normalisation et retrait des sentinelles :

| Capteur | Unité | Min | p01 | Médiane | p99 | Max | σ |
|---|---|---:|---:|---:|---:|---:|---:|
| `current_a` | A | 16,00 | 18,13 | 23,07 | 30,82 | 34,11 | 2,669 |
| `pressure_bar` | bar | 4,56 | 5,05 | 6,31 | 7,57 | 8,12 | 0,573 |
| `rpm` | rpm | 1 104,53 | 1 183,85 | 1 440,75 | 1 695,34 | 1 736,90 | 130,024 |
| `temperature_c` | °C | 42,33 | 45,97 | 57,84 | 67,55 | 74,27 | 4,909 |
| `vibration_mm_s` | mm/s | 1,65 | 2,02 | 2,84 | 3,80 | **9,76** | 0,405 |

Quatre capteurs sur cinq sont resserrés et sans valeur extrême. **`vibration_mm_s`
fait exception** : p99 à 3,80 mais maximum à 9,76, soit plus de 17 écarts-types
au-dessus de la médiane. C'est le seul dépassement de plage du corpus, et il est
instruit à l'axe 3.

## Comportements de capteur

### Valeur figée

**Un palier détecté**, au seuil de 8 relevés consécutifs strictement identiques
(48 h) : `EQ-PUMP-171 / vibration_mm_s` reste à **2,59 exactement pendant 80
relevés**, du 12/04/2026 00:00 au 01/05/2026 18:00 — **474 h, soit 19,75 jours**.

Sur un capteur analogique dont les autres relevés varient à la deuxième décimale
(σ = 0,405 sur l'ensemble du parc), la répétition exacte de la même valeur 80
fois de suite n'a pas d'interprétation physique.

### Dérive lente

**Le seuil retenu a dû être corrigé, et c'est instructif.** Une première version
exigeait une corrélation temps/valeur ≥ 0,7, au motif qu'« au-delà de 0,7 la
tendance explique l'essentiel de la variation ». Ce seuil ne trouvait **aucun**
candidat — alors que la `DATA_CARD` annonce une dérive injectée. Le seuil était
donc faux : une dérive lente noyée dans du bruit de capteur produit une
corrélation *modeste*, pas une corrélation forte.

Le seuil a été refixé **à partir de la distribution observée**, pas d'un a priori :

| Statistique sur les 71 séries | \|corrélation\| |
|---|---:|
| Médiane | 0,0216 |
| p75 | 0,0371 |
| p95 | 0,0712 |
| **Maximum** | **0,5046** |

Soixante-dix séries sur soixante-et-onze sont sous 0,11. Un seuil à **0,30**
sépare une population homogène d'un cas isolé, sans rien supposer de l'amplitude
de la dérive cherchée.

**Candidat unique : `EQ-CHILL-248 / temperature_c`** — corrélation 0,505, pente
+0,047 °C/jour, amplitude +8,37 °C ; moyenne du premier décile temporel 52,65 °C
contre 61,57 °C pour le dernier.

### Saut brutal

**Un saut détecté** au seuil de 8 σ des écarts de la série :
`EQ-FAN-304 / vibration_mm_s`, le 11/05/2026 à 12:00 — passage de 7,39 à 3,03
mm/s (8,4 σ). Le saut détecté est donc le **retour à la normale**, ce qui
implique que la série était déjà anormalement haute avant. Instruit à l'axe 3.

---

# Erreurs, mesures réelles et cas indécidables (axe 3)

Le brief demande au moins trois observations atypiques **de nature différente**.
En voici quatre, dont un cas explicitement indécidable. Chacune est rapprochée
de `events.csv` et `maintenance_history.csv` de la référence M2.

## Cas 1 — `-999` : erreur, sans hésitation

**Constat** : 12 lignes, 5 capteurs, 10 équipements, valeur exactement `-999`.

**Raisonnement** : aucune des cinq grandeurs ne peut être négative. La valeur est
identique partout, ronde, et correspond au code d'absence le plus répandu dans
les systèmes de supervision industriels. Une même défaillance physique ne
produirait pas la même valeur au centième sur cinq grandeurs de dimensions
différentes.

**Décision** : erreur. Ce n'est pas une mesure mais un **code d'absence de
mesure**. Traitement retenu : `champ_neutralise` — la valeur est mise à
manquant, la ligne est conservée et signalée. La supprimer effacerait
l'information « le capteur n'a rien renvoyé à cet instant », qui est un fait
d'exploitation.

## Cas 2 — `EQ-PUMP-171 / vibration_mm_s` figé : erreur de capteur

**Constat** : 2,59 mm/s exactement, 80 relevés consécutifs, 474 h.

**Raisonnement** : la valeur est plausible en niveau — 2,59 est proche de la
médiane du parc (2,84). Ce n'est donc pas une valeur aberrante, et aucun contrôle
de plage ne peut la détecter. C'est sa **constance** qui est impossible : σ = 0
sur 20 jours quand le reste du parc est à 0,405. Le capteur ne mesure plus, il
répète sa dernière valeur — comportement classique d'une chaîne d'acquisition
gelée.

Les interventions sur cet équipement (janvier, juin) **n'encadrent pas** la
période figée : rien n'indique un arrêt machine qui expliquerait une stabilité
réelle. Et un équipement à l'arrêt donnerait une vibration proche de zéro, pas la
valeur nominale.

**Décision** : erreur. Les 80 relevés sont **exclus** du calcul des agrégats
(décision `exclue`), conservés en quarantaine avec leur motif. Note : ils ne sont
pas « faux » au sens d'aberrants — ils sont **non informatifs**, ce qui est plus
insidieux, car ils passeraient tous les contrôles de plage.

## Cas 3 — `EQ-FAN-304 / vibration_mm_s`, 10-11/05 : mesure réelle

**Constat** : sept relevés au-dessus de 4,0 mm/s sur toute la série (720 points).
Six d'entre eux sont consécutifs :

| Instant | mm/s |
|---|---:|
| 10/05 00:00 | 5,76 |
| 10/05 06:00 | 8,03 |
| 10/05 12:00 | 9,28 |
| 10/05 18:00 | **9,76** |
| 11/05 00:00 | 7,23 |
| 11/05 06:00 | 7,39 |
| 11/05 12:00 | 3,03 *(retour)* |

**Raisonnement — c'est la forme qui tranche.** Un défaut de capteur produit un
point isolé, un créneau, ou une valeur impossible. Ici on observe une **rampe** :
montée graduelle sur 18 h, maximum, puis décroissance sur 12 h avant retour au
niveau nominal. Six relevés consécutifs cohérents entre eux décrivent un
**phénomène physique continu**, pas une défaillance d'acquisition. L'ordre de
grandeur va dans le même sens : 9,76 mm/s sur un ventilateur est un niveau
d'alarme au regard des seuils usuels de sévérité vibratoire, pas une valeur
absurde.

**Décision** : mesure réelle. Elle est **conservée et signalée**
(`conserve_signale`), jamais supprimée. « Suppression silencieuse d'une
observation atypique » est un critère bloquant du brief, et c'est aussi le seul
signal de dégradation exploitable du corpus.

**Réserve importante, à porter à M4** : cet épisode n'a **aucun événement ni
aucune intervention associés**. Les événements de `EQ-FAN-304` sont datés de
janvier, février et avril. Deux lectures possibles, non départageables ici : soit
la dégradation n'a pas été détectée par l'exploitation, soit elle a été traitée
sans être tracée. Dans les deux cas, cela signifie qu'**un rapprochement
mesures ↔ événements ne retrouvera pas cet épisode**, ce qui borne ce qu'un
modèle supervisé construit sur ces événements pourra apprendre.

## Cas 3 bis — deux épisodes confirmés par une source indépendante

Le passage au critère de plage robuste (axe 4, `R-SEN-009`) a fait apparaître
**deux épisodes de vibration que rien n'avait isolés** : ni le seuil au 99ᵉ
centile, qui les noyait parmi 504 lignes, ni le détecteur de saut, dont ils ne
franchissaient pas le seuil.

| Série | Épisode | Profil | Événement déclaré |
|---|---|---|---|
| `EQ-FAN-204 / vibration_mm_s` | 15-18/02 | 2,76 → 4,16 → **5,05** → 3,42 | **incident `critical` le 16/02 à 11:29** |
| `EQ-PUMP-006 / vibration_mm_s` | 28/04-01/05 | 3,62 → 4,87 → **5,11** → 2,93 | **incident `critical` le 29/04 à 12:10** |

Dans les deux cas, un incident de sévérité `critical` est déclaré **pendant la
montée** — 31 minutes avant le pic pour `EQ-FAN-204`. Ces deux épisodes sont donc
des mesures réelles **confirmées par une source indépendante des mesures
elles-mêmes**, ce qui est un argument bien plus fort que le raisonnement sur la
forme du signal seul.

**Décision** : mesures réelles, `conserve_signale`.

**Et cela éclaire le cas 3 d'un jour préoccupant.** Trois épisodes de vibration
élevée dans le corpus, même profil de rampe :

| Série | Pic | Événement associé |
|---|---:|---|
| `EQ-FAN-204` | 5,05 mm/s | incident `critical` |
| `EQ-PUMP-006` | 5,11 mm/s | incident `critical` |
| **`EQ-FAN-304`** | **9,76 mm/s** | **aucun** |

Le plus intense des trois — près du double des deux autres — est le seul qui ne
soit associé à aucun événement. La traçabilité des événements n'est donc pas
seulement incomplète : elle manque précisément là où la dégradation est la plus
forte. Un modèle supervisé entraîné sur ces événements apprendrait des épisodes
modérés en ignorant le cas sévère. C'est le constat le plus lourd à transmettre
à M4.

## Cas 4 — `EQ-CHILL-248 / temperature_c` : réel, mais origine indécidable

**Constat** : la régression sur six mois donne +0,047 °C/jour. Mais la moyenne
mensuelle montre que **la dérive n'est pas linéaire** :

| Mois | Moyenne (°C) |
|---|---:|
| janvier | 52,64 |
| février | 52,23 |
| mars | 52,65 |
| avril | 52,54 |
| **mai** | **55,09** |
| **juin** | **60,63** |

Quatre mois stables à ~52,5 °C, puis une montée sur les deux derniers. La
régression linéaire lissait cette rupture — elle donnait le bon signalement pour
la mauvaise raison.

**Raisonnement** : la montée est trop régulière et trop longue (deux mois) pour
une panne d'acquisition, et l'amplitude reste dans la plage physique du capteur
(max 69,12 °C, sous le maximum du parc à 74,27 °C). Le phénomène est donc réel.

Test discriminant tenté : `EQ-CHILL-248` a subi un **remplacement le 15/03**
(`MNT-2026S1-0147`). Si la dérive venait du capteur, un remplacement l'aurait
recalée. Écart mesuré entre les 7 jours précédant et les 7 jours suivant
l'intervention : **−1,20 °C**, dans le bruit de la série (σ = 4,8). **Le test
n'est pas concluant** — et pour une raison simple : l'intervention est
*antérieure* au début de la dérive, qui ne démarre qu'en mai.

**Décision : indécidable en l'état.** Les données disponibles ne permettent pas
de distinguer une dérive d'étalonnage du capteur d'une dégradation réelle du
groupe froid (encrassement de condenseur, perte de charge de fluide). Les deux
produisent exactement ce signal. Trancher demanderait une information terrain :
date du dernier étalonnage, ou une seconde mesure indépendante de la même
grandeur — dont on ne dispose pas.

Traitement : `conserve_signale`, avec la nature de l'incertitude documentée. Deux
points à porter au-delà de M3 : la dérive est **encore en cours à la fin de la
période couverte** — elle ne se referme pas —, et si l'origine est un défaut
d'étalonnage, toutes les températures de cet équipement postérieures à mai sont
biaisées à la hausse.

---

# Évolution des règles et non-régression (axe 4)

Traité en détail dans **`docs/registre_regles.md`**. Résumé et réponses aux
questions 7 du brief :

**34 règles** — 19 héritées de M2 (16 `conservee`, 3 `etendue`), 15 nouvelles pour
les capteurs. Aucune n'est modifiée ni abandonnée : le point de départ étant
l'état préparé de référence, les règles M2 y ont déjà été appliquées. Les trois
règles d'unicité sont `etendue` parce que leur décision — doublon exact supprimé,
conflit exclu — est reprise telle quelle sur la clé composite des mesures.

**Non-régression** : les trois tables M2 sont relues **depuis les fichiers écrits
par la pipeline** et comparées à l'entrée, colonne par colonne et ligne par
ligne. 416, 514 et 1 788 lignes, contenu identique. `run_pipeline_m3.py` retourne
un code de sortie non nul si le contrôle échoue — la non-régression bloque, elle
n'est pas seulement rapportée.

Sa portée est volontairement énoncée sans l'exagérer : ce qui est démontré, c'est
que **l'ajout de la source capteurs ne modifie pas l'acquis M2**. Ce n'est pas une
revalidation des règles M2 elles-mêmes.

**Quarantaine unifiée** : 1 833 lignes au format M2 pour les quatre sources, dont
les 35 lignes de la quarantaine M2 reprises intégralement. 87 % sont des
`valeur_normalisee` — transformations réelles, chacune tracée. Les rejets qui
retirent de la donnée sont rares : **127 exclusions, 0,25 % des mesures**.

**Résultat** : 50 401 mesures reçues → **50 277 préparées**. 124 retirées : 80
figées, 30 d'équipement inconnu, 8 en clé divergente, 6 doublons stricts.

**Vérification** : 56 tests passent (`tests/test_pipeline_m3.py`), couvrant un cas
valide et un cas invalide par règle, quatre cas temporels, le format de
quarantaine et la non-régression.

## Trois détecteurs corrigés parce qu'ils produisaient des résultats faux

Consigné ici parce que c'est le cœur de ce que l'axe 4 a appris.

| Détecteur | Version initiale | Défaut | Correction |
|---|---|---|---|
| Plage (`R-SEN-009`) | seuil au 99ᵉ centile | rejetait **exactement 1 % des lignes** (504/50 401) par construction — un centile découpe une distribution, il ne détecte rien | écart à la médiane en MAD |
| Saut (`R-SEN-012`) | 8 × écart-type des écarts | un saut isolé **gonfle l'écart-type qui le mesure** : un pic à 25 sur une base à 2,8 ressortait à 4,3 σ | MAD des écarts **+** amplitude ≥ 10 % du niveau série |
| Continuité (`R-SEN-004`) | trous mesurés après retrait des lignes sans valeur | **57 fausses interruptions sur 63** — un relevé sans valeur reste un relevé | mesure sur la trame des horodatages reçus |

Les deux premiers ont le même mécanisme que les sentinelles de l'axe 2 : **la
valeur cherchée fausse l'estimateur censé la trouver**. La leçon transposable est
d'employer des estimateurs robustes (médiane, MAD) partout où le contrôle porte
sur des valeurs extrêmes.

Le détecteur de saut n'a été pris en défaut que par un **test écrit exprès** :
sur les données réelles, l'unique saut du corpus était assez entouré pour rester
mesurable, et le défaut restait invisible.

---

# Rapprochement mesures ↔ événements (axe 5)

Produit par `run_rapprochement_m3.py` — **0,7 s**. Il part des **mesures
préparées** par l'axe 4, pas des mesures brutes.

Une mesure et un événement ne partagent aucune clé : seul le couple
« équipement + temps » les rapproche. Le rapprochement repose donc entièrement
sur une fenêtre d'observation, qui est un **choix**, pas un paramètre technique.

## Question 8 — Quelle fenêtre, et pourquoi celle-là

**Fenêtre retenue : 48 h avant le début de l'événement, 24 h après sa fin.**

Justifiée par les données, pas par convention :

- **48 h avant** — les trois épisodes de vibration identifiés à l'axe 3 montent
  pendant **18 à 30 h** avant l'incident déclaré (`EQ-FAN-204` : montée à partir
  du 15/02 06:00, incident le 16/02 11:29). 48 h les couvre tous les trois avec
  de la marge, soit 8 relevés au pas de 6 h.
- **24 h après** — ces mêmes épisodes retombent au niveau nominal en 12 à 24 h.
- **La fenêtre englobe l'événement**, du début à la fin : un événement dure
  **19,2 h en médiane** (max 36 h, 13 sans `end_at` sur 514). Une fenêtre
  ancrée sur le seul instant de début en amputerait la moitié.

### Le choix de la fenêtre n'est pas déterminant — et c'est démontré

Plutôt que d'affirmer que la fenêtre est raisonnable, le script rejoue le
rapprochement sur cinq largeurs :

| Avant | Après | Événements appariés | Mesures appariées | Part | Médiane / événement | Duplication |
|---:|---:|---:|---:|---:|---:|---:|
| 12 h | 6 h | **89** | 1 045 | 2,08 % | 12 | 1,000 |
| 24 h | 12 h | **89** | 1 560 | 3,10 % | 18 | 1,005 |
| **48 h** | **24 h** | **89** | **2 574** | **5,12 %** | **30** | **1,014** |
| 72 h | 48 h | **89** | 3 884 | 7,73 % | 46 | 1,030 |
| 168 h | 72 h | **89** | 7 024 | 13,97 % | 86 | 1,062 |

**Le nombre d'événements appariés reste 89 quelle que soit la fenêtre**, d'un
facteur 14 entre la plus étroite et la plus large. Élargir n'apporte aucun
événement nouveau : cela ajoute seulement des mesures autour des mêmes.

Ce qui décide de ce qui est observable, ce n'est donc pas la fenêtre —
c'est **l'instrumentation**. Le choix de 48 h/24 h est arbitraire dans sa valeur
exacte, mais sans effet sur la conclusion structurante.

## Cardinalité, dans les deux sens

**Côté événements :**

| | |
|---|---:|
| Événements au total | 514 |
| sur équipement instrumenté | **89** |
| sur équipement non instrumenté | 425 |
| **avec au moins une mesure** | **89** |
| sans aucune mesure | 425 |
| **sans mesure bien qu'instrumenté** | **0** |

Le rapprochement est **complet sur son périmètre** : 89 appariés sur 89
possibles. Les 425 événements sans mesure le sont **tous** parce que leur
équipement n'a pas de capteur — aucun ne manque par défaut de fenêtre.
Autrement dit : **83 % des événements du parc sont hors de portée** de toute
analyse fondée sur les mesures.

Mesures par événement : min 12, **médiane 30**, moyenne 29,3, max 52.

**Côté mesures :**

| | |
|---|---:|
| Mesures préparées | 50 277 |
| dans au moins une fenêtre | 2 574 |
| **hors de toute fenêtre** | **47 703** |
| Part appariée | **5,12 %** |

Près de 95 % des mesures ne tombent dans aucune fenêtre. C'est attendu — les
événements sont rares et les capteurs relèvent en continu — mais il faut
l'énoncer : le rapprochement ne décrit que 5 % du signal disponible.

## Le rapprochement duplique-t-il des mesures ?

Contrôlé, parce qu'une jointure temporelle peut multiplier les lignes sans le
dire quand deux fenêtres se recouvrent :

| | |
|---|---:|
| Lignes de rapprochement | 2 610 |
| Mesures distinctes | 2 574 |
| **Facteur de duplication** | **1,014** |
| Mesures présentes dans 2 fenêtres | 36 |
| Appartenance maximale | 2 |

**36 mesures sont comptées deux fois** — 1,4 % de l'ensemble. La duplication est
donc réelle mais marginale, et aucune mesure n'appartient à plus de deux
fenêtres. Elle est signalée plutôt que corrigée : dédoublonner reviendrait à
choisir arbitrairement à quel événement rattacher une mesure qui, de fait,
tombe dans la fenêtre des deux.

## Question 9 — Le grain d'agrégation, et ce qu'il fait perdre

**Grain retenu : `event_id × equipment_id × sensor_name`** — 175 lignes, une par
capteur et par événement, couvrant les 89 événements et les 5 capteurs.

Indicateurs par ligne : nombre de mesures, mesures renseignées, complétude,
minimum, maximum, moyenne, écart-type, première et dernière mesure.

Complétude : **médiane 100 %**, minimum 93,8 %.

Extrait — les cinq plus fortes vibrations agrégées :

| Événement | Équipement | Type | Sévérité | Mesures | Min | **Max** | Moyenne | σ |
|---|---|---|---|---:|---:|---:|---:|---:|
| `EVT-2026S1-0039` | `EQ-PUMP-006` | incident | **critical** | 15 | 3,28 | **5,11** | 4,169 | 0,574 |
| `EVT-2026S1-0364` | `EQ-FAN-204` | incident | **critical** | 18 | 2,76 | **5,05** | 3,944 | 0,715 |
| `EVT-2026S1-0064` | `EQ-FAN-204` | incident | critical | 14 | 2,53 | 4,62 | 3,738 | 0,601 |
| `EVT-2026S1-0050` | `EQ-PUMP-350` | incident | high | 18 | 2,78 | 4,48 | 3,727 | 0,475 |
| `EVT-2026S1-0344` | `EQ-FAN-284` | alert | critical | 17 | 2,46 | 4,47 | 3,486 | 0,622 |

Les deux épisodes confirmés de l'axe 3 arrivent en tête, tous deux sur des
incidents `critical`. Le rapprochement produit donc bien le signal attendu là où
il existe.

### Ce que ce grain fait perdre — trois pertes, dont une décisive

**1. L'ordre, donc la causalité apparente.** Un agrégat `min / max / moyenne /
écart-type` sur une fenêtre ne dit pas **quand** le maximum a eu lieu. Impossible
de distinguer une vibration qui monte **avant** l'incident — un précurseur,
exploitable pour anticiper — d'une vibration qui monte **après** — une
conséquence, sans valeur prédictive. Les deux produisent le même agrégat. Un
grain par sous-fenêtre (avant / pendant / après) lèverait l'ambiguïté ; c'est la
première chose à ajouter si M4 vise de la prédiction.

**2. La forme.** La rampe caractéristique — montée graduelle, pic, décroissance —
disparaît. C'est pourtant elle qui a permis, à l'axe 3, de distinguer une
dégradation réelle d'un défaut de capteur. Un maximum isolé ne porte pas cette
information.

**3. La dispersion réelle.** L'écart-type d'une fenêtre de 30 mesures mélange le
bruit normal du capteur et la variation liée à l'événement, sans permettre de les
séparer.

## Le constat le plus lourd — le rapprochement rate le cas le plus grave

`EQ-FAN-304` est apparié à des événements : 58 lignes de rapprochement. Mais son
maximum **apparié** est de **4,30 mm/s**, alors que son pic réel atteint **9,76**.

Vérification faite mesure par mesure :

| Instant | Valeur | Dans une fenêtre ? |
|---|---:|---|
| 10/05 00:00 | 5,76 | **non** |
| 10/05 06:00 | 8,03 | **non** |
| 10/05 12:00 | 9,28 | **non** |
| 10/05 18:00 | **9,76** | **non** |
| 11/05 00:00 | 7,23 | **non** |
| 11/05 06:00 | 7,39 | **non** |

Et à l'échelle du corpus entier :

| | |
|---|---:|
| Mesures de vibration au-dessus de 5 mm/s | **8** |
| dont appariées à un événement | **2** |
| **dont non appariées** | **6** |

**Les six mesures non appariées sont exactement l'épisode de `EQ-FAN-304`, pic
compris.** Trois quarts des vibrations les plus fortes du corpus — et la plus
forte de toutes, deux fois supérieure aux autres — sont invisibles à toute
analyse fondée sur les événements déclarés.

Ce n'est pas un défaut du rapprochement : il fonctionne, il est complet sur son
périmètre et sa duplication est maîtrisée. C'est un **défaut de la source des
étiquettes**. Un modèle supervisé entraîné sur ces événements apprendrait des
épisodes modérés à 5 mm/s en ignorant complètement le cas à 9,76 — et un modèle
évalué sur ce corpus serait *récompensé* pour l'ignorer.

C'est la conclusion à transmettre à M4, et elle ne se corrige pas par un
meilleur réglage de fenêtre.

---

# Axes 6, 7 et 8 — documents dédiés

Ces trois axes ont leur propre document, pour rester lisibles par leurs
destinataires respectifs sans avoir à traverser tout le diagnostic.

| Axe | Document | Contenu |
|---|---|---|
| **1** *(volet documentaire)* et **6** | [`flux_et_cycle_de_vie.md`](flux_et_cycle_de_vie.md) | Destinataires, schéma du flux avec les points d'écartement, suivi d'une ligne de bout en bout, commande de rejeu, cycle de vie, **existence / disponibilité / accès** et solution de remplacement pour les 380 équipements non couverts, règle de conservation, description du jeu mise à jour |
| **7** | [`couverture_et_risques.md`](couverture_et_risques.md) | Couverture par site, type et criticité ; périmètre de validité ; risque « personnes » **mesuré et non supposé** ; conservation du volume ; suivi proposé |
| **8** | [`decision_transmission_m4.md`](decision_transmission_m4.md) | Statut, ce qui est vérifié / transformé / incertain, cinq conditions avant M4, coût de rejeu et seuils de bascule |
| **4** | [`registre_regles.md`](registre_regles.md) | 34 règles statuées, arbitrages tracés, non-régression, quarantaine unifiée |

## Réponses aux questions 4, 10, 11 et 12

Les huit autres questions sont traitées dans les sections ci-dessus.

**Q4 — Existence, disponibilité, accès, et remplacement pour les équipements non
couverts.** Détail dans `flux_et_cycle_de_vie.md`. Ce qui est **réellement**
vérifié : le fichier existe, son volume est conforme (50 401 lignes), son
empreinte SHA-256 est stable, l'encodage est valide, et le contenu est cohérent
avec le `MANIFEST` sur le pas et le nombre d'équipements. Ce qui ne l'est pas :
l'identité du producteur, le procédé d'export, la conduite à tenir si une
livraison manque — reconstitués depuis les documents livrés, donc énoncés comme
hypothèses. **Solution de remplacement pour les 380 équipements sans capteur :
aucune retenue**, et c'est argumenté — un relevé porté par les interventions
serait ponctuel, non calibré et biaisé par construction, ce qui produirait un
signal faux avec une apparence de complétude.

**Q10 — Flux et cycle de vie, et à qui ils sont adressés.** Trois destinataires
identifiés : l'équipe technique qui reprendra la pipeline, le métier maintenance
qui exploitera les résultats, la personne chargée de la conformité. Chacun avec
ce qu'il doit pouvoir en tirer. Les deux documents sont explicitement
**périssables** et leur liste de points à revoir est datée.

**Q11 — Risques pour les personnes et pour la validité.** Le risque « personnes »
a été **mesuré plutôt que supposé**, et le résultat contredit l'énoncé du brief
dans ce corpus précis : les mesures tombent toutes à la minute zéro sur huit
heures fixes — signature d'un cycle automate, pas d'un rythme humain. La
distribution horaire des interventions est plate (56 à 96 par créneau sur 24 h),
sans signature de poste reconstituable. Décision proportionnée : aucune mesure
supplémentaire sur les capteurs, `R-MNT-008` maintenue sur les notes de bon de
travail, et trois conditions de réexamen identifiées. Le risque de validité, lui,
est majeur et structurel : biais de couverture vers les équipements critiques.

**Q12 — Transmission à M4.** Statut **`utilisable sous conditions`**, cinq
conditions dont deux bloquantes, coût de rejeu de 9,4 s avec les seuils de
bascule chiffrés. Détail dans `decision_transmission_m4.md`.

## Limites de ce qui est établi

- Les axes 1 à 3 **décrivent et qualifient** ; aucune règle n'est encore
  appliquée, aucune ligne écartée du jeu produit. Les volumes annoncés ici sont
  des constats et des décisions *proposées*, pas des rejets effectués. La
  pipeline qui les applique est l'objet de l'axe 4.
- L'hypothèse de fuseau UTC sur les 720 lignes naïves est **faible** et non
  vérifiable avec les seules données reçues.
- Les plages observées sont **descriptives, pas normatives** : elles disent ce
  que le corpus contient, pas ce qui est physiquement admissible. Elles sont
  calculées tous équipements confondus, alors qu'une pression plausible sur un
  compresseur ne l'est pas forcément sur un groupe froid. Des bornes par type
  d'équipement seraient plus justes, mais le corpus ne compte que 36 équipements
  instrumentés répartis sur 11 types — trop peu pour les établir sans risque.
- Les seuils de détection des comportements (8 relevés pour le figé, 8 σ pour le
  saut, 0,30 de corrélation pour la dérive) sont **des choix**, documentés et
  justifiés dans le script. Un seuil plus permissif produirait d'autres
  candidats ; celui de la dérive a déjà dû être corrigé une fois.
- Les quatre cas de l'axe 3 sont instruits ; **rien ne garantit qu'il n'existe
  pas d'autres anomalies** que les détecteurs actuels ne voient pas — un capteur
  figé sur 6 relevés, une dérive de corrélation 0,25, un saut à 6 σ.
- `to_utc` s'appuie sur `format="mixed"`, qui laisse pandas deviner le format
  ligne par ligne. C'est sans danger ici — les deux formes rencontrées sont
  ISO et non ambiguës — mais ce ne serait pas vrai avec des dates au format
  jour/mois.
- La cohérence entre les mesures et les tables `events` /
  `maintenance_history` n'est pas contrôlée : c'est l'objet de l'axe 5.
