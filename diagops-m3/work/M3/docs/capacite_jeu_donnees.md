---
module: M3
brief: brief 2 — online
etat: étape 1 terminée
maj: 2026-08-25
---

# Capacité du jeu de données — étape 1

Le brief 1 a conclu sur la **qualité** des données : `utilisable sous
conditions`. Cette étape mesure leur **capacité** — ce que ce jeu permet
réellement de traiter, avant toute fabrication.

Tous les chiffres proviennent de `output/capacite/capacite.json`, rejouable par
`python run_capacite_b2.py` (graine `25082026`, sorties identiques à l'octet
près sur deux exécutions successives).

## Point de départ

Arbitrage **A1**, tranché le 25/08 : notre préparation du brief 1
(`output/processed/`), et non la référence commune. Elle en dérive, la filiation
reste donc traçable, et le rapprochement temporel du brief 1 devient utilisable.

| Table | Lignes |
|---|---:|
| `equipment` | 416 |
| `events` | 514 |
| `maintenance_history` | 1 788 |
| `sensor_readings` | 50 277 |

## 1. Effectifs et rapports de déséquilibre

Rapport entre la modalité la plus représentée et la moins représentée. Il s'agit
d'un rapport **d'effectifs** : il ne remplace pas le rapport de *taux
d'instrumentation* ×23 établi au brief 1, il décrit une autre chose — la
composition du parc, non son observation.

| Variable | Modalités | La plus représentée | La moins représentée | Rapport |
|---|---:|---|---|---:|
| `equipment_type` | 18 | `pump` — 57 | `steam_unit` — 5 | **11,4** |
| `site_id` | 4 | `SITE-NORD` — 173 | `SITE-OUEST` — 16 | **10,8** |
| `event_type` | 4 | `incident` — 232 | `alert` — 49 | 4,7 |
| `criticality` | 4 | `medium` — 173 | `critical` — 46 | 3,8 |
| `severity` | 4 | `high` — 213 | `low` — 71 | 3,0 |

Le parc lui-même est bien plus déséquilibré que les événements qu'il produit.
`SITE-OUEST`, déjà à zéro capteur, est aussi le plus petit site du parc : son
absence d'instrumentation se double d'un effectif faible, ce qui limite ce
qu'une fabrication pourra en dire.

Distributions tracées : `figures/effectifs_parc.png`,
`figures/effectifs_evenements.png`.

## 2. Couverture des événements

Fenêtre d'observation reprise du brief 1 : **48 h avant** le début de
l'événement, **24 h après** sa fin.

**89 événements sur 514 (17,3 %)** disposent d'au moins une mesure dans leur
fenêtre. Les 425 autres n'en ont aucune, et dans tous les cas parce que
l'équipement concerné n'a aucun capteur — aucun événement sur équipement
instrumenté n'est resté sans mesure.

| Variable | Modalité | Documentés / total | Part |
|---|---|---:|---:|
| `severity` | `critical` | 9 / 73 | 12,33 % |
| `severity` | `high` | 35 / 213 | 16,43 % |
| `severity` | `medium` | 30 / 157 | 19,11 % |
| `severity` | `low` | 15 / 71 | 21,13 % |
| `event_type` | `alert` | 5 / 49 | 10,20 % |
| `event_type` | `observation` | 18 / 116 | 15,52 % |
| `event_type` | `intervention` | 20 / 117 | 17,09 % |
| `event_type` | `incident` | 46 / 232 | 19,83 % |

Ces taux invitent à une conclusion frappante : les événements les plus graves
seraient les moins observés. **Le test l'interdit.**

| Variable | χ² | ddl | p | Lecture |
|---|---:|---:|---:|---|
| `severity` | 2,457 | 3 | **0,483** | aucun écart distinguable du hasard |
| `event_type` | 3,019 | 3 | **0,389** | aucun écart distinguable du hasard |

La couverture d'un événement **ne dépend pas** de sa catégorie. Elle est
uniformément mauvaise, autour de 17 %. C'est un résultat moins spectaculaire
que le précédent, et c'est le seul qui soit vrai.

> Le test a été écrit dans le code (`tester_independance_couverture`) et non
> exécuté à part : le raisonnement qu'il invalide était déjà rédigé lorsqu'il a
> été lancé.

## 3. Segmentation du parc

### Variables retenues, et surtout écartées

Neuf variables numériques par équipement :

| Groupe | Variables |
|---|---|
| Référentiel | `criticite_ordinale`, `puissance_kw`, `age_annees` |
| Activité | `n_evenements`, `n_evenements_graves`, `n_interventions`, `indisponibilite_min`, `cout_pieces_eur`, `part_correctives` |

Trois variables sont **délibérément exclues**, chacune pour éviter une
conclusion circulaire :

- **`instrumente`** — segmenter sur la présence de capteurs puis conclure que
  certains groupes en manquent ne démontrerait rien ;
- **`site_id`** — le brief exige que la segmentation montre autre chose que les
  comptages par site déjà produits ;
