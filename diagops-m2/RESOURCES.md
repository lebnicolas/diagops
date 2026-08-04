# Ressources — Module 2

## Continuité M1 → M2

- `data_pack/2026-S1/reference_runs/m1_for_m2/` — état de référence commun ;
- `data_pack/2026-S1/reference_runs/m1_for_m2/README.md` — périmètre, contenu
  et limites.

Ce dossier contient les prédictions, métriques et erreurs nécessaires à M2. Il
ne contient ni poids de modèle, ni correction complète de M1, ni solution du
travail demandé en M2. Les productions personnelles de M1 peuvent être
comparées à cette référence, mais ne sont pas requises pour commencer.

## Données distribuées

- `data_pack/2026-S1/equipment/equipment.csv` ;
- `data_pack/2026-S1/events/events.csv` ;
- `data_pack/2026-S1/maintenance/maintenance_history.csv` ;
- `data_pack/MANIFEST.yaml`, `data_pack/SCHEMA.md`, `data_pack/DATA_CARD.md` et
  `data_pack/checksums.sha256`.

Ces fichiers font partie du dossier M2 ; aucune archive ni copie du data pack
global n'est nécessaire.

## Complément « Pour aller plus loin »

- `data_pack/2026-S1/m2_candidate_release/` — livraison à qualifier ;
- `data_pack/2026-S1/m2_candidate_release/RELEASE_NOTES.md` — nature des
  fichiers, volumes annoncés et évolutions déclarées ;
- GitHub Actions — documentation officielle :
  <https://docs.github.com/actions> ;
- GitHub Skills — catalogue des laboratoires : <https://skills.github.com/> ;
- GitHub Skills — Test with Actions :
  <https://github.com/skills/test-with-actions> ;
- GitHub Actions — artefacts de workflow :
  <https://docs.github.com/actions/using-workflows/storing-workflow-data-as-artifacts> ;
- GitHub Actions — sécurisation des workflows :
  <https://docs.github.com/actions/security-guides/security-hardening-for-github-actions> ;
- YAML — spécification : <https://yaml.org/spec/>.

La qualification doit d'abord fonctionner localement. Pour terminer le
complément facultatif, l'apprenant réalise ensuite le laboratoire GitHub Skills
indiqué, ou un équivalent validé par le formateur, puis applique GitHub Actions
à DiagOps dans son dépôt privé.

## Programme Atlas

- `S02/M2/data-pour-l-ia-6924c8bbbfdfc957869223.pdf` — statistiques
  descriptives, corrélation et valeurs aberrantes ;
- `S02/M2/opco-atlas-pandas-seaborn-69202f6855254983958530.docx` — Pandas,
  Seaborn et préparation des données ;
- `S02/M2/fichier de données numériques.csv` — jeu d'exemple historique Atlas.

Les trois tables DiagOps ouvertes en M2 remplacent le jeu d'exemple pour les
livrables, tout en conservant les notions du support.

## Données et statistiques

- Pandas — guide utilisateur : <https://pandas.pydata.org/docs/user_guide/> ;
- Pandas — statistiques descriptives :
  <https://pandas.pydata.org/docs/user_guide/basics.html#descriptive-statistics> ;
- Seaborn — tutoriel : <https://seaborn.pydata.org/tutorial.html> ;
- SciPy — statistiques : <https://docs.scipy.org/doc/scipy/reference/stats.html> ;
- Scikit-learn — prétraitement :
  <https://scikit-learn.org/stable/modules/preprocessing.html>.

## Validation et tests de données

- Pandera : <https://pandera.readthedocs.io/> ;
- Pydantic : <https://docs.pydantic.dev/> ;
- Pytest : <https://docs.pytest.org/> ;
- bibliothèque standard Python — `argparse`, `csv`, `json` et `pathlib` :
  <https://docs.python.org/3/library/>.

Les contrôles peuvent utiliser Pandera, Pydantic ou des fonctions Python
simples.
Le choix de l'outil n'est pas évalué en lui-même : les contrôles doivent être
compréhensibles, testés et reproductibles.

## Données personnelles

- CNIL — principe de minimisation :
  <https://www.cnil.fr/fr/les-six-grands-principes-du-rgpd> ;
- CNIL — anonymisation et pseudonymisation :
  <https://www.cnil.fr/fr/lanonymisation-de-donnees-personnelles> ;
- RGPD, texte officiel :
  <https://eur-lex.europa.eu/eli/reg/2016/679/oj>.

## AI Act

- Règlement européen 2024/1689 :
  <https://eur-lex.europa.eu/eli/reg/2024/1689/oj> ;
- article 10 — données et gouvernance des données : utiliser cette exigence
  comme grille conditionnelle, sans qualifier automatiquement DiagOps de
  système à haut risque.

## Règle d'usage

Privilégiez les documentations officielles et les sources primaires. Toute
réponse produite par un assistant doit être vérifiée contre la version de la
bibliothèque ou du texte réellement utilisée.
