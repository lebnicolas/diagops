# Reprise et mode dégradé

## Service minimal et actions interdites en mode dégradé

Le mode dégradé est déclenché par une source indisponible, un index périmé, un
document en quarantaine ou un budget dépassé. Dans ce mode :

- **maintenu** : lecture des outils structurés (fiche, événements, historique,
  rapport), qui ne dépendent pas du corpus. RES-01 montre qu'ils portent déjà
  7 réponses sur 18 quand le corpus manque ;
- **maintenu avec mention** : recherche documentaire sur les documents sains si
  un seul est en quarantaine (cible ADR-0004). La réponse signale que le corpus
  est incomplet ;
- **interdit** : toute réponse procédurale sans document cité ; toute
  promotion d'index ; toute action, même simulée (l'outil fictif reste
  `previewed`, un humain reprend hors système) ; tout changement de politique
  pour « débloquer » la situation.

## Objectifs de reprise

Fixés à partir du besoin, pas des mesures. DiagOps assiste un technicien qui
dispose toujours des procédures papier et de son responsable : une
indisponibilité ralentit le diagnostic sans l'empêcher.

| Composant | RTO cible | RPO cible | Justification | Mesuré sur ce poste |
|---|---|---|---|---|
| Index de retrieval | 15 min | 0 (reconstruit depuis le manifeste) | l'index est dérivé : aucune donnée propre | reconstruction 12 ms ; retour arrière 14 ms (RES-08) |
| Manifeste et corpus | 4 h | dernier commit relu | c'est la source de vérité ; une perte oblige à revalider chaque révision | non mesuré : aucune sauvegarde hors poste n'existe |
| Tables structurées | 4 h | dernière livraison du data pack | livrées par l'exploitation | non mesuré |
| Traces | 24 h | 24 h (proposé) | l'audit tolère une journée de trou, pas une perte silencieuse | non mesuré : pas de sauvegarde déclarée |
| Processus agent | 5 min | sans objet | sans état persistant | redémarrage non chronométré en M7 |

Les 12 et 14 ms ne sont pas des engagements : ils mesurent un corpus de
7 documents sur un poste de développement. Ils montrent seulement que la
reprise de l'index n'est pas le point dur. **Le point dur est le manifeste**,
qui n'a aucune sauvegarde hors du dépôt Git.

## Sauvegarde et source reconstructible

| Élément | Version et empreinte | Reconstruction |
|---|---|---|
| Manifeste | `3b3dfb356eee…` (release M5 `knowledge-3b3dfb356eee`) | aucune : c'est la source. Sauvegarde = dépôt Git + copie hors poste (à créer) |
| Export du corpus | `12ea939dde70…` en LF (`results/decouverte-r2`) | `python lab.py --output <nouveau dossier>` |
| Index SQLite / FTS5 | non versionnés (`.gitignore`) | `migrate()` / `migrate_fts5()` depuis l'export |
| Référence M6 | `release_manifest.json` `891140ba7ad4…` | `scripts/replay_reference.py` |

## Procédure

Déclencheur : l'un des signaux de `m5_for_m6/operations/restauration.md`, plus
les signaux M7 (index périmé, document en quarantaine, conflit de révisions).
Responsable : l'**exploitant d'astreinte** (rôle), qui consigne chaque étape.

1. Horodater, geler toute promotion en cours.
2. Identifier la couche : source (manifeste, documents), index dérivé ou
   processus.
3. **Index dérivé** : repointer `active.json` vers la dernière version saine
   avec son empreinte attendue (`activate(..., expected_sha256=...)`). Un refus
   (« source de reprise altérée ») interdit ce retour : passer à 4.
4. **Reconstruction** : réexporter depuis le manifeste, reconstruire, rejouer
   la calibration et comparer au rapport de référence.
5. **Source altérée** : restaurer le manifeste et les documents depuis Git (un
   commit relu), puis étape 4.
6. **Contrôle des permissions après reprise** : rejouer les 11 sondes du
   document restreint pour les rôles `public` et `technicien`
   (`scripts/portability_fts5.py`, bloc `restricted_leaks`). Toute valeur non
   nulle bloque le retour nominal.
7. Retour nominal : calibration identique à la référence, 0 fuite, décision
   consignée au journal.

## Durée constatée et comparaison

| Essai | Durée | Données perdues | Écart aux objectifs |
|---|---|---|---|
| RES-08 retour arrière du banc | 14 ms | aucune | sous l'objectif |
| RES-08 reconstruction complète | 12 ms, export identique octet pour octet | aucune | sous l'objectif |
| RES-01 restauration du manifeste et relecture | 16 ms | aucune | sous l'objectif, mais sur une copie : la restauration réelle dépend d'une sauvegarde qui n'existe pas |
| RES-07 révocation | effective **seulement** après rechargement ou reconstruction | aucune | **objectif non atteint** : rien ne déclenche la reconstruction |

Le `recovery_ms` du banc mesure la reprise d'un petit index sur ce poste. Ce
n'est pas un engagement de disponibilité. Le fichier SQLite corrompu reste dans
le dossier de résultat pour inspection. Chaque nouvelle exécution utilise un
nouveau dossier.
