---
module: M4
brief: brief 1 — présentiel
etat: étape 8 terminée
maj: 2026-08-31
---

# Matrice de décision

Deux décisions distinctes, qui n'appellent pas la même conclusion : le **modèle
de provenance** (capteurs) et l'**assistant documentaire** (RAG + agent). Les
mélanger produirait une décision moyenne qui ne vaudrait pour aucun des deux.

Tous les chiffres viennent des étapes 3 à 7 et sont traçables dans `results/`.

---

## Décision 1 — Modèle de provenance

### La matrice

| Critère | Baseline M3 (règles) | **Régression logistique** | Forêt aléatoire |
|---|---|---|---|
| **Qualité** — F1 hors pli | 0,375 | **0,694 ± 0,068** | 0,541 ± 0,055 |
| Rappel | 0,273 | **0,636** | 0,455 |
| Précision | 0,600 | 0,700 | 0,625 |
| ROC-AUC | — | **0,737** | 0,681 |
| **Robustesse** — min sur 5 partitions | — | **0,600** | 0,455 |
| Stabilité par segment | uniforme (mauvaise partout) | **`temperature_c` : 0,000** | `temperature_c` : 0,000 |
| **Latence** par fenêtre | — | **0,06 ms** | 1,78 ms |
| **Mémoire** | ~0 | **56 ko** | 389 ko |
| **Coût par réponse** | nul | **nul** (CPU, pas de service) | nul |
| **Complexité d'exploitation** | 1 fichier Python, zéro dépendance | scikit-learn, 1 artefact `joblib`, 19 features à recalculer | idem, artefact 7× plus gros |
| **Réversibilité** | — | **totale** — la baseline est figée et conservée | totale |

### Ce qui est établi

Le gain est net et il tient : **+0,319 de F1**, et le *minimum* des cinq
partitions (0,600) dépasse largement la baseline (0,375). Ce n'est pas un
artefact de tirage.

Et il est **expliqué** : la structure temporelle porte 38 % du signal, le contrat
capteur — tout ce que la baseline sait regarder — moins de 10 %. Le modèle ne bat
pas la baseline en appliquant mieux ses règles, il regarde ailleurs.

### Ce qui ne l'est pas

1. **Le résultat officiel n'existe pas encore.** Le candidat est gelé, les
   prédictions produites, mais le formateur n'a pas encore calculé les métriques
   sur son oracle. C'est le seul chiffre qui doit entrer dans une décision de
   déploiement, et il manque.
2. **30 fenêtres, 11 positives.** L'écart-type de 0,068 mesure la sensibilité au
   découpage d'un même jeu, pas l'erreur d'échantillonnage.
3. **Un segment entier est manqué** — `temperature_c`, 1 fabriquée sur 9, ratée
   par les deux candidats.
4. **Le rappel plafonne à 0,636** : 4 fenêtres fabriquées sur 11 passent. C'est
   mieux que les 8 de la baseline, ce n'est pas un détecteur.

### Décision

> ## `évaluer davantage`

**Pas `adopter`** : décider d'un déploiement sur un résultat de calibration,
alors qu'un oracle scellé existe et n'a pas encore parlé, viderait de son sens
tout le dispositif de gel.

**Pas `maintenir la baseline`** : le gain est démontré, reproductible, expliqué,
et le coût d'exploitation est marginal (56 ko, 0,06 ms). Refuser d'aller plus
loin ne se défendrait pas.

**Ce qui débloquerait `adopter`**, dans l'ordre :

| # | Condition | État |
|---|---|---|
| 1 | résultat du formateur sur l'oracle scellé, cohérent avec 0,694 ± 0,068 | **en attente** |
| 2 | comportement établi sur `temperature_c` — actuellement non couvert par la preuve | non traité |
| 3 | seuil de rappel acceptable arrêté avec le métier : 0,636 suffit-il ? | non posé |

**Ce qui imposerait `écarter`** : un F1 sur l'oracle inférieur à la baseline, ou
un écart tel que le gain de calibration s'expliquerait par le surajustement.

---

## Décision 2 — Assistant documentaire (RAG + agent)

### La matrice

