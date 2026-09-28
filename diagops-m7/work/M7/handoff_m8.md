# Passage de relais M7 → M8

> **M7 clos le 28/09/2026 sur décision de l'apprenant** : brief 1 et brief
> online terminés ; brief 2, phase 1 terminée ; **phases 2 (revue
> indépendante) et 3 (remédiation, défense) abandonnées**. Le gate de sortie
> M7 (« une revue indépendante a modifié ou confirmé au moins une hypothèse »)
> n'est donc pas rempli : M8 part d'une cible non revue. Il ne publie aucune référence commune et ne valide
> pas M8.

- **Version exacte revue, verdict et reviewer** : version proposée à la revue
  `531d288` (`diagops-m7/work/M7`) ; contrat gelé `893ccfa`. Verdict : **aucun,
  revue abandonnée** sur décision de l'apprenant. Reviewer : aucun.
- **Architecture et ADR retenus / options abandonnées** :
  - retenus (proposés) : ADR-0001 FTS5 par rôle ; 0002 identité OIDC ; 0003
    index lié à son manifeste, révision unique, revue à deux ; 0004 quarantaine
    au document ; 0005 pas de génération, hybride conditionnel ; 0006 outil à
    effet fictif ; 0007 purge des traces à 30 jours (190 si haut risque) ;
    0008 mention d'interaction IA ;
  - abandonnés : migration de stockage JSON → SQLite lexical (aucun gain) ;
    index FTS5 partagé (statistiques qui traversent les droits) ; embeddings
    (aucun gain mesurable sur 7 documents, dépendance au modèle).
- **Preuves de portabilité, accès et reprise** :
  - `results/portabilite-fts5-r1` : alternative exercée, 12/12 requêtes
    brutes en erreur puis corrigées, 0 fuite, canal auxiliaire mesuré ;
  - `results/migration-r1` : 24 cas gelés, hit@3 0,85 → 0,95, gates
    bloquants 5/5, 6 scénarios conformes ;
  - `results/migration-capacite-r1` et `capacite-r1` : 273 → 53 ms à
    7 000 documents ;
  - `results/resilience-r1` : 8 scénarios ; `results/red-team-r1` : 10 cas ;
  - `results/replay-reference-r1` : référence M6 rejouée à l'identique.
- **Risques résiduels, blockers, limites de validité** :
  - bloquent la **mise en service** : R-01 (manifeste sans revue), R-02
    (identité), R-13 (sauvegarde), R-16 (purge), R-17 (mention IA) ;
  - bloquent une **sortie du bac à sable** de l'outil à effet : R-REG-01,
    R-02, R-05 ;
  - bloquent l'**option cloud** : R-09, R-REG-03 et les six préalables de
    l'ADR-0005 ;
  - limites : corpus de 7 documents, cas écrits par l'auteur, un seul poste,
    aucun LLM. Un invariant « tenu » sur l'agent déterministe ne vaut pas pour
    un générateur.
- **Veille M7, décisions et questions M8** : `veille_diagops/decisions_m7.md`
  (D1 à D8, reportées dans les ADR et le registre) ; 13 questions (Q1 à Q13),
  chacune avec un responsable et une échéance. La plus structurante pour M8 :
  **Q1**. Un système sans modèle appris est-il un « système d'IA » ? Si non,
  c'est l'introduction d'un LLM qui fait entrer le projet dans l'AI Act.
  Méthode d'accès aux textes : Cellar de l'Office des publications (EUR-Lex
  vide depuis ce poste), commande dans `veille_diagops/sources.md`.
- **Méthode transférable au nouveau projet** :
  - écrire les hypothèses et les cas **avant** la mesure, et les geler par
    empreinte : 12 hypothèses fausses sur 15 au brief 1, 2 prédictions sur 6
    au brief 2 ;
  - ne pas croire une métrique qui sature : hit@3 à 1,0 sur la calibration
    cachait un classement différent à 9 questions sur 12 ;
  - tester les droits **après** chaque changement de composant, statistiques
    comprises ;
  - séparer observé, déclaré et estimé, et le dire à chaque chiffre ;
  - une injection de panne par copie, jamais sur la source ; une copie par
    variante d'attaque.
- **Éléments propres à DiagOps, à ne pas recopier** : le corpus de 7 documents
  et ses seuils synthétiques ; le planificateur à mots-clés du M6 ; les rôles
  `technicien`/`superviseur`/`auditeur`/`public` ; le coût d'API calculé sur
  une hypothèse d'usage arbitraire.
