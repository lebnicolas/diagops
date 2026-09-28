# Contrat de migration — gelé avant mesure

**Gelé le 28/09/2026, au commit qui l'introduit.** Il est rédigé sur l'état
`0cf386e`, avant toute exécution du candidat sur les cas ci-dessous. Toute
modification ultérieure de ce fichier ou de `cases.jsonl` est une révision
datée, consignée en bas de page, jamais une réécriture silencieuse.

## Versions et empreintes

| Élément | Valeur |
|---|---|
| Source : manifeste du corpus | `knowledge/manifest.csv` `3b3dfb356eee…` |
| Source : code du banc | `lab.py` `00395b1b9a55…` (état corrigé Windows, commit `d5cb365`) |
| Existant (« avant ») | index **lexical JSON**, `lab.search(..., "json")` |
| Candidat | **FTS5, une table par rôle** (`fts5.py`, ADR-0001), plus les contrôles de l'ADR-0003 et la quarantaine de l'ADR-0004, à implémenter dans `migration_exercise/` |
| Cas propres | `migration_exercise/cases.jsonl`, SHA-256 `2ed61a27b32efc136652e1d81376c1fbc9b3c923ced31d84367de03f36d6f590`, 24 cas |
| Environnement | Windows 11, Python 3.12.10, SQLite 3.49.1 |

## Composant et risque ciblés

Un composant : **l'index de retrieval documentaire**. Ni l'agent, ni les outils
structurés, ni la génération ne sont migrés.

Un risque réel, mesuré : la **capacité**. Le coût d'une requête JSON est
linéaire : 297 ms à 7 000 documents contre 21 ms en FTS5
(`results/capacite-r1`). Un second risque est traité par la même migration :
**R-11**, un index qui sert des droits révoqués.

## Sous-ensemble et justification

Le sous-ensemble migré, c'est **tout le retrieval documentaire, sur les
7 documents actifs** : 4 rôles, un document restreint, un document public, une
révision remplacée hors service. C'est le corpus entier, parce qu'il est
petit. Le sous-ensemble porte donc sur la **fonction**, pas sur le volume :
les outils structurés et l'agent en sont exclus. Le volume est exercé à part,
par duplication synthétique jusqu'à 7 000 documents, pour la capacité
seulement.

## Cas propres, distincts du smoke test

`cases.jsonl` : 24 questions écrites en lisant les documents, **jamais** tirées
de `rag_eval/questions.jsonl`. Ni la calibration ni le split `test` ne servent
à mesurer la migration.

| Groupe | Nombre | Rôle dans la mesure |
|---|---|---|
| `vocabulaire` | 11 | questions qui reprennent les mots du document |
| `reformule` | 9 | mêmes intentions, sans le vocabulaire du document (leçon M4 : c'est là qu'un classement se départage) |
| `droits` | 2 | la réponse existe, mais dans un document interdit au rôle : `forbidden` ne doit jamais sortir |
| `sans_reponse` | 2 | aucune source ne répond |

Limite connue au gel : B2-13 et B2-14 (rôle `public`) n'ont qu'un document
visible et sont donc triviaux. Ils mesurent les droits, pas le classement.

## Scénarios de migration gelés

| ID | Scénario | Injection sur copie | Comportement exigé |
|---|---|---|---|
| M-REV-A | nouvelle révision, ancienne oubliée | `DOC-CONV-CURRENT-002` (révision 2, seuil 120 % au lieu de 110 %), qui remplace 001 ; 001 reste `active` | **export refusé** (règle « une seule révision active ») |
| M-REV-B | nouvelle révision correcte | idem, 001 passé en `superseded` | l'index construit **avant** est refusé au chargement ; après reconstruction, B2-01 renvoie 002 et jamais 001 |
| M-REVOC | révocation | `technicien` retiré de `DOC-STEAM-PRESS-001` | l'index d'avant est refusé ; après reconstruction, B2-03 ne renvoie plus STEAM pour `technicien`, et le renvoie encore pour `superviseur` ; **le retour arrière vers un index antérieur à la révocation est refusé** |
| M-QUAR | document altéré | une ligne ajoutée à `DOC-CHILL-TEMP-001` | ce document est mis en quarantaine, les 6 autres sont servis, une alerte est tracée ; B2-05 ne renvoie pas CHILL |
| M-PANNE | candidat indisponible, puis corrompu | index FTS5 supprimé, puis écrasé | refus explicite, bascule sur l'index JSON conservé, mode dégradé tracé |
| M-ROLLBACK | retour arrière nominal | — | JSON restauré par empreinte ; classement identique à « avant » sur les 24 cas |

