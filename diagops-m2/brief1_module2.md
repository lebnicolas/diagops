# Brief 1 — Auditer et préparer les données DiagOps

**Modalité : présentiel**  
**Charge apprenant : 14 h — 7 h encadrées + 7 h de prolongement autonome**  
**Compétences : C1, C2 et C3 — niveau 1**

## Contexte du projet

DiagOps doit intégrer trois nouvelles sources décrivant le parc industriel, les
événements et les interventions de maintenance. Avant d'ouvrir les données
capteurs en M3, l'équipe doit comprendre ce que contiennent ces fichiers,
vérifier leur qualité et décider des traitements nécessaires.

Les données peuvent comporter des identifiants dupliqués, des références
inexistantes, des dates incohérentes, des valeurs impossibles ou des
informations relatives à des personnes dans les notes. Certaines catégories
peuvent aussi être trop peu représentées pour permettre une analyse fiable.

Votre responsable vous confie cette mission : **auditer les données DiagOps,
préparer une version exploitable et rendre une décision argumentée avant leur
transmission à M3**.

## Objectif principal

Produire un diagnostic compréhensible des données, appliquer les traitements
justifiés et démontrer que les contrôles et transformations retenus peuvent
être rejoués.

Le développement est un moyen de rendre le travail vérifiable. La mission ne
consiste pas à reproduire une architecture logicielle imposée.

## Point de départ commun

Le dossier `data_pack/` à la racine du dépôt contient :

- `2026-S1/equipment/equipment.csv` : inventaire des équipements ;
- `2026-S1/events/events.csv` : événements associés aux équipements ;
- `2026-S1/maintenance/maintenance_history.csv` : opérations de maintenance ;
- `SCHEMA.md`, `MANIFEST.yaml` et `DATA_CARD.md` : description des données.

Le dossier `data_pack/2026-S1/reference_runs/m1_for_m2/` fournit un état de
référence issu de M1 : prédictions, métriques et matrice d'erreurs. Il garantit
que le travail peut commencer même si toutes vos productions antérieures ne
sont pas terminées. Vous pouvez comparer cette référence à vos résultats M1
lorsqu'ils sont disponibles.

Les données capteurs restent réservées à M3.

## Organisation du travail

Les cinq apprenants travaillent sur le même brief et les mêmes ressources,
chacun dans son propre environnement. Les échanges et revues en séance sont
possibles, sans constitution de groupes ni partage de rôles.

## Axes d'investigation

Les axes suivants structurent la mission. Ils ne constituent pas un pas à pas
et peuvent être traités dans l'ordre qui convient à votre démarche.

### 1. Comprendre les données disponibles

- expliquer ce que représente une ligne dans chaque fichier ;
- identifier les colonnes importantes, les clés et les relations ;
- vérifier la présence et la lisibilité des sources ;
- préciser les données utiles au cas DiagOps et leurs limites connues.

Les relations principales à examiner sont :

```text
events.equipment_id
    → equipment.equipment_id

maintenance_history.equipment_id
    → equipment.equipment_id

maintenance_history.event_id
    → events.event_id
```

### 2. Établir un diagnostic de qualité

L'audit doit couvrir au minimum :

- les colonnes obligatoires et les types attendus ;
- les identifiants manquants ou dupliqués ;
- les références absentes entre les fichiers ;
- les catégories non prévues par le schéma ;
- les dates incohérentes ;
- les durées, coûts, puissances ou quantités impossibles ;
- les valeurs manquantes et les anomalies qui nécessitent un avis métier.

Toutes les bornes ne sont pas nécessairement données. Toute règle ajoutée doit
être nommée et justifiée.

### 3. Examiner les risques et la couverture

Recherchez dans les champs de notes, notamment `work_order_note`, les noms,
adresses électroniques ou numéros de téléphone éventuels. Distinguez ces
informations des identifiants techniques nécessaires au fonctionnement de
DiagOps, puis justifiez leur conservation, leur masquage ou leur mise à
l'écart.

Examinez également les effectifs par site, type d'équipement, criticité et
sévérité. La matrice d'erreurs M1 permet de rechercher si certaines erreurs
historiques semblent plus fréquentes dans certaines catégories. Des comptages
et taux simples suffisent ; un effectif trop faible doit être signalé et ne
permet pas une conclusion catégorique.

Il n'est pas demandé de produire une expertise juridique du RGPD ni une étude
statistique avancée des biais.

### 4. Préparer une version exploitable

À partir du diagnostic :

- formalisez les contrôles retenus ;
- appliquez uniquement les corrections que vous pouvez justifier ;
- isolez les données qui nécessitent un examen dans une quarantaine ;
- conservez les fichiers reçus sans modification ;
- gardez une trace de la règle, de la valeur observée et de la décision pour
  chaque anomalie ;
