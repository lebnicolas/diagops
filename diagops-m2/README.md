# Module 2 — Gouverner, auditer et préparer les données

Ce dossier contient les supports propres à M2. Il fait partie du dépôt S04 :
aucun ZIP ni kit séparé n'est à préparer. Les données restent centralisées
dans `../data_pack/` et le travail est initialisé dans `../work/M2/`.

## Contenu

- `brief1_module2.md` : brief présentiel moderne, 14 h ;
- `brief1_module2_online.md` : brief online aligné sur le programme Atlas, 6 h ;
- `../data_pack/2026-S1/` : données ouvertes de M0 à M2 ;
- `../data_pack/2026-S1/reference_runs/m1_for_m2/` : état de référence commun
  permettant de commencer M2 sans dépendre de l'achèvement des productions M1 ;
- `starter/` : exemples de chargement et de pipeline, notebook, contrôles
  simples, tests et modèles de rapport ;
- `RESOURCES.md` : ressources documentaires ;
- `module_2_synthese.md` et `acquis_m2.md` : cadrage et état cible du module.

Les rapports, annotations et contrats déjà remis en M0 et M1 ne sont pas
dupliqués. Ils restent utiles pour le brief présentiel lorsqu'ils sont
disponibles, mais la référence de continuité fournit les résultats M1
indispensables à l'enquête.

## Organisation

Les cinq apprenants travaillent sur les mêmes briefs et les mêmes ressources,
chacun dans son propre environnement. Les échanges et revues collectives sont
possibles, sans constitution de groupes ni sujet personnalisé.

## Initialisation du travail

Depuis la racine du dépôt privé, sur `main` :

```bash
python tools/init_module.py M2
cd work/M2
```

Le script refuse d'écraser un travail déjà présent.

## Vérification du starter

Depuis `work/M2/` après initialisation, ou depuis `M2/starter/` pour contrôler
le matériel de référence :

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock
python -m pytest -q
python -m src.data_pipeline --input ../../data_pack/2026-S1 --output ./output
```

Ces commandes vérifient le matériel fourni et illustrent une implémentation
possible. Le brief présentiel autorise également un notebook accompagné de
fonctions, des scripts ou une autre organisation reproductible. Les utilitaires
et notebooks retrouvent par défaut `data_pack/2026-S1/` depuis le dépôt. Un
autre dossier peut être indiqué avec la variable `DIAGOPS_DATA_DIR`.

## Hors distribution

L'oracle des anomalies, la validation formateur, la grille détaillée et les
scripts de génération sont conservés dans `_conception/M2/`, ignoré par Git.
Le contrôle `python tools/check_publication.py` empêche leur publication.
