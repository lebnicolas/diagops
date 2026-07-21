# Cartographie des sources de veille — DiagOps

> Brief 3 — Livrable 1. Créé le 21/07/2026. Les mentions « vérifié le JJ/MM/AAAA » indiquent la date à laquelle l'existence et le moyen de suivi de la source ont été contrôlés.

## Méthode de veille

La veille suit un circuit en quatre temps : **collecter → qualifier → analyser → décider**.

### Collecte — quatre canaux

| Canal | Fonctionnement | Sources concernées |
|---|---|---|
| Alertes email | Boîte de veille dédiée avec dossier et filtre spécifiques | EUR-Lex, AI Act Service Desk, The Batch |
| Flux RSS | Flux agrégés par un script maison qui envoie un digest email hebdomadaire des nouveautés | CNIL, arXiv cs.CL, blog Hugging Face, ActuIA, Simon Willison |
| Watch de dépôt GitHub | « Watch → Releases » : notification à chaque note de version | FastAPI, Transformers, Qwen |
| Consultation périodique | Créneau fixe hebdomadaire ; rythme adapté à la fréquence de la source | Commission européenne, NeurIPS, ACL Anthology, LM Studio, Mistral AI |

### Rythme

Dépouillement **chaque vendredi à 9h30, 30 minutes** : lecture du digest RSS (livré avant le créneau), des alertes email de la semaine et des pages en consultation périodique. Ce qui franchit la grille de qualification devient une entrée du [journal de veille](journal_veille.md).

### Grille de qualification

Chaque information retenue passe les trois questions du brief :

1. **La source est-elle suffisamment fiable et autoritative ?** Critères : primaire avant secondaire ; autorité de l'émetteur (qui engage sa responsabilité si l'information est fausse ?) ; intérêts commerciaux ou institutionnels ; relecture par les pairs pour le scientifique.
2. **Qu'est-ce qui a réellement changé, et à quelle date ?** Distinguer systématiquement date de publication, date d'entrée en vigueur et date d'application pour le réglementaire ; dater chaque consultation.
3. **Quelle décision DiagOps ?** Chaque entrée de journal aboutit à `maintenir`, `évaluer`, `modifier` ou `écarter`.

---

## Famille 1 — Textes réglementaires et autorités publiques

### EUR-Lex — Règlement (UE) 2024/1689 (AI Act)

| Champ | Valeur |
|---|---|
| Organisme | Office des publications de l'Union européenne |
| URL | <https://eur-lex.europa.eu/eli/reg/2024/1689/oj/fra> |
| Nature | Primaire — le texte de droit lui-même |
| Domaine | Réglementaire (AI Act : texte, actes délégués, rectificatifs, versions consolidées) |
| Fréquence | Publication continue du Journal officiel |
| Autorité | Maximale : seule source faisant foi juridiquement |
| Moyen de suivi | Alerte email/RSS sur le document via compte My EUR-Lex (fonctionnalité vérifiée le 21/07/2026 ; limite de 50 alertes par compte) |
| Limites, biais | Publie le droit mais ne l'interprète pas : aucune aide à la qualification. Lecture aride ; nécessite les sources d'accompagnement ci-dessous. |

### Commission européenne — Cadre réglementaire de l'IA

| Champ | Valeur |
|---|---|
| Organisme | Commission européenne, DG CONNECT |
| URL | <https://digital-strategy.ec.europa.eu/fr/policies/regulatory-framework-ai> |
| Nature | Primaire (positions officielles de la Commission) |
| Domaine | Réglementaire : calendrier d'application, lignes directrices, communication politique |
| Fréquence | Irrégulière, au rythme des étapes réglementaires |
| Autorité | Élevée — mais la communication n'est pas le texte de droit |
| Moyen de suivi | Consultation périodique (vendredi) : la page ne propose ni RSS ni newsletter, seulement des liens réseaux sociaux (constaté le 21/07/2026) |
| Limites, biais | La Commission promeut sa propre politique : ton institutionnel valorisant. Ne pas confondre une page de communication avec une obligation juridique — toujours redescendre vers EUR-Lex. |

### AI Act Service Desk

