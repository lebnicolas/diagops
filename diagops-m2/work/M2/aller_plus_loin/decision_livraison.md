# Note de decision — livraison `diagops-2026-S1-m2-candidate-r2`

**Date** : 04/08/2026
**Politique appliquee** : `quality_rules.yaml` version 1.0.0
**Statut produit par la qualification** : `REJECTED`
**Decision d'integration** : **rejet, relivraison demandee au fournisseur**

Les empreintes des fichiers controles, la version des regles et le detail des
constats figurent dans `run_manifest.json`. Les rapports complets sont dans
`reports/baseline/` et `reports/candidate_release/`.

---

## Resultat en une ligne

| Lot | Statut | Erreurs | Avertissements | Informations |
|---|---|---:|---:|---:|
| Socle publie (non-regression) | `ACCEPTED_WITH_WARNINGS` | 0 | 25 | 1 |
| Livraison candidate | `REJECTED` | 4 | 22 | 5 |

Le socle publie est qualifie avec la meme politique, a chaque execution. Une
politique qui rejetterait ce qui a deja ete accepte ne pourrait rien dire d'une
livraison nouvelle.

---

## Les quatre constats bloquants

### 1. Interventions ouvertes avant leur propre evenement — 86 sur 220

`MNT-TMP-003`, 39,09 % du lot. Les 86 interventions concernees referencent
**toutes** des evenements du lot candidat, aucune de l'historique. L'ecart va
de trente minutes a dix-neuf jours, mediane huit jours.

Sur le socle publie, le meme controle donne **0 echec sur 1 814 lignes**.

Ce n'est donc pas une derive de saisie ni un lot legerement plus sale que le
precedent : les deux tables du lot ont ete horodatees independamment l'une de
l'autre. La regle est passee d'`avertissement` a `erreur` par le mecanisme de
plafond de la politique — a 39 %, le constat ne decrit plus des lignes fausses
mais une livraison fausse.

### 2. `EVT-2026S1-0001` reutilise une cle deja publiee

`INC-KEY-003`. Les notes de livraison annoncent des **ajouts**, sans collision
attendue. Or la cle revient, et elle ne porte pas la meme chose :

| | equipment_id | start_at | severity |
|---|---|---|---|
| publie | `EQ-PUMP-001` | 2026-02-19T22:47:00Z | high |
| candidat | `EQ-M2X-001` | 2026-05-02T19:00:00Z | low |

Ce n'est pas un renvoi accidentel du meme lot : ce sont deux evenements
distincts sous un meme identifiant. Integrer reviendrait a ecraser un
evenement de l'historique ou a le dedoubler, selon la strategie d'insertion.

### 3. `MNT-2026S1-0001` reutilise une cle deja publiee

`INC-KEY-004`, meme situation cote interventions : evenement rattache, machine,
dates, resultat, duree, cout et note libre different tous de la version
publiee. Enjeu supplementaire : les couts et les temps d'arret se cumulent, un
dedoublement fausserait directement les indicateurs.

Cette meme ligne livre par ailleurs `labor_hours` a `'0.87'` **en texte**, la
ou la colonne est numerique dans le publie — c'est l'unique echec de
`MNT-SCH-003`.

### 4. Un equipement sans identifiant

`EQP-KEY-001`. La ligne est complete par ailleurs (`pump`, `SITE-SUD`,
`Valcor`, 44 kW, mise en service le 12/05/2021) mais sans `equipment_id`. Elle
ne peut etre rattachee a rien, ni citee en quarantaine autrement que par son
rang dans le fichier. Seul le fournisseur peut la completer.

---

## Ce qui n'est pas bloquant et merite d'etre dit

- **`EQ-M2X-002` livre deux fois.** Les deux lignes sont **strictement
  identiques** sur les sept colonnes. Ce n'est pas un conflit de version mais
  une duplication a l'export : la correction est certaine et ne perd aucune
  information. Elle reste un avertissement, pas une erreur.
- **Colonne `source_system`** sur la maintenance : annoncee dans les notes de
  livraison, donc tracee en information. Non annoncee, elle aurait leve un
  avertissement — le controle M2 ne regardait que les colonnes absentes et
  n'aurait rien vu du tout.
- **Quatre mises a jour d'equipements** deja presents au parc, conformes a
  l'operation annoncee. Aucune ne modifie `site_id` ni `commissioning_date` :
  rien qui reecrive l'interpretation d'un historique.
- **Deux valeurs inedites** sur des categories ouvertes : le type
  `hydraulic_unit` et le site `SITE-CENTRE`. Aucun schema n'autorise a les
  rejeter ; elles sont signalees pour que la nomenclature reste sous controle.
