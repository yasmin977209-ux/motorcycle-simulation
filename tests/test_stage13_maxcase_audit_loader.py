from __future__ import annotations

import hashlib
import json

import pytest

from scripts.excel_builder import (
    MAXCASE_EXPECTED_SOURCE_IDENTITY,
    MAXCASE_REPLAY_EXPECTED_SOURCE_IDENTITY,
    MAXCASE_EXPECTED_STAGE12_GLOBAL_SHA256,
    MAXCASE_REPLAY_PLAN,
    MAXCASE_REPLAY_EXPECTED_ENGINE_BLOBS,
    _maxcase_role_from_audit,
    _maxcase_role_from_replay,
    _read_maxcase_audit_bundle,
    _read_maxcase_replay_bundle,
)
from scripts.stage13_assemble import _final_acceptance_disposition, _maxcase_pending_field_summary, EXPECTED_SCENARIOS


def _active_manifest():
    return {
        "source_sha": MAXCASE_EXPECTED_SOURCE_IDENTITY["source_sha"],
        "master_seed": MAXCASE_EXPECTED_SOURCE_IDENTITY["master_seed"],
        "reference_sha256": MAXCASE_EXPECTED_SOURCE_IDENTITY["reference_sha256"],
        "global_manifest_sha256": MAXCASE_EXPECTED_SOURCE_IDENTITY["stage9a_global_manifest_sha256"],
        "artifact_manifest": {
            "enriched_artifacts": {"C050_G000": 11503510055},
            "enrichment_run_ids": {"C050_G000": 37662891608},
        },
    }


def _source_row(scenario):
    return {
        "scenario_id": scenario,
        "trial_id": 1,
        "final_cash": 10,
        "final_net_project_equity": 20,
        "cumulative_project_profit": 30,
        "final_close_date": "2027-01-01",
        "collection_probability": 1.0,
        "recovery_rate_pct": 100,
        "partner1_final_entitlement": 14,
        "partner2_final_entitlement": 6,
        "operating_net_profit": 30,
        "total_operating_revenue": 35,
        "bad_debt": 0,
        "guarantee_recovered": 0,
        "held_assets": 0,
        "owned_bikes": 0,
        "secondary_cycle_count": 0,
        "termination_count": 0,
    }


def _one_day(scenario):
    return {
        "trial_id": 1,
        "date": "2027-01-01",
        "Final_Close_Date": "2027-01-01",
        "Cash": 10,
        "Net_Equity": 20,
        "Cumulative_Project_Profit": 30,
        "Active_Bikes": 0,
        "Owned_Transferred_Bikes": 0,
        "Pending_Claims": 0,
        "Partner1_Reinvestment_Balance": "PENDING_DATA_SOURCE",
        "Partner2_Reinvestment_Balance": "PENDING_DATA_SOURCE",
        "source_sha": MAXCASE_EXPECTED_SOURCE_IDENTITY["source_sha"],
        "master_seed": MAXCASE_EXPECTED_SOURCE_IDENTITY["master_seed"],
        "result_sha256": "a" * 64,
    }


