from src.metrics import calculate_metrics, parse_raw_json, token_f1


EXPECTED = {
    "equipment_id": "EQ-1",
    "symptom": "vibration forte",
    "severity": "high",
    "failure_hypothesis": "roulement use",
    "recommended_action": "inspecter le palier",
    "confidence": 0.8,
    "evidence": ["rapport R-1"],
    "requires_human_review": True,
}


def test_parse_raw_json_rejects_markdown_fence() -> None:
    assert parse_raw_json('{"severity":"high"}') == {"severity": "high"}
    assert parse_raw_json('```json\n{"severity":"high"}\n```') is None


def test_token_f1() -> None:
    assert token_f1("vibration forte", "vibration forte") == 1.0
    assert 0.0 < token_f1("forte vibration", "vibration") < 1.0


def test_calculate_metrics_perfect_record() -> None:
    records = [
        {
            "expected_output": EXPECTED,
            "parsed_output": EXPECTED,
            "schema_valid": True,
            "latency_seconds": 1.0,
        }
    ]
    metrics = calculate_metrics(records)
    assert metrics["json_parseable_rate"] == 1.0
    assert metrics["schema_valid_rate"] == 1.0
    assert metrics["equipment_id_accuracy"] == 1.0


def test_invalid_json_counts_as_field_error() -> None:
    records = [
        {
            "expected_output": EXPECTED,
            "parsed_output": None,
            "schema_valid": False,
            "latency_seconds": 1.0,
        }
    ]
    metrics = calculate_metrics(records)
    assert metrics["json_parseable_rate"] == 0.0
    assert metrics["equipment_id_accuracy"] == 0.0
    assert metrics["requires_human_review_accuracy"] == 0.0
    assert metrics["text_lexical_f1"] == 0.0
