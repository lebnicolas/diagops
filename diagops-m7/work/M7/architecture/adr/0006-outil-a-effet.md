# ADR-0006 — L'outil à effet reste fictif et hors du chemin de référence

- Statut : **accepté pour le M7** (décision conservatoire, réversible)
- Date / auteur / reviewer : 28/09/2026 / Nicolas (rédaction assistée) / à désigner
- Constat et preuve reproductible : contrat `simulated_action/contract.json`
  (`executable: false`, `network_client: null`, `registered_in_agent: false`) ;
  exercice sur table automatisé, avec 11 séquences conformes
  (`results/action-simulee-r1`, `tests/test_simulated_action.py`). Deux limites
  prouvées : l'identité de l'approbateur est un argument, et le registre
  d'idempotence est en mémoire.
- Contraintes et hypothèses (veille D2, D4) : connecter l'outil à un système
  réel est **une requalification**, pas une évolution. Une demande d'inspection
  omise ou erronée pose la question de l'art. 6(1 ter) de l'AI Act (Q4). Les
  exigences de l'art. 14(4) b), d), e) servent de référentiel de conception.
- Options : 1. **maintenir** fictif ; 2. bac à sable avec un faux système aval
  persistant ; 3. connexion à une GMAO réelle.
- Mesures séparées des estimations : seul l'exercice sur table est mesuré.
- Choix : **option 1**. Le contrat est complété de trois exigences pour toute
  sortie future du bac à sable (veille D4) :
  - **mesure du biais d'automatisation** : taux d'approbation, délai entre
    aperçu et approbation, part des aperçus modifiés ou rejetés. Une
    approbation plus rapide que la lecture de l'aperçu est un signal ;
  - **approbateur authentifié et habilité** au moment de l'approbation
    (ADR-0002) ;
  - **interrupteur global** qui refuse toute nouvelle approbation et laisse
    expirer les approbations en attente.
- Options écartées : 2 et 3 tant que R-02 (identité) et R-05 (aucun refus
  délibéré d'une intention d'écriture) sont ouverts.
- Impacts : aucun sur l'exploitation actuelle. Le journal d'approbation, dès
  qu'il existe, suit la plus longue des durées applicables (veille D3
  point 4).
- Gate, rollback et condition de révision : un test vérifie que le contrat
  reste non exécutable et absent du registre. Toute proposition de passer
  `executable` à `true` rouvre la qualification (R-REG-01). Révision sur
  décision humaine documentée, après la réponse à Q4.
- Changement après contradiction indépendante : à remplir.
