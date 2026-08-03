# Diagnostic des données DiagOps — M2

**Périmètre** : `equipment.csv` (420), `events.csv` (520),
`maintenance_history.csv` (1 800), période `2026-S1`.
**Date de référence des contrôles** : 2026-08-03.
**Rejouable par** : `python run_audit_m2.py`.

Registre : 68 règles (`src/data_pipeline/rules.py`), conventions et
justifications dans `regles_qualite_m2.md`, révisions datées dans
`rules.REVISIONS`.

**Deux sources de référence, et leur partage.** Les domaines fermés
(`severity`, `criticality`, `event_type`, `intervention_type`, `outcome`) sont
importés de `contracts/schemas.py`, livré avec le starter. `SCHEMA.md` fait foi
pour tout le reste : colonnes attendues, types, nullabilité, relations.

Ce partage résulte d'une correction. Le registre avait d'abord été construit
sur le seul `SCHEMA.md`, qui annonce `alerte` là où le contrat et les données
disent `alert`, et qui décrit `intervention_type` et `outcome` en chaîne libre
alors que le contrat les donne fermés. Conséquences : 49 anomalies signalées
qui n'en étaient pas, et une colonne — `outcome` — que **aucune règle
d'appartenance ne contrôlait**. Elle s'est révélée propre, par chance et non
par méthode. Les domaines ne sont plus recopiés, ils sont importés : une valeur
de référence dupliquée à deux endroits finit toujours par diverger.

---

## 1. Que représente chaque fichier et comment les sources sont-elles reliées ?

| Table | Une ligne représente | Clé | Volume |
|---|---|---|---:|
| `equipment` | un équipement du parc | `equipment_id` | 420 |
| `events` | un événement survenu sur un équipement — incident, intervention, observation, alerte | `event_id` | 520 |
| `maintenance_history` | une intervention de maintenance | `maintenance_id` | 1 800 |

Trois relations annoncées, toutes vérifiées :

```
events.equipment_id              → equipment.equipment_id
maintenance_history.equipment_id → equipment.equipment_id
maintenance_history.event_id     → events.event_id
```

**Une propriété que le schéma ne dit pas et qui produit un contrôle** :
`maintenance_history` désigne l'équipement **deux fois**, directement par
`equipment_id` et indirectement via `event_id → events.equipment_id`. Les deux
chemins doivent concorder. C'est la règle `MNT-REF-003`, née de la redondance
entre deux relations documentées séparément.

Le sens analytique de la période `2026-S1` n'est pas documenté ; seule cette
période est livrée, alors que le schéma en prévoit trois.

## 2. Les données nécessaires au cas DiagOps sont-elles présentes et lisibles ?

Oui. Les 27 colonnes annoncées sont présentes (7 + 7 + 13), aucune valeur
n'échoue à la conversion dans son type attendu : dates lisibles en ISO 8601,
numériques convertibles, compteurs entiers.

Les valeurs absentes sont marginales et toutes prévues par le schéma :

| Colonne | Taux d'absence | Lecture |
|---|---:|---|
| `manufacturer` | 0,2 % | nullable au schéma |
| `rated_power_kw` | 0,2 % | nullable au schéma |
| `end_at` | 2,5 % | événement en cours |
| `closed_at` | 2,7 % | intervention en cours |
| `labor_hours` | 0,1 % | nullable |
| `parts_cost_eur` | 1,5 % | nullable |

Aucun champ n'est vide au point d'être inexploitable. `end_at` et `closed_at`
portent une information : le nul y signifie *en cours*, pas *manquant*.

## 3. Quels problèmes d'identifiants, de doublons ou de relations avez-vous détectés ?

**Doublons — 26 identifiants dupliqués, tous explicables.**

| Table | Identifiants dupliqués | Lignes intégralement dupliquées |
|---|---:|---:|
| `equipment` | 8 (4 paires) | 4 |
| `events` | 8 (4 paires) | 4 |
| `maintenance_history` | 10 (5 paires) | 5 |

Le rapprochement des deux colonnes est le résultat le plus important de
l'audit : **chaque identifiant dupliqué correspond à une ligne strictement
identique à une autre**, sur toutes ses colonnes. Il n'existe aucun cas de
« même identifiant, contenu différent » — celui qui aurait exigé un arbitrage
métier. La déduplication les résout intégralement, sans perte d'information et
sans décision arbitraire.

