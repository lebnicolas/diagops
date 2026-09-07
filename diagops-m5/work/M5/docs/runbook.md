# Runbook DiagOps M5

> État au **07/09/2026**. Toutes les commandes de ce document ont été exécutées — aucune n'est
> écrite de mémoire. Les sorties citées sont celles obtenues sur le poste de travail.
> Périmètre déclaré de la release : `pedagogical_preproduction_only`. Ce runbook ne décrit pas
> une exploitation de production réelle.

Racine des commandes : `diagops-m5/work/M5`, sauf mention contraire.

## Responsables et escalade

| Rôle | Périmètre | Alerte qui le concerne |
|---|---|---|
| **Astreinte exploitation** | disponibilité, latence, erreurs, intégrité de l'index | `diagops_ready`, `diagops_index_valid`, 5xx, p95 |
| **Responsable corpus** | contenu, révisions, admission, pertinence du retrieval | `diagops_index_documents`, `retrieval_empty`, `refusals` |
| **Responsable sécurité** | cloisonnement par rôle, actifs restreints | `diagops_restricted_citations_total`, filtrage par rôle |
| **Responsable qualité** | cohérence des réponses, abstention | chute des refus à taux de vide élevé |

**Escalade** : toute alerte à seuil « immédiat » (`diagops_index_valid = 0`,
`citations{resolvable="false"} > 0`, `restricted_citations > 0`) va à l'astreinte sans délai.
Une citation restreinte hors rôle est un **incident de sécurité**, pas une dégradation de
qualité : elle est escaladée au responsable sécurité en parallèle, pas après.

En formation, ces quatre rôles sont tenus par la même personne. Ils restent distingués parce que
c'est la **nature** de la décision qui change, pas seulement son destinataire.

## Démarrage et test de fumée

```bash
docker compose -f deploy/compose.yaml up -d --build
```

La chaîne est ordonnée par dépendances : `indexer` → `gate` → `api` → `prometheus`. L'API ne
démarre **que** si le gate est passé.

Test de fumée, dans cet ordre :

```bash
curl -fsS http://127.0.0.1:8000/health/live      # {"status":"live"}
curl -fsS http://127.0.0.1:8000/health/ready     # {"status":"ready", ..., "index":"lexical-dfb8faf0c9b4"}
curl -fsS http://127.0.0.1:8000/version          # les 6 versions liées + 4 checksums
curl -fsS -X POST http://127.0.0.1:8000/search \
  -H 'Content-Type: application/json' \
  -d '{"question":"vibration de la pompe","role":"technicien"}'
curl -fsS http://127.0.0.1:8000/metrics | grep diagops_index_valid
```

Attendu : `ready` sur `lexical-dfb8faf0c9b4`, 3 citations résolubles avec `abstained: false`,
`diagops_index_valid 1`.

Vérifier que la supervision voit le service :

```bash
curl -s "http://127.0.0.1:9090/api/v1/targets?state=active" | grep -o '"health":"[a-z]*"'
```

Attendu : `"health":"up"`. Compter **jusqu'à 30 s** après le démarrage : un `unknown` immédiat est
normal, Prometheus n'a pas encore scrappé.

## Arrêt contrôlé

```bash
docker compose -f deploy/compose.yaml down          # conserve les volumes
docker compose -f deploy/compose.yaml down -v       # DÉTRUIT index actif, historique et TSDB
```

> `-v` supprime `diagops_artifacts`, donc **l'index actif et tout l'historique de rollback**.
> Ne jamais l'employer pour un redémarrage d'exploitation. Réservé au repartir-de-zéro délibéré.

`stop_grace_period` est à 15 s sur l'API, et uvicorn a un `--timeout-graceful-shutdown` de 10 s :
les requêtes en cours se terminent avant la coupure.

## Construction et publication d'un index

Quatre étapes, dans cet ordre. **Aucune ne publie sans la précédente.**

```bash
# 1. Ingestion : admission + détection de changements
python pipelines/ingest.py \
  --manifest ../../data_pack/2026-S1/knowledge/manifest.csv \
  --documents ../../data_pack/2026-S1/knowledge/documents \
  --active artifacts/runtime/index.json \
  --output artifacts/candidates/local/index.json \
  --report artifacts/candidates/local/ingest_report.json
```

