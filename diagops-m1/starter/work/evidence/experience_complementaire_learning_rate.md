# Expérience complémentaire — learning rate 2e-4 → 1e-4

**Statut** : expérience postérieure au gel du protocole (`67c873e`) et à la
décision intermédiaire (`25f4f42`). Elle ne remet pas en cause la décision : le
candidat retenu reste `variation_1`.

**Hypothèse commitée avant exécution** : `11b4be2`. L'antériorité de la
prédiction chiffrée et de la règle de lecture sur le résultat est vérifiable
dans l'historique git.

## Question

`variation_3` a testé l'axe **régularisation** — tripler le dropout LoRA — et n'a
produit aucun effet décisionnel. La conclusion tirée alors était que le plafond
de généralisation tient au corpus et non au réglage. Un axe restait ouvert :
l'**optimisation**. C'est celui que teste `variation_4`.

Une seule variable change par rapport à `variation_2` : `training.learning_rate`,
de 2e-4 à 1e-4. Rang, α, dropout, modules cibles, nombre d'epochs, seed,
découpage et paramètres de génération sont identiques. L'évaluation se fait
adaptateur **non fusionné**, chemin sur lequel `variation_2` a été mesurée — en
changer aurait introduit une seconde variable.

Le référentiel de comparaison est donc `variation_2`, pas la référence : contre
cette dernière, deux variables bougeraient (epochs *et* learning rate).

### Budget d'optimisation

320 exemples, lot effectif de 16 : 20 pas par epoch, 100 pas sur 5 epochs. Le
produit `epochs × learning_rate` vaut 5e-4 pour `variation_4`, contre 1e-3 pour
`variation_2` et 6e-4 pour la référence. `variation_4` parcourt une distance
totale **inférieure à celle de la référence**, répartie sur des pas plus fins.
Ce n'est pas un entraînement plus long et plus doux : c'est un entraînement plus
court en distance.

## Prédiction, écrite avant le run

| Grandeur | `variation_2` | Prédit | Mesuré | |
|---|---:|---|---:|---|
| Composite `vu` | 100,00 | 97 – 99,5 | **96,80** | ✗ |
| Composite `nouveau` | 86,28 | 85,5 – 87,0 | **83,40** | ✗ |
| macro-F1 `severity` `nouveau` | 0,5615 | 0,54 – 0,58 | **0,5139** | ✗ |
| Schéma valide | 1,000 | 1,000 | **0,9875** | ✗ |

Quatre prédictions, quatre démenties, toutes dans le même sens : la dégradation
est plus forte que prévu. La direction générale — recul sur `vu`, aucun gain sur
`nouveau` — était juste ; l'amplitude ne l'était pas.

## Verdict : l'expérience n'a pas tranché

La règle de lecture prévoyait trois issues. La troisième s'est déclenchée :

> Si les métriques de forme se dégradent — schéma valide sous 1.0 — le budget
> d'optimisation réduit ne suffit plus à apprendre le contrat de sortie, et
> l'expérience mesure un sous-apprentissage, pas un effet d'optimisation. Dans
> ce troisième cas les composites `vu` et `nouveau` ne sont pas interprétables
> comme un test de généralisation.

Le schéma valide tombe à 0,9875. La `train_loss` corrobore le diagnostic
indépendamment des métriques de validation : **0,6561 contre 0,4464** pour
`variation_2`. Le modèle s'ajuste moins bien aux données d'entraînement, comme
le calcul de budget le laissait attendre.

**La thèse du plafond corpus n'est donc ni confirmée ni réfutée par ce run.** La
règle a fonctionné : elle a attrapé une issue que je ne jugeais pas la plus
probable, et elle m'interdit de lire le résultat comme il m'arrangerait.

### L'échec de schéma, en détail

Un seul cas, `ANN-2026S1-0035`. Le JSON est parfaitement formé ; c'est la valeur
qui sort de l'énumération :

```json
{"equipment_id":"EQ-MIX-001","symptom":"rotation des joint avec des decouvres",
 "severity":"light","failure_hypothesis":"asymptote du joint",
 "recommended_action":"nettoyer le joint avec une piture recommandee", ...}
```

Attendu : `severity: "low"`. Le modèle n'a pas appris le **vocabulaire fermé** du
champ, et le texte libre est du français cassé — « decouvres », « asymptote du
joint », « une piture ». Ce n'est pas un défaut de format JSON, c'est un défaut
de contrat.