**Relations — 3 références orphelines.**

| Cas | Règle | Impact |
|---|---|---|
| `EVT-2026S1-0180` pointe un équipement inexistant | `EVT-REF-002` | événement non rattachable au parc |
| `MNT-2026S1-0389` pointe un événement inexistant | `MNT-REF-001` | intervention sans contexte |
| `MNT-2026S1-0545` pointe un équipement inexistant | `MNT-REF-002` | intervention non rattachable |

`MNT-2026S1-0545` échoue aussi `MNT-REF-003` : son `equipment_id` contredit
celui de son événement. Les deux chemins de désignation divergent, et rien
n'indique lequel fait foi.

Ces trois cas représentent 0,19 % des événements et 0,11 % des interventions.
Ils sont peu nombreux mais **rompent les relations que le brief désigne comme
structurantes** — c'est la seule catégorie d'anomalie qui subsiste au niveau
bloquant après préparation.

## 4. Quelles règles métier ne sont pas respectées ?

**Énumérations fermées — une anomalie par colonne, jamais plus.** Confrontation
aux cinq domaines de `contracts/schemas.py` :

| Colonne | Hors contrat | Effectif |
|---|---|---:|
| `severity` | `URGENT` (`EVT-2026S1-0102`) | 1 |
| `event_type` | `Incident ` — espace final (`EVT-2026S1-0265`) | 1 |
| `intervention_type` | `Correctif` (`MNT-2026S1-0912`) | 1 |
| `criticality` | — | 0 |
| `outcome` | — | 0 |

Aucune valeur de ces cinq domaines n'est absente des données : les cinq types
d'intervention et les cinq résultats prévus sont tous observés.

**Cohérence temporelle** — 3 cas :

- `EVT-2026S1-0032` : `end_at` antérieur à `start_at` ;
- `MNT-2026S1-0621` : `closed_at` antérieur à `opened_at` ;
- `EVT-2026S1-0467` : événement antérieur à la mise en service de son
  équipement — incohérence **entre deux tables**, sans indication de laquelle
  porte l'erreur.

**Valeurs impossibles** — 4 cas :

- `EQ-CONV-137` : mise en service dans le futur ;
- `EQ-COMP-169` : puissance nominale négative ;
- `MNT-2026S1-0041` : durée d'indisponibilité négative ;
- `MNT-2026S1-0703` : coût de pièces négatif.

**Durées incohérentes** — 2 cas où `downtime_minutes` dépasse l'écart réel
entre ouverture et clôture (`MNT-2026S1-0206`, `MNT-2026S1-0621`). Le premier
dépasse aussi la borne des 30 jours.

## 5. Quelles anomalies peuvent être corrigées de manière certaine ?

Huit opérations, 18 lignes touchées. Journal complet dans
`output/transformation_log.csv`.

| Règle | Correction | Lignes |
|---|---|---:|
| `EQP-KEY-003` · `EVT-KEY-003` · `MNT-KEY-003` | suppression des doublons intégraux | 4 · 4 · 5 |
| `EVT-CAS-001` | `Incident` → `incident` | 1 |
| `EQP-CAS-002` | `Pump ` → `pump` | 1 |
| `MNT-CAS-001` | `Correctif` → `corrective` | 1 |
| `MNT-PII-001` | note masquée | 2 |

**420 → 416 · 520 → 516 · 1 800 → 1 795.**

Ce qui rend ces corrections certaines, règle par règle :

- **Doublons intégraux** : toutes les colonnes sont égales, la copie n'apporte
  rien. Le premier exemplaire est conservé (`keep='first'`).
- **`Incident`** : la forme normalisée correspond à une valeur du schéma. Les
  deux écritures désignent la même classe.
- **`Pump `** : catégorie ouverte, donc aucune énumération de référence — mais
  la forme normalisée coïncide avec un libellé existant, et l'écart d'effectif
  est de 1 contre 56.
- **`Correctif` → `corrective`** : `correctif` et `corrective` **diffèrent après
  normalisation** — ce n'est pas une variante de casse mais un mélange
  français/anglais. La correction se fonde sur le contrat, qui donne
  `corrective` comme valeur canonique du domaine ; sans lui, l'équivalence
  serait restée un arbitrage. Elle est déclarée dans
  `rules.DECLARED_LABEL_EQUIVALENCES` pour rester contestable sans relire le
  code.

