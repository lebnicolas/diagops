"""Promotion et retour arrière : ce qui doit être archivé, et quand.

Le compose publiait par `cp candidat actif` : l'index sain disparaissait au moment où il devenait
le seul recours. Corrigé au bloc 6. Puis un second défaut est apparu à l'usage, en enchaînant une
promotion et un retour — le rollback écrasait à son tour la version qu'il remplaçait.
"""

import json

import pytest

from pipelines.promote_index import promote_index
from pipelines.rollback_index import available, rollback_index
from src.retrieval import build_version, postings


def index(version: str) -> dict:
    return {
        "index_version": version,
        "build_version": build_version(),
        "document_count": 1,
        "documents": [{
            "document_id": "DOC-1", "revision": "1",
            "terms": postings("pompe vibration"), "allowed_roles": ["technicien"],
        }],
    }


def ecrire(chemin, contenu) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(contenu), encoding="utf-8")


def test_la_promotion_archive_avant_de_publier(tmp_path) -> None:
    actif, histo = tmp_path / "runtime/index.json", tmp_path / "history"
    ecrire(actif, index("lexical-v1"))
    candidat = tmp_path / "candidates/index.json"
    ecrire(candidat, index("lexical-v2"))

    resultat = promote_index(candidat, actif, histo)
    assert resultat == {"published": "lexical-v2", "archived": "lexical-v1",
                        "history": ["index-lexical-v1.json"]}
    assert json.loads(actif.read_text(encoding="utf-8"))["index_version"] == "lexical-v2"


def test_la_promotion_refuse_un_gate_non_passe(tmp_path) -> None:
    actif, histo = tmp_path / "runtime/index.json", tmp_path / "history"
    candidat, gate = tmp_path / "candidates/index.json", tmp_path / "gate.json"
    ecrire(candidat, index("lexical-v2"))
    ecrire(gate, {"status": "failed"})
    with pytest.raises(SystemExit):
        promote_index(candidat, actif, histo, gate)


def test_une_archive_existante_n_est_jamais_reecrite(tmp_path) -> None:
    """Un point de retour n'est pas un cache : l'écraser perd l'état vers lequel on revenait."""
    actif, histo = tmp_path / "runtime/index.json", tmp_path / "history"
    ecrire(actif, index("lexical-v1"))
    ecrire(histo / "index-lexical-v1.json", index("lexical-v1-original"))
    candidat = tmp_path / "candidates/index.json"
    ecrire(candidat, index("lexical-v2"))

    promote_index(candidat, actif, histo)
    archive = json.loads((histo / "index-lexical-v1.json").read_text(encoding="utf-8"))
    assert archive["index_version"] == "lexical-v1-original"


def test_le_rollback_archive_la_version_qu_il_remplace(tmp_path) -> None:
    """Découvert à l'usage : sans cela, un rollback pris à tort est irréversible.

    Et le post-incident perd la pièce à conviction — le brief 2 exige de n'effacer ni traces ni
    état initial avant la fin de l'exercice.
    """
    actif, histo = tmp_path / "runtime/index.json", tmp_path / "history"
    ecrire(actif, index("lexical-v1"))
    candidat = tmp_path / "candidates/index.json"
    ecrire(candidat, index("lexical-v2-fautive"))

    promote_index(candidat, actif, histo)
    rollback_index(actif, histo, "lexical-v1")

    assert sorted(available(histo)) == ["lexical-v1", "lexical-v2-fautive"]
    assert json.loads(actif.read_text(encoding="utf-8"))["index_version"] == "lexical-v1"


def test_le_rollback_refuse_une_version_absente(tmp_path) -> None:
    actif, histo = tmp_path / "runtime/index.json", tmp_path / "history"
    ecrire(actif, index("lexical-v1"))
    histo.mkdir(parents=True, exist_ok=True)
    with pytest.raises(SystemExit):
        rollback_index(actif, histo, "lexical-inexistante")


def test_le_rollback_refuse_une_archive_sans_postings(tmp_path) -> None:
    """Une archive corrompue restaurée sous incident transforme une panne en deux pannes."""
    actif, histo = tmp_path / "runtime/index.json", tmp_path / "history"
    ecrire(actif, index("lexical-v1"))
    vide = index("lexical-v0")
    vide["documents"][0]["terms"] = {}
    ecrire(histo / "index-lexical-v0.json", vide)
    with pytest.raises(SystemExit):
        rollback_index(actif, histo, "lexical-v0")
