"""Controles generiques reutilisables pour l'audit M2.

Chaque controle est une fonction pure qui recoit un DataFrame et renvoie un
**masque booleen aligne sur l'index** : `True` = la ligne echoue le controle.
Aucune fonction de ce module ne modifie les donnees ni n'ecrit sur le disque.

Le decoupage est volontairement generique : les 54 regles du registre se
ramenent a une douzaine de controles parametres. Une regle nouvelle se declare
dans `rules.py` et se branche sur un controle existant, sans code neuf.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

import pandas as pd


# ----------------------------------------------------------------------
# Resultat d'un controle
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class CheckOutcome:
    """Resultat mesure d'une regle sur une source."""

    rule_id: str
    source: str
    column: str
    rows_checked: int
    failures: int
    failing_identifiers: list[str] = field(default_factory=list)
    observed_values: list[str] = field(default_factory=list)
    comment: str = ""

    @property
    def failure_rate(self) -> float:
        return self.failures / self.rows_checked if self.rows_checked else 0.0


def outcome_from_mask(
    rule_id: str,
    source: str,
    column: str,
    frame: pd.DataFrame,
    mask: pd.Series,
    identifier_column: str | None,
    observed_column: str | None = None,
    comment: str = "",
) -> CheckOutcome:
    """Transforme un masque d'echecs en resultat exploitable.

    Les listes retournees sont **completes** : la quarantaine doit contenir
    toutes les anomalies, pas un echantillon. Le plafonnement d'affichage se
    fait au moment d'ecrire `check_results`, jamais ici.
    """
    failing = frame.loc[mask]
    if identifier_column and identifier_column in failing.columns:
        identifiers = failing[identifier_column].astype(str).tolist()
    else:
        identifiers = [f"index:{value}" for value in failing.index.tolist()]

    column_for_values = observed_column or (column if column in failing.columns else None)
    if column_for_values:
        observed = failing[column_for_values].astype(str).tolist()
    else:
        observed = ["" for _ in identifiers]

    return CheckOutcome(
        rule_id=rule_id,
        source=source,
        column=column,
        rows_checked=len(frame),
        failures=int(mask.sum()),
        failing_identifiers=identifiers,
        observed_values=observed,
        comment=comment,
    )


def _empty_mask(frame: pd.DataFrame) -> pd.Series:
    return pd.Series(False, index=frame.index, dtype=bool)


# ----------------------------------------------------------------------
# Structure et types
# ----------------------------------------------------------------------


def missing_columns(frame: pd.DataFrame, required: Iterable[str]) -> list[str]:
    """Colonnes obligatoires absentes, dans un ordre stable."""
    return sorted(set(required) - set(frame.columns))


def not_convertible(frame: pd.DataFrame, column: str, kind: str) -> pd.Series:
    """Valeurs non nulles qui ne se convertissent pas dans le type attendu.

    `kind` vaut `datetime`, `iso_datetime`, `number` ou `integer`. Une valeur
    absente n'est jamais un echec ici : c'est le role des controles `NUL`.
    """
    if column not in frame.columns:
        return _empty_mask(frame)

    raw = frame[column]
    present = raw.notna() & (raw.astype(str).str.strip() != "")

    if kind == "iso_datetime":
        converted = pd.to_datetime(raw, errors="coerce", format="ISO8601")
    elif kind == "datetime":
        converted = pd.to_datetime(raw, errors="coerce")
    elif kind in {"number", "integer"}:
        converted = pd.to_numeric(raw, errors="coerce")
    else:
        raise ValueError(f"Type de conversion inconnu : {kind}")

    failed = present & converted.isna()

    if kind == "integer":
        numeric = pd.to_numeric(raw, errors="coerce")
        fractional = present & numeric.notna() & (numeric != numeric.round())
        failed = failed | fractional

    return failed


# ----------------------------------------------------------------------
# Identifiants
# ----------------------------------------------------------------------


def is_null(frame: pd.DataFrame, column: str) -> pd.Series:
    """Valeurs absentes, chaine vide comprise."""
    if column not in frame.columns:
        return _empty_mask(frame)
    raw = frame[column]
    return raw.isna() | (raw.astype(str).str.strip() == "")


def duplicated_key(frame: pd.DataFrame, column: str) -> pd.Series:
    """Toutes les lignes participant a un identifiant en double.

    `keep=False` marque les deux exemplaires : face a un doublon de cle, on ne
    sait pas lequel garder, les deux doivent etre examines.
    Les valeurs absentes sont ignorees — elles relevent du controle de nullite.
    """
    if column not in frame.columns:
        return _empty_mask(frame)
    present = ~is_null(frame, column)
    duplicated = frame[column].duplicated(keep=False)
    return present & duplicated