def _bundle():
    now = "2026-10-24T00:00:00Z"
    report_scenarios = []
    payload_scenarios = []
    for scenario_index, scenario in enumerate(EXPECTED_SCENARIOS):
        summary = {
            "final_cash": 10,
            "final_net_project_equity": 20,
            "cumulative_project_profit": 30,
            "final_close_date": "2027-01-01",
            "trial_id": 1,
        }
        is_verified = scenario_index in (0, 5)
        selected_source = None
        if is_verified and scenario_index == 0:
            selected_source = {
                "artifact_id": 123,
                "artifact_name": f"stage9a06-enriched-{scenario}",
                "run_id": 37655041728,
                "run_head_sha": "b4a88a117fa7d7fcdc7718d6a475699e3e8ac47e",
                "run_conclusion": "failure (artifact validated individually; run-level success is not claimed)",
                "trial_id": 1,
                "trial_result_sha256": "a" * 64,
                "daily_row_count": 1,
                "artifact_zip_sha256": "b" * 64,
                "api_digest": "sha256:" + "b" * 64,
                "artifact_api_digest": "sha256:" + "b" * 64,
                "manifest_authorized_source": True,
                "metadata_sha256": "c" * 64,
                "trial_fingerprints_sha256": "e" * 64,
            }
        elif is_verified:
            selected_source = {
                "artifact_id": 124,
                "artifact_name": f"cp-f-replay-{scenario}",
                "run_id": 38619859394,
                "run_head_sha": "f7096bcc9f910df54a60d5a4329a7ebbcd2a43ae",
                "run_branch": "tmp/cp-f-delivery-20261014",
                "trial_id": 1,
                "trial_result_sha256": "a" * 64,
                "daily_row_count": 1,
                "artifact_zip_sha256": "b" * 64,
                "api_digest": "sha256:" + "b" * 64,
                "artifact_api_digest": "sha256:" + "b" * 64,
                "manifest_non_c100_gate_a_fingerprints_verified": True,
                "day_by_day_stage12_reconciliation": True,
                "historical_dataset_modified": False,
                "historical_parquet_modified": False,
                "production_monte_carlo_run": False,
                "partner_memo_fields_status": "VERIFIED_REUSED_SOURCE_ARTIFACT",
                "run_conclusion": "success",
                "scenario_manifest_sha256": "1" * 64,
                "representative_payload_member": "representatives/Max Case.json",
                "representative_payload_member_size_bytes": 100,
            }
        else:
            selected_source = {}
        day = _one_day(scenario)
        if is_verified:
            day["Partner1_Reinvestment_Balance"] = 14
            day["Partner2_Reinvestment_Balance"] = 6
        report_scenarios.append({
            "scenario": scenario,
            "maxcase_selection_status": "PASS",
            "maxcase_trial_id": 1,
            "maxcase_trial_result_sha256": "a" * 64,
            "trial_result_hashes": {"1": "a" * 64},
            "maxcase_summary": summary,
            "selected_daily_payload_source_verified": is_verified,
            "existing_payload_reusable_exactly": is_verified,
        })
        payload_scenarios.append({
            "scenario": scenario,
            "case": "Max Case",
            "trial_id": 1,
            "final_cash": 10,
            "final_net_project_equity": 20,
            "cumulative_project_profit": 30,
            "partner_memo_fields_status": "VERIFIED_REUSED_SOURCE_ARTIFACT" if is_verified else "MISSING_EVIDENCE",
            "partner_memo_fields": ["Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance"],
            "selected_daily_payload_artifact": selected_source,
            "daily_rows": [day],
        })
    summary = {
        "scenario_count": 25,
        "expected_trial_rows": 11005,
        "actual_trial_rows": 11005,
        "trial_rows_rehashed": 11005,
        "maxcase_positive_selected": 25,
        "undefined_business_rule_scenarios": [],
        "stage12_daily_rows_validated": 22546465,
        "stage12_daily_scenarios_validated": 25,
        "maxcase_daily_rows_extracted": 25,
        "representative_inventory_provenance_mismatch_count": 0,
        "representative_inventory_provenance_mismatch_scenarios": [],
        "non_c100_maxcase_payloads_missing_partner_memo_source": EXPECTED_SCENARIOS,
    }
    stage7_run = {
        "conclusion": "success",
        "created_at": "2026-10-04T18:49:34Z",
        "head_branch": "tmp/stage7-full-run-20261004",
        "head_sha": "e0b2fab6710833774937d778097363d7a8ee8e59",
        "html_url": "https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/37225915321",
        "id": 37225915321,
        "status": "completed",
    }
    stage10_run = {
        "conclusion": "failure",
        "created_at": "2026-10-08T00:51:32Z",
        "head_branch": "tmp/stage10-bench-20261008",
        "head_sha": "ca73f2df37baacebbcad965fc5f433f129675820",
        "html_url": "https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/37709936740",
        "id": 37709936740,
        "status": "completed",
    }
    stage12_run = {
        "conclusion": "success",
        "created_at": "2026-10-09T17:12:48Z",
        "head_branch": "tmp/stage12-b3-25jobs-20261009",
        "head_sha": "0156c5f4272eb0ca7e32442657d0df9eaf4973d3",
        "html_url": "https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/37964656154",
        "id": 37964656154,
        "status": "completed",
    }
    cpf_run = {
        "conclusion": "success",
        "created_at": "2026-10-14T18:59:29Z",
        "head_branch": "tmp/cp-f-delivery-20261014",
        "head_sha": "f7096bcc9f910df54a60d5a4329a7ebbcd2a43ae",
        "html_url": "https://github.com/yasmin977209-ux/motorcycle-simulation/actions/runs/38619859394",
        "id": 38619859394,
        "status": "completed",
    }
    audit = {
        "schema_version": "stage13-maxcase-source-audit-v1",
        "created_at_utc": now,
        "repository": "yasmin977209-ux/motorcycle-simulation",
        "tested_head_sha": "c00b48912e10cc0334dfb0d7bb3c3741eb002315",
        "runs": {
            "stage7": stage7_run,
            "stage10": stage10_run,
            "stage12": stage12_run,
            "cp_f_delivery_detail_replay": cpf_run,
            "stage10_aggregate_job_conclusion": "failure",
            "stage10_successful_benchmark_job_count": 45,
        },
        "source_identity": MAXCASE_EXPECTED_SOURCE_IDENTITY,
        "integrity_status": "PASS_SCOPED",
        "payload_status": "MISSING_EVIDENCE",
        "simulation_or_trial_executed": False,
        "historical_dataset_modified": False,
        "historical_artifacts_modified": False,
        "workbook_built": False,
        "summary": summary,
        "stage12_daily_validation": {
            "scenarios_validated": 25,
            "daily_rows_validated": 22546465,
            "trial_result_fingerprint_mismatches": 0,
        },
        "representative_inventory_provenance": {"mismatch_count": 0, "mismatches": [], "status": "PASS"},
        "scenarios": report_scenarios,
    }
    payloads = {
        "schema_version": "stage13-maxcase-daily-payloads-v1",
        "created_at_utc": now,
        "repository": "yasmin977209-ux/motorcycle-simulation",
        "tested_head_sha": "c00b48912e10cc0334dfb0d7bb3c3741eb002315",
        "source_identity": MAXCASE_EXPECTED_SOURCE_IDENTITY,
        "stage12_run": stage12_run,
        "stage12_global_sha256": MAXCASE_EXPECTED_STAGE12_GLOBAL_SHA256,
        "scenario_count": 25,
        "maxcase_daily_rows": 25,
        "missing_fields": ["Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance"],
        "missing_fields_status": "PARTIALLY_AVAILABLE_AND_PARTIALLY_MISSING",
        "scenarios": payload_scenarios,
    }
    return audit, payloads


