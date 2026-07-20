# Etat du projet DiagOps — fin du module 0

## Resume

DiagOps dispose d'une premiere application fonctionnelle : un rapport technicien en texte libre est soumis a une API, un diagnostic structure conforme au contrat DiagOps est retourne.

Le modele utilise est un modele sur etagere, appele sans entrainement ni fine-tuning, conformement au perimetre du module.

## Donnees utilisees

```text
data_pack/2026-S1/reports/reports.jsonl
```

40 rapports techniciens. Aucune autre source du data pack n'a ete utilisee.

Le `data_pack` a ete deplace dans le dossier du projet pour que le depot soit autonome : un tiers qui le clone peut lancer l'application sans recuperer de fichiers ailleurs.

## Etat applicatif

| Element | Emplacement | Etat |
|---|---|---|
| API FastAPI | `app/main.py` | fonctionnelle |
| Route `POST /diagnose` | `app/main.py` | documentee (Swagger sur `/docs`) |
| Route `GET /health` | `app/main.py` | fonctionnelle |
| Schemas Pydantic entree/sortie | `app/schemas.py` | complets, contraintes actives |
| Client du modele sur etagere | `app/model_client.py` | fonctionnel |
| Interface Streamlit | `ui/streamlit_app.py` | 40 rapports selectionnables + saisie libre |
| Tests API | `tests/test_api.py` | 13 rapides + 1 integration |
| README | `README.md` | complet |
| Exemples entree/sortie | `README.md` | requete curl + reponse |
| Evaluation | `evaluation_m0.md` | 40 rapports |

## Contrat de sortie

Respecte, et verifie a l'execution par Pydantic :

```json
{
  "equipment_id": "string|null",
  "symptom": "string",
  "severity": "low|medium|high|critical",
  "failure_hypothesis": "string",
  "recommended_action": "string",
  "confidence": 0.0,
  "evidence": ["string"],
  "requires_human_review": true
}
```

Contraintes appliquees :

- `severity` limitee a l'enumeration — toute autre valeur est rejetee ;
- `confidence` bornee a l'intervalle [0, 1] ;
- `equipment_id` nullable, sans identifiant invente en cas d'equipement non identifiable ;
- une note faite uniquement d'espaces est refusee (422).

**Aucune sortie non conforme ne franchit `model_client.py`** : le JSON produit par le modele est valide contre le contrat avant d'etre renvoye. Une sortie invalide provoque une erreur explicite (502), jamais une reponse silencieusement fausse.

## Choix documentes

Le README contient :

- le modele retenu : `mistralai/ministral-3-3b`, servi en local par LM Studio ;
- la raison du choix : instruction-following necessaire pour les champs redactionnels, execution locale (aucune donnee ne sort du poste), API compatible OpenAI permettant de changer de modele par variable d'environnement ;
- les alternatives considerees, dont `qwen3.5-9b` ecarte apres mesure (plus de 120 s par diagnostic contre 5 s) ;
- les limites observees, mesurees sur les 40 rapports ;
- la procedure d'installation, les commandes de lancement et de test.

## Regle metier ajoutee

`requires_human_review` n'est pas laisse au seul jugement du modele. Sous le seuil `DIAGOPS_CONFIDENCE_THRESHOLD` (0.825), la revision humaine est imposee.

Le seuil est place **entre** deux paliers de confiance emis par le modele, et non sur l'un d'eux : le modele n'emet que 6 valeurs distinctes par paliers de 0.05, et un seuil pose sur une valeur emise rendrait la regle instable.

Le taux obtenu (60 a 65 % de revisions imposees) reste choisi a l'estime : sans verite terrain, rien ne prouve que la confiance correle avec la justesse.

## Limites connues

Limites generiques attendues a ce stade du module :

- le modele n'est pas specialise sur les rapports DiagOps ;
- les diagnostics peuvent etre incomplets ou instables ;
- la confiance indiquee reste indicative ;
- la validation humaine reste obligatoire ;
- les donnees capteurs, historiques, feedback et images ne sont pas utilisees.

Limites specifiques mesurees sur les 40 rapports :

- **La severite discrimine faiblement** : `medium` 68 %, `high` 28 %, `low` 5 %, `critical` **0 %**. Un incident reellement critique risque d'etre sous-evalue.
- **La confiance est quasi discrete** : 6 valeurs distinctes seulement, par paliers de 0.05, moyenne ~0.79, ecart-type ~0.07. Le modele ne calcule pas une incertitude, il choisit un nombre rond.
- **L'evaluation n'est pas reproductible** : a `temperature=0.2`, deux executions sur les memes rapports divergent (un rapport a recu `medium` puis `low`). Les chiffres sont des ordres de grandeur.
- **Le prompt n'est pas un contrat** : la consigne d'ecrire sans accents n'est pas respectee par le modele. Seule la validation Pydantic contraint reellement la sortie.
- **Instabilite de formulation** : `alignement mecanique` puis `alimentation mecanique` sur deux appels, le second sans sens technique.
- **Un echantillon de 5 rapports induit en erreur** : les premieres mesures concluaient a tort a une severite toujours `medium`. Le passage a 40 les a dementies.

## Entree pour le module 1

Le module 1 repart de :

- un depot applicatif fonctionnel et autonome ;
- la route `POST /diagnose` disponible ;
- un contrat JSON stabilise et verifie a l'execution ;
- 40 rapports traites, resultats consignes dans `evaluation_m0.md` ;
- les limites du modele sur etagere identifiees et chiffrees.

Ces mesures constituent la **reference de comparaison** pour le module 1 : l'adaptateur LoRA entraine sur le sous-ensemble annote devra etre confronte a ces chiffres.

Le jeu `annotated_diagnostics`, disponible en M1, apportera la verite terrain qui manque aujourd'hui — elle permettra de calibrer le seuil de confiance au lieu de le choisir a l'estime.
