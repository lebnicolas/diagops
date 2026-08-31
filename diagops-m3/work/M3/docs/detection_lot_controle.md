---
module: M3
brief: brief 2 — online
etat: étape 4 terminée
maj: 2026-08-26
---

# Détection sur le lot de contrôle — étape 4

Le brief pose la question dans les deux sens : nos fabrications résistent-elles
au détecteur du module, et nos règles savent-elles qualifier un lot dont la
provenance est cachée. Les deux réponses tiennent en une phrase chacune.

Dans le sens qui va de nous vers le détecteur, **nos deux générateurs passent
sans déclencher une seule règle, alors que les mesures authentiques, elles, en
déclenchent** — 6,24 % des lignes de la livraison publiée, 3,04 % de notre
préparation. Dans le sens inverse, **nos règles de qualité employées comme test
d'authenticité obtiennent une précision de 49 %** : elles font aussi bien qu'une
pièce jetée en l'air.

Le détail du premier sens, avec les deux tours du générateur et les huit
hypothèses formulées avant lancement, est dans `journal_bord.md`. Ce document
porte le second.

---

## 1. Ce que le lot donne, et ce qu'il refuse

| Fichier | Lignes | Provenance | Rôle |
|---|---:|---|---|
| `control_batch.csv` | 6 000 | absente | le lot à qualifier |
| `control_sample.csv` | 720 | déclarée | calibrer les règles, jamais conclure |

La proportion fabriquée n'est pas communiquée, les procédés ne sont pas décrits,
l'oracle n'est pas distribué. Une phrase des notes de version fixe en revanche un
point d'appui décisif : « les mesures réelles proviennent de la livraison M3 ».

**Deux constats de structure, établis avant d'écrire la première règle.**

L'échantillon se répartit en **24 blocs de 30 lignes** à provenance homogène —
15 réels, 9 fabriqués, soit 37,5 % de fabriqué — et le lot en **200 blocs de 30
exactement**. La fabrication n'est pas ligne à ligne : elle est par segment. Une
règle qui déciderait ligne par ligne travaillerait contre la structure du
problème, et un verdict pris au bloc s'appuie sur trente observations au lieu
d'une.

## 2. Deux registres, et pourquoi ils ne peuvent pas être un seul

Le brief pose un piège explicite : *les lignes authentiques du lot portent les
anomalies de qualité de la livraison M3.* Une ligne signalée par un contrôle de
qualité n'est donc pas une ligne fabriquée.

C'est pourquoi les règles de détection forment un registre **distinct** de celui
du brief 1. `R-SEN-*` répond à « cette ligne est-elle conforme au contrat »,
`R-DET-*` à « cette ligne a-t-elle été fabriquée ». Les deux questions n'ont ni
la même réponse, ni les mêmes contre-exemples.

La preuve la plus nette tient en quarante lignes. Le lot contient un capteur
nommé `TEMPERATURE_C ` — majuscules et espace parasite. `R-SEN-005` le signale, à
juste titre. Ces **quarante lignes sont toutes retrouvées à l'identique dans la
livraison M3** : elles sont authentiques. Un contrôle de qualité les accuse,
elles n'ont rien à se reprocher qu'un nom mal écrit.

## 3. La règle décisive

> **`R-DET-001`** — un bloc dont les trente lignes se retrouvent à l'identique
> dans la livraison M3, **sur le même équipement**, à l'arrondi du contrat près,
> est authentique.
>
> **`R-DET-002`** — un bloc dont aucune ligne ne s'y retrouve est fabriqué.

Ce n'est pas consulter un oracle : `sensors/sensor_readings.csv` est une source
publique du pack, au même titre que `equipment.csv`, et les notes de version
désignent explicitement la livraison comme origine des lignes réelles. Le
rapprochement est du travail de contrôle, pas de la triche.

La règle sépare le lot presque parfaitement : **127 blocs retrouvés à 100 %, 66
blocs à 0 %**, six blocs portant une ou deux coïncidences numériques isolées
(`R-DET-003` : à deux décimales, une valeur commune finit par tomber deux fois),
et **un seul bloc entre les deux**.

Une correspondance partielle ne s'invente pas de justification. `R-DET-004`
laisse ce bloc `indécidable`.

## 4. Le plafond de détection, et il n'est pas déplaçable

`EQ-PUMP-171 / vibration_mm_s` est étiqueté **fabriqué** dans l'échantillon. Ses
trente lignes sont **identiques à la livraison** — même équipement, mêmes
horodatages, mêmes valeurs à la deuxième décimale.

