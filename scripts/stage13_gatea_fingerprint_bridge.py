#!/usr/bin/env python3
"""Read-only Gate A bridge: rehash Stage 7/10 trial rows and compare Stage 12 daily hashes."""
from __future__ import annotations
import argparse, hashlib, json, re, subprocess, tempfile, traceback, zipfile
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any
import pyarrow.parquet as pq

REPO = "yasmin977209-ux/motorcycle-simulation"
STAGE7_RUN, STAGE7_HEAD = 37225915321, "e0b2fab6710833774937d778097363d7a8ee8e59"
STAGE10_RUN, STAGE10_HEAD = 37709936740, "ca73f2df37baacebbcad965fc5f433f129675820"
STAGE12_RUN, STAGE12_HEAD = 37964656154, "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
MASTER_SEED = 20270101
MANIFEST_GLOBAL = "892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6"
STAGE12_GLOBAL = "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44"
SCENARIOS = [f"C{c:03d}_G{g:03d}" for c in (100,85,70,50,30) for g in (100,70,50,30,0)]
BASE_BLOCKS = ((1,300),(301,350),(351,400),(401,450))
IDENTITY_KEY = b"stage12.dataset_identity"
SCHEMA_VERSION = "stage12-daily-accounting-v1"
RNG_POLICY = "rng.py:SHA-256(seed key master_seed|scenario_id|trial_id|bike_id|date|event_type); draw=first_8_digest_bytes_big_endian/2^64; probability boundaries are deterministic"
SAMPLING_POLICY = "one-based contiguous trial IDs; C100 scenarios use 1..1; non-C100 scenarios use 1..550; one materialization per scenario/trial; no cross-run inputs or resume"
STABILITY_POLICY = "C100 uses one deterministic trial and no CI gate; non-C100 checkpoint N=300 then +50; 95% Student-t CI half-width <1% of absolute mean for Final_Net_Project_Equity, Partner1_Final_Entitlement, Partner2_Final_Entitlement; CI_ABSOLUTE_EPSILON=1; three consecutive successful checkpoints; accepted N=550 (checkpoints 450, 500, 550)"
TRIAL_ID_POLICY = "one-based contiguous trial IDs from 1 to scenario target; no duplicate IDs"
COLUMN_TYPES = {
    "scenario_id":"string","trial_id":"int64","date":"string","source_sha":"string","master_seed":"int64",
    "Opening_Cash":"int64","cash_inflows":"int64","cash_outflows":"int64","Closing_Cash":"int64",
    "Opening_AR":"int64","ar_accruals":"int64","ar_collections":"int64","ar_transfers_to_guarantee":"int64","Closing_AR":"int64",
    "Opening_Gross_Bike_Assets":"int64","capitalized_purchases_and_customs":"int64","gross_writeoffs_on_ownership":"int64",
    "Closing_Gross_Bike_Assets":"int64","Opening_Accumulated_Depreciation":"int64","depreciation_expense":"int64",
    "ad_removed_on_writeoff":"int64","Closing_Accumulated_Depreciation":"int64","Net_Bike_Assets":"int64","Capital":"int64",
    "Retained_Earnings":"int64","Opening_Equity":"int64","Operating_Net_Profit":"int64","Closing_Equity":"int64",
    "Guarantee_Claim_Receivable":"int64","Total_Assets":"int64","Liabilities":"int64","Balance_Difference":"int64",
    "Final_Close_Date":"string","Simulation_Stopped":"bool","Active_Bikes":"int64","Owned_Transferred_Bikes":"int64",
    "Pending_Claims":"int64","result_sha256":"string"
}

def sha_bytes(b: bytes) -> str: return hashlib.sha256(b).hexdigest()
def sha_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()

def parse_json_bytes(raw: bytes, *, allow_known_stage10_suffix: bool=False) -> tuple[dict[str,Any],str]:
    # The exact Stage 10 writer emitted a literal backslash+n after its JSON object.
    # Only that source-proven suffix is removed from the in-memory parsing buffer.
    literal_tail=bytes((125,92,110))  # close brace + backslash + 'n'
    if raw.endswith(literal_tail):
        if not allow_known_stage10_suffix:
            raise ValueError("UNEXPECTED_LITERAL_BACKSLASH_N_JSON_SUFFIX")
        obj_bytes=raw[:-2]
        if not obj_bytes.endswith(b"}"):
            raise ValueError("STAGE10_SUFFIX_TRIM_DID_NOT_END_AT_JSON_OBJECT")
        value=json.loads(obj_bytes.decode("utf-8"))
        if not isinstance(value,dict): raise ValueError("JSON_ROOT_NOT_OBJECT")
        return value,"known_stage10_literal_backslash_n_suffix_removed_in_memory"
    value=json.loads(raw.decode("utf-8"))
    if not isinstance(value,dict): raise ValueError("JSON_ROOT_NOT_OBJECT")
    return value,"standard_json"

