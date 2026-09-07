# Rapport post-incident — répétition à blanc du 07/09/2026

> **Ceci est une répétition, pas le game day du brief 2.** Le scénario a été tiré au sort parmi
> six et scellé jusqu'au rendu du diagnostic, mais l'urne est de ma main. Ce que l'exercice
> valide et ce qu'il ne valide pas est traité en fin de document.

## Résumé et impact

À 09:48:42 UTC, l'index servi a été vidé de ses postings. Le service a continué de répondre
**HTTP 200** à toutes les requêtes de recherche, en s'abstenant systématiquement : « aucun
document autorisé ne permet de répondre », zéro citation.

L'incident a été détecté en **7 secondes** par la readiness, diagnostiqué en 33 secondes,
restauré en 36 secondes. Aucune donnée perdue. Les quatre objectifs de reprise sont tenus avec
une marge large.

| Étape | Objectif | Mesuré |
|---|---|---|
| Détection | < 2 min | **7 s** |
| Décision | < 5 min | **33 s** |
| Restauration | < 10 min | **36 s** |
| Perte de données | aucune | **aucune** |

## Chronologie

Détail horodaté dans `timeline.md`.

## Cause, facteurs aggravants et symptômes

**Cause** : altération de l'artefact actif après publication. Le gate protège la livraison ; rien
ne surveille ce qui arrive à l'index une fois en place. C'est la même cause que l'incident du
brief 1 — et c'est un enseignement en soi : deux exercices, une seule cause, un seul angle mort.

**Facteur aggravant évité de justesse** : au moment de préparer l'exercice, `/artifacts/history`
était **vide dans le volume Docker**. L'historique à deux versions construit plus tôt vivait sur
le poste, dans `work/M5/artifacts/`, pas dans la stack. Injecter à ce moment-là aurait produit une
panne **irrécupérable** — sans archive, `rollback_index.py --list` n'aurait rien proposé.

C'est exactement ce que le plan de game day prescrivait — « la sauvegarde et le tag se font avant,
pas pendant ; c'est l'étape qu'on oublie » — et je l'ai oubliée. La relire au bon moment est ce
qui a sauvé l'exercice.

**Symptômes**, par ordre de visibilité :

| Symptôme | Visible par | Quand |
|---|---|---|
| `diagops_index_valid = 0` | métrique | immédiat |
| `/health/ready` → 503 | sonde | immédiat |
| `abstained: true` sur toute requête | **client** | immédiat, mais silencieux |
| Conteneur `unhealthy` | orchestrateur | ~50 s (non atteint, restauré avant) |

**Aucun symptôme sur le plan service.** Débit, latence et taux d'erreur sont restés nominaux
pendant toute la durée de l'incident : le service répondait vite et correctement — à une question
à laquelle il ne savait plus répondre.

## Détection et réponse

**Ce qui a détecté** : la readiness, parce qu'elle relit l'artefact servi à chaque appel. C'est le
correctif du bloc 2 — avant lui, `diagops_index_valid` était piloté par `faults.json` et serait
resté à 1.

**Ce qui n'aurait rien vu** : une alerte sur le taux d'erreur, sur la latence, sur le débit, ou
sur l'état du conteneur. Quatre tableaux de bord au vert pendant que le service est inutile.

**Le diagnostic a tenu en trois relevés** :

1. `diagops_index_documents = 7` → les documents sont là, ce n'est pas une amputation ;
2. `dependency_up = 1` et readiness en 10 ms → ni dépendance, ni lenteur ;
3. `index_version` et `build_version` **corrects**, postings à **0** → l'index est le bon, son
   contenu ne l'est pas.

Ces trois relevés éliminent quatre des cinq scénarios de panne de l'urne. Le fait que
`build_version` soit correcte a été décisif : c'est ce qui distingue une corruption d'un index
périmé, deux pannes aux symptômes voisins.

## Restauration et vérification

Rollback vers une version **explicitement nommée**, après avoir listé les versions disponibles.
Les quatre contrôles du plan ont été exécutés dans l'ordre, et le deuxième est celui qui compte :
`POST /search` rend **3 citations** avec `abstained: false`.

Une readiness verte ne prouve rien ici — pendant l'incident, `/search` répondait `200` lui aussi.
**Seule la présence de citations distingue un service qui marche d'un service qui répond.**

## Ce qui a fonctionné

- **La readiness branchée sur l'artefact réel** (bloc 2) : sans elle, aucun signal.
- **`build_version`** (bloc 1, étendue en phase 1) : a permis d'écarter le scénario voisin en un
  relevé.
- **Le rollback par version nommée** : lister avant de choisir a pris 3 secondes et supprime le
  risque de restaurer la version qui vient de casser.
- **Le plan relu avant d'agir** : c'est lui qui a fait constater l'historique vide.
- **Les quatre contrôles de vérification** : le deuxième a confirmé ce que le premier ne pouvait
  pas dire.

## Ce qui doit changer

| # | Constat | Action |
|---:|---|---|
| 1 | L'incident est **invisible côté client** : `200` + abstention | Ajouter une alerte sur un **taux d'abstention anormal** — `refusals / retrieval_queries` > 50 % sur 15 min figure au contrat de métriques, mais n'a jamais été éprouvé. À vérifier au prochain exercice. |
| 2 | L'historique vit dans le volume, l'exécution locale écrit ailleurs | **Deux emplacements d'artefacts pour un même dispositif** : `work/M5/artifacts/` en local, volume `deploy_diagops_artifacts` en conteneur. Le runbook doit dire lequel fait foi, et la sauvegarde porter sur le volume. |
| 3 | Même cause qu'au brief 1 : altération après publication | La remédiation « vérification périodique d'intégrité hors chemin de requête » reste **ouverte**. Deux incidents, une cause : elle mérite d'être instruite. |
| 4 | Le conteneur n'a jamais basculé `unhealthy` | Restauration en 36 s, bascule à ~50 s. Confirme que l'alerte doit porter sur la métrique, pas sur l'orchestrateur — **l'incident était fini avant que Docker s'en aperçoive**. |

Le rapport analyse le dispositif et les décisions. Aucune de ces quatre entrées ne désigne une
personne : elles désignent des endroits où le système ne dit pas ce qu'il sait.

## Ce que cet exercice ne prouve pas

**L'urne est de ma main.** Six scénarios, tous des pannes que j'avais moi-même instrumentées.
Un tiers peut injecter hors liste, combiner deux pannes, ou provoquer un mode de défaillance
auquel le dispositif n'a jamais pensé. C'est précisément là que se joue le game day.

**Le témoin n'est pas sorti.** L'urne contenait `aucun_incident` — savoir conclure « rien à
signaler » sans chercher jusqu'à trouver quelque chose est une compétence que cet exercice n'a pas
mise à l'épreuve.

**Le diagnostic a été rapide parce que je connaissais les signaux**, pour les avoir écrits. Un
diagnostic en 33 secondes sur une panne dont on a soi-même construit la détection ne dit rien de
la capacité à diagnostiquer l'inconnu.

**Aucun rôle n'était réellement séparé.** Pilote, diagnostic et exploitation étaient la même
personne — ce qui reste vrai dans le brief, mais l'animateur, lui, doit être un tiers.

Ce que la répétition valide, en revanche : la chronologie tient, les objectifs sont atteignables
avec une marge confortable, les quatre contrôles de vérification sont exécutables en moins d'une
minute, et le plan a servi à quelque chose — il a empêché d'injecter sans point de retour.