Aucune propriété interne ne peut le distinguer d'une mesure réelle, parce qu'il
n'en diffère par aucune propriété interne. Ni l'autocorrélation, ni la
dispersion, ni la grille, ni le niveau : tout est conforme, et pour cause. Soit
le procédé consiste à recopier un segment authentique — auquel cas la détection
est impossible par construction — soit l'étiquette est erronée. Les deux
hypothèses sont ouvertes et **la question est portée à la remontée formateur** :
le lot ne dit pas si « fabriqué » qualifie le procédé appliqué ou le contenu
obtenu, et la différence décide de ce qui est détectable.

C'est la seule erreur du calibrage, et elle coûte 30 lignes sur 720.

## 5. Calibrage — chaque règle mesurée dans les deux sens

Sur `control_sample.csv` : **690 lignes correctement classées sur 720, soit
95,8 %**, un seul bloc faux — celui de la section précédente.

Les cinq autres règles ne décident de rien. Elles **corroborent** : elles disent
si un bloc porte, en plus, une signature interne. Mesurées sur l'échantillon,
puis sur les verdicts du lot :

| Règle | Signature | Blocs fabriqués attrapés (lot) | Blocs **réels** accusés (lot) |
|---|---|---:|---:|
| `R-DET-010` | autocorrélation de rang 4 effondrée — cycle de 24 h absent | 45 / 72 | **14 / 127** |
| `R-DET-011` | grille d'échantillonnage irrégulière | 5 / 72 | 0 |
| `R-DET-012` | niveau incompatible avec le profil de l'équipement | 9 / 72 | 1 / 127 |
| `R-DET-013` | dispersion incompatible avec le profil de l'équipement | 13 / 72 | **6 / 127** |
| `R-DET-014` | valeurs retrouvées chez un autre équipement — greffe | 32 / 72 | 0 |

**Ce tableau justifie à lui seul l'architecture retenue.** Si ces règles avaient
porté la décision, elles auraient déclaré fabriqués **21 blocs authentiques**,
soit 16,5 % du réel. `R-DET-010` est la plus productive et la plus dangereuse :
elle attrape 45 blocs fabriqués et en accuse 14 de trop. Sur l'échantillon, le
bloc `EQ-STEAM-352 / pressure_bar` (second segment) sort à 0,403 d'autocorrélation
— au-dessous du seuil de 0,50 — alors qu'il est authentique. Son cycle journalier
est simplement plus faible que celui de ses voisins.

Deux règles seulement n'accusent jamais à tort : la **grille irrégulière** et la
**greffe inter-équipements**. Ce sont aussi les deux qui reposent sur un fait
vérifiable plutôt que sur un seuil statistique.

Le seuil d'`indécidable` (arbitrage A5) est donc placé sur la seule dimension qui
ne produit pas de fausse accusation — la correspondance —, et il est mesuré dans
les deux sens : un seuil plus strict (« tout ce qui n'est pas intégralement
retrouvé est fabriqué ») trancherait le bloc à 29/30 sans le moindre élément ; un
seuil plus prudent (« fabriqué seulement si une signature interne le confirme »)
laisserait sans verdict les blocs `EQ-CONV-336` et `EQ-COMP-002`, qui ne portent
aucune signature et sont pourtant fabriqués — le rappel tomberait de 89 % à 67 %.

## 6. Verdicts sur le lot

| Verdict | Blocs | Lignes | Part | Règle |
|---|---:|---:|---:|---|
| `réelle` | 127 | 3 810 | 63,5 % | `R-DET-001` |
| `fabriquée` | 72 | 2 160 | 36,0 % | `R-DET-002` (66) · `R-DET-003` (6) |
| `indécidable` | 1 | 30 | 0,5 % | `R-DET-004` |

La proportion fabriquée ressort à **36,0 %**, contre 37,5 % dans l'échantillon.
Les notes de version annoncent « les mêmes proportions » sans les chiffrer :
l'écart d'un point et demi est le seul contrôle externe dont nous disposions, et
il est cohérent. Il ne vaut pas validation — un lot peut être mal qualifié en
bloc tout en respectant une proportion.

