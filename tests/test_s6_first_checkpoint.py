from dataclasses import asdict, replace
from types import SimpleNamespace
import hashlib
import subprocess
import json
import pyarrow as pa
import pyarrow.parquet as pq
from monte_carlo import TrialResult
import pytest
from scripts import s6_first_checkpoint as s6


def test_time_uniform_method_identifier_tracks_normative_v23_clause():
    assert s6.constants.TIME_UNIFORM_METHOD_ID == "V2.3_14_11_4_ALPHA_SPENDING_V1"
    assert "APPENDIX_E" not in s6.constants.TIME_UNIFORM_METHOD_ID
    from pathlib import Path
    policy = json.loads(Path("docs/stage7/statistical_execution_gate.json").read_text(encoding="utf-8"))
    spending = policy["approved_policy"]["sequential_alpha_spending"]
    assert spending["checkpoints"] == [300, 600, 1200, 2400]
    assert spending["checkpoint_indices"] == [1, 2, 3, 4]


def test_owner_approved_n_unique_paths_uses_verified_daily_path_count():
    from stats_integrity import resolve_n_unique_paths
    source_sha = "a" * 40
    cohort_id = f"s6-v23-{source_sha[:8]}"
    assert resolve_n_unique_paths("C070_G100", [1, 2, 3], 3) == 3
    assert resolve_n_unique_paths("C100_G100", [0, 0, 0], 1) == 1
    legacy_manifest = {"scenario_id": "C070_G100", "source_sha": source_sha,
                       "cohort_id": cohort_id, "n_unique_paths": 1}
    assert s6.reported_unique_path_evidence(
        legacy_manifest, 3, 3, source_sha, cohort_id
    ) == (3, "OWNER_APPROVED_UNIQUE_DAILY_PATHS_CONTRACT")
    with pytest.raises(RuntimeError, match="S6_N_UNIQUE_PATHS_SOURCE_OR_COHORT_MISMATCH"):
        s6.reported_unique_path_evidence(legacy_manifest, 3, 3, "b" * 40, cohort_id)
    assert resolve_n_unique_paths("C085_G100", [1, 0, 0], 2) == 2
    with pytest.raises(RuntimeError, match="N_UNIQUE_DAILY_PATHS_EXCEEDS_TRIAL_COUNT"):
        resolve_n_unique_paths("C085_G100", [1, 0], 3)
    with pytest.raises(RuntimeError, match="C100_DETERMINISTIC_PATH_CONTRACT_VIOLATION"):
        resolve_n_unique_paths("C100_G100", [0, 0], 2)