**Deux points de méthode** :

L'ordre des opérations n'est pas neutre. La déduplication passe **avant** la
normalisation de casse : dans l'autre sens, normaliser `Incident` en `incident`
pourrait rendre deux lignes identiques, que la déduplication supprimerait — on
aurait fabriqué un doublon puis effacé une ligne réelle.

`URGENT` n'est **pas** corrigé. Sa forme normalisée reste inconnue du domaine :
le corriger serait deviner à quel niveau il correspond.

## 6. Quelles anomalies doivent être mises à l'écart ou examinées par un expert ?

Après préparation, **12 lignes distinctes** restent en quarantaine
(`output/quarantine.csv`), sur 2 727 lignes préparées — 0,44 %.

| Nature | Lignes | Pourquoi un humain doit trancher |
|---|---:|---|
| Références orphelines | 3 | Corriger supposerait de deviner la bonne cible ; supprimer perdrait une observation réelle |
| Incohérences temporelles | 3 | Deux dates se contredisent, aucune n'est identifiable comme fausse |
| Valeurs impossibles | 4 | Un signe négatif peut être une erreur de saisie ou un avoir ; seule la source le dira |
| Durées incohérentes | 2 | Deux systèmes se contredisent sur la même intervention |
| `severity` = `URGENT` | 1 | Valeur inconnue : correspond-elle à `critical`, ou à un niveau non prévu ? |

**Un constat signalé sans rejet**, parce que l'écarter reviendrait à mutiler le
jeu :

**`parts_cost_eur > 0` sans pièce remplacée — 595 interventions (33 %).** Cette
règle avait été écrite comme règle de rejet. La mesure l'a invalidée : les 595
cas se répartissent uniformément sur les cinq types d'intervention
(calibration 135, inspection 121, corrective 114, preventive 113,
replacement 112). Une anomalie ne se distribue pas ainsi. C'est un motif
structurel du jeu, pas un défaut. La règle est passée en signalement, et la
question part au métier : que recouvre un coût de pièces sans pièce déclarée —
consommables, forfait, main d'œuvre imputée en pièces ?

## 7. Les notes contiennent-elles des informations relatives à des personnes, et quelle décision ?

**Oui, 2 sur 1 800.**

```
MNT-2026S1-1121   Rappeler Nadia B. au 06 12 34 56 78.
MNT-2026S1-1334   Compte rendu transmis à leo.martin@example.test.
```

**La vérification est exhaustive, pas échantillonnée.** Le champ
`work_order_note` ne contient que **7 valeurs distinctes sur 1 800 lignes** —
cinq phrases types d'un gabarit (385, 371, 358, 352 et 332 occurrences) plus
les deux cas ci-dessus. Les 7 valeurs ont été lues : aucun faux négatif n'est
possible. La détection automatique par motifs a servi à cibler ; c'est
l'énumération complète des valeurs qui conclut.

**Décision : masquer le champ, conserver la ligne.** 1 800 lignes sur 1 800
préservées. La minimisation impose de retirer ce qui n'est pas nécessaire à la
finalité — un diagnostic de panne n'a besoin ni d'un téléphone ni d'une
adresse — mais rien ne justifie d'écarter deux interventions dont les dates,
durées, coûts et types sont valides.

**Le champ est masqué en entier, pas par fragment.** Le jeu fournit l'argument :
dans `Rappeler Nadia B. au 06 12 34 56 78.`, le motif téléphone attrape le
numéro, mais `Nadia B.` ne déclenche aucun motif — aucune civilité ne la
précède. Un masquage partiel aurait laissé un nom en clair dans une ligne
paraissant assainie. La fausse assurance est pire que l'absence de traitement.

**Où le masquage s'applique** :

| Artefact | Contenu | Destination |
|---|---|---|
| `output/processed/` | note remplacée par `[NOTE MASQUEE — DONNEE PERSONNELLE]` | M3 |
| `output/quarantine.csv` | valeur observée en clair | relecteur humain |
| `output/transformation_log.csv` | état avant en clair, après masqué | preuve de réversibilité |

