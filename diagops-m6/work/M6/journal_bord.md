# Journal de bord — Module 6

Une entrée par séance de travail. Le journal sert de preuve individuelle : il
décrit ce qui a été décidé, mesuré et rejeté, pas seulement ce qui a marché.

## Modèle d'entrée

### AAAA-MM-JJ — titre court

- objectif de la séance :
- décisions prises et alternatives écartées :
- mesures obtenues, avec la commande exécutée :
- écarts avec la référence M5 :
- difficultés, contournements, dettes assumées :
- prochaine étape :

## Points obligatoires du module

- gel du registre d'outils et motif de chaque autorisation ;
- valeurs de budget retenues et raison de chaque valeur ;
- version gelée du jeu de scénarios avant toute mesure comparative ;
- qualification du feedback avant tout usage ;
- axe unique modifié par le candidat et hypothèse associée ;
- résultat des gates et décision de promotion, rejet ou prolongation ;
- entrée de veille réglementaire M6 et question transmise à M7.

---

## 2026-09-21 — Séance 1 : le registre par l'observation

### J1-01 · Ouverture du module et point de départ vérifié

- **objectif** : installer le module, constater son point de départ au lieu de le supposer.
- **mesures** : `pytest` 45 tests verts. `eval/run_agent_eval.py` reproduit exactement les
  valeurs annoncées par le starter — réussite 0,833, choix d'outil 0,889, arguments 0,933,
  appels inutiles 0,062, 1 appel d'outil interdit, 7 refus corrects, baseline sans agent 0,111.
  `mean_steps` 0,89 : l'agent fourni appelle un outil, parfois zéro, jamais deux.
  Campagne fournie à 0,667 avec les deux échecs annoncés (`ADV-001`, `ADV-006`) ;
  `ADV-002` tient, l'instruction plantée dans `manufacturer` est tracée sans rien élargir.
  Qualification du lot `b1` : 80 retours, 39 actionnables, 8 à investiguer, 26 non
  actionnables, 7 à risque (8,7 %), 42 rapports couverts, contributeur le plus actif à 10 %.
- **décision** : ne rien corriger avant d'avoir documenté les contrats. L'étape 1 conditionne
  la politique (étape 2) et la conception de l'agent (étape 4).
- **prochaine étape** : étape 1, registre d'outils.

### J1-02 · Étape 1 — registre d'outils établi par l'observation, pas par recopie

- **objectif** : renseigner les dix champs par outil, dont `mode dégradé`, `données sensibles`
  et `erreurs` que le starter livre pré-remplis en demandant de les vérifier sur les exécutions.
- **méthode** : banc `eval/probe_tools.py` — 35 sondes (5 outils × nominal et cas limites :
  argument absent, format invalide, traversée de chemin, rôle non autorisé, bornes d'entier,
  énumération, identifiant inconnu, résultat vidé, source indisponible, délai injecté,
  champ empoisonné, outil hors registre), plus une mesure de discrimination du score
  documentaire et un chronométrage à froid et à chaud. Sortie : `results/observations_outils.json`.
- **cinq écarts trouvés entre contrat déclaré et comportement réel** :
  1. le mode dégradé de `search_knowledge` — « résultat vide, la réponse doit refuser » — **ne
     se produit jamais** : 0 résultat vide sur 5 questions hors domaine, et les intervalles de
     score se recouvrent (domaine 3,0-9,0 ; hors domaine 1,0-4,0). Le score compte les tokens
     communs sans retirer les mots vides : « de », « la », « aux » suffisent.
     `DOC-STEAM-PRESS-001` sort en tête des cinq questions hors domaine — un attracteur, pas
     une réponse. Et **2 questions du domaine sur 5 récupèrent le mauvais document** ;
  2. le filtrage de rôle est réel mais **silencieux** : sur la question de `SCN-014`, un
     technicien reçoit trois documents sans rapport et `reason` vide, là où un superviseur
     reçoit `DOC-DATA-ACCESS-001` à 7,0. L'échec `SCN-014` du starter s'explique là :
     l'information « un document pertinent existe, votre rôle ne l'autorise pas » n'existe
     nulle part dans le résultat ;
  3. les timeouts sont **inertes** — marge de ×6 250 à ×266 000 sur les durées mesurées à
     chaud — et le contrôle s'exécute *après* l'appel : un délai injecté de 1 200 ms sur un
     outil à 1 000 ms lève bien `ToolTimeout`, après avoir consommé les 1 200 ms ;
  4. les outils lisent les **sources brutes** : `severity: URGENT` (1 ligne sur 520) est
     inatteignable par filtre et ne ressort que sans filtre, sans être signalée ;
     `event_type: "Incident "` idem. Un « aucun incident critique » peut donc être faux ;
  5. un adaptateur ne juge pas ce qu'il rend : le champ empoisonné ressort sans marquage,
     la détection vit dans le runner.
