# Livraison candidate M2 — lot 02

**Identifiant : `diagops-2026-S1-m2-candidate-r2`**
**Statut : livraison candidate à qualifier — ne pas intégrer automatiquement**

## Objet

Ce dossier simule une nouvelle livraison reçue après la publication du socle
M2. Il sert au complément « Pour aller plus loin » du module 2.

La livraison doit être comparée aux données déjà publiées dans :

- `../equipment/equipment.csv` ;
- `../events/events.csv` ;
- `../maintenance/maintenance_history.csv`.

## Contenu reçu

| Fichier | Nature | Lignes annoncées | Règle d'intégration envisagée |
|---|---|---:|---|
| `equipment_update.csv` | ajouts et mises à jour du parc | 30 | insertion ou mise à jour par `equipment_id` |
| `events_batch_02.csv` | nouveaux événements | 80 | ajout sans collision de `event_id` |
| `maintenance_batch_02.csv` | nouvelles interventions | 220 | ajout sans collision de `maintenance_id` |

Ces volumes sont ceux annoncés par le fournisseur. Ils ne constituent pas une
preuve de qualité.

## Évolutions annoncées

- Le fichier de maintenance ajoute la colonne facultative `source_system` afin
  d'identifier le système ayant exporté la ligne.
- Une mise à jour d'équipement peut employer un identifiant déjà présent dans
  le parc. Ce recouvrement n'est donc pas automatiquement un doublon : sa
  signification doit être examinée comme une opération de mise à jour.
- Les événements et interventions sont des ajouts. Une collision de leur clé
  avec l'historique n'est pas attendue.

## Responsabilité de qualification

Les fichiers sont livrés tels qu'ils ont été reçus. Leur présence dans le data
pack ne signifie pas qu'ils sont conformes. Avant toute intégration, il faut
notamment vérifier le schéma, les identifiants, les relations, la chronologie,
la complétude, les valeurs inhabituelles et les notes libres.

Le fichier `checksums.sha256` permet uniquement de vérifier que la livraison
n'a pas été modifiée depuis sa publication.
