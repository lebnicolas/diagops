# ADR-0001 — Index de retrieval : FTS5, un index par périmètre de droits

- Statut : **proposé**, à confirmer par la migration du brief 2 et la revue indépendante
- Date / auteur / reviewer : 28/09/2026 / Nicolas (rédaction assistée) / **à désigner**
- Constat et preuve reproductible :
  - le backend JSON relit et revérifie tout l'export à chaque requête. Coût
    linéaire : p50 0,38 ms à 7 documents, 27 ms à 700, **297 ms à 7 000**
    (`scripts/capacity_scale.py`, `results/capacite-r1`) ;
  - la migration de stockage du starter (JSON → SQLite lexical) **ne change pas
    ce coût** : 329 ms à 7 000 documents, puisque le score reste calculé en
    Python sur toutes les lignes du rôle ;
  - FTS5 : **21 ms** à 7 000 documents ;
  - dans un index FTS5 **partagé**, le document restreint modifie les scores
    visibles d'un technicien (10/10) et son classement (2/10). Dans un index
    **par rôle**, aucun effet (`results/portabilite-fts5-r1`).
- Contraintes et hypothèses : aucune dépendance ni téléchargement ; droits
  appliqués avant le calcul du classement, statistiques comprises ; corpus
  actuel de 7 documents, croissance non connue (le kit n'en dit rien).
- Options :
  1. **maintenir** le lexical JSON (existant) ;
  2. SQLite lexical (migration du starter) ;
  3. FTS5, index partagé filtré par rôle ;
  4. **FTS5, une table par rôle** ;
  5. index vectoriel (embeddings).
- Mesures séparées des estimations : toutes les valeurs ci-dessus sont
  **mesurées** sur un poste de développement, en un seul processus. La
  croissance du corpus est **inconnue**. L'option 5 n'est **pas mesurée** :
  embeddings `nomic` cassés sur ce poste, aucune API.
- Choix et options écartées : **option 4**.
  - 1 : correct et sans canal auxiliaire (score sans statistiques de corpus),
    mais coût linéaire ; acceptable tant que le corpus reste sous quelques
    centaines de documents ;
  - 2 : même coût que 1, plus une copie à maintenir. Écartée : elle migre
    sans rien gagner ;
  - 3 : rapide, mais les statistiques traversent les droits ;
  - 5 : dépendance à un modèle, format d'index propre au modèle, aucun gain
    mesurable sur 7 documents (hit@3 saturé). Reportée à M8, sur besoin
    démontré.
- Impacts :
  - données : même export, mêmes contrôles d'entrée ; accents neutralisés par
    `unicode61` (changement de comportement, à documenter pour les
    utilisateurs) ;
  - coût : index 2,25 fois plus gros qu'un index partagé, 3 fois plus qu'un
    SQLite lexical (43,6 Mo contre 14,4 Mo à 7 000 documents) ;
  - sécurité : isolation des statistiques par rôle ; un document visible par
    trois rôles est indexé trois fois ;
  - souveraineté : SQLite, domaine public, format lisible sans le code ;
  - exploitation : reconstruction en 0,6 s à 7 000 documents, contre 0,24 s en
    SQLite lexical.
- Gate, rollback et condition de révision :
  - gate : zéro fuite (11 sondes × 2 rôles), classement mesuré sur des cas
    gelés avant la mesure (brief 2), refus d'un index périmé (ADR-0003) ;
  - rollback : repointer `active.json` vers l'index JSON conservé, avec son
    empreinte attendue (exercé au brief 1, RES-08) ;
  - révision : si le nombre de rôles dépasse une dizaine (coût disque linéaire
    en rôles), passer à un index par **périmètre** (ensemble de rôles aux
    droits identiques) plutôt que par rôle.
- Résultat de la migration exercée (brief 2, phase 1, `531d288`), sur
  24 cas gelés avant mesure : hit@3 0,85 → 0,95, hit@1 égal (0,85), perte en
  hit@1 sur les reformulations (0,778 → 0,667). Gates bloquants 5/5, capacité
  52,8 contre 273 ms à 7 000 documents. **Choix confirmé**, avec une dette :
  36 ms des 52,8 viennent de l'empreinte de l'index recalculée à chaque
  requête (D-1).
- Changement après contradiction indépendante : **à remplir après la revue du
  brief 2.**
