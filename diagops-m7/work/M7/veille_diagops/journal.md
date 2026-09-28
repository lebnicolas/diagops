# Checkpoint M7 — environ 1 h incluse dans le présentiel

Reprendre les décisions M4–M6. Si la référence commune est utilisée, son handoff est un guide et ne constitue pas une veille réglementaire réalisée par la promotion.

> Dossier de continuité pédagogique. **Ne constitue pas un avis juridique.**
> Entrée datée du **28/09/2026**. Responsable de l'entrée : porteur du dossier
> `veille_diagops/` (Nicolas Lebon en formation). Décisions détaillées :
> `decisions_m7.md`. URL, statuts de chargement et passages : `sources.md`.

## Niveaux de vérification utilisés dans le tableau

- **[TP]** vérifié sur texte primaire : texte publié au JO ou version consolidée
  de l'Office des publications, lu dans la langue française ;
- **[OS]** vérifié sur source officielle secondaire : page ou document de la
  Commission, du Parlement européen, de la CNIL, de l'ANSSI, de l'Assemblée
  nationale (lignes directrices, FAQ, dossier législatif) ;
- **[NV]** non vérifié : lecture ou interprétation sans texte officiel qui la porte.

## Levée de la limite de méthode M5-M6

EUR-Lex répond toujours `202` avec un corps vide depuis ce poste (défi anti-robot),
que ce soit par `legal-content/.../TXT/HTML`, par `eli/` ou par
`data.europa.eu/eli/`. **Le dépôt Cellar de l'Office des publications sert les
mêmes documents** par négociation de contenu :
`curl -L -H "Accept: text/html" -H "Accept-Language: fra" http://publications.europa.eu/resource/celex/<CELEX>`.
Le point d'accès SPARQL `https://publications.europa.eu/webapi/rdf/sparql` donne
les versions consolidées et les actes modificatifs. Commande détaillée dans
`sources.md`.

Conséquence : la question 1 du relais M6 (« lire le texte consolidé », reportée
depuis M5) est **close**. Le texte consolidé du règlement 2024/1689 au 27/07/2026
(CELEX 02024R1689-20260727) a été lu pour les articles 2, 3, 4, 6, 12, 14, 15, 19,
25, 26, 50, 53, 111, 113 et les annexes I et III. L'entrée 4 du M4 n'en avait lu
que l'article 6 ; l'entrée M6 affirmait qu'aucun texte consolidé n'avait été lu,
ce qui était inexact pour l'article 6 et exact pour le reste.

## Entrée M7 — 28/09/2026

