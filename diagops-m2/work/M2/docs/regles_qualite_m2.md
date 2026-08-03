# Règles de qualité — M2

Registre écrit **avant toute mesure** sur les trois fichiers, à partir de
`data_pack/SCHEMA.md` et des axes du brief. Aucune valeur des CSV n'a été
consultée à ce stade.

Source de vérité : `src/data_pipeline/rules.py`. Ce document explique les
conventions, les choix qui ne se déduisent pas du schéma, et les règles qui ont
été volontairement écartées.

## Pourquoi écrire les règles d'abord

Une règle formulée après avoir vu les données a tendance à épouser ce qu'on a
trouvé : on fixe le seuil juste au-dessus du cas gênant, on requalifie en
« acceptable » ce qu'on ne sait pas traiter. En posant la règle **et sa décision
d'échec** à l'avance, le chiffre ne peut plus déplacer la frontière.

Ça ne fige rien définitivement : une règle peut être ajoutée ou révisée après
mesure. Mais la révision se voit, elle est datée, et elle se justifie.

## Conventions

Identifiant : `<SOURCE>-<FAMILLE>-<NNN>`

| Segment | Valeurs |
|---|---|
| SOURCE | `EQP` equipment · `EVT` events · `MNT` maintenance_history |
| FAMILLE | `SCH` structure et types · `KEY` identifiants · `REF` références · `CAT` catégories · `TMP` cohérence temporelle · `VAL` valeurs impossibles · `NUL` valeurs manquantes · `PII` données personnelles |

