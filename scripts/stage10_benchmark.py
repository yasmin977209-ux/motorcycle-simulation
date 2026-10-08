from __future__ import annotations
import dataclasses, gzip, hashlib, json, os, platform, resource, shutil, sys, time, subprocess
from datetime import datetime, timezone
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
import constants, daily_engine, monte_carlo

def utc_now(): return datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
def canonical_json(v): return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"),default=str).encode("utf-8")
def result_sha(x): return hashlib.sha256(canonical_json(dataclasses.asdict(x))).hexdigest()
def dataset_fp(xs): return monte_carlo.fingerprint_trial_results(xs)
def blob_sha(path): return subprocess.check_output(["git","rev-parse",f"HEAD:{path}"],text=True).strip()
def percentile(vals,q):
    if not vals:return None
    a=sorted(vals); k=(len(a)-1)*q; lo=int(k); hi=min(lo+1,len(a)-1)
    return float(a[lo] if lo==hi else a[lo]+(a[hi]-a[lo])*(k-lo))

def load_manifest(): return json.loads(Path("docs/stage9a/dataset_manifest.json").read_text(encoding="utf-8"))
def load_state(): return json.loads(Path("baseline_state.json").read_text(encoding="utf-8"))

def verify_source(source_sha):
    subprocess.run(["git","cat-file","-e",f"{source_sha}^{{commit}"],check=True)
    files="constants.py dateutils.py rng.py entities.py state_machine.py daily_engine.py accounting.py collection.py guarantee.py friday.py settlement.py closure.py partner_equity.py monte_carlo.py".split()
    r=subprocess.run(["git","diff","--quiet",source_sha,"HEAD","--",*files])
    if r.returncode!=0: raise RuntimeError("MODEL_SOURCE_DRIFT_DETECTED")

def verify_state(s, source):
    d=load_state()
    expected=1 if s.startswith("C100_") else 450
    if d.get("source_sha")!=source: raise RuntimeError("BASELINE_STATE_SOURCE_SHA_MISMATCH")
    if int(d.get("master_seed",constants.MASTER_SEED))!=constants.MASTER_SEED: raise RuntimeError("BASELINE_STATE_MASTER_SEED_MISMATCH")
    if int(d.get("completed_trials",-1))!=expected or int(d.get("next_trial_id",-1))!=expected+1: raise RuntimeError("BASELINE_STATE_TRIAL_COUNT_MISMATCH")
    return d

def read_baseline(root,s,source,artifact_id,expected_run):
    m=load_manifest()
    expected_artifact=int(m["artifact_manifest"]["official_block_artifacts"][s])
    if expected_artifact!=int(artifact_id): raise RuntimeError("BASELINE_ARTIFACT_ID_MISMATCH")
    expected_fps=m["block_fingerprints"][s]
    metas=sorted(root.rglob("*_metadata.json"))
    if not metas: raise RuntimeError("BASELINE_METADATA_NOT_FOUND")
    rs=[]
    for mp in metas:
        d=json.loads(mp.read_text(encoding="utf-8"))
        rg=f'{int(d["trial_id_start"])}-{int(d["trial_id_end"])}'
        if d.get("scenario")!=s or d.get("source_sha")!=source or int(d.get("run_id"))!=int(expected_run): raise RuntimeError("BASELINE_METADATA_IDENTITY_MISMATCH")
        if expected_fps.get(rg)!=d.get("fingerprint_sha256"): raise RuntimeError(f"BASELINE_BLOCK_FINGERPRINT_MISMATCH:{rg}")
        pp=mp.with_name(mp.name.replace("_metadata.json",".parquet"))
        if not pp.exists(): raise RuntimeError("BASELINE_PARQUET_MISSING")
        rs += [monte_carlo.TrialResult(**row) for row in pq.read_table(pp).to_pylist()]
    rs.sort(key=lambda x:x.trial_id)
    expected=1 if s.startswith("C100_") else 450
    if [x.trial_id for x in rs] != list(range(1,expected+1)): raise RuntimeError("BASELINE_TRIAL_SEQUENCE_MISMATCH")
    fp=dataset_fp(rs); st=load_state()
    if st.get("final_fingerprint")!=fp: raise RuntimeError("BASELINE_STATE_FINGERPRINT_MISMATCH")
    return rs,fp,st,root

