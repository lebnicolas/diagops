---
module: M3
brief: brief 2 — online
etat: six étapes terminées
maj: 2026-08-31
---

# Plan de travail — Brief 2 M3

« Ce que ce jeu de données permet, et ce qu'il faut fabriquer pour la suite »

Ce document cadre le travail avant toute exécution. Il fixe le point de départ,
l'arborescence, les conventions, l'ordre des étapes et les arbitrages à
trancher. Il ne contient aucun résultat.

---

## 1. Ce que le brief change

Le brief 1 a conclu sur la **qualité** des données : `utilisable sous
conditions`. Le brief 2 pose une question différente — la **capacité**. Un jeu
de données peut être irréprochable et incapable de porter la question qu'on veut
lui poser.

Trois évolutions de cadre, à retenir :

- **les techniques de génération et d'augmentation remontent du M6 au M3**
  (`acquis_m3.md` révisé). Motif donné : ces techniques répondent à « que permet
  ce jeu de données », question qui se pose *avant* la modélisation ;
- **le contrat de provenance entre au `SCHEMA.md`.** Toute table de mesures
  transmise déclare `provenance` (`réelle` / `synthétique` / `augmentée`) et
  `procedure_id`. Transmettre du fabriqué sans provenance est **bloquant** ;
- **le régime d'échange change.** Briefs 1 : revues collectives possibles.
  Brief 2 : strictement individuel, le lot de contrôle étant identique pour les
  trois apprenants et son oracle non distribué.

## 2. Le dispositif de contradiction

Il n'y a pas de séance collective. Deux artefacts remplacent le formateur.

| Artefact | Rôle | Ce qu'il ne donne pas |
|---|---|---|
| `tools/verify_synthetic.py` | contrôles de référence M2 + M3 appliqués à **nos** productions | jamais la liste des lignes — uniquement des comptages par famille de règle |
| `data_pack/2026-S1/sensors_control/control_batch.csv` (6 000 l.) | lot à qualifier, **sans** colonne de provenance | la proportion fabriquée, les procédés, l'oracle |
| `control_sample.csv` (720 l., disjoint) | calibrage des règles, provenance déclarée | ne sert jamais à conclure sur le lot |

Trois pièges posés délibérément par le matériel, à traiter comme des contraintes
de conception et non comme des surprises :

1. **les lignes authentiques du lot portent les anomalies de qualité de la
   livraison M3.** Une ligne signalée par un contrôle de qualité n'est *pas* une
   ligne fabriquée. Nos 15 règles capteurs du brief 1 détectent la qualité, pas
   l'authenticité : les réutiliser telles quelles produira des faux positifs, et
   c'est précisément ce que le lot mesure ;
2. **le détecteur déclare son angle mort** : ni structure temporelle, ni
   cohérence inter-sources. Les fabrications de difficulté 2 (rééchantillonnage
   marginal) et 3 (greffe de segments réels) ne se trahissent que là. Le
   rapprochement temporel du brief 1 devient un **instrument de détection** ;
3. **« le détecteur ne signale rien » n'est pas une réussite.** Le présenter
   comme une preuve de fidélité est un critère bloquant. Il faudra trancher
   entre générateur fidèle et détecteur aveugle, avec un élément à l'appui.

## 3. Point de départ et intégrité

Lot de contrôle vérifié à la synchronisation du 25/08 :

```
control_batch.csv   90b45987…8964   OK
control_sample.csv  cc8912a2…1da0   OK
```

Révision du pack : `diagops-2026-S1-m3-v2`. Graine du lot amont : `20260825`
(celle du formateur — ne pas la réutiliser pour nos générateurs).

**Environnement** : `work/M3/.venv` (Python 3.12.10) suffit — numpy 2.3.2,
pandas 2.3.1, scikit-learn 1.7.1, matplotlib 3.10.3, scipy 1.16.0. Aucune
bibliothèque spécialisée à installer : le brief demande explicitement d'écrire
les méthodes à la main.

**Graine de nos productions** : `SEED = 25082026`, constante unique, importée
partout. Toute sortie doit être rejouable à l'octet près.

## 4. Arborescence retenue

Le travail reste dans `work/M3/`, en continuité du brief 1 — mêmes conventions
(`run_<etape>_b2.py` à la racine, logique en paquet, sorties sous `output/`,
un document par sujet dans `docs/`). Le suffixe `_b2` distingue les scripts du
brief 2 sans créer une seconde arborescence.

