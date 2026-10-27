from dataclasses import replace
from types import SimpleNamespace
import hashlib
import subprocess
import json
import pyarrow as pa
import pyarrow.parquet as pq
from monte_carlo import TrialResult
import pytest
from scripts import s6_first_checkpoint as s6


def test_n_unique_paths_uses_daily_paths_not_terminal_fingerprints():
    from stats_integrity import resolve_n_unique_paths
    assert resolve_n_unique_paths("C070_G100", [1, 2, 3], 3) == 3
    assert resolve_n_unique_paths("C100_G100", [0, 0, 0], 1) == 1
    assert s6.reported_unique_path_evidence({}, 3, 3) == (None, "UNDEFINED_BUSINESS_RULE")
    assert s6.reported_unique_path_evidence(
        {"n_unique_paths": 3, "unique_daily_paths": 3,
         "n_unique_paths_status": "COMPUTED_UNIQUE_DAILY_PATHS"}, 3, 3
    ) == (3, "COMPUTED_UNIQUE_DAILY_PATHS")
    with pytest.raises(RuntimeError, match="STOCHASTIC_RNG_DRAWS_REQUIRED"):
        resolve_n_unique_paths("C085_G100", [1, 0], 2)
    with pytest.raises(RuntimeError, match="C100_DETERMINISTIC_PATH_CONTRACT_VIOLATION"):
        resolve_n_unique_paths("C100_G100", [0, 0], 2)

def test_s6_first_checkpoint_has_twenty_stochastic_scenarios_and_excludes_c100():
    scenarios=s6.stochastic_scenario_ids()
    assert len(scenarios)==20
    assert all(not s.startswith("C100_") for s in scenarios)
    assert "C100_G100" not in scenarios

def test_s6_opt1_is_enabled_only_for_c085_and_c070():
    assert s6.OPT1_ENABLED_COLLECTIONS==frozenset({85,70})
    assert 50 not in s6.OPT1_ENABLED_COLLECTIONS and 30 not in s6.OPT1_ENABLED_COLLECTIONS


def test_s6_aggregate_reconstructs_opt1_command_only_for_eligible_lower_g():
    eligible=s6.reconstructed_scenario_command("C085_G070","a"*40,"40574326793",1,300,2)
    ineligible=s6.reconstructed_scenario_command("C050_G070","a"*40,"40574326793",1,300,2)
    assert eligible[-2:]==["--base-dir","results_stage7_s6/base"]
    assert "--base-dir" not in ineligible

def test_s6_c100_reuse_is_hash_verified_and_read_only(monkeypatch,tmp_path):
    golden=tmp_path/"golden.json"; manifest=tmp_path/"manifest.json"
    golden.write_text("golden")
    manifest.write_text(json.dumps({
      "workflow_run_id":"40263424595","source_sha":"965281d52441cd0d4b744e211c9f68ee4cdc3753",
      "cohort_id":"c100-v23-s4-20261026-965281d5",
      "scenario_ids":["C100_G100","C100_G070","C100_G050","C100_G030","C100_G000"],
      "trial_ids_per_scenario":[1,300],"N_unique_paths":1,
      "degeneracy_status":"DEGENERATE_DETERMINISTIC","G_status":"G_INERT"
    }))
    monkeypatch.setattr(s6,"C100_GOLDEN_PATH",golden)
    monkeypatch.setattr(s6,"C100_MANIFEST_PATH",manifest)
    monkeypatch.setattr(s6,"EXPECTED_C100_GOLDEN_SHA256",s6.sha256_file(golden))
    monkeypatch.setattr(s6,"EXPECTED_C100_MANIFEST_SHA256",s6.sha256_file(manifest))
    reused=s6.verify_c100_reuse()
    assert reused["rerun"] is False
    assert reused["scenario_ids"]==["C100_G100","C100_G070","C100_G050","C100_G030","C100_G000"]
    assert reused["trial_count_per_scenario"]==300
    assert reused["cohort_id"]=="c100-v23-s4-20261026-965281d5"
    assert reused["n_unique_paths"]==1

