"""Axe 2 du brief M3 — diagnostic propre a une serie temporelle.

Le cadrage (axe 1, `run_cadrage_m3.py`) a traite l'unicite de la cle, les
formats d'horodatage, l'alignement de grille, la continuite et les unites. Ce
script prend la suite sur ce qu'une serie temporelle seule peut reveler :

- plages de valeurs par capteur et valeurs sentinelles ;
- comportements de capteur : valeur figee, derive lente, saut brutal.

Comme le cadrage, il **decrit et ne decide rien**. Il produit des *candidats*.
Trancher entre erreur de mesure et phenomene reel est l'objet de l'axe 3, et
exige de croiser avec `events.csv` et `maintenance_history.csv`.

Usage :
    python run_audit_temporel_m3.py [--output ./output/audit]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from contracts.schemas import SENSOR_UNITS
from src.data_pipeline.io import load_sources
from src.data_pipeline.timeseries import to_utc

# Conversions vers l'unite de reference du capteur. Elles rendent les valeurs
# comparables entre elles ; elles ne corrigent pas le fichier recu, qui reste
# intact. Chaque ligne convertie est tracee dans la sortie.
CONVERSIONS = {
    ("pressure_bar", "kPa"): ("bar", lambda v: v / 100.0),
    ("temperature_c", "K"): ("°C", lambda v: v - 273.15),
}

# Un capteur qui repete exactement la meme valeur a deux decimales pendant N
# releves consecutifs est suspect. Le seuil est un choix : 8 releves au pas de
# 6 h font 48 h de valeur strictement constante.
FROZEN_RUN_THRESHOLD = 8

# Un saut est signale quand l'ecart avec la mesure precedente depasse ce nombre
# d'ecarts-types des ecarts de la serie. Choix conservateur : on veut peu de
# candidats, chacun examinable a la main.
JUMP_SIGMA = 8.0


def normalise_units(sensors: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Ramene chaque mesure a l'unite de reference de son capteur.

    Le nom de capteur est normalise (casse et espaces) avant conversion : sans
    cela, les 40 lignes `TEMPERATURE_C ` echapperaient a tout controle de plage.
    """
    frame = sensors.copy()
    frame["sensor"] = frame["sensor_name"].str.strip().str.lower()
    frame["timestamp_utc"] = to_utc(frame["timestamp"])
    frame["value_num"] = pd.to_numeric(frame["value"], errors="coerce")
    frame["value_ref"] = frame["value_num"]
    frame["unit_ref"] = frame["sensor"].map(SENSOR_UNITS)
    frame["converti"] = False

    journal = {}
    for (sensor, unit), (target, convert) in CONVERSIONS.items():
        mask = (frame["sensor"] == sensor) & (frame["unit"] == unit)
        if not mask.any():
            continue
        avant = frame.loc[mask, "value_num"]
        frame.loc[mask, "value_ref"] = convert(avant)
        frame.loc[mask, "converti"] = True
        journal[f"{sensor} : {unit} -> {target}"] = {
            "lignes": int(mask.sum()),
            "avant_min": round(float(avant.min()), 2),
            "avant_max": round(float(avant.max()), 2),
            "apres_min": round(float(frame.loc[mask, "value_ref"].min()), 2),
            "apres_max": round(float(frame.loc[mask, "value_ref"].max()), 2),
        }

    # Les unites restant non conformes apres conversion sont un angle mort a
    # signaler, pas a ignorer silencieusement.
    reste = frame[(frame["unit"] != frame["unit_ref"]) & ~frame["converti"]]
    journal["unites_non_conformes_non_converties"] = {
        f"{row.sensor} en {row.unit}": int(n)
        for (row, n) in [
            (r, c)
            for r, c in zip(
                reste.drop_duplicates(["sensor", "unit"]).itertuples(index=False),
                reste.groupby(["sensor", "unit"], observed=True).size().tolist(),
            )
        ]
    } if not reste.empty else {}
    return frame, journal