## Le résultat non planifié : rappel verbatim et décision ne coûtent pas le même prix

Sur 80 sorties, **67 diffèrent** de `variation_2`. La génération étant
déterministe (`do_sample: false`, température 0), aucune de ces différences n'est
du bruit d'échantillonnage.

Or **une seule décision change** : un `low` perdu — celui du cas ci-dessus.

| Classe `severity` | `variation_2` | `variation_4` | Attendus |
|---|---:|---:|---:|
| `low` | 13 | **12** | 14 |
| `medium` | 15 | 15 | 16 |
| `high` | 37 | 37 | 37 |
| `critical` | 12 | 12 | 13 |

`equipment_id` reste à 1,000, `requires_human_review` à 0,9875. La totalité de la
chute est **lexicale**. Décomposée par champ sur le groupe `vu` :

| Champ | `variation_1` | `variation_2` | `variation_4` |
|---|---:|---:|---:|
| `symptom` | 1,0000 | 1,0000 | 0,9769 |
| `failure_hypothesis` | 1,0000 | 1,0000 | **0,7445** |
| `recommended_action` | 1,0000 | 1,0000 | **0,7018** |

`symptom` tient à 0,977 : il se dérive largement du texte d'entrée. Les deux
champs qui s'effondrent sont ceux que le modèle ne peut **pas** déduire — ceux
qu'il ne pouvait que restituer de mémoire.

Exemple, `ANN-2026S1-0131`, groupe `vu`. Attendu : « identifier l'equipement et
realiser une inspection avant diagnostic ». `variation_2` le rend au mot près.
`variation_4` : « rechercher la source du bruit et effectuer un sonographie ».
Même `symptom`, même gravité, phrase inventée.

**Le composite de 100,00 de `variation_2` sur le groupe `vu` était porté par la
restitution mot pour mot de deux champs libres.** Du rappel, pas de la qualité.
Diviser le learning rate par deux efface ce rappel tout en laissant les décisions
intactes : mémoriser un texte et apprendre une décision ne se paient pas au même
budget d'optimisation. Les décisions s'acquièrent tôt et à bas coût ; la
restitution verbatim exige le budget complet.

Ni `variation_2` ni `variation_3` ne pouvaient faire apparaître cette
distinction. Elle qualifie précisément ce que valait ce 100,00 — et c'est le
seul apport réel de cette expérience.

## Le composite, tous systèmes

| Système | Réglage vs référence | Global | `vu` (65) | `nouveau` (15) | Écart |
|---|---|---:|---:|---:|---:|
| `baseline` | modèle brut | 18,12 | 18,21 | 17,78 | 0,43 |
| `lora_reference` | — | 90,02 | 91,57 | 81,82 | 9,75 |
| `variation_1` | +3 modules MLP | 96,86 | 98,64 | 86,23 | 12,41 |
| `variation_2` | epochs 3→5 | **98,11** | **100,00** | **86,28** | 13,72 |
| `variation_3` | dropout 0,05→0,15 | 96,80 | 98,64 | 85,92 | 12,72 |
| `variation_4` | lr 2e-4→1e-4 | 94,95 | 96,80 | 83,40 | 13,39 |

`variation_4` est le premier montage LoRA à passer **sous la référence sur les
deux groupes** : −3,16 global, −3,20 sur `vu`, −2,88 sur `nouveau`.

