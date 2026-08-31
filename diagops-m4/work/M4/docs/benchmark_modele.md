---
module: M4
brief: brief 1 — présentiel
etat: étape 3 terminée
maj: 2026-08-31
---

# Benchmark du modèle simple

Tous les chiffres viennent de `results/modele/modele.json`, produit par
`run_modele.py` sous le protocole gelé de `docs/protocole_evaluation.md`.
**Le test scellé n'a pas été chargé.**

---

## Baseline M3 figée

Sept règles de contrat capteur, livrées par le formateur et non réécrites.

| Niveau | VP | FP | FN | Précision | Rappel | **F1** |
|---|---:|---:|---:|---:|---:|---:|
| ligne (métrique officielle) | 90 | 61 | 240 | 0,596 | 0,273 | **0,374** |
| fenêtre (agrégation ≥ 2 déclarée) | 3 | 2 | 8 | 0,600 | 0,273 | **0,375** |

Elle détecte 3 fenêtres fabriquées sur 11. Ce qu'elle regarde — unité, grille,
plage, sentinelle, précision — relève du **contrat**, pas de l'authenticité.

## Candidats et justification

Les deux candidats de `configs/model.yaml`, chacun retenu contre l'autre.

| Candidat | Pourquoi celui-là | Contre quoi |
|---|---|---|
| **Régression logistique** | frontière linéaire, coefficients lisibles, robuste à 30 observations | contre la forêt : moins de capacité, donc moins de sur-ajustement sur un effectif minuscule |
| **Forêt aléatoire** | capte les interactions et les seuils, aucune hypothèse de forme | contre la logistique : le prix est la variance sur 30 observations |

Les deux avec `class_weight="balanced"` — 11 positifs sur 30 — et la mise à
l'échelle **dans le pipeline**, donc ajustée sur le pli d'entraînement seul.

## Features

**19 features par fenêtre**, toutes intrinsèques à la fenêtre et sans dimension
quand elles portent une échelle. Cinq familles : structure temporelle, régularité
de la grille, forme de la distribution, dispersion relative, contrat capteur.

**Trois exclusions délibérées :**

| Exclu | Motif |
|---|---|
| `sensor_name` | `temperature_c` compte 1 fabriquée pour 8 réelles — sur 30 fenêtres, le modèle apprendrait « température ⇒ réelle » |
| `equipment_id` | même raison, et c'est la colonne de groupe de la partition |
| toute statistique calculée sur le lot entier | ferait entrer dans une fenêtre l'information des autres, y compris celles du pli de validation |

## Splits et contrôle de fuite

`StratifiedGroupKFold` sur `equipment_id`, 5 plis × 5 répétitions = 25 plis.
**Aucun équipement ne traverse un pli** — contrôle bloquant à chaque exécution.
1 pli sur 25 ne contient aucun positif : son F1 est indéfini, il est exclu du
calcul et le compte est rapporté.

## Résultats

### Ce que la mesure naïve raconte, et pourquoi elle ne suffit pas

| Candidat | F1 moyen par pli | Écart-type | Min | Max |
|---|---:|---:|---:|---:|
| Régression logistique | 0,6632 | **0,3509** | 0,000 | 1,000 |
| Forêt aléatoire | 0,5542 | **0,3780** | 0,000 | 1,000 |

Un F1 qui va de 0 à 1 selon le pli. La dispersion est telle que l'écart à la
baseline (+0,288) reste **sous** l'écart-type — au sens du seuil grossier, aucun
gain ne serait démontrable.

**Mais cette dispersion ne mesure pas l'incertitude sur le gain.** Elle mesure la
difficulté inégale des plis : sur un pli de 3 fenêtres dont 1 positive, une seule
prédiction fait basculer le F1 de 0 à 1 — pour le modèle **comme pour la
baseline**. Il faut donc comparer sur les mêmes plis, ou changer de maille.

### Comparaison appariée, pli par pli

| Candidat | Plis gagnés | Perdus | Égaux | Différence moyenne |
|---|---:|---:|---:|---:|
| Régression logistique | **16** | 6 | 2 | +0,259 |
| Forêt aléatoire | 13 | 8 | 3 | +0,150 |

L'appariement annule la difficulté commune du pli, et la logistique gagne deux
plis sur trois. Mais l'écart-type des différences reste à 0,61 : sur ces
effectifs, un pli isolé pèse trop lourd.

### La mesure décisive — F1 hors pli, sur les 30 fenêtres

