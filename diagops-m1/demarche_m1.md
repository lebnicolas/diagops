# Démarche M1 — pas à pas

Plan de travail du module 1 (17 h). On coche au fur et à mesure : les commits
git font foi de la chronologie, et **l'ordre des étapes est noté** — le
protocole doit être écrit avant la première mesure.

## L'exercice en une phrase

DiagOps transforme un rapport de technicien écrit en français libre en une fiche
structurée toujours au même format. En M0, un modèle généraliste faisait ce
travail avec de bonnes consignes. **La question de M1 : si on lui fait réviser
320 exemples corrigés, devient-il meilleur — assez pour qu'on le mette en
service ?**

La réponse peut être non. C'est une réponse valable, et même attendue si les
mesures la soutiennent.

## Le vocabulaire minimum

| Terme | Ce que c'est |
|---|---|
| **Qwen3-0.6B** | Le modèle de langage utilisé. « 0.6B » = 600 millions de réglages internes. C'est petit : ça tient sur un laptop, mais ce n'est pas un génie. |
| **Baseline** | Le modèle brut, sans rien ajouter. Le point de comparaison. Si un candidat ne fait pas mieux que lui, il ne sert à rien. |
| **LoRA / adaptateur** | Un modèle, c'est une table de mixage géante aux boutons déjà réglés. Tout retoucher demanderait une ferme de serveurs. Le LoRA branche une **petite table à côté** qui corrige le résultat : on ne règle que la petite. Ça tient sur ton GPU et produit un fichier de quelques Mo au lieu de plusieurs Go. |
| **Entraîner / fine-tuner** | Montrer au modèle des exemples corrigés pour qu'il ajuste les boutons de la petite table. |
| **Epoch** | Un passage complet sur les exemples d'entraînement. 3 epochs = le modèle voit les 320 exemples trois fois. |
| **Hyperparamètre** | Un réglage de l'entraînement, choisi par toi et pas appris par la machine : rang, learning rate, nombre d'epochs… |
| **Métrique** | Une mesure chiffrée de la qualité du résultat. |
| **Promouvoir** | Décider de mettre le candidat en service dans l'application. |

## Les trois paquets de données — le cœur de l'honnêteté

Les 400 exemples annotés se découpent en trois, et ce découpage n'est pas
administratif : c'est ce qui rend ton résultat crédible.

- **320 pour apprendre.** Le modèle les voit et s'en imprègne.
- **80 pour comparer.** Il ne les a jamais vus. C'est là-dessus que tu compares
  tes quatre systèmes et que tu choisis ton favori.
- **100 scellés.** Ouverts **une seule fois**, tout à la fin, quand ton choix est
  définitif et gelé.

Pourquoi ce troisième paquet ? À force d'essayer des variantes sur les 80
exemples de comparaison, tu finis par choisir ce qui marche bien *sur ces
80-là*, pas ce qui marche bien en général. C'est de la triche involontaire, et
elle est invisible de l'intérieur. Le paquet scellé donne le seul chiffre
honnête : celui obtenu sur des cas que rien n'a jamais influencés.

Même logique pour le protocole écrit d'avance : sans prédiction annoncée, le
cerveau trouve toujours une bonne raison d'aimer le résultat qu'il a obtenu.

> Le garde-fou est dans le code : `src/evaluate.py` **refuse** tout fichier dont
> le nom contient `test` tant qu'on ne passe pas `--allow-test`. Ne pas
> contourner ce blocage avant la phase C.

## Ce qui est noté

Pas la performance du modèle. **La qualité de la démarche.**

Un LoRA qui dégrade tout, correctement mesuré et honnêtement rejeté, vaut mieux
qu'un LoRA promu sans preuve. Ton livrable final n'est pas un modèle, c'est un
**dossier de décision** : ce que je voulais tester, ce que j'avais prédit, ce
que j'ai mesuré, les erreurs que j'ai analysées, l'objection qu'on m'a faite et
ce que j'en ai fait, et pourquoi je recommande — ou pas — la mise en service.

## Où sont les choses

