"""Brief 2, étape 5 — protéger un agrégat par le mécanisme de Laplace.

L'agrégat retenu (arbitrage A4) est le **coût moyen des pièces par site et par
criticité** : seize cellules, dont les effectifs vont de 4 à 319 interventions.

Le choix n'est pas anodin. Sur un comptage, la sensibilité vaut 1 et le sujet se
réduit au réglage d'un curseur. Sur une **moyenne**, elle dépend de l'amplitude
des valeurs *et* de l'effectif de la cellule : la même publication protège très
inégalement selon la case du tableau, et c'est ce que l'étape doit montrer.

## Ce que le mécanisme protège, et contre quoi

Le modèle de menace est le suivant : quelqu'un connaît toutes les interventions
d'une cellule sauf une, et cherche à retrouver le coût de celle qui lui manque.
Publier la moyenne exacte la lui donne — il suffit de soustraire. Le mécanisme
ajoute un bruit calibré sur ce qu'une seule intervention peut changer.

## Pourquoi il faut borner les coûts

La sensibilité d'une somme est l'amplitude maximale qu'une observation peut lui
faire prendre. Sans borne supérieure déclarée, cette amplitude est celle du
maximum observé — 1 127,58 € — et ce maximum est lui-même une donnée du jeu :
le publier implicitement, c'est déjà fuiter. Borner les coûts à un plafond fixé
**à l'avance** résout les deux problèmes, au prix d'un biais de troncature qu'il
faut mesurer et non supposer négligeable.

## Pourquoi le budget se partage

La moyenne est un quotient. Publier une somme bruitée et un effectif exact
laisse fuiter l'effectif, qui est lui-même une information — surtout sur une
cellule à quatre interventions. Les deux quantités sont donc bruitées, chacune
avec la moitié du budget : par composition, l'ensemble consomme bien `ε`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# Plafonds de bornage évalués. Le bas de la plage est fixé à 0 : un coût de
# pièces négatif n'a pas de sens, et le minimum observé (3 €) est une donnée
# du jeu qu'on ne veut pas publier en creux.
PLAFONDS = (1128.0, 750.0, 500.0)
PLAFOND_RETENU = 750.0

# Budgets évalués. Le pas est multiplicatif : l'effet du bruit varie comme 1/ε,
# donc une progression arithmétique écraserait tout le bas de la plage.
EPSILONS = (0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0, 50.0)

# Nombre de tirages par cellule et par budget. Le mécanisme est aléatoire :
# un tirage unique ne dit rien, et présenter un tirage unique comme « le
# résultat » serait la faute exacte que le brief sanctionne.
TIRAGES = 2000

# Part du budget allouée à la somme. Le reste va à l'effectif.
PART_SOMME = 0.5

# Tolérance de l'attaque par différenciation, en euros. Estimer à ±50 € le coût
# d'une intervention qui en vaut 220 en moyenne est déjà une information sur
# cette intervention précise : c'est le seuil au-delà duquel on considère que le
# mécanisme n'a plus rien protégé.
TOLERANCE_ATTAQUE_EUR = 50.0


def bruit_laplace(generateur: np.random.Generator, echelle: float, taille: int) -> np.ndarray:
    """Tirage de Laplace centré, d'échelle `b = sensibilité / ε`.

    Écrit à la main plutôt qu'appelé depuis une bibliothèque : le brief demande
    que le mécanisme soit visible. La loi s'obtient par inversion de sa fonction
    de répartition — `−b · signe(u) · ln(1 − 2|u|)` pour `u` uniforme sur
    `]−0,5 ; 0,5[`.
    """
    uniforme = generateur.uniform(-0.5, 0.5, size=taille)
    return -echelle * np.sign(uniforme) * np.log1p(-2 * np.abs(uniforme))


def sensibilites(plafond: float) -> dict[str, float]:
    """Sensibilité de chacune des deux quantités publiées.

    Ajouter ou retirer une intervention change la somme d'au plus `plafond` —
    les coûts étant bornés à `[0, plafond]` — et l'effectif d'exactement 1.
    """
    return {"somme": float(plafond), "effectif": 1.0}


def publier_moyenne(
    valeurs: np.ndarray,
    epsilon: float,
    plafond: float,
    generateur: np.random.Generator,
    tirages: int = TIRAGES,
) -> np.ndarray:
    """Moyenne publiée sous budget `ε`, répétée `tirages` fois.

    La somme et l'effectif sont bruités séparément, puis divisés. Le quotient de
    deux quantités bruitées n'est pas centré sur la vraie moyenne — c'est une
    propriété du mécanisme, pas un défaut de l'implémentation, et elle se voit
    surtout sur les petits effectifs, où l'effectif bruité peut s'approcher de
    zéro. Ce comportement fait partie de ce qu'il faut mesurer.
    """
    bornees = np.clip(valeurs, 0.0, plafond)
    sensibilite = sensibilites(plafond)
    budget_somme = epsilon * PART_SOMME
    budget_effectif = epsilon * (1.0 - PART_SOMME)

    sommes = bornees.sum() + bruit_laplace(
        generateur, sensibilite["somme"] / budget_somme, tirages
    )
    effectifs = len(bornees) + bruit_laplace(
        generateur, sensibilite["effectif"] / budget_effectif, tirages
    )
    # Un effectif publié inférieur à 1 n'a pas de sens : il est ramené à 1, ce
    # qui est une post-correction admissible (elle ne consomme pas de budget,
    # n'utilisant que la sortie déjà bruitée).
    effectifs = np.maximum(effectifs, 1.0)
    return sommes / effectifs


def mesurer(
    publiees: np.ndarray, vraie: float, plafond: float, reference_globale: float
) -> dict[str, float]:
    """Indicateurs d'utilité et de protection d'une cellule, sur tous les tirages.

    Tous portent sur l'**utilité** : erreur absolue, intervalle de publication,
    part de sorties aberrantes, et surtout `part_conclusion_conservee` — la
    publication dit-elle encore de quel côté de la moyenne générale se situe la
    cellule ? C'est la seule question à laquelle un lecteur du tableau cherche
    vraiment une réponse.

    La **protection** ne se mesure pas ici. Une première version de ce module
    l'évaluait par la part des tirages où la moyenne vraie était retrouvée à
    10 % près, ce qui est une erreur de raisonnement : la confidentialité
    différentielle ne promet pas de cacher l'agrégat, elle promet de borner ce
    que la publication révèle d'une observation isolée. Cet indicateur mesurait
    donc la précision, et concluait à l'envers — qu'une grande cellule protège
    moins qu'une petite. Voir `attaque_par_differenciation`.
    """
    absolues = np.abs(publiees - vraie)
    au_dessus_vrai = vraie >= reference_globale
    return {
        "erreur_absolue_mediane": round(float(np.median(absolues)), 2),
        "erreur_relative_mediane": round(float(np.median(absolues) / vraie), 4)
        if vraie
        else None,
        "intervalle_5_95": [
            round(float(np.quantile(publiees, 0.05)), 2),
            round(float(np.quantile(publiees, 0.95)), 2),
        ],
        "part_hors_plage": round(
            float(((publiees < 0) | (publiees > plafond)).mean()), 4
        ),
        "part_conclusion_conservee": round(
            float(((publiees >= reference_globale) == au_dessus_vrai).mean()), 4
        ),
    }


def attaque_par_differenciation(
    epsilon: float, plafond: float, generateur: np.random.Generator, tirages: int = TIRAGES
) -> dict[str, float]:
    """Mesure ce qu'un adversaire bien informé apprend sur **une** intervention.

    Le modèle : l'adversaire connaît toutes les interventions de la cellule sauf
    une, et veut le coût de celle qui lui manque. Il soustrait ce qu'il sait de
    la somme publiée ; il lui reste la valeur cible plus le bruit du mécanisme.
    Son erreur d'estimation **est** le bruit de Laplace appliqué à la somme.

    Deux conséquences, et la première invalide une mesure qu'il aurait été
    tentant d'utiliser :

    - la protection ne dépend **pas** de l'effectif de la cellule. L'échelle du
      bruit sur la somme vaut `plafond / (ε · part_somme)`, quel que soit `n` ;
    - retrouver la **moyenne** publiée n'est pas une attaque. La confidentialité
      différentielle ne promet nulle part de cacher un agrégat — elle promet de
      borner ce que la publication révèle d'une observation isolée. Mesurer la
      protection par la précision de la moyenne revient à confondre les deux, et
      conduit à conclure qu'un grand effectif protège moins, ce qui est faux.
    """
    echelle = plafond / (epsilon * PART_SOMME)
    erreurs = np.abs(bruit_laplace(generateur, echelle, tirages))
    return {
        "echelle_bruit": round(float(echelle), 1),
        "erreur_estimation_mediane": round(float(np.median(erreurs)), 1),
        "part_cible_retrouvee": round(
            float((erreurs <= TOLERANCE_ATTAQUE_EUR).mean()), 4
        ),
    }


def agregat_reference(
    interventions: pd.DataFrame, plafond: float
) -> pd.DataFrame:
    """Tableau vrai, sans bruit — la référence à laquelle tout est comparé.

    Les interventions dont le coût n'est pas renseigné sont exclues du calcul,
    comme elles le seraient dans n'importe quelle publication. Leur répartition
    est tout sauf uniforme et cette lacune est reprise à l'étape 6.
    """
    lignes = []
    for (site, criticite), groupe in interventions.groupby(["site_id", "criticality"]):
        valeurs = groupe["parts_cost_eur"].dropna().to_numpy(dtype=float)
        if not len(valeurs):
            continue
        bornees = np.clip(valeurs, 0.0, plafond)
        lignes.append(
            {
                "site_id": site,
                "criticality": criticite,
                "effectif": int(len(valeurs)),
                "effectif_total": int(len(groupe)),
                "cout_moyen": round(float(valeurs.mean()), 2),
                "cout_moyen_borne": round(float(bornees.mean()), 2),
                "biais_troncature": round(float(bornees.mean() - valeurs.mean()), 2),
                "sensibilite_somme": float(plafond),
            }
        )
    return pd.DataFrame(lignes)
