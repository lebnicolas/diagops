# ADR-0008 — Mention d'interaction avec un système d'IA

- Statut : **proposé**, exécution immédiate (reprend la décision D8)
- Date / auteur / reviewer : 28/09/2026 / Nicolas (rédaction assistée) / à désigner
- Constat et preuve reproductible : l'art. 50(1) de l'AI Act s'applique depuis
  le 02/08/2026. Ni l'API ni la réponse de l'agent n'affichent de mention. La
  recommandation A1 du M4 n'a jamais été réalisée.
- Contraintes et hypothèses : il n'est pas tranché que DiagOps soit un
  « système d'IA » (Q1), ni que l'exception « cela ressort clairement »
  s'applique.
- Options : 1. **maintenir** sans mention, en attendant Q1 ; 2. **afficher la
  mention** dans toute réponse et à la première interaction.
- Mesures séparées des estimations : aucune ; coût estimé quasi nul (un champ de
  réponse).
- Choix : **option 2**. Elle couvre l'obligation sans attendre de trancher Q1.
  Attendre une qualification juridique pour afficher une phrase coûte plus cher
  que la phrase.
- Impacts : un champ `ai_notice` dans le contrat de réponse ; mention dans les
  supports de formation des utilisateurs, avec les limites mesurées (art. 4) :
  réponses « fondées » sur des documents sans rapport (R-04), absence de
  refus délibéré (R-05).
- Gate, rollback et condition de révision : gate = test de contrat de réponse.
  Révision si une génération non extractive est introduite : marquage lisible
  par machine (art. 50(2), ADR-0005).
- Changement après contradiction indépendante : à remplir.