| Chemin | Contenu |
|---|---|
| `data_pack/2026-S1/annotations/diagops_train.jsonl` | 400 annotations — pack régénéré le 27/07/2026, checksum `546b158…` conforme au `checksums.sha256` livré |
| `data_pack/2026-S1/annotations/diagops_test.jsonl` | **non livré** — les 100 scellés, phase C |
| `starter/src/` | le code fourni : découpage, relevé machine, entraînement, évaluation, métriques |
| `starter/configs/` | `baseline.yaml`, `lora_reference.yaml`, `variation_template.yaml` |
| `starter/templates/` | 5 gabarits de documents à remplir |
| `starter/work/` | toutes les preuves produites, créées au fil de l'eau |
| `../diagops-m0/` | l'application M0, à ne pas casser en phase C |

**Chemins corrigés le 27/07/2026** : le pack livré s'appelait
`datapack_2026-S1/` alors que le starter cherchait `../../data_pack/`. Le
dossier est désormais `data_pack/` et les commandes utilisent `../data_pack/`,
conformément à `brief1_module1.md`.

### Le pack a été régénéré le 27/07/2026

Les trois checksums ont changé. Le changement de fond porte sur le texte donné
au modèle, qui contient maintenant l'identifiant d'équipement :

```text
Identifiant equipement: EQ-PUMP-001
Rapport technicien: Pompe P-204 en zone A. Vibration plus forte que...
```

Avant, il fallait deviner `EQ-PUMP-001` à partir de « Pompe P-204 » — impossible
sans table de correspondance. Le `SCHEMA.md` l'explicite désormais.

Ce que ça change pour toi :

- **`equipment_id` devient une recopie**, plus une déduction. Un bon score n'y
  prouve rien, y compris pour la baseline. Ne fonde pas ta décision dessus.
- 36 exemples sur 400 n'ont pas d'équipement identifié (`Identifiant
  equipement: non renseigne`) et attendent `null` en sortie. C'est le vrai test
  intéressant sur ce champ : le modèle répond-il `null`, ou invente-t-il ?
- Aucun entraînement n'ayant encore tourné, il n'y a rien à refaire. Si tu avais
  déjà entraîné, tout serait à jeter.

---

## Étape 0 — Préparer la machine

Rien ici ne produit de résultat. On vérifie juste que la machine ne va pas
fausser les mesures.

- [x] **0.1 — Environnement Python créé** (`starter/.venv`)

- [x] **0.2 — Réparer l'installation de torch** *(fait le 27/07/2026)*

  L'installation a livré `torch 2.7.1+cpu` : la version qui ignore le GPU. C'est
  le piège classique sous Windows — `requirements.lock` épingle `torch==2.7.1`
  sans préciser d'où le télécharger, et PyPI sert la variante sans CUDA.

  ```powershell
  python -m pip uninstall -y torch
  python -m pip install torch==2.7.1 --index-url https://download.pytorch.org/whl/cu128
  ```

  `uninstall` puis `install` plutôt que `--force-reinstall` : on ne touche qu'à
  torch, sans réinstaller ses dépendances déjà en place. Environ 3 Go.

  Le reste du lock est correct et ne doit pas bouger : transformers 4.53.2,
  peft 0.16.0, accelerate 1.8.1, numpy 2.5.1.

- [x] **0.3 — Vérifier que le GPU calcule vraiment** *(fait — capability `(12, 0)`, calcul bf16 correct)*

  ```powershell
  python -c "import torch; print(torch.__version__, torch.version.cuda); a=torch.randn(2048,2048,device='cuda',dtype=torch.bfloat16); print((a@a).sum().item()); print(torch.cuda.get_device_capability(0))"
  ```

  Attendu : `2.7.1+cu128 12.8`, une capability `(12, 0)`, et un nombre.

  Pourquoi ce test et pas seulement `torch.cuda.is_available()` : cette fonction
  peut répondre « oui » avec une installation dépourvue des instructions
  spécifiques à ta carte. L'échec arriverait alors au milieu du premier
  entraînement. Ici il arrive en deux secondes.

  > En cas de `no kernel image is available for execution on the device` : les
  > wheels cu128 de torch 2.7.1 n'embarquent pas les instructions de ta carte.
  > Il faudra monter en version de torch, donc s'écarter de
  > `requirements.lock` — ce n'est pas une entorse, c'est un lock incompatible
  > avec le matériel. À documenter dans le protocole.

