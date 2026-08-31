---
module: M4
brief: brief 1 — présentiel
etat: candidat gelé le 31/08/2026
maj: 2026-08-31
---

# Model card — détecteur de provenance DiagOps

## Identité

| | |
|---|---|
| Nom | détecteur de provenance de fenêtres capteurs |
| Version | candidat M4, gelé le **31/08/2026** |
| Empreinte | `164d05b129ce5e4107cdc27279bc198c…` (`results/gel/gel.json`) |
| Algorithme | régression logistique, `class_weight="balanced"`, `StandardScaler` dans le pipeline |
| Graine | `20260831` |
| Artefact | `results/gel/candidat_m4.joblib`, 1,9 ko |

## Usage prévu

**Ce que le modèle fait** : il estime si une fenêtre de 30 mesures capteur
consécutives est **réelle** ou **fabriquée**.

**Utilisateurs prévus** : l'équipe data de DiagOps, en amont d'un traitement —
pour écarter ou signaler des fenêtres dont la provenance est douteuse avant
qu'elles n'entrent dans un apprentissage.

**Décision assistée, jamais automatique** : la sortie est un signalement soumis à
revue. Aucune suppression automatique de données n'est prévue ni recommandée.

### Usages exclus

| Usage | Pourquoi il est exclu |
|---|---|
| **prédire une panne** | rien dans le lot ne relie une fenêtre à une défaillance ultérieure. `decision_m3.md` l'écrit également |
| **juger la qualité d'une mesure** | une fenêtre réelle peut violer le contrat capteur (5 sur 19 ici), une fenêtre fabriquée peut être irréprochable |
| **décider seul de l'exclusion d'une donnée** | rappel de 0,636 : le modèle laisse passer 4 fenêtres fabriquées sur 11 |
| **s'appliquer à `temperature_c`** | segment manqué en totalité (voir plus bas) |
| **s'appliquer hors du parc synthétique DiagOps** | aucune donnée industrielle réelle n'a été vue |

## Cible et données

**Cible** : `provenance` ∈ {`réelle`, `fabriquée`}, classe positive `fabriquée`.
Étiquette constante à l'intérieur d'une fenêtre — vérifié sur 30 fenêtres / 30.

**Unité de décision** : la fenêtre (`window_id`), 30 mesures d'un capteur sur un
équipement, au pas de 6 h.

| Jeu | Lignes | Fenêtres | Fabriquées | Équipements |
|---|---:|---:|---:|---:|
| Calibration | 900 | **30** | 11 | 22 |
| Test (scellé) | 1 800 | 60 | *inconnu* | 32 |

**Provenance des données** : lot pédagogique `data_pack/2026-S1/model_eval/`,
généré côté formateur. Aucune donnée industrielle réelle.

## Features — 19, toutes intrinsèques à la fenêtre

| Famille | Poids du signal | Exemples |
|---|---:|---|
| **structure temporelle** | **38,4 %** | autocorrélations de rang 1, 2 et 4 ; part de changements de signe |
| forme de la distribution | 27,7 % | asymétrie, aplatissement, plus longue répétition |
| régularité de la grille | 17,7 % | part de pas non nominaux, écart-type du pas |
| contrat capteur | 9,3 % | valeurs absentes, sentinelles, hors plage, précision décimale |
| dispersion relative | 7,0 % | coefficient de variation, étendue relative |

**Exclusions délibérées** : `sensor_name` et `equipment_id` (sur 30 fenêtres, le
modèle apprendrait « température ⇒ réelle »), et toute statistique calculée sur
l'ensemble du lot (elle ferait entrer dans une fenêtre l'information des autres).

Les features portant une échelle sont **sans dimension** — des rapports — ce qui
les rend comparables d'un capteur à l'autre sans nommer le capteur.

## Protocole d'évaluation

`StratifiedGroupKFold` sur **`equipment_id`**, 5 plis × 5 répétitions.
Groupement sur l'équipement et non sur la fenêtre : 20 des 22 équipements
réapparaissent dans le test, et 4 portent les deux provenances. **Contrôle de
fuite bloquant : 0 équipement ne traverse un pli sur 25.**

Métrique de décision : **F1 sur `fabriquée`**, précision et rappel rapportés à
part. Le F1 traite les deux erreurs à égalité — c'est une hypothèse assumée,
faute de donnée de coût réelle.

## Métriques

### Globales — F1 hors pli sur les 30 fenêtres, 5 partitions

| | F1 | Écart-type | Min | Max | Précision | Rappel | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Candidat** | **0,694** | 0,068 | 0,600 | 0,800 | 0,700 | 0,636 | 0,737 |
| Forêt aléatoire | 0,541 | 0,055 | 0,455 | 0,600 | 0,625 | 0,455 | 0,681 |
| Baseline M3 | 0,375 | — | — | — | 0,600 | 0,273 | — |

