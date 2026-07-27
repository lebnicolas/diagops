# Preuve individuelle M1

## Identification

- **apprenant** : Nicolas Lebon
- **groupe** : *(à confirmer — travail conduit seul à ce stade ; la revue
  contradictoire A7 reste à faire avec un relecteur externe)*
- **commit de gel du protocole** : `aa0c036` (contenu) / `67c873e` (hash inscrit)
- **commit de la décision intermédiaire** : `25f4f42`
- **dépôt** : `lebnicolas/diagops`, dossier `diagops-m1/`

## Contribution

- **rôle principal** : pilote expérimental et analyste — formulation des
  hypothèses, rédaction du protocole, choix des variables, interprétation des
  résultats et arbitrage final.

- **hypothèse prise en charge** : *l'ajout de l'adaptateur sur les couches
  feed-forward (`gate_proj`, `up_proj`, `down_proj`) améliorera le score lexical
  des champs textuels sans gain net sur la gravité, parce que ces couches
  portent la restitution du vocabulaire plus que la décision de
  classification.*
  Configuration : `configs/variation_1.yaml`, bloc `experiment` renseigné avant
  exécution.

  **Hypothèse démentie.** Le gain lexical est de +0,272 (contre +0,02 à +0,05
  prédits) et le macro-F1 de `severity` progresse de +0,139 alors que je
  n'attendais aucun gain. Les couches feed-forward portent aussi le jugement, pas
  seulement le vocabulaire. Mon seuil d'invalidation, fixé à +10 points de
  composite, n'est toutefois pas franchi (+6,84).

- **runs exécutés** : les quatre systèmes du protocole — baseline,
  `lora_reference`, `variation_1`, `variation_2` — plus deux re-mesures
  correctives (adaptateur fusionné, banc de latence contrôlé). Environnement
  relevé dans `work/environment.json` : RTX 5060 Laptop, torch 2.7.1+cu128.

- **apport méthodologique personnel** : construction de la stratification
  vu/nouveau (`work/evidence/validation_proximite_train.json`), figée **avant**
  l'observation des résultats. Sans elle, `variation_2` — meilleur composite
  brut — aurait été retenue alors que la totalité de son avantage est de la
  mémorisation.

## Deux erreurs analysées

### Erreur 1 — le seul cas critique inédit est manqué par tous les systèmes

- **identifiant** : `ANN-2026S1-0039`, groupe `nouveau`
- **observation** : rapport « Pompe P-618. Forte odeur chaud côté moteur, bruit
  faible mais continu. Température bobinage signalée haute par automate. Arrêt
  préventif recommandé. » Gravité attendue `critical`. Les trois candidats —
  référence, `variation_1`, `variation_2` — répondent `high`.
- **cause probable** : c'est l'unique cas `critical` du groupe sans quasi-jumeau
  dans l'entraînement. La famille « pompe / surchauffe moteur » n'est représentée
  par aucun patron proche côté entraînement. Le modèle applique le motif lexical
  le plus voisin qu'il connaisse — celui des rapports de surchauffe classés
  `high` — sans percevoir le cumul de signaux (odeur, bruit continu, température
  bobinage, arrêt préventif) qui fonde la criticité.
- **impact** : maximal. C'est la seule observation dont on dispose sur la
  détection du critique en conditions inédites, et elle vaut **0 sur 1**. Elle
  contredit frontalement la lecture optimiste des scores agrégés
  (`variation_2` détecte 12 cas critiques sur 13, mais aucun inédit). Cette
  erreur justifie à elle seule la réserve inscrite dans la décision
  intermédiaire.

### Erreur 2 — échec de recopie sur un identifiant fourni en entrée

- **identifiant** : `ANN-2026S1-0247`, groupe `vu`, système `variation_1` fusionné
- **observation** : le texte d'entrée contient explicitement
  `Identifiant equipement: EQ-PRESS-117`. Le modèle produit `EQ-PRESS-17` — un
  chiffre perdu. C'est la seule erreur d'`equipment_id` du candidat (1/80).
- **cause probable** : le champ est produit par génération token par token, sans
  mécanisme de copie contraint. Rien n'oblige le modèle à reproduire exactement
  une chaîne de l'entrée, et les identifiants numériques longs sont découpés en
  plusieurs tokens dont un peut être omis. Le décodage étant glouton, aucune
  correction n'intervient ensuite.
- **impact** : modéré techniquement, mais révélateur. Depuis la régénération du
  data pack, `equipment_id` est une tâche de **copie**, réputée triviale — et
  elle échoue quand même. Un modèle de 600 millions de paramètres n'offre aucune
  garantie d'exactitude, même sur du recopiage. Conséquence opérationnelle
  directe : un diagnostic rattaché au mauvais équipement est inexploitable, voire
  dangereux. La parade ne relève pas du modèle mais de l'intégration — vérifier
  que l'identifiant produit figure dans le texte d'entrée coûte trois lignes et
  supprime entièrement cette classe d'erreur.

