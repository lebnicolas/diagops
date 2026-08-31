---
module: M3
brief: brief 2 — online
etat: étape 6 terminée
maj: 2026-08-31
---

# Biais et risques résiduels — brief 2, étape 6

Tous les chiffres de ce document sont calculés par `run_transmission_b2.py` et
consignés dans `output/transmission/biais.csv` et `transmission.json`. Aucun n'est
recopié de mémoire : ceux qui viennent du brief 1 sont recalculés sur le même
point de départ, et se retrouvent à l'identique.

Cinq biais sont documentés, là où le brief en demande trois. Les deux
supplémentaires ne sont pas du zèle : le biais de renseignement (B3) et le biais
d'historique (B4) sont ceux que la fabrication **n'atteint pas**, et sans eux la
note de décision donnerait l'impression que générer 1 799 lignes règle la
question.

---

## B1 — Biais de couverture instrumentale

**Ce qu'il est.** Le parc compte 416 équipements ; 36 portent au moins une mesure
réelle, soit **8,65 %**. La couverture n'est pas répartie au hasard : elle suit la
criticité déclarée.

| Comptage | Valeur |
|---|---|
| équipements avec au moins une mesure réelle | 36 / 416 — 8,65 % |
| `SITE-OUEST` | **0 / 16** |
| taux `critical` contre taux `low` | 30,43 % contre 1,33 % — **×22,9** |
| segment `SEG-2` | 2 / 174 — 1,15 % |
| types d'équipement sans aucune mesure | 7 / 18 |

**Atténuation appliquée.** Génération de 1 799 mesures sur les 8 équipements de
`SITE-OUEST ∩ SEG-2` (`PROC-GEN-SMOTE-V2`), janvier 2026, deux capteurs.

**Coût.** 3,45 % du jeu transmis devient fabriqué. Toute conclusion tirée sur
`SITE-OUEST` porte désormais sur des lignes qu'aucun capteur n'a produites, et
tout traitement qui les mélangerait au réel sans lire la colonne `provenance`
produirait un résultat indéfendable.

**Risque résiduel.** Il est le principal enseignement de l'étape : la couverture
passe de 8,65 % à 10,58 %, et **372 équipements restent sans aucune mesure**. Le
site couvert l'est à 50 %, entièrement en fabriqué. Surtout, le déséquilibre par
criticité *paraît* se réduire — le rapport `critical` / `low` tombe de ×22,9 à
×8,7 — alors que rien du réel n'a changé. C'est le piège de l'atténuation par
fabrication : elle corrige l'indicateur, pas le phénomène. Un tableau de bord qui
lirait la couverture sans distinguer la provenance annoncerait un progrès qui
n'existe pas.

---

## B2 — Biais d'étiquetage des événements

**Ce qu'il est.** 89 événements sur 514 disposent d'au moins une mesure dans leur
fenêtre (48 h avant, 24 h après), soit **17,3 %**. Et la documentation décroît
quand la gravité augmente.

| Gravité | Événements | Documentés (réel) | Part |
|---|---|---|---|
| `critical` | 73 | 9 | **12,33 %** |
| `high` | 213 | 35 | 16,43 % |
| `medium` | 157 | 30 | 19,11 % |
| `low` | 71 | 15 | 21,13 % |

Le brief 1 avait établi le fait de fond : **8 mesures de vibration dépassent
5 mm/s, 6 ne sont appariées à aucun événement**, dont le pic à 9,76 — le double
des deux seuls cas étiquetés. Ce que le jeu documente le mieux, ce sont les
situations les moins graves.

**Atténuation appliquée.** La génération porte sur un périmètre où 10 événements
existent, dont 3 tombent dans la période générée. Les 3 sont documentés après
transmission : le gain est **complet dans son périmètre**.

**Coût.** Ces 3 événements sont désormais « documentés » par des mesures
fabriquées. Un modèle qui apprendrait la signature capteur d'un incident sur ces
3 événements apprendrait la signature de notre interpolateur.

