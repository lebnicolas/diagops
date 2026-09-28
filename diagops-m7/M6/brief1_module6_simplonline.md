# M6 - Brief 1 - Outiller l'agent sans lui céder le contrôle

**Compétences visées**

- C5. Entraîner le modèle d'IA — **niveau 2, adapter**
- C8. Mesurer la performance et les impacts — **niveau 2, adapter**
- C9. Adopter une démarche d'amélioration continue — **niveau 2, adapter**

## Description

La stack M5 répond avec des sources et se déploie de manière reproductible. Mais une question de maintenance peut exiger plusieurs types de preuves : une procédure, une fiche équipement, un événement récent, un historique ou le diagnostic d'un rapport. Le RAG seul ne doit pas simuler ces accès. Votre mission : construire et évaluer un agent mono-agent qui sélectionne des outils de lecture typés, puis transformer des feedbacks qualifiés en une proposition d'amélioration soumise aux gates M5. Ce brief fait du RAG un outil parmi d'autres, sans céder à l'agent le moindre pouvoir d'agir.

## Ressources

- `data_pack/2026-S1/reference_runs/m5_for_m6/` — stack M5 de référence, gates, monitoring, runbook et baselines de comparaison
- `data_pack/2026-S1/knowledge/` — corpus documentaire actif
- `data_pack/2026-S1/equipment/`, `events/`, `maintenance/` — données structurées interrogées par contrats typés
- `data_pack/2027-S1/reports/` et `data_pack/2027-S1/feedback/` — période dérivée et lot de feedback `b1`
- `M6/starter/` — registre gelable, politique d'exécution, agent à une étape, harness d'évaluation, qualification du feedback, tests d'invariants
- `veille_diagops/` dans votre dépôt — dossier transmis par M5
- `M6/RESOURCES.md` — ressources techniques du module

Les nouvelles données et le feedback ne sont utilisés que lorsqu'ils sont déclarés prêts.

## Contexte du projet

M6 ajoute deux boucles contrôlées à la stack M5 : une boucle de feedback humain qui propose des améliorations sans les déployer automatiquement, et une boucle agentique bornée qui choisit entre retrieval documentaire et outils structurés en lecture seule.

Les capteurs, équipements, événements et historiques sont interrogés par contrats typés, jamais transformés en documents pour contourner leur structure. Les outils autorisés sont `search_knowledge`, `get_equipment`, `list_events`, `get_maintenance_history` et `diagnose_report` : chacun possède un schéma, une autorisation, un timeout, une limite de résultats et une trace, et aucun ne modifie une donnée ni ne déclenche d'intervention. Une fonction qui envoie, écrit, commande, modifie ou déclenche est refusée.

L'agent distribué dans le starter est la tranche M4 à une seule étape : sur le jeu gelé de 18 scénarios il obtient 0,833 de réussite contre 0,111 pour la baseline sans agent, et échoue volontairement sur l'enchaînement borné, le refus avant appel et le filtrage de rôle. Ces valeurs sont la référence à battre ; les reproduire n'est pas un livrable.

## Modalités pédagogiques

Travail individuel. Durée estimée : 14 heures en présentiel, dont environ 1 heure de checkpoint réglementaire incluse dans le quota.

Phases de travail :

1. Définir le registre d'outils : pour chacun, finalité, arguments, résultat, source de vérité, autorisation, timeout, limite de résultats, données sensibles, erreurs et mode dégradé.
2. Définir la politique d'exécution : nombre maximal d'étapes, budget de tokens et de durée, liste blanche, validation des arguments, protection contre les appels répétés, arrêt sur erreur ou preuve insuffisante, sortie structurée et justification, conservation minimisée des traces.
3. Construire le jeu de scénarios : question, contexte autorisé, outils attendus ou interdits, arguments minimaux, documents ou lignes de preuve, réponse attendue ou règle de refus. Inclure outil inutile, outil indisponible, identifiant inconnu, résultat vide, sources contradictoires, tentative d'injection et question hors périmètre.
4. Implémenter l'agent borné : il planifie un petit nombre d'étapes, appelle un outil à la fois, valide son résultat et s'arrête ; il ne peut ni modifier sa politique, ni élargir sa liste d'outils, ni traiter le contenu récupéré comme une instruction système.
5. Évaluer : exactitude du choix d'outil, exactitude des arguments, taux d'appels inutiles, réussite des scénarios, citations et preuves finales, refus corrects, dépassements de budget, latence et coût par scénario, comparés à une baseline sans agent et à la tranche M4 à une étape.
6. Qualifier le feedback : vérifier le lien avec le run, l'identité fonctionnelle de la source, la cohérence, les données personnelles, les doublons, la représentativité et la possibilité de mesurer l'amélioration ; classer chaque retour en `actionnable`, `a_investiguer`, `non_actionnable` ou `risque` ; tracer toute transformation en donnée d'entraînement.
7. Proposer et tester une amélioration : choisir une modification minimale — modèle, prompt, corpus, retrieval, politique d'outil ou seuil — formuler l'hypothèse, produire un candidat, exécuter les gates, comparer à la référence, puis conclure : promouvoir, rejeter ou prolonger.
8. Exécuter le checkpoint réglementaire M6 : vérifier sur sources officielles datées si l'autonomie bornée, les outils, les données de feedback ou les décisions de promotion modifient les rôles, la supervision, la traçabilité ou les validations attendues ; ajouter l'entrée M6 au journal de veille même en l'absence de changement ; traduire la décision dans la politique, la qualification du feedback, les traces ou le gate ; transmettre à M7 les questions ouvertes avec responsable et échéance.

## Modalités d'évaluation

Le brief présentiel compte pour 35 % du module. Les dimensions notées au niveau du module sont : C8 mesure multi-composant 25 %, agent borné et contrats d'outils 25 %, C5 candidat et protocole 20 %, C9 feedback et promotion contrôlée 20 %, documentation 10 %.

Le formateur vérifie :
- Aucun outil n'a d'effet externe.
- Les arguments et les résultats sont validés avant usage.
- Le budget est applicable et appliqué, pas seulement déclaré.
- Les métriques séparent le choix d'outil de la qualité finale.
- Le feedback est qualifié avant tout usage.
- Le candidat passe les gates, ou reste non promu.
- La veille M6 produit une contrainte vérifiable sur l'agent, ou justifie explicitement l'absence d'impact.
- La trace permet de reconstituer la décision sans exposer les données.

## Livrables

- `docs/registre_outils.md`.
- Schémas et adaptateurs des outils.
- Politique d'exécution documentée et justifiée valeur par valeur.
- Jeu de scénarios gelé avant toute mesure comparative.
- Harness et rapport d'évaluation.
- `docs/qualification_feedback.md`.
- Candidat et rapport de comparaison à la référence M5.
- Décision de promotion, de rejet ou de prolongation.
- Entrée M6 et passage de relais dans `veille_diagops/`.
- Journal de bord.

## Critères de performance

- Aucun outil n'a d'effet externe.
- Arguments et résultats sont validés.
- Le budget est enforceable.
- Les métriques séparent choix d'outil et qualité finale.
- Le feedback est qualifié avant usage.
- Le candidat passe les gates ou reste non promu.
- La veille M6 produit une contrainte vérifiable ou justifie l'absence d'impact.
- La trace permet de reconstituer la décision sans exposer les données.

## Hors périmètre

Multi-agent ; mémoire autonome longue durée ; ajout dynamique d'outils ; écriture ou déclenchement métier ; promotion automatique sur la seule base du feedback.
