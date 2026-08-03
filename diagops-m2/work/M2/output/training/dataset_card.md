# Jeu supervisé DiagOps — prédiction de la gravité

**Tâche** : prédire la `severity` d'un événement **au moment où il est signalé**, pour trier les interventions.
**Type** : classification multiclasse, 4 classes (`low`, `medium`, `high`, `critical`).
**Unité** : un événement.
**Reproductible par** : `python run_audit_m2.py && python build_dataset.py` (seed 42).

Construit à partir des **tables préparées** en M2 (`output/processed/`), jamais des fichiers reçus.

---

## Volumes

| Paquet | Lignes | Équipements | high | medium | critical | low |
|---|---:|---:|---:|---:|---:|---:|
| train | 358 | 262 | 41,3 % | 30,2 % | 14,8 % | 13,7 % |
| validation | 77 | 56 | 45,5 % | 33,8 % | 11,7 % | 9,1 % |
| test | 79 | 56 | 38,0 % | 29,1 % | 13,9 % | 19,0 % |

2 lignes écartées, motif dans `exclusions.csv` : une `severity` à `URGENT` (valeur hors énumération, non interprétable) et un événement dont l'équipement n'est pas joignable — la référence orpheline `EVT-2026S1-0180` relevée par l'audit.

## Variables (10)

| Variable | Origine | Type |
|---|---|---|
| `equipment_type` | equipment | catégorielle (18 valeurs) |
| `site_id` | equipment | catégorielle (4) |
| `criticality` | equipment | catégorielle (4) |
| `manufacturer` | equipment | catégorielle |
| `rated_power_kw` | equipment | numérique |
| `event_type` | events | catégorielle (4) |
| `equipment_age_days` | dérivée | `start_at − commissioning_date` |
| `start_month` · `start_weekday` · `start_hour` | dérivée | temporalité du signalement |

## Ce qui est volontairement exclu

**Fuite temporelle.** Tout ce qui vient de `maintenance_history` décrit ce qui s'est passé **après** l'événement — et après l'évaluation de gravité elle-même :

`downtime_minutes` · `labor_hours` · `parts_cost_eur` · `parts_replaced_count` · `outcome` · `intervention_type` · `work_order_note`

**Même raison pour `end_at`** et la durée de l'événement : au moment où l'on voudrait trier, l'événement n'est pas terminé.

**Identifiants** : `equipment_id` et `event_id` sont exclus des variables. `equipment_id` sert uniquement au découpage.

## Découpage — par équipement, pas par ligne

Un équipement n'apparaît que dans **un seul** paquet. Un découpage ligne à ligne laisserait le même équipement des deux côtés : le modèle pourrait retenir son comportement propre et afficher un score qui ne se reproduirait sur aucun équipement nouveau.

Un test verrouille l'absence de chevauchement, et le script échoue si un équipement se retrouve dans deux paquets.

## Scores de référence — à battre

Mesurés sur le test, appris sur l'entraînement seul.

| Référence | Score |
|---|---:|
| Répondre toujours la classe majoritaire | **0,380** |
| Table de correspondance `equipment_type → severity` | **0,570** |

**La seconde référence est la vraie barre.** L'information mutuelle entre `equipment_type` et `severity` vaut 0,578, contre 0,022 pour la variable suivante : la gravité est très largement déterminée par le type d'équipement. Une table de 18 lignes capture donc l'essentiel du signal.

Un modèle qui n'atteindrait pas 0,570 **coûterait plus cher qu'un dictionnaire pour faire moins bien**. Publier ce chiffre est ce qui empêche de présenter comme un résultat un modèle qui n'a fait que reconstituer ce tableau.

> À noter : la même table atteint **0,678** mesurée sur les données qui l'ont produite, contre 0,570 sur des équipements jamais vus. L'écart de 11 points est exactement ce que le découpage par équipement sert à révéler.

## Limites

**Le signal est concentré sur une seule variable.** `press` → critical à 90 %, `sensor` → medium à 94 %, `chiller` → high à 85 %. Les autres variables n'apportent presque rien. C'est un jeu qui se prête mal à démontrer la valeur d'un modèle complexe.

**Quatre types d'équipement sont déterministes sur 5 à 8 lignes** — `dryer`, `packaging_machine`, `motor`, `gearbox`, `lift`. Ce sont ceux que l'analyse de couverture M2 signalait sous le seuil de 30 observations. Leur 100 % apparent ne tiendra pas.

**Couverture héritée du M2** : `SITE-OUEST` ne pèse que 16 équipements, 12 des 18 types sont sous le seuil d'interprétabilité, et 41 équipements du parc n'ont produit aucun événement — ils sont donc absents de ce jeu par construction.

**Les autres cibles ont été écartées faute de signal**, mesuré et non supposé :

| Cible envisagée | Mesure | Verdict |
|---|---|---|
| `outcome` | information mutuelle max 0,023 · 5 classes à 20-22 % | bruit |
| `intervention_type` | distribution uniforme sur 5 classes | bruit |
| `downtime_minutes` | corrélation max 0,043 avec toute autre variable | aucun signal |

**Ce jeu ne dit rien de la causalité.** Que la gravité se distribue différemment selon le type d'équipement est une **co-occurrence** dans les données livrées. Rien n'établit qu'un type cause une gravité.

## Fichiers

```
output/training/
├── train.csv          358 lignes
├── validation.csv      77 lignes
├── test.csv            79 lignes
├── exclusions.csv       2 lignes, avec motif
└── dataset_card.md
```

Encodage `utf-8`, fins de ligne `LF`, `equipment_id` conservé en première colonne pour permettre l'audit du découpage — il n'est pas une variable.
