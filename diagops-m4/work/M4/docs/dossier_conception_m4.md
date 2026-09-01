---
module: M4
brief: brief 1 — online
etat: dossier de conception
maj: 2026-08-31
---

# Dossier de conception — qualification de la gravité d'un rapport technicien

> Brief 1 online. Dossier de conception : il instruit un besoin et recommande
> une décision. **Il ne livre pas un système** — les mesures qui l'étayent sont
> des sondages de faisabilité, faits sur le seul jeu d'entraînement.

---

## 1. Le besoin

### La décision assistée

Un technicien saisit un rapport en **texte libre** — application mobile,
formulaire web, ou transcription radio. La question posée au système est
unique :

> **Quelle gravité attribuer à ce rapport : `critical`, `high`, `medium` ou
> `low` ?**

C'est une décision **observable** : elle produit une valeur dans un domaine
fermé, comparable à celle qu'un expert aurait attribuée. Elle sert à **trier et
prioriser** les signalements avant leur traitement.

### Ce qui en découle, et qu'il ne faut pas modéliser

`requires_human_review` **se déduit de la gravité**, il ne se prédit pas :

| Gravité | En revue humaine | Sans revue |
|---|---:|---:|
| `critical` | 70 | **0** |
| `high` | 212 | **0** |
| `medium` | 153 | **0** |
| `low` | 21 | 44 |

Sur 500 annotations, aucune exception : dès que la gravité dépasse `low`, la
revue humaine est requise. Et tous les cas « sans revue » ont une confiance
≥ 0,90.

> **Conséquence de conception** : une règle de deux lignes remplace un second
> modèle. Modéliser `requires_human_review` séparément reviendrait à apprendre
> une règle qu'on peut écrire — avec le risque de l'apprendre mal.

### Utilisateurs

| | Qui | Ce qu'ils attendent |
|---|---|---|
| **direct** | le technicien qui saisit | une gravité proposée, modifiable |
| **direct** | le superviseur de maintenance | une file triée par gravité |
| **indirect** | l'exploitant du site | que rien de grave ne passe inaperçu |
| **indirect** | l'équipe data | des rapports exploitables en aval |

### Erreurs coûteuses — et elles ne sont pas symétriques

| Erreur | Conséquence | Coût |
|---|---|---|
| **`critical` classé `low`** | un signalement grave part en fond de file | **le plus élevé** — c'est l'erreur que le système existe pour éviter |
| `low` classé `critical` | un expert mobilisé pour rien | modéré — du temps perdu, pas un risque |
| confusion `high` / `medium` | ordre de file imparfait | faible — les deux sont traités |

> Le coût est **fortement asymétrique**, et il ne l'est pas de la même façon
> selon les paires de classes. Une métrique unique traitant les quatre classes à
> égalité ne dit pas la même chose que ce que le métier redoute.

### Contraintes de délai et supervision

Le rapport est saisi puis traité ; **aucune décision temps réel** n'en dépend.
Une latence de l'ordre de la seconde est acceptable.

La supervision humaine est **dans le contrat de sortie** : `requires_human_review`
vaut `True` dans 456 cas sur 500, soit 91 %. Le système ne remplace personne, il
ordonne une file.

---

## 2. Les données nécessaires

### Unité d'observation — et c'est la question centrale de ce dossier

| Candidat | Effectif | Verdict |
|---|---:|---|
| l'annotation | 500 | **faux** — voir ci-dessous |
| le rapport (`report_id`) | 500 déclarés | **faux** — 460 n'existent pas |
| **le patron de rédaction** | **80** | **la bonne unité** |

**Les 400 textes d'entraînement ne sont que 80 patrons répétés**, environ cinq
fois chacun. Mesuré : la similarité cosinus moyenne au plus proche voisin est de
**0,863**, on compte **1 576 paires au-dessus de 0,8**, et deux textes atteignent
la similarité **1,000** — identiques à « Equipement-1 » / « Equipement-3 » près.

Et **les 80 patrons ont chacun une gravité unique** : le patron détermine
entièrement l'étiquette.

> C'est une [[fuite par découpage]] au sens strict. Un découpage aléatoire place
> des variantes du même patron des deux côtés du pli : le modèle **reconnaît le
> patron**, il n'apprend pas à qualifier.

**L'effet est mesuré** (TF-IDF + régression logistique, 5 plis, sur le train) :

| Découpage | Exactitude | F1 macro |
|---|---:|---:|
| par ligne | **0,960** | **0,958** |
| **groupé par patron** | **0,695** | **0,560** |
| écart | **−0,265** | **−0,398** |

