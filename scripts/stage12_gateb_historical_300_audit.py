#!/usr/bin/env python3
"""Read-only Gate B N=300 input audit. Does not execute or resume trials."""
from __future__ import annotations
import argparse, hashlib, json, math, os, subprocess, tarfile, tempfile, zipfile
from pathlib import Path
import numpy as np
import pyarrow.parquet as pq
from scipy.stats import t

SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
MASTER_SEED = 20270101
STAGE7_RUN_ID = 37225915321
STAGE12_RUN_ID = 37964656154
TRIAL_IDS = list(range(1, 301))
METRICS = {
    "Final_Net_Project_Equity": "final_net_project_equity",
    "Partner1_Final_Entitlement": "partner1_final_entitlement",
    "Partner2_Final_Entitlement": "partner2_final_entitlement",
}
RNG_POLICY = "rng.py:SHA-256(seed key master_seed|scenario_id|trial_id|bike_id|date|event_type); draw=first_8_digest_bytes_big_endian/2^64; probability boundaries are deterministic"
SAMPLING_POLICY = "one-based contiguous trial IDs; C100 scenarios use 1..1; non-C100 scenarios use 1..550; one materialization per scenario/trial; no cross-run inputs or resume"
TRIAL_ID_POLICY = "one-based contiguous trial IDs from 1 to scenario target; no duplicate IDs"
STABILITY_POLICY = "C100 uses one deterministic trial and no CI gate; non-C100 checkpoint N=300 then +50; 95% Student-t CI half-width <1% of absolute mean for Final_Net_Project_Equity, Partner1_Final_Entitlement, Partner2_Final_Entitlement; CI_ABSOLUTE_EPSILON=1; three consecutive successful checkpoints; accepted N=550 (checkpoints 450, 500, 550)"

def sha256_file(path):
    d = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""): d.update(chunk)
    return d.hexdigest()

def download_artifact(artifact_id, target):
    repo = os.environ["GITHUB_REPOSITORY"]
    with target.open("wb") as stream:
        p = subprocess.run(["gh","api",f"repos/{repo}/actions/artifacts/{artifact_id}/zip"],stdout=stream,stderr=subprocess.PIPE)
    if p.returncode or target.stat().st_size == 0 or not zipfile.is_zipfile(target):
        raise RuntimeError(f"ARTIFACT_DOWNLOAD_FAILED id={artifact_id} exit={p.returncode} {p.stderr.decode('utf-8',errors='replace')[-1200:]}")

def unpack(path, dest):
    dest.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(path) as z: z.extractall(dest)
    for tarpath in list(dest.rglob("*.tar.gz")) + list(dest.rglob("*.tgz")):
        out = tarpath.parent / (tarpath.name[:-7] if tarpath.name.endswith(".tar.gz") else tarpath.stem)
        out.mkdir(parents=True,exist_ok=True); root=out.resolve()
        with tarfile.open(tarpath,"r:gz") as tf:
            for member in tf.getmembers():
                target=(out/member.name).resolve()
                if target != root and root not in target.parents: raise RuntimeError("TAR_PATH_TRAVERSAL_REJECTED")
                if member.issym() or member.islnk() or member.isdev(): raise RuntimeError("UNEXPECTED_TAR_ENTRY")
            tf.extractall(out)

def unique_file(root, name):
    found=[p for p in root.rglob(name) if p.is_file()]
    if len(found)!=1: raise RuntimeError(f"EXPECTED_ONE_{name}: {len(found)}")
    return found[0]

def read_json(path): return json.loads(path.read_text(encoding="utf-8"))

def fingerprint_map(meta):
    raw=meta.get("per_trial_sha256")
    if isinstance(raw,dict):
        out={}
        for k,v in raw.items():
            if isinstance(v,dict): v=v.get("sha256",v.get("fingerprint",v.get("result_sha256")))
            out[int(k)]=str(v)
        return out
    if isinstance(raw,list):
        out={}
        for i,v in enumerate(raw):
            tid=i+int(meta.get("trial_id_start",1))
            if isinstance(v,dict):
                tid=int(v.get("trial_id",tid)); v=v.get("sha256",v.get("fingerprint",v.get("result_sha256")))
            out[tid]=str(v)
        return out
    raise RuntimeError("per_trial_sha256_MISSING_OR_UNSUPPORTED")

