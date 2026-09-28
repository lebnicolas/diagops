# Politique des données et des accès

Portée : les actifs de `diagops-m6-reference-r1` et du banc M7, tous
synthétiques. Les propriétaires sont des **rôles** : le kit ne nomme personne,
et ce document ne le fait pas à sa place. Les durées marquées « proposé » ne
sont pas encore décidées. La rétention des traces dépend de la veille M7
(`veille_diagops/decisions_m7.md`).

## Registre

| Actif | Propriétaire / finalité | Sensibilité | Rôles autorisés | Localisation / transfert | Rétention / suppression | Sauvegarde / RPO | Preuve |
|---|---|---|---|---|---|---|---|
| Procédures actives (`knowledge/documents`, 6 docs `interne`) | responsable documentaire / fonder une réponse | interne | technicien, superviseur, auditeur | poste local, data pack en lecture seule ; aucun transfert | jusqu'au remplacement par une révision ; la révision remplacée est conservée hors service | source versionnée dans Git ; RPO = dernier commit | `lab.py` exporte 7 actifs sur 8 |
| Politique d'accès (`DOC-DATA-ACCESS-001`) | responsable sécurité / règle d'accès | **restreint** | superviseur, auditeur | idem | idem | idem | RT-05 : 0 renvoi sur 11 sondes × 2 rôles × 4 backends |
| Contrat de réponse (`DOC-RAG-OPS-001`) | responsable documentaire | public | tous | idem | idem | idem | — |
| Révision remplacée (`DOC-LOTO-001`) | responsable documentaire / preuve historique | interne | **aucun au retrieval** | conservée dans le data pack | conservée pour audit, jamais servie | idem | export : `status != active` refusé |
| Manifeste du corpus | responsable documentaire / contrat d'admission | interne, **intégrité critique** | écriture : responsable documentaire seul (cible) | idem | versionné | idem | RT-03 : c'est l'ancre de confiance, et elle n'est pas protégée |
| Index dérivés (JSON, SQLite, FTS5) | exploitation / servir le retrieval | celle du document le plus sensible qu'ils contiennent | ceux du document, **au moment de la construction** | poste ou volume Docker (déclaré) | supprimés à chaque reconstruction ; jamais source de vérité | **pas de sauvegarde** : reconstruits depuis le manifeste (12 ms, RES-08) | RES-07 : un index construit garde les droits d'avant |
| Tables structurées (parc, événements, interventions) | exploitation maintenance / contexte de diagnostic | interne | technicien, superviseur, auditeur (`public` refusé) | data pack | durée de vie de l'équipement (proposé) | source ; RPO = dernière livraison | RT-05 : `AuthorizationError` pour `public` |
| Rapports de terrain (`technician_note`) | exploitation / entrée du diagnostic | interne, **texte libre non fiable** | technicien, superviseur, auditeur | data pack | 24 mois (proposé) | source | SCN-006 |
| Questions utilisateur | utilisateur / requête | variable : peut contenir n'importe quoi | aucun stockage en clair | mémoire du processus | **non conservées** : seule l'empreinte l'est | — | RT-07 : aucun texte dans 24 traces |
| Traces d'exécution | exploitation / audit, diagnostic | interne | auditeur, exploitation | fichiers JSON locaux | **30 jours** dans `policy.yaml` ; à réviser selon la veille M7 | aucune (déclaré) | RT-07 : 0 champ interdit |
| Feedback (`feedback.csv`) | responsable qualité / amélioration | **personnelle indirecte** : `submitted_by_id` pseudonyme, commentaire libre | superviseur, auditeur ; jamais réinjecté sans qualification | data pack | 12 mois après qualification (proposé) ; suppression sur demande | source | 3 commentaires sur 124 contiennent un nom et un numéro de téléphone (FBK-2027S1-0070, 0072, 0073 ; synthétiques) : la minimisation doit précéder tout usage |
| Traces de l'action simulée | superviseur fictif / audit de l'exercice | interne | superviseur, auditeur | `results/action-simulee-*` | durée de l'exercice | — | `tests/test_simulated_action.py` |

## Règles d'accès

1. **Le filtre précède le classement, et aussi les statistiques du
   classement.** Un document interdit n'entre ni dans les résultats, ni dans le
   calcul des scores. Conséquence mesurée : un index FTS5 **par rôle** (ou par
   périmètre), pas un index partagé filtré après coup
   (`results/portabilite-fts5-r1` : 10/10 scores et 2/10 classements modifiés
   dans l'index partagé, 0 dans l'index par rôle).
2. **Les droits d'un index dérivé sont ceux de sa construction.** Toute
   modification de `allowed_roles`, de `status` ou de `sensitivity` dans le
   manifeste déclenche une reconstruction et une promotion atomique. En
   attendant, l'index est considéré comme **périmé** et n'est plus servi. Cela
   exige un contrôle de fraîcheur : empreinte du manifeste enregistrée dans
   l'index, comparée à chaque démarrage et à chaque chargement (ADR-0003).
3. **Une seule révision active par procédure.** Si un document en remplace un
   autre et que les deux sont `active`, l'export est refusé (règle absente
   aujourd'hui, RES-03).
4. **Une modification du manifeste passe par une revue à deux personnes**,
   tracée dans Git (auteur ≠ relecteur). C'est le seul contrôle qui aurait
   arrêté RT-03. Signer le manifeste ne suffit pas si le signataire est
   l'attaquant.
5. **Le rôle vient d'une identité authentifiée**, jamais du texte de la
   question ni d'un argument libre. Aujourd'hui, il vient de `policy.yaml`. En
   cible, il vient d'un jeton émis par le fournisseur d'identité de
   l'organisation (ADR-0002). Hors de ce cas, un rôle déclaré est une
   hypothèse de test, pas un contrôle.
6. **Aucune donnée d'un rôle n'est envoyée à un fournisseur distant** sans ADR
   (ADR-0005). En cas d'option cloud, seules les données `public` et `interne`
   peuvent sortir, et jamais un document `restreint`.

## Révocation et document obsolète

| Événement | Effet attendu | Délai cible | Délai observé aujourd'hui |
|---|---|---|---|
| Rôle retiré d'un document | le document n'est plus renvoyé pour ce rôle | ≤ 15 min (proposé) | **jusqu'au redémarrage** du processus ; indéfini pour un index déjà construit (RES-07) |
| Révision remplacée | seule la nouvelle révision est servie | à la promotion de l'index | deux révisions servies si l'ancienne n'est pas passée en `superseded` (RES-03) |
| Document compromis | ce document est retiré, les autres restent servis | immédiat | **tout le corpus** devient indisponible (RES-06) |

## Ce qui reste à concevoir, hors du périmètre testable ici

Chiffrement du disque et des sauvegardes, isolation du processus (utilisateur
système dédié, comme le UID 65532 déclaré dans le Dockerfile), gestion des
secrets le jour où un fournisseur distant existe, identité utilisateur. Rien de
cela n'est testé en M7 : ce sont des exigences de la cible, pas des preuves.
