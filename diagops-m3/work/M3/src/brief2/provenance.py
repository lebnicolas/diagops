"""Contrat de provenance et registre des procédés — brief 2, étape 6.

Le `SCHEMA.md` du pack `diagops-2026-S1-m3-v2` impose que toute table de mesures
transmise déclare, ligne à ligne, une `provenance` (`réelle` / `synthétique` /
`augmentée`) et le `procedure_id` qui l'a produite. Transmettre du fabriqué sans
provenance est un critère bloquant du brief : ce module est l'endroit unique où
le contrat est écrit, appliqué et vérifié.

Un procédé n'est pas qu'un identifiant. Le brief demande qu'une donnée fabriquée
porte **une date, un procédé, une raison et une durée de validité** : le registre
ci-dessous porte les quatre, plus le statut de transmission — car tous les
procédés produits au brief 2 ne sont pas transmis, et le motif de chaque exclusion
se défend.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


#: Colonnes du jeu de mesures transmis, dans l'ordre. `row_identifier` en est
#: absente volontairement : c'est une colonne de travail du brief 1, et le
#: détecteur de référence la signale comme colonne inattendue (soumission T1-04).
COLONNES_TRANSMISES = (
    "equipment_id",
    "timestamp",
    "sensor_name",
    "value",
    "unit",
    "period",
    "provenance",
    "procedure_id",
)

#: Domaine fermé de la colonne `provenance`.
PROVENANCES = ("réelle", "synthétique", "augmentée")

#: Convention de précision de la livraison amont : deux décimales.
DECIMALES = 2

#: Échéance de réexamen de toute ligne fabriquée transmise à M4. Ce n'est pas une
#: date de péremption technique : c'est la date à laquelle la question « ces
#: lignes sont-elles encore nécessaires ? » doit être reposée, faute de quoi le
#: provisoire devient un socle.
ECHEANCE_REEXAMEN = "2026-12-31"


@dataclass(frozen=True)
class Procede:
    """Un procédé de fabrication, tel qu'il est déclaré au contrat."""

    procedure_id: str
    famille: str  # génération | augmentation
    provenance: str
    date: str
    raison: str
    parametres: str
    validite: str
    transmis: bool
    motif_transmission: str
    etape: str
    lignes: int | None = field(default=None)


