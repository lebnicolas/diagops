# Sources consultées — checkpoint M7

Toutes les consultations datent du **28/09/2026**. Statut : **chargée** (contenu
lu), **vide** (réponse sans contenu exploitable), **erreur** (échec ou contenu
inutilisable). Nature : [TP] texte primaire, [OS] source officielle secondaire.

## Méthode d'accès aux textes de l'UE depuis ce poste

EUR-Lex renvoie `HTTP 202` avec un corps vide (défi anti-robot) à `curl` comme à
WebFetch. Le dépôt Cellar de l'Office des publications sert les mêmes
manifestations par négociation de contenu :

```bash
curl -sL -H "Accept: text/html, application/xhtml+xml" -H "Accept-Language: fra" \
  -o texte.html "http://publications.europa.eu/resource/celex/<CELEX>"
```

Versions consolidées et actes modificatifs : point d'accès SPARQL
`https://publications.europa.eu/webapi/rdf/sparql`, propriété
`cdm:resource_legal_id_celex` (préfixe `0` pour les consolidés, par exemple
`02024R1689-20260727`). Fraîcheur constatée : derniers actes indexés datés du
25/09/2026.

## Textes primaires de l'UE (via Cellar)

| Source | URL | Statut | Passages utilisés |
|---|---|---|---|
| [TP] AI Act, version consolidée au 27/07/2026 (CELEX 02024R1689-20260727) | http://publications.europa.eu/resource/celex/02024R1689-20260727 | chargée (924 ko, xhtml) | art. 2(1), 2(2) ; art. 3 points 1, 3, 4, 11, 14, 68 ; art. 4, 4 bis ; art. 6 (1 à 1 quater, 2 à 5) ; art. 12(1)-(3) ; art. 14 ; art. 15 ; art. 19 ; art. 25 ; art. 26 ; art. 50 ; art. 53(1) ; art. 75 bis ; art. 111 ; art. 113 ; annexe I (sections A et B) ; annexe III point 2 |
| [TP] AI Act, texte initial (CELEX 32024R1689) | http://publications.europa.eu/resource/celex/32024R1689 | chargée (1,38 Mo) | contrôle de cohérence avec le consolidé |
| [TP] Règlement (UE) 2026/1744 « omnibus numérique sur l'IA », JO L du 24/07/2026 (CELEX 32026R1744) | http://publications.europa.eu/resource/celex/32026R1744 | chargée (380 ko) | considérant relatif aux machines ; considérant sur l'enregistrement des systèmes relevant de l'art. 6(3) ; art. 1 (liste des articles modifiés : 12, 14, 15, 19, 26 absents) ; art. 2(2), 2(7), 2(13), art. 3 point 14 ; art. 3 (modification du règlement machines, art. 8 et 20) ; art. 4 (entrée en vigueur au troisième jour) ; note 4 (vote PE 16/06/2026, décision du Conseil 29/06/2026) |
| [TP] Cyber Resilience Act, règlement (UE) 2024/2847 (CELEX 32024R2847) | http://publications.europa.eu/resource/celex/32024R2847 | chargée (776 ko) | considérant 12 (nuage, SaaS) ; art. 2(1) ; art. 3 points 1, 2 et définitions de mise sur le marché et de mise à disposition ; art. 14(1)-(2) ; art. 69 ; art. 71(2) |
| [TP] Règlement (UE) 2025/327 (espace européen des données de santé) (CELEX 32025R0327) | http://publications.europa.eu/resource/celex/32025R0327 | chargée | article « Modification du règlement (UE) 2024/2847 » : art. 13(4), 31(3), 32 du CRA modifiés |
| [TP] Data Act, règlement (UE) 2023/2854 (CELEX 32023R2854) | http://publications.europa.eu/resource/celex/32023R2854 | chargée (655 ko) | considérant 81 ; art. 2 points 8, 32, 36, 38 ; art. 23 à 31 ; art. 50 |
| [TP] RGPD, règlement (UE) 2016/679 (CELEX 32016R0679) | http://publications.europa.eu/resource/celex/32016R0679 | chargée (877 ko) | art. 28 ; art. 45(1) |
| [TP] Décision d'exécution (UE) 2023/1795 (DPF), JO L 231 du 20/09/2023 (CELEX 32023D1795) | http://publications.europa.eu/resource/celex/32023D1795 | chargée (1,34 Mo) | art. 1 ; art. 3(1), 3(4), 3(5) |
| [TP] NIS2, directive (UE) 2022/2555 (CELEX 32022L2555) | http://publications.europa.eu/resource/celex/32022L2555 | chargée (759 ko) | art. 41 (transposition au 17/10/2024) ; annexe II point 5 |
| Proposition COM(2025) 837 « omnibus numérique » (CELEX 52025PC0837) | http://publications.europa.eu/resource/celex/52025PC0837 | erreur (`HTTP 300`, choix multiple de manifestations non résolu) | titre seul, obtenu par SPARQL : modifie les règlements 2016/679, 2018/1724, 2018/1725, 2023/2854 et les directives 2002/58/CE, 2022/2555, 2022/2557 |
| Requêtes SPARQL Cellar | https://publications.europa.eu/webapi/rdf/sparql | chargée | versions consolidées existantes (RGPD 20160504, NIS2 20221227, Data Act 20231222, CRA 20241120, AI Act 20240712 et 20260727) ; actes de 2025-2026 citant RGPD, Data Act, CRA, NIS2 ou « omnibus » ; documents de l'affaire T-553/23 (arrêt du 03/09/2025) et C-703/25 P (pourvoi du 31/10/2025, aucun arrêt ni conclusions) ; derniers actes indexés (25/09/2026) |