Dans une répétition, les 5 plis de validation **partitionnent** les 30 fenêtres :
chacune est prédite une fois et une seule. Le F1 qui en découle porte donc sur
les 30 fenêtres — exactement comme celui de la baseline. Cinq répétitions
donnent cinq partitions différentes du même jeu.

| Candidat | F1 moyen | Écart-type | Min | Max | Écart / baseline |
|---|---:|---:|---:|---:|---:|
| **Régression logistique** | **0,6940** | 0,0684 | **0,6000** | 0,8000 | **+0,3190** |
| Forêt aléatoire | 0,5414 | 0,0545 | 0,4545 | 0,6000 | +0,1664 |
| Baseline M3 | 0,3750 | — | — | — | — |

> **Le minimum des cinq partitions dépasse la baseline pour les deux candidats.**
> Le gain n'est pas un artefact de tirage : il tient sur les cinq.

À la même maille, la dispersion tombe de 0,35 à 0,068 — c'est le même jeu, la
même méthode, et une maille de mesure qui ne détruit plus l'information.

| Candidat | Précision | Rappel | ROC-AUC | VP | FP | FN | Latence | Mémoire |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Régression logistique | 0,700 | 0,636 | 0,737 | 7 | 3 | 4 | **0,06 ms** | **56 ko** |
| Forêt aléatoire | 0,625 | 0,455 | 0,681 | 5 | 3 | 6 | 1,78 ms | 389 ko |
| Baseline M3 | 0,600 | 0,273 | — | 3 | 2 | 8 | — | — |

La logistique domine sur **tous** les axes simultanément : qualité, rappel,
ROC-AUC, latence (×29) et mémoire (×7). Il n'y a pas d'arbitrage à rendre entre
les deux candidats.

## Ce qui porte le signal

Poids moyens sur les 25 plis, regroupés par famille :

| Famille | Régression logistique | Forêt |
|---|---:|---:|
| **structure temporelle** | **38,4 %** | **57,7 %** |
| forme de la distribution | 27,7 % | 28,5 % |
| régularité de la grille | 17,7 % | 0,2 % |
| **contrat capteur** | **9,3 %** | **0,2 %** |
| dispersion relative | 7,0 % | 13,4 % |

Features de tête pour la logistique : `plus_longue_repetition` (0,99),
`autocorr_lag2` (0,65), `part_changements_de_signe` (0,58), `autocorr_lag4` (0,43).

> **C'est l'explication du gain, et elle valide l'arbitrage A3.** Le contrat
> capteur — tout ce que la baseline sait regarder — ne pèse que 9,3 % du signal
> pour la logistique et 0,2 % pour la forêt. Le modèle ne bat pas la baseline en
> appliquant mieux ses règles : **il regarde ailleurs**, précisément là où le
> brief 2 du M3 avait établi que se trouve la signature d'une fabrication.

## Le seuil de décision — testé, et conservé à 0,5

Toutes les mesures ci-dessus utilisent le seuil **0,5**, celui que `predict()`
applique par défaut. Ce n'était pas une décision : avec une ROC-AUC de 0,737, le
modèle ordonne les fenêtres nettement mieux que ne le suggère son F1, et un autre
seuil pouvait déplacer le compromis précision / rappel.

Trois estimations produites par `run_seuil.py`, dont une volontairement biaisée
pour rendre l'optimisme visible :

| Candidat | Seuil 0,5 | **Seuil réglé (imbriqué)** | Optimisé sur l'ensemble |
|---|---:|---:|---:|
| Régression logistique | 0,6940 ± 0,0684 | **0,6940 ± 0,0684** | *0,7540 ± 0,0389* |
| Forêt aléatoire | 0,5414 ± 0,0545 | **0,5194 ± 0,0377** | *0,6404 ± 0,0152* |

La colonne « réglé (imbriqué) » choisit le seuil sur une validation interne du
**seul jeu d'entraînement** de chaque pli, puis l'applique au pli de validation
qu'il n'a jamais vu. La dernière colonne règle et mesure sur les mêmes données :
c'est une **borne haute**, jamais une performance.

**Trois résultats, aucun n'était acquis.**

1. **Le réglage n'apporte rien à la régression logistique** — 0,6940 dans les deux
   cas, au dix-millième près. Le seuil 0,5 n'est plus un héritage de
   bibliothèque : c'est désormais un choix mesuré.
2. **Il dégrade la forêt** — 0,541 → 0,519. Un seuil réglé sur 24 observations
   généralise moins bien que la valeur par défaut.
3. **L'optimisme d'un réglage naïf vaut +0,060 de F1.** C'est exactement ce qu'on
   aurait rapporté à tort en réglant le seuil et en le mesurant sur les mêmes
   données — un gain qui n'aurait existé que dans le rapport.