#: Registre des procédés produits au brief 2. Les volumes sont ceux constatés à
#: l'exécution ; ils sont revérifiés à la composition du jeu transmis.
REGISTRE: tuple[Procede, ...] = (
    Procede(
        procedure_id="PROC-GEN-SMOTE-V2",
        famille="génération",
        provenance="synthétique",
        date="2026-08-26",
        raison=(
            "documenter 8 équipements de SITE-OUEST ∩ SEG-2, périmètre sans "
            "aucun capteur réel (0/16 sur le site, 2/174 sur le segment)"
        ),
        parametres=(
            "interpolation entre voisins écrite à la main, k = 5, pénalité de "
            "type 1.0, λ ∈ [−0,25 ; 1,25], graine 25082026"
        ),
        validite=(
            "jusqu'à la première livraison de mesures réelles sur SITE-OUEST, "
            f"réexamen au plus tard le {ECHEANCE_REEXAMEN}"
        ),
        transmis=True,
        motif_transmission=(
            "seul procédé qui conserve une structure temporelle et une réaction "
            "aux événements ; état 2 du générateur, dispersion corrigée"
        ),
        etape="3",
        lignes=1799,
    ),
    Procede(
        procedure_id="PROC-GEN-SMOTE-V1",
        famille="génération",
        provenance="synthétique",
        date="2026-08-26",
        raison="premier état du générateur par interpolation entre voisins",
        parametres="k = 5, λ ∈ [0 ; 1], graine 25082026",
        validite="périmé — remplacé par PROC-GEN-SMOTE-V2 le 26/08",
        transmis=False,
        motif_transmission=(
            "dispersion contractée de 15 à 22 % (ratios σ 0,783 et 0,810) ; "
            "conservé comme état 1 de la démonstration, pas comme donnée"
        ),
        etape="3",
        lignes=1799,
    ),
    Procede(
        procedure_id="PROC-GEN-MARG-V1",
        famille="génération",
        provenance="synthétique",
        date="2026-08-26",
        raison="voie de comparaison — tirage marginal, chaque colonne rejouée seule",
        parametres="tirage indépendant par capteur sur la marginale réelle, graine 25082026",
        validite="non transmis — sans objet",
        transmis=False,
        motif_transmission=(
            "détruit toute structure temporelle (autocorrélation nulle) et toute "
            "corrélation entre capteurs ; transmettre ces lignes injecterait un "
            "bruit que M4 apprendrait comme un signal"
        ),
        etape="3",
        lignes=1984,
    ),
    Procede(
        procedure_id="PROC-AUG-BRUIT",
        famille="augmentation",
        provenance="augmentée",
        date="2026-08-25",
        raison="démonstration — perturbation gaussienne à 2 % de l'écart-type",
        parametres="σ_bruit = 0,02 × σ_série, graine 25082026",
        validite="non transmis — sans objet",
        transmis=False,
        motif_transmission=(
            "série support hors grille horaire : 721 lignes signalées sur 721 "
            "avant toute augmentation (T2-00). Transmettre une augmentation "
            "assise sur un support non conforme propagerait le défaut"
        ),
        etape="2",
        lignes=721,
    ),
    Procede(
        procedure_id="PROC-AUG-ECHELLE",
        famille="augmentation",
        provenance="augmentée",
        date="2026-08-25",
        raison="démonstration — mise à l'échelle multiplicative",
        parametres="facteur ×1,05, graine 25082026",
        validite="non transmis — sans objet",
        transmis=False,
        motif_transmission=(
            "biais de niveau de 0,391 σ que le détecteur ne signale pas : cas "
            "conservé comme démonstration d'angle mort, jamais comme donnée"
        ),
        etape="2",
        lignes=721,
    ),
    Procede(
        procedure_id="PROC-AUG-DECALAGE",
        famille="augmentation",
        provenance="augmentée",
        date="2026-08-25",
        raison="démonstration — décalage temporel de la série",
        parametres="décalage +18 h, multiple du pas nominal, graine 25082026",
        validite="non transmis — sans objet",
        transmis=False,
        motif_transmission="même support non conforme que PROC-AUG-BRUIT",
        etape="2",
        lignes=721,
    ),
    Procede(
        procedure_id="PROC-AUG-DEFORM",
        famille="augmentation",
        provenance="augmentée",
        date="2026-08-25",
        raison="démonstration — déformation locale de l'axe des temps",
        parametres="étirement/compression par blocs, graine 25082026",
        validite="non transmis — sans objet",
        transmis=False,
        motif_transmission=(
            "détruit la régularité du pas ; le comptage du détecteur était déjà "
            "saturé sur le support, la contribution du procédé n'est pas mesurable"
        ),
        etape="2",
        lignes=721,
    ),
    Procede(
        procedure_id="PROC-AUG-PERMUT",
        famille="augmentation",
        provenance="augmentée",
        date="2026-08-25",
        raison="démonstration — permutation aléatoire des valeurs de la série",
        parametres="permutation complète, graine 25082026",
        validite="non transmis — sans objet",
        transmis=False,
        motif_transmission=(
            "détruit intégralement la structure temporelle en rendant des "
            "marginales identiques au réel — le cas d'aveuglement du détecteur"
        ),
        etape="2",
        lignes=721,
    ),
)


