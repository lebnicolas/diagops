---
module: M4
brief: brief 1 — présentiel
etat: cadrage
maj: 2026-08-31
---

# Plan de travail — Brief 1 M4

« Prouver avant d'architecturer »

Ce document cadre le travail avant toute exécution. Il fixe le point de départ,
l'état vérifié du pack, l'arborescence, les conventions, l'ordre des étapes et
les arbitrages à trancher. **Il ne contient aucun résultat de modélisation.**

---

## 1. Ce que le module change

M3 répondait à « ces données sont-elles utilisables ». M4 répond à « qu'est-ce
qu'un modèle apporte, et faut-il le déployer ». Trois différences de nature :

- **la preuve devient comparative.** Il ne suffit plus qu'un résultat soit
  correct : il doit être meilleur qu'une baseline gelée, mesuré sur le même jeu,
  dans les mêmes conditions ;
- **l'oracle sort de nos mains.** Le test capteur (1 800 lignes) est livré sans
  la colonne `provenance`, et 12 des 24 questions RAG sont `sealed`. Le
  formateur calcule les métriques finales **après gel du candidat**. Nous ne
  pouvons pas nous auto-évaluer sur le test, par construction ;
- **une décision négative est recevable.** « Maintenir la baseline » et
  « ne pas déployer » sont des conclusions valides si elles sont prouvées.

## 2. Ce que le contrôle d'ouverture a établi

Le brief interdit d'ouvrir le module si le manifeste est incomplet, si les
checksums sont invalides ou si les oracles ne sont pas scellés. Vérifié le
31/08, deux fois — par nos propres contrôles et par `tools/check_m4_release.py`,
qui rend `status: ready`.

| Contrôle | Résultat |
|---|---|
| Manifeste : droits, sensibilité, révision, checksum | complet sur les 8 documents |
| Checksums des documents | 8 / 8 valides |
| `checksums.sha256` des 4 dossiers | 21 entrées, toutes valides |
| Oracle capteur | **scellé** — `sensor_test.csv` n'a pas la colonne `provenance` |
| Oracle RAG | **scellé** — 12 questions `test` en `label_visibility: sealed`, `answerable: null` |
| Tests du starter | 13 / 13 |

C'est la première publication depuis le M2 qui ne porte aucune contradiction
interne. Rien à remonter.

**Deux pièges sont posés volontairement et annoncés** : `DOC-LOTO-001` est une
révision `superseded` qui score bien lexicalement, et `DOC-DATA-ACCESS-001` est
`restreint` aux rôles `superviseur` et `auditeur`.

## 3. Point de départ

### Le lot capteur

| | Calibration | Test |
|---|---|---|
| lignes | 900 | 1 800 |
| fenêtres (`window_id`) | **30** | 60 |
| lignes par fenêtre | 30 | 30 |
| étiquette | `provenance`, **une par fenêtre** | absente |
| répartition | 11 fabriquées / 19 réelles | inconnue |
| équipements | 22 | 32 |

**Deux faits structurants, mesurés avant toute modélisation :**

- **30 fenêtres, 11 positives.** C'est l'effectif d'entraînement *et* de
  validation interne. Toute métrique produite ici portera un intervalle de
  confiance large, et une différence de 0,05 de F1 entre deux modèles ne sera
  pas interprétable. Le dire d'emblée vaut mieux que de le découvrir dans la
  conclusion ;
- **20 des 22 équipements de calibration réapparaissent dans le test.** Les
  `window_id` ne se chevauchent pas, mais les équipements si. Le brief demande
  explicitement de vérifier qu'un équipement ne crée pas de fuite entre
  calibration et validation interne — c'est l'objet de l'arbitrage A2.

### La baseline M3 figée

`baseline_rules.py` applique sept règles de contrat capteur — période, unité,
grille horaire, plage, sentinelle, horodatage, **précision décimale**. Elle ne
regarde jamais la fenêtre : elle prédit ligne par ligne.

| Niveau | TP | FP | FN | Précision | Rappel | **F1** |
|---|---:|---:|---:|---:|---:|---:|
| ligne (métrique officielle) | 90 | 61 | 240 | 0,596 | 0,273 | **0,374** |
| fenêtre, seuil d'agrégation ≥ 2 | 3 | 2 | 8 | 0,600 | 0,273 | **0,375** |
| fenêtre, seuil d'agrégation ≥ 1 | 3 | 3 | 8 | 0,500 | 0,273 | 0,353 |

