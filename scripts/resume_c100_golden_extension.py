#!/usr/bin/env python3
"""Verify the cancelled C100 artifact and generate only its 947 missing keys."""
from __future__ import annotations
import argparse, hashlib, json, os, re, sys, zipfile
from collections import Counter
from io import BytesIO
from pathlib import Path

from scripts.generate_c100_golden_extension import (
    SOURCE_SHA, SOURCE_COMMIT, MASTER_SEED, EXTENSION_SCHEMA_VERSION,
    SCENARIOS, MODEL_FILES, canonical_result_sha256, ordered_extension_map_sha256,
    verify_source_closure, build_record,
)
from scripts.golden_reference_provider import _load_approved_reference, _ordered_map_sha256

PRIOR_RUN_ID = 38991347472
PRIOR_RUN_ATTEMPT = 1
PRIOR_HEAD = "7e0ff045eb909a121f1f8604f927642f2fad26e8"
PRIOR_BRANCH = "tmp/cp-gatea-c100-golden-20261017"
PRIOR_ARTIFACT_ID = 12087982889
PRIOR_ARCHIVE_BYTES = 93999
PRIOR_ARCHIVE_SHA256 = "d6b867529a8998f2230055c637209c67a4e0165b4f1ab68b62aa4cb8b223bfd6"
PRIOR_MEMBER = "c100_golden_extension.progress.jsonl"
PRIOR_MEMBER_BYTES = 1815129
PRIOR_MEMBER_SHA256 = "fa222cdf3249df19837b6cfec8dad732365df1dc43f4793e2bd9397c3451f3aa"
PRIOR_COUNTS = {"C100_G000":599,"C100_G030":599,"C100_G050":599,"C100_G070":251,"C100_G100":0}
BASE_MAP_COUNT = 25205
BASE_MAP_SHA256 = "0fbe3aa87a253f9527953c77b0a122871c9344f75ece6c8a49da99b2a85c1ce1"
FINAL_MAP_COUNT = 28200
SHA_RE = re.compile(r"^[0-9a-f]{64}$")
GIT_RE = re.compile(r"^[0-9a-f]{40}$")

def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def expected_keys():
    return {(s,n) for s in SCENARIOS for n in range(2,601)}

def expected_extension_keys():
    """Compatibility API for the approved exact five-scenario C100 extension scope."""
    return expected_keys()

def expected_prior_keys():
    out=set()
    for scenario,count in PRIOR_COUNTS.items():
        out.update((scenario,n) for n in range(2,2+count))
    return out

def validate_prior_coverage(keys, counts):
    """Validate the exact prior prefix, including scenarios whose approved count is zero."""
    normalized_counts={scenario: counts.get(scenario,0) for scenario in SCENARIOS}
    if set(keys)!=expected_prior_keys() or normalized_counts!=PRIOR_COUNTS:
        raise RuntimeError("PRIOR_PROGRESS_COVERAGE_OR_SCENARIO_COUNTS_MISMATCH")
    return normalized_counts

def missing_keys(existing):
    existing=set(existing)
    if existing != expected_prior_keys():
        raise RuntimeError("PRIOR_PARTIAL_COVERAGE_MISMATCH")
    expected={("C100_G070",n) for n in range(253,601)} | {("C100_G100",n) for n in range(2,601)}
    missing=sorted(expected_keys()-existing)
    if set(missing)!=expected or len(missing)!=947:
        raise RuntimeError("CONTINUATION_MISSING_SET_MISMATCH")
    return missing

def validate_record(row, run_id=None, run_attempt=None):
    if not isinstance(row,dict): raise RuntimeError("TRIAL_RECORD_NOT_OBJECT")
    s,n=row.get("scenario_id"),row.get("trial_id")
    if s not in SCENARIOS or isinstance(n,bool) or not isinstance(n,int) or not 2<=n<=600:
        raise RuntimeError(f"UNAUTHORIZED_C100_KEY:{s}:{n}")
    result=row.get("trial_result")
    if not isinstance(result,dict) or result.get("scenario_id")!=s or result.get("trial_id")!=n:
        raise RuntimeError(f"TRIAL_RESULT_IDENTITY_MISMATCH:{s}:{n}")
    if (row.get("source_sha")!=SOURCE_SHA or row.get("source_commit")!=SOURCE_COMMIT
        or row.get("master_seed")!=MASTER_SEED or row.get("schema_version")!=EXTENSION_SCHEMA_VERSION
        or row.get("origin")!="pinned_source_reference"):
        raise RuntimeError(f"TRIAL_SOURCE_IDENTITY_MISMATCH:{s}:{n}")
    if isinstance(row.get("run_id"),bool) or not isinstance(row.get("run_id"),int) or row["run_id"]<1:
        raise RuntimeError(f"TRIAL_RUN_ID_INVALID:{s}:{n}")
    if isinstance(row.get("run_attempt"),bool) or not isinstance(row.get("run_attempt"),int) or row["run_attempt"]<1:
        raise RuntimeError(f"TRIAL_RUN_ATTEMPT_INVALID:{s}:{n}")
    if run_id is not None and row["run_id"]!=run_id: raise RuntimeError(f"TRIAL_RUN_ID_MISMATCH:{s}:{n}")
    if run_attempt is not None and row["run_attempt"]!=run_attempt: raise RuntimeError(f"TRIAL_RUN_ATTEMPT_MISMATCH:{s}:{n}")
    digest=row.get("result_sha256")
    if not isinstance(digest,str) or not SHA_RE.fullmatch(digest) or canonical_result_sha256(result)!=digest:
        raise RuntimeError(f"TRIAL_RESULT_SHA256_MISMATCH:{s}:{n}")
    return s,n,digest

