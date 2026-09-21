# Politique d'exécution — M6

Version `m6-r2`, dérivée de `m6-baseline-r1` livrée par le starter.

> **Défendre une valeur, ce n'est pas expliquer pourquoi elle paraît raisonnable.**
> C'est montrer ce qui change quand on la déplace. Chaque valeur ci-dessous a été
> mesurée en rejouant le jeu gelé sous une politique dérivée, un paramètre modifié
> à la fois.
>
> Banc : `eval/probe_policy.py` — sortie complète dans
> `results/sensibilite_politique.json`.
>
> ```bash
> python eval/probe_policy.py
> ```

## 1. Ce que la politique fixe

| Paramètre | `r1` | `r2` | Ce qui fixe la valeur |
|---|---:|---:|---|
| `max_steps` | 4 | **4** | plancher du jeu gelé : 3 outils pour `SCN-006`, plus un pour l'effet de bord de la borne (§3.1) |
| `max_tool_calls` | 4 | **4** | redondant avec `max_steps` dans l'implémentation actuelle (§4.2) |
| `max_duration_ms` | 8000 | **8000** | somme des timeouts du plan le plus long : 3 300 ms, majorée ×2,4 (§4.3) |
| `max_repeated_calls` | 1 | **1** | porte sur l'empreinte `{outil + arguments}`, pas sur l'outil (§4.4) |
| `max_result_rows` | 10 | **5** | mesure d'exposition : 26 lignes lues à 5 comme à 10, 23 à 3, 11 à 1 — à réussite constante (§4.5) |
| `stop_on_tool_error` | true | **true** | inerte sur le jeu actuel, tenu par principe (§4.6) |
| `require_evidence` | true | **true** | le mieux défendu : à `false`, 0,833 → **0,556** (§4.7) |
| `treat_tool_output_as_data` | true | **true** | désormais **refusé au chargement** s'il vaut `false` (§3.2) |
| `record_fields` | 8 champs | **9 champs** | désormais **appliqués** : la trace est projetée dessus (§3.3) |
| `forbidden_fields` | 4 champs | **4 champs** | désormais **vérifiés** : leur présence lève (§3.3) |
| `retention_days` | 30 | **30** | dette assumée : rien ne purge (§6) |

## 2. Point de contrôle : aucune régression

| | `m6-baseline-r1` | `m6-r2` |
|---|---:|---:|
| réussite des scénarios | 0,833 | **0,833** |
| choix d'outil exact | 0,889 | **0,889** |
| exactitude des arguments | 0,933 | **0,933** |
| refus corrects / incorrects | 7 / 0 | **7 / 0** |
| dépassements de budget | 0 | **0** |
| tests | 45 | **51** |

Les corrections rendent des bornes applicables ; elles ne changent pas le
comportement mesuré. C'était l'objectif : une politique qui borne réellement, à
comportement constant, avant que l'agent ne soit touché à l'étape 4.

## 3. Cinq paramètres ne bornaient rien

Le constat est le motif du M5 retrouvé ailleurs — *un contrôle qui ne mesure pas
ce qu'il prétend*. Ici : **un paramètre qui ne borne pas ce qu'il déclare**. Les
cinq étaient lus, convertis, stockés dans la `Policy`… et jamais consultés ensuite.

### 3.1 L'effet de bord de `max_steps`, à connaître avant de choisir la valeur

La borne est testée **en début de tour, avant de demander à l'agent s'il voulait
continuer**. Un plan qui consomme exactement `max_steps` appels est donc refusé au
tour suivant, alors qu'il avait terminé.

Mesuré à `max_steps = 1`, sur un agent qui ne fait qu'une étape :

| | Référence | `max_steps = 1` |
|---|---:|---:|
| réussite | 0,833 | **0,444** |
| refus incorrects | 0 | **9** |
| dépassements de budget | 0 | **14** |

Sept scénarios nominaux (`SCN-001` à `SCN-007`, `SCN-016`, `SCN-018`) basculent en
refus. La règle qui en découle : **`max_steps` ≥ nombre d'outils du plan le plus
long + 1**. Le jeu gelé exige 3 outils (`SCN-006`), donc 4.

### 3.2 `treat_tool_output_as_data` ne faisait rien

