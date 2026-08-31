"""Étape 2 du brief 2 — augmenter des séries existantes.

Augmenter, c'est déformer une série réelle pour en obtenir des variantes. Aucune
information n'est créée : chaque technique déplace un compromis, en préservant
certaines propriétés et en en détruisant d'autres.

Le brief exige que ce qu'une technique **détruit** soit décrit, et sanctionne
l'omission. Ce module ne se contente donc pas de transformer : il **mesure**,
pour chaque technique, ce qui a survécu et ce qui n'a pas survécu. Une propriété
annoncée comme préservée sans chiffre à l'appui est une affirmation, pas un
résultat.

Six propriétés sont suivies :

| Propriété | Mesure |
|---|---|
| ordre de grandeur | écart relatif de la moyenne et de l'écart-type |
| fidélité point à point | corrélation avec la série d'origine |
| structure temporelle | autocorrélation aux rangs 2 et 4 — la saisonnalité est journalière |
| régularité du pas | part des intervalles au pas nominal de 6 h |
| plausibilité physique | valeurs sortant de la plage robuste (8 MAD, règle `R-SEN-009`) |
| lien avec les événements | mesures tombant encore dans une fenêtre d'événement |

Une septième est vérifiée parce qu'elle conditionne la transmission : la
**collision de clé logique**. Une augmentation qui conserve le triplet
`equipment_id + timestamp + sensor_name` produit une ligne indiscernable de la
mesure réelle au sens de `R-SEN-001`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

import numpy as np
import pandas as pd


# Pas nominal de la livraison, en heures.
PAS_NOMINAL_H = 6

# Facteur de la plage robuste, repris de la règle R-SEN-009 du brief 1 : écart à
# la médiane exprimé en écarts absolus médians. Critère volontairement identique
# à celui du brief 1 — mesurer la plausibilité avec un autre seuil rendrait les
# deux étapes incomparables.
PLAGE_MAD_FACTOR = 8.0

# Rangs d'autocorrélation suivis, en nombre d'intervalles de 6 h.
#
# Le premier jet ne suivait que le rang 1, et concluait que les séries n'avaient
# pas de structure temporelle (autocorrélation médiane +0,053). C'était faux :
# les séries portent un cycle journalier, à raison de quatre mesures par jour.
# Au rang 1 le signal est en quadrature, donc l'autocorrélation y est nulle par
# construction — c'était exactement le rang où l'on ne pouvait rien voir.
#
#   rang 1 (6 h)  : +0,053   rang 2 (12 h) : -0,644   rang 4 (24 h) : +0,720
#
# Les rangs 2 et 4 portent la saisonnalité et servent donc au verdict ; le rang 1
# est conservé pour mémoire du raté.
LAGS_AUTOCORR = (1, 2, 4)
LAGS_STRUCTURE = (2, 4)


@dataclass
class Technique:
    """Une transformation, son identifiant de procédé et ses paramètres."""

    procedure_id: str
    nom: str
    famille: str
    parametres: dict
    applique: Callable[[pd.DataFrame, np.random.Generator], pd.DataFrame]
    intention: str = ""
    attendu_preserve: list[str] = field(default_factory=list)
    attendu_detruit: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------
# Transformations
# --------------------------------------------------------------------------


def bruit_gaussien(serie: pd.DataFrame, generateur: np.random.Generator, ratio: float = 0.02) -> pd.DataFrame:
    """Ajoute un bruit centré, d'écart-type proportionnel à celui de la série.

    Le bruit est calibré sur la dispersion propre de chaque série : un écart
    absolu fixe serait négligeable sur un régime moteur et énorme sur une
    vibration.
    """
    augmentee = serie.copy()
    sigma = float(serie["value"].std(ddof=0)) * ratio
    augmentee["value"] = (serie["value"] + generateur.normal(0.0, sigma, len(serie))).round(2)
    return augmentee


def mise_a_echelle(serie: pd.DataFrame, generateur: np.random.Generator, facteur: float = 1.05) -> pd.DataFrame:
    """Multiplie toutes les valeurs par un facteur constant.

    Simule un défaut d'étalonnage ou un changement d'unité mal converti. La
    forme de la série est intacte, son niveau ne l'est plus.
    """
    augmentee = serie.copy()
    augmentee["value"] = (serie["value"] * facteur).round(2)
    return augmentee


def decalage_temporel(serie: pd.DataFrame, generateur: np.random.Generator, pas: int = 3) -> pd.DataFrame:
    """Décale toute la série de `pas` intervalles nominaux, valeurs inchangées.

    Aucune valeur n'est touchée : la distribution est rigoureusement identique.
    C'est le contre-exemple le plus net du brief — une transformation qui ne
    change aucun histogramme et détruit pourtant le lien avec les événements.
    """
    augmentee = serie.copy()
    augmentee["timestamp"] = serie["timestamp"] + pd.Timedelta(hours=PAS_NOMINAL_H * pas)
    return augmentee


def permutation_segments(serie: pd.DataFrame, generateur: np.random.Generator, taille_bloc: int = 4) -> pd.DataFrame:
    """Découpe la série en blocs contigus et permute leur ordre.

    Les valeurs sont conservées à l'identique et les horodatages aussi : seule
    leur association change. Les marginales sont donc **exactement** préservées,
    y compris les quantiles. Ce que la permutation détruit — la structure
    temporelle — n'apparaît sur aucun histogramme.
    """
    augmentee = serie.copy()
    valeurs = serie["value"].to_numpy()
    blocs = [valeurs[i : i + taille_bloc] for i in range(0, len(valeurs), taille_bloc)]
    ordre = generateur.permutation(len(blocs))
    augmentee["value"] = np.concatenate([blocs[i] for i in ordre])[: len(valeurs)]
    return augmentee


def deformation_temporelle(serie: pd.DataFrame, generateur: np.random.Generator, amplitude: float = 0.25) -> pd.DataFrame:
    """Étire ou comprime chaque intervalle, valeurs inchangées.

    Chaque écart entre deux mesures est multiplié par un facteur tiré dans
    `[1 - amplitude, 1 + amplitude]`. La série garde sa forme mais perd sa
    grille : c'est la transformation la plus visible pour un contrôle
    d'échantillonnage, et la moins visible pour un contrôle de distribution.
    """
    augmentee = serie.copy()
    depart = serie["timestamp"].iloc[0]
    ecarts = serie["timestamp"].diff().dt.total_seconds().to_numpy()[1:]
    facteurs = generateur.uniform(1 - amplitude, 1 + amplitude, len(ecarts))
    cumules = np.concatenate([[0.0], np.cumsum(ecarts * facteurs)])
    augmentee["timestamp"] = depart + pd.to_timedelta(cumules.round(), unit="s")
    return augmentee


TECHNIQUES: list[Technique] = [
    Technique(
        procedure_id="PROC-AUG-BRUIT",
        nom="Bruit gaussien additif",
        famille="valeur",
        parametres={"sigma_ratio_ecart_type": 0.02},
        applique=bruit_gaussien,
        intention="produire des variantes proches sans changer le régime de la série",
        attendu_preserve=["ordre de grandeur", "régularité du pas", "lien aux événements"],
        attendu_detruit=["valeurs exactes", "un peu d'autocorrélation"],
    ),
    Technique(
        procedure_id="PROC-AUG-ECHELLE",
        nom="Mise à l'échelle multiplicative",
        famille="valeur",
        parametres={"facteur": 1.05},
        applique=mise_a_echelle,
        intention="simuler un défaut d'étalonnage",
        attendu_preserve=["forme", "autocorrélation", "régularité du pas"],
        attendu_detruit=["niveau absolu", "plausibilité si dépassement de plage"],
    ),
    Technique(
        procedure_id="PROC-AUG-DECALAGE",
        nom="Décalage temporel global",
        famille="temps",
        parametres={"pas_nominaux": 3, "heures": 18},
        applique=decalage_temporel,
        intention="produire une variante décorrélée du calendrier réel",
        attendu_preserve=["toutes les marginales", "autocorrélation", "régularité du pas"],
        attendu_detruit=["lien aux événements", "appartenance à la période annoncée"],
    ),
    Technique(
        procedure_id="PROC-AUG-PERMUT",
        nom="Permutation de segments",
        famille="structure",
        parametres={"taille_bloc": 4, "duree_bloc_h": 24},
        applique=permutation_segments,
        intention="conserver la population de valeurs en cassant leur ordre",
        attendu_preserve=["marginales exactes", "régularité du pas", "plausibilité"],
        attendu_detruit=["structure temporelle", "lien aux événements"],
    ),
    Technique(
        procedure_id="PROC-AUG-DEFORM",
        nom="Déformation de l'axe temporel",
        famille="temps",
        parametres={"amplitude": 0.25},
        applique=deformation_temporelle,
        intention="produire une variante au rythme irrégulier",
        attendu_preserve=["toutes les marginales", "forme de la série"],
        attendu_detruit=["grille d'échantillonnage", "lien aux événements"],
    ),
]


# --------------------------------------------------------------------------
# Mesure de ce qui survit
# --------------------------------------------------------------------------


def plage_robuste(valeurs: pd.Series, facteur: float = PLAGE_MAD_FACTOR) -> tuple[float, float]:
    """Bornes de plausibilité au sens de `R-SEN-009` : médiane ± k × MAD."""
    mediane = float(valeurs.median())
    mad = float((valeurs - mediane).abs().median())
    if mad == 0.0:
        # Série constante : la MAD n'a plus de pouvoir séparateur. Le brief 1
        # traitait ce cas par la règle « capteur figé » (R-SEN-010), pas par la
        # plage. On ne borne donc rien plutôt que de borner à zéro.
        return (-np.inf, np.inf)
    return (mediane - facteur * mad, mediane + facteur * mad)


def profil_autocorrelation(valeurs: pd.Series, lags: tuple[int, ...] = LAGS_AUTOCORR) -> dict:
    """Autocorrélation à plusieurs rangs, pour ne pas dépendre d'un seul."""
    profil = {}
    for lag in lags:
        valeur = valeurs.autocorr(lag=lag)
        profil[lag] = None if pd.isna(valeur) else round(float(valeur), 4)
    return profil


