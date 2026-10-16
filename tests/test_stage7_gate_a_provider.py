from __future__ import annotations

from dataclasses import dataclass

from scripts.golden_reference_provider import (
    APPROVED_SOURCE_SHA,
    MASTER_SEED,
    GoldenReferenceProvider,
    stage10_trial_result_sha256,
)
from scripts.stage7_gate_a_provider import (
    build_exact_gate_a_evidence,
    evaluate_gate_a_with_approved_golden,
    validate_checkpoint_coverage,
    validate_provider_full_coverage,
)

@dataclass(frozen=True)
class _Trial:
    trial_id: int
    closing_cash: int

def _results(n: int) -> list[_Trial]:
    return [_Trial(trial_id=i, closing_cash=1000 + i) for i in range(1, n + 1)]

def _provider(results: list[_Trial], scenario: str = "C070_G100", *, alter_trial: int | None = None, source_sha: str = APPROVED_SOURCE_SHA):
    fingerprints = {}
    for result in results:
        value = stage10_trial_result_sha256(result)
        if result.trial_id == alter_trial:
            value = "0" * 64
        fingerprints[result.trial_id] = value
    return GoldenReferenceProvider._from_test_map(
        {scenario: fingerprints},
        source_sha=source_sha,
        golden_reference_id="unit-test-approved-golden",
    )

def _metrics():
    return {"final_net_project_equity": {"mean": 1000.0, "stable": True}}

def _evaluate(provider, results, *, source_sha=APPROVED_SOURCE_SHA):
    return evaluate_gate_a_with_approved_golden(
        provider=provider,
        scenario_id="C070_G100",
        results=results,
        source_sha=source_sha,
        master_seed=MASTER_SEED,
        previous_n=None,
        previous_metrics=None,
        current_metrics=_metrics(),
        escalation_multiplier=2,
        relative_epsilon=0.01,
        absolute_epsilon=1.0,
    )

def test_exact_gate_a_uses_stage10_per_trial_hashes_and_approved_map():
    results = _results(300)
    provider = _provider(results)
    evidence = build_exact_gate_a_evidence(
        provider,
        scenario_id="C070_G100",
        results=results,
        source_sha=APPROVED_SOURCE_SHA,
        master_seed=MASTER_SEED,
    )
    assert evidence["status"] == "READY"
    assert evidence["trial_count_compared"] == 300
    assert evidence["per_trial_exact_values_compared"] == 300
    assert evidence["expected_golden_fingerprint_sha256"] == evidence["actual_fingerprint_sha256"]
    gate = _evaluate(provider, results)
    assert gate["status"] == "PASS"
    assert gate["checked"] is True
    assert gate["stable"] is True
    assert gate["golden_reference_id"] == "unit-test-approved-golden"

def test_exact_gate_a_fingerprint_mismatch_is_fail_not_pass():
    results = _results(300)
    provider = _provider(results, alter_trial=177)
    gate = _evaluate(provider, results)
    assert gate["status"] == "FAIL"
    assert gate["checked"] is True
    assert gate["stable"] is False
    assert gate["reason"] == "actual fingerprint differs from approved golden"

def test_exact_gate_a_source_identity_mismatch_is_blocked():
    results = _results(300)
    provider = _provider(results)
    gate = _evaluate(provider, results, source_sha="e" * 40)
    assert gate["status"] == "BLOCKED"
    assert gate["checked"] is False
    assert gate["stable"] is False
    assert "SOURCE_IDENTITY_MISMATCH" in gate["reason"]

def test_missing_next_checkpoint_coverage_blocks_before_any_new_trial():
    provider = _provider(_results(600))
    result = validate_checkpoint_coverage(
        provider,
        scenario_id="C070_G100",
        target_n=1200,
        source_sha=APPROVED_SOURCE_SHA,
        master_seed=MASTER_SEED,
    )
    assert result["status"] == "BLOCKED"
    assert "GOLDEN_CHECKPOINT_COVERAGE_MISSING" in result["reason"]

def test_noncontiguous_or_duplicate_actual_trial_ids_block_gate_a():
    results = _results(300)
    results[-1] = _Trial(trial_id=299, closing_cash=1300)
    provider = _provider(_results(300))
    gate = _evaluate(provider, results)
    assert gate["status"] == "BLOCKED"
    assert gate["checked"] is False
    assert "TRIAL_ID_COVERAGE_MISMATCH" in gate["reason"]

def test_full_provider_coverage_validation_rejects_incomplete_map():
    provider = _provider(_results(2))
    result = validate_provider_full_coverage(
        provider,
        source_sha=APPROVED_SOURCE_SHA,
        master_seed=MASTER_SEED,
    )
    assert result["status"] == "BLOCKED"
    assert "SCENARIO_COUNT_MISMATCH" in result["reason"]
