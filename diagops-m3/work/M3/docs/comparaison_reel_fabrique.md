---
module: M3
brief: brief 2 — online
etat: étape 3 terminée
maj: 2026-08-25
---

# Génération et comparaison réel / fabriqué — étape 3

C'est le point central du brief : **une génération qui respecte chaque colonne
prise isolément peut détruire toutes les relations entre elles, et cette perte
ne se voit sur aucun histogramme.** Ce document le mesure.

Rejouable par `python run_generation_b2.py` — graine `25082026`, sorties
identiques à l'octet près sur deux exécutions.

## 1. Périmètre — arbitrage A2

Les **8 équipements de `SITE-OUEST` appartenant à `SEG-2`**.

`SITE-OUEST` est le périmètre non instrumenté que le brief désigne (0 capteur
sur 16 équipements). `SEG-2` est le segment que l'étape 1 a identifié comme le
moins couvert (2 instrumentés sur 174). Leur intersection satisfait les deux
critères, et se trouve parfaitement équilibrée en criticité.

| Équipement | Type | Criticité |
|---|---|---|
| `EQ-COMP-189` | compressor | `critical` |
| `EQ-PUMP-002` | pump | `critical` |
| `EQ-DRYER-264` | dryer | `high` |
| `EQ-FAN-120` | fan | `high` |
| `EQ-OVEN-203` | oven | `medium` |
| `EQ-ROBOT-173` | robot | `medium` |
| `EQ-FAN-104` | fan | `low` |
| `EQ-PUMP-230` | pump | `low` |

Bornage : **2 capteurs** (`vibration_mm_s`, `temperature_c`), **un mois**
(01/01 → 31/01/2026), pas nominal de 6 h — soit 124 horodatages par série.

## 2. Ce que la génération ne peut pas faire

Les séries DiagOps portent un cycle journalier, mais **chaque série a sa propre
phase**. `EQ-CAB-134` culmine en température à minuit (59,55 °C) et creuse à
midi (50,91) ; `EQ-CHILL-001` fait l'inverse (52,4 à minuit, 58,8 à midi).
Moyennées sur le parc, ces phases se compensent : le profil horaire global est
plat, ce qui avait d'abord fait croire à l'absence de cycle.

Pour un équipement dépourvu de tout capteur, **la phase de son cycle est une
information absente du jeu de données**. Aucune méthode ne la crée. On peut
reproduire l'existence d'un cycle et son amplitude ; prétendre en reproduire la
phase serait inventer une information.

C'est la limite structurelle de l'étape, et elle vaut pour les deux voies.

## 3. Les deux voies

### `PROC-GEN-MARG-V1` — tirage marginal

Chaque valeur est tirée dans la distribution empirique du capteur, sans égard
pour l'instant, l'équipement ou la valeur précédente. Toutes les marginales sont
respectées **par construction**, et rien d'autre.

### `PROC-GEN-SMOTE-V1` — interpolation entre voisins

Écrit à la main avec `NearestNeighbors`, selon le principe de SMOTE.

1. **Voisinage au niveau équipement.** Descripteurs : `criticite_ordinale`,
   `log(puissance)`, `age_annees`, standardisés. `k = 5`.
2. **Traitement explicite des catégories.** Interpoler numériquement une
   catégorie n'a aucun sens : à mi-chemin entre `vibration_mm_s` et
   `temperature_c`, il n'y a rien. Deux traitements distincts, selon le principe
   de SMOTE-NC :
   - dans la **distance**, une différence de `equipment_type` ajoute une pénalité
     fixe de 1,0 — soit le coût d'un écart d'un écart-type sur une variable
     continue. `NearestNeighbors` ne sait pas gérer cette pénalité : on récupère
     un voisinage large puis on réordonne sur la distance corrigée ;
   - dans la **génération**, `unit` est obtenue par **vote majoritaire** parmi
     les voisins, jamais par interpolation.
3. **Interpolation.** Pour chaque horodatage, deux donneurs sont tirés parmi les
   `k` voisins et leurs valeurs au même instant sont interpolées :
   `v = v_i + λ (v_j − v_i)`, avec `λ ~ U(0,1)` tiré **à chaque point**, comme
   dans le SMOTE canonique.

**La pénalité de type ne peut pas toujours être satisfaite.** `EQ-DRYER-264` est
un `dryer`, et **aucun `dryer` du parc n'est instrumenté** — c'est l'un des sept
types sans aucune mesure. Ses cinq voisins sont un chiller, deux fans, un mixer
et un capteur. Le générateur emprunte donc à d'autres types, faute de mieux, et
c'est une décision qui doit être portée avec la donnée.

**Un couple n'a produit aucune ligne.** `EQ-OVEN-203 / vibration_mm_s` : aucun
de ses cinq voisins ne porte ce capteur. 124 points manquants, plus 61 points
isolés dont les donneurs n'avaient pas de mesure à l'instant demandé — soit
**185 points sans donneur**, tracés dans `generation.json`.

| Procédé | Lignes produites |
|---|---:|
| `PROC-GEN-MARG-V1` | 1 984 |
| `PROC-GEN-SMOTE-V1` | 1 799 |

