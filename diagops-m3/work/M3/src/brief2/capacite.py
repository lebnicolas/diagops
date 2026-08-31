"""Étape 1 du brief 2 — mesurer ce que le jeu de données ne permet pas.

Le brief 1 a conclu sur la qualité des données. Cette étape mesure leur
capacité : effectifs, déséquilibres, couverture réelle des événements, et
segmentation du parc.

Deux décisions de méthode structurent le module, toutes deux destinées à
éviter une conclusion tautologique :

1. **la couverture instrumentale n'entre pas dans les variables de
   segmentation.** Segmenter sur « a des capteurs ou non » puis conclure que
   certains groupes sont mal couverts ne démontre rien. On segmente sur ce
   qu'est le parc et sur ce qu'il coûte, puis on croise avec la couverture ;
2. **le site et le type d'équipement n'entrent pas non plus.** Le brief exige
   que la segmentation montre autre chose que les comptages par site déjà
   produits au brief 1 ; les inclure comme variables reviendrait à les
   redécouvrir. Ils servent à *décrire* les segments obtenus, a posteriori.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

from src.brief2.seed import SEED


# Ordre des criticités, du moins au plus critique. L'encodage ordinal suppose
# que l'écart entre deux niveaux consécutifs est comparable : c'est une
# hypothèse, pas un fait, et elle est assumée ici faute d'échelle métier.
CRITICALITY_ORDER = ["low", "medium", "high", "critical"]

# Seuil de la règle héritée R-MNT-005 : quatorze jours d'arrêt. Au brief 1, la
# ligne à 99 999 minutes avait reçu la décision `conserve_signale` — conservée,
# signalée, arbitrage métier en attente. Elle reste dans la table préparée : il
# faut donc la neutraliser à chaque agrégation, sinon elle constitue à elle
# seule un segment d'un équipement.
SENTINELLE_DOWNTIME_MIN = 14 * 24 * 60

# Fin de la période observée, référence pour le calcul de l'âge du matériel.
PERIOD_END = pd.Timestamp("2026-07-01T00:00:00Z")

SEVERITES_GRAVES = {"high", "critical"}

# Variables soumises à la segmentation. Les cinq compteurs et montants sont
# transformés en log(1+x) : leurs distributions sont très asymétriques, et sans
# cette transformation les quelques équipements les plus coûteux dicteraient
# seuls la partition.
FEATURES_LOG = [
    "n_evenements",
    "n_evenements_graves",
    "n_interventions",
    "indisponibilite_min",
    "cout_pieces_eur",
]
FEATURES_BRUTES = ["criticite_ordinale", "puissance_kw", "age_annees", "part_correctives"]
FEATURES = FEATURES_BRUTES + FEATURES_LOG

# Strate déclarée, et non segment découvert. Les équipements sans aucune
# intervention enregistrée ont tous leurs compteurs d'activité à zéro : ils
# occupent un point unique de l'espace des variables. Un partitionnement les
# isole donc en premier et la silhouette récompense cette séparation, sans que
# rien n'ait été appris. Ils sont mis de côté explicitement, et le parc actif
# est segmenté séparément — voir le diagnostic de l'état 1 dans le journal.
STRATE_INACTIVE = "SEG-INACTIF"


def effectifs(frame: pd.DataFrame, axe: str) -> pd.DataFrame:
    """Effectifs et fréquences d'une variable catégorielle."""
    table = (
        frame[axe]
        .astype("string")
        .fillna("(absent)")
        .value_counts()
        .rename_axis(axe)
        .reset_index(name="effectif")
    )
    table["part_pct"] = (100 * table["effectif"] / table["effectif"].sum()).round(2)
    return table.sort_values("effectif", ascending=False).reset_index(drop=True)


def ratio_desequilibre(table: pd.DataFrame, axe: str) -> dict:
    """Rapport entre la modalité la plus représentée et la moins représentée.

    Le brief demande un rapport d'effectifs. Il est distinct du rapport de
    *taux d'instrumentation* calculé au brief 1 (×23 entre `critical` et `low`)
    et ne le remplace pas : l'un décrit le parc, l'autre son observation.
    """
    haut = table.iloc[0]
    bas = table.iloc[-1]
    return {
        "variable": axe,
        "modalites": int(len(table)),
        "plus_representee": str(haut[axe]),
        "effectif_max": int(haut["effectif"]),
        "moins_representee": str(bas[axe]),
        "effectif_min": int(bas["effectif"]),
        "ratio": round(float(haut["effectif"]) / float(bas["effectif"]), 2),
    }


