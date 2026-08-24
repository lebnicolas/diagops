# Module 3 — Intégrer une nouvelle source et faire évoluer la pipeline

Ce dossier contient les supports propres à M3. Il fait partie du dépôt S04 :
aucun ZIP ni kit séparé n'est à préparer. Les données restent centralisées dans
`../data_pack/` et le travail est initialisé dans `../work/M3/`.

## Contenu

- `brief1_module3.md` : brief présentiel moderne, 14 h ;
- `brief1_module3_online.md` : brief online aligné sur le programme Atlas, 6 h ;
- `../data_pack/2026-S1/sensors/sensor_readings.csv` : source ouverte en M3 ;
- `../data_pack/2026-S1/reference_runs/m2_for_m3/` : état préparé de référence
  permettant de commencer M3 sans dépendre de l'achèvement des productions M2 ;
- `starter/` : chargement des quatre sources, utilitaires temporels, registre de
  règles, quarantaine unifiée, squelette de base de données, notebooks et tests ;
- `RESOURCES.md` : ressources documentaires ;
- `module_3_synthese.md` et `acquis_m3.md` : cadrage et état cible du module.

Les tables, rapports et annotations déjà remis en M0, M1 et M2 ne sont pas
dupliqués. La référence de continuité fournit l'état préparé nécessaire au
travail multi-source.

Aucun complément facultatif n'est publié pour M3.

## Parcours

| Parcours | Charge | Statut |
|---|---:|---|
| Brief présentiel moderne | 14 h | obligatoire |
| Brief online Atlas | 6 h | obligatoire |

## Organisation

Les cinq apprenants travaillent sur les mêmes briefs et les mêmes ressources,
chacun dans son propre environnement. Les échanges et revues collectives sont
possibles, sans constitution de groupes ni sujet personnalisé.

## Initialisation du travail

Depuis la racine du dépôt privé, sur `main` :

```bash
python tools/init_module.py M3
cd work/M3
```

Le script refuse d'écraser un travail déjà présent.

## Vérification du starter

Depuis `work/M3/` après initialisation, ou depuis `M3/starter/` pour contrôler le
matériel de référence :

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
et notebooks retrouvent par défaut `data_pack/2026-S1/` depuis le dépôt. Un autre
dossier peut être indiqué avec la variable `DIAGOPS_DATA_DIR`.

## Deux briefs, deux points d'entrée

Le présentiel part de `notebooks/notebook_multisource_m3.ipynb` et du paquet
`src/data_pipeline/`. L'online part de `src/db/` et de la démarche décrite dans
`starter/README.md` : la migration initiale est à créer par l'apprenant, le
starter ne fournit ni `alembic.ini` ni révision toute faite.

## Hors distribution

L'oracle des anomalies capteurs, le résumé de validation, la grille détaillée et
les scripts de génération sont conservés dans `_conception/M3/` et
`_conception/`, ignorés par Git. Le contrôle
`python tools/check_publication.py` empêche leur publication.
