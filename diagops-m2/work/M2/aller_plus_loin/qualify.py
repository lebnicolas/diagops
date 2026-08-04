"""Qualification d'une livraison DiagOps, rejouable d'une seule commande.

    cd work/M2
    python aller_plus_loin/qualify.py                       # baseline + candidat
    python aller_plus_loin/qualify.py --batch <batch_id>    # un lot precis
    python aller_plus_loin/qualify.py --baseline-only       # non-regression seule

Codes de sortie, distincts a dessein :

    0   tous les lots qualifies sont ACCEPTED ou ACCEPTED_WITH_WARNINGS
    1   au moins un lot est REJECTED — echec metier
    2   echec technique : fichier absent, politique invalide, source modifiee

La chaine d'integration a besoin de separer les deux : une livraison rejetee
est un resultat, un fichier manquant est une panne. Les confondre revient a
traiter un mauvais lot comme un bug de CI.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
WORK_M2 = HERE.parent
for entry in (WORK_M2, HERE):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from qualification.batch import load_batch  # noqa: E402
from qualification.policy import (  # noqa: E402
    PolicyError,
    conforms,
    load_batches,
    load_policy,
)
from qualification.qualify import qualify  # noqa: E402
from qualification.report import (  # noqa: E402
    build_manifest,
    render_run_summary,
    verify_untouched,
    write_manifest,
    write_reports,
)


DEFAULT_DATA_DIR = WORK_M2.parents[1] / "data_pack" / "2026-S1"

EXIT_OK = 0
EXIT_REJECTED = 1
EXIT_TECHNICAL = 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Qualification d'une livraison DiagOps.")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--policy", type=Path, default=HERE / "config" / "quality_rules.yaml")
    parser.add_argument("--batches", type=Path, default=HERE / "config" / "batches.yaml")
    parser.add_argument("--reports", type=Path, default=HERE / "reports")
    parser.add_argument("--manifest", type=Path, default=HERE / "run_manifest.json")
    parser.add_argument("--batch", help="batch_id d'une livraison candidate a qualifier")
    parser.add_argument(
        "--summary",
        type=Path,
        help="ecrit un resume consolide en Markdown (destine a $GITHUB_STEP_SUMMARY)",
    )
    parser.add_argument("--baseline-only", action="store_true", help="controle de non-regression seul")
    parser.add_argument(
        "--date",
        default="2026-08-04",
        help="date de reference des controles de non-anteriorite (reproductibilite)",
    )
    args = parser.parse_args(argv)

    try:
        policy = load_policy(args.policy)
        catalogue = load_batches(args.batches)
        baseline = load_batch(catalogue["baseline"], args.data_dir)
    except (PolicyError, FileNotFoundError, KeyError) as error:
        print(f"ECHEC TECHNIQUE : {error}", file=sys.stderr)
        return EXIT_TECHNICAL

    reference_date = pd.Timestamp(args.date)
    print(f"Politique {policy.version} ({policy.checksum[:12]}…)")
    print(f"Donnees   {args.data_dir}")

    # ------------------------------------------------------------------
    # Non-regression : la politique reste-t-elle applicable au publie ?
    # ------------------------------------------------------------------
    baseline_result = qualify(baseline, baseline, policy, reference_date, is_baseline=True)
    _print_result(baseline_result)
    write_reports(baseline_result, args.reports / "baseline")

    candidate = None
    candidate_result = None
    verdicts: list[dict] = [
        _verdict(baseline.batch_id, baseline_result.status, None)
    ]

    if not args.baseline_only:
        entries = catalogue.get("candidates") or []
        if args.batch:
            entries = [entry for entry in entries if entry["batch_id"] == args.batch]
            if not entries:
                print(f"ECHEC TECHNIQUE : lot inconnu du catalogue — {args.batch}", file=sys.stderr)
                return EXIT_TECHNICAL
        if entries:
            try:
                candidate = load_batch(entries[0], args.data_dir)
            except FileNotFoundError as error:
                print(f"ECHEC TECHNIQUE : {error}", file=sys.stderr)
                return EXIT_TECHNICAL
            candidate_result = qualify(candidate, baseline, policy, reference_date)
            _print_result(candidate_result)
            write_reports(candidate_result, args.reports / "candidate_release")
            try:
                verdict = _verdict(
                    candidate.batch_id,
                    candidate_result.status,
                    entries[0].get("expected_status"),
                )
            except PolicyError as error:
                print(f"ECHEC TECHNIQUE : {error}", file=sys.stderr)
                return EXIT_TECHNICAL
            verdicts.append(verdict)
            print(f"  attendu  {verdict['expected'] or '(aucune decision anterieure)'}")
            print(
                f"  verdict  {'CONFORME' if verdict['conforms'] else 'NON CONFORME'}"
                f" — {verdict['explanation']}"
            )

    # ------------------------------------------------------------------
    # Aucune source ne doit avoir bouge
    # ------------------------------------------------------------------
    touched = verify_untouched(baseline) + (verify_untouched(candidate) if candidate else [])
    if touched:
        print(f"ECHEC TECHNIQUE : source modifiee pendant la qualification — {touched}", file=sys.stderr)
        return EXIT_TECHNICAL

    decision = (candidate_result or baseline_result).status
    manifest = build_manifest(
        baseline=baseline,
        candidate=candidate,
        policy=policy,
        baseline_result=baseline_result,
        candidate_result=candidate_result,
        reference_date=reference_date,
        decision=decision,
    )
    manifest["run"]["conformity"] = verdicts
    write_manifest(manifest, args.manifest)
    print(f"\nManifeste : {args.manifest}")
    print("Sources inchangees : empreintes identiques avant et apres.")

    if args.summary:
        results = [baseline_result] + ([candidate_result] if candidate_result else [])
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        with args.summary.open("a", encoding="utf-8") as handle:
            handle.write(render_run_summary(manifest, results))
        print(f"Resume    : {args.summary}")

    # Le code de sortie suit la CONFORMITE, pas le statut brut. Un lot dont le
    # rejet est acte et declare au catalogue n'a plus a signaler indefiniment
    # un echec dont la conclusion est deja tiree ; en revanche tout ecart entre
    # le statut obtenu et la decision inscrite fait echouer la chaine.
    if not all(verdict["conforms"] for verdict in verdicts):
        return EXIT_REJECTED
    return EXIT_OK


def _verdict(batch_id: str, observed: str, expected: str | None) -> dict:
    ok, explanation = conforms(observed, expected)
    return {
        "batch_id": batch_id,
        "observed": observed,
        "expected": expected,
        "conforms": ok,
        "explanation": explanation,
    }


def _print_result(result) -> None:
    counts = result.counts
    print(f"\n{result.label}  [{result.batch_id}]")
    print(f"  statut   {result.status}")
    print(
        f"  constats {counts.get('error', 0)} erreur(s), "
        f"{counts.get('warning', 0)} avertissement(s), {counts.get('info', 0)} information(s)"
    )
    for _, row in result.findings.iterrows():
        flag = "^" if row["escalated"] else " "
        print(
            f"   {row['level']:<7}{flag} {row['rule_id']:<12} {row['source']:<12} "
            f"{row['failures']:>5} ({row['failure_rate']:.2%})"
        )


if __name__ == "__main__":
    raise SystemExit(main())
