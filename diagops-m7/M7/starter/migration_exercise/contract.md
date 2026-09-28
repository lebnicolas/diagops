# Contrat de migration — à geler avant mesure du brief 2

- Version/hash source, candidat et données :
- Un composant et un risque ciblés :
- Sous-ensemble justifié, cas propres distincts du smoke test :
- Format d'export, types, révisions, ACL, licences, checksums, pertes tolérées :
- Seuil qualité et protocole (calibration distincte du lot de validation) :
- RTO/RPO, budget temps/espace/coût, preuve attendue :
- Gates de sécurité non négociables : aucune fuite/permission élargie/action réelle.
- Plan de migration, opérations manuelles, rollback :
- Identité du reviewer et protocole de reproduction :

Choix minimal sans téléchargement : prolonger JSON→SQLite avec révocation de droits, changement de révision et reconstruction, sur des cas écrits puis gelés AVANT l'essai. Un autre index, embedding ou modèle est possible si ses ressources sont disponibles. Ne pas lire ni ajuster sur les oracles formateur.
