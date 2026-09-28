# Journal de migration — brief 2, phase 1

Contrat gelé au commit `893ccfa` (`contract.md`, `cases.jsonl` SHA-256
`2ed61a27…`). Les deux scripts de mesure vérifient cette empreinte et refusent
de mesurer si les cas ont changé. Environnement : Windows 11, Python 3.12.10,
SQLite 3.49.1, aucune dépendance.

Commandes, depuis `work/M7` :

```bash
python -m unittest discover -s tests -v                                   # 21 tests
python scripts/migration_run.py --output results/migration-r1             # cas gelés + 6 scénarios + gates
python scripts/migration_capacity.py --output results/migration-capacite-r1   # gate de capacité, contrôles compris
```

| Essai/date | Versions/hashes | Commande exacte | Opération manuelle | Durée | Qualité/écart | Droits | Perte | Rapport | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| avant · 28/09 | lexical JSON, export LF du manifeste `3b3dfb35…` | `migration_run.py` (partie « avant ») | 0 | 10 ms / 24 cas | hit@1 0,85 · hit@3 0,85 · MRR 0,85 | 0 renvoi interdit | — | `migration-r1` | référence |
| candidat · 28/09 | FTS5 par rôle, `migration.py`, `manifest_sha256` inscrit | `migration_run.py` | 1 (export + construction + 2 activations) | migration 19 ms ; 39 ms / 24 cas | hit@1 0,85 · **hit@3 0,95** · MRR 0,90 | 0 fuite sur 22 sondes ; statistiques isolées 4/4 rôles ; métadonnées identiques 7/7 | échelle du score (tolérée) | `migration-r1` | gates passés |
| panne · 28/09 | idem | M-PANNE : index supprimé, puis corrompu, puis repli détruit | 0 | bascule en 1,5 ms | réponses du repli JSON | inchangés | aucune | `migration-r1` | dégradé tracé, puis refus |
| révision · 28/09 | + `DOC-CONV-CURRENT-002` | M-REV-A, M-REV-B | 1 (reconstruction) | reconstruction 21 ms | 002 servie, 001 jamais | — | aucune | `migration-r1` | export refusé si 001 reste active ; index d'avant refusé |
| révocation · 28/09 | STEAM retiré à `technicien` | M-REVOC | 2 (reconstruction ; tentative de retour arrière) | reconstruction 16 ms | — | technicien : STEAM retiré ; superviseur : conservé | aucune | `migration-r1` | **retour arrière vers l'index d'avant refusé** : « rétablirait 1 droit retiré » |
| quarantaine · 28/09 | CHILL altéré | M-QUAR | 0 | — | B2-05 sans CHILL | — | CHILL indisponible jusqu'à correction | `migration-r1` | 6 documents servis, alerte tracée |
| rollback · 28/09 | JSON par empreinte | M-ROLLBACK | 1 | 29 ms (activation + 24 requêtes) | identique à « avant » sur 24 cas | — | aucune | `migration-r1` | conforme |
| capacité · 28/09 | ×1, ×100, ×1000 | `migration_capacity.py` | 0 | voir ci-dessous | — | — | — | `migration-capacite-r1` | gate passé ; **dette** sur l'empreinte par requête |

Opérations manuelles comptées sur la campagne : **5**. Trois reconstructions ou
activations, et deux retours arrière (dont un refusé). La reconstruction après
un changement de manifeste n'est **pas déclenchée automatiquement** : c'est
une opération humaine, et le service documentaire reste en refus entre les
deux. L'ADR-0003 prévoyait un déclenchement par le changement ; il n'est pas
implémenté (dette D-2).

Coût et énergie : **non mesurés**. Aucun composant n'est facturé et aucune
mesure physique n'a été faite.

## Comparaison avant / après

### Qualité, sur les 24 cas gelés

| Mesure | Avant (lexical) | Candidat (FTS5) | Seuil gelé | Lecture |
|---|---|---|---|---|
| hit@3 (20 cas à réponse) | 0,85 | **0,95** | ≥ 0,80 | gain : B2-02 et B2-05 rattrapés |
| hit@1 | 0,85 | 0,85 | ≥ 0,75 | égal |
| MRR | 0,85 | 0,90 | — | gain |
| hit@1 `vocabulaire` (11) | 0,909 | **1,000** | — | gain |
| hit@1 `reformule` (9) | **0,778** | 0,667 | — | **perte** : B2-12 |
| hit@3 `reformule` | 0,778 | 0,889 | — | gain |
| cas sans réponse avec résultats | 4/4 | 4/4 | — | aucun des deux ne s'abstient |
| documents interdits renvoyés | 0 | 0 | 0 | — |

Les cas qui départagent :

- **B2-05** « Au-delà de quelle température un groupe froid est-il classé
  urgent ? » : le lexical ne trouve pas CHILL dans son top 3, alors que la
  question reprend ses mots. Il ne pondère pas les termes, donc « de », « un »,
  « est » et « il » comptent autant que « température ». FTS5 le met premier ;