Matrice de confusion (30 fenêtres) : **7 VP, 3 FP, 4 FN, 16 VN**.

### Par segment

| Capteur | Fenêtres | Fabriquées | F1 |
|---|---:|---:|---:|
| `pressure_bar` | 3 | 1 | 1,000 |
| `vibration_mm_s` | 8 | 3 | 0,750 |
| `rpm` | 4 | 2 | 0,667 |
| `current_a` | 6 | 4 | 0,571 |
| **`temperature_c`** | 9 | 1 | **0,000** |

> [!warning] `temperature_c` n'est pas couvert par la preuve
> Une seule fenêtre fabriquée sur neuf, et le modèle ne la trouve pas — les deux
> candidats échouent identiquement. Sur un seul cas positif, ce 0,000 ne mesure
> rien de stable : il signale que ce segment est hors du périmètre de validité.

### Coût

| | |
|---|---|
| Latence | **0,06 ms** par fenêtre |
| Mémoire à l'ajustement | 56 ko |
| Artefact | 1,9 ko |
| Coût par prédiction | nul — CPU, aucun service, aucune API |

## Seuil de décision

**0,50**, conservé après mesure et non par défaut.

Un réglage en validation imbriquée donne exactement le même F1 (0,6940 avec et
sans, au dix-millième près) et **dégrade** la forêt. Les 25 plis choisissent des
seuils de 0,06 à 0,84 sans converger : sur 24 observations d'entraînement dont 9
positives, la courbe F1/seuil est en marches et de larges plages sont
équivalentes. **Le seuil n'est pas identifiable à cet effectif.**

À titre de repère : un réglage naïf — calé et mesuré sur les mêmes données —
aurait annoncé 0,754, soit **+0,060 de gain qui n'existe pas**.

## Limites et biais

1. **30 fenêtres, 11 positives.** L'écart-type de 0,068 mesure la sensibilité au
   découpage d'un même jeu, pas l'erreur d'échantillonnage. Aucun intervalle de
   confiance n'est calculable sérieusement.
2. **Le rappel plafonne à 0,636** — 4 fenêtres fabriquées sur 11 passent.
3. **Un segment entier manqué** (`temperature_c`).
4. **Déséquilibre par capteur** : de 1 fabriquée sur 9 (`temperature_c`) à 4 sur
   6 (`current_a`). C'est ce déséquilibre qui a motivé l'exclusion de
   `sensor_name` des features.
5. **Données entièrement synthétiques.** Le modèle détecte les fabrications *du
   générateur du formateur*. Rien ne dit qu'il détecterait celles d'un autre
   procédé — et le brief 2 du M3 a montré qu'un générateur amélioré devient plus
   difficile à distinguer.
6. **Aucun résultat sur l'oracle scellé** au moment de l'écriture.

## Risques et supervision humaine

| Risque | Conséquence | Atténuation |
|---|---|---|
| **faux négatif** (4 sur 11) | une fenêtre fabriquée entre dans un apprentissage comme une mesure ; une fois la provenance perdue, c'est indétectable | signalement, jamais suppression automatique ; provenance conservée en amont (M3) |
| **faux positif** (3 sur 19) | une mesure authentique est écartée, sur un parc couvert à 8,65 % | revue humaine avant toute exclusion |
| **surconfiance** | le F1 de 0,694 est cité comme performance générale | périmètre de validité écrit ; `temperature_c` explicitement hors couverture |
| **dérive du générateur** | un procédé de fabrication différent échappe au modèle | réévaluation à chaque nouvelle livraison |

**Supervision humaine requise** : la sortie du modèle est une **aide au tri**.
Toute exclusion de donnée reste une décision humaine.

## Version, empreinte et réévaluation

Le gel du 31/08/2026 fige : modèle, 19 features, seuil, graine, partition. Toute
modification de l'un d'eux **impose un nouveau gel** et interdit la comparaison à
ce résultat (`docs/protocole_evaluation.md`, règle de changement).

**Réévaluation obligatoire si** :

- le formateur rend un résultat sur l'oracle incohérent avec 0,694 ± 0,068 ;
- une nouvelle livraison de données arrive (`2026-S2`, prévue en M5) ;
- le procédé de génération change côté producteur ;
- le modèle est envisagé hors du parc synthétique DiagOps.

**Statut de déploiement : `évaluer davantage`** — voir
`docs/matrice_decision.md`. Le modèle n'est pas adopté, et il ne doit pas l'être
avant le résultat de l'oracle.
