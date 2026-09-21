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