Le drapeau portait l'invariant `INV-08`. Le passer à `false` ne changeait **aucun**
comportement : le traitement d'un résultat comme donnée est en dur dans le runner.
Un contrôle qu'on peut désactiver sans que rien ne bouge n'est pas un contrôle.

Correction : la politique est **refusée au chargement** si le drapeau vaut `false`,
comme `allow_dynamic_tools`. Le drapeau devient une assertion vérifiable au lieu
d'une déclaration.

### 3.3 Les champs de trace étaient déclarés d'un côté, produits de l'autre

La politique déclarait huit champs. La trace en portait neuf, et pas les mêmes :

| Déclaré, absent de la trace | Présent, non déclaré |
|---|---|
| `step` | `index` (même chose, autre nom) |
| | `instruction_like_content` |

Rien de sensible ne fuyait — les quatre `forbidden_fields` étaient bien absents —
mais le contrat et la réalité divergeaient sur un dispositif dont le seul rôle est
d'être **auditable**. Un auditeur qui compare la politique à la trace trouve deux
écarts sur neuf champs.

Corrections :

- la trace est **projetée** sur `record_fields`, avec `step` comme nom contractuel
  du numéro d'étape. Retirer un champ du YAML le fait disparaître de la trace, sans
  toucher au code — vérifié par `test_champ_trace_non_declare_absent_de_la_trace` ;
- la présence d'un `forbidden_field` **lève** au lieu d'être interdite sur le papier ;
- `instruction_like_content` est **ajouté au contrat**, puisqu'il est tracé et que
  `INV-08` s'appuie dessus.

### 3.4 `max_result_rows` n'était appliqué nulle part

La seule troncature effective venait du `max_results` propre à chaque outil (3 pour
`search_knowledge`, 1 pour `get_equipment`, 10 pour les deux tables). Le plafond de
la politique ne pouvait donc **jamais** être plus restrictif que le contrat de
l'outil — c'est-à-dire qu'il ne servait à rien.

Correction : la coupe est appliquée côté agent, après l'appel. La politique peut
désormais être plus stricte que l'outil, jamais plus permissive.

### 3.5 `retention_days` ne purge rien

Aucun mécanisme n'efface quoi que ce soit à 30 jours. Voir §6 — dette assumée, pas
corrigée.

## 4. Valeur par valeur

### 4.1 `max_steps: 4`

Plancher imposé par le jeu gelé, pas par l'agent. Répartition des outils attendus
sur les 18 scénarios : **3 scénarios à 0 outil** (refus purs), **14 à 1 outil**,
**1 à 3 outils** (`SCN-006`). Avec l'effet de bord du §3.1 : 3 + 1 = **4**.

Entre 2 et 8, **aucune différence mesurable** — l'agent fourni ne fait qu'une étape
(`mean_steps` 0,89). La valeur n'est donc pas défendable par la mesure de
performance aujourd'hui ; elle l'est par le besoin du jeu. **À re-mesurer à l'étape 5**,
quand l'agent enchaînera.

### 4.2 `max_tool_calls: 4`

Redondant : `max_steps` et `max_tool_calls` sont testés sur le **même compteur**
(`len(run.steps)`), donc le minimum des deux gouverne. La distinction n'aura de sens
que le jour où une étape pourra ne pas appeler d'outil. Conservé égal à `max_steps`
plutôt que supprimé, pour que la distinction reste disponible sans changer le
contrat de la politique.

### 4.3 `max_duration_ms: 8000`

Deux contraintes se rencontrent :

- **par le bas** : le budget doit couvrir le plan légitime le plus long, sinon il
  interdit un comportement attendu. `SCN-006` = `diagnose_report` (1 000 ms) +
  `get_equipment` (800) + `search_knowledge` (1 500) = **3 300 ms** de timeouts
  cumulés dans le pire cas ;
- **par le haut** : une valeur trop large ne détecte plus rien. Mesures locales —
  durée médiane par scénario **0,03 ms**, maximum **0,4 ms** : la marge réelle est
  de ×20 000.

8 000 ms = 3 300 × 2,4. La borne ne mord pas aujourd'hui, et **ne doit pas mordre** :
elle protège d'une source distante dégradée, pas du fonctionnement nominal. La
recaler sur les durées observées (par exemple 100 ms) la ferait déclencher au
premier ralentissement bénin, et rendrait `SCN-006` impossible.

