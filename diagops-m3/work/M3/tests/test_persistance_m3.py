"""Cas de verification de la persistance — brief online M3.

Les contraintes declarees dans `models.py` ne valent que si elles sont
**appliquees a l'execution**. Sur SQLite en particulier, une cle etrangere
declaree n'a aucun effet tant que `PRAGMA foreign_keys=ON` n'est pas actif : le
modele semble correct et la base accepte n'importe quoi.

Chaque contrainte a donc ici un cas qui la franchit et verifie le refus.

Les tests travaillent sur une base temporaire, jamais sur `output/diagops.db`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from src.db.models import Base, Equipment, Event, SensorReading
from src.db.session import build_engine, build_session_factory

UTC = timezone.utc


@pytest.fixture()
def session(tmp_path):
    """Base neuve par test, creee depuis les modeles.

    Les tests de contrainte n'ont pas besoin des migrations : ils verifient le
    comportement du schema. La conformite entre migrations et modeles est
    verifiee separement par `test_les_migrations_produisent_le_schema_des_modeles`.
    """
    engine = build_engine(f"sqlite+pysqlite:///{tmp_path / 'test.db'}")
    Base.metadata.create_all(engine)
    factory = build_session_factory(engine)
    with factory() as active:
        yield active
    engine.dispose()


def add_equipment(session, identifier: str = "EQ-PUMP-001") -> Equipment:
    equipment = Equipment(
        equipment_id=identifier,
        equipment_type="pump",
        site_id="SITE-NORD",
        criticality="high",
    )
    session.add(equipment)
    session.commit()
    return equipment


def reading(**overrides) -> SensorReading:
    defaults = {
        "equipment_id": "EQ-PUMP-001",
        "timestamp": datetime(2026, 3, 1, tzinfo=UTC),
        "sensor_name": "vibration_mm_s",
        "value": 2.8,
        "unit": "mm/s",
        "period": "2026-S1",
    }
    return SensorReading(**{**defaults, **overrides})


# --------------------------------------------------------------------------- #
# Clés étrangères
# --------------------------------------------------------------------------- #

def test_les_cles_etrangeres_sont_reellement_actives(session):
    """Sans PRAGMA foreign_keys=ON, ce test passerait silencieusement."""
    add_equipment(session)
    session.add(reading(equipment_id="EQ-ORPHAN-777"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_un_evenement_sur_equipement_inconnu_est_refuse(session):
    session.add(
        Event(
            event_id="EVT-1",
            equipment_id="EQ-INCONNU",
            start_at=datetime(2026, 3, 1, tzinfo=UTC),
            event_type="incident",
            severity="high",
            period="2026-S1",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_une_mesure_sur_equipement_connu_est_acceptee(session):
    add_equipment(session)
    session.add(reading())
    session.commit()
    assert session.scalar(select(func.count()).select_from(SensorReading)) == 1


# --------------------------------------------------------------------------- #
# Clé logique
# --------------------------------------------------------------------------- #

def test_la_cle_logique_refuse_un_doublon(session):
    """La contrainte d'unicite exprime la cle logique du brief."""
    add_equipment(session)
    session.add(reading())
    session.commit()
    session.add(reading(value=9.99))  # même clé, valeur différente
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_deux_capteurs_au_meme_instant_sont_acceptes(session):
    """La cle porte les trois colonnes : changer le capteur suffit a distinguer."""
    add_equipment(session)
    session.add(reading(sensor_name="vibration_mm_s"))
    session.add(reading(sensor_name="temperature_c", unit="°C", value=57.0))
    session.commit()
    assert session.scalar(select(func.count()).select_from(SensorReading)) == 2


def test_deux_instants_pour_le_meme_capteur_sont_acceptes(session):
    add_equipment(session)
    session.add(reading())
    session.add(reading(timestamp=datetime(2026, 3, 1, 6, tzinfo=UTC)))
    session.commit()
    assert session.scalar(select(func.count()).select_from(SensorReading)) == 2


# --------------------------------------------------------------------------- #
# Domaines fermés et cohérence
# --------------------------------------------------------------------------- #

