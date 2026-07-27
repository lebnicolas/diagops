# Expérience complémentaire — dropout LoRA 0,05 → 0,15

**Statut** : expérience postérieure au gel du protocole (`67c873e`) et à la
décision intermédiaire (`25f4f42`). Elle ne remet pas en cause la décision : elle
répond à la réserve qui y est inscrite — la généralisation n'est pas démontrée.

**Hypothèse commitée avant exécution** : `e675496`. L'antériorité de l'hypothèse
sur le résultat est vérifiable dans l'historique git.

## Question

La mémorisation est établie : `variation_2` atteint un composite de 100,00 sur
les 65 exemples possédant un quasi-jumeau dans l'entraînement, sans aucun gain
sur les 15 inédits. Le dropout étant le levier de régularisation le plus direct
sur un adaptateur LoRA, le tripler réduit-il cette mémorisation ?

Une seule variable change par rapport au candidat retenu : `lora.dropout`, de
0,05 à 0,15. Tout le reste est identique — rang, α, modules cibles, epochs,
learning rate, seed, découpage, paramètres de génération.

## Critère de succès, fixé avant le run

Cumulatif, les deux conditions ensemble :

1. l'écart de composite `vu` − `nouveau` (12,41 points pour `variation_1`) devait
   se réduire d'au moins 2 points ;
2. le composite `nouveau` devait progresser d'au moins 1 point.

La double condition écarte le faux succès : un écart réduit par simple
dégradation du groupe `vu` ne démontrerait rien.

## Résultat : hypothèse rejetée

| Métrique | `variation_1` | `variation_3` | Écart |
|---|---:|---:|---:|
| Schéma valide | 1.0000 | 1.0000 | 0 |
| `equipment_id` | 0.9875 | 0.9875 | 0 |
| macro-F1 `severity` | 0.8968 | 0.8968 | **0** |
| `requires_human_review` | 0.9875 | 0.9875 | 0 |
| Score lexical | 0.9398 | 0.9363 | −0,0035 |
| **Composite** | 96,86 | 96,80 | −0,06 |

| Groupe | `variation_1` | `variation_3` |
|---|---|---|
| `vu` (65) | 98,64 / macro-F1 0,934 | 98,64 / 0,934 |
| `nouveau` (15) | 86,23 / 0,562 | **85,92 / 0,562** |
| **Écart** | **12,41** | **12,72** |

- Condition 1 — écart réduit d'au moins 2 points : **NON**, il *augmente* de 0,31.
- Condition 2 — composite `nouveau` en hausse d'au moins 1 point : **NON**, il
  recule de 0,31.

F1 par classe identique au cas près, `critical` compris : 8 détections sur 13
dans les deux configurations.

## Contrôle : les deux modèles sont bien distincts

Des métriques aussi rigoureusement égales imposaient de vérifier qu'il ne
s'agissait pas du même adaptateur rechargé.

| Contrôle | `variation_1` | `variation_3` |
|---|---|---|
| `lora_dropout` dans `adapter_config.json` | 0.05 | 0.15 |
| SHA-256 de `adapter_model.safetensors` | `123a5bf8d6011c4e75a6…` | `fc6f28f8df7773d9d711…` |
| `train_loss` | 0,4883 | 0,4905 |

Les poids diffèrent, et **10 sorties sur 80** diffèrent textuellement. Mais
**aucune de ces 10 différences ne modifie une décision** : zéro changement de
`severity`, d'`equipment_id` ou de `requires_human_review`. Seules des
formulations varient — sur `ANN-2026S1-0003` (groupe `nouveau`), « arrêter le
compresseur, nettoyer le canal et contrôler la fuite » devient « contrôler
étanchéité puis réévaluer le capteur ». Deux phrasés, un même jugement.

Ce n'est donc pas un artefact : c'est bien un effet nul.

## Interprétation

Trois causes plausibles, non exclusives :

1. **L'entraînement est trop court.** 60 pas d'optimisation seulement. Le dropout
   est une régularisation stochastique dont l'effet s'établit sur un grand nombre
   d'itérations ; sur 60 pas, il n'a pas le temps de peser.
2. **La surface d'application est étroite.** Le dropout LoRA porte sur l'entrée
   des matrices de rang faible, soit une fraction minime des paramètres du modèle.
   Le modèle de base, figé, n'est pas régularisé du tout.
3. **0,15 reste faible** pour ce montage. Un signal aurait peut-être émergé à
   0,3, au risque d'un entraînement instable sur si peu de pas.

Le premier indice était déjà là avant l'évaluation : la perte d'entraînement,
pourtant calculée dropout actif, n'a bougé que de 0,4883 à 0,4905. Tripler le
dropout aurait dû la faire monter nettement si la régularisation mordait.

## Ce que cette expérience élimine, et ce qu'elle renforce

**Éliminé** : l'hypothèse selon laquelle la mémorisation observée serait un
problème de régularisation traitable par un hyperparamètre du montage LoRA.

**Renforcé** : le diagnostic posé dans `corpus_analysis.md` et
`error_analysis.md` — le plafond est dans les **données**, pas dans le réglage.
81 % des exemples de validation ont un quasi-jumeau dans l'entraînement ; les
erreurs se regroupent par famille de patron ; `critical` ne compte que 47
exemples d'entraînement répartis sur environ quatre familles. Aucun
hyperparamètre ne crée de la diversité absente du corpus.

Un résultat négatif proprement établi vaut mieux qu'un résultat positif douteux :
il ferme une piste et concentre l'effort sur la bonne.

## Recommandation révisée

Les leviers à privilégier ne sont plus des hyperparamètres :

1. **Découpage par famille de patron** plutôt qu'aléatoire, afin qu'aucune
   famille ne figure à la fois en entraînement et en validation. Les scores
   chuteraient — et deviendraient enfin informatifs. Relève du module 2, consacré
   à l'audit et à la préparation du corpus.
2. **Sur-échantillonnage ou pondération des exemples `critical`**, sous-représentés
   (47 sur 320) et concentrés sur peu de familles. C'est un changement de
   données, à déclarer comme expérience distincte.
3. **Contrôle programmatique d'`equipment_id`** à l'intégration : vérifier que
   l'identifiant produit figure dans le texte d'entrée. Trois lignes, et l'erreur
   de recopie d'`ANN-0247` disparaît.

Le candidat retenu reste `variation_1`. `variation_3` n'apporte rien et n'est pas
conservée comme candidat ; ses artefacts sont versionnés au titre de la
traçabilité.
