# Contrat de versions

> État au **07/09/2026** — ouverture du brief 1. Référence de départ : `diagops-m4-reference-r1`,
> périmètre déclaré `pedagogical_preproduction_only`.

## Principe

Un run de production doit permettre de retrouver **chaque unité** qui a contribué à sa réponse.
Une unité qui n'a pas de version identifiable est une unité qui rend le système non attribuable :
elle est signalée ici comme telle, pas passée sous silence.

Convention de nommage reprise de la référence M4 : `<famille>-<12 premiers hex du sha256>`.

## Les unités

| # | Unité | Version | Checksum ou digest | Source | Compatible avec | Procédure de retour |
|---:|---|---|---|---|---|---|
| 1 | **Code** | `À FIXER` — commit d'ouverture M5 | commit git (40 hex) | dépôt `lebnicolas/diagops`, `projets/diagops-m5/` | toute release M5 | `git checkout <commit>` puis reconstruction de l'index |
| 2 | **Configuration** | `gates-3f30ed1382d0` | `3f30ed1382d0dcf2…` (`configs/gates.json`) | dépôt, versionnée avec le code | seuils calés sur 7 documents actifs | restauration du fichier au commit correspondant |
| 3 | **Modèle** | `diagops-grounded-reference-v1` | — *(aucun poids distribué)* | référence M4 | contrat de réponse `84945f32dd21…` | remplacement du manifeste de release |
| 4 | **Corpus** | `knowledge-3b3dfb356eee` | `3b3dfb356eee6543…` | `data_pack/2026-S1/knowledge/` | 7 documents `active` sur 8 déclarés | jeu de données figé, non modifiable côté apprenant |
| 5 | **Manifeste** | identique au corpus | `3b3dfb356eee6543…` (`manifest.csv`) | `data_pack/2026-S1/knowledge/manifest.csv` | schéma à 8 champs obligatoires | idem |
| 6 | **Stratégie de chunking** | `document-entier-r1`, empreinte `build-0c139fd0de6a` | couverte depuis le 07/09 par `build_version` | stratégie + regex `TOKEN` + checksum de `pipelines/build_index.py` | index lexical seulement | `git checkout` du pipeline |
| 7 | **Modèle d'embeddings** | **sans objet** | — | retrieval lexical, aucun vecteur | — | — |
| 8 | **Index** | `lexical-dfb8faf0c9b4` | `a47a0d5a00d2557d…` (fichier `index.json`) | reconstruit par `build_index.py` | corpus `knowledge-3b3dfb356eee` | reconstruction hors chemin actif, puis `rollback_release.py` |
| 9 | **Prompts** | `prompt-5f66e3c2e1d2` | `5f66e3c2e1d2061e…` | `reference_runs/m4_for_m5/prompts/grounded_answer.txt` | contrat de réponse | restauration du fichier de référence |
| 10 | **Jeu d'évaluation** | `diagops-rag-calibration-2026-S1-r1` | `6f47a6b70539fc9e…` (métriques), `2f26ccd80a6ec7af…` (questions) | `data_pack/2026-S1/` | oracle de test scellé côté formateur | jeu figé, non modifiable |

### Unités d'exécution — à relever avant toute promotion

Le `README` du starter l'impose : les tags servent à initialiser le laboratoire, **la version promue
doit être immuable**. Un tag est mutable, un digest ne l'est pas.

| Unité | Tag déclaré | Digest résolu (relevé le 07/09) |
|---|---|---|
| Image de base API | `python:3.12.11-slim-bookworm` | `sha256:519591d6871b7bc437060736b9f7456b8731f1499a57e22e6c285135ae657bf7` |
| Image Prometheus | `prom/prometheus:v3.5.0` | `sha256:63805ebb8d2b3920190daf1cb14a60871b16fd38bed42b857a3182bc621f4996` |

Les trois images applicatives (`indexer`, `gate`, `api`) sont construites depuis le même
Dockerfile et pèsent **230 Mo** chacune. C'est la même image à trois rôles : la séparation des
responsabilités est faite par la commande et les volumes, pas par trois artefacts distincts —
un seul digest à suivre plutôt que trois, et un `.dockerignore` qui tient le venv local dehors.

## Reproductibilité vérifiée

L'index reconstruit localement le 07/09 porte `lexical-dfb8faf0c9b4` — **la même version que la
référence M4 distribuée**. Le corpus, le manifeste et le pipeline de construction produisent donc
un résultat identique à celui du formateur : la chaîne est reproductible sur ce point.

## Ce qui déclenche une nouvelle version

