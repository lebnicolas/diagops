# ADR-0002 — Le rôle vient d'une identité authentifiée

- Statut : **proposé** ; bloquant pour toute mise en service à plus d'un rôle
- Date / auteur / reviewer : 28/09/2026 / Nicolas (rédaction assistée) / à désigner
- Constat et preuve reproductible : le rôle est lu dans `policy.yaml` (un rôle
  par processus) ou passé en argument (banc, action simulée). Aucun composant
  ne l'authentifie. RT-05 montre que les droits tiennent **pour le rôle
  déclaré**, ce qui ne dit rien de qui le déclare. L'exercice sur table de
  l'action simulée a la même faiblesse : `sup-B` est un argument.
- Contraintes et hypothèses : l'organisation dispose d'un fournisseur
  d'identité (hypothèse, non vérifiée) ; aucune donnée personnelle
  supplémentaire ne doit entrer dans les traces.
- Options :
  1. **maintenir** : un processus par rôle, rôle fixé par la politique ;
  2. clé d'API par rôle, partagée entre les utilisateurs ;
  3. jeton OIDC émis par le fournisseur d'identité de l'organisation, rôle
     dérivé d'un groupe.
- Mesures séparées des estimations : rien n'est mesuré, aucune option n'est
  implémentée. C'est une décision de conception.
- Choix et options écartées : **option 3**. L'option 2 ne distingue pas deux
  utilisateurs d'un même rôle : pas de journal d'accès exploitable, pas de
  séparation demandeur/approbateur pour l'outil à effet. L'option 1 reste le
  mode de fonctionnement **tant qu'un seul rôle est servi**.
- Impacts :
  - données : naissance d'un **journal d'accès**, avec une conservation de six
    mois à un an (recommandation CNIL, veille D3 point 5) ; l'identifiant
    utilisateur n'entre pas dans les traces d'agent, qui restent minimisées ;
  - sécurité : le rôle n'est plus une déclaration. La révocation d'un
    utilisateur passe par le fournisseur d'identité ;
  - souveraineté : dépendance au fournisseur d'identité de l'organisation, pas
    à un tiers ;
  - exploitation : l'API refuse toute requête sans jeton valide ; aucun rôle
    par défaut.
- Gate, rollback et condition de révision : gate = test d'API sans jeton → 401,
  jeton `public` → 0 document interne (11 sondes). Rollback = retour à un
  processus mono-rôle. Révision si l'organisation n'a pas de fournisseur
  d'identité (Q2 de la veille : exploitant non connu).
- Changement après contradiction indépendante : à remplir.
