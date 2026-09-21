# Candidat d'amélioration — le score du retrieval

**Un seul axe modifié : la fonction de score de `search_knowledge`.** Ni le corpus,
ni la politique, ni l'agent, ni les seuils de l'ancrage.

> Ce document est écrit **en deux temps**. Les sections 1 à 4 — hypothèse,
> mécanisme, prédictions, protocole — sont rédigées et **commitées avant** que le
> candidat n'existe. Les sections 5 et suivantes sont remplies après mesure.
> C'est la seule façon de savoir si une prédiction était juste : l'écrire avant.

## 1. Ce qui motive le candidat

Deux sources indépendantes désignent le même défaut.

**La mesure** (étape 1, confirmée étape 5) : le score est un comptage de tokens
communs, mots vides inclus, sans normalisation. Deux questions du domaine sur cinq
récupèrent le mauvais document, et `SCN-019` / `SCN-020` restent les deux seuls
échecs du jeu gelé.

**L'usage** (étape 6) : trois des quatre thèmes de feedback les plus répétés
pointent le retrieval — extrait mal cadré (10 occurrences), seuil de vibration ne
correspondant pas à la procédure pompe (7), document de groupe froid jamais rendu
(7).

## 2. Référence mesurée avant modification

Jeu `eval/retrieval_eval.jsonl`, **20 questions**, gelé — empreinte
`c6bba32e18ad310c…`. Il sépare trois familles, parce qu'elles ne posent pas la
même question au système.

| Famille | Recall@1 | Recall@3 |
|---|---:|---:|
| `vocabulaire_du_corpus` (7) | 0,714 | 1,000 |
| `vocabulaire_utilisateur` (5) | **0,200** | 0,400 |
| `ambigu` (3) | 0,667 | 0,667 |
| **global hors « hors domaine »** | **0,533** | — |

| Séparation | Valeur |
|---|---:|
| score minimum sur le domaine | 2,0 |
| score maximum hors domaine | **5,0** |
| **séparation** | **−3,0** |
| silences sur les 5 questions hors domaine | **0 / 5** |

**La séparation négative est le vrai résultat de la référence.** Le pire score
d'une question légitime est inférieur au meilleur score d'une question sur la
tarte aux pommes. Aucun seuil ne peut trier ce que ce score produit — c'est le
constat du M4 sur la similarité vectorielle (0,007 d'écart entre répondables et
non répondables), retrouvé ici par un autre chemin.

## 3. Hypothèse

> Le score compte des mots qui ne portent aucun sujet. « de », « la », « aux »,
> « est » sont présents dans les sept documents ; ils rapprochent n'importe quelle
> question de n'importe quel document, et noient le signal des termes métier.
>
> **En ne comptant que les termes significatifs** — mots vides retirés, accents
> normalisés, mots de trois lettres ou moins écartés — le score ne retient que ce
> qui distingue. Le corpus s'y prête : chaque terme métier est **propre à un seul
> document** (vérifié avant mesure : `vibration`→PUMP, `courant`/`convoyeur`→CONV,
> `vapeur`/`pression`→STEAM, `consignation`→LOTO, `accès`/`données`→DATA,
> `froid`/`température`→CHILL).

La modification réutilise la couche lexicale déjà partagée entre l'outil et
l'agent (`termes_significatifs`), introduite à l'étape 4. Aucune dépendance
nouvelle, aucun modèle, aucun index.

## 4. Prédictions, écrites avant la mesure

