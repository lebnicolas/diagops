# Starter M7

Ce kit accompagne la revue d'architecture ; ses gabarits restent à remplir.
La référence `diagops-m6-reference-r1` contient les résultats et les limites du
starter M6, pas une solution terminée. Lire
`../../data_pack/2026-S1/reference_runs/m6_for_m7/README.md` depuis `work/M7/`.

## Démarrage

Python 3.11 ou plus suffit, sans installation pip, réseau, GPU ou secret.
Depuis la racine S04 :

```bash
python tools/init_module.py M7
cd work/M7
python -m unittest discover -s tests -v
python lab.py --output results/decouverte-r1
```

Les commandes sont identiques sous PowerShell. Le script d'initialisation et
le banc refusent d'écraser un dossier existant ; utiliser un nouveau nom pour
chaque essai. `--data-pack CHEMIN` permet de désigner un autre paquet.
Le data pack commun reste en lecture seule ; les résultats vont dans `results/`.

## Ce que démontre le banc

`lab.py` migre réellement un stockage documentaire JSON vers SQLite, conserve
les métadonnées et le classement lexical, vérifie les droits avant scoring,
détecte une corruption du candidat et restaure le pointeur vers JSON. Lire
`results/decouverte-r1/report.json` : parité des résultats, hit@3 sur calibration,
durées locales et limites. L'index SQLite reste volontairement corrompu après
l'exercice ; l'index actif restauré est JSON.

Le banc ne génère aucune réponse LLM. Il ne mesure ni résistance générale aux
injections, ni latence de production, ni énergie ou coût cloud. Le rôle passé
en argument n'est pas une authentification de service. Ce smoke test est un
point de départ : le reproduire ne valide pas le brief 2.

## Produire vos preuves

1. Cartographier l'état M6, puis compléter politique des données, menaces et
   alternatives. Reporter les échecs connus dans les risques résiduels.
2. Exécuter les scénarios sur copies locales ; qualifier toute simulation sur
   table et toute condition non testée.
3. Geler votre contrat, cas et seuils du brief 2 avant mesure ; étendre le banc
   à un changement de révision et une révocation d'accès, ou migrer une autre
   alternative justifiée. Conserver échec, correction et rollback.
4. Faire rejouer la version exacte par une autre personne, traiter les
   constats et défendre une décision. Compléter `handoff_m8.md`.

## Dossiers de travail

```text
work/M7/
├── architecture/
│   ├── current.md
│   ├── target.md
│   └── adr/
├── security/
│   ├── threat_model.md
│   ├── red_team_cases.yaml
│   └── residual_risks.md
├── portability/
│   ├── alternatives.md
│   └── exercise.md
├── resilience/
│   ├── scenarios.md
│   └── recovery.md
├── simulated_action/
│   ├── contract.json
│   └── approval_flow.md
├── migration_exercise/
│   ├── contract.md
│   ├── execution_log.md
│   ├── independent_review.md
│   └── remediation.md
└── journal_bord.md
```

Le dossier `simulated_action/` ne contient aucun identifiant, secret ou client
permettant de joindre un système réel.

Le kit contient aussi `security/data_policy.md`, `online/dossier.md`,
`veille_diagops/journal.md`, `handoff_m8.md`, `lab.py` et `tests/`.
La notation et le séquençage sont dans `../../M7/DIFFUSION.md` depuis `work/M7/`.