## Objection traitée

- **objection** : *« La comparaison de latence entre la baseline et les candidats
  n'est pas équitable, donc le critère de latence du protocole ne peut pas être
  appliqué. »*

- **preuve recherchée et trouvée** — deux biais distincts, mesurés :

  1. **Adaptateur non fusionné.** Coût par caractère de 30,8 ms pour la référence
     contre 16,8 ms pour la baseline, alors que ses sorties ne sont que 1,22 fois
     plus longues. Le surcoût de 83 % par token venait des couches LoRA
     recalculées à chaque token, absentes de la baseline. On comparait un modèle
     nu à un modèle portant un échafaudage d'entraînement.
  2. **Dérive thermique.** À l'intérieur d'un même run, sur données homogènes, la
     latence des 20 dernières générations valait de 0,44 à 2,33 fois celle des
     20 premières. Chaque système ayant été mesuré dans une session distincte,
     les chiffres n'étaient pas comparables entre eux.

- **réponse apportée** :

  1. Ajout de `tools/evaluate_merged.py` : évaluation après `merge_and_unload()`,
     c'est-à-dire dans l'état de mise en service. Le starter fourni n'a pas été
     modifié.
  2. Ajout de `tools/latency_benchmark.py` : mesure alternée dans une session
     unique, ordre inversé à chaque exemple, préchauffage, et dérive publiée.
     Résultat : p95 de 3,663 s (baseline) contre 3,690 s (candidat), soit un
     ratio de **1,008**, avec une dérive résiduelle de 1,03 et 0,98.

  Sans ces corrections, un candidat conforme aurait été rejeté **deux fois** sur
  un artefact de mesure. À l'inverse, le run fusionné retenu est légèrement
  *moins* favorable en qualité que le run initial (composite 89,86 contre 90,02
  sur la référence) : la correction ne va pas dans le sens de l'embellissement.

- **limite assumée** : cette objection est **auto-formulée**. La revue
  contradictoire A7, qui exige un relecteur externe, reste à faire.

## Intégration

- **candidat chargé** : `work/runs/variation_1/adapter`, appliqué à
  `Qwen/Qwen3-0.6B` révision `c1899de289a04d12100db370d81485cdf75e47ca`, puis
  fusionné via `merge_and_unload()`.
- **commande exécutée** : chargement du modèle de base et de l'adaptateur, fusion,
  puis génération sur des rapports de validation. Durée de chargement : **8,3 s**.
- **résultat** : preuve complète dans
  `work/evidence/preuve_chargement_candidat.json`.

  | Exemple | Latence | Schéma valide | `severity` produite |
  |---|---:|---|---|
  | `ANN-2026S1-0250` | 3,41 s | ✓ | `high` (attendu `high`) |
  | `ANN-2026S1-0095` | 3,25 s | ✓ | `medium` (attendu `medium`) |

  Sorties conformes au contrat DiagOps, huit champs présents, validation Pydantic
  passée.

- **réserve** : l'appel via `POST /diagnose` de l'application M0 **n'a pas encore
  été réalisé** — l'intégration derrière l'API relève du Brief 2, qui ne peut pas
  démarrer tant que `diagops_test.jsonl` n'est pas livré. La preuve ci-dessus
  atteste du chargement et de l'inférence du candidat, pas de son intégration
  applicative.

## Recommandation

**Prolonger l'expérimentation** — et non promouvoir en l'état.

Le candidat `variation_1` satisfait les six conditions de retenue du protocole
gelé (composite 18,13 → 96,87, schéma valide 1,000, latence p95 à 1,008 fois la
baseline) et il est retenu comme candidat du Brief 2. Mais deux éléments
interdisent d'en recommander la mise en service aujourd'hui :

1. **`critical` détecté à 8 cas sur 13, avec cinq sous-estimations et aucune
   sur-estimation.** Le biais va systématiquement dans le sens dangereux. Sur un
   outil de maintenance industrielle, c'est le mode de défaillance le plus
   coûteux, et ma propre règle de décision ne l'attrape pas — le critère « aucune
   classe à F1 nul » laisse passer 0,375. J'assume cet angle mort plutôt que de
   réécrire la règle après coup.
2. **La généralisation n'est pas démontrée.** 81 % des exemples de validation
   possèdent un quasi-jumeau dans l'entraînement ; le macro-F1 tombe de 0,934 sur
   ce groupe à 0,562 sur les inédits, et le seul cas critique inédit est manqué.

**Prochaine étape proposée** : une expérience complémentaire sur le dropout LoRA
(0,05 → 0,15), seul hyperparamètre attaquant directement la mémorisation mesurée,
avec pour hypothèse une baisse du composite `vu` et une hausse du composite
`nouveau`. Puis, au Brief 2, remplacer le critère de F1 sur `critical` par un
plancher de **rappel** — seule mesure des dangers manqués.
