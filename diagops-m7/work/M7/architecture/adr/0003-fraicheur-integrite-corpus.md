# ADR-0003 — Fraîcheur et légitimité du corpus : l'index connaît son manifeste

- Statut : **proposé** ; bloquant pour la migration d'index (R-11, R-12)
- Date / auteur / reviewer : 28/09/2026 / Nicolas (rédaction assistée) / à désigner
- Constat et preuve reproductible :
  - RES-07 : un rôle retiré du manifeste reste effectif tant que le processus
    tourne (caches `lru_cache`), et un index déjà construit sert le document
    avec les droits d'avant ;
  - RES-03 : deux révisions actives d'une même procédure sont servies ensemble,
    l'export les accepte, l'index construit avant la mise à jour sert l'état
    antérieur sans signal ;
  - RT-03 : une révision empoisonnée avec un checksum juste est servie. Le
    checksum prouve l'intégrité du fichier, pas la légitimité de son auteur.
- Contraintes et hypothèses : le manifeste reste la source de vérité ; aucune
  infrastructure de signature n'existe.
- Options :
  1. **maintenir** : checksum par document, index sans lien avec le manifeste ;
  2. rechargement périodique des caches et reconstruction planifiée ;
  3. **empreinte du manifeste enregistrée dans l'index, comparée à chaque
     chargement ; index périmé refusé ; reconstruction déclenchée par le
     changement** ; plus deux règles d'admission ;
  4. signature cryptographique du manifeste.
- Mesures séparées des estimations : reconstruction complète mesurée à 12 ms
  (7 documents) et 0,6 s (7 000, FTS5 par rôle). Délai de révocation actuel :
  **indéfini**. Délai cible : le temps d'une reconstruction.
- Choix : **option 3**, avec deux règles d'admission à l'export :
  - **une seule révision active** par chaîne `supersedes_document_id`, sinon
    refus ;
  - un document qui en remplace un autre exige que l'ancien soit `superseded`
    dans le **même** changement de manifeste.

  Et une règle d'organisation : tout changement de manifeste passe par une
  **revue à deux personnes** (auteur ≠ relecteur), tracée dans Git.
- Options écartées : 2, parce qu'une révocation qui attend le prochain passage
  planifié laisse une fenêtre d'exposition connue de tous ; 4, parce que signer
  ne sert à rien si le signataire est l'auteur malveillant, et que la revue à
  deux personnes couvre le même risque sans infrastructure de clés.
- Impacts :
  - données : `metadata` de l'index gagne `manifest_sha256` ; `active.json`
    aussi ;
  - sécurité : ferme R-11 et R-12 ; **réduit** R-01 sans le fermer (deux
    relecteurs peuvent se tromper ensemble) ;
  - exploitation : un changement de manifeste coupe le service documentaire le
    temps d'une reconstruction, en mode dégradé explicite ;
  - souveraineté : aucune.
- Gate, rollback et condition de révision : gate = le cas « révocation » et le
  cas « nouvelle révision » gelés du brief 2 passent (refus de l'index périmé,
  puis reconstruction, puis document retiré ou révision unique). Rollback =
  l'index antérieur reste disponible, mais **n'est pas servi** s'il est périmé
  par une révocation : un rollback ne doit pas rétablir un droit retiré.
  Révision si les reconstructions deviennent assez longues pour que la coupure
  gêne (au-delà du RTO de 15 min).
- Résultat de la migration exercée (brief 2, phase 1) : M-REV-A (export
  refusé), M-REV-B (index périmé refusé, puis révision unique servie) et
  M-REVOC (index périmé refusé, droit retiré, retour arrière vers l'index
  d'avant refusé) sont conformes. **Écart à l'ADR** : la reconstruction n'est
  pas déclenchée par le changement, elle reste manuelle (D-2). Entre le
  changement et la reconstruction, le service documentaire refuse. C'est le
  comportement sûr, mais pas encore le comportement visé.
- Changement après contradiction indépendante : à remplir.
