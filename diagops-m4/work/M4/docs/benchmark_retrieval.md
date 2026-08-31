---
module: M4
brief: brief 1 — présentiel
etat: étape 4 terminée
maj: 2026-08-31
---

# Benchmark du retrieval

Chiffres produits par `run_retrieval.py`, consignés dans
`results/retrieval/retrieval.json`. Évaluation sur les **12 questions de
calibration** ; les 12 questions du split `test` sont scellées et n'ont pas été
ouvertes.

---

## Le corpus, et ce qu'il permet de conclure

**8 documents, 5 743 octets au total**, en français, chacun traitant d'un sujet
distinct : vibration des pompes, température des groupes froids, courant des
convoyeurs, pression vapeur, consignation électrique (deux révisions), politique
d'accès aux données, contrat de réponse documentaire.

Cette structure est décisive pour la lecture des résultats : **une question, un
document**, sans ambiguïté à lever.

## Le contrat d'admission s'applique avant le classement

Trois contrôles, dans cet ordre, avant qu'un document soit récupérable :

1. `status == "active"` ;
2. le rôle demandeur figure dans `allowed_roles` ;
3. le checksum SHA-256 correspond à celui du manifeste.

**Aucune des quatre stratégies n'a jamais récupéré un document inadmissible** —
0 sur l'ensemble des questions et des valeurs de `k`.

### Admissible comme preuve ≠ connu du manifeste

Deux questions attendent un document que le contrat exclut, et c'est délibéré :

| Question | Document attendu | Pourquoi il est inadmissible | Ce que le système doit dire |
|---|---|---|---|
| `RAG-CAL-008` (rôle `public`) | `DOC-DATA-ACCESS-001` | `restreint` aux rôles `superviseur` et `auditeur` | que la note ne lui est pas accessible |
| `RAG-CAL-010` | `DOC-LOTO-001` | statut `superseded` | que la révision 1 est remplacée par la révision 2 |

Dans les deux cas, la bonne réponse **porte sur l'inadmissibilité elle-même**.
Un système qui se contente de filtrer ne peut pas la formuler ; un système qui
cite ces documents viole le contrat.

D'où deux niveaux distincts, implémentés dans `src/corpus.py` :

| Niveau | Autorise | Contrôles |
|---|---|---|
| **preuve** | citer le contenu | statut, rôle, checksum |
| **métadonnée** | dire qu'il existe, son statut, sa révision, ce qui le remplace | présence au manifeste |

Le rappel est mesuré sur les documents attendus **citables** uniquement : le
compter autrement pénaliserait le comportement correct.

## Les trois baselines

| Stratégie | Rappel | Hit rate | 1er juste | MRR | Inadmissibles | Latence |
|---|---:|---:|---:|---:|---:|---:|
| **sans retrieval** | 0,000 | 0,000 | 0,000 | 0,000 | 0 | 0 ms |
| **lexical** | 1,000 | 1,000 | 1,000 | 1,000 | 0 | **0,57 ms** |
| **vectoriel** | 1,000 | 1,000 | 1,000 | 1,000 | 0 | 12,9 ms |
| vectoriel sans préfixes | 1,000 | 1,000 | 1,000 | 1,000 | 0 | 14,5 ms |

La baseline sans retrieval établit ce que le retrieval apporte : **tout**. Aucune
réponse documentaire n'est possible sans source, et c'est la seule stratégie qui
ne propose rien sur les deux questions sans preuve — pour la mauvaise raison,
puisqu'elle ne propose jamais rien.

### La mesure sature, et une mesure saturée ne mesure rien

| Stratégie | Recall@1 | Recall@2 | Recall@3 |
|---|---:|---:|---:|
| lexical | **1,000** | 1,000 | 1,000 |
| vectoriel | **1,000** | 1,000 | 1,000 |
| vectoriel sans préfixes | **1,000** | 1,000 | 1,000 |

Réduire `k` à 1 ne change rien : les trois stratégies placent le bon document
**en première position** sur les dix questions ayant une preuve citable.

> Ce résultat ne dit pas que les trois stratégies se valent. Il dit que **ce jeu
> d'évaluation ne peut pas les départager** : les questions reprennent le
> vocabulaire des documents, chaque document traite un sujet unique, et un simple
> recouvrement de mots suffit. La mesure porte sur la facilité du corpus, pas sur
> la qualité du retrieval.

Conclure « le vectoriel n'apporte rien » sur cette base serait aussi faux que
conclure l'inverse.

## Une épreuve construite pour départager

Puisque la mesure fournie sature, une seconde a été construite. Protocole figé
**avant toute mesure** dans `data/questions_reformulees.json` :

- les 10 questions ayant une preuve citable sont reformulées ;
- contrainte d'écriture : **aucun terme technique du document attendu** — chaque
  mot-clé remplacé par un synonyme ou une périphrase ;
- les documents attendus sont inchangés : c'est la question qui bouge.

*Exemple* : « À partir de quel niveau de **vibration** une **pompe** exige-t-elle
une **revue humaine prioritaire** ? » devient « À partir de quelles **secousses**
une pompe doit-elle **passer devant un opérateur en priorité** ? ».

| Stratégie | Recall@1 d'origine | **Recall@1 reformulé** | Écart |
|---|---:|---:|---:|
| lexical | 1,000 | **0,300** | **−0,700** |
| vectoriel | 1,000 | **0,700** | −0,300 |
| vectoriel sans préfixes | 1,000 | 0,700 | −0,300 |