- **Deux notes de travail contenant des donnees personnelles** (0,91 %), sous
  le plafond de 10 % au-dela duquel le champ serait considere comme une main
  courante nominative.

---

## Reponses aux dix questions

**1. Quels controles M2 ont pu etre reutilises sans modification ?**

Sur 68 controles executes, **45 se rejouent tels quels** : types convertibles,
bornes numeriques, ordre et anteriorite des dates, taux de valeurs absentes,
doublons exacts, unicite intra-lot, detection de donnees personnelles,
inventaires de categories. Tous ont en commun de juger une ligne, ou une
colonne, sans rien avoir besoin de savoir du reste du monde.

**18 controles** dependent reellement du contexte ou d'une constante : trois
references, trois controles croises entre tables, deux controles de periode et
dix controles d'appartenance a une enumeration fermee. Cinq autres traversent
le mecanisme etendu sans en dependre — la detection de variante de casse ne
compte rien, elle compare.

L'architecture M2 a bien tenu : `run_audit()` recevait deja un dictionnaire de
DataFrames et non des chemins, et `_specs()` branchait chaque regle sur un
controle generique. Rien n'a eu a etre reecrit, seulement etendu.

**2. Quelles hypotheses de la premiere solution etaient trop liees aux fichiers initiaux ?**

Quatre, par ordre de gravite.

- **Les references se resolvaient a l'interieur du lot.** `EVT-REF-002`
  cherchait l'`equipment_id` d'un evenement dans les equipements du meme
  dictionnaire. Applique tel quel au lot candidat, il aurait declare orphelins
  les 80 evenements, qui portent sur des machines du catalogue publie. Les
  trois controles croises (`EVT-TMP-003`, `MNT-TMP-003`, `MNT-REF-003`) avaient
  le meme defaut, en pire : ils ne produisaient pas de faux positifs, ils
  s'eteignaient silencieusement.
- **La recurrence d'une valeur inconnue se calculait sur la taille du lot.**
  Il fallait 90 occurrences pour qu'une valeur cesse d'etre une anomalie sur
  1 800 lignes d'historique, 11 sur un lot de 220, et le seuil etait hors
  d'atteinte sur 30 lignes. La meme valeur, dans le meme fichier, changeait de
  classe selon le perimetre examine.
- **`EXPECTED_PERIOD = "2026-S1"`** etait une constante du module. Une
  livraison 2026-S2 aurait echoue sur chacune de ses lignes.
- **Une cle qui revient etait forcement un doublon.** Sur un lot de mise a jour,
  un identifiant deja connu est l'operation attendue, pas une anomalie.

Une cinquieme hypothese n'etait pas fausse mais aveugle : `missing_columns()`
calcule `requises - presentes` et ne voit que les absences. Une colonne
supplementaire ne declenchait rien.

**3. Le schema ou les categories ont-ils evolue, et ces changements sont-ils acceptables ?**

Oui, et oui — sous reserve.

La colonne `source_system` est ajoutee a la maintenance et annoncee comme
facultative. Elle est acceptable : elle n'enleve rien, elle documente
l'origine d'une ligne. Aucune colonne du contrat n'est absente.

Deux valeurs inedites apparaissent sur des categories ouvertes,
`hydraulic_unit` et `SITE-CENTRE`. Acceptables egalement : un parc industriel
accueille de nouveaux types de machines et de nouveaux sites. Elles sont
tracees pour que la nomenclature n'evolue pas sans que personne le sache.

En revanche `labor_hours` livre une valeur en texte sur une ligne. Ce n'est pas
une evolution de contrat, c'est un defaut d'export.

**4. La qualite globale du lot s'ameliore-t-elle ou se degrade-t-elle ?**

Elle se degrade, et sur les deux plans a la fois.

En densite d'abord. Rapporte au volume, le cumul des lignes en avertissement
represente **2,19 % du socle publie** (60 sur 2 740 lignes) contre **9,39 % du
lot candidat** (31 sur 330). Une meme ligne peut etre comptee plusieurs fois si
elle enfreint plusieurs regles, mais le biais joue identiquement des deux
cotes : le lot candidat est environ quatre fois plus dense en anomalies que ce
qui a deja ete accepte.

En nature ensuite, et c'est le point decisif. `MNT-TMP-003` passe de **0 % sur
le publie a 39,09 % sur le candidat**. Sur ce controle, le lot n'est pas un peu
moins bon que le socle : il presente un defaut que le socle ne presentait pas
du tout.

