from dataclasses import replace
import json
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

def test_s6_source_sha_validation_rejects_non_commit_identity():
    with pytest.raises(ValueError,match="S6_SOURCE_SHA_INVALID"): s6.require_source_sha("not-a-commit")