def couverture_evenements(
    events: pd.DataFrame,
    sans_mesure: pd.DataFrame,
    axes: tuple[str, ...] = ("event_type", "severity"),
) -> pd.DataFrame:
    """Part des événements documentés par au moins une mesure, par catégorie.

    La fenêtre d'observation est celle retenue au brief 1 : 48 h avant le début
    de l'événement, 24 h après sa fin.
    """
    documentes = ~events["event_id"].isin(set(sans_mesure["event_id"]))
    frame = events.assign(documente=documentes)

    lignes = []
    for axe in axes:
        table = (
            frame.groupby(axe, observed=True)["documente"]
            .agg(evenements="size", documentes="sum")
            .reset_index()
            .rename(columns={axe: "modalite"})
        )
        table.insert(0, "variable", axe)
        table["part_documentee_pct"] = (
            100 * table["documentes"] / table["evenements"]
        ).round(2)
        lignes.append(table)

    return pd.concat(lignes, ignore_index=True).sort_values(
        ["variable", "part_documentee_pct"]
    ).reset_index(drop=True)


def tester_independance_couverture(
    events: pd.DataFrame,
    sans_mesure: pd.DataFrame,
    axes: tuple[str, ...] = ("event_type", "severity"),
) -> pd.DataFrame:
    """Teste si la couverture d'un événement dépend de sa catégorie.

    Les taux bruts invitent à conclure : 12,33 % des événements `critical` sont
    documentés contre 21,13 % des `low`, ce qui suggérerait que les cas les
    plus graves sont les moins observés. Sur ces effectifs, l'écart n'est pas
    distinguable du hasard. Le test est donc produit avec les taux, et non
    après coup : c'est lui qui autorise ou interdit la lecture.
    """
    documentes = ~events["event_id"].isin(set(sans_mesure["event_id"]))
    frame = events.assign(documente=documentes)

    lignes = []
    for axe in axes:
        table = pd.crosstab(frame[axe], frame["documente"])
        khi2, p_value, ddl, attendus = chi2_contingency(table)
        lignes.append(
            {
                "variable": axe,
                "khi2": round(float(khi2), 4),
                "ddl": int(ddl),
                "p_value": round(float(p_value), 4),
                "effectif_attendu_min": round(float(attendus.min()), 2),
                "significatif_5pct": bool(p_value < 0.05),
                "lecture": (
                    "la couverture dépend de la catégorie"
                    if p_value < 0.05
                    else "aucun écart distinguable du hasard : couverture uniformément faible"
                ),
            }
        )
    return pd.DataFrame(lignes)