def test_un_capteur_hors_domaine_est_refuse(session):
    add_equipment(session)
    session.add(reading(sensor_name="humidite_pct"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_une_valeur_negative_est_refusee(session):
    """La sentinelle -999 ne doit pas pouvoir entrer en base."""
    add_equipment(session)
    session.add(reading(value=-999.0))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_une_valeur_absente_est_acceptee(session):
    """« Le capteur n'a rien renvoye » est une information, pas une erreur."""
    add_equipment(session)
    session.add(reading(value=None))
    session.commit()
    assert session.scalar(select(func.count()).select_from(SensorReading)) == 1


def test_une_criticite_hors_domaine_est_refusee(session):
    session.add(
        Equipment(
            equipment_id="EQ-X",
            equipment_type="pump",
            site_id="SITE-NORD",
            criticality="tres_haute",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_un_evenement_qui_finit_avant_de_commencer_est_refuse(session):
    add_equipment(session)
    start = datetime(2026, 3, 1, 12, tzinfo=UTC)
    session.add(
        Event(
            event_id="EVT-1",
            equipment_id="EQ-PUMP-001",
            start_at=start,
            end_at=start - timedelta(hours=3),
            event_type="incident",
            severity="high",
            period="2026-S1",
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()


def test_un_evenement_sans_fin_est_accepte(session):
    """13 evenements sur 514 sont ouverts : la contrainte ne doit pas les bloquer."""
    add_equipment(session)
    session.add(
        Event(
            event_id="EVT-1",
            equipment_id="EQ-PUMP-001",
            start_at=datetime(2026, 3, 1, tzinfo=UTC),
            end_at=None,
            event_type="incident",
            severity="high",
            period="2026-S1",
        )
    )
    session.commit()
    assert session.scalar(select(func.count()).select_from(Event)) == 1


# --------------------------------------------------------------------------- #
# Import idempotent
# --------------------------------------------------------------------------- #

def test_import_des_mesures_idempotent(session, tmp_path):
    """Deux imports du meme fichier laissent la table dans le meme etat."""
    from src.db.import_sources import import_measurements

    add_equipment(session)
    csv_path = tmp_path / "sensor_readings.csv"
    csv_path.write_text(
        "equipment_id,timestamp,sensor_name,value,unit,period,row_identifier\n"
        "EQ-PUMP-001,2026-03-01 00:00:00+00:00,vibration_mm_s,2.80,mm/s,2026-S1,a\n"
        "EQ-PUMP-001,2026-03-01 06:00:00+00:00,vibration_mm_s,2.90,mm/s,2026-S1,b\n",
        encoding="utf-8",
    )

    first = import_measurements(session, csv_path)
    session.commit()
    assert first.read == 2 and first.inserted == 2

    second = import_measurements(session, csv_path)
    session.commit()
    assert second.read == 2
    assert second.inserted == 0, "un second import ne doit rien ajouter"
    assert second.reasons["deja_presente"] == 2
    assert session.scalar(select(func.count()).select_from(SensorReading)) == 2


def test_import_compte_les_mesures_d_equipement_inconnu(session, tmp_path):
    from src.db.import_sources import import_measurements

    add_equipment(session)
    csv_path = tmp_path / "sensor_readings.csv"
    csv_path.write_text(
        "equipment_id,timestamp,sensor_name,value,unit,period,row_identifier\n"
        "EQ-PUMP-001,2026-03-01 00:00:00+00:00,vibration_mm_s,2.80,mm/s,2026-S1,a\n"
        "EQ-ORPHAN-777,2026-03-01 00:00:00+00:00,vibration_mm_s,2.80,mm/s,2026-S1,b\n",
        encoding="utf-8",
    )
    report = import_measurements(session, csv_path)
    session.commit()
    assert report.read == 2
    assert report.inserted == 1
    assert report.rejected == 1
    assert report.reasons["equipement_inconnu"] == 1


def test_import_accepte_une_valeur_vide(session, tmp_path):
    from src.db.import_sources import import_measurements

    add_equipment(session)
    csv_path = tmp_path / "sensor_readings.csv"
    csv_path.write_text(
        "equipment_id,timestamp,sensor_name,value,unit,period,row_identifier\n"
        "EQ-PUMP-001,2026-03-01 00:00:00+00:00,vibration_mm_s,,mm/s,2026-S1,a\n",
        encoding="utf-8",
    )
    report = import_measurements(session, csv_path)
    session.commit()
    assert report.inserted == 1
    assert session.scalar(select(SensorReading.value)) is None


# --------------------------------------------------------------------------- #
# Cohérence migrations / modèles
# --------------------------------------------------------------------------- #

def test_les_migrations_produisent_le_schema_des_modeles(tmp_path):
    """Une base montee par migrations doit avoir le schema des modeles.

    C'est le controle qui empeche les deux de diverger : sans lui, une colonne
    ajoutee au modele sans migration ne se verrait qu'en production.
    """
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import inspect

    url = f"sqlite+pysqlite:///{tmp_path / 'migrated.db'}"
    config = Config("alembic.ini")
    config.set_main_option("script_location", "alembic")
    import os

    previous = os.environ.get("DIAGOPS_DATABASE_URL")
    os.environ["DIAGOPS_DATABASE_URL"] = url
    try:
        command.upgrade(config, "head")
        migrated = inspect(build_engine(url))
        tables_migrees = set(migrated.get_table_names()) - {"alembic_version"}
    finally:
        if previous is None:
            os.environ.pop("DIAGOPS_DATABASE_URL", None)
        else:
            os.environ["DIAGOPS_DATABASE_URL"] = previous

    assert tables_migrees == set(Base.metadata.tables)

    for table in sorted(tables_migrees):
        colonnes_migrees = {c["name"] for c in migrated.get_columns(table)}
        colonnes_modele = set(Base.metadata.tables[table].columns.keys())
        assert colonnes_migrees == colonnes_modele, f"divergence sur {table}"