La colonne `nouveau` est celle qui porte l'information : 81,82 → 86,23 → 86,28 →
85,92 → 83,40. Le seul gain vient du passage de la référence à `variation_1`
(+4,41, l'ajout des couches feed-forward). Depuis, trois hyperparamètres testés
sur trois axes distincts — capacité, régularisation, optimisation — et le
meilleur reste 86,28. Rien ne monte ; deux font descendre.

Le plafond tient à 86,3 sur quatre montages. C'est le résultat le plus stable du
Brief 1, et il ne repose plus sur une seule expérience. Sous réserve, pour ce
run-ci, du verdict ci-dessus : il n'a pas valeur de test de généralisation.

## Un artefact de mesure confirmé au passage

| Système | Longueur de sortie médiane | Latence médiane |
|---|---:|---:|
| `variation_2` | 331 caractères | 14,49 s |
| `variation_4` | 330 caractères | 4,63 s |

Longueurs de sortie identiques, même chemin non fusionné, même machine — et un
facteur 3 sur la latence. La génération ne peut pas l'expliquer. Cette mesure
re-confirme, sur un troisième run, que la latence relevée pendant une évaluation
est inutilisable, comme les colonnes `latence_*_NON_FIABLE` de `metrics_m1.csv`
le consignaient déjà. Seul le banc contrôlé (`tools/latency_benchmark.py`) fait
foi.

## Ce que l'expérience élimine, ce qu'elle renforce

**Éliminé** : l'idée qu'un learning rate plus fin, à nombre d'epochs égal,
puisse convertir la mémorisation de `variation_2` en généralisation. Il ne la
convertit pas — il la supprime sans rien mettre à la place.

**Renforcé** : la lecture du composite `vu` comme un indicateur de rappel plutôt
que de compétence. Le 100,00 de `variation_2` est désormais décomposé et daté :
il vaut 1,0000 de recopie sur deux champs libres.

**Non tranché** : l'axe optimisation reste ouvert. Un test propre exigerait de
compenser la baisse de learning rate par davantage d'epochs, de façon à conserver
un budget `epochs × lr` constant. Ce serait alors une expérience à deux variables
coordonnées, à déclarer comme telle.

## Conséquences pour le Brief 2

Les quatre amendements de la décision intermédiaire restent valides. Cette
expérience en suggère un cinquième, **soumis à arbitrage et non encore acté** :

> **Amendement 5 (proposé)** — le seuil « qualité des champs textuels ≥ 0,65 »
> est mesuré sur une validation dont 81 % des exemples ont un quasi-jumeau dans
> l'entraînement. `variation_1` y obtient 0,94, dont 1,0000 de recopie exacte sur
> le groupe `vu`. Ce seuil mesure donc principalement du rappel verbatim, pas de
> la qualité rédactionnelle. Proposition : l'évaluer sur le groupe `nouveau`
> uniquement, où `variation_1` obtient 0,66 — soit tout juste le seuil.

Cet écart entre 0,94 et 0,66 sur le même critère, selon le groupe retenu, décide
seul du franchissement du seuil. Il doit être tranché **avant** l'ouverture du
jeu de test.

## Traçabilité

| Élément | Chemin |
|---|---|
| Configuration et hypothèse | `configs/variation_4.yaml`, commit `11b4be2` |
| Journal d'entraînement | `work/variation_4_run.log` |
| Journal d'évaluation | `work/variation_4_eval.log` |
| Adaptateur | `work/runs/variation_4/adapter` |
| Manifeste de run | `work/runs/variation_4/run_manifest.json` |
| Prédictions et métriques | `work/variation_4_validation/` |
| Métriques stratifiées | `work/variation_4_validation/stratified.json` |
| Outil de stratification | `tools/stratified_metrics.py` |

`variation_4` n'est pas conservée comme candidat. Ses artefacts sont versionnés
au titre de la traçabilité. Le candidat du Brief 2 reste `variation_1`.

## Note d'outillage

La stratification `vu` / `nouveau` avait été conduite à la main lors du Brief 1,
sans script conservé : chaque nouvelle expérience risquait une méthode de calcul
légèrement différente de la précédente. `tools/stratified_metrics.py` la fige. Il
relit la partition gelée avant la décision intermédiaire
(`work/evidence/validation_proximite_train.json`) et appelle
`src.metrics.calculate_metrics` — la fonction même qu'utilise `src/evaluate.py`,
sans réimplémentation.

Contrôle de non-dérive (`--verify`), sur les trois systèmes déjà publiés :

| Système | `vu` publié / recalculé | `nouveau` publié / recalculé |
|---|---|---|
| `variation_1` | 98,6414 / **98,6414** | 86,2285 / **86,2285** |
| `variation_2` | 100,00 / **100,00** | 86,2821 / **86,2821** |
| `variation_3` | 98,64 / **98,6414** | 85,92 / **85,9171** |

Écart nul aux arrondis de publication près. Le script ajoute le F1 **par classe**
avec précision et rappel séparés : la réserve n° 1 du Brief 1 porte sur
`critical`, et la grandeur qui compte y est le rappel — les dangers manqués — que
le F1 dilue dans la précision.
