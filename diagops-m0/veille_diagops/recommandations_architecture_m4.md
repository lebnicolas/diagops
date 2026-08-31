# Recommandations d'architecture — issues de la veille M0-M4

> Brief 3, livrable 5. Écrit au **M4**, le 31/08/2026.
> Chaque recommandation part d'un **constat de veille** et aboutit à une
> **exigence vérifiable** — test, garde-fou, gate ou point de contrôle. Une
> recommandation qui ne se traduit par rien n'est pas une recommandation.

---

## Ce que la veille a changé, et ce qu'elle a confirmé

La consolidation M0-M4 a produit **une seule exigence nouvelle** et **cinq
confirmations**. C'est un résultat en soi : les décisions techniques du brief 1,
prises pour des raisons d'ingénierie, se sont révélées compatibles avec le cadre
réglementaire sans avoir été conçues pour lui.

Le sens du lien mérite d'être noté, parce qu'il est inhabituel : **la technique a
produit la conformité**, pas l'inverse. Un système qui n'interprète rien, n'agit
sur rien et ne décide de rien sort naturellement du champ des obligations
lourdes. La contrepartie est écrite dans la matrice de décision — c'est aussi un
système au périmètre étroit.

---

## A1 — Afficher la mention d'interaction avec une IA `nouvelle exigence`

**Constat.** L'article 50(1) du règlement 2024/1689 est applicable **depuis le
02/08/2026** : le fournisseur doit informer la personne qu'elle interagit avec un
système d'IA, sauf si c'est évident. L'exécution et les sanctions ont démarré à
la même date — jusqu'à 15 M€ ou 3 % du chiffre d'affaires mondial.
*(Source primaire : [FAQ transparence de la Commission](https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act), mise à jour le 24/07/2026.)*

**Pourquoi ne pas se reposer sur l'exemption.** « C'est évident » s'apprécie du
point de vue d'une personne raisonnablement informée. Pour un assistant intégré à
un outil de maintenance et utilisé par des techniciens formés, c'est
**défendable, pas acquis**. Afficher la mention coûte une ligne d'interface ;
s'en dispenser demande de démontrer l'évidence devant une autorité.

**Exigence.** Toute interface exposant l'assistant affiche une mention explicite
d'interaction avec un système d'IA, visible avant la première réponse.

**Vérifiable par.** Un test d'interface au M5 : la mention est présente sur
chaque point d'entrée. **Aucune interface n'existe aujourd'hui** — c'est la
seule des six recommandations qui crée du travail plutôt que d'en confirmer.

---

## A2 — Conserver la génération extractive `confirmée`

**Constat, à deux sources convergentes.**

*Réglementaire* : la génération extractive place DiagOps hors du champ de
l'obligation de marquage des contenus générés (article 50(2)) — les réponses
sont des fragments littéraux, pas des contenus produits. La FAQ de la Commission
prévoit en outre des exemptions pour les contextes B2B et industriels, et pour le
texte soumis à contrôle éditorial.

*Technique* : l'état de l'art sur l'injection indirecte est sans ambiguïté — un
LLM ne distingue pas de façon fiable une instruction d'une donnée, et l'OWASP
maintient que ni le RAG ni le fine-tuning ne résolvent le problème. Des travaux
de 2026 rapportent que cinq documents construits suffisent à manipuler 90 % des
réponses par empoisonnement de corpus.

**Ce que cela dit du système actuel.** Notre campagne de menaces a montré que
l'injection indirecte n'a aucun effet — **mais parce qu'aucun composant
n'interprète**, pas parce qu'une défense l'arrête. L'immunité est
architecturale, donc conditionnelle.

**Exigence.** Toute introduction d'un modèle génératif dans DiagOps déclenche :

1. la **rejeu intégral de la campagne de menaces** (`run_menaces.py`, 8 attaques) ;
2. la mise en place, *au minimum*, d'une recherche hybride, d'un re-ranking par
   un modèle indépendant, et d'une séparation de privilèges entre contenu
   récupéré et instructions système ;
3. le réexamen de l'article 50(2) — échéance de mise en conformité au
   **02/12/2026** pour les systèmes déjà sur le marché.

**Vérifiable par.** Une condition de non-déploiement déjà écrite au threat model
(n° 3). À transformer en **gate de chaîne de livraison** au M5.

---

## A3 — Aucun outil à effet externe `confirmée`

**Constat.** Deux raisons convergent.

*Réglementaire* : l'absence d'effet externe est ce qui écarte le plus
solidement la qualification de « composant de sécurité » — DiagOps ne commande
aucun équipement, ne déclenche aucun arrêt, et sa défaillance ne crée aucun
risque santé-sécurité direct. C'est le socle du scénario B de
`ai_act_diagops.md`.

