---
module: M3
etat: axe 7 terminé
maj: 2026-08-24
---

# Couverture et risques — M3

Tous les chiffres proviennent de `output/cadrage/cadrage.json` et
`output/rapprochement_m3.json`.

## Couverture instrumentale

| Dimension | Parc complet | Parc instrumenté | Écart |
|---|---:|---:|---|
| Équipements | 416 | **36** | **8,65 %** — 380 sans aucune mesure |
| Sites | 4 | 3 | **`SITE-OUEST` : 0 / 16, aucun capteur** |
| Types d'équipement | 18 | 11 | **7 types sans aucune mesure**, dont `press` (34) et `valve` (21) |
| Criticités | 4 | 4 | toutes représentées, mais **très inégalement** (1,3 % → 30,4 %) |
| Événements rapprochables | 514 | **89** | **83 % des événements hors de portée** |

Un 37ᵉ identifiant d'équipement apparaît dans les mesures — `EQ-ORPHAN-777`,
absent du référentiel. Ses 30 mesures sont exclues (`R-SEN-013`).

### Par site

| Site | Instrumentés / parc | Taux |
|---|---:|---:|
| `SITE-NORD` | 21 / 173 | 12,14 % |
| `SITE-SUD` | 10 / 136 | 7,35 % |
| `SITE-EST` | 5 / 91 | 5,49 % |
| **`SITE-OUEST`** | **0 / 16** | **0,00 %** |

### Par type d'équipement

Instrumentés : `steam_unit` 40,0 % (2/5), `chiller` 21,7 % (5/23), `fan` 14,7 %
(5/34), `oven` 14,3 % (5/35), `mixer` 13,6 % (3/22), `compressor` 13,2 % (5/38),
`conveyor` 10,0 % (4/40), `electrical_cabinet` 8,3 % (1/12), `pump` 7,0 % (4/57),
`sensor` 6,3 % (1/16), `robot` 2,3 % (1/44).

**Sans aucune mesure** : `dryer` (8), `gearbox` (8), `lift` (5), `motor` (7),
`packaging_machine` (7), **`press` (34)**, **`valve` (21)** — soit **90
équipements**, 21,6 % du parc, dont aucun n'est observable.

### Par criticité — le biais structurant

| Criticité | Instrumentés / parc | Taux |
|---|---:|---:|
| `critical` | 14 / 46 | **30,43 %** |
| `high` | 14 / 122 | 11,48 % |
| `medium` | 7 / 173 | 4,05 % |
| `low` | 1 / 75 | **1,33 %** |

Un équipement `critical` a environ **23 fois** plus de chances d'être mesuré
qu'un équipement `low`. C'est une politique d'instrumentation parfaitement
rationnelle — on instrumente ce qui coûte cher à perdre — mais c'est un **biais
de sélection** au sens statistique : le parc instrumenté n'est pas un
échantillon du parc, c'est sa strate la plus critique.

## Périmètre de validité

**Ce à quoi les constats de ce module s'appliquent :**

- les **36 équipements instrumentés**, sur les trois sites `NORD`, `SUD` et `EST` ;
- la période du **28/12/2025 au 04/07/2026** ;
- les **cinq grandeurs** mesurées : vibration, température, pression, courant,
  vitesse de rotation ;
- au pas d'échantillonnage de **6 h**.

**Ce à quoi ils ne s'appliquent pas :**

- au parc complet — toute statistique calculée ici décrit des équipements
  majoritairement critiques ;
- à `SITE-OUEST`, à `press`, à `valve` et aux cinq autres types sans mesure —
  pour eux, ce module ne dit **rien**, et l'absence de signal ne vaut pas absence
  de problème ;
- aux phénomènes plus rapides que 12 h : au pas de 6 h, le théorème
  d'échantillonnage interdit de caractériser toute variation de période
  inférieure. Un transitoire d'une heure est invisible, et rien dans les données
  ne permet de savoir combien il y en a eu ;
- à d'autres périodes : les seuils de détection sont calibrés sur ce semestre.

**Formulation à reprendre telle quelle dans toute conclusion tirée de ces
données** : « sur les 36 équipements instrumentés, majoritairement critiques, des
sites NORD/SUD/EST, au premier semestre 2026 ». Une conclusion tirée du parc
instrumenté et présentée comme valable pour tout le parc est un critère bloquant
du brief — et une faute d'analyse indépendamment de tout barème.

## Personnes

### Ce qui a été recherché

Le brief signale un risque précis : *une mesure horodatée à la minute décrit
aussi l'activité humaine autour de l'équipement — postes, présence, rythme de
travail*. Trois vérifications ont été faites plutôt que de reprendre l'énoncé
comme un fait.

### Ce qui a été détecté — et le résultat contredit l'intuition

**1. Les mesures capteurs ne portent pas d'information sur l'activité humaine.**

| Source | Minutes distinctes | Heures distinctes |
|---|---:|---:|
| `sensor_readings` | **1** (toujours `:00`) | 8 |
| `events` | 60 | 24 |
| `maintenance_history` | 60 | 24 |

Les mesures tombent toutes à la minute zéro, sur huit heures fixes (00/06/12/18,
plus 02/08/14/20 pour la série décalée). C'est la signature d'un **cycle
automate**, pas d'un rythme humain. Un relevé à heure fixe toutes les six heures
ne dit rien de qui était présent : il aurait eu lieu de la même façon en
l'absence de tout opérateur.

