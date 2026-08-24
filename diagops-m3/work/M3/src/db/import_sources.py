"""Import des sources DiagOps en base.

L'import des équipements est fourni comme exemple : lecture, conversion,
insertion et comptage des lignes refusées. L'import des mesures est le travail
du brief : il doit être idempotent, et l'idempotence doit être démontrée, pas
affirmée.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import Equipment, Event, Maintenance, SensorReading


@dataclass
class ImportReport:
    """Comptages d'un import, à conserver comme preuve."""

    table: str
    read: int = 0
    inserted: int = 0
    rejected: int = 0
    reasons: dict[str, int] | None = None

    def as_dict(self) -> dict:
        return {
            "table": self.table,
            "read": self.read,
            "inserted": self.inserted,
            "rejected": self.rejected,
            "reasons": dict(sorted((self.reasons or {}).items())),
        }


def read_rows(path: Path) -> list[dict]:
    """Lit un CSV préparé sans conversion implicite."""
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def optional_date(value: str) -> date | None:
    """Convertit une date ISO, ou retourne None si la valeur est vide."""
    if not value:
        return None
    return date.fromisoformat(value)


def optional_float(value: str) -> float | None:
    """Convertit un nombre, ou retourne None si la valeur est vide."""
    if value in ("", None):
        return None
    return float(value)


def import_equipment(session: Session, path: Path) -> ImportReport:
    """Insère les équipements préparés et compte les lignes refusées.

    Chaque ligne est insérée dans son propre point de sauvegarde : une ligne
    refusée n'annule pas les précédentes et sa raison est conservée.
    """
    report = ImportReport(table="equipment", reasons={})
    for row in read_rows(path):
        report.read += 1
        try:
            with session.begin_nested():
                session.add(
                    Equipment(
                        equipment_id=row["equipment_id"],
                        equipment_type=row["equipment_type"],
                        site_id=row["site_id"],
                        commissioning_date=optional_date(row["commissioning_date"]),
                        criticality=row["criticality"],
                        manufacturer=row["manufacturer"] or None,
                        rated_power_kw=optional_float(row["rated_power_kw"]),
                    )
                )
            report.inserted += 1
        except IntegrityError as error:
            report.rejected += 1
            reason = type(error.orig).__name__ if error.orig else "IntegrityError"
            report.reasons[reason] = report.reasons.get(reason, 0) + 1
        except (KeyError, ValueError) as error:
            report.rejected += 1
            reason = type(error).__name__
            report.reasons[reason] = report.reasons.get(reason, 0) + 1
    return report


def optional_datetime(value: str) -> datetime | None:
    """Convertit un horodatage ISO en instant UTC, ou None si vide."""
    if value in ("", None):
        return None
    moment = datetime.fromisoformat(value)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc)


def optional_decimal(value: str) -> Decimal | None:
    """Convertit un montant en decimal exact, ou None si vide."""
    if value in ("", None):
        return None
    return Decimal(value)


def import_events(session: Session, path: Path) -> ImportReport:
    """Insere les evenements. A charger APRES les equipements : la cle etrangere
    `equipment_id` impose l'ordre."""
    report = ImportReport(table="events", reasons={})
    for row in read_rows(path):
        report.read += 1
        try:
            with session.begin_nested():
                session.add(
                    Event(
                        event_id=row["event_id"],
                        equipment_id=row["equipment_id"],
                        start_at=optional_datetime(row["start_at"]),
                        end_at=optional_datetime(row["end_at"]),
                        event_type=row["event_type"],
                        severity=row["severity"],
                        period=row["period"],
                    )
                )
            report.inserted += 1
        except IntegrityError as error:
            report.rejected += 1
            reason = type(error.orig).__name__ if error.orig else "IntegrityError"
            report.reasons[reason] = report.reasons.get(reason, 0) + 1
        except (KeyError, ValueError) as error:
            report.rejected += 1
            reason = type(error).__name__
            report.reasons[reason] = report.reasons.get(reason, 0) + 1
    return report


