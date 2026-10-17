from __future__ import annotations

import math
import re
from typing import Any

import numpy as np

import constants

STATISTICAL_ESCALATION_POLICY_ID = "DOUBLING_FROM_300_FIRST_PASSING_V2"
STATISTICAL_ESCALATION_MULTIPLIER = 2

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
        expected *= STATISTICAL_ESCALATION_MULTIPLIER
    return expected == n


def next_statistical_checkpoint(completed_trials: int) -> int:
    """Return the first approved statistical checkpoint greater than completed N."""
    if completed_trials < 0:
        raise ValueError("completed_trials must be non-negative")
    target = constants.STATISTICAL_CHECK_START_N
    while target <= completed_trials:
        target *= STATISTICAL_ESCALATION_MULTIPLIER
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



REFERENCE_STABILITY_METRICS = constants.REFERENCE_STABILITY_INDICATORS
REFERENCE_STABILITY_RELATIVE_TOLERANCE = constants.REFERENCE_STABILITY_RELATIVE_TOLERANCE
P50_CHECKPOINTS = (300, 600, 1200)
P50_CHANGE_THRESHOLD_PERCENT = 5.0
P50_REFERENCE_EPSILON = constants.REFERENCE_EPSILON
P50_ABSOLUTE_EPSILON = float(constants.ABSOLUTE_EPSILON)


def summarize_reference_stability_metrics(
    results: list[Any],
) -> dict[str, float]:
    """Summarize all seven §2.5 indicators from cumulative trial IDs 1..N.

    Quantiles use NumPy's linear method. These reference indicators are separate
    from Gate A's exact fingerprint equality and Gate B's Student-t confidence
    interval checks.
    """
    if not results:
        raise ValueError("§2.5 metrics require at least one completed trial")

    profits = np.asarray(
        [getattr(item, "cumulative_project_profit") for item in results],
        dtype=np.float64,
    )
    cash = np.asarray(
        [getattr(item, "final_cash") for item in results],
        dtype=np.float64,
    )
    terminations = np.asarray(
        [getattr(item, "termination_count") for item in results],
        dtype=np.float64,
    )
    held_assets = np.asarray(
        [getattr(item, "held_assets") for item in results],
        dtype=np.float64,
    )
    arrays = {
        "Cumulative_Project_Profit": profits,
        "Final_Cash": cash,
        "Termination_Count": terminations,
        "Held_Assets": held_assets,
    }
    for field, values in arrays.items():
        if values.size != len(results) or not np.isfinite(values).all():
            raise ValueError(f"§2.5 input {field} is incomplete or non-finite")

    summary = {
        "P10_Cumulative_Project_Profit": float(np.quantile(profits, 0.10, method="linear")),
        "P50_Cumulative_Project_Profit": float(np.quantile(profits, 0.50, method="linear")),
        "P90_Cumulative_Project_Profit": float(np.quantile(profits, 0.90, method="linear")),
        "P90_Final_Cash": float(np.quantile(cash, 0.90, method="linear")),
        "Probability_of_Accounting_Loss": float(np.mean(profits < 0.0)),
        "P90_Termination_Count": float(np.quantile(terminations, 0.90, method="linear")),
        "P90_Held_Assets": float(np.quantile(held_assets, 0.90, method="linear")),
    }
    if tuple(summary) != tuple(REFERENCE_STABILITY_METRICS):
        raise AssertionError("§2.5 metric names/order differ from constants")
    if not all(math.isfinite(value) for value in summary.values()):
        raise ValueError("§2.5 result contains a non-finite metric")
    return summary


