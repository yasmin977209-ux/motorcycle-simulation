from __future__ import annotations
from datetime import date,timedelta
import hashlib,json
from pathlib import Path
import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from scripts.s6_daily_path_identity import DAILY_BALANCE_INTEGER_FIELDS,DAILY_BALANCE_SCHEMA_VERSION,DAILY_PATH_IDENTITY_SCHEMA_VERSION,MODEL_SCHEMA_VERSION,SCENARIO_MANIFEST_SCHEMA_VERSION,build_daily_path_identity_evidence,require_daily_path_manifest_contract
from scripts.audit_s6_daily_balance_artifact import audit_scenario_artifacts
SRC="a"*40;COHORT=f"s6-v23-{SRC[:8]}";SC="C085_G100";SEED=20270101;START=date(2027,1,1)
def row(tid,day,src=SRC,cohort=COHORT):
    return {"date":day.isoformat(),"trial_id":tid,"daily_balance_schema_version":DAILY_BALANCE_SCHEMA_VERSION,"Cash":100,"Capital":100,"Retained_Earnings":0,"Net_Equity":100,"Accounts_Receivable":0,"Guarantee_Claim_Receivable":0,"Gross_Bike_Assets":0,"Accumulated_Depreciation":0,"Net_Bike_Assets":0,"Total_Assets":100,"Total_Equity":100,"Liabilities":0,"Balance_Difference":0,"Partner1_Reinvestment_Balance":0,"Partner2_Reinvestment_Balance":0,"Active_Bikes":0,"Owned_Transferred_Bikes":0,"Pending_Claims":0,"Final_Close_Date":(START+timedelta(days=1)).isoformat() if day==START+timedelta(days=1) else None,"scenario_id":SC,"source_sha":src,"cohort_id":cohort,"schema_version":MODEL_SCHEMA_VERSION}
def rows(src=SRC,cohort=COHORT):return [row(t,d,src,cohort) for t in (1,2) for d in (START,START+timedelta(days=1))]
def ev(rs,src=SRC,cohort=COHORT):return build_daily_path_identity_evidence(rs,source_sha=src,cohort_id=cohort,master_seed=SEED,scenario_id=SC,expected_trial_ids=[1,2],expected_start_date=START.isoformat())
def test_content_and_identity_bound_hashes_are_separate():
    x=ev(rows());s=x["summary"];assert s["contract_schema_version"]==DAILY_PATH_IDENTITY_SCHEMA_VERSION and s["balance_mismatch_count"]==0 and s["row_count"]==s["balance_rows_checked"]==4 and s["unique_daily_path_count"]==1
    assert x["path_content_fingerprint_by_trial"][1]==x["path_content_fingerprint_by_trial"][2] and x["identity_bound_fingerprint_by_trial"][1]!=x["identity_bound_fingerprint_by_trial"][2]
def test_identity_hash_binds_source_and_cohort():
    a=ev(rows());src="b"*40;co=f"s6-v23-{src[:8]}";b=ev(rows(src,co),src,co)
    assert a["summary"]["daily_path_content_map_sha256"]==b["summary"]["daily_path_content_map_sha256"] and a["summary"]["identity_bound_daily_path_map_sha256"]!=b["summary"]["identity_bound_daily_path_map_sha256"]
def test_foreign_source_fails_closed():
    rs=rows();rs[-1]["source_sha"]="b"*40
    with pytest.raises(RuntimeError,match="S6_DAILY_SNAPSHOT_SOURCE_COHORT_SCENARIO_OR_SCHEMA_MISMATCH"):ev(rs)
def test_wrong_schema_or_missing_field_fails_closed():
    rs=rows();rs[0]["daily_balance_schema_version"]="wrong"
    with pytest.raises(RuntimeError,match="S6_DAILY_SNAPSHOT_SOURCE_COHORT_SCENARIO_OR_SCHEMA_MISMATCH"):ev(rs)
    rs=rows();rs[0].pop("Total_Assets")
    with pytest.raises(RuntimeError,match="S6_DAILY_BALANCE_SNAPSHOT_FIELDS_OR_SCHEMA_MISMATCH"):ev(rs)
