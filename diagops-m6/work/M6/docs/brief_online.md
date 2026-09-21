# Brief 1 online — analyser une version en service, la faire évoluer

6 h, sans agent à construire : on reprend ce qui tourne, on qualifie ce qui arrive,
on formule **une** hypothèse, on mesure, on décide.

> Sections 1 à 5 écrites et **commitées avant** que le candidat n'existe.
> Sections 6 et suivantes remplies après mesure.

## 1. La référence, explicitement

| | |
|---|---|
| version en service | stack RAG M5, gelée dans `reference_runs/m5_for_m6/` |
| jeu d'évaluation | `rag_eval/` — **12 questions de calibration**, 10 répondables, 2 non répondables. Les 12 questions du split `test` restent **scellées** et ne sont pas lues |
| métriques annoncées par M5 | hit@3 **1,000** · citations résolubles **1,000** · abstention correcte **1,000** · documents rendus **2,833** |
| gates gelés | hit@3 ≥ **0,80** · citations résolubles ≥ **1,00** · abstention correcte ≥ **1,00** · ≥ **7** documents |
| environnement | Python 3.12, `requirements.lock` (pytest, PyYAML), aucun appel externe, corpus local de 7 documents |
| limites déclarées | référence extractive et déterministe, sans poids de modèle ; latence et coût non gelés, mesurés sur le poste |

**La fonction de score de référence n'est pas réimplémentée** : elle est importée
de `m5_for_m6/baseline/retrieval.py`, telle que le formateur l'a livrée. Comparer
à une copie de mémoire, c'est comparer à ce dont on se souvient.

## 2. Les nouvelles données — période 2027-S1

60 rapports dérivés et 124 retours. Qualification des retours : voir
`docs/qualification_feedback.md` (étape 6). Ici, les **rapports**.

| | 2026-S1 | **2027-S1** |
|---|---:|---:|
| rapports | 40 | 60 |
| équipements distincts | 30 | **49** |
| longueur de note — min / médiane / max | 145 / 176 / 215 | **34 / 105 / 156** |
| `event_id` renseigné | **40 / 40 (100 %)** | **6 / 60 (10 %)** |

| Canal | 2026-S1 | 2027-S1 |
|---|---:|---:|
| `mobile_app` | 18 | 20 |
| `web_form` | 18 | 12 |
| `radio_transcript` | 4 | 10 |
| **`sms_gateway`** | **0** | **18** |

**Provenance** : les deux périodes sont des données **dérivées** du même parc
synthétique — aucune n'est réelle, aucune n'est augmentée. Le contrat de
provenance instauré au M3 ne s'applique pas aux rapports, qui ne sont pas des
mesures ; il n'y a donc rien à distinguer ici, et c'est écrit pour qu'on ne le
cherche pas.

## 3. Rapport de dérive

Trois dérives, et une seule casse quelque chose.

**D1 — un canal nouveau, et des notes plus courtes.** `sms_gateway` apparaît avec
18 rapports (30 % de la période) ; la médiane de longueur tombe de 176 à 105
caractères. C'est une dérive de **distribution d'entrée**, pas une dérive de
concept : le parc n'a pas changé, la façon de le décrire si.

**D2 — le rattachement à un événement s'effondre : 100 % → 10 %.** C'est la dérive
qui a un effet mesurable. `diagnose_report` dérive `severity_hint` de l'`event_id`
du rapport : sans lui, l'indice vaut `unknown`.

| | 2026-S1 | 2027-S1 |
|---|---:|---:|
| `severity_hint: unknown` | **0 %** | **90 %** |

Le système continue de répondre, avec un champ systématiquement vide, et **rien ne
le signale**. C'est le motif du M5 — un dispositif qui ne dit pas qu'il ne sait
plus — transposé à une sortie d'outil.

**D3 — l'extraction de symptômes ne se dégrade pas**, contrairement à ce que
j'attendais des notes courtes : 22 % de symptômes non qualifiés en 2026, **17 %**
en 2027. Et le détail contredit l'intuition :

| Canal 2027 | Symptômes non qualifiés |
|---|---|
| **`sms_gateway`** | **0 / 18** |
| `mobile_app` | 2 / 20 |
| `web_form` | 4 / 12 |
| `radio_transcript` | 4 / 10 |

