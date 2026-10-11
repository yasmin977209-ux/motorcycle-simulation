from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "stage12_gateb_n1200_audit.py"
SPEC = importlib.util.spec_from_file_location("stage12_gateb_n1200_audit", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def row(trial_id: int = 601, equity: int = 100_000) -> dict:
    return {
        "scenario_id": "C085_G100",
        "collection_probability": 0.85,
        "recovery_rate_pct": 100,
        "trial_id": trial_id,
        "final_close_date": "2028-01-01",
        "final_net_project_equity": equity,
        "final_cash": 1200,
        "cumulative_project_profit": 2300,
        "operating_net_profit": 2400,
        "termination_count": 1,
        "secondary_cycle_count": 2,
        "owned_bikes": 3,
        "held_assets": 4,
        "total_operating_revenue": 5000,
        "bad_debt": 100,
        "guarantee_recovered": 200,
        "partner1_final_entitlement": equity * 70 // 100,
        "partner2_final_entitlement": equity - equity * 70 // 100,
    }


def payload(trial_id: int = 601) -> dict:
    result = row(trial_id)
    return {
        "scenario_id": "C085_G100", "trial_id": trial_id, "trial_result": result,
        "result_sha256": audit.row_sha(result), "source_sha": audit.SOURCE_SHA,
        "source_commit": audit.SOURCE_COMMIT, "master_seed": audit.MASTER_SEED,
        "run_id": 99999, "run_attempt": 1, "log_events": False,
        "origin": "new_stage12_gateb_n1200",
    }


def test_checkpoint_ranges_are_exact_and_cumulative():
    assert len(audit.SCENARIOS) == 20
    assert len(set(audit.SCENARIOS)) == 20
    assert list(audit.CUMULATIVE_IDS) == list(range(1, 601))
    assert list(audit.PREVIOUS_NEW_IDS) == list(range(551, 601))
    assert list(audit.NEW_IDS) == list(range(601, 1201))
    assert not set(audit.CUMULATIVE_IDS).intersection(audit.NEW_IDS)
    assert len(audit.NEW_IDS) == 600


def test_result_sha_is_stable_after_json_roundtrip():
    original = row()
    encoded = json.dumps(original, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    assert audit.row_sha(json.loads(encoded)) == audit.row_sha(original)


def test_ordered_map_is_order_independent_and_duplicate_safe():
    rows = [
        {"scenario_id": "C085_G100", "trial_id": 602, "result_sha256": "b" * 64},
        {"scenario_id": "C085_G100", "trial_id": 601, "result_sha256": "a" * 64},
    ]
    assert audit.ordered_map_sha(rows) == audit.ordered_map_sha(list(reversed(rows)))
    with pytest.raises(RuntimeError, match="DUPLICATE_SCENARIO_TRIAL_KEY"):
        audit.ordered_map_sha(rows + [rows[0]])


def test_new_payload_validates_source_and_hash():
    data = payload()
    audit.validate_trial_payload(data, "C085_G100", 601, expected_run_id=99999, expected_origin="new_stage12_gateb_n1200")
    data["result_sha256"] = "0" * 64
    with pytest.raises(RuntimeError, match="TRIAL_RESULT_SHA_MISMATCH"):
        audit.validate_trial_payload(data, "C085_G100", 601)


def test_n1200_payload_rejects_a_completed_trial_id():
    data = payload(600)
    with pytest.raises(RuntimeError, match="TRIAL_ROW_KEY_MISMATCH"):
        audit.validate_trial_payload(data, "C085_G100", 601)


def test_student_t_point_passes_and_uses_strict_comparison():
    values = [100_000 + ((i % 5) - 2) for i in range(1200)]
    point = audit.ci_point("C085_G100", "Final_Net_Project_Equity", "final_net_project_equity", values)
    assert point["n"] == 1200
    assert point["distribution"] == "Student-t"
    assert point["status"] == "PASS"
    assert point["ci_half_width_95"] < point["required_half_width"]


def test_near_zero_mean_is_held_as_undefined():
    point = audit.ci_point("C085_G100", "Final_Net_Project_Equity", "final_net_project_equity", [0] * 1200)
    assert point["status"] == "UNDEFINED_BUSINESS_RULE"
    assert point["required_half_width"] is None
