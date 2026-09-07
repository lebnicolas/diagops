# L'artefact déployé — détecteur de provenance DiagOps

> Étape 1 du brief online : entrées, sorties, paramètres, dépendances, version et résultats de
> référence. Tout ce qui suit a été vérifié sur l'artefact lui-même, pas repris de sa fiche.

## Identité

| | |
|---|---|
| Nom | détecteur de provenance de fenêtres capteurs |
| Origine | candidat gelé en **M4 le 31/08/2026** |
| Algorithme | régression logistique, `class_weight="balanced"`, `StandardScaler` en amont dans un `Pipeline` |
| Fichier | `artefact/candidat_m4.joblib`, **1 953 octets** |
| Empreinte SHA-256 | `164d05b129ce5e4107cdc27279bc198c…` |
| Commit du gel | `a63e45d` |
| Graine | `20260831` |
| Manifeste | `artefact/gel.json` |

L'empreinte relevée sur la copie **correspond exactement** à celle déclarée dans la model card
M4. La copie est intègre, et l'identité est vérifiable par quiconque.

## Entrées

Une **fenêtre** de 30 mesures capteur consécutives. Chaque mesure porte quatre champs, repris
sans changement du contrat capteur M3 :

| Champ | Type | Rôle |
|---|---|---|
| `timestamp` | ISO 8601, UTC | pas nominal de 6 h, grille attendue `{0, 6, 12, 18}` |
| `value` | chaîne ou nombre | mesure brute, sentinelles comprises |
| `sensor_name` | chaîne | détermine la plage physique attendue |
| `unit` | chaîne | conformité d'unité |

Le service accepte **5 à 200 mesures**. En dessous de 5, les autocorrélations à décalage 4 n'ont
plus de sens. Une fenêtre de taille autre que 30 est servie **mais comptée**
(`diagops_windows_off_spec_total`) : une dérive de format en amont se voit dans les métriques
avant de se voir dans les résultats.

### Les 19 features

Toutes **intrinsèques à la fenêtre** — aucune ne dépend d'un équipement, d'une date ou d'un
voisinage. Quatre familles :

| Famille | Features |
|---|---|
| Dispersion | `coefficient_variation`, `etendue_relative`, `ecart_type_differences_relatif` |
| Structure temporelle | `autocorr_lag1`, `autocorr_lag2`, `autocorr_lag4`, `part_changements_de_signe` |
| Forme de distribution | `asymetrie`, `aplatissement`, `part_valeurs_distinctes`, `plus_longue_repetition` |
| Conformité au contrat | `part_pas_non_nominal`, `ecart_type_pas`, `part_hors_grille`, `part_manquantes`, `part_sentinelles`, `part_hors_plage`, `part_precision_excessive`, `unite_conforme` |

**L'ordre est celui de `gel.json`, et il est contraignant.** Le `StandardScaler` a été ajusté sur
un tableau sans noms de colonnes : appliqué dans le désordre, il ne lève aucune erreur et rend
des résultats faux. `src/scoring.py` impose l'ordre du gel, et un test le prouve en vérifiant que
l'ordre inverse donne une autre probabilité.

## Sorties

```json
{
  "probabilite_fabriquee": 0.114902,
  "provenance_predite": "réelle",
  "seuil_de_decision": 0.5,
  "mesures_recues": 30,
  "modele_checksum": "164d05b129ce5e41"
}
```

Chaque réponse porte le checksum du modèle qui l'a produite : une prédiction sans artefact
identifiable est une prédiction qu'on ne peut ni expliquer ni rejouer.

## Paramètres

| Paramètre | Valeur | D'où il vient |
|---|---|---|
| Seuil de décision | **0,5** | `gel.json`, arbitré en M4 |
| Classe positive | `fabriquée` | protocole M4 |
| Pas nominal | 6 h | contrat capteur M3 |
| Plages physiques | 5 capteurs | baseline M3 figée |
| Sentinelles | `-999`, `-9999`, `9999`, `999999` | contrat capteur M3 |

Aucun de ces paramètres n'est réglable à l'exécution. Un seuil modifiable par requête ferait de
chaque appelant un décideur du compromis précision/rappel, sans que la trace en garde mémoire.

## Dépendances

| Dépendance | Version | Pourquoi elle est figée |
|---|---|---|
| **scikit-learn** | **1.7.1** | version du gel. Un `joblib` chargé sous une autre version est au mieux bruyant, au pire subtilement différent |
| numpy | 2.3.2 | dépendance de sérialisation du pipeline |
| pandas | 2.3.1 | extraction des features |
| joblib | 1.5.1 | format de l'artefact |
| Python | 3.12 | version du gel |

La conformité de scikit-learn est **vérifiée au démarrage**, exposée par `/version` et
`/health/ready`, et remontée en métrique (`diagops_model_sklearn_conforme`). Un écart ne bloque
pas le service — il est rendu visible, parce qu'un écart silencieux est le pire des deux.

## Résultats de référence

Déclarés au gel, mesurés **hors pli** sur 5 partitions :

| Métrique | Valeur |
|---|---|
| F1 moyen | **0,694** |
| Écart-type du F1 | 0,0684 |
| F1 min / max | 0,600 / 0,800 |
| Précision | 0,700 |
| Rappel | 0,636 |
| ROC AUC | 0,737 |

Baseline M3 à battre : **F1 = 0,374**.

> **Un chiffre à ne pas confondre avec ceux-ci.** Le test de non-régression du service obtient
> VP=10, FP=0, FN=1, soit **F1 = 0,952** sur les 30 fenêtres de calibration. C'est de
> l'**in-sample** : ces fenêtres ont servi à ajuster le modèle. Ce chiffre ne mesure pas la
> performance, il vérifie que la chaîne déployée rend les **mêmes décisions** que la chaîne
> d'entraînement. Le seul chiffre à annoncer reste **0,694 ± 0,068**.

## Vérification d'équivalence

Le module d'extraction a été repris de M4 **sans son code d'entraînement**. L'équivalence n'est
pas supposée : `tests/test_artefact.py` recalcule les **30 fenêtres × 19 features** et les compare
aux valeurs produites en M4, à 10⁻⁹ près.

**Résultat : zéro écart.**

C'est le contrôle le plus important de ce brief. Une dérive d'extraction ne fait pas planter le
modèle — elle le rend silencieusement faux : il prédit correctement, sur les mauvaises entrées.

## Usages exclus, repris de la model card M4

| Usage | Pourquoi |
|---|---|
| Prédire une panne | rien ne relie une fenêtre à une défaillance ultérieure |
| Juger la qualité d'une mesure | une fenêtre réelle peut violer le contrat capteur, une fabriquée peut être irréprochable |
| Décider seul d'exclure une donnée | rappel de 0,636 — le modèle laisse passer 4 fenêtres fabriquées sur 11 |
| S'appliquer à `temperature_c` | segment manqué en totalité en M4 |
| S'appliquer hors du parc synthétique DiagOps | aucune donnée industrielle réelle n'a été vue |

Le service **ne réimplémente aucun de ces garde-fous** : ils relèvent de l'usage, pas du code.
Les inscrire ici est la seule chose que le déploiement puisse faire pour eux.
