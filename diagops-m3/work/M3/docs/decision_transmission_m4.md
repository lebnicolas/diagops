---
module: M3
etat: axe 8 terminé
maj: 2026-08-24
---

# Décision de transmission à M4

## Statut

> ## `utilisable sous conditions`

L'ensemble multi-source peut être transmis à M4. Il ne peut pas l'être sans les
cinq conditions énoncées plus bas, dont deux sont bloquantes pour un usage
prédictif.

**Pourquoi pas `utilisable`** : la couverture instrumentale est biaisée par
construction, et le signal de dégradation le plus fort du corpus n'est apparié à
aucun événement. Ces deux faits limitent ce qu'un modèle peut légitimement
apprendre — les ignorer produirait un résultat qui semble bon et ne l'est pas.

**Pourquoi pas `non utilisable en l'état`** : la préparation tient. 99,75 % des
mesures reçues sont exploitables, chaque écart est tracé et réversible, la
non-régression sur l'acquis M2 est démontrée et bloquante, et le rapprochement
est complet sur son périmètre. Rien ne justifie de refuser la transmission ; tout
justifie de l'encadrer.

## Ce qui a été vérifié

| Vérification | Résultat | Preuve |
|---|---|---|
| Volume annoncé | 50 401 lignes, conforme | `cadrage.json` |
| Encodage | UTF-8 valide — le défaut apparent venait de la console | `cadrage.json` |
| Grain et clé logique | une mesure unitaire ; clé `equipment_id + timestamp + sensor_name` **non unique dans les données reçues** | `cles_dupliquees.csv` |
| Période réelle | 28/12/2025 → 04/07/2026, **5 lignes** hors du semestre annoncé | `mesures_hors_bornes.csv` |
| Pas d'échantillonnage | 6 h à **99,97 %** (50 313 / 50 329) | `cadrage.json` |
| Continuité | **1 seule** interruption réelle (270 h), les 5 autres étaient des artefacts | `interruptions.csv` |
| Alignement de grille | 1 série décalée de 2 h, 720 mesures — invisible à un contrôle de pas | `horodatages_hors_grille.csv` |
| Cohérence capteur / unité | 804 lignes non conformes, toutes convertibles et converties | `couples_capteur_unite.csv` |
| Valeurs sentinelles | 12 lignes à `-999`, critère physique | `valeurs_sentinelles.csv` |
| Comportements de capteur | 1 figé, 1 dérive, 1 saut, 10 dépassements de plage | `audit_temporel.json` |
| Couverture | 36 / 416 équipements, ventilée par site, type, criticité | `couverture_parc.csv` |
| Non-régression M2 | 416 / 514 / 1 788 lignes **identiques**, contrôle bloquant | `pipeline_m3.json` |
| Rapprochement | **89 / 89** événements instrumentés appariés, duplication 1,014 | `rapprochement_m3.json` |
| Sensibilité de la fenêtre | 89 événements appariés sur **5 largeurs** de 12 h à 168 h | `rapprochement_m3.json` |
| Risque « personnes » | mesures au pas de 6 h, minute fixe → **aucune signature d'activité humaine** ; distribution horaire des interventions plate | `couverture_et_risques.md` |

Les **onze familles d'anomalies** annoncées par la `DATA_CARD` ont toutes été
retrouvées. Deux épisodes de vibration supplémentaires, non annoncés, ont été
découverts et confirmés par des incidents `critical` indépendants.

**56 tests** passent, couvrant un cas valide et un cas invalide par règle, quatre
cas temporels, le format de quarantaine et la non-régression.

## Ce qui a été transformé

**50 401 mesures reçues → 50 277 préparées.** 124 lignes retirées, soit 0,25 %.
Aucun fichier de `data_pack/` n'a été modifié.

| Transformation | Lignes | Décision | Réversible ? |
|---|---:|---|---|
| Unités converties (kPa → bar, K → °C) | 804 | `valeur_normalisee` | oui, tracée |
| Horodatages sans fuseau interprétés en UTC | 720 | `valeur_normalisee` | oui, **hypothèse** |
| Noms de capteur normalisés | 40 | `valeur_normalisee` | oui, tracée |
| Étiquettes `period` corrigées | 30 | `valeur_normalisee` | oui, tracée |
| Sentinelles `-999` neutralisées | 12 | `champ_neutralise` | oui, ligne conservée |
| Valeurs vides tracées | 40 | `champ_neutralise` | oui, ligne conservée |
| **Capteur figé exclu** | **80** | `exclue` | oui, en quarantaine |
| **Équipement inconnu exclu** | **30** | `exclue` | oui, en quarantaine |
| **Clés divergentes exclues** | **8** | `exclue` | oui, en quarantaine |
| **Doublons stricts supprimés** | **6** | `doublon_supprime` | oui, en quarantaine |

Les 1 833 lignes de quarantaine — dont les 35 héritées de M2, reprises
intégralement — permettent de retrouver chaque ligne d'origine par son
`row_identifier`. **Toute décision de ce module est annulable.**

## Ce qui reste incertain

Classé par effet sur M4.

**1. Le biais de couverture — structurel, non corrigeable.**
36 équipements sur 416, avec une instrumentation 23 fois plus dense sur les
équipements `critical` que sur les `low`. Un site entier et sept types
d'équipement n'ont aucune mesure. Aucun traitement ne corrige cela : c'est une
propriété de la source.