Le risque énoncé par le brief est donc **réel dans son principe mais inopérant à
ce pas d'échantillonnage**. Il le deviendrait si le pas descendait à la minute —
et c'est précisément le scénario de montée en volume évoqué dans
`flux_et_cycle_de_vie.md`.

**2. Les événements et interventions, eux, sont horodatés à la minute.** C'est là
que l'information sur l'activité humaine se trouve réellement : `opened_at` et
`closed_at` marquent le moment où quelqu'un est intervenu.

**3. Mais la distribution horaire est plate.** Ouvertures d'intervention par
heure de la journée : entre **56 et 96** sur les 24 créneaux, sans creux nocturne
ni pic diurne. Aucune signature de poste, de garde ou d'astreinte n'est
reconstituable. Le corpus étant pédagogique, cette uniformité est probablement un
artefact de génération — mais le contrôle devait être fait, et son résultat est
négatif.

**4. Les notes de bon de travail** (`work_order_note`) sont renseignées sur
**1 788 lignes sur 1 788**. Elles relèvent déjà de `R-MNT-008`
(pseudonymisation), règle héritée de M2 et conservée. Les échantillons examinés
sont des formulations techniques standardisées (« Pièce remplacée puis remise en
service progressive », « Intervention préventive conforme au plan »), sans nom ni
mention directe de personne.

### Ce qui a été décidé, et pourquoi c'est proportionné

**Aucune mesure supplémentaire n'est prise sur les données capteurs.** Motif :
au pas de 6 h et à heure fixe, elles ne portent pas d'information sur les
personnes. Ajouter une pseudonymisation ou un floutage temporel dégraderait la
donnée sans réduire aucun risque identifié — ce serait une précaution
d'apparence.

**`R-MNT-008` est maintenue en l'état** sur les notes de bon de travail : elle
traite le seul vecteur direct présent dans le corpus.

**Le risque de croisement est signalé, pas traité.** Le brief le nomme :
mesure + site + horaire + bon de travail peut redevenir identifiant dans un
contexte réel — un site de 16 équipements avec deux techniciens rend une
intervention datée à la minute quasi nominative, même sans nom. Ce risque
n'est pas neutralisable par une transformation des données : il dépend de qui y
accède. Il relève d'un contrôle d'accès aux sorties, pas d'un traitement.

**Trois conditions déclencheraient un réexamen** :

1. un pas d'échantillonnage inférieur à l'heure ;
2. l'ajout d'un identifiant d'intervenant, même pseudonymisé, dans
   `maintenance_history` ;
3. une diffusion des sorties `output/` hors de l'équipe technique et du métier
   maintenance.

Il n'est pas demandé — ni produit ici — d'expertise juridique RGPD ni d'analyse
d'impact complète.

## Conservation du volume

Détaillée dans `flux_et_cycle_de_vie.md`. En résumé :

| Forme | Volume | Décision |
|---|---:|---|
| Brut reçu | 3,16 Mo / semestre | **conservé intégralement**, sans expiration |
| Préparé | 5,71 Mo | conservé, régénérable |
| Agrégats | 0,026 Mo (÷ 122) | **recalculés, jamais archivés seuls** |

À l'échelle actuelle — 365 Mo pour le parc entier sur cinq ans — aucun arbitrage
de volume ne se justifie : le coût de stockage est négligeable devant celui d'une
donnée détruite et non régénérable. Le brut est la seule forme qui permette de
rejouer un audit avec des règles différentes, et ce module a montré **quatre
fois** que les règles changent.

Le point de bascule est identifié et chiffré : un pas de la minute porterait le
volume à **13,1 Go par semestre** pour le parc entier, soit 260 Go sur cinq ans.
À cette échelle, une fenêtre glissante de brut plus des agrégats horaires
au-delà deviendrait justifiée. Pas avant.

## Suivi proposé

Ce qu'il faut remesurer, et quand.

| À vérifier | Quand | Pourquoi ce n'est pas acquis |
|---|---|---|
| Taux de couverture par site, type et criticité | À chaque livraison | Le parc instrumenté peut changer ; les taux de ce document deviendraient faux sans prévenir |
| Conformité des unités | À chaque livraison | 804 lignes sur 50 401 étaient dans une unité non conforme ce semestre |
| Distribution horaire des interventions | À chaque livraison | C'est le contrôle qui a écarté le risque « signature de poste » ; il doit rester négatif |
| Pas d'échantillonnage réel | À chaque livraison | Toute l'analyse du risque « personnes » repose sur le pas de 6 h |
| Dérive de `EQ-CHILL-248` | Livraison `2026-S2` | Elle est **en cours** à la fin de la période — le semestre suivant est le seul test disponible |
| Épisode `EQ-FAN-304` du 10-11/05 | Livraison `2026-S2` | Vérifier si un événement a été déclaré rétroactivement ; sinon l'absence est structurelle |
| Part des événements rapprochables | À chaque livraison | 17 % aujourd'hui ; c'est le plafond de ce qu'un apprentissage supervisé peut voir |
| Seuils de détection (8 MAD, 8 relevés, 0,30, 8 MAD + 10 %) | À chaque livraison | Calibrés sur ce semestre ; quatre ont déjà dû être corrigés |
