"""Construit le notebook du brief 2 M3 — capacité du jeu de données."""

from pathlib import Path

import nbformat as nbf

NOTEBOOK = Path(
    r"C:\devs\formation-Simplon\projets\diagops-m3\work\M3\notebooks\notebook_capacite_m3_b2.ipynb"
)

cells = []


def md(text: str) -> None:
    cells.append(nbf.v4.new_markdown_cell(text.strip("\n")))


def code(text: str) -> None:
    cells.append(nbf.v4.new_code_cell(text.strip("\n")))


md(
    """
# M3 — Brief 2 : ce que ce jeu de données permet, et ce qu'il faut fabriquer pour la suite

Le brief 1 a conclu sur la **qualité** des données : `utilisable sous conditions`.
Ce notebook porte sur leur **capacité** — un jeu irréprochable peut être incapable
de porter la question qu'on veut lui poser.

**Convention de ce notebook.** Le calcul lourd vit dans les scripts `run_*_b2.py`
et les modules `src/brief2/`, pas ici : c'est ce qui rend le travail rejouable à
graine fixe hors de tout noyau Jupyter. Le notebook charge leurs sorties, les
met en regard, rejoue en direct les mécanismes qui se démontrent mieux qu'ils ne
se racontent — traitement des catégories, mécanisme de Laplace — et conclut.

Pour tout rejouer depuis zéro :

```bash
python run_capacite_b2.py && python run_augmentation_b2.py && python run_generation_b2.py
python run_detection_b2.py && python run_verdicts_b2.py && python run_confidentialite_b2.py
python run_transmission_b2.py
```

**Graine unique** : `SEED = 25082026`. La graine du lot de contrôle amont
(`20260825`) n'est volontairement pas réutilisée, pour qu'aucune reproduction ne
soit ambiguë.
"""
)

md("## 0. Point de départ et intégrité")

code(
    """
import json
import os
import sys
from pathlib import Path

import pandas as pd
from IPython.display import Image, display

# Le notebook vit dans notebooks/ ; les modules et les sorties sont à la racine
# de work/M3. On s'y place une fois pour toutes.
RACINE = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
os.chdir(RACINE)
sys.path.insert(0, str(RACINE))

pd.set_option("display.max_columns", 40)
pd.set_option("display.width", 160)

OUT = RACINE / "output"


def charger(chemin):
    return json.loads((OUT / chemin).read_text(encoding="utf-8"))


from src.brief2.seed import SEED
from src.brief2.sources import prepared_checksums

print("racine :", RACINE)
print("graine :", SEED)
"""
)

md(
    """
**Arbitrage A1** — le brief 2 part de **notre préparation du brief 1**
(`output/processed/`), et non de la référence commune `m2_for_m3`. Cette
préparation en dérive, la filiation reste traçable, et le rapprochement temporel
du brief 1 devient exploitable comme instrument de détection à l'étape 4.

Les empreintes ci-dessous rattachent tout ce qui suit à un état précis des
fichiers.
"""
)

code(
    """
empreintes = pd.Series(prepared_checksums()).str.slice(0, 16) + "…"
display(empreintes.to_frame("SHA-256 (tronqué)"))

capacite = charger("capacite/capacite.json")
depart = capacite["point_de_depart"]
print(
    f"parc {depart['parc']} · événements {depart['evenements']} · "
    f"interventions {depart['interventions']} · mesures {depart['mesures']}"
)
"""
)

md(
    """
## 1. Ce que le jeu de données ne permet pas

Première règle de l'étape : **chiffrer l'incapacité avant toute fabrication**.
Une fois des lignes générées, la mesure du manque n'est plus possible.
"""
)

code(
    """
desequilibres = pd.DataFrame(capacite["desequilibres"])
display(
    desequilibres[
        ["variable", "modalites", "plus_representee", "effectif_max",
         "moins_representee", "effectif_min", "ratio"]
    ]
)
"""
)

md(
    """
Le rapport demandé par le brief est un **rapport d'effectifs**, distinct du
rapport de *taux* de couverture (×23 entre `critical` et `low`) établi au brief 1.
Les deux disent des choses différentes : le premier décrit le parc, le second
décrit ce qu'on a choisi d'observer.
"""
)

