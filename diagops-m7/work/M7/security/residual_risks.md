# Risques résiduels

Gravités : **bloquant** = fuite, élargissement de droits, action réelle non
autorisée, perte irrécupérable ou absence de rollback ; **majeur** = objectif de
qualité ou de reprise non atteint ; **mineur** = défaut sans effet sur les gates.
« Accepté » est une disposition motivée, pas une gravité. Aucune acceptation
n'est prononcée ici : l'apprenant n'a pas autorité pour accepter un risque au
nom de l'exploitant. Les responsables sont des rôles.

| ID | Constat / preuve | Gravité | Traitement | Responsable | Échéance | Acceptation explicite | Gate bloqué |
|---|---|---|---|---|---|---|---|
| R-01 | Le manifeste est la seule ancre de confiance : une révision empoisonnée avec un checksum juste est servie (RT-03), un document bourré de mots-clés capte 12/12 top 1 (RT-04) | **bloquant** (procédure de sécurité altérée servie comme valide) | revue à deux personnes de tout changement de manifeste, auteur ≠ relecteur, tracée dans Git ; un contrôle « une seule révision active » à l'export (ADR-0003) | responsable documentaire | avant toute mise en service hors formation | non | mise en service ; **pas** la migration d'index, qui ne change pas ce risque |
| R-02 | Le rôle n'est authentifié nulle part : `policy.yaml` ou argument (RT-05, action simulée) | **bloquant** pour tout usage multi-utilisateur | identité fournie par le fournisseur d'identité de l'organisation, rôle dérivé du jeton (ADR-0002) | responsable sécurité | avant ouverture à plus d'un rôle | non | mise en service multi-rôles |
| R-03 | Index partagé : le document restreint modifie scores (10/10) et classement (2/10) d'un technicien | majeur (divulgation indirecte, non exploitée) | index par périmètre de droits (ADR-0001) | exploitation | avec la migration d'index | non | migration vers un index **partagé** |
| R-04 | Réponse « fondée » sur un document sans rapport : 5/5 hors corpus (RT-06), SCN-014 | majeur | abstention explicite quand aucune preuve ne couvre les termes discriminants de la question ; critère à concevoir, un seuil de similarité seul ne suffit pas (M4) | équipe DiagOps | M8 | non | aucun gate de migration ; bloque toute extension du périmètre fonctionnel |
| R-05 | Aucun refus délibéré d'une instruction ou d'une demande d'écriture : SCN-013, ADV-001, RT-01 | majeur | refus avant appel sur intention d'écriture, dans le planificateur (hors M7) | équipe DiagOps | M8 | non | ajout de tout outil à effet, même simulé, dans le chemin de référence |
| R-06 | Planificateur à une étape : SCN-006 échoue | mineur pour le M7 | conservé ; objet du M6, pas du M7 | équipe DiagOps | M8 | non | — |
| R-07 | Conflit fiche/document non exposé : ADV-006, RES-05 | majeur | exposer le conflit dans la réponse ; la donnée structurée fait foi | équipe DiagOps | M8 | non | — |
| R-08 | Détection d'injection par liste de marqueurs : 1/3 (RT-02) | mineur tant qu'aucun composant n'interprète ; **bloquant** dès qu'un LLM est introduit | rejouer la campagne RT-01/RT-02 avant toute introduction d'un générateur (ADR-0005) | équipe DiagOps | à l'introduction d'un LLM | non | introduction d'un générateur |
| R-09 | Timeout et budget constatés après coup : 3008 ms pour 1500 (RES-05), 401 ms pour 100 (RES-04) | majeur si un fournisseur facturé est ajouté | délai qui interrompt (exécution sous échéance) | équipe DiagOps | avant tout fournisseur facturé | non | option cloud |
| R-10 | Un document altéré coupe tout le corpus (RES-06) | majeur | quarantaine au document, alerte, service des autres (ADR-0004) | exploitation | avec la migration d'index | non | — |
| R-11 | Révocation non appliquée en cours d'exécution ; index construit servi avec les droits d'avant (RES-07) | **bloquant** (élargissement de droits effectif après révocation) | empreinte du manifeste dans l'index, contrôlée au chargement ; index périmé non servi ; reconstruction déclenchée par le changement (ADR-0003) | exploitation | **avant** la migration | non | **migration d'index** |
| R-12 | Deux révisions actives servies ensemble, aucune détection (RES-03) | majeur | refus à l'export (ADR-0003) | responsable documentaire | avant la migration | non | migration d'index |
| R-13 | Manifeste sans sauvegarde hors poste | majeur (RPO non tenu en cas de perte du poste) | copie hors poste chiffrée, restauration chronométrée | exploitation | avant mise en service | non | mise en service |
| R-14 | Empreinte de l'export dépendante du système (CRLF / LF) | mineur | écriture LF imposée (corrigé dans `lab.py`), contrat d'export au niveau des octets | nous | fait | — | — |
| R-15 | 3 retours de feedback contiennent un nom et un téléphone | majeur (donnée personnelle dans un jeu d'amélioration) | minimisation avant tout usage (déjà prévue par `qualify_feedback.py`, à vérifier) | responsable qualité | avant réutilisation du feedback | non | réutilisation du feedback |

### Risques réglementaires (veille M7, `veille_diagops/decisions_m7.md`)

| ID | Constat / preuve | Gravité | Traitement | Responsable | Échéance | Acceptation explicite | Gate bloqué |
|---|---|---|---|---|---|---|---|
| R-REG-01 | Connecter l'outil à effet à un système réel requalifie DiagOps (AI Act art. 6(1 ter), D2) | **bloquant** pour toute sortie du bac à sable | contrat `executable: false` vérifié par test ; toute modification déclenche une revue art. 6 (ADR-0006) | compétence juridique + responsable maintenance | avant toute connexion (Q4) | non | sortie du bac à sable |
| R-REG-02 | Distribuer DiagOps à un tiers sans processus de notification CRA (art. 14, applicable depuis le 11/09/2026, D5) | **bloquant** pour une diffusion | revue de conformité CRA avant toute diffusion hors de l'équipe | porteur du dossier de veille | à la première diffusion | non | diffusion à un tiers |
| R-REG-03 | Invalidation du DPF en cours de contrat (pourvoi C-703/25 P, D6) | majeur | région UE exigée, ou base de repli art. 46 prête ; sortie locale rejouée | référent protection des données | à chaque checkpoint (Q8) | non | option cloud |
| R-16 | Purge des traces déclarée (30 jours) et non appliquée (D3) | majeur | job de purge testé (ADR-0007) | architecte | avant toute exploitation hors laboratoire (Q5) | non | mise en service |
| R-17 | Mention d'interaction IA absente depuis le 02/08/2026 (art. 50(1), D8) | majeur | champ `ai_notice` dans le contrat de réponse (ADR-0008) | équipe DiagOps | immédiat | non | mise en service |

## Ce qui bloque quoi

- **La migration d'index** (brief 2) est bloquée par **R-11** et **R-12**. Ce
  sont précisément la révocation et le changement de révision que le brief 2
  impose d'exercer : la migration doit les corriger, pas seulement les
  traverser.
  **Mise à jour du 28/09 (brief 2, phase 1, `531d288`)** : R-11 et R-12 sont
  traités par le candidat (M-REVOC et M-REV-A/B conformes). Leur fermeture
  attend la revue indépendante ; la reconstruction reste manuelle (D-2).
- **La mise en service**, même interne, est bloquée par **R-01**, **R-02**,
  **R-13**, **R-16** et **R-17**. Les trois premiers sont des décisions
  d'organisation, non traitées en M7. Les deux derniers sont peu coûteux et
  planifiés (étapes 5 et 6 du plan de migration).
- **L'option cloud** est bloquée par **R-09**, **R-REG-03** et les préalables
  de l'ADR-0005 (contrat art. 28, clauses du chapitre VI du Data Act, sortie
  rejouée).
- **La sortie du bac à sable de l'outil à effet** est bloquée par **R-REG-01**,
  **R-02** et **R-05**.
