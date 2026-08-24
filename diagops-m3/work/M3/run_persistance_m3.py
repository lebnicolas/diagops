"""Brief online M3 — persistance DiagOps avec SQLAlchemy et Alembic.

Sous-commandes, dans l'ordre de la demonstration :

    python run_persistance_m3.py load          # charge les 3 tables M2
    python run_persistance_m3.py measurements  # import idempotent des mesures
    python run_persistance_m3.py queries       # execute et conserve les requetes

La sequence complete, migrations comprises, est decrite dans
`docs/persistance_m3.md`. Le fichier de base n'est pas un livrable : il se
reconstruit entierement a partir des migrations et de ces commandes.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from sqlalchemy import func, select, text

from src.db.import_sources import (
    import_equipment,
    import_events,
    import_maintenance,
    import_measurements,
)
from src.db.models import Equipment, SensorReading
from src.db.session import build_engine, session_scope

PROCESSED = Path("output/processed")
REPORTS = Path("output/db")


def _write(name: str, payload: dict) -> None:
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / name).write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
    )


def load() -> int:
    """Charge les trois tables preparees, dans l'ordre impose par les cles etrangeres."""
    reports = []
    started = time.perf_counter()
    with session_scope() as session:
        # L'ordre n'est pas negociable : `events` reference `equipment`, et
        # `maintenance_history` reference les deux.
        reports.append(import_equipment(session, PROCESSED / "equipment.csv").as_dict())
        reports.append(import_events(session, PROCESSED / "events.csv").as_dict())
        reports.append(
            import_maintenance(session, PROCESSED / "maintenance_history.csv").as_dict()
        )
    elapsed = time.perf_counter() - started

    payload = {
        "etape": "chargement des tables M2",
        "duree_s": round(elapsed, 2),
        "tables": reports,
        "totaux": {
            "lues": sum(r["read"] for r in reports),
            "inserees": sum(r["inserted"] for r in reports),
            "rejetees": sum(r["rejected"] for r in reports),
        },
    }
    _write("chargement_m2.json", payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def measurements() -> int:
    """Importe les mesures deux fois de suite : l'idempotence se demontre."""
    runs = []
    for attempt in (1, 2):
        started = time.perf_counter()
        with session_scope() as session:
            report = import_measurements(session, PROCESSED / "sensor_readings.csv").as_dict()
        elapsed = time.perf_counter() - started
        with session_scope() as session:
            total = session.scalar(select(func.count()).select_from(SensorReading))
        report["duree_s"] = round(elapsed, 2)
        report["lignes_en_base_apres"] = int(total)
        runs.append(report)
        print(f"  passage {attempt} : {report['inserted']} inserees, "
              f"{total} lignes en base, {elapsed:.2f} s")

    identique = runs[0]["lignes_en_base_apres"] == runs[1]["lignes_en_base_apres"]
    payload = {
        "etape": "import des mesures",
        "strategie": "INSERT ... ON CONFLICT DO NOTHING sur la cle logique, par lots de 1000",
        "passages": runs,
        "idempotent": bool(identique and runs[1]["inserted"] == 0),
        "preuve": (
            f"deux executions successives laissent {runs[1]['lignes_en_base_apres']} lignes ; "
            f"le second passage insere {runs[1]['inserted']} ligne(s)"
        ),
    }
    _write("import_mesures.json", payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["idempotent"] else 1


# Les requetes du brief. Ecrites en SQL pour rester lisibles et rejouables hors
# de Python ; l'API SQLAlchemy aurait convenu de la meme facon.
QUERIES: list[tuple[str, str, str]] = [
    (
        "Q12",
        "Nombre de mesures par equipement et par capteur",
        """
        SELECT equipment_id, sensor_name, COUNT(*) AS mesures
        FROM sensor_readings
        GROUP BY equipment_id, sensor_name
        ORDER BY mesures DESC, equipment_id
        """,
    ),
    (
        "Q13",
        "Premiere et derniere mesure de chaque serie",
        """
        SELECT equipment_id, sensor_name,
               MIN(timestamp) AS premiere, MAX(timestamp) AS derniere,
               COUNT(*) AS mesures
        FROM sensor_readings
        GROUP BY equipment_id, sensor_name
        ORDER BY equipment_id, sensor_name
        """,
    ),
    (
        "Q14",
        "Equipements du parc sans aucune mesure",
        """
        SELECT e.equipment_id, e.equipment_type, e.site_id, e.criticality
        FROM equipment e
        LEFT JOIN sensor_readings s ON s.equipment_id = e.equipment_id
        WHERE s.equipment_id IS NULL
        ORDER BY e.criticality DESC, e.equipment_id
        """,
    ),
    (
        "Q-COUV",
        "Taux d'instrumentation par criticite",
        """
        SELECT e.criticality,
               COUNT(DISTINCT e.equipment_id) AS parc,
               COUNT(DISTINCT s.equipment_id) AS instrumentes,
               ROUND(100.0 * COUNT(DISTINCT s.equipment_id)
                     / COUNT(DISTINCT e.equipment_id), 2) AS taux_pct
        FROM equipment e
        LEFT JOIN sensor_readings s ON s.equipment_id = e.equipment_id
        GROUP BY e.criticality
        ORDER BY taux_pct DESC
        """,
    ),
    (
        "Q-VIB",
        "Vibrations les plus fortes, avec le contexte de l'equipement",
        """
        SELECT s.equipment_id, e.equipment_type, e.criticality,
               s.timestamp, s.value, s.unit
        FROM sensor_readings s
        JOIN equipment e ON e.equipment_id = s.equipment_id
        WHERE s.sensor_name = 'vibration_mm_s' AND s.value > 5.0
        ORDER BY s.value DESC
        """,
    ),
    (
        "Q-EVT",
        "Evenements critiques sur equipement instrumente, avec le nombre de mesures dans les 48 h qui precedent",
        """
        SELECT v.event_id, v.equipment_id, v.severity, v.start_at,
               COUNT(s.reading_id) AS mesures_48h_avant
        FROM events v
        JOIN sensor_readings s
          ON s.equipment_id = v.equipment_id
         AND s.timestamp BETWEEN datetime(v.start_at, '-48 hours') AND v.start_at
        WHERE v.severity = 'critical'
        GROUP BY v.event_id, v.equipment_id, v.severity, v.start_at
        ORDER BY mesures_48h_avant DESC
        """,
    ),
]


def queries() -> int:
    """Execute les requetes, conserve leurs resultats, mesure l'effet de l'index."""
    REPORTS.mkdir(parents=True, exist_ok=True)
    engine = build_engine()
    results = []
    with engine.connect() as connection:
        for code, title, sql in QUERIES:
            started = time.perf_counter()
            rows = connection.execute(text(sql)).mappings().all()
            elapsed = time.perf_counter() - started
            payload = [dict(row) for row in rows]
            (REPORTS / f"requete_{code}.json").write_text(
                json.dumps(payload, indent=2, ensure_ascii=False, default=str),
                encoding="utf-8",
            )
            results.append(
                {
                    "code": code,
                    "titre": title,
                    "lignes": len(rows),
                    "duree_ms": round(1000 * elapsed, 2),
                    "extrait": payload[:5],
                }
            )
            print(f"  {code:8} {len(rows):>4} lignes  {1000*elapsed:7.2f} ms  {title}")

    payload = {"etape": "requetes", "requetes": results}
    _write("requetes.json", payload)
    return 0


def index_effect() -> int:
    """Mesure l'effet reel de l'index `ix_sensor_readings_equipment_time`.

    Le brief demande l'effet **observe**, pas une affirmation. On compare le plan
    d'execution et le temps avec et sans l'index, sur une requete qui filtre un
    equipement sur une plage de temps — le motif d'acces attendu sur une serie.
    """
    # Requete Q-VIB, reellement executee : c'est elle qui justifie l'index.
    base = """
        SELECT equipment_id, timestamp, value
        FROM sensor_readings{hint}
        WHERE sensor_name = 'vibration_mm_s' AND value > 5.0
        ORDER BY value DESC
    """
    # Requete « un equipement sur une plage de temps » : elle motivait le
    # premier index, retire apres mesure.
    by_time = """
        SELECT COUNT(*), AVG(value)
        FROM sensor_readings{hint}
        WHERE equipment_id = 'EQ-FAN-304'
          AND timestamp BETWEEN '2026-05-01 00:00:00+00:00' AND '2026-05-31 23:59:59+00:00'
    """
    engine = build_engine()

    def measure(sql: str) -> dict:
        """Plan et temps median, sur une connexion reellement neuve.

        `engine.dispose()` est indispensable : le pool de SQLAlchemy reutilise
        la connexion SQLite sous-jacente, qui garde son cache de plans. Sans
        cela, un `EXPLAIN` execute apres un `DROP INDEX` renvoie le plan
        d'avant — c'est ce que faisaient les deux premieres versions de cette
        mesure, qui annoncaient le meme index dans tous les etats.
        """
        engine.dispose()
        with engine.connect() as connection:
            plan = connection.execute(text("EXPLAIN QUERY PLAN " + sql)).mappings().all()
            timings = []
            for _ in range(50):
                started = time.perf_counter()
                connection.execute(text(sql)).all()
                timings.append(time.perf_counter() - started)
        return {
            "plan": " | ".join(str(row["detail"]) for row in plan),
            "duree_mediane_ms": round(1000 * sorted(timings)[len(timings) // 2], 4),
        }

    retenu = {
        "avec_index": measure(base.format(hint="")),
        # `NOT INDEXED` force le parcours complet : c'est le seul moyen de
        # mesurer le gain reel, un DROP laissant l'index de la contrainte
        # d'unicite disponible.
        "sans_aucun_index": measure(base.format(hint=" NOT INDEXED")),
    }

    # Le premier index declare, mesure puis retire.
    ecarte = {"index_unicite_seul": measure(by_time.format(hint=""))}
    with engine.begin() as connection:
        connection.execute(
            text(
                "CREATE INDEX IF NOT EXISTS ix_sensor_readings_equipment_time "
                "ON sensor_readings (equipment_id, timestamp)"
            )
        )
    ecarte["avec_index_dedie"] = measure(by_time.format(hint=""))
    with engine.begin() as connection:
        connection.execute(text("DROP INDEX IF EXISTS ix_sensor_readings_equipment_time"))
    ecarte["sans_aucun_index"] = measure(by_time.format(hint=" NOT INDEXED"))

    def ratio(a: float, b: float) -> float | None:
        return round(a / b, 2) if b else None

    payload = {
        "etape": "effet de l'index",
        "index_retenu": {
            "nom": "ix_sensor_readings_sensor_value",
            "colonnes": ["sensor_name", "value"],
            "requete": " ".join(base.format(hint="").split()),
            "mesures": retenu,
            "gain": ratio(
                retenu["sans_aucun_index"]["duree_mediane_ms"],
                retenu["avec_index"]["duree_mediane_ms"],
            ),
        },
        "index_ecarte_apres_mesure": {
            "nom": "ix_sensor_readings_equipment_time",
            "colonnes": ["equipment_id", "timestamp"],
            "requete": " ".join(by_time.format(hint="").split()),
            "mesures": ecarte,
            "gain_de_l_index_dedie": ratio(
                ecarte["index_unicite_seul"]["duree_mediane_ms"],
                ecarte["avec_index_dedie"]["duree_mediane_ms"],
            ),
            "gain_de_l_indexation": ratio(
                ecarte["sans_aucun_index"]["duree_mediane_ms"],
                ecarte["index_unicite_seul"]["duree_mediane_ms"],
            ),
            "conclusion": (
                "redondant avec sqlite_autoindex_sensor_readings_1, cree par la "
                "contrainte d'unicite sur (equipment_id, timestamp, sensor_name)"
            ),
        },
    }
    _write("effet_index.json", payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "step", choices=["load", "measurements", "queries", "index", "counts"]
    )
    args = parser.parse_args()

    if args.step == "load":
        return load()
    if args.step == "measurements":
        return measurements()
    if args.step == "queries":
        return queries()
    if args.step == "index":
        return index_effect()

    # Volontairement tolerant a l'absence de `sensor_readings` : cette commande
    # sert a comparer l'etat AVANT et APRES la seconde migration, et avant, la
    # table n'existe pas encore.
    from sqlalchemy import inspect

    engine = build_engine()
    present = set(inspect(engine).get_table_names())
    counts = {}
    with engine.connect() as connection:
        for table in ("equipment", "events", "maintenance_history", "sensor_readings"):
            counts[table] = (
                connection.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                if table in present
                else "table absente"
            )
    version = None
    if "alembic_version" in present:
        with engine.connect() as connection:
            version = connection.execute(text("SELECT version_num FROM alembic_version")).scalar()
    print(json.dumps({"revision": version, "lignes": counts}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
