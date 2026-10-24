from __future__ import annotations

import math
from types import SimpleNamespace

import numpy as np
import pytest

import constants
from scripts.statistical_confidence_sequences import (
    DEFAULT_ALPHA,
    DEFAULT_T_OPT,
    bernoulli_mean_confidence_sequence,
    evaluate_adjacent_transition,
    evaluate_reference_indicators,
    evaluate_stopping_window,
    fixed_quantile_confidence_sequence,
)


def _trial_rows(n: int):
    return [
        SimpleNamespace(
            trial_id=i + 1,
            cumulative_project_profit=(i % 31 - 15) * 1500,
            final_cash=500_000 + (i % 17 - 8) * 900,
            termination_count=i % 5,
            held_assets=i % 4,
        )
        for i in range(n)
    ]


def test_fixed_quantile_cs_uses_linear_point_estimate_and_order_statistic_interval():
    values = list(range(300))
    result = fixed_quantile_confidence_sequence(values, 0.5)
    assert result["n"] == 300
    assert result["method"].startswith("HOWARD_RAMDAS_FIXED_QUANTILE")
    assert result["point_estimate"] == pytest.approx(np.quantile(values, 0.5, method="linear"))
    assert result["lower"] <= result["point_estimate"] <= result["upper"]
    assert result["lower"] in values
    assert result["upper"] in values
    assert result["alpha"] == DEFAULT_ALPHA


def test_fixed_quantile_cs_handles_discrete_ties_without_synthetic_interpolation():
    values = [0] * 150 + [5] * 150
    first = fixed_quantile_confidence_sequence(values, 0.5)
    second = fixed_quantile_confidence_sequence(values, 0.5)
    assert first == second
    assert first["point_estimate"] == 2.5
    assert first["lower"] in (0, 5, -math.inf)
    assert first["upper"] in (0, 5, math.inf)
    assert first["lower"] <= first["point_estimate"] <= first["upper"]


@pytest.mark.parametrize("successes", [0, 1, 150, 299, 300])
def test_bernoulli_beta_mixture_cs_covers_empirical_probability(successes):
    result = bernoulli_mean_confidence_sequence(successes, 300)
    empirical = successes / 300
    assert 0 <= result["lower"] <= empirical <= result["upper"] <= 1
    assert result["half_width"] >= 0
    assert result["alpha"] == DEFAULT_ALPHA
    assert result["precision_pass"] is (result["half_width"] < 0.005)


def test_bernoulli_cs_is_not_a_pointwise_interval_and_is_time_uniform_method_tagged():
    result = bernoulli_mean_confidence_sequence(0, 300)
    assert "BETA_BINOMIAL_MIXTURE" in result["method"]
    assert result["lower"] == 0
    assert result["upper"] > 0


def test_all_seven_reference_indicators_are_present_and_candidate_stays_unaccepted():
    result = evaluate_reference_indicators(_trial_rows(300))
    assert set(result["indicators"]) == set(constants.REFERENCE_STABILITY_INDICATORS)
    assert result["n"] == 300
    assert result["alpha_per_scenario"] == 0.0025
    assert result["t_opt"] == DEFAULT_T_OPT
    assert result["acceptance_status"] == "CANDIDATE_ONLY_NOT_ACCEPTED"
    assert isinstance(result["point_precision_pass"], bool)
    assert {
        name: result["indicators"][name]["margin"]
        for name in (
            "P10_Cumulative_Project_Profit",
            "P50_Cumulative_Project_Profit",
            "P90_Cumulative_Project_Profit",
            "P90_Final_Cash",
            "P90_Termination_Count",
            "P90_Held_Assets",
        )
    } == {
        "P10_Cumulative_Project_Profit": 18_500.0,
        "P50_Cumulative_Project_Profit": 18_500.0,
        "P90_Cumulative_Project_Profit": 18_500.0,
        "P90_Final_Cash": 18_500.0,
        "P90_Termination_Count": 1.0,
        "P90_Held_Assets": 1.0,
    }


def _accepted_point(n: int, p50: float):
    return {
        "n": n,
        "gate_a": {"status": "PASS", "stable": True},
        "gate_b": {"status": "ACCEPTED_TIME_UNIFORM_CS", "stable": True},
        "statistical_inference": {"status": "ACCEPTED"},
        "reference_indicators": {
            "acceptance_status": "ACCEPTED",
            "point_precision_pass": True,
            "indicators": {
                "P50_Cumulative_Project_Profit": {"point_estimate": p50},
                "Probability_of_Accounting_Loss": {
                    "point_estimate": 0.02,
                    "adjacent_change_pass": True,
                },
            },
        },
    }


def test_stopping_window_requires_four_points_and_three_passed_transitions():
    history = [_accepted_point(300, 100), _accepted_point(600, 101), _accepted_point(1200, 101), _accepted_point(2400, 101)]
    assert not evaluate_stopping_window(history[:3])["stable"]
    for i in range(1, len(history)):
        history[i]["transition"] = {"status": "PASS", "p50_continuation_trigger": False}
    outcome = evaluate_stopping_window(history)
    assert outcome["stable"] is True
    assert outcome["window_n"] == [300, 600, 1200, 2400]
    assert outcome["points_required"] == 4
    assert outcome["transitions_required"] == 3


def test_stopping_window_fails_closed_for_unaccepted_gate_or_missing_transition():
    history = [_accepted_point(300, 100), _accepted_point(600, 101), _accepted_point(1200, 101), _accepted_point(2400, 101)]
    for i in range(1, len(history)):
        history[i]["transition"] = {"status": "PASS", "p50_continuation_trigger": False}
    history[-1]["statistical_inference"]["status"] = "BLOCKED"
    outcome = evaluate_stopping_window(history)
    assert outcome["stable"] is False
    assert "ONE_OR_MORE_CHECKPOINT_COMPONENTS_NOT_ACCEPTED" in outcome["blockers"]


def test_p50_trigger_above_five_percent_requires_2400_without_erasing_history():
    previous = _accepted_point(300, 100.0)
    current = _accepted_point(600, 106.0)
    transition = evaluate_adjacent_transition(previous, current)
    assert transition["p50_continuation_trigger"] is True
    assert transition["minimum_required_n"] == 2400
    assert transition["status"] == "PASS"


def test_p50_trigger_is_strictly_greater_than_five_percent():
    previous = _accepted_point(300, 100.0)
    current = _accepted_point(600, 105.0)
    transition = evaluate_adjacent_transition(previous, current)
    assert transition["p50_continuation_trigger"] is False


def test_missing_previous_checkpoint_blocks_adjacent_transition():
    current = _accepted_point(300, 100.0)
    result = evaluate_adjacent_transition(None, current)
    assert result["status"] == "NOT_APPLICABLE"
    assert result["blockers"] == ["NO_PREVIOUS_CHECKPOINT"]


def test_confidence_sequence_validation_rejects_invalid_inputs():
    with pytest.raises(ValueError):
        fixed_quantile_confidence_sequence([1, 2], 1.0)
    with pytest.raises(ValueError):
        fixed_quantile_confidence_sequence([float("nan")], 0.5)
    with pytest.raises(ValueError):
        bernoulli_mean_confidence_sequence(2, 1)