def ci_points(rows, scenario):
    n=len(rows); critical=float(t.ppf(0.975,df=n-1)); points=[]
    for label,field in METRICS.items():
        vals=np.asarray([int(r[field]) for r in rows],dtype=np.float64)
        mean=float(vals.mean()); std=float(vals.std(ddof=1)); hw=float(critical*std/math.sqrt(n))
        if abs(mean)<=1:
            status="UNDEFINED_BUSINESS_RULE"; rel=None if mean==0 else hw/abs(mean); limit=None
            reason="abs(mean) <= CI_ABSOLUTE_EPSILON=1; exact near-zero inequality is not defined in binding text"
        else:
            rel=hw/abs(mean); limit=.01*abs(mean)
            status="PASS" if hw<limit else "FAIL"
            reason="Student-t 95% half-width < 1% of absolute mean"
        points.append({"scenario_id":scenario,"metric":label,"field":field,"n":n,"df":n-1,"confidence":.95,"distribution":"Student-t","t_critical":critical,"mean":mean,"sample_std_ddof1":std,"ci_half_width_95":hw,"relative_half_width":rel,"required_half_width":limit,"ci_absolute_epsilon":1,"status_at_N300":status,"rationale":reason})
    return points

def verify_scenario(scenario, stage12_id, stage7_id, tmp):
    out={"scenario_id":scenario,"stage12_artifact_id":stage12_id,"stage7_artifact_id":stage7_id,"stage12_run_id":STAGE12_RUN_ID,"stage7_run_id":STAGE7_RUN_ID,"source_sha":SOURCE_SHA,"master_seed":MASTER_SEED,"historical_sampling_policy":"+50/550","input_identity_status":"PENDING","checkpoint_metrics":[],"trial_metrics":[],"errors":[]}
    try:
        z12=tmp/f"{scenario}-12.zip"; z7=tmp/f"{scenario}-7.zip"
        download_artifact(stage12_id,z12); download_artifact(stage7_id,z7)
        p12=tmp/f"{scenario}-12"; p7=tmp/f"{scenario}-7"
        unpack(z12,p12); unpack(z7,p7)
        daily=unique_file(p12,f"{scenario}.parquet")
        block=unique_file(p7,"block_1_300.parquet")
        mpath=unique_file(p7,"block_1_300_metadata.json")
        md=read_json(mpath)
        if md.get("source_sha")!=SOURCE_SHA or int(md.get("run_id",-1))!=STAGE7_RUN_ID: raise RuntimeError("STAGE7_SOURCE_OR_RUN_ID_MISMATCH")
        if md.get("scenario_id",md.get("scenario"))!=scenario or int(md.get("trial_id_start",-1))!=1 or int(md.get("trial_id_end",-1))!=300 or int(md.get("trial_count",-1))!=300: raise RuntimeError("STAGE7_BLOCK_IDENTITY_MISMATCH")
        hmap=fingerprint_map(md)
        if sorted(hmap)!=TRIAL_IDS or any(not v or v=="None" for v in hmap.values()): raise RuntimeError("STAGE7_HASH_COVERAGE_MISMATCH")
        rf=read_json(Path("docs/stage12/roll_forward_validation.json")).get("scenarios",{}).get(scenario)
        if not isinstance(rf,dict): raise RuntimeError("CP12C_SCENARIO_RECORD_MISSING")
        daily_sha=sha256_file(daily)
        if daily_sha!=rf.get("content_sha256"): raise RuntimeError(f"STAGE12_PARQUET_SHA_MISMATCH {daily_sha} expected={rf.get('parquet_sha256')}")
        dt=pq.read_table(daily,columns=["scenario_id","trial_id","source_sha","master_seed","result_sha256"])
        drows=dt.to_pylist()
        if len(drows)!=int(rf.get("daily_rows",-1)): raise RuntimeError(f"STAGE12_ROW_COUNT_MISMATCH {len(drows)} expected={rf.get('daily_rows')}")
        if any(r["scenario_id"]!=scenario or r["source_sha"]!=SOURCE_SHA or int(r["master_seed"])!=MASTER_SEED for r in drows): raise RuntimeError("STAGE12_ROW_IDENTITY_MISMATCH")
        raw=(pq.read_schema(daily).metadata or {}).get(b"stage12.dataset_identity")
        if raw is None: raise RuntimeError("STAGE12_IDENTITY_METADATA_MISSING")
        identity=json.loads(raw.decode("utf-8"))
        expected={"schema_version":"stage12-daily-accounting-v1","scenario":scenario,"source_sha":SOURCE_SHA,"master_seed":MASTER_SEED,"rng_policy":RNG_POLICY,"sampling_policy":SAMPLING_POLICY,"stability_policy":STABILITY_POLICY,"trial_id_policy":TRIAL_ID_POLICY}
        mismatches={k:{"actual":identity.get(k),"expected":v} for k,v in expected.items() if identity.get(k)!=v}
        if mismatches: raise RuntimeError(f"STAGE12_DATASET_IDENTITY_MISMATCH {json.dumps(mismatches,sort_keys=True)}")
        hashes={}
        for row in drows: hashes.setdefault(int(row["trial_id"]),set()).add(str(row["result_sha256"]))
        if not set(TRIAL_IDS).issubset(hashes) or any(len(hashes.get(i,set()))!=1 for i in TRIAL_IDS): raise RuntimeError("STAGE12_TRIAL_HASH_COVERAGE_OR_STABILITY_FAILURE")
        if any(len(x)!=64 for hs in hashes.values() for x in hs): raise RuntimeError("STAGE12_INVALID_RESULT_SHA256")
        bt=pq.read_table(block); brows=bt.to_pylist()
        if len(brows)!=300 or not {"scenario_id","trial_id",*METRICS.values()}.issubset(set(bt.column_names)): raise RuntimeError("STAGE7_PARQUET_SCHEMA_OR_COUNT_MISMATCH")
        byid={}
        for r in brows:
            tid=int(r["trial_id"])
            if tid in byid: raise RuntimeError(f"STAGE7_DUPLICATE_TRIAL_ID {tid}")
            byid[tid]=r
        if sorted(byid)!=TRIAL_IDS: raise RuntimeError("STAGE7_TRIAL_ID_COVERAGE_MISMATCH")
        for tid in TRIAL_IDS:
            r=byid[tid]
            if r["scenario_id"]!=scenario: raise RuntimeError(f"STAGE7_ROW_SCENARIO_MISMATCH {tid}")
            stage12_hash=next(iter(hashes[tid]))
            if hmap[tid]!=stage12_hash: raise RuntimeError(f"TRIAL_FINGERPRINT_MISMATCH {tid} stage7={hmap[tid]} stage12={stage12_hash}")
            metrics={}
            for label,field in METRICS.items():
                v=r[field]
                if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(float(v)): raise RuntimeError(f"INVALID_METRIC {tid}/{field}/{v!r}")
                metrics[field]=int(v)
            out["trial_metrics"].append({"scenario_id":scenario,"trial_id":tid,**metrics,"result_sha256":hmap[tid],"source_sha":SOURCE_SHA,"master_seed":MASTER_SEED,"stage7_run_id":STAGE7_RUN_ID,"stage12_provenance_run_id":STAGE12_RUN_ID,"historical_sampling_policy":"+50/550","schema_version":identity["schema_version"],"stage12_parquet_sha256":daily_sha})
        out.update({"input_identity_status":"PASS","stage12_daily_rows":len(drows),"stage12_parquet_sha256":daily_sha,"stage7_block_parquet_sha256":sha256_file(block),"stage7_block_metadata_sha256":sha256_file(mpath),"stage12_dataset_identity":identity})
        out["checkpoint_metrics"]=ci_points(out["trial_metrics"],scenario)
    except Exception as exc:
        out["input_identity_status"]="FAIL"; out["errors"].append(str(exc))
    return out

