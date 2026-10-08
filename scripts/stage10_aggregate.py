from __future__ import annotations
import json, os, subprocess, sys
from datetime import datetime
from pathlib import Path

def api(path):
    return json.loads(subprocess.check_output(["gh","api","--header","X-GitHub-Api-Version: 2022-11-28",path],text=True))

def ts(s): return datetime.fromisoformat(s.replace("Z","+00:00"))
def pct(v,q):
    if not v:return None
    a=sorted(v); k=(len(a)-1)*q; lo=int(k); hi=min(lo+1,len(a)-1)
    return float(a[lo] if lo==hi else a[lo]+(a[hi]-a[lo])*(k-lo))

def main():
    run_id=int(sys.argv[1]); root=Path("all_artifacts")
    ms=[json.loads(p.read_text()) for p in root.rglob("metrics.json")]
    jobs=api(f"repos/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{run_id}/jobs?per_page=100")["jobs"]
    matrix=[j for j in jobs if str(j.get("name","")).startswith("bench-")]
    artifacts=api(f"repos/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{run_id}/artifacts?per_page=100")["artifacts"]
    chunk_artifacts=[a for a in artifacts if str(a.get("name","")).startswith("stage10-bench-") and a.get("name")!="stage10-bench-final"]
    expected=45; scenarios=[f"C{c:03d}_G{g:03d}" for c in (100,85,70,50,30) for g in (100,70,50,30,0)]
    by={s:[x for x in ms if x.get("scenario")==s] for s in scenarios}
    job_durations={}
    conclusions={}
    intervals=[]
    for j in matrix:
        if j.get("started_at") and j.get("completed_at"):
            d=(ts(j["completed_at"])-ts(j["started_at"])).total_seconds()
            job_durations[j["name"]]=d
            intervals.extend([(ts(j["started_at"]),1),(ts(j["completed_at"]),-1)])
        conclusions[j["name"]]=j.get("conclusion")
    cur=mx=0
    for _,d in sorted(intervals,key=lambda x:(x[0],x[1])): cur+=d; mx=max(mx,cur)
    scenario_rows=[]
    for s in scenarios:
        rows=by[s]; ds=[d for x in rows for d in x.get("per_execution_durations_seconds",[])]
        if rows:
            sim=sum(float(x["simulation_wall_time_seconds"]) for x in rows); chunk_e2e=sum(float(x["chunk_end_to_end_seconds"]) for x in rows)
            fixed=max(0.0,sum(job_durations.get(f"bench-{s}-{x.get('chunk_id',1)}",0.0) for x in rows)-chunk_e2e)
            mean=float(sum(ds)/len(ds))
            row={"scenario":s,"executions":sum(int(x["executions_completed"]) for x in rows),"canonical_trials_added":sum(int(x["canonical_trials_added"]) for x in rows),"mean_trial_seconds":mean,"p50_seconds":pct(ds,.5),"p95_seconds":pct(ds,.95),"p99_seconds":pct(ds,.99),"fixed_job_overhead_seconds":fixed,"job_timeout_risk":max([job_durations.get(f"bench-{s}-{x.get('chunk_id',1)}",0.0) for x in rows] or [0])>2100,"baseline_statuses":sorted({x["baseline_state"]["final_status"] for x in rows})}
        else:
            row={"scenario":s,"executions":0,"canonical_trials_added":0,"mean_trial_seconds":None,"p50_seconds":None,"p95_seconds":None,"p99_seconds":None,"fixed_job_overhead_seconds":None,"job_timeout_risk":False,"baseline_statuses":[]}
        scenario_rows.append(row)
    total_exec=sum(r["executions"] for r in scenario_rows); canonical=sum(r["canonical_trials_added"] for r in scenario_rows)
    fresh9005=fresh11005=0.0
    for r in scenario_rows:
        if r["mean_trial_seconds"] is None: continue
        n=1 if r["scenario"].startswith("C100_") else 450
        fresh9005 += r["fixed_job_overhead_seconds"] + n*r["mean_trial_seconds"]
        fresh11005 += r["fixed_job_overhead_seconds"] + (n+r["canonical_trials_added"])*r["mean_trial_seconds"]
    failures={name:con for name,con in conclusions.items() if con!="success"}
    warning_jobs={name:d for name,d in job_durations.items() if d>2100}
    gates={"matrix_jobs_45":len(matrix)==45,"scenario_count_25":len([r for r in scenario_rows if r["executions"]>0])==25,"execution_count_2500":total_exec==2500,"canonical_added_2000":canonical==2000,"execution_failures_zero":all(int(x.get("executions_failed",0))==0 for x in ms),"matrix_jobs_success":len(failures)==0,"chunk_artifacts_45":len(chunk_artifacts)==45,"model_source_drift_absent":all(x.get("source_sha")=="f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b" for x in ms),"resumable_extensions_present":all((root/f"stage10-bench-{s}-1"/"resume_descriptor.json").exists() for s in scenarios if not s.startswith("C100_"))}
    verdict="PASS" if all(gates.values()) else ("PARTIAL" if gates["execution_failures_zero"] and gates["scenario_count_25"] else "FAIL")
    report={"schema_version":"stage10-benchmark-v1","run_id":run_id,"matrix_jobs_expected":expected,"matrix_jobs_observed":len(matrix),"scenario_results":scenario_rows,"totals":{"benchmark_executions":total_exec,"canonical_trials_added":canonical,"current_total_trials":9005,"final_total_trials_if_extension_accepted":9005+canonical},"github_topology":{"configured_max_parallel":10,"observed_max_concurrency":mx,"job_durations_seconds":job_durations,"warnings_jobs_over_35m":warning_jobs,"job_conclusions":conclusions},"stage11_estimates":{"stage11_topology_status":"NOT_DEFINED_IN_CURRENT_REPOSITORY","fresh_current_dataset_9005_serial_hours":fresh9005/3600,"fresh_extended_dataset_11005_serial_hours":fresh11005/3600,"conditional_note":"These are workload estimates using measured per-scenario execution time plus measured job overhead. They are not a claim that Stage 11 uses a particular worker topology or final adaptive trial count. Current stage7-state is stable at N=450 for non-C100 and N=1 for C100; the Stage10 canonical extension itself does not modify stage7-state."},"gates":gates,"failures":failures,"verdict":verdict,"generated_at":datetime.now().astimezone().isoformat()}
    Path("stage10_final").mkdir(exist_ok=True)
    Path("stage10_final/STAGE10_METRICS.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"
",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True))
if __name__=="__main__": main()