- **confirmé** : validation avant lecture (9 sondes, 9 `ArgumentError`), traversée de chemin
  arrêtée par le motif d'identifiant, booléen refusé comme entier, autorisation avant
  validation, gel du registre effectif, aucune écriture dans les cinq adaptateurs, et
  identifiant inconnu rendu en résultat vide motivé plutôt qu'en exception.
- **décision** : **aucun contrat modifié à ce stade.** Les quatre corrections envisageables
  (signalement du filtre de rôle, score discriminant, normalisation des sources, recalage des
  timeouts) sont écrites en questions ouvertes au §6 du registre : chacune est un candidat à
  mesurer sur un seul axe, pas un correctif à appliquer au fil de l'eau.
- **arbitrage rendu par Nicolas le jour même** : le compte des documents écartés par le
  filtre de rôle sera exposé, sans les nommer, et **la formulation du refus restera
  identique** qu'un document ait été écarté ou qu'il n'en existe aucun. L'agent peut
  ainsi s'abstenir à bon escient et la trace reste auditable, sans ouvrir de canal
  auxiliaire sur l'existence d'un document restreint. Mise en œuvre renvoyée à
  l'étape 4, avec le scénario qui l'exerce : un contrat ne se modifie pas sans mesure.
- **livrable** : `docs/registre_outils.md`.
- **prochaine étape** : étape 2, politique d'exécution défendue valeur par valeur.

### J1-03 · Étape 2 — une politique se défend par ce qui change quand on la déplace

- **objectif** : fixer les onze paramètres de la politique, chacun justifié par une mesure.
- **méthode** : banc `eval/probe_policy.py` — le jeu gelé rejoué sous des politiques dérivées,
  un paramètre modifié à la fois, plus le coût du retrait de chaque autorisation, le test des
  bornes dures et l'inspection du contenu réel des traces. Sortie :
  `results/sensibilite_politique.json`.
- **cinq paramètres ne bornaient rien.** Lus, convertis, stockés dans la `Policy`, jamais
  consultés ensuite : `max_result_rows` (la seule troncature venait du contrat de chaque outil,
  donc la politique ne pouvait jamais être plus stricte), `treat_tool_output_as_data` (le passer
  à `false` ne changeait aucun comportement — or `INV-08` repose dessus), `record_fields` et
  `forbidden_fields` (la trace était construite sans les consulter), `retention_days` (rien ne
  purge). C'est le motif du M5 — *un contrôle qui ne mesure pas ce qu'il prétend* — transposé :
  un paramètre qui ne borne pas ce qu'il déclare.
- **écart de trace trouvé au passage** : la politique déclarait `step`, la trace portait `index` ;
  et `instruction_like_content` était tracé sans être déclaré. Rien de sensible ne fuyait, mais
  deux écarts sur neuf champs sur un dispositif dont le seul rôle est d'être auditable.
- **corrections, à comportement constant** : `max_result_rows` appliqué côté agent ;
  `treat_tool_output_as_data: false` refusé au chargement comme `allow_dynamic_tools` ; trace
  projetée sur `record_fields` avec le nom contractuel `step` ; `forbidden_fields` qui lèvent
  au lieu d'être interdits sur le papier ; `instruction_like_content` ajouté au contrat.
  Six tests dédiés (`tests/test_policy_enforced.py`) échouent si l'un d'eux redevient décoratif.