**Risque résiduel.** À l'échelle du parc, la documentation passe de 89 à 92
événements sur 514 — **17,3 % à 17,9 %**, et `critical` de 9 à 10 sur 73. Le
déficit d'étiquetage des cas graves est intact. Aucune technique de fabrication
ne peut le combler : les mesures manquent là où les événements graves ont eu
lieu, et générer une série sur un équipement ne crée pas l'événement qu'on
voudrait pouvoir y observer.

---

## B3 — Biais de renseignement non aléatoire

**Ce qu'il est.** 28 interventions sur 1 788 n'ont pas de coût de pièces. La
valeur manquante n'est pas répartie au hasard : **27 des 28 sont sur
`SITE-OUEST`**, soit **35,5 % des 76 interventions du site**.

| Comptage | Valeur |
|---|---|
| interventions sans coût de pièces | 28 / 1 788 — 1,57 % |
| dont `SITE-OUEST` | **27 / 28** |
| part des interventions `SITE-OUEST` concernées | 27 / 76 — 35,53 % |

Le site le moins instrumenté est aussi le moins renseigné. Les deux lacunes se
cumulent au lieu de se compenser — constat fait à l'étape 5, en cherchant un
agrégat à protéger.

**Atténuation appliquée.** Aucune. Une imputation du coût manquant reviendrait à
inventer une valeur monétaire sur le site où l'on sait le moins de choses, et à
la faire entrer dans des agrégats publiés.

**Coût de ne rien faire.** Toute statistique de coût sur `SITE-OUEST` porte sur
64,5 % de ses interventions, et cette part n'est pas un échantillon aléatoire.

**Risque résiduel.** Entier, et il touche l'étape 5 : le mécanisme de Laplace a
été appliqué au coût moyen des pièces par site × criticité. Sur `SITE-OUEST`, la
valeur protégée est déjà calculée sur des données lacunaires de façon
systématique. Protéger un chiffre biaisé ne le corrige pas — cela le publie avec
une garantie de confidentialité et aucune garantie d'exactitude.

---

## B4 — Biais historique de l'activité de maintenance

**Ce qu'il est.** Le jeu ne décrit pas le parc : il décrit ce qui a déclenché une
trace. 42 équipements n'ont **aucun** événement enregistré, 50 n'ont **aucune**
intervention. Un équipement sans historique n'est pas un équipement sans panne —
c'est un équipement sur lequel personne n'a rien écrit.

| Comptage | Valeur |
|---|---|
| équipements sans aucun événement | 42 / 416 — 10,10 % |
| équipements sans aucune intervention | 50 / 416 — 12,02 % |
| interventions correctives | 349 / 1 788 — 19,52 % |

La segmentation de l'étape 1 avait déjà buté dessus : à `k = 2` sur le parc
entier, l'algorithme isolait un groupe défini par des compteurs d'activité tous
nuls — une partition qui ne dit rien du parc et tout de l'enregistrement. D'où la
strate `SEG-INACTIF` déclarée à part, sur 50 équipements.

**Atténuation appliquée.** Déclarer la strate plutôt que la laisser structurer la
segmentation. C'est une atténuation méthodologique, pas une correction de donnée.

**Coût.** 50 équipements sont exclus de la segmentation qui sert à raisonner sur
le parc.

**Risque résiduel.** On ne sait pas distinguer « rien ne s'est passé » de « rien
n'a été saisi ». Aucune donnée du jeu ne permet de trancher, et aucune
fabrication ne le pourra : générer de l'activité sur ces 50 équipements
reviendrait à inventer la réponse à la question posée.

---

## B5 — Biais de représentation

**Ce qu'il est.** Les modalités sont très inégalement peuplées, et ces
déséquilibres traversent toutes les variables de segmentation.

| Variable | Rapport max / min |
|---|---|
| type d'équipement | 57 (`pump`) contre 5 (`lift`, `steam_unit`) — **×11,4** |
| site | 173 (`SITE-NORD`) contre 16 (`SITE-OUEST`) — ×10,8 |
| type d'événement | 232 (`incident`) contre 49 (`alert`) — ×4,7 |
| criticité | 173 (`medium`) contre 46 (`critical`) — ×3,8 |
| gravité | 213 (`high`) contre 71 (`low`) — ×3,0 |

