# Décisions d'architecture issues du checkpoint réglementaire M7

> Établi le **28/09/2026** à partir de `journal.md` (entrée M7). Ne constitue pas
> un avis juridique. Chaque décision est rédigée pour être recopiée dans un ADR
> (`architecture/adr/`), le registre des risques (`security/residual_risks.md`)
> ou le plan de migration, avec la condition qui la déclenche.
> Niveaux de vérification : [TP] texte primaire, [OS] source officielle
> secondaire, [NV] non vérifié.

## Vue d'ensemble

| ID | Sujet | Décision courte | Code | Destination |
|---|---|---|---|---|
| D1 | Rôles | L'option cloud ne transfère aucune obligation de l'équipe ; documentation du modèle exigée | `évaluer` | ADR option cloud |
| D2 | Qualification | Outil à effet maintenu simulé ; toute connexion réelle rouvre la qualification | `maintenir` | ADR outil à effet, registre des risques |
| D3 | Journaux | 30 jours maintenus hors haut risque, purge rendue effective ; six mois minimum si haut risque | `modifier` | ADR traces, plan de migration |
| D4 | Supervision | Approbation humaine instrumentée contre le biais d'automatisation | `modifier` | contrat d'outil, registre des risques |
| D5 | Cybersécurité | Hors CRA en usage interne ; distribution à un tiers = déclencheur | `maintenir` | registre des risques |
| D6 | Transferts | Option cloud conditionnée à un contrat art. 28, région UE, filtrage avant envoi | `modifier` | ADR option cloud, politique de données |
| D7 | Réversibilité | Clauses chapitre VI exigées ; réversibilité prouvée par la technique, pas par le contrat | `modifier` | ADR option cloud, plan de migration |
| D8 | Calendrier / art. 50 | Mention d'interaction IA affichée ; marquage 50(2) si génération non extractive | `modifier` | ADR interface, plan de migration |

---

## D1 — Rôles AI Act et option cloud

**Décision.** Dans toutes les options (local, cloud, hybride), l'équipe DiagOps
est fournisseur du système DiagOps. Dans les options cloud et hybride, elle est
en outre « fournisseur en aval » d'un modèle d'IA à usage général. Le choix d'un
fournisseur d'API de modèle est subordonné à la remise de la documentation
destinée aux fournisseurs en aval (annexe XII) ; cette documentation est versée
au dossier de l'ADR avant le premier appel.

**Condition de déclenchement.** Premier appel à un modèle ou à un service
d'embeddings distant, y compris en test.

**Fondement.** AI Act consolidé, art. 3 points 3, 4, 11 et 68 ; art. 53(1) b)
applicable depuis le 02/08/2025. [TP]

**Point à évaluer.** La version M7 sans modèle appris (index lexical, agent à
règles) ressemble au « traitement de données de base » exclu par le § 46 des
lignes directrices de la Commission sur la définition de système d'IA
(C(2025) 5053). [OS] Si c'est le cas, l'AI Act ne s'applique pas à cette
version, et **c'est l'introduction d'un LLM ou d'embeddings qui fait entrer
DiagOps dans son champ**. À faire trancher (Q1) ; en attendant, les décisions
D2 à D8 sont prises comme si DiagOps était un système d'IA, hypothèse prudente.

**Texte ADR proposé.** « L'option cloud n'allège aucune obligation de l'équipe au
titre de l'AI Act. Elle ajoute une dépendance documentaire (art. 53(1) b)) et,
si le système est qualifié à haut risque, un accord écrit avec le fournisseur du
modèle (art. 25(4), applicable au 02/12/2027 ou au 02/08/2028). »

---

## D2 — Qualification haut risque, outil à effet simulé, option cloud

**Décision.** L'outil `request_inspection_simulated` reste non exécutable
(`executable: false`, `network_client: null`, `environment: tabletop_only`) et
hors du chemin de référence. Sa connexion à un système réel de gestion de
maintenance est **une décision de requalification**, pas une évolution
fonctionnelle : elle exige une nouvelle analyse art. 6(1 bis) / 6(1 ter) avant
toute mise en service.

**Condition de déclenchement.** Toute proposition de passer `executable` à
`true`, de renseigner `network_client`, ou d'exposer l'outil hors bac à sable.

