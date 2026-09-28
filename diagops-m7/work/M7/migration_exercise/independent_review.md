# Revue indépendante — à remplir par un autre apprenant ou le formateur

> **Clôture du 28/09/2026 : phases 2 et 3 abandonnées sur décision de l'apprenant.**
> Aucune revue indépendante n'a eu lieu. Le module est clos sans elle, comme le
> M1 et le M3 l'avaient été. Le tableau et le verdict restent vides à dessein :
> les remplir sans reviewer serait une fausse preuve. Le paquet ci-dessous reste
> utilisable si une revue est organisée plus tard.
>
> **État antérieur : revue non réalisée.** Ce fichier prépare la revue ; il
> n'en tient pas lieu. L'auteur n'a rempli que l'en-tête (version et
> commandes). Le tableau, les gravités et le verdict appartiennent au
> reviewer. Une relecture par l'auteur, ou par un assistant qui a participé à
> la rédaction, ne remplace pas cette revue.

- Auteur du livrable : Nicolas (rédaction assistée) / reviewer distinct : **à désigner** / date : —
- Version immuable revue : commit `531d288` du dépôt `lebnicolas/diagops`,
  dossier `diagops-m7/work/M7`. Contrat gelé au commit `893ccfa`. Cas :
  `migration_exercise/cases.jsonl`, SHA-256
  `2ed61a27b32efc136652e1d81376c1fbc9b3c923ced31d84367de03f36d6f590`.
- Commandes à rejouer (Python ≥ 3.11 ; aucune dépendance, sauf PyYAML pour les
  campagnes qui rejouent l'agent M6) :

```bash
cd diagops-m7/work/M7
python -m unittest discover -s tests -v                                     # 21 tests attendus
python lab.py --output results/revue-lab                                    # smoke test du starter
python scripts/portability_fts5.py --output results/revue-portabilite       # brief 1, alternative
python scripts/migration_run.py --output results/revue-migration            # brief 2, gates
python scripts/migration_capacity.py --output results/revue-capacite        # gate de capacité (~15 s)
# avec PyYAML (venv du lock M6) :
python scripts/replay_reference.py --output results/revue-replay
python scripts/resilience_run.py --output results/revue-resilience
python scripts/red_team.py --output results/revue-red-team
```

Comparer chaque `report.json` produit à son homologue dans `results/`. Les
durées varient d'un poste à l'autre ; les classements, les gates et les
verdicts doivent être identiques.

## Grille

| Critère | Résultat/preuve | Gravité | Correction attendue | Re-test |
|---|---|---|---|---|
| Frontières et dépendances explicites | | | | |
| Droits filtrés avant classement | | | | |
| Provenance et révisions conservées | | | | |
| Qualité, coûts, pertes honnêtement mesurés | | | | |
| Échec détecté et rollback rejoué | | | | |
| Outil à effet strictement fictif | | | | |
| Hypothèse confirmée ou invalidée | | | | |

## Points que l'auteur demande au reviewer de challenger

Aucun n'est un verdict ; ce sont les endroits où l'auteur doute le plus.

1. **Dette D-1** : faut-il garder l'empreinte de l'index à chaque requête
   (36 ms sur 53 à 7 000 documents) ou la vérifier seulement à l'activation et
   sur changement de fichier ? Le second choix est plus rapide, mais il laisse
   passer une corruption survenue entre deux requêtes.
2. **Les cas gelés** sont écrits par l'auteur, qui connaissait les documents.
   Un reviewer qui écrit 5 questions de plus, sans lire `cases.jsonl`,
   trouve-t-il le même écart entre les backends ?
3. **Le contrôle « droit rétabli »** compare les couples document/rôle de
   l'index à ceux du manifeste courant. Un cas qu'il laisserait passer : un
   document supprimé du manifeste, puis recréé sous un autre identifiant ?
4. **Le canal auxiliaire** des statistiques partagées : est-il exploitable en
   pratique, ou le coût de l'index par rôle (×2,25 en disque) est-il payé pour
   un risque théorique ?
5. **Les dépendances cachées** : l'agent M6 (PyYAML), `unicode61` (le
   comportement dépend de la version de SQLite), les chemins Windows.
6. **Les hypothèses de coût** de `portability/alternatives.md` (22 000
   questions par mois, 1 500 jetons par question) : sont-elles plausibles ?

## Verdict

Approuvé / corrections requises / migration refusée : **à rendre par le
reviewer.**

Le reviewer consigne ses désaccords ; l'auteur ne réécrit pas son verdict.
