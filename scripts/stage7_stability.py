from __future__ import annotations

from typing import Any

import constants

STABILITY_METRICS = (
    "final_net_project_equity",
    "partner1_final_entitlement",
    "partner2_final_entitlement",
)


def is_statistical_checkpoint(n: int) -> bool:
    """Return whether N is on the approved 300, 600, 1200, ... schedule."""
    if n < constants.STATISTICAL_CHECK_START_N:
        return False
    expected = constants.STATISTICAL_CHECK_START_N
    while expected < n:
        expected *= constants.STATISTICAL_ESCALATION_MULTIPLIER
    return expected == n


def next_statistical_checkpoint(completed_trials: int) -> int:
    """Return the first approved statistical checkpoint greater than completed N."""
    if completed_trials < 0:
        raise ValueError("completed_trials must be non-negative")
    target = constants.STATISTICAL_CHECK_START_N
    while target <= completed_trials:
        target *= constants.STATISTICAL_ESCALATION_MULTIPLIER
    return target


def filter_statistical_history(
    history: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[int | None]]:
    """Keep valid doubling checkpoints and identify legacy intermediate points.

    This does not mutate the input history. Malformed ordering or duplicate N values
    fail closed instead of being silently normalized.
    """
    kept: list[dict[str, Any]] = []
    discarded: list[int | None] = []
    seen: set[int] = set()
    last_seen: int | None = None

    for item in history:
        raw_n = item.get("n")
        try:
            n = int(raw_n)
        except (TypeError, ValueError) as exc:
            raise ValueError("stability history contains a missing or invalid N") from exc

        if n in seen:
            raise ValueError(f"duplicate stability-history N={n}")
        seen.add(n)

        if last_seen is not None and n < last_seen:
            raise ValueError("stability history is not ordered by increasing N")
        last_seen = n

        if is_statistical_checkpoint(n):
            kept.append(item)
        else:
            discarded.append(n)

    return kept, discarded


def _relative_limit(
    old_value: float,
    relative_epsilon: float,
    absolute_epsilon: float,
) -> float:
    return max(absolute_epsilon, relative_epsilon * abs(old_value))


def _stable_delta(
    old_value: float,
    new_value: float,
    relative_epsilon: float,
    absolute_epsilon: float,
) -> tuple[bool, float, float, float]:
    delta = abs(new_value - old_value)
    limit = _relative_limit(old_value, relative_epsilon, absolute_epsilon)
    relative_delta = delta / abs(old_value) if old_value != 0 else float("inf")
    return delta < limit, delta, limit, relative_delta


def evaluate_gate_a(
    *,
    previous_n: int | None,
    previous_metrics: dict[str, dict[str, Any]] | None,
    current_n: int,
    current_metrics: dict[str, dict[str, Any]],
    escalation_multiplier: int,
    relative_epsilon: float,
    absolute_epsilon: float,
) -> dict[str, Any]:
    if escalation_multiplier != constants.STATISTICAL_ESCALATION_MULTIPLIER:
        raise ValueError("escalation_multiplier differs from approved policy")

    if previous_n is None or previous_metrics is None:
        return {
            "checked": False,
            "stable": False,
            "previous_n": previous_n,
            "current_n": current_n,
            "expected_current_n": None,
            "reason": "no previous stability point",
            "metrics": {},
        }

    if not is_statistical_checkpoint(previous_n):
        return {
            "checked": False,
            "stable": False,
            "previous_n": previous_n,
            "current_n": current_n,
            "expected_current_n": next_statistical_checkpoint(previous_n),
            "reason": "previous N is not an approved statistical checkpoint",
            "metrics": {},
        }

    expected_n = previous_n * escalation_multiplier
    if current_n != expected_n:
        return {
            "checked": False,
            "stable": False,
            "previous_n": previous_n,
            "current_n": current_n,
            "expected_current_n": expected_n,
            "reason": "current N is not previous N multiplied by escalation multiplier",
            "metrics": {},
        }

    metric_payload: dict[str, dict[str, Any]] = {}
    all_stable = True
    for name in STABILITY_METRICS:
        old_mean = float(previous_metrics[name]["mean"])
        new_mean = float(current_metrics[name]["mean"])
        stable, delta, limit, relative_delta = _stable_delta(
            old_mean, new_mean, relative_epsilon, absolute_epsilon
        )
        metric_payload[name] = {
            "previous_mean": old_mean,
            "current_mean": new_mean,
            "absolute_change": delta,
            "relative_change": relative_delta,
            "limit": limit,
            "stable": stable,
        }
        all_stable = all_stable and stable

    return {
        "checked": True,
        "stable": all_stable,
        "previous_n": previous_n,
        "current_n": current_n,
        "expected_current_n": expected_n,
        "metrics": metric_payload,
    }


def evaluate_gate_b(current_metrics: dict[str, dict[str, Any]]) -> dict[str, Any]:
    metric_payload = {}
    all_stable = True
    for name in STABILITY_METRICS:
        stable = bool(current_metrics[name]["stable"])
        metric_payload[name] = {"stable": stable}
        all_stable = all_stable and stable
    return {
        "checked": True,
        "stable": all_stable,
        "metrics": metric_payload,
    }