| # | Prédiction | Pourquoi |
|---:|---|---|
| **P1** | `vocabulaire_du_corpus` Recall@1 passe de 0,714 à **1,000** | chaque terme métier est propre à un document ; sans mots vides, rien ne peut le dépasser |
| **P2** | `hors_domaine` produit **5 silences sur 5** | aucune question hors domaine ne partage de terme significatif avec le corpus |
| **P3** | la séparation devient **positive** | conséquence directe de P2 : un score maximum de 0 hors domaine |
| **P4** | `RET-08` (givre) **échoue encore** | « givre » n'est dans **aucun** document — vérifié. Ce n'est pas un défaut de score |
| **P5** | `RET-09` (palier qui chauffe) **réussit** | « palier » est dans `DOC-PUMP-VIB-001`, et c'est le seul recouvrement possible |
| **P6** | `vocabulaire_utilisateur` reste **sous 0,600** | trois des cinq questions n'ont aucun terme commun avec leur document attendu |
| **P7** | sur le jeu gelé v3, `SCN-020` **passe**, `SCN-019` **échoue toujours** | même raison que P5 et P4 |
| **P8** | les questions `ambigu` ne régressent pas | elles reposent sur « règle », « triage », « seuils », « révision » — tous significatifs |
| **P9** | la réussite du jeu v3 passe de 0,931 à **0,966** | un seul scénario corrigé sur les deux échecs |

**Risque de régression identifié** : l'ancrage de l'agent utilise le même seuil de
termes significatifs. Si le score change les documents rendus, l'ancrage juge des
extraits différents — un scénario aujourd'hui réussi pourrait basculer. C'est
pourquoi le jeu v3 **et** la campagne **et** les 64 tests sont rejoués, pas
seulement le banc de retrieval.

## 5. Protocole

1. jeu de retrieval gelé et mesuré **avant** toute modification ✓ ;
2. prédictions écrites et commitées **avant** que le candidat n'existe ✓ ;
3. modification d'un seul axe : la fonction `_score` de `tools/knowledge.py` ;
4. rejouer : banc de retrieval, jeu gelé v3, campagne adversariale, suite de tests ;
5. comparer à la référence, prédiction par prédiction ;
6. décider : promouvoir, rejeter ou prolonger.

Aucun réglage sur le jeu de retrieval : il sert à mesurer, pas à ajuster. S'il
faut plusieurs essais, chaque essai est consigné.

---

# Résultats — mesurés après coup, prédictions non retouchées

Candidat **`m6-retrieval-r2`** : `_score` compte les termes significatifs partagés,
au lieu de tous les tokens communs. Une fonction, six lignes, aucun autre axe.

## 6. Le retrieval seul

| | Référence | **Candidat** |
|---|---:|---:|
| Recall@1 global | 0,533 | **0,667** |
| `vocabulaire_du_corpus` @1 | 0,714 | **1,000** |
| `vocabulaire_utilisateur` @1 | 0,200 | 0,200 |
| `ambigu` @1 / @3 | 0,667 / 0,667 | 0,667 / **1,000** |
| silences sur hors domaine | **0 / 5** | **5 / 5** |
| score maximum hors domaine | 5,0 | **0,0** |
| **documents rendus au total** | 60 | **31** |

**L'attracteur a disparu.** En référence, `DOC-STEAM-PRESS-001` sortait en tête de
**11 questions sur 20**, dont les cinq hors domaine. Avec le candidat, il n'est
plus premier que sur la question qui le concerne et sur les trois ambiguës.

**L'exposition est divisée par deux** : 31 documents rendus contre 60. Ce n'est pas
l'objectif visé, c'est un effet secondaire mesuré — et il va dans le sens de la
minimisation.

## 7. Les neuf prédictions, confrontées

| # | Prédiction | Verdict | Ce qui s'est passé |
|---:|---|---|---|
| P1 | corpus @1 → 1,000 | ✔ **juste** | 0,714 → 1,000 |
| P2 | 5 silences hors domaine | ✔ **juste** | 0 → 5 sur 5 |
| P3 | séparation positive | ✘ **fausse** | elle vaut 0,0 — trois questions **du domaine** se taisent aussi. Voir §8 |
| P4 | `RET-08` (givre) échoue encore | ✔ **juste** | et il se tait au lieu de rendre le mauvais document |
| P5 | `RET-09` (palier) réussit | ~ **mal posée** | il réussissait **déjà** en référence : je prédisais un gain là où il n'y avait rien à gagner |
| P6 | vocabulaire utilisateur < 0,600 | ✔ **juste** | 0,200, inchangé |
| P7 | `SCN-020` passe | ✘ **fausse** | le retrieval rend le **bon** document ; c'est l'ancrage qui le rejette. Voir §9 |
| P8 | `ambigu` ne régresse pas | ✔ **juste** | @1 stable, @3 de 0,667 à 1,000 |
| P9 | jeu v3 → 0,966 | ✘ **fausse** | reste 0,931, pour la raison de P7 |

