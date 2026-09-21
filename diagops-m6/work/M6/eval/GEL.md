# Gel du jeu de scénarios — M6

> Un jeu de scénarios se gèle **avant** toute mesure comparative. Après le gel,
> une modification impose une nouvelle version : les chiffres obtenus sur deux
> jeux différents ne se comparent pas.

**Version `m6-scenarios-v3`, gelée le 21/09/2026.**

## Composition

| Source | Scénarios | Empreinte SHA-256 |
|---|---:|---|
| `eval/scenarios.jsonl` | 18 | `8d382ab0594bed6811e22c1cdcee900ff1d15a8a95cff692326ea1a42b477445` |
| `eval/scenarios_extension.jsonl` | 11 | `124f594b6bd7aff81f9d58f7d9a6026339071ef0d5c1945a471a77c65e744775` |
| **`eval/scenarios_v3.jsonl`** | **29** | `7d125e9acbd07697da87d15fcf165d1b015f183281a94d41adda12d4982f0586` |

## Couverture

| Catégorie | Scénarios |
|---|---:|
| `ancrage_document_errone` | 2 |
| `argument_hors_bornes` | 1 |
| `contradictory_sources` | 1 |
| `empty_result` | 1 |
| `hors_perimetre_technique` | 1 |
| `identifiant_ambigu` | 1 |
| `injection_question` | 1 |
| `invalid_argument` | 1 |
| `multi_step` | 3 |
| `nominal_document` | 1 |
| `nominal_equipment` | 1 |
| `nominal_events` | 1 |
| `nominal_history` | 1 |
| `nominal_report` | 1 |
| `out_of_scope` | 1 |
| `preuve_tronquee` | 1 |
| `revision_perimee` | 1 |
| `role_restriction` | 1 |
| `role_superieur` | 1 |
| `short_channel` | 1 |
| `timeout` | 1 |
| `unavailable_tool` | 1 |
| `unknown_id` | 1 |
| `unknown_report` | 1 |
| `useless_tool` | 1 |
| `valeur_hors_domaine` | 1 |

**17 réponses attendues, 12 refus attendus.**

## Ce que la validation contrôle

- champs requis, identifiants uniques, rôle et attente connus ;
- outils attendus et interdits présents au registre, et disjoints ;
- arguments minimaux **acceptés par le contrat de l'outil** — un scénario ne peut
  pas exiger un appel que le registre refuserait ;
- preuves attendues présentes dans le data pack ;
- un refus attendu n'exige pas de preuve, et réciproquement une réponse sans preuve
  exigée est signalée.

```bash
python eval/freeze_scenarios.py --check   # valide et vérifie les empreintes
```

## Règle de modification

Après gel, un scénario ne se corrige pas en place : toute modification produit
la version suivante, et les mesures antérieures restent attachées à la version
sur laquelle elles ont été obtenues.

**v2 → v3 (21/09/2026)** : `SCN-023` reformulé. Sa première rédaction attendait un
refus sur « a-t-il déjà connu une récidive », en contradiction avec `SCN-004` du
starter qui attend une réponse sur la même famille de question — et à raison : une
récidive est une **existence**, et une existence se démontre sur un sous-ensemble dès
que la répétition y est visible. La question porte désormais sur un **total**, qui ne
se démontre pas sur un échantillon tronqué.
