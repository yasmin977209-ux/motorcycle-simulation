"""Independent read-back audit for S6 scenario artifacts; never simulates."""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from typing import Any
import pyarrow.parquet as pq
import constants
from scripts.s6_daily_path_identity import DAILY_BALANCE_INTEGER_FIELDS,MODEL_SCHEMA_VERSION,build_daily_path_identity_evidence,require_daily_path_manifest_contract
def _filehash(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def audit_scenario_artifacts(folder:Path)->dict[str,Any]:
    mp=folder/"scenario_manifest.json"
    if not mp.is_file():raise RuntimeError("S6_DAILY_AUDIT_MANIFEST_MISSING")
    m=json.loads(mp.read_text(encoding="utf-8"));n=m.get("trial_count")
    if type(n)is not int:raise RuntimeError("S6_DAILY_AUDIT_TRIAL_COUNT_INVALID")
    src,cohort,sc=str(m.get("source_sha","")),str(m.get("cohort_id","")),str(m.get("scenario_id",""))
    require_daily_path_manifest_contract(m,expected_source_sha=src,expected_cohort_id=cohort,expected_scenario_id=sc,expected_master_seed=constants.MASTER_SEED,expected_trial_count=n,model_schema_version=MODEL_SCHEMA_VERSION)
    names=("trials_summary.parquet","daily_snapshots.parquet","daily_distribution.parquet","opt1_provenance.json");fs=m.get("files")
    if not isinstance(fs,dict):raise RuntimeError("S6_DAILY_AUDIT_FILE_MANIFEST_MISSING")
    for name in names:
        e,p=fs.get(name),folder/name
        if not isinstance(e,dict) or not p.is_file():raise RuntimeError(f"S6_DAILY_AUDIT_ARTIFACT_MISSING:{name}")
        if p.stat().st_size!=e.get("size_bytes") or _filehash(p)!=e.get("sha256"):raise RuntimeError(f"S6_DAILY_AUDIT_ARTIFACT_HASH_MISMATCH:{name}")
    trials=pq.read_table(folder/"trials_summary.parquet").to_pylist()
    if len(trials)!=n:raise RuntimeError("S6_DAILY_AUDIT_TRIAL_ROW_COUNT_MISMATCH")
    for r in trials:
        if type(r.get("trial_id"))is not int or r.get("scenario_id")!=sc or r.get("source_sha")!=src or r.get("cohort_id")!=cohort or r.get("schema_version")!=MODEL_SCHEMA_VERSION:raise RuntimeError("S6_DAILY_AUDIT_TRIAL_ROW_IDENTITY_MISMATCH")
    if sorted(r["trial_id"] for r in trials)!=list(range(1,n+1)):raise RuntimeError("S6_DAILY_AUDIT_TRIAL_ID_COVERAGE_MISMATCH")
    daily=pq.read_table(folder/"daily_snapshots.parquet").to_pylist()
    ev=build_daily_path_identity_evidence(daily,source_sha=src,cohort_id=cohort,master_seed=constants.MASTER_SEED,scenario_id=sc,expected_trial_ids=range(1,n+1),expected_start_date=constants.PROJECT_START_DATE.isoformat(),model_schema_version=MODEL_SCHEMA_VERSION)
    s=ev["summary"]
    if s!=m.get("daily_path_identity_contract"):raise RuntimeError("S6_DAILY_AUDIT_PATH_IDENTITY_MANIFEST_MISMATCH")
    b=m.get("daily_balance_contract",{})
    if b.get("rows_checked")!=s["balance_rows_checked"] or b.get("balance_mismatch_count")!=0 or b.get("required_integer_fields")!=list(DAILY_BALANCE_INTEGER_FIELDS):raise RuntimeError("S6_DAILY_AUDIT_BALANCE_CONTRACT_MISMATCH")
    return {"schema_version":"s6-daily-balance-path-audit-v1","status":"PASS_SCOPED_DAILY_BALANCE_AND_PATH_IDENTITY","scenario_id":sc,"source_sha":src,"cohort_id":cohort,"master_seed":constants.MASTER_SEED,"model_schema_version":MODEL_SCHEMA_VERSION,"daily_balance_schema_version":s["daily_balance_schema_version"],"daily_path_identity_schema_version":s["contract_schema_version"],"trial_count":n,"trial_rows_checked":len(trials),"daily_rows_checked":s["row_count"],"daily_balance_mismatch_count":0,"unique_daily_path_count":s["unique_daily_path_count"],"daily_path_content_map_sha256":s["daily_path_content_map_sha256"],"identity_bound_daily_path_map_sha256":s["identity_bound_daily_path_map_sha256"],"scenario_manifest_sha256":_filehash(mp),"files_verified":list(names),"simulation_trials_run":False}
def main()->None:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--scenario-dir",required=True,type=Path);a=p.parse_args()
    print(json.dumps(audit_scenario_artifacts(a.scenario_dir),ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
