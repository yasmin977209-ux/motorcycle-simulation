from __future__ import annotations

import pytest

import constants
from scripts.s6_gate_a_golden import (
    _assert_no_float,
    _map_sha256,
    _scenario_ids,
    _validate_checkpoint,
    _validate_rng_uniqueness,
)


def test_s6_golden_runner_uses_only_approved_doubling_checkpoints() -> None:
    n = constants.STATISTICAL_CHECK_START_N
    for _ in range(4):
        _validate_checkpoint(n)
        n *= constants.STATISTICAL_ESCALATION_MULTIPLIER

    with pytest.raises(ValueError, match="S6_N_MUST_FOLLOW_THE_APPROVED_DOUBLING_SCHEDULE"):
        _validate_checkpoint(constants.STATISTICAL_CHECK_START_N + 1)


def test_s6_golden_scenario_family_contains_twenty_stochastic_scenarios_only() -> None:
    scenarios = _scenario_ids()
    expected_count = (
        len(constants.STAGE5_STOCHASTIC_COLLECTION_PERCENTAGES)
        * len(constants.GUARANTEE_RECOVERY_RATES)
    )
    assert len(scenarios) == expected_count
    assert not any(scenario.startswith("C100_") for scenario in scenarios)
    assert len(set(scenarios)) == len(scenarios)


def test_s6_gate_a_map_hash_is_order_independent_after_canonical_sort() -> None:
    records = [
        {"trial_id": 3, "trial_fingerprint": "c" * 64},
        {"trial_id": 1, "trial_fingerprint": "a" * 64},
        {"trial_id": 2, "trial_fingerprint": "b" * 64},
    ]
    forward = _map_sha256("C085_G100", records)
    reverse = _map_sha256("C085_G100", list(reversed(records)))
    assert forward == reverse
    assert len(forward) == constants.SHA256_HEX_LENGTH


def test_s6_rng_uniqueness_allows_zero_checksum_only_as_specified() -> None:
    _validate_rng_uniqueness([
        {"scenario_id": "C085_G100", "trial_id": 1, "rng_checksum": 0, "rng_draw_count": 0},
        {"scenario_id": "C085_G100", "trial_id": 2, "rng_checksum": 0, "rng_draw_count": 1},
        {"scenario_id": "C085_G100", "trial_id": 3, "rng_checksum": 7, "rng_draw_count": 1},
    ], "C085_G100")

    with pytest.raises(RuntimeError, match="DUPLICATE_RNG_CHECKSUM_DETECTED"):
        _validate_rng_uniqueness([
            {"scenario_id": "C085_G100", "trial_id": 1, "rng_checksum": 0, "rng_draw_count": 1},
            {"scenario_id": "C085_G100", "trial_id": 2, "rng_checksum": 0, "rng_draw_count": 2},
        ], "C085_G100")


def test_s6_golden_payload_rejects_float_values() -> None:
    _assert_no_float({"money": 10, "exact": {"numerator": 1, "denominator": 2}})
    with pytest.raises(AssertionError, match="FLOAT_LEAK_DETECTED"):
        _assert_no_float({"money": 10.5})
