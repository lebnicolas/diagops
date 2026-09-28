# Exercice sur table — outil à effet fictif

Aucun client réseau, credential, ticket réel ou commande industrielle. Le contrat JSON décrit un futur outil ; il n'est pas enregistré dans l'agent M6 et aucun exécuteur n'est fourni.

Jouer les séquences suivantes à deux, avec identités fictives :
1. Demande → contrôle du rôle → aperçu du contenu exact → approbation humaine liée au hash → reçu fictif.
2. Refus, expiration ou changement du contenu : aucune exécution, nouvelle approbation nécessaire.
3. Rejeu de la même clé/contenu : même reçu, pas de doublon ; même clé/contenu différent : refus.
4. Annulation avant effet ; après effet fictif, compensation journalisée sans effacer l'historique.

Consigner acteur, état initial/final, décision et raison, sans secret ni donnée personnelle. Séparer approbation du scénario de la permission d'activer un outil réel, qui reste hors module.
