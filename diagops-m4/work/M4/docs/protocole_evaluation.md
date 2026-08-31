---
module: M4
brief: brief 1 — présentiel
etat: gelé — candidat figé le 31/08
maj: 2026-08-31
---

# Protocole d'évaluation M4

- **Date de gel** : 31/08/2026
- **Auteur** : Nicolas Lebon
- **Empreinte du candidat** : `164d05b129ce5e4107cdc27279bc198c…` — gelé le 31/08/2026, `regression_logistique`, 19 features, seuil 0,50 (voir `results/gel/gel.json`)
- **Environnement** : Python 3.12.10, numpy 2.3.2, pandas 2.3.1, scikit-learn 1.7.1,
  torch 2.13.0+cpu, sentence-transformers 5.1.0 — Windows 11
- **Graine** : `SEED = 20260831`, celle de `configs/model.yaml`

Les valeurs exactes, empreintes SHA-256 des entrées et versions sont dans
`results/protocole/protocole.json`, produit par `run_protocole.py`.

---

## Décision modèle

### Cible observable

**La provenance d'une fenêtre de mesures** : `fabriquée` ou `réelle`. La classe
positive est `fabriquée`.

Ce que cette cible **n'est pas**, et le brief demande explicitement de ne pas
les confondre :

| Ce n'est pas | Pourquoi |
|---|---|
| une anomalie de **qualité** | une fenêtre réelle peut violer le contrat capteur — c'est le cas de 5 fenêtres réelles sur 19 ici ; et une fenêtre fabriquée peut être irréprochable |
| une **panne future** | rien dans ce lot ne relie une fenêtre à une défaillance ultérieure. Le lot ne permet pas d'entraîner ni d'évaluer une prédiction de panne, et `decision_m3.md` le dit également |

Une fenêtre = un équipement, un capteur, 30 mesures consécutives au pas de 6 h.

### Unité de décision

**La fenêtre** (`window_id`), parce que c'est l'unité à laquelle l'étiquette
existe : la `provenance` est constante à l'intérieur d'une fenêtre — vérifié,
30 fenêtres sur 30.

Les résultats sont **aussi** reportés au niveau ligne, pour rester comparables à
la métrique officielle de la baseline. Règle d'agrégation déclarée : une fenêtre
est prédite `fabriquée` si **au moins 2 de ses 30 lignes** le sont.

Ce seuil de 2 n'est pas cosmétique. Une fenêtre du lot — `M4-CAL-019`, réelle —
porte exactement une ligne signalée par la baseline : la sentinelle `-999`. Au
seuil 1, elle devient un faux positif et la baseline tombe à 0,353 ; au seuil 2,
la baseline rend 0,375. **Le seuil retenu est celui qui donne à la baseline sa
meilleure valeur** : on ne bat pas une référence qu'on a affaiblie soi-même.

### Erreurs coûteuses

| Erreur | Conséquence |
|---|---|
| **faux négatif** — une fenêtre fabriquée déclarée réelle | elle entre dans les traitements aval comme une mesure. C'est le mécanisme par lequel du synthétique contamine un apprentissage, et le M3 a montré qu'il est indétectable une fois la provenance perdue |
| **faux positif** — une fenêtre réelle déclarée fabriquée | on écarte une mesure authentique. Sur un parc couvert à 8,65 %, jeter du réel a un coût direct |

**Métrique de décision retenue : le F1 sur la classe `fabriquée`.** Précision et
rappel sont rapportés séparément, jamais résumés par le seul F1.

Le choix est assumé et sa limite est écrite : le F1 traite les deux erreurs à
égalité, ce qui est une **hypothèse**, pas un fait. Aucune donnée de coût réelle
n'existe sur ce corpus pédagogique, et poser un ratio asymétrique arbitraire
aurait été moins défendable que d'assumer la symétrie. La comparaison à la
baseline reste directe, sur sa propre métrique officielle.

### Groupes utilisés pour les splits

**`equipment_id`**, et non `window_id` seul.