def duplicated_rows(frame: pd.DataFrame) -> pd.Series:
    """Exemplaires surnumeraires d'une ligne integralement identique.

    `keep='first'` ne marque que les copies : le premier exemplaire est
    conserve, la suppression des suivants ne perd aucune information.
    """
    return frame.duplicated(keep="first")


# ----------------------------------------------------------------------
# Categories
# ----------------------------------------------------------------------


def not_in_set(frame: pd.DataFrame, column: str, allowed: Sequence[str]) -> pd.Series:
    """Valeurs non nulles absentes de l'enumeration attendue."""
    if column not in frame.columns:
        return _empty_mask(frame)
    present = ~is_null(frame, column)
    return present & ~frame[column].isin(list(allowed))


def unknown_value_masks(
    frame: pd.DataFrame,
    column: str,
    allowed: Sequence[str],
    recurrence_threshold: float = 0.05,
    recurrence_minimum: int = 10,
    population: pd.Series | None = None,
) -> dict[str, pd.Series]:
    """Separe trois situations distinctes derriere une meme valeur hors enumeration.

    Une valeur absente du schema n'a pas toujours la meme cause :

    - `case_variant`  : la valeur normalisee est connue, seule la casse devie
      (`Incident` pour `incident`). Erreur de saisie, correction sure.
    - `recurrent`     : valeur inconnue portee par au moins `recurrence_threshold`
      des lignes **et** vue au moins `recurrence_minimum` fois. Une anomalie ne
      se repartit pas sur 10 % d'une table de facon reguliere : c'est un ecart
      de nomenclature entre le schema et la livraison, donc un defaut de
      documentation.

      Les deux conditions sont necessaires. Une part seule ne veut rien dire
      sur une petite table — sur 3 lignes, une valeur unique pese 33 % sans
      rien prouver. Un effectif seul ne veut rien dire sur une grande table.
    - `isolated`      : valeur inconnue marginale. La seule vraie anomalie de
      donnee des trois.

    Les trois masques sont disjoints.

    `population` — AJOUTE le 04/08/2026 pour la qualification de livraisons
    incrementales. Les masques portent toujours sur `frame`, mais le comptage
    qui separe `recurrent` de `isolated` se fait sur cette population de
    reference si elle est fournie. Sans elle, le denominateur est la taille du
    lot examine : la meme valeur, dans le meme fichier, changeait de classe
    selon le perimetre qu'on lui donnait. Sur 1 800 lignes d'historique il
    fallait 90 occurrences pour qu'une valeur cesse d'etre une anomalie, sur un
    lot candidat de 220 il en fallait 11, et sur 30 lignes le seuil etait hors
    d'atteinte. La question « cette valeur est-elle une nomenclature legitime ? »
    porte sur le corpus, pas sur l'echantillon recu.
    """
    empty = _empty_mask(frame)
    if column not in frame.columns:
        return {"case_variant": empty, "recurrent": empty.copy(), "isolated": empty.copy()}

    values = frame[column]
    present = ~is_null(frame, column)
    normalized = values.astype(str).str.strip().str.casefold()
    allowed_exact = set(allowed)
    allowed_normalized = {str(value).strip().casefold() for value in allowed}

    case_variant = present & ~values.isin(allowed_exact) & normalized.isin(allowed_normalized)
    unknown = present & ~normalized.isin(allowed_normalized)

    if population is None:
        counted, counted_unknown, population_size = normalized, unknown, len(frame)
    else:
        counted = population.astype(str).str.strip().str.casefold()
        counted_present = population.notna() & (population.astype(str).str.strip() != "")
        counted_unknown = counted_present & ~counted.isin(allowed_normalized)
        population_size = len(population)

    counts = counted.where(counted_unknown).value_counts(dropna=True)
    shares = counts / population_size if population_size else counts * 0.0
    recurrent_values = set(
        counts[(shares >= recurrence_threshold) & (counts >= recurrence_minimum)].index
    )

    recurrent = unknown & normalized.isin(recurrent_values)
    isolated = unknown & ~normalized.isin(recurrent_values)

    return {"case_variant": case_variant, "recurrent": recurrent, "isolated": isolated}