*Technique* : c'est aussi ce qui rend `THR-005` inoffensive. Un document adverse
qui déclare deux actions d'écriture supplémentaires ne change rien :
`ALLOWED_ACTIONS` est un `frozenset` du code, et **il n'existe aucune fonction
d'écriture à appeler**.

**Exigence.** Les actions de l'agent restent **énumérées dans le code**, jamais
configurables par fichier, variable d'environnement ou document.

**Vérifiable par.** Contrôle bloquant déjà en place dans `run_agent.py` — 0
outil à effet sur 18 traces — et 16 tests unitaires. À porter en gate de CI au
M5.

> **Point de bascule identifié.** Le M7 prévoit un « outil à effet simulé ». Ce
> jour-là, A3 tombe, et avec elle une partie de l'analyse de qualification. À
> anticiper, pas à découvrir.

---

## A4 — Revue humaine avant toute exclusion de donnée `confirmée`

**Constat.** Le modèle de provenance a un rappel de 0,636 : il laisse passer 4
fenêtres fabriquées sur 11, et manque le segment `temperature_c` en totalité.
Une exclusion automatique de données sur cette base serait injustifiable —
réglementairement comme techniquement.

**Exigence.** La sortie du modèle est un **signalement**. Toute exclusion de
donnée reste une décision humaine, documentée.

**Vérifiable par.** Model card, section « usages exclus » : *décider seul de
l'exclusion d'une donnée* y figure explicitement.

---

## A5 — L'admission documentaire ne suffit pas `confirmée, avec réserve grave`

**Constat.** `THR-004` est la seule menace non arrêtée de la campagne. Le
contrat d'admission contrôle la **provenance** d'un document — statut, rôle,
checksum — jamais son **contenu**. Un mémo déclaré public qui recopie une donnée
restreinte la livre à un rôle public, et le dispositif entier est contourné sans
être attaqué.

**Exigence.** Aucun tiers ne peut ajouter un document au corpus sans **revue
éditoriale**. C'est une exigence organisationnelle, pas technique — et c'est
précisément pour cela qu'elle doit être écrite : aucune mesure supplémentaire ne
la remplacera.

**Vérifiable par.** Condition de non-déploiement n° 1 du threat model. À traduire
en procédure d'exploitation au M5, avec un responsable nommé.

---

## A6 — Authentifier le rôle, ne pas le déclarer `confirmée, hors périmètre M4`

**Constat.** `THR-008` — escalade de rôle par le contenu — est arrêtée parce que
les droits viennent du manifeste. Mais **le rôle lui-même est déclaré par
l'appelant** : quiconque interroge le système en se disant `auditeur` obtient les
droits d'un auditeur. Aucun mécanisme d'identité n'existe dans ce brief.

C'est aussi ce qui rend l'analyse RGPD incomplète : sans identité, aucune trace
d'accès exploitable.

**Exigence.** Le rôle est fourni par une couche d'authentification appelante, et
jamais par la requête.

**Vérifiable par.** Condition de non-déploiement n° 2 du threat model. **Hors
périmètre du M4** — à traiter au M5 avec le déploiement.

---

## Tableau de suivi

| # | Recommandation | Origine | Statut | Exigence vérifiable | Échéance |
|---|---|---|---|---|---|
| **A1** | mention d'interaction IA | AI Act art. 50(1) | **nouvelle** | test d'interface | **M5** |
| A2 | génération extractive conservée | art. 50(2) + injection indirecte | confirmée | rejeu de campagne + gate CI | avant tout LLM |
| A3 | aucun outil à effet | qualification haut risque + `THR-005` | confirmée | contrôle bloquant `run_agent.py` | tombe au M7 |
| A4 | revue humaine avant exclusion | rappel 0,636 | confirmée | model card, usages exclus | permanent |
| A5 | revue éditoriale du corpus | `THR-004` non arrêtée | confirmée | procédure + responsable nommé | **M5** |
| A6 | rôle authentifié | `THR-008`, rôle déclaré | confirmée | couche d'authentification | **M5** |

## Ce qui reste à instruire avant de recommander

| # | Question ouverte | Bloque |
|---|---|---|
| A1 de `ai_act_diagops.md` | vérifier l'article 6 modifié sur le texte consolidé — EUR-Lex inaccessible depuis ce poste | la qualification Annexe I |
| A3 de `ai_act_diagops.md` | quel est le secteur d'exploitation du parc DiagOps ? | la qualification Annexe III |
| — | dépouillement des six semaines de digest RSS non traitées | l'exhaustivité du radar |
