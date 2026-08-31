---
module: M3
brief: brief 2 — online
etat: étape 2 terminée
maj: 2026-08-25
---

# Augmentation de séries — étape 2

Augmenter, c'est déformer une série réelle pour en obtenir des variantes. Aucune
information n'est créée : chaque technique déplace un compromis.

Cinq techniques sont appliquées aux **70 séries** de la préparation du brief 1
(50 225 mesures exploitables). Pour chacune, ce document ne dit pas seulement ce
qu'elle préserve : il mesure ce qu'elle détruit, avec des seuils déclarés.

Rejouable par `python run_augmentation_b2.py` — graine `25082026`, sorties
identiques à l'octet près sur deux exécutions.

> **70 séries et non 72.** Le cadrage du brief 1 en comptait 72 sur la source
> brute. Deux ont disparu à la préparation : `EQ-ORPHAN-777 / temperature_c`,
> exclue par `R-SEN-013` (équipement absent du parc), et
> `EQ-PUMP-001 / 'TEMPERATURE_C '`, fusionnée dans `temperature_c` par la
> normalisation du nom de capteur. Ce n'est pas une perte de données.

## 1. Une découverte préalable : la saisonnalité journalière

La première version de ce travail mesurait la structure temporelle par
l'autocorrélation de **rang 1**, et concluait que les séries DiagOps n'en
avaient pratiquement pas (+0,079). C'était faux.

| Rang | Écart | Autocorrélation moyenne |
|---:|---|---:|
| 1 | 6 h | **+0,079** |
| 2 | 12 h | **−0,585** |
| 3 | 18 h | +0,060 |
| 4 | 24 h | **+0,694** |
| 8 | 48 h | +0,644 |
| 28 | 168 h | +0,684 |

Les séries portent un **cycle journalier**, à raison de quatre mesures par jour.
Au rang 1, le signal est en quadrature de phase : l'autocorrélation y est nulle
**par construction**. C'était exactement le rang où l'on ne pouvait rien voir.

Le rang 2 (12 h) est en opposition de phase, d'où l'anticorrélation de −0,585 ;
le rang 4 (24 h) est en phase, d'où +0,694. Les rangs 8 et 28 confirment : la
périodicité est bien de 24 h, sans composante hebdomadaire distincte.

**Ce que ça change**, au-delà de cette étape :

- l'axe le plus informatif des séries DiagOps est la **saisonnalité journalière**.
  C'est la relation que la génération de la partie 3 devra reproduire, et la
  première que le tirage marginal détruira ;
- pour la partie 4, c'est le levier de détection des fabrications de la famille 2
  (« rééchantillonnage marginal qui ne se trahit que par la structure
  temporelle ») — à condition de regarder aux rangs 2 et 4, pas au rang 1.

## 2. Ce qui est mesuré, et selon quels seuils

| Propriété | Mesure | Seuil de « préservé » |
|---|---|---|
| Ordre de grandeur | écart relatif de la moyenne et de l'écart-type | ≤ 1 % |
| Fidélité point à point | corrélation avec la série d'origine | ≥ 0,99 |
| Structure temporelle | autocorrélation aux rangs **2 et 4** | écart ≤ 0,05 |
| Régularité du pas | part des intervalles à 6 h exactement | perte ≤ 1 point |
| Plausibilité physique | valeurs hors plage robuste, 8 MAD (`R-SEN-009`) | pas d'augmentation |
| Présence aux événements | mesures dans une fenêtre (−48 h / +24 h) | ≥ 95 % conservées |
| Signal aux événements | niveau moyen pendant les fenêtres | écart ≤ 1 % |

Les seuils sont arbitraires mais **déclarés et versionnés** : sans eux,
« préservé » resterait une appréciation.

### Une seconde métrique corrigée en cours de route

La première version ne mesurait le lien aux événements que par la **présence** —
combien de mesures tombent encore dans une fenêtre. Verdict pour la permutation
de segments : lien préservé à 100 %. Absurde : la permutation ne déplace aucun
horodatage, donc le compte ne peut pas changer, alors que les valeurs associées
à l'événement ne sont plus les siennes.

La métrique comptait la présence, pas la pertinence. Corrigée par l'ajout du
**niveau moyen pendant la fenêtre**, la permutation tombe de 100 % à **31,4 %**.

C'est la deuxième fois dans cette seule étape qu'une mesure juste dans
l'intention se révèle inopérante dans sa formulation.

## 3. Les cinq techniques