def test_s6_c100_reuse_rejects_hash_mismatch(monkeypatch,tmp_path):
    golden=tmp_path/"golden.json"; manifest=tmp_path/"manifest.json"
    golden.write_text("changed"); manifest.write_text("manifest")
    monkeypatch.setattr(s6,"C100_GOLDEN_PATH",golden)
    monkeypatch.setattr(s6,"C100_MANIFEST_PATH",manifest)
    monkeypatch.setattr(s6,"EXPECTED_C100_GOLDEN_SHA256","0"*64)
    monkeypatch.setattr(s6,"EXPECTED_C100_MANIFEST_SHA256",s6.sha256_file(manifest))
    with pytest.raises(RuntimeError,match="S6_C100_GOLDEN_REUSE_SHA256_MISMATCH"): s6.verify_c100_reuse()

def test_s6_opt1_derived_result_keeps_financial_fingerprint():
    base=TrialResult(scenario_id="C085_G100",collection_probability=0.85,recovery_rate_pct=100,trial_id=1,
      final_close_date="2028-01-01",final_net_project_equity=100,final_cash=20,cumulative_project_profit=30,
      operating_net_profit=25,termination_count=1,secondary_cycle_count=0,owned_bikes=0,held_assets=0,
      total_operating_revenue=100,bad_debt=0,guarantee_recovered=0,partner1_final_entitlement=70,
      partner2_final_entitlement=30,claims_created=0)
    derived=replace(base,scenario_id="C085_G070",recovery_rate_pct=70,trial_fingerprint="")
    derived=replace(derived,trial_fingerprint=s6.monte_carlo.trial_fingerprint(derived))
    assert s6.monte_carlo.trial_fingerprint(base)==s6.monte_carlo.trial_fingerprint(derived)