**2. Les étiquettes manquent le cas le plus sévère.**
8 mesures dépassent 5 mm/s dans le corpus ; **2 sont appariées à un événement, 6
ne le sont pas** — et ces 6 sont l'épisode `EQ-FAN-304` du 10-11/05, pic à 9,76
mm/s, presque le double des deux épisodes étiquetés. Un modèle supervisé
apprendrait les cas modérés et serait *récompensé* pour ignorer le cas grave,
puisqu'il serait évalué sur les mêmes étiquettes.

**3. L'hypothèse de fuseau sur 720 mesures.**
La série `EQ-COMP-233 / temperature_c` est livrée sans indication de fuseau et
interprétée en UTC. L'hypothèse est faible : elle ne distingue pas UTC d'un
décalage d'un multiple exact de 6 h. Un décalage d'une heure fausserait tout
rapprochement sur cet équipement.

**4. L'origine de la dérive de `EQ-CHILL-248`.**
+8,9 °C, stable jusqu'en avril puis montée en mai-juin. Dérive d'étalonnage ou
dégradation réelle du groupe froid : les deux produisent ce signal. Le test de
recalage par l'intervention du 15/03 n'est pas concluant — elle précède la
dérive. **Elle est encore en cours à la fin de la période.**

**5. Les seuils de détection.**
Quatre ont dû être corrigés après avoir produit des résultats manifestement
faux. Les seuils actuels (8 MAD, 8 relevés consécutifs, 0,30 de corrélation,
8 MAD + 10 % d'amplitude) sont calibrés sur ce semestre et rien ne garantit
qu'ils ne laissent pas passer d'anomalies plus discrètes.

**6. Aucune revue contradictoire externe.**
Comme en M1 et en M2, toutes les objections de ce module viennent de nos propres
contrôles. C'est la faiblesse méthodologique du dossier, et elle est assumée.

## Conditions à respecter avant M4

**Bloquantes** — ne pas les tenir invaliderait les résultats de M4 :

**C1. Énoncer le périmètre de validité dans toute conclusion.**
Formulation à reprendre : « sur les 36 équipements instrumentés, majoritairement
critiques, des sites NORD/SUD/EST, au premier semestre 2026 ». Toute
généralisation au parc est fausse.

**C2. Ne pas traiter les événements comme une vérité terrain.**
Ce sont des déclarations d'exploitation, incomplètes de façon **non aléatoire** :
elles manquent le cas le plus sévère. Une métrique calculée sur ces étiquettes
surestimera la performance réelle. Si M4 fait de la détection d'anomalie, prévoir
une évaluation qui ne repose pas uniquement sur elles — l'épisode `EQ-FAN-304`
est un cas de test naturel : un bon détecteur doit le trouver **sans** étiquette.

**Recommandées** — leur absence dégrade le résultat sans l'invalider :

**C3. Ajouter un grain avant/pendant/après aux agrégats.**
Le grain actuel (`event_id × equipment_id × sensor_name`) perd l'ordre : il ne
distingue pas un précurseur d'une conséquence. C'est rédhibitoire pour de la
prédiction, et c'est un ajout peu coûteux.

**C4. Lever ou confirmer l'hypothèse de fuseau.**
Par recoupement entre les mesures de `EQ-COMP-233` et ses événements datés à la
minute. Si le recoupement échoue, écarter la série plutôt que la conserver sous
une hypothèse fausse.

**C5. Rejouer la couverture sur la livraison suivante.**
Les taux de ce module ne sont pas des constantes. Le parc instrumenté peut
changer sans préavis.

## Coût de rejeu

| Étape | Temps |
|---|---:|
| `run_cadrage_m3.py` | 4,4 s |
| `run_audit_temporel_m3.py` | 1,4 s |
| `run_pipeline_m3.py` | 2,9 s |
| `run_rapprochement_m3.py` | 0,7 s |
| **Chaîne complète** | **9,4 s** |
| `pytest` (56 tests) | 1,3 s |
| Installation de l'environnement | ~2 min (une fois) |

Médianes sur 3 exécutions, dont environ 2 s de démarrage de l'interpréteur et de
pandas par script — soit **8 s des 9,4 s** en démarrage pur. Le traitement réel
représente moins de 2 secondes.

**Ce que ce coût devient à plus grande échelle.** La volumétrie actuelle est de
3,16 Mo pour 36 équipements et un semestre. Le traitement tient entièrement en
mémoire avec pandas, ce qui reste vrai jusqu'à environ 36 Mo — le parc entier
instrumenté sur un semestre. Deux seuils font basculer :

- **parc entier sur plusieurs périodes** (~365 Mo sur 5 ans) : encore tenable,
  mais le chargement intégral devient le poste dominant. Un traitement par
  livraison, avec agrégats incrémentaux, serait préférable ;
- **pas d'échantillonnage à la minute** (13,1 Go / semestre) : **impraticable en
  l'état**. Le chargement intégral en mémoire ne passe plus, et les contrôles
  série par série — dérive, figé, saut — devraient être réécrits en traitement
  par flux ou délégués à une base.

Ce second seuil est le point de bascule à surveiller. Il ne se pose pas
aujourd'hui, et la persistance en base traitée par le brief online en est le
premier élément de réponse.

## Résumé pour un lecteur pressé

Les données multi-source sont **prêtes pour M4**, avec deux réserves qui ne se
corrigent pas par un meilleur traitement :

1. elles décrivent **8,65 % du parc**, majoritairement ses équipements critiques ;
2. leurs **étiquettes manquent le cas le plus grave** qu'elles contiennent.

Tout le reste — 124 lignes écartées sur 50 401, hypothèse de fuseau, dérive
indécidable — est tracé, réversible et sans effet structurant.
