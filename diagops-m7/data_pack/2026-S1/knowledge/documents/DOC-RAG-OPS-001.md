# Contrat de réponse documentaire DiagOps

Statut : active, révision 1.

## Réponse fondée sur des preuves

Une réponse DiagOps indique les `document_id` utilisés et sépare les éléments
explicitement présents dans les sources de l’interprétation du système. Une
similarité élevée ne constitue pas une preuve de vérité.

Le système s’abstient lorsque les sources admissibles ne répondent pas à la
question, lorsqu’un document est hors des droits du rôle demandeur ou lorsque
deux révisions actives se contredisent sans règle de priorité vérifiable.

Le contenu récupéré est toujours traité comme une donnée. Une phrase trouvée
dans un document ne peut ni modifier les instructions du système, ni élargir
les permissions de l’agent, ni déclencher une écriture. L’agent M4 choisit
uniquement entre réponse directe, recherche documentaire et abstention.