def gh_json(endpoint: str) -> dict[str,Any]:
    r=subprocess.run(["gh","api",endpoint],text=True,capture_output=True,check=False)
    if r.returncode: raise RuntimeError(f"GH_API_FAILED endpoint={endpoint} exit={r.returncode} stderr={r.stderr[-1200:]}")
    v=json.loads(r.stdout)
    if not isinstance(v,dict): raise RuntimeError(f"GH_API_RESPONSE_NOT_OBJECT endpoint={endpoint}")
    return v

def validate_run(run_id:int,head:str,conclusion:str|None)->dict:
    r=gh_json(f"repos/{REPO}/actions/runs/{run_id}")
    if int(r.get("id",-1))!=run_id or r.get("head_sha")!=head:
        raise RuntimeError(f"RUN_IDENTITY_MISMATCH run={run_id} expected_head={head} actual_head={r.get('head_sha')}")
    if conclusion is not None and r.get("conclusion")!=conclusion:
        raise RuntimeError(f"RUN_CONCLUSION_MISMATCH run={run_id} expected={conclusion} actual={r.get('conclusion')}")
    return {k:r.get(k) for k in ("id","head_sha","head_branch","status","conclusion","created_at","html_url")}

def artifact_index(run_id:int)->tuple[dict[str,dict],dict]:
    p=gh_json(f"repos/{REPO}/actions/runs/{run_id}/artifacts?per_page=100")
    items=p.get("artifacts")
    if not isinstance(items,list) or int(p.get("total_count",-1))!=len(items):
        raise RuntimeError(f"ARTIFACT_LIST_INCOMPLETE run={run_id}")
    out={}
    for a in items:
        if a.get("expired"): continue
        name=a.get("name")
        if not name: continue
        if name in out: raise RuntimeError(f"DUPLICATE_ARTIFACT_NAME run={run_id} name={name}")
        wr=a.get("workflow_run") or {}
        if wr and int(wr.get("id",-1))!=run_id: raise RuntimeError(f"ARTIFACT_WRONG_RUN run={run_id} name={name}")
        out[name]=a
    return out,p

def find_artifact(items:dict[str,dict],name:str,run_id:int)->dict:
    a=items.get(name)
    if not a: raise RuntimeError(f"ARTIFACT_MISSING run={run_id} name={name}")
    return a

def download_artifact(artifact:dict,path:Path)->dict:
    aid=int(artifact["id"]); path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("wb") as stream:
        r=subprocess.run(["gh","api",f"repos/{REPO}/actions/artifacts/{aid}/zip"],stdout=stream,stderr=subprocess.PIPE,check=False)
    if r.returncode or not zipfile.is_zipfile(path):
        raise RuntimeError(f"ARTIFACT_DOWNLOAD_FAILED id={aid} exit={r.returncode} stderr={r.stderr.decode('utf-8',errors='replace')[-1000:]}")
    actual=sha_file(path); expected=artifact.get("digest")
    if expected and actual!=expected.removeprefix("sha256:"):
        raise RuntimeError(f"ARTIFACT_DIGEST_MISMATCH id={aid} expected={expected} actual={actual}")
    return {"artifact_id":aid,"artifact_zip_sha256":actual,"api_digest":expected}

def member(zf:zipfile.ZipFile,name:str)->bytes:
    if zf.namelist().count(name)!=1: raise RuntimeError(f"ZIP_MEMBER_COUNT name={name} count={zf.namelist().count(name)}")
    return zf.read(name)

def valid_sha(v:Any,context:str)->str:
    if not isinstance(v,str) or re.fullmatch(r"[0-9a-f]{64}",v) is None: raise RuntimeError(f"INVALID_SHA256 {context} value={v!r}")
    return v

def row_sha(row:dict[str,Any])->str:
    b=json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(",",":"),default=str).encode("utf-8")
    return hashlib.sha256(b).hexdigest()

