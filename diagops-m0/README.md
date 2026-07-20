# DiagOps — Module 0

Application d'assistance au diagnostic de maintenance industrielle.

Un rapport technicien en texte libre entre, un diagnostic structuré conforme au contrat DiagOps sort.

```
"La pompe P-204 vibre fortement depuis deux jours.
 Temperature anormale et bruit metallique au demarrage."
                        ↓
{ "symptom": "vibration anormale au demarrage",
  "severity": "high",
  "failure_hypothesis": "roulement use ou desalignement", ... }
```

---

## Prérequis

- **Python 3.12** (développé et testé sur 3.12.10)
- **[LM Studio](https://lmstudio.ai/)** avec le modèle `mistralai/ministral-3-3b` chargé, serveur local actif sur le port `1234`

> Le projet n'appelle aucune API distante : tout tourne en local. Voir [Choix du modèle](#choix-du-modèle).

---

## Installation

```powershell
git clone https://github.com/lebnicolas/formation-IA.git
cd formation-IA/projets/diagops-m0

python -m venv .venv
.\.venv\Scripts\Activate.ps1        # Windows
# source .venv/bin/activate         # Linux / macOS

pip install -r requirements.txt
```

---

## Lancement

L'interface appelle l'API : il faut **deux terminaux**.

```powershell
# terminal 1 — API
uvicorn app.main:app --reload

# terminal 2 — interface
streamlit run ui/streamlit_app.py
```

| Service | URL |
|---|---|
| API | http://localhost:8000 |
| Documentation interactive (Swagger) | http://localhost:8000/docs |
| Interface Streamlit | http://localhost:8501 |

### Configuration

Toutes les variables sont optionnelles et ont une valeur par défaut fonctionnelle.

| Variable | Défaut | Rôle |
|---|---|---|
| `DIAGOPS_API_URL` | `http://localhost:1234/v1` | Endpoint du modèle |
| `DIAGOPS_MODEL` | `mistralai/ministral-3-3b` | Modèle utilisé |
| `DIAGOPS_TIMEOUT` | `120` | Timeout de l'appel modèle (s) |
| `DIAGOPS_MAX_TOKENS` | `1200` | Longueur maximale de la réponse |
| `DIAGOPS_UI_API` | `http://localhost:8000` | API visée par l'interface |

---

## Routes API

### `POST /diagnose`

Produit un diagnostic à partir d'un rapport technicien.

**Entrée**

| Champ | Type | Obligatoire | Contraintes |
|---|---|---|---|
| `technician_note` | string | oui | 10 à 5000 caractères, non vide après nettoyage |
| `equipment_id` | string | non | — |
| `report_id` | string | non | — |

**Sortie** — contrat DiagOps (`data_pack/SCHEMA.md`)

| Champ | Type | Contraintes |
|---|---|---|
| `equipment_id` | string | — |
| `symptom` | string | — |
| `severity` | enum | `low` \| `medium` \| `high` \| `critical` |
| `failure_hypothesis` | string | — |
| `recommended_action` | string | — |
| `confidence` | float | entre 0 et 1 |
| `evidence` | list[string] | — |
| `requires_human_review` | bool | — |

**Codes de retour**

| Code | Signification |
|---|---|
| `200` | Diagnostic produit, conforme au contrat |
| `422` | Rapport invalide (vide, trop court, trop long, champ manquant) |
| `502` | Modèle injoignable, ou sortie non conforme au contrat |

### `GET /health`

Réponse immédiate indiquant que le service est debout et quel modèle est configuré. Ne teste pas la disponibilité du modèle.

---

## Exemple entrée / sortie

**Requête**

```bash
curl -X POST http://localhost:8000/diagnose \
  -H "Content-Type: application/json" \
  -d '{
    "technician_note": "Pompe P-204 en zone A. Vibration plus forte que d'\''habitude depuis la prise de poste. Bruit metallique au demarrage puis baisse apres quelques minutes. Temperature carter mesuree a 71 C.",
    "equipment_id": "EQ-PUMP-001",
    "report_id": "RPT-2026S1-0001"
  }'
```

**Réponse** (`200`)

```json
{
  "equipment_id": "EQ-PUMP-001",
  "symptom": "vibration accrue et bruit metallique au demarrage, temperature carter elevee",
  "severity": "high",
  "failure_hypothesis": "usure prematuree des roulements ou jeu excessif dans l'alignement mecanique",
  "recommended_action": "arret pour inspection visuelle, mesure de jeu axial/radial, verification des roulements",
  "confidence": 0.85,
  "evidence": [
    "rapport RPT-2026S1-0001",
    "vibration plus forte que d'habitude",
    "temperature carter a 71 C"
  ],
  "requires_human_review": true
}
```

**Cas d'erreur** (`422`)

```bash
curl -X POST http://localhost:8000/diagnose \
  -H "Content-Type: application/json" -d '{"technician_note": "court"}'
```

```json
{"detail": [{"msg": "String should have at least 10 characters", ...}]}
```

---

## Choix du modèle

### Modèle retenu

**`mistralai/ministral-3-3b`**, servi en local par LM Studio via son API compatible OpenAI.

### Pourquoi celui-ci

- **Instruction-following.** La tâche demande de produire un JSON structuré à partir de texte libre. Un modèle de classification zero-shot aurait pu attribuer `severity`, mais pas rédiger `failure_hypothesis` ni `recommended_action`, qui sont des textes libres.
- **Exécution locale.** Aucune donnée ne sort de la machine — argument réel en maintenance industrielle, où les rapports peuvent contenir des informations sensibles sur l'outil de production. Pas de clé d'API, pas de coût à l'usage, pas de dépendance réseau.
- **Compromis vitesse/qualité.** ~25 s par diagnostic sur CPU. Acceptable pour un poste de travail.
- **API compatible OpenAI.** Changer de modèle ou basculer vers une API distante ne demande qu'une variable d'environnement, aucun changement de code.

### Alternatives considérées

| Alternative | Pourquoi écartée |
|---|---|
| **`qwen/qwen3.5-9b`** (local) | Meilleures réponses, mais modèle à raisonnement : **plus de 120 s** par diagnostic, dont l'essentiel en réflexion interne. Inutilisable derrière une interface. Mesuré, pas supposé. |
| **Zero-shot classification** (HuggingFace) | Adapté à `severity` seul. Ne produit pas les champs rédactionnels du contrat. Aurait imposé de combiner plusieurs modèles. |
| **Modèle HuggingFace chargé en local** (`transformers`) | Téléchargement lourd, et Python 3.14 initialement installé posait un risque de wheels indisponibles. LM Studio évite toute la gestion de dépendances ML. |
| **API distante** (OpenAI, Anthropic, Mistral) | Meilleure qualité et latence, mais coût à l'usage, clé à gérer, et sortie des données hors du poste. Reste une option : une variable d'environnement suffit. |

### Conditions d'utilisation

- **Modèle** : famille Ministral (Mistral AI). **La licence exacte est à vérifier avant tout usage commercial** — les modèles Ministral ont été publiés sous licence de recherche, avec licence commerciale distincte. Sans impact pour un usage pédagogique.
- **Taille** : ~3 milliards de paramètres, quantisé par LM Studio. Tourne sur un poste de travail standard sans GPU dédié.
- **Dépendance** : LM Studio doit être lancé avec le modèle chargé. L'API renvoie `502` sinon, avec un message explicite.

---

## Tests

```powershell
pytest                    # 8 tests rapides, modèle mocké, ~0,3 s
pytest -m integration     # test de bout en bout avec le vrai modèle, ~25 s
pytest -v                 # détail
```

Les tests rapides **remplacent le modèle par un double**. Ils sont déterministes, s'exécutent en millisecondes et ne demandent pas que LM Studio tourne — ils passent sur n'importe quelle machine après un simple `pip install`.

| Test | Vérifie |
|---|---|
| `test_health_repond` | Le service répond |
| `test_diagnose_cas_nominal` | Les 8 champs du contrat, `severity` dans l'enum, `confidence` dans [0,1] |
| `test_diagnose_transmet_les_identifiants` | `equipment_id` et `report_id` atteignent le client modèle |
| `test_diagnose_entrees_invalides` (×3) | `422` sur note courte, faite d'espaces, vide |
| `test_diagnose_champ_manquant` | `422` si `technician_note` est absent |
| `test_diagnose_modele_indisponible` | `502` explicite, pas un `500` brut |
| `test_diagnose_modele_reel` | Bout en bout, sur demande |

Le test nominal valide **la forme, jamais la formulation** : un LLM est non déterministe, exiger une phrase précise produirait un test qui échoue au hasard.

---

## Limites connues

1. **`confidence` n'est pas une mesure calibrée.** Le modèle produit un nombre plausible, pas une probabilité issue d'un calcul d'incertitude. Il ne doit pas être interprété comme une fiabilité statistique.

2. **`requires_human_review` est décidé par le modèle.** Aucune règle ne le force. Un rapport sommaire peut recevoir `false` avec une confiance élevée — le pire type d'erreur dans ce domaine. Une amélioration consisterait à le dériver d'un seuil sur `confidence`.

3. **Le prompt n'est pas un contrat.** Il demande d'écrire sans accents, comme les données d'entrée ; le modèle en produit malgré tout. Seule la validation Pydantic contraint réellement la sortie — d'où le choix de valider systématiquement.

4. **Latence de ~25 s.** Perceptible dans l'interface. Vient du modèle local sur CPU, pas du code.

5. **Aucune évaluation quantitative.** Le comportement n'a pas été mesuré sur l'ensemble des 40 rapports. Voir `evaluation_m0.md` (brief 2).

6. **Avertissement de dépréciation.** Starlette signale que `httpx` est déprécié pour `TestClient` au profit de `httpx2`. Sans effet aujourd'hui, à surveiller.

---

## Structure du projet

```
diagops-m0/
├── app/
│   ├── main.py            API FastAPI — POST /diagnose, GET /health
│   ├── schemas.py         contrat DiagOps en Pydantic
│   └── model_client.py    appel du modèle, extraction JSON, validation
├── ui/
│   └── streamlit_app.py   interface de test
├── tests/
│   └── test_api.py        8 tests rapides + 1 test d'intégration
├── data_pack/             jeu de données fourni (40 rapports, schéma)
├── pytest.ini
├── requirements.txt
└── README.md
```

### Point d'architecture

L'interface passe par l'API, elle n'appelle jamais le client modèle directement. C'est un aller-retour HTTP de plus, mais cela garantit qu'elle teste exactement ce que les utilisateurs consommeront.

De même, **aucune sortie non conforme ne franchit `model_client.py`** : le JSON produit par le modèle est validé contre le contrat avant d'être renvoyé. Un modèle qui invente un champ ou une sévérité hors énumération provoque une erreur explicite, jamais une réponse silencieusement fausse.