- [x] **0.4 — Relever la configuration machine** *(fait — premier fichier de preuve)*

  ```powershell
  python -m src.environment --output work/environment.json
  ```

  Résultat consigné dans `work/environment.json` : `backend: cuda`, torch
  `2.7.1+cu128`, RTX 5060 Laptop, 8 546 484 224 octets (7,96 Go), Python
  3.12.10, transformers 4.53.2, peft 0.16.0.

- [x] **0.4 bis — Contourner le proxy TLS de l'entreprise** *(fait le 27/07/2026)*

  Le premier accès à Hugging Face échoue en
  `CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate`. Le proxy
  du poste réémet les certificats HTTPS avec une autorité interne, présente dans
  le magasin de certificats Windows mais absente du bundle que Python utilise
  par défaut.

  Correctif appliqué **au niveau de l'environnement, pas du code** :

  ```powershell
  python -m pip install truststore
  ```

  puis un fichier `.venv/Lib/site-packages/sitecustomize.py` contenant :

  ```python
  import truststore
  truststore.inject_into_ssl()
  ```

  Python charge `sitecustomize` automatiquement au démarrage : tous les scripts
  du venv en bénéficient — `src.train`, `src.evaluate`, le notebook — **sans
  qu'une seule ligne du starter fourni soit modifiée**. C'est le bon endroit
  pour ce genre de correctif : il relève de la machine, pas de l'expérience.

  > À refaire si le venv est recréé — le `.venv/` n'est pas versionné. À
  > mentionner dans le protocole au titre des particularités d'environnement.

### La plateforme d'exécution — tranché le 27/07/2026

Tous les runs tournent sur le GPU local.

| Élément | Valeur |
|---|---|
| GPU | NVIDIA GeForce RTX 5060 Laptop |
| VRAM | 8 151 MiB (~8 Go) |
| Driver | 610.74, CUDA UMD 13.3 |
| Architecture | Blackwell `sm_120` → wheels **cu128** obligatoires |

À écrire dans le protocole : tes mesures de vitesse et de mémoire sont propres à
cette machine et **ne se comparent pas** à celles d'un autre groupe sur un autre
GPU. Seules tes comparaisons baseline ↔ candidats, faites ici, ont valeur de
preuve. Ce n'est pas une faiblesse si tu le dis ; c'en devient une si un
relecteur le découvre à ta place.

- [x] **0.5 — Limite des 8 Go de VRAM : marge confortable** *(mesuré le 27/07/2026)*

  Le gros consommateur n'est pas le modèle mais le tableau de scores produit à
  chaque mot : le vocabulaire de Qwen fait 151 669 entrées, et le calcul
  d'erreur le repasse en pleine précision.

  Mesure des longueurs réelles sur les 400 exemples (séquence complète) :

  | min | médiane | p95 | max |
  |---:|---:|---:|---:|
  | 257 | 280 | 298 | 320 |

  **Aucun exemple ne dépasse `max_length: 512`** — rien n'est tronqué. Et le
  collator remplit chaque lot à la longueur réelle du lot (~300 tokens), pas à
  512 : la mémoire consommée sera nettement inférieure à l'estimation initiale
  faite sur 512. La marge sur 8 Go est confortable.

  Si un « out of memory » survient malgré tout, deux leviers, dans cet ordre :

  1. **`per_device_batch_size: 4 → 2` et `gradient_accumulation_steps: 4 → 8`.**
     Ces deux réglages se multiplient : 4×4 et 2×8 donnent le même total de 16.
     Le modèle apprend donc de la même façon, il traite juste les exemples par
     plus petits paquets. C'est le levier propre.
  2. **Gradient checkpointing** : recalcule certaines étapes au lieu de les
     garder en mémoire. Divise la mémoire, coûte environ 30 % de temps.

  > ⚠️ Règle absolue : tout ajustement mémoire s'applique **à l'identique aux
  > quatre runs**. Un réglage différent entre la référence et une variation
  > introduit une deuxième différence, et tu ne sais plus laquelle a produit
  > l'effet. Si l'ajustement est nécessaire, il est décidé **maintenant**, écrit
  > dans le protocole, et appliqué partout.

