# Protocole M1

**Statut : figé avant toute mesure.** Aucun résultat d'évaluation n'a été
observé au moment de la rédaction. Seuls le découpage des données (déterministe)
et le relevé de la machine ont été produits.

Auteur : Nicolas Lebon — Date de rédaction : 27/07/2026

## Question

L'ajout d'un adaptateur LoRA entraîné sur 320 rapports annotés permet-il à
`Qwen/Qwen3-0.6B` de produire des diagnostics DiagOps **plus conformes au
contrat JSON et plus justes sur la gravité** que le même modèle sans
adaptateur, à conditions de génération identiques ?

## Hypothèse

- **Si** : j'entraîne un adaptateur LoRA sur les 320 exemples d'entraînement,
  puis je l'applique au modèle de base sans modifier ni le prompt, ni le
  template de dialogue, ni les paramètres de génération.

- **Alors** : sur les 80 exemples de validation, le taux de sorties JSON
  directement parseables et le taux de conformité au schéma augmenteront
  fortement (gain attendu supérieur à 30 points), et le macro-F1 de `severity`
  augmentera de façon nette (gain attendu supérieur à 0.10), sans dégradation
  du score lexical des champs textuels ni de la latence p95.

- **Parce que** : le modèle de base est un généraliste qui n'a jamais vu ce
  contrat de sortie. Ses échecs attendus sont d'abord des échecs de **forme** —
  texte d'introduction avant le JSON, encadrement en bloc markdown, champs
  absents ou typés autrement, valeur de `severity` hors des quatre valeurs
  autorisées. L'entraînement supervisé sur des paires
  `rapport → JSON de référence` agit précisément sur ce point : il apprend au
  modèle la structure exacte attendue et le vocabulaire de sévérité employé par
  les annotateurs. Le gain doit donc être maximal sur les métriques de format,
  plus modéré sur la gravité (qui demande un jugement métier), et faible sur les
  champs en texte libre (dont la formulation reste ouverte).

**Ce qui pourrait démentir cette hypothèse** : un adaptateur qui produit du JSON
conforme mais dégrade la gravité ou le contenu textuel — cas classique de
surapprentissage sur un petit corpus, le modèle apprenant à reproduire la forme
sans améliorer le fond.

## Système contrôlé

Tout ce qui suit est **identique pour les quatre systèmes comparés**. Seul
l'adaptateur change.

- **modèle et révision** : `Qwen/Qwen3-0.6B`, révision Hugging Face
  `c1899de289a04d12100db370d81485cdf75e47ca`, dtype `bfloat16`.
  La révision est épinglée dans les configurations et vérifiée à l'exécution par
  `src/config.py`, qui refuse toute autre valeur.

- **prompt et template de dialogue** : `SYSTEM_PROMPT` et `user_message` de
  `src/prompting.py`, inchangés. Le message système impose un objet JSON unique,
  sans texte avant ni après. Le template de dialogue est celui du tokenizer
  Qwen3, appliqué avec `enable_thinking: false` — le modèle ne produit donc
  aucun raisonnement explicite avant sa réponse.

- **paramètres de génération** : `max_new_tokens: 256`, `do_sample: false`
  (décodage glouton, donc déterministe et reproductible), `temperature: 0.0`
  sans effet puisque l'échantillonnage est désactivé.

  Point clé d'équité : la baseline **et** les trois candidats sont évalués avec
  le même fichier `configs/baseline.yaml`, les candidats recevant en plus
  l'option `--adapter`. Aucun paramètre de génération ne diffère entre les
  systèmes comparés.

- **découpage et seed** : partage déterministe des 400 annotations en 320
  entraînement / 80 validation, `seed: 42`, tri préalable par `annotation_id`
  garantissant l'indépendance à l'ordre du fichier source.

  | Fichier | Lignes | SHA-256 |
  |---|---:|---|
  | source `diagops_train.jsonl` | 400 | `546b15828fdafbf0…` |
  | `work/splits/train.jsonl` | 320 | `4e33fa772f125708…` |
  | `work/splits/validation.jsonl` | 80 | `3529f8c15a1d4e77…` |

  Absence de fuite vérifiée : 0 `annotation_id` commun entre les deux paquets.

  Les 100 exemples de `diagops_test.jsonl` ne sont ni chargés, ni consultés
  pendant ce brief. Le garde-fou de `src/evaluate.py` (refus de tout fichier
  nommé `test` sans `--allow-test`) n'est pas contourné.

- **métriques** : celles calculées par `src/metrics.py` — taux de JSON
  parseable, taux de conformité au schéma après validation Pydantic, exactitude
  `equipment_id`, macro-F1 `severity`, exactitude `requires_human_review`, score
  lexical (token-F1) des champs `symptom`, `failure_hypothesis` et
  `recommended_action`, latence médiane et p95, débit, mémoire maximale de
  l'accélérateur, score composite.

  Aucune réparation des sorties n'est appliquée avant calcul : une réponse
  encadrée en bloc markdown est comptée comme non parseable, conformément au
  comportement du starter.

