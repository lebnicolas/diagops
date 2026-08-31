# Brief 3 M4-M8 — Poursuivre la veille réglementaire de DiagOps

## Continuité de la mission

Le brief de veille ouvert en M0 est consolidé et restitué en M4. Le présent
brief organise son prolongement jusqu'en M8 afin que les décisions prises pour
le RAG, le déploiement et l'agent restent compatibles avec l'évolution du cadre
réglementaire.

Il ne s'agit ni de produire un avis juridique ni de recopier des textes. À
chaque module, l'apprenant vérifie ce qui a changé, mesure l'impact sur DiagOps
et prend une décision traçable.

## Charge et articulation avec les 40 heures

- **M4** : consolidation et restitution déjà prévues par le brief M0 ;
- **M5 à M8** : un checkpoint d'environ **1 h par module**, inclus dans les
  14 h du brief présentiel ;
- aucune heure ne s'ajoute au quota de **40 h par module** ;
- le checkpoint réutilise les analyses, registres de risques, ADR, runbooks et
  preuves déjà produits dans le module.

## Dossier longitudinal

Le dossier `veille_diagops/` ouvert en M0 reste la source de référence. Les cinq
livrables initiaux sont conservés :

```text
veille_diagops/
├── sources_veille.md
├── journal_veille.md
├── ai_act_diagops.md
├── radar_technologique.md
├── recommandations_architecture_m4.md
└── synthese_veille_m8.md
```

Le fichier `synthese_veille_m8.md` est créé en M8. Les autres fichiers sont
mis à jour sans effacer leur historique ni antidater une conclusion.

## Règle commune à chaque checkpoint

Chaque entrée M4-M8 doit comporter :

1. la date de consultation et la date du texte ou de la publication ;
2. le statut de la source : texte applicable, ligne directrice, projet,
   consultation ou analyse secondaire ;
3. au moins une source officielle primaire lorsqu'elle existe ;
4. la distinction entre fait vérifié, interprétation et incertitude ;
5. les rôles concernés et l'étape du cycle de vie touchée ;
6. l'impact sur les données, le modèle, le RAG, l'agent, l'exploitation ou la
   supervision humaine ;
7. une décision : `maintenir`, `evaluer`, `modifier` ou `ecarter` ;
8. le livrable du module modifié par cette décision, ou la justification datée
   de l'absence de changement.

Une absence d'évolution réglementaire constitue un résultat recevable si les
sources officielles ont été revérifiées et si cette vérification est datée.

## Progression attendue

| Module | Question de veille | Preuve intégrée au module |
|---|---|---|
| **M4** | Les scénarios, rôles et hypothèses AI Act restent-ils valides pour le modèle simple, le RAG et l'agent à une étape ? | analyse AI Act consolidée, radar, recommandation d'architecture et passage de relais M5 |
| **M5** | Le déploiement, les fournisseurs, la journalisation, la rétention et le traitement des incidents créent-ils de nouvelles obligations ou preuves ? | entrée M5, contraintes ajoutées au runbook, aux traces ou aux gates CI |
| **M6** | L'ajout d'outils, de feedback et d'une autonomie bornée modifie-t-il la qualification, la supervision ou les exigences de traçabilité ? | entrée M6, contraintes ajoutées à la politique d'outils, de feedback ou de promotion |
| **M7** | L'architecture cible, les dépendances, la souveraineté, la réversibilité et l'outil à effet simulé modifient-ils les risques et responsabilités ? | entrée M7, risques et décisions traduits dans les ADR et le plan de migration |
| **M8** | Le nouveau besoin relève-t-il des mêmes hypothèses, et quelles exigences doivent être suivies après la formation ? | analyse propre au nouveau projet, synthèse finale et plan de veille post-M8 |

## Passage de relais obligatoire

La sortie de chaque module transmet au suivant :

- la dernière entrée datée du journal ;
- les sources ajoutées, retirées ou requalifiées ;
- les décisions confirmées ou révisées ;
- les exigences devenues test, gate, métrique, règle de supervision ou point de
  validation juridique ;
- le responsable et l'échéance des questions encore ouvertes.

Une décision réglementaire importante qui n'est reliée à aucun artefact
technique ou organisationnel est considérée comme non traitée.

## Synthèse finale M8

Le fichier `synthese_veille_m8.md` contient au minimum :

- la chronologie des évolutions et requalifications de M0 à M8 ;
- les hypothèses M4 confirmées, corrigées ou devenues caduques ;
- les décisions qui ont modifié le RAG, l'agent ou l'architecture ;
- les preuves disponibles pour la traçabilité, la supervision, la robustesse et
  la gestion des incidents ;
- les écarts restant à traiter et les validations juridiques nécessaires ;
- les sources à maintenir, leur fréquence de consultation et leur responsable ;
- les critères imposant une réévaluation après M8.

## Critères de réussite

- une entrée substantielle et datée existe pour chaque module M4-M8 ;
- chaque entrée s'appuie sur une source primaire lorsque celle-ci existe ;
- les changements réglementaires sont distingués des changements techniques ;
- chaque décision produit un impact vérifiable ou une absence d'impact justifiée ;
- les passages de relais permettent de reconstituer l'évolution des décisions ;
- la synthèse M8 ne formule aucune qualification juridique catégorique sans
  hypothèses, limites et point de validation compétente.
