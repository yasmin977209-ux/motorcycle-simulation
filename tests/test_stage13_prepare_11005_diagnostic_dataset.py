from __future__ import annotations

import numpy as np

from scripts.stage13_prepare_11005_diagnostic_dataset import (
    build_daily_distribution,
    same_summary,
)


def test_daily_distribution_uses_only_present_trials_and_linear_quantiles() -> None:
    matrices = {
        "Cash": np.array([[1.0, 3.0, np.nan], [2.0, 4.0, np.nan], [3.0, np.nan, np.nan]]),
        "Net_Equity": np.array([[10.0, 30.0, np.nan], [20.0, 40.0, np.nan], [30.0, np.nan, np.nan]]),
        "Active_Bikes": np.array([[1.0, 3.0, np.nan], [2.0, 4.0, np.nan], [3.0, np.nan, np.nan]]),
        "Owned_Transferred_Bikes": np.array([[0.0, 1.0, np.nan], [1.0, 2.0, np.nan], [2.0, np.nan, np.nan]]),
        "Pending_Claims": np.array([[1.0, 0.0, np.nan], [2.0, 1.0, np.nan], [3.0, np.nan, np.nan]]),
    }
    rows = build_daily_distribution(matrices, 2)
    assert len(rows) == 2
    assert rows[0]["date"] == "2027-01-01"
    assert rows[0]["active_trial_count"] == 3
    assert rows[0]["P50_Cash"] == 2.0
    assert rows[1]["active_trial_count"] == 2
    assert rows[1]["P50_Cash"] == 3.5


def test_summary_reuse_requires_exact_keys_and_python_types() -> None:
    assert same_summary({"trial_id": 2, "value": 7}, {"trial_id": 2, "value": 7}) is True
    assert same_summary({"trial_id": 2, "value": 7.0}, {"trial_id": 2, "value": 7}) is False
    assert same_summary({"trial_id": 2}, {"trial_id": 2, "value": 7}) is False
