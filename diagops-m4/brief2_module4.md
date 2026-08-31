# Brief 2 M4 — Répliquer, attaquer et corriger la preuve

**Durée : 20 h — 12 h de réalisation, 4 h de contradiction, 4 h de remédiation et défense**

## Situation

Le brief 1 a produit un modèle simple, un pipeline RAG et une première décision.
Cette décision reste fragile tant qu'elle dépend d'un seul corpus, d'un seul jeu
d'évaluation et de l'interprétation de son auteur.

## Mission

Soumettre les résultats M4 à un lot inédit et à une reproduction indépendante,
puis corriger le système et la décision à partir des écarts observés.

## Entrées

- état M4 produit au brief 1 ou référence formateur équivalente ;
- protocole, configurations et résultats gelés ;
- second corpus ou révision documentaire qualifiée ;
- lot d'évaluation caché, révélé seulement après gel du candidat ;
- grille de reproduction commune.

Le formateur remet le paquet de contradiction dans un canal daté après le gel.
Il contient un lot capteur inédit, une livraison documentaire incrémentale et
des questions sans labels. Les oracles restent hors du dépôt apprenant.

## Phase 1 — Réalisation individuelle, 12 h

### 1. Auditer la transmissibilité

Vérifiez qu'une personne tierce peut reconstruire environnement, features,
index, prompts, modèle et métriques. Listez les informations manquantes avant de
modifier quoi que ce soit.

### 2. Qualifier le nouveau lot

Mesurez couverture, révisions, droits, sensibilité, questions non répondables et
différences de distribution. Le lot caché ne sert pas à régler les seuils.

### 3. Rejouer les baselines

Exécutez sans modification : règles M3, modèle M4, retrieval lexical,
retrieval vectoriel, génération citée et agent à une étape. Conservez toutes les
versions et écarts.

### 4. Étendre la campagne de menaces

Ajoutez au minimum : document prioritaire malveillant, instruction indirecte,
révision obsolète, conflit entre sources, citation inexistante, question hors
périmètre et tentative d'obtenir une donnée restreinte.

### 5. Formuler une seule correction

Choisissez une correction principale fondée sur un échec observé : filtre,
chunking, modèle, seuil, contrat de citation, règle de refus ou politique de
l'agent. Annoncez le gain attendu et les régressions possibles.

## Phase 2 — Contradiction indépendante, 4 h

Un autre apprenant reçoit dépôt, protocole et grille, mais aucune explication
orale préalable. Il doit :

- reconstruire un run principal ;
- vérifier un échantillon de citations ;
- rejouer au moins trois menaces ;
- rechercher une fuite de test ou une hypothèse implicite ;
- produire un rapport distinguant `reproduit`, `écart`, `bloqué` et `non testé`.

L'auteur ne corrige pas pendant cette phase.

## Phase 3 — Remédiation et défense, 4 h

- traiter chaque écart du rapport ;
- rejouer les tests concernés ;
- mettre à jour model card, threat model et matrice de décision ;
- conserver les résultats avant/après ;
- défendre la décision finale et le meilleur argument contraire.

## Livrables

- rapport de qualification du nouveau lot ;
- résultats bruts avant correction ;
- campagne de menaces étendue ;
- rapport indépendant signé et daté ;
- correction et tests de non-régression ;
- comparaison avant/après ;
- décision M4 révisée ;
- support de défense ;
- journal de bord.

## Critères de réussite

- le lot caché reste fermé jusqu'au gel ;
- la reproduction ne dépend pas d'une aide orale ;
- les écarts sont conservés, pas effacés ;
- une seule correction principale est attribuable aux résultats ;
- citations et refus restent vérifiables ;
- l'agent reste sans boucle libre ni effet externe ;
- la décision peut rester négative.

## Gate renforcé M4

Les résultats essentiels sont reproduits par un tiers et la décision résiste au
nouveau lot ou est explicitement révisée.
