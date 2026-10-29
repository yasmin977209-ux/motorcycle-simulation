"""Versioned source-bound S6 daily-balance and path-identity validation; never executes Trials."""
from __future__ import annotations
from collections import defaultdict
from datetime import date,timedelta
import hashlib,json,re
from typing import Any,Iterable
DAILY_BALANCE_SCHEMA_VERSION="s6-daily-balance-v1"
DAILY_PATH_IDENTITY_SCHEMA_VERSION="s6-daily-path-identity-v1"
SCENARIO_MANIFEST_SCHEMA_VERSION="s6-first-checkpoint-v2"
MODEL_SCHEMA_VERSION="v2.3"
DAILY_BALANCE_INTEGER_FIELDS=("Cash","Capital","Retained_Earnings","Net_Equity","Accounts_Receivable","Guarantee_Claim_Receivable","Gross_Bike_Assets","Accumulated_Depreciation","Net_Bike_Assets","Total_Assets","Total_Equity","Liabilities","Balance_Difference","Partner1_Reinvestment_Balance","Partner2_Reinvestment_Balance","Active_Bikes","Owned_Transferred_Bikes","Pending_Claims")
DAILY_SNAPSHOT_FIELDS=frozenset({"date","trial_id","daily_balance_schema_version",*DAILY_BALANCE_INTEGER_FIELDS,"Final_Close_Date","scenario_id","source_sha","cohort_id","schema_version"})
def _canon(v:object)->bytes:
    try:return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode("utf-8")
    except (TypeError,ValueError) as e:raise RuntimeError("S6_DAILY_PATH_CANONICAL_JSON_INVALID") from e
def _sha(b:bytes)->str:return hashlib.sha256(b).hexdigest()
def _identity(*,source_sha:str,cohort_id:str,master_seed:int,scenario_id:str,model_schema_version:str,daily_balance_schema_version:str)->str:
    if not isinstance(source_sha,str) or not re.fullmatch(r"[0-9a-f]{40}",source_sha):raise RuntimeError("S6_DAILY_PATH_SOURCE_SHA_INVALID")
    if cohort_id!=f"s6-v23-{source_sha[:8]}":raise RuntimeError("S6_DAILY_PATH_SOURCE_COHORT_MISMATCH")
    if type(master_seed)is not int:raise RuntimeError("S6_DAILY_PATH_MASTER_SEED_INVALID")
    m=re.fullmatch(r"C([0-9]{3})_G([0-9]{3})",str(scenario_id))
    if not m:raise RuntimeError("S6_DAILY_PATH_SCENARIO_ID_INVALID")
    if model_schema_version!=MODEL_SCHEMA_VERSION:raise RuntimeError("S6_DAILY_PATH_MODEL_SCHEMA_MISMATCH")
    if daily_balance_schema_version!=DAILY_BALANCE_SCHEMA_VERSION:raise RuntimeError("S6_DAILY_PATH_BALANCE_SCHEMA_MISMATCH")
    return f"C{m.group(1)}"
