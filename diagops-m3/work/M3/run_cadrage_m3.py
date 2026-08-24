"""Axe 1 du brief M3 — cadrer la source capteurs avant de la traiter.

Ce script ne corrige rien et ne rejette rien : il decrit. Toute regle de
qualite et tout arbitrage arrivent dans les axes suivants. Les sorties sont
ecrites dans `output/cadrage/`, les fichiers de `data_pack/` restent intacts.

Usage :
    python run_cadrage_m3.py [--output ./output/cadrage]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from contracts.schemas import ANNOUNCED_STEP_HOURS, SENSOR_UNITS
from src.data_pipeline.io import (
    data_dir,
    file_sha256,
    load_reference,
    load_sources,
    source_paths,
)
from src.data_pipeline.timeseries import (
    MEASUREMENT_KEY,
    naive_timestamps,
    observed_steps,
    series_overview,
    to_utc,
)

# Bornes du semestre annonce par la livraison, a confronter au reel.
ANNOUNCED_PERIOD = "2026-S1"
ANNOUNCED_START = pd.Timestamp("2026-01-01T00:00:00Z")
ANNOUNCED_END = pd.Timestamp("2026-07-01T00:00:00Z")  # borne haute exclue

# Grille nominale attendue pour un pas de 6 h a partir de minuit.
GRID_HOURS = {0, 6, 12, 18}


def describe_identity(sensors: pd.DataFrame, path: Path) -> dict:
    """Volumetrie et empreinte de la source recue."""
    return {
        "fichier": str(path),
        "sha256": file_sha256(path),
        "octets": path.stat().st_size,
        "lignes": int(len(sensors)),
        "colonnes": list(sensors.columns),
    }


def describe_timestamps(sensors: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """Formes d'horodatage rencontrees, fuseaux absents, alignement de grille."""
    raw = sensors["timestamp"].astype("string")
    shapes = raw.str.replace(r"\d", "9", regex=True).value_counts()
    naive = naive_timestamps(sensors["timestamp"])
    utc = to_utc(sensors["timestamp"])

    on_grid = utc.dt.hour.isin(GRID_HOURS) & (utc.dt.minute == 0) & (utc.dt.second == 0)
    off_grid = sensors.loc[~on_grid & utc.notna()].copy()
    off_grid["timestamp_utc"] = utc[off_grid.index]

    resume = {
        "formes": {forme: int(n) for forme, n in shapes.items()},
        "illisibles": int(utc.isna().sum()),
        "sans_fuseau": int(naive.sum()),
        "series_sans_fuseau": sorted(
            {
                f"{eq} / {sensor}"
                for eq, sensor in zip(
                    sensors.loc[naive, "equipment_id"],
                    sensors.loc[naive, "sensor_name"],
                )
            }
        ),
        "hors_grille": int(len(off_grid)),
        "series_hors_grille": sorted(
            {
                f"{eq} / {sensor}"
                for eq, sensor in zip(
                    off_grid["equipment_id"], off_grid["sensor_name"]
                )
            }
        ),
        "heures_hors_grille": sorted(
            off_grid["timestamp_utc"].dt.hour.unique().tolist()
        ),
    }
    return resume, off_grid


