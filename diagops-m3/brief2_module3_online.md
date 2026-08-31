# Brief 2 — Module 3 — Online

## Ce que ce jeu de données permet, et ce qu'il faut fabriquer pour la suite

**Modalité : distanciel — classe virtuelle et travail autonome**
**Compétences : C1 — niveau 2 amorcé, C2 — niveau 2 consolidé, C3 — niveau 2 consolidé**

## Situation

À la fin du brief 1, la pipeline DiagOps absorbe quatre sources, trace l'évolution
de ses règles et rend une décision de transmission. Cette décision porte sur la
**qualité** des données. Elle ne dit rien de leur **capacité**.

Or M4 va concevoir. Concevoir suppose que le jeu de données permette quelque
chose : que les situations à traiter y soient présentes, en nombre suffisant, sur
un périmètre défendable. Ce n'est pas acquis. Trente-six équipements sont
instrumentés sur les quatre cent vingt du parc. SITE-OUEST n'a aucun capteur. Les
événements les plus graves sont les plus rares. Une pipeline irréprochable peut
livrer un jeu de données incapable.

Trois familles de techniques répondent à ce type de manque : **augmenter** les
observations existantes, **générer** des observations nouvelles, et **protéger**
ce qui est publié lorsque les effectifs deviennent trop petits pour rester
anonymes. Aucune ne crée d'information : toutes déplacent un compromis.

Ce brief couvre le socle Atlas du module 3 sur les techniques de traitement de
données — génération de données synthétiques, confidentialité différentielle,
augmentation, segmentation, biais et risques résiduels — et s'en sert pour établir
ce qui est transmis à M4.

## Ce qui remplace la salle

Le travail se fait en autonomie. Deux artefacts vous donnent un retour sans
formateur, et ce sont eux qui font office de contradiction.

**Le détecteur de référence.** Il applique les contrôles de référence issus de M2
et M3 à un fichier de mesures que vous lui soumettez :

```bash
python tools/verify_synthetic.py --input <votre_fichier_de_mesures.csv>
```

Il retourne des **comptages par famille de règle**, jamais la liste des lignes
signalées. Vous pouvez le relancer autant de fois que nécessaire, à une
condition : chaque exécution est consignée dans votre journal avec l'hypothèse qui
l'a motivée et ce que le résultat vous a appris. Une série d'essais sans hypothèse
n'est pas une démarche.

**Le lot de contrôle** `data_pack/2026-S1/sensors_control/` :

- `control_batch.csv` : des mesures capteurs dont une partie a été fabriquée. La
  colonne de provenance n'y figure pas. Certaines fabrications sont grossières,
  d'autres ont été construites pour passer des contrôles semblables aux vôtres ;
- `control_sample.csv` : un échantillon dont la provenance est indiquée. Il sert à
  régler vos contrôles, pas à conclure ;
- `RELEASE_NOTES.md` et `checksums.sha256`.

Vos verdicts seront comparés à l'oracle du lot, qui n'est pas distribué.

## Données disponibles

- `2026-S1/reference_runs/m2_for_m3/processed/` : tables préparées de référence ;
- `2026-S1/sensors/sensor_readings.csv` : mesures capteurs ;
- `2026-S1/sensors_control/` : le lot de contrôle ;
- `SCHEMA.md`, `MANIFEST.yaml` et `DATA_CARD.md`.

Votre propre préparation issue du brief 1 est utilisable, à condition d'indiquer
laquelle vous employez.

Les bibliothèques du `requirements.lock` suffisent. `scikit-learn` fournit les
plus proches voisins et la segmentation, NumPy le tirage aléatoire. Le recours à
une bibliothèque spécialisée n'est pas nécessaire : les méthodes demandées
s'écrivent en quelques dizaines de lignes, et les écrire est le moyen de
comprendre ce qu'elles font.

## Organisation du travail

**Le travail est strictement individuel.** Les trois apprenants reçoivent le même
lot de contrôle et le même détecteur, et travaillent chacun dans leur
environnement, sans échange de résultats, de règles ou de code. Le lot étant
identique, une observation communiquée détruit l'exercice pour celui qui la
reçoit.

Le temps synchrone est organisé en points individuels et non en séance
collective. Il porte sur les notions et sur les difficultés de mise en œuvre ;
il ne porte jamais sur les résultats obtenus sur le lot.

## Travail attendu

Six parties, dans un ordre qui peut être adapté. Les parties 3 et 4 se nourrissent
l'une l'autre : il est normal de revenir sur votre générateur après avoir détecté,
et sur vos règles après avoir fabriqué.

### 1. Établir ce que le jeu de données ne permet pas

