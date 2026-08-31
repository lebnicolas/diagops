# Ressources — Module 4

## Priorité des sources

Utiliser d'abord les documentations primaires des outils retenus, les model
cards des modèles, les textes réglementaires officiels et les publications de
référence. Toute ressource doit être datée et reliée à une décision du module.

## Évaluation

- état M3 figé dans `data_pack/2026-S1/reference_runs/m3_for_m4/` ;
- calibration et test groupés dans `data_pack/2026-S1/model_eval/` ;
- scikit-learn — métriques de classification, courbes ROC et calibration ;
- documentation des splits groupés et temporels ;
- BEIR — principes d'évaluation du retrieval ;
- RAGAS ou DeepEval — uniquement après avoir compris et contrôlé les métriques ;
- MLflow — suivi des expériences, facultatif en M4 et requis en M5.

## Retrieval et corpus

- corpus versionné et manifeste dans `data_pack/2026-S1/knowledge/` ;
- questions de calibration et de test dans `data_pack/2026-S1/rag_eval/` ;
- BM25 ou équivalent lexical comme baseline ;
- Sentence Transformers ou modèle d'embeddings documenté ;
- FAISS, SQLite vectoriel ou autre index local reproductible ;
- documentation du format source et du manifeste DiagOps.

Le choix d'une base vectorielle distribuée n'est pas un objectif M4.

## Sécurité

- OWASP Top 10 for LLM Applications — prompt injection et excessive agency ;
- MITRE ATLAS — menaces sur les systèmes d'IA ;
- NIST AI RMF et NIST AI 100-2 — gestion des risques et adversarial ML ;
- documentation officielle de l'AI Act et autorités de protection des données.

## Veille réglementaire M4-M8

- brief longitudinal `brief3_module4_veille_reglementaire.md` ;
- dossier `veille_diagops/` ouvert en M0 ;
- EUR-Lex, Commission européenne, AI Act Service Desk et CNIL comme sources de
  départ, à vérifier à la date de chaque checkpoint ;
- sources officielles du secteur et du territoire du cas lorsque celui-ci
  dépasse le périmètre de ces sources de départ.

## Livrables de référence

- model card du candidat retenu ;
- manifeste documentaire avec licence, sensibilité et checksum ;
- protocole d'évaluation gelé ;
- threat model ;
- matrice de décision.

## À éviter

- évaluer uniquement avec un juge LLM ;
- utiliser le test pour régler les prompts ou les seuils ;
- présenter une similarité vectorielle comme une preuve de vérité ;
- laisser le modèle interpréter un document comme une instruction système ;
- indexer les tables structurées sans justifier la perte de leur contrat.

## Approfondissement de 20 h

- grille commune de reproduction ;
- lot caché fermé jusqu'au gel du candidat ;
- modèle de rapport `reproduit / écart / bloqué / non testé` ;
- conservation des résultats avant et après remédiation.