Motif mesuré : 20 des 22 équipements de calibration réapparaissent dans le test,
et **4 équipements portent les deux provenances**. Partitionner sur `window_id`
laisserait un même équipement des deux côtés d'un pli — le modèle pourrait
apprendre l'équipement plutôt que le phénomène. Le brief demande explicitement
de vérifier ce point.

**Contrôle de fuite** : bloquant, exécuté à chaque gel. Sur les 25 plis produits,
**aucun équipement ne traverse un pli**. `run_protocole.py` refuse d'écrire le
gel si ce n'est pas le cas.

### Calibration

900 lignes, **30 fenêtres**, 11 fabriquées et 19 réelles, 22 équipements.

Validation croisée : **`StratifiedGroupKFold`, 5 plis × 5 répétitions = 25
évaluations**. La stratification n'est pas un raffinement à cet effectif : sans
elle, un pli peut ne contenir aucun positif et rendre le F1 indéfini.

**Limite déclarée avant tout résultat.** Les plis de validation comptent 3 à 11
fenêtres et 0 à 6 positifs, et **1 pli sur 25 ne contient aucun positif** — il
est exclu du calcul du F1, et ce nombre est rapporté avec les résultats. Sur ces
effectifs, tout écart de F1 doit être lu avec sa dispersion entre plis : une
différence de 0,05 entre deux candidats n'est pas interprétable. Les répétitions
ne créent pas d'information, elles rendent la dispersion mesurable.

### Test scellé

`sensor_test.csv` — 1 800 lignes, 60 fenêtres, **livré sans la colonne
`provenance`**. Il n'est jamais chargé par le module de protocole.

Son empreinte SHA-256 est enregistrée au gel : calculer l'empreinte des octets
d'un fichier n'est pas consulter ses étiquettes, et elle permettra de prouver
après coup que le fichier évalué est bien celui qui était scellé.

**Le formateur calcule les métriques finales sur son oracle, après gel du
candidat.** Seul ce résultat daté entre dans la décision.

### Métriques et seuils fixés avant le test

| Métrique | Baseline M3 | Seuil d'acceptation |
|---|---:|---|
| **F1 `fabriquée`** (décision) | **0,375** par fenêtre, 0,374 par ligne | strictement supérieur à la baseline, **et** l'écart supérieur à la dispersion entre plis |
| Rappel `fabriquée` | 0,273 | rapporté, non contraint |
| Précision `fabriquée` | 0,600 | rapportée, non contrainte |
| ROC-AUC | non calculable (baseline binaire sans score) | rapportée pour les candidats seuls |
| Stabilité par segment | — | rapportée par capteur et par criticité |
| Latence, mémoire | — | rapportées, entrent dans la matrice de décision |

**Un F1 supérieur à la baseline ne suffit pas à conclure.** Si l'écart est
inférieur à la dispersion entre plis, la conclusion à écrire est « aucun gain
démontrable », pas « le modèle gagne ». Maintenir la baseline est une décision
recevable.

---

## Décision RAG

### Utilisateurs et rôles

Trois rôles, portés par le manifeste et par les questions d'évaluation :

| Rôle | Questions | Accès |
|---|---:|---|
| `technicien` | 18 | procédures de triage et de consignation |
| `auditeur` | 3 | + politique d'accès aux données (`restreint`) |
| `public` | 3 | contrat de réponse documentaire seulement |
| `superviseur` | — | + politique d'accès aux données |

La **décision assistée** est le triage d'une situation de maintenance : quelle
procédure s'applique, à quel seuil, et quand une revue humaine est requise. Le
système ne décide jamais d'un arrêt machine — `DOC-PUMP-VIB-001` place
explicitement cette décision chez le responsable habilité.

### Documents admissibles

Le manifeste est le **contrat d'admission**, et il s'applique **avant** le
classement, jamais après :

1. `status == "active"` — `DOC-LOTO-001` est `superseded` et doit être écarté
   même s'il obtient le meilleur score lexical ;