def aggregate(root):
    expected=["C030_G000","C030_G030","C030_G050","C030_G070","C030_G100","C050_G000","C050_G030","C050_G050","C050_G070","C050_G100","C070_G000","C070_G030","C070_G050","C070_G070","C070_G100","C085_G000","C085_G030","C085_G050","C085_G070","C085_G100"]
    reports={}
    for path in root.glob("*.json"):
        try:
            item=read_json(path); reports[item["scenario_id"]]=item
        except Exception as exc: reports[path.stem]={"input_identity_status":"FAIL","errors":[str(exc)]}
    good=len(reports)==20 and all(s in reports and reports[s].get("input_identity_status")=="PASS" for s in expected)
    points=[p for s in expected if s in reports for p in reports[s].get("checkpoint_metrics",[])]
    statuses=[p["status_at_N300"] for p in points]
    if not good: status="HOLD_INPUT_IDENTITY_INCOMPLETE"
    elif len(points)!=60: status="HOLD_METRIC_COVERAGE_INCOMPLETE"
    elif "UNDEFINED_BUSINESS_RULE" in statuses: status="UNDEFINED_BUSINESS_RULE"
    elif all(x=="PASS" for x in statuses): status="PASS_AT_N300_ONLY"
    else: status="FAIL_AT_N300_REQUIRES_ESCALATION"
    report={"report_id":"GATE_B_HISTORICAL_300_INPUT_AND_CHECKPOINT","status":status,"historical_reuse_authorization":"D-2026-10-11-01","stage7_run_id":STAGE7_RUN_ID,"stage12_provenance_run_id":STAGE12_RUN_ID,"source_sha":SOURCE_SHA,"master_seed":MASTER_SEED,"historical_sampling_policy":"+50/550","future_policy_source":"D-2026-10-10-01 / Amendment-01","authorized_historical_trial_ids":"1..300 per each of 20 non-C100 scenarios, analytic inputs only","scenario_count_expected":20,"scenario_count_verified":sum(reports.get(s,{}).get("input_identity_status")=="PASS" for s in expected),"historical_trial_inputs_expected":6000,"historical_trial_inputs_verified":sum(len(reports.get(s,{}).get("trial_metrics",[])) for s in expected),"metric_points_expected_at_N300":60,"metric_points_reported":len(points),"checkpoint_metrics":points,"scenarios":reports,"overall_gate_b":"NOT_ESTABLISHED_BY_N300_ALONE","limitations":["D-2026-10-10-01 requires three consecutive successful checkpoints; this report establishes N=300 only.","If abs(mean) <= CI_ABSOLUTE_EPSILON=1, the exact near-zero CI comparison is not specified; no fallback inequality is guessed.","D-2026-10-11-01 authorizes historical analytical reuse only for IDs 1..300. Historical IDs 301..550 are completed under the old policy but not included in that specific reuse authorization.","N=600 therefore requires an explicit disposition for completed IDs 301..550 so that neither unauthorized reuse nor rerunning completed trials occurs.","This report does not establish Gate A, C100 determinism, or final three-checkpoint Gate B stability."],"no_trials_executed":True,"historical_data_modified":False,"gate_b_pass":False}
    out=Path("results_gateb"); out.mkdir(parents=True,exist_ok=True)
    (out/"gate_b_n300_report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    lines=["# Gate B historical N=300 input and checkpoint audit","",f"Checkpoint result: {status}",f"Verified scenarios: {report['scenario_count_verified']}/20",f"Verified historical trial inputs: {report['historical_trial_inputs_verified']}/6000",f"CI points: {len(points)}/60","","No trial was executed; historical inputs are read-only.","This is N=300 only, not final Gate B or a three-consecutive-checkpoint pass.","","| Scenario | Metric | Mean | 95% Student-t half-width | Relative half-width | Required limit | Status |","|---|---|---:|---:|---:|---:|---|"]
    for p in points: lines.append(f"| {p['scenario_id']} | {p['metric']} | {p['mean']} | {p['ci_half_width_95']} | {p['relative_half_width']} | {p['required_half_width']} | {p['status_at_N300']} |")
    lines.extend(["","## Unresolved limits","", "- N=600 is blocked until a binding disposition is provided for already-completed IDs 301–550.", "- Near-zero CI handling remains UNDEFINED_BUSINESS_RULE if triggered.", "- Gate A, C100 determinism and final three-checkpoint stability remain separate."])
    (out/"gate_b_n300_report.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    return report

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--scenario"); ap.add_argument("--stage12-artifact",type=int); ap.add_argument("--stage7-artifact",type=int); ap.add_argument("--aggregate-dir")
    args=ap.parse_args()
    if args.aggregate_dir:
        r=aggregate(Path(args.aggregate_dir))
        print(json.dumps({"status":r["status"],"scenario_count_verified":r["scenario_count_verified"],"trial_inputs_verified":r["historical_trial_inputs_verified"],"metric_points":r["metric_points_reported"],"report":"results_gateb/gate_b_n300_report.json"},indent=2))
        return 0 if r["status"]=="PASS_AT_N300_ONLY" else 1
    if not args.scenario or args.stage12_artifact is None or args.stage7_artifact is None: ap.error("select scenario mode or aggregate mode")
    out=Path("results_gateb"); out.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"gateb_{args.scenario}_") as tmp: item=verify_scenario(args.scenario,args.stage12_artifact,args.stage7_artifact,Path(tmp))
    path=out/f"{args.scenario}.json"; path.write_text(json.dumps(item,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"scenario":args.scenario,"input_identity_status":item["input_identity_status"],"errors":item["errors"],"ci_points":item["checkpoint_metrics"]},indent=2))
    return 0 if item["input_identity_status"]=="PASS" else 1
if __name__=="__main__": raise SystemExit(main())
