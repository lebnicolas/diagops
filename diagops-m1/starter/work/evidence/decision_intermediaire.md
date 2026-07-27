# Décision intermédiaire — Brief 1

Date : 27/07/2026. Auteur : Nicolas Lebon.
Protocole de référence : `protocol_m1.md`, gelé en `67c873e` (contenu introduit
par `aa0c036`), avant toute mesure.

## Décision

**Candidat retenu : `variation_1`** — LoRA r=16, α=32, dropout 0.05, appliqué à
`q_proj`, `k_proj`, `v_proj`, `o_proj`, `gate_proj`, `up_proj`, `down_proj`,
3 epochs, learning rate 2e-4, seed 42.

Adaptateur : `work/runs/variation_1/adapter`.
Configuration : `configs/variation_1.yaml`.

Le candidat est **gelé** en vue du Brief 2. Aucun hyperparamètre ne sera ajusté
à partir du jeu de test final, qui n'a pas été consulté durant ce brief.

Cette décision est **conditionnelle** : elle retient un candidat pour la
qualification finale, elle ne préjuge pas de sa promotion. Deux réserves
documentées plus bas pèseront sur cette dernière.

## Fondement : la règle de décision, écrite avant les mesures

Les six conditions de retenue du protocole, appliquées au candidat évalué
adaptateur fusionné :

| Critère | Seuil | Mesuré | |
|---|---|---|---|
| JSON brut parseable | ≥ 0.95 | **1.000** | ✓ |
| Schéma valide après validation | ≥ 0.95 | **1.000** | ✓ |
| macro-F1 `severity` | ≥ baseline + 0.10 | **0.8968** (baseline 0.000) | ✓ |
| Aucune classe de `severity` à F1 nul | > 0 | min = `critical` **0.375** | ✓ |
| Score lexical des champs textuels | ≥ baseline | **0.9401** (baseline 0.000) | ✓ |
| Latence p95 | ≤ baseline × 1.20 | **× 1.008** | ✓ |

Aucune des quatre conditions de rejet n'est déclenchée.

Progression face à la baseline : score composite de **18,13 à 96,87**.

## Départage entre les trois candidats

`variation_2` obtient le meilleur composite brut (98,11 contre 96,86). La règle
de départage gelée prévoit : *composite le plus élevé ; à moins de 2 points
d'écart, le candidat le moins coûteux en latence p95.*

L'écart est de **1,25 point**, sous le seuil de 2. Le critère de coût s'applique
donc, et il désigne `variation_1`.

Cette conclusion, issue d'une règle écrite à l'aveugle, est confirmée par une
analyse que la règle n'anticipait pas — la stratification vu/nouveau :

| Système | `vu` (65) | `nouveau` (15) |
|---|---|---|
| `reference` | 91,57 / macro-F1 0,795 | 81,82 / 0,514 |
| `variation_1` | 98,64 / 0,934 | **86,23 / 0,562** |
| `variation_2` | 100,00 / 1,000 | **86,28 / 0,562** |

`variation_2` est parfaite sur les exemples possédant un quasi-jumeau dans
l'entraînement, et **strictement équivalente** à `variation_1` sur les exemples
inédits. La totalité de son avantage provient de la mémorisation. Elle coûte par
ailleurs plus cher : 641 s d'entraînement contre 305 s.

À généralisation égale, retenir le système le moins coûteux.

## Deux mesures corrigées en cours d'expérience

Le protocole n'a pas été modifié. Deux **méthodes de mesure** l'ont été, chacune
documentée par une preuve avant/après.

**1. Adaptateur non fusionné.** Le run initial de la référence mesurait une
latence p95 de 15,07 s, déclenchant le critère de rejet. Diagnostic : les
couches LoRA, non repliées dans le modèle de base, étaient recalculées à chaque
token — coût par caractère de 30,8 ms contre 16,8 ms pour la baseline, alors que
les sorties n'étaient que 1,22 fois plus longues. Après `merge_and_unload()`,
p95 à 7,49 s. Le run fusionné est **légèrement moins favorable en qualité**
(composite 89,86 contre 90,02) : il a été retenu pour corriger un biais, non
pour embellir un résultat.