Trois issues : `unchanged` (rien à faire, **s'arrêter là**), `rebuild` (continuer),
`rejected` (ne rien publier, lire les refus).

```bash
# 2. Mesure du candidat
python pipelines/measure_release.py \
  --index artifacts/candidates/local/index.json \
  --questions ../../data_pack/2026-S1/rag_eval/questions.jsonl \
  --inherit-abstention-from ../../data_pack/2026-S1/reference_runs/m4_for_m5/evaluation/metrics_calibration.json \
  --output artifacts/candidates/local/metrics.json

# 3. Gate
python pipelines/evaluate_release.py \
  --index artifacts/candidates/local/index.json \
  --metrics artifacts/candidates/local/metrics.json \
  --gates configs/gates.json \
  --output artifacts/candidates/local/gate_report.json

# 4. Publication — archive l'index remplacé avant de publier
python pipelines/promote_index.py \
  --candidate artifacts/candidates/local/index.json \
  --active artifacts/runtime/index.json \
  --history artifacts/history \
  --gate artifacts/candidates/local/gate_report.json
```

**Atomicité observée** : `promote_index.py` écrit dans un fichier temporaire du même répertoire
puis appelle `replace()`. Aucun lecteur ne voit un index à moitié écrit. L'archive est créée
**avant** la publication, et n'est jamais réécrite si elle existe déjà — un point de retour n'est
pas un cache.

**Ce que le gate ne couvre pas** : `correct_abstention_rate` est héritée de la référence M4, pas
mesurée sur le candidat. Le rapport de gate l'affiche (`checks_provenance`). Ne pas lire un gate
`passed` comme une validation de l'abstention.

## Incident et rollback

### Conditions de décision

| Signal | Décision |
|---|---|
| `diagops_index_valid = 0` | **rollback immédiat** de l'index |
| `citations{resolvable="false"} > 0` | **rollback immédiat** |
| `restricted_citations_total > 0` | rollback + escalade sécurité |
| `retrieval_empty` > 30 % sur 15 min | diagnostic corpus d'abord, rollback si récent |
| `diagops_ready = 0` > 1 min | diagnostic du manifeste de release |

### Procédure

```bash
# 1. Constater
curl -s http://127.0.0.1:8000/health/ready
curl -s http://127.0.0.1:8000/metrics | grep diagops_index_valid

# 2. Lister ce vers quoi on peut revenir — avant de choisir
python pipelines/rollback_index.py --list \
  --active artifacts/runtime/index.json --history artifacts/history

# 3. Restaurer une version NOMMÉE
python pipelines/rollback_index.py lexical-dfb8faf0c9b4 \
  --active artifacts/runtime/index.json --history artifacts/history

# 4. Vérifier — les quatre contrôles, pas seulement le premier
curl -s http://127.0.0.1:8000/health/ready
curl -s -X POST http://127.0.0.1:8000/search -H 'Content-Type: application/json' \
  -d '{"question":"vibration de la pompe","role":"technicien"}'
curl -s http://127.0.0.1:8000/metrics | grep diagops_index_valid
docker compose -f deploy/compose.yaml ps | grep api      # attendre `healthy`
```

Dans la stack conteneurisée, préfixer par
`docker compose -f deploy/compose.yaml run --rm --entrypoint sh gate -c "..."`.

Il n'y a **pas** de « dernière version connue » automatique : la version est un argument. Sous
incident, l'automatisme qui choisit seul est celui qui restaure la version qui vient de casser.

### Objectifs de reprise et ce qui a été mesuré

| Étape | Objectif | Mesuré le 07/09 |
|---|---|---|
| Détection | < 2 min | **3 s** (applicative) |
| Décision | < 5 min | 75 s |
| Restauration | < 10 min | **4 s** après décision |
| Perte de données | aucune | aucune |

> **Le conteneur est le dernier informé.** L'application détecte en 3 s, Prometheus en ~18 s,
> Docker passe `unhealthy` en ~50 s (`interval: 10s` × `retries: 5`). Pendant ces 50 secondes,
> l'orchestrateur croit le service sain alors qu'il répond `503`. **Ne jamais adosser une alerte
> à l'état du conteneur** : elle arrive dix-sept fois trop tard.

Détail complet : `docs/rapport_rollback.md`.

## Réindexation après changement de corpus

```bash
python pipelines/ingest.py ... --report artifacts/candidates/local/ingest_report.json
```

Lire le rapport **avant** de continuer :

- `revision_conflicts` non vide → un document a changé **à révision constante**. Ne pas publier :
  deux contenus différents porteraient la même identité dans toutes les traces. Faire corriger la
  révision au manifeste.
- `refusals` non vide → contrat d'admission non respecté (sensibilité, statut, rôles, checksum,
  remplacement d'un document encore actif).
- `added` / `removed` / `modified` → poursuivre le cycle de publication normal.

Après publication, mettre à jour `docs/contrat_versions.md` : `index_version`, `build_version`,
`corpus_version` et le commit de code.

## Sauvegarde, restauration et rotation des secrets

### Sauvegarde

L'état durable tient dans deux volumes Docker :

```bash
docker run --rm -v deploy_diagops_artifacts:/a -v "$PWD/backup:/b" alpine:3 \
  tar czf /b/artifacts-$(date +%Y%m%d).tgz -C /a .
```

`diagops_artifacts` porte l'index actif et **tout l'historique de rollback** : c'est le volume
critique. `diagops_prometheus` porte les séries (rétention 7 jours) — sa perte coûte l'historique
d'observation, pas la capacité à servir.

Le corpus et les jeux d'évaluation vivent dans `data_pack/`, monté **en lecture seule** et
versionné dans le dépôt : rien à sauvegarder de ce côté.

### Restauration

```bash
docker run --rm -v deploy_diagops_artifacts:/a -v "$PWD/backup:/b" alpine:3 \
  tar xzf /b/artifacts-AAAAMMJJ.tgz -C /a
```

Puis rejouer le test de fumée en entier. Une restauration non vérifiée n'est pas une restauration.

### Secrets

**Il n'y a aujourd'hui aucun secret dans cette stack** — pas de clé d'API, pas de mot de passe,
pas de jeton. Le retrieval est local et déterministe, Prometheus est sans authentification sur un
réseau local.

C'est un fait à vérifier, pas à supposer : `tests/test_security_gates.py` balaie les artefacts
produits à la recherche de motifs de clés (AWS, GitHub, `sk-`, clés privées, `password=`), et la
CI le rejoue à chaque livraison.

Le jour où un secret entre (serveur de génération distant, registre privé) :

1. jamais dans l'image ni dans le dépôt — variable d'environnement ou fichier monté ;
2. rotation par redémarrage du service concerné, pas par reconstruction d'image ;
3. rejouer le balayage de secrets sur les artefacts avant publication ;
4. l'inscrire au `docs/contrat_versions.md` comme unité versionnée à part entière.

## Traces, accès et rétention

| Quoi | Où | Rétention | Accès |
|---|---|---|---|
| Métriques | Prometheus, volume `diagops_prometheus` | **7 jours** | réseau local, sans authentification |
| Journaux applicatifs | `docker compose logs` | cycle de vie du conteneur | poste opérateur |
| Rapports de gate et de mesure | `artifacts/candidates/` | conservés avec le candidat | dépôt et artefacts CI (14 j) |
| Historique d'index | `artifacts/history/` | non purgé automatiquement | volume Docker |

### Ce qui n'est jamais journalisé

- **le texte des documents** — l'index ne porte que des empreintes de termes, et les extraits de
  citation sont des références (révision, nombre de tokens) ;
- **la question posée** — aucune donnée métier dans un label de métrique. Vérifié par test : une
  question contenant un numéro et le mot « patient » n'apparaît nulle part dans l'exposition ;
- **les chemins d'URL arbitraires** — réduits au motif de route, le reste agrégé sous `other`.
  Sinon une URL forgée devient une série temporelle, et l'attaquant choisit ce qu'on stocke.

Le seul label à cardinalité ouverte est `role`, borné à quatre valeurs par le contrat d'admission.

### Points ouverts

- **Prometheus est exposé sans authentification** sur le port 9090. Acceptable en laboratoire
  local, à ne pas reconduire hors de ce périmètre.
- **`artifacts/history/` n'est pas purgé.** À ce volume c'est sans effet ; une politique de
  rétention devra être posée avant tout usage prolongé — en gardant à l'esprit qu'une purge
  supprime des points de retour.
