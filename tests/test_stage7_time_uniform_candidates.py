from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from scripts.stage7_time_uniform_candidates import (
    adjacent_probability_change_pass,
    beta_binomial_mixture_confidence_sequence,
    bernoulli_precision_pass,
    checkpoint_alpha_spend,
    checkpoint_look_number,
    order_statistic_quantile_interval,
    quantile_precision_pass,
)


def test_checkpoint_grid_and_alpha_spending_are_normative() -> None:
    assert [checkpoint_look_number(n) for n in (300, 600, 1200, 2400, 4800)] == [1, 2, 3, 4, 5]
    assert checkpoint_alpha_spend(0.0025, 300) == pytest.approx(0.0025 / 2)
    assert checkpoint_alpha_spend(0.0025, 600) == pytest.approx(0.0025 / 6)
    assert checkpoint_alpha_spend(0.0025, 1200) == pytest.approx(0.0025 / 12)
    partial_spend = sum(checkpoint_alpha_spend(0.0025, n) for n in (300, 600, 1200, 2400, 4800))
    assert partial_spend < 0.0025


@pytest.mark.parametrize("n", [0, 299, 350, 400, 550, 1800, 2401, True, 300.0])
def test_checkpoint_look_rejects_nonpolicy_or_noninteger_n(n: object) -> None:
    with pytest.raises(ValueError, match="checkpoint grid"):
        checkpoint_look_number(n)  # type: ignore[arg-type]


def test_order_statistic_interval_is_finite_and_reports_checkpoint_spend() -> None:
    values = np.arange(1, 301, dtype=float)
    interval = order_statistic_quantile_interval(values, 0.9, checkpoint_n=300, alpha=0.0025)
    assert interval["method"] == "ORDER_STATISTIC_ALPHA_SPENDING_GRID_V1"
    assert interval["n"] == 300
    assert interval["look_number"] == 1
    assert interval["alpha_at_look"] == pytest.approx(0.00125)
    assert interval["lower"] <= interval["estimate"] <= interval["upper"]
    assert interval["finite_interval"] is True


def test_order_statistic_interval_fails_closed_on_mismatched_prefix_or_invalid_data() -> None:
    with pytest.raises(ValueError, match="complete prefix"):
        order_statistic_quantile_interval([1.0, 2.0], 0.5, checkpoint_n=300, alpha=0.0025)
    invalid = np.arange(1, 301, dtype=float)
    invalid[7] = np.nan
    with pytest.raises(ValueError, match="finite"):
        order_statistic_quantile_interval(invalid, 0.5, checkpoint_n=300, alpha=0.0025)
    with pytest.raises(ValueError, match="checkpoint grid"):
        order_statistic_quantile_interval(np.arange(400), 0.5, checkpoint_n=400, alpha=0.0025)


def test_quantile_precision_requires_complete_candidate_interval_and_strict_margin() -> None:
    interval = {
        "method": "ORDER_STATISTIC_ALPHA_SPENDING_GRID_V1",
        "finite_interval": True,
        "estimate": 10.0,
        "lower": 9.5,
        "upper": 10.5,
    }
    assert quantile_precision_pass(interval, 0.6) is True
    assert quantile_precision_pass(interval, 0.5) is False
    assert quantile_precision_pass({**interval, "lower": None}, 1.0) is False
    assert quantile_precision_pass({**interval, "lower": 10.5, "upper": 9.5}, 1.0) is False
    assert quantile_precision_pass({**interval, "finite_interval": False}, 1.0) is False
    assert quantile_precision_pass({**interval, "method": "other"}, 1.0) is False


def test_beta_binomial_mixture_sequence_handles_all_success_and_all_failure_edges() -> None:
    none = beta_binomial_mixture_confidence_sequence(0, 100, alpha=0.0025)
    all_ = beta_binomial_mixture_confidence_sequence(100, 100, alpha=0.0025)
    assert none["lower"] == 0.0
    assert 0.0 < none["upper"] < 1.0
    assert all_["upper"] == 1.0
    assert 0.0 < all_["lower"] < 1.0
    assert none["half_width"] < 1.0
    assert all_["half_width"] < 1.0