def test_float_or_balance_failure_fails_closed():
    rs=rows();rs[0]["Cash"]=100.0
    with pytest.raises(RuntimeError,match="S6_DAILY_SNAPSHOT_FLOAT_FORBIDDEN:Cash"):ev(rs)
    rs=rows();rs[0]["Total_Assets"]=99
    with pytest.raises(RuntimeError,match="S6_DAILY_BALANCE_IDENTITY_MISMATCH"):ev(rs)
def test_date_gap_fails_closed():
    rs=rows();rs[-1]["date"]=(START+timedelta(days=2)).isoformat();rs[-1]["Final_Close_Date"]=rs[-1]["date"]
    with pytest.raises(RuntimeError,match="S6_DAILY_PATH_DATE_GAP"):ev(rs)
def test_old_manifest_is_rejected_before_resume():
    old={"schema_version":"s6-first-checkpoint-v1","source_sha":SRC,"cohort_id":COHORT,"scenario_id":SC,"master_seed":SEED,"schema_version_model":MODEL_SCHEMA_VERSION,"trial_count":2,"trial_id_start":1,"trial_id_end":2}
    with pytest.raises(RuntimeError,match="S6_PREVIOUS_CHECKPOINT_DAILY_SCHEMA_OR_PATH_IDENTITY_MISMATCH"):
        require_daily_path_manifest_contract(old,expected_source_sha=SRC,expected_cohort_id=COHORT,expected_scenario_id=SC,expected_master_seed=SEED,expected_trial_count=2)
def test_postwrite_audit_rechecks_parquet_and_hashes(tmp_path:Path):
    d=tmp_path/SC;d.mkdir();daily=rows();trial=[{"trial_id":i,"scenario_id":SC,"source_sha":SRC,"cohort_id":COHORT,"schema_version":MODEL_SCHEMA_VERSION} for i in (1,2)]
    pq.write_table(pa.Table.from_pylist(trial),d/"trials_summary.parquet");pq.write_table(pa.Table.from_pylist(daily),d/"daily_snapshots.parquet");pq.write_table(pa.Table.from_pylist([{"date":START.isoformat(),"value":100}]),d/"daily_distribution.parquet");(d/"opt1_provenance.json").write_text("{}",encoding="utf-8")
    names=("trials_summary.parquet","daily_snapshots.parquet","daily_distribution.parquet","opt1_provenance.json");files={}
    for n in names:
        p=d/n;files[n]={"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"size_bytes":p.stat().st_size}
    contract=ev(daily)["summary"];m={"schema_version":SCENARIO_MANIFEST_SCHEMA_VERSION,"status":"EXECUTED","scenario_id":SC,"source_sha":SRC,"cohort_id":COHORT,"master_seed":SEED,"schema_version_model":MODEL_SCHEMA_VERSION,"trial_id_start":1,"trial_id_end":2,"trial_count":2,"daily_balance_contract":{"schema_version":DAILY_BALANCE_SCHEMA_VERSION,"status":"PASS_SCOPED_POST_WRITE_BALANCE_CHECK","source_sha":SRC,"cohort_id":COHORT,"master_seed":SEED,"model_schema_version":MODEL_SCHEMA_VERSION,"rows_checked":4,"balance_mismatch_count":0,"required_integer_fields":list(DAILY_BALANCE_INTEGER_FIELDS)},"daily_path_identity_contract":contract,"files":files}
    (d/"scenario_manifest.json").write_text(json.dumps(m,sort_keys=True),encoding="utf-8");report=audit_scenario_artifacts(d)
    assert report["status"]=="PASS_SCOPED_DAILY_BALANCE_AND_PATH_IDENTITY" and report["daily_rows_checked"]==4 and report["daily_balance_mismatch_count"]==0 and report["identity_bound_daily_path_map_sha256"]==contract["identity_bound_daily_path_map_sha256"]