| Événement | Unités qui changent | Unités qui ne bougent pas |
|---|---|---|
| Commit de code | code | corpus, index, prompts, évaluation |
| Nouvelle révision d'un document | corpus, manifeste, **index** | code, prompts, évaluation |
| Passage d'un document en `inactive` | corpus, manifeste, **index** | code, prompts |
| Modification d'un seuil de gate | configuration | tout le reste |
| Réécriture du prompt | prompts | corpus, index, code |
| Publication de la période `2026-S2` | corpus, manifeste, index, et **potentiellement l'évaluation** | code, prompts |

Une reconstruction d'index à corpus inchangé **ne produit pas** de nouvelle `index_version` :
l'empreinte est déterministe. C'est voulu — elle identifie un contenu, pas une exécution.

## Deux trous d'attribution constatés à l'ouverture — et comblés le 07/09

> [!success] Correctifs appliqués
> `build_version` couvre désormais la stratégie de construction (unité 6), et l'évaluation est
> branchée sur le candidat via `pipelines/measure_release.py`. Le rapport de gate porte la
> provenance de chaque contrôle et refuse une mesure faite sur un autre index. Les deux constats
> ci-dessous sont conservés : ils décrivent l'état livré du starter, qui est ce qui se défend.

> [!danger] L'empreinte d'index ne couvre pas la façon dont l'index est construit
> `index_version` est calculée sur `document_id:revision:checksum` des documents source, triés.
> Le traitement appliqué n'y entre pas. Vérifié le 07/09 en changeant la seule regex de
> tokenisation : le nombre total de tokens passe de **780 à 446**, et `index_version` reste
> **`lexical-dfb8faf0c9b4`**. Deux index mesurablement différents, une seule version.
>
> Conséquence directe sur ce contrat : les unités 6 et 8 ne peuvent pas être identifiées par la
> même empreinte. La stratégie de chunking n'est traçable que par le **checksum du pipeline**
> (unité 6), et le contrat n'est honoré que si les deux sont relevées ensemble.

> [!danger] Le gate de livraison ne mesure pas le candidat
> Sur les quatre contrôles de `evaluate_release.py`, **un seul lit l'index évalué**
> (`document_count`). Les trois autres lisent `metrics_calibration.json`, un fichier figé du
> data pack. Vérifié le 07/09 : un index conservant ses 7 documents mais dont tous les checksums
> et tous les `token_count` ont été mis à zéro obtient `status: passed`, quatre checks verts.
>
> `promote_release.py` refuse bien un gate non `passed`, mais **ne vérifie pas que le rapport de
> gate porte sur le candidat promu** : n'importe quel rapport `passed` autorise n'importe quel
> manifeste. Tant que l'évaluation n'est pas branchée sur le candidat, le contrat de versions
> décrit fidèlement ce qui est déployé — sans qu'aucun contrôle n'empêche de déployer autre chose.

## Une métrique du gate reste non mesurable ici

`correct_abstention_rate` ne se déduit pas du retrieval. Mesuré le 07/09 : les deux questions sans
réponse ramènent des documents au score non nul, et **aucun seuil ne les sépare** des questions
répondables — `RAG-CAL-008` (répondable) score 0,33 quand `RAG-CAL-012` (sans réponse) score 0,36.
S'abstenir est une décision de la couche de génération, absente de ce périmètre.

Elle est donc **héritée** de la référence M4 et tracée comme telle
(`"correct_abstention_rate": "inherited:metrics_calibration.json"`). Une métrique héritée ne dit
rien du candidat : le rapport de gate l'affiche, au lieu de la faire passer pour une mesure.

Métrique de substitution conservée à titre d'observation : `retrieval_only_abstention_rate`, à
**0,0** — le retrieval seul ne s'abstient jamais.

## À faire pour clore le bloc 1

- [x] brancher les checks du gate sur le candidat réellement évalué — `measure_release.py` ;
- [x] refuser une mesure produite sur un autre index — check `metrics_match_index` ;
- [x] tracer la provenance de chaque contrôle du gate ;
- [x] rendre la stratégie de construction traçable — `build_version` ;
- [ ] fixer `code_version` au commit d'ouverture M5 ;
- [x] relever les deux digests d'images — faits le 07/09, voir le tableau ci-dessus ;
- [ ] les figer dans `configs/release.json` au moment de la première promotion ;
- [ ] vérifier à la promotion que le rapport de gate porte sur *ce* manifeste candidat *(bloc 4)* ;
- [ ] mesurer `correct_abstention_rate` pour de bon, si une couche de génération est introduite ;
- [x] unité 7 — **reste « sans objet »** : le module demande de rendre le retrieval opérable, pas
      de l'améliorer. Introduire des embeddings ajouterait une dépendance à versionner et
      conteneuriser, et surtout ferait perdre la comparabilité avec `lexical-dfb8faf0c9b4` au
      moment où le module exige de savoir y revenir. Le hit@3 est déjà à 1,00 sur 7 documents.
      À réexaminer si `2026-S2` élargit nettement le corpus.
