from src.dataset import stable_split


def test_stable_split_is_reproducible() -> None:
    rows = [
        {
            "annotation_id": f"ANN-{index:03d}",
            "input_text": str(index),
            "expected_output": {},
        }
        for index in range(10)
    ]
    first = stable_split(rows, seed=42, validation_size=2)
    second = stable_split(list(reversed(rows)), seed=42, validation_size=2)
    assert first == second
    assert len(first[0]) == 8
    assert len(first[1]) == 2
