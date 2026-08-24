# Brief 1 — Étendre la pipeline DiagOps aux mesures capteurs

**Modalité : présentiel**  
**Charge apprenant : 14 h — 7 h encadrées + 7 h de prolongement autonome**  
**Compétences : C1 — niveau 1 consolidé, C2 — niveau 2, C3 — niveau 2**

## Contexte du projet

Les trois tables ouvertes en M2 décrivent un parc, des événements et des
interventions. Elles ne disent rien de ce qui se passe entre deux interventions.
L'exploitation ouvre aujourd'hui l'export de sa supervision : `sensor_readings.csv`,
une source temporelle qui mesure vibration, température, pression, courant et
vitesse de rotation sur une partie du parc.

Cette source ne ressemble pas aux précédentes. Elle est volumineuse, elle n'a pas
d'identifiant de ligne, son horodatage n'est pas homogène, ses unités ne sont pas
garanties et elle ne couvre ni tous les équipements ni toute la période. Les
règles écrites en M2 ne suffisent plus, mais elles ne doivent pas disparaître pour
autant.

Votre responsable vous confie cette mission : **intégrer la source capteurs à la
pipeline DiagOps, la relier aux événements existants, faire évoluer les règles
sans casser l'acquis de M2, et décider ce qui peut être transmis à M4**.

## Objectif principal

Faire passer la préparation des données d'un contrôle table par table à une
pipeline multi-source dont l'évolution est tracée. Le travail doit rendre
visible ce qui a changé depuis M2, ce qui a été ajouté pour le temporel, et ce
qui reste incertain.

Le développement est un moyen de rendre le travail vérifiable. La mission ne
consiste pas à reproduire une architecture logicielle imposée.

## Point de départ commun

Le dossier `data_pack/` à la racine du dépôt contient :

- `2026-S1/sensors/sensor_readings.csv` : mesures capteurs, ouvertes en M3 ;
- `2026-S1/equipment/equipment.csv`, `2026-S1/events/events.csv` et
  `2026-S1/maintenance/maintenance_history.csv` : tables reçues en M2 ;
- `SCHEMA.md`, `MANIFEST.yaml` et `DATA_CARD.md` : description des données.

Le dossier `data_pack/2026-S1/reference_runs/m2_for_m3/` fournit un état préparé
de référence issu de M2 : tables préparées, quarantaine, registre des règles,
rapport de validation et décision. Il garantit que le travail peut commencer même
si votre préparation M2 n'est pas terminée.

Vous pouvez repartir de votre propre préparation M2 ou de cette référence. Dans
les deux cas, indiquez clairement laquelle vous utilisez et pourquoi.

Les fichiers reçus dans `data_pack/` restent inchangés. Toutes vos sorties sont
écrites dans votre espace de travail.

## Organisation du travail

Les cinq apprenants travaillent sur le même brief et les mêmes ressources,
chacun dans son propre environnement. Les échanges et revues en séance sont
possibles, sans constitution de groupes ni partage de rôles.

## Axes d'investigation

Les axes suivants structurent la mission. Ils ne constituent pas un pas à pas et
peuvent être traités dans l'ordre qui convient à votre démarche.

### 1. Cadrer la nouvelle source avant de la traiter

- expliquer ce que représente une ligne et quelle clé identifie une mesure ;
- établir la liste des séries présentes : équipement, capteur, unité ;
- mesurer la période réellement couverte et la comparer à la période annoncée ;
- mesurer le pas d'échantillonnage observé, sa régularité et ses écarts ;
- décrire la volumétrie et son effet sur votre manière de travailler ;
- vérifier l'existence, la disponibilité et les conditions d'accès de la source :
  qui la produit, à quelle fréquence elle est livrée, sous quel format, et ce qui
  se passe si une livraison manque.

Le fichier reçu ne déclare aucune clé primaire. La clé logique
`equipment_id + timestamp + sensor_name` est une hypothèse à vérifier, pas une
propriété acquise.

Une source qui ne couvre qu'une partie du parc laisse un besoin ouvert. Pour les
équipements qu'elle n'atteint pas, examinez ce qui reste disponible — une autre
table du data pack, un relevé porté par les interventions, ou rien — et indiquez
la solution de remplacement que vous retenez, ou pourquoi vous n'en retenez
aucune. Une absence assumée et documentée est une réponse recevable ; une
absence non vue n'en est pas une.

