# DiagOps Data Pack — schema

Statut : support apprenant.

Ce document decrit les tables et fichiers fournis pour les travaux DiagOps.
Les donnees sont synthetiques et servent uniquement de support de formation.

## Identifiants communs

Les sources sont reliees par des identifiants stables :

| Champ | Role |
|---|---|
| `equipment_id` | identifiant unique d'un equipement |
| `event_id` | identifiant unique d'un incident, d'une intervention ou d'un evenement suivi |
| `report_id` | identifiant unique d'un rapport technicien |
| `image_id` | identifiant unique d'une image de defaut |
| `timestamp` | horodatage ISO 8601 |
| `period` | periode de livraison des donnees, ex. `2026-S1` |

## Contrat DiagOps

Les modules utilisent le meme contrat de sortie pour les diagnostics :

```json
{
  "equipment_id": "EQ-0001",
  "symptom": "vibration anormale au demarrage",
  "severity": "low|medium|high|critical",
  "failure_hypothesis": "roulement use ou desalignement",
  "recommended_action": "inspection prioritaire du palier",
  "confidence": 0.72,
  "evidence": ["rapport RPT-0001", "mesure vibration elevee"],
  "requires_human_review": true
}
```

## Entites

### `reports`

Rapports textuels rediges par des techniciens.

| Champ | Type | Description |
|---|---|---|
| `report_id` | string | identifiant du rapport |
| `equipment_id` | string ou null | equipement concerne, si identifiable |
| `event_id` | string ou null | evenement associe, si connu |
| `timestamp` | datetime | date de saisie |
| `technician_note` | string | texte libre du rapport |
| `source_channel` | string | canal de saisie |
| `period` | string | periode de disponibilite |

Mise a disposition initiale : `2026-S1/reports/`.

### `annotated_diagnostics`

Sous-ensemble annote utilise en M1 pour entrainer et evaluer le modele DiagOps.

| Champ | Type | Description |
|---|---|---|
| `annotation_id` | string | identifiant de l'annotation |
| `report_id` | string | rapport source |
| `equipment_id` | string ou null | equipement concerne, si identifiable |
| `event_id` | string ou null | evenement associe, si connu |
| `input_text` | string | contexte donne au modele : identifiant equipement disponible, puis rapport technicien |
| `expected_output` | object | JSON DiagOps attendu |
| `split` | enum | `train` ou `test` |
| `period` | string | periode source |

Volume cible :

- `train` : environ 400 exemples ;
- `test` : environ 100 exemples.

L'identifiant d'equipement present dans le rapport structure est inclus dans
`input_text`. La tache M1 ne demande donc pas d'inventer une cle interne a
partir d'un nom d'usage tel que `Pompe P-204`.

Mise a disposition initiale : M1.

### `equipment`

Inventaire des equipements suivis.

| Champ | Type | Description |
|---|---|---|
| `equipment_id` | string | identifiant equipement |
| `equipment_type` | string | famille d'equipement |
| `site_id` | string | site ou atelier |
| `commissioning_date` | date | mise en service |
| `criticality` | enum | `low`, `medium`, `high`, `critical` |

### `sensors`

Mesures temporelles issues des equipements.

| Champ | Type | Description |
|---|---|---|
| `equipment_id` | string | equipement mesure |
| `timestamp` | datetime | date de mesure |
| `sensor_name` | string | nom du capteur |
| `value` | number | valeur mesuree |
| `unit` | string | unite |
| `period` | string | periode de disponibilite |

### `maintenance_history`

Historique des interventions et decisions de maintenance.

| Champ | Type | Description |
|---|---|---|
| `event_id` | string | evenement de maintenance |
| `equipment_id` | string | equipement concerne |
| `opened_at` | datetime | ouverture |
| `closed_at` | datetime | cloture, si applicable |
| `intervention_type` | string | type d'intervention |
| `outcome` | string | resultat |
| `downtime_minutes` | integer | indisponibilite estimee |

### `events`

Evenements permettant de relier les rapports, capteurs, interventions et images.

| Champ | Type | Description |
|---|---|---|
| `event_id` | string | identifiant evenement |
| `equipment_id` | string | equipement concerne |
| `start_at` | datetime | debut |
| `end_at` | datetime | fin, si applicable |
| `event_type` | string | incident, intervention, observation, alerte |
| `severity` | enum | `low`, `medium`, `high`, `critical` |

### `feedback`

Retours des techniciens apres utilisation de DiagOps.

| Champ | Type | Description |
|---|---|---|
| `feedback_id` | string | identifiant du retour |
| `report_id` | string | rapport ou prediction concerne |
| `event_id` | string | evenement associe |
| `timestamp` | datetime | date du retour |
| `user_decision` | string | decision humaine |
| `model_helpfulness` | integer | note de 1 a 5 |
| `comment` | string | commentaire libre |

### `images`

Images de defauts industriels issues d'un corpus externe documente.

| Champ | Type | Description |
|---|---|---|
| `image_id` | string | identifiant image |
| `equipment_id` | string | equipement ou famille d'equipement |
| `event_id` | string | evenement associe, si applicable |
| `image_path` | string | chemin relatif |
| `asset_source` | string | source externe documentee |
| `label` | string | etiquette disponible dans le corpus |

Mise a disposition initiale : M7.

## Periodes

Les donnees sont organisees par periodes temporelles :

- `2026-S1`
- `2026-S2`
- `2027-S1`

Le sens analytique de chaque periode doit etre determine par le travail realise
dans les modules.