def test_beta_binomial_mixture_sequence_contains_sample_estimate_and_has_valid_order() -> None:
    interval = beta_binomial_mixture_confidence_sequence(50, 100, alpha=0.0025)
    assert interval["method"] == "BETA_BINOMIAL_MIXTURE_CS_V1"
    assert interval["empty_confidence_set"] is False
    assert interval["lower"] <= interval["estimate"] <= interval["upper"]
    assert 0.0 <= interval["lower"] <= interval["upper"] <= 1.0
    assert interval["half_width"] == pytest.approx((interval["upper"] - interval["lower"]) / 2)


def test_beta_mixture_confidence_endpoints_solve_the_likelihood_ratio_boundary() -> None:
    from scipy.special import betaln

    successes, n, alpha = 50, 100, 0.0025
    interval = beta_binomial_mixture_confidence_sequence(successes, n, alpha=alpha)
    log_marginal = float(betaln(successes + 1, n - successes + 1) - betaln(1, 1))
    threshold = log_marginal + math.log(alpha)

    def log_likelihood(p: float) -> float:
        return successes * math.log(p) + (n - successes) * math.log1p(-p)

    assert log_likelihood(interval["lower"]) == pytest.approx(threshold, abs=1e-10)
    assert log_likelihood(interval["upper"]) == pytest.approx(threshold, abs=1e-10)


def _valid_bernoulli_interval() -> dict[str, object]:
    return beta_binomial_mixture_confidence_sequence(50, 100, alpha=0.0025)


def test_bernoulli_precision_gate_validates_complete_interval_and_strict_width() -> None:
    valid = _valid_bernoulli_interval()
    assert bernoulli_precision_pass(valid, 0.5) is True
    assert bernoulli_precision_pass(valid, valid["half_width"]) is False
    assert bernoulli_precision_pass({**valid, "half_width": 0.0}, 0.005) is False
    assert bernoulli_precision_pass({**valid, "lower": None}, 0.5) is False
    assert bernoulli_precision_pass({**valid, "empty_confidence_set": True}, 0.5) is False
    assert bernoulli_precision_pass({**valid, "method": "other"}, 0.5) is False
    assert bernoulli_precision_pass({}, 0.005) is False


def test_adjacent_probability_change_is_strict_and_validates_inputs() -> None:
    assert adjacent_probability_change_pass(0.500, 0.504, 0.005) is True
    assert adjacent_probability_change_pass(0.500, 0.505, 0.005) is False
    assert adjacent_probability_change_pass(0.0, 1.0, 1.0) is False
    with pytest.raises(ValueError, match="between 0 and 1"):
        adjacent_probability_change_pass(-0.1, 0.5, 0.005)



def test_candidate_methods_do_not_open_the_production_execution_gate() -> None:
    contract_path = Path(__file__).resolve().parents[1] / "docs" / "stage7" / "statistical_execution_gate.json"
    gate = json.loads(contract_path.read_text(encoding="utf-8"))
    assert gate["status"] == "BLOCKED_FOR_IMPLEMENTATION"
    authorization = gate["execution_authorization"]
    assert authorization["production_trial_checkpoint_monte_carlo_allowed"] is False
    assert authorization["scenario_stability_declaration_allowed"] is False
    assert authorization["final_delivery_acceptance_allowed"] is False
    assert gate["component_status"]["section_2_5_quantiles"]["status"] == "CANDIDATE_METHOD_NOT_IMPLEMENTED"
    assert gate["component_status"]["probability_of_accounting_loss"]["status"] == "CANDIDATE_METHOD_NOT_IMPLEMENTED"
    assert gate["component_status"]["stopping_window"]["required_points"] == 4
    assert gate["component_status"]["stopping_window"]["required_successful_transitions"] == 3



def test_quantile_precision_rejects_nonfinite_or_boolean_values() -> None:
    valid = {
        "method": "ORDER_STATISTIC_ALPHA_SPENDING_GRID_V1",
        "finite_interval": True,
        "estimate": 0.5,
        "lower": 0.49,
        "upper": 0.51,
    }
    assert quantile_precision_pass({**valid, "estimate": True}, 0.5) is False
    assert quantile_precision_pass({**valid, "upper": math.inf}, 1.0) is False
