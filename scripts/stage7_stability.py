from __future__ import annotations

from typing import Any

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
        if type(raw_n) is not int:
            raise ValueError(
                "stability history N must be an integer; "
                "booleans, strings, floats, and missing values are invalid"
            )
        n = raw_n

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

def has_successful_adjacent_transition_window(
    history: list[dict[str, Any]],
    *,
    required_transitions: int | None = None,
    required_points: int | None = None,
) -> bool:
    """Require four cumulative checkpoint points to evidence three successful adjacent transitions.

    The first point is a baseline, not itself a transition. Every point in the
    window must have exact Gate A and Gate B PASS evidence, and each later Gate A
    record must explicitly bind the prior and current checkpoint N values.
    """
    transitions = (
        constants.STABILITY_CONSECUTIVE_CHECKS_REQUIRED
        if required_transitions is None
        else required_transitions
    )
    points = (
        constants.STABILITY_CUMULATIVE_CHECKPOINTS_REQUIRED
        if required_points is None
        else required_points
    )
    if (
        type(transitions) is not int
        or type(points) is not int
        or transitions < 1
        or points != transitions + 1
    ):
        return False
    if len(history) < points:
        return False

    window = history[-points:]
    for item in window:
        n = item.get("n")
        if type(n) is not int or not is_statistical_checkpoint(n):
            return False
        gate_a = item.get("gate_a")
        gate_b = item.get("gate_b")
        if not isinstance(gate_a, dict) or not isinstance(gate_b, dict):
            return False
        if (
            gate_a.get("status") != "PASS"
            or gate_a.get("checked") is not True
            or gate_a.get("stable") is not True
            or gate_b.get("stable") is not True
        ):
            return False

    for previous, current in zip(window, window[1:]):
        previous_n = previous["n"]
        current_n = current["n"]
        gate_a = current["gate_a"]
        if current_n != previous_n * STATISTICAL_ESCALATION_MULTIPLIER:
            return False
        if gate_a.get("previous_n") != previous_n or gate_a.get("current_n") != current_n:
            return False
    return True