## 4. Comparaison — les marginales

| Origine | Capteur | Moyenne | Médiane | Écart-type | q25 | q75 |
|---|---|---:|---:|---:|---:|---:|
| réel | `temperature_c` | 57,60 | 57,82 | **4,958** | 54,25 | 61,17 |
| `PROC-GEN-MARG-V1` | `temperature_c` | 57,87 | 57,98 | **4,882** | 54,31 | 61,55 |
| `PROC-GEN-SMOTE-V1` | `temperature_c` | 57,92 | 58,12 | **3,847** | 55,01 | 60,89 |
| réel | `vibration_mm_s` | 2,844 | 2,82 | **0,386** | 2,58 | 3,08 |
| `PROC-GEN-MARG-V1` | `vibration_mm_s` | 2,874 | 2,86 | **0,387** | 2,61 | 3,12 |
| `PROC-GEN-SMOTE-V1` | `vibration_mm_s` | 2,820 | 2,79 | **0,328** | 2,58 | 3,03 |

**Le tirage marginal est irréprochable** : écart-type à 1,5 % près, quantiles
alignés. C'est sa définition même.

**L'interpolation contracte la dispersion** : écart-type −22 % sur la
température, −15 % sur la vibration. C'est un effet connu et structurel de
SMOTE — tout point interpolé se trouve **à l'intérieur** du segment reliant deux
observations, donc l'enveloppe se rétrécit à chaque tirage. Les extrêmes,
qui sont précisément ce qui intéresse un diagnostic de maintenance, sont les
premiers perdus : le maximum de vibration tombe de 4,47 à 4,22.

Si l'on s'arrêtait au tableau ci-dessus, on conclurait que le tirage marginal
est le meilleur des deux générateurs.

## 5. Comparaison — les relations

### 5.1 Structure temporelle (autocorrélation aux rangs 2 et 4)

| Origine | Capteur | Rang 2 (12 h) | Rang 4 (24 h) |
|---|---|---:|---:|
| réel | `temperature_c` | **−0,759** | **+0,803** |
| `PROC-GEN-MARG-V1` | `temperature_c` | +0,022 | −0,024 |
| `PROC-GEN-SMOTE-V1` | `temperature_c` | −0,594 | +0,599 |
| réel | `vibration_mm_s` | **−0,459** | **+0,527** |
| `PROC-GEN-MARG-V1` | `vibration_mm_s` | +0,011 | −0,077 |
| `PROC-GEN-SMOTE-V1` | `vibration_mm_s` | −0,310 | +0,252 |

**Voilà le résultat du brief.** Le tirage marginal, dont chaque histogramme est
parfait, produit des séries de **structure temporelle nulle** : +0,02 et −0,02
là où le réel donne −0,76 et +0,80. Il ne reste rien du cycle journalier. Sur
une distribution, la fabrication est indétectable ; sur l'autocorrélation, elle
est flagrante.

L'interpolation conserve environ **75 % de l'amplitude** du cycle sur la
température (0,599 contre 0,803) et **48 %** sur la vibration. La perte
s'explique : `λ` étant tiré à chaque point, deux donneurs de phases différentes
sont mélangés dans des proportions qui changent d'un instant à l'autre, ce qui
atténue le cycle. Un `λ` fixé par série le préserverait davantage — c'est la
première piste si la confrontation de l'étape 4 le réclame.

### 5.2 Relation entre colonnes (vibration ↔ température)

| Origine | Équipements | Corrélation médiane |
|---|---:|---:|
| réel | 3 | **−0,142** |
| `PROC-GEN-MARG-V1` | 8 | −0,048 |
| `PROC-GEN-SMOTE-V1` | 7 | −0,005 |

**Ce test n'est pas concluant, et il faut le dire.** Seuls 3 équipements
instrumentés portent les deux capteurs simultanément, et la corrélation réelle
y est faible (−0,14). Sur une base aussi mince, l'écart avec les fabriqués n'est
pas interprétable. La relation entre colonnes ne peut pas servir de test
discriminant sur ce corpus.

### 5.3 Relation entre sources (réaction aux événements)

C'est la relation la plus exigeante : elle met en jeu `events.csv`, que ni l'un
ni l'autre générateur ne consulte.

| Origine | Capteur | En fenêtre | Écart | p (Mann-Whitney) | Réaction |
|---|---|---:|---:|---:|---|
| réel — 2026-S1 | `vibration_mm_s` | 508 | **+7,42 %** | < 0,0001 | **oui** |
| réel — 2026-S1 | `temperature_c` | 777 | **+2,69 %** | < 0,0001 | **oui** |
| `PROC-GEN-MARG-V1` | `vibration_mm_s` | 148 | −0,58 % | 0,829 | non |
| `PROC-GEN-MARG-V1` | `temperature_c` | 148 | −1,02 % | 0,093 | non |
| `PROC-GEN-SMOTE-V1` | `vibration_mm_s` | 117 | +0,08 % | 0,707 | non |
| `PROC-GEN-SMOTE-V1` | `temperature_c` | 148 | −1,01 % | 0,093 | non |