Avant toute technique, mesurez le manque.

- effectifs et fréquences par site, type d'équipement, criticité, type
  d'événement et sévérité ; visualisation de ces distributions ;
- rapport entre la classe la plus représentée et la moins représentée, sur au
  moins deux variables ;
- part des événements qui disposent effectivement de mesures dans leur fenêtre
  d'observation, par catégorie ;
- **segmentez** le parc en groupes homogènes à partir de variables choisies et
  justifiées. Indiquez comment vous avez fixé le nombre de groupes, décrivez ce
  que chacun contient, et dites quels groupes sont mal couverts par
  l'instrumentation. La segmentation doit montrer quelque chose que les comptages
  par site ne montraient pas ;
- concluez par **trois questions que ce jeu de données ne permet pas de traiter**,
  chacune motivée par un chiffre : population absente, effectifs insuffisants, ou
  grain inadapté.

Cette liste est le premier livrable réellement utile à M4. Elle vaut mieux qu'une
affirmation d'utilisabilité.

La segmentation est ici un instrument de description du parc. Ce n'est pas un
choix de modèle pour la solution DiagOps.

### 2. Augmenter des séries existantes

Appliquez au moins **deux techniques d'augmentation** distinctes à des séries de
`sensor_readings.csv` — ajout de bruit, mise à l'échelle, décalage temporel,
découpage en fenêtres, permutation de segments, déformation de l'axe temporel.

Pour chacune :

- décrivez la transformation et ses paramètres ;
- montrez une série avant et après ;
- indiquez **ce qu'elle préserve et ce qu'elle détruit** : ordre de grandeur,
  unité, régularité du pas, saisonnalité, corrélation avec les événements,
  plausibilité physique ;
- indiquez dans quel usage elle reste admissible et dans quel usage elle ne l'est
  pas.

Une technique qui produit une série physiquement impossible n'est pas à écarter du
rendu : elle est à documenter comme telle.

### 3. Générer des mesures pour un périmètre non couvert

Choisissez un périmètre non instrumenté — SITE-OUEST est le cas le plus net — et
produisez pour lui des mesures capteurs. Bornez-le : un site, un ou deux capteurs,
une période courte suffisent.

Produisez-les par **deux voies au moins** :

- **par tirage marginal** : reproduire indépendamment la distribution de chaque
  colonne ;
- **par interpolation entre voisins**, selon le principe de SMOTE : choisir une
  observation, l'un de ses plus proches voisins, tirer un point entre les deux.
  L'implémentation à la main avec `NearestNeighbors` est attendue, ainsi que le
  traitement explicite des colonnes catégorielles.

Dans les deux cas :

- respectez le contrat de `SCHEMA.md` : colonnes, types, domaine des capteurs,
  unités, clé logique ;
- documentez ce que vous reproduisez et ce que vous ne reproduisez pas ;
- votre générateur doit être **rejouable à graine fixe**.

Comparez ensuite vos productions aux données réelles :

- distributions marginales : moyennes, médianes et dispersions sont-elles
  conservées ?
- **relations entre colonnes et entre sources** : la corrélation entre deux
  variables liées survit-elle au tirage marginal ? Les mesures fabriquées
  réagissent-elles aux événements de `events.csv` ?
- contraintes métier : combien de lignes violent une règle de cohérence M2 ou M3 ?

C'est le point central du brief. Une génération qui respecte chaque colonne prise
isolément peut détruire toutes les relations entre elles, et cette perte ne se
voit sur aucun histogramme.

### 4. Se confronter

**Dans un sens.** Soumettez votre production au détecteur de référence et
interprétez son verdict.

- s'il signale beaucoup : identifiez la famille de règle en cause, corrigez le
  générateur, et notez ce que la correction vous apprend sur ce que vos propres
  contrôles regardaient sans le savoir ;
- s'il ne signale rien : **ce n'est pas une réussite en soi**. Déterminez si votre
  générateur est fidèle ou si les contrôles de référence sont aveugles sur ce
  point, et apportez un élément à l'appui de votre réponse.

Conservez au moins deux états successifs de votre générateur avec le verdict
associé. La progression est une preuve ; l'état final seul n'en est pas une.

**Dans l'autre.** Calibrez vos règles sur `control_sample.csv`, puis appliquez-les
à `control_batch.csv`. Produisez pour **chaque ligne** un verdict — `réelle`,
`fabriquée` ou `indécidable` — accompagné de la règle qui l'a motivé. Comptez vos
verdicts et présentez-les par règle.

