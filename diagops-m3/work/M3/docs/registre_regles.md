---
module: M3
etat: axe 4 terminé
maj: 2026-08-24
---

# Registre des règles — M3

**34 règles** : 19 héritées de M2, 15 ajoutées pour la source capteurs. Toutes
sont actives — aucune n'est abandonnée.

| Statut | Nombre |
|---|---:|
| `conservee` | 16 |
| `etendue` | 3 |
| `nouvelle` | 15 |

Version exécutable : `src/pipeline_m3.py::build_registry()`. Export machine :
`output/registre_regles.csv`. Le registre est **construit dans le code**, pas
recopié à la main — un identifiant en double ou un statut hors domaine lève une
erreur au démarrage (`src/data_pipeline/rules.py`).

## Règles héritées de M2

Le point de départ retenu est l'**état préparé de référence**
(`reference_runs/m2_for_m3/`), où ces 19 règles ont déjà été appliquées. Aucune
n'est modifiée ni abandonnée en M3.

Trois règles reçoivent le statut `etendue` : leur décision — *doublon exact
supprimé, conflit exclu* — est reprise telle quelle sur la clé **composite** des
mesures, qui n'existait pas en M2. C'est la même politique appliquée à un objet
nouveau, d'où l'extension plutôt qu'une règle sans filiation.

| Règle | Table | Contrôle | Statut | Justification |
|---|---|---|---|---|
| `R-EQ-001` | equipment | `equipment_id` unique | **etendue** | Décision reprise sur la clé composite des mesures — voir `R-SEN-001` |
| `R-EQ-002` | equipment | `criticality` dans le domaine fermé | conservee | |
| `R-EQ-003` | equipment | `equipment_type` normalisé | conservee | |
| `R-EQ-004` | equipment | `rated_power_kw` strictement positive | conservee | |
| `R-EQ-005` | equipment | `commissioning_date` antérieure à la fin de période | conservee | |
| `R-EQ-006` | equipment | champs descriptifs renseignés | conservee | |
| `R-EVT-001` | events | `event_id` unique | **etendue** | idem `R-SEN-001` |
| `R-EVT-002` | events | `severity` dans le domaine fermé | conservee | |
| `R-EVT-003` | events | `event_type` normalisé et dans le domaine | conservee | |
| `R-EVT-004` | events | `end_at` postérieure à `start_at` | conservee | |
| `R-EVT-005` | events | `equipment_id` présent dans la table préparée | conservee | |
| `R-MNT-001` | maintenance | `maintenance_id` unique | **etendue** | idem `R-SEN-001` |
| `R-MNT-002` | maintenance | `event_id` présent dans la table préparée | conservee | |
| `R-MNT-003` | maintenance | `equipment_id` présent dans la table préparée | conservee | |
| `R-MNT-004` | maintenance | `closed_at` postérieure à `opened_at` | conservee | |
| `R-MNT-005` | maintenance | `downtime_minutes` positive et plausible | conservee | |
| `R-MNT-006` | maintenance | `parts_cost_eur` positive | conservee | |
| `R-MNT-007` | maintenance | `intervention_type` normalisé et dans le domaine | conservee | |
| `R-MNT-008` | maintenance | absence d'information personnelle dans les notes | conservee | |

## Règles ajoutées en M3

Toutes portent sur `sensors`. Volumes constatés sur la livraison `2026-S1` :

