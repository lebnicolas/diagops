from __future__ import annotations

import json
from typing import Any


SYSTEM_PROMPT = """Vous etes DiagOps, un assistant de maintenance industrielle.
Transformez le rapport technicien en un unique objet JSON conforme au contrat.
N'ajoutez aucun texte avant ou apres le JSON. Une recommandation doit rester
soumise a une revue humaine."""


def user_message(input_text: str, report_id: str | None = None) -> str:
    report_reference = f"Identifiant du rapport: {report_id}\n" if report_id else ""
    return (
        "Analysez le rapport suivant et retournez le diagnostic JSON.\n\n"
        f"{report_reference}Rapport:\n{input_text}"
    )


def prompt_messages(
    input_text: str, report_id: str | None = None
) -> list[dict[str, str]]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message(input_text, report_id)},
    ]


def training_messages(
    input_text: str,
    expected_output: dict[str, Any],
    report_id: str | None = None,
) -> list[dict[str, str]]:
    messages = prompt_messages(input_text, report_id)
    messages.append(
        {
            "role": "assistant",
            "content": json.dumps(
                expected_output, ensure_ascii=False, separators=(",", ":")
            ),
        }
    )
    return messages


def apply_chat_template(
    tokenizer: Any,
    messages: list[dict[str, str]],
    *,
    add_generation_prompt: bool,
    enable_thinking: bool,
) -> str:
    kwargs = {
        "tokenize": False,
        "add_generation_prompt": add_generation_prompt,
    }
    try:
        return tokenizer.apply_chat_template(
            messages, enable_thinking=enable_thinking, **kwargs
        )
    except TypeError:
        return tokenizer.apply_chat_template(messages, **kwargs)
