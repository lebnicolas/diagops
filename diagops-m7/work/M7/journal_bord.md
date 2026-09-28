# Journal de bord M7

Nature de chaque entrée : **lecture**, **exécution** (sur ce poste, avec une
preuve dans `results/`), **simulation sur table** ou **rédaction**. Les
hypothèses sont écrites avant l'action ; le résultat dit si elles tiennent.

| Date/durée | Brief | Hypothèse | Action | Preuve/commande | Résultat | Décision/prochaine étape |
|---|---|---|---|---|---|---|
| 28/09 · 0,5 h | B1 | le kit M7 s'installe et ses tests passent | lecture des briefs ; `init_module.py M7` ; tests du starter ; `lab.py` | `results/decouverte-r1` | **fausse** : banc OK, mais 6/6 tests en erreur sous Windows (connexion SQLite non fermée) | corriger dans le kit apprenant, garder l'état reçu au commit d'ouverture |
| 28/09 · 0,3 h | B1 | la référence M6 se rejoue telle quelle | `tools/check_m7_release.py` | sortie du contrôle | **fausse** : inventaire comparé en chemins Windows contre chemins POSIX, référence intacte refusée | rejeu local avec chemins normalisés, `tools/` non modifié |
| 28/09 · 0,3 h | B1 | point de départ = référence commune, pas notre M6 | `scripts/replay_reference.py` | `results/replay-reference-r1` | 45 sources identiques, 4/4 égaux au gel, 5 échecs connus retrouvés | référence retenue |
| 28/09 · 0,2 h | B1 | le starter est portable | comparaison de deux exports du même corpus | `decouverte-r1` / `-r2` | **fausse** : CRLF sous Windows, 2 empreintes pour 1 corpus (7c8f… / 12ea…) | écriture LF imposée ; le contrat d'export du brief 2 fixera les octets |
| 28/09 · 1 h | B1 · ét. 1 | les traces des échecs SCN-013/014 montrent une fuite | lecture des traces gelées | `nominal_traces.json` | **fausse** : aucune fuite ; réponse citant 3 documents sans rapport | constat « preuve présente ≠ preuve pertinente » (R-04) |
| 28/09 · 1,5 h | B1 · ét. 5 | FTS5 accepte les questions telles quelles | `scripts/portability_fts5.py` | `results/portabilite-fts5-r1` | **fausse** : 12/12 erreurs de syntaxe ; corrigé par des termes cités et reliés par OR | — |
| 28/09 | B1 · ét. 5 | le filtre de rôle avant le score suffit à isoler les rôles | même banc, index partagé vs par rôle vs corpus sans document restreint | idem | **fausse pour les statistiques** : 10/10 scores, 2/10 classements modifiés ; index par rôle : 0 | ADR-0001 : un index par périmètre |
| 28/09 | B1 · ét. 5 | hit@3 départagera les backends | idem | idem | **fausse** : 1,0 partout, alors que le top 3 FTS5 ne coïncide qu'à 3/12 | le brief 2 écrira des cas qui départagent |
| 28/09 · 2 h | B1 · ét. 2 | le contrôle d'intégrité fermé protège sans coût | `scripts/resilience_run.py` (8 scénarios, copies) | `results/resilience-r1` | **fausse** : un document altéré coupe tout le corpus (RES-06) ; révocation sans effet en cours d'exécution (RES-07) ; timeout constaté après coup (RES-05) | ADR-0003, ADR-0004, R-09 |
| 28/09 · 2 h | B1 · ét. 6 | BM25 résiste mieux que le lexical au bourrage de mots-clés | `scripts/red_team.py` (RT-01 à RT-10) | `results/red-team-r1` | **fausse** : 12/12 top 1 dans les deux | R-01 : le contrôle manquant est humain (revue à deux) |
| 28/09 | B1 · ét. 6 | — | premier RT-02 : 3/3 injections « détectées » | idem | **erreur de protocole** : les 3 documents dans la même copie, le marqueur de l'un signalait les autres | une copie par variante : 1/3 repérée, 3/3 citées |
| 28/09 · 0,5 h | B1 · ét. 3 | le feedback est anonyme | recherche de noms et téléphones dans 124 commentaires | `security/data_policy.md` | **fausse** : 3 commentaires contiennent un nom et un numéro | R-15 |
| 28/09 · 1,5 h | B1 · ét. 7 | un exercice sur table joué seul ne prouve rien | arbitre automatisé `simulated_action/tabletop.py`, sans import réseau | `results/action-simulee-r1`, 4 tests | 11 séquences conformes ; identité de l'approbateur = argument (limite) | ADR-0006 : l'outil reste fictif |
| 28/09 · 0,5 h | B1 · ét. 4 | le coût d'API décide entre local et cloud | tarifs relevés (Mistral, Scaleway Paris), hypothèse de 22 000 questions par mois | `portability/alternatives.md` | **fausse** : moins de 10 $ par mois ; le coût dominant est la conformité et l'exploitation | ADR-0005 |
| 28/09 · 0,5 h | B1 · ét. 8 | la migration de stockage du starter améliore la capacité | `scripts/capacity_scale.py` (×1 à ×1000) | `results/capacite-r1` | **fausse** : SQLite lexical 329 ms contre JSON 297 ms à 7 000 docs ; FTS5 par rôle 21 ms | ADR-0001 : changer le moteur, pas le stockage |
| 28/09 · 1 h | B1 · ét. 9 | EUR-Lex reste inaccessible, le texte consolidé ne sera pas lu | veille (agent) : Cellar de l'Office des publications | `veille_diagops/` | **fausse** : texte consolidé lu via Cellar ; 8 décisions, 13 questions M8 | D1 à D8 reportées (ADR-0005 à 0008, R-REG-01 à 03, R-16, R-17) |
| 28/09 · 1 h | B1 · ét. 8 | — | cible, 8 ADR, plan de migration | `architecture/` | décision : **différer** jusqu'au brief 2 ; migrer sans l'ADR-0003 aggraverait R-11 | brief 2 |
| 28/09 · 6 h (agent) | online | — | évaluation du modèle de provenance M4 | `online/` | voir `online/journal_decisions.md` ; 6 entrées invalides sur 9 prédites sans alerte | décision « évaluer davantage » maintenue |
| 28/09 · 1 h | B2 · ph. 1 | — | contrat, 24 cas et 6 prédictions gelés **avant** tout code candidat | commit `893ccfa`, `cases.jsonl` `2ed61a27…` | — | implémentation |
| 28/09 · 3 h | B2 · ph. 1 | P1 à P6 (`contract.md`) | candidat `migration.py` ; `scripts/migration_run.py` | `results/migration-r1` | gates bloquants 5/5, scénarios 6/6 ; **P1 et P2 fausses** : le lexical n'atteint pas 0,90 ; FTS5 perd en top 1 sur les reformulations (B2-12) | FTS5 confirmé, argument corrigé |
| 28/09 | B2 · ph. 1 | — | oubli constaté : le gate de capacité n'était pas dans le script | `scripts/migration_capacity.py`, `results/migration-capacite-r1` | gate passé (53 contre 273 ms) ; 36 ms sur 53 servent à l'empreinte de l'index par requête | dette D-1 ; oubli consigné dans les révisions du contrat |
| 28/09 | B2 · ph. 1 | — | durées citées dans le journal de migration relues contre le rapport | `results/migration-r1/report.json` | **3 durées fausses** écrites de mémoire (26, 28, 12 ms au lieu de 21, 16, 29) | corrigées ; ne citer un chiffre qu'après l'avoir relu dans le rapport |
| 28/09 · 0,5 h | B2 · ph. 2 | — | paquet de revue préparé : version, commandes, six points à challenger | `independent_review.md` | **revue non faite** : il faut une autre personne | à organiser avec un apprenant ou le formateur |

Budget : 14 h présentiel (dont veille), 6 h online, 20 h approfondissement (12 réalisation + 4 revue indépendante + 4 remédiation/défense). Distinguer lecture, simulation sur table et exécution réelle.

## Bilan du brief 1

Quinze hypothèses écrites avant l'action, **douze fausses**. Trois ont changé
une décision d'architecture :

1. « le filtre de rôle avant le score suffit » → index par périmètre ;
2. « la migration du starter améliore la capacité » → changer le moteur,
   pas le stockage ;
3. « le contrôle d'intégrité fermé protège sans coût » → quarantaine au
   document et index lié à son manifeste.

Aucune n'était visible dans un résultat agrégé : hit@3 à 1,0, 15/18 réussis,
0 fuite. Il a fallu des cas construits pour chacune.