def test_s6_aggregate_accepts_twenty_current_scenarios_and_separate_c100_reuse(monkeypatch,tmp_path):
    source_sha="a"*40
    source_run_id="40574326793"
    checkpoint_n=s6.constants.STATISTICAL_CHECK_START_N
    artifacts=tmp_path/"artifacts"
    artifacts.mkdir()
    golden=tmp_path/"c100_golden.json"
    c100_manifest=tmp_path/"c100_manifest.json"
    golden.write_text('{"golden":"immutable-test-fixture"}')
    c100_manifest.write_text(json.dumps({
      "workflow_run_id":"40263424595",
      "source_sha":"965281d52441cd0d4b744e211c9f68ee4cdc3753",
      "cohort_id":"c100-v23-s4-20261026-965281d5",
      "scenario_ids":["C100_G000","C100_G030","C100_G050","C100_G070","C100_G100"],
      "trial_ids_per_scenario":[1,checkpoint_n],"N_unique_paths":1,
      "degeneracy_status":"DEGENERATE_DETERMINISTIC","G_status":"G_INERT"
    }))
    monkeypatch.setattr(s6,"C100_GOLDEN_PATH",golden)
    monkeypatch.setattr(s6,"C100_MANIFEST_PATH",c100_manifest)
    monkeypatch.setattr(s6,"EXPECTED_C100_GOLDEN_SHA256",s6.sha256_file(golden))
    monkeypatch.setattr(s6,"EXPECTED_C100_MANIFEST_SHA256",s6.sha256_file(c100_manifest))

    for scenario in sorted(s6.stochastic_scenario_ids()):
        base=artifacts/f"s6-n300-{scenario}-{source_run_id}"
        base.mkdir()
        collection=int(scenario.split("_",1)[0][1:])
        recovery=int(scenario.split("_",1)[1][1:])
        base_scenario=f"C{collection:03d}_G100"
        derived_from=f"DERIVED_FROM={base_scenario}" if collection in {70,85} and recovery!=100 else None
        if recovery==100:
            policy="G100_BASE_FULL_RUN_INCREMENTAL_RANGE"
        elif collection in {70,85}:
            policy="OPT1_ENABLED_DERIVED_ZERO_CLAIM_TRIALS_FULL_RUN_POSITIVE_CLAIM_TRIALS_INCREMENTAL_RANGE"
        else:
            policy="OPT1_INELIGIBLE_FULL_RUN_INCREMENTAL_RANGE"
        trial_rows=[]
        for tid in range(1,checkpoint_n+1):
            fingerprint_scenario=base_scenario if derived_from else scenario
            fp=hashlib.sha256(f"{fingerprint_scenario}|{tid}".encode()).hexdigest()
            if collection==70 and tid==2:
                fp=hashlib.sha256("C070_G100|1".encode()).hexdigest()
            trial_rows.append({"trial_id":tid,"final_close_date":None,"trial_fingerprint":fp,
              "claims_created":0,"derived_from":derived_from,"rng_draw_count":1,"rng_checksum":tid})
        pq.write_table(pa.Table.from_pylist(trial_rows),base/"trials_summary.parquet")
        pq.write_table(pa.Table.from_pylist([{"date":"2027-01-01","scenario_id":scenario,
          "quantile_name":"P50","metric":"Cash","value":0}]),base/"daily_distribution.parquet")
        snapshot_rows=[{"date":"2027-01-01","scenario_id":scenario,"trial_id":tid,"Cash":tid}
          for tid in range(1,checkpoint_n+1)]
        pq.write_table(pa.Table.from_pylist(snapshot_rows),base/"daily_snapshots.parquet")
        derived_trials=[{"trial_id":row["trial_id"],"derived_from":row["derived_from"],
          "trial_fingerprint":row["trial_fingerprint"]} for row in trial_rows if row["derived_from"] is not None]
        full_run_ids=[row["trial_id"] for row in trial_rows if row["derived_from"] is None]
        (base/"opt1_provenance.json").write_text(json.dumps({
          "scenario_id":scenario,"collection_level":collection,"recovery_level":recovery,
          "policy":policy,"sample_trial_count":checkpoint_n,"eligible_zero_claim_trials":checkpoint_n,
          "derived_trial_count":len(derived_trials),"full_run_trial_ids":full_run_ids,
          "derived_trials":derived_trials,"status":"EXECUTED"}))
        files={}
        for name in ("trials_summary.parquet","daily_distribution.parquet","daily_snapshots.parquet","opt1_provenance.json"):
            path=base/name
            files[name]={"sha256":s6.sha256_file(path),"size_bytes":path.stat().st_size}
        (base/"scenario_manifest.json").write_text(json.dumps({
          "schema_version":"s6-first-checkpoint-v1","status":"EXECUTED","scenario_id":scenario,
          "source_sha":source_sha,"cohort_id":f"s6-v23-{source_sha[:8]}",
          "run_id":source_run_id,"run_attempt":1,"trial_id_start":1,"trial_id_end":checkpoint_n,
          "trial_count":checkpoint_n,"n_unique_paths":checkpoint_n,"unique_daily_paths":checkpoint_n,
          "unique_terminal_fingerprints":len({row["trial_fingerprint"] for row in trial_rows}),
          "n_unique_paths_status":"COMPUTED_UNIQUE_DAILY_PATHS","opt1_policy":policy,
          "workers":2,"files":files
        }))

    package_versions={"numpy":"2.4.6","scipy":"1.17.1","pyarrow":"26.0.0","pandas":"3.1.0","python-dateutil":"2.9.0.post0"}
    source_metadata={"schema_version":"s6-source-run-metadata-v1","source_run_id":source_run_id,
      "source_run_attempt":1,"source_sha":source_sha,"git_commit":source_sha,
      "workflow_run_url":"https://example.invalid/test-fixture","scenario_count":len(s6.stochastic_scenario_ids()),
      "scenarios":{}}
    for index,scenario in enumerate(sorted(s6.stochastic_scenario_ids()),start=1):
        source_metadata["scenarios"][scenario]={"job_id":index,"job_name":f"TEST {scenario}",
          "conclusion":"success","started_at_utc":"2026-10-27T20:23:07Z",
          "finished_at_utc":"2026-10-27T20:23:46Z","exit_code":0,"git_commit":source_sha,
          "python_version":"3.11.17","package_versions":package_versions,
          "command_argv":["python","scripts/s6_first_checkpoint.py","--scenario",scenario],
          "job_log_sha256":"b"*64,"source_run_id":source_run_id,"source_run_attempt":1}
    source_metadata_path=tmp_path/"source_run_metadata.json"
    source_metadata_path.write_text(json.dumps(source_metadata))
    aggregate_run_id="99999"
    result=s6.aggregate(SimpleNamespace(source_sha=source_sha,run_id=aggregate_run_id,
      run_attempt=1,source_run_id=source_run_id,source_run_attempt=1,
      source_run_metadata_json=str(source_metadata_path),
      trials=checkpoint_n,input_root=str(artifacts),output_dir=str(tmp_path/"out")))
    assert result["run_id"]==aggregate_run_id
    assert result["source_run_id"]==source_run_id
    assert result["source_run_metadata"]["status"]=="VERIFIED_FROM_GITHUB_ACTIONS_JOB_LOGS"
    assert result["source_run_metadata"]["scenario_count"]==20
    assert result["source_run_metadata"]["sha256"]==hashlib.sha256(source_metadata_path.read_bytes()).hexdigest()
    assert all(row["execution_metadata_source"]=="source_run_job_api_and_logs" for row in result["scenario_summaries"])
    assert all(row["started_at_utc"] and row["finished_at_utc"] and row["python_version"]=="3.11.17" and row["package_versions"]==package_versions for row in result["scenario_summaries"])
    assert result["scenario_summaries"][0]["run_id"]==source_run_id
    assert result["scenario_count"]==len(s6.stochastic_scenario_ids())
    assert result["total_scenario_combinations"]==result["scenario_count"]+result["c100_reused_scenario_count"]
    assert result["c100_reused_scenario_count"]==len(result["c100_reuse"]["scenario_ids"])
    assert result["c100_reuse"]["source_sha"]=="965281d52441cd0d4b744e211c9f68ee4cdc3753"
    assert all(not row["scenario_id"].startswith("C100_") for row in result["scenario_summaries"])
    diagnostic=next(row for row in result["scenario_summaries"] if row["scenario_id"]=="C070_G100")
    assert diagnostic["n_unique_paths"]==checkpoint_n
    assert diagnostic["n_unique_paths_status"]=="COMPUTED_UNIQUE_DAILY_PATHS"
    assert diagnostic["unique_daily_paths"]==checkpoint_n
    assert diagnostic["unique_terminal_fingerprints"]==299
    assert diagnostic["n_unique_financial_outcomes"]==299
    assert diagnostic["n_unique_daily_paths_diagnostic"]==checkpoint_n
    assert result["acceptance_status"]["n_unique_paths"]=="COMPUTED_FROM_UNIQUE_DAILY_PATHS"
    assert result["opt1_audit"]["status"]=="PASS"
    assert result["opt1_audit"]["derived_trial_rows"]==8*checkpoint_n
    assert result["opt1_audit"]["full_run_scenario_rows"]==12*checkpoint_n
    assert all(row["n_total"]==row["n_closed"]+row["n_censored"] for row in result["scenario_summaries"])
    assert result["acceptance_status"]["gate_a"]!="PASS"
    assert result["acceptance_status"]["gate_b"]!="PASS"

def test_s6_current_git_commit_uses_checked_out_commit_outside_actions(monkeypatch):
    monkeypatch.delenv("GITHUB_SHA",raising=False)
    expected=subprocess.run(["git","rev-parse","HEAD"],capture_output=True,text=True,check=True).stdout.strip()
    assert s6.current_git_commit("a"*40)==expected


def test_s6_source_sha_validation_rejects_non_commit_identity():
    with pytest.raises(ValueError,match="S6_SOURCE_SHA_INVALID"): s6.require_source_sha("not-a-commit")