def evaluate_reference_stability_transition(
    *,
    previous_n: int | None,
    previous_metrics: dict[str, Any] | None,
    current_n: int,
    current_metrics: dict[str, Any],
    relative_tolerance: float = REFERENCE_STABILITY_RELATIVE_TOLERANCE,
    reference_epsilon: float = constants.REFERENCE_EPSILON,
    absolute_epsilon: float = float(constants.ABSOLUTE_EPSILON),
) -> dict[str, Any]:
    """Evaluate every §2.5 metric together for one adjacent per-scenario transition.

    N=300 is mandatory coverage and a recorded metric baseline only; it is not an
    eligible stability transition. The first eligible comparison is 300 -> 600.
    """
    base: dict[str, Any] = {
        "previous_n": previous_n,
        "current_n": current_n,
        "metrics": {},
        "checked": False,
        "stable": False,
    }
    if current_n == 300 and previous_n is None:
        try:
            valid_baseline = all(
                math.isfinite(float(current_metrics[name]))
                for name in REFERENCE_STABILITY_METRICS
            )
        except (KeyError, TypeError, ValueError):
            valid_baseline = False
        return {
            **base,
            "checked": False,
            "stable": False,
            "status": "COVERAGE_ONLY" if valid_baseline else "BLOCKED",
            "reason": (
                "N=300 is mandatory coverage only; first §2.5 comparison is 300->600"
                if valid_baseline
                else "N=300 baseline is missing or contains non-finite §2.5 metrics"
            ),
        }

    if previous_n is None or previous_metrics is None:
        return {
            **base,
            "status": "BLOCKED",
            "reason": "previous approved §2.5 checkpoint is missing",
        }
    if not is_statistical_checkpoint(previous_n) or current_n != (
        previous_n * STATISTICAL_ESCALATION_MULTIPLIER
    ):
        return {
            **base,
            "status": "BLOCKED",
            "expected_current_n": previous_n * STATISTICAL_ESCALATION_MULTIPLIER,
            "reason": "§2.5 comparison must use adjacent approved doubling checkpoints",
        }

    details: dict[str, Any] = {}
    all_stable = True
    for name in REFERENCE_STABILITY_METRICS:
        try:
            old_value = float(previous_metrics[name])
            new_value = float(current_metrics[name])
        except (KeyError, TypeError, ValueError):
            return {
                **base,
                "status": "BLOCKED",
                "reason": f"required §2.5 metric {name} is missing or non-numeric",
                "metrics": details,
            }
        if not math.isfinite(old_value) or not math.isfinite(new_value):
            return {
                **base,
                "status": "BLOCKED",
                "reason": f"required §2.5 metric {name} is non-finite",
                "metrics": details,
            }
        absolute_change = abs(new_value - old_value)
        if abs(old_value) < reference_epsilon:
            stable = absolute_change < absolute_epsilon
            relative_change = None
            rule = "absolute_near_zero"
        else:
            relative_change = absolute_change / abs(old_value)
            stable = relative_change < relative_tolerance
            rule = "relative"
        details[name] = {
            "previous_value": old_value,
            "current_value": new_value,
            "absolute_change": absolute_change,
            "relative_change": relative_change,
            "rule": rule,
            "stable": stable,
        }
        all_stable = all_stable and stable

    return {
        **base,
        "checked": True,
        "stable": all_stable,
        "status": "PASS" if all_stable else "FAIL",
        "relative_tolerance": relative_tolerance,
        "reference_epsilon": reference_epsilon,
        "absolute_epsilon": absolute_epsilon,
        "metrics": details,
    }


def evaluate_p50_transition(
    *,
    previous_n: int,
    previous_p50: float | None,
    current_n: int,
    current_p50: float | None,
    reference_epsilon: float = P50_REFERENCE_EPSILON,
    absolute_epsilon: float = P50_ABSOLUTE_EPSILON,
) -> dict[str, Any]:
    """Apply approved D-2026-10-12-01's P50 continuation trigger, separately."""
    base: dict[str, Any] = {
        "metric": "final_net_project_equity",
        "previous_n": previous_n,
        "current_n": current_n,
        "threshold_percent": P50_CHANGE_THRESHOLD_PERCENT,
        "checked": False,
        "stable": False,
        "requires_n2400": False,
        "change_percent": None,
        "absolute_change": None,
    }
    if (previous_n, current_n) not in ((300, 600), (600, 1200)):
        return {
            **base,
            "status": "NOT_APPLICABLE",
            "stable": True,
            "reason": "approved P50 continuation rule compares 300->600 and 600->1200",
        }
    try:
        old_value = float(previous_p50)  # type: ignore[arg-type]
        new_value = float(current_p50)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return {
            **base,
            "status": "BLOCKED",
            "reason": "required adjacent P50 value is missing or non-numeric",
        }
    if not math.isfinite(old_value) or not math.isfinite(new_value):
        return {
            **base,
            "status": "BLOCKED",
            "reason": "required adjacent P50 value is non-finite",
        }
    absolute_change = abs(new_value - old_value)
    if abs(old_value) < reference_epsilon:
        requires_n2400 = absolute_change >= absolute_epsilon
        return {
            **base,
            "checked": True,
            "stable": not requires_n2400,
            "requires_n2400": requires_n2400,
            "absolute_change": absolute_change,
            "status": "CONTINUE_N2400" if requires_n2400 else "PASS",
            "reason": "near-zero P50 uses the approved absolute one-unit rule",
        }
    change_percent = 100.0 * absolute_change / abs(old_value)
    requires_n2400 = change_percent > P50_CHANGE_THRESHOLD_PERCENT
    return {
        **base,
        "checked": True,
        "stable": not requires_n2400,
        "requires_n2400": requires_n2400,
        "change_percent": change_percent,
        "absolute_change": absolute_change,
        "status": "CONTINUE_N2400" if requires_n2400 else "PASS",
        "reason": (
            "adjacent P50 change is strictly greater than 5%"
            if requires_n2400
            else "adjacent P50 change does not exceed 5%"
        ),
    }