### 2. Établir un diagnostic propre au temporel

Les contrôles écrits en M2 portaient sur des lignes indépendantes. Une série
temporelle demande des contrôles supplémentaires. L'audit doit couvrir au
minimum :

- l'unicité de la clé logique, et la distinction entre doublon strict et
  doublon de clé porteur de deux valeurs différentes ;
- l'homogénéité du format d'horodatage et la présence ou l'absence de fuseau ;
- l'alignement des séries sur une grille temporelle commune ;
- la continuité de l'échantillonnage et la localisation des interruptions ;
- la cohérence entre `sensor_name`, `unit` et l'ordre de grandeur des valeurs ;
- les plages physiques plausibles et les valeurs sentinelles ;
- les comportements de capteur : valeur figée, dérive lente, saut brutal ;
- les mesures rattachées à un équipement inconnu ou à une période inattendue.

Toutes les bornes ne sont pas données. Toute règle ajoutée doit être nommée,
justifiée et rattachée à une observation.

### 3. Distinguer une erreur d'une mesure réelle

Une valeur inhabituelle n'est pas nécessairement fausse. Une élévation de
vibration peut annoncer une dégradation ; une dérive de température peut venir
du capteur comme du procédé.

Pour au moins trois observations atypiques de nature différente, expliquez ce
qui vous fait conclure à une erreur, à une mesure réelle ou à un cas indécidable,
et ce que vous décidez dans chaque cas. Le rapprochement avec `events.csv` et
`maintenance_history.csv` fait partie des éléments disponibles.

Une suppression silencieuse d'observation atypique est un défaut, pas une
préparation.

### 4. Faire évoluer les règles sans casser l'acquis

La pipeline doit maintenant porter deux familles de règles : celles héritées de
M2 et celles introduites pour le temporel.

- reprenez le registre des règles M2 et donnez à chacune un statut explicite :
  conservée, modifiée, étendue ou abandonnée ;
- justifiez chaque modification et chaque abandon ;
- ajoutez les règles capteurs avec un identifiant stable ;
- vérifiez que les résultats obtenus sur les trois tables M2 n'ont pas changé
  sans raison : une non-régression doit être démontrée, pas affirmée ;
- unifiez la quarantaine : les rejets capteurs et les rejets M2 partagent le
  même format et le même vocabulaire de décision.

Le format minimal de quarantaine reste celui de M2 :

```text
source_file
row_identifier
rule_id
column
observed_value
reason
decision
```

Pour une mesure, `row_identifier` doit permettre de retrouver la ligne d'origine
alors qu'aucun identifiant n'est fourni.

### 5. Relier les mesures aux événements

Une mesure et un événement ne partagent pas de clé commune : seul le couple
équipement et temps les rapproche.

- choisissez et documentez une fenêtre d'observation autour de chaque
  événement : durée avant, durée après, et justification ;
- construisez le rapprochement et contrôlez sa cardinalité : combien de mesures
  par événement, combien d'événements sans aucune mesure, combien de mesures
  hors de toute fenêtre ;
- vérifiez que le rapprochement ne duplique pas les mesures sans le dire ;
- produisez au moins un jeu d'agrégats à un grain défini, par exemple par
  équipement, capteur et fenêtre, avec des indicateurs simples : nombre de
  mesures, complétude, minimum, maximum, moyenne, écart-type ;
- indiquez ce que ce grain fait perdre.

Ce rapprochement prépare le travail de M4. Il n'est pas demandé de construire un
modèle ni de démontrer une relation de cause à effet.

### 6. Documenter le flux et le cycle de vie de la donnée

Une pipeline qui fonctionne mais que personne d'autre ne peut décrire n'est pas
transmissible. L'ajout d'une source rend deux documents nécessaires, et les rend
tous les deux périssables : ils doivent être mis à jour, pas écrits une fois.

**Le flux de traitement**, de la source reçue jusqu'à la sortie exploitable :
les fichiers d'entrée, les étapes traversées, ce qui est écrit à chaque étape,
les points où une ligne peut être écartée, et la commande qui rejoue l'ensemble.
Un schéma commenté suffit. Ce qui compte est qu'une autre personne puisse suivre
une ligne d'un bout à l'autre et retrouver où elle a été transformée ou perdue.