def validate_records(rows, allowed_runs):
    indexed={}
    for row in rows:
        s,n,digest=validate_record(row)
        if row["run_id"] not in allowed_runs: raise RuntimeError(f"TRIAL_RUN_NOT_ALLOWED:{s}:{n}")
        if (s,n) in indexed: raise RuntimeError(f"DUPLICATE_TRIAL_ID:{s}:{n}")
        indexed[(s,n)]=digest
    return indexed

def read_prior_archive(path):
    raw=path.read_bytes()
    if len(raw)!=PRIOR_ARCHIVE_BYTES or sha256(raw)!=PRIOR_ARCHIVE_SHA256:
        raise RuntimeError("PRIOR_ARCHIVE_SIZE_OR_SHA256_MISMATCH")
    if not zipfile.is_zipfile(BytesIO(raw)): raise RuntimeError("PRIOR_ARTIFACT_NOT_ZIP")
    with zipfile.ZipFile(BytesIO(raw)) as z:
        if z.namelist()!=[PRIOR_MEMBER]: raise RuntimeError("PRIOR_ARTIFACT_MEMBER_MISMATCH")
        member=z.read(PRIOR_MEMBER)
    if len(member)!=PRIOR_MEMBER_BYTES or sha256(member)!=PRIOR_MEMBER_SHA256:
        raise RuntimeError("PRIOR_MEMBER_SIZE_OR_SHA256_MISMATCH")
    lines=member.splitlines()
    if len(lines)!=2048: raise RuntimeError("PRIOR_LINE_COUNT_MISMATCH")
    rows=[]; keys=set(); counts=Counter()
    for i,line in enumerate(lines,1):
        try: row=json.loads(line.decode("utf-8"))
        except Exception as e: raise RuntimeError(f"PRIOR_JSONL_INVALID_LINE:{i}") from e
        s,n,_=validate_record(row,PRIOR_RUN_ID,PRIOR_RUN_ATTEMPT)
        if (s,n) in keys: raise RuntimeError(f"PRIOR_DUPLICATE_KEY:{s}:{n}")
        keys.add((s,n)); counts[s]+=1; rows.append(row)
    validate_prior_coverage(keys,counts)
    audit={"run_id":PRIOR_RUN_ID,"run_attempt":PRIOR_RUN_ATTEMPT,"branch":PRIOR_BRANCH,
           "workflow_head_sha":PRIOR_HEAD,"artifact_id":PRIOR_ARTIFACT_ID,
           "archive_bytes":len(raw),"archive_sha256":sha256(raw),"member":PRIOR_MEMBER,
           "member_bytes":len(member),"member_sha256":sha256(member),
           "record_count":len(rows),"scenario_counts":PRIOR_COUNTS,
           "record_hash_mismatches":0,"duplicate_keys":0}
    return rows,audit