def canonical_fingerprint(rows:list[dict[str,Any]])->str:
    def canonical(value:Any)->Any:
        if isinstance(value,float): return value.hex()
        if isinstance(value,dict): return {str(k):canonical(value[k]) for k in sorted(value,key=str)}
        if isinstance(value,(list,tuple)): return [canonical(x) for x in value]
        return value
    ordered=sorted(rows,key=lambda item:int(item["trial_id"]))
    payload="\n".join(json.dumps(canonical(row),ensure_ascii=False,sort_keys=True,separators=(",",":")) for row in ordered)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def validate_block(scenario:str,start:int,end:int,meta_raw:bytes,parquet_raw:bytes,manifest:dict,source_run:int,allow_bad_suffix:bool=False)->tuple[dict[int,str],dict]:
    meta,parse_mode=parse_json_bytes(meta_raw,allow_known_stage10_suffix=allow_bad_suffix)
    range_key=f"{start}-{end}"
    mf=manifest.get("block_fingerprints",{}).get(scenario,{}).get(range_key)
    fp=valid_sha(meta.get("fingerprint_sha256"),f"{scenario}/{range_key}/fingerprint")
    if mf is not None and fp!=mf: raise RuntimeError(f"OFFICIAL_BLOCK_FINGERPRINT_MISMATCH {scenario}/{range_key} metadata={fp} manifest={mf}")
    checks={
        "scenario":meta.get("scenario")==scenario,
        "source_sha":meta.get("source_sha")==SOURCE_SHA,
        "run_id":str(meta.get("run_id"))==str(source_run),
        "trial_id_start":int(meta.get("trial_id_start",-1))==start,
        "trial_id_end":int(meta.get("trial_id_end",-1))==end,
        "trial_count":int(meta.get("trial_count",-1))==end-start+1,
        "log_events":meta.get("log_events") is False
    }
    if not all(checks.values()): raise RuntimeError(f"SOURCE_BLOCK_METADATA_IDENTITY_MISMATCH {scenario}/{range_key} checks={checks}")
    hs=meta.get("per_trial_sha256")
    if not isinstance(hs,list) or len(hs)!=end-start+1: raise RuntimeError(f"SOURCE_BLOCK_HASH_COUNT_MISMATCH {scenario}/{range_key}")
    for i,h in enumerate(hs): valid_sha(h,f"{scenario}/{start+i}/metadata")
    rows=pq.read_table(BytesIO(parquet_raw)).to_pylist()
    if len(rows)!=end-start+1: raise RuntimeError(f"SOURCE_BLOCK_ROW_COUNT_MISMATCH {scenario}/{range_key} rows={len(rows)}")
    calculated_block_fp=canonical_fingerprint(rows)
    if calculated_block_fp!=fp: raise RuntimeError(f"SOURCE_BLOCK_FINGERPRINT_RECOMPUTE_MISMATCH {scenario}/{range_key} metadata={fp} parquet={calculated_block_fp}")
    out={}
    for offset,row in enumerate(rows):
        tid=start+offset
        if int(row.get("trial_id",-1))!=tid or row.get("scenario_id")!=scenario:
            raise RuntimeError(f"SOURCE_BLOCK_ROW_KEY_MISMATCH {scenario}/{tid}")
        calculated=row_sha(row)
        if calculated!=hs[offset]: raise RuntimeError(f"SOURCE_BLOCK_ROW_SHA_MISMATCH {scenario}/{tid} metadata={hs[offset]} parquet={calculated}")
        out[tid]=calculated
    return out,{"range":range_key,"run_id":source_run,"metadata_raw_sha256":sha_bytes(meta_raw),"parquet_raw_sha256":sha_bytes(parquet_raw),"metadata_parse_mode":parse_mode,"block_fingerprint_sha256":fp,"stage9a_official_block_fingerprint_sha256":mf,"trial_hashes_recomputed_from_parquet":len(rows),"per_trial_metadata_matches_parquet":True}

def daily_identity(scenario:str)->dict:
    return {"schema_version":SCHEMA_VERSION,"scenario":scenario,"source_sha":SOURCE_SHA,"master_seed":MASTER_SEED,"rng_policy":RNG_POLICY,"sampling_policy":SAMPLING_POLICY,"stability_policy":STABILITY_POLICY,"trial_id_policy":TRIAL_ID_POLICY}