def construire_features(
    equipment: pd.DataFrame,
    events: pd.DataFrame,
    maintenance: pd.DataFrame,
) -> tuple[pd.DataFrame, dict]:
    """Assemble une ligne par équipement du parc, référentiel et activité.

    Toute neutralisation et toute imputation sont comptées et retournées dans
    le rapport : une valeur remplacée en silence est une décision cachée.
    """
    rapport: dict = {"lignes_parc": int(len(equipment))}

    frame = equipment[["equipment_id", "equipment_type", "site_id", "criticality"]].copy()

    # --- référentiel ---------------------------------------------------------
    criticite = pd.Categorical(
        equipment["criticality"], categories=CRITICALITY_ORDER, ordered=True
    )
    frame["criticite_ordinale"] = criticite.codes.astype(float)
    frame.loc[frame["criticite_ordinale"] < 0, "criticite_ordinale"] = np.nan
    rapport["criticite_hors_domaine"] = int(frame["criticite_ordinale"].isna().sum())

    puissance = pd.to_numeric(equipment["rated_power_kw"], errors="coerce")
    rapport["puissance_absente"] = int(puissance.isna().sum())
    frame["puissance_kw"] = puissance.fillna(puissance.median())

    mise_en_service = pd.to_datetime(
        equipment["commissioning_date"], errors="coerce", utc=True
    )
    rapport["date_service_absente"] = int(mise_en_service.isna().sum())
    age = (PERIOD_END - mise_en_service).dt.days / 365.25
    frame["age_annees"] = age.fillna(age.median()).round(2)

    # --- activité : événements ----------------------------------------------
    par_equipement = events.groupby("equipment_id", observed=True)
    n_evenements = par_equipement.size().rename("n_evenements")
    graves = (
        events[events["severity"].isin(SEVERITES_GRAVES)]
        .groupby("equipment_id", observed=True)
        .size()
        .rename("n_evenements_graves")
    )

    # --- activité : interventions -------------------------------------------
    travaux = maintenance.copy()
    downtime = pd.to_numeric(travaux["downtime_minutes"], errors="coerce")
    sentinelles = downtime >= SENTINELLE_DOWNTIME_MIN
    rapport["downtime_sentinelles_neutralisees"] = int(sentinelles.sum())
    rapport["downtime_sentinelles_valeurs"] = sorted(
        {float(v) for v in downtime[sentinelles].unique()}
    )
    rapport["downtime_max_apres_neutralisation"] = float(downtime[~sentinelles].max())
    travaux["downtime_retenu"] = downtime.where(~sentinelles)

    cout = pd.to_numeric(travaux["parts_cost_eur"], errors="coerce")
    rapport["cout_pieces_absent"] = int(cout.isna().sum())
    travaux["cout_retenu"] = cout

    travaux["est_corrective"] = (
        travaux["intervention_type"].astype("string").str.strip().str.lower()
        == "corrective"
    )

    par_travaux = travaux.groupby("equipment_id", observed=True)
    activite = pd.DataFrame(
        {
            "n_interventions": par_travaux.size(),
            "indisponibilite_min": par_travaux["downtime_retenu"].sum(min_count=1),
            "cout_pieces_eur": par_travaux["cout_retenu"].sum(min_count=1),
            "n_correctives": par_travaux["est_corrective"].sum(),
        }
    )

    # --- assemblage ----------------------------------------------------------
    frame = (
        frame.merge(n_evenements, left_on="equipment_id", right_index=True, how="left")
        .merge(graves, left_on="equipment_id", right_index=True, how="left")
        .merge(activite, left_on="equipment_id", right_index=True, how="left")
    )

    compteurs = [
        "n_evenements",
        "n_evenements_graves",
        "n_interventions",
        "indisponibilite_min",
        "cout_pieces_eur",
        "n_correctives",
    ]
    # Un équipement sans événement ni intervention n'a pas une valeur manquante :
    # il a un compteur nul. La distinction est importante — c'est une absence
    # d'activité observée, pas une absence de donnée.
    rapport["equipements_sans_evenement"] = int(frame["n_evenements"].isna().sum())
    rapport["equipements_sans_intervention"] = int(frame["n_interventions"].isna().sum())
    frame[compteurs] = frame[compteurs].fillna(0.0)

    frame["part_correctives"] = np.where(
        frame["n_interventions"] > 0,
        frame["n_correctives"] / frame["n_interventions"],
        0.0,
    ).round(4)

    rapport["colonnes_features"] = FEATURES
    return frame, rapport