- **mesures qui fixent les valeurs** :
  - `max_steps` : la borne est testée avant de demander à l'agent s'il voulait continuer, donc
    un plan de N outils exige N+1. À `max_steps: 1`, la réussite tombe à **0,444** avec 9 refus
    incorrects et 14 dépassements, sur des scénarios nominaux que l'agent avait traités. Le jeu
    exige 3 outils (`SCN-006`) → **4**. Entre 2 et 8, aucune différence : l'agent ne fait qu'une
    étape ;
  - `require_evidence` : le paramètre le mieux défendu — à `false`, **0,833 → 0,556**, six
    scénarios de refus basculent en réponses non fondées ;
  - `max_result_rows` : ne gouverne pas la performance mais la donnée lue — 11 / 23 / 26 / 26
    lignes à 1 / 3 / 5 / 10, réussite 0,833 dans les quatre cas ;
  - `max_duration_ms` : borné par le bas par la somme des timeouts du plan le plus long
    (3 300 ms pour `SCN-006`), et sans objet par le haut — durée médiane 0,03 ms, maximum 0,4 ms ;
  - liste blanche : chaque retrait se paie, de 1 à 3 scénarios. Aucune autorisation n'est gratuite ;
  - bornes dures : les quatre politiques invalides testées sont refusées au chargement.
- **seule valeur modifiée** : `max_result_rows` 10 → 5. 10 était inapplicable ; 5 correspond à ce
  que l'agent demande et rend la borne active. **3 serait gratuit sur la mesure** (−12 % de données
  lues, zéro scénario perdu) mais couperait l'historique de maintenance à 3 interventions sur 14,
  et **1 rendrait impossible de constater une contradiction entre sources** (`INV-09`). Décision
  prise pour Nicolas, à valider ou amender.
- **dettes écrites** : aucun budget de tokens — il n'y a pas de modèle génératif, et il faudra
  en poser un *avant* d'en introduire un ; `retention_days: 30` ne purge rien, la rétention
  appartient au pipeline qui écrit `results/*.jsonl`. Une durée annoncée et non appliquée est une
  promesse réglementaire non tenue : à reprendre au checkpoint de veille (étape 8).
- **honnêteté de l'étape** : quatre valeurs ne sont pas discriminées par le jeu gelé
  (`max_steps` entre 2 et 8, `max_tool_calls`, `max_repeated_calls`, `stop_on_tool_error`) parce
  que l'agent ne fait qu'une étape. Écrites comme fixées par le besoin ou par principe, à
  re-mesurer à l'étape 5.
- **non-régression** : 0,833 / 0,889 / 0,933, 7 refus corrects, 0 dépassement — identiques à la
  référence. 51 tests verts (45 + 6).
- **livrables** : `agent/policy.yaml` en `m6-r2` (chaque valeur commentée par sa mesure),
  `docs/politique_execution.md`.
- **prochaine étape** : étape 3, construction et gel du jeu de scénarios étendu.

### J1-04 · Étape 3 — un jeu de scénarios qui mesure, puis qui gèle

- **objectif** : étendre le jeu du starter, le valider, le geler avant toute comparaison.
- **onze scénarios ajoutés**, aucun sorti d'une intuition : deux d'ancrage documentaire
  (`SCN-019`, `SCN-020`, issus des deux questions du domaine sur cinq qui récupèrent le mauvais
  document), un hors périmètre avec vocabulaire technique (`SCN-021`), un sur la valeur
  `severity: URGENT` inatteignable par filtre (`SCN-022`), un sur la récidive jugée depuis un
  historique tronqué (`SCN-023`), un sur le nom d'usage « P-416 » (`SCN-024` — le vecteur
  *identifiant ambigu* que le brief 2 déclare « à produire »), deux multi-étapes sur des paires
  d'outils différentes (`SCN-025`, `SCN-026`), un de rôle supérieur (`SCN-027`), un d'argument
  hors bornes (`SCN-028`) et un de révision périmée (`SCN-029`).