def part_pas_nominal(horodatages: pd.Series) -> float:
    """Part des intervalles exactement égaux au pas nominal."""
    ecarts = horodatages.diff().dropna().dt.total_seconds() / 3600
    if ecarts.empty:
        return float("nan")
    return round(100 * float((ecarts == PAS_NOMINAL_H).mean()), 2)


def masque_fenetres(
    horodatages: pd.Series, fenetres: list[tuple[pd.Timestamp, pd.Timestamp]]
) -> pd.Series:
    """Marque les mesures tombant dans au moins une fenêtre d'événement."""
    dedans = pd.Series(False, index=horodatages.index)
    if not fenetres:
        return dedans
    for debut, fin in fenetres:
        dedans |= (horodatages >= debut) & (horodatages <= fin)
    return dedans


def signal_en_fenetre(
    horodatages: pd.Series,
    valeurs: pd.Series,
    fenetres: list[tuple[pd.Timestamp, pd.Timestamp]],
) -> float | None:
    """Niveau moyen observé pendant les fenêtres d'événement.

    Compter les mesures présentes dans une fenêtre ne suffit pas à établir
    qu'un lien subsiste. Une permutation de valeurs ne déplace aucun
    horodatage : le compte reste identique et le lien est pourtant rompu, les
    valeurs associées à l'événement n'étant plus les siennes. Le niveau moyen
    pendant la fenêtre, lui, bouge.
    """
    dedans = masque_fenetres(horodatages, fenetres)
    if not dedans.any():
        return None
    return round(float(valeurs[dedans].mean()), 4)


