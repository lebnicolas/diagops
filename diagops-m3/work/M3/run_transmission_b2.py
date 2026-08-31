"""Brief 2, étape 6 — décider ce qui est transmis à M4.

Trois choses sont produites ici, dans cet ordre :

1. **le jeu transmis** — chaque ligne porte sa provenance et le procédé qui l'a
   produite, sous le contrat écrit dans `src/brief2/provenance.py` ;
2. **les biais**, rattachés à des comptages calculés sur les données et non
   cités de mémoire, avec ce que la fabrication corrige et ce qu'elle amplifie ;
3. **l'effet mesuré de la transmission** sur la couverture — avant / après, en
   distinguant systématiquement ce qui est réel de ce qui est fabriqué.

Décision retenue (arbitrage tranché le 31/08) : **une partie sous conditions**.
Le réel complet, plus les 1 799 mesures synthétiques de `PROC-GEN-SMOTE-V2` sur
les 8 équipements de `SITE-OUEST ∩ SEG-2`, étiquetées, réservées à l'exploration
et au rodage de pipeline, **interdites d'usage en évaluation**. Le motif est dans
nos propres résultats : le générateur s'est amélioré entre V1 et V2 et le
détecteur de référence a rendu le même zéro dans les deux cas (T2-01). Nous
n'avons donc aucune preuve de fidélité — seulement une absence de signalement —
et la dispersion reste contractée de 10 à 14 % (ratios σ 0,858 et 0,897).

Usage :
    python run_transmission_b2.py [--output ./output/transmission]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from src.brief2.provenance import (
    COLONNES_TRANSMISES,
    ECHEANCE_REEXAMEN,
    etiqueter,
    normaliser_precision,
    procedes_transmis,
    registre_dataframe,
    verifier_contrat,
)
from src.brief2.seed import SEED
from src.brief2.sources import load_prepared, prepared_checksums
from src.data_pipeline.io import file_sha256


GENERATION_DIR = Path("output") / "generation"

# Fenêtre de rapprochement du brief 1 — reprise à l'identique pour que la
# couverture « avant » soit comparable à celle qui a été publiée.
FENETRE_AVANT_H = 48
FENETRE_APRES_H = 24

CRITICITES = ("critical", "high", "medium", "low")


def composer_jeu_transmis(
    prepared: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, int]:
    """Assemble le jeu de mesures transmis à M4, étiqueté ligne à ligne.

    Rend le jeu et le nombre de valeurs dont la précision a été ramenée à la
    convention de la livraison par `R-TRA-001`.
    """
    reel = etiqueter(prepared["sensors"], "réelle", "")

    morceaux = [reel]
    for procede in procedes_transmis():
        chemin = GENERATION_DIR / f"mesures_{procede.procedure_id}.csv"
        if not chemin.is_file():
            raise FileNotFoundError(
                f"{chemin} absent — rejouer `python run_generation_b2.py`."
            )
        fabrique = pd.read_csv(chemin)
        # Le fichier de génération porte déjà provenance et procedure_id ;
        # l'étiquetage est réappliqué pour que le contrat vienne d'un seul
        # endroit, quel que soit le producteur du fichier.
        morceaux.append(etiqueter(fabrique, procede.provenance, procede.procedure_id))

    jeu = pd.concat(morceaux, ignore_index=True)
    jeu = jeu.sort_values(["equipment_id", "sensor_name", "timestamp"], kind="stable")
    jeu, precision_corrigees = normaliser_precision(jeu.reset_index(drop=True))
    return jeu, precision_corrigees


def couverture(
    equipment: pd.DataFrame, mesures: pd.DataFrame, etiquette: str
) -> pd.DataFrame:
    """Couverture instrumentale du parc, par site et par criticité."""
    instrumentes = set(mesures["equipment_id"].unique())
    lignes = []

    for variable, colonne in (("site", "site_id"), ("criticité", "criticality")):
        for modalite, groupe in equipment.groupby(colonne, observed=True):
            couverts = len(set(groupe["equipment_id"]) & instrumentes)
            lignes.append(
                {
                    "etat": etiquette,
                    "variable": variable,
                    "modalite": modalite,
                    "equipements": int(len(groupe)),
                    "instrumentes": couverts,
                    "taux_pct": round(100 * couverts / len(groupe), 2),
                }
            )

    couverts = len(set(equipment["equipment_id"]) & instrumentes)
    lignes.append(
        {
            "etat": etiquette,
            "variable": "parc",
            "modalite": "total",
            "equipements": int(len(equipment)),
            "instrumentes": couverts,
            "taux_pct": round(100 * couverts / len(equipment), 2),
        }
    )
    return pd.DataFrame(lignes)


def evenements_documentes(
    events: pd.DataFrame, mesures: pd.DataFrame
) -> tuple[int, pd.DataFrame]:
    """Événements disposant d'au moins une mesure dans leur fenêtre.

    Rend le total et le détail par gravité — c'est la gravité qui porte le biais
    d'étiquetage, pas le type d'événement.
    """
    mesures = mesures.copy()
    mesures["timestamp"] = pd.to_datetime(mesures["timestamp"], utc=True, errors="coerce")
    par_equipement = {
        equipement: groupe["timestamp"].to_numpy()
        for equipement, groupe in mesures.groupby("equipment_id", observed=True)
    }

    evenements = events.copy()
    evenements["start_at"] = pd.to_datetime(evenements["start_at"], utc=True, errors="coerce")
    debut = evenements["start_at"] - pd.Timedelta(hours=FENETRE_AVANT_H)
    fin = evenements["start_at"] + pd.Timedelta(hours=FENETRE_APRES_H)

    documente = []
    for equipement, borne_min, borne_max in zip(
        evenements["equipment_id"], debut, fin, strict=True
    ):
        horodatages = par_equipement.get(equipement)
        if horodatages is None or pd.isna(borne_min):
            documente.append(False)
            continue
        documente.append(bool(((horodatages >= borne_min) & (horodatages <= borne_max)).any()))
    evenements["documente"] = documente

    detail = (
        evenements.groupby("severity", observed=True)
        .agg(evenements=("event_id", "size"), documentes=("documente", "sum"))
        .reindex(list(CRITICITES))
        .reset_index()
    )
    detail["documentes"] = detail["documentes"].astype(int)
    detail["part_pct"] = (100 * detail["documentes"] / detail["evenements"]).round(2)
    return int(evenements["documente"].sum()), detail


def comptages_biais(
    prepared: dict[str, pd.DataFrame],
    jeu: pd.DataFrame,
    avant: pd.DataFrame,
    apres: pd.DataFrame,
) -> pd.DataFrame:
    """Les comptages qui adossent chaque biais à un chiffre vérifiable."""
    equipment = prepared["equipment"]
    events = prepared["events"]
    maintenance = prepared["maintenance"]
    reel = jeu[jeu["provenance"] == "réelle"]

    parc = len(equipment)
    instrumentes_reels = reel["equipment_id"].nunique()
    instrumentes_apres = jeu["equipment_id"].nunique()

    ouest = equipment[equipment["site_id"] == "SITE-OUEST"]
    mnt_ouest = maintenance[maintenance["equipment_id"].isin(set(ouest["equipment_id"]))]
    cout_absent = maintenance["parts_cost_eur"].isna()
    cout_absent_ouest = int((cout_absent & maintenance["equipment_id"].isin(set(ouest["equipment_id"]))).sum())

    documentes_avant, gravite_reel = evenements_documentes(events, reel)
    documentes_apres, _ = evenements_documentes(events, jeu)

    critical = gravite_reel[gravite_reel["severity"] == "critical"].iloc[0]
    critical_total = int(critical["evenements"])
    critical_documentes = int(critical["documentes"])

    # Ce que la génération pouvait espérer documenter : les événements des
    # équipements générés, tombant dans la période générée. Le gain constaté
    # doit être lu contre cette borne, pas contre les 514 événements du parc.
    perimetre = set(jeu.loc[jeu["provenance"] == "synthétique", "equipment_id"].unique())
    fabrique = jeu[jeu["provenance"] == "synthétique"].copy()
    fabrique["timestamp"] = pd.to_datetime(fabrique["timestamp"], utc=True, errors="coerce")
    debut_generation = fabrique["timestamp"].min() - pd.Timedelta(hours=FENETRE_APRES_H)
    fin_generation = fabrique["timestamp"].max() + pd.Timedelta(hours=FENETRE_AVANT_H)

    evenements_perimetre_frame = events[events["equipment_id"].isin(perimetre)].copy()
    evenements_perimetre = int(len(evenements_perimetre_frame))
    debuts = pd.to_datetime(evenements_perimetre_frame["start_at"], utc=True, errors="coerce")
    evenements_perimetre_periode = int(
        ((debuts >= debut_generation) & (debuts <= fin_generation)).sum()
    )

    types = equipment["equipment_type"].value_counts()
    types_instrumentes = set(
        equipment.loc[equipment["equipment_id"].isin(set(reel["equipment_id"])), "equipment_type"]
    )

    sans_evenement = parc - events["equipment_id"].nunique()
    sans_intervention = parc - maintenance["equipment_id"].nunique()
    correctives = int((maintenance["intervention_type"] == "corrective").sum())

    taux = lambda frame, variable, modalite: float(  # noqa: E731
        frame[(frame["variable"] == variable) & (frame["modalite"] == modalite)]["taux_pct"].iloc[0]
    )

    lignes = [
        {
            "biais": "B1 — couverture instrumentale",
            "indicateur": "équipements avec au moins une mesure réelle",
            "valeur": f"{instrumentes_reels} / {parc}",
            "chiffre": round(100 * instrumentes_reels / parc, 2),
        },
        {
            "biais": "B1 — couverture instrumentale",
            "indicateur": "SITE-OUEST, mesures réelles",
            "valeur": f"0 / {len(ouest)}",
            "chiffre": 0.0,
        },
        {
            "biais": "B1 — couverture instrumentale",
            "indicateur": "écart de taux critical / low (réel)",
            "valeur": f"{taux(avant, 'criticité', 'critical')} % contre {taux(avant, 'criticité', 'low')} %",
            "chiffre": round(taux(avant, "criticité", "critical") / max(taux(avant, "criticité", "low"), 1e-9), 2),
        },
        {
            "biais": "B1 — couverture instrumentale",
            "indicateur": "types d'équipement sans aucune mesure réelle",
            "valeur": f"{len(types) - len(types_instrumentes)} / {len(types)}",
            "chiffre": float(len(types) - len(types_instrumentes)),
        },
        {
            "biais": "B1 — couverture instrumentale",
            "indicateur": "équipements couverts après transmission (dont fabriqué)",
            "valeur": f"{instrumentes_apres} / {parc} dont {instrumentes_apres - instrumentes_reels} fabriqués",
            "chiffre": round(100 * instrumentes_apres / parc, 2),
        },
        {
            "biais": "B2 — étiquetage des événements",
            "indicateur": "événements documentés par au moins une mesure réelle",
            "valeur": f"{documentes_avant} / {len(events)}",
            "chiffre": round(100 * documentes_avant / len(events), 2),
        },
        {
            "biais": "B2 — étiquetage des événements",
            "indicateur": "événements documentés après transmission",
            "valeur": f"{documentes_apres} / {len(events)}",
            "chiffre": round(100 * documentes_apres / len(events), 2),
        },
        {
            "biais": "B2 — étiquetage des événements",
            "indicateur": "événements de gravité critical documentés (réel)",
            "valeur": f"{critical_documentes} / {critical_total}",
            "chiffre": round(100 * critical_documentes / max(critical_total, 1), 2),
        },
        {
            "biais": "B2 — étiquetage des événements",
            "indicateur": "événements du périmètre généré, dans la période générée",
            "valeur": f"{evenements_perimetre_periode} sur {evenements_perimetre} du périmètre",
            "chiffre": float(evenements_perimetre_periode),
        },
        {
            "biais": "B3 — renseignement non aléatoire",
            "indicateur": "interventions sans coût de pièces",
            "valeur": f"{int(cout_absent.sum())} / {len(maintenance)}",
            "chiffre": round(100 * int(cout_absent.sum()) / len(maintenance), 2),
        },
        {
            "biais": "B3 — renseignement non aléatoire",
            "indicateur": "dont SITE-OUEST",
            "valeur": f"{cout_absent_ouest} / {int(cout_absent.sum())}",
            "chiffre": round(100 * cout_absent_ouest / max(int(cout_absent.sum()), 1), 2),
        },
        {
            "biais": "B3 — renseignement non aléatoire",
            "indicateur": "part des interventions SITE-OUEST sans coût",
            "valeur": f"{cout_absent_ouest} / {len(mnt_ouest)}",
            "chiffre": round(100 * cout_absent_ouest / max(len(mnt_ouest), 1), 2),
        },
        {
            "biais": "B4 — historique d'activité",
            "indicateur": "équipements sans aucun événement enregistré",
            "valeur": f"{sans_evenement} / {parc}",
            "chiffre": round(100 * sans_evenement / parc, 2),
        },
        {
            "biais": "B4 — historique d'activité",
            "indicateur": "équipements sans aucune intervention",
            "valeur": f"{sans_intervention} / {parc}",
            "chiffre": round(100 * sans_intervention / parc, 2),
        },
        {
            "biais": "B4 — historique d'activité",
            "indicateur": "interventions correctives",
            "valeur": f"{correctives} / {len(maintenance)}",
            "chiffre": round(100 * correctives / len(maintenance), 2),
        },
        {
            "biais": "B5 — représentation",
            "indicateur": "rapport d'effectifs entre types d'équipement",
            "valeur": (
                f"{types.max()} ({types.idxmax()}) contre {types.min()} "
                f"({', '.join(sorted(types[types == types.min()].index))})"
            ),
            "chiffre": round(types.max() / types.min(), 2),
        },
        {
            "biais": "B5 — représentation",
            "indicateur": "rapport d'effectifs entre sites",
            "valeur": (
                f"{int(equipment['site_id'].value_counts().max())} contre "
                f"{int(equipment['site_id'].value_counts().min())}"
            ),
            "chiffre": round(
                equipment["site_id"].value_counts().max()
                / equipment["site_id"].value_counts().min(),
                2,
            ),
        },
        {
            "biais": "B5 — représentation",
            "indicateur": "part fabriquée du jeu transmis",
            "valeur": f"{int((jeu['provenance'] != 'réelle').sum())} / {len(jeu)}",
            "chiffre": round(100 * int((jeu["provenance"] != "réelle").sum()) / len(jeu), 2),
        },
    ]
    return pd.DataFrame(lignes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="./output/transmission", type=Path)
    arguments = parser.parse_args()

    sortie: Path = arguments.output
    sortie.mkdir(parents=True, exist_ok=True)

    prepared = load_prepared()
    jeu, precision_corrigees = composer_jeu_transmis(prepared)

    print("Composition du jeu transmis")
    repartition = jeu.groupby(["provenance", "procedure_id"], dropna=False).size()
    for (provenance, procede), lignes in repartition.items():
        etiquette = procede if procede else "—"
        print(f"  {provenance:<14} {etiquette:<22} {lignes:>7} lignes")
    print(f"  {'total':<14} {'':<22} {len(jeu):>7} lignes")
    print(
        f"\n  R-TRA-001 — précision ramenée à 2 décimales : "
        f"{precision_corrigees} valeurs modifiées"
    )

    rapport = verifier_contrat(jeu)
    print("\nContrat de provenance")
    for cle in (
        "colonnes_conformes",
        "provenance_absente",
        "provenance_hors_domaine",
        "fabriquees_sans_procede",
        "reelles_portant_un_procede",
    ):
        print(f"  {cle:<28} {rapport[cle]}")
    print(f"  {'conforme':<28} {rapport['conforme']}")
    if not rapport["conforme"]:
        raise SystemExit("contrat de provenance non respecté — transmission interrompue")

    reel = jeu[jeu["provenance"] == "réelle"]
    avant = couverture(prepared["equipment"], reel, "avant transmission (réel seul)")
    apres = couverture(prepared["equipment"], jeu, "après transmission (réel + fabriqué)")
    couvertures = pd.concat([avant, apres], ignore_index=True)

    _, gravite_avant = evenements_documentes(prepared["events"], reel)
    _, gravite_apres = evenements_documentes(prepared["events"], jeu)
    gravite_avant["etat"] = "avant"
    gravite_apres["etat"] = "après"
    gravites = pd.concat([gravite_avant, gravite_apres], ignore_index=True)

    biais = comptages_biais(prepared, jeu, avant, apres)

    print("\nCouverture du parc")
    for etat, groupe in couvertures[couvertures["variable"] == "parc"].groupby("etat"):
        ligne = groupe.iloc[0]
        print(f"  {etat:<34} {ligne['instrumentes']:>3} / {ligne['equipements']} ({ligne['taux_pct']} %)")

    print("\nComptages des biais")
    for _, ligne in biais.iterrows():
        print(f"  {ligne['biais']:<32} {ligne['indicateur']:<52} {ligne['valeur']}")

    chemin_jeu = sortie / "sensor_readings_m4.csv"
    jeu.to_csv(chemin_jeu, index=False, encoding="utf-8")
    registre_dataframe().to_csv(sortie / "registre_procedes.csv", index=False, encoding="utf-8")
    biais.to_csv(sortie / "biais.csv", index=False, encoding="utf-8")
    couvertures.to_csv(sortie / "couverture_transmission.csv", index=False, encoding="utf-8")
    gravites.to_csv(sortie / "documentation_par_gravite.csv", index=False, encoding="utf-8")

    synthese = {
        "graine": SEED,
        "decision": "une partie sous conditions",
        "echeance_reexamen": ECHEANCE_REEXAMEN,
        "colonnes": list(COLONNES_TRANSMISES),
        "point_de_depart": prepared_checksums(),
        "empreinte_jeu_transmis": file_sha256(chemin_jeu),
        "volumes": {
            "total": int(len(jeu)),
            "reelles": int((jeu["provenance"] == "réelle").sum()),
            "synthetiques": int((jeu["provenance"] == "synthétique").sum()),
            "augmentees": int((jeu["provenance"] == "augmentée").sum()),
            "part_fabriquee_pct": round(
                100 * int((jeu["provenance"] != "réelle").sum()) / len(jeu), 2
            ),
        },
        "contrat": rapport,
        "R-TRA-001_valeurs_corrigees": precision_corrigees,
        "procedes": registre_dataframe().to_dict(orient="records"),
        "couverture": couvertures.to_dict(orient="records"),
        "documentation_par_gravite": gravites.to_dict(orient="records"),
        "biais": biais.to_dict(orient="records"),
    }
    (sortie / "transmission.json").write_text(
        json.dumps(synthese, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    print(f"\nSorties écrites dans {sortie}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