**Sévérités** — `bloquante` (la donnée ne peut pas partir en M3 en l'état),
`majeure` (traitement obligatoire, ligne isolée), `mineure` (constat à
documenter).

**Décisions en cas d'échec** :

| Décision | Sens |
|---|---|
| `arret_audit` | la source n'est pas exploitable, on ne poursuit pas |
| `correction_certaine` | correction reproductible et non ambiguë, tracée dans le journal de transformation |
| `quarantaine_rejet` | la ligne est écartée du jeu transmis à M3 |
| `quarantaine_examen_metier` | la ligne est isolée, un humain tranche |
| `signalement` | constat chiffré, aucune ligne écartée |

## Répartition

| Source | Bloquantes | Majeures | Mineures | Total |
|---|---:|---:|---:|---:|
| equipment | 3 | 7 | 7 | 17 |
| events | 5 | 10 | 3 | 18 |
| maintenance_history | 5 | 14 | 6 | 25 |
| **Total** | **13** | **31** | **16** | **60** |

Par décision d'échec : 3 `arret_audit`, 4 `quarantaine_rejet`,
34 `quarantaine_examen_metier`, 6 `correction_certaine`, 13 `signalement`.

> Le registre comptait **54 règles avant la première mesure**. Il en compte 60
> après révision — voir la section « Révisions » en fin de document.

Le déséquilibre est volontaire : **35 règles sur 54 renvoient à un examen
métier**. À ce stade on ne sait presque rien du terrain, et une correction
automatique décidée depuis un schéma serait exactement la « correction
silencieuse » que le brief liste en critère bloquant.

## Les décisions qui ne se déduisent pas du schéma

Ce sont celles à valider ou à amender — le brief demande que toute règle ajoutée
soit **nommée et justifiée**.

### Bornes inventées

Le schéma ne donne aucune borne numérique. Quatre ont été posées, chacune
choisie pour attraper une **erreur d'unité ou une valeur par défaut**, pas pour
juger du métier :

| Règle | Borne | Ce qu'elle cherche |
|---|---|---|
| `EQP-TMP-002` | mise en service ≥ 1950-01-01 | les dates sentinelles type `1900-01-01` |
| `EQP-VAL-002` | puissance ≤ 10 000 kW | des watts saisis dans une colonne en kW |
| `MNT-VAL-002` | arrêt ≤ 43 200 min (30 j) | des secondes saisies dans une colonne en minutes |
| `MNT-VAL-004` | main d'œuvre ≤ 2 000 h | au-delà d'une année-homme sur une intervention |

Elles sont toutes en `quarantaine_examen_metier` et jamais en rejet : une valeur
hors borne est **suspecte**, pas fausse. C'est le point à défendre — une borne
arbitraire qui supprimerait des lignes serait indéfendable.

### Doublon exact vs clé dupliquée

Deux situations traitées différemment :

- **ligne intégralement identique** (`*-KEY-003`) → `correction_certaine`.
  Supprimer le second exemplaire ne perd aucune information, l'opération est
  reproductible. Elle reste tracée dans le journal de transformation.
- **même identifiant, lignes différentes** (`*-KEY-002`) →
  `quarantaine_examen_metier`. Rien ne permet de savoir laquelle est la bonne ;
  choisir automatiquement serait une correction silencieuse.

### Contradiction interne sur l'équipement

`MNT-REF-003` : `maintenance_history` porte `equipment_id` **et** `event_id`,
et `events` porte lui aussi `equipment_id`. L'équipement est donc désigné deux
fois par deux chemins. Une divergence est une contradiction — et rien ne dit
quel chemin fait foi. D'où l'examen métier plutôt qu'un arbitrage automatique.

C'est le contrôle le plus intéressant du lot : il ne se voit pas dans le schéma,
il naît de la redondance entre deux relations annoncées séparément.

### Contrôles croisés entre tables

`EVT-TMP-003` (événement antérieur à la mise en service) et `MNT-TMP-003`
(intervention ouverte avant le début de son événement) mettent en cause **deux
tables à la fois**. On ne peut pas dire laquelle porte l'erreur, seulement
qu'elles se contredisent. Les deux sont donc en examen métier.

### Catégories ouvertes

`site_id`, `equipment_type`, `intervention_type` et `outcome` sont annoncés
`string` sans liste fermée. On ne peut donc **rien rejeter** : les règles
correspondantes (`*-CAT-002`, `*-CAT-003`, `MNT-CAT-001/002`) se limitent à un
inventaire des valeurs et de leurs effectifs, avec signalement des libellés
rares ou visiblement voisins (`pompe` / `Pompe` / `pompes`). Une liste fermée ne
pourra être proposée qu'après avoir vu les données — et devra être validée par
le métier.

Seuls `criticality`, `severity` et `event_type` ont une énumération explicite
dans le schéma, donc une règle qui peut échouer.

### Le nul n'est pas toujours une anomalie

`end_at`, `closed_at`, `manufacturer` et `rated_power_kw` sont nullables au
schéma. Pour `end_at` et `closed_at`, le nul porte même une information :
événement ou intervention **en cours**. Les règles `*-NUL-*` ne rejettent donc
rien, elles mesurent un taux — un taux aberrant révélerait un export tronqué.

### Filtre de période

`EVT-CAT-003` et `MNT-CAT-003` exigent `period == 2026-S1`. Le schéma prévoit
trois périodes (`2026-S1`, `2026-S2`, `2027-S1`) mais la livraison n'en contient
qu'une. Une autre valeur signalerait un mélange de livraisons, qui fausserait
toute analyse temporelle.

## Règles écartées, et pourquoi

- **`labor_hours` ≤ durée d'intervention** — écartée. Plusieurs techniciens
  peuvent intervenir simultanément : 6 heures de main d'œuvre sur une
  intervention de 2 heures est parfaitement normal. La règle aurait produit du
  faux positif en masse.
- **`parts_replaced_count > 0` ⇒ `parts_cost_eur > 0`** — écartée dans ce sens.
  Une pièce prise sur un stock interne peut ne pas être valorisée. Seul le sens
  inverse est retenu (`MNT-VAL-007`) : facturer sans remplacer est une
  incohérence.
- **Équipement sans aucun événement** — ce n'est pas une anomalie de qualité
  mais une question de couverture. Traité à l'axe 3, pas ici.
- **Format des identifiants** (`EQ-…`, `EVT-…`) — non contrôlé. Le schéma
  n'impose aucun motif ; inventer une expression régulière reviendrait à
  fabriquer une règle à partir de ce qu'on croit avoir vu.

## Révisions — 03/08/2026, après la première mesure

Le registre a été confronté aux données réelles (420 / 520 / 1800 lignes).
Deux règles se sont révélées mal posées. Elles sont corrigées ici, et la
correction est datée : c'est la révision qui doit être visible, pas seulement
le résultat final.

Journal machine : `rules.REVISIONS`.

### `MNT-VAL-007` — rejet → signalement

**Constat** : 595 échecs sur 1 800 lignes, soit 33 %, répartis uniformément sur
les cinq `intervention_type` (calibration 135, inspection 121, corrective 114,
preventive 113, replacement 112).

**Lecture** : une anomalie ne se distribue pas régulièrement sur un tiers d'une
table. Le coût des pièces et le compteur de pièces sont simplement indépendants
dans ce jeu. La règle — « facturer des pièces sans en remplacer est
incohérent » — a été inventée depuis le schéma, sans connaître le terrain.

**Décision** : le constat reste publié, le rejet est retiré. Passe en
`signalement`, sévérité `mineure`. La question est posée au métier : que
recouvre un coût de pièces sans pièce déclarée — consommables, forfait,
main d'œuvre facturée en pièces ?

C'est exactement le motif pour lequel la règle `labor_hours ≤ durée` avait été
écartée d'avance. Le critère existait, il n'a pas été appliqué à celle-ci.

### `EVT-CAT-001` — scindée en trois

**Constat** : 50 échecs, dont `alert` × 49 et `Incident` × 1.

**Lecture** : deux causes sans rapport sous une seule règle.

- `SCHEMA.md` annonce `alerte`, la livraison écrit `alert`. Le schéma et les
  données ne parlent pas la même langue sur cette valeur. C'est un défaut de
  **documentation**, pas de donnée — et il touche 9,4 % de la table de façon
  parfaitement régulière.
- `Incident` avec une majuscule est la vraie anomalie : un cas isolé, une casse
  déviante. Elle était **invisible** derrière les 49 autres.

**Décision** : trois règles là où il y en avait une, distinction appliquée à
**toutes** les énumérations fermées et pas seulement à celle où le problème est
apparu :

| Suffixe | Situation | Décision |
|---|---|---|
| `CAT` | valeur inconnue et **isolée** | `quarantaine_examen_metier` |
| `NOM` | valeur inconnue et **récurrente** | `signalement` — écart de nomenclature |
| `CAS` | seule la casse ou l'espacement dévie | `correction_certaine` |

« Récurrente » se mesure par **deux conditions cumulatives** : au moins 5 % des
lignes **et** au moins 10 occurrences. Une part seule ne veut rien dire sur une
petite table — sur 3 lignes, une valeur unique pèse 33 %. Un effectif seul ne
veut rien dire sur une grande table. Ce point n'est pas théorique : la première
version, à seuil de part seul, classait mal le jeu de test et un test l'a
attrapée.

### Effet mesuré

| | Avant révision | Après |
|---|---:|---:|
| Règles au registre | 54 | 60 |
| Lignes en quarantaine | 701 | 57 |
| Lignes distinctes concernées | 670 | 28 |

Les 644 lignes sorties de la quarantaine n'ont pas disparu : elles sont
**signalées et chiffrées**, sans être écartées. C'est la différence entre un
audit qui documente et un audit qui mutile.

## Suite

Les contrôles sont implémentés (`src/data_pipeline/checks.py`) et exécutés
(`src/data_pipeline/audit.py`), avec cas valides et invalides dans `tests/`.
Restent : l'analyse de couverture et des erreurs M1 (axe 3), l'application des
6 règles `correction_certaine` avec état avant/après, et la décision finale.
