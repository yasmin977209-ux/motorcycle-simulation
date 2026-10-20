from __future__ import annotations

from types import SimpleNamespace

import pytest

import constants
import run_batch
from scripts.stage7_stability import ci_half_width_limit


def _trial(value: float) -> SimpleNamespace:
    return SimpleNamespace(
        final_net_project_equity=value,
        partner1_final_entitlement=value,
        partner2_final_entitlement=value,
    )


def test_ci_limit_uses_relative_tolerance_away_from_zero() -> None:
    assert ci_half_width_limit(10.0) == pytest.approx(0.1)
    assert ci_half_width_limit(-10.0) == pytest.approx(0.1)


def test_ci_limit_uses_absolute_epsilon_strictly_inside_near_zero() -> None:
    assert ci_half_width_limit(constants.REFERENCE_EPSILON / 2) == float(
        constants.CI_ABSOLUTE_EPSILON
    )


def test_ci_limit_uses_relative_branch_at_exact_reference_epsilon() -> None:
    assert ci_half_width_limit(constants.REFERENCE_EPSILON) == pytest.approx(
        constants.CI_RELATIVE_TOLERANCE * constants.REFERENCE_EPSILON
    )


def test_metric_summary_uses_conditional_limit() -> None:
    summary = run_batch._metric_summary([_trial(10.0), _trial(10.0)])
    assert summary["final_net_project_equity"]["limit"] == pytest.approx(0.1)


def _gate_b_metrics(value: object = True) -> dict[str, dict[str, object]]:
    return {
        "final_net_project_equity": {"stable": value},
        "partner1_final_entitlement": {"stable": True},
        "partner2_final_entitlement": {"stable": True},
    }


def test_gate_b_accepts_explicit_boolean_evidence() -> None:
    result = run_batch.evaluate_gate_b(_gate_b_metrics(True))
    assert result["checked"] is True
    assert result["stable"] is True


def test_gate_b_rejects_truthy_string_false() -> None:
    with pytest.raises(TypeError, match="stable must be a bool"):
        run_batch.evaluate_gate_b(_gate_b_metrics("False"))
