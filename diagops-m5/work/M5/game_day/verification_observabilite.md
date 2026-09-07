# Vérification d'observabilité — phase 1 du brief 2

> « Chaque panne envisagée doit produire un signal attribuable. » Vérifié le **07/09/2026** sur
> les six scénarios annoncés par le brief. Deux trous trouvés, un corrigé, un assumé.

## Les six scénarios

| # | Scénario | Signal attendu | Vérifié | Délai de détection |
|---:|---|---|---|---|
| 1 | Index partiellement corrompu | `diagops_index_valid = 0`, readiness 503 | **oui**, bloc 6 | 3 s |
| 2 | Corpus candidat dégradant les citations | gate `failed`, promotion refusée | **oui**, bloc 4 | avant publication |
| 3 | Serveur de génération indisponible | `diagops_dependency_up = 0` | **partiellement** — voir plus bas | — |
| 4 | Latence du retrieval multipliée | `diagops_retrieval_duration_seconds` p95 | **oui**, mais invisible côté HTTP | 15 s |
| 5 | Configuration incompatible | readiness 503, gate `failed` | **oui**, corrigé ce jour | 3 s |
| 6 | Alerte manquante ou trop bruyante | *méta-scénario* | **c'est ce document** | — |

Deux scénarios s'ajoutent depuis la mise à jour du starter du 07/09 à 10h11 :

| # | Scénario | Signal attendu | Vérifié | Délai de détection |
|---:|---|---|---|---|
| 7 | **Dégradation du plan réponse seul**, service intact | les trois jauges de qualité tombent, tout le reste reste vert | **oui** | 15 s |
| 8 | **Configuration de release incompatible** | `ready = 0` **avec** `index_valid = 1` | **oui** | immédiat |

---

## Trou n°1 — trouvé et corrigé : l'index périmé, panne totale et silencieuse

Le scénario 5 a révélé une panne que rien ne voyait.

Un index dont les postings ont été produits par une **version antérieure du module de retrieval**
passe tous les contrôles existants : les documents sont là, les comptes sont cohérents, les
postings ne sont pas vides. Le service se déclare **`ready`**.

Et il rend **zéro résultat à toutes les requêtes**.

Constaté en conditions réelles : l'index local du poste, construit avant le passage aux postings
hachés, portait `build_version: build-0c139fd0de6a` avec un `index_version` identique à l'index
courant. Même contenu documentaire, autre façon de l'indexer, aucun signal.

> C'est le pire mode de défaillance possible : **le service est vert, répond `200`, et n'a plus
> aucune utilité**. Ni le taux d'erreur, ni la latence, ni la disponibilité ne bougent. Seul un
> humain lisant les réponses s'en apercevrait.

**Correctif appliqué.** `build_version()` est désormais calculée par le module de retrieval
lui-même, et la readiness **compare** l'empreinte de l'index servi à celle que le code produirait :

```
503 — index construit par une autre stratégie :
      build-0c139fd0de6a servi, build-ef4b168389e9 attendu
```

Deux tests figent le comportement (`build_version` divergent, `build_version` absent).

**Ce que ça dit du brief 1** : `build_version` avait été ajoutée pour combler un trou
d'*attribution* — savoir avec quelle stratégie un index avait été construit. Elle vient de servir
à autre chose : détecter une panne. Une donnée de traçabilité qui devient un contrôle
d'exploitation, c'est exactement ce que le module demande de construire.

---

## Mise à jour du 07/09, 10h11 — le formateur comble le trou du plan réponse

Un commit du dépôt pédagogique ajoute au starter trois jauges du plan réponse
(`diagops_citation_resolvable_rate`, `diagops_correct_abstention_rate`,
`diagops_expected_document_hit_at_3`) et un champ de défaut `release_valid`.

Son message de commit dit exactement ce que cette vérification avait constaté de son côté :

> « Trois des six scénarios de game day laissent le service répondre : sans compteurs du plan
> réponse, l'incident ne pouvait pas être détecté par le système, seulement signalé par
> l'animateur, ce que le brief 2 refuse explicitement. »

**Ce que ça change concrètement.** Le scénario que la répétition à blanc avait révélé comme
indétectable — un service qui répond `200` en étant inutile — devient injectable et donc
observable. Vérifié en conteneur :

| | Avant injection | Après injection |
|---|---|---|
| `/health/ready` | 200 | **200** |
| `diagops_ready` · `index_valid` · `dependency_up` | 1 · 1 · 1 | **1 · 1 · 1** |
| `citation_resolvable_rate` | 1,0 | **0,5** |
| `correct_abstention_rate` | 1,0 | **0,6** |
| `expected_document_hit_at_3` | 1,0 | **0,7** |
| `POST /search` | 3 citations | **3 citations** |
| Conteneur | `healthy` | **`healthy`** |

**Le plan service est intégralement vert pendant que le plan réponse s'effondre.** C'est la panne
que ce document décrivait comme invisible ; elle a maintenant trois signaux.

### Deux signatures à ne pas confondre

`release_valid: false` produit une signature distincte de celle d'un index cassé :

| Signature | Cause désignée | Vérifié |
|---|---|---|
| `ready = 0` **et** `index_valid = 1` | configuration de release | 503 « Configuration de release incompatible » |
| `ready = 1` **et** `index_valid = 0` | index incohérent | 503 « index actif sans postings exploitables » |

Deux causes voisines, deux remédiations différentes. Sous incident, une minute perdue à restaurer
le mauvais artefact compte — c'est le genre de distinction qui se lit en trois secondes quand elle
est écrite d'avance, et qui coûte dix minutes quand elle ne l'est pas.