| Date de consultation | Source officielle/section | Statut/application à la date | Rôle/fournisseur/transfert | Impact ADR/risque/migration | Question ouverte M8 |
|---|---|---|---|---|---|
| 28/09/2026 | **1. Rôles.** [TP] AI Act consolidé 27/07/2026 : art. 2(1), art. 3 points 3 (fournisseur), 4 (déployeur), 11 (mise en service « pour usage propre »), 68 (fournisseur en aval) ; art. 25(1) et 25(4) (ce dernier réécrit par l'Omnibus) ; art. 53(1) b). [OS] Lignes directrices Commission sur la définition de système d'IA, C(2025) 5053 final du 29/07/2025, § 40 et § 46. | Art. 3 applicable depuis le 02/02/2025, art. 53 depuis le 02/08/2025. Art. 25 relève du chapitre III section 3 : applicable au 02/12/2027 (annexe III) ou au 02/08/2028 (annexe I). Aucune modification des définitions 3, 4 et 68 par l'Omnibus. | **Local** : l'équipe est fournisseur (la mise en service pour usage propre suffit, art. 3 point 11), l'exploitant du site est déployeur. **Cloud (LLM ou embeddings par API)** : l'éditeur de l'API est fournisseur d'un modèle d'IA à usage général ; l'équipe **reste** fournisseur du système DiagOps et devient « fournisseur en aval » (art. 3 point 68). Passer par une API ne transfère pas le rôle. **Hybride** : idem pour la part distante. | L'option cloud n'allège aucune obligation de l'équipe ; elle ajoute une dépendance documentaire : la documentation de l'annexe XII due par le fournisseur de modèle (art. 53(1) b)) devient une pièce d'entrée de l'ADR. Fait nouveau [OS] : la version actuelle (index lexical, agent à règles fixées par des humains, aucun modèle appris) ressemble au « traitement de données de base » exclu par le § 46 des lignes directrices. **Un LLM ou des embeddings appris la font entrer sans ambiguïté dans la définition.** → D1 | La version M7 sans modèle est-elle un système d'IA au sens de l'art. 3 point 1 ? Qui porte le rôle de fournisseur hors du cadre de formation ? |
| 28/09/2026 | **2. Qualification haut risque.** [TP] Art. 6(1), 6(1 bis), 6(1 ter), 6(1 quater), 6(2)-(4) ; art. 3 point 14 réécrit ; art. 2(2) réécrit ; annexe I : règlement machines 2023/1230 **déplacé de la section A à la section B** ; annexe III point 2 ; règlement 2026/1744, art. 3 (modifie le règlement machines, art. 8 et 20). [OS] Projet de lignes directrices art. 6, publié le 19/05/2026, toujours « draft » au 28/09/2026. | Haut risque annexe III au 02/12/2027, annexe I au 02/08/2028 (art. 113 c)). Pour les machines (désormais section B) : seuls l'art. 6(1), l'art. 60 bis et les art. 102 à 112 de l'AI Act s'appliquent ; les exigences passent par des actes délégués du règlement machines, applicables au plus tard le 02/08/2028. Règlement machines applicable au 20/01/2027 [OS, FAQ CRA]. Lignes directrices art. 6(5) : échéance légale du 02/02/2026 dépassée de près de huit mois. | Si DiagOps était composant de sécurité d'une machine : fournisseur = fabricant de la machine au sens du règlement machines, plus l'équipe DiagOps pour l'AI Act. Annexe III point 2 : seulement si composant de sécurité dans la gestion d'infrastructures numériques critiques, du trafic routier ou de la fourniture d'eau, gaz, chauffage, électricité. | **Outil à effet simulé** : ne modifie pas la qualification tant qu'il reste `executable: false`, `network_client: null`. Connecté à un système réel, il fait basculer l'analyse sur le 1 ter : une demande d'inspection omise ou erronée peut-elle mettre en danger la santé et la sécurité ? **Option cloud** : ne modifie pas la qualification (elle dépend de la destination, pas de l'hébergement). Le déplacement des machines en section B change la voie réglementaire du scénario B de M4 (annexe I section A → règlement machines). → D2 | Secteur d'exploitation du parc (question Q2 ouverte depuis M4). Application du 1 ter à un outil à effet réel. Relire l'analyse du scénario B de `ai_act_diagops.md` au regard de la section B. |
| 28/09/2026 | **3. Traçabilité et journaux.** [TP] Art. 12(1)-(2), 19(1), 26(6) ; art. 113 c) ; règlement 2026/1744 art. 3 point 1 (nouvel alinéa de l'art. 8 du règlement machines : exigences à refléter = chapitre III section 2, art. 17, 19, 72, 73). [OS] CNIL, délibération n° 2021-122 du 14/10/2021, recommandation journalisation. | Art. 12, 19 et 26 **inchangés au fond** par l'Omnibus (absents de la liste des articles modifiés) ; seule leur date d'application a bougé : 02/12/2027 (annexe III) ou 02/08/2028 (annexe I section A). Durées : fournisseur **au moins six mois** (19(1)), déployeur **au moins six mois** (26(6)), « sauf disposition contraire […] en particulier dans le droit de l'Union sur la protection des données à caractère personnel ». CNIL : journaux d'accès conservés entre six mois et un an. | Obligation 19(1) sur le fournisseur pour les journaux « sous son contrôle », 26(6) sur le déployeur. Voie machines : la liste de l'Omnibus reprend l'art. 19 mais **pas l'art. 26** [interprétation, NV]. Option cloud : les journaux côté fournisseur d'API ne sont pas sous le contrôle de l'équipe. | `retention_days: 30` est **inférieur** au minimum de six mois **si** DiagOps est à haut risque ; hors haut risque, l'AI Act n'impose aucune durée. 30 jours restent défendables pour des traces d'agent minimisées (clés, empreintes, pas de texte). Deux écarts qui ne dépendent pas de la qualification : aucun journal d'accès n'existe (rôle non authentifié), et la purge à 30 jours n'est pas implémentée (dette M6). → D3 | Qualification (point 2) avant le 02/12/2027. Durée cible des journaux d'accès une fois l'authentification créée. |
| 28/09/2026 | **4. Supervision humaine.** [TP] Art. 14(1)-(4), en particulier 14(4) b) (biais d'automatisation), d) (ignorer, remplacer, inverser) et e) (arrêt) ; art. 26(1), 26(2), 26(5). | Haut risque uniquement ; mêmes dates que le point 3. Articles non modifiés par l'Omnibus. | Art. 14 : obligation de conception, sur le fournisseur. Art. 26(2) : le déployeur confie le contrôle à des personnes « qui disposent des compétences, de la formation et de l'autorité nécessaires ». | Le contrat `request_inspection_simulated` couvre déjà 14(4) d) : rejet, expiration, invalidation sur changement, annulation, compensation, approbation liée à l'empreinte exacte de l'aperçu. Il ne couvre pas 14(4) b) : rien ne détecte l'approbation réflexe. 26(2) n'est pas tenable : `authorized_role: superviseur_fictif` n'est pas authentifié. 14(4) e) : pas d'arrêt global documenté. → D4 | Qui approuve en exploitation réelle, avec quelle autorité, et comment le prouver ? |
| 28/09/2026 | **5. Cybersécurité.** [TP] AI Act art. 15(1), 15(4), 15(5). CRA (règlement 2024/2847) : art. 2(1), 3 points 1-2, 14(1)-(2), 69, 71 ; considérant 12. NIS2 (directive 2022/2555) : art. 41, annexe II point 5 d). [OS] FAQ CRA de la Commission v1.4 du 04/09/2026, FAQ 1.5 et section sur les produits antérieurs au 11/12/2027 ; page CRA (mise à jour 07/09/2026) ; dossier législatif de l'Assemblée nationale ; FAQ ANSSI « MonEspaceNIS2 » (mise à jour 19/09/2025). | AI Act art. 15 : haut risque, 2027 ou 2028. **CRA : art. 14 (notification) applicable depuis le 11/09/2026**, application générale le 11/12/2027. **NIS2 non transposée en France au 28/09/2026** : projet de loi « résilience » adopté au Sénat le 12/03/2025, rapport de commission spéciale AN le 10/09/2025, **séance publique inscrite au 07/10/2026** ; délai de transposition échu le 17/10/2024. | CRA : s'applique aux produits « mis à disposition sur le marché » ; FAQ 1.5 : un produit fabriqué pour usage propre n'est pas mis sur le marché → **DiagOps interne hors champ**. Un SaaS autonome (API de LLM) n'est pas un produit comportant des éléments numériques sauf s'il constitue le traitement à distance d'un produit. NIS2 : la fabrication de machines (NACE C28) figure à l'annexe II ; l'exploitant du site peut être entité importante. | Pas d'obligation CRA pour DiagOps en l'état. Déclencheur : distribution de DiagOps à un tiers dans le cadre d'une activité commerciale, même gratuite → l'équipe devient fabricant, notification 24 h / 72 h des vulnérabilités activement exploitées par la plateforme unique. Art. 15(5) sert de référentiel de conception : la red team M7 couvre empoisonnement, injection et confidentialité. Côté exploitant, NIS2 viendra par le SI du site, pas par DiagOps. → D5 | L'exploitant est-il entité NIS2 ? Suivre le vote AN du 07/10/2026 puis les décrets. |
| 28/09/2026 | **6. Transferts et fournisseurs.** [TP] RGPD art. 28(1), 28(3) a), g), h), art. 45 ; décision d'exécution (UE) 2023/1795, art. 1 et 3(4)-(5). [TP, métadonnées Cellar] arrêt du Tribunal T-553/23 du 03/09/2025 ; pourvoi C-703/25 P enregistré le 31/10/2025 ; aucun arrêt ni conclusions publiés. [OS] CNIL, fiche « Déterminer la qualification juridique des acteurs », 08/04/2024 (phase de développement uniquement). | RGPD inchangé : la proposition « omnibus numérique » COM(2025) 837, qui le modifie, est au stade du projet de rapport en commissions LIBE/ITRE (Parlement européen, information au 01/08/2026). **DPF en vigueur**, mais seulement pour les organisations inscrites sur la « liste du cadre de protection des données » (art. 1). Pourvoi pendant. | Fournisseur d'API : **sous-traitant** (art. 28) s'il ne traite que sur instruction documentée ; **responsable de traitement** pour toute réutilisation à ses propres fins (raisonnement de la fiche CNIL, transposé de la phase de développement à l'inférence : [NV]). Transfert hors UE si le traitement ou l'accès a lieu aux États-Unis ; le DPF ne couvre que l'entité certifiée. | Les données qui partiraient vers l'API : questions, extraits de corpus, et potentiellement du texte libre de feedback (6 retours sur 124 portaient des données personnelles en M6). Exigences option cloud : contrat art. 28(3) complet, dont point a) (transferts sur instruction) et point g) (suppression ou restitution en fin de prestation) ; aucune réutilisation pour entraînement ; filtrage avant envoi ; base de transfert de repli en cas d'invalidation du DPF ; sortie vers le local rejouée. → D6 | Base légale et information des contributeurs du feedback (Q7 du relais M6). Localisation effective du traitement chez le fournisseur retenu. |
| 28/09/2026 | **7. Réversibilité.** [TP] Data Act (règlement 2023/2854) : art. 2 points 8, 32, 36, 38 ; art. 23, 25(2) a), d), e), g), h), 25(4), 26, 28, 29(1)-(3), 30(5), 31(1)-(2), 50 ; considérant 81. [OS] Parlement européen, « Legislative Train », procédure 2025/0360(COD). | Applicable depuis le 12/09/2025 ; l'art. 50 ne diffère pas le chapitre VI. Frais de changement **réduits** (au coût) autorisés jusqu'au 12/01/2027, **interdits à partir du 12/01/2027** (art. 29). Préavis maximal deux mois, transition maximale 30 jours (sept mois si impossibilité technique motivée sous 14 jours ouvrables), récupération au moins 30 jours, effacement intégral ensuite. Omnibus numérique : exemptions ciblées pour les petites entreprises en projet, non adopté. | DiagOps est client ; l'hébergeur cloud est « fournisseur de services de traitement de données » (IaaS, PaaS, SaaS selon le considérant 81). Une API de modèle entre probablement dans la définition du point 8 [NV]. | Le chapitre VI donne les clauses à exiger ; il ne garantit pas la réversibilité de DiagOps. Deux limites qui touchent le M7 : **art. 31(2)**, le chapitre VI ne s'applique pas à une version non destinée à la production fournie pour essai et pour une durée limitée → un pilote cloud n'a aucune de ces garanties ; **art. 2 point 38**, les données exportables excluent ce qui est protégé par la propriété intellectuelle ou le secret d'affaires du fournisseur. La réversibilité doit donc rester démontrée techniquement (JSON → SQLite exercé en M7). → D7 | Des embeddings produits par l'API d'un tiers sont-ils des « données exportables » ou un actif du fournisseur ? |
| 28/09/2026 | **8. Calendrier AI Act après l'Omnibus.** [TP] Règlement 2026/1744 (JO du 24/07/2026, en vigueur le 27/07/2026, art. 4) ; AI Act consolidé : art. 113 a)-d), art. 111(2) et 111(4), art. 4 remplacé, art. 50 (seul le § 7 remplacé). [OS] Calendrier de l'AI Act Service Desk. | Revérifié : 02/08/2026 application générale, art. 50 inclus ; 02/12/2026 nouvelles interdictions et fin du transitoire 50(2) pour les systèmes mis sur le marché **avant** le 02/08/2026 (art. 111(4)) ; 02/12/2027 annexe III ; 02/08/2028 annexe I. Art. 111(2) : un système à haut risque mis en service avant ces dates n'est couvert qu'en cas « d'importantes modifications de [sa] conception ». Art. 4 (maîtrise de l'IA) applicable depuis le 02/02/2025, réécrit sans niveau de maîtrise imposé. | Le report ne touche ni les rôles ni l'art. 50. | Une génération ajoutée par l'option cloud **après** le 02/08/2026 relève de l'art. 50(2) sans délai de grâce : marquage lisible par machine, sauf fonction d'assistance à la mise en forme standard ou absence de modification substantielle des données d'entrée (cas d'une génération extractive). L'art. 50(1) (mention d'interaction) s'applique depuis le 02/08/2026 à tout système d'IA destiné à interagir avec des personnes, et DiagOps ne l'affiche pas. L'art. 111(2) n'est pas une stratégie : une migration cloud est une modification de conception. → D8 | Adoption des lignes directrices art. 6 (annoncée fin 2026). Code de bonne pratique sur le marquage (art. 50(7)). |

