"""Fail-closed verification of independent S6 Gate A Golden fingerprint maps.

A candidate map is not accepted merely because its own manifest is internally valid.
The caller must supply a separate, immutable approval manifest binding that exact map
SHA-256 to the same source SHA, cohort, seed, model schema, scenario set, and trial range.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable

import constants
import monte_carlo

STOCHASTIC_GOLDEN_SCHEMA = "s6-independent-golden-map-v1"
APPROVED_GOLDEN_STATUS = "APPROVED_PRODUCTION_GOLDEN"
CANDIDATE_STATUS = "INDEPENDENT_GOLDEN_CANDIDATE_NOT_APPROVED"


class GoldenEvidenceError(RuntimeError):
    """Raised when Golden evidence is absent, incompatible, or incomplete."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")


def scenario_fingerprint_map_sha256(
    scenario_id: str, fingerprints: dict[str, str]
) -> str:
    try:
        ordered_ids = sorted((int(key) for key in fingerprints), key=int)
    except (TypeError, ValueError) as exc:
        raise GoldenEvidenceError("GOLDEN_TRIAL_ID_KEY_INVALID") from exc
    lines: list[str] = []
    for trial_id in ordered_ids:
        key = str(trial_id)
        fp = fingerprints.get(key)
        if not isinstance(fp, str) or len(fp) != 64 or any(
            char not in "0123456789abcdef" for char in fp
        ):
            raise GoldenEvidenceError(f"GOLDEN_FINANCIAL_FINGERPRINT_INVALID:{scenario_id}:{trial_id}")
        lines.append(f"{scenario_id}|{trial_id}|{fp}")
    return sha256_bytes(("\n".join(lines) + "\n").encode("utf-8"))


def expected_stochastic_scenarios() -> set[str]:
    return {
        f"C{collection:03d}_G{guarantee:03d}"
        for collection in (85, 70, 50, 30)
        for guarantee in (100, 70, 50, 30, 0)
    }


def load_approved_stochastic_golden(
    golden_map_path: Path,
    approval_manifest_path: Path,
    *,
    source_sha: str,
    cohort_id: str,
    master_seed: int,
    required_trial_count: int,
) -> dict[str, Any]:
    """Load only a reviewed Golden whose approval binds the exact map file hash."""
    if not golden_map_path.is_file() or not approval_manifest_path.is_file():
        raise GoldenEvidenceError("GOLDEN_EVIDENCE_FILE_MISSING")
    map_sha = sha256_file(golden_map_path)
    approval = json.loads(approval_manifest_path.read_text(encoding="utf-8"))
    golden = json.loads(golden_map_path.read_text(encoding="utf-8"))

    if approval.get("approval_status") != APPROVED_GOLDEN_STATUS:
        raise GoldenEvidenceError("GOLDEN_APPROVAL_STATUS_NOT_APPROVED")
    if approval.get("candidate_map_sha256") != map_sha:
        raise GoldenEvidenceError("GOLDEN_APPROVAL_MAP_SHA256_MISMATCH")
    identity_fields = {
        "source_sha": source_sha,
        "cohort_id": cohort_id,
        "master_seed": master_seed,
        "model_schema_version": "v2.3",
        "schema_version": STOCHASTIC_GOLDEN_SCHEMA,
        "scenario_count": 20,
        "trial_count_per_scenario": required_trial_count,
        "independent_execution": True,
        "production_result_artifacts_read": False,
    }
    for field, expected in identity_fields.items():
        if golden.get(field) != expected:
            raise GoldenEvidenceError(f"GOLDEN_MAP_IDENTITY_MISMATCH:{field}")
        if approval.get(field) != expected:
            raise GoldenEvidenceError(f"GOLDEN_APPROVAL_IDENTITY_MISMATCH:{field}")
    for field, expected in (
        ("source_sha", source_sha),
        ("cohort_id", cohort_id),
        ("master_seed", master_seed),
        ("candidate_map_sha256", map_sha),
    ):
        if approval.get(field) != expected:
            raise GoldenEvidenceError(f"GOLDEN_APPROVAL_IDENTITY_MISMATCH:{field}")
    if golden.get("status") != CANDIDATE_STATUS:
        raise GoldenEvidenceError("GOLDEN_CANDIDATE_STATUS_INVALID")
    if approval.get("independent_manifest_sha256") is None or len(
        str(approval.get("independent_manifest_sha256"))
    ) != 64:
        raise GoldenEvidenceError("GOLDEN_INDEPENDENT_MANIFEST_HASH_MISSING")
    if approval.get("source_tree_sha_verified") is not True:
        raise GoldenEvidenceError("GOLDEN_SOURCE_TREE_NOT_INDEPENDENTLY_VERIFIED")

    scenarios = golden.get("scenarios")
    expected = expected_stochastic_scenarios()
    if not isinstance(scenarios, dict) or set(scenarios) != expected:
        raise GoldenEvidenceError("GOLDEN_SCENARIO_COVERAGE_MISMATCH")
    if golden.get("trial_id_start") != 1 or golden.get("trial_id_end") != required_trial_count:
        raise GoldenEvidenceError("GOLDEN_TRIAL_RANGE_MISMATCH")
    if golden.get("total_trial_fingerprints") != 20 * required_trial_count:
        raise GoldenEvidenceError("GOLDEN_TOTAL_FINGERPRINT_COUNT_MISMATCH")

    expected_trial_ids = {str(trial_id) for trial_id in range(1, required_trial_count + 1)}
    for scenario_id, entry in scenarios.items():
        if not isinstance(entry, dict):
            raise GoldenEvidenceError(f"GOLDEN_SCENARIO_RECORD_INVALID:{scenario_id}")
        if (
            entry.get("trial_id_start") != 1
            or entry.get("trial_id_end") != required_trial_count
            or entry.get("trial_count") != required_trial_count
        ):
            raise GoldenEvidenceError(f"GOLDEN_SCENARIO_TRIAL_RANGE_MISMATCH:{scenario_id}")
        fingerprints = entry.get("trial_fingerprints")
        if not isinstance(fingerprints, dict) or set(fingerprints) != expected_trial_ids:
            raise GoldenEvidenceError(f"GOLDEN_SCENARIO_TRIAL_COVERAGE_MISMATCH:{scenario_id}")
        actual_map_sha = scenario_fingerprint_map_sha256(scenario_id, fingerprints)
        if actual_map_sha != entry.get("financial_trial_fingerprint_map_sha256"):
            raise GoldenEvidenceError(f"GOLDEN_SCENARIO_FINGERPRINT_MAP_SHA256_MISMATCH:{scenario_id}")
        rng_sha = entry.get("rng_audit_map_sha256")
        trial_result_sha = entry.get("complete_trial_result_audit_sha256")
        for field, value in (
            ("rng_audit_map_sha256", rng_sha),
            ("complete_trial_result_audit_sha256", trial_result_sha),
        ):
            if not isinstance(value, str) or len(value) != 64 or any(
                char not in "0123456789abcdef" for char in value
            ):
                raise GoldenEvidenceError(f"GOLDEN_SCENARIO_AUDIT_HASH_INVALID:{scenario_id}:{field}")
    approval_scenarios = approval.get("scenario_ids")
    if not isinstance(approval_scenarios, list) or set(approval_scenarios) != expected:
        raise GoldenEvidenceError("GOLDEN_APPROVAL_SCENARIO_SET_MISMATCH")
    return {
        "golden_map": golden,
        "approval_manifest": approval,
        "golden_map_sha256": map_sha,
        "approval_manifest_sha256": sha256_file(approval_manifest_path),
    }


