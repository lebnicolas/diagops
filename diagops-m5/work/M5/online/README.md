# Brief online M5 — déployer et monitorer le détecteur de provenance

Service de scoring autonome autour de l'artefact **gelé en M4** : un détecteur de provenance de
fenêtres capteurs (réelle / fabriquée). Aucun lien avec le service RAG du brief présentiel — son
propre artefact, ses propres dépendances, sa propre chaîne de livraison.

## Démarrage

```bash
python -m venv .venv && .venv\Scripts\Activate.ps1     # PowerShell
python -m pip install -r requirements.lock
python -m pytest -q                                     # 18 tests

docker compose -f deploy/compose.yaml up -d --build --wait
curl http://127.0.0.1:8100/health/ready
```

Ports : **8100** (service), **9190** (Prometheus). Décalés de la stack RAG pour que les deux
coexistent sur le même poste.

## API

| Route | Rôle |
|---|---|
| `GET /health/live` | le processus répond — ne dépend pas de l'artefact |
| `GET /health/ready` | le modèle est chargé, identifié et conforme |
| `GET /version` | date de gel, commit, algorithme, seuil, checksum, versions sklearn, référence |
| `POST /predict` | provenance d'une fenêtre de mesures |
| `GET /metrics` | exposition Prometheus |

```bash
curl -X POST http://127.0.0.1:8100/predict -H 'Content-Type: application/json' \
  -d '{"mesures":[{"timestamp":"...","value":"1.2","sensor_name":"vibration_mm_s","unit":"mm/s"}, ...]}'
```

## Documents

| Fichier | Contenu |
|---|---|
| `docs/artefact.md` | entrées, sorties, paramètres, dépendances, résultats de référence |
| `docs/registre_versions.md` | unités versionnées et ce qui déclenche une version |
| `docs/metriques_et_declencheurs.md` | source, fréquence, seuil, destinataire, action |
| `docs/rapport_livraison.md` | livraison exécutée, candidat défectueux bloqué, preuves |
| `docs/rollback.md` | procédure de restauration, exécutée en 7 s |
| `journal_bord.md` | chronologie datée |

## Trois choses à savoir avant d'y toucher

1. **L'ordre des 19 features est contraignant.** Le `StandardScaler` a été ajusté sans noms de
   colonnes : dans le désordre il ne lève pas, il rend des résultats faux.
2. **scikit-learn est figé à 1.7.1**, la version du gel. La conformité est vérifiée au démarrage
   et exposée en métrique.
3. **L'artefact est dans l'image, pas dans un volume.** Tout changement de modèle est un
   redéploiement, et le rollback est un retour à un digest antérieur.

## Résultats de référence

F1 hors pli **0,694 ± 0,068** (baseline M3 : 0,374). Le F1 de 0,952 obtenu par le test de
non-régression est **in-sample** — il vérifie que la chaîne déployée décide comme la chaîne
d'entraînement, il ne mesure pas la performance.
