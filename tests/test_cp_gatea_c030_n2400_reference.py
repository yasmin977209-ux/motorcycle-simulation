from __future__ import annotations

import hashlib
import json

import pytest

from scripts.cp_gatea_c030_n2400_reference import (
    SCENARIO,
    SOURCE_COMMIT,
    SOURCE_SHA,
    MASTER_SEED,
    canonical_trial_sha256,
    extension_map_sha,
    validate_extension_records,
)


def make_record(trial_id: int, *, run_id: int = 123, run_attempt: int = 1) -> dict:
    row = {
        "scenario_id": SCENARIO,
        "trial_id": trial_id,
        "final_net_project_equity": 1000 + trial_id,
    }
    return {
        "scenario_id": SCENARIO,
        "trial_id": trial_id,
        "trial_result": row,
        "result_sha256": canonical_trial_sha256(row),
        "source_sha": SOURCE_SHA,
        "source_commit": SOURCE_COMMIT,
        "master_seed": MASTER_SEED,
        "run_id": run_id,
        "run_attempt": run_attempt,
        "origin": "pinned_source_reference",
    }


def test_stage10_hash_matches_sha256_of_canonical_trial_json() -> None:
    row = make_record(1201)["trial_result"]
    canonical = json.dumps(
        row,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    assert canonical_trial_sha256(row) == hashlib.sha256(canonical).hexdigest()


def test_extension_hash_is_order_independent_and_unique() -> None:
    rows = [make_record(1202), make_record(1201)]
    left = extension_map_sha(rows)
    right = extension_map_sha(list(reversed(rows)))
    assert left == right
    assert len(left) == 64


def test_extension_validation_rejects_wrong_source_identity() -> None:
    bad = make_record(1201)
    bad["source_sha"] = "0" * 40
    with pytest.raises(RuntimeError, match="TRIAL_PROVENANCE_MISMATCH"):
        validate_extension_records([bad], run_id=123, run_attempt=1)


def test_extension_validation_rejects_result_hash_mismatch() -> None:
    bad = make_record(1201)
    bad["result_sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="TRIAL_RESULT_SHA_MISMATCH"):
        validate_extension_records([bad], run_id=123, run_attempt=1)