**Fondement.** Art. 6(1 bis) : l'exclusion ne vaut que pour un système
« uniquement » utilisé pour des aspects non liés à la sécurité ; art. 6(1 ter) :
un système « dont la défaillance ou le dysfonctionnement mettrait en danger la
santé et la sécurité » est composant de sécurité. [TP] Une demande d'inspection
réelle, omise ou erronée, entre dans le champ de la question du 1 ter ; une
demande simulée, non.

**Option cloud.** Sans effet sur la qualification : elle dépend de la destination
du système, pas de son hébergement. [TP, art. 6]

**Fait nouveau à reporter.** Le règlement machines (UE) 2023/1230 est passé de
l'annexe I section A à la section B (règlement 2026/1744). Si DiagOps devenait
composant de sécurité d'une machine, seuls l'art. 6(1), l'art. 60 bis et les
art. 102 à 112 de l'AI Act s'appliqueraient ; les exigences viendraient des
actes délégués du règlement machines, applicables au plus tard le 02/08/2028.
[TP] Le scénario B de `ai_act_diagops.md` (M4) est à réécrire sur cette base.

**Texte registre des risques proposé.** « R-REG-01 — Requalification haut risque
par connexion de l'outil à effet à un système réel. Probabilité : conditionnelle
à une décision humaine. Impact : obligations du chapitre III (journaux six mois,
supervision art. 14, cybersécurité art. 15). Contrôle : contrat
`executable: false` vérifié en CI ; toute modification déclenche une revue
art. 6(1 ter). Bloquant pour la migration : oui. »

---

## D3 — Rétention des traces et journaux

**Décision.**

1. `retention_days: 30` est **maintenu** pour les traces d'exécution de l'agent
   tant que DiagOps n'est pas qualifié à haut risque. Ces traces sont
   minimisées (clés d'arguments, empreintes, compteurs ; `document_text`,
   `raw_arguments`, `personal_data` interdits) et aucune durée ne leur est
   imposée par l'AI Act hors haut risque.
2. **La purge à 30 jours est rendue effective** et testée avant toute
   exploitation hors laboratoire. Une durée déclarée et non appliquée est une
   non-conformité à la politique de l'agent, indépendamment du droit.
3. **Si DiagOps est qualifié à haut risque**, la rétention des journaux générés
   automatiquement est portée à **au moins six mois** (retenir 190 jours pour
   absorber les mois de 31 jours), côté fournisseur pour les journaux sous son
   contrôle et côté déployeur. Les traces restant minimisées, cette durée
   n'entre pas en conflit avec le RGPD ; si un champ personnel y entrait, la
   durée serait à arbitrer avec le référent protection des données (réserve
   « sauf disposition contraire […] protection des données » des art. 19(1) et
   26(6)).
4. Le **journal d'approbation** de l'outil à effet (acteur, empreinte, décision,
   horodatage, reçu) suit la plus longue des durées applicables : c'est la
   preuve de la supervision humaine.
5. Les **journaux d'accès**, qui n'existent pas faute d'authentification, sont
   conçus avec une conservation de six mois à un an dès que l'authentification
   est créée (recommandation CNIL). [OS]
6. Le **feedback nominatif** (`results/feedback_qualification.csv`, colonne
   `author`) n'est pas une trace : sa durée est fixée avec sa base légale (Q6),
   pas alignée par défaut sur 30 jours.

**Conditions de déclenchement.** Point 3 : qualification haut risque confirmée,
au plus tard avant le 02/12/2027 (annexe III) ou le 02/08/2028 (annexe I).
Point 5 : création de l'authentification (condition de non-déploiement n° 2 du
threat model M4). Point 2 : immédiat.

**Fondement.** AI Act art. 12(1)-(2), 19(1), 26(6), non modifiés par l'Omnibus ;
dates art. 113 c). [TP] CNIL, délibération n° 2021-122. [OS] Voie machines
(section B) : l'Omnibus demande de refléter l'art. 19 dans le règlement
machines, pas l'art. 26 ; la durée déployeur n'y serait donc pas reprise telle
quelle. [TP pour la liste, NV pour la conséquence]

**Texte ADR proposé.** « Rétention des traces d'agent : 30 jours, purge
automatique testée. Portée à six mois minimum (190 jours) si le système est
qualifié à haut risque. Journal d'approbation de l'outil à effet et journaux
d'accès : six mois minimum dès leur création. Aucune de ces durées ne s'applique
au feedback nominatif, régi par sa propre base légale. »

---

## D4 — Supervision humaine et outil à effet avec approbation

**Décision.** Le contrat d'approbation est complété, sans le rendre exécutable :