def _write_json(tmp_path, name, value):
    path = tmp_path / name
    path.write_text(json.dumps(value, sort_keys=True), encoding="utf-8")
    return path, hashlib.sha256(path.read_bytes()).hexdigest()


def test_maxcase_audit_bundle_requires_matching_digest_pins_and_pair_identity(tmp_path):
    audit, payloads = _bundle()
    audit_path, audit_sha = _write_json(tmp_path, "audit.json", audit)
    payload_path, payload_sha = _write_json(tmp_path, "payloads.json", payloads)
    manifest = _active_manifest()
    result = _read_maxcase_audit_bundle(
        audit_path, payload_path,
        audit_sha256=audit_sha, payloads_sha256=payload_sha, manifest=manifest,
        manifest_git_blob_sha=MAXCASE_EXPECTED_SOURCE_IDENTITY["stage9a_manifest_git_blob"],
    )
    assert len(result["payloads_by_scenario"]) == 25
    assert result["metadata"]["payload_status"] == "MISSING_EVIDENCE"
    with pytest.raises(RuntimeError, match="MAXCASE_PAYLOADS_DIGEST_MISMATCH"):
        _read_maxcase_audit_bundle(
            audit_path, payload_path,
            audit_sha256=audit_sha, payloads_sha256="0" * 64, manifest=manifest,
        )