### Faits nouveaux par rapport aux entrées M4 à M6

1. **Le règlement machines est passé en annexe I section B** (Omnibus). Le
   scénario B de M4 raisonnait sur la section A. La voie change : l'AI Act ne
   s'applique plus que par l'art. 6(1), l'art. 60 bis et les art. 102 à 112, et
   les exigences arrivent par des actes délégués du règlement machines, au plus
   tard le 02/08/2028. [TP]
2. **Les articles 12, 14, 15, 19 et 26 n'ont pas été modifiés** ; seule leur date
   d'application a bougé. Les minima de six mois (art. 19 et 26) sont intacts. [TP]
3. **L'obligation de notification du CRA est applicable depuis 17 jours.**
   DiagOps en usage interne n'est pas concerné. [TP + OS]
4. **NIS2 n'est toujours pas transposée en France** ; la séance publique de
   l'Assemblée est inscrite au 07/10/2026. La FAQ de l'ANSSI consultée date du
   19/09/2025 et ne reflète pas ce calendrier. [OS]
5. **Le DPF tient, avec un pourvoi pendant** devant la Cour de justice. [TP]
6. **L'omnibus numérique « données » (RGPD, Data Act, NIS2) n'est pas adopté.**
   Cellar ne recense, entre juin 2025 et le 25/09/2026 (dernier acte indexé),
   aucun acte modificatif du RGPD, du Data Act ni de NIS2. Le CRA a été modifié
   par le règlement (UE) 2025/327 (espace européen des données de santé), sur
   ses art. 13(4), 31(3) et 32 : aucun des articles utilisés ici (2, 3, 14, 69,
   71) n'est touché. [TP]
