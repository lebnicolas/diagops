# M7 — Guide de diffusion et d'évaluation

## Kit et prérequis

Python 3.11 ou plus, Git, terminal et espace local pour un petit index. Le starter M7 n'a aucune dépendance pip, aucun compte cloud, image, GPU ou clé d'API requis. Pour rejouer l'agent M6 et les contrôles formateur, utiliser les versions de `M6/starter/requirements.lock` (pytest et PyYAML).

Référence commune : `diagops-m6-reference-r1`, fournie pour l'audit, avec limites connues. Les apprenants ayant terminé M6 peuvent utiliser leur version, à condition d'en figer hashes, politique, scénarios, métriques, traces et décision. Ne pas mélanger les deux états dans une comparaison. « Prêt à distribuer » qualifie le matériel, pas les acquis ni la date de réalisation du module.

## Distribution

1. Vérifier les fichiers et la référence : `python tools/check_m7_release.py --trainer` puis `python tools/check_publication.py` depuis la racine S04.
2. Distribuer les trois briefs, synthèse, ressources, grille ci-dessous et starter ; conserver `_conception/` local au formateur. Aucun corrigé/oracle n'est ajouté au kit M7.
3. L'apprenant initialise `python tools/init_module.py M7`, puis suit `work/M7/README.md`. Un dossier existant n'est jamais écrasé.
4. Le brief 2 peut être lu à l'avance mais commence après le dossier du brief 1. Le reviewer doit être une autre personne ; à défaut, organiser une revue avec le formateur.
5. La publication Git/Simplonline est une action opérateur distincte ; ce contrôle ne publie rien.

## Séquençage proposé, sans dépassement des 40 h

| Séquence présentielle | Heures | Preuve |
|---|---:|---|
| Prise en main et architecture réelle M6 | 2 | replay, diagramme, limites |
| Frontières, politique données et red team | 3 | matrice droits/menaces et tests |
| Résilience et modes dégradés | 2 | injections/simulations qualifiées |
| Alternatives et essai de portabilité | 3 | comparaison et rapport local |
| Outil fictif, cible et ADR | 2 | contrat, exercice sur table et décision |
| Veille réglementaire | 1 | source datée et impact |
| Revue de préparation du brief 2 | 1 | contrat de migration et gates |

Online : 3 h de classe virtuelle + 3 h de dossier autonome. Approfondissement : 12 h réalisation, 4 h reproduction/revue indépendante, 4 h remédiation et défense. Ne pas ajouter un service distribué ou une modalité image pour remplir le volume.

## Grille de notation commune

Chaque brief est noté sur 100 : C2 risques/droits/supervision 25 ; C7 architecture/migration ou plan d'évolution online 30 ; red team/modes dégradés (analyse de scénarios pour l'online) 20 ; souveraineté/réversibilité 15 ; documentation/restitution 10.

Pour chaque dimension : 0 % si absente ; 25 % si déclarative ; 50 % si partielle avec preuve limitée ; 75 % si vérifiable avec limites ; 100 % si complète, reproductible dans le périmètre et défendue. Note module = 0,35 × brief 1 + 0,30 × online + 0,35 × brief 2. Les poids par dimension ne s'ajoutent pas aux poids par brief. Il s'agit de l'évaluation pédagogique, pas du verdict officiel CISIA.

## Gates et preuves minimales

- Brief 1 : diagramme réel, politique de données, huit scénarios de résilience qualifiés, campagne de menaces, alternative locale exécutée, cible/ADR, exercice sur table et veille.
- Online : procédure explicite, cycle de vie, grille, impacts, alternative, cible et restitution ; aucune migration RAG imposée.
- Brief 2 : sous-ensemble/version gelés, cas personnels distincts de la démonstration, export/import, avant/après, panne et rollback, avis signé du reviewer, remédiation et défense.
- Une fuite, permission élargie, action réelle non autorisée ou absence de reprise bloque la cible, quelle que soit la note. Le refus argumenté de migrer peut valider la démarche si la preuve et la revue sont complètes ; il ne valide pas le déploiement de la cible.
- Les tests fournis et les rapports du kit n'attestent ni de la sécurité générale d'un LLM ni d'une revue indépendante des livrables futurs.

## Passage vers M8

Remettre `handoff_m8.md` complété et les preuves exactes. M8 reste un nouveau projet à préparer séparément ; sa référence commune n'est pas créée par la diffusion M7.