| Procédé | Transformation | Paramètres |
|---|---|---|
| `PROC-AUG-BRUIT` | bruit gaussien additif | σ = 2 % de l'écart-type de la série |
| `PROC-AUG-ECHELLE` | mise à l'échelle multiplicative | facteur 1,05 |
| `PROC-AUG-DECALAGE` | décalage temporel global | +18 h (3 pas nominaux) |
| `PROC-AUG-PERMUT` | permutation de blocs contigus | blocs de 4 mesures (24 h) |
| `PROC-AUG-DEFORM` | déformation de l'axe temporel | chaque intervalle × U(0,75 ; 1,25) |

Résultats, en part des 70 séries où la propriété tient :

| Procédé | Ordre de grandeur | Fidélité | Structure | Pas | Plausibilité | Présence évts | Signal évts |
|---|---:|---:|---:|---:|---:|---:|---:|
| `PROC-AUG-BRUIT` | 100 % | 100 % | 100 % | 100 % | 100 % | 100 % | 100 % |
| `PROC-AUG-ECHELLE` | **0 %** | 100 % | 100 % | 100 % | 94,3 % | 100 % | **0 %** |
| `PROC-AUG-DECALAGE` | 100 % | — | 100 % | 100 % | 100 % | 97,1 % | 90,0 % |
| `PROC-AUG-PERMUT` | 100 % | **0 %** | **27,1 %** | 100 % | 100 % | 100 % | **31,4 %** |
| `PROC-AUG-DEFORM` | 100 % | — | 100 % | **0 %** | 100 % | 97,1 % | 88,6 % |

« — » : propriété non mesurable, l'axe temporel ayant changé. Ces cas sont
exclus du dénominateur et non comptés comme des échecs.

### `PROC-AUG-BRUIT` — bruit gaussien

**Préserve** tout, aux seuils retenus : corrélation 0,9998, écart-type +0,03 %,
autocorrélations inchangées à 0,0001 près.
**Détruit** les valeurs exactes — réel, mais sous le seuil de détection de
toutes nos métriques à σ = 2 %.
**Admissible** pour produire des variantes destinées à un apprentissage robuste
au bruit de mesure. **Non admissible** dès qu'une valeur individuelle fait foi :
seuil d'alarme, preuve de dépassement, valeur contractuelle.

### `PROC-AUG-ECHELLE` — mise à l'échelle

**Préserve** la forme exactement (corrélation 1,0000), la structure temporelle
et la grille.
**Détruit** le niveau absolu : +5,0002 % sur la moyenne, +4,996 % sur
l'écart-type. Et **fait sortir des valeurs de la plage plausible** : 8 valeurs
hors plage avant, **13 après**. La transformation fabrique donc de nouvelles
anomalies apparentes, sur 4 séries.
**Admissible** pour simuler un défaut d'étalonnage — c'est même sa raison
d'être. **Non admissible** pour toute analyse de niveau : comparaison à un
seuil physique, calcul de consommation, diagnostic de dépassement.

### `PROC-AUG-DECALAGE` — décalage temporel

**Préserve** toutes les marginales à l'identique (écart 0,0000 %) et toute la
structure temporelle (autocorrélations inchangées au dix-millième).
**Détruit**, en principe, le calendrier — mais **pas autant qu'annoncé**.

C'était l'effet attendu le plus net, et la mesure le dément : sur 2 560 mesures
en fenêtre d'événement, **2 553 y sont encore** après un décalage de 18 h. Le
lien tient sur 97,1 % des séries.

**Ce n'est pas un défaut de la technique, c'est un constat sur le brief 1.** La
fenêtre d'observation retenue — 48 h avant le début, 24 h après la fin — est
tellement plus large qu'un décalage de 18 h que celui-ci ne fait pratiquement
sortir personne. Le rapprochement temporel du brief 1 est **peu sélectif** : il
tolère un désalignement de trois quarts de journée sans le voir.

La métrique de niveau est un peu plus sensible : le signal en fenêtre est
conservé sur 90 % des séries seulement.

**Admissible** pour produire des variantes destinées à l'étude des formes de
série. **Non admissible** dès qu'un rapprochement temporel est en jeu — et à
proscrire pour une transmission, puisque les mesures de fin de série sortent de
la période annoncée (`R-SEN-014`).

### `PROC-AUG-PERMUT` — permutation de segments

C'est le cas central du brief.