- [x] **0.6 — Vérifier que l'entraînement apprend au bon endroit** *(vérifié le 27/07/2026 — RAS)*

  Quand on entraîne le modèle, on lui montre la question **et** la réponse, mais
  on ne veut le noter que sur la réponse — sinon il apprend à réciter la
  question. Le code masque donc la partie question.

  `src/train.py` fait ce masquage en supposant que les mots de la question sont
  le début exact de la séquence complète. Or le format de dialogue de Qwen3
  insère un bloc technique `<think>` dans la question. Si un décalage se
  produisait, le modèle serait noté au mauvais endroit : **aucune erreur, aucun
  avertissement**, et le run de référence serait faux pour tout le module.

  Vérification faite avec le seul tokenizer, sans GPU : construction de la
  question et de la séquence complète via `apply_chat_template`, puis contrôle
  que `full_ids[:len(prompt_ids)] == prompt_ids`.

  **Résultat : alignement correct sur les exemples testés.** Le modèle est noté
  sur ~100 tokens (le JSON de réponse), la question en fait ~190. Le starter est
  utilisable tel quel, aucune correction nécessaire.

- [x] **0.7 — Lancer les tests fournis** *(fait — 5 passés en 0,33 s)*

  ```powershell
  pytest -q
  ```

- [ ] **0.8 — Décider ce qu'on met dans git**

  Le `.gitignore` du dépôt public ne mentionne pas `work/`. Or les preuves
  doivent être traçables, mais pas les fichiers intermédiaires lourds.
  Proposition : ignorer `starter/work/runs/*/checkpoints/`, versionner tout le
  reste (relevé machine, découpages, prédictions, métriques, adaptateurs
  retenus). Un adaptateur LoRA pèse quelques Mo : il a sa place dans le dépôt.

---

## Phase A — Brief 1 : monter l'expérience (7 h)

### A1 — Découper les données *(00:00–00:45)* — **fait le 27/07/2026**

- [x] ```powershell
  python -m src.dataset --input ../data_pack/2026-S1/annotations/diagops_train.jsonl --output-dir work/splits --seed 42 --validation-size 80
  ```

  Produit : `train.jsonl` (320 lignes), `validation.jsonl` (80),
  `split_manifest.json`. Le « seed 42 » garantit que le tirage est le même pour
  tout le monde et reproductible à l'identique demain.

- [x] **Contrôles effectués** :
  - volumes conformes : 320 / 80 ;
  - **aucune fuite** : 0 `annotation_id` commun entre les deux paquets ;
  - distributions de la validation relevées et reportées dans le protocole —
    `severity` : high 37, medium 16, low 14, critical 13 ;
    `requires_human_review` : 71 `true` / 9 `false` ;
    7 exemples sans identifiant d'équipement.

- [ ] **Reste à faire — inspection qualitative des annotations.** Le brief
  demande de noter toute anomalie plutôt que de la corriger. Un contrôle de
  forme a été fait (structure, longueurs, cas `null`), mais **aucune relecture
  du fond** des annotations n'a encore eu lieu : cohérence entre le rapport et la
  gravité attribuée, pertinence de l'hypothèse de panne, valeurs de `confidence`.
  À faire sur un échantillon, et à documenter dans `error_analysis.md`.

**Preuve produite** : `work/environment.json` + `work/splits/split_manifest.json`

### A2 — Écrire ta prédiction et figer le protocole *(00:45–01:30)* — **fait et gelé le 27/07/2026**

L'étape la plus discriminante du module. Elle se fait **avant** de voir le
moindre chiffre.

> **État** : protocole rédigé dans `starter/work/evidence/protocol_m1.md`,
> commité en `aa0c036`, gelé en `67c873e`. Variations retenues :
> `target_modules` + couches feed-forward (capacité), et `epochs: 3 → 5`
> (optimisation). Le rang a été écarté — voir la justification dans le
> protocole. Hypothèses, prédictions et règle de décision ne sont plus
> modifiables.

- [x] Remplir `templates/protocol_m1.md` → `work/evidence/protocol_m1.md` :
  - la question précise que l'expérience tranche ;
  - ton hypothèse en **si / alors / parce que** ;
  - tout ce que tu maintiens constant : modèle et version exacte, consignes
    envoyées au modèle, réglages de génération, découpage et seed, métriques,
    machine ;
  - les 4 runs, et pour chacun **ce que tu prédis avant de lancer** ;
  - ta **règle de décision** : qu'est-ce qui te fera retenir, rejeter, ou
    relancer une expérience. Écrite maintenant, pas après.

  > Ta règle de décision doit éviter deux métriques trompeuses (voir A6) :
  > `equipment_id` mesure une recopie, et `requires_human_review` est à 90 %
  > d'une seule valeur. Adosse ta décision au JSON correct, au format valide, à
  > la gravité **détaillée par classe**, et au score textuel.

