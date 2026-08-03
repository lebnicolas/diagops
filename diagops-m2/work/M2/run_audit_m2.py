"""Chaine complete de l'audit M2, rejouable d'une seule commande.

    python run_audit_m2.py [--output output] [--date 2026-08-03]

Enchaine : lecture des sources -> audit sans correction -> preparation ->
export. Verifie a la fin que les fichiers recus n'ont pas bouge, en comparant
leurs empreintes avant et apres.

Le notebook peut faire la meme chose cellule par cellule ; ce script existe
pour qu'une autre personne puisse tout rejouer sans ouvrir Jupyter.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.data_pipeline import checks
from src.data_pipeline.audit import SOURCE_FILES, run_audit
from src.data_pipeline.prepare import export_prepared, prepare_all


DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data_pack" / "2026-S1"

SOURCE_PATHS = {
    "equipment": ("equipment", "equipment.csv"),
    "events": ("events", "events.csv"),
    "maintenance": ("maintenance", "maintenance_history.csv"),
}


def load_sources(data_dir: Path) -> tuple[dict[str, pd.DataFrame], dict[str, str]]:
    paths = {name: data_dir / folder / filename for name, (folder, filename) in SOURCE_PATHS.items()}
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Sources M2 absentes : " + ", ".join(missing))
    frames = {name: pd.read_csv(path) for name, path in paths.items()}
    fingerprints = {name: checks_sha(path) for name, path in paths.items()}
    return frames, fingerprints


def checks_sha(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit et preparation des donnees M2.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parent / "output")
    parser.add_argument(
        "--date",
        default="2026-08-03",
        help="date de reference des controles de non-anteriorite (reproductibilite)",
    )
    args = parser.parse_args()

    frames, before = load_sources(args.data_dir)
    print(f"Sources lues depuis {args.data_dir}")
    for name, frame in frames.items():
        print(f"  {name:12s} {len(frame):5d} lignes x {frame.shape[1]} colonnes")

    result = run_audit(frames, reference_date=pd.Timestamp(args.date))
    failed = result.failed_rules()
    print(f"\nAudit : {len(result.check_results)} regles, {len(failed)} en echec")
    print(f"        {len(result.quarantine)} entrees de quarantaine")

    prepared, log = prepare_all(frames)
    print(f"\nPreparation : {len(log)} operations, {int(log['rows_affected'].sum())} lignes touchees")
    for name in frames:
        print(f"  {name:12s} {len(frames[name]):5d} -> {len(prepared[name]):5d}")

    written = export_prepared(
        prepared=prepared,
        quarantine=result.quarantine,
        transformation_log=log,
        check_results=result.check_results,
        output_dir=args.output,
    )
    print(f"\nExport dans {args.output}")
    for label, path in written.items():
        print(f"  {label:35s} {path.stat().st_size:8d} octets")

    after = {name: checks_sha(args.data_dir / folder / filename)
             for name, (folder, filename) in SOURCE_PATHS.items()}
    if before != after:
        modified = [name for name in before if before[name] != after[name]]
        raise SystemExit(f"ECHEC : source modifiee pendant l'audit — {modified}")
    print("\nSources recues inchangees : empreintes identiques avant et apres.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