**Atténuation appliquée.** Le périmètre généré a été composé à criticités
équilibrées — 2 `critical`, 2 `high`, 2 `medium`, 2 `low` — plutôt que tiré au
hasard dans `SITE-OUEST`.

**Coût.** Le jeu transmis contient un sous-ensemble dont la structure de
criticité ne ressemble à aucun site réel. Une statistique calculée toutes
provenances confondues est faussée par construction.

**Risque résiduel.** C'est le point que le brief formule le plus nettement : *une
classe minoritaire dupliquée reste minoritaire dans le réel*. Les 5 `lift` du parc
restent 5. Générer des mesures pour eux augmenterait le nombre de **lignes**, pas
le nombre d'**équipements observés** : l'information reste celle de 5 machines,
répartie sur davantage de lignes, ce qui donne à un modèle l'illusion d'un
effectif qu'il n'a pas.

---

## Ce que la fabrication corrige, et ce qu'elle amplifie

| Biais | L'augmentation / la génération… | Effet net |
|---|---|---|
| B1 couverture | **corrige en apparence** — le taux passe de 8,65 % à 10,58 %, le rapport `critical`/`low` de ×22,9 à ×8,7 | **amplifie le risque de lecture** : l'indicateur progresse, le parc observé est identique |
| B2 étiquetage | corrige 3 événements sur 425 non documentés | négligeable au parc ; **amplifie** si un modèle apprend la signature d'un incident sur des séries interpolées |
| B3 renseignement | ne touche pas — aucune imputation | inchangé, et il contamine les agrégats protégés à l'étape 5 |
| B4 historique | ne touche pas — générer de l'activité serait inventer la réponse | inchangé |
| B5 représentation | **amplifie** — plus de lignes, pas plus d'équipements observés | un effectif apparent supérieur à l'effectif réel |

Deux biais sur cinq sont hors de portée de toute technique de fabrication, et le
seul que la fabrication améliore vraiment (B1) est aussi celui où elle crée le
plus grand risque d'erreur de lecture. C'est ce constat, et non une préférence de
principe, qui conduit à transmettre le fabriqué **étiqueté et cloisonné** plutôt
qu'à s'en priver ou à le fondre dans le réel.

---

## Risques propres aux données fabriquées transmises

Trois risques ne sont pas des biais du jeu d'origine mais des risques que **nous**
introduisons.

**Le détecteur ne sait pas les arbitrer.** `PROC-GEN-SMOTE-V1` et
`PROC-GEN-SMOTE-V2` ont reçu le même verdict — zéro signalement — alors que la
dispersion du second est mesurablement meilleure (ratios σ 0,858 et 0,897 contre
0,783 et 0,810). Nous transmettons donc un procédé que nous croyons meilleur, sans
instrument de référence capable de le confirmer. Atténuation : la contraction
résiduelle de 10 à 14 % est écrite dans le registre des procédés, et l'usage en
évaluation est interdit. Risque résiduel : si la contraction importe pour la
tâche de M4, elle passera pour une propriété des données.

**Le silence du détecteur reste un silence.** Une série sans aucune structure
temporelle — `PROC-GEN-MARG-V1` — a été déclarée conforme, et plus propre que les
deux témoins réels (T1-02). L'absence de signalement ne prouve rien, et c'est
précisément pourquoi `PROC-GEN-MARG-V1` n'est pas transmis.

**Un défaut de notre chaîne a survécu au brief 1.** La soumission T3-00 du jeu
transmis a fait apparaître 68 valeurs à plus de trois décimales, toutes réelles,
toutes sur `EQ-SENSOR-305` : la conversion kelvin → °C de `R-SEN-006` écrivait
`56.85000000000002`. Corrigé à la transmission par `R-TRA-001`, vérifié par
T3-01. Risque résiduel : le correctif est appliqué **au point de transmission**,
pas dans `prepare_sensors` — la dette est inscrite au registre des règles et dans
la note de décision, et toute chaîne rejouée sans elle reproduira le défaut.
