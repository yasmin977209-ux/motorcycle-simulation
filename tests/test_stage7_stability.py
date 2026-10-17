from __future__ import annotations

from types import SimpleNamespace

import pytest

from scripts.stage7_stability import (
    evaluate_p50_transition,
    evaluate_reference_stability_transition,
    p50_requires_n2400,
    summarize_reference_stability_metrics,
)


def _trial(
    trial_id: int,
    *,
    profit: float = 100.0,
    cash: float = 200.0,
    terminations: float = 2.0,
    held_assets: float = 5.0,
    equity: float = 300.0,
) -> SimpleNamespace:
    return SimpleNamespace(
        trial_id=trial_id,
        cumulative_project_profit=profit,
        final_cash=cash,
        termination_count=terminations,
        held_assets=held_assets,
        final_net_project_equity=equity,
    )


def _seven(value: float = 100.0) -> dict[str, float]:
    return {
        "P10_Cumulative_Project_Profit": value,
        "P50_Cumulative_Project_Profit": value,
        "P90_Cumulative_Project_Profit": value,
        "P90_Final_Cash": value,
        "Probability_of_Accounting_Loss": value,
        "P90_Termination_Count": value,
        "P90_Held_Assets": value,
    }


def test_reference_summary_calculates_exact_seven_section_2_5_metrics() -> None:
    rows = [
        _trial(1, profit=-2, cash=10, terminations=0, held_assets=0),
        _trial(2, profit=0, cash=20, terminations=1, held_assets=2),
        _trial(3, profit=100, cash=30, terminations=2, held_assets=4),
    ]

    actual = summarize_reference_stability_metrics(rows)

    assert tuple(actual) == (
        "P10_Cumulative_Project_Profit",
        "P50_Cumulative_Project_Profit",
        "P90_Cumulative_Project_Profit",
        "P90_Final_Cash",
        "Probability_of_Accounting_Loss",
        "P90_Termination_Count",
        "P90_Held_Assets",
    )
    assert actual["P10_Cumulative_Project_Profit"] == pytest.approx(-1.6)
    assert actual["P50_Cumulative_Project_Profit"] == pytest.approx(0.0)
    assert actual["P90_Cumulative_Project_Profit"] == pytest.approx(80.0)
    assert actual["P90_Final_Cash"] == pytest.approx(28.0)
    assert actual["Probability_of_Accounting_Loss"] == pytest.approx(1.0 / 3.0)
    assert actual["P90_Termination_Count"] == pytest.approx(1.8)
    assert actual["P90_Held_Assets"] == pytest.approx(3.6)


def test_reference_summary_fails_closed_on_empty_or_nonfinite_data() -> None:
    with pytest.raises(ValueError, match="at least one"):
        summarize_reference_stability_metrics([])
    with pytest.raises(ValueError, match="non-finite"):
        summarize_reference_stability_metrics([_trial(1, cash=float("nan"))])


def test_n300_is_mandatory_coverage_not_a_stability_pass() -> None:
    result = evaluate_reference_stability_transition(
        previous_n=None,
        previous_metrics=None,
        current_n=300,
        current_metrics=_seven(),
    )
    assert result["status"] == "COVERAGE_ONLY"
    assert result["checked"] is False
    assert result["stable"] is False


def test_first_eligible_reference_transition_is_300_to_600() -> None:
    passed = evaluate_reference_stability_transition(
        previous_n=300,
        previous_metrics=_seven(),
        current_n=600,
        current_metrics=_seven(),
    )
    assert passed["status"] == "PASS"
    assert passed["checked"] is True
    assert passed["stable"] is True
    assert len(passed["metrics"]) == 7


def test_reference_transition_checks_all_metrics_and_threshold_is_strict() -> None:
    current = _seven()
    current["P90_Held_Assets"] = 101.0
    failed = evaluate_reference_stability_transition(
        previous_n=300,
        previous_metrics=_seven(),
        current_n=600,
        current_metrics=current,
    )
    assert failed["status"] == "FAIL"
    assert failed["stable"] is False
    assert failed["metrics"]["P90_Held_Assets"]["relative_change"] == pytest.approx(0.01)
    assert failed["metrics"]["P90_Held_Assets"]["stable"] is False


def test_reference_transition_uses_strict_absolute_rule_near_zero() -> None:
    previous = _seven()
    previous["Probability_of_Accounting_Loss"] = 0.0

    under_one = _seven()
    under_one["Probability_of_Accounting_Loss"] = 0.999
    passed = evaluate_reference_stability_transition(
        previous_n=300,
        previous_metrics=previous,
        current_n=600,
        current_metrics=under_one,
    )
    assert passed["status"] == "PASS"
    assert passed["metrics"]["Probability_of_Accounting_Loss"]["rule"] == "absolute_near_zero"

    exactly_one = _seven()
    exactly_one["Probability_of_Accounting_Loss"] = 1.0
    failed = evaluate_reference_stability_transition(
        previous_n=300,
        previous_metrics=previous,
        current_n=600,
        current_metrics=exactly_one,
    )
    assert failed["status"] == "FAIL"
    assert failed["metrics"]["Probability_of_Accounting_Loss"]["stable"] is False


@pytest.mark.parametrize(
    ("previous_n", "current_n", "previous_metrics", "current_metrics"),
    [
        (None, 600, None, _seven()),
        (300, 1200, _seven(), _seven()),
        (300, 600, None, _seven()),
        (300, 600, _seven(), {**_seven(), "P90_Held_Assets": float("inf")}),
    ],
)
def test_reference_transition_blocks_missing_or_skipped_comparisons(
    previous_n, current_n, previous_metrics, current_metrics
) -> None:
    if previous_n == 300 and current_n == 600 and previous_metrics is None:
        current_metrics = dict(current_metrics)
        current_metrics.pop("P90_Held_Assets")
    result = evaluate_reference_stability_transition(
        previous_n=previous_n,
        previous_metrics=previous_metrics,
        current_n=current_n,
        current_metrics=current_metrics,
    )
    assert result["status"] == "BLOCKED"
    assert result["stable"] is False


def test_p50_continuation_threshold_is_strictly_greater_than_five_percent() -> None:
    exactly_five = evaluate_p50_transition(
        previous_n=300, previous_p50=100.0,
        current_n=600, current_p50=105.0,
    )
    above_five = evaluate_p50_transition(
        previous_n=300, previous_p50=100.0,
        current_n=600, current_p50=105.0001,
    )
    assert exactly_five["status"] == "PASS"
    assert exactly_five["requires_n2400"] is False
    assert above_five["status"] == "CONTINUE_N2400"
    assert above_five["requires_n2400"] is True


def test_p50_near_zero_uses_one_unit_absolute_rule() -> None:
    stable = evaluate_p50_transition(
        previous_n=600, previous_p50=0.0,
        current_n=1200, current_p50=0.999,
    )
    continuation = evaluate_p50_transition(
        previous_n=600, previous_p50=0.0,
        current_n=1200, current_p50=1.0,
    )
    assert stable["status"] == "PASS"
    assert continuation["status"] == "CONTINUE_N2400"


def test_p50_continuation_remains_required_through_n2400_checkpoint() -> None:
    history = [
        {"n": 300, "p50_transition": {"status": "BASELINE", "requires_n2400": False}},
        {"n": 600, "p50_transition": {"status": "CONTINUE_N2400", "requires_n2400": True}},
        {"n": 1200, "p50_transition": {"status": "PASS", "requires_n2400": False}},
    ]
    assert p50_requires_n2400(history) is True