def test_maxcase_payload_pair_rejects_different_scenario_or_selected_trial():
    audit, payloads = _bundle()
    first = EXPECTED_SCENARIOS[0]
    payloads["scenarios"][0]["trial_id"] = 2
    audit["scenarios"][0]["maxcase_trial_id"] = 2
    payloads["scenarios"][0]["daily_rows"][0]["trial_id"] = 2
    audit["scenarios"][0]["trial_result_hashes"]["2"] = "a" * 64
    payload_path_hash_input = json.dumps(payloads).encode()
    # The same-source pair still has to fail because the canonical selection map is binding
    # at role-construction time, not because an arbitrary CP-F ID was accepted.
    row = _source_row(first)
    with pytest.raises(RuntimeError, match="MAXCASE_SELECTED_TRIAL_MISMATCH"):
        _maxcase_role_from_audit(
            first, [row], payloads["scenarios"][0], audit["scenarios"][0],
        )


def test_final_acceptance_report_counts_pending_required_maxcase_cells():
    data = {
        "C100_G100": {
            "Max Case": {
                "daily": [{
                    "Retained_Earnings": 30,
                    "Partner1_Reinvestment_Balance": "PENDING_DATA_SOURCE",
                    "Partner2_Reinvestment_Balance": None,
                }]
            }
        }
    }
    result = _maxcase_pending_field_summary(data)
    assert result["count"] == 2
    assert result["by_scenario"] == {"C100_G100": 2}
    assert result["by_field"] == {
        "Partner1_Reinvestment_Balance": 1,
        "Partner2_Reinvestment_Balance": 1,
    }


def test_final_acceptance_report_does_not_call_complete_payload_final_release():
    data = {
        scenario: {
            "Max Case": {
                "daily": [{
                    "Retained_Earnings": 30,
                    "Cumulative_Project_Profit": 30,
                    "Partner1_Reinvestment_Balance": 14,
                    "Partner2_Reinvestment_Balance": 6,
                }]
            }
        }
        for scenario in EXPECTED_SCENARIOS
    }
    result = _maxcase_pending_field_summary(data)
    assert result["count"] == 0


def test_build_success_never_implies_final_acceptance():
    pending = {"count": 0, "by_scenario": {}, "by_field": {}}
    complete_audit = {
        "representative_inventory_mismatch_count": 0,
        "payload_status": "EXISTING_PAYLOADS_REUSABLE",
    }
    result = _final_acceptance_disposition(pending, complete_audit)
    assert result["final_acceptance_status"] == "NOT_FINAL_BLOCKED"
    assert result["final_acceptance_blockers"] == ["GOVERNANCE_RELEASE_GATE_NOT_RUN"]


def test_final_acceptance_reports_missing_memo_fields_and_manifest_conflict():
    pending = {"count": 2, "by_scenario": {"C050_G000": 2}, "by_field": {"Partner1_Reinvestment_Balance": 1, "Partner2_Reinvestment_Balance": 1}}
    audit = {
        "representative_inventory_mismatch_count": 1,
        "payload_status": "MISSING_EVIDENCE",
    }
    result = _final_acceptance_disposition(pending, audit)
    assert result["final_acceptance_status"] == "NOT_FINAL_BLOCKED"
    assert "PENDING_REQUIRED_MAXCASE_DAILY_FIELDS" in result["final_acceptance_blockers"]
    assert "REPRESENTATIVE_INVENTORY_PROVENANCE_MISMATCH" in result["final_acceptance_blockers"]
    assert "MAXCASE_PAYLOAD_EVIDENCE_INCOMPLETE" in result["final_acceptance_blockers"]


