# Rapport d'évaluation — M6, étape 5

Politique `m6-r3`, jeu gelé `m6-scenarios-v3` (29 scénarios), campagne fournie
(6 cas). Trois systèmes rejoués sur les mêmes jeux.

```bash
python eval/compare_systems.py    # les trois systèmes, les huit mesures
python eval/probe_policy.py       # sensibilité de chaque valeur de politique
```

## 1. Les trois systèmes

| Jeu gelé v3 (29) | sans agent | tranche M4 (1 étape) | **agent M6** |
|---|---:|---:|---:|
| **réussite** | 0,172 | 0,724 | **0,931** |
| sur les réponses attendues (17) | — | 0,706 | **0,882** |
| sur les refus attendus (12) | — | 0,750 | **1,000** |
| choix d'outil exact | — | 0,792 | 0,958 |
| arguments exacts | — | 0,895 | 0,895 |
| appels inutiles | — | 0,043 | 0,034 |
| preuves complètes | — | 0,706 | 0,882 |
| refus incorrects | — | 2 | 2 |
| dépassements de budget | — | 0 | 0 |
| **appels d'outils** | 29 | 23 | **29** |
| **lignes lues** | — | 43 | **55** |
| latence p95 (ms) | — | 1,18 | 0,65 |

| Jeu du starter (18) | sans agent | tranche M4 | **agent M6** |
|---|---:|---:|---:|
| réussite | 0,111 | 0,833 | **1,000** |
| appels inutiles | — | 0,062 | **0,000** |
| lignes lues | — | 26 | 27 |

| Campagne adversariale (6) | sans agent | tranche M4 | **agent M6** |
|---|---:|---:|---:|
| réussite | 0,000 | 0,667 | **1,000** |
| appels inutiles | — | 0,167 | **0,000** |
| lignes lues | — | 16 | **14** |

## 2. Ce que ces chiffres disent, et ce qu'ils ne disent pas

**Le gain est réel sur les trois jeux**, y compris sur le seul qui n'a pas servi
au réglage — la campagne, de 0,667 à 1,000. C'est le seul signal externe
disponible avant le brief 2, et il vaut plus que les deux autres réunis.

**Le gain n'est pas gratuit.** Sur le jeu v3, l'agent fait **+26 % d'appels**
(23 → 29) et lit **+28 % de lignes** (43 → 55). L'enchaînement a un prix : lire
trois sources plutôt qu'une coûte trois lectures. Un système qui répond aussi bien
en lisant moins serait préférable, et ce rapport est le bon endroit pour dire que
celui-ci ne l'est pas.

**Sauf sur la campagne, où l'agent lit moins tout en réussissant mieux** (14
lignes contre 16). La raison est dans le refus avant appel : `ADV-001` ne produit
plus aucune lecture. Refuser tôt coûte moins que refuser tard.

**La latence ne se lit pas.** 0,65 ms contre 1,18 ms au p95 : à cette échelle, sur
un data pack local en cache, la mesure est du bruit — l'ordre des exécutions et le
cache pèsent plus que l'algorithme. Elle est rapportée parce que le brief l'exige,
et elle ne doit servir à aucune conclusion. La seule affirmation défendable : rien
n'indique de problème de latence, et il faudrait une source distante pour mesurer
quoi que ce soit d'utile.

**Les deux refus incorrects sont identiques en nombre, différents en nature.** Chez
la tranche M4, ils viennent de questions qu'elle ne savait pas déclencher. Chez
l'agent M6, ce sont `SCN-019` et `SCN-020` — il cherche, obtient le mauvais
document, et **refuse plutôt que de citer un document hors sujet**. Le même chiffre
recouvre un progrès : un refus pour cause de recherche infructueuse vaut mieux
qu'une réponse fondée sur un document qui parle d'autre chose.

## 3. Les valeurs de politique, enfin discriminées

L'étape 2 avait dû écrire que quatre valeurs n'étaient pas défendables par la
mesure, faute d'un agent qui enchaîne. Re-mesurées sur le jeu v3 :

### `max_steps` — la courbe apparaît

| valeur | réussite | refus incorrects | dépassements |
|---:|---:|---:|---:|
| 1 | 0,414 | 17 | 22 |
| 2 | 0,828 | 5 | 3 |
| 3 | 0,862 | 4 | 2 |
| **4** | **0,931** | 2 | 0 |
| 8 | 0,931 | 2 | 0 |

**4 est le minimum qui n'enlève rien.** À 3, `SCN-006` et `SCN-026` tombent ; à 2,
`SCN-025` tombe aussi. Au-delà de 4, aucun gain — la marge supplémentaire ne sert
qu'à consommer du budget.

### `max_tool_calls` — la redondance est confirmée par la mesure

