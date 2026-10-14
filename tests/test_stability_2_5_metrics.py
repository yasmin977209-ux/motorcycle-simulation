"""Unit tests for the seven Reference §2.5 stability indicators.

Reference: §2.5; decision D-2026-10-14-20.
These tests do not replace Gate A or Gate B acceptance evidence.
"""
from __future__ import annotations

import constants
from scripts.stage7_stability import evaluate_reference_stability


def metric_values(value: float = 100.0) -> dict[str, float]:
    return {name: value for name in constants.REFERENCE_STABILITY_INDICATORS}


def evaluate_one(name: str, previous: float, current: float) -> dict:
    old = metric_values()
    new = metric_values()
    old[name] = previous
    new[name] = current
    return evaluate_reference_stability(old, new)


def test_reference_metric_list_has_seven_canonical_indicators() -> None:
    assert constants.REFERENCE_STABILITY_INDICATORS == (
        "P10_Cumulative_Project_Profit",
        "P50_Cumulative_Project_Profit",
        "P90_Cumulative_Project_Profit",
        "P90_Final_Cash",
        "Probability_of_Accounting_Loss",
        "P90_Termination_Count",
        "P90_Held_Assets",
    )
    assert "Probability_of_Loss" not in constants.REFERENCE_STABILITY_INDICATORS


def test_all_seven_metrics_pass_when_unchanged() -> None:
    metrics = metric_values()
    result = evaluate_reference_stability(metrics, metrics)
    assert result["checked"] is True
    assert result["stable"] is True
    assert result["status"] == "PASS"
    assert len(result["metrics"]) == 7
    assert all(item["status"] == "PASS" for item in result["metrics"].values())


def test_relative_change_strictly_below_one_percent_passes() -> None:
    name = "P10_Cumulative_Project_Profit"
    result = evaluate_one(name, 100.0, 100.999)
    assert result["status"] == "PASS"
    assert result["metrics"][name]["relative_change"] < 0.01


def test_relative_change_equal_to_one_percent_fails_strict_inequality() -> None:
    name = "P50_Cumulative_Project_Profit"
    result = evaluate_one(name, 100.0, 101.0)
    assert result["status"] == "FAIL"
    assert result["metrics"][name]["relative_change"] == 0.01


def test_relative_change_uses_absolute_previous_value_for_negative_metrics() -> None:
    name = "P90_Cumulative_Project_Profit"
    result = evaluate_one(name, -100.0, -100.5)
    assert result["status"] == "PASS"
    assert result["metrics"][name]["relative_change"] == 0.005


def test_near_zero_uses_strict_absolute_fallback() -> None:
    name = "Probability_of_Accounting_Loss"
    below = evaluate_one(name, 0.0, 0.999)
    equal = evaluate_one(name, 0.0, 1.0)
    assert below["status"] == "PASS"
    assert below["metrics"][name]["comparison"] == "ABSOLUTE_NEAR_ZERO"
    assert below["metrics"][name]["relative_change"] is None
    assert equal["status"] == "FAIL"


def test_missing_metric_is_blocked_not_passed() -> None:
    previous = metric_values()
    current = metric_values()
    del current["P90_Held_Assets"]
    result = evaluate_reference_stability(previous, current)
    assert result["checked"] is False
    assert result["stable"] is False
    assert result["status"] == "BLOCKED"
    assert result["missing_current"] == ["P90_Held_Assets"]


def test_non_finite_or_boolean_metric_is_blocked() -> None:
    for value in (float("nan"), float("inf"), True):
        previous = metric_values()
        current = metric_values()
        current["P90_Final_Cash"] = value
        result = evaluate_reference_stability(previous, current)
        assert result["checked"] is False
        assert result["stable"] is False
        assert result["status"] == "BLOCKED"
        assert "P90_Final_Cash" in result["invalid_values"]