def test_maxcase_verified_stage9a_source_requires_explicit_manifest_authorization(tmp_path):
    audit, payloads = _bundle()
    first = payloads["scenarios"][0]
    first["selected_daily_payload_artifact"]["manifest_authorized_source"] = False
    ap, ah = _write_json(tmp_path, "audit.json", audit)
    pp, ph = _write_json(tmp_path, "payloads.json", payloads)
    manifest = _active_manifest()
    with pytest.raises(RuntimeError, match="MAXCASE_AUDIT_SOURCE_PROVENANCE_MISMATCH"):
        _read_maxcase_audit_bundle(
            ap, pp, audit_sha256=ah, payloads_sha256=ph, manifest=manifest,
            manifest_git_blob_sha=MAXCASE_EXPECTED_SOURCE_IDENTITY["stage9a_manifest_git_blob"],
        )


def test_maxcase_verified_cpf_source_requires_reconciliation_and_gatea_proof(tmp_path):
    audit, payloads = _bundle()
    scenario = EXPECTED_SCENARIOS[5]
    item = next(row for row in payloads["scenarios"] if row["scenario"] == scenario)
    item["partner_memo_fields_status"] = "VERIFIED_REUSED_SOURCE_ARTIFACT"
    item["daily_rows"][0]["Partner1_Reinvestment_Balance"] = 14
    item["daily_rows"][0]["Partner2_Reinvestment_Balance"] = 6
    item["selected_daily_payload_artifact"] = {
        "artifact_id": 124,
        "artifact_name": f"cp-f-replay-{scenario}",
        "run_id": 38619859394,
        "run_head_sha": "f7096bcc9f910df54a60d5a4329a7ebbcd2a43ae",
        "run_branch": "tmp/cp-f-delivery-20261014",
        "trial_id": 1,
        "trial_result_sha256": "a" * 64,
        "daily_row_count": 1,
        "artifact_zip_sha256": "b" * 64,
        "api_digest": "sha256:" + "b" * 64,
        "artifact_api_digest": "sha256:" + "b" * 64,
        "manifest_non_c100_gate_a_fingerprints_verified": False,
        "day_by_day_stage12_reconciliation": True,
        "historical_dataset_modified": False,
        "historical_parquet_modified": False,
        "production_monte_carlo_run": False,
        "partner_memo_fields_status": "VERIFIED_REUSED_SOURCE_ARTIFACT",
        "run_conclusion": "success",
        "scenario_manifest_sha256": "1" * 64,
        "representative_payload_member": "representatives/Max Case.json",
        "representative_payload_member_size_bytes": 100,
    }
    audit_item = next(row for row in audit["scenarios"] if row["scenario"] == scenario)
    audit_item["selected_daily_payload_source_verified"] = True
    audit_item["existing_payload_reusable_exactly"] = True
    ap, ah = _write_json(tmp_path, "audit.json", audit)
    pp, ph = _write_json(tmp_path, "payloads.json", payloads)
    manifest = _active_manifest()
    with pytest.raises(RuntimeError, match="MAXCASE_AUDIT_SOURCE_PROVENANCE_MISMATCH"):
        _read_maxcase_audit_bundle(
            ap, pp, audit_sha256=ah, payloads_sha256=ph, manifest=manifest,
            manifest_git_blob_sha=MAXCASE_EXPECTED_SOURCE_IDENTITY["stage9a_manifest_git_blob"],
        )


def test_maxcase_audit_rejects_unpinned_audit_execution_head(tmp_path):
    audit, payloads = _bundle()
    audit["tested_head_sha"] = "d" * 40
    payloads["tested_head_sha"] = "d" * 40
    ap, ah = _write_json(tmp_path, "audit.json", audit)
    pp, ph = _write_json(tmp_path, "payloads.json", payloads)
    manifest = _active_manifest()
    with pytest.raises(RuntimeError, match="MAXCASE_AUDIT_EXECUTION_HEAD_NOT_APPROVED"):
        _read_maxcase_audit_bundle(
            ap, pp, audit_sha256=ah, payloads_sha256=ph, manifest=manifest,
            manifest_git_blob_sha=MAXCASE_EXPECTED_SOURCE_IDENTITY["stage9a_manifest_git_blob"],
        )


