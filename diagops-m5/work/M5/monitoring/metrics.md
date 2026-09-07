# Contrat de métriques M5

> État au **07/09/2026**. Source unique : `/metrics` de l'API, scrappé par Prometheus toutes les
> 15 s (`deploy/prometheus.yml`), rétention 7 jours.

## Pourquoi trois plans

Le mot « monitoring » recouvre trois choses qui tombent en panne indépendamment. Un service à
100 % de disponibilité qui cite des documents inexistants est **vert sur le plan service et cassé
sur le plan réponse** — c'est précisément la panne que le starter ne pouvait pas voir, puisqu'il
n'exposait que trois gauges statiques.

Une métrique sans seuil ni responsable n'est pas une métrique : c'est une courbe. Chaque ligne
ci-dessous porte les cinq champs exigés par le brief online — source, fréquence, seuil,
destinataire, action.

## Plan service — le service répond-il ?

| Métrique | Type | Fréquence | Seuil d'alerte | Responsable | Action attendue |
|---|---|---|---|---|---|
| `diagops_ready` | gauge | 15 s | `0` pendant 1 min | Astreinte exploitation | Diagnostiquer le manifeste de release, restaurer la dernière version saine |
| `diagops_http_requests_total{status=~"5.."}` | counter | 15 s | taux 5xx > 5 % sur 5 min | Astreinte exploitation | Lire les logs applicatifs, décider rollback ou correctif |
| `diagops_http_request_duration_seconds` | histogram | 15 s | p95 > 0,5 s sur 5 min | Astreinte exploitation | Vérifier la charge et les limites de ressources du conteneur |
| `diagops_http_requests_total` (débit) | counter | 15 s | chute > 80 % vs 1 h avant | Astreinte exploitation | Vérifier que le trafic arrive — panne amont probable |
| `diagops_dependency_up` | gauge | 15 s | `0` pendant 1 min | Astreinte exploitation | Scénario « serveur de génération indisponible » du game day |

## Plan retrieval — cherche-t-il vraiment ?

| Métrique | Type | Fréquence | Seuil d'alerte | Responsable | Action attendue |
|---|---|---|---|---|---|
| `diagops_index_valid` | gauge | 15 s | `0` immédiat | Astreinte exploitation | **Rollback de l'index** vers la dernière version saine |
| `diagops_index_documents` | gauge | 15 s | ≠ 7 sans livraison déclarée | Responsable corpus | Vérifier le rapport d'ingestion : un document a été retiré ou refusé |
| `diagops_retrieval_empty_total` | counter | 15 s | > 30 % des requêtes sur 15 min | Responsable corpus | Index dégradé ou corpus inadapté aux questions posées |
| `diagops_retrieval_results` | histogram | 15 s | médiane < 1 sur 15 min | Responsable corpus | Le top-k ne se remplit plus : vérifier les postings |
| `diagops_retrieval_duration_seconds` | histogram | 15 s | p95 > 0,1 s sur 5 min | Astreinte exploitation | Scénario « latence du retrieval multipliée » |
| `diagops_retrieval_filtered_documents_total` | counter | 15 s | variation brusque | Responsable sécurité | Un changement de rôles a modifié le périmètre visible |

## Plan réponse — répond-il correctement ?

| Métrique | Type | Fréquence | Seuil d'alerte | Responsable | Action attendue |
|---|---|---|---|---|---|
| `diagops_citations_total{resolvable="false"}` | counter | 15 s | **> 0, immédiat** | Astreinte exploitation | Une citation ne se résout pas dans l'index : rollback |
| `diagops_refusals_total` | counter | 15 s | > 50 % des requêtes sur 15 min | Responsable corpus | Abstention massive : index vide, corpus hors sujet, ou dégradation |
| `diagops_refusals_total` (chute) | counter | 15 s | ≈ 0 alors que le taux vide monte | Responsable qualité | Le système répond là où il devrait s'abstenir — plus grave que l'inverse |
| `diagops_restricted_citations_total` | counter | 15 s | **> 0, immédiat** | Responsable sécurité | Un document restreint a été cité hors rôle. Incident de sécurité, pas de qualité |
| `diagops_search_errors_total` | counter | 15 s | > 0 sur 5 min | Astreinte exploitation | Aucun index actif servi |

## Ce qui n'est pas mesuré, et pourquoi

**Revue humaine et coût** : le brief les cite au plan réponse. Aucun des deux n'a d'objet ici —
il n'y a ni boucle de validation humaine (elle arrive en M6) ni appel facturé (le retrieval est
local et déterministe). Les compter à zéro donnerait deux courbes plates qu'on finirait par ne
plus regarder.

**Validation de schéma** : la réponse est produite par un modèle Pydantic, donc conforme au
contrat `DiagOpsGroundedAnswer` par construction. Une entrée malformée est rejetée en 422 et
comptée par `diagops_http_requests_total{status="422"}`.

**Ressources conteneur** (CPU, mémoire) : non exposées par l'application. Les limites sont
posées dans `compose.yaml` ; leur observation demanderait un cAdvisor ou un node-exporter, hors
périmètre du brief 1. Signalé comme trou connu plutôt que simulé.

## Minimisation des traces

Règle tenue et testée (`tests/test_observability.py`) :

- **aucune donnée métier dans un label** — pas de texte de question, pas d'extrait de document,
  pas d'identifiant d'utilisateur. Un test vérifie qu'une question contenant un numéro et le mot
  « patient » n'apparaît nulle part dans l'exposition ;
- **le chemin HTTP est réduit au motif de route**, les autres sont agrégés sous `other` — sinon
  une URL forgée devient une série temporelle, et un attaquant choisit ce qu'on stocke ;
- **les extraits de citation sont des références**, pas du contenu : révision et nombre de tokens
  indexés, jamais le texte du document ;
- **rétention 7 jours** côté Prometheus, sur un volume dédié.

Le seul label à cardinalité ouverte est `role`, borné à quatre valeurs connues par le contrat
d'admission du corpus.