- **environnement** : relevé complet dans `work/environment.json`.
  Windows 11 (build 26200), Python 3.12.10, `torch 2.7.1+cu128`,
  `transformers 4.53.2`, `peft 0.16.0`, `accelerate 1.8.1`, `pydantic 2.11.7`.
  Accélérateur : NVIDIA GeForce RTX 5060 Laptop, 8 546 484 224 octets de mémoire,
  CUDA 12.8, capability `sm_120`.

  Particularité d'environnement : le poste passe par un proxy TLS d'entreprise
  qui réémet les certificats HTTPS. Le contournement est appliqué au niveau du
  venv (`truststore` chargé par un `sitecustomize.py`), **sans aucune
  modification du code du starter**.

  Conséquence à retenir : les mesures de latence, de débit et de mémoire sont
  propres à cette machine. Elles autorisent la comparaison entre nos quatre
  systèmes, mais ne sont pas comparables à celles d'un autre groupe.

## Runs

Chaque variation ne modifie **qu'un seul réglage** par rapport à la
configuration de référence (`r: 16`, `alpha: 32`, `dropout: 0.05`, modules
`q_proj`/`k_proj`/`v_proj`/`o_proj`, `epochs: 3`, `learning_rate: 2e-4`,
`max_length: 512`, `batch: 4`, `accumulation: 4`, `seed: 42`).

| Run | Variable modifiée | Valeur | Prédiction formulée avant exécution |
|---|---|---|---|
| **Baseline** | aucune | sans LoRA | JSON parseable **< 0.80** et schéma valide **< 0.70** : les échecs seront majoritairement de forme. Macro-F1 `severity` **< 0.40**, le modèle se rabattant sur les classes fréquentes (`high`, `medium`). Score lexical **< 0.50**. |
| **Référence** | aucune | configuration commune imposée | JSON parseable **≥ 0.95**, schéma valide **≥ 0.90** — c'est le gain principal attendu. Macro-F1 `severity` **entre 0.45 et 0.70**. Score lexical **≥ 0.55**. Latence p95 quasi inchangée (**+10 % au plus**), l'adaptateur n'ajoutant qu'un calcul marginal. |
| **Variation 1** | `lora.target_modules` | ajout de `gate_proj`, `up_proj`, `down_proj` | Gain **marginal** sur la référence : moins de 5 points de composite. Les couches feed-forward mémorisent davantage le vocabulaire, donc léger gain attendu sur le score lexical (**+0.02 à +0.05**), sans gain net sur `severity`. Un gain supérieur à 10 points de composite invaliderait mon hypothèse selon laquelle le format se joue d'abord dans l'attention. |
| **Variation 2** | `training.epochs` | `3 → 5` | **Pas de gain net attendu**, voire une dégradation. Sur 320 exemples, deux passages supplémentaires devraient provoquer du surapprentissage : format stable ou légèrement meilleur, mais score lexical **en baisse** (récitation de formulations vues) et `severity` stable. Je prédis que cette variation **ne dépassera pas la référence** sur le score composite. |

Hypothèse écrite pour chaque variation, avant exécution :

- **Variation 1** — *Si* je branche l'adaptateur également sur les couches
  feed-forward, *alors* le score lexical progressera légèrement sans que la
  gravité s'améliore, *parce que* ces couches portent davantage la restitution
  du vocabulaire que la décision de classification.
- **Variation 2** — *Si* je porte l'entraînement de 3 à 5 epochs, *alors* les
  métriques de forme resteront stables tandis que le score lexical baissera,
  *parce que* 320 exemples sont trop peu nombreux pour absorber deux passages
  supplémentaires sans mémorisation.

