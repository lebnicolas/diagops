"""Lecture d'un lot et construction du contexte de qualification.

Un lot est un triplet de fichiers, decrit dans `config/batches.yaml`. Il peut
etre le socle publie ou une livraison candidate — la difference n'est pas dans
la nature des fichiers, elle est dans ce a quoi on les compare.

Rien n'est jamais ecrit ici. Les empreintes sont relevees a la lecture et
revalidees apres coup par l'appelant.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd


SOURCES = ("equipment", "events", "maintenance")


@dataclass(frozen=True)
class Batch:
    """Un lot lu, avec de quoi prouver ce qui a ete lu."""

    batch_id: str
    label: str
    root: Path
    paths: dict[str, Path]
    frames: dict[str, pd.DataFrame]
    checksums: dict[str, str]
    announced_rows: dict[str, int] = field(default_factory=dict)
    announced_columns: dict[str, list[str]] = field(default_factory=dict)
    update_by_key: dict[str, str] = field(default_factory=dict)

    def row_counts(self) -> dict[str, int]:
        return {name: len(frame) for name, frame in self.frames.items()}

    def relative_paths(self) -> dict[str, str]:
        return {name: path.relative_to(self.root).as_posix() for name, path in self.paths.items()}


def file_sha256(path: Path) -> str:
    """Empreinte d'un fichier, lue par blocs."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_batch(entry: dict, root: Path) -> Batch:
    """Charge un lot decrit par une entree du catalogue.

    Les CSV sont lus sans conversion implicite : `dtype=str` n'est pas impose,
    mais aucune colonne n'est parsee en date ou en nombre. C'est le meme parti
    pris qu'en M2 — un audit qui corrige en lisant ne peut plus constater.
    """
    root = root.resolve()
    paths = {name: (root / relative).resolve() for name, relative in entry["sources"].items()}

    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Fichiers du lot absents : " + ", ".join(missing))

    return Batch(
        batch_id=entry["batch_id"],
        label=entry.get("label", entry["batch_id"]),
        root=root,
        paths=paths,
        frames={name: pd.read_csv(path) for name, path in paths.items()},
        checksums={name: file_sha256(path) for name, path in paths.items()},
        announced_rows=entry.get("announced_rows") or {},
        announced_columns=entry.get("announced_columns") or {},
        update_by_key=entry.get("update_by_key") or {},
    )


def build_context(baseline: Batch, candidate: Batch | None) -> dict[str, pd.DataFrame]:
    """Univers dans lequel le lot candidat s'inserera s'il est accepte.

    Sert a resoudre les references et a compter les valeurs de categorie. Ce
    n'est PAS une integration : le resultat vit en memoire, ne retourne jamais
    sur disque, et sert uniquement a poser les questions dans le bon
    referentiel.

    Le candidat est concatene APRES la baseline, puis les cles en double sont
    resolues en gardant la derniere occurrence. Une mise a jour d'equipement
    doit primer sur la version publiee : sinon un controle croise irait
    chercher l'ancienne date de mise en service pour juger un evenement
    nouveau, et conclurait sur une donnee que la livraison remplace.
    """
    if candidate is None:
        return {name: frame.copy() for name, frame in baseline.frames.items()}

    keys = {"equipment": "equipment_id", "events": "event_id", "maintenance": "maintenance_id"}
    context: dict[str, pd.DataFrame] = {}

    for name in baseline.frames:
        published = baseline.frames[name]
        incoming = candidate.frames.get(name)
        if incoming is None:
            context[name] = published.copy()
            continue

        merged = pd.concat([published, incoming], ignore_index=True, sort=False)
        key = keys.get(name)
        if key and key in merged.columns:
            merged = merged.drop_duplicates(subset=[key], keep="last").reset_index(drop=True)
        context[name] = merged

    return context