Quand vos contrôles ligne à ligne et série par série ne suffisent plus, **remontez
au multi-source** : une mesure peut être irréprochable en elle-même et incohérente
avec `events.csv` ou `maintenance_history.csv`. Le rapprochement temporel construit
au brief 1 est un instrument de détection, pas seulement un livrable.

Concluez enfin sur vos propres règles : lesquelles ont servi, lesquelles n'ont
rien attrapé, lesquelles ont accusé à tort une mesure réelle, et qu'en déduisez-vous
sur la préparation rendue au brief 1. Votre registre est mis à jour en
conséquence, avec les statuts et justifications déjà en usage.

Un `indécidable` assumé et motivé vaut mieux qu'un verdict tranché au hasard ; un
`indécidable` généralisé n'est pas une position.

### 5. Protéger une publication agrégée

Certains comptages sont si peu nombreux qu'ils désignent une situation unique : un
site avec deux équipements, une intervention par an, un technicien.

- identifiez au moins un agrégat de DiagOps trop peu fourni pour être publié tel
  quel ;
- appliquez-lui le mécanisme de Laplace : sensibilité, budget `ε`, bruit tiré,
  résultat publié ;
- faites varier `ε` sur au moins trois valeurs et montrez l'effet sur l'utilité ;
- concluez : à partir de quel `ε` le chiffre publié cesse-t-il d'être exploitable,
  et à partir de quel `ε` cesse-t-il de protéger ?

Il n'est pas demandé de garantie formelle ni de comptabilité de budget sur une
suite de requêtes.

### 6. Décider ce qui est transmis à M4

**Provenance.** Toute ligne du jeu transmis porte désormais une provenance
explicite — `réelle`, `synthétique` ou `augmentée` — avec l'identifiant du procédé
qui l'a produite. Ce n'est pas une commodité : sans elle, tout travail conduit en
M4 sur ces données est indéfendable.

**Biais.** Nommez au moins **trois biais** présents dans le jeu DiagOps, en les
rattachant à des comptages : couverture, sélection, mesure, représentation, biais
historique de l'activité de maintenance. Pour chacun, indiquez une atténuation
possible, son coût, et ce qui **subsiste** après elle. Dites enfin quels biais
l'augmentation et la génération corrigent, et lesquels elles amplifient : une
classe minoritaire dupliquée reste minoritaire dans le réel.

**Décision.** Que transmettez-vous : rien de fabriqué, une partie sous conditions,
ou l'ensemble avec réserves ? Justifiez par les résultats des parties 1 à 5, pas
par une intention. Indiquez ce que la présence de données fabriquées interdit de
conclure, et à quelles conditions elles pourraient être retirées.

**Mise à jour.** La description du jeu de données et le cycle de vie : une donnée
fabriquée a une date, un procédé, une raison et une durée de validité. Le
périmètre de validité annoncé au brief 1 est réécrit s'il n'est plus exact.

## Questions auxquelles votre rendu doit répondre

1. Quels rapports de déséquilibre observez-vous, et sur quelles variables ?
2. Quelles variables avez-vous retenues pour segmenter, comment avez-vous fixé le
   nombre de groupes, et quels groupes sont mal couverts ?
3. Quelles sont les trois questions que ce jeu de données ne permet pas de
   traiter, et sur quels chiffres reposent-elles ?
4. Quelles techniques d'augmentation avez-vous appliquées, et pour chacune, que
   préserve-t-elle et que détruit-elle ?
5. Quel périmètre avez-vous choisi de générer, et pourquoi celui-là ?
6. Quelles distributions marginales chaque méthode conserve-t-elle ?
7. Quelle relation entre colonnes ou entre sources le tirage marginal perd-il, et
   comment le montrez-vous ?
8. Combien de lignes générées violent une règle de cohérence M2 ou M3 ?
9. Comment traitez-vous les colonnes catégorielles dans l'interpolation entre
   voisins ?
10. Qu'a signalé le détecteur de référence, à quelle étape, et qu'avez-vous changé
    en conséquence ?
11. Lorsqu'il ne signale plus rien, comment savez-vous si votre générateur est
    fidèle ou si le détecteur est aveugle ?
12. Combien de lignes du lot avez-vous classées `réelle`, `fabriquée` et
    `indécidable`, et par quelles règles ?
13. Quelles fabrications n'étaient détectables qu'en confrontant plusieurs
    sources, et comment les avez-vous prises ?
14. Quelles règles du brief 1 se sont révélées inopérantes, et lesquelles ont
    accusé à tort une mesure réelle ?
15. Quel agrégat avez-vous jugé non publiable, quelle sensibilité avez-vous
    retenue, et quel effet observez-vous quand `ε` diminue ?
16. Quels biais avez-vous identifiés, que reste-t-il après atténuation, et
    lesquels vos techniques amplifient-elles ?
