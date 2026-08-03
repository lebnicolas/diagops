# Note de décision — préparation des données M2

**Objet** : statuer sur la transmission à M3 des trois sources DiagOps
`2026-S1`.
**Date** : 2026-08-03.
**Rejouable par** : `python run_audit_m2.py`.
**Détail des constats** : `diagnostic_donnees.md`.

---

## Statut : utilisables sous conditions

## Ce qui fonde la décision

**Aucun défaut structurel.** Les 27 colonnes annoncées sont présentes, aucune
valeur n'échoue à la conversion dans son type attendu, les valeurs absentes
sont marginales et toutes prévues par le schéma. Les cinq domaines fermés du
contrat sont respectés à **une valeur près par colonne**, et aucune sur
`criticality` et `outcome`.

**La preuve déterminante.** Les 26 identifiants dupliqués — 8 sur `equipment`,
8 sur `events`, 10 sur `maintenance_history` — correspondent **tous** à des
lignes strictement identiques à une autre, sur l'intégralité de leurs colonnes.
Il n'existe aucun cas de « même identifiant, contenu différent ».

C'est ce qui fait basculer la décision. Un identifiant dupliqué sur des lignes
divergentes aurait imposé un arbitrage impossible à automatiser, sur 26 lignes
réparties dans les trois tables — soit un défaut d'intégrité de fond. Un
doublon intégral se supprime sans perte ni décision. Le rapprochement entre les
règles `KEY-002` (unicité de la clé) et `KEY-003` (ligne entière dupliquée)
sépare exactement ces deux situations ; il ne servait qu'à ça, et c'est ici
qu'il paie.

**Après préparation, il reste 3 anomalies bloquantes sur 2 727 lignes** — les
trois références orphelines — et 12 lignes distinctes en quarantaine, soit
0,44 % du jeu.

## Options considérées

| Option | Écartée / retenue | Motif |
|---|---|---|
| **Utilisables** | écartée | Trois références orphelines rompent des relations que le brief désigne comme structurantes. Les livrer sans arbitrage ferait porter l'incertitude à M3 sans qu'il le sache. |
| **Utilisables sous conditions** | **retenue** | Les défauts restants sont peu nombreux, identifiés ligne à ligne, et aucun ne demande de retoucher la structure. Ils demandent des décisions, pas des corrections. |
| **Non utilisables en l'état** | écartée | Aurait été le choix si les identifiants dupliqués avaient porté des contenus divergents. La mesure a montré l'inverse. |

## Ce qui a été transformé

18 lignes sur 2 740, toutes tracées dans `output/transformation_log.csv` avec
état avant et après. **Aucune suppression silencieuse.**

| Règle | Correction | Lignes |
|---|---|---:|
| `EQP-KEY-003` · `EVT-KEY-003` · `MNT-KEY-003` | doublons intégraux | 13 |
| `EVT-CAS-001` · `EQP-CAS-002` · `MNT-CAS-001` | libellés normalisés | 3 |
| `MNT-PII-001` | notes masquées | 2 |

Les fichiers reçus sont inchangés : vérifié par comparaison d'empreintes
SHA-256 avant et après exécution, contrôle intégré au script.

## Conditions à satisfaire avant M3

| # | Condition | Volume | Qui tranche |
|---|---|---:|---|
| 1 | Statuer sur les références orphelines — rattacher ou écarter | 3 lignes | métier + fournisseur des données |
| 2 | Expliquer les coûts de pièces sans pièce déclarée | 595 interventions | métier |
| 3 | Arbitrer la quarantaine — dates contradictoires, valeurs négatives, `URGENT` | 12 lignes | métier |
| 4 | Documenter les limites de couverture dans toute production M3 | — | équipe M3 |

**Priorité à la condition 2 en volume**, à la condition 1 en gravité. La 2 ne
bloque pas la transmission mais rend inexploitable toute analyse de coût tant
qu'elle n'est pas levée — un tiers des interventions est concerné.

`MNT-2026S1-0545` cumule deux défauts et mérite un traitement à part :
équipement inexistant, **et** contradiction entre son `equipment_id` et celui
de son événement. Les deux chemins de désignation divergent ; rien n'indique
lequel fait foi.

## Signalement au fournisseur des données

Sans effet sur la décision — les données sont correctes — mais à remonter.

`data_pack/SCHEMA.md` contredit `starter/contracts/schemas.py` sur trois
colonnes : il annonce `alerte` là où le contrat et les 49 lignes concernées
disent `alert`, et décrit `intervention_type` et `outcome` en chaîne libre
alors que le contrat les donne fermés.

Ce défaut a déjà produit un faux diagnostic dans cet audit — 49 anomalies
signalées à tort, et une colonne laissée sans contrôle d'appartenance. Il en
produira d'autres tant que les deux sources divergeront.

## Limites et réversibilité

**Réversible.** Les fichiers reçus sont intacts, chaque transformation est
tracée avec son état initial, et l'ensemble se rejoue par une commande. Revenir
en arrière ne demande aucune reconstruction.

**Ce que cette décision ne couvre pas** :

- Elle porte sur l'état des données, **pas** sur la promotion du modèle M1. Le
  jeu de validation M1 est un historique déjà consulté ; il ne redevient pas un
  test inédit.
- Aucune causalité n'est établie entre une caractéristique du parc et une
  erreur du modèle. La seule régularité observée — le modèle sous-évalue
  `critical`, 9 erreurs sur 12 — repose sur 13 cas et reste une hypothèse.
- Les seuils ajoutés (30 observations pour l'interprétabilité, bornes
  numériques, 5 % et 10 occurrences pour la récurrence) sont des conventions
  assumées et documentées, pas des vérités démontrées. Elles forcent la mention
  de l'incertitude ; elles ne la lèvent pas.
- La détection de données personnelles repose sur des motifs. Sur ce jeu elle
  est doublée d'une vérification exhaustive — 7 valeurs distinctes sur 1 800
  lignes, toutes lues — mais cette exhaustivité tient à la nature gabarit du
  champ. Elle ne serait pas transposable à un texte libre réel.

## Ce que M3 hérite

```
output/processed/equipment.csv              416 lignes
output/processed/events.csv                 516 lignes
output/processed/maintenance_history.csv   1795 lignes
```

Accompagnés de `quarantine.csv` (60 entrées, 12 lignes distinctes),
`transformation_log.csv` (8 opérations) et `check_results.csv` (68 règles).

Les notes de maintenance sont masquées dans les tables préparées. La valeur
d'origine reste dans la quarantaine et le journal, qui sont des artefacts
d'audit destinés à un relecteur et n'alimentent aucun traitement en aval.