**Le cycle de vie du jeu de données** : d'où viennent les données, qui les
produit, à quelle fréquence elles arrivent, combien de temps et sous quelle forme
elles sont conservées, qui y accède, ce qui se passe à l'arrivée d'une nouvelle
période, et à partir de quand elles cessent d'être utilisables. La règle de
conservation formulée à l'axe 7 en fait partie.

Mettez enfin à jour la description du jeu de données : l'ajout d'une source
change ce qu'il contient, ce qu'il ne contient pas, et ce qu'il permet de
conclure.

Ces documents sont destinés à d'autres que vous — équipe technique, métier, ou
personne chargée de la conformité. Indiquez à qui vous les adresseriez et ce que
chacun doit pouvoir en tirer.

### 7. Examiner les risques et la couverture

Le parc instrumenté n'est pas le parc complet. Mesurez cette différence :
combien d'équipements sont instrumentés, quels sites, quels types, quelles
criticités sont absents ou peu représentés, et quelle part des événements peut
réellement être rapprochée de mesures.

Examinez ensuite les risques que cette source introduit :

- une mesure horodatée à la minute décrit aussi l'activité humaine autour de
  l'équipement : postes, présence, rythme de travail. Ce n'est pas une donnée
  identifiante en soi, mais le croisement avec un site, un horaire et un bon de
  travail peut le devenir. Décidez d'une position et justifiez-la ;
- le volume conservé est un choix : conserver toutes les mesures brutes,
  agrégées ou les deux n'a pas le même coût ni les mêmes conséquences.
  Formulez une règle de conservation proportionnée au besoin ;
- une conclusion tirée du parc instrumenté ne vaut pas pour le parc entier.
  Indiquez explicitement le périmètre de validité de vos constats.

Il n'est pas demandé de produire une expertise juridique du RGPD ni une analyse
d'impact complète.

### 8. Rendre une décision

À l'issue du travail, classez l'état multi-source dans l'un des états suivants :

- **utilisable** ;
- **utilisable sous conditions** ;
- **non utilisable en l'état**.

Votre décision doit distinguer ce qui a été vérifié, ce qui a été transformé, ce
qui reste incertain, les conditions à respecter avant M4 et le coût de rejeu de
votre pipeline.

## Questions auxquelles votre diagnostic doit répondre

1. Que représente une ligne de `sensor_readings.csv` et quelle clé identifie une
   mesure ?
2. Quelle période et quel pas d'échantillonnage la source couvre-t-elle
   réellement, par rapport à ce qui est annoncé ?
3. Quelle part du parc est instrumentée, et quels sites, types ou criticités
   sont absents ou sous-représentés ?
4. L'existence, la disponibilité et l'accès de cette source sont-ils vérifiés, et
   que proposez-vous pour les équipements qu'elle ne couvre pas ?
5. Quels défauts propres à une série temporelle avez-vous détectés, et comment
   les avez-vous quantifiés ?
6. Quelles variations atypiques sont des erreurs, lesquelles sont des mesures
   réelles, et sur quoi vous appuyez-vous pour trancher ?
7. Quelles règles M2 avez-vous conservées, modifiées, étendues ou abandonnées,
   et comment démontrez-vous l'absence de régression ?
8. Comment avez-vous relié les mesures aux événements : quelle fenêtre, quelle
   cardinalité, combien de lignes non appariées ?
9. À quel grain avez-vous agrégé les mesures, et que perd-on à ce grain ?
10. Comment décrivez-vous le flux de traitement et le cycle de vie du jeu de
    données après l'ajout de cette source, et à qui adressez-vous ces documents ?
11. Quels risques cette source introduit-elle pour les personnes et pour la
    validité des conclusions, et quelles mesures proportionnées avez-vous prises ?
12. L'ensemble multi-source peut-il être transmis à M4, sous quelles conditions,
    et à quel coût de rejeu ?

## Liberté technique

Vous choisissez la forme la plus adaptée pour conduire et rendre votre travail,
par exemple :

- un notebook complété par des fonctions Python ;
- des scripts organisés en pipeline ;
- une combinaison notebook, scripts et tests ;
- Pandas, Polars, Pandera, Pydantic ou des contrôles Python explicites ;
- Pytest ou des cas de vérification documentés équivalents.

