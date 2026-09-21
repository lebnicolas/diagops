# Décision de transmission M3 vers M4

Statut : `utilisable sous conditions`.

Le lot capteur peut servir à comparer une baseline de règles et des modèles
simples sur la cible pédagogique de provenance. Les fenêtres sont groupées par
`window_id` et toute partition doit préserver ces groupes.

Conditions conservées :

- les mesures réelles peuvent contenir des anomalies de qualité ;
- les mesures fabriquées ne prouvent rien sur une panne future ;
- les conclusions restent limitées au parc synthétique et à la procédure de
  génération documentée côté formateur ;
- le test reste scellé jusqu’au gel du candidat ;
- une décision de maintien de la baseline ou de non-déploiement est recevable.

Le corpus documentaire M4 constitue une source distincte. Les tables capteurs,
événements et historiques ne sont pas transformées en documents RAG.
