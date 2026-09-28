"""Mesures du brief online M7 sur le modèle de provenance M4.

Ce script réutilise le code M4 **sans le modifier** (import en lecture seule,
écriture de bytecode désactivée) et produit `results/mesures.json`.

Ce qui est mesuré ici, sur ce poste :

- temps d'import des dépendances et démarrage à froid dans un processus neuf ;
- préparation (chargement CSV + 19 features) sur la calibration et le test ;
- entraînement (ajustement sur 30 fenêtres) et validation croisée complète ;
- reproductibilité : réajustement comparé à l'artefact gelé du 31/08/2026 ;
- latence d'inférence p50/p95/p99, à l'unité, par lot et de bout en bout ;
- mémoire (tracemalloc et RSS psutil) ;
- taille des artefacts et empreinte disque des dépendances ;
- qualité recalculable sans l'oracle : F1 hors pli sur la calibration ;
- deux alternatives exécutées : modèle exporté en JSON sans scikit-learn, et
  journal des prédictions en SQLite avec purge de rétention ;
- modes de panne injectés sur des copies en mémoire.

Ce qui est estimé (hypothèse écrite dans le JSON) : capacité rapportée au parc,
énergie par prédiction. Le coût monétaire n'est pas mesuré.

Le test scellé est lu **sans étiquette** (il n'en porte pas) : le gel du
31/08/2026 a déjà autorisé sa lecture pour produire les prédictions. Aucune
métrique de qualité n'est calculée sur le test.

Usage (depuis diagops-m7/work/M7/online) :
    ..\\..\\..\\..\\diagops-m4\\work\\M4\\.venv\\Scripts\\python.exe mesures.py
"""

from __future__ import annotations

import sys

sys.dont_write_bytecode = True  # ne rien écrire dans le dossier M4

import argparse
import hashlib
import io
import json
import math
import os
import platform
import sqlite3
import subprocess
import tempfile
import time
import tracemalloc
import warnings
from datetime import datetime, timedelta, timezone
from pathlib import Path

DEBUT_SCRIPT = time.perf_counter()

ICI = Path(__file__).resolve().parent
M4_DEFAUT = ICI.parents[3] / "diagops-m4" / "work" / "M4"
M7_PACK = ICI.parents[2] / "data_pack" / "2026-S1"

EXCLUS_INSTANTANE = {".venv", ".pytest_cache", "__pycache__"}


# --- outils ----------------------------------------------------------------


def sha256_fichier(chemin: Path) -> str:
    h = hashlib.sha256()
    with chemin.open("rb") as f:
        for bloc in iter(lambda: f.read(1 << 20), b""):
            h.update(bloc)
    return h.hexdigest()


def instantane(racine: Path) -> dict[str, str]:
    """Empreinte de chaque fichier M4 hors venv et caches — preuve de non-modification."""
    resultat = {}
    for chemin in sorted(racine.rglob("*")):
        if any(partie in EXCLUS_INSTANTANE for partie in chemin.relative_to(racine).parts):
            continue
        if chemin.is_file():
            resultat[chemin.relative_to(racine).as_posix()] = sha256_fichier(chemin)
    return resultat


def taille_dossier(chemin: Path) -> int:
    if chemin.is_file():
        return chemin.stat().st_size
    return sum(f.stat().st_size for f in chemin.rglob("*") if f.is_file())


def stats_ms(durees_ns: list[int]) -> dict[str, float | int]:
    import numpy as np

    ms = np.array(durees_ns, dtype=float) / 1e6
    return {
        "n": int(len(ms)),
        "p50_ms": round(float(np.percentile(ms, 50)), 4),
        "p95_ms": round(float(np.percentile(ms, 95)), 4),
        "p99_ms": round(float(np.percentile(ms, 99)), 4),
        "min_ms": round(float(ms.min()), 4),
        "max_ms": round(float(ms.max()), 4),
        "moyenne_ms": round(float(ms.mean()), 4),
    }


def chronometrer(fonction, repetitions: int, echauffement: int = 3) -> list[int]:
    for _ in range(echauffement):
        fonction()
    durees = []
    for _ in range(repetitions):
        debut = time.perf_counter_ns()
        fonction()
        durees.append(time.perf_counter_ns() - debut)
    return durees


def nom_processeur() -> str:
    try:
        import winreg

        cle = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
        )
        return str(winreg.QueryValueEx(cle, "ProcessorNameString")[0]).strip()
    except Exception:
        return platform.processor() or "inconnu"


def rss_mo() -> float | None:
    try:
        import psutil

        return round(psutil.Process().memory_info().rss / 2**20, 1)
    except Exception:
        return None


