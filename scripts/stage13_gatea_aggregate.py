#!/usr/bin/env python3
"""Aggregate per-scenario Gate A evidence without modifying any source artifacts."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
SCENARIOS=[f"C{c:03d}_G{g:03d}" for c in (100,85,70,50,30) for g in (100,70,50,30,0)]
EXPECTED_GLOBAL="7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44"
EXPECTED_TRIALS=11005
EXPECTED_DAILY_ROWS=22546465
SOURCE_SHA="f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
STAGE7_RUN_ID=37225915321
STAGE10_RUN_ID=37709936740
STAGE12_RUN_ID=37964656154

def hash_entries(rows):
    ordered=sorted(rows,key=lambda x:(x[0],int(x[1]),x[2]))
    payload="".join(f"{scenario}|{trial_id}|{sha}\n" for scenario,trial_id,sha in ordered)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--input-root",required=True); p.add_argument("--output-root",default="gatea_evidence")
    p.add_argument("--unit-result",default="unknown"); p.add_argument("--matrix-result",default="unknown")
    a=p.parse_args(); output=Path(a.output_root); output.mkdir(parents=True,exist_ok=True)
    reports={}; duplicates=[]
    for path in sorted(Path(a.input_root).rglob("*.json")):
        try: d=json.loads(path.read_text(encoding="utf-8"))
        except Exception: continue
        s=d.get("scenario")
        if s in SCENARIOS:
            if s in reports: duplicates.append(s)
            else: reports[s]=d
    missing=sorted(set(SCENARIOS)-set(reports)); extra=sorted(set(reports)-set(SCENARIOS))
    comparisons=[]; mismatches=[]; summaries=[]; daily_rows=0; source_rows_rehashed=0
    s7=set(); s10=set(); s12=set(); parse_events=[]
    for scenario in SCENARIOS:
        d=reports.get(scenario)
        if d is None:
            summaries.append({"scenario":scenario,"status":"MISSING_REPORT"}); continue
        for row in d.get("trial_comparisons",[]):
            comparisons.append((scenario,int(row["trial_id"]),row.get("stage12_sha256"),row.get("golden_sha256"),bool(row.get("exact_match"))))
            if not row.get("exact_match"): mismatches.append({"scenario":scenario,**row})
        daily_rows+=int(d.get("daily_row_count",0))
        source_rows_rehashed+=sum(int(b.get("trial_hashes_recomputed_from_parquet",0)) for b in d.get("source_blocks",[]))
        parse_events.extend([{"scenario":scenario,**x} for x in d.get("stage10_metadata_parse_events",[])])
        if d.get("stage7_artifact"): s7.add(scenario)
        if d.get("stage10_artifact"): s10.add(scenario)
        if d.get("stage12_artifact"): s12.add(scenario)
        summaries.append({"scenario":scenario,"status":d.get("status"),"source_golden_trial_count":d.get("source_golden_trial_count",0),"daily_row_count":d.get("daily_row_count",0),"exact_trial_comparisons":d.get("exact_trial_comparisons",0),"hash_mismatch_count":d.get("hash_mismatch_count",0),"fatal_error":d.get("fatal_error"),"gates":d.get("gates",{})})
    usable=[x for x in comparisons if x[2] and x[3]]
    actual_global=hash_entries([(s,t,actual) for s,t,actual,_,_ in usable])
    golden_global=hash_entries([(s,t,golden) for s,t,_,golden,_ in usable])
    keys=[(s,t) for s,t,_,_,_ in comparisons]
    unique_complete=len(keys)==EXPECTED_TRIALS and len(set(keys))==EXPECTED_TRIALS
    exact_all=len(comparisons)==EXPECTED_TRIALS and len(usable)==EXPECTED_TRIALS and all(x[4] for x in comparisons) and not mismatches
    scenario_pass=len(reports)==25 and not missing and not extra and not duplicates and all(reports[s].get("status")=="PASS" for s in SCENARIOS)
    parse_pass=(len(parse_events)==60 and all(x.get("parse_mode")=="known_stage10_literal_backslash_n_suffix_removed_in_memory" for x in parse_events) and len({(x.get("scenario"),x.get("file")) for x in parse_events})==60)
    gates={
        "25_unique_scenario_reports_present":len(reports)==25 and not missing and not extra and not duplicates,
        "all_25_scenario_reports_pass":scenario_pass,
        "stage7_golden_inputs_cover_25_scenarios":len(s7)==25,
        "stage10_extensions_cover_20_non_c100_scenarios":len(s10)==20 and not any(s.startswith("C100_") for s in s10),
        "stage12_parquets_cover_25_scenarios":len(s12)==25,
        "11005_source_trial_rows_rehashed":source_rows_rehashed==EXPECTED_TRIALS,
        "11005_exact_trial_comparisons":len(comparisons)==EXPECTED_TRIALS,
        "trial_scenario_keys_unique_and_complete":unique_complete,
        "all_11005_stage12_hashes_equal_source_goldens":exact_all,
        "stage12_daily_rows_match_cp12b_cp12c":daily_rows==EXPECTED_DAILY_ROWS,
        "reconstructed_stage12_global_hash_matches_cp12b":actual_global==EXPECTED_GLOBAL,
        "reconstructed_source_golden_global_hash_matches_cp12b":golden_global==EXPECTED_GLOBAL,
        "actual_and_golden_global_hashes_equal":actual_global==golden_global,
        "source_sha_provenance_correct":all(reports[s].get("source_sha")==SOURCE_SHA for s in reports),
        "inputs_remained_read_only":all(reports[s].get("simulation_or_trial_executed") is False and reports[s].get("historical_dataset_modified") is False and reports[s].get("historical_artifacts_modified") is False for s in reports),
        "stage10_json_suffix_defect_exactly_disclosed":parse_pass,
        "parser_unit_tests_pass":a.unit_result=="success",
        "scenario_matrix_jobs_pass":a.matrix_result=="success",
    }
    status="PASS" if all(gates.values()) else "FAIL"
    report={"gate":"A — exact per-trial golden fingerprint bridge","status":status,"scope":"Gate A only; no Gate B calculations, trial runs, dataset resume, or source artifact mutation",
        "source_sha":SOURCE_SHA,"stage7_run_id":STAGE7_RUN_ID,"stage10_run_id":STAGE10_RUN_ID,"stage12_run_id":STAGE12_RUN_ID,
        "expected_stage12_global_sha256":EXPECTED_GLOBAL,"actual_stage12_global_sha256":actual_global,"source_golden_global_sha256":golden_global,
        "expected_trials":EXPECTED_TRIALS,"actual_comparisons":len(comparisons),"source_trial_rows_rehashed":source_rows_rehashed,
        "expected_daily_rows":EXPECTED_DAILY_ROWS,"actual_daily_rows":daily_rows,"hash_mismatch_count":len(mismatches),"hash_mismatches":mismatches,
        "stage10_metadata_serialization_defect":{"classification":"K_CODE","source":"scripts/stage10_benchmark.py at ca73f2df37baacebbcad965fc5f433f129675820; blob d54602982b6422939955ca841a251ecd250b4139",
        "disposition":"Only the exact, source-proven literal backslash+n suffix was removed in memory. Raw bytes and SHA-256 were preserved, and source Parquet rows were independently rehashed.","recovery_events_count":len(parse_events),"recovery_events":parse_events},
        "missing_scenario_reports":missing,"extra_scenario_reports":extra,"duplicate_scenario_reports":duplicates,"scenario_results":summaries,"gates":gates,
        "simulation_or_trial_executed":False,"historical_dataset_modified":False,"historical_artifacts_modified":False}
    (output/"gatea_fingerprint_bridge_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    lines=["# Gate A — exact golden fingerprint bridge","",f"Status: {status}","",
        f"- Stage 7 / Stage 10 / Stage 12 Run IDs: {STAGE7_RUN_ID} / {STAGE10_RUN_ID} / {STAGE12_RUN_ID}",
        f"- Trials compared: {len(comparisons)} / {EXPECTED_TRIALS}",f"- Daily rows checked: {daily_rows} / {EXPECTED_DAILY_ROWS}",
        f"- Exact per-trial hash mismatches: {len(mismatches)}",f"- Stage 12 reconstructed global SHA-256: {actual_global}",
        f"- Source golden reconstructed global SHA-256: {golden_global}",f"- Disclosed Stage 10 suffix recoveries: {len(parse_events)}","",
        "## Gates","","| Gate | Result |","|---|---|"]
    lines += [f"| {k} | {'PASS' if v else 'FAIL'} |" for k,v in gates.items()]
    lines += ["","## Scenario results","","| Scenario | Status | Trials | Daily rows | Mismatches |","|---|---:|---:|---:|---:|"]
    lines += [f"| {x['scenario']} | {x['status']} | {x['source_golden_trial_count']} | {x['daily_row_count']} | {x['hash_mismatch_count']} |" for x in summaries]
    lines += ["","This report evaluates Gate A only. It does not establish Gate B, CP-B2, Stage 9C, or final delivery."]
    (output/"gatea_fingerprint_bridge_report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({"status":status,"trials":len(comparisons),"daily_rows":daily_rows,"mismatches":len(mismatches),"actual_global":actual_global,"golden_global":golden_global,"gates":gates,"report":str(output/"gatea_fingerprint_bridge_report.json")},ensure_ascii=False,indent=2))
    if status!="PASS": raise SystemExit(1)
if __name__=="__main__": main()
