# Pour aller plus loin — Industrialiser la qualification des données DiagOps

**Complément facultatif au module M2**

**Charge apprenant : 20 h — qualification 14 h + GitHub Actions 6 h**
**Compétences approfondies : C1, C2 et C3**

## Situation professionnelle

L'audit réalisé en M2 a permis de comprendre et de préparer les premières
données DiagOps. Une nouvelle livraison est maintenant disponible. L'équipe ne
souhaite pas reprendre manuellement l'ensemble de l'audit à chaque arrivée de
fichiers : elle veut réutiliser ses contrôles, comparer les versions et repérer
rapidement une régression de qualité.

Votre responsable vous demande de **qualifier cette livraison candidate et de
faire évoluer votre travail M2 en un dispositif réutilisable pour les
livraisons suivantes**. Le dispositif devra ensuite être exécuté dans votre
dépôt GitHub privé afin que les contrôles ne dépendent plus de votre poste de
travail.

Ce complément prolonge M2. Il n'ouvre pas les données capteurs et ne constitue
pas un prérequis pour M3.

## Point de départ

Vous disposez :

- des données M2 publiées dans `data_pack/2026-S1/` ;
- de votre audit, de vos contrôles et de vos décisions du brief présentiel ;
- d'une livraison candidate dans
  `data_pack/2026-S1/m2_candidate_release/` ;
- des notes de livraison et des empreintes associées.

La livraison contient des ajouts et des mises à jour. Elle peut aussi présenter
des erreurs, des évolutions légitimes ou des valeurs qui nécessitent un avis
métier. Elle ne doit pas être fusionnée automatiquement avec les données déjà
publiées.

## Mission

Déterminez si la nouvelle livraison peut rejoindre le data pack sans dégrader
la qualité du socle M2. Pour cela, vous devez :

- examiner si vos contrôles M2 restent valables sur une nouvelle livraison ;
- comparer le lot candidat aux données déjà publiées ;
- distinguer les erreurs, les avertissements et les évolutions acceptables ;
- définir des règles et des seuils de décision compréhensibles ;
- rendre la qualification reproductible et vérifiable ;
- intégrer les contrôles dans une chaîne GitHub Actions ;
- conclure par une décision d'intégration argumentée.

Le résultat attendu n'est pas une liste d'anomalies trouvées à la main. Une
autre personne doit pouvoir appliquer le même dispositif à une prochaine
livraison et comprendre la décision obtenue.

## Axes d'investigation

Les axes suivants structurent la mission sans imposer un ordre de réalisation
ni une architecture logicielle.

### Réutilisabilité du travail M2

Examinez votre solution précédente :

- quels contrôles fonctionnent sans modification ;
- quelles règles dépendent trop fortement des premiers fichiers ;
- quelles valeurs, catégories ou limites sont codées en dur ;
- quelles hypothèses étaient implicites ;
- quels contrôles deviennent nécessaires lorsqu'un lot s'ajoute à un
  historique existant.

Faites évoluer ce qui doit l'être sans écrire une solution qui reconnaît
uniquement les exemples de la livraison candidate.

### Comparaison avec la version publiée

La qualification doit permettre de comparer au minimum :

- les colonnes, les types et les formats ;
- les identifiants dans le lot et les collisions avec l'historique ;
- les relations entre équipements, événements et interventions ;
- les valeurs manquantes et leur fréquence ;
- les catégories connues et les nouvelles valeurs ;
- les cohérences temporelles et les règles métier ;
- les distributions principales et les valeurs inhabituelles ;
- la représentation des sites, types d'équipement et criticités ;
- les informations relatives à des personnes dans les notes libres.

Une différence avec la version précédente n'est pas nécessairement une erreur.
Votre travail doit distinguer une anomalie de ligne, une régression globale,
une évolution de contrat et une évolution métier potentiellement légitime.

### Politique de qualification

Définissez une politique qui classe les résultats, par exemple :

- **erreur bloquante** : la livraison ne peut pas être intégrée ;
- **avertissement** : une décision humaine ou une condition est nécessaire ;
- **information** : l'évolution doit être tracée mais ne bloque pas le lot.

Les règles et les seuils importants doivent être identifiables, modifiables et
justifiés. Leur format est libre : fichier YAML ou JSON, constantes documentées
ou autre solution lisible.

Exemple indicatif :

```yaml
rules:
  orphan_equipment_reference:
    level: error
    maximum_rate: 0
  missing_work_order_note:
    level: warning
    maximum_rate: 0.05
```

Cet exemple illustre une configuration ; il ne constitue pas la politique
attendue ni la liste exhaustive des règles.

### Reproductibilité et non-régression

Votre dispositif doit conserver :

- l'identifiant ou la version de la livraison contrôlée ;
- les empreintes des fichiers reçus ;
- la version des règles appliquées ;
- les résultats obtenus ;
- la décision produite ;
- la distinction entre données reçues, acceptées et mises à l'écart.

