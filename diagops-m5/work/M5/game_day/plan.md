# Plan du game day

> Rédigé le **07/09/2026**, avant toute injection. Phase 1 du brief 2.
> Ce qui est écrit ici ne se renégocie pas pendant l'incident : c'est le rôle d'un plan.

## Version saine et sauvegarde

| | |
|---|---|
| **Index sain** | `lexical-dfb8faf0c9b4`, `build-ef4b168389e9`, 7 documents |
| **Release** | `diagops-m4-reference-r1`, périmètre `pedagogical_preproduction_only` |
| **Archive de retour** | `artifacts/history/index-lexical-dfb8faf0c9b4.json` |
| **Sauvegarde préalable** | `docker run --rm -v deploy_diagops_artifacts:/a -v "$PWD/backup:/b" alpine:3 tar czf /b/artifacts-avant-gameday.tgz -C /a .` |
| **Image** | `deploy-api`, à taguer `diagops-rag:avant-gameday` **avant** l'injection |

> **La sauvegarde et le tag se font avant, pas pendant.** C'est l'étape qu'on oublie, et c'est
> celle qui décide si l'incident dure 80 secondes ou n'a pas de fin.

## Candidat

Le brief 2 prévoit une **nouvelle révision de corpus** comme candidat. La période `2026-S2`
**n'est pas publiée à ce jour** : le candidat sera donc soit fourni avec le scénario formateur,
soit construit à partir d'une modification contrôlée du corpus `2026-S1`.

Dans les deux cas la règle est la même, et elle est déjà tenue par la stack : le candidat est
construit dans `artifacts/candidates/`, passe les gates, et n'est publié dans `artifacts/runtime/`
qu'après un gate `passed`. **Un candidat recalé ne devient jamais l'index servi** — vérifié le
07/09, l'API ne démarre même pas.

## Rôles

En formation les quatre rôles sont tenus par la même personne. Ils restent distingués parce que
c'est la **nature de la décision** qui change, et qu'endosser explicitement un rôle évite de
mélanger « je constate » et « je décide ».

| Rôle | Qui | Ce qu'il fait pendant l'incident | Ce qu'il ne fait pas |
|---|---|---|---|
| **Pilote d'incident** | Nicolas Lebon | tient la chronologie, décide du rollback, annonce l'arrêt | ne diagnostique pas en même temps qu'il pilote |
| **Diagnostic** | Nicolas Lebon | lit les signaux, formule des hypothèses, les teste | ne décide pas seul de restaurer |
| **Exploitation** | Nicolas Lebon | exécute rollback, sauvegarde, vérifications | n'improvise pas hors runbook |
| **Animateur** | formateur ou pair | injecte le scénario, observe | **ne signale pas la panne** |

## Canal de décision

**Le journal `timeline.md` est le canal.** Toute décision y est écrite au moment où elle est
prise, avec son horodatage UTC, le signal qui l'a motivée et son auteur. Rien de rétroactif.

Une décision non écrite est réputée non prise : c'est ce qui empêche de reconstruire après coup
une chronologie plus flatteuse que la vraie.

## Objectifs de service et de reprise

| Étape | Objectif | Mesuré au brief 1 |
|---|---|---|
| Détection | < 2 min | 3 s |
| Décision | < 5 min | 75 s |
| Restauration | < 10 min | 4 s |
| Perte de données | aucune | aucune |

Contrat de service pendant l'exercice, issu du rapport de capacité :
**p95 < 200 ms à concurrence 8**, taux d'erreur < 1 %.

Les objectifs formateur sont **conservés tels quels**. Les temps du brief 1 les tiennent avec une
marge large, mais cet incident-là était choisi, à un moment choisi, sur un mécanisme connu. Se
donner des cibles plus dures sur un incident qu'un tiers va choisir serait de la bravade.

## Signaux attendus, par scénario

| Scénario | Premier signal | Où regarder | Délai attendu |
|---|---|---|---|
| Index corrompu | `diagops_index_valid = 0` | readiness, métriques | ~3 s |
| Corpus dégradant les citations | gate `failed` | rapport de gate | avant publication |
| Génération indisponible | `diagops_dependency_up = 0` | **signal simulé**, pas observé | immédiat |
| Latence retrieval ×N | `diagops_retrieval_duration_seconds` p95 | **pas** la latence HTTP | ~15 s |
| Configuration incompatible | readiness 503 « autre stratégie » | readiness | ~3 s |
| Alerte manquante | *aucun signal, par définition* | écart entre comportement et tableau de bord | indéterminé |

> **Trois pièges connus, écrits d'avance** — voir `verification_observabilite.md` :
> 1. le service **ralentit sans jamais renvoyer d'erreur** : une alerte sur le taux d'erreur ne
>    verra rien, le seuil utile est le p95 ;
> 2. `citations{resolvable="false"}` **ne peut structurellement pas se déclencher** ;
> 3. si le service répond `200` avec des réponses vides, **regarder `build_version` en premier**.

## Conditions d'arrêt

L'exercice s'arrête, et le rollback est exécuté sans attendre, si :

1. une **donnée** est menacée — l'archive de l'index sain ou l'historique sont touchés ;
2. l'incident **sort du périmètre** de la stack (poste, réseau domestique, autre service) ;
3. les **20 minutes** d'investigation sont écoulées sans hypothèse testable ;
4. un signal **inattendu** apparaît hors des six scénarios — on préfère un exercice écourté à un
   incident réel mal compris ;
5. l'animateur l'annonce.

Dans tous les cas, l'état initial et les traces **ne sont pas effacés** avant la fin de
l'exercice — y compris en cas d'arrêt anticipé. Une chronologie sans preuves ne vaut rien.

## Procédure de rollback

Détail complet : `docs/runbook.md`, section « Incident et rollback ». En résumé :

```bash
# 1. Constater et horodater
curl -s http://127.0.0.1:8000/health/ready
curl -s http://127.0.0.1:8000/metrics | grep diagops_index_valid
curl -s http://127.0.0.1:8000/version          # ← quelle version servait-on ?

# 2. Lister avant de choisir
docker compose -f deploy/compose.yaml run --rm --entrypoint sh gate -c \
  "python pipelines/rollback_index.py --list --active /artifacts/runtime/index.json --history /artifacts/history"

# 3. Restaurer une version NOMMÉE
docker compose -f deploy/compose.yaml run --rm --entrypoint sh gate -c \
  "python pipelines/rollback_index.py lexical-dfb8faf0c9b4 --active /artifacts/runtime/index.json --history /artifacts/history"
```

Pas de « dernière version connue » automatique : sous incident, l'automatisme qui choisit seul est
celui qui restaure la version qui vient de casser.

## Vérification après reprise

Les quatre contrôles, dans cet ordre. **Le premier ne suffit pas.**

| # | Contrôle | Attendu |
|---:|---|---|
| 1 | `GET /health/ready` | `200`, `lexical-dfb8faf0c9b4` |
| 2 | `POST /search` « vibration de la pompe », rôle technicien | **3 citations**, `abstained: false` |
| 3 | `diagops_index_valid` (API **et** Prometheus) | `1` des deux côtés |
| 4 | `docker compose ps` | `api` et `prometheus` en `healthy` |

Le contrôle 2 est celui qui compte : un service qui répond `200` en rendant zéro citation est
exactement la panne trouvée en phase 1. **Une readiness verte n'est pas une preuve de service.**

Puis, avant de clore : rejouer un palier de charge à concurrence 8 et vérifier que le p95 est
revenu sous 200 ms — une restauration fonctionnelle peut rester dégradée.