- [x] Choisir tes deux variations. Chacune ne change **qu'un seul réglage** par
  rapport à la référence (rang 16, alpha 32, dropout 0.05, 4 modules ciblés,
  3 epochs, learning rate 2e-4, longueur 512) :

  | Variation | Réglage changé | En clair | Hypothèse |
  |---|---|---|---|
  | rang LoRA | `r: 16 → 32` | la petite table de mixage a deux fois plus de boutons | 16 ne suffit pas à capturer la tâche |
  | modules ciblés | ajout des couches MLP | on branche la petite table à d'autres endroits du modèle | le format JSON se joue ailleurs que dans l'attention |
  | durée | `epochs: 3 → 5` | le modèle révise 5 fois au lieu de 3 | 3 passages sur 320 exemples, c'est trop peu |
  | vitesse d'apprentissage | `2e-4 → 1e-4` | il corrige ses réglages par plus petits pas | le réglage par défaut sur-corrige et abîme le texte libre |

  Choix qui se défend bien à l'oral : une variation sur la **capacité** (rang ou
  modules) et une sur l'**optimisation** (epochs ou learning rate) — deux axes
  différents plutôt que deux points du même axe.

- [x] **Committer le protocole avant la première mesure.** Le hash du commit va
  dans la section « Gel ». C'est lui qui prouve que tu n'as pas écrit ta règle
  après avoir vu les chiffres.

### A3 — Mesurer la baseline *(01:30–02:15)*

- [ ] ```powershell
  python -m src.evaluate --config configs/baseline.yaml --data work/splits/validation.jsonl --output-dir work/baseline_validation
  ```

Le modèle brut sur les 80 exemples de comparaison. C'est le score à battre.

À savoir : si le modèle répond avec son JSON entouré de ``` ```` ```, c'est
compté comme raté. Le starter ne répare volontairement rien — un JSON qu'il faut
nettoyer avant usage n'est pas un JSON exploitable. C'est à expliquer, pas à
contourner.

### A4 — Entraîner et évaluer le LoRA de référence *(02:15–03:00)*

- [ ] ```powershell
  python -m src.train --config configs/lora_reference.yaml --train-data work/splits/train.jsonl --output-dir work/runs/lora_reference

  python -m src.evaluate --config configs/baseline.yaml --adapter work/runs/lora_reference/adapter --data work/splits/validation.jsonl --output-dir work/lora_reference_validation
  ```

Noter que l'évaluation utilise **`baseline.yaml`** avec l'option `--adapter` :
mêmes réglages de génération que la baseline, seul l'adaptateur change. C'est ce
qui rend la comparaison équitable. Ne pas y toucher.

Ce run de référence reste **intact** pour tout le module.

### A5 — Les deux variations *(03:00–04:00)*

- [ ] Copier `configs/variation_template.yaml` en `variation_1.yaml` et
  `variation_2.yaml`. Remplir le bloc `experiment` (hypothèse, réglage changé,
  effet attendu) **avant** de lancer.
- [ ] Entraîner puis évaluer chacune, en sortant dans `work/runs/variation_N/`
  et `work/variation_N_validation/`.

Pendant qu'un entraînement tourne, on n'attend pas : on prépare la grille
d'analyse d'erreurs et on vérifie la reproductibilité du run précédent.

### A6 — Comparer et analyser les erreurs *(04:00–05:00)*

- [ ] Regrouper les 4 fichiers `metrics.json` dans `work/metrics_m1.csv` — une
  ligne par système, une colonne par métrique.
- [ ] Analyser **au moins 12 erreurs** dans `error_analysis.md` : type, champ,
  gravité, cause probable, action envisageable.

**Les pièges de ce jeu de données**, relevés sur les 400 annotations :

- **`requires_human_review` est une métrique en trompe-l'œil** : 361 `true` pour
  39 `false`. Un modèle qui répondrait toujours `true` obtient 90,25 % — juste
  sous le seuil de 95 %. Le chiffre paraîtra bon sans rien démontrer. Regarde
  l'exactitude **sur les 39 `false` uniquement** : c'est là que se joue la vraie
  valeur du champ.
