---
module: M4
brief: brief 1 — présentiel
etat: étape 5 terminée
maj: 2026-08-31
---

# Génération citée et abstention

Produit par `run_generation.py`. Traces complètes dans
`results/generation/traces.jsonl`, une par question.

> [!warning] Ce que vaut le 12/12 annoncé plus bas
> Ces douze questions ont servi à **régler** la politique d'abstention, en trois
> tours documentés ci-dessous. Le résultat est donc une mesure de calibration,
> pas une performance : c'est le jeu sur lequel on s'est ajusté. Les 12 questions
> du split `test` sont scellées et diront ce qu'il en est réellement.

---

## Arbitrage : génération extractive, pas de LLM

Rien dans le brief n'impose un modèle génératif, et le contrat de sortie du
starter (`GroundedAnswer`) n'en suppose aucun. Trois raisons :

1. **la fidélité aux extraits devient une propriété, pas une mesure** — une
   réponse composée de fragments copiés du document *est* fidèle par
   construction, et se vérifie par comparaison de chaînes ;
2. **la reproductibilité est exacte** — pas de température, pas de graine ;
3. **le coût par réponse est nul**, ce que la matrice de décision doit chiffrer.

**Ce que cela coûte, et qui est assumé** : les réponses sont brutes — des
extraits juxtaposés, pas de la prose. Pour un assistant réellement destiné à des
techniciens, un modèle génératif *contraint aux extraits* serait le prolongement
naturel, et c'est le premier écart à combler si DiagOps va plus loin. Il
introduirait alors une infidélité à mesurer, là où elle est ici garantie.

## Arbitrage A5 — l'abstention ne repose pas sur un seuil de similarité

C'est mesuré, pas supposé. Meilleur score de similarité par question :

| | Meilleur score |
|---|---|
| 10 questions répondables | 0,811 à 0,909 |
| 2 questions **sans réponse** | 0,801 et 0,804 |

**L'écart entre la pire répondable et la meilleure non-répondable est de 0,007.**
Un seuil placé dans cet intervalle séparerait parfaitement les douze — en étant
calé sur **deux** exemples négatifs. C'est du surajustement, et le corpus le dit
lui-même dans `DOC-RAG-OPS-001` : *« une similarité élevée ne constitue pas une
preuve de vérité »*.

La similarité cosinus reste élevée entre deux textes du même domaine, quelle que
soit leur pertinence. Elle sert à **classer**, elle ne sait pas juger.

## La politique retenue — cinq règles nommées

| Règle | Décision | Fondement |
|---|---|---|
| `ABS-001` | abstention | aucun document admissible pour ce rôle |
| `ABS-002` | abstention | aucun document ne couvre assez les termes porteurs de la question |
| `ABS-003` | abstention | la question demande une prédiction que le corpus exclut explicitement |
| `REP-001` | réponse | un document admissible couvre la question |
| `SIG-001` / `SIG-002` | signalement | révision remplacée, ou document restreint — annoncés sans être cités |

`ABS-003` s'appuie sur une phrase du corpus, pas sur une intuition :
`DOC-PUMP-VIB-001` écrit « Le système ne prédit pas une panne future à partir de
ces seuls seuils ». La question `RAG-CAL-012` — « à quelle date exacte la
prochaine panne… » — est refusée **en citant cette exclusion**.

### Le seuil de couverture

Couverture maximale par question, après correction :

| | Couverture |
|---|---|
| 10 questions répondables | **0,500 à 1,000** |
| 2 questions sans réponse | **0,143 et 0,200** |

Les deux groupes sont séparés par un intervalle de **0,300**. Le seuil est placé
à **0,35**, au milieu de cet intervalle, et non juste au-dessus du dernier
négatif : un seuil posé au bord se transporte mal sur des questions non vues.

**La limite est déclarée** : deux questions négatives ne suffisent pas à caler un
seuil. La marge est confortable *sur ce jeu*, elle ne dit rien de sa stabilité
ailleurs.

## Les trois tours de réglage

Ils sont rapportés parce qu'ils sont la démarche, et que le dernier chiffre seul
donnerait une fausse impression de facilité.