### Pourquoi le seuil n'est pas identifiable ici

Les 25 plis ont choisi des seuils allant de **0,06 à 0,84** :

| Seuil retenu | 0,06–0,32 | 0,41–0,44 | **0,50** | 0,57–0,63 | 0,76–0,84 |
|---|---:|---:|---:|---:|---:|
| Plis | 6 | 3 | **8** | 4 | 4 |

Aucune convergence. Sur 24 fenêtres d'entraînement dont 9 positives, la courbe
F1 / seuil est en marches d'escalier — chaque fenêtre qui bascule déplace le F1
d'un cran, et de larges plages de seuils sont équivalentes :

| Seuil | 0,20 | 0,30 | 0,40 | **0,50** | 0,60 | 0,70 | 0,80 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Précision | 0,667 | 0,667 | 0,667 | 0,700 | 0,875 | 0,875 | 0,875 |
| Rappel | 0,727 | 0,727 | 0,727 | 0,636 | 0,636 | 0,636 | 0,636 |
| F1 | 0,696 | 0,696 | 0,696 | 0,667 | 0,737 | 0,737 | 0,737 |

> **Décision : seuil maintenu à 0,50.** Le régler ne rapporte rien sur le
> candidat retenu, la valeur n'est pas identifiable sur cet effectif, et une
> valeur choisie sur du bruit se transporterait mal sur le test scellé. Ce que ce
> travail établit n'est pas un meilleur seuil, mais que **le seuil par défaut est
> défendable** — et de combien un réglage naïf aurait embelli le résultat.

## Stabilité par segment

Par capteur, sur la première répétition (régression logistique) :

| Capteur | Fenêtres | Fabriquées | VP | FP | FN | F1 |
|---|---:|---:|---:|---:|---:|---:|
| `vibration_mm_s` | 8 | 3 | 3 | 2 | 0 | 0,750 |
| `pressure_bar` | 3 | 1 | 1 | 0 | 0 | **1,000** |
| `rpm` | 4 | 2 | 1 | 0 | 1 | 0,667 |
| `current_a` | 6 | 4 | 2 | 1 | 2 | 0,571 |
| **`temperature_c`** | 9 | 1 | 0 | 0 | 1 | **0,000** |

> [!warning] Le segment `temperature_c` est manqué en totalité
> Une seule fenêtre fabriquée sur 9, et le modèle ne la trouve pas. Les deux
> candidats échouent identiquement.
>
> Ce n'est pas un F1 de 0,000 à interpréter comme une contre-performance : c'est
> **un seul cas**, et le segment est celui où le déséquilibre est le plus fort.
> Une métrique par segment sur 1 positif ne mesure rien de stable — elle signale
> seulement que ce segment n'est pas couvert par la preuve.

Les F1 par capteur vont de 0,00 à 1,00 sur des effectifs de 3 à 9 fenêtres.
**Aucun de ces chiffres ne doit être cité isolément.**

## Limites et décision

**Ce qui est établi.** Sur la calibration, la régression logistique atteint un F1
de 0,694 contre 0,375 pour la baseline, et le gain tient sur les cinq partitions
testées. Il vient de features de structure temporelle que la baseline n'exploite
pas. Elle est aussi la plus légère des deux candidats.

**Ce qui ne l'est pas.**

1. **30 fenêtres, 11 positives.** Tout ce qui précède est mesuré sur un effectif
   qui interdit une estimation fine. L'écart-type de 0,068 est calculé sur
   5 partitions **du même jeu** — il mesure la sensibilité au découpage, pas
   l'erreur d'échantillonnage.
2. **Le rappel plafonne à 0,64** : 4 fenêtres fabriquées sur 11 restent
   manquées. C'est mieux que les 8 de la baseline, ce n'est pas un détecteur.
3. **Un segment entier n'est pas couvert** (`temperature_c`).
4. **Rien n'est prouvé sur le test scellé.** Le résultat officiel sera calculé
   par le formateur après gel du candidat, et c'est le seul qui entrera dans la
   décision de déploiement.
5. **La cible reste la provenance.** Ni la qualité, ni la panne future.

**Candidat retenu pour le gel** : `regression_logistique`, 19 features,
`class_weight="balanced"`, graine 20260831.

**Décision de déploiement** : elle n'est pas prise ici. Elle appartient à la
matrice de décision (`docs/matrice_decision.md`), après le travail sur le
retrieval, l'agent et les menaces — et elle devra intégrer le résultat du
formateur sur l'oracle.