def describe_ranges(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Distribution par capteur, apres normalisation des unites."""
    stats = (
        frame.dropna(subset=["value_ref"])
        .groupby("sensor", observed=True)["value_ref"]
        .agg(
            mesures="size",
            minimum="min",
            p01=lambda s: s.quantile(0.01),
            p25=lambda s: s.quantile(0.25),
            mediane="median",
            p75=lambda s: s.quantile(0.75),
            p99=lambda s: s.quantile(0.99),
            maximum="max",
            moyenne="mean",
            ecart_type="std",
        )
        .round(3)
        .reset_index()
    )
    stats["unite"] = stats["sensor"].map(SENSOR_UNITS)
    resume = {
        row.sensor: {
            "unite": row.unite,
            "min": float(row.minimum),
            "p01": float(row.p01),
            "median": float(row.mediane),
            "p99": float(row.p99),
            "max": float(row.maximum),
            "ecart_type": float(row.ecart_type),
        }
        for row in stats.itertuples(index=False)
    }
    return stats, resume


def find_sentinels(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, dict]:
    """Valeurs qui codent une absence de mesure plutot qu'une mesure.

    Critere retenu : **une valeur negative est physiquement impossible** pour
    les cinq grandeurs de ce corpus (vibration, temperature de procede en °C
    autour de 57, pression, courant, vitesse de rotation). C'est un critere
    physique, pas une liste de codes devinee.

    Une premiere version cherchait aussi les valeurs « anormalement repetees »
    (>= 20 occurrences). Ce critere est inutilisable ici : `vibration_mm_s`
    varie entre 2 et 4 avec deux decimales, donc chaque valeur revient
    naturellement une centaine de fois. Il produisait des dizaines de faux
    positifs et aucun vrai. Il est remplace par le controle des valeurs rondes
    classiques, qui ne coute rien et ne se declenche que si elles existent.
    """
    usable = frame.dropna(subset=["value_ref"])
    negatives = usable[usable["value_ref"] < 0]

    # Codes usuels d'absence, verifies un par un plutot que supposes presents.
    codes = {}
    for candidate in (0.0, -1.0, 999.0, -999.0, 9999.0, -9999.0):
        count = int((usable["value_ref"] == candidate).sum())
        if count:
            codes[f"{candidate:g}"] = count

    detail = (
        negatives.groupby(["sensor", "value_ref"], observed=True)
        .size()
        .reset_index(name="occurrences")
        .sort_values("occurrences", ascending=False)
    )

    # Le masque porte sur le frame complet : il sert a exclure ces lignes des
    # controles de comportement, ou un -999 fabriquerait un faux saut geant.
    mask = frame["value_ref"].notna() & (frame["value_ref"] < 0)

    resume = {
        "critere": "valeur negative — physiquement impossible pour ces cinq grandeurs",
        "lignes_sentinelles": int(mask.sum()),
        "valeurs_rencontrees": {
            f"{value:g}": int(n)
            for value, n in negatives["value_ref"].value_counts().items()
        },
        "codes_usuels_presents": codes,
        "par_capteur": {
            str(k): int(v) for k, v in negatives["sensor"].value_counts().items()
        },
        "equipements_touches": sorted(set(negatives["equipment_id"])),
        "valeurs_manquantes_hors_sentinelles": int(frame["value_ref"].isna().sum()),
        "effet_sur_les_statistiques": {
            "ecart_type_avec_sentinelles": {
                str(sensor): round(float(group["value_ref"].std()), 3)
                for sensor, group in usable.groupby("sensor", observed=True)
            },
            "ecart_type_sans_sentinelles": {
                str(sensor): round(float(group["value_ref"].std()), 3)
                for sensor, group in usable[usable["value_ref"] >= 0].groupby(
                    "sensor", observed=True
                )
            },
        },
    }
    return detail, mask, resume


def find_frozen(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Series presentant une valeur strictement constante sur plusieurs releves."""
    working = frame.dropna(subset=["value_ref", "timestamp_utc"]).sort_values(
        ["equipment_id", "sensor", "timestamp_utc"]
    )
    # Un identifiant de palier change des que la valeur change ou que la serie
    # change : les paliers ne debordent pas d'une serie a l'autre.
    change = (
        (working["value_ref"] != working["value_ref"].shift())
        | (working["equipment_id"] != working["equipment_id"].shift())
        | (working["sensor"] != working["sensor"].shift())
    )
    working["palier"] = change.cumsum()

    runs = (
        working.groupby(["equipment_id", "sensor", "palier"], observed=True)
        .agg(
            valeur=("value_ref", "first"),
            releves=("value_ref", "size"),
            debut=("timestamp_utc", "min"),
            fin=("timestamp_utc", "max"),
        )
        .reset_index()
    )
    frozen = runs[runs["releves"] >= FROZEN_RUN_THRESHOLD].sort_values(
        "releves", ascending=False
    )
    frozen = frozen.assign(
        duree_heures=(frozen["fin"] - frozen["debut"]).dt.total_seconds() / 3600
    )

    resume = {
        "seuil_releves_consecutifs": FROZEN_RUN_THRESHOLD,
        "paliers_detectes": int(len(frozen)),
        "series_concernees": sorted(
            {f"{row.equipment_id} / {row.sensor}" for row in frozen.itertuples(index=False)}
        ),
        "plus_long_palier": (
            {
                "serie": f"{frozen.iloc[0].equipment_id} / {frozen.iloc[0].sensor}",
                "valeur": float(frozen.iloc[0].valeur),
                "releves": int(frozen.iloc[0].releves),
                "duree_heures": float(frozen.iloc[0].duree_heures),
                "debut": str(frozen.iloc[0].debut),
                "fin": str(frozen.iloc[0].fin),
            }
            if not frozen.empty
            else None
        ),
    }
    return frozen, resume


def find_drift(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Derive lente : tendance monotone marquee sur la duree d'une serie.

    On regresse la valeur sur le temps, serie par serie. La pente seule ne dit
    rien : une pente forte sur une serie tres bruitee est du bruit. On la
    rapporte donc a la dispersion de la serie via le coefficient de correlation.
    """
    working = frame.dropna(subset=["value_ref", "timestamp_utc"])
    lignes = []
    for (equipment, sensor), group in working.groupby(
        ["equipment_id", "sensor"], observed=True
    ):
        if len(group) < 30:
            continue
        group = group.sort_values("timestamp_utc")
        jours = (
            group["timestamp_utc"] - group["timestamp_utc"].min()
        ).dt.total_seconds() / 86400
        valeurs = group["value_ref"].to_numpy()
        if np.std(valeurs) == 0 or np.std(jours) == 0:
            continue
        pente, intercept = np.polyfit(jours, valeurs, 1)
        correlation = float(np.corrcoef(jours, valeurs)[0, 1])
        lignes.append(
            {
                "equipment_id": equipment,
                "sensor": sensor,
                "releves": len(group),
                "pente_par_jour": round(float(pente), 5),
                "amplitude_totale": round(float(pente) * float(jours.max()), 3),
                "correlation_temps": round(correlation, 4),
                "ecart_type": round(float(np.std(valeurs)), 3),
                "debut_moyenne_10pct": round(
                    float(valeurs[: max(1, len(valeurs) // 10)].mean()), 3
                ),
                "fin_moyenne_10pct": round(
                    float(valeurs[-max(1, len(valeurs) // 10) :].mean()), 3
                ),
            }
        )

    table = pd.DataFrame(lignes).sort_values(
        "correlation_temps", key=abs, ascending=False
    )
    absolute = table["correlation_temps"].abs()

    # Seuil informe par la distribution, pas choisi d'avance.
    #
    # Une premiere version exigeait |correlation| >= 0,7, en raisonnant « au-dela
    # de 0,7 la tendance explique l'essentiel de la variation ». Ce seuil ne
    # trouvait AUCUN candidat, alors que la DATA_CARD annonce une derive lente
    # injectee. Il etait donc faux : une derive lente noyee dans du bruit de
    # capteur produit une correlation modeste, pas une correlation forte.
    #
    # La distribution observee sur les 71 series est sans ambiguite : mediane
    # 0,022, troisieme quartile 0,037, et deux valeurs hautes seulement — 0,103
    # puis 0,505. Le seuil de 0,3 separe une population homogene d'un cas isole ;
    # il ne depend d'aucune hypothese sur l'amplitude de la derive cherchee.
    seuil = 0.3
    candidats = table[absolute >= seuil]
    resume = {
        "seuil_correlation": seuil,
        "justification_seuil": (
            "distribution des 71 series : mediane 0,022, p75 0,037, "
            "deuxieme plus forte correlation 0,103. Le seuil isole ce qui sort "
            "de la population, il n'est pas fixe a priori."
        ),
        "distribution_correlations": {
            "mediane": round(float(absolute.median()), 4),
            "p75": round(float(absolute.quantile(0.75)), 4),
            "p95": round(float(absolute.quantile(0.95)), 4),
            "max": round(float(absolute.max()), 4),
        },
        "series_evaluees": int(len(table)),
        "candidats": int(len(candidats)),
        "detail": [
            {
                "serie": f"{row.equipment_id} / {row.sensor}",
                "correlation_temps": row.correlation_temps,
                "pente_par_jour": row.pente_par_jour,
                "amplitude_totale": row.amplitude_totale,
                "debut_moyenne_10pct": row.debut_moyenne_10pct,
                "fin_moyenne_10pct": row.fin_moyenne_10pct,
            }
            for row in candidats.itertuples(index=False)
        ],
    }
    return table, resume


def find_jumps(frame: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Sauts brutaux : ecart avec la mesure precedente hors de proportion."""
    working = frame.dropna(subset=["value_ref", "timestamp_utc"]).sort_values(
        ["equipment_id", "sensor", "timestamp_utc"]
    )
    grouped = working.groupby(["equipment_id", "sensor"], observed=True)
    working = working.assign(
        ecart=grouped["value_ref"].diff(),
        precedent=grouped["value_ref"].shift(),
        instant_precedent=grouped["timestamp_utc"].shift(),
    )
    sigma = grouped["value_ref"].transform(lambda s: s.diff().std())
    working["ecart_sigma"] = (working["ecart"] / sigma).abs()

    jumps = working[working["ecart_sigma"] >= JUMP_SIGMA].sort_values(
        "ecart_sigma", ascending=False
    )
    resume = {
        "seuil_sigma": JUMP_SIGMA,
        "sauts_detectes": int(len(jumps)),
        "series_concernees": sorted(
            {f"{row.equipment_id} / {row.sensor}" for row in jumps.itertuples(index=False)}
        ),
        "detail": [
            {
                "serie": f"{row.equipment_id} / {row.sensor}",
                "instant": str(row.timestamp_utc),
                "precedent": round(float(row.precedent), 2),
                "valeur": round(float(row.value_ref), 2),
                "ecart_sigma": round(float(row.ecart_sigma), 1),
            }
            for row in jumps.head(20).itertuples(index=False)
        ],
    }
    return jumps, resume


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("output/audit"))
    args = parser.parse_args()
    out = args.output
    out.mkdir(parents=True, exist_ok=True)

    sensors = load_sources()["sensors"]
    frame, conversions = normalise_units(sensors)

    # Les sentinelles se traitent EN PREMIER : laissees en place, elles gonflent
    # les ecarts-types, ecrasent les plages et fabriquent un faux saut brutal a
    # chaque occurrence. Tous les controles suivants portent sur `mesures`.
    sentinels, sentinel_mask, sentinels_resume = find_sentinels(frame)
    mesures = frame[~sentinel_mask]

    ranges, ranges_resume = describe_ranges(mesures)
    frozen, frozen_resume = find_frozen(mesures)
    drift, drift_resume = find_drift(mesures)
    jumps, jumps_resume = find_jumps(mesures)

    ranges.to_csv(out / "plages_par_capteur.csv", index=False)
    sentinels.to_csv(out / "valeurs_sentinelles.csv", index=False)
    frozen.to_csv(out / "capteurs_figes.csv", index=False)
    drift.to_csv(out / "tendances_series.csv", index=False)
    jumps.to_csv(out / "sauts_brutaux.csv", index=False)

    resume = {
        "normalisation_unites": conversions,
        "sentinelles": sentinels_resume,
        "lignes_retenues_pour_les_controles": int(len(mesures)),
        "plages_par_capteur": ranges_resume,
        "capteurs_figes": frozen_resume,
        "derive_lente": drift_resume,
        "sauts_brutaux": jumps_resume,
    }
    (out / "audit_temporel.json").write_text(
        json.dumps(resume, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(resume, indent=2, ensure_ascii=False))
    print(f"\nSorties ecrites dans {out.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
