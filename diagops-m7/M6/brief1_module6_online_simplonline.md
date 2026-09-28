# M6 - Brief 1 online - Améliorer un modèle avec de nouvelles données et du feedback

**Compétences visées**

- C5. Entraîner le modèle d'IA — **niveau 2, adapter**
- C8. Mesurer la performance et les impacts — **niveau 2, adapter**
- C9. Adopter une démarche d'amélioration continue — **niveau 2, adapter**

## Description

Une version en service vieillit : les données changent, les usages se déplacent, et les utilisateurs signalent ce qui ne va pas. Votre mission : analyser la version active, qualifier de nouvelles données et des retours humains, entraîner un candidat, mesurer ses effets puis décider de sa promotion dans une chaîne d'amélioration continue. Le brief est autonome et n'exige pas d'agent.

## Ressources

- Version active de référence : `data_pack/2026-S1/reference_runs/m5_for_m6/` — versions liées, métriques et gates
- `data_pack/2027-S1/reports/` — période postérieure, support de l'analyse de dérive
- `data_pack/2027-S1/feedback/` — retours humains bruts, lot `b1`
- `data_pack/2026-S1/annotations/` et `model_eval/` — jeux d'entraînement et d'évaluation existants
- `M6/starter/feedback/qualify_feedback.py` — qualification outillée des retours
- `M6/RESOURCES.md` — ressources techniques du module

## Contexte du projet

Ce brief couvre le programme officiel CampusAtlas du module 6 : exploiter de nouvelles données et du feedback pour entraîner ou adapter un modèle, reprendre les métriques, analyser la dérive et intégrer la validation à la chaîne MLOps.

La période `2027-S1` est volontairement décalée : nouveau canal de saisie, notes plus courtes, part plus élevée de rapports sans équipement identifié, mélange d'équipements déplacé. Cet écart se mesure ; il ne se corrige pas en retirant les lignes gênantes. Les données synthétiques et augmentées déjà traitées en M3 sont auditées par provenance, elles ne sont pas recréées pour remplir artificiellement le module.

Un feedback n'est pas une vérité terrain : le lot livré contient des doublons, des retours rattachés à des rapports inexistants, des notes hors échelle, des données personnelles et des tentatives d'instruction adressées au système. Aucun n'est signalé comme tel.

## Modalités pédagogiques

Travail individuel. Durée estimée : 6 heures — 3 h en classe virtuelle sur la dérive, l'hypothèse d'amélioration et le protocole, puis 3 h en autonomie pour le candidat, l'évaluation et la décision.

Phases de travail :

1. Reprendre la référence : identifier version, données, métriques, limites, seuils et environnement de la version active. Aucun progrès ne peut être affirmé sans référence comparable.
2. Qualifier les nouvelles données : qualité, distribution, couverture, biais, doublons et lien avec la cible ; distinguer données réelles, synthétiques et augmentées selon leur provenance ; qualifier séparément les feedbacks humains.
3. Formuler une hypothèse : une seule modification à la fois — données, feature engineering, hyperparamètre, modèle ou seuil — en expliquant le mécanisme attendu et les segments susceptibles de régresser.
4. Entraîner le candidat : versionner la référence, exécuter l'entraînement de façon reproductible, conserver configurations, métriques, artefacts et journal.
5. Évaluer : comparer précision, rappel, F1, erreurs, stabilité par segment, ressources et impacts, en utilisant validation et test sans réutiliser le test pour régler le candidat.
6. Décider et intégrer : promouvoir, rejeter ou prolonger ; une promotion passe par la chaîne M5, avec préproduction, gate et rollback disponible.

## Modalités d'évaluation

Le brief online compte pour 30 % du module. L'évaluation porte sur la rigueur du protocole d'amélioration et sur le contrôle de la promotion, pas sur le gain obtenu.

Le formateur vérifie :
- La référence est explicite et comparable.
- Les feedbacks ne sont pas assimilés automatiquement à des labels.
- Une seule hypothèse principale est testée.
- Les jeux restent séparés, le test ne sert pas au réglage.
- Les régressions par segment sont recherchées, pas seulement la moyenne.
- La décision est reliée aux exigences initiales.
- La promotion reste contrôlée, avec gate et rollback disponibles.

## Livrables

- Rapport de dérive.
- Qualification des nouvelles données et des feedbacks, traitées séparément.
- Hypothèse et protocole.
- Configuration et résultats du candidat.
- Comparaison segmentée avec la référence.
- Tableau de bord mis à jour.
- Décision et plan de déploiement.
- Journal de bord.

## Critères de performance

- La référence est explicite.
- Les feedbacks ne sont pas assimilés automatiquement à des labels.
- Une seule hypothèse principale est testée.
- Les jeux restent séparés.
- Les régressions par segment sont recherchées.
- La décision est reliée aux exigences initiales.
- La promotion reste contrôlée.