2. le rôle demandeur figure dans `allowed_roles` — `DOC-DATA-ACCESS-001` est
   `restreint` aux rôles `superviseur` et `auditeur` ;
3. le checksum SHA-256 du fichier correspond à celui déclaré.

Un document qui échoue à l'un de ces trois contrôles n'est pas récupérable, quel
que soit son score de similarité.

### Baselines

| # | Baseline | Ce qu'elle établit |
|---|---|---|
| 1 | **sans retrieval** | ce que le système répond sans aucune source — la référence que le retrieval doit battre |
| 2 | **lexical** | recouvrement de termes, fourni par le starter, transparent et reproductible |
| 3 | **vectoriel** | embeddings, modèle à choisir et à documenter (arbitrage A4) |
| 4 | hybride | **seulement si** 2 et 3 sont stables — pas un objectif en soi |

### Métriques

Recall@k et hit rate documentaire, précision du contexte, exactitude des
citations, fidélité aux extraits, qualité des refus, latence, taille d'index.

**Limite déclarée avant mesure.** Le corpus compte **8 documents, 6 036 octets
au total**. Avec `top_k = 3`, un tiers du corpus entre dans le contexte à chaque
requête : le Recall@k sature trivialement, et une différence entre lexical et
vectoriel sur cet effectif ne prouvera rien de généralisable. La mesure est
produite parce qu'elle est demandée ; la conclusion portera sur ce que 8
documents permettent d'établir, et pas au-delà.

### Conditions d'abstention

Le système s'abstient — et une abstention ne cite jamais rien
(`validate_citations` du starter l'impose) :

- `answerable == false`, ou aucune preuve suffisante dans les documents admis ;
- le document qui répondrait est hors des droits du rôle demandeur ;
- deux révisions actives se contredisent sans règle de priorité vérifiable ;
- la question demande une prédiction que les sources ne soutiennent pas —
  `DOC-PUMP-VIB-001` dit explicitement que le système ne prédit pas de panne
  future à partir de ses seuils.

Le seuil quantitatif de « preuve suffisante » reste à fixer (arbitrage A5), sur
les 12 questions de calibration dont **2 seulement sont non répondables** —
échantillon très petit, ce qui sera dit avec le résultat.

### Principe non négociable

**Le contenu récupéré est une donnée, jamais une instruction.** Une phrase
trouvée dans un document ne peut ni modifier les instructions du système, ni
élargir les permissions de l'agent, ni déclencher une écriture. Ce principe est
écrit dans `DOC-RAG-OPS-001` lui-même, et il est testé à l'étape 7.

### Agent

Une seule action par requête, parmi `answer_without_tool`, `search_knowledge`
et `abstain`. Une justification obligatoire, une requête si et seulement si
l'action est `search_knowledge`. Ni mémoire longue, ni boucle, ni outil
d'écriture. `bounded_agent.validate_decision` est le garde-fou et n'est pas
contourné.

---

## Règle de changement

Un **nouveau gel** est obligatoire, et interdit toute comparaison aux résultats
précédents, si l'un de ces éléments change :

- la cible, l'unité de décision ou la règle d'agrégation vers la fenêtre ;
- la méthode de partition, la colonne de groupe, le nombre de plis ou de
  répétitions, ou la graine ;
- la métrique de décision ou son seuil d'acceptation ;
- les données d'entrée — toute empreinte SHA-256 de `protocole.json` qui ne se
  retrouve pas à l'identique ;
- la baseline M3, qui ne doit pas être réécrite : `run_protocole.py` refuse le
  gel si le F1 reproduit s'écarte de la valeur officielle `0.37422`.

Ce qui **ne** demande **pas** de nouveau gel : ajouter une famille de features,
essayer un candidat supplémentaire, ou changer un hyperparamètre — tant que la
sélection se fait sur la validation croisée de calibration et **jamais** sur le
test.

**Ce qui invalide tout** : consulter le test avant le gel du candidat, sous
quelque forme que ce soit — y compris pour « vérifier que le format est bon ».