| Tour | Ce qui a changé | Décisions correctes | Nature de l'erreur restante |
|---|---|---:|---|
| 1 | appariement exact des termes | 11 / 12 | **abstention à tort** sur `RAG-CAL-009` |
| 2 | racinisation à 5 caractères + mots grammaticaux composés écartés | 11 / 12 | **réponse à tort** sur `RAG-CAL-011` |
| 3 | racine appariée en **début de mot**, seuil au centre de l'intervalle | **12 / 12** | aucune |

**Tour 1 — le refus excessif.** « Quelles actions l'agent M4 est-il autorisé à
choisir ? » était refusée : le document écrit « choisit », la question dit
« choisir », et l'appariement exact échoue sur la conjugaison. `est-il` était par
ailleurs compté comme terme porteur. Deux défauts de principe, pas des
particularités de cette question.

**Tour 2 — le compromis s'est déplacé, pas amélioré.** La racinisation a réglé
`RAG-CAL-009` et **cassé `RAG-CAL-011`** : la question sur la marque de
lubrifiant, qui n'a aucune réponse dans le corpus, a reçu une réponse citant
`DOC-PUMP-VIB-001`. Le score restait 11/12, mais l'erreur avait changé de
nature — et en pire :

> Une abstention à tort est un refus conservateur. Une **réponse à tort à une
> question sans preuve** est le critère bloquant que le brief nomme. Deux erreurs
> qui comptent pour un même point n'ont pas la même gravité.

**Tour 3 — un défaut de conception, pas une limite.** La cause était que
`present()` cherchait la racine comme **sous-chaîne** : « commander » devenait
« comma », qui se retrouve au milieu de « re**comma**ndé ». Une recherche de
sous-chaîne n'est pas une racinisation. Corrigé en appariant la racine au
**début d'un mot** — après quoi la couverture de `RAG-CAL-011` retombe de 0,400 à
0,200, et l'intervalle séparant les deux groupes passe de nul à 0,300.

## Résultats

| Mesure | Résultat |
|---|---|
| Décisions d'abstention correctes | **12 / 12** |
| Questions répondables — répondues | 10 / 10 |
| Questions sans réponse — abstenues | **2 / 2**, aucune réponse à tort |
| Citations valides (contrat du starter) | **12 / 12** |
| Extraits littéraux (fidélité) | **12 / 12** |
| Signalements produits | 5 |

**Citations valides** signifie : une abstention ne cite rien, une réponse cite au
moins un document **admissible pour le rôle**, aucun extrait n'est vide.
**Extraits littéraux** signifie : chaque extrait cité est un fragment exact du
document, vérifié par appartenance de chaîne.

### Les signalements

Cinq signalements produits, sur des documents que le système **ne cite pas** :

- `SIG-001` sur les questions de consignation — `DOC-LOTO-001` est remplacé par
  `DOC-LOTO-002` (révision 2). La révision périmée est **nommée avec son statut**,
  son contenu n'est jamais lu ni cité. C'est ce que `DOC-RAG-OPS-001` appelle
  « signaler les conflits de révision au lieu de les masquer » ;
- `SIG-002` sur `RAG-CAL-008` (rôle `public`) — `DOC-DATA-ACCESS-001` existe mais
  n'est pas accessible à ce rôle. Le taire reviendrait à répondre « je ne sais
  pas » à la place de « vous n'y avez pas accès », deux choses différentes.

Le rôle `public` n'a d'ailleurs accès qu'à **un seul document sur huit** — fait
mesuré au passage, et qui limite d'emblée ce que le système peut lui répondre.

## Ce que ce résultat ne dit pas

1. **Il est obtenu sur le jeu de réglage.** Trois tours d'ajustement sur douze
   questions : le 12/12 mesure l'ajustement autant que la méthode.
2. **Deux questions négatives**, c'est tout ce dont on dispose pour calibrer une
   politique d'abstention. C'est très peu.
3. **La couverture lexicale n'est pas la compréhension.** Un document peut
   contenir tous les termes d'une question sans y répondre. Le seuil mesure la
   présence du vocabulaire, pas celle de la réponse.
4. **Les réponses ne sont pas rédigées.** Ce sont des extraits juxtaposés : le
   contrat de citation est respecté, la lisibilité pour un technicien ne l'est
   pas.
5. **Rien n'est mesuré sur le split `test`**, scellé.
