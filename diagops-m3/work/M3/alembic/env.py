"""Environnement Alembic pour DiagOps M3.

Trois reglages ne sont pas ceux du modele genere par `alembic init` :

1. **L'URL vient du code**, pas de `alembic.ini`. `src/db/session.py::database_url`
   lit `DIAGOPS_DATABASE_URL` et retombe sur SQLite. Dupliquer l'URL dans le
   fichier de configuration ferait diverger les deux tot ou tard.

2. **`render_as_batch=True`.** SQLite ne sait pas faire la plupart des
   `ALTER TABLE`. Sans ce reglage, une migration qui modifie une colonne ou
   ajoute une contrainte echoue a l'execution. Alembic contourne en recreant la
   table et en recopiant les donnees.

3. **`include_object` filtre `sensor_readings` a la premiere migration.** Le
   brief demande deux migrations : le schema initial, puis l'ajout des mesures
   sur une base **deja chargee**. Comme les quatre modeles vivent dans le meme
   `models.py`, un autogenerate naif produirait les quatre tables d'un coup.
   La variable `DIAGOPS_ALEMBIC_STAGE=initial` exclut la table de mesures le
   temps de generer la premiere revision. Sans elle, aucun filtre : c'est
   l'etat normal du depot.
"""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context


# Rendre `src` importable quand Alembic est lance depuis work/M3.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.db.models import Base  # noqa: E402
from src.db.session import build_engine, database_url  # noqa: E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

SKIP_SENSORS = os.environ.get("DIAGOPS_ALEMBIC_STAGE") == "initial"


def include_object(obj, name, type_, reflected, compare_to):
    """Exclut la table de mesures pendant la generation de la revision initiale."""
    if SKIP_SENSORS and type_ == "table" and name == "sensor_readings":
        return False
    if SKIP_SENSORS and type_ == "index" and getattr(obj, "table", None) is not None:
        return obj.table.name != "sensor_readings"
    return True


def run_migrations_offline() -> None:
    """Migrations en mode « offline » : genere le SQL sans se connecter."""
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,
        include_object=include_object,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Migrations en mode « online » : applique sur la base connectee."""
    connectable = build_engine()
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,
            include_object=include_object,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