def run_trial(s,trial_id,seed):
    c,r=monte_carlo.parse_scenario_id(s)
    before=resource.getrusage(resource.RUSAGE_SELF); t=time.perf_counter()
    project=daily_engine.run_deterministic_trial(recovery_rate_pct=r,trial_id=trial_id,scenario_id=s,master_seed=seed,collection_probability=c,log_events=False)
    elapsed=time.perf_counter()-t; after=resource.getrusage(resource.RUSAGE_SELF)
    x=monte_carlo._trial_result_from_project(project,scenario_id=s,collection_probability=c,recovery_rate_pct=r,trial_id=trial_id)
    return x,{"trial_id":trial_id,"elapsed_seconds":elapsed,"cpu_user_seconds":after.ru_utime-before.ru_utime,"cpu_system_seconds":after.ru_stime-before.ru_stime,"result_sha256":result_sha(x)}

def percentile(vals,q):
    if not vals:return None
    a=sorted(vals); k=(len(a)-1)*q; lo=int(k); hi=min(lo+1,len(a)-1)
    return float(a[lo] if lo==hi else a[lo]+(a[hi]-a[lo])*(k-lo))

def write_json(path,d): Path(path).write_text(json.dumps(d,ensure_ascii=False,indent=2,sort_keys=True)+"
",encoding="utf-8")

def main(argv):
    if len(argv)!=10: raise SystemExit("usage: mode scenario start end artifact_id expected_run current_run source_sha master_seed baseline_root")
    mode,s,start,end,artifact_id,expected_run,current_run,source,seed,root=argv
    start=int(start); end=int(end); artifact_id=int(artifact_id); expected_run=int(expected_run); current_run=int(current_run); seed=int(seed)
    verify_source(source)
    if seed!=constants.MASTER_SEED: raise RuntimeError("MASTER_SEED_MISMATCH")
    rs,basefp,st,baseline_root=read_baseline(Path(root),s,source,artifact_id,expected_run)
    out=Path("stage10_output")/s; out.mkdir(parents=True,exist_ok=True)
    chunk_started=utc_now(); t0=time.perf_counter(); measures=[]; new=[]
    if mode=="canonical":
        if end-start+1!=100 or start!=len(rs)+1: raise RuntimeError("CANONICAL_RANGE_MISMATCH")
        for tid in range(start,end+1):
            x,m=run_trial(s,tid,seed); new.append(x); measures.append(m)
        block=out/f"block_{start}_{end}.parquet"
        pq.write_table(pa.Table.from_pylist([dataclasses.asdict(x) for x in new]),block)
        combined=rs+new
        meta={"scenario":s,"trial_id_start":start,"trial_id_end":end,"trial_count":100,"elapsed_seconds":sum(m["elapsed_seconds"] for m in measures),"max_rss_kb":int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),"cpu_count":os.cpu_count(),"fingerprint_sha256":dataset_fp(new),"per_trial_sha256":[result_sha(x) for x in new],"log_events":False,"source_sha":source,"run_id":str(current_run),"baseline_fingerprint_sha256":basefp,"combined_fingerprint_sha256":dataset_fp(combined)}
        write_json(out/f"block_{start}_{end}_metadata.json",meta)
        for p in sorted(baseline_root.rglob("block_*.parquet")): shutil.copy2(p,out/p.name)
        for p in sorted(baseline_root.rglob("*_metadata.json")): shutil.copy2(p,out/p.name)
        write_json(out/"resume_descriptor.json",{"schema_version":"stage10-resume-v1","scenario":s,"source_sha":source,"master_seed":seed,"baseline_trials":len(rs),"canonical_trials_added":100,"new_trial_range":[start,end],"next_trial_id":end+1,"baseline_fingerprint_sha256":basefp,"new_block_fingerprint_sha256":dataset_fp(new),"combined_dataset_fingerprint_sha256":dataset_fp(combined),"baseline_state_sha":st.get("state_sha"),"baseline_final_status":st.get("final_status"),"baseline_stable_at_n":st.get("stable_at_n"),"baseline_next_check_n":st.get("next_check_n"),"baseline_stability_history":st.get("stability_history",[])})
        canonical_added=100
    elif mode=="c100":
        if end-start+1!=20 or len(rs)!=1: raise RuntimeError("C100_CHUNK_RANGE_MISMATCH")
        base=rs[0]
        for sample in range(start,end+1):
            x,m=run_trial(s,1,seed); m["benchmark_sample_id"]=sample
            a=dataclasses.asdict(x); b=dataclasses.asdict(base); a.pop("trial_id",None); b.pop("trial_id",None)
            if a!=b: raise RuntimeError(f"C100_RESULT_MISMATCH:{sample}")
            measures.append(m)
        raw=json.dumps({"schema_version":"stage10-c100-v1","scenario":s,"benchmark_sample_start":start,"benchmark_sample_end":end,"trial_id":1,"canonical_trials_added":0,"baseline_fingerprint_sha256":basefp,"measurements":measures},ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()
        (out/"benchmark_samples.json").write_bytes(raw)
        with gzip.open(out/"benchmark_samples.json.gz","wb",compresslevel=6) as fh: fh.write(raw)
        write_json(out/"resume_descriptor.json",{"schema_version":"stage10-resume-v1","scenario":s,"source_sha":source,"master_seed":seed,"baseline_trials":1,"canonical_trials_added":0,"benchmark_only":True,"benchmark_sample_range":[start,end],"baseline_fingerprint_sha256":basefp})
        canonical_added=0
    else: raise SystemExit("unsupported mode")
    chunk_elapsed=time.perf_counter()-t0; chunk_finished=utc_now(); dur=[m["elapsed_seconds"] for m in measures]
    files=[p for p in out.rglob("*") if p.is_file()]
    write_json(out/"metrics.json",{"schema_version":"stage10-benchmark-v1","scenario":s,"mode":mode,"chunk_id":((start-1)//20+1 if mode=="c100" else 1),"benchmark_sample_range":[start,end] if mode=="c100" else None,"canonical_trial_range":[start,end] if mode=="canonical" else None,"executions_completed":len(measures),"executions_failed":0,"errors":[],"chunk_started_utc":chunk_started,"chunk_finished_utc":chunk_finished,"simulation_wall_time_seconds":sum(dur),"chunk_end_to_end_seconds":chunk_elapsed,"cpu_user_seconds":sum(m["cpu_user_seconds"] for m in measures),"cpu_system_seconds":sum(m["cpu_system_seconds"] for m in measures),"peak_rss_mb":resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,"executions_per_second":len(measures)/sum(dur),"per_execution_durations_seconds":dur,"p50_seconds":percentile(dur,.5),"p95_seconds":percentile(dur,.95),"p99_seconds":percentile(dur,.99),"output_uncompressed_bytes":sum(p.stat().st_size for p in files),"source_sha":source,"requirements_blob_sha":blob_sha("requirements.txt"),"manifest_blob_sha":blob_sha("docs/stage9a/dataset_manifest.json"),"baseline_fingerprint_sha256":basefp,"final_dataset_fingerprint_sha256":dataset_fp(rs+new) if mode=="canonical" else basefp,"canonical_trials_added":canonical_added,"master_seed":seed,"expected_source_run_id":expected_run,"benchmark_run_id":current_run,"baseline_state":{"final_status":st.get("final_status"),"stable_at_n":st.get("stable_at_n"),"next_check_n":st.get("next_check_n"),"stability_history":st.get("stability_history",[]),"final_fingerprint":st.get("final_fingerprint")},"environment":{"python_version":sys.version,"runner_os":os.environ.get("RUNNER_OS"),"runner_arch":os.environ.get("RUNNER_ARCH"),"image_os":os.environ.get("ImageOS"),"image_version":os.environ.get("ImageVersion"),"cpu_count":os.cpu_count(),"cpu_model":platform.processor(),"platform":platform.platform()}})

if __name__=="__main__": main(sys.argv[1:])
