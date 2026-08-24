---
module: M3
objet: écarts constatés dans le matériel pédagogique
maj: 2026-08-24
destinataire: Mickael Mahabot
---

# Écarts constatés dans le matériel — M2 et M3

Trois écarts, prêts à être transmis. Le premier a été constaté en M2 et **est
toujours présent** dans le M3 publié le 24/08/2026 (commit `6c35204`).

## 1. `data_pack/SCHEMA.md` contredit `starter/contracts/schemas.py`

Signalé une première fois pendant le M2, republié tel quel avec le M3.

**a. `event_type` : `alerte` contre `alert`**

`SCHEMA.md` ligne 159 :

```
| `event_type` | string | incident, intervention, observation, alerte |
```

Le contrat livré et les données disent `alert` :

```python
EVENT_TYPES = {"incident", "intervention", "observation", "alert"}
```

Vérifié sur `events.csv` : la valeur présente est bien `alert` (49 occurrences).

**Effet constaté en M2** : une règle écrite d'après `SCHEMA.md` produit **49
fausses anomalies**, l'intégralité des événements de ce type.

**b. `intervention_type` et `outcome` décrits comme chaînes libres**

`SCHEMA.md` lignes 137-138 :

```
| `intervention_type` | string | type d'intervention |
| `outcome`           | string | resultat            |
```

Les deux sont en réalité des **domaines fermés**, confirmés par le contrat et
par les données :

- `intervention_type` : `calibration`, `corrective`, `inspection`,
  `preventive`, `replacement` — 5 valeurs, aucune autre ;
- `outcome` : `follow_up_required`, `monitoring`, `no_fault_found`,
  `parts_ordered`, `resolved` — 5 valeurs, aucune autre.

**Effet** : un apprenant qui suit `SCHEMA.md` ne pose aucun contrôle de domaine
sur ces deux colonnes, et l'absence de contrôle ne se voit nulle part dans le
résultat.

**Correction suggérée** : aligner `SCHEMA.md` sur `contracts/schemas.py`, qui
est la source juste dans les trois cas.

## 2. Un test du starter échoue sous Windows — M3

`M3/starter/tests/test_io.py::test_file_sha256_known_content`

```python
sample.write_text("diagops\n", encoding="utf-8")
assert file_sha256(sample) == "38cc32b0…"
```

Sous Windows, `Path.write_text` traduit `\n` en `\r\n`. Le fichier contient donc
`diagops\r\n`, dont l'empreinte est `dfd23ca5…` et non `38cc32b0…`, qui est
celle de `diagops\n`.

**La fonction `file_sha256` est correcte** — elle lit en binaire. C'est le test
qui dépend de la plateforme.

**Correctif** : `sample.write_text("diagops\n", encoding="utf-8", newline="")`,
ou écrire en octets avec `write_bytes(b"diagops\n")`.

**Portée** : 20 tests sur 21 passent ; celui-ci échoue sur toute machine Windows.
C'est le deuxième test dépendant de la plateforme rencontré après le M2.

## 3. Point mineur — `MANIFEST.yaml` et période réelle

`MANIFEST.yaml` annonce `nominal_step_hours: 6` et `instrumented_equipment: 36`,
tous deux exacts. La `DATA_CARD` précise « du 2 janvier au 30 juin 2026 ».

Les données contiennent **5 mesures hors de ces bornes** : 2 les 28 et
29/12/2025, 3 les 2, 3 et 4/07/2026 — toutes étiquetées `period = 2026-S1`.

Ce n'est pas signalé comme un écart : les « mesures hors période » figurent
explicitement dans la liste des anomalies pédagogiques de la `DATA_CARD`. Le
point est mentionné pour confirmer qu'elles ont bien été détectées, et pour
signaler qu'elles produisent un effet de bord peut-être non prévu : chacune crée
une **fausse interruption d'échantillonnage** dans un décompte naïf des trous —
5 des 6 trous détectés en sont l'artefact.

---

*Constats issus du travail M3 — `projets/diagops-m3/work/M3/`. Chaque chiffre
est reproductible par `python run_cadrage_m3.py`.*