**Le lexical s'effondre, le vectoriel tient plus du double.** C'est exactement ce
qu'un appariement sémantique est censé apporter — et c'est maintenant mesuré au
lieu d'être supposé.

Le détail des échecs est parlant : le lexical rate **7 questions sur 10** et se
rabat sur des documents sans rapport — « secousses » n'appartient à aucun
document, il propose alors `DOC-RAG-OPS-001`, le document le plus générique du
corpus, trois fois. Le vectoriel n'en rate que 3.

### Les préfixes E5 : hypothèse non vérifiée

La famille E5 est entraînée avec `query: ` et `passage: `. J'attendais une
dégradation nette en les omettant. **Il n'y en a aucune** : 1,000 et 0,700 dans
les deux cas, à l'identique.

Deux lectures possibles, et rien ici ne permet de trancher : soit le corpus est
trop facile pour que la différence se voie, soit l'effet des préfixes est
marginal sur des textes aussi courts. Les préfixes sont **conservés** — ils sont
la façon documentée d'employer ce modèle, et rien ne justifie de s'en écarter.

## Coût

| Poste | Lexical | Vectoriel |
|---|---:|---:|
| Index | **0 octet** (construit à la volée) | 12 288 octets (8 × 384 flottants) |
| Modèle | aucun | **~470 Mo** sur disque |
| Chargement | 0 s | **11,4 s** au démarrage |
| Latence par requête | **0,57 ms** | 12,9 ms (**×23**) |
| Dépendances | aucune | `sentence-transformers`, `torch` |

Sur 8 documents, une base vectorielle dédiée n'a pas été retenue : le brief
l'autorise explicitement, et elle ajouterait un service et une latence réseau
pour indexer 6 Ko de texte. Un index en mémoire est reproductible et suffit.

## Le modèle d'embeddings — arbitrage A4

**`intfloat/multilingual-e5-small`**, empreinte des poids gérée par
`sentence-transformers`.

| Critère | Valeur | Ce qui a décidé |
|---|---|---|
| Langue | 100+ langues dont le français | le corpus est **entièrement en français** — un modèle anglophone est disqualifié |
| Objectif d'entraînement | retrieval | les modèles `paraphrase-*` optimisent la similarité de paraphrases, pas la correspondance question → passage |
| Dimensions | 384 | index de 12 ko |
| Contexte | 512 tokens | aucun document tronqué (le plus long fait 896 octets) |
| Taille | 118 M paramètres, ~470 Mo | tourne en CPU sur un poste sans GPU |
| Licence | MIT | aucune contrainte de réutilisation |

**Écartés** : `paraphrase-multilingual-MiniLM-L12-v2` (objectif d'entraînement
inadapté) et `multilingual-e5-base` (278 M paramètres pour 6 Ko de corpus — payer
ce prix sans gain établi contredit l'éco-conception que le brief demande de
mesurer).

## Ce que le retrieval ne règle pas

Sur les **2 questions sans preuve citable** — `RAG-CAL-011` (marque de lubrifiant
absente du corpus) et `RAG-CAL-012` (date de la prochaine panne) — les trois
stratégies proposent **3 documents chacune, soit 6 au total**.

> Le retrieval propose **toujours** quelque chose. Il n'a aucune notion de
> « rien de pertinent » : il classe, il ne juge pas. C'est l'abstention qui doit
> trancher, et c'est l'objet de l'étape 5.

C'est le point le plus important de cette étape pour la suite : un rappel de
1,000 sur les questions répondables ne dit **rien** du comportement sur les
questions qui n'ont pas de réponse.

## Décision

**Pas d'hybride.** Le brief le subordonne à la stabilité des deux baselines
précédentes ; elles sont stables, mais indiscernables sur le jeu fourni.
Construire un hybride pour départager deux stratégies à 1,000 n'aurait aucun sens.

**Recommandation, conditionnelle et assumée :**

| Si les questions… | Alors | Motif mesuré |
|---|---|---|
| reprennent le vocabulaire des procédures | **le lexical suffit** | 1,000 partout, 23× plus rapide, zéro dépendance |
| sont formulées librement par des utilisateurs | **le vectoriel se justifie** | 0,700 contre 0,300 sur l'épreuve reformulée |

Rien dans le matériel fourni ne dit laquelle des deux situations correspond à
l'usage réel de DiagOps. **Cette information manque, et c'est elle qui trancherait
la décision** — pas une mesure supplémentaire sur ce corpus.

En l'absence de cette information, le vectoriel est retenu pour la suite du
brief : il est le seul des deux à ne pas s'effondrer quand la formulation change,
et son coût — 12 ko d'index, 13 ms par requête — reste négligeable à cette
échelle. La décision définitive appartient à `docs/matrice_decision.md`.

## Limites

1. **Les reformulations sont écrites par nous**, pas par un tiers ni par des
   utilisateurs. Elles mesurent la robustesse à une paraphrase *choisie* — un
   indice, pas une preuve.
2. **10 questions.** Un écart de 0,300 à 0,700 représente 4 questions sur 10 ;
   l'intervalle de confiance est large et n'est pas calculé ici.
3. **8 documents.** Tout ce qui précède décrit un corpus minuscule. Le
   comportement à 800 ou 8 000 documents — où le rappel cesse d'être trivial et
   où le coût d'index compte — n'est pas établi.
4. **Le chunking n'a pas été exploré** : les documents font moins de 900 octets
   et tiennent chacun sous la limite de contexte du modèle. Sur des procédures
   réelles de plusieurs pages, ce serait le premier paramètre à traiter.
5. **Aucune mesure sur le split `test`**, scellé.
