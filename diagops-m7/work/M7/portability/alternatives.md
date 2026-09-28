# Alternatives local / cloud / hybride

Même besoin pour les trois options : assister le diagnostic d'un technicien à
partir d'un corpus de procédures versionné, avec des droits par rôle, et sans
action sur un système réel.

Chaque valeur porte sa nature : **mesuré** (sur ce poste, avec une preuve),
**relevé** (source datée) ou **estimé** (calcul à partir d'une hypothèse
écrite). Aucune alternative distante n'a été exercée : aucun compte, aucune
clé. La seule alternative exécutée est locale (SQLite FTS5).

## Hypothèse d'usage, écrite avant le calcul

50 techniciens × 20 questions par jour × 22 jours = **22 000 questions par
mois**. Par question avec génération : 1 500 jetons en entrée (consigne,
question, 3 extraits de 240 caractères, métadonnées) et 300 en sortie. Soit
**33 M jetons d'entrée et 6,6 M de sortie par mois**. Le kit ne donne aucun
chiffre d'usage : cette hypothèse est arbitraire, elle sert à donner un ordre
de grandeur, et la conclusion la supporte à un facteur 10 près.

## Sources relevées le 28/09/2026

| Source | Valeur relevée |
|---|---|
| mistral.ai/pricing/api (tarifs publics, USD) | Mistral Small 4 : 0,15 $ / M en entrée, 0,6 $ / M en sortie ; Ministral 3 (3B) : 0,1 $ / 0,1 $ ; Mistral Embed : 0,1 $ / M ; inférence régionale +10 % |
| scaleway.com/en/pricing/model-as-a-service (Paris, HT, EUR) | mistral-small-3.2-24b-instruct-2506 : 0,15 € / M en entrée, 0,35 € / M en sortie ; bge-multilingual-gemma2 : 0,10 € / M |

Les tarifs changent souvent : ces chiffres valent pour la date de relevé.

## Matrice par brique

| Brique | Local | Cloud | Hybride retenu |
|---|---|---|---|
| Génération | aucune dans la référence ; modèle local possible (LM Studio, `ministral-3-3b`, ~5 s par diagnostic mesuré au M0 sur RTX 5060) | API d'un fournisseur (Mistral, Scaleway…) | **aucune en M7** ; si un besoin est démontré : cloud UE avec repli extractif local |
| Embeddings | non utilisés ; les embeddings `nomic` de LM Studio sont cassés sur ce poste | API (0,10 € / M, relevé) | **non retenus** : le lexical sature déjà sur 7 documents (hit@3 = 1,0) |
| Index | JSON, SQLite, FTS5 : **mesurés** | index vectoriel managé | **local**, FTS5 par rôle |
| API applicative | FastAPI en conteneur (déclaré M5) | PaaS | local |
| Traces | fichiers JSON locaux | journalisation managée | local ; rétention selon la veille M7 |
| Sauvegardes | aucune hors poste aujourd'hui (R-13) | stockage objet | **copie chiffrée hors poste**, seule brique cloud retenue sans condition |

## Matrice de synthèse

| Option | Qualité | Latence / capacité | Coût total | Énergie / empreinte | Données / transferts | Dépendances / licence | Sortie / compétences | Preuve ou estimation |
|---|---|---|---|---|---|---|---|---|
| **Local** (référence + FTS5) | retrieval : hit@3 1,0 sur 12 questions, saturé ; aucune génération | **mesuré** : p50 7,6 ms pour 12 requêtes FTS5, agent p50 0,04 ms ; 2000 exécutions en 519 ms | pas de facture ; coût réel = poste, exploitation, compétences (**non chiffré**) | **non mesuré** ; pas de GPU pour le retrieval | aucun transfert | Python, SQLite (domaine public), PyYAML (MIT) | sortie immédiate (fichiers, SQL standard) ; compétence : Python, SQLite | mesures `results/portabilite-fts5-r1`, `resilience-r1` |
| **Cloud** (génération + embeddings via API) | inconnue sur ce corpus : **aucun essai** | dépend du réseau et du fournisseur ; non mesurée | **estimé** : génération Mistral Small 4 ≈ 33 × 0,15 + 6,6 × 0,6 ≈ **8,9 $ / mois** ; Scaleway Mistral Small 3.2 ≈ 33 × 0,15 + 6,6 × 0,35 ≈ **7,3 € HT / mois** ; plus le temps d'intégration, de contrat et de conformité, qui domine (**non chiffré**) | **non mesuré** ; déplacée chez le fournisseur, pas supprimée | questions et extraits de documents **sortent** du poste : RGPD, sous-traitance, localisation (voir veille) | fournisseur, version de modèle imposée, conditions d'usage | réversibilité **contractuelle** ; format des embeddings propre au modèle : changer de modèle = réindexer | tarifs relevés ; aucun appel effectué |
| **Hybride** (local par défaut, génération distante optionnelle) | celle du local, plus une génération à qualifier | locale pour le retrieval ; distante pour la génération | estimé : celui du cloud, limité à la génération | idem | seules les données `public` et `interne` peuvent sortir, jamais `restreint` | idem cloud, sur une seule brique | le repli extractif local reste le mode dégradé ; sortie = couper le fournisseur | raisonnement ; RES-02 simulé sur table |

## Ce que la matrice décide

1. **Le coût d'API n'est pas le critère.** À l'hypothèse d'usage, la génération
   coûte moins de 10 $ par mois. Même multiplié par dix, le coût est dominé
   par l'intégration, le contrat, la conformité et l'exploitation, qu'aucune
   facture n'affiche. Comparer les fournisseurs sur le prix affiché est
   l'erreur que `RESOURCES.md` signale.
2. **Rien ne justifie aujourd'hui une brique distante pour le retrieval.** Le
   lexical local sature la calibration. Les embeddings ajouteraient une
   dépendance (le format d'un index vectoriel est propre au modèle) sans gain
   mesurable sur 7 documents.
3. **La génération est une décision à part**, prise en M8 sur un besoin
   démontré. Elle arrive avec trois préalables : campagne RT-01/RT-02 rejouée
   (R-08), délai qui interrompt (R-09), clause de réversibilité et de
   localisation (veille M7).
4. **La seule brique distante retenue sans condition est la sauvegarde chiffrée
   du manifeste.** Elle ne transporte aucune donnée en clair et répond à R-13.
