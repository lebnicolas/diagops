from __future__ import annotations

import argparse
import json
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import load_config
from .dataset import file_sha256, load_jsonl
from .model_provider import resolve_dtype
from .prompting import apply_chat_template, prompt_messages, training_messages


class SupervisedDataset:
    def __init__(
        self,
        rows: list[dict[str, Any]],
        tokenizer: Any,
        max_length: int,
    ) -> None:
        self.examples: list[dict[str, list[int]]] = []
        for row in rows:
            prompt = apply_chat_template(
                tokenizer,
                prompt_messages(row["input_text"], row.get("report_id")),
                add_generation_prompt=True,
                enable_thinking=False,
            )
            full = apply_chat_template(
                tokenizer,
                training_messages(
                    row["input_text"],
                    row["expected_output"],
                    row.get("report_id"),
                ),
                add_generation_prompt=False,
                enable_thinking=False,
            )
            prompt_ids = tokenizer(
                prompt,
                add_special_tokens=False,
                truncation=True,
                max_length=max_length,
            )["input_ids"]
            full_ids = tokenizer(
                full,
                add_special_tokens=False,
                truncation=True,
                max_length=max_length,
            )["input_ids"]
            labels = [-100] * min(len(prompt_ids), len(full_ids))
            labels.extend(full_ids[len(labels):])
            self.examples.append(
                {
                    "input_ids": full_ids,
                    "attention_mask": [1] * len(full_ids),
                    "labels": labels,
                }
            )

    def __len__(self) -> int:
        return len(self.examples)

    def __getitem__(self, index: int) -> dict[str, list[int]]:
        return self.examples[index]


@dataclass
class SupervisedCollator:
    tokenizer: Any

    def __call__(self, examples: list[dict[str, list[int]]]) -> dict[str, Any]:
        import torch

        max_length = max(len(example["input_ids"]) for example in examples)
        input_ids: list[list[int]] = []
        attention_masks: list[list[int]] = []
        labels: list[list[int]] = []
        for example in examples:
            padding = max_length - len(example["input_ids"])
            input_ids.append(
                example["input_ids"] + [self.tokenizer.pad_token_id] * padding
            )
            attention_masks.append(example["attention_mask"] + [0] * padding)
            labels.append(example["labels"] + [-100] * padding)
        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_masks, dtype=torch.long),
            "labels": torch.tensor(labels, dtype=torch.long),
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--train-data", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    import torch
    from peft import LoraConfig, TaskType, get_peft_model
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        Trainer,
        TrainingArguments,
        set_seed,
    )

    if not torch.cuda.is_available():
        raise RuntimeError(
            "Le run de reference doit etre execute sur l'environnement CUDA commun."
        )

    config = load_config(args.config)
    training = config["training"]
    model_config = config["model"]
    lora = config["lora"]
    seed = int(training["seed"])
    set_seed(seed)
    random.seed(seed)

    tokenizer = AutoTokenizer.from_pretrained(
        model_config["id"],
        revision=model_config["revision"],
        trust_remote_code=False,
    )
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype_name = model_config.get("dtype", "bfloat16")
    if dtype_name == "bfloat16" and not torch.cuda.is_bf16_supported():
        dtype_name = "float16"
    dtype = resolve_dtype(torch, dtype_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_config["id"],
        revision=model_config["revision"],
        torch_dtype=dtype,
        trust_remote_code=False,
    )
    peft_config = LoraConfig(
        task_type=TaskType.CAUSAL_LM,
        r=int(lora["r"]),
        lora_alpha=int(lora["alpha"]),
        lora_dropout=float(lora["dropout"]),
        target_modules=list(lora["target_modules"]),
        bias="none",
    )
    model = get_peft_model(model, peft_config)

    rows = load_jsonl(args.train_data)
    dataset = SupervisedDataset(
        rows=rows,
        tokenizer=tokenizer,
        max_length=int(training["max_length"]),
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    trainer_args = TrainingArguments(
        output_dir=str(args.output_dir / "checkpoints"),
        seed=seed,
        data_seed=seed,
        per_device_train_batch_size=int(training["per_device_batch_size"]),
        gradient_accumulation_steps=int(
            training["gradient_accumulation_steps"]
        ),
        num_train_epochs=float(training["epochs"]),
        learning_rate=float(training["learning_rate"]),
        warmup_ratio=float(training["warmup_ratio"]),
        weight_decay=float(training["weight_decay"]),
        lr_scheduler_type="cosine",
        logging_steps=int(training["logging_steps"]),
        save_strategy=str(training["save_strategy"]),
        bf16=dtype == torch.bfloat16,
        fp16=dtype == torch.float16,
        report_to=[],
        remove_unused_columns=False,
    )
    trainer = Trainer(
        model=model,
        args=trainer_args,
        train_dataset=dataset,
        data_collator=SupervisedCollator(tokenizer),
    )
    result = trainer.train()

    adapter_dir = args.output_dir / "adapter"
    model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)
    manifest = {
        "model_id": model_config["id"],
        "model_revision": model_config["revision"],
        "config": config,
        "effective_dtype": dtype_name,
        "config_sha256": file_sha256(args.config),
        "train_data": str(args.train_data),
        "train_data_sha256": file_sha256(args.train_data),
        "train_rows": len(rows),
        "train_metrics": result.metrics,
    }
    (args.output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result.metrics, indent=2))


if __name__ == "__main__":
    main()
