# Bilan du brief 1 présentiel — M6

Huit étapes, du 21/09/2026. Ce document confronte ce qui est produit à ce que le
brief demande, et rend la décision de fin de brief.

## 1. Les dix livrables

| Livrable attendu | Où | État |
|---|---|---|
| `docs/registre_outils.md` | 5 fiches, 5 écarts mesurés, 4 questions ouvertes | ✔ |
| schémas et adaptateurs des outils | `tools/` — contrats vérifiés par 35 sondes | ✔ |
| politique d'exécution | `agent/policy.yaml` (`m6-r3`) + `docs/politique_execution.md` | ✔ |
| jeu de scénarios gelé | `eval/scenarios_v3.jsonl` (29), manifeste `eval/GEL.md` | ✔ |
| harness et rapport d'évaluation | `eval/compare_systems.py`, `docs/rapport_evaluation.md` | ✔ |
| `docs/qualification_feedback.md` | 124 retours, seuils éprouvés, 6 questions ouvertes | ✔ |
| candidat et rapport de comparaison | `docs/candidat_retrieval.md` — deux candidats, 14 prédictions | ✔ |
| décision de promotion | §12 du même document — **promu le 21/09 par Nicolas** | ✔ |
| entrée M6 et passage de relais | `veille_diagops/journal.md` — 7 questions à M7 | ✔ |
| journal de bord | 8 entrées, `journal_bord.md` | ✔ |

## 2. Les critères de réussite, un par un

| Critère du brief | Preuve |
|---|---|
| aucun outil n'a d'effet externe | `tests/test_no_side_effects.py` + relecture : les deux seules ouvertures de fichier sont en lecture, aucun `subprocess`, aucun réseau |
| arguments et résultats sont validés | 9 sondes → 9 `ArgumentError` avant appel ; la traversée de chemin est arrêtée par le motif d'identifiant |
| **le budget est enforceable** | il ne l'était pas : 5 paramètres étaient chargés et jamais appliqués (§3 de `politique_execution.md`). Corrigés, et 6 tests échouent si l'un redevient décoratif |
| les métriques séparent choix d'outil et qualité finale | `compare_systems.py` mesure huit dimensions et décompose par type d'attente |
| le feedback est qualifié avant usage | 124 retours classés, 11 à risque écartés, `training_data_exported: false` |
| le candidat passe les gates ou reste non promu | `eval/gate_promotion.py` → **PASS** sur six contrôles |
| la veille produit une contrainte vérifiable **ou** justifie l'absence d'impact | elle produit une contrainte : le gate refuse une promotion si le feedback n'a pas été qualifié |
| la trace reconstitue la décision sans exposer les données | 29 étapes, 9 champs déclarés et **aucun autre**, 0 champ interdit, empreinte d'argument à 12 caractères |

## 3. Le chemin, en chiffres

| | Départ | Fin |
|---|---:|---:|
| jeu du starter (18) | 0,833 | **1,000** |
| jeu gelé v3 (29) | 0,724 | **0,966** |
| campagne adversariale (6) | 0,667 | **1,000** |
| appels d'outils interdits | 1 | **0** |
| Recall@1 du retrieval | 0,533 | **0,667** |
| silences sur questions hors domaine | 0 / 5 | **5 / 5** |
| documents rendus (banc retrieval) | 60 | **31** |
| tests | 45 | **64** |

## 4. Ce que ce brief a trouvé, et qui ne se voit pas dans les scores

Sept constats qui ont changé une décision :

1. **Le mode dégradé de `search_knowledge` n'existait pas.** Zéro résultat vide sur
   cinq questions hors domaine, et les intervalles de score se recouvraient —
   l'abstention ne pouvait reposer ni sur le vide, ni sur un seuil.
2. **Le filtrage de rôle était silencieux.** `SCN-014` échouait parce que
   l'information « un document pertinent existe, votre rôle ne l'autorise pas »
   n'existait nulle part. D'où `withheld`, et l'arbitrage du refus neutre.
3. **Cinq paramètres de politique ne bornaient rien** — chargés, stockés, jamais
   consultés. Dont `treat_tool_output_as_data`, sur lequel repose `INV-08`.
4. **∃ se démontre sur un sous-ensemble, ∀ ne s'y démontre pas.** Une récidive se
   prouve sur un échantillon, un total jamais. C'est cette distinction qui a
   révélé qu'un de mes propres scénarios était mal posé.
5. **92,7 % du lot de feedback est composé de textes répétés.** 64 retours
   actionnables recouvrent 12 sujets : compter des retours n'est pas compter des
   observations.
6. **25 % du lot actionnable décrit un système qui n'existe pas** — le feedback est
   daté, et le contrat de collecte ne demande pas de version.
7. **Un candidat peut corriger un composant sans que le système bouge.** Le
   retrieval rendait le bon document ; l'ancrage le rejetait. Il a fallu un second
   candidat pour libérer un gain déjà acquis.

Et deux erreurs de ma main, consignées parce qu'elles instruisent :

- **un jeu de scénarios écrit sans accents** mesure un autre système que celui
  qu'on croit tester (0,690 contre 0,724) ;
- **un contrôle que j'ai rendu inerte** : à `ANCRAGE_MINIMUM = 1`, l'ancrage ne
  rejette plus jamais rien — le défaut que ce dossier dénonce depuis l'étape 2,
  reproduit par moi trois étapes plus loin.

## 5. Ce qui reste ouvert

| Sujet | Où | Qui décide |
|---|---|---|
| reclassement des 16 retours datés (`a_investiguer`) | `qualification_feedback.md` §5 | **Nicolas** |
| troisième candidat : le corpus — « givre » n'est dans aucun document | `candidat_retrieval.md` §16 | brief 2 |
| rétention des données de feedback : 30 jours déclarés, rien ne purge | `veille_diagops/journal.md` | M7 |
| version du système absente du contrat de collecte | idem | M7 |
| texte consolidé du règlement, reporté depuis M5 | idem | M7 |
| convention des identifiants `EVT-…-X0..` (54 sur 520) | `registre_outils.md` §6 | formateur |
| l'ancrage redeviendra critique si le retrieval devient vectoriel | `candidat_retrieval.md` §15 | brief 2 |

## 6. Décision de fin de brief

**Le brief 1 présentiel est complet** : dix livrables sur dix, huit critères de
réussite tenus, gate de promotion au vert, et une décision de promotion prise par
un humain et datée.

La réserve qui accompagne le chiffre de 0,966 est écrite à l'étape 4 et n'a pas
changé : **les règles de l'agent ont été construites en regardant les échecs du jeu
gelé.** La campagne fournie — jamais consultée pendant le réglage — passe de 0,667
à 1,000, et c'est le seul signal externe disponible. Le contrôle réel est la
campagne d'un pair, au brief 2.
