# Ressources — Module 7

## Architecture

- [C4 model](https://c4model.com/) ;
- [ADR : exemples et méthode](https://adr.github.io/) ;
- [SQLite : format et documentation](https://www.sqlite.org/docs.html) ;
- [Python sqlite3](https://docs.python.org/3/library/sqlite3.html).

- C4 model — contexte, conteneurs, composants et code ;
- ADR — décisions, alternatives et conséquences ;
- diagrammes de flux de données et frontières de confiance ;
- documentation primaire des fournisseurs retenus.

## Sécurité et risques

- [OWASP GenAI Security Project](https://genai.owasp.org/) ;
- [MITRE ATLAS](https://atlas.mitre.org/) ;
- [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework).

- OWASP Top 10 for LLM Applications ;
- MITRE ATLAS ;
- NIST AI RMF ;
- pratiques de threat modeling et moindre privilège ;
- textes officiels applicables à la protection des données et à l'IA.

## Veille réglementaire

- [RGPD — texte EUR-Lex](https://eur-lex.europa.eu/eli/reg/2016/679/oj) ;
- [AI Act — texte EUR-Lex](https://eur-lex.europa.eu/eli/reg/2024/1689/oj) ;
- [CNIL — intelligence artificielle](https://www.cnil.fr/fr/intelligence-artificielle).

Ces liens sont des points d'entrée : relever la version, la date de consultation,
le calendrier d'application et la section effectivement utilisée. Leur présence
ne constitue pas une vérification juridique actualisée du projet.

- reprendre `../M4/brief3_module4_veille_reglementaire.md` et la dernière entrée
  de `veille_diagops/` ;
- documenter le statut et la date des sources portant sur les rôles,
  fournisseurs, transferts, cybersécurité, supervision et traçabilité ;
- inscrire les conséquences dans les ADR, le registre des risques ou le plan de
  migration.

## Souveraineté et portabilité

- formats exportables des corpus, index et traces ;
- contrats d'API et schémas indépendants du fournisseur ;
- modèles et embeddings alternatifs avec licences documentées ;
- matrices de coût total, localisation et reprise.

## Fiabilité

- objectifs RTO/RPO ;
- circuit breakers, timeouts et budgets ;
- sauvegarde et reconstruction d'index ;
- tests de charge et chaos bornés à l'environnement local.

## À éviter

- comparer des fournisseurs uniquement sur le prix affiché ;
- appeler souverain un système sans documenter données, contrôle et sortie ;
- appliquer les droits après retrieval ;
- tester une attaque sur un service externe ou de production ;
- confondre diagramme cible et preuve de faisabilité.

## Approfondissement de 20 h

- contrat d'export et de reconstruction ;
- journal des opérations manuelles et incompatibilités ;
- grille de revue indépendante avec sévérités ;
- preuve de rollback sur le sous-ensemble migré.
