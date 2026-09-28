---
module: M7
brief: brief 1 — online
maj: 2026-09-28
---

# Journal des décisions — brief online M7

Les décisions marquées **à valider** ont été prises par l'agent de rédaction à
la place de Nicolas ; elles restent ouvertes à sa relecture.

| # | Date | Décision | Raison | Preuve | Statut |
|---|---|---|---|---|---|
| D-01 | 28/09/2026 | Cas évalué : le modèle de provenance M4, seul | décision prise en amont ; objet mesurable localement, sans RAG ni agent | consigne du brief ; `diagops-m4/work/M4/docs/model_card.md` | prise par Nicolas |
| D-02 | 28/09/2026 | Réutiliser le venv M4 au lieu d'en créer un | versions identiques au gel (Python 3.12.10, numpy 2.3.2, pandas 2.3.1, scikit-learn 1.7.1) ; aucune installation réseau nécessaire | `results/mesures.json` → `environnement` | à valider |
| D-03 | 28/09/2026 | Importer le code M4 en lecture seule depuis son dossier (changement de répertoire courant, bytecode désactivé) plutôt que le copier | le code M4 résout le data pack en chemin relatif ; une copie aurait créé une deuxième version du code | `non_modification_m4.identique_avant_apres = true` sur 95 fichiers | à valider |
| D-04 | 28/09/2026 | Relire le test scellé, sans étiquette, pour mesurer la latence et le traitement par segment | le gel du 31/08 a déjà autorisé sa lecture ; le fichier ne porte pas de colonne `provenance` ; aucune métrique de qualité n'y est calculée | `integrite_entrees`, `reproductibilite` | à valider |
| D-05 | 28/09/2026 | Figer axes, protocoles et répétitions dans `mesures.py` avant la première exécution ; chiffrer les critères d'acceptation avec le dossier | les critères s'appuient sur des références extérieures (gel, volume du parc) ; mais ils ont été écrits après avoir vu les premiers chiffres — limite déclarée | `dossier.md` §3.2 et §14 | limite assumée |
| D-06 | 28/09/2026 | Mesurer la latence à trois niveaux (unitaire, lot, bout en bout) | la prédiction seule (0,09 ms) masquait la préparation (1,5 ms), qui fait l'essentiel du temps | `inference` | prise |
| D-07 | 28/09/2026 | Ajouter une injection de pannes non demandée explicitement | le M4 n'avait jamais soumis d'entrée invalide au modèle ; la grille note les modes dégradés | `modes_de_panne` : 6 prédictions silencieuses sur 9 | prise |
| D-08 | 28/09/2026 | Corriger le cas « valeur extrême » de l'injection après une première exécution | l'alerte pandas relevée venait du montage du test (chaîne écrite dans une colonne numérique), pas du code M4 ; la conserver aurait compté une fausse détection | exécution de 06:08:06 contre exécution de 06:08:48 | prise |
| D-09 | 28/09/2026 | Énergie : borne haute temps CPU × 115 W, sourcée, plutôt qu'une valeur typique | aucune mesure physique possible ; seule la puissance maximale du constructeur est une source vérifiable | Intel ARK i7-13620H, consulté le 28/09/2026 | à valider |
| D-10 | 28/09/2026 | Coût : un seul tarif cité (Scaleway DEV1-S, 0,00898 €/h HT) | besoin d'un ordre de grandeur pour l'alternative E2, pas d'un comparatif fournisseurs | page tarifaire consultée le 28/09/2026, lue par extraction automatique | à valider — à revérifier |
| D-11 | 28/09/2026 | Exécuter deux alternatives (JSON, SQLite) au lieu de les décrire | réalisables localement sans réseau ; transforment deux lignes de la matrice en preuves | `alternative_packaging_json` (60/60), `alternative_stockage_sqlite` | prise |
| D-12 | 28/09/2026 | Proposer une rétention de 180 jours pour le journal | valeur de travail pour exercer la purge ; aucune source ne la fixe | aucune — **arbitraire** | à valider avec DPO et métier |
| D-13 | 28/09/2026 | Maintenir la décision M4 `évaluer davantage` | l'oracle n'a pas été restitué ; rien de ce qui a été mesuré ne change la qualité connue | recherche dans `diagops-m4` à `diagops-m7` ; `qualite.oracle_test` | à valider |
| D-14 | 28/09/2026 | Cible retenue : contrat d'entrée + JSON + journal SQLite + batch sur serveur interne ; E2 (cloud) et E3 (API) écartées | E3 sans besoin (109 fenêtres/jour) ; E2 inutile tant que les données réelles ne sont pas qualifiées | `dossier.md` §8 | à valider |
| D-15 | 28/09/2026 | Priorité 1 au contrat d'entrée, avant tout le reste sauf l'oracle | constat le plus grave et indépendant du verdict de l'oracle ; profite aussi à la baseline | `modes_de_panne` | à valider |
| D-16 | 28/09/2026 | Ne pas corriger les pannes dans le modèle (pas de nouveau gel) | ajouter du signal sur les valeurs manquantes exigerait des fenêtres incomplètes en calibration, absentes du lot ; un nouveau gel invaliderait la comparaison à l'oracle | coefficient de `part_manquantes` = 0,0 (`explicabilite`) ; règle de changement M4 | à valider |
| D-17 | 28/09/2026 | Classer le système hors haut risque AI Act, sous réserve | usage interne de tri de données, hors annexe III ; texte consolidé non lu, comme au M6 | `diagops-m6/work/M6/veille_diagops/journal.md` | à valider par le juridique |

## Échecs et corrections rencontrés

| Moment | Ce qui s'est passé | Traitement |
|---|---|---|
| recherche de la puissance du processeur | la première page Intel consultée (identifiant de produit deviné) décrivait un autre processeur (i9-13950HX) | recherche sur intel.com, bonne fiche (232130) relue ; valeur retenue : 115 W |
| première exécution complète | alerte pandas comptée à tort dans le cas « valeur extrême » | montage du test corrigé (D-08), exécution refaite |
| mesure du temps CPU de la prédiction seule | résolution de `process_time` sous Windows à 15,6 ms : valeur arrondie à ±17 % | limite écrite au dossier §4.4 ; l'estimation d'énergie s'appuie sur le bout en bout, peu affecté |
| latence | trois exécutions complètes donnent un p95 de bout en bout de 1,81, 1,95 et 2,09 ms | valeurs de la dernière exécution retenues, variation rapportée |