Le volume défendable n'est donc pas 400 exemples : c'est **80 situations
distinctes**, dont il faut retirer celles réservées à la validation.

### Tableau des données nécessaires

| Donnée | Source | Disponible ? | Rôle | Réserve |
|---|---|---|---|---|
| `input_text` | annotations | oui, 500 | **entrée** | 80 patrons seulement |
| `severity` | `expected_output` | oui, 500 | **cible** | distribution décalée train/test |
| `equipment_id` | annotations | oui | contrôle de fuite | 3 équipements communs train/test sur 392 — **bonne séparation** |
| `confidence` | `expected_output` | oui | dérivation de la revue | c'est une **sortie**, pas une entrée : indisponible à l'inférence |
| `requires_human_review` | `expected_output` | oui | **dérivé par règle** | ne pas modéliser |
| `source_channel` | `reports.jsonl` | **40 sur 500** | segment d'analyse | inexploitable — voir ci-dessous |
| historique capteurs | M3 | oui | enrichissement possible | non relié aux rapports |
| `evidence` | `expected_output` | oui | traçabilité annoncée | **non résoluble à 92 %** |

### Trois défauts de données à porter au dossier

**1. L'intégrité référentielle est rompue.** Les annotations citent 500
`report_id` ; `reports.jsonl` n'en contient que **40**. **460 références sur 500
— 92 % — pointent vers un rapport qui n'existe pas.** Le champ `evidence` de
chaque annotation cite pourtant « rapport RPT-2026S1-XXXX » : **la traçabilité
annoncée n'est pas vérifiable pour 92 % des exemples**.

**2. Le canal de saisie est inexploitable.** `source_channel` — application
mobile, formulaire web, transcription radio — n'existe que pour les 40 rapports
réels. C'est pourtant le segment le plus intéressant : une transcription radio
n'a ni la même ponctuation ni le même vocabulaire qu'un formulaire. **Impossible
de mesurer la robustesse par canal.**

**3. Le train et le test ne suivent pas la même distribution.**

| Classe | Train (400) | Test (100) | Écart |
|---|---:|---:|---:|
| `critical` | 15,0 % | 10,0 % | −5,0 |
| `high` | 44,2 % | 35,0 % | −9,3 |
| `medium` | 25,8 % | **50,0 %** | **+24,2** |
| `low` | 15,0 % | 5,0 % | −10,0 |

Distance de variation totale : **0,242**. `medium` double, `low` est divisé par
trois. **Ce décalage n'est annoncé nulle part dans le pack.** Un modèle calibré
sur le train verra une population différente à l'évaluation.

### Représentativité, droits, confidentialité

**Représentativité** : 80 situations pour 389 équipements et 18 types. La
couverture des situations réelles de terrain est inconnue et probablement faible.

**Confidentialité** : les rapports contiennent des **noms de personnes** —
« Contrôle demandé par Nadia B. ». C'est une donnée personnelle au sens du RGPD,
dans le texte d'entrée. La règle `R-MNT-008` (pseudonymisation), héritée du M2,
s'applique et doit être étendue à ce corpus.

---

## 3. Comparaison des familles de modèles

Quatre familles, chacune retenue contre les autres. Les chiffres viennent de
sondages sur le **train uniquement**, en validation croisée.

### F1 — Modèle à règles

**Principe.** Mots-clés associés à une gravité — « fumée », « arrêt immédiat »
pour `critical` ; « fonctionnement normal » pour `low`.

**Mesuré** : exactitude **0,443**, F1 macro **0,455**.

> **Le piège que ce chiffre révèle.** La baseline triviale — prédire toujours la
> classe majoritaire — obtient **exactement la même exactitude, 0,443**. Mais son
> F1 macro n'est que de **0,153**.
>
> Deux modèles à exactitude identique, dont l'un couvre quatre classes et l'autre
> une seule. **L'exactitude ne voit pas la différence ; le F1 macro la voit
> entièrement.** C'est l'argument qui fixe la métrique de la section 4.

| | |
|---|---|
| Données requises | aucune — de la connaissance métier |
| Explicabilité | **totale** — chaque décision se trace à une règle |
| Généralisation | faible ; les règles vieillissent avec le vocabulaire |
| Coût | rédaction initiale, puis maintenance permanente |
| Contraintes | aucune |

### F2 — Modèle supervisé sur représentation textuelle

**Principe.** TF-IDF (mots et bigrammes) + régression logistique.

**Mesuré** : **0,695** d'exactitude et **0,560** de F1 macro **en validation
groupée par patron** — et 0,960 / 0,958 sans groupement, ce qui est un mirage.

### Ce que le F1 macro de 0,560 cache

