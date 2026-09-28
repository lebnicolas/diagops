# Scénarios de résilience — compléter et geler avant essais

Le banc automatique ne couvre que l'index local. Pour les autres scénarios, implémenter une injection bornée dans le composant réellement présent, ou réaliser une simulation sur table explicitement qualifiée. Ne jamais déclarer un test distant exécuté sur la base d'une discussion.

| ID | Situation | Injection locale / simulation | Impact | Détection | Réponse | Reprise | Preuve/limite |
|---|---|---|---|---|---|---|---|
| RES-01 | index/modèle indisponible | | | | | | |
| RES-02 | fournisseur distant inaccessible | | | | | | |
| RES-03 | corpus obsolète | | | | | | |
| RES-04 | charge/budget épuisé | | | | | | |
| RES-05 | outil lent ou contradictoire | | | | | | |
| RES-06 | document compromis | | | | | | |
| RES-07 | droits absents/révoqués | | | | | | |
| RES-08 | index corrompu/perdu | banc `lab.py` | | hash invalide | refus | retour JSON | rapport à analyser |