def category_inventory(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    """Effectifs et parts d'une categorie ouverte, du plus rare au plus frequent."""
    if column not in frame.columns:
        return pd.DataFrame(columns=["value", "count", "share"])
    counts = frame[column].value_counts(dropna=False)
    return (
        pd.DataFrame(
            {
                "value": counts.index.astype(str),
                "count": counts.to_numpy(),
                "share": (counts / len(frame)).to_numpy(),
            }
        )
        .sort_values("count")
        .reset_index(drop=True)
    )


def has_declared_label(
    frame: pd.DataFrame, column: str, equivalences: dict[str, str]
) -> pd.Series:
    """Lignes portant un libelle declare equivalent a un autre.

    Contrepartie de detection des corrections declarees sur les categories
    ouvertes : le registre annonce la correction, l'audit doit pouvoir compter
    combien de lignes elle touche avant qu'elle soit appliquee.
    """
    if column not in frame.columns or not equivalences:
        return _empty_mask(frame)
    return frame[column].isin(list(equivalences))


def near_duplicate_labels(frame: pd.DataFrame, column: str) -> list[tuple[str, ...]]:
    """Libelles distincts qui se confondent une fois normalises.

    Detecte `pompe` / `Pompe ` / `POMPE`, pas les fautes de frappe.
    """
    if column not in frame.columns:
        return []
    groups: dict[str, set[str]] = {}
    for value in frame[column].dropna().astype(str).unique():
        groups.setdefault(value.strip().casefold(), set()).add(value)
    return [tuple(sorted(variants)) for variants in groups.values() if len(variants) > 1]


# ----------------------------------------------------------------------
# References entre tables
# ----------------------------------------------------------------------


def unresolved_reference(
    frame: pd.DataFrame, column: str, reference_values: Iterable[str]
) -> pd.Series:
    """Cles etrangeres renseignees mais absentes de la table de reference."""
    if column not in frame.columns:
        return _empty_mask(frame)
    known = set(reference_values)
    present = ~is_null(frame, column)
    return present & ~frame[column].isin(known)


def inconsistent_join(
    frame: pd.DataFrame,
    column: str,
    reference: pd.DataFrame,
    reference_key: str,
    reference_column: str,
) -> pd.Series:
    """Valeur contredite par la table jointe.

    Sert a `MNT-REF-003` : l'equipement porte par l'intervention doit etre celui
    de son evenement. Les lignes dont la jointure n'aboutit pas ne sont pas
    marquees ici — c'est le controle de reference qui s'en charge.
    """
    if column not in frame.columns or reference_key not in frame.columns:
        return _empty_mask(frame)
    mapping = reference.set_index(reference_key)[reference_column]
    expected = frame[reference_key].map(mapping)
    both_present = expected.notna() & ~is_null(frame, column)
    return both_present & (frame[column] != expected)


# ----------------------------------------------------------------------
# Coherence temporelle
# ----------------------------------------------------------------------


def out_of_order_dates(
    frame: pd.DataFrame, earlier_column: str, later_column: str
) -> pd.Series:
    """Lignes ou la date censee etre anterieure est posterieure a l'autre.

    Les lignes dont l'une des deux dates manque ou est illisible ne sont pas
    marquees : elles relevent des controles de nullite et de type.
    """
    if earlier_column not in frame.columns or later_column not in frame.columns:
        return _empty_mask(frame)
    earlier = pd.to_datetime(frame[earlier_column], errors="coerce", utc=True)
    later = pd.to_datetime(frame[later_column], errors="coerce", utc=True)
    return earlier.notna() & later.notna() & (earlier > later)


def date_out_of_bounds(
    frame: pd.DataFrame,
    column: str,
    minimum: str | pd.Timestamp | None = None,
    maximum: str | pd.Timestamp | None = None,
) -> pd.Series:
    """Dates hors d'un intervalle admissible."""
    if column not in frame.columns:
        return _empty_mask(frame)
    values = pd.to_datetime(frame[column], errors="coerce", utc=True)
    failed = _empty_mask(frame)
    if minimum is not None:
        failed = failed | (values.notna() & (values < pd.Timestamp(minimum, tz="UTC")))
    if maximum is not None:
        failed = failed | (values.notna() & (values > pd.Timestamp(maximum, tz="UTC")))
    return failed


def date_gap_exceeded(
    frame: pd.DataFrame,
    start_column: str,
    end_column: str,
    value_column: str,
    unit_minutes: float = 1.0,
    tolerance_minutes: float = 1.0,
) -> pd.Series:
    """Duree declaree superieure a l'ecart reel entre deux horodatages.

    Sert a `MNT-VAL-003`. La tolerance absorbe les arrondis de saisie.
    """
    for name in (start_column, end_column, value_column):
        if name not in frame.columns:
            return _empty_mask(frame)
    start = pd.to_datetime(frame[start_column], errors="coerce", utc=True)
    end = pd.to_datetime(frame[end_column], errors="coerce", utc=True)
    declared = pd.to_numeric(frame[value_column], errors="coerce") * unit_minutes
    elapsed = (end - start).dt.total_seconds() / 60.0
    usable = start.notna() & end.notna() & declared.notna()
    return usable & (declared > elapsed + tolerance_minutes)


# ----------------------------------------------------------------------
# Valeurs numeriques
# ----------------------------------------------------------------------


def numeric_out_of_bounds(
    frame: pd.DataFrame,
    column: str,
    minimum: float | None = None,
    maximum: float | None = None,
    strict_minimum: bool = False,
) -> pd.Series:
    """Valeurs numeriques hors bornes.

    Les valeurs non convertibles ne sont pas marquees : c'est le role du
    controle de type. Sans cette separation, une meme ligne echouerait deux
    regles pour une seule cause.
    """
    if column not in frame.columns:
        return _empty_mask(frame)
    values = pd.to_numeric(frame[column], errors="coerce")
    failed = _empty_mask(frame)
    if minimum is not None:
        below = values < minimum if not strict_minimum else values <= minimum
        failed = failed | (values.notna() & below)
    if maximum is not None:
        failed = failed | (values.notna() & (values > maximum))
    return failed


def inconsistent_pair(
    frame: pd.DataFrame,
    driver_column: str,
    dependent_column: str,
    driver_minimum: float = 0.0,
    dependent_minimum: float = 1.0,
) -> pd.Series:
    """Une colonne strictement positive alors que sa contrepartie est nulle.

    Sert a `MNT-VAL-007` : un cout de pieces sans piece remplacee.
    """
    if driver_column not in frame.columns or dependent_column not in frame.columns:
        return _empty_mask(frame)
    driver = pd.to_numeric(frame[driver_column], errors="coerce")
    dependent = pd.to_numeric(frame[dependent_column], errors="coerce")
    return driver.notna() & dependent.notna() & (driver > driver_minimum) & (
        dependent < dependent_minimum
    )


# ----------------------------------------------------------------------
# Valeurs manquantes
# ----------------------------------------------------------------------


def missing_rate(frame: pd.DataFrame, column: str) -> float:
    """Part de valeurs absentes sur une colonne, entre 0 et 1."""
    if column not in frame.columns or len(frame) == 0:
        return 0.0
    return float(is_null(frame, column).mean())


# ----------------------------------------------------------------------
# Donnees personnelles dans du texte libre
# ----------------------------------------------------------------------


PII_PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(r"[\w.+-]+@[\w-]+\.[\w.]{2,}"),
    "telephone": re.compile(
        r"(?:(?:\+|00)33[\s.-]?|0)[1-9](?:[\s.-]?\d{2}){4}"
    ),
    "nom_apres_civilite": re.compile(
        r"\b(?:M|Mr|Mme|Mlle|Dr)\.?\s+[A-ZÀ-Ý][\wÀ-ÿ'-]+"
    ),
}