Prévoyez des vérifications démontrant au minimum qu'une rupture de schéma, une
relation absente et une règle bloquante sont détectées. Un avertissement ne
doit pas provoquer le même comportement qu'une erreur bloquante. Deux
exécutions sur les mêmes entrées et avec les mêmes règles doivent aboutir à la
même décision, sans modifier les données publiées.

### Automatisation locale

La qualification doit pouvoir être lancée sans reprendre manuellement les
contrôles. Elle doit d'abord fonctionner localement avec des dépendances et une
commande documentées. Un autre développeur doit pouvoir cloner le dépôt,
installer l'environnement et reproduire les résultats annoncés.

L'automatisation peut produire l'un des statuts suivants ou un vocabulaire
équivalent :

```text
ACCEPTED
ACCEPTED_WITH_WARNINGS
REJECTED
```

Elle ne doit ni fusionner ni publier automatiquement les données candidates.
La décision d'intégration finale reste explicite.

## Laboratoire GitHub Actions — 6 h

Cette partie prolonge la qualification locale. Elle est obligatoire pour
terminer le complément « Pour aller plus loin », mais elle n'est pas requise
pour valider le parcours principal de M2.

### Prise en main

Réalisez le parcours officiel **GitHub Skills — Test with Actions**, ou un
laboratoire équivalent validé par le formateur. Le laboratoire peut être
réalisé dans un dépôt d'exercice distinct.

Il doit vous permettre de manipuler au minimum :

- un fichier de workflow YAML ;
- les déclencheurs `push`, `pull_request` et `workflow_dispatch` ;
- l'installation des dépendances ;
- l'exécution des tests ;
- la lecture des journaux et du résumé d'une exécution ;
- la conservation d'un rapport comme artefact.

Conservez dans votre journal de bord les difficultés rencontrées et les
éléments que vous réutilisez pour DiagOps. Il n'est pas demandé de reproduire
un cours GitHub Actions dans votre compte rendu.

### Application à DiagOps

Ajoutez dans votre dépôt privé un workflow actif :

```text
.github/workflows/data-quality.yml
```

GitHub ne détecte pas un workflow placé sous `work/M2/`. Le fichier YAML est
donc la seule production de ce complément située hors de ce dossier. Le code,
les tests, les configurations et les rapports restent sous
`work/M2/aller_plus_loin/`.

Le workflow doit pouvoir être lancé :

- lors d'une pull request interne à votre dépôt privé ;
- lors d'un push sur `main` ;
- manuellement depuis l'interface GitHub.

Aucune pull request ne doit être ouverte vers le dépôt pédagogique
`upstream`.

### Comportement attendu du workflow

La chaîne d'intégration doit :

1. récupérer une copie propre du dépôt ;
2. installer explicitement les dépendances nécessaires ;
3. exécuter les tests automatisés ;
4. qualifier les données M2 déjà publiées comme contrôle de non-régression ;
5. qualifier la livraison candidate avec les mêmes règles ;
6. publier un résumé lisible de la qualification ;
7. conserver les rapports détaillés comme artefacts.

Le résumé doit présenter au minimum :

- la version des règles ;
- les fichiers ou la livraison contrôlés ;
- le nombre d'erreurs, d'avertissements et d'informations ;
- le statut obtenu pour chaque lot ;
- la décision finale.

### Résultats et échecs

Le workflow doit distinguer les situations suivantes :

| Situation | Comportement attendu |
|---|---|
| test ou dépendance en échec | échec technique |
| fichier absent ou illisible | échec technique |
| règle bloquante enfreinte | livraison `REJECTED` et contrôle en échec |
| avertissements uniquement | workflow réussi, avertissements visibles |
| aucune anomalie bloquante | workflow réussi |

Les rapports doivent rester consultables même lorsque la livraison est
rejetée. Une intégration ou une modification automatique du data pack reste
interdite.

### Démonstration attendue

Créez une branche temporaire dans votre dépôt privé et ouvrez une pull request
vers votre propre branche `main`. Utilisez-la pour montrer :

- une exécution réussie ;
- une exécution qui rejette un cas incorrect contrôlé ;
- le résultat des contrôles visible sur la pull request ;
- un résumé compréhensible sans lire tous les journaux ;
- un rapport téléchargeable comme artefact.

La branche et la pull request servent uniquement à la démonstration du
workflow. Elles ne modifient pas l'organisation habituelle du cursus sur
`origin/main`.

### Sécurité minimale

Le workflow doit :

- limiter ses permissions à `contents: read` lorsque aucune écriture n'est
  nécessaire ;
- ne contenir ni jeton, ni mot de passe, ni secret en clair ;
- ne pas exécuter le contenu textuel des fichiers CSV ;
- ne pas écrire dans `data_pack/` ;
- ne pas publier automatiquement une livraison candidate ;
- utiliser des actions et dépendances identifiables et versionnées.

## Questions auxquelles répondre

1. Quels contrôles M2 ont pu être réutilisés sans modification ?
2. Quelles hypothèses de votre première solution étaient trop liées aux
   fichiers initiaux ?