- **La gravité est déséquilibrée** : `high` 177, `medium` 103, `critical` 60,
  `low` 60. Le macro-F1 donne le même poids aux 4 niveaux — c'est le bon choix,
  mais rater `critical` coûte 0,25 d'un coup. Publie le score **par niveau**, pas
  seulement la moyenne. C'est exactement l'objection « la moyenne cache une
  classe faible » que le brief liste, et que ton relecteur va chercher.
- **`equipment_id` mesure une recopie** depuis la régénération du pack. Le cas
  intéressant est celui des 36 exemples sans équipement : le modèle répond-il
  `null` ou invente-t-il ?
- Un gain sur le score textuel payé par une perte sur `requires_human_review`
  est un mauvais échange : sur un outil de maintenance, le champ qui protège
  l'humain compte plus que la formulation.
- Séparer les erreurs de **forme** (JSON cassé, format invalide) des erreurs de
  **fond** (mauvaise gravité, panne mal identifiée). Un LoRA corrige surtout les
  premières — c'est un vrai gain, mais ce n'est pas de la compréhension métier.

### A7 — Revue contradictoire *(05:00–05:45)*

- [ ] Remplir `peer_review.md`. Le relecteur doit **essayer de démolir** au moins
  un point : mélange entre données d'apprentissage et de comparaison, consignes
  différentes entre candidats, deuxième variable qui a bougé sans qu'on le
  remarque, métrique mal définie, moyenne qui cache une classe faible, mesure de
  vitesse non comparable, conclusion qui dépasse les résultats.

> **À trancher** : le brief suppose des groupes de 2-3 et une revue croisée entre
> groupes. En solo, il faut un relecteur externe réel — un pair, le formateur.
> Une auto-revue n'a pas la même valeur probante, et ça se verra à la soutenance.

### A8 — Corriger et re-mesurer *(05:45–06:30)*

- [ ] Traiter l'objection : correction ou run ciblé, avec **preuve avant / preuve
  après**. C'est le point le plus souvent raté : l'objection doit produire un
  effet visible dans le dépôt, pas un paragraphe de réponse.

### A9 — Décision intermédiaire *(06:30–07:00)*

- [ ] Écrire la décision : candidat **retenu / rejeté / à réexpérimenter**, en
  citant des chiffres précis. Synthèse de 5 minutes.

---

## Phase B — Distanciel : reproduction croisée (3 h)

- [ ] Refaire l'expérience d'un pair depuis son dépôt, sans explication orale.
- [ ] Vérifier ses preuves : versions, seed, consignes, découpage, métriques
  recalculables.
- [ ] Formuler une objection méthodologique argumentée.
- [ ] Corriger un point de ton propre protocole à la lumière de ce que tu as vu.

Compléter la section « Reproduction » de `peer_review.md` : tableau original /
reproduction / écart. Un écart non nul n'est pas un échec — c'est un résultat, à
condition de l'expliquer (le GPU n'est pas parfaitement déterministe, une
version de bibliothèque diffère, la précision de calcul n'est pas la même).

---

## Phase C — Brief 2 : l'examen final et l'intégration (7 h)

Le candidat est **gelé** avant d'ouvrir les 100 exemples scellés. Aucun réglage
ne sera retouché à partir de ces résultats.

### C1 — Reproduire le candidat depuis zéro *(00:00–00:45)*
- [ ] Empreinte de la configuration + journal de reprise.

### C2 — Ouvrir l'examen final, une seule fois *(00:45–01:30)*
- [ ] ```powershell
  python -m src.evaluate --config configs/baseline.yaml --data ../data_pack/2026-S1/annotations/diagops_test.jsonl --output-dir work/final/baseline --allow-test

  python -m src.evaluate --config configs/baseline.yaml --adapter work/model_final --data ../data_pack/2026-S1/annotations/diagops_test.jsonl --output-dir work/final/candidate --allow-test
  ```

