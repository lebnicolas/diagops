# Plan de migration et de retour arrière

Chaque étape est réversible seule, et a son critère d'acceptation. Aucune étape
ne dépend d'un fournisseur distant. Les étapes 1 à 4 sont exercées au brief 2
sur un sous-ensemble ; les étapes 5 à 8 sont des décisions d'organisation,
hors laboratoire.

| # | Étape | Critère d'acceptation | Retour arrière | Opérations manuelles | Risque fermé |
|---|---|---|---|---|---|
| 0 | Geler le contrat de migration, les cas et les seuils **avant** toute mesure | contrat commité avant le premier essai | — | 1 (écriture) | — |
| 1 | Contrôles d'admission à l'export : une seule révision active par chaîne, ancienne révision `superseded` dans le même changement, écriture LF | cas « deux révisions actives » refusé ; export identique octet pour octet d'un système à l'autre | revenir à l'export du starter (les contrôles sont additifs) | 0 | R-12, R-14 |
| 2 | Index FTS5 par rôle, avec `manifest_sha256` dans `metadata`, construit hors du chemin actif | gates de `target.md` : 0 fuite, statistiques isolées, métadonnées conservées, écart de qualité sous le seuil gelé | `active.json` repointé vers le JSON conservé, par empreinte | 0 | — |
| 3 | Contrôle de fraîcheur au chargement : un index dont l'empreinte de manifeste diffère est refusé, puis reconstruit | cas « révocation » : refus, reconstruction, document retiré ; cas « nouvelle révision » : révision unique servie | désactiver le contrôle, ce qui rouvre R-11 : **interdit** sans décision écrite | 0 | R-11 |
| 4 | Quarantaine au document | cas « document altéré » : ce document seul exclu, les autres servis, alerte tracée | refus global (état actuel) | 0 | R-10 |
| 5 | Purge des traces à 30 jours, journal d'accès | test de purge ; journal d'accès présent | aucun, la purge est irréversible par nature : tester sur copie | 1 (planification) | veille D3 |
| 6 | Mention d'interaction IA dans le contrat de réponse | test de contrat | retrait du champ | 0 | veille D8 |
| 7 | Sauvegarde chiffrée du manifeste hors poste, restauration chronométrée | restauration sous 4 h, empreinte identique | — | 2 (clé, planification) | R-13 |
| 8 | Identité OIDC, rôle dérivé du jeton | 401 sans jeton ; 0 fuite avec un jeton `public` | retour mono-rôle | plusieurs (dépend de l'organisation) | R-02 |

## Rollback, règle générale

Un retour arrière restaure un index **par son empreinte attendue** (exercé en
RES-08 : une source altérée est refusée). Une exception : un index antérieur à
une **révocation** n'est jamais restauré, car le retour arrière rétablirait un
droit retiré. Dans ce cas, le mode dégradé (outils structurés seuls) est
préférable à un index périmé.

## Ordre et parallélisme

Les étapes 1 à 4 forment un seul lot, exercé au brief 2. Les étapes 5 à 7 sont
indépendantes et peuvent commencer tout de suite. L'étape 8 conditionne toute
mise en service multi-rôles. Aucune étape n'ouvre la génération ni l'outil à
effet (ADR-0005, ADR-0006).