def dans_fenetres(horodatages: pd.Series, fenetres: list[tuple[pd.Timestamp, pd.Timestamp]]) -> int:
    """Nombre de mesures tombant dans au moins une fenêtre d'événement."""
    if not fenetres:
        return 0
    # Comparaison en pandas et non en numpy : `np.datetime64` perd le fuseau
    # horaire, et comparer un horodatage UTC à un horodatage naïf lève une
    # erreur — ou pire, passerait silencieusement si les deux étaient naïfs.
    dedans = pd.Series(False, index=horodatages.index)
    for debut, fin in fenetres:
        dedans |= (horodatages >= debut) & (horodatages <= fin)
    return int(dedans.sum())


def mesurer(
    original: pd.DataFrame,
    augmentee: pd.DataFrame,
    fenetres: list[tuple[pd.Timestamp, pd.Timestamp]],
) -> dict:
    """Compare une série augmentée à son original, propriété par propriété."""
    valeurs_avant = original["value"]
    valeurs_apres = augmentee["value"]
    basse, haute = plage_robuste(valeurs_avant)

    moyenne_avant = float(valeurs_avant.mean())
    ecart_avant = float(valeurs_avant.std(ddof=0))

    # La corrélation point à point n'a de sens que si l'axe temporel n'a pas
    # bougé : comparer deux séries décalées reviendrait à mesurer autre chose.
    axe_identique = bool(original["timestamp"].equals(augmentee["timestamp"]))
    correlation = (
        round(float(valeurs_avant.corr(valeurs_apres)), 4)
        if axe_identique and valeurs_apres.std(ddof=0) > 0
        else None
    )

    # Une ligne augmentée entre en collision de clé logique dès que son triplet
    # `equipment_id + timestamp + sensor_name` existe déjà dans la table réelle.
    # L'équipement et le capteur étant conservés par construction, seule la
    # coïncidence des horodatages est à compter.
    collisions = int(augmentee["timestamp"].isin(set(original["timestamp"])).sum())

    moyenne_apres = float(valeurs_apres.mean())
    ecart_apres = float(valeurs_apres.std(ddof=0))
    profil_avant = profil_autocorrelation(valeurs_avant)
    profil_apres = profil_autocorrelation(valeurs_apres)

    return {
        "lignes": int(len(augmentee)),
        "axe_temporel_identique": axe_identique,
        "moyenne_avant": round(moyenne_avant, 4),
        "moyenne_apres": round(moyenne_apres, 4),
        "delta_moyenne_pct": (
            round(100 * (moyenne_apres - moyenne_avant) / moyenne_avant, 4)
            if moyenne_avant
            else None
        ),
        "ecart_type_avant": round(ecart_avant, 4),
        "ecart_type_apres": round(ecart_apres, 4),
        "delta_ecart_type_pct": (
            round(100 * (ecart_apres - ecart_avant) / ecart_avant, 4) if ecart_avant else None
        ),
        "correlation_point_a_point": correlation,
        **{
            f"autocorr_lag{lag}_avant": profil_avant[lag] for lag in LAGS_AUTOCORR
        },
        **{
            f"autocorr_lag{lag}_apres": profil_apres[lag] for lag in LAGS_AUTOCORR
        },
        "part_pas_nominal_avant_pct": part_pas_nominal(original["timestamp"]),
        "part_pas_nominal_apres_pct": part_pas_nominal(augmentee["timestamp"]),
        "hors_plage_robuste_avant": int(
            ((valeurs_avant < basse) | (valeurs_avant > haute)).sum()
        ),
        "hors_plage_robuste_apres": int(
            ((valeurs_apres < basse) | (valeurs_apres > haute)).sum()
        ),
        "en_fenetre_evenement_avant": dans_fenetres(original["timestamp"], fenetres),
        "en_fenetre_evenement_apres": dans_fenetres(augmentee["timestamp"], fenetres),
        "signal_en_fenetre_avant": signal_en_fenetre(
            original["timestamp"], original["value"], fenetres
        ),
        "signal_en_fenetre_apres": signal_en_fenetre(
            augmentee["timestamp"], augmentee["value"], fenetres
        ),
        "collisions_cle_logique": collisions,
    }
