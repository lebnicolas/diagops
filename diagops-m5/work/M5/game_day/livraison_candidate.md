# Livraison candidate — révision de corpus

> Phase 1, point 1 du brief 2 : construire la livraison candidate, produire l'index hors du
> chemin actif, exécuter les gates, préparer une promotion réversible. Exécuté le **07/09/2026**.

## Le candidat

La période `2026-S2` n'étant pas publiée, le candidat est une **révision contrôlée** du corpus
`2026-S1`, construite dans `candidat_corpus/` — le data pack reste intact, monté en lecture seule.

| | |
|---|---|
| Document modifié | `DOC-PUMP-VIB-001` |
| Révision | 1 → **2** |
| Changement | seuil de revue humaine **4,5 → 4,0 mm/s**, et une règle de dérive lente ajoutée |
| Nouveau checksum | `3971c51dfcc5d5f2…` |

Le changement est délibérément **sémantique** : il modifie ce que le document *affirme*, pas
seulement sa forme. C'est le seul type de changement qui teste vraiment un gate de RAG.

## Le cycle, exécuté

| Étape | Résultat |
|---|---|
| **Ingestion** | `rebuild` — 1 modification, 6 inchangés, **0 conflit de révision** |
| Index candidat | `lexical-dfb8faf0c9b4` → **`lexical-3a6510a3321f`**, écrit dans `candidates/s2/` |
| **Mesure** | hit@3 = 1,00 · citations = 1,00 · restreints cités = 0 |
| **Gate** | `passed`, 4 contrôles verts, `metrics_match_index` cohérent |
| **Promotion** | index sain archivé, puis candidat publié |
| **Retour arrière** | `lexical-b042af1b826b` → `lexical-dfb8faf0c9b4`, historique à **2 versions** |

La chaîne fonctionne de bout en bout, et la promotion est bien réversible.

---

## Le constat qui compte : le gate ne voit pas ce changement

Le candidat **passe le gate avec des métriques identiques** à celles de la référence.

Et c'est normal : les quatre contrôles mesurent le **retrieval** — retrouve-t-on le bon document,
les citations se résolvent-elles, l'abstention est-elle correcte. Le document attendu pour
`RAG-CAL-003` et `RAG-CAL-004` reste `DOC-PUMP-VIB-001`, et il est toujours retrouvé au rang 1.

> **Le gate valide qu'on retrouve le bon document. Il ne valide pas que le document dit toujours
> la même chose.**

Un corpus dont un seuil de sécurité passe de 4,5 à 4,0 mm/s change ce qu'une réponse citée
affirme. Sur ce service, il n'y a pas de génération, donc rien ne se voit. Dans un RAG complet,
la réponse changerait — et **aucun contrôle actuel ne l'aurait signalé**.

C'est très exactement le scénario 2 du game day, « corpus candidat dégradant les citations » :
notre chaîne l'attraperait s'il cassait le retrieval, elle le laisserait passer s'il se contente
de changer le sens.

### Ce que le gate voit, et ce qu'il ne voit pas

| Changement de corpus | Détecté ? | Par quoi |
|---|---|---|
| Document ajouté / retiré | oui | ingestion, `document_count` |
| Contenu modifié à révision constante | oui | **rejeté** — conflit de révision |
| Document restreint ouvert au public | oui | contrat d'admission |
| Document qui cesse d'être retrouvé | oui | hit@3 |
| **Contenu modifié qui change le sens** | **non** | *rien* |

### Le contrôle qui manque

Ni le hit@3 ni les citations ne peuvent l'attraper : ce sont des mesures de retrieval. Il faudrait
un contrôle d'une autre nature — au choix :

1. **une revue humaine obligatoire** sur tout document modifié, avant promotion : le gate liste
   les `modified` de l'ingestion et exige un acquittement nommé ;
2. **des questions d'évaluation portant sur les valeurs** (« quel est le seuil de revue
   humaine ? ») avec une réponse attendue, transformant un changement de sens en échec mesurable ;
3. **un diff sémantique** des documents modifiés, présenté au décideur.

La piste 1 est la plus honnête à ce stade : elle ne prétend pas automatiser un jugement. Elle est
inscrite au registre des remédiations et **n'a pas été implémentée** — l'ajouter maintenant sans
l'avoir éprouvée en game day serait de la conception à l'aveugle.

---

## Troisième constat : je suis tombé dans le piège que le dépôt documente

Le candidat a d'abord été écrit avec `Path.write_text`, qui applique sous Windows la traduction
universelle des fins de ligne : le fichier est parti en **CRLF** alors que tout le corpus de
référence est en **LF**. Le checksum ayant été calculé sur ce même fichier, le contrat d'admission
passait — sur ce poste, à cet instant.

Au premier `git checkout`, `.gitattributes` (`* text=auto eol=lf`) aurait réécrit le fichier en
LF. Le checksum déclaré au manifeste n'aurait plus correspondu, et **le contrat d'admission aurait
refusé le candidat sans qu'aucune donnée n'ait été modifiée**.

C'est exactement le scénario que le `.gitattributes` de ce dépôt décrit en commentaire depuis M2,
et le quatrième écart de fins de ligne de la formation — les trois premiers venaient des outils du
formateur, celui-ci est de mon fait.

Corrigé : réécriture en LF avec `newline=""`, checksum recalculé
(`3971c51dfcc5d5f2…`), chaîne rejouée. Le nouvel index candidat est `lexical-3a6510a3321f` — la
valeur précédente, `lexical-b042af1b826b`, était l'empreinte d'un fichier CRLF qui n'aurait pas
survécu au dépôt.

> La leçon utile : un checksum calculé sur le fichier qu'on vient d'écrire ne prouve rien. Il
> prouve quelque chose quand il est calculé sur le fichier tel qu'il sera **lu** — après passage
> par git, par une image Docker, par une copie entre systèmes.

## Second défaut trouvé à l'usage : le rollback effaçait sa propre trace

En enchaînant promotion puis retour, l'historique n'a gardé **qu'une version** : `rollback_index`
écrasait la version qu'il remplaçait sans l'archiver.

Deux conséquences, chacune suffisante pour corriger :

1. **un rollback pris à tort devenait irréversible** — plus moyen de revenir à la version qu'on
   venait de quitter ;
2. **le post-incident perdait la pièce à conviction** — or le brief 2 exige de n'effacer « ni
   traces ni état initial avant la fin de l'exercice ».

Corrigé : le rollback archive la version courante avant restauration, **y compris et surtout une
version fautive**. Vérifié — l'historique porte désormais `index-lexical-b042af1b826b.json` et
`index-lexical-dfb8faf0c9b4.json`. Six tests figent le comportement des deux pipelines.

## État après l'exercice

| | |
|---|---|
| Index actif | `lexical-dfb8faf0c9b4` (référence) |
| Historique | 2 versions restaurables |
| Index candidat | `lexical-3a6510a3321f` (fichiers en LF) |
| Candidat conservé | `artifacts/candidates/s2/` avec son rapport d'ingestion, sa mesure et son gate |
| Corpus candidat | `candidat_corpus/`, prêt à être rejoué |
| Tests | **61 passés** |

Le candidat est **prêt à être promu** le jour du game day : c'est la « nouvelle révision de
corpus » que le brief 2 demande de combiner avec l'incident.