def validate_stage12(scenario:str,p:Path,roll:dict,closure:dict,golden:dict[int,str])->tuple[list[dict],dict]:
    rs=roll.get("scenarios",{}).get(scenario); cs=closure.get("scenarios",{}).get(scenario)
    if not isinstance(rs,dict) or not isinstance(cs,dict): raise RuntimeError(f"STAGE12_SCENARIO_REPORT_MISSING {scenario}")
    expected_file_sha=rs.get("content_sha256")
    if expected_file_sha!=cs.get("content_sha256"): raise RuntimeError(f"STAGE12_VALIDATION_REPORT_SHA_DISAGREEMENT {scenario}")
    actual_file_sha=sha_file(p)
    if actual_file_sha!=expected_file_sha: raise RuntimeError(f"STAGE12_PARQUET_FILE_SHA_MISMATCH {scenario} expected={expected_file_sha} actual={actual_file_sha}")
    if rs.get("content_sha256_matches_cp12b_manifest") is not True or cs.get("content_sha256_matches_cp12c_report") is not True: raise RuntimeError(f"STAGE12_REPORT_SOURCE_HASH_GATE_NOT_PASS {scenario}")
    pf=pq.ParquetFile(p); schema=pf.schema_arrow
    if {f.name:str(f.type) for f in schema}!=COLUMN_TYPES: raise RuntimeError(f"STAGE12_SCHEMA_TYPE_MISMATCH {scenario}")
    if any(f.nullable!=(f.name=="Final_Close_Date") for f in schema): raise RuntimeError(f"STAGE12_SCHEMA_NULLABILITY_MISMATCH {scenario}")
    identity_raw=(schema.metadata or {}).get(IDENTITY_KEY)
    if identity_raw is None or json.loads(identity_raw.decode("utf-8"))!=daily_identity(scenario): raise RuntimeError(f"STAGE12_DATASET_IDENTITY_MISMATCH {scenario}")
    expected_count=1 if scenario.startswith("C100_") else 550
    if int(rs.get("trials",-1))!=expected_count or int(cs.get("trial_count",-1))!=expected_count: raise RuntimeError(f"STAGE12_TRIAL_COUNT_REPORT_MISMATCH {scenario}")
    checks=[]; count_by_trial={}; current=None; first_day=None; last_day=None; nday=0; trial_hash=None; total_rows=0
    def close_trial():
        nonlocal current,first_day,last_day,nday,trial_hash
        if current is None: return
        if first_day!=date(2027,1,1): raise RuntimeError(f"STAGE12_FIRST_DATE_MISMATCH {scenario}/{current} date={first_day}")
        if last_day is None or first_day is None or nday!=(last_day-first_day).days+1: raise RuntimeError(f"STAGE12_DAILY_GAP_OR_DUPLICATE {scenario}/{current} rows={nday}")
        if current not in golden: raise RuntimeError(f"GOLDEN_TRIAL_MISSING {scenario}/{current}")
        checks.append({"trial_id":current,"golden_sha256":golden[current],"stage12_sha256":trial_hash,"exact_match":trial_hash==golden[current],"daily_rows":nday,"first_date":first_day.isoformat(),"last_date":last_day.isoformat()})
    for batch in pf.iter_batches(batch_size=65536,columns=["scenario_id","trial_id","date","source_sha","master_seed","result_sha256"]):
        for row in batch.to_pylist():
            total_rows+=1
            if row["scenario_id"]!=scenario or row["source_sha"]!=SOURCE_SHA or int(row["master_seed"])!=MASTER_SEED: raise RuntimeError(f"STAGE12_ROW_IDENTITY_MISMATCH {scenario}/{row['trial_id']}")
            tid=int(row["trial_id"]); h=valid_sha(row["result_sha256"],f"{scenario}/{tid}"); day=date.fromisoformat(row["date"])
            if current is None or tid!=current:
                if current is not None: close_trial()
                expected_tid=len(checks)+1
                if tid!=expected_tid: raise RuntimeError(f"STAGE12_TRIAL_ID_SEQUENCE_MISMATCH {scenario} expected={expected_tid} actual={tid}")
                current=tid; first_day=day; last_day=day; nday=1; trial_hash=h
            else:
                if last_day is None or day!=last_day+timedelta(days=1): raise RuntimeError(f"STAGE12_DAILY_DATE_GAP_OR_DUPLICATE {scenario}/{tid}/{day}")
                if h!=trial_hash: raise RuntimeError(f"STAGE12_RESULT_SHA_DRIFT_WITHIN_TRIAL {scenario}/{tid}")
                last_day=day; nday+=1
    close_trial()
    if len(checks)!=expected_count or [c["trial_id"] for c in checks]!=list(range(1,expected_count+1)): raise RuntimeError(f"STAGE12_TRIAL_COVERAGE_MISMATCH {scenario} count={len(checks)} expected={expected_count}")
    if total_rows!=int(rs.get("daily_rows",-1)) or total_rows!=int(cs.get("daily_rows",-1)): raise RuntimeError(f"STAGE12_DAILY_ROW_COUNT_MISMATCH {scenario} actual={total_rows} roll={rs.get('daily_rows')} closure={cs.get('daily_rows')}")
    return checks,{"file_sha256_actual":actual_file_sha,"file_sha256_cp12b_report":expected_file_sha,"file_sha256_cp12c_report":cs.get("content_sha256"),"stage12_source_run_id":STAGE12_RUN,"trial_count":expected_count,"daily_rows":total_rows,"schema_identity":daily_identity(scenario),"schema_identity_sha256":sha_bytes(identity_raw),"exact_comparison_count":len(checks),"mismatch_count":sum(not x["exact_match"] for x in checks),"row_source_seed_valid":True,"dates_contiguous":True,"result_sha_constant_within_trial":True}