def matrice_normalisee(features: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    """Prépare la matrice soumise au partitionnement.

    Les compteurs et montants passent en log(1+x) avant standardisation. Sans
    cette transformation, la partition suivrait les quelques équipements les
    plus coûteux — la leçon du brief 1 sur les valeurs extrêmes vaut ici aussi.
    """
    matrice = features[FEATURES].copy()
    for colonne in FEATURES_LOG:
        matrice[colonne] = np.log1p(matrice[colonne])
    return StandardScaler().fit_transform(matrice.to_numpy(dtype=float)), FEATURES


def explorer_k(matrice: np.ndarray, ks: range) -> pd.DataFrame:
    """Inertie et silhouette pour chaque nombre de groupes envisagé.

    L'inertie décroît mécaniquement avec `k` : lue seule, elle ne désigne aucun
    optimum. La silhouette mesure autre chose — à quel point un point est plus
    proche de son groupe que du groupe voisin — et peut donc être maximisée.
    Les deux sont produites, et le choix s'appuie sur les deux.
    """
    lignes = []
    inertie_precedente = None
    for k in ks:
        modele = KMeans(n_clusters=k, n_init=10, random_state=SEED)
        labels = modele.fit_predict(matrice)
        gain = (
            None
            if inertie_precedente is None
            else round(100 * (inertie_precedente - modele.inertia_) / inertie_precedente, 2)
        )
        lignes.append(
            {
                "k": k,
                "inertie": round(float(modele.inertia_), 2),
                "gain_inertie_pct": gain,
                "silhouette": round(float(silhouette_score(matrice, labels)), 4),
                "plus_petit_groupe": int(np.bincount(labels).min()),
            }
        )
        inertie_precedente = modele.inertia_
    return pd.DataFrame(lignes)


def segmenter(matrice: np.ndarray, k: int) -> np.ndarray:
    """Partitionne le parc en `k` groupes, à graine fixe."""
    return KMeans(n_clusters=k, n_init=10, random_state=SEED).fit_predict(matrice)


def nommer_segments(labels: np.ndarray, prefixe: str = "SEG") -> list[str]:
    """Transforme des étiquettes numériques en identifiants lisibles."""
    return [f"{prefixe}-{int(label) + 1}" for label in labels]


def diagnostiquer_partition(
    features: pd.DataFrame, labels: np.ndarray, seuil: float = 0.90
) -> dict:
    """Cherche un groupe qui ne fait que redire un critère booléen connu.

    Le critère testé est `n_interventions == 0` : ces équipements ont tous
    leurs compteurs d'activité nuls et occupent donc un point unique de
    l'espace. Un partitionnement les isole en premier et la silhouette
    récompense cette séparation, sans que rien n'ait été appris.

    Un premier essai testait `max(features) == 0` sur le groupe, et ne
    détectait rien : certains équipements sans intervention ont malgré tout un
    événement enregistré, donc le maximum du groupe n'est pas nul. Le bon test
    n'est pas l'exactitude arithmétique mais le **recouvrement** entre le
    groupe et le critère, dans les deux sens — pureté et rappel.
    """
    frame = features.assign(_label=labels)
    inactifs = frame["n_interventions"] == 0
    total_inactifs = int(inactifs.sum())

    groupes = []
    for label, groupe in frame.groupby("_label", observed=True):
        part_inactifs = float((groupe["n_interventions"] == 0).mean())
        rappel = (
            float((groupe["n_interventions"] == 0).sum() / total_inactifs)
            if total_inactifs
            else 0.0
        )
        groupes.append(
            {
                "label": int(label),
                "equipements": int(len(groupe)),
                "purete_inactifs_pct": round(100 * part_inactifs, 2),
                "rappel_inactifs_pct": round(100 * rappel, 2),
                "redit_le_critere": bool(part_inactifs >= seuil and rappel >= seuil),
            }
        )

    return {
        "critere_teste": "n_interventions == 0",
        "population_du_critere": total_inactifs,
        "seuil_pct": round(100 * seuil, 1),
        "groupes": groupes,
        "degenere": any(groupe["redit_le_critere"] for groupe in groupes),
    }


def profil_segments(features: pd.DataFrame) -> pd.DataFrame:
    """Décrit chaque segment par ses moyennes et sa composition dominante."""
    groupes = features.groupby("segment", observed=True)
    profil = groupes[FEATURES].mean().round(2)
    profil.insert(0, "equipements", groupes.size())

    profil["type_dominant"] = groupes["equipment_type"].agg(
        lambda s: f"{s.mode().iat[0]} ({100 * (s == s.mode().iat[0]).mean():.0f} %)"
    )
    profil["site_dominant"] = groupes["site_id"].agg(
        lambda s: f"{s.mode().iat[0]} ({100 * (s == s.mode().iat[0]).mean():.0f} %)"
    )
    profil["criticite_dominante"] = groupes["criticality"].agg(
        lambda s: f"{s.mode().iat[0]} ({100 * (s == s.mode().iat[0]).mean():.0f} %)"
    )
    profil["types_distincts"] = groupes["equipment_type"].nunique()
    return profil.reset_index()


def composition_segments(
    features: pd.DataFrame, axes: tuple[str, ...] = ("criticality", "site_id")
) -> pd.DataFrame:
    """Composition des segments selon les variables qui n'ont pas servi.

    C'est le contrôle qui permet d'affirmer — ou de réfuter — que la
    segmentation apporte autre chose que les comptages déjà produits. Si les
    segments ont la même composition en criticité et en site, alors ils
    séparent le parc sur un axe que ces comptages ne montraient pas.
    """
    lignes = []
    for axe in axes:
        croise = pd.crosstab(features["segment"], features[axe])
        parts = (100 * croise.div(croise.sum(axis=1), axis=0)).round(2)
        for segment in croise.index:
            for modalite in croise.columns:
                lignes.append(
                    {
                        "segment": segment,
                        "variable": axe,
                        "modalite": modalite,
                        "equipements": int(croise.loc[segment, modalite]),
                        "part_du_segment_pct": float(parts.loc[segment, modalite]),
                    }
                )
    return pd.DataFrame(lignes)


def croiser_couverture(features: pd.DataFrame) -> pd.DataFrame:
    """Croise les segments avec l'instrumentation — le résultat de l'étape.

    La couverture n'ayant pas servi à construire les segments, le fait qu'elle
    varie d'un segment à l'autre est une observation, pas une conséquence de la
    méthode.
    """
    table = (
        features.groupby("segment", observed=True)["instrumente"]
        .agg(equipements="size", instrumentes="sum")
        .reset_index()
    )
    table["taux_pct"] = (100 * table["instrumentes"] / table["equipements"]).round(2)
    return table.sort_values("taux_pct").reset_index(drop=True)
