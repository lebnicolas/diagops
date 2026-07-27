# Analyse des erreurs M1

Date : 27/07/2026. Périmètre : les 80 exemples de validation, quatre systèmes
comparés. Le jeu de test final n'a pas été consulté.

Systèmes : `baseline` (Qwen3-0.6B brut), `reference` (LoRA r=16 sur q/k/v/o,
3 epochs), `variation_1` (idem + couches feed-forward, mesuré adaptateur
fusionné), `variation_2` (référence portée à 5 epochs).

## Synthèse

- **Nombre de cas examinés : 17**, dont les 13 cas de gravité `critical` de la
  validation (population entière, pas un échantillon) et 4 erreurs isolées
  relevées sur le candidat retenu.
- **Méthode d'échantillonnage** : exhaustive sur `critical` — c'est la classe qui
  engage la sécurité et celle où les systèmes échouent le plus. Complétée par la
  totalité des erreurs résiduelles de `variation_1` sur les autres champs
  (schéma, `equipment_id`, `requires_human_review`, `severity` hors `critical`).
- **Limite principale** : les erreurs **ne sont pas indépendantes**. Le corpus
  étant produit par patrons (voir `corpus_analysis.md`), un patron non appris
  produit mécaniquement une erreur sur chacune de ses occurrences. Compter 4
  erreurs revient parfois à compter 1 échec d'apprentissage, répété. Les
  effectifs par classe sont par ailleurs faibles (13 `critical`, dont **un seul**
  dans le groupe `nouveau`).

## Matrice d'erreurs

