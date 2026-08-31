# Module 4 — Concevoir une IA simple, fondée sur des preuves

**Durée S04 : 40 h — 14 h présentiel + 6 h online + 20 h approfondissement**

**Fil rouge moderne : première tranche RAG-agentique de DiagOps**

## Positionnement

M4 transforme les données, règles et limites transmises par M3 en décisions de
conception mesurées. Il poursuit deux questions complémentaires :

1. un modèle simple apporte-t-il un gain démontrable sur la qualification des
   fenêtres capteurs face à la baseline par règles de M3 ?
2. un système de retrieval puis de génération citée apporte-t-il une réponse
   plus fiable aux questions de maintenance qu'une réponse sans contexte ?

Le présentiel construit une tranche verticale minimale : modèle simple, RAG
cité et agent limité à une décision de consultation. L'online couvre le module
CampusAtlas « Concevoir une IA simple » avec son vocabulaire C1, C2 et C4.

Les deux briefs sont autonomes. Un état formateur M3 commun permet de commencer
sans dépendre de la production personnelle précédente.

## Compétences travaillées

| Compétence | Résultat attendu | Niveau visé | Preuve principale |
|---|---|---:|---|
| **C1** | Constituer des jeux d'évaluation cohérents avec le besoin | **N2** | protocole, splits gelés, couverture et limites |
| **C2** | Consolider les risques éthiques, réglementaires et de sécurité | **N3** | threat model, analyse AI Act et risques résiduels |
| **C4** | Choisir un modèle et une approche de retrieval par démarche scientifique | **N1** | benchmarks, matrice de décision et recommandation |

C7 et C8 sont mobilisées comme compétences transversales de préparation : la
mesure et le dossier de conception seront approfondis dans les modules suivants.

## Entrées

- état de référence `data_pack/2026-S1/reference_runs/m3_for_m4/` ;
- calibration et test `data_pack/2026-S1/model_eval/`, avec oracle scellé ;
- corpus et manifeste `data_pack/2026-S1/knowledge/` ;
- questions gelées `data_pack/2026-S1/rag_eval/questions.jsonl` ;
- schéma et contrat de sortie DiagOps ;
- dossier `veille_diagops/` et mission de veille ouverte en M0.

Les actifs marqués `planned` dans le manifeste doivent passer à un état de
distribution vérifié avant l'ouverture du module.

## Brief présentiel — pratique moderne

### Mission

Prouver, sur des jeux gelés, ce qu'apportent un modèle simple et un RAG minimal,
puis limiter l'agent à un choix explicable entre réponse directe, consultation
documentaire et refus.

### Sorties attendues

- besoin, cible et erreurs coûteuses explicités ;
- baseline M3 figée avant le test ;
- au moins deux candidats de modélisation comparés équitablement ;
- baseline sans retrieval, retrieval lexical et retrieval vectoriel mesurés ;
- réponses associées à des citations résolubles vers le manifeste ;
- refus lorsque le corpus ne contient pas de preuve suffisante ;
- agent à une étape, sans outil à effet ni boucle libre ;
- tests de documents contradictoires, obsolètes et porteurs d'instructions ;
- matrice de décision et conditions de non-déploiement.

## Brief online — couverture Atlas

Le brief online reprend les attendus du programme officiel : analyser le besoin,
identifier les données nécessaires, comparer des familles de modèles, intégrer
les contraintes opérationnelles et d'éco-conception, communiquer les risques et
documenter les choix.

Il n'exige ni RAG, ni agent, ni base vectorielle pour valider la couverture
CampusAtlas. Les preuves de modernisation ne remplacent pas les preuves C1-C4.

## Brief 2 — approfondissement et réplication

Le brief 2 consacre 12 h à une seconde itération individuelle, 4 h à la
reproduction ou au red teaming par un pair et 4 h à la remédiation puis à la
défense. Il introduit un corpus ou un lot caché, teste la robustesse du modèle et
du RAG, puis exige que les résultats principaux soient reproduits sans aide de
l'auteur.

## Brief 3 — veille réglementaire M4-M8

M4 consolide la mission M0-M4 : sources, journal, analyse AI Act, radar et
recommandations d'architecture. Il ouvre ensuite un checkpoint réglementaire
dans chaque module jusqu'en M8 selon
`brief3_module4_veille_reglementaire.md`. Cette continuité n'ajoute pas d'heures
au module ; la charge M4 est déjà portée par le brief ouvert en M0.

## Matrice de couverture

| Attendu | Programme Atlas | Mise à jour 2026 | Compétence |
|---|---|---|---|
| Nouveau besoin sur un projet existant | besoins, données, résultats attendus | décision d'utiliser ou non retrieval et agent | C1, C4 |
| Choix de modèle | familles, contraintes d'apprentissage, performance | baseline par règles et deux candidats gelés | C4 |
| Menaces | adversarial examples et atténuation | empoisonnement documentaire, injection indirecte, exfiltration | C2 |
| Risques sociétaux | confidentialité, biais, destinataires | AI Act daté, supervision humaine et refus | C2 |
| Éco-conception | contraintes de ressources | taille d'index, latence, mémoire et coût par réponse | C2, C4 |
| Documentation | étapes et justification | manifeste, citations, model card et décision | C1, C4 |
| Veille réglementaire | sources et cadre applicables | analyse datée, impact technique et passage de relais | C2 |

## Évaluation

- brief 1 présentiel : **35 %** ;
- brief 1 online : **30 %** ;
- brief 2 d'approfondissement : **35 %**.

| Dimension | Poids |
|---|---:|
| C1 — jeux, splits, couverture et provenance | 20 % |
| C2 — menaces, atténuations et risques résiduels | 20 % |
| C4 — comparaison et décision | 25 % |
| Reproductibilité des évaluations | 20 % |
| Documentation et argumentation | 15 % |

## Gate de sortie

M4 est franchi si le gain ou l'absence de gain est démontré contre les
baselines, si les citations sont vérifiables, si les questions non répondables
déclenchent un refus, si l'agent reste borné à une étape sans effet externe et
si une autre personne reproduit les résultats essentiels. Le dossier de veille
M4 doit être consolidé et transmettre à M5 les décisions, exigences et points
de validation juridique encore ouverts.

## Résultat de fin de module

DiagOps dispose d'une baseline de modèle simple, d'un premier pipeline de
retrieval évalué, d'un contrat de réponse citée, d'un agent minimal et d'un
registre de risques. M5 reçoit un état de référence figé et le passage de relais
réglementaire pour déployer et observer le système sans modifier silencieusement
les résultats M4.
