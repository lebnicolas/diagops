# Référence M6 pour M7 — diagops-m6-reference-r1

Cette référence gèle le starter M6 réellement distribué et ses campagnes. Elle n'est ni un corrigé M6 ni une preuve de réalisation par les apprenants. Le code reste dans M6/starter ; release_manifest.json en fixe les hashes, ainsi que ceux des données utilisées. Aucun modèle ni fournisseur distant n'est invoqué.

## Résultats et risques connus

- nominal : échecs SCN-006, SCN-013, SCN-014.
- adversarial : échecs ADV-001, ADV-006.

Le planificateur reste à une étape. Les cas multi-étapes, l'instruction directe et le filtrage du rôle avant appel présentent des limites. Lire les résultats cas par cas. Aucune promotion globale n'est autorisée par cette référence ; M7 doit conserver, traiter ou bloquer ces risques explicitement. Le banc JSON/SQLite porte uniquement sur le retrieval documentaire.

## Reproduction

Depuis S04, avec les dépendances M6 : `python tools/check_m7_release.py`. Le contrôle rejoue les deux campagnes et compare résultats et traces hors durées, sans toucher aux travaux apprenants. Les durées locales ne sont pas des garanties.

## Handoff réglementaire et opérationnel

Reprendre les politiques et runbooks de m5_for_m6, la politique agent/policy.yaml, le registre docs/registre_outils.md et les invariants adversarial/invariants.md de M6. Aucune veille M6 ni revue indépendante n'est inventée pour cette référence. Compléter en M7 les décisions, sources officielles datées, propriétaires, RTO/RPO et risques résiduels dans les gabarits ; joindre son propre handoff M6 s'il existe.
