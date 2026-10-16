"""Fail-closed binding of Stage 7 Gate A to approved per-trial golden hashes."""
from __future__ import annotations

from typing import Any, Iterable

from scripts.golden_reference_provider import (
    APPROVED_SOURCE_SHA, APPROVED_SOURCE_COMMIT, MASTER_SEED, SCENARIOS,
    GoldenReferenceProvider, _ordered_map_sha256, stage10_trial_result_sha256,
)
from scripts.stage7_stability import evaluate_gate_a

EXPECTED_COUNT = 25205
EXPECTED_COUNTS = {
    scenario: 1 if scenario.startswith("C100_") else 2400 if scenario == "C030_G030" else 1200
    for scenario in SCENARIOS
}


def _identity_error(provider: GoldenReferenceProvider, source_sha: str, master_seed: int) -> str | None:
    if provider.load_error:
        return f"GOLDEN_PROVIDER_LOAD_FAILED:{provider.load_error}"
    if source_sha != APPROVED_SOURCE_SHA or not provider.verify_source_identity(source_sha):
        return "GOLDEN_PROVIDER_SOURCE_IDENTITY_MISMATCH"
    if master_seed != MASTER_SEED or provider.master_seed != master_seed:
        return "GOLDEN_PROVIDER_MASTER_SEED_MISMATCH"
    if provider.source_commit != APPROVED_SOURCE_COMMIT:
        return "GOLDEN_PROVIDER_SOURCE_COMMIT_MISMATCH"
    if not provider.get_golden_reference_id():
        return "GOLDEN_PROVIDER_REFERENCE_ID_MISSING"
    return None


def validate_provider_full_coverage(provider: GoldenReferenceProvider, *, source_sha: str, master_seed: int) -> dict[str, Any]:
    """Validate all pinned golden rows and their identities. Never runs trials."""
    error = _identity_error(provider, source_sha, master_seed)
    if error:
        return {"status": "BLOCKED", "reason": error, "source_sha": source_sha, "master_seed": master_seed}
    if provider.scenario_count != 25:
        return {"status": "BLOCKED", "reason": f"GOLDEN_PROVIDER_SCENARIO_COUNT_MISMATCH:{provider.scenario_count}"}
    if provider.trial_count != EXPECTED_COUNT:
        return {"status": "BLOCKED", "reason": f"GOLDEN_PROVIDER_TRIAL_COUNT_MISMATCH:{provider.trial_count}"}
    coverage = {}
    for scenario in SCENARIOS:
        count = EXPECTED_COUNTS[scenario]
        expected_ids = set(range(1, count + 1))
        actual_ids = provider.get_coverage(scenario)
        missing, extra = sorted(expected_ids - actual_ids), sorted(actual_ids - expected_ids)
        if missing or extra:
            return {
                "status": "BLOCKED",
                "reason": f"GOLDEN_PROVIDER_COVERAGE_MISMATCH:{scenario}:missing={missing[:5]}:extra={extra[:5]}",
                "scenario_coverage": coverage,
            }
        invalid = [trial_id for trial_id in range(1, count + 1) if provider.get_fingerprint(scenario, trial_id) is None]
        if invalid:
            return {"status": "BLOCKED", "reason": f"GOLDEN_PROVIDER_INVALID_FINGERPRINTS:{scenario}:{invalid[:5]}"}
        coverage[scenario] = {"trial_count": count, "first_trial_id": 1, "last_trial_id": count}
    return {
        "status": "PASS", "reason": None, "source_sha": source_sha, "source_commit": provider.source_commit,
        "master_seed": master_seed, "trial_fingerprint_algorithm": "Stage 10 result_sha: dataclasses.asdict + canonical sorted JSON",
        "golden_reference_id": provider.get_golden_reference_id(), "base_trial_count": provider.base_trial_count,
        "trial_count": provider.trial_count, "scenario_count": provider.scenario_count,
        "base_source_map_sha256": provider.base_source_map_sha256, "source_map_sha256": provider.source_map_sha256,
        "extension_decision_id": provider.extension_decision_id, "extension_run_id": provider.extension_run_id,
        "extension_run_head_sha": provider.extension_run_head_sha, "extension_artifact_id": provider.extension_artifact_id,
        "extension_artifact_sha256": provider.extension_artifact_sha256, "extension_map_sha256": provider.extension_map_sha256,
        "scenario_coverage": coverage, "trial_generation_executed": False, "historical_dataset_modified": False,
        "parquet_modified": False,
    }


def validate_checkpoint_coverage(provider: GoldenReferenceProvider, *, scenario_id: str, target_n: int, source_sha: str, master_seed: int) -> dict[str, Any]:
    """Check target checkpoint's exact golden coverage before invoking its trial block."""
    error = _identity_error(provider, source_sha, master_seed)
    if error:
        return {"status": "BLOCKED", "reason": error}
    if scenario_id not in EXPECTED_COUNTS:
        return {"status": "BLOCKED", "reason": f"GOLDEN_PROVIDER_UNKNOWN_SCENARIO:{scenario_id}"}
    if isinstance(target_n, bool) or not isinstance(target_n, int) or target_n < 1:
        return {"status": "BLOCKED", "reason": f"GOLDEN_PROVIDER_INVALID_TARGET_N:{target_n}"}
    if target_n > EXPECTED_COUNTS[scenario_id]:
        return {"status": "BLOCKED", "reason": f"GOLDEN_CHECKPOINT_COVERAGE_MISSING:{scenario_id}:target_n={target_n}:approved_max={EXPECTED_COUNTS[scenario_id]}"}
    coverage = provider.get_coverage(scenario_id)
    missing = sorted(set(range(1, target_n + 1)) - coverage)
    if missing:
        return {"status": "BLOCKED", "reason": f"GOLDEN_CHECKPOINT_COVERAGE_MISSING:{scenario_id}:missing_first={missing[:5]}:target_n={target_n}"}
    for trial_id in range(1, target_n + 1):
        if provider.get_fingerprint(scenario_id, trial_id) is None:
            return {"status": "BLOCKED", "reason": f"GOLDEN_CHECKPOINT_INVALID_FINGERPRINT:{scenario_id}:trial_id={trial_id}"}
    return {
        "status": "READY", "reason": None, "scenario_id": scenario_id, "target_n": target_n,
        "source_sha": source_sha, "master_seed": master_seed,
        "golden_reference_id": provider.get_golden_reference_id(), "golden_source_map_sha256": provider.source_map_sha256,
    }