| Règle | Contrôle | Décision | Lignes |
|---|---|---|---:|
| `R-SEN-001` | Clé logique `equipment_id + timestamp + sensor_name` unique | `doublon_supprime` / `exclue` | **14** |
| `R-SEN-002` | `timestamp` lisible ; fuseau explicite ou hypothèse UTC tracée | `valeur_normalisee` | 720 |
| `R-SEN-003` | Horodatage aligné sur la grille nominale 00/06/12/18 | `conserve_signale` | 1 *(série)* |
| `R-SEN-004` | Continuité de l'échantillonnage au pas de 6 h | `conserve_signale` | 10 |
| `R-SEN-005` | `sensor_name` normalisé et dans le domaine des 5 capteurs | `valeur_normalisee` | 40 |
| `R-SEN-006` | `unit` conforme à l'unité de référence du capteur | `valeur_normalisee` | 804 |
| `R-SEN-007` | `value` renseignée et numérique | `champ_neutralise` | 40 |
| `R-SEN-008` | `value` non sentinelle — une valeur négative est impossible | `champ_neutralise` | 12 |
| `R-SEN-009` | `value` dans la plage robuste du capteur (8 MAD) | `conserve_signale` | 10 |
| `R-SEN-010` | Capteur non figé — valeur constante prolongée | `exclue` | 80 |
| `R-SEN-011` | Absence de dérive monotone marquée | `conserve_signale` | 1 *(série)* |
| `R-SEN-012` | Absence de saut brutal (8 MAD **et** ≥ 10 % du niveau série) | `conserve_signale` | 1 |
| `R-SEN-013` | `equipment_id` présent dans le parc préparé | `exclue` | 30 |
| `R-SEN-014` | Mesure comprise dans la période annoncée | `conserve_signale` | 5 |
| `R-SEN-015` | Étiquette `period` cohérente avec la date | `valeur_normalisee` | 30 |

### Deux règles signalent au niveau *série*, pas au niveau ligne

`R-SEN-003` (série décalée de la grille) et `R-SEN-011` (dérive) portent sur le
comportement d'une série entière. Une première version émettait une ligne de
quarantaine **par mesure** : 720 et 719 lignes respectivement, soit 1 439 entrées
qui noyaient les 14 rejets réellement informatifs de `R-SEN-001`.

Ces deux règles émettent désormais **une ligne par série**, dont la raison porte
le volume concerné (« série décalée — relevés à [2, 8, 14, 20] h, 720 mesures
concernées »). L'information est conservée, la quarantaine redevient lisible.

### `R-SEN-012` — un détecteur que ses propres tests ont invalidé

La première version rapportait l'écart entre deux mesures à l'**écart-type** des
écarts de la série. Un test construit exprès — un pic à 25 sur une base à 2,8 —
n'était pas détecté : les deux écarts extrêmes que produit un saut isolé (l'aller
et le retour) **gonflent l'écart-type qui sert à les mesurer**, et le rapport
retombe à 4,3, sous le seuil de 8.

C'est la mécanique des sentinelles transposée à un autre estimateur : la valeur
cherchée fausse le détecteur censé la trouver. Sur les données réelles le défaut
était invisible, parce que l'unique saut du corpus était assez entouré pour
rester mesurable.

Remplacé par le **MAD des écarts** (× 1,4826 pour rester comparable à un
écart-type). Ce critère seul s'est révélé trop sensible dans l'autre sens : sur
une série synthétique très régulière, le MAD devient minuscule et le détecteur
signalait 38 « sauts » sur 40 points. D'où un **second garde-fou d'amplitude** :
l'écart doit aussi atteindre 10 % du niveau médian de la série. Un saut brutal
doit l'être physiquement, pas seulement statistiquement.

Résultat inchangé sur la livraison réelle — un saut, `EQ-FAN-304` le 11/05 — mais
le détecteur résiste désormais aux deux cas limites.

### Ordre d'application — trois contraintes non négociables

1. **`R-SEN-005` (nom de capteur) en premier.** Sans normalisation préalable, les
   40 lignes `TEMPERATURE_C ` ne sont reconnues comme des températures par aucune
   règle en aval : ni contrôle d'unité, ni contrôle de plage.
2. **`R-SEN-008` (sentinelles) avant tout contrôle de comportement.** Les 12
   valeurs `-999` multiplient l'écart-type de `vibration_mm_s` par 36. Laissées
   en place, elles faussent le seuil de saut, écrasent la plage robuste et
   fabriquent un faux saut brutal à chaque occurrence.
