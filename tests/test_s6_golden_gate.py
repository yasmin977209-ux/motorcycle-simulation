from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import s6_golden_gate as gate


SOURCE_SHA = "a" * 40
COHORT_ID = f"s6-v23-{SOURCE_SHA[:8]}"
SCENARIO = "C085_G100"


def result(trial_id: int, *, scenario_id: str = SCENARIO, offset: int = 0):
    return SimpleNamespace(
        scenario_id=scenario_id,
        trial_id=trial_id,
        final_close_date="2028-01-01",
        final_net_project_equity=1000 + offset,
        final_cash=300 + offset,
        cumulative_project_profit=200 + offset,
        operating_net_profit=150 + offset,
        termination_count=2 + offset,
        secondary_cycle_count=1,
        owned_bikes=3,
        held_assets=1,
        total_operating_revenue=1800 + offset,
        bad_debt=20,
        guarantee_recovered=5,
        partner1_final_entitlement=650 + offset,
        partner2_final_entitlement=350 + offset,
        trial_fingerprint="",
    )


def make_evidence(tmp_path: Path, *, approve: bool = True):
    trial_count = 2
    scenarios = {}
    for scenario_id in sorted(gate.expected_stochastic_scenarios()):
        fingerprints = {
            "1": gate.monte_carlo.trial_fingerprint(result(1, scenario_id=scenario_id)),
            "2": gate.monte_carlo.trial_fingerprint(result(2, scenario_id=scenario_id, offset=1)),
        }
        scenarios[scenario_id] = {
            "trial_id_start": 1,
            "trial_id_end": trial_count,
            "trial_count": trial_count,
            "trial_fingerprints": fingerprints,
            "financial_trial_fingerprint_map_sha256": gate.scenario_fingerprint_map_sha256(
                scenario_id, fingerprints
            ),
            "rng_audit_map_sha256": "b" * 64,
            "complete_trial_result_audit_sha256": "c" * 64,
        }
    golden = {
        "schema_version": gate.STOCHASTIC_GOLDEN_SCHEMA,
        "status": gate.CANDIDATE_STATUS,
        "run_id": "GOLDEN-RUN-800",
        "source_sha": SOURCE_SHA,
        "cohort_id": COHORT_ID,
        "master_seed": 20270101,
        "model_schema_version": "v2.3",
        "scenario_count": 20,
        "trial_id_start": 1,
        "trial_id_end": trial_count,
        "trial_count_per_scenario": trial_count,
        "total_trial_fingerprints": 20 * trial_count,
        "independent_execution": True,
        "production_result_artifacts_read": False,
        "scenarios": scenarios,
    }
    golden_path = tmp_path / "golden-map.json"
    golden_path.write_text(json.dumps(golden, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    golden_sha = hashlib.sha256(golden_path.read_bytes()).hexdigest()
    approval = {
        "approval_status": gate.APPROVED_GOLDEN_STATUS if approve else "PENDING_REVIEW",
        "approval_schema_version": "s6-golden-approval-manifest-v1",
        "golden_run_id": "GOLDEN-RUN-800",
        "production_run_id": "PRODUCTION-RUN-900",
        "golden_schema_version": gate.STOCHASTIC_GOLDEN_SCHEMA,
        "candidate_map_sha256": golden_sha,
        "source_sha": SOURCE_SHA,
        "cohort_id": COHORT_ID,
        "master_seed": 20270101,
        "model_schema_version": "v2.3",
        "scenario_count": 20,
        "trial_count_per_scenario": trial_count,
        "independent_execution": True,
        "production_result_artifacts_read": False,
        "independent_manifest_sha256": "d" * 64,
        "source_tree_sha_verified": True,
        "scenario_ids": sorted(gate.expected_stochastic_scenarios()),
    }
    approval_path = tmp_path / "approval.json"
    approval_path.write_text(json.dumps(approval, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return golden_path, approval_path, golden, approval


def load(golden_path: Path, approval_path: Path):
    return gate.load_approved_stochastic_golden(
        golden_path,
        approval_path,
        source_sha=SOURCE_SHA,
        cohort_id=COHORT_ID,
        master_seed=20270101,
        required_trial_count=2,
        production_run_id="PRODUCTION-RUN-900",
    )


def test_gate_a_without_approved_golden_is_not_evaluated():
    evaluated = gate.evaluate_gate_a_point(
        SCENARIO,
        [result(1), result(2, offset=1)],
        n=2,
        source_sha=SOURCE_SHA,
        cohort_id=COHORT_ID,
        approved_golden=None,
    )
    assert evaluated["status"] == "NOT_EVALUATED_NO_APPROVED_SAME_SOURCE_GOLDEN"
    assert evaluated["checked"] is False


def test_approved_same_source_golden_exact_fingerprint_match_is_pass_scoped(tmp_path):
    golden_path, approval_path, _, _ = make_evidence(tmp_path)
    approved = load(golden_path, approval_path)
    evaluated = gate.evaluate_gate_a_point(
        SCENARIO,
        [result(1), result(2, offset=1)],
        n=2,
        source_sha=SOURCE_SHA,
        cohort_id=COHORT_ID,
        approved_golden=approved,
    )
    assert evaluated["status"] == "PASS_SCOPED"
    assert evaluated["checked"] is True
    assert evaluated["mismatches"] == 0
    assert evaluated["trial_count_compared"] == 2


def test_gate_a_financial_fingerprint_mismatch_fails(tmp_path):
    golden_path, approval_path, _, _ = make_evidence(tmp_path)
    approved = load(golden_path, approval_path)
    evaluated = gate.evaluate_gate_a_point(
        SCENARIO,
        [result(1), result(2, offset=2)],
        n=2,
        source_sha=SOURCE_SHA,
        cohort_id=COHORT_ID,
        approved_golden=approved,
    )
    assert evaluated["status"] == "FAIL_GOLDEN_FINANCIAL_FINGERPRINT_MISMATCH"
    assert evaluated["trial_id"] == 2


def test_gate_a_missing_or_noncontiguous_trial_ids_is_missing_evidence(tmp_path):
    golden_path, approval_path, _, _ = make_evidence(tmp_path)
    approved = load(golden_path, approval_path)
    evaluated = gate.evaluate_gate_a_point(
        SCENARIO,
        [result(1), result(3, offset=1)],
        n=2,
        source_sha=SOURCE_SHA,
        cohort_id=COHORT_ID,
        approved_golden=approved,
    )
    assert evaluated["status"] == "MISSING_EVIDENCE"


def test_gate_a_rejects_unapproved_candidate(tmp_path):
    golden_path, approval_path, _, _ = make_evidence(tmp_path, approve=False)
    with pytest.raises(gate.GoldenEvidenceError, match="GOLDEN_APPROVAL_STATUS_NOT_APPROVED"):
        load(golden_path, approval_path)


def test_gate_a_rejects_approval_map_hash_mismatch(tmp_path):
    golden_path, approval_path, _, approval = make_evidence(tmp_path)
    approval["candidate_map_sha256"] = "0" * 64
    approval_path.write_text(json.dumps(approval, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(gate.GoldenEvidenceError, match="GOLDEN_APPROVAL_MAP_SHA256_MISMATCH"):
        load(golden_path, approval_path)


def test_gate_a_rejects_wrong_source_identity(tmp_path):
    golden_path, approval_path, _, approval = make_evidence(tmp_path)
    approval["source_sha"] = "f" * 40
    approval_path.write_text(json.dumps(approval, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(gate.GoldenEvidenceError, match="GOLDEN_APPROVAL_IDENTITY_MISMATCH:source_sha"):
        load(golden_path, approval_path)


def test_gate_a_rejects_scenario_coverage_gap(tmp_path):
    golden_path, approval_path, golden, _ = make_evidence(tmp_path)
    golden["scenarios"].pop("C030_G000")
    golden_path.write_text(json.dumps(golden, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    approval["candidate_map_sha256"] = hashlib.sha256(golden_path.read_bytes()).hexdigest()
    approval_path.write_text(json.dumps(approval, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(gate.GoldenEvidenceError, match="GOLDEN_SCENARIO_COVERAGE_MISMATCH"):
        load(golden_path, approval_path)


def test_gate_a_rejects_using_the_production_run_as_its_own_golden(tmp_path):
    golden_path, approval_path, _, approval = make_evidence(tmp_path)
    approval["production_run_id"] = "GOLDEN-RUN-800"
    approval_path.write_text(json.dumps(approval, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(gate.GoldenEvidenceError, match="GOLDEN_PRODUCTION_SELF_REFERENCE_FORBIDDEN"):
        gate.load_approved_stochastic_golden(
            golden_path,
            approval_path,
            source_sha=SOURCE_SHA,
            cohort_id=COHORT_ID,
            master_seed=20270101,
            required_trial_count=2,
            production_run_id="GOLDEN-RUN-800",
        )


def test_scenario_map_digest_rejects_invalid_fingerprint():
    with pytest.raises(gate.GoldenEvidenceError, match="GOLDEN_FINANCIAL_FINGERPRINT_INVALID"):
        gate.scenario_fingerprint_map_sha256(SCENARIO, {"1": "not-a-sha256"})
