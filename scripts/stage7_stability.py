from __future__ import annotations

from typing import Any

import math
import constants
import re

STATISTICAL_ESCALATION_POLICY_ID = "DOUBLING_FROM_300_V1"
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



P50_CHECKPOINTS = (300, 600, 1200)
P50_CHANGE_THRESHOLD_PERCENT = 5.0
P50_REFERENCE_EPSILON = 1e-6
P50_ABSOLUTE_EPSILON = 1.0


def evaluate_p50_transition(
    *,
    previous_n: int,
    previous_p50: float | None,
    current_n: int,
    current_p50: float | None,
    reference_epsilon: float = P50_REFERENCE_EPSILON,
    absolute_epsilon: float = P50_ABSOLUTE_EPSILON,
) -> dict[str, Any]:
    """Apply D-2026-10-12-01's adjacent-checkpoint P50 continuation rule."""
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
            "reason": "P50 continuation rule only compares 300->600 and 600->1200",
        }
    try:
        previous_value = float(previous_p50)  # type: ignore[arg-type]
        current_value = float(current_p50)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return {
            **base,
            "status": "BLOCKED",
            "reason": "required P50 checkpoint value is missing or non-numeric",
        }
    if not math.isfinite(previous_value) or not math.isfinite(current_value):
        return {
            **base,
            "status": "BLOCKED",
            "reason": "required P50 checkpoint value is not finite",
        }

    absolute_change = abs(current_value - previous_value)
    if abs(previous_value) < reference_epsilon:
        requires_continuation = absolute_change >= absolute_epsilon
        return {
            **base,
            "checked": True,
            "stable": not requires_continuation,
            "requires_n2400": requires_continuation,
            "absolute_change": absolute_change,
            "reason": (
                "near-zero prior P50 requires continuation when absolute change is >= 1 currency unit"
                if requires_continuation
                else "near-zero prior P50 absolute change is below 1 currency unit"
            ),
            "status": "CONTINUE_N2400" if requires_continuation else "PASS",
        }

    change_percent = 100.0 * absolute_change / abs(previous_value)
    requires_continuation = change_percent > P50_CHANGE_THRESHOLD_PERCENT
    return {
        **base,
        "checked": True,
        "stable": not requires_continuation,
        "requires_n2400": requires_continuation,
        "change_percent": change_percent,
        "absolute_change": absolute_change,
        "status": "CONTINUE_N2400" if requires_continuation else "PASS",
        "reason": (
            "adjacent-checkpoint P50 change is strictly greater than 5%"
            if requires_continuation
            else "adjacent-checkpoint P50 change does not exceed 5%"
        ),
    }


def hydrate_p50_history(
    history: list[dict[str, Any]],
    p50_values: dict[int, float],
) -> list[dict[str, Any]]:
    """Attach reproducible P50 and transition evidence to verified checkpoint rows."""
    points: dict[int, dict[str, Any]] = {}
    for point in history:
        n = int(point["n"])
        if n in points:
            raise ValueError(f"duplicate stability-history N={n}")
        points[n] = point
        if n in p50_values:
            point["p50_final_net_project_equity"] = float(p50_values[n])

    for n in P50_CHECKPOINTS:
        point = points.get(n)
        if point is None:
            continue
        current_p50 = point.get("p50_final_net_project_equity")
        if n == 300:
            try:
                valid_baseline = math.isfinite(float(current_p50))
            except (TypeError, ValueError):
                valid_baseline = False
            point["p50_transition"] = {
                "metric": "final_net_project_equity",
                "previous_n": None,
                "current_n": 300,
                "checked": False,
                "stable": valid_baseline,
                "requires_n2400": False,
                "status": "BASELINE" if valid_baseline else "BLOCKED",
                "reason": None if valid_baseline else "N=300 P50 baseline is missing or non-finite",
            }
        else:
            previous = points.get(n // 2)
            previous_p50 = (
                previous.get("p50_final_net_project_equity")
                if previous is not None
                else None
            )
            point["p50_transition"] = evaluate_p50_transition(
                previous_n=n // 2,
                previous_p50=previous_p50,
                current_n=n,
                current_p50=current_p50,
            )
    return history


def p50_history_ready(history: list[dict[str, Any]], completed_n: int) -> bool:
    """Fail closed if any required P50 checkpoint/transition evidence is absent."""
    points = {int(point.get("n", -1)): point for point in history}
    for n in P50_CHECKPOINTS:
        if completed_n < n:
            continue
        point = points.get(n)
        if point is None:
            return False
        try:
            value = float(point.get("p50_final_net_project_equity"))
        except (TypeError, ValueError):
            return False
        if not math.isfinite(value):
            return False
        transition = point.get("p50_transition") or {}
        if n == 300:
            if transition.get("status") != "BASELINE":
                return False
        elif (
            transition.get("checked") is not True
            or transition.get("status") not in ("PASS", "CONTINUE_N2400")
        ):
            return False
    return True


def p50_requires_n2400(history: list[dict[str, Any]]) -> bool:
    """Whether either approved adjacent P50 comparison requires continuing to N=2400."""
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
