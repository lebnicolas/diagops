"""Gel du candidat M4 — irréversible, et daté.

Ce script fait trois choses, dans cet ordre, et une seule fois :

1. **il fige le candidat** — modèle, features, seuil, graine, versions — et le
   sérialise ;
2. **il ouvre le test scellé**, pour la première fois. C'est l'acte que le gel
   autorise : jusqu'ici `sensor_test.csv` n'avait jamais été chargé ;
3. **il produit les prédictions** à remettre au formateur, qui calculera les
   métriques finales sur son oracle.

Le test ne porte pas de colonne `provenance` : aucune auto-évaluation n'est
possible ici, et c'est voulu. La seule chose que ce script rapporte du test est
la **répartition de nos propres prédictions**, qui n'utilise aucune étiquette.

Après exécution, toute modification des features, du seuil ou du modèle impose un
nouveau gel et interdit la comparaison au résultat précédent — voir la règle de
changement de `docs/protocole_evaluation.md`.

Usage :
    python run_gel.py [--output ./results/gel]
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd

from src.modele import NOMS_FEATURES, candidats, etiquettes, features_fenetre, table_features
from src.protocole import (
    CLASSE_NEGATIVE,
    CLASSE_POSITIVE,
    COLONNE_FENETRE,
    COLONNE_GROUPE,
    SEED,
    TEST_SCELLE,
    baseline_deux_niveaux,
    charger_calibration,
    commit_courant,
    empreintes,
    environnement,
    sha256,
    table_fenetres,
)


#: Candidat retenu à l'issue de l'étape 3 — voir `docs/benchmark_modele.md`.
CANDIDAT = "regression_logistique"

#: Seuil de décision, conservé après mesure — voir `run_seuil.py`.
SEUIL = 0.50


def table_test() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Charge le test scellé et construit ses features.

    Aucune colonne `provenance` n'est attendue : sa présence signalerait que le
    fichier n'est plus scellé, et le script s'arrête.
    """
    lignes = pd.read_csv(TEST_SCELLE)
    if "provenance" in lignes.columns:
        raise SystemExit(
            "sensor_test.csv porte une colonne provenance — le test n'est plus "
            "scellé, le gel est refusé"
        )

    fenetres = (
        lignes.groupby(COLONNE_FENETRE)
        .agg(
            equipment_id=("equipment_id", "first"),
            sensor_name=("sensor_name", "first"),
            unit=("unit", "first"),
            lignes=("value", "size"),
        )
        .reset_index()
    )
    calculees = pd.DataFrame(
        [
            {COLONNE_FENETRE: identifiant, **features_fenetre(groupe)}
            for identifiant, groupe in lignes.groupby(COLONNE_FENETRE, sort=True)
        ]
    )
    table = fenetres.merge(calculees, on=COLONNE_FENETRE, how="left", validate="one_to_one")
    if table[NOMS_FEATURES].isna().any().any():
        raise ValueError("features manquantes sur le test")
    return lignes, table


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="./results/gel", type=Path)
    arguments = parser.parse_args()
    sortie: Path = arguments.output
    sortie.mkdir(parents=True, exist_ok=True)

    # --- 1. le candidat, ajusté sur la totalité de la calibration -----------
    lignes = charger_calibration()
    fenetres = table_fenetres(lignes)
    table = table_features(lignes, fenetres)
    y = etiquettes(table)

    modele = candidats()[CANDIDAT]
    modele.fit(table[NOMS_FEATURES].to_numpy(), y.to_numpy())

    chemin_modele = sortie / "candidat_m4.joblib"
    joblib.dump(modele, chemin_modele)

    print("Candidat gelé")
    print(f"  modèle                 {CANDIDAT}")
    print(f"  features               {len(NOMS_FEATURES)}")
    print(f"  seuil de décision      {SEUIL}")
    print(f"  graine                 {SEED}")
    print(f"  ajusté sur             {len(table)} fenêtres, {int(y.sum())} fabriquées")
    print(f"  empreinte du modèle    {sha256(chemin_modele)[:16]}…")

    # --- 2. ouverture du test scellé ---------------------------------------
    print(f"\nOuverture du test scellé — {TEST_SCELLE}")
    lignes_test, table_test_features = table_test()
    print(f"  {len(lignes_test)} lignes, {len(table_test_features)} fenêtres")
    print("  colonne provenance     absente (scellé confirmé)")

    # --- 3. prédictions à remettre au formateur ----------------------------
    probabilites = modele.predict_proba(table_test_features[NOMS_FEATURES].to_numpy())[:, 1]
    predictions = pd.DataFrame(
        {
            COLONNE_FENETRE: table_test_features[COLONNE_FENETRE],
            COLONNE_GROUPE: table_test_features[COLONNE_GROUPE],
            "sensor_name": table_test_features["sensor_name"],
            "probabilite_fabriquee": probabilites.round(6),
            "prediction": [
                CLASSE_POSITIVE if p >= SEUIL else CLASSE_NEGATIVE for p in probabilites
            ],
        }
    )
    predictions.to_csv(sortie / "predictions_test.csv", index=False, encoding="utf-8")

    repartition = predictions["prediction"].value_counts().to_dict()
    print("\nPrédictions produites — aucune étiquette n'a été consultée")
    for classe, nombre in repartition.items():
        print(f"  {classe:<14} {nombre:>3} fenêtres ({nombre / len(predictions):.1%})")
    print(
        f"  taux de calibration    "
        f"{int(y.sum())}/{len(table)} fabriquées ({y.mean():.1%})"
    )

    # --- le procès-verbal ---------------------------------------------------
    baseline = baseline_deux_niveaux()
    gel = {
        "date_de_gel": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "commit": commit_courant(),
        "candidat": CANDIDAT,
        "seuil_de_decision": SEUIL,
        "graine": SEED,
        "features": NOMS_FEATURES,
        "ajuste_sur": {
            "fenetres": int(len(table)),
            "fabriquees": int(y.sum()),
            "lignes": int(len(lignes)),
        },
        "performance_attendue_calibration": {
            "source": "results/modele/modele.json — F1 hors pli, 5 partitions",
            "f1_moyen": 0.6940,
            "f1_ecart_type": 0.0684,
            "f1_min": 0.6000,
            "f1_max": 0.8000,
            "precision": 0.700,
            "rappel": 0.636,
            "roc_auc": 0.737,
        },
        "baseline_m3": baseline["par_fenetre"],
        "test": {
            "fichier": str(TEST_SCELLE),
            "empreinte": sha256(TEST_SCELLE),
            "lignes": int(len(lignes_test)),
            "fenetres": int(len(table_test_features)),
            "colonne_provenance_absente": True,
            "repartition_predictions": repartition,
        },
        "empreintes_entrees": empreintes(),
        "empreinte_modele": sha256(chemin_modele),
        "environnement": environnement(),
        "regle_de_changement": (
            "Toute modification des features, du seuil, du modèle, de la partition "
            "ou de la graine impose un nouveau gel et interdit la comparaison au "
            "résultat de celui-ci."
        ),
    }
    (sortie / "gel.json").write_text(
        json.dumps(gel, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )

    print(f"\nGel écrit dans {sortie}")
    print("  candidat_m4.joblib · predictions_test.csv · gel.json")
    print("\nÀ remettre au formateur : predictions_test.csv et gel.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