3. **Les exclusions après les normalisations**, pour que la quarantaine porte la
   valeur telle qu'elle a été **reçue**, et non une valeur déjà transformée.

### Arbitrage tracé — clés à valeurs divergentes (`R-SEN-001`)

10 clés portent plusieurs lignes. Deux cas, deux décisions :

- **6 clés / 12 lignes — doublons stricts** : toutes les colonnes sont
  identiques. Une ligne est conservée, l'autre part en quarantaine avec
  `doublon_supprime`. Aucune information perdue.
- **4 clés / 8 lignes — valeurs divergentes** : le fichier affirme deux valeurs
  différentes pour le même instant.

| Clé | Valeurs en conflit | Écart |
|---|---|---:|
| `EQ-CHILL-115` · 13/03 18:00 · `temperature_c` | 55,72 / 66,45 °C | 17,6 % |
| `EQ-COMP-396` · 18/06 06:00 · `pressure_bar` | 6,29 / 8,12 bar | 25,4 % |
| `EQ-OVEN-366` · 26/02 06:00 · `temperature_c` | 47,60 / 56,87 °C | 17,7 % |
| `EQ-PUMP-171` · 17/02 18:00 · `temperature_c` | 59,40 / 70,79 °C | 17,5 % |

**Décision retenue : aucune des deux valeurs n'est conservée** — les 8 lignes
sont exclues et tracées.

Options écartées et pourquoi :

- *garder la première occurrence* — déterministe, mais l'ordre des lignes dans
  un export n'a aucune signification métier ; le choix serait arbitraire tout en
  ayant l'air d'une règle ;
- *arbitrer sur le voisinage* — défendable sur `EQ-COMP-396`, où 8,12 bar est
  hors du voisinage immédiat (6,07 / 5,73 avant, 6,39 / 6,01 après) **et**
  constitue le maximum global du capteur. Mais sur les trois autres cas, les
  deux valeurs candidates tombent dans la plage d'oscillation normale de la
  série : l'arbitrage y redeviendrait arbitraire sous une apparence de méthode ;
- *moyenne des deux* — produit une valeur que le capteur n'a jamais mesurée, et
  qui devient indiscernable d'une vraie mesure en aval.

**Coût assumé** : 4 mesures perdues sur des séries de 720 points, soit 0,008 % du
fichier, et 4 trous de 6 h. Ces trous sont eux-mêmes remontés par `R-SEN-004` —
la pipeline signale la discontinuité que notre propre décision vient de créer,
ce qui est le comportement attendu.

## Non-régression sur les tables M2

**Exigence** : démontrée, pas affirmée.

**Ce qui est vérifié** : les trois tables héritées traversent la pipeline sans
transformation. Le contrôle relit les fichiers **écrits par la pipeline** — et
non les objets en mémoire — puis les compare à l'entrée colonne par colonne et
ligne par ligne (`pandas.DataFrame.equals`). Passer par l'aller-retour CSV fait
subir au contrôle exactement ce que subissent les consommateurs en aval.

| Table | Lignes avant | Lignes après | Colonnes | Contenu |
|---|---:|---:|---|---|
| `equipment` | 416 | 416 | identiques | **identique** |
| `events` | 514 | 514 | identiques | **identique** |
| `maintenance_history` | 1 788 | 1 788 | identiques | **identique** |

`run_pipeline_m3.py` retourne un **code de sortie non nul** si la non-régression
échoue : elle n'est pas seulement rapportée, elle bloque.

**Portée réelle de cette démonstration — à ne pas surinterpréter.** Le point de
départ étant l'état préparé de référence, les règles M2 ne sont pas ré-exécutées
ici : ce qui est démontré, c'est que **l'ajout de la source capteurs ne modifie
pas l'acquis M2**. Ce n'est pas une revalidation des règles M2 elles-mêmes, qui
relève du module précédent. La formulation est délibérée : une non-régression
qui prétendrait plus que ce qu'elle contrôle serait pire qu'absente.