def _replay_fixture(plan=None):
    plan = plan or MAXCASE_REPLAY_PLAN
    audit_by, payload_by, replay_scenarios = {}, {}, []
    for scenario, spec in plan.items():
        trial_id, trial_hash = spec["trial_id"], spec["trial_result_sha256"]
        close_date = "2027-01-01"
        summary = {
            "scenario_id": scenario,
            "trial_id": trial_id,
            "final_cash": 10,
            "final_net_project_equity": 20,
            "cumulative_project_profit": 30,
            "final_close_date": close_date,
            "collection_probability": int(scenario[1:4]) / 100,
            "recovery_rate_pct": int(scenario.split("_G")[1]),
            "partner1_final_entitlement": 14,
            "partner2_final_entitlement": 6,
            "operating_net_profit": 30,
            "total_operating_revenue": 35,
            "bad_debt": 0,
            "guarantee_recovered": 0,
            "held_assets": 0,
            "owned_bikes": 0,
            "secondary_cycle_count": 0,
            "termination_count": 0,
        }
        replay_day = {
            "trial_id": trial_id,
            "date": close_date,
            "Final_Close_Date": close_date,
            "Cash": 10,
            "Net_Equity": 20,
            "Cumulative_Project_Profit": 30,
            "Active_Bikes": 0,
            "Owned_Transferred_Bikes": 0,
            "Pending_Claims": 0,
            "Partner1_Reinvestment_Balance": 14,
            "Partner2_Reinvestment_Balance": 6,
            "source_sha": MAXCASE_EXPECTED_SOURCE_IDENTITY["source_sha"],
            "master_seed": MAXCASE_EXPECTED_SOURCE_IDENTITY["master_seed"],
            "result_sha256": trial_hash,
        }
        source_day = {
            **replay_day,
            "Partner1_Reinvestment_Balance": "PENDING_DATA_SOURCE",
            "Partner2_Reinvestment_Balance": "PENDING_DATA_SOURCE",
        }
        audit_by[scenario] = {
            "scenario": scenario,
            "maxcase_selection_status": "PASS",
            "maxcase_trial_id": trial_id,
            "maxcase_trial_result_sha256": trial_hash,
            "trial_result_hashes": {str(trial_id): trial_hash},
            "maxcase_summary": dict(summary),
            "selected_daily_payload_source_verified": False,
            "existing_payload_reusable_exactly": False,
        }
        payload_by[scenario] = {
            "scenario": scenario,
            "case": "Max Case",
            "trial_id": trial_id,
            "partner_memo_fields_status": "MISSING_EVIDENCE",
            "daily_rows": [source_day],
        }
        replay_scenarios.append({
            "scenario": scenario,
            "trial_id": trial_id,
            "trial_result_sha256": trial_hash,
            "status": "PASS_EXACT_REPLAY_AND_STAGE12_COMMON_FIELDS",
            "daily_row_count": 1,
            "first_date": close_date,
            "final_close_date": close_date,
            "summary": dict(summary),
            "comparison_contract": {
                "stage12_trial_result_hash_equal": True,
                "all_daily_common_fields_equal": True,
                "dates_consecutive": True,
                "memo_balances_integer_nonnegative": True,
            },
            "daily_rows": [replay_day],
        })
    audit_bundle = {
        "audit_by_scenario": audit_by,
        "payloads_by_scenario": payload_by,
        "metadata": {
            "missing_memo_scenarios": list(plan),
            "source_identity": MAXCASE_EXPECTED_SOURCE_IDENTITY,
        },
    }
    recovery = {
        "schema_version": "stage13-maxcase-replay-recovery-v1",
        "repository": "yasmin977209-ux/motorcycle-simulation",
        "status": "PASS",
        "owner_authorization": "EXPLICIT_USER_DELEGATION_2026-10-24_FOR_BOUNDED_EXACT_TRIAL_REPLAY",
        "pinned_source_commit": MAXCASE_EXPECTED_SOURCE_IDENTITY["source_sha"],
        "source_identity": MAXCASE_REPLAY_EXPECTED_SOURCE_IDENTITY,
        "pinned_engine_git_blobs": MAXCASE_REPLAY_EXPECTED_ENGINE_BLOBS,
        "input_artifacts": {
            "audit_artifact_id": 12537818827,
            "audit_run_id": 40038112945,
            "audit_artifact_zip_sha256": "88abdc9e0ce4097df044280b517f08b1595642476c8d596ac13fc128b88092b3",
            "audit_json_sha256": "b9ba0ff23b3dfd42abd7436b7935017f15ba8cbaf5198d8e31093a56441fb951",
            "payloads_json_sha256": "096a85448ff5c7ece0648739fdc4ccad499763f1862467751983e0152f8e8c7d",
            "stage12_global_sha256": MAXCASE_EXPECTED_STAGE12_GLOBAL_SHA256,
            "stage12_daily_rows_validated_before_replay": 22546465,
            "stage12_trial_fingerprint_mismatches_before_replay": 0,
            "source_audit_tested_head_sha": "c00b48912e10cc0334dfb0d7bb3c3741eb002315",
            "source_audit_integrity_status": "PASS_SCOPED",
            "source_audit_payload_status_before_replay": "MISSING_EVIDENCE",
        },
        "execution": {
            "selected_trials_expected": 10,
            "selected_trials_replayed": 10,
            "successful_trials": 10,
            "new_trial_ids_created": False,
            "canonical_stage12_files_modified": False,
            "source_artifacts_modified": False,
            "random_seed_or_rng_changed": False,
            "production_workbook_built": False,
            "monte_carlo_expansion_run": False,
            "checkpoint_run": False,
        },
        "summary": {
            "expected_scenarios": 10,
            "passed_scenarios": list(plan),
            "failed_scenarios": [],
            "recovered_daily_rows": sum(item["daily_rows"] for item in plan.values()),
            "source_trial_hash_mismatches": 0,
            "stage12_common_field_mismatches": 0,
        },
        "scenarios": replay_scenarios,
        "errors": [],
    }
    return audit_bundle, recovery


