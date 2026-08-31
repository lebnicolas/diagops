---
module: M3
brief: brief 2 — online
etat: étape 5 terminée
maj: 2026-08-26
---

# Protéger un agrégat trop peu fourni — étape 5

Agrégat retenu (arbitrage A4) : le **coût moyen des pièces par site et par
criticité**. Seize cellules, des effectifs de 4 à 319 interventions, des coûts
de 3 à 1 127,58 €.

Le choix porte l'étape. Sur un comptage, la sensibilité vaut 1 et tout se réduit
au réglage d'un curseur. Sur une **moyenne**, elle dépend de l'amplitude des
valeurs, et le tableau contient une cellule à 4 interventions à côté d'une à 319 :
la même publication n'y a pas du tout le même coût.

---

## 1. Le mécanisme, et ce qu'il protège exactement

Le modèle de menace est explicite : quelqu'un connaît toutes les interventions
d'une cellule sauf une, et cherche le coût de celle qui lui manque. Publier la
moyenne exacte la lui donne — il soustrait ce qu'il sait. Le mécanisme de Laplace
ajoute à la publication un bruit calibré sur ce qu'**une seule** intervention
peut changer.

La loi est écrite à la main, par inversion de sa fonction de répartition :
`−b · signe(u) · ln(1 − 2|u|)` pour `u` uniforme sur `]−0,5 ; 0,5[`, avec
`b = sensibilité / ε`.

**Deux décisions de conception précèdent tout calcul.**

**Borner les coûts.** La sensibilité d'une somme est l'amplitude maximale qu'une
observation peut lui faire prendre. Sans plafond déclaré, cette amplitude est
celle du maximum observé — 1 127,58 € — et ce maximum est lui-même une donnée du
jeu : l'utiliser comme paramètre revient à le publier en creux. Les coûts sont
donc bornés à `[0 ; B]` avec `B` fixé à l'avance.

**Partager le budget.** Une moyenne est un quotient. Publier une somme bruitée et
un effectif exact laisse fuiter l'effectif, qui est une information en soi —
surtout sur une cellule à quatre interventions. Les deux quantités sont bruitées,
chacune avec la moitié du budget ; par composition, l'ensemble consomme bien `ε`.
La sensibilité vaut alors `B` pour la somme et 1 pour l'effectif.

Chaque cellule est publiée **2 000 fois** par budget. Un mécanisme aléatoire ne
se juge pas sur un tirage, et présenter un tirage unique comme « le résultat »
serait exactement la faute que le brief sanctionne.

## 2. Le plafond de bornage n'est pas une donnée, c'est un arbitrage

Le plafond joue dans les deux sens : il réduit le bruit, dont l'échelle lui est
proportionnelle, et il introduit un biais en tronquant les coûts élevés. Trois
valeurs comparées, à `ε = 1`, médiane sur les seize cellules :

| Plafond | Biais de troncature | Erreur due au bruit | **Erreur totale** |
|---:|---:|---:|---:|
| 500 € | 13,18 € | 9,08 € | 23,60 € |
| **750 €** | **1,27 €** | 12,66 € | **13,64 €** |
| 1 128 € (maximum observé) | 0,00 € | 18,19 € | 18,19 € |

Le minimum n'est à aucune des deux extrémités. Tronquer trop bas remplace le
bruit par un biais plus lourd que lui ; ne pas tronquer laisse le bruit à sa
valeur maximale. **750 € est retenu** : il coupe 1,9 % des interventions et
0,89 % de la masse des coûts.

Une remarque qui compte pour la lecture du tableau. À plafond 500 €, la
« conclusion conservée » est *meilleure* (83 %) qu'à 750 € (79 %) alors que
l'erreur totale y est presque double. Ce n'est pas une contradiction : le biais
de troncature est **systématique** — il déplace toutes les cellules et la moyenne
générale dans le même sens — tandis que le bruit est aléatoire et déplace chaque
cellule indépendamment. Un biais systématique préserve les comparaisons, un bruit
aléatoire les détruit. Deux erreurs de même taille n'ont pas le même effet sur ce
qu'on veut lire.

## 3. Les deux bornes

**En bas — le chiffre cesse d'être exploitable.** Le critère retenu est celui que
le lecteur du tableau cherche réellement : la publication dit-elle encore de quel
côté de la moyenne générale (217,49 €) se situe la cellule, dans plus de 90 % des
tirages ?

**En haut — le mécanisme cesse de protéger.** L'adversaire du modèle de menace
soustrait de la somme publiée ce qu'il connaît déjà ; il lui reste la valeur cible
plus le bruit. Son erreur d'estimation **est** le bruit appliqué à la somme. On
mesure la part des tirages où il retrouve le coût cible à ±50 € — une précision
qui, sur une intervention valant 220 € en moyenne, est déjà une information.

| `ε` | Cellules exploitables | Erreur médiane de l'adversaire | Cible retrouvée à ±50 € |
|---:|---:|---:|---:|
| 0,1 | 0 / 16 | 10 589 € | 0,3 % |
| 0,5 | 2 / 16 | 2 095 € | 1,5 % |
| 1 | 4 / 16 | 1 013 € | 2,9 % |
| 2 | 8 / 16 | 512 € | 7,7 % |
| **5** | **11 / 16** | **197 €** | **14,8 %** |
| 10 | 12 / 16 | 99 € | 29,5 % |
| 20 | 15 / 16 | 54 € | 46,7 % |
| 50 | 15 / 16 | 20 € | 81,2 % |