code(
    """
couverture_evt = capacite["couverture_evenements"]
print(
    f"événements documentés : {couverture_evt['evenements_documentes']} "
    f"/ {couverture_evt['evenements_total']}"
)
display(pd.DataFrame(couverture_evt["par_categorie"]))
display(pd.DataFrame(couverture_evt["test_independance"])[
    ["variable", "khi2", "p_value", "significatif_5pct"]
])
"""
)

md(
    """
La documentation des événements décroît quand la gravité augmente — 12,3 % pour
`critical` contre 21,1 % pour `low`. Le test du khi² ne rejette pas
l'indépendance : l'écart n'est pas distinguable du hasard sur ces effectifs. Il
est cité comme **tendance mesurée, pas comme fait établi** — et c'est le brief 1
qui porte le fait dur, lui non statistique : 6 des 8 mesures de vibration au-delà
de 5 mm/s ne sont appariées à aucun événement, dont le pic à 9,76.
"""
)

code(
    """
segmentation = capacite["segmentation"]
print("état 1 — parc entier :", segmentation["etat_1_parc_entier"]["conclusion"])
print()
etat2 = segmentation["etat_2_strate_puis_segments"]
print(
    f"état 2 — strate {etat2['strate_declaree']} ({etat2['equipements_strate']} équipements) "
    f"puis k = {etat2['k_retenu']} sur {etat2['equipements_segmentes']}, "
    f"silhouette {etat2['silhouette_retenue']}"
)
display(pd.DataFrame(segmentation["profil"]))
display(pd.DataFrame(segmentation["croisement_couverture"]))
"""
)

md(
    """
**Arbitrage A3** — la segmentation retient référentiel **et** activité, et
**exclut la couverture instrumentale des variables**. L'inclure aurait rendu la
conclusion tautologique : « ces groupes sont mal couverts » n'apprend rien si la
couverture a servi à les construire. Elle est croisée **après**, et c'est ce
croisement qui constitue le résultat : `SEG-2` réunit 174 équipements et 2
capteurs — 1,15 %.
"""
)

code(
    """
for figure in ("effectifs_parc.png", "distributions_activite.png",
               "choix_k.png", "segments_couverture.png"):
    display(Image(filename=str(OUT / "capacite" / "figures" / figure)))
"""
)

md(
    """
### Trois questions que ce jeu ne permet pas de traiter

| Question | Chiffre qui l'interdit |
|---|---|
| « Quels équipements de `SITE-OUEST` vont tomber en panne ? » | **0 capteur sur 16 équipements** — aucune mesure, aucune série, rien à apprendre |
| « Une presse ou une vanne montre-t-elle une signature avant défaillance ? » | **7 types sans aucune mesure**, dont `press` (34) et `valve` (21) — 90 équipements, 21,6 % du parc |
| « Quelle est la signature capteur d'un incident grave ? » | **9 événements `critical` documentés sur 73**, et le pic de vibration le plus élevé du corpus n'est apparié à aucun événement |

Le détail est dans `docs/capacite_jeu_donnees.md`.
"""
)

md(
    """
## 2. Augmenter — ce que chaque technique préserve et détruit

Cinq procédés appliqués à une série réelle. La colonne qui compte n'est pas ce
qu'ils préservent : c'est ce qu'ils **détruisent**.
"""
)

code(
    """
fiche = pd.read_csv(OUT / "augmentation" / "fiche_techniques.csv")
display(fiche)
display(pd.read_csv(OUT / "augmentation" / "mesures_par_technique.csv"))
display(Image(filename=str(OUT / "augmentation" / "figures" / "augmentation_series.png")))
display(Image(filename=str(OUT / "augmentation" / "figures" / "augmentation_distributions.png")))
"""
)

md(
    """
Le cas à retenir est `PROC-AUG-PERMUT` : la permutation détruit **intégralement**
la structure temporelle et rend des marginales identiques au réel. Sur un
histogramme, elle est indiscernable d'une série intacte. Une technique qui produit
une série physiquement impossible se documente, elle ne se supprime pas.
"""
)