**2. Dérive thermique.** Les latences dérivaient à l'intérieur d'un même run, sur
données homogènes, dans un rapport allant de 0,44 à 2,33 entre premier et
dernier tiers — et chaque système avait été mesuré dans une session distincte.
Un banc dédié (`tools/latency_benchmark.py`, même session, alternance avec
inversion d'ordre, préchauffage, dérive publiée) donne une mesure stable : dérive
résiduelle de 1,03 et 0,98, ratio p95 candidat/baseline de **1,008**.

Sans ces deux corrections, un candidat conforme aurait été rejeté deux fois sur
un artefact de mesure.

## Réserves

**1. La classe `critical` reste insuffisamment détectée.**
`variation_1` détecte 8 cas critiques sur 13 (F1 0,375 sur le run fusionné,
0,76 sur le run standard). Les 5 échecs sont **tous** des sous-estimations —
aucune sur-estimation. Sur un outil de maintenance industrielle, c'est le mode
de défaillance le plus coûteux.

Ma règle de décision ne l'attrape pas : le critère « aucune classe à F1 nul »
laisse passer 0,375. C'est un **angle mort assumé** de la règle. Le protocole
étant gelé, il n'a pas été réécrit ; l'amendement est proposé pour le Brief 2.

**2. La généralisation est faible et mal mesurée.**
81 % des exemples de validation possèdent un quasi-jumeau dans l'entraînement,
avec sortie identique à 100 % hors `equipment_id`, `evidence` et `confidence`.
Sur les 15 exemples inédits, le macro-F1 tombe à 0,562 contre 0,934. Le seul cas
`critical` inédit (ANN-0039) est raté par les trois candidats.

Ce n'est pas une faute de méthode — aucun `annotation_id` n'est partagé et le
découpage imposé (seed 42) a été respecté : la duplication est dans le corpus
source. Mais elle interdit de présenter les scores de validation comme une
mesure de généralisation.

## Ce que cette décision ne dit pas

- Que le candidat comprend le diagnostic de maintenance. Il a appris un format et
  des associations lexicales sur un corpus synthétique produit par patrons.
- Que `variation_2` est meilleure sur `critical`. Ses 12 détections sur 13
  portent sur des patrons vus ; elle échoue sur le cas inédit comme les autres.
- Que les scores tiendraient sur des rapports réels. La data card exclut
  explicitement cette généralisation.

## Prédictions gelées : quatre démenties sur sept

| Prédiction écrite avant les runs | Résultat | |
|---|---|---|
| Baseline : JSON parseable < 0.80 | 1.000 | ✗ |
| Baseline : schéma < 0.70, macro-F1 < 0.40, lexical < 0.50 | 0.000 partout | ✓ |
| V1 : gain < 5 points de composite | +6,84 | ✗ |
| V1 : lexical +0.02 à +0.05 | +0,272 | ✗ |
| V1 : pas de gain net sur `severity` | +0,139 | ✗ |
| V2 : ne dépassera pas la référence | +8,09 | ✗ |
| V2 : par mémorisation | confirmé par la stratification | ✓ |

L'erreur d'analyse principale porte sur la baseline : j'attendais des échecs de
**forme** (blocs markdown, texte parasite). Le modèle maîtrise parfaitement la
syntaxe JSON ; ce qu'il ignore, c'est le **contrat**. Il produit ses propres clés
en français — `diagnostic` dans 65 cas sur 80, `identifiant_rapport` dans 21.
Distinction que je n'avais pas faite en rédigeant le protocole.

Seconde erreur : j'attendais que le surapprentissage de `variation_2` se
manifeste par une **dégradation**. Il s'est manifesté par un **gain illusoire**,
bien plus difficile à détecter — et invisible sans la stratification, figée avant
tout résultat.

## Amendements proposés pour le Brief 2

1. **Remplacer le critère « aucune classe à F1 nul » par un plancher de rappel
   sur `critical`.** Le rappel mesure les dangers manqués ; le F1 les dilue dans
   la précision. Valeur à fixer avant l'ouverture du test.
2. **Reporter systématiquement les métriques stratifiées** vu/nouveau, et fonder
   l'appréciation de la généralisation sur le second groupe.
3. **Mesurer la latence exclusivement au banc contrôlé**, adaptateur fusionné.
4. **Ajouter un contrôle programmatique d'`equipment_id`** à l'intégration :
   vérifier que l'identifiant produit figure dans le texte d'entrée. Supprime
   l'erreur de recopie observée sur ANN-0247, sans toucher au modèle.

## Trame de restitution — 5 minutes

1. **La question et le plancher** *(45 s)* — la baseline produit du JSON valide
   mais ignore le contrat : composite 18,1, aucune clé attendue, macro-F1 nul.
2. **Le gain, et ce qu'il vaut** *(1 min)* — composite 96,9, schéma valide à
   100 %. Mais 81 % de la validation a un quasi-jumeau dans l'entraînement.
3. **La variation qui semblait gagner** *(1 min 15)* — `variation_2`, meilleur
   composite, parfaite sur les exemples vus, identique à `variation_1` sur les
   inédits. Sans stratification, elle était promue.
4. **Deux mesures qu'il a fallu corriger** *(1 min)* — adaptateur non fusionné
   puis dérive thermique. Le candidat a failli être rejeté deux fois sur des
   artefacts.
5. **La décision et sa réserve** *(1 min)* — `variation_1` retenue, 6 critères
   sur 6. Réserve : 5 sous-estimations sur 13 cas critiques, et un angle mort de
   ma propre règle que je n'ai pas réécrite après coup.

## Suite

- **A7 — revue contradictoire** : reste à faire, nécessite un relecteur externe.
  Trois objections sont déjà instruites et documentées : la quasi-duplication à
  81 %, l'artefact de la métrique `equipment_id` sur les cas `null`, et
  l'instabilité des mesures de latence.
- **Brief 2** : reproduction depuis un environnement propre, ouverture unique du
  test final, 20 perturbations de robustesse, intégration derrière `/diagnose`
  sans modification du contrat M0.
