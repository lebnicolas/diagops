# Corpus documentaire M4

Ce corpus synthétique sert à comparer les baselines de retrieval et la
génération citée de DiagOps. Les documents ne sont pas des procédures
industrielles réelles.

`manifest.csv` constitue le contrat d’admission. Un index doit vérifier le
checksum, le statut de révision, la sensibilité et les rôles autorisés avant de
rendre un document récupérable. `asset_path` est relatif à `documents/`.

La présence de `DOC-LOTO-001` est volontaire : cette révision remplacée permet
de vérifier qu’un bon score lexical ne suffit pas à rendre une source
admissible. Le document restreint permet de tester les contrôles d’accès ; son
contenu reste entièrement synthétique.
