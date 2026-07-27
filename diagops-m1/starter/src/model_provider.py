from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from .prompting import apply_chat_template, prompt_messages


@dataclass
class GenerationResult:
    text: str
    latency_seconds: float
    accelerator_memory_bytes: int | None


def resolve_dtype(torch: Any, name: str) -> Any:
    if name == "bfloat16":
        return torch.bfloat16
    if name == "float16":
        return torch.float16
    if name == "float32":
        return torch.float32
    raise ValueError(f"dtype non supporte: {name}")


class ModelProvider:
    def __init__(
        self,
        config: dict[str, Any],
        adapter_path: str | None = None,
    ) -> None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        model_config = config["model"]
        self.generation_config = config.get("generation", {})
        self.enable_thinking = config.get("prompt", {}).get(
            "enable_thinking", False
        )

        self.tokenizer = AutoTokenizer.from_pretrained(
            model_config["id"],
            revision=model_config["revision"],
            trust_remote_code=False,
        )
        if self.tokenizer.pad_token_id is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        if torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")

        dtype_name = model_config.get("dtype", "bfloat16")
        if self.device.type == "mps" and dtype_name == "bfloat16":
            dtype_name = "float16"
        if self.device.type == "cpu" and dtype_name != "float32":
            dtype_name = "float32"
        dtype = resolve_dtype(torch, dtype_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_config["id"],
            revision=model_config["revision"],
            torch_dtype=dtype,
            trust_remote_code=False,
        )
        if adapter_path:
            from peft import PeftModel

            self.model = PeftModel.from_pretrained(self.model, adapter_path)

        self.model.to(self.device)
        self.model.eval()

    def generate(
        self, input_text: str, report_id: str | None = None
    ) -> GenerationResult:
        import torch

        prompt = apply_chat_template(
            self.tokenizer,
            prompt_messages(input_text, report_id),
            add_generation_prompt=True,
            enable_thinking=self.enable_thinking,
        )
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        if self.device.type == "cuda":
            torch.cuda.reset_peak_memory_stats(self.device)
            torch.cuda.synchronize(self.device)
        started = time.perf_counter()

        kwargs: dict[str, Any] = {
            "max_new_tokens": self.generation_config.get("max_new_tokens", 256),
            "do_sample": self.generation_config.get("do_sample", False),
            "pad_token_id": self.tokenizer.pad_token_id,
            "eos_token_id": self.tokenizer.eos_token_id,
        }
        if kwargs["do_sample"]:
            kwargs["temperature"] = self.generation_config.get("temperature", 0.7)

        with torch.inference_mode():
            outputs = self.model.generate(**inputs, **kwargs)

        if self.device.type == "cuda":
            torch.cuda.synchronize(self.device)
        latency = time.perf_counter() - started
        prompt_length = inputs["input_ids"].shape[1]
        text = self.tokenizer.decode(
            outputs[0][prompt_length:], skip_special_tokens=True
        )
        memory = (
            int(torch.cuda.max_memory_allocated(self.device))
            if self.device.type == "cuda"
            else None
        )
        return GenerationResult(
            text=text,
            latency_seconds=latency,
            accelerator_memory_bytes=memory,
        )