Le chiffre agrégé est trompeur. En découpage groupé, classe par classe :

| Classe | Précision | Rappel | F1 | Support |
|---|---:|---:|---:|---:|
| `high` | 0,773 | 0,887 | **0,826** | 177 |
| `medium` | 0,686 | 0,786 | **0,733** | 103 |
| `critical` | 0,661 | 0,650 | **0,655** | 60 |
| **`low`** | **0,050** | **0,017** | **0,025** | 60 |

**La classe `low` est manquée en totalité** — 1 exemple retrouvé sur 60. Les
patrons qui la portent sont peu nombreux ; dès qu'ils sortent du pli
d'entraînement, le modèle n'a jamais vu cette formulation. C'est la conséquence
directe des 80 patrons : sur une classe minoritaire, le découpage groupé retire
l'essentiel du signal.

**Deux lectures, et elles ne mènent pas au même endroit.**

*Défavorable* : un modèle qui ignore une classe sur quatre n'est pas un
classifieur à quatre classes. Le F1 macro de 0,560 est porté par les trois
autres.

*Favorable, et c'est celle que je retiens* : **le sens de l'erreur est le bon**.
Manquer les `low` signifie que le modèle **sur-classe** — il envoie en priorité
ce qui pourrait rester en fond de file. Pour un système qui trie une file sous
supervision humaine, sur-prioriser coûte du temps ; sous-prioriser coûte un
incident. L'erreur tombe du côté le moins cher.

**Le vrai point de vigilance est ailleurs** : le rappel de `critical` est de
**0,650**. **Plus d'un signalement critique sur trois n'est pas reconnu comme
tel.** C'est exactement l'erreur R3 du registre des risques, et c'est elle qui
doit être suivie — pas le F1 macro.

| | |
|---|---|
| Données requises | 80 situations étiquetées — **très peu** |
| Explicabilité | bonne — coefficients par terme, inspectables |
| Généralisation | **incertaine** : le corpus est synthétique et redondant |
| Coût | négligeable — quelques secondes d'ajustement, CPU |
| Contraintes | sensible au vocabulaire ; un nouveau canal de saisie le dégrade |

### F3 — Modèle non supervisé

**Principe.** Regrouper les rapports par similarité, puis étiqueter les groupes.

**Écarté, et le motif est mesuré.** Les 400 textes forment **80 groupes naturels
à gravité unique** : un algorithme de partitionnement retrouverait les patrons de
génération, pas des familles de situations. Il découvrirait la **structure du
générateur**, ce qui n'a aucune valeur métier — et c'est exactement le piège de
la partition triviale rencontré au brief 2 du M3.

Utile pour une chose : **auditer la redondance du corpus**, ce qui a d'ailleurs
servi à écrire la section 2.

### F4 — Modèle pré-entraîné

**Principe.** Un modèle de langue produit la sortie structurée. C'est
l'architecture du M0 (LM Studio, `ministral-3-3b`, contrat JSON) et l'objet du
M1 (adaptateur LoRA sur Qwen3-0.6B).

| | |
|---|---|
| Données requises | **zéro** en amorçage ; quelques centaines pour spécialiser |
| Explicabilité | **faible** — pas de trace de décision par terme |
| Généralisation | la meilleure sur du texte libre non vu |
| Coût | le plus élevé — mémoire, latence de l'ordre de la seconde |
| Contraintes | **rouvre entièrement la question de l'injection indirecte** |

> **Le coût caché, et il est réglementaire.** Introduire un modèle génératif fait
> entrer DiagOps dans le champ de l'obligation de marquage de l'article 50(2) —
> voir `veille_diagops/ai_act_diagops.md`, § 5 — et impose de rejouer la campagne
> de menaces du brief présentiel. Ce coût n'apparaît sur aucun banc d'essai.

### Synthèse

| Critère | F1 règles | **F2 supervisé** | F3 non supervisé | F4 pré-entraîné |
|---|---|---|---|---|
| F1 macro mesuré | 0,455 | **0,560** | — | non mesuré |
| Exactitude mesurée | 0,443 | **0,695** | — | non mesuré |
| Données requises | aucune | 80 situations | aucune | zéro à quelques centaines |
| Explicabilité | totale | bonne | faible | faible |
| Généralisation | faible | incertaine | sans objet | la meilleure |
| Coût d'exploitation | nul | négligeable | nul | élevé |
| Charge réglementaire | nulle | nulle | nulle | **art. 50(2)** |

---

## 4. Protocole d'évaluation

### Métrique de décision : F1 macro

