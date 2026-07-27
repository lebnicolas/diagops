from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


PINNED_MODEL_REVISION = "c1899de289a04d12100db370d81485cdf75e47ca"


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    revision = config.get("model", {}).get("revision")
    if revision != PINNED_MODEL_REVISION:
        raise ValueError(
            "La configuration doit utiliser la revision Qwen3-0.6B epinglee : "
            f"{PINNED_MODEL_REVISION}."
        )
    return config
