# L'agent borné — M6, étape 4

Le starter livre la tranche M4 à une étape : un outil choisi sur des mots-clés,
appelé une fois, puis une conclusion. Quatre capacités manquaient, toutes nommées
d'avance par le point de départ mesuré.

## 1. Résultats

| | Départ | **Après étape 4** |
|---|---:|---:|
| **jeu du starter** (18) | 0,833 | **1,000** |
| **jeu gelé v3** (29) | 0,724 | **0,931** |
| **campagne adversariale** (6) | 0,667 | **1,000** |
| choix d'outil exact (v3) | 0,793 | 0,966 |
| premier outil correct (v3) | 0,917 | 1,000 |
| appels d'outils interdits | 1 | **0** |
| dépassements de budget | 0 | 0 |
| tests | 51 | **64** |

Décomposé par type d'attente sur le jeu v3 : **12 / 12** sur les refus, **15 / 17**
sur les réponses. Les deux échecs restants sont `SCN-019` et `SCN-020`, les deux
scénarios d'ancrage documentaire — et ils **doivent** échouer : l'outil rend le
mauvais document, ce qui relève du retrieval (étape 7), pas de l'agent.

> **Ce chiffre mérite une réserve, et elle est importante.** Un agent qui refuse
> davantage est trivialement meilleur sur un jeu qui contient 12 refus attendus
> sur 29. C'est pourquoi la mesure sépare les deux colonnes, et pourquoi les
> refus *incorrects* comptent : il y en a 2, et ce sont exactement les deux
> scénarios ci-dessus.

## 2. Ce qui a été construit

### 2.1 Un plan, puis son déroulé

L'agent arrête un plan au premier tour — la liste des outils que la question
appelle — puis le déroule un outil à la fois, en réévaluant à chaque étape.