## Quarantaine unifiée

**1 833 lignes**, format et vocabulaire M2 identiques pour les quatre sources :
`source_file`, `row_identifier`, `rule_id`, `column`, `observed_value`, `reason`,
`decision`.

| Source | Lignes |
|---|---:|
| `sensor_readings.csv` | 1 798 |
| `maintenance_history.csv` | 18 |
| `equipment.csv` | 9 |
| `events.csv` | 8 |

| Décision | Lignes |
|---|---:|
| `valeur_normalisee` | 1 597 |
| `exclue` | 127 |
| `champ_neutralise` | 57 |
| `conserve_signale` | 31 |
| `doublon_supprime` | 19 |
| `pseudonymise` | 2 |

Les 35 lignes de la quarantaine M2 sont reprises **intégralement**, sans
réécriture ni renumérotation.

Le volume est dominé par `valeur_normalisee` (87 %) : 804 conversions d'unité,
720 hypothèses de fuseau, 40 noms de capteur, 30 étiquettes de période. Ce sont
des transformations réelles appliquées à des lignes réelles — chacune mérite sa
trace. Les rejets qui retirent de la donnée sont beaucoup plus rares : **127
exclusions**, soit 0,25 % des mesures.

`row_identifier` d'une mesure est le triplet de sa clé logique, avec les valeurs
**telles que reçues** — y compris `TEMPERATURE_C ` avec sa casse et son espace.
Un identifiant doit permettre de retrouver la ligne dans le fichier d'origine,
pas de la corriger.

## Vocabulaire des décisions

Repris de M2 sans modification.

| Décision | Sens | Emploi en M3 |
|---|---|---|
| `doublon_supprime` | ligne strictement identique retirée, trace conservée | doublons stricts de clé |
| `exclue` | ligne retirée de la table préparée | clé divergente, équipement inconnu, capteur figé |
| `champ_neutralise` | ligne conservée, champ vidé et tracé | sentinelle `-999`, valeur absente |
| `valeur_normalisee` | valeur corrigée de façon déterministe | unité, nom de capteur, fuseau, étiquette de période |
| `conserve_signale` | ligne conservée, anomalie signalée pour expertise | hors période, hors grille, dérive, saut, dépassement de plage |
| `pseudonymise` | information directe remplacée par un marqueur stable | hérité M2 uniquement |

## Résultat

**50 401 mesures reçues → 50 277 mesures préparées.** 124 lignes retirées
(0,25 %) : 80 figées, 30 rattachées à un équipement inconnu, 8 en clé divergente,
6 doublons stricts.

## Limites connues

- Les règles M2 ne sont pas ré-exécutées : elles sont **portées et statuées**,
  pas revalidées (voir la portée de la non-régression ci-dessus).
- Les seuils de `R-SEN-009` (8 MAD), `R-SEN-010` (8 relevés), `R-SEN-011` (0,30
  de corrélation) et `R-SEN-012` (8 σ) sont des choix. Deux d'entre eux ont déjà
  dû être corrigés après avoir produit des résultats manifestement faux — un
  seuil au 99ᵉ centile pour la plage, et un seuil de corrélation à 0,70 pour la
  dérive. Rien ne garantit que les seuils actuels ne laissent pas passer des
  anomalies plus discrètes.
- `R-SEN-009` compare chaque valeur à la médiane de **son capteur, tous
  équipements confondus**. Une vibration élevée pour une pompe pourrait être
  normale pour un ventilateur. Des bornes par type d'équipement seraient plus
  justes ; le corpus — 36 équipements sur 11 types — est trop maigre pour les
  établir.
- L'hypothèse de fuseau UTC sur les 720 horodatages naïfs (`R-SEN-002`) reste
  une hypothèse. Elle est tracée ligne à ligne en quarantaine, donc réversible.
