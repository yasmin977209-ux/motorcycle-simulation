"""Independent read-back audit for S6 scenario artifacts; never simulates."""
from __future__ import annotations
import argparse,gzip,hashlib,json
from pathlib import Path
from typing import Any
from datetime import date,timedelta
from entities import EventType
import pyarrow.parquet as pq
import constants
from scripts.s6_daily_path_identity import DAILY_BALANCE_INTEGER_FIELDS,MODEL_SCHEMA_VERSION,build_daily_path_identity_evidence,require_daily_path_manifest_contract
import stats_integrity
def _filehash(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()
def validate_daily_balance_contract_record(manifest:dict[str,Any], summary:dict[str,Any])->None:
    contract=manifest.get("daily_balance_contract")
    if not isinstance(contract,dict):
        raise RuntimeError("S6_DAILY_AUDIT_BALANCE_CONTRACT_MISSING")
    if (
        contract.get("schema_version")!="s6-daily-balance-v1"
        or contract.get("status")!="PASS_SCOPED_POST_WRITE_BALANCE_CHECK"
        or contract.get("source_sha")!=manifest.get("source_sha")
        or contract.get("cohort_id")!=manifest.get("cohort_id")
        or contract.get("master_seed")!=constants.MASTER_SEED
        or contract.get("model_schema_version")!=MODEL_SCHEMA_VERSION
        or contract.get("rows_checked")!=summary.get("balance_rows_checked")
        or contract.get("balance_mismatch_count")!=0
        or contract.get("required_integer_fields")!=list(DAILY_BALANCE_INTEGER_FIELDS)
    ):
        raise RuntimeError("S6_DAILY_AUDIT_BALANCE_CONTRACT_MISMATCH")


def audit_scenario_artifacts(folder:Path)->dict[str,Any]:
    mp=folder/"scenario_manifest.json"
    if not mp.is_file():raise RuntimeError("S6_DAILY_AUDIT_MANIFEST_MISSING")
    m=json.loads(mp.read_text(encoding="utf-8"));n=m.get("trial_count")
    if type(n)is not int:raise RuntimeError("S6_DAILY_AUDIT_TRIAL_COUNT_INVALID")
    src,cohort,sc=str(m.get("source_sha","")),str(m.get("cohort_id","")),str(m.get("scenario_id",""))
    require_daily_path_manifest_contract(m,expected_source_sha=src,expected_cohort_id=cohort,expected_scenario_id=sc,expected_master_seed=constants.MASTER_SEED,expected_trial_count=n,model_schema_version=MODEL_SCHEMA_VERSION)
    names=("trials_summary.parquet","daily_snapshots.parquet","daily_distribution.parquet","opt1_provenance.json");fs=m.get("files")
    if not isinstance(fs,dict) or set(fs)!=set(names):raise RuntimeError("S6_DAILY_AUDIT_FILE_MANIFEST_MISSING_OR_INCOMPLETE")
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
    validate_daily_balance_contract_record(m,s)
    distribution_table=pq.read_table(folder/"daily_distribution.parquet")
    distribution=distribution_table.to_pylist()
    distribution_fields=set(distribution_table.schema.names)
    required_distribution_fields={
        "source_sha","cohort_id","scenario_id","date","mode","quantile_name",
        "active_trial_count","sample_trial_count","metric_name",
        "exact_numerator","exact_denominator","display_value",
    }
    if required_distribution_fields.issubset(distribution_fields):
        stats_integrity.validate_daily_distribution_rows(
            distribution,scenario_id=sc,source_sha=src,cohort_id=cohort,
            expected_dates=sorted({str(row["date"]) for row in daily}),
            expected_trial_count=n,
        )
        distribution_status="PASS_SCOPED_DAILY_DISTRIBUTION_SCHEMA_AND_COVERAGE"
    else:
        # Legacy/sample-only distributions are not promoted to complete coverage.
        distribution_status="MISSING_EVIDENCE_DAILY_DISTRIBUTION_SCHEMA"
    return {"schema_version":"s6-daily-balance-path-audit-v1","status":"PASS_SCOPED_DAILY_BALANCE_AND_PATH_IDENTITY","scenario_id":sc,"source_sha":src,"cohort_id":cohort,"master_seed":constants.MASTER_SEED,"model_schema_version":MODEL_SCHEMA_VERSION,"daily_balance_schema_version":s["daily_balance_schema_version"],"daily_path_identity_schema_version":s["contract_schema_version"],"trial_count":n,"trial_rows_checked":len(trials),"daily_rows_checked":s["row_count"],"daily_balance_mismatch_count":0,"unique_daily_path_count":s["unique_daily_path_count"],"daily_path_content_map_sha256":s["daily_path_content_map_sha256"],"identity_bound_daily_path_map_sha256":s["identity_bound_daily_path_map_sha256"],"scenario_manifest_sha256":_filehash(mp),"files_verified":list(names),"daily_distribution_status":distribution_status,"simulation_trials_run":False}

def _read_jsonl_gzip(path:Path)->list[dict[str,Any]]:
    with gzip.open(path,"rt",encoding="utf-8") as f:return [json.loads(x) for x in f if x.strip()]

def audit_representative_full_logging_trial(folder:Path,*,expected_scenario_id:str,expected_trial_id:int,expected_source_sha:str,expected_cohort_id:str,expected_trial_fingerprint:str)->dict[str,Any]:
    """Independent post-write audit of one representative replay; never executes Trials."""
    mp=folder/"trial_manifest.json"
    if not mp.is_file():raise RuntimeError("S6_REPRESENTATIVE_TRIAL_MANIFEST_MISSING")
    m=json.loads(mp.read_text(encoding="utf-8"))
    if (m.get("scenario_id"),m.get("trial_id"),m.get("source_sha"),m.get("cohort_id"),m.get("master_seed"),m.get("expected_trial_fingerprint"))!=(expected_scenario_id,expected_trial_id,expected_source_sha,expected_cohort_id,constants.MASTER_SEED,expected_trial_fingerprint):raise RuntimeError("S6_REPRESENTATIVE_TRIAL_MANIFEST_IDENTITY_MISMATCH")
    names=("trial_result.json","daily_snapshots.jsonl.gz","events.jsonl.gz","contracts.jsonl.gz","claims.jsonl.gz","assets.jsonl.gz","tenants.jsonl.gz","guarantors.jsonl.gz","receivables.jsonl.gz","cash_rollforward.jsonl.gz","ar_rollforward.jsonl.gz","asset_rollforward.jsonl.gz","equity_rollforward.jsonl.gz")
    files=m.get("files")
    if not isinstance(files,dict) or set(files)!=set(names):raise RuntimeError("S6_REPRESENTATIVE_FILE_MANIFEST_INCOMPLETE")
    for name in names:
        p=folder/name;e=files.get(name)
        if not p.is_file() or not isinstance(e,dict) or p.stat().st_size!=e.get("size_bytes") or _filehash(p)!=e.get("sha256"):raise RuntimeError(f"S6_REPRESENTATIVE_FILE_HASH_MISMATCH:{name}")
    result=json.loads((folder/"trial_result.json").read_text(encoding="utf-8"))
    if result.get("trial_fingerprint")!=expected_trial_fingerprint or result.get("scenario_id")!=expected_scenario_id or result.get("trial_id")!=expected_trial_id:raise RuntimeError("S6_REPRESENTATIVE_FINANCIAL_FINGERPRINT_MISMATCH")
    daily=_read_jsonl_gzip(folder/"daily_snapshots.jsonl.gz")
    cash=_read_jsonl_gzip(folder/"cash_rollforward.jsonl.gz");ar=_read_jsonl_gzip(folder/"ar_rollforward.jsonl.gz")
    asset_rf=_read_jsonl_gzip(folder/"asset_rollforward.jsonl.gz");equity=_read_jsonl_gzip(folder/"equity_rollforward.jsonl.gz")
    events=_read_jsonl_gzip(folder/"events.jsonl.gz");contracts=_read_jsonl_gzip(folder/"contracts.jsonl.gz")
    claims=_read_jsonl_gzip(folder/"claims.jsonl.gz");assets=_read_jsonl_gzip(folder/"assets.jsonl.gz")
    tenants=_read_jsonl_gzip(folder/"tenants.jsonl.gz");guarantors=_read_jsonl_gzip(folder/"guarantors.jsonl.gz")
    receivables=_read_jsonl_gzip(folder/"receivables.jsonl.gz")
    if not daily:raise RuntimeError("S6_REPRESENTATIVE_DAILY_ROWS_MISSING")
    dates=[]
    for row in daily:
        if (row.get("scenario_id"),row.get("trial_id"),row.get("source_sha"),row.get("cohort_id"),row.get("schema_version"),row.get("daily_balance_schema_version"))!=(expected_scenario_id,expected_trial_id,expected_source_sha,expected_cohort_id,MODEL_SCHEMA_VERSION,"s6-daily-balance-v1"):raise RuntimeError("S6_REPRESENTATIVE_DAILY_IDENTITY_MISMATCH")
        for field in DAILY_BALANCE_INTEGER_FIELDS:
            if type(row.get(field)) is not int:raise RuntimeError(f"S6_REPRESENTATIVE_DAILY_FIELD_INVALID:{field}")
        if row["Total_Assets"]!=row["Total_Equity"] or row["Balance_Difference"]!=0:raise RuntimeError("S6_REPRESENTATIVE_DAILY_BALANCE_MISMATCH")
        dates.append(date.fromisoformat(row["date"]))
    if dates!=sorted(dates) or dates!=[dates[0]+timedelta(days=i) for i in range((dates[-1]-dates[0]).days+1)]:raise RuntimeError("S6_REPRESENTATIVE_DAILY_DATE_GAP_OR_ORDER")
    if any(row.get("Partner1_Reinvestment_Balance") is None or row.get("Partner2_Reinvestment_Balance") is None for row in daily):raise RuntimeError("S6_REPRESENTATIVE_PARTNER_BALANCE_MISSING")
    if any(len(x)!=len(daily) for x in (cash,ar,asset_rf,equity)):raise RuntimeError("S6_REPRESENTATIVE_ROLLFORWARD_ROW_COUNT_MISMATCH")
    checks=0
    for c,a,b,e in zip(cash,ar,asset_rf,equity):
        if c["Opening_Cash"]+c["Inflows"]-c["Outflows"]!=c["Closing_Cash"] or c["Outflows"]!=c["Operating_Cash_Outflows"]+c["Investing_Cash_Outflows"]:raise RuntimeError("S6_REPRESENTATIVE_CASH_ROLLFORWARD_MISMATCH")
        if a["Opening_AR"]+a["Accruals"]-a["Collections"]-a["TransfersToGuarantee"]!=a["Closing_AR"]:raise RuntimeError("S6_REPRESENTATIVE_AR_ROLLFORWARD_MISMATCH")
        if b["Opening_Gross_Bike_Assets"]+b["Capitalized_Purchases_And_Customs"]-b["Gross_Writeoffs_On_Ownership"]!=b["Closing_Gross_Bike_Assets"]:raise RuntimeError("S6_REPRESENTATIVE_GROSS_ASSET_ROLLFORWARD_MISMATCH")
        if b["Opening_Accumulated_Depreciation"]+b["Expense_Depreciation"]-b["AD_Removed_On_Writeoff"]!=b["Closing_Accumulated_Depreciation"]:raise RuntimeError("S6_REPRESENTATIVE_DEPRECIATION_ROLLFORWARD_MISMATCH")
        if e["Opening_Equity"]+e["Operating_Net_Profit"]!=e["Closing_Equity"]:raise RuntimeError("S6_REPRESENTATIVE_EQUITY_ROLLFORWARD_MISMATCH")
        checks+=6
    event_ids=[x.get("event_id") for x in events]
    if len(event_ids)!=len(set(event_ids)) or any(x.get("event_type") not in {v.value for v in EventType} for x in events):raise RuntimeError("S6_REPRESENTATIVE_EVENT_LOG_INVALID")
    for rows,field,label in ((contracts,"contract_id","CONTRACT"),(claims,"claim_id","CLAIM"),(assets,"bike_id","ASSET")):
        ids=[x.get(field) for x in rows]
        if any(not isinstance(v,str) or not v for v in ids) or len(ids)!=len(set(ids)):raise RuntimeError(f"S6_REPRESENTATIVE_{label}_RECORDS_INVALID")
    identity=build_daily_path_identity_evidence(daily,source_sha=expected_source_sha,cohort_id=expected_cohort_id,master_seed=constants.MASTER_SEED,scenario_id=expected_scenario_id,expected_trial_ids=[expected_trial_id],expected_start_date=constants.PROJECT_START_DATE.isoformat(),model_schema_version=MODEL_SCHEMA_VERSION)
    return {"schema_version":"s6-representative-post-write-audit-v1","status":"PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING","scenario_id":expected_scenario_id,"trial_id":expected_trial_id,"source_sha":expected_source_sha,"cohort_id":expected_cohort_id,"trial_fingerprint_match":True,"trial_fingerprint":expected_trial_fingerprint,"daily_rows_checked":len(daily),"balance_mismatch_count":0,"partner1_balance_rows":len(daily),"partner2_balance_rows":len(daily),"rollforward_days_checked":len(daily),"rollforward_equation_checks":checks,"rollforward_mismatch_count":0,"event_count":len(events),"contract_count":len(contracts),"claim_count":len(claims),"asset_count":len(assets),"tenant_count":len(tenants),"guarantor_count":len(guarantors),"receivable_count":len(receivables),"daily_path_identity":identity["summary"],"historical_48000_trial_daily_artifacts_audited":False}


def main()->None:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--scenario-dir",required=True,type=Path);a=p.parse_args()
    print(json.dumps(audit_scenario_artifacts(a.scenario_dir),ensure_ascii=False,sort_keys=True))
if __name__=="__main__":main()
