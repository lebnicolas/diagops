# ADR-0004 — Un document altéré est mis en quarantaine, pas le corpus

- Statut : **proposé**
- Date / auteur / reviewer : 28/09/2026 / Nicolas (rédaction assistée) / à désigner
- Constat et preuve reproductible : RES-06. Une ligne ajoutée à
  `DOC-CHILL-TEMP-001` fait lever `ToolError` au chargement du corpus. **Toute**
  la recherche documentaire tombe : 6 scénarios touchés, et l'export du banc est
  refusé en bloc. Le contrôle est fermé, mais à la maille du corpus : un seul
  fichier altéré suffit à provoquer un déni de service (RT-09).
- Contraintes et hypothèses : un document altéré ne doit jamais être servi ;
  les autres documents restent valides, puisque leur empreinte est vérifiée
  séparément.
- Options :
  1. **maintenir** : refus global ;
  2. **quarantaine au document** : le document fautif est exclu, une alerte est
     émise, les réponses signalent que le corpus est incomplet ;
  3. servir le document avec un avertissement.
- Mesures séparées des estimations : impact du refus global mesuré (14/18,
  contre 15/18 nominal, 6 scénarios documentaires). L'impact de la quarantaine
  n'est pas mesuré : il le sera au brief 2 (cas gelé « document altéré »).
- Choix et options écartées : **option 2**. L'option 3 sert un contenu dont on
  sait qu'il n'est pas celui qui a été relu.
- Impacts :
  - sécurité : un attaquant qui altère un fichier ne coupe plus le service ; il
    retire seulement ce document, et l'alerte le signale ;
  - qualité : une question dont la réponse est dans le document en quarantaine
    reçoit un refus ou une réponse partielle **signalée comme telle** ;
  - exploitation : nouvelle alerte ; procédure de reprise
    (`resilience/recovery.md`, étape 5).
- Gate, rollback et condition de révision : gate = le document altéré n'est
  jamais renvoyé, les autres le sont, et l'alerte est tracée. Rollback = refus
  global (option 1), plus sûr, moins disponible. Révision : si plus d'un tiers
  du corpus est en quarantaine, le refus global redevient la bonne réponse,
  car le corpus n'est plus représentatif.
- Changement après contradiction indépendante : à remplir.