**Préserve les marginales exactement** — mêmes valeurs, même moyenne, même
écart-type, mêmes quantiles, à 0,0000 % près. Sur un histogramme, la série
augmentée est **rigoureusement indiscernable** de l'originale.
**Détruit** ce qui ne se voit pas sur un histogramme :

- la fidélité point à point s'effondre — corrélation moyenne **0,347** ;
- la saisonnalité recule — rang 4 : **+0,694 → +0,442** ; rang 2 : −0,585 → −0,508 ;
- le signal pendant les fenêtres d'événement n'est conservé que sur **31,4 %**
  des séries.

La destruction est **partielle**, et c'est instructif : les blocs font 24 h et
sont alignés sur la journée, donc le cycle intra-journalier survit à l'intérieur
de chaque bloc. Seule la succession des jours est cassée. Une taille de bloc non
alignée sur la période détruirait bien davantage.

**Admissible** pour produire un témoin négatif — une série qui a les bonnes
valeurs et le mauvais ordre, exactement ce qu'il faut pour vérifier qu'un
contrôle regarde la structure et pas seulement la distribution. **Non
admissible** pour toute analyse temporelle, de tendance ou de corrélation aux
événements.

### `PROC-AUG-DEFORM` — déformation de l'axe temporel

**Préserve** toutes les marginales et toute la structure (les valeurs et leur
ordre sont intacts).
**Détruit** la grille d'échantillonnage : la part d'intervalles au pas nominal
passe de **99,873 % à 0,014 %**. C'est la transformation la plus visible pour un
contrôle de grille — et la plus invisible pour un contrôle de distribution.

**Admissible** pour simuler une acquisition à rythme irrégulier. **Non
admissible** pour toute analyse fréquentielle, et détectable immédiatement par
le contrôle d'échantillonnage du brief 1 comme par le détecteur de référence.

## 4. Un constat transversal : la clé logique

**Aucune des cinq techniques ne produit une ligne transmissible telle quelle.**

| Procédé | Lignes en collision de clé | Sur 50 225 |
|---|---:|---:|
| `PROC-AUG-BRUIT` | 50 225 | 100 % |
| `PROC-AUG-ECHELLE` | 50 225 | 100 % |
| `PROC-AUG-PERMUT` | 50 225 | 100 % |
| `PROC-AUG-DECALAGE` | 49 949 | 99,5 % |
| `PROC-AUG-DEFORM` | 73 | 0,1 % |

Une ligne augmentée conserve `equipment_id` et `sensor_name` par construction.
Dès que l'horodatage est conservé lui aussi, le triplet de la clé logique est
identique à celui de la mesure réelle : `R-SEN-001` est violée, et les deux
lignes sont indiscernables au sens de la clé.

Seule la déformation temporelle y échappe, et par accident — ses horodatages
tombent rarement sur la grille d'origine.

**Conséquence pour la partie 6** : une table transmise à M4 contenant à la fois
le réel et son augmentation ne peut pas se contenter du triplet comme clé. Il
faut soit un identifiant de ligne distinct, soit une clé étendue par
`procedure_id`. C'est une contrainte de schéma, pas un détail d'implémentation.

## 5. Limites de ce qui précède

- **Le seuil de niveau capte aussi les changements d'échelle.**
  `PROC-AUG-ECHELLE` sort à 0 % sur le signal aux événements, alors que la forme
  du signal est parfaitement conservée : c'est le niveau global qui a bougé de
  5 %, pas le lien à l'événement. Cette ligne se lit avec la colonne « ordre de
  grandeur », pas seule.
- **Les seuils sont des choix.** À σ = 2 %, le bruit gaussien ne détruit rien de
  mesurable ; à σ = 20 %, le verdict serait tout autre. Les résultats valent pour
  les paramètres déclarés, pas pour la famille de techniques.
- **Une seule série sert aux figures** (`EQ-PUMP-001 / vibration_mm_s`, 721
  mesures, 3 fenêtres d'événement). Les chiffres du tableau portent, eux, sur les
  70 séries.
- **Aucune de ces augmentations n'est retenue pour transmission à ce stade.**
  L'étape 2 mesure des coûts ; la décision de transmettre appartient à la
  partie 6, et devra tenir compte de la collision de clé ci-dessus.

## 6. Figures

- `figures/augmentation_series.png` — la série de référence avant et après
  chaque technique, 60 premières mesures ;
- `figures/augmentation_distributions.png` — les distributions comparées. Deux
  techniques n'y laissent **aucune trace** alors qu'elles ont détruit la série :
  le décalage temporel et la permutation de segments. C'est l'illustration du
  point central du brief.
