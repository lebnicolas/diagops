# Journal de veille — DiagOps

> Brief 3 — Livrable 2. Chaque entrée est datée, cite au moins une source primaire, distingue les faits vérifiés de l'interprétation, précise les incertitudes, formule un impact sur DiagOps et aboutit à une décision : `maintenir`, `évaluer`, `modifier` ou `écarter`.

---

## Entrée 1 — M0 — 21/07/2026

### Sujet : le calendrier de l'AI Act a changé en juin 2026 — le 2 août 2026 tient, mais le « haut risque » est reporté

**Contexte.** Le brief demandait de vérifier le calendrier d'application du règlement (UE) 2024/1689, notamment « l'échéance générale annoncée pour le 2 août 2026 ». La vérification révèle que le calendrier communément cité n'est plus le bon : un règlement modificatif (« Digital Omnibus » sur l'IA) a été adopté par les co-législateurs en juin 2026.

### Faits vérifiés

Sources consultées le 21/07/2026 :

1. **Calendrier officiel** — AI Act Service Desk, [Timeline for the implementation of the EU AI Act](https://ai-act-service-desk.ec.europa.eu/en/ai-act/timeline/timeline-implementation-eu-ai-act) (Commission européenne, source primaire ; statut : `applicable` pour le règlement de base — texte publié au JO le 12/07/2024, en vigueur depuis le 01/08/2024) :
   - **2 février 2025** (passé) : définitions, littératie IA, interdictions.
   - **2 août 2025** (passé) : modèles à usage général (GPAI), gouvernance.
   - **2 août 2026** : la majorité des règles s'applique, dont la **transparence (article 50)**, et **l'exécution commence** (pouvoirs des autorités, sanctions jusqu'à 35 M€ ou 7 % du CA mondial).
   - **2 décembre 2026** : interdictions supplémentaires (deepfakes sexuels non consentis, matériel pédocriminel) ; fin du délai transitoire pour l'article 50(2) (marquage technique des contenus générés) pour les systèmes mis sur le marché avant août 2026.
   - **2 août 2027** : au moins un bac à sable réglementaire opérationnel par État membre.
   - **2 décembre 2027** *(reporté — Digital Omnibus)* : obligations des systèmes à haut risque **Annexe III** (systèmes autonomes : RH, éducation, services essentiels…).
   - **2 août 2028** *(reporté — Digital Omnibus)* : obligations des systèmes à haut risque **Annexe I** (IA intégrée aux produits réglementés : machines, dispositifs médicaux…).

2. **Procédure législative du Digital Omnibus** — proposition de la Commission [COM(2025) 836](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=celex:52025PC0836) (EUR-Lex, primaire, statut : `projet` devenu texte adopté) ; accord Conseil/Parlement annoncé par le [Conseil de l'UE le 07/05/2026](https://www.consilium.europa.eu/en/press/press-releases/2026/05/07/artificial-intelligence-council-and-parliament-agree-to-simplify-and-streamline-rules/) (primaire, `communiqué officiel`) ; vote du Parlement européen le 16/06/2026 et approbation finale du Conseil le 29/06/2026 (rapportés par plusieurs analyses secondaires concordantes, dont [Morgan Lewis](https://www.morganlewis.com/pubs/2026/06/eu-approves-delays-and-other-amendments-to-certain-eu-ai-act-obligations-what-businesses-should-know), `analyse secondaire`).

3. **Contre-exemple documenté** : le site [artificialintelligenceact.eu](https://artificialintelligenceact.eu/implementation-timeline/) — référence non officielle très citée — affichait encore, au 21/07/2026, le calendrier d'origine (page datée du 01/08/2024), sans mention des reports. Illustration concrète du risque de recopier une date depuis une source secondaire non datée.

### Interprétation (distincte des faits)

Pour un système comme DiagOps, la lecture que je fais de ce nouveau calendrier :

- Si DiagOps relevait du **haut risque** (hypothèse du scénario B du livrable 3, non tranchée à ce stade), ses obligations les plus lourdes glisseraient vers décembre 2027 ou août 2028 selon l'annexe applicable.
- En revanche, les obligations de **transparence de l'article 50** (informer l'utilisateur qu'il interagit avec une IA, marquer les contenus générés) s'appliquent dès le 2 août 2026 — dans 12 jours — indépendamment de la qualification de risque. C'est potentiellement le premier point de conformité concret pour DiagOps.
- Le report ne « libère » pas : l'exécution et les sanctions démarrent bien au 2 août 2026 pour tout ce qui est applicable.

### Incertitudes

- Au 21/07/2026, je n'ai **pas trouvé le texte modificatif publié au Journal officiel** (pas de numéro de règlement) : les analyses concordent sur une publication attendue avant le 02/08/2026. Tant que le texte n'est pas au JO, les dates exactes des reports restent à confirmer sur EUR-Lex.
- Les dates des votes finaux (16/06 et 29/06/2026) proviennent de sources secondaires concordantes ; le communiqué primaire du Conseil vérifié date de l'accord du 07/05/2026.
- La portée exacte de l'article 50 pour un outil interne d'aide au diagnostic (utilisateurs professionnels avertis) reste à instruire — c'est l'objet du livrable 3.
- Aucune de ces conclusions ne constitue un avis juridique.

### Impact sur DiagOps

L'analyse AI Act (livrable 3) devra être conduite sur le **calendrier révisé**, pas sur celui de 2024 : la qualification haut risque des scénarios A/B change d'horizon de mise en conformité, tandis que la transparence article 50 devient le sujet immédiat.

### Décision

`évaluer` — instruire au livrable 3 : (a) l'applicabilité de l'article 50 à DiagOps dès août 2026, (b) la qualification de risque des scénarios A et B sur le calendrier révisé. La décision d'architecture existante (revue humaine obligatoire avant toute action) est par ailleurs `maintenir` : elle reste favorable quel que soit le scénario de qualification.

### Révision programmée

Cette entrée sera **révisée à la publication du règlement modificatif au Journal officiel** (détection : alerte My EUR-Lex) pour remplacer les dates rapportées par les dates du texte publié — révision qui satisfera l'exigence du brief d'une entrée révisée avant fin M4.

---

## Entrée 2 — M4 — 31/08/2026 — **révision de l'entrée 1**

### Sujet : le règlement modificatif est publié — les dates rapportées deviennent des dates de texte

**Motif de la révision.** L'entrée 1 se terminait par une révision programmée
« à la publication du règlement modificatif au Journal officiel ». Le déclencheur
s'est produit **trois jours après** son écriture.

### Faits vérifiés — sources consultées le 31/08/2026

1. **Le texte existe et il est identifié** : règlement **(UE) 2026/1744** du
   **8 juillet 2026**, modifiant les règlements (UE) 2024/1689, (UE) 2018/1139
   (aviation civile) et **(UE) 2023/1230 (machines)** — « Digital Omnibus on
   AI ». Publié au Journal officiel le **24/07/2026**, entré en vigueur le
   **27/07/2026**.
   *Source : notice ELI [reg/2026/1744](https://eur-lex.europa.eu/eli/reg/2026/1744/oj/eng)
   (EUR-Lex, primaire, statut `texte applicable`), corroborée par l'existence
   d'une version consolidée du 2024/1689 datée du 27/07/2026
   ([CELEX 02024R1689-20260727](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02024R1689-20260727)).*

2. **Le calendrier de l'entrée 1 est confirmé sur source primaire**, désormais
   intégré à la [timeline officielle](https://ai-act-service-desk.ec.europa.eu/en/ai-act/timeline/timeline-implementation-eu-ai-act)
   (AI Act Service Desk, Commission, primaire) : Annexe III au **02/12/2027**,
   Annexe I au **02/08/2028**, le **02/08/2026** tenant pour la majorité des
   règles et le début de l'exécution.

3. **L'article 50 est applicable depuis le 02/08/2026** — soit 29 jours au moment
   de cette entrée. Sanctions jusqu'à 15 M€ ou 3 % du chiffre d'affaires mondial.
   *Source : [FAQ transparence de la Commission](https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act),
   primaire, page mise à jour le 24/07/2026.*

4. **Un contre-exemple, à nouveau.** L'entrée 1 signalait qu'une référence
   secondaire très citée affichait un calendrier périmé. Cette fois, c'est une
   **page officielle de la Commission** qui n'est pas à jour — et qui le dit :
   la page de l'[article 6](https://ai-act-service-desk.ec.europa.eu/en/ai-act/article-6)
   porte la mention *« The text displayed on this page has not yet been updated
   to reflect those amendments. »*

### Interprétation (distincte des faits)

Les dates que l'entrée 1 tenait de sources secondaires concordantes se sont
révélées exactes. **Ce n'est pas une raison de faire confiance aux sources
secondaires** : c'est une raison de programmer la vérification, ce que l'entrée 1
avait fait.

### Incertitudes

- **Le contenu de l'article 6 modifié n'a pas pu être vérifié sur le texte
  primaire.** EUR-Lex n'est pas consultable depuis ce poste : les pages reviennent
  vides. Les analyses secondaires concordent sur l'introduction d'un article
  6(1a)–(1c) restreignant la notion de « composant de sécurité », mais **une
  concordance d'analyses n'est pas une lecture du texte**. C'est le point ouvert
  bloquant de cette consolidation.
- Les lignes directrices de la Commission sur la classification haut risque sont
  encore à l'état de **projet** — consultation close le 23/07/2026, adoption
  annoncée pour la fin 2026.

### Rôles et cycle de vie concernés

Fournisseur (l'équipe DiagOps) et déployeur (l'exploitant du site). Étape :
**conception**, avant tout déploiement.

### Impact sur DiagOps

Sur les **données** et le **modèle** : aucun. Sur le **RAG** et l'**agent** :
l'article 50(1) devient une obligation immédiate. Sur l'**exploitation** : aucune
interface n'existe encore, donc l'obligation ne peut pas être satisfaite
aujourd'hui. Sur la **supervision humaine** : inchangé, elle était déjà acquise.

### Décision

`modifier` — l'analyse AI Act est conduite sur le calendrier confirmé, et la
mention d'interaction IA devient une exigence d'interface (recommandation A1).

### Livrable modifié

`ai_act_diagops.md` (créé), `recommandations_architecture_m4.md` (créé, A1).

---

## Entrée 3 — M4 — 31/08/2026

### Sujet : consolidation M0-M4 — ce que la conformité doit aux choix techniques

**Contexte.** Le brief 1 M4 demande de réviser les scénarios et rôles à partir de
sources officielles datées, et de **relier chaque décision réglementaire à une
exigence technique**. La consolidation a produit un résultat que je n'attendais
pas.

### Faits vérifiés

Sources primaires consultées le 31/08/2026 : timeline et article 6 de l'AI Act
Service Desk, FAQ transparence de la Commission, notice ELI du règlement
2026/1744. Détail et statuts dans l'entrée 2 et dans `ai_act_diagops.md`.

Faits techniques, issus de nos propres mesures du brief 1 :

- l'agent n'appelle **aucun outil à effet** — 0 sur 18 traces, contrôle bloquant ;
- la génération est **extractive** — 12/12 extraits littéraux vérifiés par
  appartenance de chaîne ;
- le modèle a un **rappel de 0,636** et manque un segment entier ;
- **7 menaces arrêtées sur 8** ; la huitième — recopie de contenu restreint dans
  un document public — n'est couverte par aucune défense.

### Interprétation

**Quatre décisions réglementaires sur cinq sont satisfaites par des choix faits
pour des raisons techniques**, avant toute considération de conformité :

| Décision réglementaire | Choix technique qui la porte |
|---|---|
| pas de marquage art. 50(2) | génération extractive (étape 5) |
| revue humaine obligatoire | usages exclus de la model card (étape 8) |
| aucun effet externe | `ALLOWED_ACTIONS` figé dans le code (étape 6) |
| pas « composant de sécurité » | l'agent ne décide d'aucun arrêt (étape 6) |

Une seule décision crée du travail : la mention d'interaction IA, parce
qu'**aucune interface n'existe encore**.

Ma lecture : un système qui n'interprète rien, n'agit sur rien et ne décide de
rien sort naturellement du champ des obligations lourdes. Ce n'est pas une
stratégie de conformité — c'est la contrepartie d'un périmètre étroit, et la
matrice de décision dit ce que ce périmètre coûte.

### Incertitudes

Les cinq points de validation juridique de `ai_act_diagops.md` (J1 à J5), dont
deux bloquants : la qualification de « composant de sécurité » au sens révisé, et
le secteur d'exploitation du parc — **le `data_pack` ne dit nulle part s'il
s'agit d'une infrastructure critique**.

### Rôles et cycle de vie concernés

Fournisseur et déployeur. Étape : **conception et évaluation**, avant
déploiement.

### Impact sur DiagOps

| Composant | Impact |
|---|---|
| données | aucun — RGPD instruit au M3, absence de signature humaine mesurée |
| modèle | aucun — mais rappel 0,636 impose la revue humaine (A4) |
| RAG | `THR-004` non arrêtée : revue éditoriale du corpus exigée (A5) |
| agent | aucun changement — l'absence d'outil à effet est confirmée comme structurante (A3) |
| exploitation | mention IA à créer (A1), authentification du rôle à créer (A6) |
| supervision humaine | confirmée et documentée |

### Décision

`évaluer` sur la qualification de risque (deux points bloquants non levés),
`modifier` sur l'interface (A1), `maintenir` sur les cinq autres recommandations.

### Livrables modifiés

`ai_act_diagops.md`, `radar_technologique.md`,
`recommandations_architecture_m4.md` — les trois créés ce jour. `sources_veille.md`
inchangé, et cette absence de changement est justifiée : aucune source n'a été
ajoutée, retirée ni requalifiée depuis le 21/07.

### Aveu de méthode

Le collecteur RSS a tourné tous les jours depuis le 21/07 — il tournait encore le
31/08 à 09:00, avec 160 items en attente du digest. **Le dépouillement n'a pas
suivi.** Les vérifications de cette consolidation ont été faites le 31/08 pour
les besoins du M4, pas au fil de l'eau. Le dispositif technique a tenu, la
discipline hebdomadaire non — c'est le premier écart à corriger en M5, et il
n'est pas technique.

---

---

## Entrée 4 — M4 — 31/08/2026 — **levée de l'incertitude de l'entrée 2**

### Sujet : le texte primaire dit plus que les analyses secondaires

**Motif.** L'entrée 2 laissait un point ouvert bloquant : le contenu de
l'article 6 modifié n'avait pas pu être vérifié, EUR-Lex étant inaccessible
depuis le poste de travail. Le texte consolidé a été récupéré le même jour par
un autre canal.

### Faits vérifiés

Texte consolidé du règlement (UE) 2024/1689 au **27/07/2026** (CELEX
02024R1689-20260727), article 6, paragraphes marqués `▼M1` — c'est-à-dire
introduits par le Digital Omnibus. Cités in extenso dans `ai_act_diagops.md`, § 2.

**Trois éléments qu'aucune analyse secondaire consultée ne mentionnait :**

1. **le mot « uniquement » au paragraphe 1 bis** — l'exclusion ne joue que si le
   système est *exclusivement* employé pour des aspects non liés à la sécurité.
   Un usage mixte la fait tomber ;
2. **le paragraphe 1 ter, qui est un renversement** — « les systèmes d'IA dont la
   défaillance ou le dysfonctionnement mettrait en danger la santé et la sécurité
   sont considérés comme des composants de sécurité ». Le critère porte sur la
   **conséquence d'une panne**, pas sur la fonction nominale. Les analyses
   disaient « la définition est restreinte » ; le texte dit « restreinte, sauf
   si… » ;
3. **l'article 6(4)** — invoquer la dérogation de l'article 6(3) pour un système
   relevant de l'Annexe III oblige à **documenter l'évaluation** et à
   **s'enregistrer** (article 49(2)). Obligation non identifiée avant lecture du
   texte.

**Un quatrième fait, sur le régulateur lui-même** : l'article 6(5) prévoit que la
Commission fournisse des lignes directrices sur la mise en œuvre pratique de
l'article 6 **au plus tard le 2 février 2026**. Au 31/08/2026, elles sont encore
à l'état de projet — consultation close le 23/07/2026, adoption annoncée fin
2026. **Près de sept mois de retard sur une échéance inscrite dans le
règlement**, et ce sont précisément ces exemples pratiques qui trancheraient la
qualification de DiagOps.

### Interprétation

L'écart entre « la définition est restreinte » (analyses secondaires) et
« restreinte, sauf si la défaillance met en danger la santé et la sécurité »
(texte) n'est pas de nuance : **c'est le paragraphe 1 ter qui porte toute
l'analyse du scénario B**, et il était absent de tout ce que j'avais lu.

La leçon de méthode dépasse le cas : plusieurs analyses professionnelles
concordantes peuvent converger sur un résumé exact **et** omettre la disposition
qui décide. La concordance mesure la diffusion d'une lecture, pas sa complétude.

### Incertitudes restantes

L'application du 1 ter à DiagOps — « mettrait en danger la santé et la sécurité »
est une notion d'appréciation. L'analyse conclut que non, sur la base de quatre
scénarios de défaillance examinés et de trois éléments mesurés (extraits
littéraux, 0 document inadmissible récupéré, décision d'arrêt réservée à
l'humain). **Cela reste une lecture, pas une qualification juridique.**

### Rôles et cycle de vie concernés

Fournisseur. Étape : conception.

### Impact sur DiagOps

Aucun changement technique. L'analyse de qualification gagne un fondement
primaire, et une obligation conditionnelle apparaît (article 6(4)) si l'Annexe III
s'applique — ce qui dépend toujours du secteur d'exploitation, inconnu.

### Décision

`évaluer` — maintenue sur la qualification, mais désormais fondée sur le texte
plutôt que sur des analyses. La question Q1 du passage de relais est **close** ;
J1 est reformulé : le texte est connu, son application reste à valider.

### Livrable modifié

`ai_act_diagops.md` — § 2 (texte cité), scénario B (réécrit autour du 1 ter),
scénario C (dérogation 6(3) et obligation 6(4) ajoutées), § 8 et § 9 mis à jour.

# Passage de relais vers M5

*Établi le 31/08/2026, conformément au brief 3 M4-M8.*

## Dernière entrée datée

Entrée 4, **31/08/2026**.

## Sources ajoutées, retirées ou requalifiées

**Aucune.** Les 16 sources de `sources_veille.md` restent en place. Une
requalification de fait, à noter : la page « article 6 » de l'AI Act Service Desk
est **temporairement non fiable** — elle déclare elle-même ne pas refléter les
modifications du Digital Omnibus. À revérifier mensuellement.

## Décisions confirmées ou révisées

| Décision | État au M4 |
|---|---|
| revue humaine avant toute action | **confirmée** (M0 → M4) |
| calendrier AI Act révisé | **confirmée sur source primaire** — l'entrée 1 avait juste |
| article 6 modifié | **texte primaire lu et cité** — le 1 ter porte l'analyse, absent des analyses secondaires |
| génération extractive | **confirmée**, et devenue structurante |
| aucun outil à effet | **confirmée**, tombe au M7 |
| mention d'interaction IA | **nouvelle** — art. 50(1) applicable depuis le 02/08/2026 |

## Exigences devenues test, gate, métrique ou point de validation

| Exigence | Forme prise | Où |
|---|---|---|
| aucun outil à effet | **contrôle bloquant** — 0 sur 18 traces | `run_agent.py` |
| une seule action par question | **contrôle bloquant** — 18/18 | `run_agent.py` |
| garde-fou des actions | **16 tests unitaires** | `tests/test_agent_politique.py` |
| campagne de menaces rejouable | **script** — 8 attaques | `run_menaces.py` |
| revue éditoriale du corpus | **condition de non-déploiement n° 1** | `threat_model.md` |
| authentification du rôle | **condition de non-déploiement n° 2** | `threat_model.md` |
| rejeu de campagne si LLM | **condition de non-déploiement n° 3** | `threat_model.md` |
| mention d'interaction IA | **à créer** — aucun test possible aujourd'hui | — |

## Questions ouvertes — responsable et échéance

| # | Question | Responsable | Échéance |
|---|---|---|---|
| ~~Q1~~ | ~~vérifier l'article 6 modifié~~ — **CLOSE le 31/08/2026**, texte primaire lu et cité (entrée 4) | — | faite |
| Q1 bis | l'article 6(1 ter) — « défaillance mettant en danger la santé et la sécurité » — s'applique-t-il à DiagOps ? | compétence juridique | avant tout déploiement |
| Q1 ter | si l'Annexe III s'applique : documenter l'évaluation et s'enregistrer (art. 6(4) et 49(2)) | Nicolas Lebon | conditionné à Q2 |
| Q2 | quel secteur d'exploitation pour le parc DiagOps ? Infrastructure critique ou non | à poser au formateur | avant M5 |
| Q3 | adoption des lignes directrices de classification haut risque (projet, consultation close le 23/07/2026) | veille — alerte à poser | fin 2026 |
| Q4 | reprendre le dépouillement hebdomadaire du digest RSS | Nicolas Lebon | M5, dès la première semaine |
| Q5 | validation juridique des points J1 à J5 | compétence juridique externe | avant tout déploiement |

## Ce que M5 doit savoir en une phrase

DiagOps n'est probablement pas un système à haut risque, **une seule obligation
lui est immédiatement applicable** — la mention d'interaction IA, non satisfaite
faute d'interface —, et les trois conditions de non-déploiement du threat model
sont toutes des exigences d'exploitation, pas de modèle.