**Il n'existe pas de valeur qui satisfasse les deux bornes sur l'ensemble du
tableau.** Amener quinze cellules sur seize à l'exploitabilité demande `ε = 20`,
budget auquel l'adversaire retrouve sa cible une fois sur deux. La zone de
compromis se situe entre 2 et 5 : la moitié à deux tiers des cellules
exploitables, un adversaire qui réussit dans 8 à 15 % des cas.

**Un `ε` unique pour tout le tableau est donc indéfendable**, et c'est le
résultat de l'étape. Le budget qui convient à `SITE-NORD / medium` (319
interventions) est très loin de celui qu'il faudrait à `SITE-OUEST / critical`
(4 interventions).

## 4. Ce que l'effectif explique, et ce qu'il n'explique pas

Deux corrections à l'intuition, mesurées sur les quatre cellules de `SITE-OUEST`
à `ε = 5` :

| Cellule | Effectif | Coût moyen | Erreur médiane | Conclusion conservée |
|---|---:|---:|---:|---:|
| `SITE-OUEST / high` | 14 | 81,90 € | 15,70 € (19 %) | **99,8 %** |
| `SITE-OUEST / medium` | 27 | 223,50 € | 8,70 € (4 %) | 69,5 % |
| `SITE-OUEST / critical` | 4 | 264,32 € | 57,94 € (22 %) | 70,6 % |
| `SITE-OUEST / low` | 4 | 219,18 € | 55,97 € (26 %) | 49,3 % |

**L'effectif ne décide pas seul.** `SITE-OUEST / high` n'a que 14 interventions
et reste lisible à 99,8 %, parce que son coût moyen — 81,90 € contre 217,49 € de
moyenne générale — s'écarte massivement. Ce qui compte est le rapport entre
l'écart à mesurer et le bruit, pas l'effectif pris isolément.

**Et une conclusion peut échouer sans que le mécanisme y soit pour rien.**
`SITE-OUEST / low` vaut 219,18 € pour une moyenne générale de 217,49 € : l'écart
est de **1,69 €**. Aucun bruit, si faible soit-il, ne dira de façon fiable de quel
côté elle se trouve — la cellule est sur la ligne de partage. À `ε = 50`, où
l'erreur de publication tombe à 5,77 €, la conclusion n'est encore juste que dans
59 % des tirages. Ce n'est pas la publication qui est mauvaise : c'est la question
qui n'a pas de réponse robuste pour cette cellule. Confondre les deux conduirait à
dépenser du budget pour rien.

## 5. La maille, pas le budget

Si aucun budget ne convient au tableau croisé, la question n'est plus « quel
`ε` » mais « quelle granularité ». Regrouper les sites porte les effectifs de 4 à
plusieurs centaines sans changer la sensibilité : le bruit reste le même en euros
et devient négligeable devant la masse.

| `ε` | site × criticité (16 cellules) | criticité seule (4 cellules) |
|---:|---:|---:|
| 0,5 | 2 / 16 | 1 / 4 |
| 1 | 4 / 16 | 2 / 4 |
| 2 | 8 / 16 | 3 / 4 |
| 5 | 11 / 16 | **4 / 4** |

À `ε = 5`, la maille grossière est intégralement exploitable quand la maille fine
laisse cinq cellules sur seize inutilisables. **La protection d'un agrégat trop
peu fourni ne s'achète pas en budget, elle s'obtient en renonçant à la finesse.**

## 6. Correction apportée en cours d'étape

La première version de ce travail mesurait la protection par la part des tirages
où la **moyenne vraie** était retrouvée à 10 % près. L'indicateur donnait des
résultats absurdes : plus une cellule était fournie, moins elle paraissait
protégée — jusqu'à 98 % de « réidentification » sur la cellule à 319
interventions dès `ε = 1`.

L'erreur est de raisonnement, pas de code. La confidentialité différentielle **ne
promet nulle part de cacher un agrégat** ; elle promet de borner ce que la
publication révèle d'une observation isolée. Retrouver une moyenne publiée n'est
pas une attaque : c'est le service rendu. L'indicateur mesurait donc la précision
et l'appelait vulnérabilité.

Il est remplacé par l'attaque par différenciation décrite en section 3, qui suit
le modèle de menace annoncé. Conséquence directe, visible dans le tableau :
**la protection ne dépend pas de l'effectif** — l'échelle du bruit sur la somme
vaut `B / (ε · 0,5)` quel que soit `n`. C'est la théorie, et la mesure corrigée
la retrouve.

## 7. Ce qui est retenu pour l'étape 6

- **Ne pas publier le tableau croisé site × criticité.** Aucun budget ne le rend
  simultanément utile et protecteur.
- **Publier à la maille « criticité seule », `ε = 5`** — quatre cellules, toutes
  exploitables, adversaire à 14,8 % de réussite.
- **Documenter les quatre cellules `SITE-OUEST`** comme non publiables à la maille
  fine, et dire pourquoi : effectifs de 4 à 27 interventions.
- **Signaler la lacune de renseignement.** Les seize cellules portent 1 760
  interventions avec coût sur 1 788 ; **27 des 28 valeurs manquantes sont sur
  `SITE-OUEST`**, qui compte 76 interventions dont 27 sans coût — 35 %. Le site le
  moins instrumenté est aussi le moins renseigné. Ce cumul est repris parmi les
  biais de l'étape 6.