> À noter pour l'oral : comme le timeout d'outil (§ registre, 2.3), le contrôle de
> durée s'exécute **en début de tour**, donc après que le temps a été consommé. Un
> budget de durée ne raccourcit pas une exécution lente, il l'empêche de continuer.

### 4.4 `max_repeated_calls: 1`

L'empreinte compte `{outil + arguments}`, vérifié : `list_events` sur `EQ-PUMP-001`
et sur `EQ-PUMP-002` produisent deux empreintes différentes. La valeur 1 interdit
donc le **rappel strictement identique** — la répétition coûteuse d'`ADV-004` — sans
gêner un plan qui interroge deux équipements.

Inerte sur le jeu actuel (l'agent ne répète jamais : à 1 comme à 2, 0,833 et
26 lignes lues). À re-mesurer à l'étape 5.

### 4.5 `max_result_rows: 5` — la seule valeur modifiée

Ce paramètre ne gouverne pas la performance. Il gouverne **la donnée lue**.

| `max_result_rows` | Lignes lues sur le jeu | Réussite | Échecs |
|---:|---:|---:|---|
| 1 | 11 | 0,833 | `SCN-006`, `SCN-013`, `SCN-014` |
| 3 | 23 | 0,833 | les mêmes |
| 5 | **26** | 0,833 | les mêmes |
| 10 | 26 | 0,833 | les mêmes |

Lecture : **10 était sans effet** (aucun outil ne rend plus de 10 lignes) et 1
diviserait la donnée lue par 2,4 sans perdre un scénario.

Pourquoi ne pas descendre à 1, alors ? Parce que la réussite mesure ce que le jeu
gelé sait voir aujourd'hui, et pas ce que le gate exige :

- à **1**, l'agent ne reçoit qu'un document par recherche — il devient **incapable de
  constater une contradiction entre deux sources**, ce que demande `INV-09` et ce que
  `SCN-016` exerce ;
- à **3**, l'historique de maintenance est coupé à 3 interventions sur 14 pour
  `EQ-PUMP-001`, alors que le contrat de l'outil prévient qu'*une récidive ne se
  déduit pas d'un historique tronqué*.

**5** est le plus petit plafond qui n'enlève rien : il correspond exactement à ce que
l'agent demande (`limit: 5`), il rend la borne active comme plafond de sécurité, et
il laisse l'arbitrage entre sources possible.

> **Décision prise pour toi, à valider ou amender.** Si la minimisation prime sur la
> complétude du jugement, 3 est mesurément gratuit aujourd'hui (−12 % de données
> lues, zéro scénario perdu). Le coût est ailleurs : un historique de maintenance
> réduit au tiers.

### 4.6 `stop_on_tool_error: true`

**Inerte sur le jeu actuel** : à `false`, la réussite reste 0,833. Les scénarios qui
produisent une erreur d'outil (`SCN-011` indisponible, `SCN-012` timeout) attendent
de toute façon un refus, et l'agent refuse ensuite faute de preuve.

Conservé par principe — `INV-05` — et non par la mesure : continuer après une erreur,
c'est répondre sur une preuve partielle sans le dire. Le jour où l'agent enchaînera
plusieurs outils, ce drapeau décidera si une deuxième source peut compenser l'échec
de la première. À re-mesurer alors.

### 4.7 `require_evidence: true`

Le paramètre le mieux défendu de la politique.

| | Réussite | Scénarios perdus |
|---|---:|---|
| `true` | 0,833 | — |
| `false` | **0,556** | `SCN-008`, `SCN-009`, `SCN-010`, `SCN-014`, `SCN-015`, `SCN-017` |

Six scénarios de refus basculent en réponses non fondées. C'est ce seul drapeau qui
transforme « je n'ai rien trouvé » en abstention explicite.

### 4.8 Le budget de tokens, qui n'existe pas

Le brief demande « budget de tokens et durée ». La politique n'a **pas** de budget de
tokens, et c'est cohérent : aucun composant de l'agent n'appelle de modèle génératif.
Le nombre de tokens consommés est structurellement nul.

