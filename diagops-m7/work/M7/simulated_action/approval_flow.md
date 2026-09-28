# Exercice sur table — outil à effet fictif

Aucun client réseau, credential, ticket réel ou commande industrielle. Le
contrat `contract.json` décrit un futur outil, `request_inspection_simulated`.
Il n'est pas enregistré dans l'agent M6, dont le registre est gelé, et aucun
exécuteur n'est fourni.

## Choix de l'action

Créer une **demande d'inspection** pour un équipement fictif, à partir d'un
diagnostic. Elle a été préférée à « clôturer une intervention » (l'objet
d'ADV-001) parce qu'elle est réversible (on annule une demande, on ne
« dé-clôture » pas proprement une intervention) et parce qu'une demande
d'inspection ne commande aucun équipement. C'est l'effet le plus faible qui
exerce quand même toute la chaîne : aperçu, approbation, idempotence, reçu,
annulation, compensation.

## Automatisation de l'arbitre, pas de l'outil

L'exercice est prévu « à deux, avec identités fictives ». Joué seul, il se
réduirait à une affirmation. `tabletop.py` joue donc le rôle d'**arbitre** : un
registre en mémoire qui applique le contrat et journalise chaque décision. Ce
n'est pas l'outil. Il n'importe aucun module réseau (vérifié par analyse de
l'AST dans `tests/test_simulated_action.py`) et n'écrit que son rapport.

```bash
python simulated_action/tabletop.py --output results/action-simulee-r1
python -m unittest tests.test_simulated_action -v
```

Ajouts au contrat du starter, chacun motivé par une séquence :

| Ajout | Motif |
|---|---|
| `approver_distinct_from_requester` | sans lui, le demandeur s'approuve lui-même et l'approbation humaine n'est qu'une formalité |
| `ttl_seconds: 900` | le starter prévoit `expires` sans durée ; 15 min couvrent une relecture sans laisser une approbation dormir une journée |
| `registered_in_agent: false`, `reference_path` | rend explicite que l'outil est hors du chemin de référence |
| `preview.shown_fields`, `preview.hash` | l'approbation porte sur ce qui a été **affiché**, pas sur une requête interne que l'approbateur n'a pas vue |
| `degraded_mode` | aucune action en mode dégradé (`resilience/recovery.md`) |
| `audit_forbidden_fields` | les journaux n'emportent ni donnée personnelle ni identifiant réel |

## Séquences jouées

Acteurs fictifs : `sup-A` (demandeur), `sup-B` (approbateur), `tech-C`. Équipement
`EQ-FICTIF-001`. Horloge logique en secondes.

| # | Séquence | État initial → final | Décision et raison | Résultat |
|---|---|---|---|---|
| 1 | demande → aperçu → approbation par `sup-B` liée au hash → exécution | draft → simulated_done | approbation humaine | reçu `RECU-FICTIF-0001` |
| 2a | approbation **rejetée** puis tentative d'exécution | previewed → rejected | refus : « état rejected » | aucune exécution |
| 2b | approbation puis exécution après **901 s** | approved → expired | refus : « approbation expirée » | aucune exécution |
| 2c | approbation, puis le demandeur **modifie le motif**, puis exécution | approved → previewed | la modification fait tomber l'approbation ; refus : « état previewed » | aucune exécution |
| 2d | `sup-B` tente de réapprouver avec l'**ancien aperçu** | previewed | refus : « aperçu périmé » | il faut approuver le nouveau contenu |
| 3a | même clé, même contenu, exécuté deux fois | simulated_done | rejeu | **même reçu**, 0 doublon |
| 3b | même clé, **contenu différent** | simulated_done | refus : « même clé, contenu différent » | aucune nouvelle demande |
| 4a | annulation **avant** effet, puis tentative d'exécution | approved → cancelled | annulation | exécution refusée |
| 4b | annulation **après** effet | simulated_done → compensated | compensation : nouvelle entrée, reçu conservé | 8 entrées de journal, aucune effacée |
| 5a | `tech-C` (technicien) demande | — | refus : « rôle non autorisé » | — |
| 5b | `sup-A` approuve sa propre demande | previewed | refus : « auto-approbation » | — |

Chaque ligne du journal contient l'acteur fictif, la clé d'idempotence,
l'empreinte du contenu, la décision, la raison et la transition d'état
(`results/action-simulee-r1/report.json`). Aucune donnée personnelle ni aucun
secret.

## Ce que l'exercice ne prouve pas

- **L'identité.** `sup-A` et `superviseur_fictif` sont des arguments. Rien ne
  vérifie qui est `sup-B`. La séparation demandeur/approbateur tient dans le
  registre, pas face à un utilisateur qui se déclarerait approbateur. Même
  faiblesse que R-02 : aucun outil à effet ne peut sortir de l'exercice sur
  table tant que l'identité n'est pas authentifiée.
- **La persistance.** Le registre est en mémoire. Un vrai registre
  d'idempotence doit survivre à un redémarrage, sinon un rejeu après une panne
  crée un doublon.
- **L'effet.** Un reçu fictif n'exerce ni l'échec partiel d'un système aval
  (demande créée, reçu perdu), ni la compensation d'un effet que l'aval refuse
  d'annuler.

## Décision

L'approbation du **scénario** ne vaut pas permission d'activer un outil réel.
Celle-ci reste hors module et exige : identité authentifiée (R-02), refus
délibéré des intentions d'écriture dans le planificateur (R-05), registre
d'idempotence persistant, et un ADR dédié. L'outil reste **fictif** et **hors
du chemin de référence** (ADR-0006).