def contains_personal_data(
    frame: pd.DataFrame, column: str, patterns: dict[str, re.Pattern[str]] | None = None
) -> pd.Series:
    """Lignes dont le texte libre declenche au moins un motif de donnee personnelle.

    Detection **automatique et indicative** : elle produit des faux positifs
    (une reference technique peut ressembler a un numero) et des faux negatifs
    (un nom seul, sans civilite, n'est pas detecte). Elle sert a cibler une
    verification humaine, pas a conclure.
    """
    if column not in frame.columns:
        return _empty_mask(frame)
    active = patterns or PII_PATTERNS
    text = frame[column].fillna("").astype(str)
    failed = _empty_mask(frame)
    for pattern in active.values():
        failed = failed | text.str.contains(pattern, regex=True, na=False)
    return failed


def personal_data_kinds(
    frame: pd.DataFrame, column: str, patterns: dict[str, re.Pattern[str]] | None = None
) -> pd.Series:
    """Motifs declenches par ligne, en clair, pour la relecture humaine."""
    if column not in frame.columns:
        return pd.Series("", index=frame.index, dtype=str)
    active = patterns or PII_PATTERNS
    text = frame[column].fillna("").astype(str)
    kinds = pd.Series("", index=frame.index, dtype=str)
    for name, pattern in active.items():
        hit = text.str.contains(pattern, regex=True, na=False)
        kinds = kinds.where(~hit, kinds.str.cat(pd.Series(name, index=frame.index), sep="|"))
    return kinds.str.strip("|")