def build_daily_path_identity_evidence(rows:list[dict[str,Any]],*,source_sha:str,cohort_id:str,master_seed:int,scenario_id:str,expected_trial_ids:Iterable[int],expected_start_date:str,model_schema_version:str=MODEL_SCHEMA_VERSION,daily_balance_schema_version:str=DAILY_BALANCE_SCHEMA_VERSION)->dict[str,Any]:
    stream=_identity(source_sha=source_sha,cohort_id=cohort_id,master_seed=master_seed,scenario_id=scenario_id,model_schema_version=model_schema_version,daily_balance_schema_version=daily_balance_schema_version)
    try:start=date.fromisoformat(expected_start_date)
    except (TypeError,ValueError) as e:raise RuntimeError("S6_DAILY_PATH_EXPECTED_START_DATE_INVALID") from e
    if start.isoformat()!=expected_start_date:raise RuntimeError("S6_DAILY_PATH_EXPECTED_START_DATE_INVALID")
    tids=list(expected_trial_ids)
    if not tids or any(type(t)is not int or t<1 for t in tids) or tids!=sorted(set(tids)):raise RuntimeError("S6_DAILY_PATH_EXPECTED_TRIAL_IDS_INVALID")
    if not rows:raise RuntimeError("S6_DAILY_PATH_SNAPSHOT_ROWS_MISSING")
    grouped:dict[int,list[dict[str,Any]]]=defaultdict(list)
    for r in rows:
        if not isinstance(r,dict) or set(r)!=set(DAILY_SNAPSHOT_FIELDS):raise RuntimeError("S6_DAILY_BALANCE_SNAPSHOT_FIELDS_OR_SCHEMA_MISMATCH")
        tid=r.get("trial_id")
        if type(tid)is not int or tid<1:raise RuntimeError("S6_DAILY_PATH_TRIAL_ID_INVALID")
        if (r.get("source_sha")!=source_sha or r.get("cohort_id")!=cohort_id or r.get("scenario_id")!=scenario_id or r.get("schema_version")!=model_schema_version or r.get("daily_balance_schema_version")!=daily_balance_schema_version):raise RuntimeError("S6_DAILY_SNAPSHOT_SOURCE_COHORT_SCENARIO_OR_SCHEMA_MISMATCH")
        for k,v in r.items():
            if isinstance(v,float):raise RuntimeError(f"S6_DAILY_SNAPSHOT_FLOAT_FORBIDDEN:{k}")
        for k in DAILY_BALANCE_INTEGER_FIELDS:
            if type(r.get(k))is not int:raise RuntimeError(f"S6_DAILY_BALANCE_INTEGER_FIELD_INVALID:{k}")
        if r.get("Final_Close_Date") is not None and not isinstance(r.get("Final_Close_Date"),str):raise RuntimeError("S6_DAILY_FINAL_CLOSE_DATE_INVALID")
        try:d=date.fromisoformat(str(r.get("date","")))
        except (TypeError,ValueError) as e:raise RuntimeError("S6_DAILY_PATH_DATE_INVALID") from e
        if d.isoformat()!=r.get("date"):raise RuntimeError("S6_DAILY_PATH_DATE_INVALID")
        if (r["Gross_Bike_Assets"]-r["Accumulated_Depreciation"]!=r["Net_Bike_Assets"] or r["Cash"]+r["Accounts_Receivable"]+r["Guarantee_Claim_Receivable"]+r["Net_Bike_Assets"]!=r["Total_Assets"] or r["Capital"]+r["Retained_Earnings"]!=r["Total_Equity"] or r["Net_Equity"]!=r["Total_Equity"] or r["Liabilities"]!=0 or r["Total_Assets"]!=r["Total_Equity"] or r["Balance_Difference"]!=r["Total_Assets"]-r["Total_Equity"] or r["Balance_Difference"]!=0):raise RuntimeError(f"S6_DAILY_BALANCE_IDENTITY_MISMATCH:{tid}:{d.isoformat()}")
        grouped[tid].append(r)
    if set(grouped)!=set(tids):raise RuntimeError("S6_DAILY_PATH_TRIAL_COVERAGE_MISMATCH")
    content,bound,spans={},{},{}
    for tid in tids:
        path=sorted(grouped[tid],key=lambda x:x["date"]);ds=[date.fromisoformat(x["date"]) for x in path]
        if not path or ds[0]!=start:raise RuntimeError(f"S6_DAILY_PATH_START_DATE_MISMATCH:{tid}")
        if len(set(ds))!=len(ds):raise RuntimeError(f"S6_DAILY_PATH_DUPLICATE_DATE:{tid}")
        for prev,cur in zip(ds,ds[1:]):
            if cur!=prev+timedelta(days=1):raise RuntimeError(f"S6_DAILY_PATH_DATE_GAP:{tid}:{prev}:{cur}")
        if path[-1].get("Final_Close_Date")!=path[-1]["date"]:raise RuntimeError(f"S6_DAILY_PATH_CLOSE_DATE_MISMATCH:{tid}")
        if any(x.get("Final_Close_Date") is not None for x in path[:-1]):raise RuntimeError(f"S6_DAILY_PATH_EARLY_CLOSE_MARKER:{tid}")
        payload=[{k:v for k,v in x.items() if k not in {"trial_id","scenario_id","source_sha","cohort_id","schema_version"}} for x in path]
        ch=_sha(b"\n".join(_canon(x) for x in payload));content[tid]=ch;spans[tid]=(path[0]["date"],path[-1]["date"])
        env={"fingerprint_schema_version":DAILY_PATH_IDENTITY_SCHEMA_VERSION,"source_sha":source_sha,"cohort_id":cohort_id,"master_seed":master_seed,"rng_stream_id":stream,"scenario_id":scenario_id,"trial_id":tid,"model_schema_version":model_schema_version,"daily_balance_schema_version":daily_balance_schema_version,"expected_start_date":expected_start_date,"row_count":len(path),"first_date":path[0]["date"],"last_date":path[-1]["date"],"path_content_sha256":ch}
        bound[tid]=_sha(_canon(env))
    cm="".join(f"{t}|{content[t]}\n" for t in tids).encode();bm="".join(f"{t}|{bound[t]}\n" for t in tids).encode()
    summary={"contract_schema_version":DAILY_PATH_IDENTITY_SCHEMA_VERSION,"status":"PASS_SCOPED_DAILY_BALANCE_PATH_CONTRACT","hash_algorithm":"SHA-256","content_fingerprint_algorithm":"canonical-jsonl-v1; identity metadata excluded; daily_balance_schema_version retained","identity_bound_fingerprint_algorithm":"canonical-json-v1; source/cohort/seed/RNG stream/scenario/trial/model schema/daily schema/date span/row count bound","source_sha":source_sha,"cohort_id":cohort_id,"master_seed":master_seed,"rng_stream_id":stream,"scenario_id":scenario_id,"model_schema_version":model_schema_version,"daily_balance_schema_version":daily_balance_schema_version,"expected_start_date":expected_start_date,"trial_count":len(tids),"row_count":len(rows),"balance_rows_checked":len(rows),"balance_mismatch_count":0,"unique_daily_path_count":len(set(content.values())),"daily_path_content_map_sha256":_sha(cm),"identity_bound_daily_path_map_sha256":_sha(bm),"trial_date_spans":{str(t):{"first_date":spans[t][0],"last_date":spans[t][1]} for t in tids},"identity_fields":["source_sha","cohort_id","master_seed","rng_stream_id","scenario_id","trial_id","model_schema_version","daily_balance_schema_version"]}
    return {"summary":summary,"path_content_fingerprint_by_trial":content,"identity_bound_fingerprint_by_trial":bound}
