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