def p50_requires_n2400(history: list[dict[str, Any]]) -> bool:
    """Keep the approved P50 escalation requirement in force through its N=2400 check."""
    return any(
        bool((point.get("p50_transition") or {}).get("requires_n2400"))
        for point in history
        if int(point.get("n", -1)) in (600, 1200)
    )


_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def evaluate_gate_a(
    *,
    previous_n: int | None,
    previous_metrics: dict[str, dict[str, Any]] | None,
    current_n: int,
    current_metrics: dict[str, dict[str, Any]],
    escalation_multiplier: int,
    relative_epsilon: float,
    absolute_epsilon: float,
    expected_golden_fingerprint_sha256: str | None = None,
    actual_fingerprint_sha256: str | None = None,
    golden_reference_id: str | None = None,
    expected_source_sha: str | None = None,
    actual_source_sha: str | None = None,
) -> dict[str, Any]:
    """Require exact approved-golden equality; never substitute mean deltas.

    The relative/absolute epsilon parameters remain in the call contract for
    compatibility with the Stage 7 authoring layer, but Gate A does not use them.
    Gate B owns confidence-interval tolerances. Runtime callers that do not supply
    an approved golden identity are explicitly BLOCKED rather than implicitly PASS.
    """
    del relative_epsilon, absolute_epsilon, current_metrics

    if escalation_multiplier != STATISTICAL_ESCALATION_MULTIPLIER:
        raise ValueError("escalation_multiplier differs from approved policy")

    expected_n = previous_n * escalation_multiplier if previous_n is not None else current_n
    base = {
        "previous_n": previous_n,
        "current_n": current_n,
        "expected_current_n": expected_n,
        "metrics": {},
    }

    if previous_n is None:
        if not is_statistical_checkpoint(current_n):
            return {
                **base,
                "checked": False,
                "stable": False,
                "status": "BLOCKED",
                "reason": "current N is not an approved statistical checkpoint",
            }
    else:
        if previous_metrics is None:
            return {
                **base,
                "checked": False,
                "stable": False,
                "status": "BLOCKED",
                "reason": "previous checkpoint metrics are missing",
            }
        if not is_statistical_checkpoint(previous_n):
            return {
                **base,
                "checked": False,
                "stable": False,
                "status": "BLOCKED",
                "expected_current_n": next_statistical_checkpoint(previous_n),
                "reason": "previous N is not an approved statistical checkpoint",
            }
        if current_n != expected_n:
            return {
                **base,
                "checked": False,
                "stable": False,
                "status": "BLOCKED",
                "reason": "current N is not previous N multiplied by escalation multiplier",
            }

    evidence = (
        expected_golden_fingerprint_sha256,
        actual_fingerprint_sha256,
        golden_reference_id,
        expected_source_sha,
        actual_source_sha,
    )
    if any(not isinstance(value, str) or not value.strip() for value in evidence):
        return {
            **base,
            "checked": False,
            "stable": False,
            "status": "BLOCKED",
            "reason": "approved exact-golden fingerprint and source identity evidence not supplied",
        }

    if not _SHA256_RE.fullmatch(expected_golden_fingerprint_sha256 or ""):
        return {
            **base, "checked": True, "stable": False, "status": "FAIL",
            "reason": "approved golden fingerprint is not a canonical lowercase SHA-256",
        }
    if not _SHA256_RE.fullmatch(actual_fingerprint_sha256 or ""):
        return {
            **base, "checked": True, "stable": False, "status": "FAIL",
            "reason": "actual fingerprint is not a canonical lowercase SHA-256",
        }
    if not _COMMIT_SHA_RE.fullmatch(expected_source_sha or ""):
        return {
            **base, "checked": True, "stable": False, "status": "FAIL",
            "reason": "golden source SHA is not a canonical lowercase commit SHA",
        }
    if not _COMMIT_SHA_RE.fullmatch(actual_source_sha or ""):
        return {
            **base, "checked": True, "stable": False, "status": "FAIL",
            "reason": "actual source SHA is not a canonical lowercase commit SHA",
        }
    if expected_source_sha != actual_source_sha:
        return {
            **base,
            "checked": True,
            "stable": False,
            "status": "FAIL",
            "reason": "golden and actual source identities differ",
            "golden_reference_id": golden_reference_id,
            "expected_source_sha": expected_source_sha,
            "actual_source_sha": actual_source_sha,
        }

    exact_match = expected_golden_fingerprint_sha256 == actual_fingerprint_sha256
    return {
        **base,
        "checked": True,
        "stable": exact_match,
        "status": "PASS" if exact_match else "FAIL",
        "golden_reference_id": golden_reference_id,
        "golden_fingerprint_sha256": expected_golden_fingerprint_sha256,
        "actual_fingerprint_sha256": actual_fingerprint_sha256,
        "expected_source_sha": expected_source_sha,
        "actual_source_sha": actual_source_sha,
        "reason": None if exact_match else "actual fingerprint differs from approved golden",
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