def require_daily_path_manifest_contract(manifest:dict[str,Any],*,expected_source_sha:str,expected_cohort_id:str,expected_scenario_id:str,expected_master_seed:int,expected_trial_count:int,model_schema_version:str=MODEL_SCHEMA_VERSION)->None:
    if manifest.get("schema_version")!=SCENARIO_MANIFEST_SCHEMA_VERSION:raise RuntimeError("S6_PREVIOUS_CHECKPOINT_DAILY_SCHEMA_OR_PATH_IDENTITY_MISMATCH")
    if (manifest.get("source_sha")!=expected_source_sha or manifest.get("cohort_id")!=expected_cohort_id or manifest.get("scenario_id")!=expected_scenario_id or manifest.get("master_seed")!=expected_master_seed or manifest.get("schema_version_model")!=model_schema_version or manifest.get("trial_count")!=expected_trial_count or manifest.get("trial_id_start")!=1 or manifest.get("trial_id_end")!=expected_trial_count):raise RuntimeError("S6_PREVIOUS_CHECKPOINT_DAILY_SCHEMA_OR_PATH_IDENTITY_MISMATCH")
    b=manifest.get("daily_balance_contract")
    if not isinstance(b,dict) or (b.get("schema_version")!=DAILY_BALANCE_SCHEMA_VERSION or b.get("status")!="PASS_SCOPED_POST_WRITE_BALANCE_CHECK" or b.get("source_sha")!=expected_source_sha or b.get("cohort_id")!=expected_cohort_id or b.get("master_seed")!=expected_master_seed or b.get("model_schema_version")!=model_schema_version or b.get("balance_mismatch_count")!=0):raise RuntimeError("S6_PREVIOUS_CHECKPOINT_DAILY_SCHEMA_OR_PATH_IDENTITY_MISMATCH")
    p=manifest.get("daily_path_identity_contract")
    if not isinstance(p,dict) or (p.get("contract_schema_version")!=DAILY_PATH_IDENTITY_SCHEMA_VERSION or p.get("status")!="PASS_SCOPED_DAILY_BALANCE_PATH_CONTRACT" or p.get("source_sha")!=expected_source_sha or p.get("cohort_id")!=expected_cohort_id or p.get("master_seed")!=expected_master_seed or p.get("scenario_id")!=expected_scenario_id or p.get("model_schema_version")!=model_schema_version or p.get("daily_balance_schema_version")!=DAILY_BALANCE_SCHEMA_VERSION or p.get("trial_count")!=expected_trial_count or p.get("row_count",0)<=0 or p.get("balance_rows_checked")!=p.get("row_count") or p.get("balance_mismatch_count")!=0 or not re.fullmatch(r"[0-9a-f]{64}",str(p.get("daily_path_content_map_sha256",""))) or not re.fullmatch(r"[0-9a-f]{64}",str(p.get("identity_bound_daily_path_map_sha256","")))):raise RuntimeError("S6_PREVIOUS_CHECKPOINT_DAILY_SCHEMA_OR_PATH_IDENTITY_MISMATCH")
