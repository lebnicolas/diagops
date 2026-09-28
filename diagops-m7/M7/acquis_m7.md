# État attendu du projet DiagOps — fin du module 7

Cette fiche décrit les acquis à vérifier après réalisation et revue. Elle
n'atteste ni qu'une promotion a suivi M7 ni que le kit distribué remplit déjà
les livrables demandés.

## Résumé

L'architecture RAG-agentique de DiagOps a été évaluée sous contraintes de
performance, sécurité, coût, souveraineté et réversibilité. Une cible et un plan
de migration sont documentés.

## Acquis techniques

- cartographie des flux et frontières de confiance ;
- registre des données, dépendances et permissions ;
- scénarios de panne et modes dégradés testés ;
- comparaison local/cloud/hybride ;
- exercice de portabilité ;
- red team documentée ;
- contrat d'outil à effet simulé avec approbation ;
- ADR, architecture cible et plan de rollback.
- migration exercée sur un sous-ensemble représentatif ;
- rapport de revue indépendant ;
- ADR révisés à partir des preuves de portabilité.
- entrée de veille M7 intégrée aux ADR, au registre des risques ou au plan de
  migration ;
- passage de relais réglementaire M8.

## Compétences visées, à valider

- **C2 — niveau 3 consolidé** : intégrer risques éthiques, sécurité,
  confidentialité et supervision dans une décision d'architecture ;
- **C7 — niveau 2** : évaluer une architecture et proposer une évolution
  vérifiable sous contraintes.

## Limites conservées

- aucun système externe réel n'est modifié ;
- le chemin de référence reste en lecture seule ;
- la portabilité testée sur un sous-ensemble ne garantit pas une migration
  totale ;
- le multi-agent reste optionnel et doit être justifié en M8.

## Entrées pour M8

- architecture revue et ADR ;
- politiques de données et d'outils ;
- résultats de portabilité et red team ;
- objectifs de reprise et mode dégradé ;
- coûts et risques résiduels ;
- critères qui bloquent ou autorisent une nouvelle conception ;
- dossier `veille_diagops/`, sources actualisées et points de validation
  juridique.
