"""Modeles DiagOps — brief online M3.

Trois entites heritees de M2 (`equipment`, `events`, `maintenance_history`) et la
table de mesures ouverte en M3 (`sensor_readings`).

`SensorReading` est declaree ici mais **n'est pas creee par la premiere
migration** : elle fait l'objet d'une seconde migration, appliquee sur une base
deja chargee. C'est l'objet meme du brief — faire evoluer un schema sans
detruire ce qui existe.

Choix de types : voir `docs/persistance_m3.md`, section « Types retenus ».
Le principe general est de ne jamais elargir un domaine que les donnees ferment.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Domaines fermes, repris de `contracts/schemas.py`. Les exprimer en base plutot
# que de s'en remettre au code applicatif : une contrainte declaree resiste a un
# import ecrit par quelqu'un d'autre.
CRITICALITIES = ("low", "medium", "high", "critical")
SEVERITIES = ("low", "medium", "high", "critical")
EVENT_TYPES = ("incident", "intervention", "observation", "alert")
INTERVENTION_TYPES = (
    "inspection",
    "corrective",
    "preventive",
    "calibration",
    "replacement",
)
OUTCOMES = (
    "resolved",
    "monitoring",
    "parts_ordered",
    "no_fault_found",
    "follow_up_required",
)
SENSOR_NAMES = (
    "vibration_mm_s",
    "temperature_c",
    "pressure_bar",
    "current_a",
    "rpm",
)


def _in(column: str, values: tuple[str, ...]) -> str:
    joined = ", ".join(f"'{value}'" for value in values)
    return f"{column} IN ({joined})"


class Base(DeclarativeBase):
    """Base declarative commune a tous les modeles DiagOps."""


class Equipment(Base):
    """Inventaire des equipements suivis. 416 lignes."""

    __tablename__ = "equipment"
    __table_args__ = (
        CheckConstraint(_in("criticality", CRITICALITIES), name="ck_equipment_criticality"),
        CheckConstraint("rated_power_kw IS NULL OR rated_power_kw > 0", name="ck_equipment_power"),
    )

    equipment_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    equipment_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    site_id: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    commissioning_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    criticality: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    manufacturer: Mapped[str | None] = mapped_column(String(64), nullable=True)
    rated_power_kw: Mapped[float | None] = mapped_column(Float, nullable=True)

    events: Mapped[list["Event"]] = relationship(back_populates="equipment")

    def __repr__(self) -> str:  # pragma: no cover - confort de lecture
        return f"<Equipment {self.equipment_id} {self.equipment_type}>"


class Event(Base):
    """Evenements d'exploitation. 514 lignes.

    `end_at` est facultative : 13 evenements sur 514 sont ouverts. La contrainte
    d'ordre chronologique ne s'applique donc que lorsque la fin est renseignee.
    """

    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint(_in("severity", SEVERITIES), name="ck_events_severity"),
        CheckConstraint(_in("event_type", EVENT_TYPES), name="ck_events_type"),
        CheckConstraint("end_at IS NULL OR end_at >= start_at", name="ck_events_chronology"),
        Index("ix_events_equipment_start", "equipment_id", "start_at"),
    )

    event_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    equipment_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("equipment.equipment_id", ondelete="RESTRICT"), nullable=False
    )
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    event_type: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    period: Mapped[str] = mapped_column(String(16), nullable=False)

    equipment: Mapped[Equipment] = relationship(back_populates="events")
    interventions: Mapped[list["Maintenance"]] = relationship(back_populates="event")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Event {self.event_id} {self.event_type}/{self.severity}>"


class Maintenance(Base):
    """Interventions de maintenance. 1 788 lignes."""

    __tablename__ = "maintenance_history"
    __table_args__ = (
        CheckConstraint(
            _in("intervention_type", INTERVENTION_TYPES), name="ck_maintenance_type"
        ),
        CheckConstraint(_in("outcome", OUTCOMES), name="ck_maintenance_outcome"),
        CheckConstraint(
            "closed_at IS NULL OR closed_at >= opened_at", name="ck_maintenance_chronology"
        ),
        CheckConstraint("downtime_minutes >= 0", name="ck_maintenance_downtime"),
        CheckConstraint(
            "parts_cost_eur IS NULL OR parts_cost_eur >= 0", name="ck_maintenance_cost"
        ),
    )

    maintenance_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    event_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("events.event_id", ondelete="RESTRICT"), nullable=False, index=True
    )
    equipment_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("equipment.equipment_id", ondelete="RESTRICT"), nullable=False
    )
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    intervention_type: Mapped[str] = mapped_column(String(16), nullable=False)
    outcome: Mapped[str] = mapped_column(String(24), nullable=False)
    downtime_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    labor_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Numeric et non Float : un montant se compare et s'additionne, et le binaire
    # flottant ne represente pas exactement 0,10 €. Sur 1 788 lignes l'ecart est
    # invisible ; sur un cumul annuel il ne l'est plus.
    parts_cost_eur: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    parts_replaced_count: Mapped[int] = mapped_column(Integer, nullable=False)
    work_order_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    period: Mapped[str] = mapped_column(String(16), nullable=False)

    event: Mapped[Event] = relationship(back_populates="interventions")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Maintenance {self.maintenance_id} {self.intervention_type}>"


class SensorReading(Base):
    """Mesures capteurs. Ajoutee par la SECONDE migration, sur base chargee.

    Deux choix structurants :

    - une **cle primaire de substitution** (`reading_id`) plutot que la cle
      logique en cle primaire. La cle logique est exprimee par une contrainte
      d'unicite. Motif : une cle primaire composite de trois colonnes dont une
      chaine de 32 caracteres et un horodatage serait recopiee dans chaque
      index ; et surtout, la cle logique n'etait **pas unique dans le fichier
      recu** — la promouvoir en cle primaire aurait rendu l'import impossible
      avant nettoyage, alors qu'une contrainte permet de constater le rejet.
    - `ondelete="RESTRICT"` sur la reference vers `equipment` : une mesure
      orpheline est **refusee a l'insertion**, elle n'est pas silencieusement
      rattachee ni supprimee en cascade. Les 30 mesures de `EQ-ORPHAN-777` sont
      deja ecartees par la pipeline (`R-SEN-013`) ; la contrainte est la seconde
      barriere, pour un import qui contournerait la pipeline.
    """

    __tablename__ = "sensor_readings"
    __table_args__ = (
        UniqueConstraint(
            "equipment_id", "timestamp", "sensor_name", name="uq_sensor_readings_logical_key"
        ),
        CheckConstraint(_in("sensor_name", SENSOR_NAMES), name="ck_sensor_readings_name"),
        CheckConstraint("value IS NULL OR value >= 0", name="ck_sensor_readings_value"),
        # Index justifie par la requete Q-VIB, reellement executee : filtrer un
        # capteur et un seuil de valeur, puis trier par valeur.
        # Gain mesure : x84,6 (4,31 ms -> 0,051 ms), et le tri temporaire
        # disparait du plan.
        #
        # Un index (equipment_id, timestamp) avait ete declare en premier, pour
        # le motif « un equipement sur une plage de temps ». Il a ete **retire
        # apres mesure** : la contrainte d'unicite cree deja
        # `sqlite_autoindex_sensor_readings_1` sur
        # (equipment_id, timestamp, sensor_name), dont les deux premieres
        # colonnes couvrent exactement ce motif. Gain mesure de l'index dedie :
        # x0,99 — aucun. Voir `docs/persistance_m3.md`.
        Index("ix_sensor_readings_sensor_value", "sensor_name", "value"),
    )

    reading_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    equipment_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("equipment.equipment_id", ondelete="RESTRICT"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    sensor_name: Mapped[str] = mapped_column(String(24), nullable=False)
    # Nullable : une mesure peut exister sans valeur exploitable — sentinelle
    # neutralisee ou champ vide. « Le capteur n'a rien renvoye » est une
    # information d'exploitation, la ligne ne doit pas disparaitre.
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str] = mapped_column(String(16), nullable=False)
    period: Mapped[str] = mapped_column(String(16), nullable=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<SensorReading {self.equipment_id} {self.sensor_name} {self.timestamp}>"
