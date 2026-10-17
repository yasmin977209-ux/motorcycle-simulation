from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass

import pytest

from scripts.generate_c100_golden_extension import (
    EXTENSION_DECISION_ID,
    EXPECTED_RECORD_COUNT,
    MASTER_SEED,
    SCENARIOS,
    SOURCE_COMMIT,
    SOURCE_SHA,
    TRIAL_ID_END,
    TRIAL_ID_START,
    canonical_result_sha256,
    ordered_extension_map_sha256,
)


@dataclass(frozen=True)
class _TrialResult:
    scenario_id: str
    trial_id: int
    final_cash: int


def test_c100_extension_contract_is_exact_and_bounded() -> None:
    assert EXTENSION_DECISION_ID == "D-2026-10-17-07"
    assert SOURCE_SHA == "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
    assert SOURCE_COMMIT == "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
    assert MASTER_SEED == 20270101
    assert SCENARIOS == (
        "C100_G000", "C100_G030", "C100_G050", "C100_G070", "C100_G100"
    )
    assert TRIAL_ID_START == 2
    assert TRIAL_ID_END == 600
    assert EXPECTED_RECORD_COUNT == 2995


def test_fingerprint_matches_stage10_canonical_json_contract() -> None:
    result = _TrialResult(scenario_id="C100_G000", trial_id=7, final_cash=123456)
    expected_payload = json.dumps(
        asdict(result),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    assert canonical_result_sha256(result) == hashlib.sha256(expected_payload).hexdigest()
    assert canonical_result_sha256(asdict(result)) == hashlib.sha256(expected_payload).hexdigest()


def _full_records() -> list[dict]:
    records = []
    for scenario in SCENARIOS:
        for trial_id in range(TRIAL_ID_START, TRIAL_ID_END + 1):
            digest = hashlib.sha256(f"{scenario}|{trial_id}".encode()).hexdigest()
            records.append({
                "scenario_id": scenario,
                "trial_id": trial_id,
                "result_sha256": digest,
            })
    return records


def test_extension_map_hash_is_order_independent_but_keyed_by_trial() -> None:
    records = _full_records()
    digest = ordered_extension_map_sha256(records)
    assert len(digest) == 64
    assert ordered_extension_map_sha256(list(reversed(records))) == digest
    changed = [dict(row) for row in records]
    changed[0]["result_sha256"] = "0" * 64
    assert ordered_extension_map_sha256(changed) != digest


def test_extension_map_rejects_duplicates_and_unauthorized_rows() -> None:
    records = _full_records()
    with pytest.raises(ValueError, match="DUPLICATE_TRIAL_ID"):
        ordered_extension_map_sha256(records + [records[0]])
    with pytest.raises(ValueError, match="UNAUTHORIZED_C100_SCENARIO"):
        ordered_extension_map_sha256(records + [{
            "scenario_id": "C070_G000",
            "trial_id": 2,
            "result_sha256": "a" * 64,
        }])
    with pytest.raises(ValueError, match="UNAUTHORIZED_TRIAL_ID"):
        ordered_extension_map_sha256(records + [{
            "scenario_id": "C100_G000",
            "trial_id": 601,
            "result_sha256": "b" * 64,
        }])


def test_extension_map_rejects_incomplete_range() -> None:
    records = _full_records()
    with pytest.raises(ValueError, match="C100_EXTENSION_COVERAGE_MISMATCH"):
        ordered_extension_map_sha256(records[:-1])
