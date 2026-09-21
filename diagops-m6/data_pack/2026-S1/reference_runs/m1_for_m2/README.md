# Référence de continuité M1 → M2

Ce dossier fournit à tous les apprenants le même état de départ pour le brief
présentiel M2. Il est publié dans le data pack commun du dépôt S04.

Il ne remplace ni l'évaluation ni la production personnelle de M1. Si vous
disposez de vos propres résultats, vous pouvez les comparer à cette référence,
mais les analyses demandées en M2 s'appuient sur les fichiers de ce dossier.

## Contenu

- `reference_run/validation_reference.jsonl` : 80 exemples de validation déjà
  consultés en M1 ;
- `reference_run/predictions_baseline.jsonl` et
  `predictions_lora.jsonl` : sorties brutes de référence ;
- `reference_run/metrics_baseline.json` et `metrics_lora.json` : métriques ;
- `reference_run/run_manifest.json` : configuration et environnement du run ;
- `analyses/matrice_erreurs_m1.csv` : table joignable avec les données M2 ;
- `analyses/synthese_chiffree.json` et `synthese_erreurs_m1.md` : lecture
  initiale à vérifier et prolonger ;
- `decision_m1.md` : décision de référence ;
- `checksums.sha256` : intégrité du dossier.

## Limites

Le run LoRA a été exécuté sur Apple MPS avec un type effectif `float32`. Il ne
constitue pas le pilote CUDA commun prévu par le protocole. La comparaison de
latence est en outre fragilisée par la non-conformité structurelle des sorties
de la baseline. Ces résultats sont un historique d'enquête, pas un étalon de
performance matérielle ni un nouveau jeu de test inédit.

Le dossier ne contient aucun poids, checkpoint, code corrigé de M1 ou solution
du brief M2.
