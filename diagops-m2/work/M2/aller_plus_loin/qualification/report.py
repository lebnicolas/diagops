"""Rapports et manifeste d'execution.

Deux sorties de nature differente :

- un rapport lisible, destine a quelqu'un qui doit comprendre un rejet sans
  relancer quoi que ce soit ;
- un manifeste machine, qui associe donnees, regles, resultats et decision.
  C'est lui qui rend le resultat rejouable : sans les empreintes des fichiers
  ET la version des regles, « meme resultat » ne veut rien dire.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .batch import Batch, file_sha256
from .policy import Policy
from .qualify import Qualification


def write_reports(qualification: Qualification, directory: Path) -> dict[str, Path]:
    """Ecrit les constats detailles d'un lot."""
    directory.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}

    findings = directory / "findings.csv"
    qualification.findings.to_csv(findings, index=False, encoding="utf-8")
    written["findings"] = findings

    quarantine = directory / "quarantine.csv"
    qualification.quarantine.to_csv(quarantine, index=False, encoding="utf-8")
    written["quarantine"] = quarantine

    summary = directory / "summary.md"
    summary.write_text(render_summary(qualification), encoding="utf-8")
    written["summary"] = summary

    return written


def render_summary(qualification: Qualification) -> str:
    """Resume lisible d'une qualification, sans avoir a lire les journaux."""
    counts = qualification.counts
    lines = [
        f"# Qualification — {qualification.label}",
        "",
        f"- **Lot** : `{qualification.batch_id}`",
        f"- **Version des regles** : `{qualification.policy_version}`",
        f"- **Statut** : **{qualification.status}**",
        f"- **Constats** : {counts.get('error', 0)} erreur(s), "
        f"{counts.get('warning', 0)} avertissement(s), {counts.get('info', 0)} information(s)",
        "",
    ]

    for level, title in (("error", "Erreurs bloquantes"), ("warning", "Avertissements"), ("info", "Informations")):
        subset = qualification.findings.loc[qualification.findings["level"] == level]
        if subset.empty:
            continue
        lines += [f"## {title}", "", "| Regle | Source | Colonne | Echecs | Taux | Constat |", "|---|---|---|---:|---:|---|"]
        for _, row in subset.iterrows():
            comment = str(row["comment"]).replace("|", "/").replace("\n", " ")
            flag = " ⬆" if row["escalated"] else ""
            lines.append(
                f"| `{row['rule_id']}`{flag} | {row['source']} | {row['column']} | "
                f"{row['failures']} | {row['failure_rate']:.2%} | {comment[:160]} |"
            )
        lines.append("")

    if qualification.findings.empty:
        lines += ["Aucun constat.", ""]

    lines += [
        "> ⬆ signale une regle passee au niveau superieur parce que son taux",
        "> d'echec depasse le plafond de la politique : le constat ne decrit",
        "> plus des lignes fausses mais une livraison fausse.",
        "",
    ]
    return "\n".join(lines)


