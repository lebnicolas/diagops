# Brief 2 M7 — Exercer la réversibilité de l'architecture

**Durée : 20 h — 12 h de migration, 4 h de revue indépendante, 4 h de remédiation et défense**

## Situation

Le brief 1 a proposé une architecture cible, des ADR et une stratégie de
réversibilité. Une stratégie écrite ne prouve pas que les formats, contrats et
procédures permettent réellement de changer un composant.

## Mission

Migrer un sous-ensemble représentatif vers une alternative, mesurer les pertes,
subir une revue de sécurité et corriger l'architecture cible.

## Entrées

- architecture, ADR et matrice local/cloud/hybride du brief 1 ;
- sous-ensemble de corpus, index, scénarios et traces ;
- alternative qualifiée pour embeddings, index, générateur ou fournisseur ;
- grille de sécurité et portabilité commune.

Voir [DIFFUSION.md](DIFFUSION.md) et les gabarits `migration_exercise/`.
Le smoke test JSON → SQLite ne suffit pas comme livrable : choisir un
sous-ensemble justifié, écrire puis geler ses propres cas avant mesure, et
exercer au minimum une évolution de révision et une révocation de droits avec
reconstruction et rollback. Une autre alternative peut répondre au même
contrat. Aucun téléchargement de modèle ou compte cloud n'est imposé.

## Phase 1 — Migration individuelle, 12 h

### 1. Choisir le composant

Justifiez le composant migré par un risque réel : coût, disponibilité,
localisation, licence, verrou fournisseur, qualité ou fin de support.

### 2. Définir le contrat de sortie

Documentez formats exportés, métadonnées, checksums, versions, pertes connues et
critères de réussite. Aucun secret ou identifiant de production n'est utilisé.

### 3. Exécuter la migration

Reconstruisez le sous-ensemble avec l'alternative, adaptez le minimum de code et
conservez temps, opérations manuelles, erreurs et incompatibilités.

### 4. Comparer

Mesurez qualité, latence, ressources, coût, sécurité, observabilité et capacité
de rollback. Distinguez régression acceptable, blocage et dette reportée.

### 5. Rejouer le mode dégradé

Testez indisponibilité du composant remplacé, fallback, restauration et
cohérence des traces.

## Phase 2 — Revue indépendante, 4 h

Le reviewer challenge :

- frontières de confiance ;
- filtres d'accès avant retrieval ;
- export réellement portable ;
- dépendances cachées ;
- hypothèses de coût ;
- outil à effet simulé et approbation ;
- modes de panne non testés.

Il produit des constats classés `bloquant`, `majeur` ou `mineur` et documente
séparément leur disposition, dont une éventuelle acceptation motivée. Le reviewer
est une autre personne (apprenant ou formateur), et identifie exactement la
version revue et les commandes rejouées.

## Phase 3 — Remédiation et défense, 4 h

- traiter les constats bloquants et majeurs ;
- mettre à jour ADR et risques résiduels ;
- rejouer les tests affectés ;
- réviser le plan de migration et rollback ;
- défendre la cible, y compris les choix abandonnés.

## Livrables

- choix et contrat de migration ;
- export ou reconstruction du sous-ensemble ;
- journal d'exécution ;
- comparaison avant/après ;
- tests de mode dégradé ;
- rapport indépendant ;
- ADR et architecture cible révisés ;
- plan de migration et rollback corrigé ;
- support de défense.

Compléter `handoff_m8.md` avec les références des preuves, les décisions de
veille et les questions ouvertes. Cette remise ne crée pas une référence
commune M8 et n'autorise aucun effet externe.

## Critères de réussite

- la migration est exécutée sur un sous-ensemble représentatif ;
- les opérations manuelles sont comptées ;
- les pertes de format ou de qualité sont explicites ;
- le reviewer est indépendant de l'auteur ;
- un constat bloquant non résolu bloque la cible ;
- l'outil à effet reste simulé ;
- au moins une hypothèse est confirmée, révisée ou abandonnée par preuve.

## Gate renforcé M7

La réversibilité est exercée, la revue indépendante est traitée et
l'architecture cible reflète les résultats plutôt que l'intention initiale.
