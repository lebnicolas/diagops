# Remédiation

> Registre ouvert le **07/09/2026**. Les entrées « ouvertes » attendent le game day : implémenter
> un correctif avant d'avoir éprouvé le défaut serait de la conception à l'aveugle.

| Action | Hypothèse | Responsable | Échéance | Test de non-régression | Statut |
|---|---|---|---|---|---|
| Archiver l'index avant publication | Sans point de retour, une corruption est irrécupérable | Exploitation | fait le 07/09 | `test_la_promotion_archive_avant_de_publier` | **fait** |
| Archiver la version remplacée **au rollback** | Un rollback pris à tort est sinon irréversible, et le post-incident perd la pièce à conviction | Exploitation | fait le 07/09 | `test_le_rollback_archive_la_version_qu_il_remplace` | **fait** |
| Comparer `build_version` à la readiness | Un index d'une autre stratégie se déclarait `ready` en rendant zéro résultat | Exploitation | fait le 07/09 | `test_un_index_construit_par_une_autre_strategie_bloque_la_readiness` | **fait** |
| Requalifier `citations{resolvable="false"}` | Branche inatteignable : alerte décorative | Qualité | fait le 07/09 | — *(invariant, pas alerte)* | **fait** |
| Alerter sur `diagops_index_valid`, pas sur l'état du conteneur | Docker détecte 17× plus tard que l'application | Exploitation | fait le 07/09 | — *(inscrit au contrat de métriques)* | **fait** |
| Réduire `retries` du healthcheck de 5 à 2 | Bascule `unhealthy` en ~20 s au lieu de ~50 s | Exploitation | à arbitrer | — | **ouvert** — appliqué sur le service de scoring, pas sur le RAG : gain ~30 s contre sensibilité aux faux positifs |
| Revue humaine obligatoire sur tout document modifié | Le gate ne voit pas un changement de **sens** du corpus | Corpus | à instruire | — | **ouvert** — voir `livraison_candidate.md` |
| Vérification périodique d'intégrité hors chemin de requête | Sans trafic, une corruption dort jusqu'au prochain healthcheck | Exploitation | à instruire | — | **ouvert** |
| Exposer les versions en labels de métriques | Une alerte ne porte pas la version concernée | Exploitation | non retenu | — | **écarté** — cardinalité : une série nouvelle à chaque réindexation. Le runbook prescrit d'appeler `/version` à la première minute |
| Alerte sur un taux d'abstention anormal | L'incident du 07/09 était invisible côté client : HTTP 200 + abstention systématique | Qualité | à éprouver | — | **ouvert** — le seuil figure au contrat de métriques, jamais déclenché en exercice |
| Trancher quel emplacement d'artefacts fait foi | `work/M5/artifacts/` en local contre le volume `deploy_diagops_artifacts` en conteneur : l'historique construit sur le poste n'existait pas dans la stack | Exploitation | avant le game day | — | **ouvert** — a failli rendre la répétition irrécupérable |
| Élucider le plafond de débit à 4 workers | c=1 tombe de 172 à 20,9 req/s, p50 fixe à 48 ms | Exploitation | à instruire | — | **ouvert** — à rejouer sur hôte Linux avec un vrai proxy |