**Aucun des deux générateurs ne reproduit la réaction aux événements.** La
vibration réelle monte de 7,4 % pendant les fenêtres d'observation ; les séries
fabriquées ne bougent pas.

Pour le tirage marginal, c'est attendu. **Pour l'interpolation, c'est plus
intéressant** : elle copie pourtant des séries réelles, qui *portent* cette
réaction. Mais les événements de l'équipement donneur ne tombent pas aux mêmes
dates que ceux de l'équipement cible : le signal existe dans la matière
première, au mauvais moment. Copier une série réelle ne transporte pas son
calendrier.

> **Une précaution de méthode qui a changé la conclusion.** Ce test a d'abord
> été mené sur le seul mois de janvier — le périmètre du livrable. Restreint à
> janvier, il ne détecte **rien**, y compris **sur le réel** : p = 0,18 pour la
> température et p = 0,97 pour la vibration. Conclure « les fabriqués ne
> réagissent pas » à partir d'un test incapable de voir la réaction du réel
> aurait été une faute. Une génération de contrôle couvrant tout le semestre a
> donc été produite pour cette seule question, et le tableau ci-dessus en est
> tiré. Le livrable reste borné à janvier.

## 6. Contraintes métier

Question 8 du brief : combien de lignes générées violent une règle M2 ou M3 ?

| Contrôle | `PROC-GEN-MARG-V1` | `PROC-GEN-SMOTE-V1` |
|---|---:|---:|
| `R-SEN-001` clé logique unique dans le lot | 0 | 0 |
| `R-SEN-001` clé en collision avec le réel | 0 | 0 |
| `R-SEN-003` horodatage sur la grille de 6 h | 0 | 0 |
| `R-SEN-006` unité cohérente avec le capteur | 0 | 0 |
| `R-SEN-007` valeur renseignée et numérique | 0 | 0 |
| `R-SEN-008` valeur non négative | 0 | 0 |
| `R-SEN-009` valeur dans la plage robuste (8 MAD) | **2** | 0 |
| `R-SEN-013` équipement présent dans le parc | 0 | 0 |
| `R-SEN-014` mesure dans la période annoncée | 0 | 0 |
| `R-SEN-015` étiquette `period` cohérente | 0 | 0 |
| Précision à deux décimales | 0 | 0 |

**Deux lignes en faute sur 3 783.** Le contraste avec la section précédente est
le vrai enseignement : **nos contrôles de qualité valident presque intégralement
1 984 lignes dont la structure temporelle est nulle.** Ils regardent chaque
ligne isolément, et une fabrication qui respecte les bornes, la grille et les
unités les traverse sans encombre.

Les zéros de `R-SEN-001` s'expliquent par le périmètre : les équipements cibles
n'ayant aucune mesure réelle, aucune collision de clé n'est possible. Ce n'était
pas le cas des augmentations de l'étape 2, qui entraient en collision sur 99,5 à
100 % de leurs lignes.

## 7. Ce que chaque voie reproduit et ne reproduit pas

| | `PROC-GEN-MARG-V1` | `PROC-GEN-SMOTE-V1` |
|---|---|---|
| Marginales | **fidèles** (écart-type à 1,5 %) | contractées (−15 à −22 %) |
| Extrêmes | conservés | **perdus** (max 4,47 → 4,22) |
| Cycle journalier | **détruit** (autocorr. ≈ 0) | conservé à 48–75 % |
| Phase du cycle | absente — impossible | absente — impossible |
| Relation entre capteurs | non concluant | non concluant |
| Réaction aux événements | **absente** | **absente** |
| Contrat `SCHEMA.md` | respecté (2 lignes hors plage) | respecté |

## 8. Limites

- **Aucun des deux générateurs n'est validé à ce stade.** L'étape 3 mesure des
  écarts ; la confrontation au détecteur de référence est l'étape 4, et la
  décision de transmission la partie 6.
- **La comparaison des marginales porte sur des populations différentes** : le
  réel décrit 36 équipements instrumentés, majoritairement critiques, les
  fabriqués décrivent 8 équipements de `SEG-2`. Un écart de niveau ne serait donc
  pas nécessairement un défaut du générateur.
- **`k = 5` et la pénalité de type à 1,0 sont des choix**, déclarés dans le code
  et non optimisés. Une pénalité plus forte aurait écarté davantage de donneurs
  de types différents — et pour `EQ-DRYER-264`, elle n'aurait rien changé :
  aucun `dryer` n'est instrumenté.
- **`λ` tiré par point est le principe canonique de SMOTE**, pas nécessairement
  le meilleur choix pour une série temporelle. C'est un paramètre à reprendre si
  l'étape 4 sanctionne la perte de structure.

## 9. Figures

- `figures/generation_series.png` — une série réelle et les deux séries
  fabriquées. Le tirage marginal se voit à l'œil nu : aucun motif ;
- `figures/generation_distributions.png` — les distributions comparées. Le
  tirage marginal y est le plus fidèle des deux. C'est exactement là que
  s'arrêterait une comparaison limitée aux marginales — et c'est le critère
  bloquant du brief.
