# Journal de veille DiagOps

> Dossier de continuité pédagogique. **Ne constitue pas un avis juridique.**
> Chaque entrée est datée, sourcée auprès de textes officiels ou d'autorités compétentes, et
> reliée à un contrôle d'exploitation.

## Passage de relais M4 (repris tel quel)

- périmètre : assistant pédagogique de maintenance sur données synthétiques ;
- autonomie : une décision, aucun outil à effet externe ;
- état : qualification juridique industrielle non réalisée ;
- points M5 à vérifier : fournisseur d'inférence, localisation et sous-traitance, contenu et
  rétention des traces, accès opérateur, supervision humaine, traitement des incidents et
  obligations de documentation ;
- responsable : à nommer par l'équipe M5 ;
- échéance : avant la promotion du premier candidat M5.

---

## Entrée M5 — 7 septembre 2026

**Responsable** : Nicolas Lebon (les quatre rôles d'exploitation sont tenus par la même personne
en formation — voir `docs/runbook.md`).

### Sources consultées le 07/09/2026

| Source | Nature | Ce qu'elle établit |
|---|---|---|
| [Règlement (UE) 2026/1744](https://eur-lex.europa.eu/eli/reg/2026/1744/oj/eng) — « Digital Omnibus on AI », JO L du 24/07/2026 | **Officielle** (EUR-Lex) | Modifie le règlement (UE) 2024/1689. Adopté le 8 juillet 2026, **en vigueur depuis le 27 juillet 2026** |
| [Cadre réglementaire IA](https://digital-strategy.ec.europa.eu/en/policies/regulatory-framework-ai) — Commission européenne | **Officielle** | Calendrier d'application à jour après l'Omnibus |
| [AI Act Explorer — Digital Omnibus](https://artificialintelligenceact.eu/ai-act-explorer/digital-omnibus/) | Secondaire | Détail article par article des reports |

> **Limite de méthode à signaler.** Le texte intégral d'EUR-Lex n'a pas pu être lu directement
> avec les outils disponibles (la page ne rend pas son contenu). Les dates ci-dessous viennent de
> la page officielle de la Commission, recoupée avec une source secondaire spécialisée. Les
> références de publication du règlement, elles, sont bien issues d'EUR-Lex. **Une lecture du
> texte consolidé reste à faire** avant toute conclusion engageante.

### Ce qui a changé depuis le relais M4

Le **Digital Omnibus on AI** a reporté l'essentiel des obligations « haut risque ». Le calendrier
au 07/09/2026 :

| Échéance | Ce qui s'applique |
|---|---|
| 2 février 2025 | Interdictions (art. 5), littératie IA (art. 4) |
| 2 août 2025 | Gouvernance, obligations GPAI, sanctions |
| **2 août 2026** | **Application générale** ; obligations de transparence (art. 50) |
| 2 décembre 2026 | Art. 50(2) étendu aux systèmes déjà sur le marché ; nouvelles interdictions (contenus intimes non consentis, CSAM) |
| **2 décembre 2027** | **Haut risque Annexe III** — art. 6, et avec lui la journalisation (art. 12), la supervision humaine (art. 14), le signalement d'incidents graves (art. 73). *Report de 16 mois* |
| 2 août 2028 | Haut risque intégré à des produits (Annexe I) |

**Le point qui compte pour M5** : les trois articles que ce module aurait le plus directement
touchés — journalisation, supervision humaine, signalement d'incidents — **ne sont pas
applicables avant le 2 décembre 2027**. Au relais M4, ils étaient attendus pour le 2 août 2026.

### Analyse pour DiagOps

DiagOps reste **hors du champ « haut risque »** pour trois raisons cumulatives, inchangées depuis
M4 et revérifiées :

1. **Pas un cas d'usage de l'Annexe III** — assistance documentaire à la maintenance industrielle,
   sur données synthétiques. Ni emploi, ni crédit, ni biométrie, ni accès à un service essentiel.
2. **Aucune donnée personnelle** — le corpus est synthétique et déclaré comme tel dans sa data
   card. Le RGPD ne trouve pas de prise.
3. **Aucune décision autonome** — l'agent reste borné à une action, sans effet externe. Le
   périmètre déclaré dans le manifeste de release est `pedagogical_preproduction_only`.

**Transparence (art. 50), applicable depuis le 2 août 2026** : le seul article dont la date n'a
pas bougé. Il vise les systèmes qui interagissent avec des personnes ou génèrent du contenu.
`POST /search` **ne génère rien** — il retourne des identifiants de documents et des références
de révision. Il n'y a ni contenu synthétique à marquer, ni risque qu'un utilisateur prenne une
sortie de modèle pour un fait établi. **Conclusion : pas d'obligation déclenchée**, et c'est la
conception qui le garantit, pas une exemption.

> Le jour où une couche de génération est introduite — elle est annoncée pour M6 — cette
> conclusion tombe. C'est la première question du passage de relais ci-dessous.

### Décision : aucun changement réglementaire ne modifie une obligation

Cette entrée conclut à **l'absence de changement contraignant** pour DiagOps. Le brief autorise
explicitement cette conclusion, à condition qu'elle soit sourcée — elle l'est.

### Contrôles d'exploitation reliés

Le brief exige que la décision soit traduite dans un gate, une alerte, un accès aux traces ou le
runbook. Trois contrôles portent cette décision — et **ils préexistaient**, ce qui est le point :
la minimisation n'a pas été construite parce que le droit l'exigeait, mais parce qu'elle est la
bonne conception. Le report de décembre 2027 ne les remet pas en cause.

| Contrôle | Où | Ce qu'il tient |
|---|---|---|
| **Minimisation des traces** | `src/observability.py`, `tests/test_observability.py` | Aucune donnée métier dans un label. Vérifié par test : une question contenant un numéro et le mot « patient » n'apparaît nulle part dans l'exposition |
| **Rétention et accès** | `deploy/compose.yaml`, `docs/runbook.md` | Métriques 7 jours, artefacts CI 14 jours, historique d'index non purgé. Point ouvert : Prometheus est exposé **sans authentification** — acceptable en laboratoire local, à ne pas reconduire |
| **Cloisonnement par rôle** | `pipelines/ingest.py`, `tests/test_security_gates.py` | Un document `restreint` ouvert au rôle `public` est refusé à l'admission. `diagops_restricted_citations_total > 0` déclenche une escalade sécurité immédiate |

**Aucun gate CI n'a été modifié par cette entrée.** Ajouter un contrôle réglementaire qui ne
correspond à aucune obligation applicable reviendrait à fabriquer de la conformité de façade.

### Fournisseurs et sous-traitance

Point du relais M4 traité : **il n'y a aujourd'hui aucun fournisseur d'inférence**. Le retrieval
est lexical, local et déterministe. Les seules dépendances externes sont deux images publiques,
dont les digests sont figés au contrat de versions — pas de traitement de données par un tiers,
donc pas de question de localisation ni de sous-traitance.

---

## Passage de relais M5 vers M6

| # | Question ouverte | Responsable | Échéance |
|---|---|---|---|
| 1 | **L'introduction d'une couche de génération en M6 déclenche-t-elle l'art. 50 ?** Un système qui produit du texte destiné à une personne relève de la transparence, applicable depuis le 2 août 2026 — sans report | Équipe M6 | Avant la première réponse générée servie |
| 2 | **Un fournisseur d'inférence externe rouvre les questions de localisation, sous-traitance et rétention** laissées ouvertes par M4 | Équipe M6 | Avant tout appel à un service tiers |
| 3 | **La boucle de feedback humain annoncée en M6 crée-t-elle un traitement de données personnelles ?** Un retour d'utilisateur est rattaché à une personne, contrairement au corpus synthétique | Équipe M6 | Avant la mise en place de la boucle |
| 4 | **Lire le texte consolidé du règlement 2024/1689 tel que modifié**, plutôt que les pages de synthèse — limite de méthode assumée dans cette entrée | Équipe M6 | Avant toute conclusion engageante |
| 5 | **Le report au 2 décembre 2027 peut encore bouger.** L'Omnibus est passé six jours avant l'échéance qu'il repoussait : le calendrier n'est pas un acquis | Équipe M6 | À revérifier à chaque checkpoint |