def normaliser_precision(frame: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """`R-TRA-001` — ramène `value` à la convention de précision de la livraison.

    Motif, découvert par la soumission T3-00 du 31/08 : `EQ-SENSOR-305` livre 84
    mesures en kelvins, que la règle `R-SEN-006` du brief 1 convertit par
    `v − 273,15`. La conversion est juste, mais son résultat est écrit tel quel —
    `56.85000000000002`. Le défaut a traversé tout le brief 1 sans être vu par
    nos propres contrôles, qui ne portaient pas sur la précision d'écriture.

    Correction faite **ici**, au point de transmission, et non dans
    `prepare_sensors` : rejouer la chaîne du brief 1 changerait toutes les
    empreintes citées dans les deux briefs déjà rendus. Le correctif à porter en
    amont est inscrit comme dette dans la note de décision.

    Rend le jeu corrigé et le nombre de valeurs effectivement modifiées.
    """
    corrige = frame.copy()
    valeurs = pd.to_numeric(corrige["value"], errors="coerce")
    arrondies = valeurs.round(DECIMALES)
    modifiees = int(((valeurs - arrondies).abs() > 0).sum())
    corrige["value"] = arrondies
    return corrige, modifiees


def registre_dataframe() -> pd.DataFrame:
    """Registre des procédés sous forme tabulaire, pour le livrable."""
    return pd.DataFrame([procede.__dict__ for procede in REGISTRE])


def procedes_transmis() -> tuple[Procede, ...]:
    """Procédés dont les lignes entrent dans le jeu transmis à M4."""
    return tuple(procede for procede in REGISTRE if procede.transmis)


def etiqueter(frame: pd.DataFrame, provenance: str, procedure_id: str) -> pd.DataFrame:
    """Applique le contrat de provenance à une table de mesures.

    La table est réduite aux colonnes du contrat : toute colonne de travail est
    retirée ici, et non plus loin, pour qu'aucun chemin ne puisse produire un
    fichier transmis hors contrat.
    """
    if provenance not in PROVENANCES:
        raise ValueError(f"provenance hors domaine : {provenance!r}")

    etiquete = frame.copy()
    etiquete["provenance"] = provenance
    etiquete["procedure_id"] = procedure_id

    manquantes = [col for col in COLONNES_TRANSMISES if col not in etiquete.columns]
    if manquantes:
        raise ValueError("colonnes absentes du contrat : " + ", ".join(manquantes))
    return etiquete.loc[:, list(COLONNES_TRANSMISES)]


def verifier_contrat(frame: pd.DataFrame) -> dict[str, object]:
    """Contrôle le respect du contrat de provenance sur un jeu transmis.

    Rend un rapport plutôt qu'une exception : un contrôle qui s'arrête à la
    première faute ne dit pas combien il y en a.
    """
    connus = {procede.procedure_id for procede in REGISTRE}
    colonnes_attendues = list(COLONNES_TRANSMISES)

    provenance_absente = int(frame["provenance"].isna().sum()) if "provenance" in frame else len(frame)
    hors_domaine = (
        int((~frame["provenance"].isin(PROVENANCES)).sum()) if "provenance" in frame else len(frame)
    )
    fabriquees = frame[frame["provenance"] != "réelle"] if "provenance" in frame else frame
    sans_procede = int(
        fabriquees["procedure_id"].isna().sum() + (fabriquees["procedure_id"] == "").sum()
    )
    procedes_inconnus = sorted(
        set(fabriquees["procedure_id"].dropna().unique()) - connus - {""}
    )
    reelles_avec_procede = int(
        (frame.loc[frame["provenance"] == "réelle", "procedure_id"].fillna("") != "").sum()
    )

    return {
        "lignes": int(len(frame)),
        "colonnes_conformes": list(frame.columns) == colonnes_attendues,
        "colonnes_observees": list(frame.columns),
        "provenance_absente": provenance_absente,
        "provenance_hors_domaine": hors_domaine,
        "fabriquees_sans_procede": sans_procede,
        "procedes_inconnus": procedes_inconnus,
        "reelles_portant_un_procede": reelles_avec_procede,
        "conforme": (
            list(frame.columns) == colonnes_attendues
            and provenance_absente == 0
            and hors_domaine == 0
            and sans_procede == 0
            and not procedes_inconnus
            and reelles_avec_procede == 0
        ),
    }
