# Lot de contrôle capteurs — 2026-S1

Ce lot accompagne le brief 2 du module M3. Il contient des mesures
capteurs dont une partie a été fabriquée. Il n'est pas une livraison
opérationnelle : il sert exclusivement à éprouver des contrôles.

## Contenu

| Fichier | Lignes | Colonne `provenance` |
|---|---:|---|
| `control_batch.csv` | 6000 | absente |
| `control_sample.csv` | 720 | présente |

`control_batch.csv` est le lot à qualifier. `control_sample.csv` est un
échantillon **disjoint**, produit par la même procédure et dans les mêmes
proportions, dont la provenance de chaque ligne est déclarée. Il sert à
régler des contrôles, jamais à conclure sur le lot.

## Schéma

Les colonnes de `control_batch.csv` sont celles de
`2026-S1/sensors/sensor_readings.csv` : `equipment_id`, `timestamp`,
`sensor_name`, `value`, `unit`, `period`. `control_sample.csv` ajoute
`provenance`, à valeurs `réelle` ou `fabriquée`.

La clé logique reste le triplet `equipment_id + timestamp + sensor_name`.
Le pas nominal est de six heures. Le contrat complet est décrit dans
`data_pack/SCHEMA.md`.

## Ce que le lot ne dit pas

La proportion de lignes fabriquées n'est pas communiquée, ni dans ce
fichier ni ailleurs dans le pack. Les procédés de fabrication ne sont pas
décrits. Les mesures réelles proviennent de la livraison M3 et contiennent
donc les défauts de qualité de cette livraison : une ligne anormale n'est
pas nécessairement une ligne fabriquée.

## Intégrité

```
90b45987d8f6b093906386f0204b243bc72270b9978e21f81cde666397738964  control_batch.csv
cc8912a2cb3b27a33e2ced37b9c13fe4a2438e4dc44264aaab3d97c04e1a1da0  control_sample.csv
```

Graine de génération : `20260825`. Période : `2026-S1`.
