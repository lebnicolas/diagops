# Analyse AI Act — DiagOps

> Brief 3, livrable 3. Consolidé au **M4**, le 31/08/2026.
> Sources consultées le 31/08/2026. **Ce document n'est pas un avis juridique** :
> il distingue les faits vérifiés, les interprétations et les points qui exigent
> une validation par une compétence juridique.

---

## 1. Le système analysé

Ce que DiagOps est **au terme du M4** — pas ce qu'il pourrait devenir :

| Brique | Fonction | Décide-t-elle quelque chose ? |
|---|---|---|
| Modèle de provenance | signale si une fenêtre de mesures est fabriquée ou réelle | non — aide au tri, exclusion soumise à revue humaine |
| Retrieval documentaire | récupère des procédures de maintenance admissibles | non |
| Génération citée | compose des extraits **littéraux**, ou s'abstient | non |
| Agent à une étape | choisit entre répondre, consulter, s'abstenir | une seule action, **aucun effet externe** |

**Utilisateurs** : techniciens de maintenance, superviseurs, auditeurs — des
professionnels, dans un cadre professionnel.

**Ce que le système ne fait pas**, et c'est déterminant pour l'analyse :

- il **ne commande aucun équipement** — aucun outil d'écriture n'existe dans le
  code, `ALLOWED_ACTIONS` est un `frozenset` de trois lectures ;
- il **ne décide d'aucun arrêt machine** — `DOC-PUMP-VIB-001` place explicitement
  cette décision chez le responsable habilité ;
- il **ne prédit aucune panne** — le corpus l'exclut, et la règle `ABS-003`
  refuse ces questions en citant l'exclusion ;
- il **ne supprime aucune donnée** — la model card l'écrit : toute exclusion
  reste une décision humaine.

## 2. Le cadre applicable au 31/08/2026

### Faits vérifiés

**Le règlement (UE) 2024/1689 (AI Act)** est en vigueur depuis le 01/08/2024.

**Il a été modifié par le règlement (UE) 2026/1744** — « Digital Omnibus on AI »,
du 8 juillet 2026, publié au Journal officiel le **24/07/2026**, entré en vigueur
le **27/07/2026**. Ce règlement modifie aussi le règlement (UE) 2018/1139
(aviation civile) et le **règlement (UE) 2023/1230 (machines)**.

