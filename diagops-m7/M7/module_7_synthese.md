# Module 7 — Challenger et sécuriser l'architecture DiagOps

**Durée S04 : 40 h — 14 h présentiel + 6 h online + 20 h approfondissement**

**Fil rouge moderne : souveraineté, réversibilité et contrôle des effets**

## Positionnement

M7 prend de la hauteur sur le système déployé et l'agent outillé. Il ne cherche
pas d'abord une nouvelle fonctionnalité : il vérifie les frontières de
confiance, les flux, permissions, dépendances et modes dégradés, puis propose une
architecture cible soutenable.

Un outil à effet peut être spécifié et exercé uniquement dans un environnement
simulé. Son exécution exige une approbation humaine explicite, une idempotence,
une trace et une reprise. Le chemin de référence reste en lecture seule.

Le brief online couvre C2 et C7 du programme CampusAtlas : évaluer une
architecture selon une procédure et proposer des évolutions sous contraintes.

## Compétences travaillées

| Compétence | Résultat attendu | Niveau visé | Preuve principale |
|---|---|---:|---|
| **C2** | Évaluer risques sociétaux, sécurité et protection des données | **N3 consolidé** | threat model, red team et risques résiduels |
| **C7** | Challenger et faire évoluer l'architecture cible | **N2** | dossier d'architecture, ADR et plan de migration |

## Entrées

La référence commune `diagops-m6-reference-r1` est un état M6 rejouable pour
audit, avec échecs connus ; elle n'est pas un corrigé ni une solution promue.
Le guide [DIFFUSION.md](DIFFUSION.md) fixe prérequis, séquençage et preuves.

- `data_pack/2026-S1/reference_runs/m6_for_m7/` ;
- stack, outils, traces et métriques M5-M6 ;
- corpus documentaire, données structurées et politiques ;
- corpus image M7 seulement lorsqu'il est qualifié ;
- décisions AI Act et risques M4-M6 ;
- dossier `veille_diagops/` et passage de relais réglementaire M6.

## Brief présentiel — pratique moderne

### Mission

Évaluer l'architecture RAG-agentique existante, tester ses hypothèses sous
attaque et sous panne, comparer des options local/cloud/hybride puis proposer
une évolution réversible.

### Sorties attendues

- cartographie des composants, flux et frontières de confiance ;
- inventaire des données, modèles, fournisseurs et dépendances ;
- politique d'accès au corpus et aux outils ;
- matrice local/cloud/hybride et coût total ;
- contrats de portabilité pour embeddings, index, modèles et traces ;
- campagne red team et analyse des risques résiduels ;
- mode dégradé et objectifs de reprise ;
- spécification d'un outil à effet simulé avec approbation ;
- architecture cible, ADR et plan de migration réversible.

## Brief online — couverture Atlas

Le brief online applique une procédure d'évaluation à une architecture IA :
flux de données, cycle de vie, performance, coût, impacts éthiques, stockage,
packaging et propositions d'évolution. Il ne dépend pas de l'agent M6.

## Brief 2 — approfondissement et migration exercée

Le brief 2 rend la revue d'architecture expérimentale : 12 h pour préparer une
migration sur sous-ensemble et les scénarios de sécurité, 4 h de revue ou red
team indépendante, puis 4 h pour corriger les ADR, rejouer la migration et
défendre la cible révisée.

## Checkpoint de veille réglementaire M7

Environ 1 h des 14 h du présentiel confronte les rôles, dépendances,
fournisseurs, transferts, exigences de cybersécurité et de supervision aux
sources officielles datées. La décision est intégrée aux ADR, aux risques ou au
plan de migration et transmise à M8.

## Matrice de couverture

| Attendu | Programme Atlas | Mise à jour 2026 | Compétence |
|---|---|---|---|
| Flux et cycle de vie | source jusqu'à exploitation | corpus, chunks, index, prompts, traces et feedback | C7 |
| Impacts | destinataires, biais, confidentialité | permissions, exfiltration et supervision humaine | C2 |
| Performance | latence, capacité, coût | budgets agentiques et mode dégradé | C7 |
| Stockage | choix adapté aux données | relationnel, objet, vectoriel et journal d'audit | C7 |
| Architecture | challenge technique | souveraineté, réversibilité et dépendances | C2, C7 |
| Veille réglementaire | rôles et exigences | impact daté sur ADR, risques et migration | C2, C7 |

## Évaluation

- brief 1 présentiel : **35 %** ;
- brief 1 online : **30 %** ;
- brief 2 d'approfondissement : **35 %**.

| Dimension | Poids |
|---|---:|
| C2 — risques, droits et supervision | 25 % |
| C7 — architecture et migration | 30 % |
| Red team et modes dégradés | 20 % |
| Souveraineté et réversibilité | 15 % |
| Documentation et restitution | 10 % |

Cette grille sur 100 s'applique à chaque brief, en adaptant les preuves à
l'online autonome. La note module combine ensuite les trois notes avec les
poids 35/30/35 ; ces deux séries de poids ne s'additionnent pas. Le guide de
diffusion définit les niveaux de preuve et distingue note pédagogique, gate de
migration et certification officielle.

## Gate de sortie

L'architecture cible possède des frontières de confiance explicites, une
réversibilité exercée, des permissions minimales, un mode dégradé et une
position documentée sur tout outil à effet. Une revue indépendante a modifié ou
confirmé au moins une hypothèse ; les risques non acceptables bloquent la
migration. L'entrée de veille M7 doit être traduite dans l'architecture ou
justifier de façon sourcée l'absence de changement.

## Résultat de fin de module

DiagOps dispose d'une architecture revue et d'un plan de migration. M8 reçoit
un point de comparaison autoritatif pour cadrer un nouveau projet sans recopier
automatiquement la solution existante, ainsi que le dossier de veille et ses
points ouverts.
