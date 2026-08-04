"""Rend le paquet `qualification` importable depuis les tests.

Les tests M2 se lancent depuis `work/M2` avec `python -m pytest`, ce qui place
ce dossier sur le chemin d'import et rend `src.data_pipeline` visible. Le
paquet de qualification vit un cran plus bas ; ce fichier ajoute son dossier.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
for entry in (HERE.parent, HERE):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))
