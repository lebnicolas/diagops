# Starter M1 — DiagOps LoRA

Ce kit fournit le code repetitif du module. Il ne choisit ni l'hypothese, ni la
variation, ni la conclusion a votre place.

## Objectifs

Le kit permet de :

- creer un split train/validation reproductible depuis les 400 annotations ;
- relever l'environnement d'execution ;
- entrainer `Qwen/Qwen3-0.6B` avec LoRA ;
- evaluer une baseline ou un adaptateur avec les memes metriques ;
- exporter les predictions et les preuves ;
- charger l'adaptateur derriere une interface commune.

## Environnement

Le depot peut etre prepare depuis macOS, Linux ou Windows. Les entrainements de
reference s'executent sur l'environnement GPU commun.

Le modele est epingle sur la revision Hugging Face suivante :

```text
c1899de289a04d12100db370d81485cdf75e47ca
```

Ne remplacez pas cette revision par `main` : elle garantit que tous les runs
utilisent les memes poids, le meme tokenizer et la meme configuration.

## Installation

Depuis ce dossier :

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.lock
```

Sous PowerShell :

```powershell
.venv\Scripts\Activate.ps1
```

Pour le parcours guide :

```bash
python -m jupyter lab notebooks/m1_lora_diagops.ipynb
```

## Preparation

```bash
python -m src.environment --output work/environment.json

python -m src.dataset \
  --input ../data_pack/2026-S1/annotations/diagops_train.jsonl \
  --output-dir work/splits \
  --seed 42 \
  --validation-size 80
```

La commande doit produire :

```text
work/splits/train.jsonl       # 320 lignes
work/splits/validation.jsonl  # 80 lignes
work/splits/split_manifest.json
```

## Baseline sur la validation

La revision est deja gelee dans `configs/baseline.yaml` :

```bash
python -m src.evaluate \
  --config configs/baseline.yaml \
  --data work/splits/validation.jsonl \
  --output-dir work/baseline_validation
```

## Run LoRA de reference

```bash
python -m src.train \
  --config configs/lora_reference.yaml \
  --train-data work/splits/train.jsonl \
  --output-dir work/runs/lora_reference

python -m src.evaluate \
  --config configs/baseline.yaml \
  --adapter work/runs/lora_reference/adapter \
  --data work/splits/validation.jsonl \
  --output-dir work/lora_reference_validation
```

Copiez `configs/lora_reference.yaml` pour chaque variation. Une seule variable
doit changer entre la reference et une variation.

## Test final

Le test final ne doit etre execute que dans le Brief 2, apres gel du candidat :

```bash
python -m src.evaluate \
  --config configs/baseline.yaml \
  --data ../data_pack/2026-S1/annotations/diagops_test.jsonl \
  --output-dir work/final/baseline \
  --allow-test

python -m src.evaluate \
  --config configs/baseline.yaml \
  --adapter work/model_final \
  --data ../data_pack/2026-S1/annotations/diagops_test.jsonl \
  --output-dir work/final/candidate \
  --allow-test
```

Sans `--allow-test`, le programme refuse un fichier dont le nom contient
`test`.

## Verification locale sans GPU

Les tests du starter ne chargent pas le modele :

```bash
pytest -q
```

L'analyse des fichiers `metrics.json` et `predictions.jsonl` peut etre realisee
sur n'importe quel poste.

## Structure des preuves

```text
work/
├── environment.json
├── splits/
├── baseline_validation/
├── runs/
│   ├── lora_reference/
│   ├── variation_1/
│   └── variation_2/
├── final/
└── evidence/
    ├── protocol_m1.md
    ├── error_analysis.md
    ├── peer_review.md
    └── model_card.md
```

## Niveau d'assistance

- **Guide** : utilisez le notebook et les commandes ci-dessus.
- **Standard** : utilisez directement les scripts et configurations.
- **Approfondissement** : ajoutez une mesure, une quantification ou un backend
  local, sans remplacer les preuves obligatoires.

## Limites

- Ce starter ne repare pas une sortie JSON avant de calculer le taux de JSON
  brut parseable.
- Le score textuel est lexical. Il ne remplace pas une revue qualitative.
- Une erreur de donnees ou d'annotation doit etre documentee, pas corrigee
  silencieusement.