```text
work/M3/
├── run_capacite_b2.py            → output/capacite/          (partie 1)
├── run_augmentation_b2.py        → output/augmentation/      (partie 2)
├── run_generation_b2.py          → output/generation/        (partie 3)
├── run_detection_b2.py           → output/detection/         (partie 4)
├── run_confidentialite_b2.py     → output/confidentialite/   (partie 5)
├── run_transmission_b2.py        → output/transmission/      (partie 6)
├── src/brief2/
│   ├── seed.py            constante SEED, fabriques de générateurs numpy
│   ├── sources.py         chargement du point de départ (arbitrage A1)
│   ├── capacite.py        effectifs, ratios, couverture, segmentation
│   ├── augmentation.py    transformations de séries + fiche préserve/détruit
│   ├── generation.py      tirage marginal, interpolation entre voisins
│   ├── detection.py       règles de détection, verdicts, motifs
│   ├── privacy.py         sensibilité, mécanisme de Laplace
│   └── provenance.py      colonnes provenance / procedure_id, registre procédés
├── notebooks/
│   └── notebook_capacite_m3_b2.ipynb   + export HTML
└── docs/
    ├── plan_brief2.md                  ce document
    ├── capacite_jeu_donnees.md         partie 1, dont les 3 questions ✔
    ├── augmentation_techniques.md      partie 2 ✔
    ├── comparaison_reel_fabrique.md    partie 3 ✔
    ├── detection_lot_controle.md       partie 4
    ├── confidentialite_agregats.md     partie 5
    ├── biais_et_risques.md             partie 6
    ├── registre_regles.md              (mis à jour)
    ├── decision_transmission_m4.md     (réécrit)
    ├── couverture_et_risques.md        (périmètre de validité réécrit)
    ├── flux_et_cycle_de_vie.md         (cycle de vie d'une donnée fabriquée)
    └── journal_bord.md                 (section brief 2 + table du détecteur)
```

**Sorties de données** : `output/transmission/sensor_readings_m4.csv` (jeu
transmis, avec provenance) et `output/detection/verdicts_control_batch.csv`
(6 000 lignes, un verdict + une règle chacune). Les fichiers générés
intermédiaires ne sont pas des livrables — ils doivent se reproduire depuis le
code.

## 5. Conventions de nommage

| Objet | Préfixe | Exemple |
|---|---|---|
| Règles héritées / qualité | `R-EQ-`, `R-EVT-`, `R-MNT-`, `R-SEN-` | inchangé, 34 règles du brief 1 |
| Règles de **détection d'authenticité** | `R-DET-` | `R-DET-001` grille temporelle irrégulière |
| Procédés de fabrication (`procedure_id`) | `PROC-` | `PROC-SMOTE-V2`, `PROC-MARG-V1`, `PROC-AUG-NOISE` |
| Segments du parc | `SEG-` | `SEG-3` |

Les règles `R-DET-*` sont un **registre distinct** de celui de la qualité, et
c'est un point à défendre : détecter une fabrication et détecter une anomalie
sont deux questions différentes, le lot est construit pour punir la confusion.
Le registre de règles existant est mis à jour, pas remplacé.

## 6. Découpage en étapes

Les parties 3 et 4 forment une boucle : on génère, on soumet au détecteur, on
corrige le générateur, on resoumet. Prévoir au moins deux tours — deux états
successifs du générateur avec leur verdict sont une exigence minimale.

### Étape 1 — Chiffrer l'incapacité (partie 1)

**Déjà acquis au brief 1, réutilisable tel quel** : couverture 8,65 % (36/416),
`SITE-OUEST` 0/16, 7 types sans mesure, ratio criticité ×23, 83 % des événements
hors de portée. Ces chiffres sont dans `docs/couverture_et_risques.md` et
`output/cadrage/cadrage.json` — ne pas les recalculer, les citer.

**À produire** :

- les **visualisations** des distributions (le brief les exige, le brief 1 les
  avait rendues en tableaux) ;
- le **rapport max/min explicite** sur au moins deux variables — la formulation
  du brief est un rapport d'effectifs, distinct du rapport de *taux* ×23 déjà
  calculé ;
- la part d'événements disposant de mesures **par catégorie** (le brief 1 donne
  le global 89/514) ;
- la **segmentation** du parc — c'est le vrai ajout de l'étape ;
- **trois questions que le jeu ne permet pas de traiter**, chacune adossée à un
  chiffre.

### Étape 2 — Augmenter (partie 2)

Deux techniques distinctes au minimum, chacune documentée par ce qu'elle
**préserve** et ce qu'elle **détruit** : ordre de grandeur, unité, régularité du
pas, saisonnalité, corrélation aux événements, plausibilité physique. Une
technique produisant une série physiquement impossible se documente, elle ne se
supprime pas.

### Étape 3 — Générer (partie 3)

Périmètre non couvert, borné. Deux voies obligatoires :

- **tirage marginal** — chaque colonne rejouée indépendamment ;
- **interpolation entre voisins** (principe SMOTE), écrite à la main avec
  `NearestNeighbors`, **traitement explicite des colonnes catégorielles**
  (utiliser une interpolation numérique sur une catégorie encodée est le
  contresens que le critère bloquant vise).

