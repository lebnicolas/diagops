# Métriques et déclencheurs — service de scoring

> Étape 5 du brief online. Chaque ligne porte les cinq champs exigés : **source, fréquence,
> seuil, destinataire, action**. Une métrique sans destinataire ni action n'est pas une métrique,
> c'est une courbe.

Source unique : `/metrics` du service, scrappé par Prometheus toutes les **15 s**, rétention
**7 jours**.

## Santé système

| Métrique | Fréquence | Seuil | Destinataire | Action |
|---|---|---|---|---|
| `diagops_model_loaded` | 15 s | `0` immédiat | Astreinte | Le service ne peut rien servir. Vérifier l'artefact dans l'image, redéployer le digest précédent |
| `diagops_model_sklearn_conforme` | 15 s | `0` immédiat | Responsable modèle | Le modèle tourne sous une version non testée. **Bloquer la promotion**, revalider ou revenir au digest conforme |
| `diagops_http_requests_total{status=~"5.."}` | 15 s | > 1 % sur 5 min | Astreinte | Lire les journaux, décider correctif ou rollback |
| `diagops_http_request_duration_seconds` | 15 s | p95 > 0,5 s sur 5 min | Astreinte | Vérifier charge et limites de ressources |

## Stabilité des données en entrée

| Métrique | Fréquence | Seuil | Destinataire | Action |
|---|---|---|---|---|
| `diagops_windows_off_spec_total` | 15 s | > 5 % des prédictions sur 1 h | Responsable données | Fenêtres de taille ≠ 30 : dérive de format en amont. Le modèle a été ajusté sur 30 mesures |
| `diagops_prediction_errors_total{reason="features"}` | 15 s | > 0 sur 15 min | Responsable données | Fenêtres inexploitables : champs manquants ou horodatages non conformes |

Ces deux métriques sont le seul signal de **dérive d'entrée** disponible ici. Elles ne mesurent pas
la dérive de distribution — voir les limites plus bas.

## Performance du modèle

C'est la section qui demande le plus de prudence : **la vérité terrain n'existe pas en service**.
Personne ne dira si la fenêtre était réellement fabriquée. Les indicateurs ci-dessous sont donc
des **proxys**, et ils sont nommés comme tels.

| Métrique | Fréquence | Seuil | Destinataire | Action |
|---|---|---|---|---|
| `diagops_predictions_total{classe="fabriquée"}` (part) | 15 s | part hors de **20 % ± 15 pts** sur 24 h | Responsable modèle | Le taux d'ajustement était de 11/30 ≈ 37 %, mais sur un lot volontairement enrichi. Un écart durable interroge l'entrée, pas le modèle |
| `diagops_model_probability` (histogramme) | 15 s | > 40 % des prédictions dans `[0,4 ; 0,6]` sur 24 h | Responsable modèle | Le modèle hésite près du seuil : ses entrées ne ressemblent plus à celles du gel |
| `diagops_prediction_duration_seconds` | 15 s | p95 > 0,1 s | Astreinte | Régression d'inférence |

> **Ce que ces seuils ne prouvent pas.** Un taux de positifs stable n'est pas une preuve que le
> modèle a raison : il peut se tromper de façon constante. Ces indicateurs détectent un
> **changement**, jamais une **justesse**. La seule mesure de justesse reste l'oracle scellé du
> formateur, hors ligne.

## Usage

| Métrique | Fréquence | Seuil | Destinataire | Action |
|---|---|---|---|---|
| `diagops_predictions_total` (débit) | 15 s | chute > 80 % vs 24 h avant | Astreinte | Vérifier que les appelants tournent — panne amont probable |
| `diagops_http_requests_total{path="other"}` | 15 s | > 10 % du trafic | Astreinte | Un appelant se trompe de route, ou balayage automatisé |

## Déclencheurs de réentraînement

Le brief demande d'identifier ce qui déclenche une amélioration. **Aucun de ces déclencheurs
n'automatise quoi que ce soit** — chacun ouvre une décision humaine, conformément à la model card
M4 : « décision assistée, jamais automatique ».

| Déclencheur | Condition | Ce qu'il ouvre |
|---|---|---|
| Dérive d'entrée | `windows_off_spec` > 5 % ou erreurs de features > 0 sur 1 h | Revoir le producteur des fenêtres avant de toucher au modèle |
| Hésitation du modèle | > 40 % des probabilités dans `[0,4 ; 0,6]` sur 24 h | Revue du seuil, ou reconnaissance que le lot a changé |
| Nouveau lot étiqueté | livraison `2026-S2` qualifiée | Réévaluation hors pli, comparaison au F1 de 0,694 |
| Écart de version | `sklearn_conforme = 0` | Revalidation complète avant toute promotion |
| Segment manqué connu | `temperature_c`, documenté en M4 | Réentraînement ciblé si ce segment devient servi |

## Ce qui n'est pas mesuré, et pourquoi

**La dérive de distribution des features.** Ce serait le bon indicateur — comparer la distribution
des 19 features servies à celle du lot d'ajustement. Il faudrait un état persistant côté service
et un test statistique par feature. Hors périmètre de ces 6 heures, mais c'est **le premier ajout
à faire** si le service devait vivre.

**Le coût.** Aucun appel facturé : l'inférence est locale, un `predict_proba` sur 19 features.

**La justesse.** Pas de vérité terrain en service, voir plus haut.

**Les ressources conteneur.** Limites posées dans `compose.yaml`, non observées : il faudrait un
cAdvisor. Signalé plutôt que simulé.

## Minimisation

Aucune valeur capteur, aucun horodatage, aucun identifiant de fenêtre ne figure dans un label de
métrique. Vérifié par test : une mesure à `424242.42` envoyée au service n'apparaît nulle part
dans l'exposition.

Les seuls labels sont `classe` (deux valeurs), `path` (routes connues plus `other`), `method`,
`status` et `reason` — tous à cardinalité bornée.