def test_exact_replay_bundle_is_digest_pinned_and_bound_to_original_audit(tmp_path, monkeypatch):
    import scripts.excel_builder as builder
    plan = {name: {**spec, "daily_rows": 1} for name, spec in MAXCASE_REPLAY_PLAN.items()}
    monkeypatch.setattr(builder, "MAXCASE_REPLAY_PLAN", plan)
    monkeypatch.setattr(builder, "MAXCASE_REPLAY_RECOVERED_ROWS", 10)
    audit_bundle, recovery = _replay_fixture(plan)
    path, digest = _write_json(tmp_path, "recovery.json", recovery)
    monkeypatch.setattr(builder, "MAXCASE_REPLAY_EXPECTED_JSON_SHA256", digest)
    manifest = _active_manifest()
    result = _read_maxcase_replay_bundle(
        path, replay_sha256=digest, manifest=manifest,
        manifest_git_blob_sha=MAXCASE_EXPECTED_SOURCE_IDENTITY["stage9a_manifest_git_blob"],
        audit_bundle=audit_bundle,
    )
    assert set(result["payloads_by_scenario"]) == set(MAXCASE_REPLAY_PLAN)
    assert result["metadata"]["replay_recovery_status"] == "PASS_EXACT_REPLAY"
    assert result["metadata"]["replay_covers_all_missing_memo_scenarios"] is True


def test_exact_replay_bundle_rejects_one_mismatched_stage12_common_field(tmp_path, monkeypatch):
    import scripts.excel_builder as builder
    plan = {name: {**spec, "daily_rows": 1} for name, spec in MAXCASE_REPLAY_PLAN.items()}
    monkeypatch.setattr(builder, "MAXCASE_REPLAY_PLAN", plan)
    monkeypatch.setattr(builder, "MAXCASE_REPLAY_RECOVERED_ROWS", 10)
    audit_bundle, recovery = _replay_fixture(plan)
    recovery["scenarios"][0]["daily_rows"][0]["Cash"] = 11
    path, digest = _write_json(tmp_path, "recovery-bad.json", recovery)
    monkeypatch.setattr(builder, "MAXCASE_REPLAY_EXPECTED_JSON_SHA256", digest)
    manifest = _active_manifest()
    with pytest.raises(RuntimeError, match="MAXCASE_REPLAY_STAGE12_COMMON_FIELD_MISMATCH"):
        _read_maxcase_replay_bundle(
            path, replay_sha256=digest, manifest=manifest,
        manifest_git_blob_sha=MAXCASE_EXPECTED_SOURCE_IDENTITY["stage9a_manifest_git_blob"],
        audit_bundle=audit_bundle,
        )