def reconstruct_base():
    p=_load_approved_reference()
    fp=p.get("fingerprints")
    if not isinstance(fp,dict): raise RuntimeError("BASE_FINGERPRINTS_MISSING")
    n=sum(len(v) for v in fp.values()); digest=_ordered_map_sha256(fp)
    if not (p.get("source_sha")==SOURCE_SHA and p.get("source_commit")==SOURCE_COMMIT
            and p.get("master_seed")==MASTER_SEED and p.get("trial_count")==BASE_MAP_COUNT==n
            and p.get("scenario_count")==25 and p.get("source_map_sha256")==BASE_MAP_SHA256
            and digest==BASE_MAP_SHA256
            and p.get("golden_reference_id")==f"D-2026-10-14-01:GateA:{BASE_MAP_COUNT}:{BASE_MAP_SHA256}"):
        raise RuntimeError("APPROVED_BASE_MAP_IDENTITY_FAIL")
    for s in SCENARIOS:
        if sorted(fp.get(s,{}))!=[1]: raise RuntimeError(f"BASE_C100_COVERAGE_FAIL:{s}")
    return p,{"status":"PASS_BASE_MAP_RECONSTRUCTED","trial_count":n,"scenario_count":25,
              "ordered_map_sha256":digest,"golden_reference_id":p["golden_reference_id"],
              "source_sha":SOURCE_SHA,"source_commit":SOURCE_COMMIT,"master_seed":MASTER_SEED}

def check_model_imports(source_root):
    proof=verify_source_closure(source_root)
    if proof.get("model_file_count")!=14 or proof.get("all_model_file_blobs_equal") is not True:
        raise RuntimeError("PINNED_MODEL_CLOSURE_NOT_PROVEN")
    sys.path.insert(0,str(source_root))
    import constants, monte_carlo, rng
    if constants.MASTER_SEED!=MASTER_SEED: raise RuntimeError("PINNED_SEED_MISMATCH")
    if Path(monte_carlo.__file__).resolve().parent!=source_root or Path(rng.__file__).resolve().parent!=source_root:
        raise RuntimeError("MODEL_OR_RNG_IMPORT_NOT_PINNED")
    rates={"C100_G000":0,"C100_G030":30,"C100_G050":50,"C100_G070":70,"C100_G100":100}
    if set(x for x in constants.SCENARIO_IDS if x in SCENARIOS)!=set(SCENARIOS):
        raise RuntimeError("C100_SCENARIO_SET_MISMATCH")
    for s,g in rates.items():
        probability,recovery=monte_carlo.parse_scenario_id(s)
        if probability!=1.0 or recovery!=g: raise RuntimeError(f"SCENARIO_PARAMETERS_MISMATCH:{s}")
    return proof,monte_carlo