L'ordre n'est pas arbitraire : **le rapport en premier** (il porte l'identifiant
d'équipement dont les lectures suivantes ont besoin), **la recherche documentaire
en dernier** (la règle applicable dépend de ce qui a été relevé). Trois scénarios
enchaînent réellement : `SCN-006` (3 outils), `SCN-025` et `SCN-026` (2 outils).

Deux garde-fous :

- **le plan est dirigé par la question**, jamais systématique. Un test du starter
  le vérifie : « Que retenir du rapport RPT-2027S1-0002 ? » ne doit produire
  **qu'une** étape, même si le rapport livre un identifiant d'équipement exploitable.
  Un agent qui enchaîne par défaut lit plus que nécessaire ;
- **une intention dont les arguments manquent est abandonnée, pas devinée.** Si le
  rapport n'a pas livré d'équipement, la lecture d'événements qui en dépendait
  disparaît du plan.

### 2.2 Ce qui se refuse sans rien lire

Trois vérifications, avant le choix du premier outil :

| Vérification | Motif | Pourquoi avant l'appel |
|---|---|---|
| marqueur d'instruction dans la question | `instruction_dans_la_question` | appeler un outil sur une question qui cherche à détourner le système, c'est avoir déjà obéi à sa moitié recevable |
| terme hors domaine, ou aucun terme du domaine | `hors_perimetre` | interroger le corpus rendrait trois documents avec un score de 4 — mesuré à l'étape 1 sur cinq questions hors sujet |
| nom d'usage sans identifiant | `identifiant_ambigu` | le contrat l'écrit : « identifiant d'inventaire, jamais un nom d'usage ». Deviner l'équipement est la faute |

Ces vérifications vivent dans le **planificateur**, pas dans la boucle : une
sous-classe qui remplace `plan_next` garde le contrôle complet de ce qu'elle
appelle, et les tests du starter qui exercent la boucle avec un planificateur
bavard continuent de mesurer ce qu'ils mesuraient.

### 2.3 L'ancrage : un document rendu n'est pas une preuve

Le score du corpus place un document en tête de **n'importe quelle** question. La
règle retenue : un extrait cité doit porter au moins **deux termes significatifs**
de la question — mots vides et mots de trois lettres exclus, accents normalisés.
Sinon le document n'est pas cité.

La vérification porte sur **ce que l'agent voit** (titre et extrait), pas sur le
document entier : c'est exactement ce qu'on demande à une réponse fondée — que la
preuve citée porte la réponse.

**Une exception, découverte par une régression.** Une question composite — « la
procédure **et** la criticité » — se répond en partie par les sources structurées.
Mesurer l'ancrage de la question entière contre un document qui ne couvre qu'une
de ses deux moitiés donne un score faible et faisait refuser `SCN-006`, alors que
le rapport et la fiche avaient déjà fourni les preuves attendues. Règle corrigée :
quand d'autres preuves existent, le document faiblement ancré est **écarté de la
citation** sans faire tomber la réponse.

### 2.4 Existence contre exhaustivité — une distinction logique, pas cosmétique

Première version de la règle : « résultat tronqué + question d'ensemble → refus ».
Elle a fait échouer `SCN-004` du starter, qui attend une réponse sur « y a-t-il une
récidive… ». Diagnostic : **∃ se démontre sur un sous-ensemble, ∀ ne s'y démontre
pas.** Deux interventions du même type dans les lignes visibles suffisent à établir
une récidive ; aucun échantillon ne prouve un total.

| Famille | Termes | Tronqué ⇒ |
|---|---|---|
| **existence** | récidive, déjà, systématiquement | réponse si la répétition est visible, sinon refus |
| **exhaustive** | combien, au total, toutes, jamais | refus, toujours |

Conséquence : **mon propre scénario `SCN-023` était mal posé.** Il attendait un
refus sur une question de récidive, en contradiction directe avec `SCN-004`. Le jeu
étant gelé, il n'a pas été corrigé en place : il est passé en **v3**, reformulé sur
un total, avec la raison écrite au manifeste. C'est l'usage prévu de la règle de
version — le gel n'interdit pas de corriger, il interdit de corriger en silence.

## 3. L'arbitrage du 21/09, mis en œuvre

`search_knowledge` expose désormais `withheld` : le **nombre** de documents écartés
par le filtre de rôle, jamais leur identité.

Un faux positif a été corrigé en chemin. La première version comptait tout document
écarté dont le score dépassait zéro — c'est-à-dire presque tous, puisque le score
compte les mots vides. Le motif d'audit annonçait « filtre de rôle » sur une
question de givre. Le compte porte maintenant sur la **pertinence lexicale**, avec
le seuil qui sert déjà à juger les documents rendus : ce qui décide qu'un document
rendu est une preuve décide aussi qu'un document écarté méritait d'être compté.

Le résultat, vérifié par test :

| Question (rôle technicien) | `refusal_detail` | Réponse rendue |
|---|---|---|
| politique d'accès aux données | `filtre_de_role` | « Refus : aucune preuve admissible n'a été obtenue. » |
| givre sur un groupe froid | `ancrage_insuffisant` | **la même phrase, mot pour mot** |

Le motif vit dans la trace, pour l'audit. La formulation rendue est identique :
le canal auxiliaire reste fermé.

## 4. Une correction que je n'ai pas faite

Mon planificateur filtrait d'abord le plan par la liste blanche — un agent ne
planifie que ce qu'il a le droit d'appeler. Un test du starter est tombé, et il
avait raison : ce filtrage rendait `INV-02` (« aucun outil hors liste n'est
appelé ») **inobservable**. Plus aucune trace ne pouvait porter
`stop_reason = outil_hors_liste`.

C'est exactement le défaut dénoncé à l'étape 2 — un contrôle qui ne peut plus
échouer ne prouve plus rien. Le plan n'est donc pas filtré : c'est la boucle
d'exécution qui refuse, avec son motif.

## 5. Le sur-ajustement, et ce qui le contrôle

**Ces règles ont été écrites en regardant les échecs du jeu gelé.** C'est
précisément ce que l'oracle scellé du M4 interdisait, et il faut le dire avant
qu'on le remarque : le 0,931 est un score *sur le jeu qui a servi à régler*.

Trois éléments l'atténuent, aucun ne le supprime :

- la **campagne adversariale** (6 cas, construits par le formateur, jamais consultés
  pendant le réglage) passe de 0,667 à **1,000** — c'est le seul signal externe
  disponible aujourd'hui ;
- les règles sont **générales par construction** : périmètre, ancrage, existence
  contre exhaustivité, plafonnement d'argument. Aucune ne nomme un scénario ;
- les **64 tests** vérifient les règles, pas les scénarios.

Le vrai contrôle arrive au brief 2 : une campagne construite par un pair, sur un
agent qu'il n'a pas réglé. D'ici là, le chiffre se cite avec sa réserve.

## 6. Ce qui reste fragile

| Fragilité | Conséquence | Quand la traiter |
|---|---|---|
| le périmètre est une **liste de mots** | une question hors sujet formulée sans terme de la liste noire passe ; une question légitime au vocabulaire inhabituel est refusée | étape 7, si le feedback le désigne |
| l'ancrage compte des **termes**, pas du sens | une reformulation sans le vocabulaire du corpus est jugée non ancrée — c'est l'épreuve que le M4 avait dû construire pour départager lexical et vectoriel | idem |
| `ANCRAGE_MINIMUM = 2` | choisi par essai : 1 laissait passer un document partageant un mot de vocabulaire général, 3 refusait des cas nominaux courts. **Aucune mesure ne l'a validé sur un jeu indépendant** | étape 5 |
| la **répétition visible** approxime la récidive | deux interventions du même type ne sont pas nécessairement la même panne | à requalifier si le feedback le signale |
| l'ordre du plan porte l'exception d'ancrage | la règle « écarter sans refuser » suppose que le documentaire vient après les sources structurées | à rendre explicite si le plan se complexifie |

## 7. Ce qui reste à faire

- **étape 5** : mesurer proprement — dont les quatre valeurs de politique que le
  jeu ne discriminait pas tant que l'agent ne faisait qu'une étape (`max_steps`
  entre 2 et 8, `max_tool_calls`, `max_repeated_calls`, `stop_on_tool_error`) ;
- **étape 7** : le retrieval. `SCN-019` et `SCN-020` ne passeront pas avant, et
  c'est le candidat d'amélioration le plus évident — un seul axe, mesurable.
