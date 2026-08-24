# Ressources — Module 3

## Continuité M2 → M3

- `data_pack/2026-S1/reference_runs/m2_for_m3/` — état préparé de référence ;
- `data_pack/2026-S1/reference_runs/m2_for_m3/README.md` — périmètre, contenu et
  limites ;
- `data_pack/2026-S1/reference_runs/m2_for_m3/regles_m2.md` — registre des règles
  à reprendre, à modifier ou à abandonner en M3.

Ce dossier contient les tables préparées, la quarantaine, le registre des règles
et la décision de référence issus de M2. Il ne contient pas la correction du
brief M2 : le registre est partiel et plusieurs décisions restent discutables.
Votre propre préparation M2 reste utilisable si vous indiquez laquelle vous
employez.

## Données distribuées

- `data_pack/2026-S1/sensors/sensor_readings.csv` — nouvelle source ouverte en
  M3 ;
- `data_pack/2026-S1/equipment/equipment.csv` ;
- `data_pack/2026-S1/events/events.csv` ;
- `data_pack/2026-S1/maintenance/maintenance_history.csv` ;
- `data_pack/MANIFEST.yaml`, `data_pack/SCHEMA.md`, `data_pack/DATA_CARD.md` et
  `data_pack/checksums.sha256`.

La section `sensors` de `SCHEMA.md` décrit les colonnes, la clé logique et le pas
nominal annoncé. Ce qui est annoncé n'est pas ce qui est garanti : le brief
demande de le vérifier.

## Programme Atlas

- `S02/M3/opco-atlas-sqlalchemy-alembic-692db40185fa4325592656.docx` — SQLAlchemy,
  Alembic et migrations ;
- `S02/M3/OPCO-ATLAS-Module-3-Brief-3-main/` — projet Atlas de référence :
  modèles, base, seed et import d'un nouveau jeu de données.

Les données DiagOps remplacent le jeu d'exemple Atlas pour les livrables, tout en
conservant les notions du support.

## Base de données, ORM et migrations

- SQLAlchemy — documentation : <https://docs.sqlalchemy.org/> ;
- SQLAlchemy — ORM, déclaration des modèles :
  <https://docs.sqlalchemy.org/en/20/orm/quickstart.html> ;
- SQLAlchemy — types de colonnes :
  <https://docs.sqlalchemy.org/en/20/core/type_basics.html> ;
- SQLAlchemy — contraintes et index :
  <https://docs.sqlalchemy.org/en/20/core/constraints.html> ;
- Alembic — tutoriel : <https://alembic.sqlalchemy.org/en/latest/tutorial.html> ;
- Alembic — autogénération de révision :
  <https://alembic.sqlalchemy.org/en/latest/autogenerate.html> ;
- Alembic — opérations de migration :
  <https://alembic.sqlalchemy.org/en/latest/ops.html> ;
- SQLite — types et limites : <https://www.sqlite.org/datatype3.html> ;
- SQLite — clés étrangères : <https://www.sqlite.org/foreignkeys.html> ;
- PostgreSQL — types de données :
  <https://www.postgresql.org/docs/current/datatype.html>.

Sur SQLite, les clés étrangères ne sont pas appliquées par défaut. Vérifiez le
comportement de votre moteur avant de conclure qu'une contrainte fonctionne.

L'idempotence d'un import peut s'obtenir de plusieurs manières : contrôle
préalable, contrainte d'unicité assortie d'une insertion tolérante, ou
`INSERT ... ON CONFLICT`. Le choix doit être justifié et son coût observé.

## Séries temporelles

- Pandas — séries temporelles :
  <https://pandas.pydata.org/docs/user_guide/timeseries.html> ;
- Pandas — `merge_asof`, rapprochement par proximité temporelle :
  <https://pandas.pydata.org/docs/reference/api/pandas.merge_asof.html> ;
- Pandas — `resample` et agrégation par fenêtre :
  <https://pandas.pydata.org/docs/user_guide/timeseries.html#resampling> ;