La quarantaine et le journal conservent la valeur d'origine : le brief l'exige,
et sans elle un relecteur ne peut ni confirmer la détection ni vérifier la
correction. Ces deux fichiers sont des artefacts d'audit, ils n'alimentent
aucun traitement en aval.

Détail : `.test` est un domaine réservé par la RFC 2606 et `06 12 34 56 78` est
une suite — les deux valeurs sont manifestement fabriquées. Le traitement
appliqué est néanmoins identique à celui de données réelles.

## 8. Certaines catégories sont-elles peu représentées ?

Seuil d'interprétabilité retenu : **30 observations**. C'est une convention
assumée, documentée dans `coverage.py` ; elle ne démontre rien, elle force la
mention de l'incertitude.

**Sites** — `SITE-NORD` 176, `SITE-SUD` 137, `SITE-EST` 91, **`SITE-OUEST` 16
(3,8 %)**. Le dernier est sous le seuil : aucune conclusion par site ne pourra
le concerner.

**Types d'équipement** — 18 types après correction de `Pump `, dont **12 sous le
seuil** : `lift` 5, `steam_unit` 5, `motor` 7, `packaging_machine` 7, `dryer` 8,
`gearbox` 8, `electrical_cabinet` 12, `sensor` 16, `valve` 21, `mixer` 22,
`chiller` 24. Au-dessus : `press` 34, `fan` 34, `oven` 36, `compressor` 38,
`conveyor` 41, `robot` 45, `pump` 57.

**Criticité** — `medium` 174, `high` 122, `low` 76, `critical` 48. Le seul axe
entièrement exploitable.

**Sévérité des événements** — `high` 213, `medium` 160, `critical` 74, `low` 72.

**Le défaut de couverture le plus lourd : 41 équipements sur 420 (9,8 %) n'ont
ni événement ni intervention.** Ils figurent au parc et n'ont produit aucune
observation sur la période. Répartition : `medium` 17, **`high` 12**, `low` 9,
**`critical` 3**. Quinze équipements jugés importants sur lesquels M3 n'aura
rien à apprendre.

Ce n'est pas une anomalie de qualité — les données sont correctes. C'est une
limite du jeu, et elle doit accompagner tout modèle entraîné dessus.

## 9. Les erreurs historiques de M1 sont-elles plus fréquentes dans certaines catégories ?

Source : `reference_runs/m1_for_m2/analyses/matrice_erreurs_m1.csv`, 80 cas.
12 erreurs de sévérité, 1 erreur de revue humaine, 1 schéma invalide.

**Le résultat n'est pas dans les découpages par catégorie, il est dans la
matrice de confusion** :

| Attendu | Prédit | Cas |
|---|---|---:|
| `critical` | `high` | 7 |
| `critical` | `medium` | 2 |
| `low` | *`light`* | 1 |
| `low` | `medium` | 1 |
| `medium` | `high` | 1 |

**9 erreurs sur 12 sont des `critical` sous-évalués.** Sur un outil de
maintenance, c'est la direction dangereuse : sous-estimer une panne critique
coûte davantage que l'inverse. Par ailleurs `light` n'appartient à aucune
énumération — le modèle a produit une valeur inventée.

**Les découpages par catégorie ne concluent rien** :

| Découpage | Taux le plus élevé | Effectif |
|---|---|---:|
| Site | `SITE-OUEST` 50 % | **2** |
| Type d'équipement | `fan` 57 % · `press` 50 % | **7 · 8** |
| Criticité équipement | `critical` 28,6 % | **7** |
| Sévérité événement | `critical` 69 % | **13** |

Un seul groupe dépasse 30 observations dans chaque découpage. Sur `SITE-OUEST`,
deux lignes suffisent à afficher 50 % — une erreur de plus ou de moins fait
basculer de 0 % à 100 %.

**Les limites de ce constat, explicitement** :

1. **Effectifs insuffisants.** Le seul contraste marquant — 0 erreur sur 34 cas
   `high` contre 9 sur 13 `critical` — repose sur 13 observations.
2. **Biais de sélection introduit par l'analyse.** 7 des 80 cas ont un
   `equipment_id` nul et sortent de toute jointure. Ce ne sont pas des
   références cassées : ce sont les cas M1 où l'équipement n'était pas
   identifiable. Or ils affichent **0 % d'erreur** contre 16,4 % pour les 73
   restants. La jointure ne retire que des cas réussis : toute concentration
   observée ensuite est mécaniquement gonflée.