md(
    """
## 3. Générer — deux voies, et ce que chacune perd

**Arbitrage A2** — périmètre généré : `SITE-OUEST ∩ SEG-2`, 8 équipements,
2 capteurs, janvier 2026. Il satisfait la consigne (`SITE-OUEST`) et vise le trou
chiffré à l'étape 1 (`SEG-2`, 1,15 % de couverture), avec une répartition de
criticité équilibrée — 2 `critical`, 2 `high`, 2 `medium`, 2 `low`.
"""
)

code(
    """
generation = charger("generation/generation.json")
print("périmètre :", generation["perimetre"]["arbitrage"])
print("équipements :", ", ".join(generation["perimetre"]["equipements"]))
print("volumes :", generation["volumes"])
print("voisinage :", {k: v for k, v in generation["voisinage"].items() if k != "journal_interpolation"})
print("journal :", generation["voisinage"]["journal_interpolation"])
"""
)

md(
    """
### Le traitement des colonnes catégorielles, écrit et non emprunté

Interpoler numériquement une catégorie encodée est le contresens que le critère
bloquant du brief vise. Ici, les colonnes numériques sont interpolées entre
voisins ; les colonnes catégorielles sont tranchées par **vote majoritaire** des
donneurs, jamais moyennées.
"""
)

code(
    """
import inspect

from src.brief2.generation import vote_majoritaire

print(inspect.getsource(vote_majoritaire))
"""
)

code(
    """
marginales = pd.DataFrame(generation["marginales"])
display(marginales[["origine", "sensor_name", "lignes", "moyenne", "ecart_type", "min", "max"]])

structure = pd.DataFrame(generation["structure_temporelle"])
display(structure)
"""
)

md(
    """
**C'est ici que tout se joue.** Le tirage marginal conserve chaque histogramme —
les moyennes et les écarts-types sont proches du réel — et **détruit
l'autocorrélation de rang 4**, c'est-à-dire le cycle de 24 h : elle passe de 0,80
à −0,02 sur la température. Une comparaison limitée aux marginales conclurait que
la série est fidèle. Elle ne l'est pas : elle a la bonne distribution et aucune
dynamique.

L'interpolation entre voisins, elle, conserve la dynamique (0,60 contre 0,80) et
paie ailleurs : **elle contracte la dispersion**. L'écart-type de la température
tombe à 3,85 contre 4,96 pour le réel, soit un ratio de 0,78. C'est le défaut qui
a motivé un second état du générateur.

> Les deux tableaux ci-dessus portent sur l'**état 1** du générateur
> (`PROC-GEN-SMOTE-V1`), seul existant à l'étape 3. L'état 2
> (`PROC-GEN-SMOTE-V2`, λ élargi à [−0,25 ; 1,25]) est produit à l'étape 4 en
> réponse à ce défaut : ratios σ 0,858 et 0,897 contre 0,783 et 0,810. C'est lui
> qui est transmis.
"""
)

code(
    """
display(pd.DataFrame(generation["correlation_entre_capteurs"]))
display(pd.DataFrame(generation["reaction_aux_evenements_controle_semestre"]))
"""
)

md(
    """
La réaction aux événements est testée **sur le semestre**, pas sur le mois généré.
Motif écrit avant le test : sur janvier seul, le réel lui-même ne montre aucune
réaction détectable (p = 0,18 et p = 0,97) alors qu'elle est franche sur le
semestre. Conclure « les fabriqués ne réagissent pas » à partir d'un test
incapable de voir la réaction du réel n'aurait rien démontré.
"""
)

code(
    """
controles = pd.DataFrame(generation["controles_metier"])
en_faute = controles[controles["lignes_en_faute"] > 0]
print(f"contrôles métier exécutés : {len(controles)}")
print(f"contrôles avec au moins une ligne en faute : {len(en_faute)}")
display(en_faute if len(en_faute) else controles.head(8))
"""
)

md(
    """
## 4. Se confronter — dans les deux sens

**Sens 1** : nos productions au détecteur de référence, chaque soumission
consignée avec son hypothèse formulée **avant** lancement.
**Sens 2** : nos règles sur le lot de contrôle, verdict par ligne.
"""
)