La baseline est **presque** tout ou rien par fenêtre : 24 fenêtres n'ont aucune
ligne signalée, 5 en ont 30, et **une seule fait exception** — `M4-CAL-019`,
avec exactement 1 ligne signalée, la sentinelle `-999` isolée du lot, sur une
fenêtre `pressure_bar` authentique.

Cette unique ligne décide du seuil d'agrégation. À 1, elle transforme une
fenêtre réelle en faux positif et fait tomber la baseline à 0,353 ; à partir de
2, la baseline rend 0,375, valeur stable jusqu'à 30. **Le seuil retenu est 2**,
et le motif n'est pas qu'il nous arrange : on ne bat pas une baseline qu'on a
handicapée par son propre choix d'agrégation. Une valeur aberrante isolée sur
30 mesures signale un défaut de qualité, pas une fabrication — c'est la
distinction établie au brief 2 M3.

Au seuil retenu, les deux niveaux donnent la même valeur à un millième près, ce
qui **neutralise le risque de comparaison inéquitable** entre un modèle par
fenêtre et une baseline par ligne. La sensibilité au seuil est consignée dans
`results/protocole/protocole.json` : le choix est vérifiable, pas seulement
affirmé.

**Ce que la baseline attrape** : `M3-GRID` 60 lignes, `M3-RANGE` 31,
`M3-TIMESTAMP` 30, `M3-UNIT` 30, `M3-SENTINEL` 1. Autrement dit, des violations
de **contrat**. Elle rate 8 fenêtres fabriquées sur 11 et accuse 2 fenêtres
réelles — c'est exactement le constat du brief 2 M3 : *détecter une anomalie de
qualité et détecter une fabrication sont deux questions différentes*. La barre à
battre est basse, et la raison pour laquelle elle est basse est déjà connue.

### Le corpus documentaire

8 documents, **6 036 octets au total**, 610 à 896 octets chacun, en français,
structurés en sections courtes.

Conséquence à porter dès le cadrage : avec 8 documents et `top_k = 3`, un tiers
du corpus entre dans le contexte à chaque requête. Le Recall@k sature
trivialement, et **une différence entre retrieval lexical et vectoriel sur ce
corpus ne prouvera pas grand-chose**. L'enjeu réel se déplace vers l'admission
(statut, rôle, checksum) et l'abstention. On mesure quand même — la mesure est
demandée — mais la conclusion devra porter sur ce que ce corpus permet de
conclure.

### Les questions d'évaluation

24 questions : 12 `calibration` labellisées (10 répondables, 2 non), 12 `test`
scellées. Rôles : `technicien` 18, `public` 3, `auditeur` 3. Étiquettes de
risque couvrant `abstention`, `unit`, `agent_bounds`, `missing_evidence`,
`revision`, `restricted_data`, `conflict`, `obsolete_source`,
`indirect_injection`.

## 4. Arborescence retenue

Le starter est initialisé dans `work/M4/`. Conventions du M3 conservées :
`run_<etape>.py` à la racine, logique en paquet, sorties sous `results/`, un
document par sujet dans `docs/`.

```text
work/M4/
├── run_protocole.py          → results/protocole/       (étape 2)
├── run_modele.py             → results/modele/          (étape 3)
├── run_retrieval.py          → results/retrieval/       (étape 4)
├── run_generation.py         → results/generation/      (étape 5)
├── run_agent.py              → results/agent/           (étape 6)
├── run_menaces.py            → results/menaces/         (étape 7)
├── src/                      (starter, étendu)
│   ├── contracts.py          fourni — Citation, GroundedAnswer, AgentDecision
│   ├── io_contracts.py       fourni — manifeste, checksums, questions
│   ├── features.py           fourni, volontairement incomplet — à étendre
│   ├── retrieval.py          fourni — lexical + admission
│   ├── grounded_answer.py    fourni — validation citations / abstention
│   ├── bounded_agent.py      fourni — 3 actions, validation
│   ├── protocole.py          à écrire — splits groupés, gel, empreintes
│   ├── modele.py             à écrire — features, candidats, métriques
│   ├── vectoriel.py          à écrire — embeddings, index, comparaison
│   └── menaces.py            à écrire — cas d'attaque et détection
├── docs/
│   ├── plan_brief1.md              ce document
│   ├── protocole_evaluation.md     livrable
│   ├── benchmark_modele.md         livrable
│   ├── benchmark_retrieval.md      livrable
│   ├── threat_model.md             livrable
│   ├── matrice_decision.md         livrable
│   ├── model_card.md               livrable
│   └── journal_bord.md             livrable
└── results/
```