*Vérifié le 31/08/2026 sur :* la notice ELI d'EUR-Lex
([reg/2026/1744](https://eur-lex.europa.eu/eli/reg/2026/1744/oj/eng), source
primaire, statut `applicable`), et confirmé par l'existence d'une **version
consolidée** du 2024/1689 datée du 27/07/2026
([CELEX 02024R1689-20260727](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A02024R1689-20260727)).

**Le calendrier applicable**, vérifié le 31/08/2026 sur la
[timeline officielle de l'AI Act Service Desk](https://ai-act-service-desk.ec.europa.eu/en/ai-act/timeline/timeline-implementation-eu-ai-act)
(Commission européenne, source primaire, **intégrant le Digital Omnibus**) :

| Date | Ce qui s'applique | État au 31/08/2026 |
|---|---|---|
| 02/02/2025 | définitions, littératie IA, interdictions | passé |
| 02/08/2025 | modèles à usage général, gouvernance | passé |
| **02/08/2026** | **majorité des règles, dont l'article 50 ; début de l'exécution et des sanctions** | **passé — depuis 29 jours** |
| 02/12/2026 | interdictions supplémentaires ; fin du transitoire art. 50(2) | à venir |
| 02/08/2027 | un bac à sable réglementaire par État membre | à venir |
| **02/12/2027** | **haut risque — Annexe III** *(reporté par le Digital Omnibus)* | à venir |
| **02/08/2028** | **haut risque — Annexe I** *(reporté par le Digital Omnibus)* | à venir |

### L'article 6 modifié — texte primaire vérifié le 31/08/2026

Le texte consolidé du règlement 2024/1689 au 27/07/2026 (CELEX
02024R1689-20260727) porte trois paragraphes nouveaux, marqués `▼M1` — la
modification du Digital Omnibus. **Ils sont cités ici in extenso**, parce que
toute la qualification en dépend.

> **1 bis.** *Aux fins du présent règlement, y compris le paragraphe 1 du présent
> article, les systèmes d'IA qui sont **uniquement** utilisés pour des aspects
> non liés à la sécurité en ce qui concerne **l'assistance aux utilisateurs**,
> l'optimisation des performances, l'efficacité des services, l'automatisation,
> la commodité ou **le contrôle de la qualité** ne sont pas considérés comme des
> composants de sécurité.*
>
> **1 ter.** *Nonobstant le paragraphe 1 bis, les systèmes d'IA dont la
> défaillance ou le dysfonctionnement **mettrait en danger la santé et la
> sécurité** sont considérés comme des composants de sécurité.*
>
> **1 quater.** *N'est pas considéré comme remplissant la condition énoncée au
> paragraphe 1, point b), un produit qui doit faire l'objet d'une évaluation de
> la conformité par un tiers **uniquement en raison de risques autres que les
> risques pour la santé et la sécurité**, en particulier les risques liés à la
> distribution du spectre radioélectrique ou aux interférences
> électromagnétiques qui n'affectent pas la santé et la sécurité.*

**Ce que le texte primaire ajoute aux analyses secondaires** — et qu'aucune ne
mentionnait :

1. **le mot « uniquement » au 1 bis.** L'exclusion ne joue que si le système est
   *exclusivement* employé pour des aspects non liés à la sécurité. Un usage
   mixte fait tomber l'exclusion ;
2. **le paragraphe 1 ter, qui est un renversement.** Il ne suffit pas d'être une
   aide à l'utilisateur : si la **défaillance** du système mettrait en danger la
   santé et la sécurité, il redevient composant de sécurité. Le critère porte
   sur la conséquence d'une panne, pas sur la fonction nominale ;
3. **le paragraphe 1 quater**, sans effet ici — il vise les évaluations par tiers
   motivées par le spectre radio ou la compatibilité électromagnétique.

Les analyses secondaires disaient « la définition est restreinte ». Le texte dit
« restreinte, **sauf si une défaillance met en danger la santé et la sécurité** ».
La nuance n'est pas de détail : **c'est elle qui porte l'analyse du scénario B**.

## 3. Rôles au sens du règlement

| Rôle AI Act | Qui | Pourquoi |
|---|---|---|
| **Fournisseur** | l'équipe DiagOps | elle développe le système et le met à disposition sous son nom |
| **Déployeur** | l'exploitant du site industriel | il l'utilise sous sa propre autorité, dans un cadre professionnel |
| Personnes concernées | techniciens, superviseurs, auditeurs | utilisateurs professionnels, pas des consommateurs |

**Dans le cadre de la formation, les deux rôles se confondent** — je développe et
j'exploite. C'est une commodité pédagogique, pas une situation réelle : en
production, les obligations se répartissent entre deux entités, et cette
répartition est elle-même un point à instruire.

## 4. Qualification de risque — trois scénarios

### Scénario A — pratique interdite (article 5)

**Écarté, sans réserve.** DiagOps ne pratique ni notation sociale, ni
manipulation subliminale, ni exploitation de vulnérabilité, ni biométrie à
distance, ni reconnaissance d'émotions sur des travailleurs. Il lit des mesures
de vibration et cite des procédures.

Le point le plus proche serait la **reconnaissance d'émotions au travail**, qui
est interdite : DiagOps n'en fait aucune, et n'a accès à aucune donnée sur les
personnes. Le M3 l'avait d'ailleurs mesuré — les mesures capteurs tombent à la
minute fixe, sans aucune signature d'activité humaine reconstituable.

### Scénario B — haut risque par l'Annexe I (produits réglementés)

C'est **le scénario à instruire en priorité**, parce que DiagOps opère sur des
machines et que le Digital Omnibus modifie précisément le règlement machines.

**Le raisonnement suit l'ordre du texte : 1 bis, puis 1 ter, puis 1(b).**

**Étape 1 — le 1 bis exclut-il DiagOps ?** Le paragraphe vise les systèmes
« uniquement utilisés pour des aspects non liés à la sécurité en ce qui concerne
l'assistance aux utilisateurs […] ou le contrôle de la qualité ». DiagOps est
exactement cela : une aide au tri et au diagnostic, sans fonction de sécurité.

Attention au mot **« uniquement »** : l'exclusion tombe dès qu'un usage touche la
sécurité. Aujourd'hui, aucun ne le fait — l'agent n'a aucun outil à effet, ne
décide d'aucun arrêt et ne prédit aucune panne. **La condition est remplie, et
elle l'est parce que le périmètre a été volontairement tenu étroit.**

**Étape 2 — le 1 ter le réintègre-t-il ?** C'est la vraie question, et elle est
plus dure. Le critère ne porte pas sur la fonction nominale mais sur **la
conséquence d'une défaillance** : « les systèmes d'IA dont la défaillance ou le
dysfonctionnement mettrait en danger la santé et la sécurité sont considérés
comme des composants de sécurité ».

Il faut donc examiner ce que produit une défaillance de DiagOps :

| Défaillance | Conséquence | Met-elle en danger la santé et la sécurité ? |
|---|---|---|
| faux négatif du modèle (4 sur 11 mesuré) | une fenêtre fabriquée entre dans un traitement aval | non — effet sur la qualité des données, pas sur une machine |
| citation erronée du RAG | un technicien lit un mauvais seuil | **c'est le point sensible** |
| abstention à tort | le technicien n'obtient pas la procédure | non — il consulte la procédure par ailleurs |
| indisponibilité totale | le système ne répond plus | non — la maintenance se fait sans lui, comme avant |

**Le seul chemin de danger est la citation erronée d'un seuil de sécurité.** Trois
éléments l'écartent, et tous sont mesurés plutôt que supposés :

1. les réponses sont des **extraits littéraux** de documents admissibles — 12/12
   vérifiés par appartenance de chaîne. Le système ne peut pas inventer un seuil,
   au pire il cite le mauvais document ;
2. les documents inadmissibles ne sont **jamais** récupérés — 0 sur toute la
   campagne de menaces, y compris les révisions périmées ;
3. la décision d'arrêt appartient explicitement au responsable habilité
   (`DOC-PUMP-VIB-001`), et la supervision humaine est inscrite à la model card.

**Reste `THR-003`** : deux documents actifs annonçant des seuils contradictoires.
Le système les signale sans arbitrer (`SIG-003`) — c'est le comportement voulu,
mais il transfère la charge sur l'humain. Si le corpus contenait durablement des
seuils de sécurité contradictoires, l'argument du 1 ter deviendrait plus fragile.

**Étape 3 — la machine est-elle soumise à évaluation par tiers ?** Non instruit :
cela dépend du parc réel, inconnu du `data_pack`. Le 1 quater est sans effet ici.

**Interprétation.** DiagOps n'est **pas** un composant de sécurité au sens du
1 bis, et le 1 ter ne le réintègre pas au vu des mesures disponibles. Ce n'est pas
une conclusion juridique — c'est une lecture, et elle repose sur des faits qui
peuvent changer.

**Ce qui ferait basculer le scénario**, par ordre de probabilité :

- brancher un **outil à effet** — écriture GMAO, arrêt, commande. Le M4 l'interdit,
  le M7 prévoit un « outil à effet simulé » : c'est le point de bascule daté ;
- laisser le corpus accumuler des **seuils de sécurité contradictoires** sans les
  résoudre ;
- introduire un modèle **génératif** capable de produire un seuil qui n'est dans
  aucun document.

### Scénario C — haut risque par l'Annexe III

Le point 2 de l'Annexe III vise les systèmes d'IA utilisés **comme composants de
sécurité dans la gestion et l'exploitation d'infrastructures critiques** —
infrastructures numériques, trafic routier, eau, gaz, chauffage, électricité.

**Deux conditions cumulatives**, et aucune n'est acquise :

- *composant de sécurité* — écarté au scénario B pour les mêmes motifs ;
- *infrastructure critique* — **indéterminé**. Le parc DiagOps compte des pompes,
  groupes froids, convoyeurs, compresseurs, fours et unités vapeur. Cela évoque
  un site industriel manufacturier, pas un réseau d'eau, de gaz ou d'électricité.
  **Mais le `data_pack` ne dit nulle part quel est le secteur exploité.**

**Point à instruire** : si le parc appartient à un opérateur d'importance vitale
— production ou distribution d'énergie, traitement d'eau —, la qualification
change, et avec elle l'échéance du 02/12/2027.

### La dérogation de l'article 6(3) — et l'obligation qu'elle crée

Même dans l'hypothèse où DiagOps relèverait de l'Annexe III, l'article 6(3)
prévoit qu'un système n'est pas à haut risque s'il « ne présente pas de risque
important de préjudice » **et** remplit l'une de quatre conditions. La troisième
décrit DiagOps presque mot pour mot :

> *c) le système d'IA est destiné à détecter les constantes en matière de prise
> de décision ou les écarts par rapport aux constantes habituelles antérieures
> et n'est pas destiné à se substituer à l'évaluation humaine préalablement
> réalisée, ni à influencer celle-ci, sans examen humain approprié.*