code(
    """
tour1 = charger("detection/detection_tour1.json")
tour2 = charger("detection/detection_tour2.json")

soumissions = pd.DataFrame(tour1["soumissions"] + tour2["soumissions"])
print(f"soumissions consignées aux tours 1 et 2 : {len(soumissions)}")
display(soumissions[["soumission", "fichier"]] if "fichier" in soumissions
        else soumissions.iloc[:, :2])
print()
print("générateur, état 2 :", tour2["generateur_v2"])
"""
)

md(
    """
### Le résultat central du tour 2

`PROC-GEN-SMOTE-V1` et `PROC-GEN-SMOTE-V2` reçoivent **le même verdict — zéro
signalement** — alors que le second est mesurablement meilleur : ratios σ 0,858 et
0,897 contre 0,783 et 0,810.

Le détecteur ne sait pas arbitrer entre deux états du générateur. **Son silence ne
prouve donc rien.** La preuve en est faite au tour 1 : `PROC-GEN-MARG-V1`, série
sans aucune structure temporelle, est déclarée conforme et *plus propre* que les
deux témoins réels. La question « générateur fidèle ou détecteur aveugle ? » se
tranche par un élément extérieur au détecteur — ici l'autocorrélation, qu'il
déclare lui-même hors de son périmètre.
"""
)

code(
    """
verdicts = charger("detection/verdicts.json")
print("calibrage sur control_sample.csv :",
      f"{verdicts['calibrage']['lignes_justes']} / {verdicts['calibrage']['lignes']} "
      f"({verdicts['calibrage']['part_juste']:.1%})")
print("répartition du lot :", verdicts["lot"]["repartition"])
print("blocs fabriqués sans signature interne :",
      verdicts["lot"]["blocs_fabriques_sans_signature"])
display(pd.DataFrame(verdicts["registre"]))
"""
)

md(
    """
**Arbitrage A5 — politique d'`indécidable`.** 30 lignes sur 6 000, soit un bloc :
un seuil strict, assumé et mesuré dans les deux sens. Le verdict se prend au bloc
de 30 lignes — unité de fabrication constatée — et une seule famille de règles
décide. Les cinq règles de corroboration n'ont jamais voix au chapitre : portées à
la décision, elles auraient déclaré fabriqués **21 blocs authentiques sur 127**.

C'est le piège que le lot tend : nos 15 règles capteurs du brief 1 détectent la
**qualité**, pas l'**authenticité**, et les lignes réelles du lot portent les
anomalies de la livraison M3.
"""
)

code(
    """
contre = pd.DataFrame(verdicts["contre_epreuve"])
display(contre)
"""
)

md(
    """
## 5. Protéger une publication agrégée

**Arbitrage A4** — agrégat retenu : le **coût moyen des pièces par site ×
criticité**, choisi sur les effectifs constatés à l'étape 1. Mécanisme de Laplace,
sensibilité bornée par un plafond, budget `ε` balayé sur huit valeurs.
"""
)

code(
    """
confidentialite = charger("confidentialite/confidentialite.json")
print("agrégat :", confidentialite["agregat"])
print("plafond retenu :", confidentialite["plafond_retenu"], "€ —",
      "comparé à", confidentialite["plafonds_compares"])
print("budgets testés :", confidentialite["epsilons"])

balayage = pd.DataFrame(confidentialite["balayage"])
exploitables = (
    balayage.assign(exploitable=balayage["part_conclusion_conservee"] > 0.90)
    .groupby("epsilon")["exploitable"].sum()
    .rename("cellules exploitables / 16")
)
attaque = pd.DataFrame(confidentialite["attaque"]).set_index("epsilon")
display(pd.concat([exploitables, attaque[["erreur_estimation_mediane", "part_cible_retrouvee"]]], axis=1))
display(Image(filename=str(OUT / "confidentialite" / "figures" / "budgets_epsilon.png")))
"""
)