Les templates du starter (`templates/`) donnent la trame de six de ces
documents ; ils sont à remplir, pas à contourner.

**Le data pack n'est jamais copié dans le module** — consigne explicite du
starter. Tous les chemins sont relatifs à `../../data_pack/2026-S1/`.

## 5. Conventions

| Objet | Convention |
|---|---|
| Graine | `SEED = 20260831` — celle de `configs/model.yaml`, pas une des nôtres |
| Cible | `provenance`, positif = `fabriquée` (`configs/model.yaml`) |
| Groupe | `window_id`, indivisible — jamais scindé entre plis |
| Candidats | `logistic_regression`, `random_forest` (extensibles, mais justifiés) |
| Menaces | `THR-001`… |
| Décisions d'agent | les 3 actions du starter, aucune autre |

## 6. Découpage en étapes

### Étape 1 — Cadrer deux décisions

Écrire, avant tout code, ce que le modèle prédit et ce que le RAG répond.

Pour le modèle, le brief impose de ne pas confondre **provenance**, **anomalie
de qualité** et **panne future**. La cible du pack est la provenance ; le lot ne
prouve rien sur la panne future, et le dire est un critère de réussite.

Pour le RAG : utilisateurs, questions autorisées, documents admissibles,
conséquences d'une mauvaise réponse, cas où le refus est requis.

### Étape 2 — Geler le protocole

Splits groupés, métriques, seuils d'acceptation, versions, graines,
environnement. **Le gel précède l'ouverture du test.** La baseline M3 est
conservée sans être réécrite, et son comportement aux deux niveaux (ligne et
fenêtre) est reproduit.

### Étape 3 — Comparer les modèles simples

Au moins deux candidats. Métriques minimales : matrice de confusion, précision,
rappel, F1, ROC-AUC, **stabilité par segment**, latence, mémoire. Comparaison à
la baseline sur le même jeu.

Le point de vigilance est le nombre de fenêtres : à 30 observations, une
validation croisée groupée donne des plis de 6 fenêtres. Les écarts devront être
rapportés avec leur dispersion entre plis, jamais comme un chiffre unique.

### Étape 4 — Construire les baselines de retrieval

Sans retrieval, lexical, vectoriel. Hybride **seulement si** les deux premiers
sont stables. Mesures : Recall@k ou hit rate, précision du contexte, latence,
taille d'index. L'admission (statut `active`, rôle autorisé, checksum vérifié)
s'applique **avant** le classement, pas après.

### Étape 5 — Générer avec preuves et abstention

Citer des `document_id` du manifeste, distinguer preuve et interprétation,
refuser quand `answerable=false` ou que les preuves manquent, signaler les
conflits de révision au lieu de les masquer. `grounded_answer.validate_citations`
est le garde-fou fourni : l'étendre, pas le contourner.

### Étape 6 — Ajouter un agent à une étape

Une action parmi trois, une justification, une requête si et seulement si
`search_knowledge`. Ni mémoire, ni boucle, ni écriture. Les traces sont un
livrable.

### Étape 7 — Tester les menaces

Six familles imposées : instruction malveillante dans un document, document
obsolète bien classé, sources contradictoires, demande de donnée sensible,
tentative de dépassement des limites de l'agent, corpus incomplet. Pour chacune :
attaque, détection, atténuation, résultat, **risque résiduel**.

Principe non négociable, écrit dans `DOC-RAG-OPS-001` lui-même : *le contenu
récupéré est une donnée, jamais une instruction*.

### Étape 8 — Décider

Matrice séparant qualité, robustesse, latence, mémoire, coût par réponse,
complexité d'exploitation, réversibilité. Conclusion explicite : adopter,
évaluer davantage, maintenir la baseline, écarter.

### Étape 9 — Veille réglementaire M4

