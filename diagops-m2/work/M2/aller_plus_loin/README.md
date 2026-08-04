# Qualification des livraisons DiagOps

Complement « Pour aller plus loin » du module 2. Repond a une question que
l'audit M2 ne se posait pas : **un nouveau lot peut-il rejoindre le socle
publie sans en degrader la qualite ?**

Le dispositif ne corrige rien, n'integre rien et n'ecrit jamais dans
`data_pack/`. Il constate, classe, et produit une decision motivee que
quelqu'un doit ensuite prendre.

## Lancer

Depuis `work/M2/` :

```bash
python -m venv .venv && .venv/Scripts/pip install -r aller_plus_loin/requirements.txt
.venv/Scripts/python aller_plus_loin/qualify.py
```

| Commande | Effet |
|---|---|
| `python aller_plus_loin/qualify.py` | qualifie le socle publie puis la livraison candidate |
| `python aller_plus_loin/qualify.py --baseline-only` | controle de non-regression seul |
| `python aller_plus_loin/qualify.py --batch <batch_id>` | une livraison precise du catalogue |
| `python -m pytest aller_plus_loin/tests` | les 19 verifications du dispositif |

Codes de sortie, distincts a dessein :

| Code | Signification |
|---:|---|
| `0` | tous les lots sont `ACCEPTED` ou `ACCEPTED_WITH_WARNINGS` |
| `1` | au moins un lot est `REJECTED` — **rejet metier** |
| `2` | fichier absent, politique invalide, source modifiee — **echec technique** |

Une chaine d'integration doit separer les deux. Confondre un lot rejete avec
une panne de CI revient a traiter une mauvaise livraison comme un bug.

## Organisation

```
aller_plus_loin/
├── qualify.py                 point d'entree
├── config/
│   ├── quality_rules.yaml     LA POLITIQUE — niveaux, seuils, justifications
│   └── batches.yaml           catalogue des lots : chemins, volumes annonces
├── qualification/
│   ├── policy.py              lecture et validation de la politique
│   ├── batch.py               lecture d'un lot, construction du contexte
│   ├── incremental.py         controles absents de M2
│   ├── qualify.py             orchestration, statut
│   └── report.py              rapports et manifeste
├── tests/                     19 verifications
├── reports/
│   ├── baseline/              non-regression sur le socle publie
│   └── candidate_release/     livraison candidate
├── run_manifest.json          donnees + regles + resultats + decision
└── decision_livraison.md      les dix reponses et la decision
```

La separation `config/` contre `qualification/` n'est pas cosmetique : changer
d'avis sur un seuil ne doit jamais obliger a rouvrir le code qui compte.
`data_pipeline` **constate**, la politique **juge**.

## Comment une decision se forme

1. Le registre M2 est rejoue sur le lot, **dans le contexte du publie**.
2. Les controles propres a une livraison incrementale s'ajoutent.
3. La politique traduit chaque constat en `error`, `warning` ou `info`.
4. Le statut se deduit : une erreur suffit a rejeter, un avertissement suffit a
   conditionner.

Une regle peut changer de niveau selon son ampleur. `EVT-REF-002` est un
avertissement a une ligne orpheline et une erreur au-dela de 2 % : ce n'est
plus la meme chose qu'on constate. Une ligne fausse se traite ; une livraison
construite sur un autre referentiel se renvoie.

## Ce qui a du changer dans le code M2

Deux points d'extension, inertes tant qu'on ne s'en sert pas. L'audit M2
produit un `check_results.csv` **identique octet pour octet** a celui d'avant,
et ses 69 tests passent sans modification.

| Extension | Pourquoi |
|---|---|
| `AuditOptions.context_frames` | Les references d'un lot incremental se resolvent dans le publie. Sans cela, 80 evenements candidats portant sur des machines du catalogue seraient declares orphelins. Les trois controles croises avaient le meme defaut en pire : ils ne produisaient pas de faux positifs, ils s'eteignaient. |
| `unknown_value_masks(population=…)` | La recurrence d'une valeur inconnue se calculait sur la taille du lot examine. Il fallait 90 occurrences sur 1 800 lignes, 11 sur 220, et le seuil etait hors d'atteinte sur 30. La meme valeur changeait de classe selon le perimetre. |

`AuditOptions.population_frames` est distinct de `context_frames` a dessein :
resoudre une reference dans le contexte est toujours correct, y compter les
categories est un choix de politique, qu'un lecteur doit pouvoir contester sans
que cela remette en cause la resolution des references.

## Ce que le dispositif ne fait pas

- Il n'integre rien et ne modifie aucun fichier source. Le contexte
  publie + candidat vit en memoire et n'en sort jamais.
- Il ne remplace pas une decision. Il produit un statut ; la decision
  d'integration est ecrite dans `decision_livraison.md`, par un humain.
- Il n'a recu aucune revue contradictoire externe. Toutes les objections
  viennent de nos propres controles — meme limite qu'en M1 et M2.
