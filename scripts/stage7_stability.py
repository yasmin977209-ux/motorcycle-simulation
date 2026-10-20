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


def ci_half_width_limit(mean: float) -> float:
    """Return the approved conditional absolute/relative Gate B threshold."""
    if abs(mean) < constants.REFERENCE_EPSILON:
        return float(constants.CI_ABSOLUTE_EPSILON)
    return float(constants.CI_RELATIVE_TOLERANCE * abs(mean))


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
    """Evaluate only explicit Boolean evidence; invalid values fail closed."""
    metric_payload = {}
    all_stable = True
    for name in STABILITY_METRICS:
        stable = current_metrics[name]["stable"]
        if type(stable) is not bool:
            raise TypeError(f"Gate B metric {name} stable must be a bool")
        metric_payload[name] = {"stable": stable}
        all_stable = all_stable and stable
    return {
        "checked": True,
        "stable": all_stable,
        "metrics": metric_payload,
    }