7. **La version actuelle de DiagOps n'est peut-être pas un système d'IA.** Le
   § 46 des lignes directrices sur la définition exclut les systèmes à règles
   fixées par des humains, sans apprentissage ni inférence. La question n'avait
   jamais été posée depuis M0 : toutes les entrées supposaient la qualification
   acquise. [OS, application à DiagOps NV]

### Réponse au relais M6

| # | Question M6 | État au 28/09/2026 |
|---|---|---|
| 1 | Lire le texte consolidé | **Close** — lu via Cellar (voir plus haut) |
| 2 | Rétention du feedback non implémentée | **Ouverte**, reprise en D3 (purge) et D6 (données personnelles) |
| 3 | Version du système absente du formulaire de feedback | Hors veille réglementaire : question de conception, transmise telle quelle |
| 4 | Génération et art. 50 | **Précisée** : 50(1) ne dépend pas de la génération mais de l'interaction ; 50(2) s'appliquerait sans délai de grâce (D8) |
| 5 | Fournisseur d'inférence externe | **Traitée** en D1, D6 et D7 (conditions de l'option cloud) |
| 6 | Calendrier du report au 02/12/2027 | **Close** — revérifié sur l'art. 113 consolidé |
| 7 | Base légale du traitement des retours | **Ouverte** — transmise à M8 (Q6 de `decisions_m7.md`) |

