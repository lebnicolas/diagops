"""Brief 2, étape 4, sens 1 — soumettre nos productions au détecteur de référence.

Le brief exige que chaque exécution de `tools/verify_synthetic.py` soit
consignée **avec l'hypothèse qui l'a motivée**, écrite avant le lancement. Ces
hypothèses sont donc inscrites ici, dans le code, à côté du fichier soumis :
elles sont figées au moment où le script est écrit, pas rédigées après lecture
des comptages. Une série d'essais sans hypothèse n'est pas une démarche, et
l'omission est un critère bloquant.

Deux témoins ouvrent la série, et ce sont eux qui rendent le reste lisible :

- `T1-00`, la livraison de référence du module elle-même, telle qu'elle est
  publiée ;
- `T1-01`, un extrait de **notre** préparation du brief 1, sur le périmètre et
  les capteurs de nos fabrications.

Tous deux sont authentiques. S'ils déclenchent des règles — et le brief annonce
que les lignes réelles portent les anomalies de qualité de la livraison — alors
« zéro signalement » ne peut plus se lire comme « authentique », et seul l'écart
au témoin est interprétable.

Le tour 1 soumet les fichiers **tels qu'ils sortent des étapes 2 et 3**, sans
retouche : c'est une photographie de l'état réel de nos productions, y compris
de ce qui leur manque.

Usage :
    python run_detection_b2.py [--output ./output/detection]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from run_generation_b2 import CAPTEURS, DEBUT, FIN, SEGMENT_CIBLE, SITE_CIBLE
from src.brief2.augmentation import LAGS_STRUCTURE, profil_autocorrelation
from src.brief2.detection import (
    preparer_pour_detecteur,
    resume_soumission,
    soumettre,
    table_distributions,
)
from src.brief2.generation import (
    K_VOISINS,
    contexte_generation,
    generer_par_interpolation,
    grille_horaire,
)
from src.brief2.seed import SEED, rng
from src.brief2.sources import load_prepared


WORK_ROOT = Path(__file__).resolve().parent
MODULE_ROOT = WORK_ROOT.parents[1]
PACK_SENSORS = MODULE_ROOT / "data_pack" / "2026-S1" / "sensors" / "sensor_readings.csv"

GENERATION_DIR = WORK_ROOT / "output" / "generation"
AUGMENTATION_DIR = WORK_ROOT / "output" / "augmentation"

# Périmètre du témoin : celui des fabrications de l'étape 3 — janvier 2026, les
# deux capteurs générés. Le témoin doit ressembler à ce qu'il sert à comparer,
# sinon son taux de signalement n'est pas une référence mais une autre mesure.
CAPTEURS_TEMOIN = ("vibration_mm_s", "temperature_c")
TEMOIN_DEBUT = pd.Timestamp("2026-01-01T00:00:00Z")
TEMOIN_FIN = pd.Timestamp("2026-02-01T00:00:00Z")


def construire_temoin(destination: Path) -> tuple[Path, dict]:
    """Extrait des mesures authentiques sur le périmètre des fabrications.

    Aucune correction n'est appliquée : le témoin doit porter les défauts de la
    livraison, c'est tout son intérêt. La colonne de provenance est renseignée à
    `réelle` — c'est ce qu'elle est.
    """
    tables = load_prepared()
    sensors = tables["sensors"].copy()
    moments = pd.to_datetime(sensors["timestamp"], utc=True, format="mixed")
    fenetre = (
        (moments >= TEMOIN_DEBUT)
        & (moments < TEMOIN_FIN)
        & sensors["sensor_name"].isin(CAPTEURS_TEMOIN)
    )
    temoin = sensors.loc[fenetre].copy()
    temoin["provenance"] = "réelle"
    temoin["procedure_id"] = ""
    chemin = preparer_pour_detecteur(temoin, destination)
    resume = {
        "lignes": int(len(temoin)),
        "equipements": int(temoin["equipment_id"].nunique()),
        "capteurs": sorted(temoin["sensor_name"].unique()),
        "fenetre": [TEMOIN_DEBUT.isoformat(), TEMOIN_FIN.isoformat()],
    }
    return chemin, resume


def soumissions(temoin: Path) -> list[dict]:
    """Les neuf soumissions du tour 1, chacune avec son hypothèse préalable."""
    return [
        {
            "id": "T1-00",
            "chemin": PACK_SENSORS,
            "nature": "témoin — livraison de référence du module",
            "hypothese": (
                "La livraison publiée n'est pas exempte de défauts : le brief 2 "
                "annonce que les lignes authentiques du lot de contrôle portent "
                "les anomalies de qualité du M3. J'attends donc des comptages "
                "non nuls, surtout sur R-FORMAT et R-RANGE. R-DISTRIB sera "
                "trivialement conforme, ce fichier étant celui qui sert à "
                "calculer le profil de référence."
            ),
        },
        {
            "id": "T1-01",
            "chemin": temoin,
            "nature": "témoin — notre préparation du brief 1, janvier, 2 capteurs",
            "hypothese": (
                "Notre préparation conserve 5 lignes hors période et 720 hors "
                "grille de 6 h sur 50 277. Sur la fenêtre du témoin, j'attends "
                "un taux de signalement faible mais non nul, porté par R-FORMAT. "
                "C'est ce taux qui servira de seuil de lecture pour toutes les "
                "soumissions suivantes."
            ),
        },
        {
            "id": "T1-02",
            "chemin": GENERATION_DIR / "mesures_PROC-GEN-MARG-V1.csv",
            "nature": "génération — tirage marginal",
            "hypothese": (
                "Le tirage rejoue des valeurs observées sur une grille construite "
                "par nos soins : plage physique, unité, précision, période et pas "
                "de 6 h sont corrects par construction. J'attends **zéro ligne "
                "signalée** et une R-DISTRIB conforme — alors que l'étape 3 a "
                "mesuré une autocorrélation nulle (+0,02 au rang 2 contre −0,759 "
                "sur le réel). Si l'hypothèse se vérifie, ce fichier est la "
                "démonstration que le silence du détecteur ne prouve rien."
            ),
        },
        {
            "id": "T1-03",
            "chemin": GENERATION_DIR / "mesures_PROC-GEN-SMOTE-V1.csv",
            "nature": "génération — interpolation entre voisins",
            "hypothese": (
                "Même conformité de forme attendue, donc zéro ligne signalée. "
                "Le point à surveiller est le ratio d'écart-type de R-DISTRIB : "
                "l'étape 3 a mesuré une contraction de dispersion de 15 à 22 %, "
                "effet structurel de l'interpolation. Le détecteur signale sous "
                "0,70 ; j'attends un ratio inférieur à 1 mais au-dessus du seuil, "
                "donc un défaut réel visible dans le détail et non signalé."
            ),
        },
        {
            "id": "T1-04",
            "chemin": AUGMENTATION_DIR / "exemple_PROC-AUG-BRUIT.csv",
            "nature": "augmentation — bruit gaussien, σ = 2 % de l'écart-type",
            "hypothese": (
                "Un bruit de 2 % ne déplace ni le niveau ni la dispersion de "
                "façon mesurable. J'attends zéro ligne signalée. En revanche ce "
                "fichier ne porte pas de colonne `provenance` et traîne une "
                "colonne de travail `row_identifier` : le détecteur devrait le "
                "dire, et ce serait un manquement au contrat de transmission."
            ),
        },
        {
            "id": "T1-05",
            "chemin": AUGMENTATION_DIR / "exemple_PROC-AUG-ECHELLE.csv",
            "nature": "augmentation — mise à l'échelle ×1,05",
            "hypothese": (
                "Un défaut d'étalonnage de 5 % décale la moyenne d'environ 0,05 "
                "écart-type de référence, très en deçà du seuil de 0,8 utilisé "
                "par R-DISTRIB. J'attends donc **aucun signalement**, alors que "
                "la fiche de l'étape 2 classe ce procédé comme destructeur de "
                "l'ordre de grandeur. Le détecteur devrait laisser passer un "
                "défaut que nous avons nous-mêmes documenté."
            ),
        },
        {
            "id": "T1-06",
            "chemin": AUGMENTATION_DIR / "exemple_PROC-AUG-DECALAGE.csv",
            "nature": "augmentation — décalage temporel de +18 h",
            "hypothese": (
                "18 h est un multiple de 6 h : la grille est préservée et R-FORMAT "
                "ne devrait se déclencher que sur les lignes poussées hors de la "
                "période. Comme la série de départ commence avant le 1er janvier, "
                "j'attends un R-FORMAT faible mais non nul, sans autre famille."
            ),
        },
        {
            "id": "T1-07",
            "chemin": AUGMENTATION_DIR / "exemple_PROC-AUG-PERMUT.csv",
            "nature": "augmentation — permutation de blocs de 24 h",
            "hypothese": (
                "La permutation conserve la population de valeurs **exactement** "
                "et ne touche pas aux horodatages. Toutes les familles de règles "
                "regardent la ligne, jamais l'ordre : j'attends zéro signalement "
                "sur une série dont la structure temporelle est détruite. C'est "
                "le second cas d'aveuglement, et le plus net des deux."
            ),
        },
        {
            "id": "T1-08",
            "chemin": AUGMENTATION_DIR / "exemple_PROC-AUG-DEFORM.csv",
            "nature": "augmentation — déformation de l'axe temporel ×U(0,75 ; 1,25)",
            "hypothese": (
                "Chaque intervalle est étiré ou comprimé : les horodatages "
                "quittent la grille de 6 h dès la première déformation. J'attends "
                "un R-FORMAT proche de la totalité des lignes. Ce serait le seul "
                "de nos procédés que le détecteur attrape franchement — et il "
                "l'attrape parce que le défaut est visible ligne à ligne, pas "
                "parce qu'il comprend la série."
            ),
        },
    ]


# --------------------------------------------------------------------------
# Tour 2 — corriger, puis resoumettre
# --------------------------------------------------------------------------

# Bornes du coefficient d'interpolation, élargies après le tour 1. Avec les
# bornes canoniques (0 ; 1) tout point fabriqué est intérieur au segment joignant
# ses deux parents, ce qui contracte mécaniquement la dispersion — mesurée à
# 0,783 et 0,810 fois l'écart-type de référence. L'extrapolation corrige la
# cause ; son coût attendu est le franchissement de la plage physique.
LAMBDA_BORNES_V2 = (-0.25, 1.25)
PROCEDURE_V2 = "PROC-GEN-SMOTE-V2"


def _profil_series(mesures: pd.DataFrame) -> dict:
    """Écart-type et autocorrélation moyenne, par capteur, sur un jeu de séries."""
    frame = mesures.copy()
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, format="mixed")
    frame["value"] = pd.to_numeric(frame["value"], errors="coerce")
    profil: dict[str, dict] = {}
    for capteur, bloc in frame.groupby("sensor_name"):
        autocorrelations: dict[int, list[float]] = {lag: [] for lag in LAGS_STRUCTURE}
        for _, serie in bloc.groupby("equipment_id"):
            valeurs = serie.sort_values("timestamp")["value"].reset_index(drop=True)
            if len(valeurs) < max(LAGS_STRUCTURE) + 2:
                continue
            for lag, valeur in profil_autocorrelation(valeurs, LAGS_STRUCTURE).items():
                if valeur is not None:
                    autocorrelations[lag].append(valeur)
        profil[capteur] = {
            "lignes": int(len(bloc)),
            "ecart_type": round(float(bloc["value"].std(ddof=0)), 4),
            "moyenne": round(float(bloc["value"].mean()), 4),
            "autocorrelation_moyenne": {
                str(lag): (round(sum(v) / len(v), 4) if v else None)
                for lag, v in autocorrelations.items()
            },
        }
    return profil


def produire_generateur_v2() -> tuple[Path, dict]:
    """Second état du générateur par interpolation : bornes de λ élargies.

    Le contexte — cibles, donneurs, voisinage, horodatages — et le flux aléatoire
    sont **identiques** à ceux de l'étape 3 : seul le domaine de tirage de λ
    change. Deux états successifs du générateur ne sont comparables qu'à cette
    condition.
    """
    prepared = load_prepared()
    parc_segmente = pd.read_csv(WORK_ROOT / "output" / "capacite" / "parc_segmente.csv")
    contexte = contexte_generation(
        CAPTEURS, SITE_CIBLE, SEGMENT_CIBLE, parc_segmente, prepared, K_VOISINS
    )
    horodatages = grille_horaire(DEBUT, FIN)

    interpole, journal = generer_par_interpolation(
        contexte["cibles"],
        contexte["reelles"],
        CAPTEURS,
        horodatages,
        contexte["voisins"],
        rng(offset=102),
        lambda_bornes=LAMBDA_BORNES_V2,
    )
    interpole["provenance"] = "synthétique"
    interpole["procedure_id"] = PROCEDURE_V2

    destination = WORK_ROOT / "output" / "generation" / f"mesures_{PROCEDURE_V2}.csv"
    interpole.to_csv(destination, index=False, encoding="utf-8")

    v1 = pd.read_csv(
        WORK_ROOT / "output" / "generation" / "mesures_PROC-GEN-SMOTE-V1.csv"
    )
    reel_janvier = pd.read_csv(WORK_ROOT / "output" / "detection" / "temoin_reel.csv")

    mesures = {
        "lambda_bornes": list(LAMBDA_BORNES_V2),
        "points_extrapoles": journal["points_extrapoles"],
        "points_hors_plage": journal["points_hors_plage"],
        "lignes": int(len(interpole)),
        "profils": {
            "reel_janvier": _profil_series(reel_janvier),
            "smote_v1": _profil_series(v1),
            "smote_v2": _profil_series(interpole),
        },
    }
    return destination, mesures


def normaliser_augmentations(destination: Path) -> list[tuple[str, Path]]:
    """Met les exemples d'augmentation au format du contrat de transmission.

    Le tour 1 a montré que ces fichiers ne déclaraient pas leur provenance et
    traînaient une colonne de travail. Les deux manquements sont corrigés ici,
    sans toucher aux valeurs ni aux horodatages : c'est une correction de
    contrat, pas une correction de fabrication.
    """
    destination.mkdir(parents=True, exist_ok=True)
    normalises: list[tuple[str, Path]] = []
    for chemin in sorted(AUGMENTATION_DIR.glob("exemple_PROC-AUG-*.csv")):
        procedure = chemin.stem.replace("exemple_", "")
        frame = pd.read_csv(chemin)
        frame["provenance"] = "augmentée"
        frame["procedure_id"] = procedure
        cible = preparer_pour_detecteur(frame, destination / f"{procedure}.csv")
        normalises.append((procedure, cible))
    return normalises


def preparer_tour2(sortie: Path) -> tuple[list[dict], dict]:
    """Construit les soumissions du tour 2, chacune avec son hypothèse préalable."""
    chemin_v2, mesures = produire_generateur_v2()
    print(
        f"  {PROCEDURE_V2} produit : {mesures['lignes']} lignes, "
        f"{mesures['points_extrapoles']} points extrapolés, "
        f"{mesures['points_hors_plage']} hors plage physique"
    )
    normalises = normaliser_augmentations(sortie / "tour2" / "augmentation_normalisee")

    items = [
        {
            "id": "T2-00",
            "chemin": AUGMENTATION_DIR / "exemple_serie_reelle.csv",
            "nature": "témoin manquant du tour 1 — série support, non augmentée",
            "hypothese": (
                "C'est le témoin qui aurait dû ouvrir le tour 1. `EQ-PUMP-001` est "
                "échantillonné aux heures 2, 8, 14 et 20 : j'attends **721 lignes "
                "signalées sur 721 en R-FORMAT avant toute augmentation**. Si "
                "l'attente se vérifie, les cinq comptages identiques du tour 1 ne "
                "mesuraient pas nos procédés, et aucune conclusion ne peut leur "
                "être attribuée."
            ),
        },
        {
            "id": "T2-01",
            "chemin": chemin_v2,
            "nature": "génération — interpolation, second état, λ ∈ [−0,25 ; 1,25]",
            "hypothese": (
                "L'extrapolation restaure la dispersion : j'attends un ratio "
                "d'écart-type nettement plus proche de 1 que les 0,783 et 0,810 du "
                "premier état. Le coût attendu est un R-RANGE non nul, les points "
                "extrapolés pouvant franchir la plage physique — et ils ne sont "
                "pas écrêtés. **Le résultat qui compte est le classement** : un "
                "générateur amélioré devrait obtenir du détecteur un verdict égal "
                "ou pire que le premier état, qui était à zéro signalement. Si "
                "c'est le cas, le détecteur ne peut pas arbitrer une amélioration, "
                "et nos propres règles deviennent nécessaires."
            ),
        },
    ]

    attendus = {
        "PROC-AUG-BRUIT": (
            "provenance désormais déclarée et colonne de travail retirée ; "
            "R-FORMAT inchangé à 721, puisque le défaut vient du support et non "
            "du procédé"
        ),
        "PROC-AUG-DECALAGE": (
            "mêmes 721 R-FORMAT qu'au tour 1 : le décalage de 18 h préserve le "
            "pas, et la grille était déjà fausse avant lui"
        ),
        "PROC-AUG-DEFORM": (
            "721 R-FORMAT, indiscernable des autres — la destruction de la grille "
            "ne peut pas s'ajouter à un comptage déjà saturé"
        ),
        "PROC-AUG-ECHELLE": (
            "écart de distribution inchangé à 0,391 σ, toujours sous le seuil de "
            "0,8 : la normalisation des colonnes ne change rien au biais"
        ),
        "PROC-AUG-PERMUT": (
            "721 R-FORMAT et marginales identiques au réel : la destruction de la "
            "structure temporelle reste invisible"
        ),
    }
    for rang, (procedure, chemin) in enumerate(normalises, start=2):
        items.append(
            {
                "id": f"T2-{rang:02d}",
                "chemin": chemin,
                "nature": f"augmentation normalisée — {procedure}",
                "hypothese": attendus[procedure],
            }
        )
    return items, mesures


def executer_tour(numero: int, items: list[dict], sortie: Path, extra: dict) -> list[dict]:
    """Soumet une série de fichiers au détecteur et écrit les sorties du tour."""
    tour = sortie / f"tour{numero}"
    tour.mkdir(parents=True, exist_ok=True)

    lignes: list[dict] = []
    distributions: list[pd.DataFrame] = []

    for item in items:
        identifiant = item["id"]
        chemin = Path(item["chemin"])
        rapport = soumettre(chemin)
        (tour / f"{identifiant}.json").write_text(
            json.dumps(
                {
                    "fichier": chemin.name,
                    "nature": item["nature"],
                    "hypothese": item["hypothese"],
                    "rapport": rapport,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        resume = resume_soumission(identifiant, item["hypothese"], rapport)
        resume["fichier"] = chemin.name
        resume["nature"] = item["nature"]
        lignes.append(resume)
        detail = table_distributions(identifiant, rapport)
        if not detail.empty:
            distributions.append(detail)
        print(
            f"  {identifiant}  {chemin.name:<40} "
            f"{rapport['rows']:>6} lignes  "
            f"{rapport['flagged_rows_total']:>6} signalements  "
            f"provenance={'oui' if rapport['declares_provenance'] else 'non'}"
        )

    table = pd.DataFrame(lignes)
    colonnes = ["soumission", "fichier", "nature"] + [
        c for c in table.columns if c not in ("soumission", "fichier", "nature")
    ]
    table[colonnes].to_csv(
        tour / f"soumissions_tour{numero}.csv", index=False, encoding="utf-8"
    )
    if distributions:
        pd.concat(distributions, ignore_index=True).to_csv(
            tour / f"distributions_tour{numero}.csv", index=False, encoding="utf-8"
        )

    synthese = {
        "graine": SEED,
        "tour": numero,
        "detecteur": "tools/verify_synthetic.py",
        "soumissions": lignes,
        **extra,
    }
    (sortie / f"detection_tour{numero}.json").write_text(
        json.dumps(synthese, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return lignes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=WORK_ROOT / "output" / "detection"
    )
    parser.add_argument(
        "--tour", choices=["1", "2", "tous"], default="tous", help="tour à exécuter"
    )
    args = parser.parse_args()

    sortie = args.output
    sortie.mkdir(parents=True, exist_ok=True)

    chemin_temoin, resume_temoin = construire_temoin(sortie / "temoin_reel.csv")
    print(
        f"Témoin réel construit : {resume_temoin['lignes']} lignes, "
        f"{resume_temoin['equipements']} équipements, "
        f"{', '.join(resume_temoin['capteurs'])}"
    )

    if args.tour in ("1", "tous"):
        print("\nTour 1 — nos productions telles qu'elles sortent des étapes 2 et 3")
        executer_tour(1, soumissions(chemin_temoin), sortie, {"temoin": resume_temoin})

    if args.tour in ("2", "tous"):
        print("\nTour 2 — second état du générateur et correction des colonnes")
        items, mesures = preparer_tour2(sortie)
        executer_tour(2, items, sortie, {"generateur_v2": mesures})

    print(f"\nSorties écrites dans {sortie}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