**Le bloc indécidable est un cas propre.** `EQ-OVEN-386 / current_a` : 29 lignes
sur 30 retrouvées à l'identique, une seule diffère. Son autocorrélation (0,783)
et sa dispersion (1,054) sont celles d'une série authentique. Soit une valeur a
été altérée dans un bloc réel, soit un bloc fabriqué reproduit 29 valeurs exactes
— ce qui est invraisemblable. Trancher demanderait de savoir si la ligne divergente
est une erreur de mesure ou une retouche, et rien dans le lot ne permet de le dire.

## 7. Onze blocs que rien d'interne ne trahit

**Sur les 72 blocs déclarés fabriqués, 11 ne déclenchent aucune règle de
corroboration** — 330 lignes dont l'autocorrélation, la dispersion, la grille et
le niveau sont conformes à ce qu'on attend d'une mesure réelle.

Sans le rapprochement à la livraison, ces 330 lignes seraient passées. Elles
mesurent exactement ce que valent des contrôles internes seuls face à une
fabrication soignée, et elles expliquent pourquoi le sens 1 s'est terminé sur un
constat d'impuissance : un générateur qui reproduit les marginales et une part de
la structure ne laisse **aucune trace interne exploitable**.

C'est le résultat le plus utile de l'étape pour la suite : la détection d'une
fabrication soignée ne repose pas sur l'examen de la fabrication, mais sur son
rapprochement avec une source de vérité extérieure.

## 8. Contre-épreuve — ce que valent nos règles du brief 1 sur cette question

Le brief demande de conclure sur nos propres règles : lesquelles ont servi,
lesquelles n'ont rien attrapé, lesquelles ont accusé à tort une mesure réelle.
Chacune des dix règles capteurs applicables a été passée sur les 6 000 lignes et
croisée avec les verdicts.

| Contrôle du brief 1 | Lignes signalées | Dont **authentiques** | Verdict d'utilité |
|---|---:|---:|---|
| `R-SEN-006` unité conforme | 210 | **210** | aucune — n'attrape que du réel |
| `R-SEN-005` nom de capteur normalisé | 40 | **40** | aucune — n'attrape que du réel |
| `R-SEN-015` étiquette `period` cohérente | 30 | **30** | aucune — n'attrape que du réel |
| `R-SEN-001` clé logique unique | 2 | **2** | aucune |
| `R-SEN-008` valeur non sentinelle | 1 | **1** | aucune |
| `R-SEN-003` horodatage sur la grille | 210 | 60 | partielle — 150 fabriquées, 60 fausses accusations |
| `R-SEN-009` valeur dans la plage physique | 211 | 31 | partielle — 180 fabriquées, 31 fausses accusations |
| `R-SEN-007` valeur numérique | 1 | 0 | anecdotique |

Cinq règles sur huit qui signalent **n'attrapent que des lignes authentiques**.
Elles ne sont pas mauvaises : elles répondent à une autre question, et elles y
répondent bien. Employées hors de leur objet, elles produisent exclusivement des
fausses accusations.

Le bilan d'ensemble est sans appel. En prenant « signalée par au moins un
contrôle de qualité » comme test d'authenticité :

- **rappel : 15,3 %** — 330 lignes fabriquées sur 2 160 ;
- **fausses accusations : 343 lignes authentiques sur 3 810**, soit 9,0 % ;
- **précision : 49,0 %.**

Une pièce lancée en l'air fait 50 %. C'est la démonstration chiffrée de ce que le
lot a été construit pour établir, et c'est la raison d'être du registre `R-DET-*`.

## 9. Ce que l'étape établit

1. **Détecter une fabrication et détecter une anomalie sont deux problèmes
   disjoints.** Confondre les registres coûte 343 fausses accusations pour
   15 % de rappel.
2. **Les signatures internes ne suffisent pas.** 11 blocs fabriqués sur 72 n'en
   portent aucune ; à l'inverse, 21 blocs authentiques en portent au moins une.
   Elles corroborent, elles ne décident pas.
3. **Le rapprochement à une source extérieure est ce qui décide.** C'est
   l'instrument, pas les statistiques descriptives.
4. **Il existe un plafond.** Un segment authentique recopié est indétectable, et
   aucune règle ne le franchira.
5. **Le silence n'est pas une preuve.** Deux états successifs de notre générateur,
   mesurablement différents, obtiennent du détecteur du module le même zéro.

Les comptages de cette étape constituent la **base de comparaison par règles**
que le modèle du M4 devra battre : 36,0 % de fabriqué détecté avec une seule règle
décisive, et un plafond documenté à 30 lignes indécidables.
