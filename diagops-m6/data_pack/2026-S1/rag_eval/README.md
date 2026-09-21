# Jeu d’évaluation RAG M4

`questions.jsonl` est gelé pour la révision M4 du data pack.

- Les lignes `calibration` exposent leurs documents attendus et leur étiquette
  `answerable`.
- Les lignes `test` exposent uniquement la question, le rôle et les risques. Les
  labels restent scellés côté formateur jusqu’au gel du pipeline candidat.
- Un `answerable=false` attend une abstention motivée. Il n’autorise pas une
  réponse issue des connaissances générales du modèle.

Le score de test est produit par le formateur. Les apprenants ne modifient ni
ce fichier, ni le corpus documentaire.
