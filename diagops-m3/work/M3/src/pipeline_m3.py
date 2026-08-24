"""Pipeline multi-source M3 — regles, quarantaine unifiee, tables preparees.

Le module porte la logique ; `run_pipeline_m3.py` l'execute. Cette separation
existe pour que les tests appellent les regles une par une sur des cas
construits, sans rejouer toute la chaine.

Principes tenus :

- les fichiers recus ne sont jamais modifies ;
- toute ligne ecartee ou corrigee laisse une trace en quarantaine, au format M2 ;
- `row_identifier` est construit sur les valeurs **recues**, pas normalisees :
  il sert a retrouver la ligne d'origine, pas a la corriger ;
- les trois tables M2 traversent la pipeline **sans transformation**, et un
  controle le verifie au lieu de l'affirmer.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from contracts.schemas import SENSOR_UNITS
from src.data_pipeline.quarantine import (
    QUARANTINE_COLUMNS,
    empty_quarantine,
    measurement_identifier,
)
from src.data_pipeline.rules import Rule, RuleRegistry
from src.data_pipeline.timeseries import to_utc

SOURCE_FILE = "sensor_readings.csv"

# Bornes du semestre annonce.
PERIOD_LABEL = "2026-S1"
PERIOD_START = pd.Timestamp("2026-01-01T00:00:00Z")
PERIOD_END = pd.Timestamp("2026-07-01T00:00:00Z")

# Conversions vers l'unite de reference du capteur.
UNIT_CONVERSIONS = {
    ("pressure_bar", "kPa"): ("bar", lambda v: v / 100.0),
    ("temperature_c", "K"): ("°C", lambda v: v - 273.15),
}

GRID_HOURS = {0, 6, 12, 18}
NOMINAL_STEP_HOURS = 6
FROZEN_RUN_THRESHOLD = 8
DRIFT_CORRELATION_THRESHOLD = 0.30
JUMP_SIGMA = 8.0

# Amplitude minimale d'un saut, en fraction du niveau median de la serie. Evite
# qu'un ecart statistiquement rare mais physiquement negligeable soit signale.
JUMP_MIN_RELATIVE = 0.10

# Depassement de plage : ecart a la mediane exprime en ecarts absolus medians
# (MAD). Critere robuste, insensible aux valeurs extremes qu'il cherche. Il
# remplace un seuil au 99e centile, qui rejetait 1 % des lignes par
# construction sans rien detecter.
PLAGE_MAD_FACTOR = 8.0


# --------------------------------------------------------------------------- #
# Registre
# --------------------------------------------------------------------------- #

def build_registry() -> RuleRegistry:
    """Registre complet : les 19 regles heritees de M2 et les 15 regles M3.

    Statuts des regles M2 : le travail part de l'etat prepare de reference
    (`reference_runs/m2_for_m3/`), ou ces regles ont deja ete appliquees. Aucune
    n'est modifiee ni abandonnee ici. Les trois regles d'unicite sont marquees
    `etendue` : leur decision — doublon exact supprime, conflit exclu — est
    reprise telle quelle sur la cle composite des mesures, qui n'existait pas
    en M2.
    """
    registry = RuleRegistry()

    inherited = [
        ("R-EQ-001", "equipment", "`equipment_id` unique", True),
        ("R-EQ-002", "equipment", "`criticality` dans le domaine ferme", False),
        ("R-EQ-003", "equipment", "`equipment_type` normalise", False),
        ("R-EQ-004", "equipment", "`rated_power_kw` strictement positive", False),
        ("R-EQ-005", "equipment", "`commissioning_date` anterieure a la fin de periode", False),
        ("R-EQ-006", "equipment", "champs descriptifs renseignes", False),
        ("R-EVT-001", "events", "`event_id` unique", True),
        ("R-EVT-002", "events", "`severity` dans le domaine ferme", False),
        ("R-EVT-003", "events", "`event_type` normalise et dans le domaine", False),
        ("R-EVT-004", "events", "`end_at` posterieure a `start_at`", False),
        ("R-EVT-005", "events", "`equipment_id` present dans la table preparee", False),
        ("R-MNT-001", "maintenance", "`maintenance_id` unique", True),
        ("R-MNT-002", "maintenance", "`event_id` present dans la table preparee", False),
        ("R-MNT-003", "maintenance", "`equipment_id` present dans la table preparee", False),
        ("R-MNT-004", "maintenance", "`closed_at` posterieure a `opened_at`", False),
        ("R-MNT-005", "maintenance", "`downtime_minutes` positive et plausible", False),
        ("R-MNT-006", "maintenance", "`parts_cost_eur` positive", False),
        ("R-MNT-007", "maintenance", "`intervention_type` normalise et dans le domaine", False),
        ("R-MNT-008", "maintenance", "absence d'information personnelle dans les notes", False),
    ]
    for rule_id, table, description, extended in inherited:
        registry.add(
            Rule(
                rule_id=rule_id,
                table=table,
                status="etendue" if extended else "conservee",
                description=description,
                origin="M2",
                justification=(
                    "Decision reprise a l'identique sur la cle composite des "
                    "mesures (voir R-SEN-001)."
                    if extended
                    else ""
                ),
            )
        )

    added = [
        ("R-SEN-001", "Cle logique `equipment_id + timestamp + sensor_name` unique"),
        ("R-SEN-002", "`timestamp` lisible ; fuseau explicite ou hypothese UTC tracee"),
        ("R-SEN-003", "Horodatage aligne sur la grille nominale 00/06/12/18"),
        ("R-SEN-004", "Continuite de l'echantillonnage au pas nominal de 6 h"),
        ("R-SEN-005", "`sensor_name` normalise et dans le domaine des 5 capteurs"),
        ("R-SEN-006", "`unit` conforme a l'unite de reference du capteur"),
        ("R-SEN-007", "`value` renseignee et numerique"),
        ("R-SEN-008", "`value` non sentinelle — une valeur negative est impossible"),
        ("R-SEN-009", "`value` dans la plage observee du capteur"),
        ("R-SEN-010", "Capteur non fige — valeur strictement constante prolongee"),
        ("R-SEN-011", "Absence de derive monotone marquee sur la serie"),
        ("R-SEN-012", "Absence de saut brutal hors de proportion"),
        ("R-SEN-013", "`equipment_id` present dans le parc prepare"),
        ("R-SEN-014", "Mesure comprise dans la periode annoncee"),
        ("R-SEN-015", "Etiquette `period` coherente avec la date de la mesure"),
    ]
    for rule_id, description in added:
        registry.add(
            Rule(rule_id=rule_id, table="sensors", status="nouvelle", description=description)
        )
    return registry


# --------------------------------------------------------------------------- #
# Quarantaine
# --------------------------------------------------------------------------- #

@dataclass
class Collector:
    """Accumule les rejets au format M2 et les rend sous forme de table."""

    records: list[dict]

    def __init__(self) -> None:
        self.records = []

    def add(
        self,
        frame: pd.DataFrame,
        rule_id: str,
        column: str,
        reason: str,
        decision: str,
        observed: pd.Series | None = None,
    ) -> None:
        if frame.empty:
            return
        identifiers = measurement_identifier(frame)
        values = observed if observed is not None else frame.get(column, pd.Series(dtype=object))
        for index, identifier in identifiers.items():
            self.records.append(
                {
                    "source_file": SOURCE_FILE,
                    "row_identifier": identifier,
                    "rule_id": rule_id,
                    "column": column,
                    "observed_value": values.get(index, ""),
                    "reason": reason,
                    "decision": decision,
                }
            )

    def to_frame(self) -> pd.DataFrame:
        if not self.records:
            return empty_quarantine()
        return pd.DataFrame(self.records).loc[:, QUARANTINE_COLUMNS]


# --------------------------------------------------------------------------- #
# Regles capteurs
# --------------------------------------------------------------------------- #

def prepare_sensors(
    sensors: pd.DataFrame, park: set[str]
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Applique les 15 regles M3 et retourne (mesures preparees, quarantaine, stats).

    L'ordre compte et n'est pas negociable sur trois points :

    1. `sensor_name` est normalise en premier — sinon les 40 lignes
       `TEMPERATURE_C ` echappent a tout controle d'unite et de plage ;
    2. les sentinelles sont neutralisees avant les controles de comportement —
       sinon chaque `-999` fabrique un faux saut brutal ;
    3. les exclusions de lignes viennent apres les normalisations, pour que la
       quarantaine porte la valeur telle qu'elle a ete recue.
    """
    quarantine = Collector()
    frame = sensors.copy()
    stats: dict[str, int] = {"lignes_recues": len(frame)}

    # Cle et identifiant construits sur les valeurs RECUES, avant toute
    # normalisation : ils doivent pointer la ligne du fichier d'origine.
    frame["row_identifier"] = measurement_identifier(frame)
    received_key = (
        frame[["equipment_id", "timestamp", "sensor_name"]]
        .astype("string")
        .fillna("")
        .agg("|".join, axis=1)
    )

    # --- R-SEN-005 : nom de capteur -----------------------------------------
    normalised_name = frame["sensor_name"].str.strip().str.lower()
    renamed = frame[normalised_name != frame["sensor_name"]]
    quarantine.add(
        renamed, "R-SEN-005", "sensor_name",
        "Nom de capteur non normalise (casse ou espace)", "valeur_normalisee",
        observed=frame.loc[renamed.index, "sensor_name"],
    )
    frame["sensor_name"] = normalised_name
    stats["noms_normalises"] = len(renamed)

    unknown_sensor = frame[~frame["sensor_name"].isin(SENSOR_UNITS)]
    quarantine.add(
        unknown_sensor, "R-SEN-005", "sensor_name",
        "Capteur hors du domaine connu", "exclue",
    )
    stats["capteurs_inconnus"] = len(unknown_sensor)

    # --- R-SEN-002 : horodatage ---------------------------------------------
    text = frame["timestamp"].astype("string")
    naive = ~text.str.contains(r"(?:Z|[+-]\d{2}:?\d{2})$", regex=True, na=False) & text.notna()
    quarantine.add(
        frame[naive], "R-SEN-002", "timestamp",
        "Horodatage sans fuseau — interprete en UTC (hypothese tracee)",
        "valeur_normalisee",
    )
    frame["timestamp_utc"] = to_utc(frame["timestamp"])
    unreadable = frame[frame["timestamp_utc"].isna()]
    quarantine.add(
        unreadable, "R-SEN-002", "timestamp", "Horodatage illisible", "exclue"
    )
    stats["horodatages_sans_fuseau"] = int(naive.sum())
    stats["horodatages_illisibles"] = len(unreadable)

    # --- R-SEN-006 : unites --------------------------------------------------
    frame["value_num"] = pd.to_numeric(frame["value"], errors="coerce")
    frame["value_ref"] = frame["value_num"]
    converted_total = 0
    for (sensor, unit), (target, convert) in UNIT_CONVERSIONS.items():
        mask = (frame["sensor_name"] == sensor) & (frame["unit"] == unit)
        if not mask.any():
            continue
        quarantine.add(
            frame[mask], "R-SEN-006", "unit",
            f"Unite {unit} convertie en {target}", "valeur_normalisee",
            observed=frame.loc[mask, "unit"],
        )
        frame.loc[mask, "value_ref"] = convert(frame.loc[mask, "value_num"])
        frame.loc[mask, "unit"] = target
        converted_total += int(mask.sum())
    stats["unites_converties"] = converted_total

    expected_unit = frame["sensor_name"].map(SENSOR_UNITS)
    wrong_unit = frame[frame["unit"].notna() & (frame["unit"] != expected_unit)]
    quarantine.add(
        wrong_unit, "R-SEN-006", "unit",
        "Unite non conforme au capteur et non convertible", "exclue",
    )
    stats["unites_non_conformes_restantes"] = len(wrong_unit)

    # --- R-SEN-008 : sentinelles (AVANT les controles de comportement) -------
    sentinel = frame["value_ref"].notna() & (frame["value_ref"] < 0)
    quarantine.add(
        frame[sentinel], "R-SEN-008", "value",
        "Valeur sentinelle — negative, physiquement impossible", "champ_neutralise",
        observed=frame.loc[sentinel, "value"],
    )
    frame.loc[sentinel, "value_ref"] = np.nan
    stats["sentinelles_neutralisees"] = int(sentinel.sum())

    # --- R-SEN-007 : valeur manquante ---------------------------------------
    missing = frame["value_ref"].isna() & ~sentinel
    quarantine.add(
        frame[missing], "R-SEN-007", "value",
        "Valeur absente ou non numerique", "champ_neutralise",
        observed=frame.loc[missing, "value"],
    )
    stats["valeurs_manquantes"] = int(missing.sum())

    # --- R-SEN-015 : etiquette de periode ------------------------------------
    mislabelled = frame[frame["period"] != PERIOD_LABEL]
    quarantine.add(
        mislabelled, "R-SEN-015", "period",
        f"Etiquette de periode incoherente avec la date — normalisee en {PERIOD_LABEL}",
        "valeur_normalisee",
        observed=frame.loc[mislabelled.index, "period"],
    )
    frame["period"] = PERIOD_LABEL
    stats["etiquettes_normalisees"] = len(mislabelled)

    # --- R-SEN-014 : hors periode --------------------------------------------
    outside = frame[
        frame["timestamp_utc"].notna()
        & ((frame["timestamp_utc"] < PERIOD_START) | (frame["timestamp_utc"] >= PERIOD_END))
    ]
    quarantine.add(
        outside, "R-SEN-014", "timestamp",
        "Mesure hors de la periode annoncee — conservee et signalee",
        "conserve_signale",
    )
    stats["hors_periode"] = len(outside)

    # --- R-SEN-003 : alignement de grille ------------------------------------
    on_grid = (
        frame["timestamp_utc"].dt.hour.isin(GRID_HOURS)
        & (frame["timestamp_utc"].dt.minute == 0)
        & (frame["timestamp_utc"].dt.second == 0)
    )
    off_grid = frame[frame["timestamp_utc"].notna() & ~on_grid]
    # Signalement au niveau serie : le decalage porte sur la serie entiere, pas
    # sur chacune de ses mesures. Une ligne par serie, la raison porte le volume.
    for (equipment, sensor), group in off_grid.groupby(
        ["equipment_id", "sensor_name"], observed=True
    ):
        head = group.sort_values("timestamp_utc").head(1)
        hours = sorted(group["timestamp_utc"].dt.hour.unique().tolist())
        quarantine.add(
            head, "R-SEN-003", "timestamp",
            f"Serie decalee de la grille nominale — releves a {hours} h, "
            f"{len(group)} mesures concernees",
            "conserve_signale",
        )
    stats["lignes_hors_grille"] = len(off_grid)
    stats["series_hors_grille"] = int(
        off_grid.groupby(["equipment_id", "sensor_name"], observed=True).ngroups
    ) if not off_grid.empty else 0

    # --- R-SEN-013 : equipement inconnu du parc ------------------------------
    orphan = frame[~frame["equipment_id"].isin(park)]
    quarantine.add(
        orphan, "R-SEN-013", "equipment_id",
        "Equipement absent du parc prepare — rattachement impossible", "exclue",
        observed=frame.loc[orphan.index, "equipment_id"],
    )
    stats["lignes_equipement_inconnu"] = len(orphan)
    stats["equipements_inconnus"] = int(orphan["equipment_id"].nunique())

    # --- R-SEN-001 : unicite de la cle logique -------------------------------
    # Deux cas distincts, deux decisions distinctes. Sur une cle portant des
    # valeurs divergentes, aucune des deux lignes n'est retenue : le fichier se
    # contredit, et choisir arbitrairement introduirait une valeur fausse
    # indetectable en aval. Arbitrage acte, cf. docs/registre_regles.md.
    full = frame[["equipment_id", "timestamp", "sensor_name", "value", "unit"]] \
        .astype("string").fillna("").agg("|".join, axis=1)
    duplicated_key = received_key.duplicated(keep=False)
    duplicated_full = full.duplicated(keep=False)

    strict = duplicated_key & duplicated_full
    divergent = duplicated_key & ~duplicated_full

    # Sur un doublon strict, une seule ligne est conservee : celle qui est
    # retiree part en quarantaine.
    strict_removed = frame[strict & full.duplicated(keep="first")]
    quarantine.add(
        strict_removed, "R-SEN-001", "equipment_id",
        "Ligne strictement dupliquee", "doublon_supprime",
    )
    quarantine.add(
        frame[divergent], "R-SEN-001", "value",
        "Cle dupliquee portant des valeurs divergentes — aucune des deux retenue",
        "exclue",
        observed=frame.loc[divergent, "value"],
    )
    stats["doublons_stricts_supprimes"] = len(strict_removed)
    stats["lignes_cle_divergente_exclues"] = int(divergent.sum())

    # --- Exclusions cumulees --------------------------------------------------
    excluded = (
        frame.index.isin(unknown_sensor.index)
        | frame.index.isin(unreadable.index)
        | frame.index.isin(wrong_unit.index)
        | frame.index.isin(orphan.index)
        | divergent.to_numpy()
        | frame.index.isin(strict_removed.index)
    )
    prepared = frame[~excluded].copy()

    # --- Controles de comportement, sur les lignes retenues -------------------
    behaviour = detect_behaviours(prepared)
    for rule_id, column, reason, subset in behaviour["rejets_ligne"]:
        quarantine.add(subset, rule_id, column, reason, "conserve_signale")
    for rule_id, column, _, subset in behaviour["rejets_serie"]:
        for index, row in subset.iterrows():
            quarantine.add(
                subset.loc[[index]], rule_id, column, row["_reason"], "conserve_signale"
            )

    frozen_index = behaviour["figes"].index
    quarantine.add(
        prepared.loc[frozen_index], "R-SEN-010", "value",
        "Capteur fige — valeur strictement constante sur une duree prolongee",
        "exclue",
        observed=prepared.loc[frozen_index, "value"],
    )
    prepared = prepared.drop(index=frozen_index)
    stats.update(behaviour["stats"])
    stats["lignes_preparees"] = len(prepared)

    prepared = prepared.loc[
        :,
        [
            "equipment_id",
            "timestamp_utc",
            "sensor_name",
            "value_ref",
            "unit",
            "period",
            "row_identifier",
        ],
    ].rename(columns={"timestamp_utc": "timestamp", "value_ref": "value"})

    return prepared, quarantine.to_frame(), stats