### Incertitudes

- La qualification de DiagOps (système d'IA ou non, haut risque ou non) reste une
  lecture, pas une qualification juridique.
- Le texte consolidé est un outil de documentation « sans effet juridique » (il
  le dit en tête) ; les passages décisifs de l'Omnibus ont été recoupés sur le
  règlement 2026/1744 publié.
- La FAQ CRA « ne doit pas être considérée comme représentative de la position
  officielle de la Commission » (avertissement du document) : elle éclaire, elle
  ne tranche pas.
- La qualification d'une API de modèle comme « service de traitement de données »
  au sens du Data Act et celle du fournisseur d'API comme sous-traitant ne
  s'appuient sur aucun texte ou document officiel lu ce jour qui les traite
  explicitement.
- La page CURIA de l'affaire C-703/25 n'a pas pu être lue ; l'état du pourvoi
  repose sur les métadonnées Cellar (absence d'arrêt et de conclusions indexés).

### Décision

- `modifier` : D3 (purge effective, journaux d'accès), D4 (mesure du biais
  d'automatisation), D6 et D7 (conditions contractuelles de l'option cloud), D8
  (mention d'interaction IA) ;
- `maintenir` : D2 (outil à effet simulé, hors chemin de référence), D5 (hors CRA) ;
- `évaluer` : D1 (qualification de système d'IA de la version sans modèle).

### Livrables modifiés et report dans les artefacts

Créés dans ce dossier : `decisions_m7.md`, `sources.md` ; `journal.md` rempli.

**Report à faire** : les décisions D1 à D8 sont rédigées pour être recopiées dans
`architecture/adr/`, `security/residual_risks.md` et le plan de migration. Ce
report n'est pas fait dans cette entrée, qui n'écrit que dans `veille_diagops/`.
Tant qu'il n'est pas fait, la règle du brief 3 s'applique : une décision non
reliée à un artefact est considérée comme non traitée.

Une absence de changement doit être justifiée par une source datée. Les synthèses et textes générés ne remplacent pas les textes officiels.
