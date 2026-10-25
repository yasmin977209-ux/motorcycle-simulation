"""Focused integrity tests for per-trial random-draw audit metadata."""
from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

import pytest

import rng
import run_batch
from monte_carlo import TrialResult, fingerprint_rng_audit, fingerprint_trial_results
from scripts.golden_reference_provider import stage10_trial_result_sha256
from scripts.stage7_state import StateIntegrityError


def test_rng_checksum_sums_drawn_high_53_bit_values_modulo_2_to_64() -> None:
    value = 0x3EDCBA9876543210
    seed = value.to_bytes(8, "big") + bytes(24)
    with rng.capture_rng_checksum() as audit:
        assert rng.draw_success(seed, 50) is True
    assert audit.draw_count == 1
    assert audit.checksum == (value >> 11)


def test_deterministic_probability_endpoints_create_no_rng_draws() -> None:
    seed = bytes.fromhex("ab" * 32)
    with rng.capture_rng_checksum() as audit:
        assert rng.deterministic_success(0.0, seed) is False
        assert rng.deterministic_success(1.0, seed) is True
    assert audit.draw_count == 0
    assert audit.checksum == 0


def _trial(rng_checksum: int, rng_draw_count: int) -> TrialResult:
    return TrialResult(
        scenario_id="C085_G070",
        collection_probability=0.85,
        recovery_rate_pct=70,
        trial_id=1,
        final_close_date="2033-01-06",
        final_net_project_equity=123456,
        final_cash=45678,
        cumulative_project_profit=34567,
        operating_net_profit=23456,
        termination_count=7,
        secondary_cycle_count=2,
        owned_bikes=3,
        held_assets=4,
        total_operating_revenue=456789,
        bad_debt=5678,
        guarantee_recovered=6789,
        partner1_final_entitlement=86419,
        partner2_final_entitlement=37037,
        rng_checksum=rng_checksum,
        rng_draw_count=rng_draw_count,
    )


def test_rng_audit_is_separate_from_financial_and_golden_fingerprints() -> None:
    first = _trial(123, 8)
    second = replace(first, rng_checksum=456, rng_draw_count=9)
    assert fingerprint_trial_results([first]) == fingerprint_trial_results([second])
    assert stage10_trial_result_sha256(first) == stage10_trial_result_sha256(second)
    assert fingerprint_rng_audit(
        [first], source_sha="a" * 40, master_seed=20270101
    ) != fingerprint_rng_audit(
        [second], source_sha="a" * 40, master_seed=20270101
    )
    assert fingerprint_rng_audit(
        [first], source_sha="a" * 40, master_seed=20270101
    ) != fingerprint_rng_audit(
        [first], source_sha="b" * 40, master_seed=20270101
    )


def test_rng_audit_validation_rejects_duplicate_nonzero_checksums() -> None:
    records = [
        SimpleNamespace(
            scenario_id="C070_G100",
            collection_probability=0.7,
            recovery_rate_pct=100,
            trial_id=1,
            rng_checksum=123456,
            rng_draw_count=20,
        ),
        SimpleNamespace(
            scenario_id="C070_G100",
            collection_probability=0.7,
            recovery_rate_pct=100,
            trial_id=2,
            rng_checksum=123456,
            rng_draw_count=21,
        ),
    ]
    with pytest.raises(StateIntegrityError, match="DUPLICATE_SEED_DETECTED"):
        run_batch._validate_rng_audits(records, expected_scenario="C070_G100")


def test_rng_audit_validation_requires_draws_for_stochastic_trials() -> None:
    record = SimpleNamespace(
        scenario_id="C070_G100",
        collection_probability=0.7,
        recovery_rate_pct=100,
        trial_id=1,
        rng_checksum=0,
        rng_draw_count=0,
    )
    with pytest.raises(StateIntegrityError, match="stochastic trial has no RNG draws"):
        run_batch._validate_rng_audits([record], expected_scenario="C070_G100")


def test_rng_audit_validation_accepts_deterministic_scenario_without_draws() -> None:
    record = SimpleNamespace(
        scenario_id="C100_G100",
        collection_probability=1.0,
        recovery_rate_pct=100,
        trial_id=1,
        rng_checksum=0,
        rng_draw_count=0,
    )
    run_batch._validate_rng_audits([record], expected_scenario="C100_G100")


def test_stage10_baseline_audit_field_guard_rejects_legacy_rows_without_metadata() -> None:
    from scripts.stage10_benchmark import require_rng_audit_fields

    with pytest.raises(RuntimeError, match="BASELINE_RNG_AUDIT_FIELDS_MISSING"):
        require_rng_audit_fields({"trial_id": 1, "final_cash": 100})

    require_rng_audit_fields({"trial_id": 1, "rng_checksum": 0, "rng_draw_count": 0})


def test_stage10_baseline_requires_valid_source_bound_block_audit_fingerprint() -> None:
    from scripts.stage10_benchmark import validate_block_rng_audit

    result = _trial(123, 8)
    source_sha = "a" * 40
    master_seed = 20270101
    valid = {
        "rng_audit_schema": rng.RNG_CHECKSUM_SCHEMA,
        "master_seed": master_seed,
        "rng_checksum_fingerprint_sha256": fingerprint_rng_audit(
            [result], source_sha=source_sha, master_seed=master_seed
        ),
    }
    validate_block_rng_audit(
        valid, [result], scenario="C085_G070",
        source_sha=source_sha, master_seed=master_seed
    )

    tampered = dict(valid, rng_checksum_fingerprint_sha256="b" * 64)
    with pytest.raises(RuntimeError, match="BASELINE_BLOCK_RNG_AUDIT_FINGERPRINT_MISMATCH"):
        validate_block_rng_audit(
            tampered, [result], scenario="C085_G070",
            source_sha=source_sha, master_seed=master_seed
        )

    wrong_seed = dict(valid, master_seed=7)
    with pytest.raises(RuntimeError, match="BASELINE_RNG_AUDIT_MASTER_SEED_MISMATCH"):
        validate_block_rng_audit(
            wrong_seed, [result], scenario="C085_G070",
            source_sha=source_sha, master_seed=master_seed
        )


def test_stage10_write_json_emits_parseable_json_with_real_newline(tmp_path) -> None:
    import json
    from scripts.stage10_benchmark import write_json

    target = tmp_path / "stage10.json"
    payload = {"valid": True, "count": 3}
    write_json(target, payload)
    raw = target.read_text(encoding="utf-8")
    assert raw.endswith("\n")
    assert json.loads(raw) == payload
    assert not raw.endswith("\\n")


def test_rng_audit_validation_does_not_skip_duplicate_zero_checksum_when_draws_occur() -> None:
    records = [
        SimpleNamespace(
            scenario_id="C070_G100",
            collection_probability=0.7,
            recovery_rate_pct=100,
            trial_id=1,
            rng_checksum=0,
            rng_draw_count=20,
        ),
        SimpleNamespace(
            scenario_id="C070_G100",
            collection_probability=0.7,
            recovery_rate_pct=100,
            trial_id=2,
            rng_checksum=0,
            rng_draw_count=25,
        ),
    ]
    with pytest.raises(StateIntegrityError, match="DUPLICATE_SEED_DETECTED"):
        run_batch._validate_rng_audits(records, expected_scenario="C070_G100")