def _series_head(frame: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    """Une ligne representative par serie, pour un signalement de niveau serie."""
    if frame.empty:
        return frame
    return frame.sort_values("timestamp_utc").groupby(group_columns, observed=True).head(1)


def detect_behaviours(frame: pd.DataFrame) -> dict:
    """Capteur fige, derive lente, saut brutal, plage et continuite.

    Deux niveaux de signalement, volontairement distincts :

    - **par ligne** — la mesure elle-meme est en cause (valeur hors plage,
      saut, reprise apres interruption) ;
    - **par serie** — c'est le comportement de la serie entiere qui est en cause
      (derive). Signaler chacune de ses 720 mesures noierait les rejets utiles
      sans rien apprendre de plus : une seule ligne porte le constat, et sa
      raison indique le volume concerne.
    """
    # La continuite se mesure sur les horodatages RECUS, avant tout retrait lie
    # a la valeur : un capteur qui renvoie une valeur vide a tout de meme emis
    # un releve. Mesurer les trous apres `dropna` fabriquait 57 fausses
    # interruptions sur les 63 detectees.
    timeline = frame.dropna(subset=["timestamp_utc"]).sort_values(
        ["equipment_id", "sensor_name", "timestamp_utc"]
    )
    working = timeline.dropna(subset=["value_ref"])
    rejets_ligne: list[tuple[str, str, str, pd.DataFrame]] = []
    rejets_serie: list[tuple[str, str, str, pd.DataFrame]] = []
    stats: dict[str, int] = {}

    # Fige : paliers de valeurs strictement identiques.
    change = (
        (working["value_ref"] != working["value_ref"].shift())
        | (working["equipment_id"] != working["equipment_id"].shift())
        | (working["sensor_name"] != working["sensor_name"].shift())
    )
    plateau = change.cumsum()
    sizes = plateau.map(plateau.value_counts())
    frozen = working[sizes >= FROZEN_RUN_THRESHOLD]
    stats["lignes_figees_exclues"] = len(frozen)

    reference = working.drop(index=frozen.index)

    # Plage : ecart robuste a la mediane (MAD), et non un centile.
    #
    # Une premiere version signalait tout ce qui depassait le p99 du capteur.
    # C'est une tautologie : un centile decoupe la distribution, il ne detecte
    # rien. Elle rejetait exactement 1 % des lignes — 504 sur 50 401 — quelle
    # que soit la donnee. Le critere robuste ne se declenche que sur ce qui
    # s'ecarte reellement du corps de la distribution.
    above_parts = []
    for sensor, group in reference.groupby("sensor_name", observed=True):
        values = group["value_ref"]
        median = values.median()
        mad = (values - median).abs().median()
        if mad == 0:
            continue
        above_parts.append(group[(values - median).abs() >= PLAGE_MAD_FACTOR * mad])
    above = (
        pd.concat(above_parts) if above_parts else reference.iloc[0:0]
    )
    rejets_ligne.append(
        (
            "R-SEN-009",
            "value",
            f"Valeur a plus de {PLAGE_MAD_FACTOR:g} ecarts absolus medians de la mediane du capteur",
            above,
        )
    )
    stats["depassements_plage"] = len(above)

    # Derive : correlation temps/valeur par serie — signalee au niveau serie.
    drifting = []
    for (equipment, sensor), group in reference.groupby(
        ["equipment_id", "sensor_name"], observed=True
    ):
        if len(group) < 30:
            continue
        days = (
            group["timestamp_utc"] - group["timestamp_utc"].min()
        ).dt.total_seconds() / 86400
        values = group["value_ref"].to_numpy()
        if np.std(values) == 0 or np.std(days) == 0:
            continue
        correlation = float(np.corrcoef(days, values)[0, 1])
        if abs(correlation) >= DRIFT_CORRELATION_THRESHOLD:
            drifting.append((group, correlation))

    if drifting:
        heads = []
        for group, correlation in drifting:
            head = group.sort_values("timestamp_utc").head(1).copy()
            head["_reason"] = (
                f"Serie en derive monotone : correlation {correlation:.3f} "
                f"sur {len(group)} mesures"
            )
            heads.append(head)
        drift_frame = pd.concat(heads)
    else:
        drift_frame = reference.iloc[0:0].assign(_reason=pd.Series(dtype=object))
    rejets_serie.append(("R-SEN-011", "value", None, drift_frame))
    stats["series_en_derive_signalees"] = len(drift_frame)

    # Saut : ecart avec la mesure precedente, rapporte a la dispersion ROBUSTE
    # des ecarts de la serie.
    #
    # Une premiere version divisait par l'ecart-type des ecarts. Elle ne
    # detectait pas un saut isole : les deux ecarts extremes qu'il produit
    # (l'aller et le retour) gonflent l'ecart-type qui sert a les mesurer, et le
    # rapport retombe sous le seuil. Sur une serie de 40 points, un pic a 25 sur
    # une base a 2,8 ressortait a 4,3 — invisible a 8 sigma. C'est la meme
    # mecanique que les sentinelles : la valeur cherchee fausse le detecteur.
    #
    # Le MAD des ecarts n'est pas sensible aux quelques valeurs extremes qu'on
    # cherche. Le facteur 1,4826 le rend comparable a un ecart-type sur une
    # distribution normale, pour que le seuil garde le meme sens.
    grouped = reference.groupby(["equipment_id", "sensor_name"], observed=True)
    delta = grouped["value_ref"].diff()

    def _robust_scale(series: pd.Series) -> float:
        differences = series.diff().dropna()
        if differences.empty:
            return float("nan")
        return 1.4826 * float((differences - differences.median()).abs().median())

    scale = grouped["value_ref"].transform(_robust_scale)

    # Second garde-fou, d'amplitude. Sur une serie tres stable, le MAD des
    # ecarts devient minuscule et le seul rapport statistique se declenche sur
    # des micro-variations : une serie synthetique reguliere produisait 38
    # « sauts » sur 40 points. Un saut brutal doit l'etre aussi en amplitude —
    # au moins un dixieme du niveau habituel de la serie.
    level = grouped["value_ref"].transform("median").abs()
    significant = delta.abs() >= JUMP_MIN_RELATIVE * level

    jumps = reference[(scale > 0) & ((delta / scale).abs() >= JUMP_SIGMA) & significant]
    rejets_ligne.append(("R-SEN-012", "value", "Saut brutal entre deux mesures", jumps))
    stats["sauts_signales"] = len(jumps)

    # Continuite : trous superieurs au pas nominal, sur la trame temporelle.
    timeline_grouped = timeline.groupby(["equipment_id", "sensor_name"], observed=True)
    gaps = timeline[
        timeline_grouped["timestamp_utc"].diff() > pd.Timedelta(hours=NOMINAL_STEP_HOURS)
    ]
    rejets_ligne.append(
        ("R-SEN-004", "timestamp", "Reprise apres interruption de l'echantillonnage", gaps)
    )
    stats["reprises_apres_interruption"] = len(gaps)

    return {
        "rejets_ligne": rejets_ligne,
        "rejets_serie": rejets_serie,
        "figes": frozen,
        "stats": stats,
    }


# --------------------------------------------------------------------------- #
# Non-regression
# --------------------------------------------------------------------------- #

def check_no_regression(
    reference: dict[str, pd.DataFrame], produced: dict[str, pd.DataFrame]
) -> dict:
    """Compare table par table l'entree M2 et ce que la pipeline restitue.

    La non-regression est ici **demontree** : on ne se contente pas de ne pas
    toucher aux tables, on verifie l'egalite ligne a ligne et le comptage.
    """
    report = {}
    for name in ("equipment", "events", "maintenance"):
        before, after = reference[name], produced[name]
        identical = before.equals(after)
        report[name] = {
            "lignes_avant": int(len(before)),
            "lignes_apres": int(len(after)),
            "colonnes_identiques": list(before.columns) == list(after.columns),
            "contenu_identique": bool(identical),
        }
    report["non_regression"] = all(
        entry["contenu_identique"] for key, entry in report.items() if key != "non_regression"
    )
    return report