def run_scenario(scenario:str,outroot:Path)->dict:
    report={"scenario":scenario,"status":"FAIL","source_sha":SOURCE_SHA,"master_seed":MASTER_SEED,"simulation_or_trial_executed":False,"historical_dataset_modified":False,"historical_artifacts_modified":False,"stage10_metadata_parse_events":[],"source_blocks":[],"trial_comparisons":[],"fatal_error":None}
    try:
        manifest=json.loads(Path("docs/stage9a/dataset_manifest.json").read_text(encoding="utf-8"))
        identity=json.loads(Path("docs/stage11/dataset_identity.json").read_text(encoding="utf-8"))
        roll=json.loads(Path("docs/stage12/roll_forward_validation.json").read_text(encoding="utf-8"))
        closure=json.loads(Path("docs/stage12/closure_settlement_validation.json").read_text(encoding="utf-8"))
        if manifest.get("global_manifest_sha256")!=MANIFEST_GLOBAL or manifest.get("source_sha")!=SOURCE_SHA or str(manifest.get("run_id"))!=str(STAGE7_RUN): raise RuntimeError("STAGE9A_MANIFEST_IDENTITY_MISMATCH")
        if int(identity.get("total_canonical_trials",-1))!=11005 or int(identity.get("scenarios_count",-1))!=25: raise RuntimeError("STAGE11_IDENTITY_COVERAGE_MISMATCH")
        if identity.get("sources",{}).get("stage7",{}).get("run_head_sha")!=STAGE7_HEAD: raise RuntimeError("STAGE11_STAGE7_RUN_HEAD_MISMATCH")
        stage10_recorded_head=identity.get("sources",{}).get("stage10",{}).get("branch_head_sha")
        if not isinstance(stage10_recorded_head,str): raise RuntimeError("STAGE11_STAGE10_RECORDED_HEAD_MISSING")
        if str(identity.get("sources",{}).get("stage10",{}).get("run_id"))!=str(STAGE10_RUN): raise RuntimeError("STAGE11_STAGE10_RUN_ID_MISMATCH")
        if roll.get("source_sha")!=SOURCE_SHA or str(roll.get("source_run_id"))!=str(STAGE12_RUN) or roll.get("expected_global_sha256_from_cp12b")!=STAGE12_GLOBAL: raise RuntimeError("STAGE12_ROLLFORWARD_IDENTITY_MISMATCH")
        if closure.get("source_sha")!=SOURCE_SHA or str(closure.get("cp12b_run_id"))!=str(STAGE12_RUN) or closure.get("expected_global_sha256")!=STAGE12_GLOBAL: raise RuntimeError("STAGE12_CLOSURE_IDENTITY_MISMATCH")
        run7=gh_json(f"repos/{REPO}/actions/runs/{STAGE7_RUN}"); run12=gh_json(f"repos/{REPO}/actions/runs/{STAGE12_RUN}")
        run10=gh_json(f"repos/{REPO}/actions/runs/{STAGE10_RUN}")
        for data,expected,head in ((run7,STAGE7_RUN,STAGE7_HEAD),(run10,STAGE10_RUN,STAGE10_HEAD),(run12,STAGE12_RUN,STAGE12_HEAD)):
            if int(data.get("id",-1))!=expected or data.get("head_sha")!=head: raise RuntimeError(f"LIVE_RUN_IDENTITY_MISMATCH {expected}")
        if run7.get("conclusion")!="success" or run12.get("conclusion")!="success": raise RuntimeError("STAGE7_OR_STAGE12_RUN_NOT_SUCCESS")
        report["run_provenance"]={"stage7":{"id":STAGE7_RUN,"head_sha":STAGE7_HEAD,"conclusion":run7.get("conclusion")},"stage10":{"id":STAGE10_RUN,"head_sha":STAGE10_HEAD,"conclusion":run10.get("conclusion")},"stage12":{"id":STAGE12_RUN,"head_sha":STAGE12_HEAD,"conclusion":run12.get("conclusion")}}
        report["stage10_identity_metadata_deviation"]={"classification":"K_CODE","recorded_branch_head_sha":stage10_recorded_head,"recorded_value_length":len(stage10_recorded_head),"live_run_api_head_sha":STAGE10_HEAD,"live_value_length":len(STAGE10_HEAD),"matches_live_run":stage10_recorded_head==STAGE10_HEAD,"handling":"Preserved the immutable Stage 11 identity document; uses live GitHub Run 37709936740 identity and independently verifies source_sha and every trial hash."}
        report["stage12_global_identity"]={"cp12b_expected_global_sha256":roll.get("expected_global_sha256_from_cp12b"),"cp12c_expected_global_sha256":closure.get("expected_global_sha256"),"both_match_known_identity":roll.get("expected_global_sha256_from_cp12b")==STAGE12_GLOBAL and closure.get("expected_global_sha256")==STAGE12_GLOBAL}
        report["stage10_run_aggregate_conclusion_is_not_claimed_pass"]=run10.get("conclusion")!="success"

        arts7,_=artifact_index(STAGE7_RUN); name7=f"stage7-blocks-{scenario}-1"; art7=find_artifact(arts7,name7,STAGE7_RUN)
        official_id=int(manifest.get("artifact_manifest",{}).get("official_block_artifacts",{}).get(scenario,-1))
        if official_id!=int(art7.get("id",-2)): raise RuntimeError(f"STAGE7_MANIFEST_ARTIFACT_ID_MISMATCH {scenario}")
        with tempfile.TemporaryDirectory(prefix=f"gatea_{scenario}_") as td:
            root=Path(td); zip7=root/"stage7.zip"; art7ev=download_artifact(art7,zip7)
            with zipfile.ZipFile(zip7) as z7:
                if scenario.startswith("C100_"):
                    meta=member(z7,"block_1_1_metadata.json"); parquet=member(z7,"block_1_1.parquet")
                    g,ev=validate_block(scenario,1,1,meta,parquet,manifest,STAGE7_RUN)
                    stage7_raw={"block_1_1":(meta,parquet)}
                    block_ev=[ev]
                else:
                    g={}; stage7_raw={}; block_ev=[]
                    for start,end in BASE_BLOCKS:
                        stem=f"block_{start}_{end}"; meta=member(z7,stem+"_metadata.json"); parquet=member(z7,stem+".parquet")
                        b,ev=validate_block(scenario,start,end,meta,parquet,manifest,STAGE7_RUN)
                        if set(g)&set(b): raise RuntimeError(f"STAGE7_DUPLICATE_TRIAL_IDS {scenario}")
                        g.update(b); stage7_raw[stem]=(meta,parquet); block_ev.append(ev)
                    if sorted(g)!=list(range(1,451)): raise RuntimeError(f"STAGE7_TRIAL_COVERAGE_MISMATCH {scenario}")
            report["stage7_artifact"]={"name":name7,**art7ev}
            report["source_blocks"].extend(block_ev)
            golden=dict(g)

            if not scenario.startswith("C100_"):
                arts10,_=artifact_index(STAGE10_RUN); name10=f"stage10-bench-{scenario}-1"; art10=find_artifact(arts10,name10,STAGE10_RUN)
                jobs=gh_json(f"repos/{REPO}/actions/runs/{STAGE10_RUN}/jobs?per_page=100")
                joblist=jobs.get("jobs",[])
                if int(jobs.get("total_count",-1))!=len(joblist): raise RuntimeError("STAGE10_JOB_LIST_INCOMPLETE")
                matching=[j for j in joblist if j.get("name")==f"bench-{scenario}-1"]
                if len(matching)!=1 or matching[0].get("conclusion")!="success": raise RuntimeError(f"STAGE10_SCENARIO_JOB_NOT_SUCCESS {scenario} jobs={[(j.get('name'),j.get('conclusion')) for j in matching]}")
                zip10=root/"stage10.zip"; art10ev=download_artifact(art10,zip10)
                with zipfile.ZipFile(zip10) as z10:
                    for start,end in BASE_BLOCKS:
                        stem=f"block_{start}_{end}"
                        if member(z10,stem+"_metadata.json")!=stage7_raw[stem][0] or member(z10,stem+".parquet")!=stage7_raw[stem][1]:
                            raise RuntimeError(f"STAGE10_BASE_1_450_NOT_BYTE_IDENTICAL_TO_STAGE7 {scenario}/{stem}")
                    meta_raw=member(z10,"block_451_550_metadata.json")
                    meta,mode=parse_json_bytes(meta_raw,allow_known_stage10_suffix=True)
                    if mode!="known_stage10_literal_backslash_n_suffix_removed_in_memory": raise RuntimeError(f"STAGE10_KNOWN_SUFFIX_PATTERN_CHANGED {scenario}/block_451_550_metadata.json")
                    report["stage10_metadata_parse_events"].append({"file":"block_451_550_metadata.json","raw_sha256":sha_bytes(meta_raw),"parse_mode":mode,"writer_blob":"d54602982b6422939955ca841a251ecd250b4139"})
                    new_parquet_raw=member(z10,"block_451_550.parquet")
                    b,ev=validate_block(scenario,451,550,meta_raw,new_parquet_raw,manifest,STAGE10_RUN,allow_bad_suffix=True)
                    stage9a_fp=manifest.get("scenarios",{}).get(scenario,{}).get("scenario_fingerprint")
                    combined=identity.get("per_scenario",{}).get(scenario,{}).get("combined_dataset_fingerprint_sha256_stage10")
                    if meta.get("baseline_fingerprint_sha256")!=stage9a_fp or meta.get("combined_fingerprint_sha256")!=combined:
                        raise RuntimeError(f"STAGE10_BASELINE_OR_COMBINED_FINGERPRINT_MISMATCH {scenario}")
                    raw_metrics=member(z10,"metrics.json"); metrics,metrics_mode=parse_json_bytes(raw_metrics,allow_known_stage10_suffix=True)
                    raw_resume=member(z10,"resume_descriptor.json"); resume,resume_mode=parse_json_bytes(raw_resume,allow_known_stage10_suffix=True)
                    for fn,raw,mode2 in (("metrics.json",raw_metrics,metrics_mode),("resume_descriptor.json",raw_resume,resume_mode)):
                        if mode2!="known_stage10_literal_backslash_n_suffix_removed_in_memory": raise RuntimeError(f"STAGE10_KNOWN_SUFFIX_PATTERN_CHANGED {scenario}/{fn}")
                        report["stage10_metadata_parse_events"].append({"file":fn,"raw_sha256":sha_bytes(raw),"parse_mode":mode2,"writer_blob":"d54602982b6422939955ca841a251ecd250b4139"})
                    metrics_ok=(metrics.get("scenario")==scenario and metrics.get("mode")=="canonical" and metrics.get("source_sha")==SOURCE_SHA and int(metrics.get("master_seed",-1))==MASTER_SEED and str(metrics.get("expected_source_run_id"))==str(STAGE7_RUN) and str(metrics.get("benchmark_run_id"))==str(STAGE10_RUN) and metrics.get("canonical_trial_range")==[451,550] and int(metrics.get("canonical_trials_added",-1))==100 and int(metrics.get("executions_completed",-1))==100 and int(metrics.get("executions_failed",-1))==0 and metrics.get("errors")==[] and metrics.get("final_dataset_fingerprint_sha256")==combined)
                    resume_ok=(resume.get("schema_version")=="stage10-resume-v1" and resume.get("scenario")==scenario and resume.get("source_sha")==SOURCE_SHA and int(resume.get("master_seed",-1))==MASTER_SEED and int(resume.get("baseline_trials",-1))==450 and int(resume.get("canonical_trials_added",-1))==100 and resume.get("new_trial_range")==[451,550] and resume.get("baseline_fingerprint_sha256")==stage9a_fp and resume.get("combined_dataset_fingerprint_sha256")==combined and int(resume.get("next_trial_id",-1))==551)
                    if not metrics_ok or not resume_ok: raise RuntimeError(f"STAGE10_METRICS_OR_RESUME_IDENTITY_INVALID {scenario} metrics={metrics_ok} resume={resume_ok}")
                    # Recompute the Stage 10 combined 1..550 fingerprint from the unchanged source row data.
                    baseline_rows=[]
                    for bstart,bend in BASE_BLOCKS:
                        baseline_rows.extend(pq.read_table(BytesIO(stage7_raw[f"block_{bstart}_{bend}"][1])).to_pylist())
                    appended_rows=pq.read_table(BytesIO(new_parquet_raw)).to_pylist()
                    recomputed_combined=canonical_fingerprint(baseline_rows+appended_rows)
                    if recomputed_combined!=combined: raise RuntimeError(f"STAGE10_COMBINED_FINGERPRINT_RECOMPUTE_MISMATCH {scenario} expected={combined} actual={recomputed_combined}")
                    ev["combined_fingerprint_recomputed_from_parquet"]=recomputed_combined
                if sorted(set(g)&set(b)): raise RuntimeError(f"GOLDEN_TRIAL_ID_OVERLAP {scenario}")
                g.update(b)
                report["stage10_artifact"]={"name":name10,**art10ev,"scenario_job_conclusion":matching[0].get("conclusion"),"stage10_run_conclusion":run10.get("conclusion"),"base_1_450_byte_identical_to_stage7":True,"new_block_rows_rehashed":100,"metrics_identity_pass":True,"resume_descriptor_identity_pass":True}
                report["source_blocks"].append(ev)
            expected_ids=[1] if scenario.startswith("C100_") else list(range(1,551))
            if sorted(g)!=expected_ids: raise RuntimeError(f"FINAL_SOURCE_GOLDEN_MAP_COVERAGE_MISMATCH {scenario}")
            report["source_golden_trial_count"]=len(g)

            arts12,_=artifact_index(STAGE12_RUN); name12=f"stage12-daily-{scenario}"; art12=find_artifact(arts12,name12,STAGE12_RUN)
            zip12=root/"stage12.zip"; art12ev=download_artifact(art12,zip12)
            extract=root/"stage12"; extract.mkdir()
            with zipfile.ZipFile(zip12) as z12:
                parquet_names=[n for n in z12.namelist() if n.endswith(".parquet")]
                if parquet_names!=[f"{scenario}.parquet"]: raise RuntimeError(f"STAGE12_ARCHIVE_PARQUET_MEMBERS_INVALID {scenario} {parquet_names}")
                if any(n.startswith("/") or ".." in Path(n).parts for n in parquet_names): raise RuntimeError(f"STAGE12_ARCHIVE_PATH_INVALID {scenario}")
                z12.extract(parquet_names[0],extract)
            roll=json.loads(Path("docs/stage12/roll_forward_validation.json").read_text(encoding="utf-8"))
            closure=json.loads(Path("docs/stage12/closure_settlement_validation.json").read_text(encoding="utf-8"))
            trial_checks,st12=validate_stage12(scenario,extract/f"{scenario}.parquet",roll,closure,g)
            report["stage12_artifact"]={"name":name12,**art12ev}
            report["stage12"]=st12
            report["trial_comparisons"]=[{**v,"golden_origin":("stage7_trial_1" if scenario.startswith("C100_") else ("stage7_trials_1_450" if v["trial_id"]<=450 else "stage10_trials_451_550"))} for v in trial_checks]
            gates={
                "source_rows_rehashed_and_metadata_matches":sum(x["trial_hashes_recomputed_from_parquet"] for x in report["source_blocks"])==len(expected_ids),
                "stage12_file_hash_matches_cp12b_and_cp12c_reports":st12["file_sha256_actual"]==st12["file_sha256_cp12b_report"]==st12["file_sha256_cp12c_report"],
                "stage12_identity_schema_and_daily_sequence_valid":st12["unique_trial_keys"]==len(expected_ids) and st12["row_source_seed_valid"] and st12["dates_contiguous"] and st12["result_sha_constant_within_trial"],
                "all_trial_hashes_exact":len(trial_checks)==len(expected_ids) and st12["mismatch_count"]==0,
                "trial_id_coverage_complete":[x["trial_id"] for x in trial_checks]==expected_ids
            }
            if not scenario.startswith("C100_"):
                gates["stage10_copied_blocks_1_450_byte_identical_to_stage7"]=report["stage10_artifact"]["base_1_450_byte_identical_to_stage7"]
                gates["stage10_new_block_rehashed_and_run_job_success"]=report["stage10_artifact"]["new_block_rows_rehashed"]==100 and report["stage10_artifact"]["scenario_job_conclusion"]=="success"
            report["gates"]=gates
            report["status"]="PASS" if all(gates.values()) else "FAIL"
            report["daily_row_count"]=st12["daily_rows"]
            report["exact_trial_comparisons"]=len(trial_checks)
            report["hash_mismatch_count"]=st12["mismatch_count"]
    except Exception as exc:
        report["status"]="FAIL"; report["fatal_error"]=str(exc); report["traceback"]=traceback.format_exc()[-6500:]
        report.setdefault("gates",{})
    outroot.mkdir(parents=True,exist_ok=True)
    outpath=outroot/f"{scenario}.json"
    outpath.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"scenario":scenario,"status":report.get("status"),"trials":report.get("source_golden_trial_count",0),"daily_rows":report.get("daily_row_count",0),"comparisons":report.get("exact_trial_comparisons",0),"mismatches":report.get("hash_mismatch_count",0),"fatal_error":report.get("fatal_error"),"report":str(outpath)},ensure_ascii=False,sort_keys=True))
    return report

def main():
    p=argparse.ArgumentParser(); p.add_argument("--scenario",required=True,choices=SCENARIOS); p.add_argument("--output-root",default="gatea_evidence/scenarios"); a=p.parse_args()
    result=run_scenario(a.scenario,Path(a.output_root))
    if result.get("status")!="PASS": raise SystemExit(1)
if __name__=="__main__": main()
