"""Chargement et exécution du détecteur de provenance gelé en M4.

Trois choses que ce module refuse de faire silencieusement :

1. **charger un artefact non identifié** — le checksum du `.joblib` est vérifié contre celui
   déclaré, à chaque démarrage. Un modèle servi sans identité vérifiée rend toute trace
   inexploitable : on ne sait plus ce qui a produit la prédiction ;
2. **prédire avec un jeu de features désaligné** — l'ordre des colonnes est celui de `gel.json`,
   et un écart lève. Un `StandardScaler` appliqué dans le désordre ne plante pas, il donne des
   résultats faux ;
3. **tourner avec une version de scikit-learn différente de celle du gel** — un `joblib` chargé
   par une autre version est au mieux bruyant, au pire subtilement différent. La version est
   comparée et l'écart est signalé.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import joblib
import pandas as pd
import sklearn

from .features import COLONNE_FENETRE, features_fenetre


ARTEFACT = Path(os.environ.get("DIAGOPS_ARTEFACT_DIR", Path(__file__).resolve().parents[1] / "artefact"))
MODELE = ARTEFACT / "candidat_m4.joblib"
GEL = ARTEFACT / "gel.json"

# Version sous laquelle le candidat a été gelé le 31/08/2026, relevée dans le venv M4.
SKLEARN_DU_GEL = "1.7.1"

# Empreinte déclarée dans la model card M4 (`docs/model_card.md`).
CHECKSUM_ATTENDU = "164d05b129ce5e4107cdc27279bc198c"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class Detecteur:
    """Modèle chargé une fois, servi ensuite. L'identité est établie au chargement."""

    def __init__(self) -> None:
        if not MODELE.is_file():
            raise FileNotFoundError(f"Artefact absent : {MODELE}")
        if not GEL.is_file():
            raise FileNotFoundError(f"Manifeste de gel absent : {GEL}")

        self.checksum = sha256(MODELE)
        if not self.checksum.startswith(CHECKSUM_ATTENDU):
            raise ValueError(
                f"Artefact non conforme : {self.checksum[:32]} attendu {CHECKSUM_ATTENDU}"
            )

        self.gel = json.loads(GEL.read_text(encoding="utf-8"))
        self.features = list(self.gel["features"])
        self.seuil = float(self.gel["seuil_de_decision"])
        self.pipeline = joblib.load(MODELE)
        self.sklearn_version = sklearn.__version__
        self.sklearn_conforme = self.sklearn_version == SKLEARN_DU_GEL

    def version(self) -> dict:
        return {
            "modele": "detecteur-provenance-m4",
            "date_de_gel": self.gel["date_de_gel"],
            "commit_du_gel": self.gel["commit"],
            "algorithme": self.gel["candidat"],
            "seuil_de_decision": self.seuil,
            "graine": self.gel["graine"],
            "checksum_sha256": self.checksum,
            "nombre_de_features": len(self.features),
            "sklearn_du_gel": SKLEARN_DU_GEL,
            "sklearn_execute": self.sklearn_version,
            "sklearn_conforme": self.sklearn_conforme,
            "performance_de_reference": self.gel.get("performance_attendue_calibration"),
        }

    def predire_fenetre(self, mesures: list[dict]) -> dict:
        """Prédit la provenance d'UNE fenêtre de mesures consécutives."""
        cadre = pd.DataFrame(mesures)
        cadre["timestamp"] = pd.to_datetime(cadre["timestamp"], utc=True, format="mixed")
        calculees = features_fenetre(cadre)

        manquantes = [nom for nom in self.features if nom not in calculees]
        if manquantes:
            raise ValueError(f"Features non calculées : {manquantes}")

        # Ordre imposé par le gel, jamais celui du dictionnaire : un scaler appliqué dans le
        # désordre ne lève pas, il rend des résultats faux.
        #
        # Tableau nu et non DataFrame : le `StandardScaler` a été ajusté sans noms de colonnes en
        # M4. Lui passer un DataFrame nommé déclenche un avertissement sklearn à chaque appel —
        # bruit qui finirait par masquer un vrai signal dans les journaux. L'ordre reste garanti
        # par la liste ci-dessous, qui vient de `gel.json`.
        vecteur = [[calculees[nom] for nom in self.features]]
        probabilite = float(self.pipeline.predict_proba(vecteur)[0][1])
        return {
            "probabilite_fabriquee": round(probabilite, 6),
            "provenance_predite": "fabriquée" if probabilite >= self.seuil else "réelle",
            "seuil_de_decision": self.seuil,
            "mesures_recues": len(mesures),
        }


def charger() -> Detecteur:
    return Detecteur()


def fenetres_depuis_csv(chemin: Path) -> dict[str, list[dict]]:
    """Regroupe un CSV de mesures par `window_id`, pour les tests et le test de fumée."""
    lignes = pd.read_csv(chemin)
    return {
        str(identifiant): groupe.to_dict("records")
        for identifiant, groupe in lignes.groupby(COLONNE_FENETRE)
    }