Comparaison réel / fabriqué obligatoirement **sur les relations**, pas seulement
sur les marginales : une comparaison limitée aux moyennes est bloquante. Le point
central du brief est que le tirage marginal préserve chaque histogramme et
détruit toutes les corrélations — et que cette perte est invisible sur un
histogramme.

### Étape 4 — Se confronter (partie 4)

**Sens 1** — nos productions au détecteur. Chaque exécution consignée avec son
hypothèse *avant* lancement.

**Sens 2** — nos règles sur le lot. Calibrage sur `control_sample.csv`, puis
verdict par ligne sur `control_batch.csv` : `réelle` / `fabriquée` /
`indécidable`, chacun rattaché à une règle nommée. Remonter au multi-source
quand les contrôles ligne à ligne saturent.

Conclusion obligatoire sur nos propres règles du brief 1 : lesquelles ont servi,
lesquelles n'ont rien attrapé, lesquelles ont accusé à tort une mesure réelle.

### Étape 5 — Protéger (partie 5)

Mécanisme de Laplace sur un agrégat trop peu fourni : sensibilité, budget `ε`,
bruit, résultat. **Au moins trois valeurs de `ε`**, avec l'effet mesuré sur
l'utilité. Conclure sur les deux bornes : à partir de quand le chiffre cesse
d'être exploitable, à partir de quand il cesse de protéger. Un `ε` unique
présenté comme un choix est bloquant.

### Étape 6 — Décider (partie 6)

Provenance sur chaque ligne transmise. **Trois biais** nommés, rattachés à des
comptages, avec atténuation, coût et **risque résiduel**. Dire lesquels
l'augmentation et la génération corrigent, et lesquels elles amplifient.
Décision de transmission justifiée par les résultats des parties 1 à 5. Périmètre
de validité du brief 1 réécrit s'il n'est plus exact.

## 7. Arbitrages à trancher

Ces cinq points ne se déduisent pas du brief. Ils sont à décider avant de coder
l'étape concernée ; ils seront défendus, donc ils sont tracés ici avec leur
motif.

| # | Arbitrage | Options | Décision |
|---|---|---|---|
| **A1** ✔ | Préparation de départ | (a) référence `m2_for_m3` seule, comme au brief 1 ; (b) notre préparation du brief 1, `output/processed/` | **tranché le 25/08 : (b)** — 416 équipements, 514 événements, 1 788 interventions, 50 277 mesures. Elle dérive de la référence, la filiation reste traçable, et le rapprochement temporel du brief 1 devient exploitable comme instrument de détection |
| **A2** ✔ | Périmètre à générer | `SITE-OUEST` (16 équipements, 0 capteur) ; un type absent comme `press` (34) ou `valve` (21) | **tranché le 25/08 : `SITE-OUEST` ∩ `SEG-2`** — 8 équipements, 2 capteurs, janvier 2026. Satisfait le brief (SITE-OUEST) et vise le trou chiffré à l'étape 1 (SEG-2). Criticités équilibrées : 2 `critical`, 2 `high`, 2 `medium`, 2 `low` |
| **A3** ✔ | Variables de segmentation | référentiel seul (type, criticité, puissance, âge, site) ; référentiel + activité (nb événements, nb interventions, coût pièces, indisponibilité) ; activité seule | **tranché le 25/08 : référentiel + activité** — la segmentation doit montrer ce que les comptages par site ne montrent pas ; sans variables d'activité elle reproduirait la partition par type. **La couverture instrumentale est exclue des variables de segmentation** : l'inclure rendrait tautologique la conclusion « ces groupes sont mal couverts ». Elle est croisée *après*, et c'est ce croisement qui constitue le résultat |
| **A4** ✔ | Agrégat à protéger | à choisir sur les petits effectifs réels — candidats : interventions par site × type, `SITE-OUEST` (16 équipements), comptages par technicien | **tranché le 26/08 : coût moyen des pièces par site × criticité**, 16 cellules dont 5 sous 40 interventions. Plafond de sensibilité à 750 € comparé à 500 et 1 128 ; huit budgets balayés. Résultat structurant : la sortie n'est pas le budget, c'est la maille |
| **A5** ✔ | Politique d'`indécidable` | seuil strict (peu d'indécidables, plus d'erreurs) ; seuil prudent (beaucoup d'indécidables) | **tranché le 26/08 : seuil strict**, verdict au bloc de 30 lignes, une seule famille de règles décidant. 30 lignes `indécidable` sur 6 000 (1 bloc sur 200). Coût mesuré : calibrage juste à 95,83 %, une erreur — un bloc fabriqué identique à la livraison ligne pour ligne, donc indétectable par toute règle interne |

