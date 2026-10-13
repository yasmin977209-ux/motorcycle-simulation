from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

from scripts.golden_reference_provider import (
    APPROVED_SOURCE_SHA,
    DECISION_ID,
    EXPECTED_CANONICAL_MAP_SHA256,
    EXPECTED_FULL_MAP_SHA256,
    EXPECTED_N1200_MAP_SHA256,
    EXPECTED_N600_MAP_SHA256,
    GATE_A_RUN_ID,
    GATE_A_SCENARIO_ARTIFACTS,
    MASTER_SEED,
    NON_C100_SCENARIOS,
    SCENARIOS,
    GoldenReferenceProvider,
    _ordered_map_sha256,
    stage10_trial_result_sha256,
)


@dataclass(frozen=True)
class _Record:
    trial_id: int
    amount: int


def test_stage10_per_trial_hash_matches_canonical_json_contract() -> None:
    record = _Record(trial_id=7, amount=123456)
    payload = json.dumps(
        asdict(record),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    assert stage10_trial_result_sha256(record) == hashlib.sha256(payload).hexdigest()


def test_approved_provider_scope_and_source_pins_are_explicit() -> None:
    assert len(SCENARIOS) == 25
    assert len(set(SCENARIOS)) == 25
    assert len(NON_C100_SCENARIOS) == 20
    assert len(GATE_A_SCENARIO_ARTIFACTS) == 25
    assert len({artifact_id for artifact_id, _ in GATE_A_SCENARIO_ARTIFACTS.values()}) == 25
    assert all(len(digest) == 64 for _, digest in GATE_A_SCENARIO_ARTIFACTS.values())
    assert len(APPROVED_SOURCE_SHA) == 40
    assert MASTER_SEED == 20270101
    assert DECISION_ID == "D-2026-10-14-01"
    assert GATE_A_RUN_ID == 38169163565
    assert EXPECTED_CANONICAL_MAP_SHA256 == "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44"
    assert EXPECTED_N600_MAP_SHA256 == "dd537fe96c5a8736201441e9a620db148a0d16cadae518d2a777fbc723db395f"
    assert EXPECTED_N1200_MAP_SHA256 == "eaf1f8f3060aac6967b064d3199c082d2a9b47027c865628986f56cbb23c1fc3"
    assert EXPECTED_FULL_MAP_SHA256 == "166cae242d972c597f1a4466d184062f3d959649eb5e2440ad8de8b75663ff2c"


def test_ordered_map_sha256_is_stable_and_keeps_scenario_trial_keys() -> None:
    first = {
        "C070_G100": {2: "b" * 64, 1: "a" * 64},
        "C030_G000": {1: "c" * 64},
    }
    second = {
        "C030_G000": {1: "c" * 64},
        "C070_G100": {1: "a" * 64, 2: "b" * 64},
    }

    assert _ordered_map_sha256(first) == _ordered_map_sha256(second)
    assert len(_ordered_map_sha256(first)) == 64


def test_provider_without_token_fails_closed(monkeypatch) -> None:
    monkeypatch.delenv("GH_TOKEN", raising=False)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)

    provider = GoldenReferenceProvider()

    assert provider.get_fingerprint("C070_G100", 1) is None
    assert provider.get_coverage("C070_G100") == set()
    assert provider.verify_source_identity(APPROVED_SOURCE_SHA) is False
    assert provider.get_golden_reference_id() == ""
    assert provider.load_error == "GOLDEN_PROVIDER_TOKEN_MISSING"


def test_test_provider_does_not_mutate_coverage_values() -> None:
    provider = GoldenReferenceProvider._from_test_map(
        {"C070_G100": {1: "a" * 64, 2: "b" * 64}}
    )
    coverage = provider.get_coverage("C070_G100")
    coverage.clear()

    assert provider.get_coverage("C070_G100") == {1, 2}
    assert provider.get_fingerprint("C070_G100", 1) == "a" * 64
    assert provider.verify_source_identity(APPROVED_SOURCE_SHA)