**Cinq justes, trois fausses, une mal posée.** Les trois fausses tiennent à deux
causes qu'aucune lecture du code n'aurait données : un contrôle en aval qui absorbe
le gain, et une métrique qui mélange deux choses.

## 8. P3 — pourquoi la séparation n'est pas le bon indicateur

Elle compare le pire score du domaine au meilleur score hors domaine. Elle
supposait que le domaine rend toujours quelque chose. Le candidat rend aussi des
**silences sur le domaine** — quand la question ne partage aucun terme avec le
corpus (`RET-08`, `RET-10`, `RET-12`) — et un silence compte 0.

En ne comparant que les questions qui rendent un résultat :

| | Référence | Candidat |
|---|---|---|
| pire score du domaine | 2,0 | 1,0 |
| meilleur score hors domaine | 5,0 | **aucun résultat rendu** |

Le hors-domaine ne produit plus rien du tout : il n'y a plus de frontière à
franchir, donc plus de seuil à régler. **Le progrès est réel, l'indicateur que
j'avais choisi ne sait pas l'exprimer.** C'est la leçon du M5 sur les contrôles qui
ne mesurent pas ce qu'ils prétendent, appliquée à une métrique que j'ai écrite
moi-même.

## 9. P7 — le gain existe, et il est absorbé

`SCN-020` (« Comment interpréter un courant moteur anormal sur un convoyeur ? ») :

- en référence, le retrieval rendait `DOC-RAG-OPS-001` — le mauvais document ;
- avec le candidat, il rend **`DOC-CONV-CURRENT-001`**, le bon, avec un score de 1,0 ;
- et l'agent **le refuse** : un seul terme commun (« courant ») pour un
  `ANCRAGE_MINIMUM` de 2.

Le composant est corrigé, le système ne bouge pas. Deux contrôles empilés comptent
la même chose — le score du retrieval et l'ancrage de l'agent utilisent la même
couche lexicale — et quand le premier devient sélectif, le second devient
**redondant et trop strict** : il re-filtre une liste déjà filtrée par pertinence.

C'est le risque de régression annoncé au §4, arrivé dans l'autre sens : l'ancrage
n'a pas cassé un cas qui marchait, il a empêché un cas de se réparer.

**Le second candidat est identifié, et il n'est pas modifié ici** : abaisser
`ANCRAGE_MINIMUM` à 1 lorsque le score du retrieval porte déjà la pertinence.
Un seul axe par candidat — celui-ci portait sur le score.

## 10. Le système complet, et un effet non prévu

| | Référence | Candidat |
|---|---:|---:|
| jeu gelé v3 | 0,931 | **0,931** |
| échecs | `SCN-019`, `SCN-020` | `SCN-019`, `SCN-020` |
| campagne adversariale | 1,000 | **1,000** |
| appels d'outils interdits | 0 | 0 |
| tests | 64 | **64** |
| **baseline sans agent (v3)** | 0,172 | **0,345** |

**Le dernier chiffre n'était pas prévu et il compte.** La baseline « sans agent »
interroge directement `search_knowledge` : améliorer le score l'améliore aussi, et
elle **double**. L'écart entre l'agent et sa baseline passe de 0,759 à 0,586.

> Modifier un composant partagé déplace la référence en même temps que le candidat.
> Un gain mesuré contre une baseline mobile n'est pas le gain qu'on croit mesurer —
> et ici, l'amélioration profite davantage au système qu'on cherchait à battre
> qu'à celui qu'on cherchait à améliorer.

**Un test a dû être recalibré** : `test_max_result_rows_coupe_le_resultat` avait
besoin d'une question rendant plusieurs documents, et le candidat rend moins de
documents. C'est la question du test qui change, **jamais son assertion** — et le
fait est consigné ici plutôt que passé sous silence.

## 11. Décision