## Format d'export

JSON UTF-8, **fins de ligne LF**, clés triées, `ensure_ascii=False`,
indentation 2. Par document : `document_id`, `title`, `revision`,
`effective_at`, `source_type`, `license`, `sensitivity`, `status`,
`supersedes_document_id`, `allowed_roles` (liste triée), `checksum_sha256`,
`text`. En tête : `schema_version`, `manifest_sha256`. Tout document dont le
checksum ne correspond pas va en **quarantaine** (liste séparée, avec le motif),
jamais dans l'export.

Pertes tolérées : l'échelle du score (BM25 contre entier lexical ; aucun seuil
ne dépend du score aujourd'hui). Pertes **non** tolérées : un champ de
métadonnées, un rôle, une révision.

## Seuils, gelés avant mesure

| Gate | Seuil | Type |
|---|---|---|
| Fuite | 0 document `forbidden` renvoyé ; 0 renvoi du document restreint sur les 11 sondes × 2 rôles | **bloquant** |
| Statistiques isolées | scores d'un rôle identiques avec et sans les documents qu'il ne voit pas | **bloquant** |
| Métadonnées | égalité champ par champ entre l'export et l'index, pour les 7 documents | **bloquant** |
| M-REV-A, M-REV-B, M-REVOC, M-QUAR | comportement exigé ci-dessus, 4/4 | **bloquant** |
| Retour arrière | M-ROLLBACK identique ; retour vers un index antérieur à une révocation refusé | **bloquant** |
| Qualité | hit@3 candidat ≥ hit@3 existant − 0,05 sur les 20 cas à réponse (au plus un cas perdu) | **majeur** |
| Qualité fine | hit@1 candidat ≥ hit@1 existant − 0,10 | majeur |
| Capacité | p50 candidat ≤ p50 existant à 700 documents et au-delà | majeur |
| Reprise | bascule sur le JSON en moins de 15 min (RTO) ; mesurée | majeur |

Protocole : la calibration (`RAG-CAL-*`) sert seulement à vérifier que rien ne
casse. Les seuils se lisent sur les 24 cas propres. Aucun réglage du candidat
après la première mesure sur les cas propres : un réglage ouvrirait une
révision du contrat.

## Prédictions, écrites avant mesure

| # | Prédiction | Raison |
|---|---|---|
| P1 | hit@3 : les deux backends ≥ 0,90 sur les 20 cas | 7 documents, 3 places |
| P2 | hit@1 du groupe `reformule` : FTS5 > lexical | BM25 pondère les termes rares ; le lexical compte les mots vides |
| P3 | les 4 cas `droits` et `sans_reponse` reçoivent des documents dans les deux backends | aucun des deux ne sait s'abstenir (brief 1) |
| P4 | 0 fuite dans les deux | le filtre de rôle précède le calcul |
| P5 | M-REVOC échoue avec le code actuel du banc | RES-07 : aucun contrôle de fraîcheur |
| P6 | la reconstruction complète après changement de manifeste prend moins de 1 s à 7 documents | brief 1 : 12 ms |

## RTO / RPO, budget

RTO index : 15 min. RPO : 0 (reconstruit depuis le manifeste). Budget : pas de
réseau, pas de dépendance, moins de 100 Mo de disque, moins de 5 min
d'exécution par campagne.

## Gates de sécurité non négociables

Aucune fuite, aucune permission élargie, aucune action réelle. Un retour
arrière ne rétablit jamais un droit retiré.

## Plan, opérations manuelles, rollback

Plan : `architecture/migration_plan.md`, étapes 1 à 4. Chaque commande lancée
à la main est comptée dans `execution_log.md`. Rollback : `active.json`
repointé par empreinte, sauf après une révocation.

## Reviewer et protocole de reproduction

Reviewer : **à désigner, une autre personne** (apprenant ou formateur).
L'auteur ne peut pas le remplacer. Protocole : cloner la version identifiée
dans `independent_review.md`, puis lancer les commandes de `execution_log.md`
depuis `work/M7` et comparer aux rapports de `results/`.

## Révisions du contrat

| Date | Changement | Motif | Avant ou après mesure |
|---|---|---|---|
| | | | |
