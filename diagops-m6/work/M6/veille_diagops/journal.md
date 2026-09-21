# Journal de veille DiagOps — M6

> Dossier de continuité pédagogique. **Ne constitue pas un avis juridique.**
> Chaque entrée est datée, reliée à un contrôle d'exploitation, et déclare ce
> qu'elle n'a pas pu vérifier.

## Passage de relais M5 (repris tel quel)

| # | Question ouverte | Échéance annoncée |
|---|---|---|
| 1 | L'introduction d'une couche de génération en M6 déclenche-t-elle l'art. 50 ? | avant la première réponse générée servie |
| 2 | Un fournisseur d'inférence externe rouvre localisation, sous-traitance et rétention | avant tout appel à un service tiers |
| 3 | La boucle de feedback humain crée-t-elle un traitement de données personnelles ? | avant la mise en place de la boucle |
| 4 | Lire le texte consolidé du règlement 2024/1689 tel que modifié | avant toute conclusion engageante |
| 5 | Le report au 2 décembre 2027 peut encore bouger | à revérifier à chaque checkpoint |

---

## Entrée M6 — 21 septembre 2026

**Responsable** : Nicolas Lebon.

### Ce que le module a introduit

Un agent **outillé** — cinq outils de lecture, une liste blanche gelée, un budget
d'exécution — et une **boucle de feedback** alimentée par 124 retours d'utilisateurs
identifiés. Aucune capacité de génération, aucun appel externe.

### Les cinq questions du relais M5, une par une

**1 — Couche de génération et article 50 : NON, et c'est vérifiable dans le code.**

M6 n'introduit **aucune génération**. L'agent compose une phrase gabarit à partir
des références qu'il a obtenues (`_conclude` dans `agent/runner.py` : « Réponse
fondée sur : … »). Aucun modèle de langage n'est appelé — ni localement, ni à
distance. La conclusion du M5 tient donc sans changement : **l'article 50 n'est pas
déclenché**, parce qu'aucun contenu n'est produit par un système d'IA à destination
d'une personne.

> La réserve du M5 reste entière et se reporte à M7 : *le jour où une couche de
> génération est introduite, cette conclusion tombe.*

**2 — Fournisseur d'inférence externe : NON.**

`requirements.lock` du module ne contient que `pytest` et `PyYAML`. Aucun appel
réseau dans les cinq adaptateurs (vérifié à l'étape 1 : les deux seules ouvertures
de fichier du module sont en lecture). Localisation, sous-traitance et rétention
chez un tiers restent donc **sans objet**, comme en M5.

**3 — La boucle de feedback crée-t-elle un traitement de données personnelles ?
OUI. C'est le seul changement réel de la période.**

C'est la question que le M5 avait posée en anticipant, et la réponse est nette :

| Constat | Mesure |
|---|---|
| chaque retour porte un **identifiant d'auteur** et un **rôle** | `submitted_by_id`, `submitted_by_role` — 18 auteurs identifiés |
| des commentaires contiennent des données personnelles **en clair** | **6 sur 124** : un numéro de téléphone mobile, un matricule nominatif, deux noms de personnes |
| des commentaires tentent de reconfigurer le système | **5 sur 124** |
| la qualification produit un fichier **nominatif persistant** | `results/feedback_qualification.csv`, colonne `author` |

Jusqu'à M6, le corpus était synthétique et les traces minimisées : **aucune donnée
personnelle n'entrait dans le système**. Le canal de feedback en fait entrer, et il
le fait par un chemin que personne ne contrôle — le texte libre.

### Décision : il y a un changement, et il se traduit dans un gate

Contrairement à l'entrée M5, celle-ci ne conclut pas à l'absence d'impact.

