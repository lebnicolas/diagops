from __future__ import annotations

import argparse
import json
import platform
import sys
from importlib import metadata
from pathlib import Path


def version(package: str) -> str | None:
    try:
        return metadata.version(package)
    except metadata.PackageNotFoundError:
        return None


def collect_environment() -> dict[str, object]:
    result: dict[str, object] = {
        "platform": platform.platform(),
        "machine": platform.machine(),
        "python": sys.version,
        "packages": {
            name: version(name)
            for name in ["torch", "transformers", "peft", "accelerate", "pydantic"]
        },
    }
    try:
        import torch

        backend = "cpu"
        accelerator = None
        memory_bytes = None
        if torch.cuda.is_available():
            backend = "cuda"
            accelerator = torch.cuda.get_device_name(0)
            memory_bytes = torch.cuda.get_device_properties(0).total_memory
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            backend = "mps"
            accelerator = "Apple Metal"
        result.update(
            {
                "backend": backend,
                "accelerator": accelerator,
                "accelerator_memory_bytes": memory_bytes,
                "torch_cuda_version": torch.version.cuda,
            }
        )
    except ImportError:
        result["backend"] = "torch_not_installed"
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    data = collect_environment()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps(data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
