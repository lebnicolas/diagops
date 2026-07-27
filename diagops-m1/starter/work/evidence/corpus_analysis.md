# Analyse du corpus DiagOps — contrôle des annotations

**Date : 27/07/2026.** Analyse réalisée **après le gel du protocole**
(`67c873e`) et **avant l'observation de tout résultat d'évaluation**. Ce
document ne modifie ni les hypothèses, ni les prédictions, ni la règle de
décision : il documente une propriété du corpus qui conditionne
l'interprétation des mesures à venir.

Périmètre : `work/splits/train.jsonl` (320) et `work/splits/validation.jsonl`
(80). Le jeu de test final n'a pas été consulté.

## 1. Contrôles de forme — aucune anomalie

| Contrôle | Résultat |
|---|---|
| Cohérence `equipment_id` racine vs `expected_output` | 0 écart sur 400 |
| `requires_human_review: false` sur un cas `high`/`critical` | 0 cas |
| Champs textuels vides ou `evidence` absente | 0 cas |
| `confidence` hors de l'intervalle [0, 1] | 0 cas |
| Textes strictement dupliqués avec sorties contradictoires | 0 cas |
| Fuite d'`annotation_id` entre train et validation | 0 cas |

Aucune annotation n'a été modifiée. Conformément au brief, les observations
sont documentées, pas corrigées.

## 2. `confidence` est déterminée par la gravité

| Gravité | n | min | max | moyenne |
|---|---:|---:|---:|---:|
| `critical` | 60 | 0.91 | 0.99 | 0.977 |
| `low` | 60 | 0.62 | 0.95 | 0.823 |
| `high` | 177 | 0.64 | 0.94 | 0.810 |
| `medium` | 103 | 0.54 | 0.96 | 0.784 |

Les cas `critical` occupent une plage de confiance disjointe des autres
(≥ 0.91). Ce n'est pas une incohérence, mais un artefact de génération : la
confiance n'exprime pas une incertitude de diagnostic, elle est corrélée à
l'étiquette. Un modèle entraîné apprendra cette association mécaniquement.

## 3. Le corpus est produit par patrons

Les rapports sont des variations de surface d'un même gabarit. Exemple, deux
annotations de validation :

```
ANN-2026S1-0293 : Four F-17 ... ecart maximal de 2 C sur la consigne
ANN-2026S1-0193 : Four F-20 ... ecart maximal de 2 C sur la consigne
```

Textes différents (numéro de four, identifiant d'équipement), **sortie attendue
strictement identique**. Le vocabulaire est par ailleurs fortement typé par
gravité : certains termes sont jusqu'à 6,7 fois surreprésentés dans une classe.
Aucune paire de rapports lexicalement proches ne porte de gravité différente
(0 paire au-dessus de 0,72 de similarité).

Conséquence : la classification de `severity` sur ce corpus est en grande partie
un problème de **reconnaissance de marqueurs lexicaux**, pas de jugement métier.

## 4. Quasi-duplication entre entraînement et validation

Pour chacun des 80 exemples de validation, recherche du plus proche voisin dans
les 320 exemples d'entraînement (similarité de Jaccard sur les mots de 3
lettres ou plus).

| Seuil de similarité | Exemples de validation concernés |
|---|---|
| ≥ 0.95 | **65 / 80 (81 %)** |
| ≥ 0.90 | 69 / 80 (86 %) |
| ≥ 0.80 | 72 / 80 (90 %) |

Médiane de similarité : **1.00**. Moyenne : 0.92.

**Sur les 65 exemples au-dessus de 0.95, la sortie attendue est identique à
100 %** une fois neutralisés `equipment_id`, `evidence` et `confidence` — même
`symptom`, même `severity`, même `failure_hypothesis`, même
`recommended_action`.

Il ne s'agit **pas d'une fuite au sens strict** : aucun `annotation_id` n'est
partagé, aucun texte n'est strictement dupliqué, et le découpage appliqué est
bien celui imposé par le brief (seed 42). La duplication est **dans le corpus
source** : le découpage aléatoire répartit mécaniquement les exemplaires d'un
même patron des deux côtés.

### Ce que cela implique pour l'interprétation

Pour 81 % de la validation, un modèle entraîné n'a rien à généraliser : il lui
suffit de reconnaître un patron déjà rencontré, de recopier l'identifiant
d'équipement — fourni dans le texte d'entrée — et de restituer la sortie
mémorisée.

Les gains mesurés sur la validation **surestimeront donc la capacité réelle de
généralisation**. Un macro-F1 élevé sur `severity` ne démontrera pas que le
modèle sait évaluer une gravité, mais qu'il a mémorisé l'association entre un
gabarit de rapport et son étiquette.

## 5. Analyse stratifiée proposée

Sans modifier le protocole gelé ni la règle de décision, les métriques seront
**également** reportées séparément sur deux sous-ensembles, définis avant
observation des résultats et figés dans
`work/evidence/validation_proximite_train.json` :

| Groupe | Effectif | Définition |
|---|---:|---|
| `vu` | 65 | plus proche voisin dans le train à Jaccard ≥ 0.95 |
| `nouveau` | 15 | plus proche voisin sous ce seuil |

Répartition du groupe `nouveau` : `high` 8, `low` 4, `medium` 2, `critical` 1.

Un écart important entre les deux groupes constituera la preuve directe de la
mémorisation. Le groupe `nouveau` reste toutefois trop petit (15 exemples, dont
une seule occurrence `critical`) pour fonder une décision : il sert
d'**indicateur d'alerte**, au même titre que `requires_human_review`.

La décision de retenir ou rejeter un candidat reste régie par la règle figée
dans `protocol_m1.md`, appliquée sur l'ensemble des 80 exemples.

## 6. Limites à porter dans la note de décision

1. Corpus synthétique produit par patrons — la data card exclut déjà toute
   généralisation à un site réel, cette analyse en donne la mesure concrète.
2. 81 % de la validation possède un quasi-jumeau dans l'entraînement : les
   scores de validation mesurent en grande partie de la mémorisation.
3. `confidence` est déterminée par la gravité et n'exprime aucune incertitude
   exploitable.
4. `severity` est prédictible à partir de marqueurs lexicaux, ce qui rend la
   tâche plus facile qu'un diagnostic réel.
5. Le sous-ensemble permettant d'observer une généralisation ne compte que 15
   exemples.

## Reproduction

Les mesures de ce document sont recalculables à partir des seuls fichiers
`work/splits/train.jsonl` et `work/splits/validation.jsonl`, dont les empreintes
SHA-256 figurent dans `work/splits/split_manifest.json` et dans le protocole.