- **B2-02** (reformulée) : absent du top 3 lexical, 2e en FTS5 ;
- **B2-12** (reformulée) : 1er en lexical, 2e en FTS5, derrière le contrat de
  réponse. C'est la perte de hit@1 sur les reformulations ;
- **B2-16** (auditeur, reformulée) : raté par les deux. La question ne partage
  aucun terme discriminant avec le document d'accès. Ni l'un ni l'autre ne
  comprend « contrôler le fonctionnement de l'outil » comme « traces et
  métadonnées ».

### Ressources et latence

| Mesure | Avant | Candidat | Lecture |
|---|---|---|---|
| p50 par requête, 7 docs | 0,35 ms | 1,67 ms servi (0,65 nu) | **régression acceptable** : négligeable dans les deux cas |
| p50, 700 docs | 26,4 ms | 6,3 ms servi (2,1 nu) | gain ×4 |
| p50, 7 000 docs | 273 ms | **52,8 ms** servi (14,6 nu) | gain ×5 ; gate passé |
| dont empreinte de l'index à chaque requête | — | 36,1 ms sur 52,8 à 7 000 docs | **dette** (D-1) |
| taille, 7 docs | export 9,5 Ko | index 184 Ko | ×19, sans enjeu à cette taille |
| taille, 7 000 docs | export 10 Mo | index 41 Mo | ×4 |
| construction + activation, 7 000 docs | — | 10,9 s | sous le RTO de 15 min |

### Sécurité, observabilité, rollback

| Axe | Avant | Candidat |
|---|---|---|
| Droits avant classement | oui (score sans statistiques) | oui, statistiques comprises (index par rôle), 4/4 rôles vérifiés |
| Révocation | **non appliquée** : le code actuel du banc sert encore STEAM à un technicien après révocation (P5 vérifiée) | index périmé refusé ; après reconstruction, droit retiré |
| Deux révisions actives | acceptées | export refusé |
| Document altéré | tout le corpus refusé | quarantaine au document |
| Retour arrière | par empreinte | par empreinte, **et refusé s'il rétablit un droit retiré** |
| Observabilité | aucune | `events.jsonl` : activation, réponse (mode, rôle, empreinte de question, nombre), refus, quarantaine ; aucune question en clair ; séquence M-PANNE cohérente (nominal, dégradé, dégradé, refus) |

## Classement des écarts

| Écart | Catégorie | Motif |
|---|---|---|
| hit@1 `reformule` 0,778 → 0,667 (B2-12) | **régression acceptable** | hit@3 et MRR progressent ; le cas perdu reste 2e |
| latence ×5 à 7 documents | régression acceptable | 1,7 ms |
| D-1 : l'empreinte de l'index est recalculée à chaque requête, et son coût croît avec l'index (68 % du temps à 7 000 docs) | **dette reportée** | vérifier à l'activation et sur changement de taille ou de date du fichier ; mais cela affaiblit la détection d'une corruption entre deux requêtes, à trancher en revue |
| D-2 : la reconstruction après changement de manifeste est manuelle ; le service documentaire est en refus entre les deux | **dette reportée** | un déclencheur sur changement de manifeste ; RTO tenu tant qu'un humain est d'astreinte |
| D-3 : aucun backend ne s'abstient (4/4 cas sans réponse ou interdits reçoivent des documents) | dette reportée, hors migration | R-04, M8 |
| B2-16 raté par les deux | dette reportée, hors migration | limite du lexical, que les embeddings pourraient lever (ADR-0005, M8) |
| aucun blocage | — | les 5 gates bloquants passent |

## Prédictions, confrontées

| # | Prédiction | Résultat | Tenue |
|---|---|---|---|
| P1 | hit@3 ≥ 0,90 pour les deux | lexical 0,85, FTS5 0,95 | **non** : le lexical rate B2-02, B2-05 et B2-16 |
| P2 | FTS5 > lexical en hit@1 sur les reformulations | 0,667 contre 0,778 | **non** : BM25 fait mieux en top 3, pas en top 1 |
| P3 | les 4 cas droits et sans réponse reçoivent des documents | 4/4 dans les deux | oui |
| P4 | 0 fuite | 0 | oui |
| P5 | la révocation échoue avec le code actuel du banc | STEAM encore servi | oui |
| P6 | reconstruction sous 1 s à 7 documents | 21 et 16 ms | oui |

Deux prédictions sur six sont fausses, et les deux portent sur la qualité.
Aucune ne change la décision : le seuil gelé est tenu. Elles changent
l'argument. FTS5 n'est pas « meilleur sur les reformulations » : il est
meilleur pour mettre le bon document **dans** les trois premiers, parce qu'il
cesse de compter les mots vides.

## Écart au protocole

Le contrat gelait un gate de capacité (« p50 candidat ≤ p50 existant à
700 documents et au-delà »). `migration_run.py` ne l'implémentait pas : c'est
un oubli. Il a été mesuré après coup par `migration_capacity.py`, avec le
seuil inchangé et sur les cas gelés. L'oubli est consigné dans les révisions
du contrat.