3. Le schéma ou les catégories ont-ils évolué, et ces changements sont-ils
   acceptables ?
4. La qualité globale du lot candidat s'améliore-t-elle ou se dégrade-t-elle
   par rapport à la version publiée ?
5. Quels écarts concernent une ligne et lesquels concernent l'ensemble de la
   livraison ?
6. Quelles règles doivent bloquer automatiquement une intégration ?
7. Quels constats nécessitent une décision humaine ou métier ?
8. Le lot peut-il être intégré sans altérer ni rendre incohérentes les données
   historiques ?
9. Les résultats peuvent-ils être reproduits à partir d'une version précise
   des données et des règles ?
10. Quelle décision prenez-vous : acceptation, acceptation sous conditions ou
    rejet ?

Pour la partie GitHub Actions, répondez également aux questions suivantes :

11. Les résultats locaux et ceux de GitHub Actions sont-ils identiques ?
12. Quelles dépendances et commandes ont dû être rendues explicites ?
13. Comment distinguez-vous un échec technique d'un rejet de la livraison ?
14. Comment les avertissements restent-ils visibles sans provoquer un échec ?
15. Peut-on diagnostiquer une livraison rejetée à partir du résumé et des
    artefacts, sans relancer le workflow ?
16. Quelles opérations doivent rester soumises à une validation humaine ?

## Liberté technique

Vous pouvez prolonger votre notebook M2, faire évoluer vos scripts, construire
une petite commande de qualification ou combiner ces approches. L'outil choisi
n'est pas évalué pour lui-même.

La solution doit toutefois séparer clairement :

- les données publiées ;
- la livraison candidate reçue ;
- les règles de qualification ;
- les résultats et rapports produits ;
- les données éventuellement préparées pour intégration.

## Productions attendues

- les contrôles M2 adaptés à plusieurs livraisons ;
- une politique versionnée des règles et seuils ;
- des vérifications couvrant les principaux cas de qualification ;
- un rapport comparant la version publiée et le lot candidat ;
- un manifeste d'exécution associant données, règles, résultats et décision ;
- la preuve que la qualification peut être relancée automatiquement ;
- une note de décision répondant aux dix questions ;
- une entrée complémentaire dans le journal de bord.

La partie GitHub Actions ajoute :

- le workflow `.github/workflows/data-quality.yml` dans le dépôt privé ;
- une exécution réussie et une exécution démontrant un rejet ;
- un résumé de qualification visible dans GitHub ;
- les rapports détaillés conservés comme artefacts ;
- une pull request interne montrant le résultat des contrôles ;
- les réponses aux questions 11 à 16 dans la note de décision ou le README.

Une organisation possible, sans caractère obligatoire :

```text
work/M2/aller_plus_loin/
├── README.md
├── config/
│   └── quality_rules.yaml
├── src/
├── tests/
├── reports/
│   ├── baseline/
│   └── candidate_release/
├── run_manifest.json
└── decision_livraison.md

.github/workflows/
└── data-quality.yml
```

## Critères de réussite

- les contrôles ne sont pas spécifiques aux anomalies déjà observées ;
- les données publiées restent intactes ;
- le lot historique et le lot candidat sont contrôlés avec une politique
  identifiable ;
- les écarts sont quantifiés et expliqués ;
- erreurs, avertissements et informations sont distingués ;
- les règles et seuils importants peuvent être modifiés sans réécrire toute la
  solution ;
- la qualification produit un statut exploitable et un rapport compréhensible ;
- les résultats sont reproductibles ;
- la décision finale correspond aux résultats obtenus et expose les conditions
  ou incertitudes restantes.

Pour GitHub Actions :

- le workflow fonctionne depuis une copie propre du dépôt ;
- les dépendances et commandes ne reposent pas sur l'environnement local ;
- les résultats locaux et distants sont cohérents ;
- les échecs techniques, rejets métier et avertissements sont distingués ;
- le résumé et les artefacts permettent de comprendre un rejet ;
- les permissions sont minimales et aucun secret n'est exposé ;
- aucune donnée source n'est modifiée ou publiée automatiquement.

## Hors périmètre

Il n'est pas demandé de :

- traiter les données capteurs ou anticiper le travail temporel de M3 ;
- réentraîner le modèle M1 ;
- construire une plateforme de données ou une base de production ;
- déployer un service ;
- intégrer automatiquement la livraison candidate ;
- configurer une infrastructure cloud ou un runner GitHub auto-hébergé ;
- rendre obligatoire un contrôle de branche dépendant d'une offre GitHub
  particulière ;
- retrouver exactement toutes les anomalies prévues par le formateur.

## Statut pédagogique

Ce complément représente environ 20 h de travail supplémentaire : 14 h pour
la qualification et 6 h pour le laboratoire et l'intégration GitHub Actions.
Il est facultatif et ne modifie ni la charge obligatoire de M2, fixée à 20 h,
ni les acquis communs attendus pour commencer M3.