C'est la définition même du détecteur de provenance : il signale un écart, il ne
se substitue à rien, et l'examen humain est inscrit à la model card.

> [!warning] Mais la dérogation n'est pas gratuite — article 6(4)
> *« Un fournisseur qui considère qu'un système d'IA visé à l'annexe III n'est
> pas à haut risque **documente son évaluation** avant que ce système ne soit mis
> sur le marché ou mis en service. Ce fournisseur est soumis à l'**obligation
> d'enregistrement** visée à l'article 49, paragraphe 2. »*
>
> Invoquer la dérogation crée donc **deux obligations** : documenter l'évaluation,
> et s'enregistrer. C'est une obligation que je n'avais pas identifiée avant de
> lire le texte primaire, et elle ne s'active que si DiagOps relève effectivement
> de l'Annexe III — ce qui dépend de la question A3, non résolue.

Un dernier point du même article : le profilage de personnes physiques ramène
**toujours** un système au haut risque, sans dérogation possible. DiagOps n'en
fait aucun.

### Un retard de la Commission, à porter au dossier

L'article 6(5) prévoit que la Commission fournisse, **au plus tard le 2 février
2026**, des lignes directrices sur la mise en œuvre pratique de l'article 6,
« assorties d'une liste exhaustive d'exemples pratiques de cas d'utilisation ».