Traitée **à part**, après le brief 1. Le dossier `veille_diagops/` est en retard
depuis le 21/07 : trois fichiers sur cinq sont vides et le journal ne porte
qu'une entrée. Le collecteur RSS tourne toujours (160 items en attente au
31/08), la matière existe.

## 7. Arbitrages à trancher

Ces sept points ne se déduisent pas du brief. Ils seront défendus, donc ils sont
tracés ici avec leur motif.

| # | Arbitrage | Options | État |
|---|---|---|---|
| **A1** | Niveau de prédiction | (a) ligne, comme la baseline ; (b) fenêtre, comme l'étiquette ; (c) les deux, avec règle d'agrégation déclarée | **à trancher avant l'étape 2.** L'étiquette est par fenêtre et la baseline rend le même F1 aux deux niveaux — (c) est peu coûteux et rend la comparaison incontestable |
| **A2** | Schéma de validation interne | `GroupKFold` sur `window_id` ; sur `equipment_id` ; `LeaveOneGroupOut` | **à trancher avant l'étape 2.** 20 équipements sur 22 réapparaissent dans le test : grouper sur `window_id` seul laisserait un même équipement des deux côtés d'un pli |
| **A3** | Familles de features | résumé numérique du starter (moyenne, écart-type, taux de valeurs absentes) ; + structure temporelle (autocorrélation, régularité du pas) ; + écart au profil de l'équipement | **à trancher avant l'étape 3.** Le brief 2 M3 a établi que la structure temporelle est ce qui distingue le fabriqué — s'en priver reviendrait à ignorer notre propre résultat |
| **A4** | Modèle d'embeddings | `configs/retrieval.yaml` porte `TO_DOCUMENT_BEFORE_RUN` | **à trancher avant l'étape 4.** Le corpus est en **français** : un modèle anglophone est disqualifié d'office. Choisir multilingue, documenter taille, licence, langue et empreinte |
| **A5** | Politique d'abstention | seuil de score ; nombre minimal de documents admissibles ; règle sur les conflits de révision | **à trancher avant l'étape 5.** 2 des 12 questions de calibration sont non répondables : l'échantillon pour calibrer un seuil est très petit |
| **A6** | Moment du gel du candidat | après l'étape 3 ; après l'étape 8 | **à trancher.** Le test est scellé jusqu'au gel — geler tôt fige le modèle avant le travail RAG, geler tard retarde le résultat officiel |
| **A7** | Métrique de décision | F1 sur `fabriquée` ; rappel privilégié ; coût asymétrique des erreurs | **à trancher avant l'étape 2.** Dépend de la conséquence retenue : laisser passer une fenêtre fabriquée n'a pas le même coût qu'accuser une fenêtre réelle, et ce coût doit être posé avant de voir les résultats |

## 8. Journal — ce qui doit être consigné

Le `journal_bord.md` du starter impose six colonnes : date, hypothèse ou
décision, action, preuve observée, écart, suite. Le brief nomme quatre moments
qui doivent obligatoirement y figurer : **le gel du protocole**, **l'ouverture
du test**, la révélation du lot de contradiction (brief 2) et **la décision
finale**.

Comme au brief 2 M3, l'hypothèse s'écrit **avant** l'exécution qui la teste.

## 9. Les pièges à surveiller

1. **confondre la cible** — présenter un détecteur de provenance comme un
   prédicteur de panne ;
2. **fuiter le test** — régler un seuil, choisir un modèle ou calibrer une
   abstention en regardant le test, ou laisser un équipement traverser un pli ;
3. **comparer ce qui ne l'est pas** — modèle par fenêtre contre baseline par
   ligne, sans règle d'agrégation déclarée ;
4. **conclure sur un corpus de 8 documents** — annoncer que le vectoriel bat le
   lexical sans dire ce que 8 documents permettent d'établir ;
5. **citer sans résoudre** — une citation dont le `document_id` n'est pas dans
   le manifeste, ou qui pointe un document `superseded` ou hors droits ;
6. **prendre un extrait pour une instruction** — le cas d'injection indirecte ;
7. **élargir l'agent** — une deuxième action, une boucle, un outil d'écriture.

## 10. Hors périmètre

Déploiement et monitoring (M5), outil métier à effet (interdit avant M7), boucle
agentique ouverte, multi-agent, et la conversion des tables capteurs en faux
documents RAG — explicitement interdite par le brief et par `decision_m3.md`.