1. **Mesure du biais d'automatisation** : taux d'approbation, délai entre aperçu
   et approbation, part des aperçus modifiés ou rejetés. Une approbation en moins
   de N secondes ou un taux d'approbation proche de 100 % sur une période est
   un signal d'approbation réflexe (N à fixer par l'exercice sur table).
2. **Approbateur identifié et habilité** : `superviseur_fictif` reste un rôle de
   démonstration ; en exploitation, l'approbation exige une identité
   authentifiée et une habilitation vérifiée au moment de l'approbation, pas
   seulement à l'aperçu.
3. **Arrêt** : un interrupteur global qui refuse toute nouvelle approbation et
   laisse les états `approved` non exécutés expirer.

**Condition de déclenchement.** Immédiat pour la spécification (M7) ; bloquant
avant toute sortie du bac à sable.

**Fondement.** Art. 14(4) b) (biais d'automatisation), 14(4) d) (ignorer,
remplacer, inverser), 14(4) e) (arrêt), art. 26(2) (compétences, formation,
autorité). [TP] Applicables au haut risque seulement ; retenus ici comme
référentiel de conception, parce que l'outil à effet est précisément ce qui
pourrait faire basculer la qualification (D2).

**Déjà couvert par le contrat M7** : aperçu avant action, approbation liée à
l'empreinte exacte de l'aperçu, expiration, invalidation sur changement,
idempotence, annulation avant effet, compensation après effet.

---

## D5 — Cybersécurité : AI Act art. 15, CRA, NIS2

**Décision.**

1. DiagOps en usage interne **n'est pas soumis au CRA** : il n'est pas mis à
   disposition sur le marché. Aucun processus de notification CRA n'est créé.
2. **Déclencheur** : toute distribution de DiagOps (code, image Docker, service)
   à une entité tierce dans le cadre d'une activité commerciale, même gratuite.
   L'équipe deviendrait alors fabricant, et l'art. 14 (applicable depuis le
   11/09/2026) exigerait une alerte précoce sous 24 heures et une notification
   sous 72 heures pour toute vulnérabilité activement exploitée, par la
   plateforme unique de signalement.
3. L'art. 15(5) de l'AI Act sert de **référentiel de conception** pour la red
   team (empoisonnement, entrées adverses, attaques sur la confidentialité),
   même hors haut risque.
4. Les dépendances (FastAPI, Prometheus, images de base) relèvent du CRA côté
   de leurs fabricants ; DiagOps suit leurs avis de sécurité et tient
   l'inventaire des versions (déjà figé au contrat de versions M5).