## 8. Journal — traçabilité des exécutions du détecteur

Exigence explicite du brief : chaque exécution de `verify_synthetic.py` est
consignée **avec l'hypothèse qui l'a motivée**. Une série d'essais sans
hypothèse n'est pas une démarche, et l'omission est un critère bloquant.

Table à tenir dans `docs/journal_bord.md`, section brief 2 :

| # | Date | Fichier soumis | Hypothèse formulée avant | Comptages retournés | Ce que ça apprend | Changement effectué |
|---|---|---|---|---|---|---|

L'hypothèse s'écrit **avant** de lancer, pas après lecture du résultat.

## 9. Critères bloquants — les six pièges à surveiller

Les quinze critères bloquants du brief se ramènent à six comportements :

1. **fabriquer sans étiqueter** — provenance absente, ou générateur non
   reproductible ;
2. **décrire sans détruire** — présenter une technique par ses bénéfices sans
   dire ce qu'elle détruit, ou comparer réel et fabriqué sur les seules moyennes ;
3. **utiliser une méthode en boîte noire** — interpolation entre voisins sans
   traitement explicite des catégories ;
4. **verdict sans règle** — un verdict non motivé, ou un lot majoritairement
   `indécidable` sans démarche ;
5. **prendre le silence pour une preuve** — l'absence de signalement présentée
   comme fidélité, les exécutions non consignées ;
6. **conclure sans compter** — `ε` unique, biais cités sans comptage,
   atténuation sans risque résiduel, décision de transmission sans chiffre.

## 10. Hors périmètre

Ce brief prépare M4 sans l'entamer. Sont explicitement exclus : analyse d'un
besoin métier, jeu d'évaluation, partition, protocole, métrique cible, choix ou
entraînement de modèle, courbe ROC, générateur à base d'apprentissage,
génération d'images ou de texte, garantie formelle de confidentialité.

Les comptages de détection produits ici constituent une **base de comparaison
par règles** — le point de départ que le modèle de M4 devra battre.

## 11. Point ouvert repris du brief 1

La remontée formateur (`docs/remontee_formateur.md`) est rédigée et **toujours
non envoyée**. La contradiction `SCHEMA.md` / `contracts/schemas.py` sur
`event_type` (`alerte` contre `alert`) est **encore présente** dans la
publication du 25/08 — désormais ligne 184, décalée par les ajouts du contrat de
provenance. Elle traverse donc deux publications successives.

---

## 12. Clôture — 31/08/2026

Les six étapes sont exécutées. Les cinq arbitrages sont tranchés et tracés.

| Étape | Sortie de données | Document |
|---|---|---|
| 1 — capacité | `output/capacite/` | `capacite_jeu_donnees.md` |
| 2 — augmentation | `output/augmentation/` | `augmentation_techniques.md` |
| 3 — génération | `output/generation/` | `comparaison_reel_fabrique.md` |
| 4 — confrontation | `output/detection/` | `detection_lot_controle.md` |
| 5 — protection | `output/confidentialite/` | `confidentialite_agregats.md` |
| 6 — transmission | `output/transmission/` | `biais_et_risques.md`, `decision_transmission_m4.md` |

**Livrables du brief** : notebook `notebooks/notebook_capacite_m3_b2.ipynb`
(exécuté de bout en bout, conclusion intégrée) et son export HTML ; le code sous
`src/brief2/` et les sept `run_*_b2.py`, rejouables à graine fixe ;
`output/detection/verdicts_control_batch.csv` ; le registre de règles mis à jour
(`R-DET-*` et `R-TRA-*`) ; `output/transmission/sensor_readings_m4.csv` avec sa
colonne de provenance ; la note de décision ; la description du jeu et le cycle de
vie mis à jour ; le journal de bord avec les 18 soumissions du détecteur et leurs
hypothèses.

**Deux écarts au plan initial, tous deux assumés :**

- `run_transmission_b2.py` produit aussi les comptages de biais, là où le plan
  prévoyait un `biais_et_risques.md` alimenté à la main. Les chiffres d'un
  document qui sert à décider ne doivent pas être recopiés ;
- une règle non prévue est née à l'étape 6 : **`R-TRA-001`**, en réponse à un
  défaut de notre propre chaîne du brief 1 que la soumission du livrable a
  révélé. Le plan n'avait pas anticipé qu'un contrôle extérieur trouverait
  d'abord quelque chose chez nous.

**Tests** : 88 passent, dont 14 nouveaux sur le contrat de provenance et
`R-TRA-001`. Le seul échec de la suite est `test_io.py::test_file_sha256_known_content`,
défaut du starter sous Windows (`Path.write_text` traduit `\n` en `\r\n`) —
inscrit dans `docs/remontee_formateur.md`, toujours non envoyée.
