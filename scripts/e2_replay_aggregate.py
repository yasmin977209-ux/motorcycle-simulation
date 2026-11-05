from __future__ import annotations
import argparse,json
from pathlib import Path
EXPECTED={f"C{c:03d}_G{g:03d}" for c in (85,70,50,30) for g in (100,70,50,30,0)}
LABEL="REPLAY_RECONSTRUCTED_NOT_ORIGINAL_PRESERVED"
def main():
 p=argparse.ArgumentParser(); p.add_argument("--input-root",required=True,type=Path); p.add_argument("--output-dir",required=True,type=Path); p.add_argument("--run-id",required=True); p.add_argument("--head-sha",required=True); a=p.parse_args()
 found={}
 for f in a.input_root.rglob("replay_scenario_manifest.json"):
  r=json.loads(f.read_text()); s=r["scenario_id"]
  if s in found: raise RuntimeError(f"DUPLICATE_SCENARIO:{s}")
  found[s]=r
 if set(found)!=EXPECTED: raise RuntimeError(f"SCENARIO_SET_MISMATCH:missing={sorted(EXPECTED-set(found))}:extra={sorted(set(found)-EXPECTED)}")
 for s,r in found.items():
  if r.get("status")!="PASS_SCOPED_REPLAY_RECONSTRUCTION" or r.get("replay_label")!=LABEL or r.get("trial_count")!=2400 or r.get("financial_trial_fingerprints",{}).get("status")!="PASS_EXACT_MATCH" or r.get("daily_overlap_comparison",{}).get("status")!="PASS_EXACT_OVERLAP" or r.get("balance_sheet",{}).get("status")!="PASS_ALL_REPLAY_DAILY_ROWS": raise RuntimeError(f"SCENARIO_NOT_ACCEPTED:{s}")
 trials=sum(r["trial_count"] for r in found.values()); src=sum(r["source_daily_rows"] for r in found.values()); rep=sum(r["replay_daily_rows"] for r in found.values()); chk=sum(r["balance_sheet"]["rows_checked"] for r in found.values())
 if trials!=48000 or src!=rep or rep!=chk: raise RuntimeError(f"GLOBAL_COVERAGE_MISMATCH:{trials}:{src}:{rep}:{chk}")
 result={"schema_version":"e2-s6-deterministic-replay-aggregate-v1","status":"PASS_SCOPED_REPLAY_RECONSTRUCTION","replay_label":LABEL,"repository":"yasmin977209-ux/motorcycle-simulation","working_branch":"tmp/d1-rebuild-20261101","workflow_run_id":a.run_id,"workflow_head_sha":a.head_sha,"source_run_id":"40731224990","source_execution_commit":"a23ba71f48487f3ebead99bc30039b14ef9b7609","source_sha":"da1a9ea9b5cd789c944de3f07b08395bb67c49e7","cohort_id":"s6-v23-da1a9ea9","master_seed":20270101,"scenario_count":20,"trial_count":trials,"source_daily_rows":src,"replay_daily_rows":rep,"daily_balance_rows_validated":chk,"scenario_results":{s:{"trials":r["trial_count"],"daily_rows":r["replay_daily_rows"],"fingerprints":r["financial_trial_fingerprints"]["status"],"overlap":r["daily_overlap_comparison"]["status"],"balance":r["balance_sheet"]["status"]} for s,r in sorted(found.items())},"financial_gate_a_status":"PASS_SCOPED_ONLY","production_gate_a_status":"NOT_DECLARED_REQUIRES_SEPARATE_REVIEW","historical_source_artifacts_modified":False,"historical_manifests_modified":False,"stage12_stage13_c100_lineage_mixed":False,"final_acceptance":"NOT_GRANTED"}
 a.output_dir.mkdir(parents=True,exist_ok=True); (a.output_dir/"E2_S6_DETERMINISTIC_REPLAY_AGGREGATE.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"status":result["status"],"trials":trials,"daily_rows":rep,"production_gate_a":result["production_gate_a_status"],"final_acceptance":"NOT_GRANTED"}))
if __name__=="__main__": main()