Le starter fournit un point de départ possible : chargement des quatre sources,
utilitaires temporels, registre de règles et quarantaine unifiée. Son utilisation
n'est pas obligatoire. Quelle que soit la solution retenue, une autre personne
doit pouvoir comprendre les règles, rejouer les traitements et retrouver les
résultats annoncés.

La volumétrie reste modeste, mais elle approche trente fois celle de la plus
grande table de M2. Surveillez le temps d'exécution de votre pipeline et signalez
ce qui deviendrait impraticable sur un parc entièrement instrumenté ou sur
plusieurs périodes.

## Livrables attendus

- un registre de règles versionné indiquant, pour chaque règle, son identifiant,
  sa source (M2 ou M3), son statut et sa justification ;
- la pipeline multi-source sous une forme rejouable ;
- la table de mesures préparée ;
- au moins une table d'agrégats et une table de rapprochement mesures ↔
  événements, à un grain documenté ;
- une quarantaine unifiée couvrant les quatre sources ;
- des cas de vérification valides et invalides, dont au moins un cas temporel et
  une non-régression sur les tables M2 ;
- une documentation du flux de traitement et du cycle de vie du jeu de données,
  accompagnée de la description du jeu mise à jour ;
- un diagnostic répondant aux douze questions et portant la décision finale ;
- une note de couverture et de risques ;
- l'entrée M3 du journal de bord.

Une organisation possible, sans caractère obligatoire :

```text
m3/
├── README.md
├── notebooks/
│   └── notebook_multisource_m3.ipynb
├── src/
├── tests/
├── output/
│   ├── processed/
│   ├── aggregates/
│   ├── alignment/
│   └── quarantine.csv
├── docs/
│   ├── registre_regles.md
│   ├── diagnostic_multisource.md
│   ├── flux_et_cycle_de_vie.md
│   ├── couverture_et_risques.md
│   └── decision_transmission_m4.md
└── journal_bord.md
```

## Critères de réussite

- la nouvelle source est décrite avant d'être traitée : grain, clé, période,
  pas, séries et volumétrie ;
- l'existence, la disponibilité et l'accès de la source sont vérifiés, et
  l'absence de couverture donne lieu à une solution de remplacement examinée ;
- la clé logique est reconstruite et son unicité contrôlée ;
- les défauts temporels sont recherchés et quantifiés, pas seulement cités ;
- erreurs et mesures réelles sont distinguées avec des arguments ;
- le registre de règles rend visible ce qui vient de M2 et ce qui est nouveau ;
- la non-régression sur les tables M2 est démontrée ;
- la quarantaine est unifiée et chaque rejet reste compréhensible ;
- le rapprochement temporel est explicite : fenêtre, sens, cardinalité, lignes
  non appariées ;
- le flux de traitement et le cycle de vie du jeu de données sont documentés,
  tenus à jour et adressés à un destinataire identifié ;
- la couverture instrumentale est chiffrée et son effet sur les conclusions est
  énoncé ;
- les risques liés aux personnes et à la conservation sont traités de manière
  proportionnée ;
- la décision finale s'appuie sur les résultats obtenus et expose ses limites.

## Critères bloquants

- modification des données reçues ;
- suppression ou correction silencieuse, en particulier d'une valeur atypique ;
- doublon de clé résolu sans arbitrage tracé ;
- horodatages normalisés sans indiquer l'hypothèse de fuseau retenue ;
- règle M2 modifiée ou abandonnée sans trace ni justification ;
- rapprochement temporel présenté sans fenêtre ni contrôle de cardinalité ;
- conclusion tirée du parc instrumenté et présentée comme valable pour tout le
  parc ;
- traitements impossibles à rejouer ;
- décision finale sans résultat vérifiable.

## Hors périmètre

Il n'est pas demandé de :

- entraîner ou évaluer un modèle de détection d'anomalie ;
- démontrer statistiquement qu'une mesure cause une panne ;
- mettre en place une base de données pour le brief présentiel ; ce travail est
  couvert par le brief online ;
- construire une plateforme de données complète ni une chaîne CI/CD ;
- maîtriser DVC ou un ordonnanceur ;
- produire une expertise juridique exhaustive ;
- retrouver exactement toutes les anomalies injectées par le formateur.