- **`equipment_type`** — l'inclure reviendrait à redécouvrir la partition par
  type.

Les trois servent à **décrire** les segments a posteriori, et le croisement avec
la couverture constitue le résultat de l'étape.

### Deux préparations nécessaires, toutes deux tracées

**La sentinelle.** Une intervention porte `downtime_minutes = 99999`, quand le
maximum réel du parc est de 385 minutes. Le brief 1 l'avait classée
`conserve_signale` — conservée, signalée, arbitrage métier en attente. Cette
décision a un effet en aval : sommée par équipement, cette seule ligne aurait
constitué à elle seule un segment. Elle est neutralisée au seuil de la règle
héritée `R-MNT-005` (quatorze jours), et le compte est reporté dans le rapport.

**L'asymétrie.** Les cinq compteurs et montants passent en `log(1+x)` avant
standardisation. Sans cette transformation, les quelques équipements les plus
coûteux dicteraient seuls la partition — la leçon du brief 1 sur les valeurs
extrêmes vaut ici. Les distributions brutes sont tracées avant transformation
(`figures/distributions_activite.png`), pour que l'asymétrie soit constatée et
non supposée.

Autres traitements : 2 puissances et 1 date de mise en service absentes,
imputées par la médiane ; 28 coûts de pièces absents, ignorés dans la somme.
42 équipements sans aucun événement et 50 sans aucune intervention reçoivent un
compteur **nul** et non une valeur manquante : c'est une absence d'activité
observée, pas une absence de donnée.

### État 1 — partition rejetée

Premier passage sur le parc entier, `k` choisi par silhouette maximale.
Résultat : **k = 2, silhouette 0,454** — un chiffre flatteur.

Il ne vaut rien. Le diagnostic automatique le montre :

| Groupe | Équipements | Pureté en inactifs | Rappel des inactifs |
|---|---:|---:|---:|
| 0 | 366 | 0,00 % | 0,00 % |
| 1 | **50** | **100,00 %** | **100,00 %** |

Le second groupe **est** exactement le critère booléen `n_interventions == 0`.
Ces 50 équipements ont tous leurs compteurs d'activité nuls : ils occupent un
point unique de l'espace des variables. K-means les isole en premier, la
silhouette récompense cette séparation triviale, et les 366 autres restent
entièrement non structurés — ce qu'atteste la chute de la silhouette à 0,215
dès k = 3, avec un plus petit groupe qui reste bloqué à 50 pour k = 2, 3 et 4.

> **Un raté à signaler.** La première version du diagnostic testait
> `max(activité) == 0` sur chaque groupe et ne détectait rien. Certains
> équipements sans intervention ont malgré tout un événement enregistré : le
> maximum du groupe n'est donc pas nul. Le bon test n'est pas l'exactitude
> arithmétique mais le **recouvrement** entre le groupe et le critère, mesuré
> dans les deux sens. Corrigé, il donne 100 % / 100 %.

### État 2 — strate déclarée, puis segmentation

Les 50 équipements sans activité sont sortis en **strate déclarée**
(`SEG-INACTIF`) : c'est un fait booléen, pas une découverte. Les 366 restants
sont segmentés séparément et standardisés sur leur propre population.

Résultat : **k = 2, silhouette 0,193**.

| Segment | Équipements | Interventions moy. | Indispo. moy. (min) | Coût pièces moy. (€) | Événements moy. |
|---|---:|---:|---:|---:|---:|
| `SEG-1` | 192 | 6,66 | 1 134,8 | 1 601,19 | 1,64 |
| `SEG-2` | 174 | 2,93 | 346,5 | 452,80 | 1,09 |
| `SEG-INACTIF` | 50 | 0,00 | 0,0 | 0,00 | 0,18 |

## 4. Le résultat — un second biais, orthogonal au premier

Les trois groupes ont des compositions **quasi identiques** sur les variables
qui n'ont pas servi à les construire :

| Segment | `critical` | `high` | `medium` | `low` | `SITE-NORD` | Types distincts |
|---|---:|---:|---:|---:|---:|---:|
| `SEG-1` | 10,94 % | 30,73 % | 41,67 % | 16,67 % | 44,27 % | 18 / 18 |
| `SEG-2` | 12,07 % | 28,16 % | 40,80 % | 18,97 % | 40,80 % | 18 / 18 |
| `SEG-INACTIF` | 8,00 % | 28,00 % | 44,00 % | 20,00 % | 34,00 % | 16 / 18 |

Même criticité, même site dominant, même âge moyen (11,4 / 11,4 / 10,7 ans),
même puissance moyenne (72,6 / 72,8 kW), et les 18 types d'équipement présents
dans chacun. Les segments ne sont **ni géographiques, ni typologiques, ni
hiérarchiques**.

Et pourtant :

| Segment | Instrumentés / total | Taux |
|---|---:|---:|
| `SEG-2` | 2 / 174 | **1,15 %** |
| `SEG-INACTIF` | 1 / 50 | 2,00 % |
| `SEG-1` | 33 / 192 | **17,19 %** |