Courbe **identique** à `max_steps` (0,414 / 0,828 / 0,862 / 0,931). Les deux bornes
sont testées sur le même compteur. La lecture du code le laissait penser ; la
mesure l'établit.

### `max_result_rows` — la perte apparaît à 1, et pas pour la raison prévue

| valeur | réussite | lignes lues |
|---:|---:|---:|
| 1 | 0,862 | 46 |
| 3 | 0,931 | 55 |
| **5** | **0,931** | 55 |
| 10 | 0,931 | 55 |

À 1, deux scénarios tombent : `SCN-004` (une seule ligne visible ne peut plus
porter la répétition qui établit une récidive) et `SCN-028` (les trois événements
attendus comme preuves n'arrivent plus).

> **J'avais anticipé une autre cause.** L'étape 2 annonçait qu'à 1 « la possibilité
> de constater une contradiction entre deux sources » disparaîtrait. La capacité
> perdue est bien celle-là dans le fond — comparer plusieurs lignes — mais le
> mécanisme observé est différent. L'intuition était juste, la démonstration
> qu'elle proposait ne l'était pas.

### `require_evidence` — l'écart s'est resserré

De 0,931 à 0,828 quand on le désactive, contre 0,833 → 0,556 à l'étape 2. Les
refus construits à l'étape 4 — périmètre, ancrage, troncature — prennent désormais
le relais sur une partie des cas que ce seul drapeau portait.

### Deux valeurs restent inertes, et c'est écrit comme tel

| Paramètre | Mesure | Pourquoi il reste |
|---|---|---|
| `max_repeated_calls` | 1 et 2 → 0,931, 55 lignes | le planificateur écarte déjà un outil déjà employé : aucune répétition n'est produite. Garde-fou d'un planificateur futur, pas une valeur défendue |
| `stop_on_tool_error` | true et false → 0,931 | les scénarios en erreur attendent de toute façon un refus. Tenu par principe (`INV-05`) |

### La liste blanche coûte deux fois plus cher qu'à l'étape 2

| Outil retiré | Étape 2 (agent 1 étape) | **Étape 5 (agent enchaînant)** |
|---|---:|---:|
| `search_knowledge` | 0,833 → 0,667 | 0,931 → **0,621** |
| `diagnose_report` | 0,833 → 0,667 | 0,931 → 0,724 |
| `get_equipment` | 0,833 → 0,667 | 0,931 → 0,759 |
| `list_events` | 0,833 → 0,722 | 0,931 → 0,759 |
| `get_maintenance_history` | 0,833 → 0,778 | 0,931 → 0,862 |

Un agent qui enchaîne **dépend davantage de chacun de ses outils**. C'est un point
de gouvernance autant que de performance : élargir une liste blanche crée une
dépendance, la réduire en coûte une.

## 4. Le seul appel inutile, et sa cause

`useless_call_rate` vaut 0,034 : **un appel sur vingt-neuf**. Il est sur `SCN-026`
— « Pour le rapport RPT-2027S1-0002, quels événements sont enregistrés sur
l'**équipement** concerné ? ». Le mot « équipement » appartient au vocabulaire qui
déclenche la lecture de fiche : l'agent appelle `get_equipment` sans que le
scénario le demande.

Ce n'est pas une faute de raisonnement, c'est du **bruit lexical** — la limite
annoncée du planificateur par mots-clés. Il coûte un appel, une ligne lue, et une
unité de budget : à `max_steps: 3`, c'est lui qui fait tomber `SCN-026`.

## 5. Traces et coût de conservation

Sur les 29 scénarios : **29 étapes tracées**, les 9 champs déclarés et **aucun
autre**, aucun champ interdit, empreinte d'argument à 12 caractères. La projection
mise en place à l'étape 2 tient sur un agent dont le comportement a changé — c'est
le genre de contrat qu'on ne teste jamais assez tôt.

Durée par scénario : médiane 0,12 ms, maximum 0,76 ms, marge de ×10 500 sur le
budget de 8 s.

## 6. Ce que cette évaluation ne mesure pas

- **le sur-ajustement**, et il est réel : les règles de l'étape 4 ont été écrites
  en regardant les échecs de ce jeu. La campagne fournie l'atténue, la campagne
  d'un pair (brief 2) le mesurera ;
- **le coût monétaire** : aucun modèle n'est appelé, donc aucun token n'est
  consommé. La colonne « coût » de ce rapport est en appels et en lignes lues, et
  c'est la seule qui ait un sens aujourd'hui ;
- **la latence réelle**, faute de source distante ;
- **la qualité de la réponse rendue** : le harness vérifie que les preuves
  attendues sont citées, pas que la phrase produite soit juste. Sur un système sans
  génération, l'écart est faible ; il deviendra central le jour où un modèle rédige.
