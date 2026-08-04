"""Controles qui n'ont de sens que pour un lot compare a un publie.

Le brief presentiel M2 ne connaissait qu'un lot unique : il etait a lui seul
tout l'univers, et les questions posees ici ne se posaient pas. Une cle en
double etait forcement un doublon, une colonne en trop ne genait personne,
et il n'y avait rien a quoi comparer une nouvelle valeur.

Chaque controle produit un `CheckOutcome`, le meme type que l'audit M2 : le
rapport reste homogene et un lecteur n'a pas deux formats a apprendre.
"""

from __future__ import annotations

import pandas as pd

from src.data_pipeline.checks import CheckOutcome, is_null, outcome_from_mask


ROW_IDENTIFIER = {
    "equipment": "equipment_id",
    "events": "event_id",
    "maintenance": "maintenance_id",
}


def _empty(frame: pd.DataFrame) -> pd.Series:
    return pd.Series(False, index=frame.index, dtype=bool)


# ----------------------------------------------------------------------
# Structure
# ----------------------------------------------------------------------


def extra_columns(
    frame: pd.DataFrame, required: tuple[str, ...], announced: list[str]
) -> tuple[list[str], list[str]]:
    """Colonnes presentes en plus du contrat, separees selon leur annonce.

    Le controle M2 `missing_columns` calcule `requises - presentes` : il ne
    voit que les absences. Une colonne surnumeraire ne declenchait rien, donc
    une evolution de contrat passait entierement inapercue — le genre d'ecart
    qui ne se lit pas dans le resultat.
    """
    extra = sorted(set(frame.columns) - set(required))
    declared = [column for column in extra if column in announced]
    undeclared = [column for column in extra if column not in announced]
    return declared, undeclared


def column_outcome(rule_id: str, source: str, columns: list[str], frame: pd.DataFrame) -> CheckOutcome:
    """Constat de structure : porte sur des colonnes, pas sur des lignes."""
    return CheckOutcome(
        rule_id=rule_id,
        source=source,
        column=", ".join(columns) if columns else "*",
        rows_checked=len(frame),
        failures=len(columns),
        failing_identifiers=list(columns),
        observed_values=["" for _ in columns],
        comment=("colonnes : " + ", ".join(columns)) if columns else "aucune",
    )


def row_count_outcome(source: str, frame: pd.DataFrame, announced: int | None) -> CheckOutcome:
    """INC-VOL-001 — lignes lues confrontees aux lignes annoncees.

    Les notes de livraison precisent elles-memes que les volumes annonces ne
    prouvent rien. Justement : un ecart revele une troncature, un mauvais
    export ou une erreur de comptage du fournisseur, et il vaut mieux le
    savoir avant de commencer a juger le contenu.
    """
    observed = len(frame)
    if announced is None:
        return CheckOutcome(
            rule_id="INC-VOL-001",
            source=source,
            column="*",
            rows_checked=observed,
            failures=0,
            comment=f"{observed} lignes lues, aucun volume annonce",
        )

    gap = observed - int(announced)
    return CheckOutcome(
        rule_id="INC-VOL-001",
        source=source,
        column="*",
        rows_checked=observed,
        failures=1 if gap else 0,
        failing_identifiers=[f"{source}:{observed}!={announced}"] if gap else [],
        observed_values=[str(observed)] if gap else [],
        comment=(
            f"{observed} lignes lues pour {announced} annoncees (ecart {gap:+d})"
            if gap
            else f"{observed} lignes lues, conforme a l'annonce"
        ),
    )


# ----------------------------------------------------------------------
# Cles
# ----------------------------------------------------------------------


def key_overlap(frame: pd.DataFrame, published: pd.DataFrame, key: str) -> pd.Series:
    """Lignes du lot dont la cle existe deja dans le publie."""
    if key not in frame.columns or key not in published.columns:
        return _empty(frame)
    known = set(published.loc[~is_null(published, key), key].astype(str))
    present = ~is_null(frame, key)
    return present & frame[key].astype(str).isin(known)


def key_overlap_outcome(
    rule_id: str, source: str, frame: pd.DataFrame, published: pd.DataFrame, key: str, comment: str
) -> CheckOutcome:
    mask = key_overlap(frame, published, key)
    outcome = outcome_from_mask(
        rule_id=rule_id,
        source=source,
        column=key,
        frame=frame,
        mask=mask,
        identifier_column=ROW_IDENTIFIER.get(source),
        observed_column=key if key in frame.columns else None,
    )
    return CheckOutcome(
        rule_id=outcome.rule_id,
        source=outcome.source,
        column=outcome.column,
        rows_checked=outcome.rows_checked,
        failures=outcome.failures,
        failing_identifiers=outcome.failing_identifiers,
        observed_values=outcome.observed_values,
        comment=f"{outcome.failures} cle(s) deja presente(s) dans le publie — {comment}",
    )


def updates_changing_columns(
    frame: pd.DataFrame, published: pd.DataFrame, key: str, watched: tuple[str, ...]
) -> tuple[pd.Series, dict[str, list[str]]]:
    """INC-UPD-001 — mises a jour qui modifient une colonne structurante.

    Changer le site d'une machine ou sa date de mise en service reecrit
    l'interpretation de tout son historique : un controle temporel valide hier
    peut devenir faux demain sans qu'une seule ligne d'evenement ait bouge.
    Ce n'est pas une correction anodine.

    Retourne le masque des lignes concernees et, pour chacune, la liste des
    colonnes qui changent — sans quoi un relecteur devrait comparer les
    fichiers a la main.
    """
    changes: dict[str, list[str]] = {}
    if key not in frame.columns or key not in published.columns:
        return _empty(frame), changes

    reference = published.drop_duplicates(subset=[key], keep="last").copy()
    reference[key] = reference[key].astype(str)
    reference = reference.set_index(key)

    mask = _empty(frame)
    for position, row in frame.iterrows():
        identifier = str(row.get(key, ""))
        if identifier not in reference.index:
            continue
        previous = reference.loc[identifier]
        differing = [
            column
            for column in watched
            if column in frame.columns
            and column in reference.columns
            and _differs(row.get(column), previous.get(column))
        ]
        if differing:
            mask.loc[position] = True
            changes[identifier] = differing
    return mask, changes


def _differs(new: object, old: object) -> bool:
    """Comparaison tolerante aux representations d'une valeur absente."""
    new_missing = pd.isna(new) or str(new).strip() == ""
    old_missing = pd.isna(old) or str(old).strip() == ""
    if new_missing and old_missing:
        return False
    if new_missing != old_missing:
        return True
    return str(new).strip() != str(old).strip()


# ----------------------------------------------------------------------
# Categories
# ----------------------------------------------------------------------


def new_category_values(
    frame: pd.DataFrame, published: pd.DataFrame, column: str
) -> tuple[pd.Series, list[str]]:
    """INC-CAT-001 — valeurs d'une categorie ouverte jamais vues dans le publie.

    Sur une categorie ouverte, aucun schema n'autorise a rejeter une valeur
    nouvelle : elle peut parfaitement etre un site qui vient d'ouvrir. Elle se
    signale pour que la nomenclature reste sous controle.
    """
    if column not in frame.columns or column not in published.columns:
        return _empty(frame), []

    known = set(published.loc[~is_null(published, column), column].astype(str).str.strip())
    present = ~is_null(frame, column)
    values = frame[column].astype(str).str.strip()
    mask = present & ~values.isin(known)
    return mask, sorted(set(values[mask]))