md(
    """
### Les deux bornes, et une erreur corrigée en cours d'étape

**La sortie n'est pas le budget, c'est la maille.** À `ε = 5`, la publication par
criticité seule est exploitable sur ses 4 cellules quand la maille croisée en
laisse 5 sur 16 inutilisables. Protéger un agrégat trop peu fourni ne s'achète pas
en budget : on renonce à la finesse.

**L'erreur, et pourquoi elle comptait.** La première version mesurait la
protection par la part des tirages où la moyenne vraie était retrouvée à 10 % près
— et concluait que les grandes cellules étaient les moins protégées, ce qui est
faux. L'indicateur mesurait la **précision** et l'appelait vulnérabilité. Remplacé
par l'attaque par différenciation, conforme au modèle de menace annoncé, qui rend
le résultat théorique attendu : **la protection ne dépend pas de l'effectif**.
"""
)

md(
    """
## 6. Décider ce qui est transmis à M4
"""
)

code(
    """
transmission = charger("transmission/transmission.json")
print("décision :", transmission["decision"])
print("volumes :", transmission["volumes"])
print("échéance de réexamen :", transmission["echeance_reexamen"])
print("contrat de provenance respecté :", transmission["contrat"]["conforme"])
print("R-TRA-001, valeurs corrigées :", transmission["R-TRA-001_valeurs_corrigees"])

procedes = pd.DataFrame(transmission["procedes"])
display(procedes[["procedure_id", "famille", "provenance", "transmis", "lignes", "motif_transmission"]])
"""
)

code(
    """
couverture = pd.DataFrame(transmission["couverture"])
display(
    couverture[couverture["variable"] != "parc"]
    .pivot_table(index=["variable", "modalite"], columns="etat", values="taux_pct")
)
display(pd.DataFrame(transmission["documentation_par_gravite"]))
"""
)

md(
    """
**Le piège de l'atténuation par fabrication.** La couverture passe de 8,65 % à
10,58 % et le rapport `critical` / `low` de ×22,9 à ×8,7 **sans qu'un seul
équipement supplémentaire ait été instrumenté**. L'indicateur progresse, le parc
observé est identique. C'est ce constat qui a produit la condition C7 : ne jamais
compter la couverture sans filtrer sur la provenance.
"""
)

code(
    """
biais = pd.read_csv(OUT / "transmission" / "biais.csv")
for nom, groupe in biais.groupby("biais", sort=False):
    print(f"\\n{nom}")
    for _, ligne in groupe.iterrows():
        print(f"   {ligne['indicateur']:<58} {ligne['valeur']}")
"""
)

md(
    """
| Biais | La fabrication… | Effet net |
|---|---|---|
| B1 couverture | corrige **en apparence** | amplifie le risque de lecture |
| B2 étiquetage | corrige 3 événements sur 425 non documentés | négligeable au parc |
| B3 renseignement | ne touche pas | inchangé, et contamine les agrégats de l'étape 5 |
| B4 historique | ne touche pas | inchangé |
| B5 représentation | **amplifie** | un effectif apparent supérieur à l'effectif réel |

Deux biais sur cinq sont hors de portée de toute technique de fabrication, et le
seul qu'elle améliore vraiment est aussi celui où elle crée le plus grand risque
d'erreur de lecture. Le détail est dans `docs/biais_et_risques.md`.
"""
)

md(
    """
## Conclusion

### La décision

**Une partie sous conditions.** Le réel complet — 50 277 mesures — plus **1 799
mesures synthétiques** de `PROC-GEN-SMOTE-V2` sur 8 équipements de `SITE-OUEST`,
soit **3,45 %** du jeu transmis. Chaque ligne porte sa provenance et son procédé.

Sont écartés le tirage marginal (structure temporelle détruite), l'état 1 du
générateur (dispersion contractée de 15 à 22 %) et les cinq augmentations (série
support hors grille, 721 lignes signalées sur 721 **avant** toute augmentation).

Trois conditions s'ajoutent aux cinq du brief 1 : **C6** aucun usage du fabriqué en
évaluation, **C7** aucun comptage de couverture sans filtrer la provenance, **C8**
réexamen au plus tard le 31/12/2026.

### Ce que cette composition interdit de conclure

Rien sur `SITE-OUEST` qui ne soit une propriété de notre générateur ; rien sur la
réaction des capteurs aux 3 événements que la transmission rend « documentés » ;
aucune conclusion de forme « la couverture s'améliore » ; et **aucune preuve de
fidélité tirée du silence du détecteur**.

### Ce que ce brief a appris qui ne figurait pas au programme

La soumission du **livrable** — et non des cas de démonstration — a fait
apparaître 68 valeurs à plus de trois décimales, toutes réelles, produites par
notre propre conversion kelvin → °C au brief 1. Aucune des 34 règles ne contrôlait
la sortie de ses propres transformations. Un contrôle qui ne s'applique qu'aux
données reçues laisse un angle mort de la taille de tout ce qu'on produit
soi-même.
"""
)

