# Essai de portabilité du brief 1

Exécuter `python lab.py --output results/decouverte-r1`. Le banc exporte les documents actifs, leurs révisions, ACL, licences et checksums ; migre le stockage JSON vers SQLite ; compare le classement sur la calibration ; corrompt le candidat ; restaure le pointeur vers JSON.

Le score lexical est conservé : on change réellement le stockage d'index, pas le modèle. Le banc ne mesure ni qualité des réponses générées ni service multi-utilisateur.

## Analyse personnelle attendue
Identifier une perte ou incompatibilité plausible, la provoquer sur une copie, constater l'échec, remédier puis rejouer. Comparer IDs/rangs, droits, provenance, temps, taille et étapes manuelles. Fournir commandes, versions et rapports. Reproduire seulement la démonstration ne valide pas le brief 2.
