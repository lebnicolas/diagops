# ADR-0005 — Pas de génération en M7 ; option cloud hybride conditionnelle

- Statut : **proposé** ; la génération reste une décision M8
- Date / auteur / reviewer : 28/09/2026 / Nicolas (rédaction assistée) / à désigner
- Constat et preuve reproductible :
  - la référence est extractive, sans modèle ; le retrieval local sature la
    calibration (hit@3 = 1,0) ;
  - tarifs relevés le 28/09/2026 : à l'hypothèse de 22 000 questions par mois,
    une génération distante coûte moins de 10 $ par mois
    (`portability/alternatives.md`). Le coût d'API n'est pas le critère ;
  - la campagne RT-01/RT-02 tient **parce qu'aucun composant n'interprète**. La
    liste de marqueurs ne repère qu'une injection sur trois (R-08) ;
  - les budgets sont constatés après coup (R-09) : un fournisseur facturé
    lent ou bavard n'est pas borné.
- Contraintes et hypothèses (veille M7, `veille_diagops/decisions_m7.md`) :
  - D1 : l'option cloud ne transfère aucune obligation ; l'équipe reste
    fournisseur du système et devient « fournisseur en aval » du modèle ;
    documentation de l'annexe XII exigée avant le premier appel. La version
    sans modèle appris n'est peut-être pas un « système d'IA » (Q1) : **c'est
    l'introduction d'un LLM qui ferait entrer DiagOps dans le champ de l'AI
    Act** ;
  - D6 : contrat art. 28(3) RGPD, aucune réutilisation par le fournisseur,
    traitement dans l'UE de préférence, base de repli si le DPF tombe
    (pourvoi C-703/25 P pendant), feedback libre jamais envoyé ;
  - D7 : clauses du chapitre VI du Data Act exigées, mais elles ne couvrent ni
    un pilote (art. 31(2)) ni les artefacts propres au fournisseur (art. 2
    point 38). La réversibilité se prouve par la technique ;
  - D8 : une génération non extractive impose le marquage des sorties
    (art. 50(2)), sans délai de grâce.
- Options :
  1. **maintenir** : extractif local, sans modèle ;
  2. modèle local (LM Studio, `ministral-3-3b`, ~5 s par diagnostic mesuré au
     M0) ;
  3. API cloud UE (Mistral, Scaleway Paris) ;
  4. **hybride** : retrieval et repli extractif locaux, génération distante
     optionnelle, coupable sans perte de service.
- Mesures séparées des estimations : coût **estimé** ; qualité, latence et
  énergie de 2, 3 et 4 **non mesurées**.
- Choix : **option 1 en M7**. **Option 4** comme cible si un besoin de
  génération est démontré en M8, sous six préalables :
  1. campagne RT-01/RT-02 rejouée avec le générateur, et bloquante (R-08) ;
  2. délai qui **interrompt** l'appel distant (R-09) ;
  3. seules les données `public` et `interne` sortent, jamais `restreint` ;
     le filtre s'applique avant l'envoi ;
  4. contrat : art. 28(3) RGPD, région UE, clauses du chapitre VI, frais de
     changement nuls après le 12/01/2027 (D6, D7) ;
  5. sortie rejouée : couper le fournisseur et revenir au repli extractif,
     chronométré (RES-02 aujourd'hui simulé sur table) ;
  6. marquage art. 50(2) si la génération n'est pas strictement extractive
     (D8).
- Options écartées : 2, parce que 5 s par réponse sur un GPU de poste
  personnel ne tient pas une charge multi-utilisateur, sans gain démontré ;
  3 seule, parce qu'une coupure du fournisseur couperait tout.
- Impacts : données (transferts), coût (faible en API, élevé en conformité),
  sécurité (surface d'injection réelle), souveraineté (dépendance au
  fournisseur, réversibilité à prouver), exploitation (second chemin de
  réponse à superviser).
- Gate, rollback et condition de révision : les six préalables sont le gate.
  Rollback = désactiver la génération, le repli extractif répond seul.
  Révision : décision d'un besoin métier de génération en M8, ou arrêt du DPF.
- Changement après contradiction indépendante : à remplir.
