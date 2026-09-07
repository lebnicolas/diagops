# Chronologie du game day

> **Répétition à blanc du 07/09/2026.** Scénario tiré au sort par `game_day/injecteur.py` parmi
> six, dont un témoin sans incident, et scellé jusqu'au rendu du diagnostic. Ce n'est pas le game
> day contradictoire du brief : voir `post_incident.md`, section « ce que cet exercice ne prouve
> pas ».

| Horodatage UTC | Observation | Signal | Décision | Responsable | Preuve |
|---|---|---|---|---|---|
| 09:47 | Préparation — constat de l'état sain | `ready`, `lexical-dfb8faf0c9b4`, api et prometheus `healthy` | Créer le point de retour avant d'injecter | Exploitation | `docker compose ps`, `/health/ready` |
| 09:47 | **`/artifacts/history` est vide dans le volume** | `ls /artifacts/history` → rien | **Ne pas injecter** : l'historique construit plus tôt était sur le poste, pas dans la stack | Pilote | sortie du conteneur jetable |
| 09:48 | Point de retour créé | `promote_index.py` → `index-lexical-dfb8faf0c9b4.json` archivé ; sauvegarde `backup/artifacts-avant-repetition.tgz` (6 980 o) ; image taguée `diagops-rag:avant-repetition` | Injection autorisée | Exploitation | archive + tgz + tag |
| **09:48:42** | **T0 — injection** | scénario tiré au sort et scellé | — | Injecteur | `game_day/_scelle.json` |
| **09:48:49** | **T+7 s — détection** | `/health/ready` → **503 « index actif sans postings exploitables »** ; `diagops_index_valid = 0` | Qualifier avant de décider | Diagnostic | HTTP 503, métrique |
| 09:49:02 | Qualification | `diagops_index_documents = 7` · `dependency_up = 1` · readiness en 10 ms · `index_version` et `build_version` **corrects** · postings du 1ᵉʳ document : **0** | Écarte 4 des 5 scénarios de panne : ni amputation, ni dépendance, ni lenteur, ni index périmé | Diagnostic | `/version`, inspection du volume |
| 09:49:02 | Effet utilisateur mesuré | `POST /search` → **HTTP 200**, `abstained: true`, 0 citation | L'incident est **invisible côté client** : ni erreur, ni lenteur | Diagnostic | réponse de l'API |
| **09:49:15** | **T+33 s — décision** | diagnostic : `index_corrompu` | Rollback vers `lexical-dfb8faf0c9b4` | Pilote | ce journal |
| 09:49:15 | Versions listées **avant** de choisir | `rollback_index.py --list` → 1 version disponible | Cible confirmée | Exploitation | sortie du script |
| **09:49:18** | **T+36 s — restauration** | `Index restaure : lexical-dfb8faf0c9b4 -> lexical-dfb8faf0c9b4` | — | Exploitation | sortie du script |
| 09:49:24 | Vérification, les 4 contrôles du plan | 1. `ready` sur `lexical-dfb8faf0c9b4` · 2. **3 citations**, `abstained: false` · 3. `diagops_index_valid 1` · 4. api et prometheus `healthy` | Incident clos | Pilote | sorties ci-dessus |
| 09:49:30 | Diagnostic rendu, **puis** scellé ouvert | annoncé `index_corrompu` — scellé : `index_corrompu` | **Diagnostic exact** | Pilote | `injecteur.py --reveler` |