def _write_run_status(output_path, updates):
    status_path=Path(output_path).parent/"continuation_status.json"
    status_path.parent.mkdir(parents=True,exist_ok=True)
    try:
        current=json.loads(status_path.read_text(encoding="utf-8")) if status_path.is_file() else {}
    except Exception:
        current={}
    current.update(updates)
    status_path.write_text(json.dumps(current,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return status_path

def run(args):
    output,progress,audit_path=map(Path,(args.output,args.progress,args.base_audit))
    output.parent.mkdir(parents=True,exist_ok=True)
    progress.parent.mkdir(parents=True,exist_ok=True)
    audit_path.parent.mkdir(parents=True,exist_ok=True)
    run_context={
        "workflow_run_id":int(os.environ.get("GITHUB_RUN_ID","0") or 0),
        "workflow_run_attempt":int(os.environ.get("GITHUB_RUN_ATTEMPT","0") or 0),
        "workflow_head_sha":os.environ.get("GITHUB_SHA",""),
        "branch":os.environ.get("GITHUB_REF_NAME",""),
        "source_sha":SOURCE_SHA,"source_commit":SOURCE_COMMIT,"master_seed":MASTER_SEED,
    }
    _write_run_status(output,{"schema_version":"c100-resume-execution-status-v1",
        "status":"RUNNING","phase":"PRECHECK","generation_started":False,**run_context})
    if os.environ.get("SOURCE_SHA")!=SOURCE_SHA or os.environ.get("MASTER_SEED")!=str(MASTER_SEED):
        raise RuntimeError("SOURCE_SHA_OR_SEED_ENVIRONMENT_MISMATCH")
    rid=int(os.environ.get("GITHUB_RUN_ID","0")); attempt=int(os.environ.get("GITHUB_RUN_ATTEMPT","0"))
    head=os.environ.get("GITHUB_SHA","")
    if rid<1 or attempt!=1 or not GIT_RE.fullmatch(head): raise RuntimeError("CONTINUATION_RUN_PROVENANCE_INVALID")
    if output.exists() or progress.exists(): raise RuntimeError("CONTINUATION_OUTPUT_ALREADY_EXISTS_NO_RERUN")
    prior,prior_audit=read_prior_archive(Path(args.prior_artifact_zip))
    _write_run_status(output,{"phase":"PRIOR_ARTIFACT_VERIFIED","generation_started":False,
        "prior_record_count":len(prior),"prior_archive_sha256":prior_audit["archive_sha256"],
        "prior_member_sha256":prior_audit["member_sha256"]})
    # Reconstruct all pinned prior evidence and require the exact 25,205-row baseline before any generation.
    base,base_audit=reconstruct_base()
    _write_run_status(output,{"phase":"APPROVED_BASE_MAP_VERIFIED","generation_started":False,
        "base_map_count":base_audit["trial_count"],"base_map_sha256":base_audit["ordered_map_sha256"],
        "golden_reference_id":base_audit["golden_reference_id"]})
    proof,engine=check_model_imports(Path(args.source_root).resolve())
    _write_run_status(output,{"phase":"SOURCE_CLOSURE_VERIFIED","generation_started":False,
        "model_file_count":proof.get("model_file_count"),
        "all_model_file_blobs_equal":proof.get("all_model_file_blobs_equal")})
    prior_keys={(r["scenario_id"],r["trial_id"]) for r in prior}
    missing=missing_keys(prior_keys)
    output.parent.mkdir(parents=True,exist_ok=True)
    audit_path.write_text(json.dumps({"prior_artifact":prior_audit,"approved_base_map":base_audit,
       "source_closure":proof,"missing_count":len(missing),"missing_ranges":{"C100_G070":"253..600","C100_G100":"2..600"},
       "generation_started_only_after_preflight":True},ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    new=[]
    _write_run_status(output,{"phase":"GENERATION_STARTED","generation_started":True,
        "planned_new_record_count":len(missing),
        "planned_missing_ranges":{"C100_G070":"253..600","C100_G100":"2..600"}})
    with progress.open("x",encoding="utf-8",newline="\n") as stream:
        for s,n in missing:
            if (s,n) in prior_keys: raise RuntimeError(f"REFUSE_COMPLETED_KEY:{s}:{n}")
            result,_daily=engine.run_single_trial(s,n,master_seed=MASTER_SEED)
            row=build_record(result,scenario_id=s,trial_id=n,run_id=rid,run_attempt=attempt)
            validate_record(row,rid,attempt)
            stream.write(json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(",",":"),default=str)+"\n")
            stream.flush(); new.append(row); prior_keys.add((s,n))
    if len(new)!=947: raise RuntimeError(f"NEW_RECORD_COUNT_MISMATCH:{len(new)}")
    records=sorted(prior+new,key=lambda r:(r["scenario_id"],r["trial_id"]))
    idx=validate_records(records,{PRIOR_RUN_ID,rid})
    if len(records)!=2995 or set(idx)!=expected_keys(): raise RuntimeError("EXTENSION_COVERAGE_FAIL")
    extension_sha=ordered_extension_map_sha256(records)
    combined={s:{int(i):str(h) for i,h in vals.items()} for s,vals in base["fingerprints"].items()}
    for row in records:
        s,n=row["scenario_id"],row["trial_id"]
        if n in combined.get(s,{}): raise RuntimeError(f"BASE_EXTENSION_OVERLAP:{s}:{n}")
        combined[s][n]=row["result_sha256"]
    final_count=sum(map(len,combined.values())); final_sha=_ordered_map_sha256(combined)
    if final_count!=FINAL_MAP_COUNT: raise RuntimeError(f"FINAL_MAP_COUNT_MISMATCH:{final_count}")
    for s in SCENARIOS:
        if sorted(combined[s])!=list(range(1,601)): raise RuntimeError(f"FINAL_C100_COVERAGE_FAIL:{s}")
    counts={s:sum(r["scenario_id"]==s for r in records) for s in SCENARIOS}
    payload={"status":"COMPLETE_PENDING_INDEPENDENT_ARTIFACT_AUDIT","decision_id":"D-2026-10-17-07",
       "base_decision_ids":["D-2026-10-14-01","D-2026-10-15-10"],"schema_version":EXTENSION_SCHEMA_VERSION,
       "source_sha":SOURCE_SHA,"source_commit":SOURCE_COMMIT,"master_seed":MASTER_SEED,"model_source_closure":proof,
       "base_golden_map_count":BASE_MAP_COUNT,"base_golden_map_sha256":BASE_MAP_SHA256,
       "base_golden_reference_id":base["golden_reference_id"],"trial_id_start":2,"trial_id_end":600,
       "trial_count":len(records),"prior_verified_count":len(prior),"newly_generated_count":len(new),
       "scenario_ids":list(SCENARIOS),"scenario_counts":counts,
       "extension_map_sha256":extension_sha,"combined_map_count":final_count,
       "combined_ordered_map_sha256":final_sha,
       "prior_run":{"run_id":PRIOR_RUN_ID,"run_attempt":PRIOR_RUN_ATTEMPT,"workflow_head_sha":PRIOR_HEAD,
          "branch":PRIOR_BRANCH,"artifact_id":PRIOR_ARTIFACT_ID,"archive_sha256":PRIOR_ARCHIVE_SHA256,
          "member_sha256":PRIOR_MEMBER_SHA256},
       "continuation_run":{"run_id":rid,"run_attempt":attempt,"workflow_head_sha":head,
          "branch":os.environ.get("GITHUB_REF_NAME","")},
       "provenance_by_run":[{"run_id":PRIOR_RUN_ID,"run_attempt":1,"record_count":len(prior),"workflow_head_sha":PRIOR_HEAD},
          {"run_id":rid,"run_attempt":attempt,"record_count":len(new),"workflow_head_sha":head,
           "generated_trial_ids":{"C100_G070":"253..600","C100_G100":"2..600"}}],
       "records":records,"historical_dataset_modified":False,"historical_parquet_modified":False,
       "completed_ids_rerun":False,"source_sha_bumped":False,"rng_or_seed_changed":False,
       "production_checkpoint_accepted":False,"overall_gate_a_or_stability_accepted":False}
    output.write_text(json.dumps(payload,ensure_ascii=False,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    saved=json.loads(output.read_text(encoding="utf-8"))
    saved_index=validate_records(saved["records"],{PRIOR_RUN_ID,rid})
    if (len(saved_index)!=2995 or ordered_extension_map_sha256(saved["records"])!=extension_sha
        or saved.get("combined_ordered_map_sha256")!=final_sha or saved.get("combined_map_count")!=FINAL_MAP_COUNT):
        raise RuntimeError("POST_WRITE_AUDIT_FAILED")
    _write_run_status(output,{"status":"COMPLETE_PENDING_INDEPENDENT_ARTIFACT_AUDIT",
        "phase":"COMPLETE_PENDING_INDEPENDENT_ARTIFACT_AUDIT","generation_started":True,
        "prior_records_verified":len(prior),"new_records_generated":len(new),
        "extension_record_count":len(saved["records"]),"extension_map_sha256":extension_sha,
        "combined_map_count":final_count,"combined_ordered_map_sha256":final_sha,
        "output_bytes":output.stat().st_size,"output_sha256":sha256(output.read_bytes()),
        "progress_bytes":progress.stat().st_size,"completed_ids_rerun":False,
        "production_checkpoint_accepted":False})
    print(json.dumps({"status":saved["status"],"prior_records_verified":len(prior),"missing_records_generated":len(new),
      "total_extension_records":len(saved["records"]),"base_map_count":BASE_MAP_COUNT,"base_map_sha256":BASE_MAP_SHA256,
      "combined_map_count":final_count,"combined_ordered_map_sha256":final_sha,"extension_map_sha256":extension_sha,
      "prior_run_id":PRIOR_RUN_ID,"continuation_run_id":rid,"continuation_head_sha":head,
      "output_bytes":output.stat().st_size,"output_sha256":sha256(output.read_bytes()),
      "progress_bytes":progress.stat().st_size,"completed_ids_rerun":False,"production_checkpoint_accepted":False},
      ensure_ascii=False,sort_keys=True))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--prior-artifact-zip",required=True); p.add_argument("--source-root",required=True)
    p.add_argument("--output",default="results_gatea_resume/c100_golden_extension.json")
    p.add_argument("--progress",default="results_gatea_resume/c100_golden_extension.resume.progress.jsonl")
    p.add_argument("--base-audit",default="results_gatea_resume/base_map_audit.json")
    a=p.parse_args()
    try:
        if not (os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")):
            raise RuntimeError("GOLDEN_PROVIDER_TOKEN_MISSING")
        run(a)
        return 0
    except Exception as exc:
        status_path=Path(a.output).parent/"continuation_status.json"
        status_path.parent.mkdir(parents=True,exist_ok=True)
        try:
            status=json.loads(status_path.read_text(encoding="utf-8")) if status_path.is_file() else {}
        except Exception:
            status={}
        status.update({"status":"FAIL","error_type":type(exc).__name__,"error":str(exc),
            "workflow_run_id":int(os.environ.get("GITHUB_RUN_ID","0") or 0),
            "workflow_run_attempt":int(os.environ.get("GITHUB_RUN_ATTEMPT","0") or 0),
            "workflow_head_sha":os.environ.get("GITHUB_SHA",""),
            "branch":os.environ.get("GITHUB_REF_NAME",""),
            "source_sha":SOURCE_SHA,"source_commit":SOURCE_COMMIT,"master_seed":MASTER_SEED})
        status_path.write_text(json.dumps(status,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        raise

if __name__=="__main__": raise SystemExit(main())
