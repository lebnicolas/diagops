# Hypothèse figée avant la soumission T3-00 — 31/08/2026

Fichier soumis : `work/M3/output/transmission/sensor_readings_m4.csv`
(52 076 lignes — 50 277 `réelle`, 1 799 `synthétique` `PROC-GEN-SMOTE-V2`).

Ce document est écrit **avant** le lancement de `tools/verify_synthetic.py`.

## Ce que j'attends

**Volet contrat — aucun manquement.** `provenance` et `procedure_id` sont
présentes sur toutes les lignes, `row_identifier` a été retirée à la composition
(elle avait été signalée comme colonne inattendue en T1-04). J'attends zéro
signalement de structure de colonnes.

**Volet R-FORMAT — environ 725 lignes, soit 1,4 %.** Le défaut de grille de notre
préparation est connu et chiffré au brief 1 : 720 horodatages hors grille horaire
et 5 lignes hors période, sur les 50 277 mesures réelles. Les 1 799 lignes
synthétiques sont posées sur une grille de 6 h exacte et ne doivent rien ajouter.
La proportion attendue est donc franchement **inférieure** aux 3,04 % du témoin
T1-01, qui portait sur un sous-ensemble de janvier où ces 720 lignes pèsent
beaucoup plus lourd, et inférieure aux 6,24 % de la livraison publiée (T1-00).

**Volet R-DISTRIB — conforme.** La part fabriquée est de 3,45 % du jeu. Même avec
une dispersion contractée de 10 à 14 % sur les deux capteurs concernés, l'effet
sur les marginales globales est de l'ordre du centième d'écart-type : très en
dessous du seuil de 0,8 σ.

**Volet R-FK / R-KEY — zéro.** Les 8 équipements générés existent au référentiel,
et les clés logiques ont été contrôlées à la génération (`controles_metier`,
0 ligne en faute).

## Ce que le résultat ne prouvera pas

Un taux bas ne dira **pas** que les 1 799 lignes fabriquées sont fidèles. Le
détecteur a déjà rendu zéro sur deux états successifs du générateur dont l'un
était mesurablement moins bon (T2-01) : il ne sait pas arbitrer. Cette soumission
vérifie la **conformité de la transmission**, pas l'authenticité de son contenu.
Présenter son résultat comme une preuve de fidélité serait exactement le critère
bloquant que le brief nomme.

---

# Hypothèse figée avant la soumission T3-01 — 31/08/2026

Fichier soumis : le même jeu, après application de `R-TRA-001` (68 valeurs
ramenées à 2 décimales).

**R-PRECISION passe à 0.** Les 68 signalements du tour précédent venaient tous de
lignes `réelle`, sur `EQ-SENSOR-305` : la conversion kelvin → °C de `R-SEN-006`
écrivait `56.85000000000002`. L'arrondi à la convention de la livraison doit les
faire disparaître intégralement.

**Tout le reste est inchangé.** R-FORMAT reste à 725, R-RANGE à 52 — ces 52 sont
40 valeurs vides à la livraison plus 12 sentinelles `-999` que notre pipeline
neutralise volontairement au brief 1 ; les neutraliser est le comportement voulu,
et le détecteur les compte comme absentes. R-DISTRIB reste conforme : arrondir au
centième ne déplace aucune marginale.

Si un autre compteur bouge, c'est que l'arrondi a touché autre chose que la
précision d'écriture — et il faudra le chercher.