**5. Quels ecarts concernent une ligne et lesquels concernent l'ensemble ?**

C'est exactement ce que traduit le mecanisme de plafond de la politique.

Concernent **une ligne** : l'equipement sans identifiant, le doublon
`EQ-M2X-002`, l'evenement orphelin, la valeur en texte dans `labor_hours`,
les deux notes contenant des donnees personnelles. Chacun se traite
individuellement, sans remettre en cause le reste.

Concernent **la livraison** : les 86 interventions desynchronisees. Aucune
n'est corrigible isolement, parce qu'on ignore laquelle des deux dates est la
bonne — celle de l'evenement ou celle de l'intervention. Le defaut est en
amont, dans la construction du lot.

Cas particulier, les deux collisions de cle. Elles ne portent que sur deux
lignes, mais leur consequence porte sur l'historique : integrer, c'est
modifier des donnees deja publiees. Le nombre est faible, l'effet ne l'est pas.

**6. Quelles regles doivent bloquer automatiquement une integration ?**

Celles dont l'echec rend une ligne inexploitable (`quarantaine_rejet`, dont
`EQP-KEY-001`), celles qui rendent une source illisible (`arret_audit`), les
collisions de cle avec l'historique (`INC-KEY-003`, `INC-KEY-004`) — et toute
regle dont le taux d'echec depasse son plafond, quel que soit son niveau
nominal.

Ce dernier point est le plus important : ce n'est pas la regle qui bloque,
c'est son ampleur.

**7. Quels constats necessitent une decision humaine ou metier ?**

Les doublons de cle intra-lot — il faut dire laquelle des deux lignes fait
foi, meme quand elles sont identiques. Les valeurs inedites de categorie
ouverte — il faut confirmer que `SITE-CENTRE` est un site reel. Les donnees
personnelles dans les notes. Les quatre mises a jour d'equipements. Et,
toujours en attente depuis le 03/08, les 595 interventions du socle publie qui
facturent des pieces sans en declarer, auxquelles ce lot en ajoute 45.

**8. Le lot peut-il etre integre sans rendre l'historique incoherent ?**

Non. Les deux collisions de cle suffisent a repondre : elles ecraseraient ou
dedoubleraient un evenement et une intervention deja publies. Et les 86
interventions desynchronisees introduiraient dans l'historique une population
de lignes ou l'ordre de causalite est inverse, ce que le socle ne contient
aujourd'hui nulle part.

**9. Les resultats sont-ils reproductibles ?**

Oui, sous trois conditions toutes remplies par le manifeste : les empreintes
SHA-256 des six fichiers controles, la version **et** l'empreinte de la
politique, et une date de reference passee explicitement — sans quoi les
controles de non-anteriorite changeraient de resultat d'un jour a l'autre.

Les empreintes du socle publie sont enregistrees au meme titre que celles du
lot recu. Ce n'est pas de la precaution : la politique compte les valeurs de
categorie sur l'union des deux, la qualification du candidat depend donc de
l'etat du publie.

Un test verifie que deux executions sur les memes entrees produisent le meme
tableau de constats, ligne pour ligne.

**10. Quelle decision ?**

**Rejet, avec demande de relivraison.**

Aucune des quatre erreurs ne se corrige de notre cote sans inventer de la
donnee. Les 86 interventions desynchronisees demandent de savoir quelle date
fait foi. Les deux collisions demandent de savoir si le fournisseur a voulu
mettre a jour ou ajouter. L'equipement sans identifiant demande son
identifiant. Ce sont quatre questions pour le fournisseur, pas quatre
corrections a appliquer.

Sont transmis avec la demande : `reports/candidate_release/summary.md`, le
detail ligne a ligne dans `findings.csv`, et `run_manifest.json` pour que le
fournisseur puisse verifier qu'il parle bien des memes fichiers.

Les donnees publiees ne sont pas modifiees. La livraison candidate reste en
place, telle qu'elle a ete recue.

---

## Ce que cette qualification ne dit pas

- **Aucune revue contradictoire externe.** Toutes les objections ci-dessus
  viennent de nos propres controles. C'est la meme limite qu'en M1 et en M2, et
  elle est toujours la.
- **Les seuils de plafond sont des choix, pas des mesures.** 2 % sur les
  references, 5 % sur les controles croises, 10 % sur les donnees
  personnelles : aucun ne se deduit des donnees. Ils sont dans le YAML, avec
  leur justification, precisement pour etre contestes.
- **Un seul lot candidat a ete qualifie.** Que la politique tienne sur une
  deuxieme livraison reste a demontrer.