**Un facteur 15 entre `SEG-1` et `SEG-2`**, sur deux populations que rien ne
distingue en criticité, en site, en type, en âge ni en puissance. **33 des 36
équipements instrumentés — 92 % de l'instrumentation — sont concentrés dans un
segment qui représente 46 % du parc.**

Le brief 1 avait établi un premier biais : l'instrumentation suit la criticité
(×23 entre `critical` et `low`). Celui-ci en est **indépendant** : à criticité
égale, l'instrumentation suit l'intensité de maintenance. C'est ce que les
comptages par site ne montraient pas.

### Le sens de la relation n'est pas établi

Deux lectures restent possibles et les données ne permettent pas de trancher :

1. **on instrumente ce qui tombe souvent en panne** — l'activité précède
   l'instrumentation ;
2. **on enregistre plus d'interventions sur ce qui est instrumenté**, parce que
   les anomalies y sont visibles — l'instrumentation précède l'activité.

Un élément va dans le sens de la seconde, sans la démontrer : **à l'intérieur du
seul `SEG-1`**, les équipements instrumentés portent en moyenne 8,70
interventions contre 6,23 pour les non instrumentés du même segment. L'écart
persiste donc à niveau d'activité comparable. Sur l'ensemble du parc, il est de
8,14 contre 3,93.

Trancher demanderait la date de pose des capteurs, absente du jeu de données.
La conséquence pour M4 est la même dans les deux cas : le parc instrumenté n'est
pas un échantillon du parc.

### Limite de la segmentation elle-même

**La silhouette retenue vaut 0,193**, et elle ne dépasse 0,175 pour aucun `k`
entre 2 et 10. C'est faible. Les groupes ne sont pas nettement séparés : la
structure du parc est un **gradient continu d'intensité de maintenance**, pas
une collection de familles distinctes. Le découpage en deux est une coupe
opérée dans ce gradient, pas la découverte d'une frontière.

Cela n'invalide pas le résultat de couverture — le facteur 15 est mesuré sur des
effectifs de 174 et 192 — mais interdit de présenter `SEG-1` et `SEG-2` comme
deux populations de nature différente.

## 5. Trois questions que ce jeu de données ne permet pas de traiter

### Question 1 — population absente

> *Quel signal précède une défaillance sur un équipement de `SITE-OUEST`, ou sur
> une presse, ou sur une vanne ?*

Aucune réponse possible. `SITE-OUEST` : **0 équipement instrumenté sur 16**.
Sept types d'équipement n'ont **aucune mesure**, dont `press` (34 équipements)
et `valve` (21) — soit **90 équipements, 21,6 % du parc**, sur lesquels le jeu
ne dit rien du tout. L'absence de signal n'y vaut pas absence de problème.

### Question 2 — effectifs insuffisants

> *À quoi ressemble la dégradation d'un équipement peu sollicité ?*

`SEG-2` regroupe **174 équipements, 41,8 % du parc**, dont **2 sont
instrumentés**. Toute caractérisation reposerait sur deux équipements, et rien
ne garantit qu'ils soient représentatifs des 172 autres — d'autant que ces deux
équipements ont pu être instrumentés précisément parce qu'ils sortaient de
l'ordinaire. La criticité `low` illustre le même mur : **1 équipement
instrumenté sur 75**.

### Question 3 — grain inadapté

> *Combien de transitoires de courte durée ont précédé les incidents ?*

Le pas d'échantillonnage est de **6 heures**. Le théorème d'échantillonnage
interdit de caractériser toute variation de période inférieure à 12 heures : un
transitoire d'une heure est invisible, et **rien dans les données ne permet de
savoir combien il y en a eu**. Aucune fabrication ne peut créer cette
information — augmenter ou générer à ce pas reproduirait le trou, en le rendant
plus difficile à voir.

## 6. Ce que cette étape impose à la suite

**Pour l'arbitrage A2 (périmètre à générer).** `SITE-OUEST` reste le cas le plus
net au sens du brief, mais ses 16 équipements se répartissent sur les trois
segments (`SEG-2` : 8, `SEG-1` : 6, `SEG-INACTIF` : 2). **Générer `SITE-OUEST`
ne comble donc aucun segment** — cela ajoute des mesures à une population déjà
hétérogène. Le trou le plus significatif, en volume comme en enjeu, est
`SEG-2` : 174 équipements pour 2 instrumentés.

**Pour la partie 6 (biais).** Deux des trois biais à nommer sont déjà chiffrés :
biais de couverture par criticité (×23, brief 1) et biais de couverture par
intensité de maintenance (×15, ici), le second indépendant du premier.

**Pour la partie 4 (détection).** Le rapprochement événements / mesures ne
couvre que 89 événements. Comme instrument de détection sur le lot de contrôle,
il ne pourra donc s'appliquer qu'aux mesures tombant dans une fenêtre
d'événement — c'est une contrainte de portée à mesurer avant d'y compter.
