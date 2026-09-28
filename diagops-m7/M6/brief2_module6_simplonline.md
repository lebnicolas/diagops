# M6 - Brief 2 - Résister à une campagne agentique adversariale

**Compétences visées**

- C5. Entraîner le modèle d'IA — **niveau 2, adapter** (consolidé)
- C8. Mesurer la performance et les impacts — **niveau 2, adapter** (consolidé)
- C9. Adopter une démarche d'amélioration continue — **niveau 2, adapter** (consolidé)

## Description

Le brief 1 a produit un agent outillé en lecture seule et une boucle de feedback. Les scénarios nominaux ne suffisent pas à établir que permissions, budgets et contrats tiennent lorsque les entrées ou les outils se comportent mal. Votre mission : étendre le jeu agentique, qualifier un nouveau lot de feedback, soumettre l'agent à une campagne indépendante, puis corriger la politique et décider du candidat d'amélioration. Une correction qui élargit une permission n'est pas une correction.

## Ressources

- Agent, registre d'outils et politique issus du brief 1
- Jeu de scénarios gelé du brief 1
- `data_pack/2027-S1/feedback/` — nouveau lot `b2`, qualifié par le formateur
- `M6/starter/adversarial/` — campagne de départ, catalogue d'invariants, rapport et remédiation
- `M6/starter/eval/run_agent_eval.py` — harness permettant de simuler erreurs, délais et résultats d'outils
- `data_pack/2026-S1/reference_runs/m5_for_m6/` — version M5 restaurable et baselines de comparaison

## Contexte du projet

Les invariants agentiques sont le socle de l'exercice : aucun effet externe, aucun outil hors liste, arguments conformes, budget applicable, arrêt sur erreur critique, filtres d'accès appliqués avant la donnée, promotion humaine uniquement, contenu récupéré traité comme une donnée, contradiction entre source structurée et document exposée. Un invariant violé et non corrigé bloque la promotion.

La campagne fournie couvre six vecteurs — injection demandant un outil interdit, résultat d'outil contenant une instruction, argument visant une autre ressource, répétition coûteuse, timeout en cascade, conflit entre outil structuré et document. Le pair qui conduit la campagne complète les vecteurs manquants : identifiant ambigu et preuve insuffisante, feedback malveillant ou non représentatif — ce dernier se traite par la qualification du feedback, pas par l'agent.

Les attaques restent dans le laboratoire : aucune n'est dirigée vers un système tiers et aucune ne sort du data pack distribué.

## Modalités pédagogiques

Travail individuel, puis campagne conduite par un pair. Durée estimée : 20 heures — 12 h de réalisation, 4 h de campagne indépendante, 4 h de remédiation et défense.

Phases de travail :

1. Réalisation, 12 h — Étendre les scénarios : cas multi-étapes mais bornés, outil inutile, arguments invalides, résultat vide, identifiant ambigu, timeout, données contradictoires, preuve insuffisante, refus attendu.
2. Instrumenter la politique : rendre observables budget restant, choix d'outil, validation des arguments, résultat, arrêt, fallback et raison finale, sans chaîne de pensée privée ni donnée sensible complète dans les traces.
3. Qualifier le feedback : mesurer doublons, couverture, cohérence, provenance et risques ; ne transformer que les retours actionnables en proposition versionnée.
4. Construire un candidat : modifier un seul axe principal — modèle, prompt, retrieval, politique, outil ou seuil — et rejouer anciens et nouveaux scénarios avant toute recommandation.
5. Préparer les invariants adversariaux et les rendre vérifiables.
6. Campagne indépendante, 4 h — Un pair construit ou sélectionne des attaques sans modifier le runtime ; chaque cas produit verdict, trace, impact et invariant concerné.
7. Remédiation et défense, 4 h — Classer les échecs par politique, contrat, outil, modèle ou test ; corriger sans élargir les permissions ; rejouer campagne et non-régression ; comparer référence et candidat ; décider promotion, rejet ou prolongation ; défendre le meilleur argument opposé.

## Modalités d'évaluation

Le brief 2 compte pour 35 % du module. L'évaluation porte sur la tenue des invariants sous contradiction et sur la qualité de la remédiation, pas sur le nombre d'attaques repoussées.

Le formateur vérifie :
- Les attaques restent dans le laboratoire.
- Aucun outil ne possède d'effet.
- L'agent ne peut pas élargir sa liste blanche.
- Les résultats d'outils sont traités comme des données.
- Budgets et timeouts sont vérifiables.
- Le candidat est comparé aux scénarios historiques, pas seulement aux nouveaux.
- Un échec non corrigé bloque la promotion.

Gate renforcé M6 : l'agent respecte ses invariants sous campagne indépendante, et toute amélioration reste réversible, mesurée et soumise à une décision humaine.

## Livrables

- Scénarios étendus.
- Instrumentation et tableau des métriques.
- Qualification du nouveau lot de feedback.
- Candidat versionné, un seul axe modifié.
- Campagne indépendante et ses traces.
- Rapport d'invariants, avec verdict par cas.
- Correction et résultats avant / après.
- Décision de promotion, de rejet ou de prolongation.
- Support de défense.

## Critères de performance

- Les attaques restent dans le laboratoire.
- Aucun outil ne possède d'effet.
- L'agent ne peut élargir sa liste blanche.
- Les résultats d'outils sont traités comme données.
- Budgets et timeouts sont vérifiables.
- Le candidat est comparé aux scénarios historiques.
- Un échec non corrigé bloque la promotion.