**Pas l'exactitude.** La section 3 le démontre : deux modèles à exactitude
identique (0,443) ont des F1 macro de 0,455 et 0,153. Sur un jeu où `high`
représente 44 % du train et `medium` 50 % du test, l'exactitude récompense la
prédiction de la classe majoritaire — c'est-à-dire le modèle inutile.

**Rapportées à côté, jamais résumées** : la matrice de confusion complète, et le
**rappel de la classe `critical`**, qui porte l'erreur la plus coûteuse.

**Seuil d'acceptation, posé avant toute mesure sur le test** : F1 macro
supérieur à **0,560** — le résultat de F2 en validation groupée — d'un écart
supérieur à la dispersion entre plis. En dessous, la conclusion à écrire est
« aucun gain démontrable ».

### Partition — groupée par patron, sans exception

C'est la conséquence directe de la section 2. Un découpage par ligne surestime la
performance de **26 points d'exactitude et 40 points de F1 macro**.

- **groupe** : le patron de rédaction, obtenu en normalisant identifiants et
  nombres ;
- **méthode** : `StratifiedGroupKFold`, 5 plis répétés ;
- **contrôle bloquant** : aucun patron ne traverse un pli. Le même contrôle que
  le brief présentiel applique à `equipment_id`.

### Jeux et réserve sur le test fourni

Le pack livre un `diagops_test.jsonl` de 100 exemples **avec ses étiquettes** :
ce n'est pas un oracle scellé, contrairement au lot capteur du brief présentiel.

> **Réserve à écrire dans toute conclusion** : le test a une distribution
> différente du train (distance de variation 0,242, `medium` doublé). Une
> performance mesurée dessus mélange deux effets — la qualité du modèle et le
> décalage de population. Les deux doivent être rapportés séparément.

**Discipline retenue** : le test n'est ouvert qu'une fois, après gel du candidat,
et le nombre d'ouvertures est déclaré. C'est la règle du brief présentiel, et
rien ici ne justifie de l'assouplir.

### Analyse ROC

Pertinente en **un contre reste**, principalement pour `critical` : elle
montrerait le compromis entre rappel des cas graves et fausses alertes, qui est
la vraie question métier. Sur 60 exemples `critical` au train, la courbe sera
bruitée — à rapporter avec cette réserve.

### Mesure par segment

| Segment | Faisable ? |
|---|---|
| par classe de gravité | oui — c'est le F1 macro détaillé |
| par patron | oui — 80 groupes, faible effectif chacun |
| **par canal de saisie** | **non — `source_channel` manque sur 460 exemples sur 500** |
| par type d'équipement | oui, via `equipment_id` |

L'impossibilité de mesurer par canal est une **limite du dossier**, pas un choix.

### Conditions de réévaluation

- toute nouvelle livraison d'annotations ;
- l'apparition d'un canal de saisie non représenté ;
- un changement du vocabulaire métier ;
- **un changement de la distribution des gravités** — le décalage train/test
  montre qu'elle bouge.

---

## 5. Registre des risques

| # | Risque | Impact | Atténuation | Risque résiduel |
|---|---|---|---|---|
| **R1** | **le corpus est 80 patrons, pas 400 exemples** | performance surestimée de 26 points | partition groupée par patron, obligatoire | le volume réel reste **très faible** — 80 situations |
| **R2** | décalage de distribution train/test (0,242) | performance mesurée non transposable | rapporter séparément qualité et décalage | non maîtrisable sans nouvelles données |
| **R3** | **`critical` classé `low`** | un signalement grave part en fond de file | rappel `critical` suivi à part — **mesuré à 0,650** | **élevé** : plus d'un critique sur trois n'est pas reconnu |
| **R3 bis** | la classe `low` est manquée en totalité (F1 0,025) | sur-priorisation systématique | garde-fou par règles sur « fonctionnement normal » | du temps d'expert consommé pour rien — **erreur du bon côté** |
| **R4** | corpus **synthétique** | rien ne prouve que des rapports réels ressemblent à ceux-ci | déclarer le périmètre de validité | **entier** — aucune donnée de terrain |
| **R5** | **noms de personnes dans les textes** | données personnelles en entrée (RGPD) | `R-MNT-008`, pseudonymisation héritée du M2 | à étendre à ce corpus, non fait |
| **R6** | `evidence` non résoluble à 92 % | la traçabilité annoncée n'existe pas | signaler au producteur des données | **non traité** |
| **R7** | robustesse par canal non mesurable | une transcription radio peut se comporter autrement | — | **non mesurable** en l'état |
| **R8** | dérive du vocabulaire métier | dégradation silencieuse | réévaluation périodique | inhérent au supervisé |

### Éco-conception