| Ce qui change | Traduction concrète | État |
|---|---|---|
| un retour peut porter une donnée personnelle | le qualificateur les classe `risque` et les écarte — 11 détections, **0 faux positif** | existait, **désormais vérifié par un gate** |
| rien n'empêchait qu'un retour à risque alimente une amélioration | **`eval/gate_promotion.py`** — nouveau : le gate refuse la promotion si la qualification n'a pas eu lieu ou si une exportation a été faite | **créé le 21/09** |
| le feedback qualifié persiste sous forme nominative | rétention non implémentée — voir dette ci-dessous | **ouvert** |
| un retour ne dit pas quelle **version** il juge | 16 retours sur 64 décrivent un comportement que le système ne produit pas (§5 de `docs/qualification_feedback.md`) | **ouvert**, porté à M7 |

Le gate vérifie six conditions avant toute promotion : jeu gelé conforme à son
empreinte, aucune régression, campagne adversariale sans violation, traces
projetées sur le contrat sans champ interdit, **feedback qualifié avec retours à
risque écartés et aucune exportation**, décision humaine tracée. Il rend `PASS` au
21/09.

> C'est la première fois depuis M4 qu'une entrée de veille **crée** un contrôle au
> lieu d'en relier un qui préexistait. La raison est simple : c'est la première
> fois qu'une donnée personnelle entre réellement dans le système.

### Dette assumée : la rétention

`retention_days: 30` est déclaré dans la politique et **rien ne purge**. Le constat
est de l'étape 2 ; la période le rend plus coûteux, puisque les fichiers concernés
sont désormais nominatifs. Une durée de rétention annoncée et non appliquée est une
promesse non tenue — et elle porte maintenant sur des données personnelles.

Deux voies, aucune retenue à ce stade : purge au démarrage du harness (simple,
mais elle efface des preuves d'évaluation avec les traces d'exploitation), ou purge
côté volume dans la chaîne M5 (cohérent, hors périmètre du brief 1).

### Limite de méthode, déclarée

**Aucune source primaire n'a été consultée pour cette entrée.** EUR-Lex n'est pas
accessible depuis ce poste — limite constatée en M4, toujours présente. Les
conclusions 1 et 2 ne dépendent d'aucun texte nouveau : elles constatent l'état du
système, et cet état est vérifiable dans le dépôt. La conclusion 3 relève du RGPD,
dont l'applicabilité n'est pas en question.

En revanche, **le point 4 du relais M5 reste entier** : le texte consolidé du
règlement 2024/1689 tel que modifié par l'Omnibus n'a toujours pas été lu. Il est
reporté à M7 avec la même échéance — *avant toute conclusion engageante* — et il
faut noter que cette échéance a maintenant été repoussée deux fois.

---

## Passage de relais M6 vers M7

| # | Question ouverte | Responsable | Échéance |
|---|---|---|---|
| 1 | **Lire le texte consolidé** du règlement 2024/1689 tel que modifié. Reporté depuis M5, donc depuis deux modules. Aucune conclusion engageante ne devrait être rendue avant | Équipe M7 | avant la première décision opposable |
| 2 | **La rétention des données de feedback n'est pas implémentée.** 30 jours déclarés, aucune purge, fichiers nominatifs | Équipe M7 | avant toute exploitation hors laboratoire |
| 3 | **Le contrat de collecte du feedback ne demande pas la version du système.** 25 % du lot actionnable décrit un comportement inexistant. Les empreintes existent depuis M5 (`index_version`, `build_version`) — elles ne sont pas portées jusqu'au formulaire | Équipe M7 | avant le prochain lot de feedback |
| 4 | **Une couche de génération déclencherait l'article 50**, non reporté par l'Omnibus. Question du M5, toujours valable puisque M6 n'a pas généré | Équipe M7 | avant la première réponse générée servie |
| 5 | **Un fournisseur d'inférence externe** rouvrirait localisation, sous-traitance et rétention | Équipe M7 | avant tout appel à un service tiers |
| 6 | **Le calendrier du report au 2 décembre 2027 n'a pas été revérifié** depuis le 07/09 — EUR-Lex inaccessible depuis ce poste | Équipe M7 | à chaque checkpoint |
| 7 | **La base légale du traitement des retours n'est pas établie** : information des contributeurs, durée, droits d'accès et d'effacement. Question neuve, ouverte par cette entrée | Équipe M7 | avant la mise en service de la boucle hors laboratoire |
