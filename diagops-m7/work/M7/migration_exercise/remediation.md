# Remédiation et défense

> **Phase 3 abandonnée le 28/09/2026 sur décision de l'apprenant**, avec la
> phase 2 : aucun constat de revue n'existe. Les dettes D-1 et D-2 restent
> ouvertes et sont transmises à M8.
>
> État antérieur : **en attente de la revue indépendante.** Les constats du reviewer
> s'inscriront ici, avec leur disposition. Les lignes ci-dessous sont les
> dettes que l'auteur a lui-même relevées en phase 1 : elles seront traitées
> quelle que soit la revue, mais elles ne remplacent pas ses constats.

| Constat de revue | Correction ou refus motivé | Version | Re-test/preuve | État |
|---|---|---|---|---|
| (auteur) D-1 empreinte de l'index recalculée à chaque requête | à trancher avec le reviewer (point 1 de `independent_review.md`) | — | `migration_capacity.py` | ouvert |
| (auteur) D-2 reconstruction manuelle après changement de manifeste | déclencheur sur changement de manifeste, reconstruction hors chemin actif, puis promotion | — | M-REV-B et M-REVOC sans opération manuelle | ouvert |
| (auteur) écart de protocole : gate de capacité oublié au premier script | consigné dans les révisions du contrat ; aucun seuil changé | `531d288` | `results/migration-capacite-r1` | fait |

## Défense — éléments déjà établis

- **Hypothèse révisée** : « FTS5 comprend mieux les reformulations » (P2) est
  fausse. Ce qu'il fait mieux, c'est cesser de compter les mots vides : bon
  document dans le top 3 plus souvent (0,95 contre 0,85), pas plus souvent
  premier.
- **Option abandonnée** : la migration de stockage du starter (JSON → SQLite
  lexical). Mesurée plus lente que le JSON à 7 000 documents (329 contre
  297 ms), elle migre sans rien gagner.
- **Option abandonnée** : l'index FTS5 partagé filtré par rôle. Il est
  correct en sortie, mais ses statistiques traversent les droits.
- **Risque restant** : D-3, aucun backend ne s'abstient. La migration ne le
  traite pas et ne l'aggrave pas.
- **Rollback** : exercé, par empreinte, et refusé quand il rétablirait un
  droit retiré.