5. NIS2 : sans effet direct sur DiagOps. Si l'exploitant est une entité
   importante (la fabrication de machines, NACE C28, figure à l'annexe II), DiagOps
   entre dans le périmètre de son SI une fois la loi française promulguée et ses
   décrets pris.

**Fondement.** CRA art. 2(1), 3 points 1-2, 14, 71 [TP] ; FAQ CRA v1.4 du
04/09/2026, FAQ 1.5 (usage propre) et section sur les SaaS [OS] ; NIS2 art. 41
et annexe II [TP] ; dossier législatif AN, séance publique inscrite au
07/10/2026 [OS].

**Texte registre des risques proposé.** « R-REG-02 — Distribution de DiagOps à un
tiers sans processus de notification CRA. Contrôle : toute diffusion hors de
l'équipe passe par une revue de conformité CRA. Bloquant pour une diffusion :
oui. »

---

## D6 — Transferts, fournisseurs d'API, sous-traitance

**Décision.** L'option cloud (génération ou embeddings par API) n'est retenue que
si les conditions suivantes sont réunies, vérifiées avant le premier appel :

1. **Contrat de sous-traitance conforme à l'art. 28(3) RGPD**, dont traitement
   sur instruction documentée y compris pour les transferts (point a),
   suppression ou restitution en fin de prestation (point g), audit (point h),
   et encadrement des sous-traitants ultérieurs (art. 28(2)).
2. **Aucune réutilisation** des requêtes et réponses par le fournisseur à ses
   propres fins (entraînement, amélioration) ; à défaut, le fournisseur devient
   responsable de traitement pour cette finalité et l'option est écartée.
3. **Traitement dans l'UE** par préférence. Si un traitement ou un accès a lieu
   aux États-Unis : l'entité contractante figure sur la liste du DPF, et une
   base de transfert de repli (art. 46) est identifiée pour le cas où la
   décision 2023/1795 serait invalidée à l'issue du pourvoi C-703/25 P.
4. **Filtrage avant envoi** : le texte libre de feedback n'est jamais transmis
   à l'API ; les questions passent par le même filtre que le qualificateur de
   feedback M6 (11 retours à risque écartés sur 124, dont 6 porteurs de données
   personnelles, 0 faux positif déclaré).
5. **Sortie éprouvée** : le retour à l'option locale est rejoué avant la
   migration (lien avec D7).

**Condition de déclenchement.** Premier appel à un service tiers, y compris en
pilote.

**Fondement.** RGPD art. 28, 45 [TP] ; décision 2023/1795 art. 1 (couverture
limitée aux organisations inscrites) et 3(5) (suspension ou abrogation
possible) [TP] ; métadonnées Cellar : arrêt T-553/23 du 03/09/2025, pourvoi
C-703/25 P du 31/10/2025, sans arrêt au 28/09/2026 [TP] ; qualification du
fournisseur d'API comme sous-traitant : raisonnement transposé de la fiche CNIL
du 08/04/2024 [NV].

**Texte registre des risques proposé.** « R-REG-03 — Invalidation du DPF en cours
de contrat. Impact : transfert sans base légale. Contrôle : région UE exigée ou
base de repli art. 46 prête ; sortie locale rejouée. »

---

## D7 — Réversibilité et Data Act chapitre VI

**Décision.**

1. Tout contrat d'hébergement cloud ou d'API retenu comporte au minimum les
   clauses de l'art. 25(2) : préavis de changement de deux mois au plus,
   transition de 30 jours au plus (sept mois si impossibilité technique motivée),
   récupération des données pendant au moins 30 jours, liste exhaustive des
   données exportables, effacement intégral après récupération.
2. **Aucun frais de changement accepté après le 12/01/2027** ; avant cette date,
   seuls des frais au coût direct sont acceptables (art. 29).
3. **Un pilote cloud n'est pas couvert** : l'art. 31(2) exclut du chapitre VI
   les versions non destinées à la production fournies pour essai et pour une
   durée limitée. Pendant un pilote, la réversibilité repose entièrement sur la
   technique : formats ouverts pour corpus, index et traces, export et
   reconstruction rejoués (comme la migration JSON → SQLite exercée en M7).
4. **Les artefacts produits par le fournisseur sont supposés non récupérables**
   tant que le contraire n'est pas établi : l'art. 2 point 38 exclut des données
   exportables ce qui relève de la propriété intellectuelle ou du secret
   d'affaires du fournisseur. En pratique, les embeddings calculés par une API
   tierce doivent pouvoir être recalculés localement à partir du corpus, qui
   reste la source de vérité.
5. Le fournisseur retenu publie les juridictions de son infrastructure (art. 28) ;
   cette information entre dans la matrice local/cloud/hybride.

**Condition de déclenchement.** Toute contractualisation d'un service de
traitement de données ; le point 3 dès le démarrage d'un pilote.

**Fondement.** Data Act art. 2 points 8, 32, 36, 38 ; art. 23, 25, 26, 28, 29,
30(5), 31, 50 ; considérant 81 [TP]. Proposition « omnibus numérique »
COM(2025) 837 : exemptions ciblées pour les petites entreprises en projet, non
adoptée (procédure 2025/0360(COD)) [OS]. Qualification d'une API de modèle comme
service de traitement de données : [NV].

**Texte ADR proposé.** « La réversibilité de DiagOps est une propriété de
l'architecture, vérifiée par un exercice de sortie rejoué. Les clauses du Data
Act, chapitre VI, sont exigées en complément, pas en substitution : elles ne
couvrent ni un pilote (art. 31(2)) ni les artefacts propres au fournisseur
(art. 2 point 38). »

---

## D8 — Calendrier AI Act après l'Omnibus et article 50

**Décision.**

1. **Mention d'interaction avec un système d'IA** affichée à la première
   interaction, dans l'API (champ de réponse) et dans toute interface. Coût
   quasi nul ; elle couvre l'art. 50(1) sans avoir à trancher l'exception
   « cela ressort clairement » ni la question D1. Écart constaté depuis le
   02/08/2026 (recommandation A1 de M4, jamais réalisée).
2. Si l'option cloud introduit une **génération non extractive** : marquage des
   sorties dans un format lisible par machine (art. 50(2)), **sans délai de
   grâce**, le transitoire au 02/12/2026 ne valant que pour les systèmes mis
   sur le marché avant le 02/08/2026. Une génération strictement extractive
   (extraits littéraux, comme en M4) relève de l'exception « ne modifient pas de
   manière substantielle les données d'entrée » ; cette lecture est à confirmer.
3. L'art. 111(2) (systèmes à haut risque déjà en service couverts seulement en
   cas d'importantes modifications de conception) **n'est pas retenu comme
   levier** : la migration vers le cloud est elle-même une modification de
   conception.
4. Maîtrise de l'IA (art. 4, applicable depuis le 02/02/2025, réécrit par
   l'Omnibus sans niveau imposé) : les supports de formation des utilisateurs
   décrivent les limites mesurées (rappel, abstentions, cas refusés).

**Condition de déclenchement.** Point 1 : immédiat. Point 2 : première réponse
générée servie par un modèle.

**Fondement.** Règlement 2026/1744 ; AI Act consolidé art. 4, 50(1), 50(2),
50(7), 111(2), 111(4), 113 [TP] ; calendrier AI Act Service Desk [OS].

---

## Questions ouvertes transmises à M8

| # | Question | Responsable (rôle) | Échéance |
|---|---|---|---|
| Q1 | La version sans modèle appris est-elle un « système d'IA » au sens de l'art. 3 point 1 (lignes directrices C(2025) 5053, § 46) ? | Compétence juridique, sur dossier technique du fournisseur | Avant la décision de migration cloud |
| Q2 | Secteur d'exploitation du parc et statut de l'exploitant : annexe III point 2 (infrastructure critique), entité NIS2 (annexe II, NACE C28) ? Ouverte depuis M4 | Exploitant du site (déployeur) | Avant toute exploitation hors laboratoire |
| Q3 | Réécrire le scénario B de `ai_act_diagops.md` sur la base de l'annexe I section B (règlement machines) | Porteur du dossier de veille | Checkpoint M8 |
| Q4 | Appliquer l'art. 6(1 ter) à un outil à effet réel : une demande d'inspection omise ou erronée met-elle en danger la santé et la sécurité ? | Compétence juridique avec le responsable maintenance de l'exploitant | Avant toute connexion de l'outil à un système réel |
| Q5 | Implémenter et tester la purge à 30 jours (dette M6) ; définir la durée du journal d'approbation et des journaux d'accès | Architecte / porteur des ADR | Avant toute exploitation hors laboratoire |
| Q6 | Base légale, information des contributeurs, durée de conservation et droits sur le feedback nominatif (Q7 du relais M6) | Référent protection des données | Avant la mise en service de la boucle de feedback hors laboratoire |
| Q7 | Les embeddings calculés par une API tierce sont-ils des « données exportables » (art. 2 point 38 Data Act) ? Une API de modèle est-elle un « service de traitement de données » (art. 2 point 8) ? | Acheteur / juriste contrats | Avant signature d'un contrat cloud |
| Q8 | Suivre le pourvoi C-703/25 P (DPF) | Référent protection des données | À chaque checkpoint ; immédiatement à l'arrêt |
| Q9 | Suivre la loi « résilience » (séance publique AN du 07/10/2026) puis les décrets NIS2 | Porteur du dossier de veille | 07/10/2026, puis à chaque checkpoint |
| Q10 | Suivre l'adoption des lignes directrices art. 6 (projet du 19/05/2026, adoption annoncée fin 2026) et du code de bonne pratique sur le marquage (art. 50(7)) | Porteur du dossier de veille | 31/12/2026 |
| Q11 | Suivre la proposition « omnibus numérique » COM(2025) 837 : modifications du RGPD, du chapitre VI du Data Act (exemptions petites entreprises) et point unique de notification des incidents | Porteur du dossier de veille | À chaque checkpoint |
| Q12 | ~~Recopier D1 à D8 dans `architecture/adr/`, `security/residual_risks.md` et le plan de migration~~ **Fait le 28/09/2026** : D1, D6, D7 → ADR-0005 ; D2, D4 → ADR-0006 et R-REG-01 ; D3 → ADR-0007 et R-16 ; D5 → R-REG-02 ; D6 → R-REG-03 ; D8 → ADR-0008 et R-17 ; plan de migration, étapes 5 et 6 | Architecte / porteur des ADR | Avant la revue indépendante M7 |
| Q13 | Vérifier le délai de frais nuls au 12/01/2027 dans tout contrat cloud signé avant cette date | Acheteur / juriste contrats | 12/01/2027 |
