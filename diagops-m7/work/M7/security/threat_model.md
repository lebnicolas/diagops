# Modèle de menaces

Méthode : pour chaque frontière de `architecture/current.md`, un acteur, ce
qu'il peut réellement faire, la menace, le contrôle **observé** et sa preuve.
Référentiels de nommage : OWASP Top 10 for LLM Applications 2025 (LLM01
injection, LLM02 divulgation, LLM04 empoisonnement, LLM06 agence excessive,
LLM08 faiblesses des vecteurs et embeddings, LLM10 consommation non bornée) et
MITRE ATLAS pour l'empoisonnement. Ces codes servent de vocabulaire commun ;
aucune conformité n'est revendiquée.

Tous les tests portent sur des copies locales synthétiques. **Un contenu
malveillant qui reste une donnée dans le banc déterministe ne prouve pas la
résistance d'un LLM à l'injection** : la référence n'interprète rien.

| Actif / frontière | Acteur et capacité | Menace | Impact C2 / C7 | Contrôle observé | Test / preuve | Limite |
|---|---|---|---|---|---|---|
| Question → agent (F1) | utilisateur légitime ou non, texte libre | injection directe (LLM01), demande d'outil d'écriture | C2 : réponse hors périmètre ; C7 : refus non conçu | rôle fixé par la politique, liste blanche, aucun outil d'écriture | RT-01 : permissions inchangées 6/6, **0 refus délibéré** ; SCN-013, ADV-001 | l'invariant tient parce qu'il n'y a **rien** à détourner ; un LLM avec outils à effet change la donne |
| Corpus → classement (F4) | rédacteur de document, ou quiconque écrit dans le dépôt | injection indirecte (LLM01) | C2 : consigne cachée présentée comme preuve | contenu traité comme donnée ; détection par liste de marqueurs | RT-02 : capacités inchangées 3/3, **1/3 repérée**, 3/3 citées | la liste de marqueurs est contournée par une reformulation ou une autre langue |
| Manifeste (F4) | rédacteur, compte compromis | empoisonnement de révision (LLM04, ATLAS « Poison Training Data » transposé au corpus) | C2 : procédure de sécurité altérée servie comme valide | checksum par document | RT-03 : révision 3 sans vérification d'absence d'énergie **servie** | le checksum prouve l'intégrité du fichier, pas la légitimité de son auteur |
| Corpus → classement (F9) | rédacteur, compte compromis | document prioritaire (bourrage de mots-clés) | C2 : un document capte toutes les réponses | aucun | RT-04 : **12/12** top 1 en lexical **et** en BM25 ; l'agent le cite 4/12 | l'hypothèse « BM25 normalise la longueur, donc résiste » est fausse |
| Identité → retrieval (F1, F3) | utilisateur d'un autre périmètre | fuite de document (LLM02) | C2 : divulgation d'un document restreint | filtre de rôle avant score | RT-05 : **0 renvoi** sur 11 sondes × 2 rôles × 4 backends ; outils structurés refusés à `public` | le rôle n'est **authentifié nulle part** |
| Index partagé (F9) | utilisateur d'un rôle limité, observant les classements | canal auxiliaire par statistiques (LLM08) | C2 : le contenu restreint influence ce que voit un technicien | aucun dans un index partagé | portabilité : scores visibles modifiés **10/10**, classement **2/10** ; index par rôle : 0 | exploitation réelle non démontrée : il faudrait de nombreuses requêtes et l'accès aux scores |
| Outil → réponse (F2, F3) | source structurée compromise | donnée contradictoire ou champ empoisonné | C2 : conclusion sur une donnée fausse | marqueur d'instruction tracé | RT-06 : champ empoisonné repéré, réponse **produite quand même** ; ADV-006 conflit non exposé | aucune vérification croisée entre sources |
| Preuve → réponse | utilisateur | réponse « fondée » sur une preuve non pertinente | C2 : fausse assurance | `require_evidence` (existence d'une preuve) | RT-06 : **5/5** questions hors corpus répondues | c'est la faille la plus probable en exploitation, sans aucun attaquant |
| Sorties et traces (F6, F7) | auditeur, tiers ayant accès aux journaux | extraction (LLM02) | C2 : texte de document ou donnée personnelle dans une trace | champs interdits, empreinte des arguments | RT-07 : 0 champ interdit, 0 fragment de document sur 71 testés, 0 secret sur 159 fichiers | un technicien peut reconstituer un document interne par requêtes successives ; son rôle l'y autorise |
| Boucle d'agent | planificateur défaillant ou manipulé | boucle coûteuse (LLM10) | C7 : coût et latence | appel répété interdit, plafond dur de 8 étapes | RT-08 : arrêt au 1er ou au 3e appel ; politique à 50 étapes refusée | le budget de durée ne coupe pas un outil en cours (RES-04, RES-05) |
| Processus agent | utilisateur, rafale | déni de service (LLM10) | C7 : indisponibilité | validation de longueur (200 car.) | RT-09 : question longue **refusée** comme erreur d'outil ; 2000 exécutions en 519 ms | le vrai déni de service est ailleurs : **un document altéré coupe tout le corpus** (RES-06) |
| Arguments d'outils (F2) | question forgée | argument manipulé (chemin, SQL, limite, champ inconnu) | C2 : lecture hors ressource | validation stricte par contrat | RT-10 : **5/5 refusés** ; second identifiant ignoré sans le dire | défaut de réponse, pas de sécurité |
| Outil à effet simulé | demandeur, approbateur | action sans approbation, rejeu, changement après accord (LLM06) | C2 : effet non autorisé | contrat non exécutable, approbation liée au hash, TTL, idempotence | exercice sur table : 5 séquences conformes, `tests/test_simulated_action.py` | acteurs et rôles fictifs **passés en argument** : même faiblesse d'identité que F1 |

## Ce que le modèle de menaces décide

1. **Deux contrôles manquent, et aucun n'est algorithmique** : une revue à deux
   personnes des changements de manifeste (RT-03, RT-04) et une identité
   authentifiée (RT-05). Aucun réglage de classement ne remplace l'un ou
   l'autre.
2. **La faille la plus probable n'a pas besoin d'attaquant** : une réponse
   « fondée » sur un document sans rapport (RT-06, SCN-014). Un seuil de
   pertinence ou une abstention explicite fait partie de la cible. Le M4 a
   déjà montré qu'un seuil de similarité ne suffit pas à décider l'abstention
   (0,007 d'écart) : la décision reste ouverte pour M8.
3. **Un index partagé filtré par rôle n'isole pas les statistiques.** La cible
   retient un index par périmètre de droits (ADR-0001).