**Choix écarté et pourquoi** : faire varier le rang de l'adaptateur (`r: 16 →
32`) était tentant, mais le facteur d'échelle appliqué par LoRA vaut
`alpha / r`. Augmenter `r` seul le ferait passer de 2 à 1, et ajuster `alpha`
en conséquence reviendrait à modifier deux réglages. L'effet de capacité serait
alors confondu avec un effet d'échelle, et la variation ne serait plus
interprétable. Les deux variations retenues ne présentent pas cet effet de bord.

## Règle de décision

Établie **avant toute observation des résultats**, et applicable par un tiers à
partir du seul fichier `work/metrics_m1.csv`.

### Hiérarchie des métriques

Toutes les métriques ne se valent pas sur ce corpus, et deux d'entre elles sont
trompeuses. Cette hiérarchie est donc fixée à l'avance :

**Métriques décisionnelles** — elles fondent la décision :

1. taux de JSON parseable ;
2. taux de conformité au schéma ;
3. macro-F1 de `severity`, **examiné classe par classe** ;
4. score lexical des champs textuels.

**Métriques de contrôle** — surveillées, mais ne fondent aucune décision :

- **exactitude `equipment_id`** : depuis la régénération du data pack,
  l'identifiant figure explicitement dans le texte d'entrée. La métrique mesure
  une recopie, pas une déduction. Un score élevé ne démontre rien. Seul cas
  informatif : les 7 exemples de validation sans identifiant, où l'on vérifie
  que le modèle répond `null` au lieu d'inventer.
- **exactitude `requires_human_review`** : la validation ne contient que
  **9 cas `false` sur 80**. Un modèle répondant systématiquement `true`
  obtiendrait 88,75 %. La métrique globale est donc quasi dégénérée, et le
  sous-ensemble utile est trop petit pour trancher (une erreur vaut 11 points).
  Traitée comme un **indicateur d'alerte** : une chute signale une régression, une
  valeur haute ne prouve rien.
- **latence p95, débit, mémoire** : critères de coût, appliqués en garde-fou.

### Retenir un candidat

Le candidat est retenu pour le Brief 2 si **toutes** ces conditions sont
réunies :

1. taux de JSON parseable **≥ 0.95** ;
2. taux de conformité au schéma **≥ 0.95** ;
3. macro-F1 `severity` **≥ baseline + 0.10** ;
4. **aucune** des quatre classes de `severity` avec un F1 nul ;
5. score lexical **≥ celui de la baseline** (non-régression) ;
6. latence p95 **≤ baseline × 1.20**.

### Rejeter un candidat

Le candidat est rejeté si **au moins une** de ces conditions est vraie :

1. taux de JSON parseable **inférieur** à celui de la baseline ;
2. macro-F1 `severity` **inférieur** à celui de la baseline ;
3. une classe de `severity` tombe à un F1 nul alors que la baseline ne
   présentait pas ce défaut ;
4. latence p95 **> baseline × 1.50**.

Le cas « le LoRA est moins bon que le modèle brut » est explicitement couvert
par les points 1 et 2. Dans cette situation, la conclusion du brief sera la
**non-promotion**, et c'est un résultat recevable.

### Demander une expérience complémentaire

Dans tous les autres cas, et en particulier :

- métriques de forme atteintes, mais gain sur `severity` compris entre 0 et
  +0.10 — gain réel mais insuffisant pour être distingué du bruit ;
- les deux variations produisent des résultats contradictoires ;
- suspicion de surapprentissage sur la variation 2 (forme en hausse, fond en
  baisse) : une expérience à 4 epochs serait alors demandée pour situer le point
  de bascule.

### Départage entre plusieurs candidats retenus

1. score composite le plus élevé ;
2. à moins de 2 points d'écart de composite, le candidat le moins coûteux en
   latence p95 ;
3. à coût équivalent, la configuration la plus simple, c'est-à-dire celle
   comptant le moins de paramètres entraînables.

### Arbitrage explicite qualité / coût

Un gain de moins de 0.10 de macro-F1 `severity` payé par plus de 20 % de
latence p95 supplémentaire est refusé. Sur un outil de maintenance destiné à
être appelé en ligne, un ralentissement se paie à chaque diagnostic, alors qu'un
gain marginal de gravité reste soumis à revue humaine.

## Limites reconnues

Elles conditionnent ce que ce protocole autorise à conclure.

1. **Un seul run par configuration.** Aucune répétition avec des seeds
   différentes n'est prévue : la variance des résultats n'est donc pas estimée.
   Un écart faible entre deux systèmes ne peut pas être attribué de façon fiable
   à la variable manipulée. C'est la raison du seuil de +0.10 sur `severity` —
   choisi pour rester au-dessus du bruit plausible plutôt que pour être atteint
   facilement.

2. **Validation de petite taille et déséquilibrée** : 80 exemples, dont
   `high` 37, `medium` 16, `low` 14, `critical` 13. Sur les deux classes
   minoritaires, une seule erreur déplace le F1 de la classe d'environ 7 points.
   Les écarts de macro-F1 inférieurs à 0.05 ne seront pas interprétés.

3. **`requires_human_review` : 9 cas négatifs seulement.** Aucune conclusion
   solide n'est possible sur ce champ pourtant central pour la sécurité
   d'exploitation. Limite à porter dans la note de décision.

4. **`equipment_id` mesure une recopie** depuis la régénération du data pack, et
   ne renseigne pas sur la compréhension du rapport.

5. **Score lexical purement lexical** : le token-F1 récompense le vocabulaire
   commun, pas l'exactitude du diagnostic. Une hypothèse de panne fausse mais
   formulée avec les mots attendus obtiendra un bon score. L'analyse d'erreurs
   devra corriger cette cécité par une lecture qualitative.

6. **Corpus synthétique** : la data card exclut explicitement toute
   généralisation à un site industriel réel.

## Gel

- **commit** : *(à compléter au commit de gel)*
- **date** : 27/07/2026
- **auteurs** : Nicolas Lebon