| Champ | Valeur |
|---|---|
| Organisme | Commission européenne (plateforme d'information unique / SIP) |
| URL | <https://ai-act-service-desk.ec.europa.eu/> |
| Nature | Primaire (guidance officielle), sans valeur contraignante |
| Domaine | Réglementaire appliqué : FAQ, AI Act Explorer, Compliance Checker |
| Fréquence | Mises à jour au fil des lignes directrices et retours des parties prenantes |
| Autorité | Élevée pour l'accompagnement ; les réponses ne constituent pas un avis juridique |
| Moyen de suivi | Abonnement email « SIP updates » (vérifié le 21/07/2026 ; pas de RSS) |
| Limites, biais | Contenu explicatif simplifié : utile pour s'orienter, insuffisant pour qualifier. Les outils d'aide (Compliance Checker) ne remplacent ni le texte ni une validation juridique. |

### CNIL — Intelligence artificielle

| Champ | Valeur |
|---|---|
| Organisme | Commission nationale de l'informatique et des libertés (autorité française) |
| URL | <https://www.cnil.fr/fr/intelligence-artificielle> |
| Nature | Primaire (doctrine et recommandations d'une autorité de contrôle) |
| Domaine | Données personnelles × IA, recommandations pratiques, articulation RGPD/AI Act |
| Fréquence | Plusieurs publications par mois (flux actif constaté le 21/07/2026 : articles IA des 9 et 20 juillet) |
| Autorité | Élevée en France ; influente au niveau européen via le CEPD |
| Moyen de suivi | Flux RSS <https://www.cnil.fr/fr/rss.xml> (vérifié le 21/07/2026) → digest hebdomadaire |
| Limites, biais | Lecture française et prisme « protection des données » : la CNIL n'est pas l'autorité de surveillance désignée pour tout l'AI Act, et sa doctrine ne lie pas les autres États membres. |

---

## Famille 2 — Publications scientifiques et actes de conférences

La famille est construite sur la complémentarité **détection → validation** : arXiv voit passer les travaux des mois avant leur validation ; les conférences à comité de lecture disent ce qui a survécu à la relecture par les pairs.

### arXiv — catégorie cs.CL (Computation and Language)

| Champ | Valeur |
|---|---|
| Organisme | arXiv (Cornell University), dépôts par les auteurs |
| URL | <https://arxiv.org/list/cs.CL/recent> |
| Nature | Primaire (préprints) |
| Domaine | Recherche LLM/NLP : modèles, RAG, évaluation, techniques d'adaptation |
| Fréquence | Quotidienne, volume élevé (dizaines de papiers/jour) |
| Autorité | Moyenne : source primaire mais **non relue par les pairs** |
| Moyen de suivi | Flux RSS <https://rss.arxiv.org/rss/cs.CL> → digest hebdomadaire, tri par titre + abstract uniquement |
| Limites, biais | Aucune validation scientifique au dépôt : résultats parfois non reproductibles ou survendus. Le volume impose un tri brutal ; un préprint cité dans le journal de veille est toujours marqué comme tel. |

### NeurIPS — actes de la conférence

| Champ | Valeur |
|---|---|
| Organisme | Neural Information Processing Systems Foundation |
| URL | <https://proceedings.neurips.cc/> |
| Nature | Primaire, relue par les pairs |
| Domaine | Machine learning au sens large : architectures, apprentissage, évaluation, sécurité |
| Fréquence | Annuelle (conférence en décembre, actes en libre accès) |
| Autorité | Très élevée (conférence de premier rang, sélection sévère) |
| Moyen de suivi | Consultation annuelle à la parution des actes, filtrée sur les *orals* et *spotlights* (tri déjà opéré par le comité) |
| Limites, biais | Lenteur structurelle : l'état de l'art publié a 6 à 12 mois. Volume énorme (milliers de papiers acceptés) ; biais académique vers la nouveauté plutôt que l'applicabilité industrielle. |

### ACL Anthology

| Champ | Valeur |
|---|---|
| Organisme | Association for Computational Linguistics |
| URL | <https://aclanthology.org/> |
| Nature | Primaire, relue par les pairs |
| Domaine | Traitement du langage : archive libre de toutes les conférences ACL, EMNLP, NAACL, etc. |
| Fréquence | Alimentée en continu au rythme des conférences (plusieurs par an) |
| Autorité | Très élevée sur le NLP — le pendant validé du flux arXiv cs.CL |
| Moyen de suivi | Consultation périodique après chaque conférence majeure du calendrier ACL |
| Limites, biais | Couvre le langage uniquement ; même délai structurel que toute publication relue. Interface de recherche sommaire. |

---

## Famille 3 — Documentation technique primaire

Critère de sélection : les outils dont un changement impacte directement ce que DiagOps construit. Biais commun à toute la famille : **l'éditeur parle de son propre produit** — la documentation ne signale ni les régressions ni les faiblesses face à la concurrence.

### FastAPI (et Pydantic)

| Champ | Valeur |
|---|---|
| Organisme | Projet open source (mainteneur principal : Sebastián Ramírez) |
| URL | <https://fastapi.tiangolo.com/> — releases : <https://github.com/fastapi/fastapi/releases> |
| Nature | Primaire (documentation et notes de version officielles) |
| Domaine | Framework d'API de DiagOps ; validation Pydantic |
| Fréquence | Releases fréquentes (plusieurs par mois) |
| Autorité | Élevée — référence du projet lui-même |
| Moyen de suivi | Watch GitHub → Releases |
| Limites, biais | Projet très dépendant d'un mainteneur central. Les notes de version minimisent l'impact des changements de comportement ; tester avant de monter de version. |

### LM Studio

| Champ | Valeur |
|---|---|
| Organisme | LM Studio (Element Labs) — produit propriétaire gratuit |
| URL | <https://lmstudio.ai/docs> |
| Nature | Primaire (documentation éditeur) |
| Domaine | Serving local des modèles de DiagOps (API compatible OpenAI sur localhost:1234) |
| Fréquence | Releases régulières de l'application |
| Autorité | Élevée sur son propre produit, sans plus |
| Moyen de suivi | Consultation périodique (vendredi) + notifications de mise à jour dans l'application ; pas de dépôt public de l'application |
| Limites, biais | Produit fermé : pas de code source à auditer, roadmap opaque. La documentation peut être en retard sur l'application — régression vécue sur DiagOps M0 : worker d'embeddings `nomic` cassé, non documenté. |

### Hugging Face — documentation Transformers

| Champ | Valeur |
|---|---|
| Organisme | Hugging Face |
| URL | <https://huggingface.co/docs/transformers> — releases : <https://github.com/huggingface/transformers/releases> |
| Nature | Primaire (documentation et notes de version officielles) |
| Domaine | Écosystème des modèles ouverts : chargement, quantization, fine-tuning |
| Fréquence | Releases rapprochées, documentation mise à jour en continu |
| Autorité | Élevée — bibliothèque de référence du domaine |
| Moyen de suivi | Watch GitHub → Releases |
| Limites, biais | Rythme de release soutenu avec changements de comportement fréquents. Hugging Face a des intérêts commerciaux (Hub, services payants) qui orientent la documentation vers son propre écosystème. |

---

## Famille 4 — Model cards, dépôts et notes de version des fournisseurs

Critère de sélection : les fournisseurs des modèles réellement utilisés ou évalués par DiagOps. Biais commun : la model card est **auto-déclarative** — c'est le fournisseur qui décrit son modèle, sans vérification indépendante.

### Mistral AI

| Champ | Valeur |
|---|---|
| Organisme | Mistral AI (fournisseur du modèle de production DiagOps : ministral-3-3b) |
| URL | <https://mistral.ai/news> — model cards : <https://huggingface.co/mistralai> |
| Nature | Primaire (annonces et model cards du fournisseur) |
| Domaine | Modèles, licences, conditions d'usage |
| Fréquence | Plusieurs annonces par mois (constaté le 21/07/2026) |
| Autorité | Élevée sur ses propres modèles |
| Moyen de suivi | Consultation périodique (vendredi) : le blog n'offre ni RSS ni newsletter (constaté le 21/07/2026) ; model cards suivies via l'organisation Hugging Face |
| Limites, biais | Communication commerciale : benchmarks choisis à l'avantage du fournisseur. Model cards parfois lacunaires sur les données d'entraînement — point sensible pour l'analyse AI Act (obligations des fournisseurs de modèles). |

### Hugging Face Hub — model cards

| Champ | Valeur |
|---|---|
| Organisme | Hugging Face (hébergeur) ; cartes rédigées par chaque fournisseur |
| URL | <https://huggingface.co/models> — annonces : <https://huggingface.co/blog> |
| Nature | Primaire (model cards originales), qualité variable |
| Domaine | Point central de distribution des modèles ouverts : poids, licences, cartes |
| Fréquence | Continue ; blog quasi quotidien (constaté le 21/07/2026) |
| Autorité | Le Hub fait référence comme canal de distribution ; l'autorité de chaque carte dépend de son auteur |
| Moyen de suivi | Flux RSS du blog <https://huggingface.co/blog/feed.xml> (vérifié le 21/07/2026) → digest hebdomadaire |
| Limites, biais | Aucune vérification centrale des cartes : champs licence ou données d'entraînement parfois vides ou inexacts. Toujours croiser la carte avec la licence réelle du dépôt. |

### Qwen (Alibaba Cloud)

| Champ | Valeur |
|---|---|
| Organisme | Alibaba Cloud — équipe Qwen (famille évaluée sur DiagOps : qwen3.5-9b, écartée pour latence) |
| URL | <https://github.com/QwenLM> — model cards : <https://huggingface.co/Qwen> |
| Nature | Primaire (dépôts, notes de version, model cards) |
| Domaine | Modèles ouverts alternatifs ; suivi du rythme des poids ouverts |
| Fréquence | Releases régulières |
| Autorité | Élevée sur ses propres modèles |
| Moyen de suivi | Watch GitHub → Releases sur les dépôts QwenLM |
| Limites, biais | Documentation parfois d'abord en chinois, traduction décalée. Communication fournisseur (mêmes réserves que Mistral). Contexte géopolitique à garder en tête dans les analyses de dépendance. |

---

## Famille 5 — Presse spécialisée et analyses secondaires

Rôle : couverture périphérique des axes non suivis en profondeur, et détection de signaux à remonter ensuite vers les sources primaires. **Règle du brief : une source secondaire n'est jamais utilisée comme seule preuve quand une source primaire existe.**

### ActuIA

| Champ | Valeur |
|---|---|
| Organisme | ActuIA (presse spécialisée IA, France) |
| URL | <https://www.actuia.com/> |
| Nature | Secondaire |
| Domaine | Actualité IA généraliste en français : industrie, réglementation, écosystème européen |
| Fréquence | Quotidienne (flux actif constaté le 21/07/2026) |
| Autorité | Moyenne — presse spécialisée, pas d'autorité normative |
| Moyen de suivi | Flux RSS <https://www.actuia.com/feed/> (vérifié le 21/07/2026) → digest hebdomadaire |
| Limites, biais | Dépend largement des communiqués et annonces : angle éditorial favorable à l'écosystème IA francophone. Tout fait significatif est revérifié à la source primaire. |

### The Batch (DeepLearning.AI)

| Champ | Valeur |
|---|---|
| Organisme | DeepLearning.AI (Andrew Ng) |
| URL | <https://www.deeplearning.ai/the-batch/> |
| Nature | Secondaire (synthèse hebdomadaire commentée) |
| Domaine | Panorama hebdomadaire de l'IA : recherche, industrie, régulation, vu des États-Unis |
| Fréquence | Hebdomadaire (vérifié le 21/07/2026) |
| Autorité | Moyenne à élevée pour la synthèse — signature reconnue, mais lecture d'opinion |
| Moyen de suivi | Newsletter email (boîte de veille dédiée) |
| Limites, biais | Émane d'une entreprise de formation : intérêt à entretenir l'enthousiasme du domaine. Prisme américain — la réglementation européenne y est traitée en observateur extérieur. |

### Simon Willison's Weblog

| Champ | Valeur |
|---|---|
| Organisme | Simon Willison (indépendant, créateur de Datasette, contributeur open source de longue date) |
| URL | <https://simonwillison.net/> |
| Nature | Secondaire (analyses d'expert, tests reproductibles) |
| Domaine | LLM appliqués : outillage, prompt injection, évaluation pratique des modèles à leur sortie |
| Fréquence | Quasi quotidienne (flux actif vérifié le 21/07/2026) |
| Autorité | Élevée dans la communauté des praticiens LLM ; indépendant des fournisseurs |
| Moyen de suivi | Flux Atom <https://simonwillison.net/atom/everything/> (vérifié le 21/07/2026) → digest hebdomadaire |
| Limites, biais | Blog personnel : un seul regard, centré outillage et usage pratique, peu de recul académique. Ses tests rapides ne valent pas un benchmark systématique. |

---

## Synthèse

| # | Source | Famille | Nature | Canal de collecte |
|---|---|---|---|---|
| 1 | EUR-Lex 2024/1689 | Réglementaire | Primaire | Alerte email My EUR-Lex |
| 2 | Commission — cadre IA | Réglementaire | Primaire | Consultation périodique |
| 3 | AI Act Service Desk | Réglementaire | Primaire | Abonnement email SIP |
| 4 | CNIL | Réglementaire | Primaire | RSS → digest |
| 5 | arXiv cs.CL | Scientifique | Primaire (préprints) | RSS → digest |
| 6 | NeurIPS | Scientifique | Primaire (relu) | Consultation annuelle |
| 7 | ACL Anthology | Scientifique | Primaire (relu) | Consultation périodique |
| 8 | FastAPI | Doc technique | Primaire | Watch GitHub Releases |
| 9 | LM Studio | Doc technique | Primaire | Consultation périodique |
| 10 | HF Transformers | Doc technique | Primaire | Watch GitHub Releases |
| 11 | Mistral AI | Fournisseurs | Primaire | Consultation périodique + HF |
| 12 | HF Hub (model cards) | Fournisseurs | Primaire | RSS blog → digest |
| 13 | Qwen | Fournisseurs | Primaire | Watch GitHub Releases |
| 14 | ActuIA | Presse | Secondaire | RSS → digest |
| 15 | The Batch | Presse | Secondaire | Newsletter email |
| 16 | Simon Willison | Presse | Secondaire | RSS → digest |