3. **Glissement de vocabulaire à éviter.** « Les erreurs se concentrent sur les
   équipements critiques » serait faux. Ce qu'on observe, c'est que **le modèle
   rate la classe `critical`** — une propriété du modèle, pas du parc. Un taux
   d'erreur par sévérité attendue est une ligne de matrice de confusion.

Cohérent avec ce que l'on savait de M1 : `critical` était la classe la plus
rare à l'entraînement. **Hypothèse à tester sur un échantillon plus large, pas
conclusion.** Aucune causalité n'est démontrée ni suggérée.

## 10. Les données peuvent-elles être transmises à M3, et sous quelles conditions ?

### Décision : **utilisables sous conditions**

### Ce qui a été vérifié

68 règles exécutées sur les trois tables, 26 en échec avant préparation.
Structure conforme, types lisibles, valeurs absentes marginales et prévues.
Les trois relations annoncées sont contrôlées, ainsi que la cohérence entre les
deux chemins de désignation de l'équipement. Les cinq domaines fermés du
contrat sont confrontés aux données : **une seule valeur hors domaine par
colonne, aucune sur `criticality` et `outcome`**.

### Ce qui a été transformé

18 lignes sur 2 740, toutes tracées dans `output/transformation_log.csv` avec
état avant et après. Aucune suppression silencieuse. Les fichiers reçus sont
inchangés — vérifié par comparaison d'empreintes SHA-256 avant et après
exécution.

**Le point qui pèse le plus dans la décision** : les 26 identifiants dupliqués,
seule anomalie bloquante de volume, étaient **tous** des lignes intégralement
dupliquées. Leur correction est certaine et n'a demandé aucun arbitrage. Après
préparation, il ne reste que **3 anomalies bloquantes** sur 2 727 lignes.

### Ce qui reste incertain

| Point | Volume | Nature |
|---|---:|---|
| Références orphelines | 3 lignes | rompent les relations structurantes |
| Coût sans pièce | 595 interventions | motif structurel non expliqué |
| Incohérences temporelles et valeurs impossibles | 10 lignes | arbitrage métier |
| `severity` = `URGENT` | 1 ligne | valeur non interprétable |
| Équipements sans activité | 41 (9,8 %) | limite de couverture |
| `SCHEMA.md` contredit le contrat | 1 ligne de doc | à corriger en amont |

### Conditions à satisfaire avant M3

1. **Statuer sur les 3 références orphelines** — rattacher ou écarter. Elles
   sont peu nombreuses mais brisent l'intégrité relationnelle du jeu, et
   `MNT-2026S1-0545` cumule deux défauts : équipement inexistant, et
   contradiction avec l'équipement de son événement.
2. **Obtenir une réponse métier sur `parts_cost_eur`** sans pièce déclarée.
   Tant qu'elle n'est pas donnée, aucune analyse de coût en M3 ne repose sur
   une base interprétable.
3. **Arbitrer les 12 lignes en quarantaine** — dates contradictoires, valeurs
   négatives, `URGENT`.
4. **Documenter les limites de couverture dans toute production M3.**
   `SITE-OUEST`, les 12 types sous le seuil et les 41 équipements muets — dont
   3 `critical` et 12 `high` — bornent ce qu'un modèle entraîné sur ce jeu peut
   prétendre couvrir.

**Signalement au fournisseur des données** : `SCHEMA.md` annonce `alerte` là où
le contrat `contracts/schemas.py` et les 49 lignes concernées disent `alert`,
et décrit `intervention_type` et `outcome` en chaîne libre alors que le contrat
les donne fermés. Ce n'est pas une condition — les données sont correctes — mais
un défaut de documentation qui a déjà produit un faux diagnostic dans cet audit
et en produira d'autres tant qu'il subsiste.

### Ce que cette décision ne dit pas

Elle porte sur **l'état des données**, pas sur la promotion du modèle M1. Le
jeu de validation M1 est un historique déjà consulté ; il ne redevient pas un
test inédit.

Aucun lien de causalité n'est établi entre une caractéristique du parc et une
erreur du modèle. La seule régularité observée — le modèle sous-évalue
`critical` — est une hypothèse documentée, appuyée sur 13 cas, et signalée
comme telle.
