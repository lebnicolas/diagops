# Brief présentiel M7 — Évaluer l'architecture RAG-agentique

## Situation

DiagOps est déployé, observé et doté d'outils de lecture. L'ajout d'un nouvel
outil ou fournisseur peut pourtant déplacer les données, augmenter les coûts,
affaiblir les permissions ou rendre le système impossible à remplacer. L'équipe
demande une revue d'architecture avant toute autonomie supplémentaire.

## Mission

Produire une évaluation contradictoire de l'architecture actuelle et une cible
réversible, puis démontrer sur des tests les principaux modes d'échec.

## Point de départ commun

**14 h, dont environ 1 h de veille.** Voir [DIFFUSION.md](DIFFUSION.md)
pour le séquençage et la grille commune.

- `data_pack/2026-S1/reference_runs/m6_for_m7/` ;
- inventaire des versions, outils, métriques et incidents ;
- politiques et threat models M4-M6 ;
- corpus image uniquement s'il est qualifié et utile à une hypothèse explicite.

La référence `diagops-m6-reference-r1` fige le starter M6 et ses échecs connus ;
elle ne représente pas une solution M6 validée. Lire son README et ses traces.
Un travail M6 personnel peut la remplacer si versions, données et mesures sont
figées. Initialiser `python tools/init_module.py M7` depuis S04, puis suivre
`work/M7/README.md`. Aucun corpus image, GPU ou service payant n'est requis.

## Travail attendu

### 1. Cartographier l'existant

Représentez composants, acteurs, données, flux, réseaux, stockages, modèles,
outils, secrets, traces et fournisseurs. Marquez les frontières de confiance et
les points où un contenu non fiable entre dans le système.

### 2. Évaluer par scénarios

Testez au minimum :

- index ou modèle indisponible ;
- fournisseur distant inaccessible ;
- corpus partiellement obsolète ;
- montée en charge et budget épuisé ;
- outil lent ou incohérent ;
- compromission d'un document ;
- demande sans droit d'accès ;
- perte ou corruption d'un index.

Pour chaque scénario, consignez impact, détection, réponse, reprise et preuve.
Injectez les pannes dans les copies locales des composants présents. Pour un
composant absent, notamment un fournisseur distant, réalisez une simulation sur
table et indiquez explicitement ce qui reste non testé. La corruption d'index,
son refus et le rollback doivent être réellement exécutés.

### 3. Définir la politique de données

Reliez chaque type de donnée à : propriétaire, sensibilité, finalité, lieu de
stockage, chiffrement, accès, rétention, suppression, sauvegarde et audit.
Définissez les filtres de retrieval avant génération, pas après exposition.

### 4. Comparer les architectures

Comparez local, cloud et hybride pour : génération, embeddings, index, API,
traces et sauvegardes. Analysez performance, coût, empreinte, compétences,
disponibilité, localisation, verrou fournisseur et réversibilité.

### 5. Tester la portabilité

Exportez ou reconstruisez un sous-ensemble avec une alternative : modèle
d'embeddings, index, générateur ou fournisseur. Comparez qualité, temps de
migration, formats perdus et adaptations nécessaires.

Le starter propose un premier passage JSON → SQLite sans téléchargement. Il
conserve le score lexical et les ACL ; analyser sa portée puis provoquer et
corriger une incompatibilité sur une copie. Ne pas confondre parité du
classement et qualité des réponses d'un modèle génératif.

### 6. Conduire une red team

Couvrez : injection directe et indirecte, empoisonnement du corpus, document
prioritaire malveillant, fuite inter-périmètre, arguments d'outils manipulés,
extraction de données, boucle coûteuse et déni de service.

Conservez résultats, limites du test et risque résiduel. Une absence d'échec
n'est pas une preuve d'absence de vulnérabilité.

### 7. Spécifier un outil à effet simulé

Choisissez une action fictive, par exemple créer une demande d'inspection dans
un bac à sable. Le contrat exige : aperçu avant action, approbation humaine,
idempotency key, contrôle d'autorisation, journal, annulation ou compensation.

L'outil ne contacte aucun système réel et n'entre pas dans le chemin de
référence sans une décision ultérieure.
Le starter fournit un contrat non exécutable et un exercice sur table couvrant
refus, expiration, changement après approbation, rejeu et compensation.

### 8. Proposer l'architecture cible

Produisez diagrammes, ADR, objectifs de reprise, politique de permissions,
mode dégradé, plan de migration par étapes, critères d'acceptation et rollback.

### 9. Exécuter le checkpoint réglementaire M7

Confrontez l'architecture cible aux sources officielles datées :

- réévaluez les rôles, responsabilités, transferts, fournisseurs, dépendances,
  exigences de cybersécurité, supervision et traçabilité ;
- vérifiez si l'outil à effet simulé ou une option local/cloud/hybride modifie
  la qualification ou le niveau de risque envisagé ;
- ajoutez une entrée M7 au journal de veille et traduisez la décision dans les
  ADR, le registre des risques ou le plan de migration ;
- transmettez à M8 les questions ouvertes avec responsable et échéance.

Ce checkpoint représente environ 1 h incluse dans les 14 h du présentiel.

## Livrables

- `architecture/current.md` ;
- diagramme de flux et frontières de confiance ;
- registre des données et dépendances ;
- matrice local/cloud/hybride ;
- rapport de portabilité ;
- rapport red team ;
- contrat d'outil à effet simulé ;
- `architecture/target.md` et `architecture/adr/` ;
- plan de migration et rollback ;
- entrée M7 et passage de relais dans `veille_diagops/` ;
- journal de bord.

Utiliser les gabarits `security/`, `portability/`, `resilience/` et
`simulated_action/` pour les autres pièces ; joindre les rapports réellement
produits et leurs commandes de reproduction.

## Critères de réussite

- les flux couvrent corpus, index, prompts, outils, feedback et traces ;
- les droits sont appliqués avant retrieval ;
- au moins une alternative est exercée, pas seulement citée ;
- les pannes des composants présents produisent des résultats observés ; les
  simulations sur table et les conditions non testées sont identifiées ;
- l'outil à effet reste simulé et soumis à approbation ;
- les risques résiduels peuvent bloquer la migration ;
- la décision réglementaire M7 est reflétée dans les ADR ou son absence
  d'impact est justifiée ;
- la cible est réversible par construction.

## Hors périmètre

- connexion à un système métier réel ;
- action sans approbation ;
- architecture multi-agent imposée ;
- ajout d'une modalité image sans besoin et corpus qualifiés.