# --- programme -------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m4", type=Path, default=M4_DEFAUT, help="dossier work/M4")
    parser.add_argument("--output", type=Path, default=ICI / "results" / "mesures.json")
    parser.add_argument("--rapide", action="store_true", help="répétitions réduites (test du script)")
    args = parser.parse_args()
    m4: Path = args.m4.resolve()
    facteur = 0.1 if args.rapide else 1.0

    def n(valeur: int) -> int:
        return max(5, int(valeur * facteur))

    mesures: dict = {
        "meta": {
            "date_execution_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "script": "work/M7/online/mesures.py",
            "code_m4_reutilise": str(m4),
            "convention": (
                "Chaque bloc porte un champ 'nature' : 'mesuré' (exécuté sur ce poste "
                "par ce script), 'estimé' (calcul à partir d'une hypothèse écrite), "
                "'non mesuré'."
            ),
        }
    }

    # 0. instantané M4 avant ------------------------------------------------
    avant = instantane(m4)

    # 1. imports ------------------------------------------------------------
    rss_depart = rss_mo()
    debut = time.perf_counter_ns()
    import numpy as np
    import pandas as pd
    import sklearn
    import joblib

    t_libs = time.perf_counter_ns() - debut

    os.chdir(m4)  # le code M4 résout le data pack en chemin relatif
    sys.path.insert(0, str(m4))
    debut = time.perf_counter_ns()
    from src.modele import NOMS_FEATURES, candidats, etiquettes, features_fenetre, table_features
    from src.protocole import (
        CALIBRATION,
        TEST_SCELLE,
        charger_calibration,
        plis,
        table_fenetres,
    )
    import run_gel
    import run_modele

    t_m4 = time.perf_counter_ns() - debut
    rss_apres_imports = rss_mo()

    try:
        import psutil

        batterie = psutil.sensors_battery()
        secteur = None if batterie is None else bool(batterie.power_plugged)
        ram_totale = round(psutil.virtual_memory().total / 2**30, 1)
        psutil_version = psutil.__version__
    except Exception:
        secteur, ram_totale, psutil_version = None, None, None

    mesures["environnement"] = {
        "nature": "mesuré",
        "processeur": nom_processeur(),
        "coeurs_logiques": os.cpu_count(),
        "ram_totale_gio": ram_totale,
        "alimentation_secteur": secteur,
        "systeme": platform.platform(),
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scikit_learn": sklearn.__version__,
        "joblib": joblib.__version__,
        "psutil": psutil_version,
        "interpreteur": sys.executable,
        "remarque": "poste portable personnel, autres applications ouvertes : mesures bruitées, à lire en ordre de grandeur",
    }
    mesures["demarrage"] = {
        "nature": "mesuré",
        "import_numpy_pandas_sklearn_joblib_ms": round(t_libs / 1e6, 1),
        "import_modules_m4_ms": round(t_m4 / 1e6, 1),
        "rss_depart_mo": rss_depart,
        "rss_apres_imports_mo": rss_apres_imports,
    }

    # 2. intégrité des entrées ---------------------------------------------
    gel = json.loads((m4 / "results" / "gel" / "gel.json").read_text(encoding="utf-8"))
    empreintes_gel = gel["empreintes_entrees"]
    integrite = {"nature": "mesuré", "fichiers": {}}
    for nom, chemin, copie_m7 in (
        ("sensor_calibration.csv", CALIBRATION, M7_PACK / "model_eval" / "sensor_calibration.csv"),
        ("sensor_test.csv", TEST_SCELLE, M7_PACK / "model_eval" / "sensor_test.csv"),
    ):
        actuel = sha256_fichier(chemin)
        integrite["fichiers"][nom] = {
            "sha256": actuel,
            "identique_au_gel": actuel == empreintes_gel[nom],
            "identique_copie_data_pack_m7": copie_m7.exists() and sha256_fichier(copie_m7) == actuel,
            "taille_octets": chemin.stat().st_size,
        }
    mesures["integrite_entrees"] = integrite

    # 3. préparation --------------------------------------------------------
    def preparer_calibration():
        lignes = charger_calibration()
        fenetres = table_fenetres(lignes)
        return lignes, table_features(lignes, fenetres)

    durees = chronometrer(preparer_calibration, n(30))
    lignes_cal, table_cal = preparer_calibration()
    prep_cal = stats_ms(durees)
    prep_cal["par_fenetre_p50_ms"] = round(prep_cal["p50_ms"] / len(table_cal), 4)

    durees = chronometrer(run_gel.table_test, n(30))
    lignes_test, table_test = run_gel.table_test()
    prep_test = stats_ms(durees)
    prep_test["par_fenetre_p50_ms"] = round(prep_test["p50_ms"] / len(table_test), 4)

    mesures["preparation"] = {
        "nature": "mesuré",
        "description": "lecture CSV + contrôle d'étiquette par fenêtre + 19 features (code M4)",
        "calibration": {"lignes": len(lignes_cal), "fenetres": len(table_cal), **prep_cal},
        "test_sans_etiquette": {"lignes": len(lignes_test), "fenetres": len(table_test), **prep_test},
    }

    X_cal = table_cal[NOMS_FEATURES].to_numpy()
    y_cal = etiquettes(table_cal).to_numpy()
    X_test = table_test[NOMS_FEATURES].to_numpy()

    # 4. entraînement -------------------------------------------------------
    def ajuster():
        modele = candidats()["regression_logistique"]
        modele.fit(X_cal, y_cal)
        return modele

    durees = chronometrer(ajuster, n(200))
    tracemalloc.start()
    ajuster()
    _, pic_fit = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    decoupes = plis(table_fenetres(lignes_cal))
    debut_cv = time.perf_counter_ns()
    cv = run_modele.evaluer(
        "regression_logistique", candidats()["regression_logistique"], table_cal, etiquettes(table_cal), decoupes
    )
    t_cv = time.perf_counter_ns() - debut_cv

    mesures["entrainement"] = {
        "nature": "mesuré",
        "ajustement_30_fenetres": stats_ms(durees),
        "memoire_pic_ajustement_ko_tracemalloc": round(pic_fit / 1024, 1),
        "validation_croisee_5x5_complete_s": round(t_cv / 1e9, 3),
        "remarque": "l'ajustement exclut la préparation des features, mesurée à part",
    }

    # 5. qualité recalculable sans oracle ----------------------------------
    attendu = gel["performance_attendue_calibration"]
    mesures["qualite"] = {
        "nature": "mesuré",
        "perimetre": "calibration seule (30 fenêtres, 11 fabriquées), F1 hors pli sur 5 partitions ; le test scellé n'est pas évaluable ici",
        "f1_hors_pli_moyen": cv["f1_hors_pli_moyen"],
        "f1_hors_pli_ecart_type": cv["f1_hors_pli_ecart_type"],
        "f1_hors_pli_min": cv["f1_hors_pli_min"],
        "f1_hors_pli_max": cv["f1_hors_pli_max"],
        "roc_auc_hors_pli": cv["roc_auc_hors_pli"],
        "matrice_premiere_repetition": {
            k: int(cv["matrice_hors_pli"][k])
            for k in ("vrai_positif", "faux_positif", "faux_negatif", "vrai_negatif")
        },
        "baseline_m3_f1": gel["baseline_m3"]["f1"],
        "reproduit_valeur_gel": abs(cv["f1_hors_pli_moyen"] - attendu["f1_moyen"]) < 1e-4,
        "oracle_test": "non disponible — aucun retour du formateur trouvé dans les dépôts M4 à M7 au 28/09/2026",
    }

    # 6. reproductibilité et artefacts ---------------------------------------
    chemin_gele = m4 / "results" / "gel" / "candidat_m4.joblib"
    with tempfile.TemporaryDirectory(prefix="m7_online_") as dossier:
        dossier = Path(dossier)
        reajuste = ajuster()
        chemin_reajuste = dossier / "reajuste.joblib"
        joblib.dump(reajuste, chemin_reajuste)
        sha_reajuste = sha256_fichier(chemin_reajuste)
        taille_reajuste = chemin_reajuste.stat().st_size

        durees_chargement = chronometrer(lambda: joblib.load(chemin_gele), n(100))
        gele = joblib.load(chemin_gele)

        p_gele = gele.predict_proba(X_test)[:, 1]
        p_reajuste = reajuste.predict_proba(X_test)[:, 1]
        remis = pd.read_csv(m4 / "results" / "gel" / "predictions_test.csv")
        remis = remis.set_index("window_id").loc[table_test["window_id"]]
        decisions_gele = np.where(p_gele >= run_gel.SEUIL, "fabriquée", "réelle")

        # modes de panne sur l'artefact : copie tronquée
        tronque = dossier / "tronque.joblib"
        tronque.write_bytes(chemin_gele.read_bytes()[: chemin_gele.stat().st_size // 2])
        try:
            joblib.load(tronque)
            panne_artefact = {"resultat": "chargé sans erreur", "detecte": False}
        except Exception as exc:  # noqa: BLE001 — on consigne le type exact
            panne_artefact = {"resultat": "exception", "type": type(exc).__name__, "detecte": True}

        mesures["reproductibilite"] = {
            "nature": "mesuré",
            "empreinte_artefact_gele": sha256_fichier(chemin_gele),
            "empreinte_artefact_gele_conforme_gel_json": sha256_fichier(chemin_gele) == gel["empreinte_modele"],
            "empreinte_reajustement": sha_reajuste,
            "reajustement_identique_octet_pour_octet": sha_reajuste == gel["empreinte_modele"],
            "ecart_max_probabilites_gele_vs_reajuste": float(np.max(np.abs(p_gele - p_reajuste))),
            "ecart_max_probabilites_vs_predictions_remises": float(
                np.max(np.abs(np.round(p_gele, 6) - remis["probabilite_fabriquee"].to_numpy()))
            ),
            "decisions_identiques_aux_predictions_remises": int(
                (decisions_gele == remis["prediction"].to_numpy()).sum()
            ),
            "fenetres_test": len(table_test),
            "repartition_decisions_test": {
                str(k): int(v) for k, v in zip(*np.unique(decisions_gele, return_counts=True))
            },
        }

        # 7. inférence --------------------------------------------------------
        durees_lot = chronometrer(lambda: gele.predict_proba(X_test), n(1000), echauffement=20)
        lot = stats_ms(durees_lot)
        lot["par_fenetre_p50_ms"] = round(lot["p50_ms"] / len(X_test), 5)
        lot["debit_fenetres_par_s_p50"] = round(len(X_test) / (lot["p50_ms"] / 1000))

        unitaires = []
        for _ in range(n(50)):
            for i in range(len(X_test)):
                ligne = X_test[i : i + 1]
                debut = time.perf_counter_ns()
                gele.predict_proba(ligne)
                unitaires.append(time.perf_counter_ns() - debut)

        groupes = [g for _, g in lignes_test.groupby("window_id", sort=True)]
        bout_en_bout = []
        cpu_bout_debut = time.process_time_ns()
        for _ in range(n(20)):
            for groupe in groupes:
                debut = time.perf_counter_ns()
                f = features_fenetre(groupe)
                gele.predict_proba(np.array([[f[k] for k in NOMS_FEATURES]]))
                bout_en_bout.append(time.perf_counter_ns() - debut)
        cpu_bout_par_fenetre_s = (time.process_time_ns() - cpu_bout_debut) / 1e9 / len(bout_en_bout)

        tracemalloc.start()
        gele.predict_proba(X_test)
        _, pic_lot = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        # temps CPU du processus pour 1 000 lots (base de l'estimation énergie)
        cpu_debut = time.process_time_ns()
        mur_debut = time.perf_counter_ns()
        for _ in range(1000):
            gele.predict_proba(X_test)
        cpu_par_fenetre_s = (time.process_time_ns() - cpu_debut) / 1e9 / (1000 * len(X_test))
        mur_par_fenetre_s = (time.perf_counter_ns() - mur_debut) / 1e9 / (1000 * len(X_test))

        mesures["inference"] = {
            "nature": "mesuré",
            "modele": "artefact gelé candidat_m4.joblib (StandardScaler + LogisticRegression)",
            "chargement_artefact_joblib": stats_ms(durees_chargement),
            "lot_60_fenetres_predict_proba": lot,
            "unitaire_predict_proba_1_fenetre": stats_ms(unitaires),
            "bout_en_bout_1_fenetre_features_plus_prediction": stats_ms(bout_en_bout),
            "memoire_pic_lot_ko_tracemalloc": round(pic_lot / 1024, 1),
            "temps_cpu_par_fenetre_us": round(cpu_par_fenetre_s * 1e6, 3),
            "temps_mur_par_fenetre_us": round(mur_par_fenetre_s * 1e6, 3),
            "temps_cpu_bout_en_bout_par_fenetre_us": round(cpu_bout_par_fenetre_s * 1e6, 1),
            "remarque": "la préparation des features domine la latence de bout en bout ; la prédiction seule est un produit scalaire",
        }

        # 8. démarrage à froid dans un processus neuf ------------------------
        code_froid = (
            "import time;t=time.perf_counter();"
            "import sys;sys.dont_write_bytecode=True;"
            "import joblib,numpy as np;"
            f"m=joblib.load(r'{chemin_gele}');"
            "m.predict_proba(np.zeros((1,19)));"
            "print((time.perf_counter()-t)*1000)"
        )
        froids_interne, froids_total = [], []
        for _ in range(5 if args.rapide else 10):
            debut = time.perf_counter_ns()
            sortie = subprocess.run(
                [sys.executable, "-c", code_froid], capture_output=True, text=True, check=True
            )
            froids_total.append(time.perf_counter_ns() - debut)
            froids_interne.append(int(float(sortie.stdout.strip()) * 1e6))
        mesures["demarrage_a_froid"] = {
            "nature": "mesuré",
            "description": "nouveau processus Python : imports + chargement de l'artefact + une prédiction ; cache disque déjà chaud",
            "processus_complet": stats_ms(froids_total),
            "dans_le_processus": stats_ms(froids_interne),
        }

        # 9. alternative de packaging : paramètres en JSON, sans scikit-learn -----
        echelle = gele.named_steps["echelle"]
        logistique = gele.named_steps["modele"]
        parametres = {
            "format": "diagops-provenance-lr/1",
            "features": NOMS_FEATURES,
            "moyennes": echelle.mean_.tolist(),
            "echelles": echelle.scale_.tolist(),
            "coefficients": logistique.coef_[0].tolist(),
            "intercept": float(logistique.intercept_[0]),
            "seuil": run_gel.SEUIL,
            "source": {"artefact": "candidat_m4.joblib", "sha256": gel["empreinte_modele"]},
        }
        chemin_json = dossier / "candidat_m4.json"
        chemin_json.write_text(json.dumps(parametres, indent=1), encoding="utf-8", newline="\n")
        relu = json.loads(chemin_json.read_text(encoding="utf-8"))

        mu = np.array(relu["moyennes"])
        sigma = np.array(relu["echelles"])
        w = np.array(relu["coefficients"])
        b = relu["intercept"]

        def proba_numpy(X):
            z = ((X - mu) / sigma) @ w + b
            return 1.0 / (1.0 + np.exp(-z))

        def proba_python(ligne):
            z = b
            for x, m_, s_, c_ in zip(ligne, relu["moyennes"], relu["echelles"], relu["coefficients"]):
                z += (x - m_) / s_ * c_
            return 1.0 / (1.0 + math.exp(-z))

        p_json = proba_numpy(X_test)
        p_pur = np.array([proba_python(list(map(float, l))) for l in X_test])
        unit_numpy, unit_pur = [], []
        lignes_py = [list(map(float, l)) for l in X_test]
        for _ in range(n(50)):
            for i in range(len(X_test)):
                ligne = X_test[i : i + 1]
                debut = time.perf_counter_ns()
                proba_numpy(ligne)
                unit_numpy.append(time.perf_counter_ns() - debut)
                debut = time.perf_counter_ns()
                proba_python(lignes_py[i])
                unit_pur.append(time.perf_counter_ns() - debut)

        mesures["alternative_packaging_json"] = {
            "nature": "mesuré",
            "description": "paramètres du pipeline exportés en JSON, inférence réécrite en numpy puis en Python pur ; scikit-learn, scipy et pickle ne sont plus nécessaires à l'exploitation",
            "taille_json_octets": chemin_json.stat().st_size,
            "taille_joblib_octets": chemin_gele.stat().st_size,
            "ecart_max_proba_numpy_vs_sklearn": float(np.max(np.abs(p_json - p_gele))),
            "ecart_max_proba_python_pur_vs_sklearn": float(np.max(np.abs(p_pur - p_gele))),
            "decisions_identiques_numpy": int(
                ((p_json >= run_gel.SEUIL) == (p_gele >= run_gel.SEUIL)).sum()
            ),
            "decisions_identiques_python_pur": int(
                ((p_pur >= run_gel.SEUIL) == (p_gele >= run_gel.SEUIL)).sum()
            ),
            "fenetres": len(X_test),
            "unitaire_numpy": stats_ms(unit_numpy),
            "unitaire_python_pur": stats_ms(unit_pur),
            "limite": "la préparation des features reste en pandas/numpy ; seul le modèle change de format",
        }

        # 10. alternative de stockage : journal SQLite avec rétention ----------
        base = dossier / "journal.sqlite"
        maintenant = datetime.now(timezone.utc)
        sha_entrees = sha256_fichier(TEST_SCELLE)
        debut = time.perf_counter_ns()
        cx = sqlite3.connect(base)
        cx.execute(
            "CREATE TABLE prediction (window_id TEXT, equipment_id TEXT, sensor_name TEXT, "
            "probabilite REAL, decision TEXT, seuil REAL, sha256_modele TEXT, "
            "sha256_entree TEXT, predit_le TEXT, revue_humaine TEXT)"
        )
        # 12 lots simulés, un tous les 30 jours, pour exercer la purge
        lignes_sql = []
        for lot_i in range(12):
            date = (maintenant - timedelta(days=30 * lot_i)).isoformat(timespec="seconds")
            for idx in range(len(table_test)):
                lignes_sql.append(
                    (
                        f"{table_test['window_id'].iloc[idx]}#{lot_i}",
                        table_test["equipment_id"].iloc[idx],
                        table_test["sensor_name"].iloc[idx],
                        float(p_gele[idx]),
                        str(decisions_gele[idx]),
                        run_gel.SEUIL,
                        gel["empreinte_modele"],
                        sha_entrees,
                        date,
                        None,
                    )
                )
        cx.executemany("INSERT INTO prediction VALUES (?,?,?,?,?,?,?,?,?,?)", lignes_sql)
        cx.commit()
        t_insert = time.perf_counter_ns() - debut
        avant_purge = cx.execute("SELECT COUNT(*) FROM prediction").fetchone()[0]
        limite = (maintenant - timedelta(days=180)).isoformat(timespec="seconds")
        debut = time.perf_counter_ns()
        cx.execute("DELETE FROM prediction WHERE predit_le < ?", (limite,))
        cx.commit()
        t_purge = time.perf_counter_ns() - debut
        apres_purge = cx.execute("SELECT COUNT(*) FROM prediction").fetchone()[0]
        cx.execute("VACUUM")
        cx.close()
        mesures["alternative_stockage_sqlite"] = {
            "nature": "mesuré",
            "description": "journal des prédictions versionné (empreinte modèle + empreinte entrée + date + champ de revue humaine), purge de rétention à 180 jours",
            "lignes_inserees": avant_purge,
            "insertion_ms": round(t_insert / 1e6, 2),
            "purge_ms": round(t_purge / 1e6, 2),
            "lignes_apres_purge": apres_purge,
            "taille_apres_purge_octets": base.stat().st_size,
            "taille_csv_predictions_actuel_octets": (m4 / "results" / "gel" / "predictions_test.csv").stat().st_size,
            "remarque": "le CSV actuel ne porte ni version du modèle ni date par ligne",
        }

    # 11. modes de panne injectés -------------------------------------------
    reference = groupes[0].copy()

    def essai(nom: str, fabrique):
        with warnings.catch_warnings(record=True) as alertes:
            warnings.simplefilter("always")
            try:
                fenetre = fabrique(reference.copy())
                f = features_fenetre(fenetre)
                x = np.array([[f[k] for k in NOMS_FEATURES]])
                if not np.all(np.isfinite(x)):
                    return {
                        "cas": nom,
                        "resultat": "features non finies",
                        "detecte": True,
                        "alertes": len(alertes),
                    }
                p = float(gele.predict_proba(x)[0, 1])
                return {
                    "cas": nom,
                    "resultat": "prédiction produite",
                    "probabilite_fabriquee": round(p, 4),
                    "decision": "fabriquée" if p >= run_gel.SEUIL else "réelle",
                    "detecte": False,
                    "alertes": len(alertes),
                    "premiere_alerte": str(alertes[0].message)[:120] if alertes else None,
                }
            except Exception as exc:  # noqa: BLE001
                return {
                    "cas": nom,
                    "resultat": "exception",
                    "type": type(exc).__name__,
                    "message": str(exc)[:160],
                    "detecte": True,
                    "alertes": len(alertes),
                }

    def toutes_manquantes(d):
        d["value"] = ""
        return d

    def une_ligne(d):
        return d.iloc[:1]

    def capteur_inconnu(d):
        d["sensor_name"] = "humidite_pct"
        return d

    def constantes(d):
        d["value"] = "5.0"
        return d

    def horodatages_invalides(d):
        d["timestamp"] = "pas-une-date"
        return d

    def sans_unite(d):
        return d.drop(columns=["unit"])

    def valeur_extreme(d):
        valeurs = d["value"].astype(float).to_numpy().copy()
        valeurs[0] = 1e12
        d["value"] = valeurs
        return d

    def fenetre_vide(d):
        return d.iloc[0:0]

    cas = [
        essai("reference_sans_alteration", lambda d: d),
        essai("toutes_valeurs_manquantes", toutes_manquantes),
        essai("une_seule_ligne", une_ligne),
        essai("capteur_inconnu", capteur_inconnu),
        essai("valeurs_constantes", constantes),
        essai("horodatages_invalides", horodatages_invalides),
        essai("colonne_unit_absente", sans_unite),
        essai("valeur_extreme_1e12", valeur_extreme),
        essai("fenetre_vide", fenetre_vide),
    ]
    cas.append({"cas": "artefact_joblib_tronque", **panne_artefact})
    mesures["modes_de_panne"] = {
        "nature": "mesuré",
        "fenetre_de_reference": str(reference["window_id"].iloc[0]),
        "lecture": "detecte=False signifie qu'une prédiction est rendue sans erreur ni alerte : panne silencieuse",
        "cas": cas,
        "non_testes": [
            "version de scikit-learn différente au chargement du pickle (aucune autre version installée, pas d'accès réseau pour en installer)",
            "disque plein, droits en écriture refusés",
            "dérive du générateur de données (aucun nouveau lot disponible)",
        ],
    }

    # 11 bis. biais et explicabilité -----------------------------------------
    equipements = pd.read_csv(Path("../../data_pack/2026-S1/equipment/equipment.csv"))
    test_detail = table_test[["window_id", "equipment_id", "sensor_name"]].copy()
    test_detail["signalee"] = p_gele >= run_gel.SEUIL
    test_detail = test_detail.merge(equipements, on="equipment_id", how="left")

    def taux(colonne: str) -> dict:
        g = test_detail.groupby(colonne, dropna=False)["signalee"].agg(["size", "sum"])
        return {
            str(k): {"fenetres": int(r["size"]), "signalees": int(r["sum"]),
                     "taux": round(float(r["sum"] / r["size"]), 3)}
            for k, r in g.iterrows()
        }

    cal_detail = table_cal[["window_id", "sensor_name", "provenance"]].copy()
    cal_detail["predit"] = cv["predictions_premiere_repetition"]
    cal_par_capteur = {}
    for capteur, g in cal_detail.groupby("sensor_name"):
        reel = g["provenance"] != "fabriquée"
        cal_par_capteur[str(capteur)] = {
            "fenetres": int(len(g)),
            "fabriquees": int((~reel).sum()),
            "faux_positifs_sur_reelles": int(((g["predit"] == 1) & reel).sum()),
            "faux_negatifs_sur_fabriquees": int(((g["predit"] == 0) & ~reel).sum()),
        }

    z = (X_test - mu) / sigma
    contributions = z * w
    signalees = np.where(p_gele >= run_gel.SEUIL)[0]
    compte_top3: dict[str, int] = {}
    for i in signalees:
        for j in np.argsort(-contributions[i])[:3]:
            compte_top3[NOMS_FEATURES[j]] = compte_top3.get(NOMS_FEATURES[j], 0) + 1

    mesures["biais"] = {
        "nature": "mesuré",
        "lecture": "test : taux de signalement sans étiquette (écart de traitement, pas une erreur) ; calibration : erreurs hors pli de la première répétition",
        "test_taux_signalement_par_capteur": taux("sensor_name"),
        "test_taux_signalement_par_site": taux("site_id"),
        "test_taux_signalement_par_criticite": taux("criticality"),
        "test_taux_signalement_par_type_equipement": taux("equipment_type"),
        "test_equipements_sans_fiche": int(test_detail["site_id"].isna().sum()),
        "calibration_erreurs_par_capteur": cal_par_capteur,
        "colonnes_entree": list(lignes_test.columns),
    }
    mesures["explicabilite"] = {
        "nature": "mesuré",
        "methode": "contribution = coefficient × valeur standardisée ; comptage des 3 premières contributions positives par fenêtre signalée du test",
        "fenetres_signalees": int(len(signalees)),
        "top3_occurrences": dict(sorted(compte_top3.items(), key=lambda kv: -kv[1])),
        "coefficients": {k: round(float(c), 4) for k, c in zip(NOMS_FEATURES, w)},
    }

    # 12. empreinte disque des dépendances -----------------------------------
    venv = Path(sys.prefix)
    site = venv / "Lib" / "site-packages"
    if not site.exists():
        site = next(venv.glob("lib/python*/site-packages"), site)

    def taille_prefixes(prefixes):
        total = 0
        for entree in site.iterdir():
            nom = entree.name.lower()
            if any(nom == p or nom.startswith(p + "-") or nom.startswith(p + ".") for p in prefixes):
                total += taille_dossier(entree)
        return total

    exec_actuel = ["sklearn", "scikit_learn", "scipy", "joblib", "threadpoolctl",
                   "numpy", "pandas", "dateutil", "python_dateutil", "pytz", "tzdata", "six"]
    exec_json = ["numpy", "pandas", "dateutil", "python_dateutil", "pytz", "tzdata", "six"]
    mesures["empreinte_disque"] = {
        "nature": "mesuré",
        "venv_m4_complet_mo": round(taille_dossier(venv) / 2**20, 1),
        "dependances_execution_actuelles_mo": round(taille_prefixes(exec_actuel) / 2**20, 1),
        "dependances_execution_variante_json_mo": round(taille_prefixes(exec_json) / 2**20, 1),
        "torch_mo": round(taille_prefixes(["torch"]) / 2**20, 1),
        "artefact_modele_octets": chemin_gele.stat().st_size,
        "code_m4_modele_octets": sum(
            (m4 / p).stat().st_size for p in ("src/modele.py", "src/protocole.py", "run_gel.py")
        ),
        "remarque": "le venv M4 sert aussi le RAG (torch, sentence-transformers) et Jupyter ; le modèle n'en utilise qu'une partie",
    }

    # 13. capacité et énergie : estimations --------------------------------
    lectures = pd.read_csv(Path("../../data_pack/2026-S1/sensors/sensor_readings.csv"))
    series = lectures[["equipment_id", "sensor_name"]].drop_duplicates()
    equipements_parc = len(pd.read_csv(Path("../../data_pack/2026-S1/equipment/equipment.csv")))
    capteurs_par_equipement = len(series) / lectures["equipment_id"].nunique()
    duree_fenetre_j = 30 * 6 / 24
    fenetres_par_jour = equipements_parc * capteurs_par_equipement / duree_fenetre_j
    bout_p95_s = stats_ms(bout_en_bout)["p95_ms"] / 1000
    mesures["capacite"] = {
        "nature": "estimé",
        "hypotheses": {
            "equipements_parc": equipements_parc,
            "capteurs_par_equipement_observes": round(capteurs_par_equipement, 2),
            "source_capteurs": "sensor_readings.csv : séries équipement×capteur distinctes / équipements présents",
            "pas_nominal_h": 6,
            "mesures_par_fenetre": 30,
            "duree_fenetre_jours": duree_fenetre_j,
        },
        "fenetres_a_traiter_par_jour": round(fenetres_par_jour, 1),
        "temps_calcul_par_jour_s_au_p95_bout_en_bout": round(fenetres_par_jour * bout_p95_s, 3),
        "lecture": "charge journalière du parc entier rapportée à la latence mesurée ; la capacité n'est pas une contrainte à ce volume",
    }
    puissance_max_w = 115  # Intel ARK i7-13620H, Maximum Turbo Power, consulté le 28/09/2026
    joules_prediction = cpu_par_fenetre_s * puissance_max_w
    joules_bout = cpu_bout_par_fenetre_s * puissance_max_w
    mesures["energie"] = {
        "nature": "estimé",
        "methode": "temps CPU mesuré par fenêtre × puissance maximale turbo du processeur entier ; borne haute grossière, pas une mesure au wattmètre",
        "source_puissance": "Intel ARK, Core i7-13620H, Maximum Turbo Power 115 W (base 45 W), consulté le 28/09/2026",
        "joules_par_fenetre_prediction_seule_borne_haute": joules_prediction,
        "joules_par_fenetre_bout_en_bout_borne_haute": joules_bout,
        "wh_par_jour_parc_bout_en_bout_borne_haute": round(joules_bout * fenetres_par_jour / 3600, 6),
        "wh_demarrage_a_froid_borne_haute": round(
            stats_ms(froids_total)["p50_ms"] / 1000 * puissance_max_w / 3600, 4
        ),
        "non_mesure": "consommation réelle (pas de wattmètre ni de compteur RAPL lisible sous Windows), poste au repos, empreinte carbone, fabrication du matériel",
    }
    mesures["cout"] = {
        "nature": "non mesuré",
        "constat": "exécution sur un poste existant : aucun coût marginal facturé ; le coût du poste, de l'électricité et du temps humain de revue n'est pas chiffré",
    }

    # 14. instantané M4 après ------------------------------------------------
    apres = instantane(m4)
    mesures["non_modification_m4"] = {
        "nature": "mesuré",
        "fichiers_controles": len(avant),
        "identique_avant_apres": avant == apres,
        "differences": sorted(set(avant.items()) ^ set(apres.items()))[:10],
    }
    mesures["meta"]["duree_totale_s"] = round(time.perf_counter() - DEBUT_SCRIPT, 1)
    mesures["meta"]["mode_rapide"] = args.rapide

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8", newline="\n") as f:
        json.dump(mesures, f, ensure_ascii=False, indent=2, default=str)
        f.write("\n")

    q, inf = mesures["qualite"], mesures["inference"]
    print(f"F1 hors pli {q['f1_hors_pli_moyen']} (gel : {attendu['f1_moyen']}) — reproduit : {q['reproduit_valeur_gel']}")
    print(f"unitaire p50/p95 : {inf['unitaire_predict_proba_1_fenetre']['p50_ms']} / {inf['unitaire_predict_proba_1_fenetre']['p95_ms']} ms")
    print(f"bout en bout p50/p95 : {inf['bout_en_bout_1_fenetre_features_plus_prediction']['p50_ms']} / {inf['bout_en_bout_1_fenetre_features_plus_prediction']['p95_ms']} ms")
    print(f"M4 inchangé : {mesures['non_modification_m4']['identique_avant_apres']}")
    print(f"écrit : {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
