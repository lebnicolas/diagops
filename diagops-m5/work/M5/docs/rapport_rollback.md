# Rapport de rollback — incident contrôlé du 07/09/2026

> Scénario joué : **index partiellement corrompu**, l'un des six du brief 2.
> Le rollback a été **exécuté**, pas décrit. Tous les temps ci-dessous sont mesurés.

## Ce qui manquait avant

Le compose publiait l'index par un `cp candidat actif`. La publication était atomique, mais
**l'index sain disparaissait au moment même où il devenait le seul recours**. Il n'y avait rien
vers quoi revenir : la procédure de retour arrière était inapplicable, quoi qu'en dise un runbook.

Deux pipelines ont été ajoutés avant de pouvoir jouer l'incident :

- `pipelines/promote_index.py` — archive l'index remplacé sous `history/index-<version>.json`
  **avant** de publier, et ne réécrit jamais une archive existante : un point de retour n'est pas
  un cache ;
- `pipelines/rollback_index.py` — restaure une version **explicitement nommée**. Pas de « dernière
  version connue » implicite : sous incident, l'automatisme qui choisit seul est celui qui
  restaure la version qui vient de casser. L'archive est revérifiée avant remise en service —
  une archive corrompue restaurée sous incident transforme une panne en deux pannes.

## Chronologie

| Horodatage (UTC) | Δ | Événement |
|---|---|---|
| 06:18:17 | T0 | **Injection** — postings effacés dans l'index actif, en simulant une corruption disque après publication |
| 06:18:20 | **T+3 s** | **Détection applicative** — `/health/ready` rend `503 index actif sans postings exploitables`, `diagops_index_valid` passe à `0` |
| ~06:18:35 | ~T+18 s | **Détection supervision** — Prometheus rend `diagops_index_valid = 0` au scrape suivant |
| ~06:19:07 | ~T+50 s | **Détection orchestrateur** — le conteneur passe `unhealthy` |
| 06:19:32 | T+75 s | **Décision** — restaurer `lexical-dfb8faf0c9b4` après consultation de l'historique |
| 06:19:36 | **T+4 s après décision** | **Restauration vérifiée** — `/health/ready` rend `200` sur `lexical-dfb8faf0c9b4` |

## Tenue des objectifs

| Objectif formateur | Cible | Mesuré | Verdict |
|---|---|---|---|
| Détection | < 2 min | **3 s** (applicative), 18 s (supervision) | tenu |
| Décision | < 5 min | **75 s** | tenu |
| Restauration | < 10 min | **4 s** après décision, 79 s depuis l'injection | tenu |
| Perte de données | aucune | **aucune** — l'index corrompu n'a écrasé aucune archive | tenu |

## Trois observateurs, trois temps — et ce que ça change

C'est le résultat le plus utile de l'exercice. Le même incident est vu à **3 s**, **18 s** et
**50 s** selon qui regarde :

- l'**application** sait immédiatement : elle relit l'artefact à chaque appel de readiness ;
- **Prometheus** dépend de son `scrape_interval` de 15 s ;
- **Docker** attend `interval: 10s` × `retries: 5`, soit ~50 s avant de déclarer `unhealthy`.

Conséquence opérationnelle : **une alerte adossée à l'état du conteneur arrive dix-sept fois plus
tard qu'une alerte adossée à la métrique.** Le seuil « `diagops_index_valid = 0` immédiat » du
contrat de métriques n'est pas une précaution de style — c'est le seul des trois qui tient
l'objectif de détection avec de la marge.

Le corollaire compte autant : pendant les 50 secondes où Docker croyait le service sain, l'API
répondait `503` à toute requête. **Un orchestrateur qui juge la santé plus lentement que le
service ne la dégrade continue de router du trafic vers un service cassé.** Réduire `retries` à
2 ramènerait la bascule à ~20 s ; c'est l'arbitrage à instruire — un healthcheck plus nerveux
redémarre aussi plus vite sur un faux positif.

## Vérification après restauration

| Contrôle | Résultat |
|---|---|
| `/health/ready` | `200`, index `lexical-dfb8faf0c9b4` |
| `POST /search` (technicien, « vibration de la pompe ») | 3 citations résolubles, `abstained: false` |
| `diagops_index_valid` (API) | `1` |
| `diagops_index_valid` (Prometheus) | `1` |
| Conteneur API | `healthy` |

La version restaurée est **la même que celle publiée avant l'incident** : le contenu documentaire
n'ayant pas changé, `index_version` est identique. C'est le comportement voulu — l'empreinte
identifie un contenu, pas une exécution.

## Cause, facteurs aggravants, symptômes

**Cause** : altération de l'artefact actif après publication. Le gate ne protège que la
livraison ; il ne surveille pas ce qui arrive à l'index une fois en place.

**Facteur aggravant** : jusqu'à ce correctif, aucune archive n'existait. La cause aurait produit
une panne **irrécupérable** au lieu d'une panne de 79 secondes.

**Symptômes** : `503` sur la readiness, `diagops_index_valid` à 0, puis conteneur `unhealthy`.
Aucun symptôme sur le plan service tant que le trafic n'atteint pas `/search` — le débit et la
latence restaient nominaux pendant que le service était inutilisable.

## Remédiation

| # | Correctif | État |
|---|---|---|
| 1 | Archiver l'index avant publication (`promote_index.py`) | **fait** — sans quoi l'incident était irrécupérable |
| 2 | Restauration par version explicite, avec revérification de l'archive | **fait** |
| 3 | Alerte sur `diagops_index_valid = 0` plutôt que sur l'état du conteneur | inscrite au contrat de métriques |
| 4 | Réduire `retries` du healthcheck de 5 à 2 | **à arbitrer** — gain ~30 s de bascule contre sensibilité aux faux positifs |
| 5 | Vérification périodique de l'intégrité de l'index, hors chemin de requête | **ouvert** — aujourd'hui l'intégrité n'est constatée que si quelqu'un appelle |

Le point 5 est la limite honnête du dispositif actuel : sans trafic, la corruption reste invisible
jusqu'au prochain healthcheck. Sur ce service, le healthcheck fournit ce trafic toutes les 10 s ;
sur un service sans sonde, la panne pourrait dormir.

## Ce que l'exercice ne prouve pas

L'incident a été **injecté par nous**, à un moment choisi, sur un mécanisme connu. Il valide la
chaîne détection → décision → restauration → vérification. Il ne dit rien de la capacité à
diagnostiquer un incident dont la cause n'est pas connue d'avance — c'est l'objet du game day
contradictoire du brief 2, où le scénario est tiré par un tiers.