- Pandas — `IntervalIndex`, appartenance à une fenêtre :
  <https://pandas.pydata.org/docs/reference/api/pandas.IntervalIndex.html> ;
- Python — module `zoneinfo` et fuseaux horaires :
  <https://docs.python.org/3/library/zoneinfo.html> ;
- ISO 8601 — représentation des dates et heures :
  <https://www.iso.org/iso-8601-date-and-time-format.html>.

Deux rapprochements sont possibles et ne répondent pas à la même question :
`merge_asof` associe chaque ligne à l'observation la plus proche dans le temps ;
une jointure par intervalle associe toutes les mesures d'une fenêtre. Choisissez
en fonction de la question posée, pas de la commodité d'écriture.

## Qualité d'une source temporelle

- NIST/SEMATECH — *Engineering Statistics Handbook*, détection d'observations
  atypiques et contrôle de procédé :
  <https://www.itl.nist.gov/div898/handbook/> ;
- NIST/SEMATECH — cartes de contrôle et détection d'une dérive :
  <https://www.itl.nist.gov/div898/handbook/pmc/section3/pmc3.htm> ;
- Gebru et al. — *Datasheets for Datasets* : <https://arxiv.org/abs/1803.09010> —
  la fiche de données est mise à jour à chaque nouvelle source.

Un capteur figé, une dérive lente et un pic isolé ne se traitent pas de la même
manière. Les deux premiers concernent l'instrument ; le troisième peut concerner
l'équipement.

## Validation et tests

- Pandera — validation de DataFrame : <https://pandera.readthedocs.io/> ;
- Pydantic : <https://docs.pydantic.dev/> ;
- Pytest — fixtures et paramétrage : <https://docs.pytest.org/> ;
- bibliothèque standard Python — `csv`, `datetime`, `pathlib`, `sqlite3` :
  <https://docs.python.org/3/library/>.

Le choix de l'outil n'est pas évalué en lui-même. Les contrôles doivent être
compréhensibles, testés et reproductibles. Un test de non-régression sur les
tables M2 vaut mieux qu'une affirmation.

## Données personnelles et proportionnalité

- CNIL — principe de minimisation :
  <https://www.cnil.fr/fr/les-six-grands-principes-du-rgpd> ;
- CNIL — anonymisation et pseudonymisation :
  <https://www.cnil.fr/fr/lanonymisation-de-donnees-personnelles> ;
- CNIL — vidéosurveillance et dispositifs de suivi de l'activité des salariés :
  <https://www.cnil.fr/fr/la-surveillance-des-salaries> ;
- RGPD, texte officiel : <https://eur-lex.europa.eu/eli/reg/2016/679/oj>.

Une mesure d'équipement n'est pas une donnée personnelle en soi. Croisée avec un
site, un horaire et un bon de travail, elle peut le devenir. La question à
traiter est celle de la proportionnalité, pas celle de la qualification
juridique.

## AI Act

- Règlement européen 2024/1689 :
  <https://eur-lex.europa.eu/eli/reg/2024/1689/oj> ;
- article 10 — données et gouvernance des données : la représentativité des
  données d'entraînement se prépare ici, au moment où la couverture
  instrumentale est mesurée.

## Volume et sobriété

- Green Algorithms — empreinte d'un calcul :
  <https://www.green-algorithms.org/> ;
- ADEME — sobriété numérique et cycle de vie des données :
  <https://www.ademe.fr/> .

Conserver toutes les mesures brutes, seulement des agrégats, ou les deux, est un
arbitrage à formuler. Mesurez le temps de rejeu de votre pipeline et indiquez ce
qui deviendrait impraticable sur une période complète.

## Règle d'usage

Privilégiez les documentations officielles et les sources primaires. Toute
réponse produite par un assistant doit être vérifiée contre la version de la
bibliothèque ou du texte réellement utilisée. C'est particulièrement vrai pour
Alembic et SQLAlchemy, dont les exemples en circulation mélangent souvent les
styles 1.4 et 2.0.
