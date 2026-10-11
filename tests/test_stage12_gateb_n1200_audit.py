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




def test_prior_n1200_run_identity_must_be_exact_and_completed():
    good = {
        "id": audit.N1200_PRIOR_RUN_ID,
        "head_sha": audit.N1200_PRIOR_HEAD,
        "head_branch": audit.N1200_PRIOR_BRANCH,
        "run_attempt": audit.N1200_PRIOR_ATTEMPT,
        "status": "completed",
        "conclusion": "success",
    }
    assert audit.validate_prior_n1200_run_identity(good)["id"] == audit.N1200_PRIOR_RUN_ID

    # Cancellation is allowed only as a terminal state that will still undergo per-job and artifact auditing.
    cancelled = dict(good, conclusion="cancelled")
    assert audit.validate_prior_n1200_run_identity(cancelled)["conclusion"] == "cancelled"
    cancelled_not_finished = dict(cancelled, status="in_progress")
    with pytest.raises(RuntimeError, match="PRIOR_N1200_RUN_NOT_SAFELY_COMPLETED"):
        audit.validate_prior_n1200_run_identity(cancelled_not_finished)

    bad_head = dict(good, head_sha="0" * 40)
    with pytest.raises(RuntimeError, match="PRIOR_N1200_RUN_IDENTITY_MISMATCH"):
        audit.validate_prior_n1200_run_identity(bad_head)

    not_finished = dict(good, status="in_progress")
    with pytest.raises(RuntimeError, match="PRIOR_N1200_RUN_NOT_SAFELY_COMPLETED"):
        audit.validate_prior_n1200_run_identity(not_finished)


def _install_cancelled_prior_run_fixture(monkeypatch, missing_artifact_scenario: str | None = None):
    run = {
        "id": audit.N1200_PRIOR_RUN_ID,
        "head_sha": audit.N1200_PRIOR_HEAD,
        "head_branch": audit.N1200_PRIOR_BRANCH,
        "run_attempt": audit.N1200_PRIOR_ATTEMPT,
        "status": "completed",
        "conclusion": "cancelled",
        "created_at": "2026-10-11T21:51:19Z",
        "updated_at": "2026-10-11T22:10:30Z",
        "html_url": "https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/38178068848",
    }
    materialize_name = "Materialize only missing IDs 601–1200; restore same-run completed IDs first"
    jobs = []
    artifacts = []
    for index, scenario in enumerate(audit.SCENARIOS):
        started = index < 10
        job = {
            "name": f"Run only missing IDs 601–1200 — {scenario}",
            "status": "completed",
            "conclusion": "cancelled",
            "steps": ([{"name": materialize_name, "status": "completed", "conclusion": "cancelled"}] if started else []),
        }
        jobs.append(job)
        if started and scenario != missing_artifact_scenario:
            artifacts.append({
                "id": 20000 + index,
                "name": f"gateb-n1200-new-{scenario}-attempt-{audit.N1200_PRIOR_ATTEMPT}",
                "expired": False,
                "digest": "sha256:" + (f"{index + 1:064x}"[-64:]),
            })

    def fake_gh_json(endpoint: str):
        if endpoint == f"repos/{audit.REPO}/actions/runs/{audit.N1200_PRIOR_RUN_ID}":
            return run
        if endpoint == f"repos/{audit.REPO}/actions/runs/{audit.N1200_PRIOR_RUN_ID}/jobs?per_page=100":
            return {"total_count": len(jobs), "jobs": jobs}
        if endpoint == f"repos/{audit.REPO}/actions/runs/{audit.N1200_PRIOR_RUN_ID}/artifacts?per_page=100":
            return {"total_count": len(artifacts), "artifacts": artifacts}
        raise AssertionError(f"Unexpected GitHub API endpoint: {endpoint}")

    monkeypatch.setattr(audit, "gh_json", fake_gh_json)


def test_cancelled_prior_run_reuses_only_scenarios_with_artifacts(monkeypatch):
    _install_cancelled_prior_run_fixture(monkeypatch)
    evidence = audit.prior_n1200_run_evidence()
    assert evidence["run"]["conclusion"] == "cancelled"
    assert set(evidence["scenario_artifacts"]) == set(audit.SCENARIOS[:10])
    assert len(evidence["scenario_artifacts"]) == 10


def test_cancelled_prior_run_fails_closed_if_started_step_has_no_artifact(monkeypatch):
    missing = audit.SCENARIOS[3]
    _install_cancelled_prior_run_fixture(monkeypatch, missing_artifact_scenario=missing)
    with pytest.raises(RuntimeError, match=f"PRIOR_N1200_OUTPUT_ARTIFACT_MISSING_AFTER_TRIAL_STEP {missing}"):
        audit.prior_n1200_run_evidence()


def test_workflow_enables_all_scenario_jobs_with_exact_branch_pin():
    workflow_path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "gateb-historical-1200-verify.yml"
    workflow = workflow_path.read_text(encoding="utf-8")
    assert 'tmp/gateb-parallel20-n1200-20261012' in workflow
    assert "max-parallel: 20" in workflow
    assert "workflow_dispatch:" not in workflow
    assert 'tmp/**' not in workflow


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
