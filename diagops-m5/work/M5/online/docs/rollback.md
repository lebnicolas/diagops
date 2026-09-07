# Procédure de rollback — service de scoring

> Exécutée le 07/09/2026 : **7 secondes** de la décision au service rétabli. Voir
> `docs/rapport_livraison.md` pour les preuves.

## Principe

L'artefact est **figé dans l'image**. Il n'y a donc rien à restaurer sur disque : revenir en
arrière, c'est **redéployer un digest antérieur**. Un seul objet à suivre, une seule opération à
faire — au prix assumé qu'un changement de modèle est toujours un redéploiement.

## Avant toute livraison — créer le point de retour

```bash
docker tag deploy-scoring diagops-scoring:v1-sain
docker image inspect deploy-scoring --format '{{.Id}}'   # relever le digest
```

Sans cette étape, il n'y a pas de rollback possible : l'image précédente porte le même tag et
sera écrasée au build suivant. **C'est l'étape qu'on oublie, et c'est celle qui compte.**

## Conditions de déclenchement

| Signal | Décision |
|---|---|
| Conteneur `unhealthy` après déploiement | **rollback immédiat** |
| `diagops_model_loaded = 0` | rollback immédiat |
| `diagops_model_sklearn_conforme = 0` | rollback, puis revalidation avant toute nouvelle tentative |
| `/health/ready` rend « Artefact non conforme » | rollback — l'image livrée ne contient pas le modèle attendu |
| Taux de 5xx > 1 % sur 5 min | diagnostic 2 min, puis rollback si non résolu |
| Prédictions déviantes sans changement d'entrée | rollback, puis comparaison des checksums |

## Procédure

```bash
# 1. Constater
docker compose -f deploy/compose.yaml ps
curl -s http://127.0.0.1:8100/health/ready

# 2. Vérifier que le point de retour existe — avant de détruire quoi que ce soit
docker image inspect diagops-scoring:v1-sain --format '{{.Id}}'

# 3. Restaurer
cat > deploy/rollback.yaml <<'EOF'
services:
  scoring:
    image: diagops-scoring:v1-sain
    build: !reset null
EOF
docker compose -f deploy/compose.yaml -f deploy/rollback.yaml up -d --wait --wait-timeout 60

# 4. Vérifier — les trois contrôles, pas seulement le premier
curl -fsS http://127.0.0.1:8100/health/ready
curl -fsS -X POST http://127.0.0.1:8100/predict \
  -H 'Content-Type: application/json' -d @fenetre_temoin.json
docker compose -f deploy/compose.yaml ps
```

`build: !reset null` est indispensable : sans lui, Compose reconstruit l'image depuis le
Dockerfile et **réintroduit exactement le défaut** qu'on cherche à fuir.

## Vérification après restauration

| Contrôle | Attendu |
|---|---|
| `/health/ready` | `ready`, checksum `164d05b129ce5e41`, `sklearn_conforme: true` |
| `/predict` sur la **fenêtre témoin** | `probabilite_fabriquee: 0.114902` — **exactement** |
| `docker compose ps` | `scoring` et `prometheus` en `healthy` |
| `diagops_model_loaded` | `1` |

La fenêtre témoin (`M4-CAL-001`) est le contrôle qui compte : un service qui répond `200` n'est
pas un service qui répond **juste**. Une probabilité différente au même artefact signalerait un
problème d'environnement, pas de modèle.

## Après le rollback

1. **Ne pas relancer la livraison à l'identique.** Le défaut est dans le candidat, pas dans la
   chaîne.
2. Rejouer `pytest` localement sur le candidat : les tests d'artefact attrapent une corruption
   avant tout déploiement.
3. Comparer les checksums — celui de l'image livrée et celui attendu par `src/scoring.py`.
4. Consigner l'incident au `journal_bord.md` avec les temps mesurés.

## Limite connue

Le point de retour est un **tag local**. Il ne survit ni à un `docker image prune`, ni à un
changement de poste. Sur un déploiement réel, le digest doit vivre dans un registre — c'est la
première chose à ajouter avant tout usage hors laboratoire.