- rendez les contrôles et transformations rejouables.

La quarantaine doit permettre de retrouver au minimum :

```text
source_file
row_identifier
rule_id
column
observed_value
reason
decision
```

### 5. Rendre une décision

À l'issue de l'audit, classez les données dans l'un des états suivants :

- **utilisables** ;
- **utilisables sous conditions** ;
- **non utilisables en l'état**.

Votre décision doit distinguer ce qui a été vérifié, ce qui a été transformé,
ce qui reste incertain et les conditions à respecter avant M3.

M2 statue sur l'état des données, pas sur la promotion du modèle M1. Le jeu de
validation M1 est un historique déjà consulté ; il ne redevient pas un test
inédit.

## Questions auxquelles votre diagnostic doit répondre

1. Que représente chaque fichier et comment les trois sources sont-elles
   reliées ?
2. Les données nécessaires au cas DiagOps sont-elles présentes et lisibles ?
3. Quels problèmes d'identifiants, de doublons ou de relations avez-vous
   détectés ?
4. Quelles règles métier ne sont pas respectées ?
5. Quelles anomalies peuvent être corrigées de manière certaine ?
6. Quelles anomalies doivent être mises à l'écart ou examinées par un expert
   métier ?
7. Les notes contiennent-elles des informations relatives à des personnes et
   quelle décision prenez-vous à leur sujet ?
8. Certaines catégories de sites, d'équipements, de criticité ou de sévérité
   sont-elles peu représentées ?
9. Les erreurs historiques de M1 semblent-elles plus fréquentes dans certaines
   catégories, et quelles sont les limites de ce constat ?
10. Les données préparées peuvent-elles être transmises à M3, et sous quelles
    conditions ?

## Liberté technique

Vous choisissez la forme la plus adaptée pour conduire et rendre votre
travail, par exemple :

- un notebook complété par des fonctions Python ;
- des scripts organisés en pipeline ;
- une combinaison notebook, scripts et tests ;
- Pandera, Pydantic ou des contrôles Python explicites ;
- Pytest ou des cas de vérification documentés équivalents.

Le starter fournit une commande et une structure de pipeline comme point de
départ possible. Leur utilisation n'est pas obligatoire. Quelle que soit la
solution retenue, une autre personne doit pouvoir comprendre les règles,
rejouer les traitements et retrouver les résultats annoncés.

## Livrables attendus

- un support d'audit présentant les observations et les résultats utiles
  (notebook, rapport ou combinaison des deux) ;
- les contrôles et transformations sous une forme rejouable ;
- des cas de vérification valides et invalides ;
- les trois tables préparées ;
- une quarantaine expliquant les anomalies écartées ou laissées à examiner ;
- un diagnostic répondant aux dix questions et portant la décision finale ;
- l'entrée M2 du journal de bord.

Une organisation possible, sans caractère obligatoire :

```text
m2/
├── README.md
├── notebook_audit_m2.ipynb
├── src/
├── tests/
├── data/
│   ├── processed/
│   └── quarantine.csv
├── docs/
│   ├── diagnostic_donnees.md
│   └── decision_preparation.md
└── journal_bord.md
```

## Critères de réussite

- le rôle des sources, des clés et des relations est expliqué ;
- les principaux problèmes de qualité sont recherchés et quantifiés ;
- les fichiers reçus restent inchangés ;
- les corrections sont justifiées et les exclusions sont traçables ;
- les contrôles et transformations peuvent être rejoués ;
- des cas valides et invalides vérifient les règles importantes ;
- les informations relatives à des personnes et les défauts de couverture sont
  examinés avec un niveau d'analyse adapté ;
- le diagnostic répond aux dix questions ;
- la décision finale s'appuie sur les résultats obtenus et expose ses limites.

## Critères bloquants

- modification des données reçues ;
- suppression ou correction silencieuse ;
- traitements impossibles à rejouer ;
- rupture de relation non signalée ;
- quarantaine sans motif compréhensible ;
- conclusion sur M1 présentée comme une causalité démontrée ;
- décision finale sans résultat vérifiable.

## Hors périmètre

Il n'est pas demandé de :

- réentraîner le modèle M1 ou améliorer ses scores ;
- démontrer statistiquement qu'une caractéristique cause une erreur du modèle ;
- construire une plateforme de données complète ;
- maîtriser DVC ou mettre en place une chaîne CI/CD ;
- produire une expertise juridique exhaustive ;
- retrouver exactement toutes les anomalies injectées par le formateur.
