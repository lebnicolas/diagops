# Plan de travail — Brief 3 : veille technologique et réglementaire DiagOps

Mission de M0 à M4, 12 h au total. Ce fichier pilote l'avancement : on coche au fur et à mesure, les livrables se remplissent progressivement (jamais d'un coup en fin de parcours).

## Livrables et fichiers

| Fichier | Livrable | Rempli en |
|---|---|---|
| `sources_veille.md` | Cartographie ≥ 15 sources qualifiées | M0, enrichi ensuite |
| `journal_veille.md` | ≥ 4 entrées substantielles (1 par module M0→M3) | M0 → M3, révision avant fin M4 |
| `ai_act_diagops.md` | Analyse AI Act — scénarios A et B | M4 (préparé par le journal) |
| `radar_technologique.md` | Radar Adopter / Évaluer / Surveiller / Écarter | M4 |
| `recommandations_architecture_m4.md` | Recommandations pour le dossier d'architecture | fin M4 |

## Phase M0 — Initialisation (4 h)

- [x] Créer l'arborescence `veille_diagops/`
- [x] Définir la méthode de veille — actée le 21/07/2026 :
  - canaux : alertes email (boîte de veille dédiée + dossier/filtre), flux RSS agrégés par script maison avec digest email hebdomadaire, watch GitHub → Releases, consultation périodique pour les sources sans flux
  - rythme : dépouillement le vendredi 9h30 (30 min), digest livré avant
  - grille de qualification : les 3 questions du brief (fiabilité de la source ? quoi a changé et quand ? quelle décision DiagOps ?)
  - reste à rédiger dans `sources_veille.md`
- [x] `sources_veille.md` : cartographie rédigée le 21/07/2026 — 16 sources sur les 5 familles :
  - [x] textes réglementaires et autorités publiques : EUR-Lex 2024/1689 (alerte My EUR-Lex), Commission digital-strategy (consultation périodique), AI Act Service Desk (abonnement SIP updates), CNIL (RSS)
  - [x] publications scientifiques et actes de conférences : arXiv cs.CL (RSS), NeurIPS (actes annuels, filtre orals/spotlights), ACL Anthology
  - [x] documentation technique primaire : FastAPI, LM Studio, HF Transformers
  - [x] model cards, dépôts et notes de version : Mistral AI, HF Hub, Qwen
  - [x] presse spécialisée et analyses secondaires : ActuIA, The Batch, Simon Willison
- [ ] Mettre en place les canaux (actions manuelles) :
  - [ ] compte EU Login + alerte EUR-Lex sur le règlement 2024/1689
  - [ ] abonnement "SIP updates" de l'AI Act Service Desk
  - [ ] dossier + filtre "veille" dans la boîte email dédiée
  - [ ] script d'agrégation RSS + digest email (à coder une fois les 15 sources posées)
- [x] Vérifier sur sources officielles le calendrier d'application de l'AI Act — fait le 21/07/2026 : le Digital Omnibus (adopté juin 2026) reporte le haut risque (Annexe III → 02/12/2027, Annexe I → 02/08/2028) ; le 2 août 2026 reste la date de la majorité des règles (dont transparence art. 50) et du début de l'exécution
- [x] `journal_veille.md` : première entrée rédigée le 21/07/2026 (calendrier AI Act révisé ; décision `évaluer` ; révision programmée à la publication au JO — satisfera l'exigence de révision avant fin M4)

## Phase M1 — Suivi (1 h)

- [ ] Entrée journal : modèles, licences, techniques d'adaptation ou contraintes de calcul

## Phase M2 — Suivi (1 h)

- [ ] Entrée journal : données, conformité, biais ou gouvernance

## Phase M3 — Suivi (1 h)

- [ ] Entrée journal : architectures, intégration multi-source ou dépendances

## Phase M4 — Consolidation (3 h)

- [ ] Réviser au moins une entrée du journal à partir d'une source plus récente ou plus autoritative (expliquer ce qui a changé dans le raisonnement)
- [ ] `ai_act_diagops.md` : analyser les scénarios A (aide au diagnostic) et B (fonction liée à la sécurité) — conclusion conditionnelle
- [ ] `radar_technologique.md` : classer les technologies observées, chaque position justifiée (sources, critères, impacts, recommandation)

## Restitution — fin M4 (2 h)

- [ ] `recommandations_architecture_m4.md` : synthèse exploitable (évolutions, décisions confirmée/révisée, risque réglementaire, choix de modèle, architecture, métriques, journalisation, revue humaine, seuils d'alerte, points juridiques)
- [ ] Préparer la présentation de 10 min (évolution majeure, hypothèse corrigée, qualification des 2 scénarios, décision technique, exigences transmises)

## Garde-fous (critères éliminatoires du brief)

- Aucune affirmation importante sans source.
- Toujours distinguer date de publication / entrée en vigueur / date d'application.
- Jamais une source secondaire seule quand une source officielle existe.
- Qualification juridique toujours conditionnelle (hypothèses + limites).
- Journal alimenté au fil de l'eau — les commits git en font foi.
- Chaque entrée aboutit à un impact concret sur une décision DiagOps.
- Toute source citée est vérifiée avant d'être utilisée.