## Points d'entrée EUR-Lex testés

| URL | Statut | Remarque |
|---|---|---|
| https://eur-lex.europa.eu/legal-content/FR/TXT/HTML/?uri=CELEX:32024R1689 | vide (`HTTP 202`, 0 octet) | défi anti-robot |
| https://eur-lex.europa.eu/eli/reg/2026/1744/oj/fra | vide (`HTTP 202`, 0 octet) | idem |
| http://data.europa.eu/eli/reg/2024/1689/oj | vide (redirige vers EUR-Lex, `HTTP 202`) | idem |
| http://publications.europa.eu/resource/celex/32024R1689 (sans en-tête `Accept`) | redirection `303` vers la notice RDF | résolu en ajoutant l'en-tête `Accept: text/html` |

## Sources officielles secondaires

| Source | URL | Statut | Passage utilisé |
|---|---|---|---|
| [OS] AI Act Service Desk — calendrier de mise en œuvre | https://ai-act-service-desk.ec.europa.eu/en/ai-act/timeline/timeline-implementation-eu-ai-act | chargée (pas de date de mise à jour affichée) | jalons 02/08/2026, 02/12/2026, 02/08/2027, 02/12/2027, 02/08/2028 ; aucune adoption des lignes directrices art. 6 |
| [OS] Commission — projet de lignes directrices sur la classification haut risque | https://digital-strategy.ec.europa.eu/en/library/draft-commission-guidelines-classification-high-risk-ai-systems | chargée | « Publication 19 May 2026 », statut « Draft » ; aucune adoption |
| [OS] Commission — lignes directrices sur la définition de système d'IA, C(2025) 5053 final du 29/07/2025 | https://digital-strategy.ec.europa.eu/en/library/commission-publishes-guidelines-ai-system-definition-facilitate-first-ai-acts-rules-application ; PDF https://ec.europa.eu/newsroom/dae/redirection/document/112455 | chargée (PDF, 13 pages) | § 40 (considérant 12, règles définies par des personnes) ; § 46 (traitement de données de base) |
| [OS] Commission — page Cyber Resilience Act | https://digital-strategy.ec.europa.eu/en/policies/cyber-resilience-act | chargée (mise à jour 07/09/2026) | notification au 11/09/2026 ; application principale au 11/12/2027 |
| [OS] Commission — FAQ CRA, version 1.4 du 04/09/2026 | https://digital-strategy.ec.europa.eu/en/library/cyber-resilience-act-implementation-frequently-asked-questions ; texte https://ec.europa.eu/newsroom/dae/redirection/document/123307 | chargée | FAQ « produit comportant des éléments numériques » (SaaS autonome hors champ) ; FAQ 1.5 (usage propre hors champ) ; section règlement machines (applicable au 20/01/2027) ; FAQ sur la notification pour les produits antérieurs au 11/12/2027 ; avertissement : pas la position officielle de la Commission |
| [OS] Parlement européen — Legislative Train, « Digital Omnibus Regulation » | https://www.europarl.europa.eu/legislative-train/theme-a-new-plan-for-europe-s-sustainable-prosperity-and-competitiveness/file-digital-package | chargée (information au 01/08/2026) | procédure 2025/0360(COD) ; projet de rapport LIBE/ITRE discuté le 13/07/2026 ; pas de vote ; exemptions ciblées cloud et point unique de notification |
| [OS] Commission — transferts de données UE-États-Unis | https://commission.europa.eu/law/law-topic/data-protection/international-dimension-data-protection/eu-us-data-transfers_en | chargée (pas de date) | adoption du DPF le 10/07/2023 ; aucune mention du contentieux Latombe |
| [OS] Assemblée nationale — dossier législatif « résilience des infrastructures critiques et renforcement de la cybersécurité » | https://www.assemblee-nationale.fr/dyn/17/dossiers/DLR5L17N50731 | chargée | adoption Sénat 12/03/2025 (T.A. n° 78) ; dépôt AN 13/03/2025 ; rapport n° 1779 du 10/09/2025 ; « Discussion en séance publique — Mercredi 7 octobre 2026 » |
| [OS] ANSSI — MonEspaceNIS2, « Avancement de la transposition de la directive NIS 2 » | https://aide.monespacenis2.cyber.gouv.fr/fr/article/avancement-de-la-transposition-de-la-directive-nis-2-1b3j1da/ | chargée (mise à jour 19/09/2025, en retard sur le dossier AN) | entrée en vigueur à la promulgation de la loi, des décrets et des arrêtés |
| [OS] CNIL — recommandation relative aux mesures de journalisation | https://www.cnil.fr/fr/la-cnil-publie-une-recommandation-relative-aux-mesures-de-journalisation | chargée (18/11/2021, délibération n° 2021-122 du 14/10/2021) | conservation des journaux entre six mois et un an ; cas des données sources conservées moins de six mois |
| [OS] CNIL — consultation sur le projet de recommandation journalisation | https://www.cnil.fr/fr/consultation-publique-projet-de-recommandation-journalisation | chargée | consultation du 28/05 au 25/07/2021 ; pas de recommandation plus récente identifiée |
| [OS] CNIL — fiche « Déterminer la qualification juridique des acteurs » | https://www.cnil.fr/fr/determiner-la-qualification-juridique-des-fournisseurs-de-systemes-dia | chargée (08/04/2024) | phase de développement uniquement ; prestataire réutilisant un jeu de données pour son compte = responsable de traitement ; ne traite pas l'usage d'un modèle par API |
| CURIA — affaire C-703/25 | https://curia.europa.eu/juris/liste.jsf?num=C-703/25&language=fr | erreur (réponse de 130 ko sans contenu exploitable) | aucun ; état du pourvoi pris dans les métadonnées Cellar |

## Sources de repérage (non citées comme preuve)

Utilisées pour trouver les références exactes, puis remplacées par les textes
officiels ci-dessus : résultats de recherche renvoyant à digitalpolicyalert.org
et privacy-daily.com (pourvoi Latombe), directive-nis2.fr, vie-publique.fr et
village-justice.com (loi « résilience »), Bird & Bird, DLA Piper, Hunton,
Freshfields (projet de lignes directrices art. 6), iubenda, Kennedys, Maples
(omnibus numérique). Aucune n'est reprise dans le tableau du journal.
