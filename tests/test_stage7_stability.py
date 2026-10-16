from __future__ import annotations

import pytest

from scripts.stage7_stability import (
    evaluate_p50_transition,
    hydrate_p50_history,
    p50_history_ready,
    p50_requires_n2400,
)


@pytest.mark.parametrize(
    ("previous", "current", "status", "requires"),
    [
        (100.0, 105.0, "PASS", False),       # exactly 5% is not over the threshold
        (100.0, 105.0001, "CONTINUE_N2400", True),
        (100.0, 95.0, "PASS", False),
        (100.0, 94.99, "CONTINUE_N2400", True),
    ],
)
def test_p50_threshold_is_strictly_greater_than_five_percent(
    previous: float, current: float, status: str, requires: bool
) -> None:
    result = evaluate_p50_transition(
        previous_n=300, previous_p50=previous,
        current_n=600, current_p50=current,
    )
    assert result["checked"] is True
    assert result["status"] == status
    assert result["requires_n2400"] is requires


@pytest.mark.parametrize(
    ("current", "status", "requires"),
    [
        (0.999999, "PASS", False),
        (1.0, "CONTINUE_N2400", True),
        (-1.0, "CONTINUE_N2400", True),
    ],
)
def test_p50_near_zero_uses_absolute_one_unit_rule(
    current: float, status: str, requires: bool
) -> None:
    result = evaluate_p50_transition(
        previous_n=300, previous_p50=0.0,
        current_n=600, current_p50=current,
    )
    assert result["status"] == status
    assert result["requires_n2400"] is requires
    assert result["change_percent"] is None


def test_p50_transition_fails_closed_when_values_are_missing() -> None:
    result = evaluate_p50_transition(
        previous_n=300, previous_p50=None,
        current_n=600, current_p50=5.0,
    )
    assert result["checked"] is False
    assert result["status"] == "BLOCKED"
    assert result["stable"] is False


def test_p50_history_hydrates_adjacent_checkpoint_values_and_triggers() -> None:
    history = [
        {"n": 300, "metrics": {}},
        {"n": 600, "metrics": {}},
        {"n": 1200, "metrics": {}},
    ]
    hydrated = hydrate_p50_history(history, {300: 100.0, 600: 110.0, 1200: 110.0})
    assert p50_history_ready(hydrated, 1200) is True
    assert hydrated[1]["p50_transition"]["change_percent"] == pytest.approx(10.0)
    assert hydrated[1]["p50_transition"]["requires_n2400"] is True
    assert hydrated[2]["p50_transition"]["requires_n2400"] is False
    assert p50_requires_n2400(hydrated) is True


def test_p50_history_is_blocked_if_a_required_point_is_missing() -> None:
    history = [{"n": 300, "metrics": {}}]
    hydrated = hydrate_p50_history(history, {300: 100.0})
    assert p50_history_ready(hydrated, 600) is False