def test_exact_replay_role_constructor_rechecks_selected_trial_id():
    audit_bundle, recovery = _replay_fixture()
    scenario = next(iter(MAXCASE_REPLAY_PLAN))
    item = recovery["scenarios"][0]
    row = dict(item["summary"])
    role = _maxcase_role_from_replay(
        scenario, [row], item, audit_bundle["audit_by_scenario"][scenario],
    )
    assert role["summary"]["trial_id"] == item["trial_id"]
    assert role["daily"][0]["Partner1_Reinvestment_Balance"] == 14
    with pytest.raises(RuntimeError, match="MAXCASE_REPLAY_SELECTED_TRIAL_MISMATCH"):
        _maxcase_role_from_replay(
            scenario, [{**row, "trial_id": item["trial_id"] + 1}], item,
            audit_bundle["audit_by_scenario"][scenario],
        )


def test_final_gate_drops_only_recovered_memo_blocker_and_retains_release_blockers():
    pending = {"count": 0, "by_scenario": {}, "by_field": {}}
    audit = {
        "representative_inventory_mismatch_count": 1,
        "payload_status": "MISSING_EVIDENCE",
        "replay_recovery_status": "PASS_EXACT_REPLAY",
        "replay_covers_all_missing_memo_scenarios": True,
        "replay_selected_trial_sha256_mismatches": 0,
        "replay_stage12_common_field_mismatches": 0,
    }
    result = _final_acceptance_disposition(pending, audit)
    assert result["final_acceptance_status"] == "NOT_FINAL_BLOCKED"
    assert "MAXCASE_PAYLOAD_EVIDENCE_INCOMPLETE" not in result["final_acceptance_blockers"]
    assert "REPRESENTATIVE_INVENTORY_PROVENANCE_MISMATCH" in result["final_acceptance_blockers"]
    assert "GOVERNANCE_RELEASE_GATE_NOT_RUN" in result["final_acceptance_blockers"]


def test_active_stage9a_manifest_pin_is_separate_from_historical_replay_identity():
    from scripts.excel_builder import _validate_active_stage9a_manifest

    current_manifest = _active_manifest()
    current_sha = MAXCASE_EXPECTED_SOURCE_IDENTITY["stage9a_manifest_git_blob"]
    old_replay_sha = MAXCASE_REPLAY_EXPECTED_SOURCE_IDENTITY["stage9a_manifest_git_blob"]
    assert current_sha == "c8591aac3d309fd94c4e67a547d33fb62ac5694d"
    assert old_replay_sha == "e796fa2443493b607f1f9c60b58eb63607959c26"
    assert _validate_active_stage9a_manifest(current_manifest, manifest_git_blob_sha=current_sha) is None
    with pytest.raises(RuntimeError, match="MAXCASE_ACTIVE_MANIFEST_GIT_BLOB_MISMATCH"):
        _validate_active_stage9a_manifest(current_manifest, manifest_git_blob_sha=old_replay_sha)


def test_current_manifest_must_keep_approved_c050_artifact_and_run_pointer():
    from scripts.excel_builder import _validate_active_stage9a_manifest

    current_manifest = _active_manifest()
    current_manifest["artifact_manifest"]["enriched_artifacts"]["C050_G000"] = MAXCASE_EXPECTED_C050_POINTER_PREVIOUS_ARTIFACT_ID
    with pytest.raises(RuntimeError, match="MAXCASE_ACTIVE_MANIFEST_IDENTITY_OR_C050_POINTER_MISMATCH"):
        _validate_active_stage9a_manifest(
            current_manifest,
            manifest_git_blob_sha=MAXCASE_EXPECTED_SOURCE_IDENTITY["stage9a_manifest_git_blob"],
        )
