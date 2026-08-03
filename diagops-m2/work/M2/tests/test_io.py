from pathlib import Path

from src.data_pipeline.io import file_sha256


def test_file_sha256_known_content(tmp_path: Path):
    sample = tmp_path / "sample.txt"
    # write_bytes et pas write_text : en mode texte, Windows traduit "\n" en
    # "\r\n" et le fichier fait 9 octets au lieu de 8 — le checksum attendu
    # devient inatteignable. Un test de checksum se pilote en binaire.
    sample.write_bytes(b"diagops\n")
    assert file_sha256(sample) == "38cc32b04546d8571adbe5542929faa4aefef0d904ca62340a55685844f1b64b"