Dette explicite : **introduire un LLM dans le plan ou la rédaction de la réponse rend
ce budget obligatoire**, et il devra être borné avant, pas après. Consigné ici pour
qu'on ne découvre pas le manque au moment de l'ajout.

## 5. La liste blanche — ce que coûte chaque autorisation

| Outil retiré | Réussite | Refus incorrects |
|---|---:|---:|
| `diagnose_report` | 0,667 | 3 |
| `get_equipment` | 0,667 | 2 |
| `search_knowledge` | 0,667 | 2 |
| `list_events` | 0,722 | 1 |
| `get_maintenance_history` | 0,778 | 1 |

**Aucune autorisation n'est gratuite** : chaque outil est exercé par au moins un
scénario, et son retrait se paie. C'est la justification demandée par le brief —
une liste blanche se défend par ce que coûte le retrait de chaque ligne, pas par
l'intention de celui qui l'a écrite.

Le rôle retenu est `technicien`, le plus restreint des trois rôles opérationnels :
il ne voit pas `DOC-DATA-ACCESS-001` (restreint), ce qui est précisément la
situation que `SCN-013` et `SCN-014` mettent à l'épreuve.

## 6. Traces, minimisation et la dette de rétention

Ce que la trace contient réellement, vérifié sur 16 étapes du jeu gelé :

- les 9 champs déclarés, sous leur nom contractuel, et **aucun autre** ;
- **aucun** des 4 champs interdits ;
- l'empreinte d'argument fait **12 caractères** (SHA-256 tronqué) : assez pour prouver
  que deux appels étaient identiques, pas assez pour relire la valeur ;
- aucun identifiant d'équipement en clair — vérifié par le test du starter.

**La dette** : `retention_days: 30` ne purge rien. Un agent qui ne stocke pas ne peut
pas purger ; la rétention appartient à ce qui écrit `results/*.jsonl`. Deux voies,
aucune retenue à ce stade :

1. une purge dans le harness, au démarrage — simple, mais elle efface des preuves
   d'évaluation en même temps que des traces d'exploitation ;
2. une purge dans le pipeline de déploiement M5, côté volume — cohérent avec
   l'architecture, hors périmètre du brief 1.

Écrite ici pour qu'elle ne disparaisse pas : **une durée de rétention annoncée et non
appliquée est une promesse réglementaire non tenue**, et c'est exactement le genre de
point que le checkpoint de veille (étape 8) doit reprendre.

## 7. Ce qui n'est pas encore défendable par la mesure

Honnêteté de l'étape : quatre valeurs ne sont pas discriminées par le jeu gelé,
parce que l'agent fourni ne fait qu'une étape.

| Paramètre | Pourquoi la mesure est muette | Quand la refaire |
|---|---|---|
| `max_steps` entre 2 et 8 | l'agent n'enchaîne pas | étape 5, agent multi-étapes |
| `max_tool_calls` | compteur partagé avec `max_steps` | idem |
| `max_repeated_calls` | aucune répétition produite | idem |
| `stop_on_tool_error` | les erreurs tombent sur des scénarios de refus | idem |

Elles sont fixées par le besoin du jeu ou par principe, et c'est écrit comme tel.
Prétendre les avoir mesurées serait le défaut que ce document vient de corriger.

## 8. Journal des décisions

| Date | Décision | Motif | Décidée par |
|---|---|---|---|
| 21/09/2026 | `max_result_rows` 10 → 5 | 10 était inapplicable ; 5 rend la borne active sans rien retirer (§4.5) | proposé, **à valider** |
| 21/09/2026 | `treat_tool_output_as_data: false` refusé au chargement | un drapeau désactivable sans effet n'est pas un contrôle (§3.2) | Nicolas |
| 21/09/2026 | `record_fields` appliqués, `forbidden_fields` vérifiés, `instruction_like_content` déclaré | aligner le contrat de trace et la trace produite (§3.3) | Nicolas |
| 21/09/2026 | `max_result_rows` appliqué côté agent | le plafond de la politique doit pouvoir être plus strict que celui de l'outil (§3.4) | Nicolas |
| 21/09/2026 | `retention_days` laissé sans mécanisme | hors périmètre du brief 1, dette écrite (§6) | Nicolas |