**Les SMS sont les mieux qualifiés du lot.** Une note courte va droit au symptôme ;
ce sont les transcriptions radio et les formulaires web qui décrivent en contournant
le vocabulaire attendu (« écart de 7 °C entre la consigne et la mesure », « odeur de
chaud », « alarme thermocouple fugitive »). Hypothèse intuitive **invalidée avant
d'écrire une ligne de code**.

## 4. Ce que le jeu du formateur révèle, et que mon jeu ne voyait pas

Les 12 questions de calibration rejouées à travers le système complet :

| | Référence (score M5) | Candidat retrieval promu |
|---|---:|---:|
| hit@3 | **0,800** | **0,800** |
| citations résolubles | 1,000 | 1,000 |
| abstention correcte (2 q.) | 1,000 | 1,000 |
| **abstentions incorrectes** | **2** | **2** |
| documents rendus | 2,000 | 1,750 |
| gate M5 | PASS | PASS |

Le gate passe — le seuil est à 0,80 — mais **M5 annonçait 1,000 et nous sommes à
0,800**. Deux questions répondables sur dix reçoivent une abstention, et les deux
causes sont différentes :

| Question | Ce qui se passe |
|---|---|
| `RAG-CAL-002` « Quelle vérification supplémentaire est prévue pour un équipement de criticité critique ? » | le plan retenu est `['get_equipment']` — « équipement » et « criticité » déclenchent l'intention fiche — mais aucun identifiant n'est fourni, l'intention est abandonnée, **le plan se vide et aucun outil n'est appelé** |
| `RAG-CAL-008` « Un utilisateur public demande le contenu intégral d'une note restreinte. Quelle réponse faut-il donner ? » | refus **`hors_perimetre`** : la question n'emploie **aucun** mot de ma liste de vocabulaire du domaine |

**Trois sources disent la même chose.** Le jeu du formateur (2 échecs sur 10), le
feedback d'usage (« sur les rapports courts issus du canal SMS, la réponse abandonne
alors que l'équipement est identifiable » — **7 occurrences**), et la fragilité que
j'avais écrite moi-même à l'étape 4 : *une question légitime au vocabulaire
inhabituel est refusée*. Elle est maintenant mesurée.

## 5. Hypothèse, prédictions et protocole

> **Un seul axe : le critère de périmètre.**
>
> Refuser sur l'absence de vocabulaire connu était la seule option tant que le
> corpus répondait à tout — à l'étape 1, cinq questions hors domaine sur cinq
> rendaient trois documents chacune. **Le candidat retrieval promu a changé cela** :
> le corpus se tait désormais sur 5 questions hors domaine sur 5.
>
> Le périmètre peut donc être décidé par **le silence du corpus** plutôt que par une
> liste de mots : l'agent se rabat sur la recherche documentaire quand aucune
> intention structurée n'est servable, et c'est l'absence de document qui fonde le
> refus.

La liste noire — prix, coût, chiffre d'affaires, météo — **reste** : ces demandes
se refusent avant tout appel, sans rien lire.

| # | Prédiction | Pourquoi |
|---:|---|---|
| **R1** | `RAG-CAL-002` et `RAG-CAL-008` passent, hit@3 **0,800 → 1,000** | les deux causes sont couvertes par le repli |
| **R2** | abstentions incorrectes **2 → 0** | conséquence directe |
| **R3** | `SCN-015` et `SCN-021` restent des refus | le corpus se tait sur ces questions — mesuré à l'étape 7 |
| **R4** | le jeu gelé v3 ne régresse pas (0,966) | aucun scénario ne dépend du refus par vocabulaire, sauf via la liste noire, conservée |
| **R5** | les 64 tests restent verts | les quatre cas de `test_refus_avant_tout_appel` passent par la liste noire ou l'instruction |
| **R6** | un appel de plus sur les questions hors domaine sans mot de la liste noire | c'est le coût assumé : une lecture contre deux abstentions incorrectes |

**Protocole** : jeu de calibration rejoué avant et après ; jeu gelé v3 et campagne
rejoués pour la non-régression ; gates M5 appliqués ; segmentation par `risk_tag`
et par rôle pour chercher les régressions locales. Le split `test` n'est pas ouvert.