Au 31/08/2026, ces lignes directrices sont encore à l'état de **projet** :
consultation ciblée close le 23/07/2026, adoption annoncée pour la fin 2026
([Commission, projet de lignes directrices](https://digital-strategy.ec.europa.eu/en/library/draft-commission-guidelines-classification-high-risk-ai-systems)).

**Près de sept mois de retard sur une échéance inscrite dans le règlement.** Ce
n'est pas un détail de veille : ce sont précisément ces exemples pratiques qui
trancheraient les questions J1 et J2 de ce document. En leur absence, la
qualification repose sur une lecture du texte — la mienne.

### Ce qui est certain aujourd'hui

Aucun des deux scénarios de haut risque n'a d'échéance avant **décembre 2027**.
Ce n'est pas une raison de ne rien faire : l'article 50 s'applique **déjà**.

## 5. Article 50 — applicable depuis 29 jours

C'est le seul point de conformité **immédiatement exigible**.

*Vérifié le 31/08/2026 sur la [FAQ de la Commission sur les obligations de
transparence](https://digital-strategy.ec.europa.eu/en/faqs/transparency-obligations-under-article-50-ai-act)
(source primaire, page mise à jour le 24/07/2026).*

| Situation visée | DiagOps est-il concerné ? |
|---|---|
| **interaction directe avec une personne** | **oui** — l'assistant documentaire répond à un technicien |
| contenus synthétiques à marquer | **à instruire** — voir ci-dessous |
| reconnaissance d'émotions, catégorisation biométrique | non |
| deepfakes, texte d'intérêt public | non |

### Obligation 1 — informer que l'on interagit avec une IA

**Applicable**, sauf si « c'est évident » pour une personne raisonnablement
informée. Un assistant documentaire intégré à un outil de maintenance, utilisé
par des techniciens formés : le caractère évident est **défendable, pas acquis**.

> **Décision : `modifier`.** L'exemption « c'est évident » ne se plaide pas, elle
> se constate. Afficher la mention coûte une ligne d'interface ; s'en dispenser
> demande de démontrer l'évidence. Le rapport coût/risque ne laisse pas hésiter.

### Obligation 2 — marquer les contenus générés

**Position retenue : non applicable en l'état, et c'est une conséquence directe
d'un choix technique du brief 1.**

La génération de DiagOps est **extractive** : les réponses sont des fragments
**littéraux** des documents sources, sans reformulation. Ce ne sont pas des
contenus générés au sens de l'article 50(2) — ce sont des citations.

Deux éléments renforcent la position, et tous deux viennent de sources primaires
ou de nos propres mesures : la FAQ de la Commission prévoit une **exemption pour
les contextes B2B et industriels**, ainsi qu'une exemption pour le texte soumis
à **examen humain ou contrôle éditorial**.

> [!warning] Cette position tombe le jour où un modèle génératif est introduit
> C'est la conséquence réglementaire la plus nette du brief 1. Le choix de
> l'extraction avait été fait pour trois raisons techniques — fidélité garantie
> par construction, reproductibilité exacte, coût nul. Il a un quatrième effet,
> non anticipé : **il place DiagOps hors du champ de l'obligation de marquage**.
>
> Introduire un LLM y ferait entrer le système, avec une échéance de mise en
> conformité au **02/12/2026** pour les systèmes déjà sur le marché.

### Sanctions

Jusqu'à **15 M€ ou 3 % du chiffre d'affaires mondial** pour manquement à
l'article 50 — et l'exécution a commencé le 02/08/2026.

## 6. Ce qui relève d'autres textes

**RGPD.** DiagOps traite des données d'équipements, pas de personnes. Le M3
l'avait vérifié plutôt que supposé : les mesures capteurs tombent toutes à la
minute zéro sur huit heures fixes — signature d'un cycle automate, pas d'un
rythme humain — et la distribution horaire des interventions est plate, sans
creux nocturne reconstituable. **Aucune signature d'activité humaine
exploitable.**

Le point de vigilance est ailleurs : les **notes de bon de travail**
(`work_order_note`), renseignées sur 1 788 lignes sur 1 788, sont du texte libre
susceptible de contenir des noms. La règle `R-MNT-008` (pseudonymisation),
héritée du M2, s'applique et reste active.

**Directive machines / règlement (UE) 2023/1230.** Modifié par le même Digital
Omnibus. Sans effet tant que DiagOps ne commande aucun équipement — donc à
réexaminer au M7.

## 7. Décisions

| # | Objet | Décision | Livrable modifié |
|---|---|---|---|
| D1 | mention « vous interagissez avec une IA » | **`modifier`** | interface — à porter en M5 |
| D2 | marquage des contenus générés (art. 50(2)) | **`maintenir`** — sans objet, génération extractive | `generation_et_abstention.md` |
| D3 | qualification haut risque Annexe I | **`évaluer`** — non composant de sécurité au sens du 1 bis ; le 1 ter ne le réintègre pas au vu des mesures. Texte primaire vérifié | ce document, § 4 |
| D4 | qualification haut risque Annexe III | **`évaluer`** — dépend du secteur du parc, inconnu | ce document, § 4 |
| D5 | revue humaine avant toute action | **`maintenir`** | `model_card.md`, `agent_borne.md` |
| D6 | aucun outil à effet dans l'agent | **`maintenir`** | `threat_model.md`, condition n° 3 |
| D7 | pseudonymisation des notes de travail | **`maintenir`** | règle `R-MNT-008`, héritée M2 |

### Ce que chaque décision doit à une exigence technique

Le brief demande de relier les décisions réglementaires aux artefacts. Le lien
va ici **dans les deux sens**, et c'est le constat le plus intéressant de cette
consolidation :

| Décision réglementaire | Artefact technique qui la porte | Sens du lien |
|---|---|---|
| D2 — pas de marquage | génération extractive (étape 5) | **la technique produit la conformité** |
| D5 — revue humaine | model card, usages exclus (étape 8) | la technique produit la conformité |
| D6 — aucun effet externe | `ALLOWED_ACTIONS`, 0 outil à effet sur 18 traces (étape 6) | la technique produit la conformité |
| D3 — pas composant de sécurité | l'agent ne décide d'aucun arrêt (étape 6) | la technique produit la conformité |
| D1 — mention IA | **rien** — aucune interface n'existe encore | la conformité crée une exigence |

**Quatre décisions sur cinq sont satisfaites par des choix faits pour des raisons
techniques**, avant toute considération réglementaire. Ce n'est pas de la chance :
un système qui n'interprète rien, n'agit sur rien et ne décide de rien sort
naturellement du champ des obligations lourdes. La contrepartie est écrite dans
la matrice de décision — c'est aussi un système qui ne fait pas grand-chose.

## 8. Points nécessitant une validation juridique

Aucun des points suivants ne peut être tranché par ce document.

| # | Point | Pourquoi il faut une compétence juridique |
|---|---|---|
| J1 | l'article 6(1 ter) réintègre-t-il DiagOps ? | le texte est vérifié, son **application** au cas d'espèce demande une compétence juridique — « mettrait en danger la santé et la sécurité » est une notion d'appréciation |
| J1 bis | l'obligation de documentation et d'enregistrement de l'article 6(4) s'applique-t-elle ? | elle ne s'active que si DiagOps relève de l'Annexe III — dépend de J2 |
| J2 | le parc relève-t-il d'une infrastructure critique ? | qualification factuelle et sectorielle, hors de ma portée |
| J3 | l'exemption « c'est évident » de l'article 50(1) | notion d'appréciation ; D1 la contourne par prudence |
| J4 | répartition fournisseur / déployeur en exploitation réelle | dépend du montage contractuel |
| J5 | une réponse extractive citée est-elle un « contenu généré » ? | question d'interprétation, non tranchée par la FAQ |

## 9. Actions programmées

| # | Action | Échéance | Déclencheur |
|---|---|---|---|
| A1 | ~~vérifier l'article 6 modifié sur le texte consolidé~~ — **FAIT le 31/08/2026**, texte primaire cité au § 2 | — | J1 reformulé : le texte est connu, son application reste à valider |
| A1 bis | instruire l'obligation de documentation de l'article 6(4) si l'Annexe III s'applique | conditionné à A3 | bloque J1 bis |
| A2 | surveiller la publication des **guidelines de classification haut risque** — encore en projet, consultation close le 23/07/2026, adoption annoncée fin 2026 | fin 2026 | source : [Commission, projet de lignes directrices](https://digital-strategy.ec.europa.eu/en/library/draft-commission-guidelines-classification-high-risk-ai-systems) |
| A3 | établir le secteur d'exploitation du parc DiagOps | avant M5 | bloque J2, D4 |
| A4 | vérifier si la page article 6 de l'AI Act Service Desk a été mise à jour | mensuel | elle se déclare obsolète au 31/08/2026 |

---

*Consolidé le 31/08/2026, complété le même jour après lecture du texte primaire.
Sources primaires consultées : **texte consolidé du règlement 2024/1689 au
27/07/2026 (article 6, paragraphes 1 bis à 1 quater, cités in extenso)**, AI Act
Service Desk (timeline), FAQ transparence de la Commission, notice ELI EUR-Lex du
règlement 2026/1744. Analyses secondaires utilisées uniquement là où
c'est signalé, et jamais comme unique fondement d'une décision.*