- **`SCN-027` est le seul à tester une sur-correction** : un filtrage de rôle trop large
  refuserait aussi la question légitime d'un superviseur, et cette régression resterait invisible
  tant que seul `SCN-014` mesure le filtrage. Toute restriction a besoin de son cas symétrique,
  sinon « refuser tout » devient une stratégie gagnante.
- **outil de gel** (`eval/freeze_scenarios.py`) : valide huit familles de défauts avant de
  concaténer — champs, unicité, rôles, attentes, outils présents au registre et disjoints,
  **arguments minimaux acceptés par le contrat de l'outil**, preuves présentes dans le data pack,
  cohérence refus/preuve. Puis écrit `eval/scenarios_v2.jsonl` et le manifeste `eval/GEL.md` avec
  les empreintes SHA-256. `--check` rejoue la validation et compare les empreintes, sans réécrire.
- **ce que la validation a trouvé, et qui n'est pas de nous** : `SCN-003` et `SCN-004` du starter
  attendent une réponse **sans exiger de preuve** — n'importe quelle réponse les satisfait, y
  compris fondée sur la mauvaise source. Non corrigés : modifier le jeu du starter romprait la
  comparabilité avec la référence 0,833. Signalés, et `SCN-028` a été renforcé en cours d'étape
  pour ne pas reproduire le défaut.
- **faute de ma part, corrigée avant le gel** : les onze scénarios étaient d'abord écrits en ASCII,
  sans accents. Le score du corpus compte des tokens exacts — « acces » n'est pas « accès ».
  `SCN-027` échouait donc pour une raison sans rapport avec ce qu'il mesure, et le point de départ
  global était faussé : 0,690 en ASCII contre **0,724** une fois accentué. Un jeu de scénarios
  écrit dans une autre langue que ses données mesure un autre système.
- **point de départ sur v2** : réussite **0,724** (contre 0,833 sur les 18), choix d'outil 0,793,
  arguments 0,895, premier outil 0,917, 9 refus corrects et 2 incorrects, 1 appel d'outil interdit,
  0 dépassement, baseline sans agent 0,172. Le jeu est plus dur de dix points, et c'est le but :
  un jeu qu'un agent à une étape réussit à 83 % ne laisse pas de place pour mesurer un progrès.
- **huit échecs, quatre causes** : enchaînement (`SCN-006`, `SCN-025`, `SCN-026`), refus avant
  appel (`SCN-013`), filtre de rôle (`SCN-014`), déclenchement puis ancrage (`SCN-019`,
  `SCN-020`), preuve tronquée (`SCN-023`). Trois viennent du starter, cinq de l'extension.
- **distinction à tenir pour l'étape 5** : `SCN-019` et `SCN-020` échouent aujourd'hui *avant*
  d'avoir exercé ce qu'ils mesurent — l'agent n'appelle aucun outil parce que la question ne porte
  aucun de ses termes déclencheurs. Confondre « il n'a pas cherché » et « il a mal cherché » ferait
  conclure à tort que le retrieval a été réparé.
- **trouvé en chemin, non exploité** : 54 identifiants d'événements sur 520 (10,4 %) portent un
  préfixe `EVT-2026S1-X0..` qui ne correspond à aucune convention documentée. L'agent les cite
  comme preuves sans distinction. Aucun scénario ne juge ce qu'il faudrait en faire : on n'écrit
  pas une règle de jugement sur une convention qu'on ne comprend pas. Question ouverte au registre.
- **livrables** : `eval/scenarios_extension.jsonl` (11), `eval/scenarios_v2.jsonl` (29, gelé),
  `eval/GEL.md`, `eval/freeze_scenarios.py`, `docs/jeu_de_scenarios.md`,
  `results/agent_eval_v2.json`.
- **prochaine étape** : étape 4, l'agent borné — enchaînement, refus avant appel, filtre de rôle
  avant lecture, et la mise en œuvre de l'arbitrage du 21/09 sur le compte de documents écartés.