### C3 — 20 cas tordus pour tester la solidité *(01:30–02:30)*
- [ ] `robustness_cases.jsonl` : des rapports du test déformés **sans changer le
  sens attendu**. Familles imposées : fautes de frappe et abréviations, phrases
  dans le désordre, information parasite ajoutée, équipement mentionné en
  dernier, formulation raccourcie, plusieurs symptômes en même temps, aucun
  identifiant d'équipement, rapport ambigu qui exige un humain.
- [ ] Pour chaque famille : en quoi c'est plausible sur le terrain, et comment tu
  as vérifié que la bonne réponse n'avait pas changé.

### C4 — Comparer baseline et candidat sur ces cas *(02:30–03:30)*
### C5 — Analyser par champ, par gravité, par type d'échec *(03:30–04:30)*
### C6 — Mesurer vitesse et mémoire *(04:30–05:15)*
### C7 — Intégrer dans l'API M0 *(05:15–06:00)*

- [ ] Même schéma Pydantic qu'en M0, contrat `POST /diagnose` **inchangé** — une
  application qui appelait DiagOps avant doit continuer à marcher sans rien
  changer.
- [ ] Baseline et LoRA derrière la même interface, choix par fichier de
  configuration.
- [ ] Adaptateur chargé séparément du modèle de base ; erreurs de chargement et
  de génération gérées proprement.
- [ ] Tests de non-régression sur **les deux chemins**.
- [ ] API conteneurisable sans exiger de GPU dans Docker.

### C8 — Model card et décision *(06:00–07:00)*

- [ ] Model card, note de décision, fiche individuelle, restitution de 8 minutes.

### Les seuils de mise en service

Tous doivent être satisfaits pour proposer la promotion :

| Critère | Seuil |
|---|---|
| Réponses qui sont du JSON valide | ≥ 95 % |
| Réponses au bon format une fois vérifiées | 100 % |
| Bon identifiant d'équipement | ≥ 95 % |
| Gravité — macro-F1 | ≥ 0.80 |
| Bon jugement sur « revue humaine nécessaire » | ≥ 95 % |
| Qualité des champs textuels | ≥ 0.65 |
| Ralentissement accepté | ≤ 20 % |
| Progrès global face à la baseline | ≥ 10 points, ou autre bénéfice défendu |

Ces seuils conditionnent **la promotion, pas la réussite du module**. Si les
preuves ne suivent pas, la bonne réponse est la non-promotion ou la
prolongation, avec une hypothèse et une prochaine étape précises.

---

## Livrables → fichiers

| Livrable | Fichier | Phase |
|---|---|---|
| Relevé machine | `work/environment.json` | 0 |
| Protocole figé | `work/evidence/protocol_m1.md` | A2 |
| Configurations des 4 systèmes | `configs/*.yaml` | A2–A5 |
| Prédictions et métriques | `work/*/predictions.jsonl`, `metrics.json`, `work/metrics_m1.csv` | A3–A6 |
| Analyse des erreurs (≥ 12) | `work/evidence/error_analysis.md` | A6 |
| Revue et reproduction | `work/evidence/peer_review.md` | A7, B |
| Preuve de correction | commits avant / après | A8 |
| Décision intermédiaire | note versionnée | A9 |
| Cas de robustesse | `work/final/robustness_cases.jsonl` | C3 |
| Rapport de performance | `work/final/performance.md` | C6 |
| API mise à jour + tests | `../diagops-m0/` (ou copie M1) | C7 |
| Model card | `work/evidence/model_card.md` | C8 |
| Note de décision | `work/evidence/decision.md` | C8 |
| Fiche individuelle | `work/evidence/individual_evidence.md` | C8 |

## Garde-fous (éliminatoires)

- Les 100 exemples scellés ne sont ouverts qu'une fois, après gel du candidat.
- Les 4 systèmes sont comparés dans des conditions strictement identiques.
- Chaque variation répond à une hypothèse **écrite avant** l'exécution.
- Une capture d'écran n'est pas une preuve : prédictions, métriques,
  configuration et relevé machine doivent être exportés en fichiers.
- Une annotation douteuse se documente, elle ne se corrige pas.
- La décision cite des chiffres précis — y compris en cas de non-promotion.

## Points ouverts

- [x] ~~GPU commun ou local ?~~ → **local, RTX 5060 8 Go** (27/07/2026).
- [ ] Groupe de 2-3 ou solo — impacte la revue contradictoire et le distanciel.
- [ ] Politique de versionnement de `work/` (voir 0.8).
