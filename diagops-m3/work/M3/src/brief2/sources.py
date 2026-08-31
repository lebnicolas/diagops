"""Chargement du point de départ du brief 2.

Arbitrage A1, tranché le 25/08 : le brief 2 part de **notre préparation du
brief 1** (`output/processed/`), et non de la référence commune
`reference_runs/m2_for_m3/`. Notre préparation dérive elle-même de cette
référence, la filiation reste donc traçable, et le rapprochement temporel
produit au brief 1 devient exploitable comme instrument de détection.

Ce module ne transforme rien. Les neutralisations nécessaires aux calculs
(sentinelles, valeurs absentes) sont faites à l'endroit où elles servent, et
tracées là-bas.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data_pipeline.io import file_sha256


WORK_ROOT = Path(__file__).resolve().parents[2]
PREPARED_DIR = WORK_ROOT / "output" / "processed"
ALIGNMENT_DIR = WORK_ROOT / "output" / "alignment"

PREPARED_FILES = {
    "equipment": "equipment.csv",
    "events": "events.csv",
    "maintenance": "maintenance_history.csv",
    "sensors": "sensor_readings.csv",
}


def prepared_paths() -> dict[str, Path]:
    """Chemins des quatre tables préparées au brief 1."""
    return {name: PREPARED_DIR / filename for name, filename in PREPARED_FILES.items()}


def load_prepared() -> dict[str, pd.DataFrame]:
    """Charge les quatre tables préparées au brief 1."""
    paths = prepared_paths()
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Préparation du brief 1 absente : "
            + ", ".join(missing)
            + " — rejouer `python run_pipeline_m3.py`."
        )
    return {name: pd.read_csv(path) for name, path in paths.items()}


def load_alignment() -> dict[str, pd.DataFrame]:
    """Charge le rapprochement événements / mesures produit au brief 1.

    `mesures_evenements.csv` porte une ligne par couple mesure-fenêtre ;
    `evenements_sans_mesure.csv` porte les événements qu'aucune mesure ne
    documente, avec l'indicateur `equipement_instrumente` qui distingue
    l'absence de capteur de l'absence de mesure.
    """
    paths = {
        "apparies": ALIGNMENT_DIR / "mesures_evenements.csv",
        "sans_mesure": ALIGNMENT_DIR / "evenements_sans_mesure.csv",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            "Rapprochement du brief 1 absent : "
            + ", ".join(missing)
            + " — rejouer `python run_rapprochement_m3.py`."
        )
    return {name: pd.read_csv(path) for name, path in paths.items()}


def prepared_checksums() -> dict[str, str]:
    """Empreintes du point de départ, pour que le run soit rattachable."""
    return {name: file_sha256(path) for name, path in prepared_paths().items()}