def evaluate_gate_a_point(
    scenario_id: str,
    trial_results: Iterable[Any],
    *,
    n: int,
    source_sha: str,
    cohort_id: str,
    approved_golden: dict[str, Any] | None,
) -> dict[str, Any]:
    """Compare all financial-only trial fingerprints for IDs 1..N, fail closed."""
    base = {
        "checked": False,
        "stable": False,
        "source_sha": source_sha,
        "cohort_id": cohort_id,
        "scenario_id": scenario_id,
        "n": n,
    }
    if approved_golden is None:
        return {
            **base,
            "status": "NOT_EVALUATED_NO_APPROVED_SAME_SOURCE_GOLDEN",
            "reason": "APPROVED_GOLDEN_MAP_NOT_PROVIDED",
        }
    if scenario_id not in expected_stochastic_scenarios():
        return {**base, "status": "BLOCKED_SCENARIO_NOT_IN_GOLDEN_FAMILY"}
    golden = approved_golden["golden_map"]
    if golden.get("source_sha") != source_sha or golden.get("cohort_id") != cohort_id:
        return {**base, "status": "BLOCKED_GOLDEN_IDENTITY_MISMATCH"}
    scenario_entry = golden["scenarios"][scenario_id]
    fingerprints = scenario_entry["trial_fingerprints"]
    materialized = sorted(trial_results, key=lambda result: int(result.trial_id))
    expected_ids = list(range(1, n + 1))
    actual_ids = [int(result.trial_id) for result in materialized]
    if actual_ids != expected_ids:
        return {
            **base,
            "status": "MISSING_EVIDENCE",
            "reason": "PRODUCTION_TRIAL_ID_RANGE_MISMATCH",
            "expected_trial_id_start": 1,
            "expected_trial_id_end": n,
            "actual_trial_count": len(actual_ids),
        }
    for result in materialized:
        if str(result.scenario_id) != scenario_id:
            return {
                **base,
                "status": "FAIL_PRODUCTION_SCENARIO_IDENTITY_MISMATCH",
                "trial_id": int(result.trial_id),
            }
        trial_id = int(result.trial_id)
        actual_fp = monte_carlo.trial_fingerprint(result)
        recorded_fp = getattr(result, "trial_fingerprint", "")
        if recorded_fp and recorded_fp != actual_fp:
            return {
                **base,
                "status": "FAIL_PRODUCTION_FINANCIAL_FINGERPRINT_SELF_MISMATCH",
                "trial_id": trial_id,
            }
        if fingerprints.get(str(trial_id)) != actual_fp:
            return {
                **base,
                "status": "FAIL_GOLDEN_FINANCIAL_FINGERPRINT_MISMATCH",
                "trial_id": trial_id,
                "golden_trial_fingerprint": fingerprints.get(str(trial_id)),
                "production_trial_fingerprint": actual_fp,
            }
    return {
        **base,
        "status": "PASS_SCOPED",
        "checked": True,
        "stable": True,
        "scope": "STOCHASTIC_SCENARIO_CUMULATIVE_TRIAL_FINGERPRINTS",
        "trial_id_start": 1,
        "trial_id_end": n,
        "trial_count_compared": n,
        "mismatches": 0,
        "golden_map_sha256": approved_golden["golden_map_sha256"],
        "approval_manifest_sha256": approved_golden["approval_manifest_sha256"],
        "financial_trial_fingerprint_map_sha256": scenario_fingerprint_map_sha256(
            scenario_id, {str(result.trial_id): monte_carlo.trial_fingerprint(result) for result in materialized}
        ),
    }