def test_action_checkpoint_config_pins_valid_incremental_resume(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    config = s6._s6_action_checkpoint_config()
    assert config is not None
    target = config["active_target_trials"]
    assert target >= 2400
    assert s6.validate_checkpoint_target_range(
        target, config["trial_start"], config["trial_end"]
    ) == target // 2
    assert config["previous_run_id"] > 0
    assert config["n300_aggregate_run_id"] == 40588234012
    assert config["n600_aggregate_run_id"] == 40582501871
    assert config["n1200_aggregate_run_id"] == 40596643263
    assert config["source_sha"] == "da1a9ea9b5cd789c944de3f07b08395bb67c49e7"
    assert config["cohort_id"] == "s6-v23-da1a9ea9"


def test_statistical_checkpoint_schedule_has_no_fixed_upper_cap():
    assert s6.statistical_checkpoint_schedule(300) == [300]
    assert s6.statistical_checkpoint_schedule(2400) == [300, 600, 1200, 2400]
    assert s6.statistical_checkpoint_schedule(4800) == [300, 600, 1200, 2400, 4800]
    assert s6.statistical_checkpoint_schedule(9600) == [300, 600, 1200, 2400, 4800, 9600]
    assert s6.stats_integrity.statistical_checkpoint_index(4800) == 5
    assert s6.validate_checkpoint_target_range(4800, 2401, 4800) == 2400
    assert s6.validate_checkpoint_target_range(9600, 4801, 9600) == 4800


def test_statistical_checkpoint_schedule_rejects_nonapproved_checkpoints():
    with pytest.raises(ValueError, match="S6_CHECKPOINT_N_NOT_APPROVED_DOUBLING_POINT"):
        s6.statistical_checkpoint_schedule(4801)
    with pytest.raises(RuntimeError, match="S6_CHECKPOINT_CONFIG_RANGE_INVALID"):
        s6.validate_checkpoint_target_range(4800, 1201, 4800)


def test_aggregate_checkpoint_n_is_resolved_from_verified_manifest_counts():
    config = {"active_target_trials": 1200, "trial_start": 601, "trial_end": 1200}
    assert s6.resolve_aggregate_checkpoint_n(300, [300] * 20, config) == 300
    assert s6.resolve_aggregate_checkpoint_n(600, [1200] * 20, config) == 1200
    assert s6.resolve_aggregate_checkpoint_n(1200, [1200] * 20, config) == 1200
    with pytest.raises(RuntimeError, match="S6_AGGREGATE_MIXED_CHECKPOINT_N"):
        s6.resolve_aggregate_checkpoint_n(600, [600] * 19 + [1200], config)
    with pytest.raises(RuntimeError, match="S6_AGGREGATE_REQUESTED_N_MISMATCH"):
        s6.resolve_aggregate_checkpoint_n(300, [1200] * 20, None)


def test_action_checkpoint_config_does_not_override_aggregate_trial_count(monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    args = SimpleNamespace(
        mode="aggregate", source_sha="da1a9ea9b5cd789c944de3f07b08395bb67c49e7", trials=300,
    )
    config = s6.apply_action_checkpoint_config(args)
    assert config is not None and config["active_target_trials"] >= 2400
    assert s6.previous_checkpoint_n(config["active_target_trials"]) == config["active_target_trials"] // 2
    assert args.trials == 300
    assert args._s6_checkpoint_config["cohort_id"] == "s6-v23-da1a9ea9"


def test_exact_statistical_transition_requires_gate_a_gate_b_and_both_change_guards():
    from fractions import Fraction
    from stats_integrity import evaluate_statistical_transition

    def point(n, gate_a="PASS", gate_b="PASS", p50=100, loss=Fraction(1, 10)):
        return {
            "n": n,
            "gate_a": {"status": gate_a, "stable": gate_a == "PASS"},
            "gate_b": {"status": gate_b, "stable": gate_b == "PASS"},
            "p50_cumulative_project_profit": {"numerator": p50, "denominator": 1},
            "probability_accounting_loss": {
                "numerator": loss.numerator, "denominator": loss.denominator,
            },
        }

    from stats_integrity import statistical_checkpoint_index
    assert [statistical_checkpoint_index(n) for n in (300, 600, 1200, 2400)] == [1, 2, 3, 4]
    assert evaluate_statistical_transition(point(300), point(600))["status"] == "PASS"
    assert evaluate_statistical_transition(
        point(300, gate_a="NOT_EVALUATED"), point(600)
    )["status"] == "BLOCKED_GATE_A"
    assert evaluate_statistical_transition(
        point(300, p50=100), point(600, p50=106)
    )["status"] == "CONTINUE_P50_GUARD"
    assert evaluate_statistical_transition(
        point(300, loss=Fraction(1, 10)),
        point(600, loss=Fraction(107, 1000)),
    )["status"] == "CONTINUE_LOSS_PROBABILITY_CHANGE"


def test_cumulative_trial_id_contract_rejects_duplicates_and_missing_ids():
    from stats_integrity import validate_cumulative_trial_ids
    assert validate_cumulative_trial_ids([3, 1, 2], 3, scenario_id="C070_G100") == [1, 2, 3]
    with pytest.raises(RuntimeError, match="S6_DUPLICATE_TRIAL_ID"):
        validate_cumulative_trial_ids([1, 2, 2], 3, scenario_id="C070_G100")
    with pytest.raises(RuntimeError, match="S6_TRIAL_ID_COVERAGE_MISMATCH"):
        validate_cumulative_trial_ids([1, 2, 4], 3, scenario_id="C070_G100")
    with pytest.raises(RuntimeError, match="S6_TRIAL_ID_COUNT_MISMATCH"):
        validate_cumulative_trial_ids([1, 2], 3, scenario_id="C070_G100")


def test_cumulative_rng_audit_checks_cross_checkpoint_duplicates_and_exempts_zero_draws():
    source_sha = "a" * 40
    def record(scenario, trial_id, checksum, draws):
        return {
            "scenario_id": scenario,
            "trial_id": trial_id,
            "rng_checksum": checksum,
            "rng_draw_count": draws,
            "rng_checksum_fingerprint_sha256": s6.rng.rng_audit_fingerprint(
                source_sha=source_sha, master_seed=s6.constants.MASTER_SEED,
                scenario_id=scenario, trial_id=trial_id,
                rng_checksum=checksum, rng_draw_count=draws,
            ),
        }
    assert s6.validate_cumulative_rng_audit(
        [record("C100_G100", 1, 0, 0), record("C100_G100", 2, 0, 0)], source_sha
    ) == 2
    with pytest.raises(RuntimeError, match="DUPLICATE_RNG_CHECKSUM_DETECTED"):
        s6.validate_cumulative_rng_audit(
            [record("C030_G000", 1, 0, 1), record("C030_G000", 2, 0, 1)], source_sha
        )


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
            finance_tid = 1 if collection == 70 and tid == 2 else tid
            audit_fingerprint=s6.rng.rng_audit_fingerprint(source_sha=source_sha,
              master_seed=s6.constants.MASTER_SEED,scenario_id=scenario,trial_id=tid,
              rng_checksum=tid,rng_draw_count=1)
            result=TrialResult(
              scenario_id=scenario,collection_probability=collection/100,recovery_rate_pct=recovery,trial_id=tid,
              final_close_date=None,final_net_project_equity=10000+finance_tid,final_cash=1000+finance_tid,
              cumulative_project_profit=3000+finance_tid,operating_net_profit=2000+finance_tid,
              termination_count=finance_tid%4,secondary_cycle_count=finance_tid%3,owned_bikes=finance_tid%5,
              held_assets=finance_tid%7,total_operating_revenue=5000+finance_tid,bad_debt=finance_tid%6,
              guarantee_recovered=finance_tid%8,partner1_final_entitlement=4000+finance_tid,
              partner2_final_entitlement=2000+finance_tid,trial_fingerprint="",rng_checksum=tid,
              rng_draw_count=1,rng_checksum_fingerprint_sha256=audit_fingerprint,claims_created=0)
            fp=s6.monte_carlo.trial_fingerprint(result)
            result=replace(result,trial_fingerprint=fp)
            row=asdict(result)
            row.update(source_sha=source_sha,cohort_id=f"s6-v23-{source_sha[:8]}",
              schema_version=s6.SCHEMA_VERSION,derived_from=derived_from)
            trial_rows.append(row)
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
    assert diagnostic["n_unique_paths_status"]=="OWNER_APPROVED_UNIQUE_DAILY_PATHS_CONTRACT"
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

def test_gate_a_checkpoint_stays_not_evaluated_without_approved_golden():
    result = s6.evaluate_gate_a_checkpoint(
        "C030_G000", 2, {1: {"trial_fingerprint": "a" * 64}},
        None, source_sha="da1a9ea9b5cd789c944de3f07b08395bb67c49e7",
        cohort_id="s6-v23-da1a9ea9",
    )
    assert result["status"] == "NOT_EVALUATED_NO_SAME_SOURCE_PRODUCTION_GOLDEN"
    assert result["checked"] is False and result["stable"] is False


def test_gate_a_checkpoint_requires_exact_financial_fingerprint_match():
    golden = {
        "golden_trial_count_per_scenario": 3,
        "golden_run_id": "12345",
        "golden_map_sha256": "a" * 64,
        "golden_map": {
            "scenarios": {
                "C030_G000": {"trial_fingerprints": {"1": "a" * 64, "2": "b" * 64, "3": "c" * 64}}
            }
        },
    }
    kwargs = {
        "source_sha": "da1a9ea9b5cd789c944de3f07b08395bb67c49e7",
        "cohort_id": "s6-v23-da1a9ea9",
    }
    exact = s6.evaluate_gate_a_checkpoint(
        "C030_G000", 2,
        {1: {"trial_fingerprint": "a" * 64}, 2: {"trial_fingerprint": "b" * 64}},
        golden, **kwargs,
    )
    mismatch = s6.evaluate_gate_a_checkpoint(
        "C030_G000", 2,
        {1: {"trial_fingerprint": "a" * 64}, 2: {"trial_fingerprint": "d" * 64}},
        golden, **kwargs,
    )
    insufficient = s6.evaluate_gate_a_checkpoint(
        "C030_G000", 4, {}, golden, **kwargs,
    )
    assert exact["status"] == "PASS" and exact["mismatch_count"] == 0
    assert mismatch["status"] == "FAIL_FINANCIAL_TRIAL_FINGERPRINT_MISMATCH"
    assert mismatch["mismatch_trial_ids_sample"] == [2]
    assert insufficient["status"] == "NOT_EVALUATED_GOLDEN_COVERAGE_INSUFFICIENT"
    assert insufficient["checked"] is False


def test_gate_a_golden_loader_rejects_partial_approval_input_set():
    with pytest.raises(RuntimeError, match="S6_GATE_A_GOLDEN_INPUT_SET_INCOMPLETE"):
        s6.load_approved_gate_a_golden(
            "some-map.json", None, None,
            expected_source_sha="da1a9ea9b5cd789c944de3f07b08395bb67c49e7",
            expected_cohort_id="s6-v23-da1a9ea9",
        )
