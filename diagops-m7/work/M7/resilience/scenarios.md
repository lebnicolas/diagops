# Scénarios de résilience

Exécutés le 28/09/2026 par `scripts/resilience_run.py`
(`results/resilience-r1/report.json`). Chaque injection porte sur une **copie**
du data pack, supprimée après la campagne. L'agent est celui de la référence
M6, non modifié.

Trois niveaux de preuve, jamais mélangés :

- **injection locale** : panne réellement provoquée sur un composant présent ;
- **proxy local** : panne injectée par le registre M6 pour imiter un composant
  absent. C'est un indice, pas un test du composant ;
- **simulation sur table** : raisonnement écrit, sans exécution.

Point de comparaison : la référence réussit 15 scénarios nominaux sur 18.

| ID | Situation | Injection / simulation | Impact observé | Détection | Réponse | Reprise | Preuve / limite |
|---|---|---|---|---|---|---|---|
| RES-01 | index ou modèle indisponible | **injection locale** : `manifest.csv` supprimé ; index actif du banc supprimé | 14/18 réussis, **11 refus** (6 `erreur_outil`, 5 `preuve_insuffisante`), 7 réponses par les outils structurés. Côté banc : `FileNotFoundError` | `ToolUnavailable` côté agent ; **rien** côté banc, qui lève une exception non prévue au lieu d'un refus | refus explicite côté agent ; plantage côté banc | manifeste restauré, caches vidés : 15/18 en **16 ms** | Aucun modèle génératif dans la référence : « modèle indisponible » n'est **pas testé** |
| RES-02 | fournisseur distant inaccessible | **simulation sur table** + proxy local (`error: unavailable` sur `search_knowledge`) | proxy : même profil que RES-01 (14/18, 11 refus) | proxy : `ToolUnavailable` | refus, les outils structurés continuent | sans objet pour le proxy | La référence n'a **aucun** fournisseur distant. Non testés : latence réseau, quota, réponse tronquée, changement de version côté fournisseur, coupure en cours de réponse. Sur table : sans cache ni repli local, une coupure fournisseur coupe tout ce qui en dépend ; d'où le repli lexical local de la cible (ADR-0005) |
| RES-03 | corpus partiellement obsolète | **injection locale** : révision 2 de `DOC-PUMP-VIB` ajoutée (seuil 3,5 au lieu de 4,5 mm/s), révision 1 laissée `active` | l'agent cite **les deux révisions** ; l'export du banc les accepte ; l'index construit avant la mise à jour sert l'état antérieur | **aucune** | aucune | aucune automatique | Deux seuils contradictoires présentés comme preuves. Correction cible : une seule révision active par chaîne `supersedes`, empreinte du manifeste contrôlée par l'index (ADR-0003) |
| RES-04 | montée en charge, budget épuisé | **injection locale** : 360 exécutions séquentielles, 360 sur 8 fils ; budget ramené à 100 ms, outil ralenti de 400 ms | p50 0,04 ms, p95 0,42 ms (séquentiel) ; 8 fils : 54 ms au total pour 360. Budget : refus `budget_duree_depasse` **après 401 ms** de travail | contrôle entre deux étapes | refus | sans objet | Le débit n'est pas le point faible à cette échelle. Le budget de durée ne coupe rien : il constate. Non testé : coût facturé (aucun appel payant), mémoire sous charge, plusieurs processus |
| RES-05 | outil lent ou incohérent | **injection locale** : délai de 3000 ms (timeout outil 1500 ms), résultat vide ; ADV-006 rejoué | lent : `ToolTimeout` après **3008 ms** ; vide : refus `preuve_insuffisante` ; incohérent : réponse fondée sur la seule fiche, conflit **non exposé** | timeout constaté après coup ; conflit non détecté | refus ; réponse partielle pour le conflit | sans objet | Le timeout déclaré ne borne pas la latence réelle : il faut un délai qui interrompt (exécution dans un fil ou un processus avec échéance). Non testé : données fausses mais bien formées |
| RES-06 | document compromis | **injection locale** : une ligne ajoutée à `DOC-CHILL-TEMP-001`, manifeste inchangé | **toute** la recherche documentaire tombe : 14/18, 6 scénarios documentaires touchés ; export du banc refusé (`checksum source invalide`) | checksum | refus (fermé) | restaurer le fichier ou le manifeste | Fermé, mais à la maille du corpus : un seul document altéré retire les 6 autres. Cible : quarantaine du document fautif, service des autres, alerte (ADR-0004). Le cas « document altéré et manifeste mis à jour » est RT-03 : accepté |
| RES-07 | droits absents ou révoqués | **injection locale** : rôle `technicien` retiré de `DOC-PUMP-VIB-001` | même processus : le document **reste servi** ; index construit avant : **reste servi** ; après rechargement des caches ou reconstruction (15 ms) : retiré | **aucune** | aucune | redémarrage ou reconstruction manuelle | Révocation non effective sans action. Cible : empreinte du manifeste comparée à chaque chargement, index périmé non servi (ADR-0003) |
| RES-08 | index corrompu ou perdu | **exécution réelle du banc** : candidat SQLite corrompu ; puis source de reprise altérée ; puis reconstruction complète | corruption détectée, retour au JSON en 14 ms, classement identique ; source de reprise altérée **refusée** ; reconstruction depuis le manifeste en **12 ms**, export identique octet pour octet | empreinte de l'index actif ; empreinte attendue de la source | refus, puis retour arrière | JSON conservé, ou reconstruction | Le SQLite corrompu reste dans `results/` pour inspection. Non testé : perte simultanée du manifeste et de l'export (aucune sauvegarde hors poste) |

## Ce que ces huit scénarios changent

Deux hypothèses de départ tombent :

- *« Un contrôle d'intégrité fermé suffit »* : il est fermé, mais à une maille
  qui transforme un document altéré en panne totale (RES-06) et ne voit pas
  deux révisions valides qui se contredisent (RES-03).
- *« Les budgets bornent le coût »* : le timeout d'outil et le budget de durée
  sont vérifiés **après** le travail (RES-04, RES-05). Ils décident de la
  réponse, pas de la dépense.

Et une se confirme : le **retour arrière** du banc fonctionne et refuse une
source altérée (RES-08). Reconstruire depuis le manifeste est si rapide sur ce
corpus (12 ms) que l'index n'a pas besoin de sauvegarde : c'est le manifeste
qui en a besoin.
