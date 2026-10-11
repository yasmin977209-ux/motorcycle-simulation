from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "stage12_gateb_n600_audit.py"
SPEC = importlib.util.spec_from_file_location("stage12_gateb_n600_audit", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def result_row(trial_id: int = 551) -> dict:
    return {
        "scenario_id": "C085_G100",
        "collection_probability": 0.85,
        "recovery_rate_pct": 100,
        "trial_id": trial_id,
        "final_close_date": "2028-01-01",
        "final_net_project_equity": 123456,
        "final_cash": 1234,
        "cumulative_project_profit": 3456,
        "operating_net_profit": 5678,
        "termination_count": 1,
        "secondary_cycle_count": 2,
        "owned_bikes": 3,
        "held_assets": 4,
        "total_operating_revenue": 9000,
        "bad_debt": 100,
        "guarantee_recovered": 200,
        "partner1_final_entitlement": 86419,
        "partner2_final_entitlement": 37037,
    }


def test_n600_policy_ranges_are_exact_and_disjoint():
    assert len(audit.SCENARIOS) == 20
    assert len(set(audit.SCENARIOS)) == 20
    assert list(audit.HISTORICAL_IDS) == list(range(1, 551))
    assert list(audit.NEW_IDS) == list(range(551, 601))
    assert not set(audit.HISTORICAL_IDS).intersection(audit.NEW_IDS)
    assert len(audit.NEW_IDS) == 50
    assert set(audit.METRICS.values()) == {
        "final_net_project_equity",
        "partner1_final_entitlement",
        "partner2_final_entitlement",
    }


def test_result_sha256_is_stable_after_json_round_trip():
    row = result_row()
    first = audit.row_sha(row)
    round_tripped = json.loads(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    assert audit.row_sha(round_tripped) == first


def test_canonical_block_fingerprint_is_order_independent():
    rows = [
        {"scenario_id": "C085_G100", "trial_id": 552, "value": 5.0},
        {"scenario_id": "C085_G100", "trial_id": 551, "value": 4.0},
    ]
    assert audit.canonical_fingerprint(rows) == audit.canonical_fingerprint(list(reversed(rows)))


def test_stage10_known_suffix_is_read_only_and_parsed_only_when_allowed():
    raw = b'{"scenario":"C085_G100"}\\n'
    parsed, mode = audit.parse_json_bytes(raw, allow_known_stage10_suffix=True)
    assert parsed == {"scenario": "C085_G100"}
    assert mode == "known_stage10_literal_backslash_n_suffix_removed_in_memory"
    assert raw.endswith(b"}\\n")
    with pytest.raises(RuntimeError, match="UNEXPECTED_LITERAL_BACKSLASH_N_JSON_SUFFIX"):
        audit.parse_json_bytes(raw, allow_known_stage10_suffix=False)


def test_trial_payload_validation_requires_exact_hash_and_identity():
    row = result_row()
    payload = {
        "scenario_id": "C085_G100",
        "trial_id": 551,
        "trial_result": row,
        "result_sha256": audit.row_sha(row),
        "source_sha": audit.SOURCE_SHA,
        "master_seed": audit.MASTER_SEED,
        "source_commit": audit.SOURCE_COMMIT,
        "run_id": 12345,
        "log_events": False,
    }
    audit.validate_trial_payload(payload, "C085_G100", 551, expected_run_id=12345)
    payload["result_sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="NEW_TRIAL_RESULT_HASH_MISMATCH"):
        audit.validate_trial_payload(payload, "C085_G100", 551, expected_run_id=12345)


def test_trial_payload_rejects_historical_id_as_new_trial():
    row = result_row(trial_id=550)
    payload = {
        "scenario_id": "C085_G100", "trial_id": 550, "trial_result": row,
        "result_sha256": audit.row_sha(row), "source_sha": audit.SOURCE_SHA,
        "master_seed": audit.MASTER_SEED, "source_commit": audit.SOURCE_COMMIT,
        "run_id": 12345, "log_events": False,
    }
    with pytest.raises(RuntimeError, match="NEW_TRIAL_ID_OUT_OF_RANGE"):
        if int(payload["trial_id"]) not in audit.NEW_IDS:
            audit.fail("NEW_TRIAL_ID_OUT_OF_RANGE C085_G100/550")
        audit.validate_trial_payload(payload, "C085_G100", 550)
