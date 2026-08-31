# Brief online M4 — Concevoir une IA simple pour un nouveau besoin

## Mission

Faire évoluer la conception de DiagOps pour un nouveau besoin, depuis l'analyse
métier jusqu'au choix argumenté d'un modèle, en couvrant explicitement C1, C2 et
C4 du programme CampusAtlas.

Le brief est autonome. Il n'exige pas d'avoir terminé le brief présentiel et ne
demande ni RAG, ni agent.

## Organisation

- 3 h en classe virtuelle : cadrage, revue du protocole et confrontation des
  choix ;
- 3 h de travail autonome : dossier de conception et recommandation finale.

## Travail attendu

### 1. Analyser le besoin

Décrivez les utilisateurs directs et indirects, la décision assistée, les
résultats attendus, les erreurs coûteuses, les contraintes de délai et les
conditions de supervision humaine.

### 2. Identifier les données nécessaires

- unité d'observation et cible ;
- sources disponibles et sources manquantes ;
- pertinence, cohérence et représentativité ;
- accès, droits et confidentialité ;
- volume minimal défendable ;
- biais et périmètre de validité.

### 3. Comparer des familles de modèles

Comparez au moins trois familles possibles : modèle à règles, modèle supervisé,
modèle non supervisé ou modèle pré-entraîné. Pour chacune, analysez données
requises, explicabilité, capacité de généralisation, coût, maintenance et
contraintes d'apprentissage.

### 4. Définir l'évaluation

Définissez métriques, jeux de calibration et de test, seuils d'acceptation,
analyse ROC lorsque la cible s'y prête, mesure par segment et conditions de
réévaluation.

### 5. Analyser les risques

Traitez impacts directs et indirects, données sensibles, biais, sécurité,
éco-conception et cadre réglementaire. Distinguez obligations établies,
interprétations et points nécessitant une validation juridique.

### 6. Recommander

Choisissez un modèle ou recommandez de rester sans modèle. Présentez les
preuves, limites, mesures d'atténuation et informations manquantes qui pourraient
changer la décision.

## Livrables

- `dossier_conception_m4.md` ;
- tableau des données nécessaires ;
- comparaison des familles de modèles ;
- protocole d'évaluation ;
- registre des risques ;
- décision finale datée ;
- entrée dans le journal de bord.

## Critères de réussite

- le besoin est formulé comme une décision observable ;
- les données sont reliées au besoin et non simplement inventoriées ;
- le modèle est choisi contre des alternatives ;
- les performances attendues sont mesurables ;
- les risques sont communiqués avec leurs atténuations et limites ;
- chaque choix est documenté de façon transmissible.
