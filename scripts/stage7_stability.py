from __future__ import annotations

from typing import Any

STABILITY_METRICS = (
    "final_net_project_equity",
    "partner1_final_entitlement",
    "partner2_final_entitlement",
)

def _relative_limit(old_value: float, relative_epsilon: float, absolute_epsilon: float) -> float:
    return max(absolute_epsilon, relative_epsilon * abs(old_value))

def _stable_delta(old_value: float, new_value: float, relative_epsilon: float, absolute_epsilon: float) -> tuple[bool, float, float, float]:
    delta = abs(new_value - old_value)
    limit = _relative_limit(old_value, relative_epsilon, absolute_epsilon)
    relative_delta = delta / abs(old_value) if old_value != 0 else float('inf')
    return delta < limit, delta, limit, relative_delta

def evaluate_gate_a(*, previous_n: int | None, previous_metrics: dict[str, dict[str, Any]] | None, current_n: int, current_metrics: dict[str, dict[str, Any]], escalation_step: int, relative_epsilon: float, absolute_epsilon: float) -> dict[str, Any]:
    if previous_n is None or previous_metrics is None:
        return {
            "checked": False,
            "stable": False,
            "previous_n": previous_n,
            "current_n": current_n,
            "expected_current_n": None if previous_n is None else previous_n + escalation_step,
            "reason": "no previous stability point",
            "metrics": {},
        }
    expected_n = previous_n + escalation_step
    if current_n != expected_n:
        return {
            "checked": False,
            "stable": False,
            "previous_n": previous_n,
            "current_n": current_n,
            "expected_current_n": expected_n,
            "reason": "current n is not previous n plus escalation step",
            "metrics": {},
        }
    metric_payload: dict[str, dict[str, Any]] = {}
    all_stable = True
    for name in STABILITY_METRICS:
        old_mean = float(previous_metrics[name]["mean"])
        new_mean = float(current_metrics[name]["mean"])
        stable, delta, limit, relative_delta = _stable_delta(old_mean, new_mean, relative_epsilon, absolute_epsilon)
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
