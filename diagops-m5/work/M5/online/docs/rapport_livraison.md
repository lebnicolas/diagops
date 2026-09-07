# Rapport de livraison — service de scoring, 07/09/2026

> Étape 6 du brief online : exécuter une livraison candidate, conserver les preuves, documenter
> une procédure de restauration. **Tout ce qui suit a été exécuté.**

## Ce qui a été livré

| | |
|---|---|
| Service | détecteur de provenance M4 derrière une API instrumentée |
| Image | `deploy-scoring`, `sha256:8d8ffaef4e5ebdb5ca9b725…` |
| Modèle embarqué | `164d05b129ce5e41…`, gelé le 31/08/2026 |
| Stack | `scoring` (port 8100) + `prometheus` (port 9190) |
| Tests | **18 passés** |

Ports décalés de la stack RAG (8000 / 9090) : les deux services coexistent sur le même poste
sans se marcher dessus.

## Chaîne de livraison

```
tests → build image → up --wait (healthcheck bloquant) → test de fumée → scrape Prometheus
```

`--wait` est ce qui rend la livraison **bloquante** : Compose ne rend la main que lorsque le
healthcheck passe. Et ce healthcheck interroge `/health/ready`, pas `/health/live` — le service
n'est déclaré sain que si le modèle est **chargé, identifié par son checksum, et exécuté sous la
version de scikit-learn du gel**. Un conteneur qui démarre n'est pas un service qui sert.

## Preuves de la livraison nominale

| Contrôle | Résultat |
|---|---|
| `GET /health/ready` | `ready`, checksum `164d05b129ce5e41`, `sklearn_conforme: true` |
| `POST /predict` (fenêtre `M4-CAL-001`) | `probabilite_fabriquee: 0.114902`, `provenance_predite: réelle` |
| Reproductibilité poste ↔ conteneur | **probabilité identique au chiffre près** |
| Prometheus, cible `diagops-scoring` | `up` |
| `diagops_model_loaded` | `1` |
| `diagops_model_sklearn_conforme` | `1` |
| Équivalence des features avec M4 | 30 × 19 comparées, **zéro écart** |
| Non-régression du modèle | VP=10, FP=0, FN=1 — identique à M4 |

## Livraison d'un candidat défectueux, et ce qui l'a arrêté

Pour vérifier que la chaîne bloque vraiment, un artefact corrompu a été introduit dans l'image
(10 octets réécrits au milieu du `.joblib`), puis livré comme un candidat normal.

**Deux barrières indépendantes ont fonctionné.**

**1. Les tests** — `test_l_artefact_est_celui_du_gel` échoue avant tout déploiement :

```
ValueError: Artefact non conforme : 630004cc8865a7d08f73903bd51c3848
            attendu 164d05b129ce5e4107cdc27279bc198c
```

En CI, la livraison s'arrête là.

**2. Le healthcheck** — en supposant les tests contournés, le conteneur a été déployé quand même.
Il passe **`unhealthy` en 33 secondes**, `/health/ready` rend le détail de la non-conformité, et
Prometheus **ne démarre pas** : sa dépendance `service_healthy` n'est jamais satisfaite.

> Le point à retenir : la seconde barrière n'est pas une redondance de confort. Un artefact peut
> être remplacé **après** la CI — pendant un build manuel, dans un registre, par une erreur de
> tag. Vérifier l'identité au démarrage est le seul contrôle qui porte sur ce qui tourne
> réellement, pas sur ce qui a été testé.

## Restauration

Le rollback consiste à **redéployer un digest antérieur** — l'artefact étant figé dans l'image,
il n'y a pas de fichier à restaurer.

```bash
docker tag deploy-scoring diagops-scoring:v1-sain   # avant toute livraison
# ... incident ...
docker compose -f deploy/compose.yaml -f deploy/rollback.yaml up -d --wait
```

où `rollback.yaml` force `image: diagops-scoring:v1-sain`.

| Étape | Mesuré |
|---|---|
| Détection du candidat défectueux | 33 s (bascule `unhealthy`) |
| **Restauration complète** | **7 s** |
| Vérification après restauration | `ready`, checksum sain, **prédiction identique à l'avant-incident** (`0.114902`) |

La vérification ne s'arrête pas au `200` de la readiness : la même fenêtre est rejouée et doit
rendre **exactement** la même probabilité. Un service qui répond n'est pas un service qui répond
juste.

## Ce qui a été conservé

- `docs/artefact.md` — entrées, sorties, paramètres, dépendances, résultats de référence ;
- `docs/registre_versions.md` — unités versionnées et déclencheurs de version ;
- `docs/metriques_et_declencheurs.md` — les cinq champs par métrique ;
- ce rapport ;
- `journal_bord.md` — chronologie datée ;
- artefacts de CI conservés 14 jours.

## Limites de cette livraison

**Un seul environnement.** Le brief demande de distinguer préproduction et production. Ici il n'y
a qu'un poste local : la distinction est **structurelle** (le healthcheck bloque la mise en
service) mais pas **topologique**. Le dire est plus honnête que de renommer un port en
« production ».

**Pas de registre d'images.** Les digests sont locaux. Un vrai registre donnerait des digests
immuables et partageables ; ici la traçabilité repose sur les tags locaux et ce document.

**Pas de dérive de distribution surveillée.** Le premier ajout à faire si ce service devait
vivre — voir `docs/metriques_et_declencheurs.md`.
