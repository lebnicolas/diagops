# État du projet DiagOps — fin du module 4

## Résumé

DiagOps dispose d'un dossier de conception fondé sur des évaluations gelées.
Le projet sait distinguer ce qu'apportent le modèle simple, le retrieval et la
génération citée par rapport à leurs baselines.

## Acquis techniques

- cible de modélisation et conséquences d'erreur explicites ;
- baseline par règles et candidats comparés ;
- corpus documentaire versionné par manifeste ;
- jeux de calibration et de test séparés ;
- baselines sans retrieval, lexicale et vectorielle ;
- contrat de citation et d'abstention ;
- agent limité à une action sans effet externe ;
- threat model et matrice de décision.
- résultats sur un lot inédit ;
- rapport de reproduction indépendant ;
- correction mesurée et décision révisée.
- dossier de veille M0-M4 consolidé : sources, journal, analyse AI Act, radar et
  recommandations d'architecture ;
- passage de relais réglementaire M5 avec décisions et points ouverts.

## Compétences acquises

- **C1 — niveau 2** : constituer un jeu d'évaluation relié au besoin, en
  documenter couverture, provenance et limites ;
- **C2 — niveau 3** : analyser les menaces et risques sociétaux, proposer des
  atténuations et énoncer le risque résiduel ;
- **C4 — niveau 1** : comparer scientifiquement plusieurs options et justifier
  un choix ou un non-déploiement.

## Limites conservées

- une donnée réelle n'est pas nécessairement correcte ;
- une bonne performance sur les données synthétiques ne prouve pas une
  performance industrielle ;
- une citation ne prouve pas que la réponse interprète correctement la source ;
- l'agent M4 ne boucle pas et ne peut agir sur aucun système.

## Entrées pour M5

M5 repart d'un état formateur comprenant :

- code et configurations retenus ;
- corpus et index versionnés ;
- jeux d'évaluation gelés ;
- résultats et seuils d'acceptation ;
- contrat de réponse citée et de refus ;
- traces de l'agent à une étape ;
- risques, décisions et conditions de non-déploiement ;
- dossier `veille_diagops/`, dernière entrée datée et validations juridiques
  encore nécessaires.

M5 ne modifie pas silencieusement ces baselines : il les place dans une chaîne
de livraison, les observe et prouve qu'un rollback est possible.
