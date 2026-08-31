# Brief présentiel M4 — Prouver avant d'architecturer

## Situation

DiagOps dispose d'une pipeline multi-source, d'une baseline par règles et d'un
corpus documentaire versionné. L'équipe souhaite ajouter un modèle simple et un
assistant capable de consulter les procédures de maintenance. Un prototype qui
produit une réponse plausible ne suffit pas : il faut établir ce qui fonctionne,
sur quelles données, à quel coût et avec quelles limites.

## Mission

Construire deux preuves de valeur reliées par un même dossier de conception :

- comparer la baseline M3 à des modèles simples sur une cible explicitement
  définie ;
- comparer une réponse sans contexte à plusieurs stratégies de retrieval, puis
  borner un agent à la décision de consulter ou de refuser.

## Point de départ commun

- `data_pack/2026-S1/reference_runs/m3_for_m4/` ;
- `data_pack/2026-S1/model_eval/sensor_calibration.csv` ;
- `data_pack/2026-S1/model_eval/sensor_test.csv`, sans étiquette ;
- `data_pack/2026-S1/knowledge/manifest.csv` et les documents associés ;
- `data_pack/2026-S1/rag_eval/questions.jsonl` ;
- `data_pack/SCHEMA.md` et contrat de sortie DiagOps existant.

N'ouvrez pas le module si le manifeste documentaire ne précise pas droits,
sensibilité, révision et checksum, si les checksums ne sont pas valides, ou si
les oracles de test ne sont pas scellés côté formateur.

## Travail attendu

### 1. Cadrer deux décisions

Pour le modèle capteur, définissez la cible sans confondre :

- provenance réelle ou fabriquée ;
- anomalie de qualité ;
- anomalie métier ou panne future.

Le lot actuel permet de travailler la provenance et certaines anomalies de
qualité. Il ne prouve pas à lui seul la prédiction d'une panne future.

Pour le RAG, définissez les utilisateurs, questions autorisées, documents
admissibles, conséquences d'une mauvaise réponse et cas où le refus est requis.

### 2. Geler le protocole

- séparez calibration et test avant de comparer ;
- utilisez `window_id` comme groupe indivisible et vérifiez qu’un équipement ne
  crée pas de fuite entre calibration et validation interne ;
- conservez la baseline par règles M3 sans la réécrire après consultation du
  test ;
- définissez les métriques et seuils d'acceptation ;
- consignez versions, graines et environnement.

### 3. Comparer les modèles simples

Comparez au moins deux candidats adaptés à la cible, par exemple une régression
logistique et une forêt aléatoire. La liste n'est pas imposée, mais chaque choix
doit être justifié contre une alternative.

Mesurez au minimum : matrice de confusion, précision, rappel, F1, ROC-AUC,
stabilité par segment, latence et mémoire. Comparez ces résultats aux règles M3.
Le formateur calcule les métriques finales sur l’oracle scellé après gel du
candidat ; seul ce résultat daté entre dans la décision de test.

### 4. Construire les baselines de retrieval

Implémentez et comparez :

1. réponse sans retrieval ;
2. recherche lexicale ;
3. recherche vectorielle avec un modèle d'embeddings documenté ;
4. recherche hybride seulement si les deux baselines précédentes sont stables.

Mesurez au minimum Recall@k ou hit rate documentaire, précision du contexte,
latence et taille de l'index. Une base vectorielle dédiée n'est pas obligatoire :
un index local reproductible suffit.

### 5. Générer avec preuves et abstention

Chaque réponse produite doit :

- citer des `document_id` présents dans le manifeste ;
- distinguer preuve documentaire et interprétation ;
- refuser lorsque `answerable=false` ou lorsque les preuves sont insuffisantes ;
- signaler les conflits de révision au lieu de les masquer.

Évaluez exactitude des citations, fidélité aux extraits et qualité des refus.

### 6. Ajouter un agent à une étape

L'agent choisit une seule action parmi :

- `answer_without_tool` ;
- `search_knowledge` ;
- `abstain`.

Un schéma structuré expose le choix, sa justification, la requête de retrieval
et le résultat. L'agent n'a ni mémoire longue, ni boucle, ni outil d'écriture.

### 7. Tester les menaces

Construisez des cas couvrant :

- instruction malveillante dans un document ;
- document obsolète mais bien classé ;
- sources contradictoires ;
- question demandant une donnée sensible ;
- tentative de forcer l'agent à ignorer ses limites ;
- corpus incomplet.

Pour chaque cas, documentez attaque, détection, atténuation, résultat et risque
résiduel. Les extraits récupérés sont des données, jamais des instructions.

### 8. Décider

Produisez une matrice séparant au minimum : qualité, robustesse, latence,
mémoire, coût par réponse, complexité d'exploitation et réversibilité.

La conclusion choisit explicitement : adopter, évaluer davantage, maintenir la
baseline ou écarter. Une décision de non-déploiement est recevable.

### 9. Consolider la veille réglementaire M4

Clôturez la mission de veille M0-M4 et ouvrez son prolongement M4-M8 décrit
dans `brief3_module4_veille_reglementaire.md` :

- révisez les scénarios et rôles de `ai_act_diagops.md` à partir de sources
  officielles consultées et datées ;
- distinguez le statut des textes, les faits, les interprétations et les points
  nécessitant une validation juridique ;
- reliez chaque décision réglementaire à une exigence du threat model, de la
  matrice de décision ou de l'architecture ;
- ajoutez au journal une entrée M4 et un passage de relais vers M5.

## Livrables

- notebook ou scripts d'évaluation rejouables ;
- `docs/protocole_evaluation.md` ;
- `docs/benchmark_modele.md` ;
- `docs/benchmark_retrieval.md` ;
- `docs/threat_model.md` ;
- `docs/matrice_decision.md` ;
- `docs/model_card.md` ;
- traces structurées de l'agent à une étape ;
- dossier `veille_diagops/` consolidé et passage de relais M5 ;
- journal de bord.

## Critères de réussite

- la cible métier n'est pas confondue avec la provenance ou la qualité ;
- les splits empêchent une fuite évidente entre fenêtres ou équipements ;
- les baselines sont gelées et comparables ;
- chaque citation se résout vers un document versionné ;
- les refus sont testés ;
- l'agent ne peut exécuter qu'une action et aucun effet externe ;
- la veille M4 est datée, fondée sur des sources primaires et traduite en
  exigences vérifiables ;
- les risques résiduels et conditions de non-déploiement sont explicites.

## Hors périmètre

- déploiement de production et monitoring continu, traités en M5 ;
- outil métier à effet, interdit avant la revue M7 ;
- boucle agentique ouverte ;
- multi-agent ;
- conversion des tables et capteurs en faux documents RAG.