17. Que transmettez-vous à M4, avec quelle provenance, et qu'est-ce que cette
    composition interdit de conclure ?

## Exigences minimales

- les distributions et la couverture mesurées avant toute transformation ;
- une segmentation exécutée, avec son critère de choix ;
- deux techniques d'augmentation appliquées et comparées ;
- deux méthodes de génération, dont une par interpolation entre voisins écrite à
  la main ;
- une comparaison réel / fabriqué portant sur les marginales **et** sur au moins
  une relation entre colonnes ou entre sources ;
- deux états successifs du générateur avec le verdict du détecteur ;
- un verdict par ligne sur `control_batch.csv`, rattaché à une règle ;
- un mécanisme de Laplace appliqué avec au moins trois valeurs de `ε` ;
- trois biais nommés, rattachés à des comptages, avec atténuation et risque
  résiduel ;
- le jeu transmis à M4, chaque ligne portant sa provenance.

## Livrables attendus

- un notebook exécutable de bout en bout, conclusion intégrée ;
- son export HTML ;
- le code des générateurs, des augmentations et des règles de détection, rejouable
  à graine fixe ;
- le tableau de comparaison réel / fabriqué ;
- `verdicts_control_batch.csv` : une ligne par mesure, verdict et règle motivante ;
- le registre de règles mis à jour ;
- le jeu transmis à M4 avec sa colonne de provenance et le procédé associé ;
- une note de décision : capacité du jeu, biais, risques résiduels, conditions ;
- la description du jeu de données et le cycle de vie mis à jour ;
- le journal de bord, incluant les exécutions du détecteur et leurs hypothèses.

Les fichiers de données générés ne sont pas des livrables : ils doivent pouvoir
être reproduits à partir de votre code.

## Critères de réussite

- l'incapacité du jeu de données est chiffrée avant toute fabrication ;
- la segmentation repose sur des variables justifiées et révèle autre chose que
  les comptages par site ;
- chaque augmentation est décrite par ce qu'elle préserve **et** ce qu'elle
  détruit ;
- l'interpolation entre voisins est écrite, le traitement des catégories est
  explicite ;
- la comparaison réel / fabriqué porte sur les relations, pas seulement sur les
  marginales ;
- la confrontation au détecteur a produit au moins une correction argumentée ;
- l'absence de signalement est interprétée, pas revendiquée ;
- chaque verdict de détection est rattaché à une règle nommée ;
- au moins une détection repose sur une incohérence entre sources ;
- les règles du brief 1 sont réévaluées, y compris celles qui n'ont rien attrapé ;
- le compromis utilité / protection est observé sur des valeurs, pas affirmé ;
- les biais sont rattachés à des comptages et le risque résiduel est énoncé ;
- toute ligne transmise porte sa provenance et son procédé ;
- la décision distingue ce qui est corrigé de ce qui est masqué ;
- l'ensemble est reproductible à graine fixe.

## Critères bloquants

- données fabriquées transmises sans provenance ;
- générateur ou résultats non reproductibles ;
- technique appliquée sans description de ce qu'elle détruit ;
- comparaison réel / fabriqué limitée aux moyennes ;
- interpolation entre voisins utilisée comme boîte noire, sans traitement des
  catégories ;
- verdicts de détection sans règle motivante ;
- lot classé majoritairement `indécidable` sans démarche ;
- exécutions du détecteur non consignées, ou consignées sans hypothèse ;
- absence de signalement présentée comme une preuve de fidélité ;
- règle du brief 1 conservée alors que les résultats l'ont invalidée ;
- `ε` fixé à une seule valeur et présenté comme un choix ;
- biais cités sans comptage, ou atténuation présentée sans risque résiduel ;
- décision de transmission sans comptage à l'appui ;
- échange de code, de règles, de verdicts ou d'observations avec un autre
  apprenant.

## Hors périmètre

Ce brief prépare M4 sans l'entamer. Il n'est pas demandé de :

- définir un besoin métier ni analyser un nouveau cas d'usage — ce travail ouvre
  M4 ;
- constituer un jeu d'évaluation : pas de partition, pas de protocole, pas de
  métrique cible ;
- choisir, entraîner ou comparer un modèle ;
- produire une courbe ROC ou toute évaluation de performance de modèle ;
- utiliser un générateur à base d'apprentissage ;
- traiter la génération d'images ou de texte ;
- fournir une garantie formelle de confidentialité.

Les comptages de détection que vous produisez constituent une **base de
comparaison par règles**. M4 s'en servira comme point de départ, et c'est à ce
moment-là que la mesure de performance et ses indicateurs seront introduits.
