from __future__ import annotations
import argparse,hashlib,json
from collections import Counter
from dataclasses import asdict
from itertools import zip_longest
from pathlib import Path
from typing import Any
import pyarrow as pa, pyarrow.parquet as pq
import constants,monte_carlo
RUN="40731224990"; SOURCE_COMMIT="a23ba71f48487f3ebead99bc30039b14ef9b7609"; SOURCE_SHA="da1a9ea9b5cd789c944de3f07b08395bb67c49e7"; COHORT="s6-v23-da1a9ea9"; SEED=20270101; N=2400; LABEL="REPLAY_RECONSTRUCTED_NOT_ORIGINAL_PRESERVED"
FIELDS=("Cash","Accounts_Receivable","Guarantee_Claim_Receivable","Gross_Bike_Assets","Accumulated_Depreciation","Net_Bike_Assets","Total_Assets","Total_Equity","Liabilities","Balance_Difference")
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""): h.update(b)
 return h.hexdigest()
def validate_balance(r,s,t):
 for f in FIELDS:
  if f not in r or type(r[f]) is not int: raise RuntimeError(f"REPLAY_BALANCE_FIELD_INVALID:{s}:{t}:{f}")
 if r["Balance_Difference"]!=0 or r["Total_Assets"]!=r["Total_Equity"]: raise RuntimeError(f"REPLAY_ASSETS_EQUITY_MISMATCH:{s}:{t}:{r['date']}")
 if r["Net_Equity"]!=r["Total_Equity"] or r["Liabilities"]!=0: raise RuntimeError(f"REPLAY_BALANCE_IDENTITY_MISMATCH:{s}:{t}:{r['date']}")
