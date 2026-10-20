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


def _stable_checkpoint(n: int, *, gate_a: bool = True, gate_b: bool = True) -> dict:
    return {
        "n": n,
        "gate_a": {
            "status": "PASS" if gate_a else "FAIL",
            "checked": gate_a,
            "stable": gate_a,
        },
        "gate_b": {"checked": gate_b, "stable": gate_b},
    }


def test_three_checkpoint_points_are_not_three_transitions() -> None:
    from scripts.stage7_stability import has_required_stability_window

    history = [_stable_checkpoint(n) for n in (300, 600, 1200)]
    assert has_required_stability_window(history) is False


def test_four_adjacent_doubling_points_satisfy_three_transition_window() -> None:
    from scripts.stage7_stability import has_required_stability_window

    history = [_stable_checkpoint(n) for n in (300, 600, 1200, 2400)]
    assert has_required_stability_window(history) is True


def test_non_adjacent_or_non_doubling_points_fail_closed() -> None:
    from scripts.stage7_stability import has_required_stability_window

    history = [_stable_checkpoint(n) for n in (300, 600, 1200, 4800)]
    assert has_required_stability_window(history) is False


def test_stability_constants_express_three_transitions_and_four_points() -> None:
    assert constants.STABILITY_CONSECUTIVE_TRANSITIONS_REQUIRED == 3
    assert constants.STABILITY_CONSECUTIVE_CHECKS_REQUIRED == 4


def test_failed_point_keeps_window_blocked_until_three_new_transitions_pass() -> None:
    from scripts.stage7_stability import has_required_stability_window

    history = [
        _stable_checkpoint(300),
        _stable_checkpoint(600, gate_b=False),
        _stable_checkpoint(1200),
        _stable_checkpoint(2400),
    ]
    assert has_required_stability_window(history) is False

    history.append(_stable_checkpoint(4800))
    assert has_required_stability_window(history) is False

    history.append(_stable_checkpoint(9600))
    assert has_required_stability_window(history) is True