| Famille | Ajustement | Inférence | Mémoire |
|---|---|---|---|
| F1 règles | néant | immédiate | néant |
| **F2 supervisé** | **quelques secondes, CPU** | **< 1 ms** | **quelques centaines de ko** |
| F4 pré-entraîné | heures (GPU) si spécialisation | ~1 s | plusieurs Go |

F2 est **trois ordres de grandeur** moins coûteux que F4, pour un besoin qui ne
demande aucune génération de texte. Sur ce critère seul, F4 devrait démontrer un
gain considérable pour se justifier.

### Cadre réglementaire

Analyse complète dans `veille_diagops/ai_act_diagops.md`. Pour ce besoin :

| | |
|---|---|
| **Obligation établie** | l'article 50(1) — informer que l'on interagit avec une IA — est applicable **depuis le 02/08/2026** |
| **Interprétation** | le système reste une aide au tri sous supervision humaine (91 % des cas), ce qui l'éloigne du haut risque |
| **Validation juridique** | l'article 6(1 ter) — une défaillance mettrait-elle en danger la santé et la sécurité ? Un `critical` classé `low` retarde un traitement : la question mérite d'être posée à une compétence juridique |

Le choix de F2 **plutôt que F4** évite par ailleurs l'obligation de marquage de
l'article 50(2).

---

## 6. Recommandation

> ## Adopter **F2 — supervisé sur représentation textuelle**, sous conditions

**Contre F1 (règles)** : F2 fait 0,560 de F1 macro contre 0,455, avec cent fois
moins de maintenance. Mais l'écart n'est pas celui qu'annonce le chiffre agrégé :
F2 domine nettement sur `high`, `medium` et `critical`, et **s'effondre sur
`low`** (F1 0,025). Les règles restent donc utiles comme **garde-fou**, sur deux
fronts — les formulations sans ambiguïté (« fumée », « arrêt immédiat ») et
**précisément la classe `low`**, où « fonctionnement normal » est un marqueur
lexical fiable que F2 n'exploite pas faute d'exemples.

**Contre F3 (non supervisé)** : sans objet — il retrouverait les patrons du
générateur, pas des familles de situations.

**Contre F4 (pré-entraîné)** : F4 généraliserait mieux sur du texte non vu, et
c'est un vrai argument. Mais il coûte trois ordres de grandeur de plus, perd
l'explicabilité, **fait entrer DiagOps dans l'obligation de marquage de l'article
50(2)** et impose de rejouer toute la campagne de menaces. Sur un besoin de
classification en quatre classes, ce prix ne se justifie pas — **tant qu'on n'a
pas montré que F2 échoue sur des rapports réels.**

### Conditions

1. **partition groupée par patron**, contrôle bloquant — sans quoi toute mesure
   est surestimée de 26 points ;
2. **F1 macro comme métrique de décision**, jamais l'exactitude ;
3. **`requires_human_review` dérivé par règle**, pas modélisé ;
4. **pseudonymisation** appliquée aux textes d'entrée avant tout traitement ;
5. **supervision humaine maintenue** — le système ordonne une file, il ne décide
   pas ;
6. **le rappel de `critical` est suivi comme métrique de sécurité**, séparément
   du F1 macro. À 0,650, plus d'un signalement critique sur trois n'est pas
   reconnu : c'est le chiffre qui doit déclencher une alerte s'il baisse, et il
   ne doit jamais être noyé dans une moyenne.

### Ce qui pourrait changer la décision

| Information manquante | Effet si elle arrivait |
|---|---|
| des **rapports réels**, non synthétiques | si F2 s'effondre dessus, F4 redevient candidat |
| `source_channel` sur tout le corpus | permettrait de mesurer la robustesse par canal — peut-être décisive |
| un **volume supérieur à 80 situations** | rendrait les mesures interprétables |
| la résolution des 460 `report_id` manquants | rétablirait la traçabilité de `evidence` |

### Et si la réponse était « pas de modèle » ?

Elle serait défendable si l'objectif était de **remplacer** le jugement du
technicien : 0,560 de F1 macro sur un corpus synthétique de 80 situations ne le
permet pas.

Elle ne l'est pas ici, parce que le besoin est de **trier une file** sous
supervision humaine permanente. Dans ce cadre, un F1 macro de 0,560 — contre
0,153 pour la baseline triviale — apporte un gain réel, et l'erreur reste
rattrapable par la revue humaine qui suit dans 91 % des cas.

---

**Décision datée** : 31/08/2026 — **adopter F2 sous les cinq conditions
ci-dessus**, avec réévaluation obligatoire à la première livraison de rapports
non synthétiques.
