# ADR-0007 — Traces : 30 jours appliqués, six mois si haut risque

- Statut : **proposé** (reprend la décision D3 de la veille M7)
- Date / auteur / reviewer : 28/09/2026 / Nicolas (rédaction assistée) / à désigner
- Constat et preuve reproductible : `policy.yaml` déclare `retention_days: 30`,
  mais **aucune purge n'existe** (dette M6). RT-07 : les traces sont minimisées
  (0 champ interdit, 0 fragment de document, 0 secret). Aucun journal d'accès
  n'existe, faute d'authentification.
- Contraintes et hypothèses : hors haut risque, l'AI Act n'impose aucune durée.
  S'il y a haut risque : au moins six mois (art. 19(1) et 26(6), non modifiés
  par l'Omnibus, applicables au 02/12/2027 ou au 02/08/2028). La qualification
  est ouverte (Q1, Q2, Q4).
- Options :
  1. **maintenir** : 30 jours déclarés, non appliqués ;
  2. 30 jours appliqués ;
  3. 190 jours tout de suite, par prudence.
- Mesures séparées des estimations : aucune. Volume des traces non mesuré en
  exploitation.
- Choix : **option 2**, avec un déclencheur écrit. Portée à **190 jours**
  (six mois, marge pour les mois de 31 jours) dès que la qualification haut
  risque est confirmée. Le journal d'approbation de l'outil à effet et les
  journaux d'accès : six mois minimum dès leur création. Le feedback nominatif
  n'est pas une trace : sa durée suit sa propre base légale (Q6).
- Option écartée : 3, parce que garder plus longtemps que nécessaire n'est pas
  neutre au regard du RGPD si un champ personnel entre un jour dans les
  traces. La minimisation actuelle rend le risque faible, pas nul.
- Impacts : un job de purge, à tester (Q5) ; un contrôle qui compare la date de
  la plus vieille trace à la durée déclarée.
- Gate, rollback et condition de révision : gate = une trace de 31 jours
  n'existe plus après la purge, vérifié par un test. Révision à la réponse à
  Q1/Q2/Q4.
- Changement après contradiction indépendante : à remplir.