def describe_period(sensors: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """Periode reellement couverte, confrontee au semestre annonce."""
    utc = to_utc(sensors["timestamp"])
    frame = sensors.assign(timestamp_utc=utc)
    outside = frame[
        (frame.timestamp_utc < ANNOUNCED_START)
        | (frame.timestamp_utc >= ANNOUNCED_END)
    ]

    # L'etiquette `period` peut contredire la date : ce sont deux defauts distincts.
    mislabelled = frame[frame["period"] != ANNOUNCED_PERIOD].copy()
    mislabelled_in_range = mislabelled[
        (mislabelled.timestamp_utc >= ANNOUNCED_START)
        & (mislabelled.timestamp_utc < ANNOUNCED_END)
    ]

    resume = {
        "annoncee": ANNOUNCED_PERIOD,
        "premiere_mesure": str(utc.min()),
        "derniere_mesure": str(utc.max()),
        "etendue_jours": round((utc.max() - utc.min()).total_seconds() / 86400, 2),
        "par_mois": {
            str(mois): int(n)
            for mois, n in utc.dt.strftime("%Y-%m").value_counts().sort_index().items()
        },
        "hors_bornes": int(len(outside)),
        "hors_bornes_avant": int((frame.timestamp_utc < ANNOUNCED_START).sum()),
        "hors_bornes_apres": int((frame.timestamp_utc >= ANNOUNCED_END).sum()),
        "etiquette_period_autre": {
            valeur: int(n) for valeur, n in mislabelled["period"].value_counts().items()
        },
        "etiquette_fausse_mais_date_dans_S1": int(len(mislabelled_in_range)),
        "equipements_etiquette_fausse": sorted(set(mislabelled["equipment_id"])),
    }
    return resume, outside


def describe_sampling(
    sensors: pd.DataFrame, outside: pd.DataFrame
) -> tuple[dict, pd.DataFrame]:
    """Pas observe, ecarts, et origine reelle des interruptions.

    Une mesure isolee hors du semestre cree mecaniquement un faux trou jusqu'au
    demarrage de la serie. Les compter comme des pannes de capteur serait une
    erreur : on distingue les deux.
    """
    steps = observed_steps(sensors)
    counts = steps.value_counts().sort_index()

    frame = sensors.assign(timestamp_utc=to_utc(sensors["timestamp"]))
    frame = frame.dropna(subset=["timestamp_utc"]).sort_values(
        ["equipment_id", "sensor_name", "timestamp_utc"]
    )
    grouped = frame.groupby(["equipment_id", "sensor_name"], observed=True)
    delta = grouped["timestamp_utc"].diff()
    previous = grouped["timestamp_utc"].shift()

    gaps = frame[delta > pd.Timedelta(hours=ANNOUNCED_STEP_HOURS)].copy()
    gaps["ecart_heures"] = delta[gaps.index].dt.total_seconds() / 3600
    gaps["mesure_precedente"] = previous[gaps.index]
    gaps["mesures_manquantes"] = (
        (gaps["ecart_heures"] / ANNOUNCED_STEP_HOURS - 1).round().astype(int)
    )

    # Le trou est un artefact si l'une des deux mesures qui le bordent est hors
    # bornes. Ne tester que la precedente ne capte que les mesures isolees en
    # debut de serie (decembre) et laisse passer celles de fin (juillet), ou
    # c'est la ligne de reprise qui est l'anomalie.
    isolees = set(
        zip(
            outside["equipment_id"],
            outside["sensor_name"],
            to_utc(outside["timestamp"]),
        )
    )
    gaps["origine"] = [
        "artefact_mesure_isolee"
        if (eq, sensor, prev) in isolees or (eq, sensor, current) in isolees
        else "interruption_reelle"
        for eq, sensor, prev, current in zip(
            gaps["equipment_id"],
            gaps["sensor_name"],
            gaps["mesure_precedente"],
            gaps["timestamp_utc"],
        )
    ]

    reelles = gaps[gaps["origine"] == "interruption_reelle"]
    total = int(steps.notna().sum())
    nominal = int((steps == ANNOUNCED_STEP_HOURS).sum())
    resume = {
        "pas_annonce_heures": ANNOUNCED_STEP_HOURS,
        "ecarts_mesures": total,
        "ecarts_au_pas_nominal": nominal,
        "part_au_pas_nominal": round(100 * nominal / total, 4),
        "ecarts_nuls_doublons_de_cle": int((steps == 0).sum()),
        "ecarts_deviants": total - nominal,
        "trous": int(len(gaps)),
        "trous_artefacts": int((gaps["origine"] == "artefact_mesure_isolee").sum()),
        "trous_reels": int(len(reelles)),
        "mesures_manquantes_trous_reels": int(reelles["mesures_manquantes"].sum()),
        "ecart_max_heures": float(steps.max()),
        "distribution_ecarts": {f"{h:g} h": int(n) for h, n in counts.items()},
    }
    return resume, gaps


def describe_units(sensors: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """Coherence entre `sensor_name`, `unit` et le contrat annonce."""
    pairs = (
        sensors.groupby(["sensor_name", "unit"], observed=True)
        .size()
        .reset_index(name="lignes")
    )
    pairs["nom_normalise"] = pairs["sensor_name"].str.strip().str.lower()
    pairs["unite_attendue"] = pairs["nom_normalise"].map(SENSOR_UNITS)
    pairs["conforme"] = pairs["unit"] == pairs["unite_attendue"]
    pairs["nom_non_normalise"] = pairs["sensor_name"] != pairs["nom_normalise"]

    normalized = sensors["sensor_name"].str.strip().str.lower()
    values = pd.to_numeric(sensors["value"], errors="coerce")
    resume = {
        "capteurs_distincts_bruts": int(sensors["sensor_name"].nunique()),
        "capteurs_distincts_normalises": int(normalized.nunique()),
        "noms_non_normalises": {
            nom: int(n)
            for nom, n in sensors.loc[
                sensors["sensor_name"] != normalized, "sensor_name"
            ]
            .value_counts()
            .items()
        },
        "unites_distinctes": int(sensors["unit"].nunique()),
        "lignes_unite_non_conforme": int(pairs.loc[~pairs["conforme"], "lignes"].sum()),
        "couples_non_conformes": {
            f"{row.sensor_name!r} en {row.unit!r} (attendu {row.unite_attendue!r})": int(
                row.lignes
            )
            for row in pairs[~pairs["conforme"]].itertuples(index=False)
        },
        "valeurs_non_numeriques": int(values.isna().sum()),
        "valeurs_vides": int(
            (sensors["value"].astype("string").fillna("") == "").sum()
        ),
    }
    return resume, pairs


def describe_key(sensors: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """Unicite de la cle logique : doublon strict contre valeur divergente."""
    # `load_sources` laisse pandas convertir les cellules vides en NA : les 40
    # `value` vides deviennent NAType. On les rend explicites avant de composer
    # une cle textuelle, sinon le join echoue et l'information disparait.
    key = (
        sensors[list(MEASUREMENT_KEY)]
        .astype("string")
        .fillna("")
        .agg("|".join, axis=1)
    )
    duplicated_key = key.duplicated(keep=False)

    full = sensors.astype("string").fillna("").agg("|".join, axis=1)
    duplicated_full = full.duplicated(keep=False)

    divergent_mask = duplicated_key & ~duplicated_full
    detail = sensors.loc[duplicated_key].copy()
    detail["cle_logique"] = key[duplicated_key]
    detail["nature"] = [
        "doublon_strict" if strict else "valeur_divergente"
        for strict in duplicated_full[duplicated_key]
    ]
    detail = detail.sort_values(["cle_logique"])

    resume = {
        "cle_logique": list(MEASUREMENT_KEY),
        "lignes_en_cle_dupliquee": int(duplicated_key.sum()),
        "cles_dupliquees": int(key[duplicated_key].nunique()),
        "lignes_doublon_strict": int(duplicated_full[duplicated_key].sum()),
        "cles_doublon_strict": int(key[duplicated_key & duplicated_full].nunique()),
        "lignes_valeur_divergente": int(divergent_mask.sum()),
        "cles_valeur_divergente": int(key[divergent_mask].nunique()),
    }
    return resume, detail


def describe_coverage(
    sensors: pd.DataFrame, sources: dict, reference: dict
) -> tuple[dict, pd.DataFrame]:
    """Couverture instrumentale, et equipements mesures absents du parc."""
    measured = set(sensors["equipment_id"])
    raw_park = set(sources["equipment"]["equipment_id"])
    ref_park = set(reference["equipment"]["equipment_id"])

    known = measured & ref_park
    park = reference["equipment"]
    park = park.assign(instrumente=park["equipment_id"].isin(measured))

    # Question 3 du brief : la couverture n'est pas homogene. Un taux global de
    # 8,65 % masque des angles morts entiers, qui bornent ce que M4 pourra dire.
    ventilation = {}
    for axis in ("site_id", "equipment_type", "criticality"):
        table = (
            park.groupby(axis, observed=True)["instrumente"]
            .agg(parc="size", instrumentes="sum")
            .reset_index()
        )
        table["taux_pct"] = (100 * table["instrumentes"] / table["parc"]).round(2)
        ventilation[axis] = {
            str(getattr(row, axis)): {
                "parc": int(row.parc),
                "instrumentes": int(row.instrumentes),
                "taux_pct": float(row.taux_pct),
            }
            for row in table.itertuples(index=False)
        }
        ventilation[f"{axis}_sans_aucune_mesure"] = sorted(
            str(getattr(row, axis))
            for row in table.itertuples(index=False)
            if row.instrumentes == 0
        )

    resume = {
        "ventilation": ventilation,
        "base_retenue": "reference_runs/m2_for_m3/processed/equipment.csv",
        "parc_reference": len(ref_park),
        "parc_brut": len(raw_park),
        "ecart_reference_vs_brut": {
            "retires": sorted(raw_park - ref_park),
            "ajoutes": sorted(ref_park - raw_park),
        },
        "equipements_mesures": len(measured),
        "instrumentes_connus": len(known),
        "inconnus_du_parc": sorted(measured - ref_park),
        "non_instrumentes": len(ref_park - measured),
        "taux_instrumentation_pct": round(100 * len(known) / len(ref_park), 2),
    }
    return resume, park


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/cadrage"))
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)

    sources = load_sources()
    reference = load_reference()
    sensors = sources["sensors"]
    path = source_paths()["sensors"]

    identity = describe_identity(sensors, path)
    timestamps, off_grid = describe_timestamps(sensors)
    period, outside = describe_period(sensors)
    sampling, gaps = describe_sampling(sensors, outside)
    units, unit_pairs = describe_units(sensors)
    key, key_detail = describe_key(sensors)
    coverage, park = describe_coverage(sensors, sources, reference)

    overview = series_overview(sensors)

    overview.to_csv(out / "series_overview.csv", index=False)
    off_grid.to_csv(out / "horodatages_hors_grille.csv", index=False)
    outside.to_csv(out / "mesures_hors_bornes.csv", index=False)
    gaps.to_csv(out / "interruptions.csv", index=False)
    unit_pairs.to_csv(out / "couples_capteur_unite.csv", index=False)
    key_detail.to_csv(out / "cles_dupliquees.csv", index=False)
    park.to_csv(out / "couverture_parc.csv", index=False)

    resume = {
        "source_donnees": str(data_dir()),
        "identite": identity,
        "series": {
            "nombre": int(len(overview)),
            "longueur_min": int(overview["measurements"].min()),
            "longueur_mediane": int(overview["measurements"].median()),
            "longueur_max": int(overview["measurements"].max()),
            "capteurs_par_equipement": {
                str(k): int(v)
                for k, v in sensors.groupby("equipment_id")["sensor_name"]
                .nunique()
                .value_counts()
                .items()
            },
        },
        "horodatage": timestamps,
        "periode": period,
        "echantillonnage": sampling,
        "unites": units,
        "cle_logique": key,
        "couverture": coverage,
    }
    (out / "cadrage.json").write_text(
        json.dumps(resume, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(json.dumps(resume, indent=2, ensure_ascii=False))
    print(f"\nSorties ecrites dans {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