| Critère de promotion | État |
|---|---|
| un seul axe modifié | ✔ la fonction de score, rien d'autre |
| hypothèse formulée avant mesure | ✔ commit `d976e1e`, avant que le candidat n'existe |
| jeu d'évaluation gelé avant modification | ✔ empreinte `c6bba32e18ad310c…` |
| gain sur le composant visé | ✔ Recall@1 0,533 → 0,667, corpus à 1,000 |
| aucune régression sur le jeu gelé | ✔ 0,931 inchangé |
| aucune régression sur la campagne | ✔ 1,000 inchangé |
| invariants tenus | ✔ 64 tests verts, 0 appel interdit |
| gain sur le système complet | ✘ **nul** — absorbé par l'ancrage (§9) |

**Proposition : promouvoir**, pour trois raisons qui ne dépendent pas de l'ancrage :

1. **sécurité** — cinq questions hors domaine sur cinq ne rendent plus rien, là où
   la référence servait un document avec un score supérieur à celui de vraies
   questions ;
2. **minimisation** — 31 documents rendus au lieu de 60 ;
3. **honnêteté du système** — les questions sans réponse dans le corpus produisent
   un silence au lieu d'un document hors sujet cité avec aplomb.

Et **ouvrir immédiatement le second candidat** sur l'ancrage, sans lequel
l'utilisateur ne verra rien de ce gain.

> `INV-07` — aucune promotion sans décision humaine. Celle-ci est proposée, pas
> appliquée : le candidat est mesuré, la décision revient à Nicolas.

## 12. Décision rendue

**PROMU** le 21/09/2026, décidé par **Nicolas**, sur la proposition du §11.

| | |
|---|---|
| candidat | `m6-retrieval-r2` — `_score` sur les termes significatifs |
| gate | jeu gelé v3 **0,931** (inchangé), campagne **1,000** (inchangée), 64 tests verts, 0 appel d'outil interdit |
| motif | sécurité (5/5 silences hors domaine), minimisation (60 → 31 documents rendus), honnêteté (silence plutôt qu'un document hors sujet) |
| réversibilité | un `git revert` du commit `4b245f7` ramène le score d'origine ; le jeu d'évaluation et les mesures de référence restent au dossier |
| suite | second candidat ouvert sur l'ancrage (§9), sans lequel le gain n'atteint pas l'utilisateur |

La décision ne s'appuie pas sur un gain système — il est nul. Elle s'appuie sur
trois propriétés acquises **indépendamment** de l'ancrage, et sur l'absence de
régression. C'est une promotion défendable, et c'est aussi la limite de ce qu'on
peut en dire.

---

# Second candidat — l'ancrage qui absorbe le gain

**Axe unique : `ANCRAGE_MINIMUM`.** Le premier candidat a rendu le score sélectif ;
l'ancrage de l'agent compte la même chose et re-filtre une liste déjà filtrée.

## 13. Hypothèse et prédictions, écrites avant mesure

> Quand le score du retrieval porte déjà la pertinence, exiger **deux** termes
> communs entre la question et l'extrait cité est redondant. Un seul suffit, parce
> qu'un document sans aucun terme commun n'est plus rendu du tout : le silence du
> retrieval a remplacé le filtre de l'agent.

| # | Prédiction | Pourquoi |
|---:|---|---|
| **Q1** | `SCN-020` passe, le jeu v3 monte à **0,966** | le bon document est rendu, seul l'ancrage le bloque |
| **Q2** | `SCN-019` **échoue toujours** | le retrieval se tait : aucun document à ancrer, quel que soit le seuil |
| **Q3** | `SCN-014` reste un refus | le document restreint est filtré par le rôle, les autres ne partagent pas de terme |
| **Q4** | campagne **1,000** maintenue | aucun cas de la campagne ne dépend de l'ancrage |
| **Q5** | les 64 tests restent verts | le test d'invariant du refus neutre repose sur un silence, pas sur un seuil |

**Risque identifié** : à 1, un document partageant un seul mot de vocabulaire
général — « règle », « seuil » — redeviendrait citable. Le premier candidat a
réduit ce risque en supprimant les mots vides, il ne l'a pas supprimé.
