from src.features import build_feature_table, group_windows


def test_rows_are_grouped_by_window():
    rows = [
        {"window_id": "W1", "value": "1.0"},
        {"window_id": "W2", "value": "2.0"},
        {"window_id": "W1", "value": "3.0"},
    ]
    assert {key: len(value) for key, value in group_windows(rows).items()} == {
        "W1": 2,
        "W2": 1,
    }


def test_feature_table_has_one_row_per_window():
    rows = [
        {"window_id": "W1", "value": "1.0"},
        {"window_id": "W1", "value": "3.0"},
    ]
    assert build_feature_table(rows) == [
        {"window_id": "W1", "value_mean": 2.0, "value_std": 1.0, "missing_share": 0.0}
    ]