def import_maintenance(session: Session, path: Path) -> ImportReport:
    """Insere les interventions. A charger en DERNIER : deux cles etrangeres,
    vers `equipment` et vers `events`."""
    report = ImportReport(table="maintenance_history", reasons={})
    for row in read_rows(path):
        report.read += 1
        try:
            with session.begin_nested():
                session.add(
                    Maintenance(
                        maintenance_id=row["maintenance_id"],
                        event_id=row["event_id"],
                        equipment_id=row["equipment_id"],
                        opened_at=optional_datetime(row["opened_at"]),
                        closed_at=optional_datetime(row["closed_at"]),
                        intervention_type=row["intervention_type"],
                        outcome=row["outcome"],
                        downtime_minutes=int(row["downtime_minutes"]),
                        labor_hours=optional_float(row["labor_hours"]),
                        parts_cost_eur=optional_decimal(row["parts_cost_eur"]),
                        parts_replaced_count=int(row["parts_replaced_count"]),
                        work_order_note=row["work_order_note"] or None,
                        period=row["period"],
                    )
                )
            report.inserted += 1
        except IntegrityError as error:
            report.rejected += 1
            reason = type(error.orig).__name__ if error.orig else "IntegrityError"
            report.reasons[reason] = report.reasons.get(reason, 0) + 1
        except (KeyError, ValueError) as error:
            report.rejected += 1
            reason = type(error).__name__
            report.reasons[reason] = report.reasons.get(reason, 0) + 1
    return report


BATCH_SIZE = 1000


def import_measurements(session: Session, path: Path) -> ImportReport:
    """Insere les mesures capteurs de maniere idempotente.

    **Strategie retenue : `INSERT ... ON CONFLICT DO NOTHING`** sur la contrainte
    d'unicite de la cle logique, par lots de 1 000 lignes.

    Pourquoi celle-la plutot que les deux autres :

    - *relire les cles existantes et filtrer en memoire* — correct, mais il faut
      charger 50 000 cles avant d'ecrire, et la fenetre entre la lecture et
      l'ecriture n'est pas protegee. L'unicite serait garantie par le code, pas
      par la base ;
    - *inserer ligne a ligne dans un point de sauvegarde et rattraper
      l'IntegrityError* — c'est ce que font les trois imports M2 ci-dessus, et
      c'est acceptable sur 1 788 lignes. Sur 50 000, le cout des points de
      sauvegarde devient l'essentiel du temps ;
    - **`ON CONFLICT DO NOTHING`** delegue l'unicite a la base, ne demande
      aucune lecture prealable et tient en une instruction par lot. Le cout est
      celui de l'index unique, qui existe de toute facon.

    Contrepartie assumee : l'instruction ne dit pas quelles lignes ont ete
    ignorees, seulement combien. C'est suffisant ici — la trace ligne a ligne
    est deja portee par la quarantaine du brief presentiel.

    Les mesures dont l'equipement est inconnu sont **comptees avant insertion**,
    plutot que laissees echouer sur la cle etrangere : un lot entier echouerait
    a cause d'une seule ligne, et le comptage par raison serait perdu.
    """
    report = ImportReport(table="sensor_readings", reasons={})
    known = {identifier for (identifier,) in session.query(Equipment.equipment_id).all()}

    payload: list[dict] = []
    for row in read_rows(path):
        report.read += 1
        try:
            if row["equipment_id"] not in known:
                report.rejected += 1
                report.reasons["equipement_inconnu"] = (
                    report.reasons.get("equipement_inconnu", 0) + 1
                )
                continue
            moment = optional_datetime(row["timestamp"])
            if moment is None:
                report.rejected += 1
                report.reasons["horodatage_illisible"] = (
                    report.reasons.get("horodatage_illisible", 0) + 1
                )
                continue
            payload.append(
                {
                    "equipment_id": row["equipment_id"],
                    "timestamp": moment,
                    "sensor_name": row["sensor_name"],
                    "value": optional_float(row["value"]),
                    "unit": row["unit"],
                    "period": row["period"],
                }
            )
        except (KeyError, ValueError) as error:
            report.rejected += 1
            reason = type(error).__name__
            report.reasons[reason] = report.reasons.get(reason, 0) + 1

    for start in range(0, len(payload), BATCH_SIZE):
        batch = payload[start : start + BATCH_SIZE]
        statement = sqlite_insert(SensorReading).values(batch)
        statement = statement.on_conflict_do_nothing(
            index_elements=["equipment_id", "timestamp", "sensor_name"]
        )
        result = session.execute(statement)
        report.inserted += result.rowcount if result.rowcount and result.rowcount > 0 else 0

    ignored = len(payload) - report.inserted
    if ignored > 0:
        report.reasons["deja_presente"] = ignored
    return report
