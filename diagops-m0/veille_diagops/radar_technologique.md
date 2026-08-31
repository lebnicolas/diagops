# Radar technologique — DiagOps

> Brief 3, livrable 4. Consolidé au **M4**, le 31/08/2026.
> Ne recense que ce qui **touche une décision technique de DiagOps**. Un radar
> qui liste tout ce qui bouge dans l'IA n'aide personne à décider.

---

## Méthode

Trois canaux, décrits dans `sources_veille.md` :

- **collecte automatique** — `scripts/veille-digest.mjs` sur srv909692, timer
  systemd quotidien, digest hebdomadaire le vendredi. Opérationnel depuis le
  21/07/2026, il tournait encore le 31/08 à 09:00 ;
- **consultation ponctuelle** des sources sans flux (Mistral, LM Studio) ;
- **vérification ciblée** au moment où une décision se pose — c'est le cas de
  cette consolidation.

> **Aveu de méthode.** Entre le 21/07 et le 31/08, la collecte a tourné mais
> **le dépouillement n'a pas suivi**. Les entrées ci-dessous viennent de
> vérifications faites le 31/08 pour les besoins du M4, pas d'un suivi
> hebdomadaire régulier. Le dispositif technique fonctionnait ; la discipline
> humaine, non. C'est le premier écart à corriger en M5.

---

## R1 — Modèles d'embeddings multilingues

**Décision concernée** : arbitrage A4 du brief 1 — `intfloat/multilingual-e5-small`.

**État vérifié le 31/08/2026.** `mE5-small` reste une référence défendable pour
un corpus francophone à faible volume : nDCG@10 de 60,8 et R@100 de 92,4 sur les
bancs multilingues, pour 118 M paramètres et 384 dimensions
([rapport technique mE5](https://arxiv.org/pdf/2402.05672), source primaire des
auteurs, statut `article`).

**Alternatives identifiées, non testées** : `jina-embeddings-v3` (optimisé pour
30 langues dont le français), la famille `granite-embedding` d'IBM (une révision
R2 est parue), et `bilingual-embedding-small`.

**Impact sur DiagOps** : nul à court terme. Sur 8 documents et 6 Ko, le Recall@1
sature à 1,000 pour toutes les stratégies testées — aucun modèle d'embeddings ne
peut se distinguer sur ce corpus. Changer de modèle avant d'avoir un corpus qui
discrimine serait une optimisation sans mesure.

**Décision : `maintenir`.** Réévaluer si le corpus dépasse quelques centaines de
documents, ou si l'épreuve de reformulation (0,700 pour le vectoriel contre
0,300 pour le lexical) devient un critère opérationnel.

---

## R2 — Injection indirecte et empoisonnement de base documentaire

**Décision concernée** : `THR-001` et `THR-005` du threat model, et la condition
de non-déploiement n° 3.

**État vérifié le 31/08/2026.** Le sujet s'est nettement durci :

- des travaux de janvier 2026 rapportent que **cinq documents soigneusement
  construits suffisent à manipuler 90 % des réponses** d'un système RAG par
  empoisonnement du corpus ;
- l'OWASP maintient que **ni le RAG ni le fine-tuning ne résolvent l'injection**
  — un LLM ne distingue pas de façon fiable une instruction d'une donnée dans son
  entrée. L'injection reste en tête de sa liste des menaces LLM ;
- les défenses qui progressent sont **architecturales**, pas comportementales :
  séparation de privilèges, validation de sortie, recherche hybride (l'attaquant
  doit alors manipuler l'index lexical *et* l'espace vectoriel), re-ranking par
  un modèle indépendant, listes d'outils autorisées au niveau passerelle.

*Sources : principalement des analyses secondaires et des préprints arXiv,
statut `analyse` et `préprint non relu`. Aucune source réglementaire ou
normative primaire sur ce point.*

**Impact sur DiagOps — et c'est le point le plus important du radar.**

Notre campagne de menaces a montré que l'injection indirecte n'a **aucun effet**
sur le système actuel. Le threat model le dit sans complaisance : ce n'est pas
une défense, c'est **l'absence de composant interprétant**. Aucun texte n'est lu
comme une instruction parce que rien n'interprète.

> La veille confirme que cette immunité est **entièrement conditionnelle à
> l'architecture**. Le jour où un modèle génératif entre dans DiagOps, le système
> hérite d'un problème que l'état de l'art déclare non résolu — et les cinq
> documents de l'étude suffiraient.

**Décision : `maintenir`** la génération extractive tant qu'aucun besoin
opérationnel n'impose de la remplacer. Et si elle est remplacée : hybride,
re-ranking, séparation de privilèges — au minimum. C'est reporté dans
`recommandations_architecture_m4.md`.

---

## R3 — Détection de contenu synthétique

**Décision concernée** : le modèle de provenance, cible du brief 1.

**État.** Le brief 2 du M3 avait établi le fait qui compte, et il vient de nos
propres mesures plutôt que de la littérature : **un générateur qui s'améliore
devient plus difficile à distinguer**, et un détecteur qui ne signale rien ne
prouve rien. Le détecteur de référence du formateur avait rendu le même verdict
sur deux états successifs d'un générateur mesurablement inégaux.

**Impact sur DiagOps.** Le modèle du M4 détecte les fabrications *du générateur
du formateur*. La model card l'écrit en limite n° 5. Rien ne garantit qu'il
détecterait un autre procédé.

**Décision : `évaluer`** — réévaluation obligatoire à chaque livraison de données
ou changement de procédé de génération, déjà inscrite à la model card.

---

## R4 — Petits modèles et exécution locale

**Décision concernée** : le socle d'exécution DiagOps (M0 : LM Studio,
ministral-3-3b) et le coût d'exploitation de la matrice de décision.

**État.** Pas de vérification ciblée conduite ce mois-ci. Le sujet n'a pas
d'effet sur une décision ouverte du M4 : la génération est extractive, donc
aucun modèle de langue n'est en service.

**Décision : `maintenir`** en observation, sans action. À rouvrir si R2 conduit à
introduire un modèle génératif — c'est alors le choix du modèle **et** de son
lieu d'exécution qui se pose, avec les conséquences de souveraineté que le M7
traitera.

---

## Synthèse — ce qui bouge et ce qui ne bouge pas

| # | Sujet | Mouvement observé | Décision | Échéance |
|---|---|---|---|---|
| R1 | embeddings multilingues | incrémental, plusieurs alternatives | `maintenir` | corpus > quelques centaines de documents |
| **R2** | **injection indirecte** | **durcissement net, non résolu** | **`maintenir` l'extraction** | avant toute introduction d'un LLM |
| R3 | détection de synthétique | établi par nos mesures M3 | `évaluer` | à chaque livraison |
| R4 | petits modèles locaux | non instruit ce mois-ci | `maintenir` | conditionné à R2 |

**Le radar tient en une phrase** : rien de ce qui bouge n'impose de changer une
décision du M4, et un seul sujet — l'injection indirecte — rend une décision du
M4 **structurante pour la suite** plutôt que provisoire.
