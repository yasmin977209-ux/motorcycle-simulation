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
        trial_rows=[{"trial_id":tid,"final_close_date":None,
          "trial_fingerprint":hashlib.sha256(f"{scenario}|{tid}".encode()).hexdigest()}
          for tid in range(1,checkpoint_n+1)]
        pq.write_table(pa.Table.from_pylist(trial_rows),base/"trials_summary.parquet")
        pq.write_table(pa.Table.from_pylist([{"date":"2027-01-01","scenario_id":scenario,
          "quantile_name":"P50","metric":"Cash","value":0}]),base/"daily_distribution.parquet")
        pq.write_table(pa.Table.from_pylist([{"date":"2027-01-01","trial_id":1}]),base/"daily_snapshots.parquet")
        (base/"opt1_provenance.json").write_text('{"status":"TEST_FIXTURE"}')
        files={}
        for name in ("trials_summary.parquet","daily_distribution.parquet","daily_snapshots.parquet","opt1_provenance.json"):
            path=base/name
            files[name]={"sha256":s6.sha256_file(path),"size_bytes":path.stat().st_size}
        (base/"scenario_manifest.json").write_text(json.dumps({
          "schema_version":"s6-first-checkpoint-v1","status":"EXECUTED","scenario_id":scenario,
          "source_sha":source_sha,"cohort_id":f"s6-v23-{source_sha[:8]}",
          "run_id":source_run_id,"run_attempt":1,"trial_id_start":1,"trial_id_end":checkpoint_n,
          "trial_count":checkpoint_n,"n_unique_paths":checkpoint_n,"opt1_policy":"TEST_FIXTURE",
          "workers":2,"files":files
        }))

    aggregate_run_id="99999"
    result=s6.aggregate(SimpleNamespace(source_sha=source_sha,run_id=aggregate_run_id,
      run_attempt=1,source_run_id=source_run_id,source_run_attempt=1,
      trials=checkpoint_n,input_root=str(artifacts),output_dir=str(tmp_path/"out")))
    assert result["run_id"]==aggregate_run_id
    assert result["source_run_id"]==source_run_id
    assert result["scenario_summaries"][0]["run_id"]==source_run_id
    assert result["scenario_count"]==len(s6.stochastic_scenario_ids())
    assert result["total_scenario_combinations"]==result["scenario_count"]+result["c100_reused_scenario_count"]
    assert result["c100_reused_scenario_count"]==len(result["c100_reuse"]["scenario_ids"])
    assert result["c100_reuse"]["source_sha"]=="965281d52441cd0d4b744e211c9f68ee4cdc3753"
    assert all(not row["scenario_id"].startswith("C100_") for row in result["scenario_summaries"])
    assert result["acceptance_status"]["gate_a"]!="PASS"
    assert result["acceptance_status"]["gate_b"]!="PASS"

def test_s6_current_git_commit_uses_checked_out_commit_outside_actions(monkeypatch):
    monkeypatch.delenv("GITHUB_SHA",raising=False)
    expected=subprocess.run(["git","rev-parse","HEAD"],capture_output=True,text=True,check=True).stdout.strip()
    assert s6.current_git_commit("a"*40)==expected


def test_s6_source_sha_validation_rejects_non_commit_identity():
    with pytest.raises(ValueError,match="S6_SOURCE_SHA_INVALID"): s6.require_source_sha("not-a-commit")