def main():
 p=argparse.ArgumentParser()
 for x in ("scenario","source-artifact-name","source-artifact-digest"): p.add_argument("--"+x,required=True)
 p.add_argument("--source-artifact-dir",required=True,type=Path); p.add_argument("--output-dir",required=True,type=Path); p.add_argument("--source-artifact-id",required=True,type=int); p.add_argument("--overlay-dir",required=True,type=Path); p.add_argument("--workers",type=int,default=2); p.add_argument("--batch-trials",type=int,default=40); a=p.parse_args()
 if constants.MASTER_SEED!=SEED: raise RuntimeError("MASTER_SEED_DEFAULT_DRIFT")
 if Path(monte_carlo.__file__).resolve()!=a.overlay_dir.resolve()/"monte_carlo.py": raise RuntimeError("REPLAY_OVERLAY_NOT_IMPORTED")
 ms=list(a.source_artifact_dir.rglob("scenario_manifest.json"))
 if len(ms)!=1: raise RuntimeError(f"SOURCE_MANIFEST_CARDINALITY:{len(ms)}")
 mp=ms[0]; m=json.loads(mp.read_text())
 expected={"scenario_id":a.scenario,"source_sha":SOURCE_SHA,"cohort_id":COHORT,"master_seed":SEED,"trial_count":N,"trial_id_start":1,"trial_id_end":N,"run_id":RUN,"git_commit":SOURCE_COMMIT}
 for k,v in expected.items():
  if m.get(k)!=v: raise RuntimeError(f"SOURCE_MANIFEST_IDENTITY_MISMATCH:{k}:{m.get(k)!r}")
 src=mp.parent
 for name in ("trials_summary.parquet","daily_snapshots.parquet"):
  e=m.get("files",{}).get(name); f=src/name
  if not e or not f.is_file() or f.stat().st_size!=e.get("size_bytes") or sha(f)!=e.get("sha256"): raise RuntimeError(f"SOURCE_ARTIFACT_HASH_MISMATCH:{name}")
 old=pq.read_table(src/"trials_summary.parquet",columns=["trial_id","trial_fingerprint"]).to_pylist()
 oldfp={int(x["trial_id"]):str(x["trial_fingerprint"]) for x in old}
 if set(oldfp)!=set(range(1,N+1)): raise RuntimeError("SOURCE_TRIAL_COVERAGE_INVALID")
 out=a.output_dir.resolve(); out.mkdir(parents=True,exist_ok=True); tp=out/"trials_summary.parquet"; dp=out/"daily_balance_snapshots.parquet"; tw=dw=None; newfp={}; checked=0
 try:
  for start in range(1,N+1,a.batch_trials):
   ids=list(range(start,min(N+1,start+a.batch_trials)))
   results,daily=monte_carlo.run_trials_parallel(a.scenario,ids,a.workers,master_seed=SEED,source_sha=SOURCE_SHA)
   if [int(x.trial_id) for x in results]!=ids: raise RuntimeError("REPLAY_TRIAL_ORDER_INVALID")
   tr=[]; dr=[]
   for result in results:
    tid=int(result.trial_id); newfp[tid]=str(result.trial_fingerprint)
    rec=asdict(result); rec.update(source_sha=SOURCE_SHA,cohort_id=COHORT,model_schema_version="v2.3",replay_label=LABEL); tr.append(rec)
    rows=sorted(daily[tid],key=lambda x:str(x["date"]))
    if not rows: raise RuntimeError(f"REPLAY_DAILY_ROWS_MISSING:{tid}")
    for row in rows:
     x=dict(row); x.update(scenario_id=a.scenario,source_sha=SOURCE_SHA,cohort_id=COHORT,schema_version="v2.3",replay_label=LABEL)
     validate_balance(x,a.scenario,tid); dr.append(x); checked+=1
   tt=pa.Table.from_pylist(tr); dt=pa.Table.from_pylist(dr)
   if tw is None: tw=pq.ParquetWriter(tp,tt.schema,compression="zstd"); dw=pq.ParquetWriter(dp,dt.schema,compression="zstd")
   else: tt=tt.cast(tw.schema); dt=dt.cast(dw.schema)
   tw.write_table(tt); dw.write_table(dt)
   print(json.dumps({"scenario":a.scenario,"completed_trials":len(newfp),"balance_rows_checked":checked}),flush=True)
 finally:
  if tw: tw.close()
  if dw: dw.close()
 if set(newfp)!=set(oldfp): raise RuntimeError("REPLAY_TRIAL_COVERAGE_MISMATCH")
 bad=[i for i in sorted(oldfp) if oldfp[i]!=newfp[i]]
 if bad: raise RuntimeError(f"REPLAY_FINANCIAL_FINGERPRINT_MISMATCH:{bad[:20]}")
 a_pf=pq.ParquetFile(src/"daily_snapshots.parquet"); b_pf=pq.ParquetFile(dp); common=[f for f in a_pf.schema_arrow.names if f in b_pf.schema_arrow.names]
 if not {"trial_id","date"}.issubset(common): raise RuntimeError("DAILY_OVERLAP_KEYS_MISSING")
 ac=Counter(); bc=Counter(); compared=0; prev=None
 for ba,bb in zip_longest(a_pf.iter_batches(batch_size=20000,columns=common),b_pf.iter_batches(batch_size=20000,columns=common)):
  if ba is None or bb is None or ba.num_rows!=bb.num_rows: raise RuntimeError("DAILY_ROW_COVERAGE_MISMATCH")
  for oldrow,newrow in zip(ba.to_pylist(),bb.to_pylist()):
   ko=(int(oldrow["trial_id"]),str(oldrow["date"])); kn=(int(newrow["trial_id"]),str(newrow["date"]))
   if ko!=kn or (prev is not None and ko<prev): raise RuntimeError(f"DAILY_DATE_ORDER_MISMATCH:{ko}:{kn}")
   for f in common:
    if oldrow[f]!=newrow[f]: raise RuntimeError(f"OVERLAPPING_DAILY_FIELD_MISMATCH:{ko}:{f}")
   prev=ko; ac[ko[0]]+=1; bc[kn[0]]+=1; compared+=1
 if ac!=bc or set(ac)!=set(range(1,N+1)): raise RuntimeError("DAILY_PER_TRIAL_COVERAGE_MISMATCH")
 report={"schema_version":"e2-s6-deterministic-replay-scenario-v1","status":"PASS_SCOPED_REPLAY_RECONSTRUCTION","replay_label":LABEL,"scenario_id":a.scenario,"source_run_id":RUN,"source_execution_commit":SOURCE_COMMIT,"source_sha":SOURCE_SHA,"cohort_id":COHORT,"master_seed":SEED,"trial_count":N,"trial_id_start":1,"trial_id_end":N,"source_artifact":{"name":a.source_artifact_name,"id":a.source_artifact_id,"digest":a.source_artifact_digest,"manifest_sha256":sha(mp)},"financial_trial_fingerprints":{"status":"PASS_EXACT_MATCH","matched":N,"mismatched":0},"daily_overlap_comparison":{"status":"PASS_EXACT_OVERLAP","rows_compared":compared,"common_fields":common,"trial_count":len(ac)},"balance_sheet":{"status":"PASS_ALL_REPLAY_DAILY_ROWS","rows_checked":checked,"fields":list(FIELDS),"assets_equal_equity_mismatches":0},"source_daily_rows":a_pf.metadata.num_rows,"replay_daily_rows":b_pf.metadata.num_rows,"production_gate_a_status":"NOT_DECLARED_REQUIRES_SEPARATE_REVIEW","historical_source_artifacts_modified":False,"historical_manifests_modified":False,"model_business_logic_modified":False,"output_files":{"trials_summary.parquet":{"size_bytes":tp.stat().st_size,"sha256":sha(tp)},"daily_balance_snapshots.parquet":{"size_bytes":dp.stat().st_size,"sha256":sha(dp)}}}
 (out/"replay_scenario_manifest.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"status":report["status"],"scenario":a.scenario,"trials":N,"daily_rows":checked,"fingerprints":"PASS","overlap":"PASS","balance":"PASS"}),flush=True)
if __name__=="__main__": main()