### Ces jauges ne sont pas des mesures

Point à tenir clair pour la défense : elles sont **pilotées par `faults.json`** et valent `1.0`
par défaut. Ce sont des **leviers d'injection**, exactement comme `diagops_index_valid` l'était
avant le correctif du bloc 2.

La différence est que c'est ici **assumé et documenté** : nos compteurs (`refusals_total`,
`citations_total`, `restricted_citations_total`) mesurent le trafic réel ; ces jauges permettent
de simuler une dégradation que le trafic ne produirait pas spontanément. Les deux familles se
complètent, et le contrat de métriques distingue les unes des autres.

---

## Trou n°2 — assumé : une alerte qui ne peut jamais se déclencher

`diagops_citations_total{resolvable="false"}` figure au contrat de métriques avec un seuil
« **> 0, immédiat** ». Lecture du code :

```python
allowed    = visible_to(documents, role)      # allowed ⊆ documents
retrieved  = rank(..., allowed)               # retrieved ⊆ allowed
known      = {d["document_id"] for d in documents}
resolvable = item["document_id"] in known     # toujours True
```

Les documents cités **viennent de l'index** : ils y sont par construction. La branche `false` est
**inatteignable**, et le compteur ne peut structurellement jamais valoir autre chose que `true`.

> Une alerte qui ne peut pas se déclencher est pire que pas d'alerte : elle donne une assurance
> sans contrepartie. C'est très exactement le scénario 6 du brief — « alerte manquante » — sauf
> qu'ici elle n'est pas manquante, elle est **décorative**.

**Décision : la garder, et la requalifier.** La métrique reste utile comme invariant — si elle
bougeait un jour, cela signifierait que le chemin `retrieved ⊆ documents` a été cassé par une
modification du code. Elle est donc reclassée d'**alerte d'exploitation** en **invariant de
conception**, et le contrat de métriques le dit.

Ce qu'elle ne remplace pas : un contrôle de résolubilité **côté appelant**, qui vérifierait que
les `document_id` cités existent encore dans le corpus au moment de la lecture. Hors périmètre
ici, noté pour M6.

---

## Scénario 3 — signal simulé, pas observé

`diagops_dependency_up` est piloté par `faults.json`, un interrupteur d'incident. **Il n'y a
aucune dépendance de génération dans ce périmètre** : le retrieval est local et déterministe.

La métrique ne mesure donc rien de réel. Elle est conservée parce que le scénario formateur
« serveur de génération indisponible » peut être injecté par ce fichier — mais elle est marquée
comme **simulée** et non comme observée. La distinction compte : au moment du game day, il faudra
savoir que ce signal-là est déclaré, pas constaté.

---

## Scénario 4 — le signal existe, mais pas là où on le chercherait

La campagne de capacité a mesuré que le retrieval pèse **0,054 ms sur 5,01 ms** de traitement
HTTP, soit **1,1 %**.

Conséquence directe pour ce scénario : **multiplier la latence du retrieval par dix serait
invisible** sur `diagops_http_request_duration_seconds` — 0,54 ms ajoutés à 5 ms, sous le bruit.
Le p95 HTTP ne bougerait pas.

Le signal existe, mais c'est `diagops_retrieval_duration_seconds` qu'il faut regarder, avec son
propre seuil (p95 > 0,1 s). Une alerte posée uniquement sur la latence HTTP raterait complètement
une dégradation d'un facteur dix du composant qu'elle est censée surveiller.

---

## Attribution des signaux aux versions

Le brief demande que les alertes portent un lien vers les versions. État :

| Élément | Où il est disponible |
|---|---|
| `index_version` servie | `/health/ready` et `/version` |
| `build_version` servie | comparée à la readiness, dans le détail de l'erreur |
| `release_id` | `/health/ready` et `/version` |
| Checksums des composants | `/version` |

**Limite** : ces valeurs ne sont **pas** exposées en labels de métriques. Une alerte Prometheus ne
porte donc pas la version concernée — il faut appeler `/version` pour la connaître. C'est un choix
de cardinalité : un label `index_version` créerait une nouvelle série temporelle à chaque
réindexation, et les anciennes séries resteraient jusqu'à expiration. Le compromis est assumé, et
le runbook indique d'appeler `/version` à la première minute d'un incident.

## Rétention et données sensibles

| Contrôle | État |
|---|---|
| Rétention des métriques | 7 jours, volume Prometheus dédié |
| Données métier dans les labels | **aucune**, vérifié par test |
| Contenu documentaire dans les traces | aucun — l'index ne porte que des empreintes de termes |
| Accès à Prometheus | **sans authentification**, port 9090 — acceptable en laboratoire local uniquement |

## Bilan pour la phase 2

**Prêt** : scénarios 1, 2, 4, 5, plus la dégradation du plan réponse seul et la release
incompatible — chacun produit un signal attribuable et daté.

**À garder en tête pendant l'incident** :
- le scénario 3 sera un signal **simulé**, pas observé ;
- une alerte sur le taux d'erreur ne verra rien : le service ralentit, il ne casse pas
  (zéro erreur sur tous les paliers de charge) ;
- `citations{resolvable="false"}` ne se déclenchera pas, quoi qu'il arrive ;
- si le service répond `200` mais que les réponses sont vides, regarder `build_version` **avant**
  toute autre hypothèse ;
- si le plan service est **entièrement vert**, regarder les trois jauges du plan réponse : c'est
  désormais un scénario injectable, et c'est celui qu'aucun tableau de bord de disponibilité ne
  montre.