| Critère | Sans retrieval | **Lexical** | **Vectoriel** |
|---|---|---|---|
| **Qualité** — Recall@1 (questions d'origine) | 0,000 | 1,000 | 1,000 |
| Recall@1 (questions reformulées) | 0,000 | **0,300** | **0,700** |
| Décisions d'abstention correctes | — | — | **12 / 12** (sur le jeu de réglage) |
| Citations valides / extraits littéraux | — | — | 12 / 12 · 12 / 12 |
| **Robustesse** — menaces arrêtées | — | — | **7 / 8** |
| Documents inadmissibles récupérés | — | **0** | **0** |
| **Latence** par requête | 0 ms | **0,57 ms** | 12,9 ms |
| **Mémoire** — index | 0 | **0** | 12 ko |
| Modèle sur disque | 0 | **0** | **~470 Mo** |
| Chargement au démarrage | 0 s | **0 s** | 11,4 s |
| **Coût par réponse** | nul | nul | nul (CPU, pas d'API) |
| **Complexité d'exploitation** | — | zéro dépendance | `torch` + `sentence-transformers`, modèle à télécharger, corpus et manifeste à maintenir |
| **Réversibilité** | — | totale | **totale** — aucune écriture, aucun état persistant |

La génération est **extractive** : pas de modèle génératif, donc pas de coût par
appel, pas de dérive, et une fidélité aux extraits garantie par construction
plutôt que mesurée après coup.

### Décision

> ## `ne pas déployer` — et ce n'est pas un échec de mesure

Les trois briques fonctionnent : le retrieval récupère, la génération cite et
s'abstient, l'agent tient ses bornes sur 18 cas. **La décision négative ne porte
pas sur leur qualité, elle porte sur deux conditions extérieures qui ne sont pas
tenues.**

**Condition 1 — aucun ajout au corpus sans revue éditoriale.**
`THR-004` le démontre : un mémo déclaré `public` recopiant du contenu restreint
est livré à un utilisateur `public`, sans qu'aucun contrôle ne bronche. Le
contrat d'admission vérifie la **provenance** d'un document, jamais son
**contenu**. Tant qu'un tiers peut déposer un document, la confidentialité ne
repose sur rien.

**Condition 2 — le rôle doit être authentifié par la couche appelante.**
`THR-008` n'est arrêtée que parce que le manifeste fait autorité sur les droits.
Mais le rôle lui-même est **déclaré par l'appelant** : quiconque interroge le
système en se disant `auditeur` obtient les droits d'un auditeur. Il n'existe
aucun mécanisme d'identité dans ce brief.

Ces deux conditions sont **organisationnelles et d'architecture**, pas des
défauts du pipeline. Aucune mesure supplémentaire sur ce corpus ne les lèvera.

### Ce qui est prêt, et qui doit être transmis

- le **contrat d'admission** — statut, rôle, checksum, vérifiés avant tout
  classement ; 0 document inadmissible récupéré sur toute la campagne ;
- le **contrat de citation et d'abstention** — 5 règles nommées, une abstention
  ne cite jamais, une réponse cite toujours un document admissible ;
- l'**agent à une étape** — trois actions, aucun outil à effet, garde-fou
  vérifié par mutation ;
- le **threat model** — 8 menaces, risques résiduels chiffrés ;
- la **base de comparaison par règles**, que le modèle de M5 devra battre.

### Le choix retrieval reste ouvert, et l'information manque

| Si les questions… | Alors | Motif mesuré |
|---|---|---|
| reprennent le vocabulaire des procédures | **le lexical suffit** | 1,000 partout, 23× plus rapide, zéro dépendance |
| sont formulées librement | **le vectoriel se justifie** | 0,700 contre 0,300 sur l'épreuve reformulée |

Rien dans le matériel fourni ne dit laquelle des deux situations est celle de
DiagOps. **C'est cette information qui trancherait — pas une mesure de plus.**

Le vectoriel est retenu pour la suite du brief : seul à ne pas s'effondrer quand
la formulation change, pour 12 ko d'index et 13 ms. Mais 470 Mo de modèle et une
dépendance à `torch` pour un corpus de 6 Ko est un rapport que seul l'usage réel
peut justifier.

---

## Ce que la campagne a coûté en hypothèses fausses

Neuf hypothèses formulées avant mesure se sont révélées fausses, sur 31 entrées
de journal. Les quatre qui ont changé une décision :

| Hypothèse | Ce qui s'est passé |
|---|---|
| « comparer les F1 moyens par pli suffira à trancher » | la dispersion mesurait la difficulté des plis, pas l'incertitude du gain — changement de maille, dispersion 0,35 → 0,068 |
| « un seuil de similarité décidera de l'abstention » | 0,007 d'écart entre répondables et non-répondables — politique par règles à la place |
| « la racinisation corrigera le refus excessif » | elle a produit une **réponse à tort**, plus grave ; cause : une recherche de sous-chaîne prise pour une racinisation |
| « les 8 menaces seront arrêtées » | 7 sur 8 — la fuite par recopie n'est couverte par aucune défense |

---

## Résumé pour un lecteur pressé

**Le modèle capteur fonctionne** — F1 0,694 contre 0,375, gain expliqué et
reproductible — et attend le verdict de l'oracle avant toute adoption.

**L'assistant documentaire fonctionne aussi**, et ne doit pas être déployé : un
document public peut recopier une donnée restreinte sans qu'aucun contrôle ne
s'y oppose, et le rôle de l'appelant n'est jamais authentifié. Deux conditions à
tenir avant d'y revenir, ni l'une ni l'autre technique.