| ID | Système | Type d'erreur | Champ | Gravité | Hypothèse de cause | Action possible |
|---|---|---|---|---|---|---|
| tous (80) | baseline | contrat ignoré | tous | bloquante | le modèle n'a jamais vu le schéma DiagOps ; il produit du JSON valide avec ses propres clés (`diagnostic`, `identifiant_rapport`, `rapport_tech`) | c'est précisément ce que l'entraînement corrige |
| ANN-0044 | reference, variation_1 | sous-estimation | `severity` | **critique** | patron « ventilateur / odeur de chauffe / intensité moteur » classé `high` au lieu de `critical` | patron entier non appris — augmenter sa représentation |
| ANN-0124 | reference, variation_1 | sous-estimation | `severity` | **critique** | même patron, intensité 34 A | idem |
| ANN-0144 | reference, variation_1 | sous-estimation | `severity` | **critique** | même patron, intensité 28 A | idem |
| ANN-0244 | reference, variation_1 | sous-estimation | `severity` | **critique** | même patron, intensité 36 A | idem |
| ANN-0039 | **les trois** | sous-estimation | `severity` | **critique** | pompe, odeur de chauffe, température bobinage haute → `high`. **Seul cas `critical` du groupe `nouveau`** | aucun système ne détecte un critique inédit |
| ANN-0067 | reference | sous-estimation | `severity` | **critique** | fuite hydraulique 16 ml/h → `high` | corrigé par `variation_1` |
| ANN-0247 | reference | sous-estimation | `severity` | **critique** | fuite hydraulique 24 ml/h → `high` | corrigé par `variation_1` |
| ANN-0254 | reference | sous-estimation | `severity` | **critique** | arrêt d'urgence difficile à réarmer → `high` | corrigé par `variation_1` |
| ANN-0327 | reference | sous-estimation forte | `severity` | **critique** | fuite hydraulique 8 ml/h → `medium` (deux niveaux d'écart) | corrigé par `variation_1` |
| ANN-0387 | reference | sous-estimation forte | `severity` | **critique** | fuite hydraulique 18 ml/h → `medium` | corrigé par `variation_1` |
| ANN-0054 | — | *(réussi par les trois)* | `severity` | — | patron « arrêt d'urgence » appris dès la référence | — |
| ANN-0214 | — | *(réussi par les trois)* | `severity` | — | idem | — |
| ANN-0334 | — | *(réussi par les trois)* | `severity` | — | idem | — |
| ANN-0035 | reference | **valeur hors énumération** | `severity` | bloquante | produit `"severity":"light"`, valeur inexistante, plus une hypothèse hallucinée (« asymptote du joint ») | seul schéma invalide des 80 ; le garde-fou Pydantic l'attrape |
| ANN-0035 | variation_1 | faux positif de prudence | `requires_human_review` | modérée | répond `true` alors que `false` est attendu | erreur du côté sûr |
| ANN-0247 | variation_1 | **erreur de recopie** | `equipment_id` | modérée | produit `EQ-PRESS-17` au lieu de `EQ-PRESS-117` — un chiffre perdu alors que l'identifiant figure dans l'entrée | vérification programmatique post-génération |
| ANN-0011 | variation_1 | sur-estimation | `severity` | faible | `medium` → `high`, groupe `nouveau` | erreur du côté sûr |
| ANN-0027 | variation_1 | sur-estimation | `severity` | faible | `low` → `medium`, groupe `nouveau` | erreur du côté sûr |

## Répartition

- **Erreurs de format** : 80/80 pour la baseline (contrat entièrement ignoré),
  1/80 pour la référence (`"light"`), **0/80** pour `variation_1` et
  `variation_2`. L'apprentissage du format est le gain le plus net et le plus
  généralisable — il tient à 0,933 sur les exemples inédits.
- **Erreurs d'équipement** : 1/80 pour `variation_1`, et c'est une erreur de
  **recopie** (un chiffre perdu), pas de compréhension.
- **Erreurs de gravité** : 10/13 sur `critical` pour la référence, 5/13 pour
  `variation_1`, 1/13 pour `variation_2`. Sur les autres classes, 2 erreurs pour
  `variation_1`, toutes deux dans le groupe `nouveau`.
- **Erreurs de revue humaine** : 1/80 pour les trois candidats, toujours le même
  exemple (ANN-0035), et dans le sens prudent.
- **Erreurs textuelles** : non dénombrées individuellement, mesurées par le score
  lexical (0,668 → 0,940 entre la référence et `variation_1`). Limite du score :
  il récompense le vocabulaire commun, pas l'exactitude du diagnostic.
- **Erreurs critiques pour le métier** : les sous-estimations de `critical`, soit
  10, 5 et 1 selon le système.

## Cinq enseignements

### 1. Les erreurs se regroupent par patron, pas au hasard

Les quatre échecs `ANN-0044/0124/0144/0244` sont le **même rapport** à
l'identifiant et à l'intensité près (« Ventilateur VF-xx, odeur de chauffe,
débit d'air nettement réduit, intensité moteur à N A »). Ce n'est pas quatre
erreurs indépendantes : c'est un patron non appris, compté quatre fois.

Conséquence directe sur l'interprétation des métriques : le F1 de `critical`
n'agrège pas 13 observations indépendantes, mais **quatre familles** — pompe,
ventilateur, presse hydraulique, arrêt d'urgence. Un intervalle de confiance
calculé sur 13 tirages indépendants serait trompeur.

### 2. La progression entre systèmes se lit par famille

| Famille de patron | reference | variation_1 | variation_2 |
|---|---|---|---|
| Arrêt d'urgence (4 cas) | 3/4 | 4/4 | 4/4 |
| Presse hydraulique (4 cas) | 0/4 | 4/4 | 4/4 |
| Ventilateur / chauffe (4 cas) | 0/4 | **0/4** | 4/4 |
| Pompe / chauffe (1 cas, `nouveau`) | 0/1 | **0/1** | 0/1 |

`variation_1` a appris la famille « presse hydraulique » que la référence
manquait entièrement. `variation_2` a appris en plus la famille « ventilateur ».
Et **aucun système** ne traite le cas inédit.

### 3. Le seul cas critique inédit est raté par tous

`ANN-0039` est le seul `critical` du groupe `nouveau`. Les trois systèmes le
classent `high`. Sur des rapports que le modèle n'a pas déjà rencontrés sous une
forme quasi identique, **la détection du critique est nulle** — 0 sur 1.

L'effectif interdit toute conclusion statistique, mais l'observation est
cohérente avec la stratification : macro-F1 de 0,562 sur les inédits contre
0,934 sur les exemples vus. Ce point doit figurer dans la note de décision.

### 4. Le biais d'erreur n'est pas uniforme

Sur `critical`, les erreurs vont **toujours** vers la sous-estimation : 10/10
pour la référence, 5/5 pour `variation_1`, aucune sur-estimation. En revanche,
sur les classes basses et sur données inédites, `variation_1` **sur-estime**
(`medium`→`high`, `low`→`medium`).

Le modèle compresse donc les extrêmes vers le centre. Pour un outil de
maintenance, seule une moitié de ce biais est acceptable : sur-estimer déclenche
une vérification inutile, sous-estimer laisse passer un danger.

### 5. Même la recopie échoue

`ANN-0247` : l'identifiant `EQ-PRESS-117` est **écrit dans le texte d'entrée**,
et le modèle produit `EQ-PRESS-17`. Un chiffre perdu sur une tâche de copie pure.

C'est un rappel utile : un modèle de 600 millions de paramètres n'a aucune
garantie d'exactitude, même sur du recopiage. En intégration, un contrôle
programmatique — vérifier que l'identifiant produit figure bien dans l'entrée —
coûte trois lignes et supprime cette classe d'erreur entièrement.

## Conclusion

**Quelles erreurs changent la décision ?**

Les sous-estimations de `critical`. C'est la seule catégorie où une erreur a une
conséquence de sécurité, et c'est celle où les systèmes échouent le plus. Elle
justifie à elle seule d'amender la règle de décision pour le Brief 2 : le
critère « aucune classe à F1 nul » laisse passer un F1 de 0,375, ce qui est
inacceptable sur cette classe précise. Un plancher de **rappel** sur `critical`
serait le bon critère — c'est le rappel qui mesure les dangers manqués, pas le F1.

**Quelles erreurs sont acceptables ?**

- Les sur-estimations de gravité sur les classes basses : elles coûtent une
  vérification humaine inutile, jamais un incident.
- Le faux positif de `requires_human_review` : même logique, erreur prudente.
- L'erreur de recopie d'`equipment_id` : réelle mais corrigeable par un contrôle
  déterministe à l'intégration, sans toucher au modèle.
- Le `"severity":"light"` de la référence : bloqué par la validation Pydantic
  avant d'atteindre l'appelant. Le garde-fou fonctionne.

**Ce que l'analyse ne permet pas de conclure.** Que `variation_2` soit meilleure
sur `critical` (12/13) : son avantage porte exclusivement sur des patrons vus à
l'entraînement, et elle échoue sur le seul cas inédit, comme les autres. Douze
détections mémorisées ne valent pas une détection généralisée.
