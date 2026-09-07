# État de continuité M3 vers M4

Ce dossier fournit une baseline commune, figée avant l’ouverture du M4. Il
permet de commencer le module sans dépendre de l’achèvement d’une production
personnelle M3.

## Contenu

- `baseline_rules.py` : règles M3 figées, sans apprentissage ;
- `baseline_predictions_calibration.csv` : prédictions sur le lot de
  calibration M4 ;
- `baseline_metrics_calibration.json` : métriques observées avant tout modèle ;
- `regles_m3.md` : périmètre et limites des règles ;
- `decision_m3.md` : décision de transmission ;
- `checksums.sha256` : intégrité interne du dossier.

La baseline détecte uniquement des violations visibles du contrat capteur. Elle
ne constitue ni un détecteur complet de fabrication, ni un modèle d’anomalie
métier. Elle doit rester inchangée après consultation du test M4.

## Rejouer la référence

Depuis la racine du dépôt :

```bash
python data_pack/2026-S1/reference_runs/m3_for_m4/baseline_rules.py \
  --input data_pack/2026-S1/model_eval/sensor_calibration.csv \
  --predictions /tmp/m4_baseline_predictions.csv \
  --metrics /tmp/m4_baseline_metrics.json
```