def render_run_summary(manifest: dict, results: list[Qualification]) -> str:
    """Resume consolide d'une execution, lisible sans ouvrir les journaux.

    Destine au resume d'une execution GitHub Actions : quelqu'un doit pouvoir
    comprendre un rejet a partir de ce seul texte, sans relancer le workflow ni
    derouler les logs.
    """
    policy = manifest["policy"]
    run = manifest["run"]
    conformity = {entry["batch_id"]: entry for entry in run.get("conformity", [])}

    lines = [
        "# Qualification des donnees DiagOps",
        "",
        f"- **Regles** : version `{policy['version']}` (`{policy['sha256'][:12]}…`)",
        f"- **Date de reference** : {run['reference_date']}",
        f"- **Comptage des categories** : {policy['recurrence_population']} "
        f"(seuils {policy['recurrence_share']:.0%} et {policy['recurrence_minimum']} occurrences)",
        "",
        "| Lot | Statut | Erreurs | Avert. | Infos | Attendu | Verdict |",
        "|---|---|---:|---:|---:|---|---|",
    ]

    for result in results:
        entry = conformity.get(result.batch_id, {})
        expected = entry.get("expected") or "—"
        verdict = "✅ conforme" if entry.get("conforms", True) else "❌ **non conforme**"
        counts = result.counts
        lines.append(
            f"| {result.label} | **{result.status}** | {counts.get('error', 0)} | "
            f"{counts.get('warning', 0)} | {counts.get('info', 0)} | {expected} | {verdict} |"
        )

    lines += ["", "## Fichiers controles", "", "| Lot | Fichier | Lignes | Empreinte |", "|---|---|---:|---|"]
    for key in ("baseline", "candidate"):
        block = manifest.get(key)
        if not block:
            continue
        for name, meta in block["files"].items():
            lines.append(
                f"| `{block['batch_id']}` | {meta['path']} | {meta['rows']} | `{meta['sha256'][:16]}…` |"
            )

    for result in results:
        blocking = result.blocking()
        if blocking.empty:
            continue
        lines += ["", f"## Constats bloquants — {result.label}", "",
                  "| Regle | Source | Echecs | Taux | Constat |", "|---|---|---:|---:|---|"]
        for _, row in blocking.iterrows():
            comment = str(row["comment"]).replace("|", "/").replace("\n", " ")[:180]
            flag = " ⬆" if row["escalated"] else ""
            lines.append(
                f"| `{row['rule_id']}`{flag} | {row['source']} | {row['failures']} | "
                f"{row['failure_rate']:.2%} | {comment} |"
            )

    lines += [
        "",
        f"**Decision enregistree** : `{run['decision']}`",
        "",
        "> Aucune livraison n'est integree automatiquement et aucun fichier de",
        "> `data_pack/` n'est modifie. Le detail ligne a ligne est dans les",
        "> artefacts de cette execution.",
        "",
    ]
    return "\n".join(lines)


def build_manifest(
    *,
    baseline: Batch,
    candidate: Batch | None,
    policy: Policy,
    baseline_result: Qualification,
    candidate_result: Qualification | None,
    reference_date: pd.Timestamp,
    decision: str,
) -> dict:
    """Manifeste d'execution : de quoi rejouer et de quoi contester.

    Contient les empreintes de la baseline **et** du candidat. La politique
    retenue compte les valeurs de categorie sur l'union des deux : la
    qualification du lot depend donc de l'etat du publie, et un manifeste qui
    ne noterait que le lot recu ne permettrait pas de reproduire le resultat.
    """
    manifest = {
        "run": {
            "reference_date": reference_date.date().isoformat(),
            "decision": decision,
        },
        "policy": {
            "version": policy.version,
            "file": policy.path.name,
            "sha256": policy.checksum,
            "recurrence_population": policy.recurrence_population,
            "recurrence_share": policy.recurrence_share,
            "recurrence_minimum": policy.recurrence_minimum,
        },
        "baseline": _batch_block(baseline, baseline_result),
    }
    if candidate is not None and candidate_result is not None:
        manifest["candidate"] = _batch_block(candidate, candidate_result)
        manifest["candidate"]["details"] = _jsonable(candidate_result.details)
    return manifest


def _batch_block(batch: Batch, result: Qualification) -> dict:
    return {
        "batch_id": batch.batch_id,
        "label": batch.label,
        "files": {
            name: {
                "path": batch.relative_paths()[name],
                "sha256": batch.checksums[name],
                "rows": batch.row_counts()[name],
            }
            for name in batch.frames
        },
        "status": result.status,
        "counts": result.counts,
        "rules_triggered": result.findings["rule_id"].tolist() if not result.findings.empty else [],
    }


def _jsonable(value: object) -> object:
    """Rend une structure serialisable sans perdre d'information utile."""
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def write_manifest(manifest: dict, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def verify_untouched(batch: Batch) -> list[str]:
    """Verifie qu'aucun fichier du lot n'a bouge pendant la qualification."""
    return [
        name
        for name, path in batch.paths.items()
        if file_sha256(path) != batch.checksums[name]
    ]