md(
    """
### Les 17 questions du brief, et où se trouve la réponse

| # | Question | Réponse courte | Démonstration |
|---|---|---|---|
| 1 | Rapports de déséquilibre | ×11,4 sur le type d'équipement, ×10,8 sur le site, ×4,7 sur le type d'événement | étape 1 |
| 2 | Variables de segmentation, choix de `k`, groupes mal couverts | référentiel + activité, couverture **exclue** ; strate `SEG-INACTIF` puis `k = 2` ; `SEG-2` à 1,15 % | étape 1 |
| 3 | Trois questions impossibles | `SITE-OUEST` (0/16), `press`/`valve` (7 types sans mesure), signature d'incident grave (9/73) | étape 1 |
| 4 | Techniques d'augmentation, préservé / détruit | 5 procédés, fiche par procédé — la permutation détruit tout en gardant l'histogramme | étape 2 |
| 5 | Périmètre généré et pourquoi | `SITE-OUEST ∩ SEG-2`, 8 équipements, criticités équilibrées | étape 3 |
| 6 | Marginales conservées | les deux voies conservent moyennes et quantiles ; l'interpolation contracte σ de 10 à 14 % | étape 3 |
| 7 | Relation perdue par le tirage marginal | l'autocorrélation de rang 4 — le cycle de 24 h — et la corrélation entre capteurs | étape 3 |
| 8 | Lignes générées violant une règle M2/M3 | 0 sur 22 contrôles métier ; 0 hors plage physique | étape 3 |
| 9 | Colonnes catégorielles dans l'interpolation | vote majoritaire des donneurs, jamais de moyenne — code affiché | étape 3 |
| 10 | Ce que le détecteur a signalé, et ce qu'on a changé | 18 soumissions consignées avec hypothèse préalable ; corrections : λ élargi, contrat de colonnes, témoin systématique | étape 4, journal |
| 11 | Fidèle ou aveugle ? | **aveugle** — même zéro sur deux états inégaux ; tranché par l'autocorrélation, hors de son périmètre | étape 4 |
| 12 | Verdicts sur le lot | 3 810 `réelle`, 2 160 `fabriquée`, 30 `indécidable`, chacun rattaché à une règle `R-DET-*` | étape 4 |
| 13 | Fabrications visibles seulement en multi-source | les greffes de segments réels — `R-DET-014`, 32 blocs sur 72 | étape 4 |
| 14 | Règles inopérantes, règles accusant à tort | corroborations portées à la décision : **21 blocs authentiques sur 127** accusés | étape 4 |
| 15 | Agrégat non publiable, sensibilité, effet de `ε` | coût moyen des pièces par site × criticité, plafond 750 € ; sous `ε = 1` la maille croisée est inexploitable | étape 5 |
| 16 | Biais, résiduel, amplification | 5 biais chiffrés ; 2 hors de portée de toute fabrication ; B5 amplifié | étape 6 |
| 17 | Ce qui est transmis, avec quelle provenance | 96,55 % `réelle` + 3,45 % `synthétique` étiquetée, sous conditions C6–C8 | étape 6 |
"""
)

notebook = nbf.v4.new_notebook(cells=cells)
notebook.metadata = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {"name": "python", "version": "3.12.10"},
}
NOTEBOOK.parent.mkdir(parents=True, exist_ok=True)
nbf.write(notebook, str(NOTEBOOK))
print(f"écrit : {NOTEBOOK} ({len(cells)} cellules)")