def build_exact_gate_a_evidence(provider: GoldenReferenceProvider, *, scenario_id: str, results: Iterable[Any], source_sha: str, master_seed: int) -> dict[str, Any]:
    """Hash actual TrialResult rows using Stage 10's per-trial contract and compare to golden."""
    rows = list(results)
    count = len(rows)
    coverage = validate_checkpoint_coverage(provider, scenario_id=scenario_id, target_n=count, source_sha=source_sha, master_seed=master_seed)
    if coverage.get("status") != "READY":
        return {**coverage, "status": "BLOCKED", "scenario_id": scenario_id, "current_n": count,
                "expected_golden_fingerprint_sha256": None, "actual_fingerprint_sha256": None,
                "golden_reference_id": None, "expected_source_sha": None, "actual_source_sha": source_sha}
    trial_ids = [getattr(row, "trial_id", None) for row in rows]
    if any(isinstance(i, bool) or not isinstance(i, int) for i in trial_ids) or sorted(trial_ids) != list(range(1, count + 1)):
        return {"status": "BLOCKED", "reason": f"GOLDEN_ACTUAL_TRIAL_ID_COVERAGE_MISMATCH:{scenario_id}:count={count}:ids={sorted(str(i) for i in trial_ids)[:5]}",
                "scenario_id": scenario_id, "current_n": count, "expected_golden_fingerprint_sha256": None,
                "actual_fingerprint_sha256": None, "golden_reference_id": None, "expected_source_sha": None, "actual_source_sha": source_sha}
    actual, golden = {}, {}
    for row in rows:
        trial_id = int(row.trial_id)
        actual[trial_id] = stage10_trial_result_sha256(row)
        golden_hash = provider.get_fingerprint(scenario_id, trial_id)
        if golden_hash is None:
            return {"status": "BLOCKED", "reason": f"GOLDEN_CHECKPOINT_FINGERPRINT_MISSING:{scenario_id}:trial_id={trial_id}",
                    "scenario_id": scenario_id, "current_n": count, "expected_golden_fingerprint_sha256": None,
                    "actual_fingerprint_sha256": None, "golden_reference_id": None, "expected_source_sha": None, "actual_source_sha": source_sha}
        golden[trial_id] = golden_hash
    return {
        "status": "READY", "reason": None, "scenario_id": scenario_id, "current_n": count,
        "expected_golden_fingerprint_sha256": _ordered_map_sha256({scenario_id: golden}),
        "actual_fingerprint_sha256": _ordered_map_sha256({scenario_id: actual}),
        "golden_reference_id": provider.get_golden_reference_id(), "expected_source_sha": provider.source_sha,
        "actual_source_sha": source_sha, "master_seed": master_seed, "golden_source_map_sha256": provider.source_map_sha256,
        "trial_count_compared": count, "per_trial_exact_values_compared": count,
        "trial_generation_executed": False, "historical_dataset_modified": False, "parquet_modified": False,
    }


def evaluate_gate_a_with_approved_golden(*, provider: GoldenReferenceProvider, scenario_id: str, results: Iterable[Any],
    source_sha: str, master_seed: int, previous_n: int | None, previous_metrics: dict[str, dict[str, Any]] | None,
    current_metrics: dict[str, dict[str, Any]], escalation_multiplier: int, relative_epsilon: float,
    absolute_epsilon: float) -> dict[str, Any]:
    rows = list(results)
    evidence = build_exact_gate_a_evidence(provider, scenario_id=scenario_id, results=rows, source_sha=source_sha, master_seed=master_seed)
    gate = evaluate_gate_a(
        previous_n=previous_n, previous_metrics=previous_metrics, current_n=len(rows), current_metrics=current_metrics,
        escalation_multiplier=escalation_multiplier, relative_epsilon=relative_epsilon, absolute_epsilon=absolute_epsilon,
        expected_golden_fingerprint_sha256=evidence.get("expected_golden_fingerprint_sha256"),
        actual_fingerprint_sha256=evidence.get("actual_fingerprint_sha256"), golden_reference_id=evidence.get("golden_reference_id"),
        expected_source_sha=evidence.get("expected_source_sha"), actual_source_sha=evidence.get("actual_source_sha"),
    )
    if evidence.get("status") != "READY":
        gate.update({"checked": False, "stable": False, "status": "BLOCKED", "reason": evidence.get("reason") or "GOLDEN_PROVIDER_EVIDENCE_BLOCKED"})
    gate["golden_provider_evidence"] = evidence
    return gate
