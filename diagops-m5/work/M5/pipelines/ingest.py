#!/usr/bin/env python3
"""Ingestion idempotente : valider le manifeste, comparer à l'état servi, décider de rebâtir.

`build_index.py` reconstruit l'index à chaque appel sans jamais regarder l'état précédent. Le
résultat est déterministe, donc rejouable — mais il ne dit pas *ce qui a changé*, et rien
n'empêche un document d'être modifié sans que sa révision bouge. Ce pipeline ajoute les deux
contrôles que le brief demande : la validation d'admission complète, et la détection
ajout / modification / retrait / conflit de révision.

Idempotence : rejoué sur un corpus inchangé, il rend `unchanged` et ne produit aucun candidat.
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pipelines.build_index import build_index  # noqa: E402
from src.versioning import atomic_write_json, load_json, sha256  # noqa: E402


SENSITIVITIES = {"public", "interne", "restreint"}
STATUSES = {"active", "superseded", "draft", "retired"}
KNOWN_ROLES = {"public", "technicien", "superviseur", "auditeur"}


def read_manifest(path: Path) -> list[dict]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def validate_admission(rows: list[dict], documents: Path) -> list[str]:
    """Contrat d'admission du corpus. Rend la liste des refus, vide si tout passe.

    Le README du corpus est explicite : un index doit vérifier le checksum, le statut de
    révision, la sensibilité et les rôles autorisés *avant* de rendre un document récupérable.
    `build_index.py` ne vérifiait que le checksum.
    """
    refusals: list[str] = []
    seen: set[str] = set()
    known_ids = {row["document_id"] for row in rows}

    for row in rows:
        document_id = row["document_id"]
        if document_id in seen:
            refusals.append(f"{document_id} : document_id dupliqué")
        seen.add(document_id)

        if row["sensitivity"] not in SENSITIVITIES:
            refusals.append(f"{document_id} : sensibilité inconnue « {row['sensitivity']} »")
        if row["status"] not in STATUSES:
            refusals.append(f"{document_id} : statut inconnu « {row['status']} »")

        roles = set(filter(None, row["allowed_roles"].split(";")))
        if not roles:
            refusals.append(f"{document_id} : aucun rôle autorisé")
        unknown = roles - KNOWN_ROLES
        if unknown:
            refusals.append(f"{document_id} : rôles inconnus {sorted(unknown)}")
        # Un document restreint ouvert à tous est une contradiction, pas une tolérance.
        if row["sensitivity"] == "restreint" and "public" in roles:
            refusals.append(f"{document_id} : document restreint ouvert au rôle public")

        superseded = row.get("supersedes_document_id") or ""
        if superseded:
            if superseded not in known_ids:
                refusals.append(f"{document_id} : remplace un document absent du manifeste")
            else:
                previous = next(r for r in rows if r["document_id"] == superseded)
                if previous["status"] == "active":
                    refusals.append(
                        f"{document_id} : remplace {superseded}, qui est toujours actif"
                    )

        asset = documents / row["asset_path"]
        if not asset.is_file():
            refusals.append(f"{document_id} : fichier absent ({row['asset_path']})")
        elif sha256(asset) != row["checksum_sha256"]:
            refusals.append(f"{document_id} : checksum du fichier ≠ checksum déclaré")

    return refusals


def diff_against(previous: dict | None, candidate: dict) -> dict:
    """Compare deux index et qualifie chaque écart.

    Le cas qui compte est `revision_conflict` : le contenu a changé sans que la révision bouge.
    Le document est alors indistinguable de sa version précédente dans toute trace — c'est
    précisément ce que le contrat de versions doit rendre impossible.
    """
    new = {item["document_id"]: item for item in candidate["documents"]}
    old = {item["document_id"]: item for item in (previous or {}).get("documents", [])}

    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    modified, unchanged, conflicts, silent_revisions = [], [], [], []

    for document_id in sorted(set(new) & set(old)):
        before, after = old[document_id], new[document_id]
        content_changed = before["checksum_sha256"] != after["checksum_sha256"]
        revision_changed = str(before["revision"]) != str(after["revision"])
        if content_changed and not revision_changed:
            conflicts.append(document_id)
            modified.append(document_id)
        elif revision_changed and not content_changed:
            silent_revisions.append(document_id)
            modified.append(document_id)
        elif content_changed:
            modified.append(document_id)
        else:
            unchanged.append(document_id)

    return {
        "added": added,
        "removed": removed,
        "modified": modified,
        "unchanged": unchanged,
        "revision_conflicts": conflicts,
        "revisions_without_content_change": silent_revisions,
        "previous_index_version": (previous or {}).get("index_version"),
        "candidate_index_version": candidate.get("index_version"),
        "previous_build_version": (previous or {}).get("build_version"),
        "candidate_build_version": candidate.get("build_version"),
    }


def decide(changes: dict, refusals: list[str]) -> tuple[str, str]:
    """Trois issues seulement : refusé, inchangé, à évaluer."""
    if refusals:
        return "rejected", "le manifeste ne passe pas le contrat d'admission"
    if changes["revision_conflicts"]:
        return "rejected", (
            "contenu modifié à révision constante : "
            + ", ".join(changes["revision_conflicts"])
        )
    documentary_change = changes["added"] or changes["removed"] or changes["modified"]
    build_changed = changes["candidate_build_version"] != changes["previous_build_version"]
    if not documentary_change and not build_changed:
        return "unchanged", "aucun changement documentaire ni de stratégie de construction"
    if not documentary_change and build_changed:
        return "rebuild", "stratégie de construction modifiée à corpus constant"
    return "rebuild", "corpus modifié"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--documents", type=Path, required=True)
    parser.add_argument("--active", type=Path, default=None, help="index actuellement servi")
    parser.add_argument("--output", type=Path, required=True, help="index candidat à écrire")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    rows = read_manifest(args.manifest)
    refusals = validate_admission(rows, args.documents)

    candidate = None if refusals else build_index(args.manifest, args.documents)
    previous = load_json(args.active) if args.active and args.active.is_file() else None
    changes = diff_against(previous, candidate) if candidate else {
        "added": [], "removed": [], "modified": [], "unchanged": [],
        "revision_conflicts": [], "revisions_without_content_change": [],
        "previous_index_version": (previous or {}).get("index_version"),
        "candidate_index_version": None,
        "previous_build_version": (previous or {}).get("build_version"),
        "candidate_build_version": None,
    }
    decision, reason = decide(changes, refusals)

    atomic_write_json(args.report, {
        "decision": decision,
        "reason": reason,
        "refusals": refusals,
        "changes": changes,
        "manifest_sha256": sha256(args.manifest),
    })

    # Un candidat n'est écrit que s'il y a lieu de le réévaluer : rejouer l'ingestion sur un
    # corpus inchangé ne produit aucun artefact et ne touche pas au chemin actif.
    if decision == "rebuild" and candidate is not None:
        atomic_write_json(args.output, candidate)

    print(f"Ingestion : {decision} — {reason}")
    if refusals:
        for refusal in refusals:
            print(f"  refus : {refusal}")
    else:
        print(
            f"  +{len(changes['added'])} ajouts, ~{len(changes['modified'])} modifications, "
            f"-{len(changes['removed'])} retraits, ={len(changes['unchanged'])} inchangés"
        )
    return 0 if decision in {"rebuild", "unchanged"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
