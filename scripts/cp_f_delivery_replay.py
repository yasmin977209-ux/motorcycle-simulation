#!/usr/bin/env python3
"""Delivery-only deterministic replay for missing Stage 12 daily/detail outputs."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
from dataclasses import asdict, is_dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import daily_engine
import monte_carlo
from scripts.golden_reference_provider import APPROVED_SOURCE_SHA, MASTER_SEED, GoldenReferenceProvider, stage10_trial_result_sha256

SOURCE_SHA = APPROVED_SOURCE_SHA
SCHEMA_VERSION = "stage12-daily-accounting-v1"
REFERENCE_RUN_ID = 37964656154
QUANTILES = (("P10", 0.10), ("P25", 0.25), ("P50", 0.50), ("P75", 0.75), ("P90", 0.90))
DAILY_METRICS = ("Cash", "Net_Equity", "Active_Bikes", "Owned_Transferred_Bikes", "Pending_Claims")
BUSINESS_RESULT_FIELDS = tuple(k for k in monte_carlo.TrialResult.__dataclass_fields__ if k != "trial_id")
DAILY_FIELDS = [
    ("scenario_id", pa.string()), ("trial_id", pa.int64()), ("date", pa.string()),
    ("source_sha", pa.string()), ("master_seed", pa.int64()),
    ("Opening_Cash", pa.int64()), ("cash_inflows", pa.int64()), ("cash_outflows", pa.int64()), ("Closing_Cash", pa.int64()),
    ("Opening_AR", pa.int64()), ("ar_accruals", pa.int64()), ("ar_collections", pa.int64()), ("ar_transfers_to_guarantee", pa.int64()), ("Closing_AR", pa.int64()),
    ("Opening_Gross_Bike_Assets", pa.int64()), ("capitalized_purchases_and_customs", pa.int64()), ("gross_writeoffs_on_ownership", pa.int64()), ("Closing_Gross_Bike_Assets", pa.int64()),
    ("Opening_Accumulated_Depreciation", pa.int64()), ("depreciation_expense", pa.int64()), ("ad_removed_on_writeoff", pa.int64()), ("Closing_Accumulated_Depreciation", pa.int64()),
    ("Net_Bike_Assets", pa.int64()), ("Capital", pa.int64()), ("Retained_Earnings", pa.int64()), ("Opening_Equity", pa.int64()),
    ("Operating_Net_Profit", pa.int64()), ("Closing_Equity", pa.int64()), ("Guarantee_Claim_Receivable", pa.int64()), ("Total_Assets", pa.int64()),
    ("Liabilities", pa.int64()), ("Balance_Difference", pa.int64()), ("Final_Close_Date", pa.string()), ("Simulation_Stopped", pa.bool_()),
    ("Active_Bikes", pa.int64()), ("Owned_Transferred_Bikes", pa.int64()), ("Pending_Claims", pa.int64()), ("result_sha256", pa.string()),
]

def business_result_projection(row: dict[str, Any]) -> dict[str, Any]:
    """Exclude trial identity only; preserve every other recorded business field (D-2026-10-14-11; Reference §14.4)."""
    return {key: value for key, value in row.items() if key != "trial_id"}

def linear_quantile(values: list[float], quantile: float) -> float:
    return float(np.quantile(np.asarray(values, dtype=np.float64), quantile, method="linear"))

def _identity(scenario: str) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION, "scenario": scenario, "source_sha": SOURCE_SHA, "master_seed": MASTER_SEED,
        "rng_policy": "rng.py:SHA-256(seed key master_seed|scenario_id|trial_id|bike_id|date|event_type); draw=first_8_digest_bytes_big_endian/2^64; probability boundaries are deterministic",
        "sampling_policy": "delivery-only deterministic replay; no new statistical cohort; no historical dataset mutation",
        "trial_id_policy": "preserve original one-based scenario/trial identities; no duplicates",
    }

def _identity_historical(scenario: str) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION, "scenario": scenario, "source_sha": SOURCE_SHA, "master_seed": MASTER_SEED,
        "rng_policy": "rng.py:SHA-256(seed key master_seed|scenario_id|trial_id|bike_id|date|event_type); draw=first_8_digest_bytes_big_endian/2^64; probability boundaries are deterministic",
        "sampling_policy": "one-based contiguous trial IDs; C100 scenarios use 1..1; non-C100 scenarios use 1..550; one materialization per scenario/trial; no cross-run inputs or resume",
        "stability_policy": "C100 uses one deterministic trial and no CI gate; non-C100 checkpoint N=300 then +50; 95% Student-t CI half-width <1% of absolute mean for Final_Net_Project_Equity, Partner1_Final_Entitlement, Partner2_Final_Entitlement; CI_ABSOLUTE_EPSILON=1; three consecutive successful checkpoints; accepted N=550 (checkpoints 450, 500, 550)",
        "trial_id_policy": "one-based contiguous trial IDs from 1 to scenario target; no duplicate IDs",
    }

def _daily_schema(scenario: str) -> pa.Schema:
    raw = json.dumps(_identity(scenario), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return pa.schema([pa.field(n, t, nullable=(n == "Final_Close_Date")) for n,t in DAILY_FIELDS], metadata={b"stage12.dataset_identity":raw})

def _jsonable(value: Any) -> Any:
    if is_dataclass(value): return _jsonable(asdict(value))
    if isinstance(value, Enum): return value.value
    if isinstance(value, date): return value.isoformat()
    if isinstance(value, dict): return {str(k):_jsonable(v) for k,v in value.items()}
    if isinstance(value, (list,tuple)): return [_jsonable(v) for v in value]
    if isinstance(value, np.generic): return value.item()
    return value

def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))

def _validate_historical_daily(path: Path, scenario: str) -> dict[str, Any]:
    pf=pq.ParquetFile(path); metadata=pf.schema_arrow.metadata or {}; raw=metadata.get(b"stage12.dataset_identity")
    if raw is None or json.loads(raw.decode("utf-8")) != _identity_historical(scenario):
        raise RuntimeError(f"HISTORICAL_DAILY_IDENTITY_MISMATCH:{scenario}")
    expected=[1] if scenario.startswith("C100_") else list(range(1,551))
    seen=[]; current=None; previous=None; count=0; rows=0
    for batch in pf.iter_batches(batch_size=50000, columns=["scenario_id","trial_id","date","source_sha","master_seed"]):
        for r in batch.to_pylist():
            rows+=1
            if r.get("scenario_id")!=scenario or r.get("source_sha")!=SOURCE_SHA or int(r.get("master_seed",-1))!=MASTER_SEED:
                raise RuntimeError(f"HISTORICAL_DAILY_ROW_IDENTITY_MISMATCH:{scenario}")
            tid=int(r["trial_id"]); day=date.fromisoformat(str(r["date"]))
            if current is None:
                current=tid; seen.append(tid); previous=day; count=1; continue
            if tid==current:
                if previous is None or (day-previous).days!=1: raise RuntimeError(f"HISTORICAL_DAILY_GAP_OR_DUPLICATE:{scenario}/{tid}/{day}")
                previous=day; count+=1
            else:
                if tid<=current or previous is None or count<1: raise RuntimeError(f"HISTORICAL_DAILY_ORDER_INVALID:{scenario}")
                current=tid; seen.append(tid); previous=day; count=1
    if seen!=expected or rows==0: raise RuntimeError(f"HISTORICAL_DAILY_TRIAL_COVERAGE_MISMATCH:{scenario}")
    return {"trial_count":len(seen),"rows":rows,"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}

def _check_trial_source_row(row: dict[str,Any], scenario: str, tid: int) -> None:
    if row.get("scenario_id")!=scenario or int(row.get("trial_id",-1))!=tid: raise RuntimeError(f"TRIAL_SOURCE_KEY_MISMATCH:{scenario}/{tid}")
    if row.get("source_sha")!=SOURCE_SHA or int(row.get("master_seed",-1))!=MASTER_SEED: raise RuntimeError(f"TRIAL_SOURCE_IDENTITY_MISMATCH:{scenario}/{tid}")
    payload=row.get("trial_result")
    if not isinstance(payload,dict) or payload.get("scenario_id")!=scenario or int(payload.get("trial_id",-1))!=tid:
        raise RuntimeError(f"TRIAL_SOURCE_PAYLOAD_MISMATCH:{scenario}/{tid}")

def _capture_day(daily: list[dict[str,Any]], partner: list[dict[str,Any]], project: Any, day: date, tid: int, daily_meta: list[dict[str,Any]]) -> None:
    row=monte_carlo._daily_snapshot(project,day,tid)
    row.update({
        "Accounts_Receivable":project.accounts_receivable, "Accumulated_Depreciation":project.accumulated_depreciation,
        "Cumulative_Project_Profit":project.cumulative_project_profit, "Gross_Bike_Assets":project.gross_bike_assets,
        "Guarantee_Claim_Receivable":project.guarantee_claim_receivable, "Operating_Expenses":project.operating_expenses,
        "Operating_Revenue":project.operating_revenue, "Operating_Net_Profit":project.operating_net_profit,
        "Partner1_Reinvestment_Balance":project.partner1_reinvestment_balance, "Partner2_Reinvestment_Balance":project.partner2_reinvestment_balance,
    })
    daily.append(row)
    partner.append({"date":day.isoformat(),"Partner1_Reinvestment_Balance":project.partner1_reinvestment_balance,"Partner2_Reinvestment_Balance":project.partner2_reinvestment_balance})
    daily_meta.append({
        "date":day.isoformat(),"Capital":project.capital,"Retained_Earnings":project.retained_earnings,"Simulation_Stopped":project.simulation_stopped,
        "Active_Bikes":sum(b.current_state in daily_engine.POSSESSION_STATES for b in project.bikes),
        "Owned_Transferred_Bikes":sum(b.current_state.value=="OWNED_TRANSFERRED" for b in project.bikes),
        "Pending_Claims":sum(c.status.value=="PENDING" for c in project.guarantee_claims),
    })

def _accounting_rows(project: Any, scenario: str, tid: int, result_sha: str, meta: list[dict[str,Any]]) -> list[dict[str,Any]]:
    series=(project.daily_snapshots,project.cash_rollforward,project.ar_rollforward,project.asset_rollforward,project.equity_rollforward,meta)
    if len({len(x) for x in series})!=1: raise RuntimeError(f"DAILY_ACCOUNTING_LENGTH_MISMATCH:{scenario}/{tid}")
    rows=[]
    for snap,cash,ar,asset,equity,m in zip(*series):
        day=snap["date"].isoformat()
        if m["date"]!=day: raise RuntimeError(f"DAILY_ACCOUNTING_DATE_MISMATCH:{scenario}/{tid}:{day}")
        rows.append({
            "scenario_id":scenario,"trial_id":tid,"date":day,"source_sha":SOURCE_SHA,"master_seed":MASTER_SEED,
            "Opening_Cash":cash["Opening_Cash"],"cash_inflows":cash["Inflows"],"cash_outflows":cash["Outflows"],"Closing_Cash":cash["Closing_Cash"],
            "Opening_AR":ar["Opening_AR"],"ar_accruals":ar["Accruals"],"ar_collections":ar["Collections"],"ar_transfers_to_guarantee":ar["TransfersToGuarantee"],"Closing_AR":ar["Closing_AR"],
            "Opening_Gross_Bike_Assets":asset["Opening_Gross_Bike_Assets"],"capitalized_purchases_and_customs":asset["Capitalized_Purchases_And_Customs"],"gross_writeoffs_on_ownership":asset["Gross_Writeoffs_On_Ownership"],"Closing_Gross_Bike_Assets":asset["Closing_Gross_Bike_Assets"],
            "Opening_Accumulated_Depreciation":asset["Opening_Accumulated_Depreciation"],"depreciation_expense":asset["Depreciation_Expense"],"ad_removed_on_writeoff":asset["AD_Removed_On_Writeoff"],"Closing_Accumulated_Depreciation":asset["Closing_Accumulated_Depreciation"],
            "Net_Bike_Assets":snap["Net_Bike_Assets"],"Capital":m["Capital"],"Retained_Earnings":m["Retained_Earnings"],"Opening_Equity":equity["Opening_Equity"],"Operating_Net_Profit":equity["Operating_Net_Profit"],"Closing_Equity":equity["Closing_Equity"],
            "Guarantee_Claim_Receivable":snap["Guarantee_Claim_Receivable"],"Total_Assets":snap["Total_Assets"],"Liabilities":snap["Liabilities"],"Balance_Difference":snap["Balance_Difference"],
            "Final_Close_Date":project.final_close_date.isoformat() if project.final_close_date else None,"Simulation_Stopped":m["Simulation_Stopped"],
            "Active_Bikes":m["Active_Bikes"],"Owned_Transferred_Bikes":m["Owned_Transferred_Bikes"],"Pending_Claims":m["Pending_Claims"],"result_sha256":result_sha,
        })
    return rows

def _representative_payload(project: Any, result: Any, daily: list[dict[str,Any]], partner: list[dict[str,Any]]) -> dict[str,Any]:
    inventory=[]
    for b in project.bikes:
        inventory.append({"bike_id":b.bike_id,"source":_jsonable(b.source),"purchase_date":_jsonable(b.purchase_date),"delivery_date":_jsonable(b.delivery_date),"gross_cost":b.gross_cost,"accumulated_depreciation":b.accumulated_depreciation,"net_book_value":b.net_book_value,"termination_count":b.termination_count,"secondary_cycle_count":b.secondary_cycle_count,"state":_jsonable(b.current_state)})
    return {
        "summary":_jsonable(result),"daily":daily,"partner_memo":partner,
        "accounting":{"cash_rollforward":_jsonable(project.cash_rollforward),"ar_rollforward":_jsonable(project.ar_rollforward),"asset_rollforward":_jsonable(project.asset_rollforward),"equity_rollforward":_jsonable(project.equity_rollforward),"daily_balance_checks":_jsonable(project.daily_balance_checks)},
        "assets":_jsonable(project.bikes),"final_inventory":inventory,"contracts":_jsonable(list(project.contracts.values()),),
        "tenants":_jsonable(project.tenants),"guarantors":_jsonable(project.guarantors),"guarantee_claims":_jsonable(project.guarantee_claims),
        "receivables":_jsonable(project.receivables),"event_log":_jsonable(project.event_log),"error_log":_jsonable(project.error_log),
        "final_reconciliation":{"final_cash":int(project.project_cash),"final_close_date":_jsonable(project.final_close_date),"final_equity_from_m17":int(project.final_net_project_equity),"final_net_project_equity":int(project.final_net_project_equity)},
    }

def _daily_distribution(historical_path: Path, extension_path: Path, result_rows: list[dict[str,Any]], scenario: str, out: Path) -> dict[str,Any]:
    closes={int(r["trial_id"]):r.get("final_close_date") for r in result_rows}
    tids=list(range(1,1201))
    if sorted(closes)!=tids: raise RuntimeError(f"DELIVERY_TRIAL_RESULT_COVERAGE_MISMATCH:{scenario}")
    grouped: dict[str,dict[str,list[float]]]={}; bounds:dict[int,dict[str,Any]]={}; last_tid=0
    def consume(rows:list[dict[str,Any]]) -> None:
        nonlocal last_tid
        for r in rows:
            if r.get("scenario_id")!=scenario or r.get("source_sha")!=SOURCE_SHA or int(r.get("master_seed",-1))!=MASTER_SEED: raise RuntimeError(f"DAILY_ROW_IDENTITY_MISMATCH:{scenario}")
            tid=int(r["trial_id"]); day=str(r["date"])
            if tid not in closes or tid<last_tid: raise RuntimeError(f"DAILY_TRIAL_ORDER_OR_RANGE_MISMATCH:{scenario}/{tid}")
            b=bounds.setdefault(tid,{"first":day,"last":day,"count":0})
            if b["count"] and (date.fromisoformat(day)-date.fromisoformat(b["last"])).days!=1: raise RuntimeError(f"DAILY_DUPLICATE_OR_GAP:{scenario}/{tid}/{day}")
            b["last"]=day; b["count"]+=1; last_tid=tid
            target=grouped.setdefault(day,{m:[] for m in DAILY_METRICS})
            vals={"Cash":r["Closing_Cash"],"Net_Equity":r["Closing_Equity"],"Active_Bikes":r["Active_Bikes"],"Owned_Transferred_Bikes":r["Owned_Transferred_Bikes"],"Pending_Claims":r["Pending_Claims"]}
            for metric in DAILY_METRICS:
                v=vals[metric]
                if v is None or not math.isfinite(float(v)): raise RuntimeError(f"DAILY_METRIC_UNDEFINED:{scenario}/{tid}/{day}/{metric}")
                target[metric].append(float(v))
    cols=["scenario_id","trial_id","date","source_sha","master_seed","Closing_Cash","Closing_Equity","Active_Bikes","Owned_Transferred_Bikes","Pending_Claims"]
    for path in (historical_path,extension_path):
        pf=pq.ParquetFile(path)
        for batch in pf.iter_batches(batch_size=50000,columns=cols): consume(batch.to_pylist())
    if sorted(bounds)!=tids: raise RuntimeError(f"DAILY_HISTORY_TRIAL_COVERAGE_MISMATCH:{scenario}")
    for tid,b in bounds.items():
        if (date.fromisoformat(b["last"])-date.fromisoformat(b["first"])).days+1!=b["count"]: raise RuntimeError(f"DAILY_HISTORY_GAP:{scenario}/{tid}")
        if closes[tid] is not None and str(closes[tid])!=b["last"]: raise RuntimeError(f"DAILY_FINAL_CLOSE_DATE_MISMATCH:{scenario}/{tid}")
    first=date.fromisoformat(min(grouped,key=date.fromisoformat)); last=date.fromisoformat(max(grouped,key=date.fromisoformat))
    expected_dates=[(first.fromordinal(first.toordinal()+i)).isoformat() for i in range((last-first).days+1)]
    if sorted(grouped,key=date.fromisoformat)!=expected_dates: raise RuntimeError(f"DAILY_DISTRIBUTION_DATE_GAP:{scenario}")
    out_rows=[]
    for day in expected_dates:
        dt=date.fromisoformat(day); active=[tid for tid in tids if closes[tid] is None or date.fromisoformat(str(closes[tid]))>=dt]
        if len(grouped[day]["Cash"])!=len(active): raise RuntimeError(f"DAILY_ACTIVE_TRIAL_COUNT_MISMATCH:{scenario}/{day}")
        for qname,q in QUANTILES:
            row={"scenario_id":scenario,"date":day,"quantile_name":qname,"active_trial_count":len(active),"source_sha":SOURCE_SHA,"master_seed":MASTER_SEED,"schema_version":SCHEMA_VERSION}
            for m in DAILY_METRICS: row[m]=linear_quantile(grouped[day][m],q)
            out_rows.append(row)
    schema=pa.schema([("scenario_id",pa.string()),("date",pa.string()),("quantile_name",pa.string()),("active_trial_count",pa.int64()),("source_sha",pa.string()),("master_seed",pa.int64()),("schema_version",pa.string()),("Cash",pa.float64()),("Net_Equity",pa.float64()),("Active_Bikes",pa.float64()),("Owned_Transferred_Bikes",pa.float64()),("Pending_Claims",pa.float64())],metadata={b"stage12.dataset_identity":json.dumps(_identity(scenario),sort_keys=True,separators=(",",":")).encode("utf-8")})
    out.parent.mkdir(parents=True,exist_ok=True); pq.write_table(pa.Table.from_pylist(out_rows,schema=schema),out,compression="zstd")
    return {"daily_distribution_rows":len(out_rows),"dates":len(expected_dates),"quantiles":len(QUANTILES),"rows_sha256":hashlib.sha256(out.read_bytes()).hexdigest()}

def run_scenario(scenario: str, historical_path: Path, audit_path: Path, trial_path: Path, out: Path) -> dict[str,Any]:
    expected_scenarios={f"C{c:03d}_G{g:03d}" for c in (100,85,70,50,30) for g in (100,70,50,30,0)}
    if scenario not in expected_scenarios: raise RuntimeError(f"UNSUPPORTED_SCENARIO:{scenario}")
    audit=_read_json(audit_path); source=_read_json(trial_path)
    if audit.get("status")!="READY_FOR_DETERMINISTIC_REPLAY": raise RuntimeError(f"SOURCE_READINESS_NOT_VERIFIED:{audit.get('status')}")
    if audit.get("dataset",{}).get("source_sha")!=SOURCE_SHA or audit.get("dataset",{}).get("master_seed")!=MASTER_SEED: raise RuntimeError("SOURCE_READINESS_IDENTITY_MISMATCH")
    records=source.get("scenarios",{}).get(scenario)
    if not isinstance(records,list): raise RuntimeError(f"TRIAL_RESULTS_SCENARIO_MISSING:{scenario}")
    by_id={int(r["trial_id"]):r for r in records}; expected_src=[1] if scenario.startswith("C100_") else list(range(1,1201))
    if sorted(by_id)!=expected_src or len(by_id)!=len(expected_src): raise RuntimeError(f"TRIAL_RESULTS_COVERAGE_MISMATCH:{scenario}")
    for tid,row in by_id.items(): _check_trial_source_row(row,scenario,tid)
    hist_audit=_validate_historical_daily(historical_path,scenario)
    selected=audit["representative_roles"]["selection_by_n1200_source"][scenario]["selected_roles"]
    labels={"P10":"P10","P50":"P50","P90":"P90","LossCase":"Loss","MaxCase":"Max Case"}
    roles_by_id:dict[int,list[str]]={}
    for role,label in labels.items():
        tid=int(selected[role])
        if tid not in by_id: raise RuntimeError(f"REPRESENTATIVE_TRIAL_ID_NOT_IN_SOURCE:{scenario}/{role}/{tid}")
        roles_by_id.setdefault(tid,[]).append(label)
    primary=set(range(2,1201)) if scenario.startswith("C100_") else set(range(551,1201))
    replay_ids=sorted(primary|set(roles_by_id))
    provider=GoldenReferenceProvider()
    if provider.load_error is not None or not provider.verify_source_identity(SOURCE_SHA) or provider.master_seed!=MASTER_SEED: raise RuntimeError(f"GOLDEN_PROVIDER_NOT_VALID:{provider.load_error}")
    if not scenario.startswith("C100_") and provider.get_coverage(scenario)!=set(range(1,1201)): raise RuntimeError(f"GOLDEN_PROVIDER_COVERAGE_MISMATCH:{scenario}")
    out.mkdir(parents=True,exist_ok=True); reps=out/"representatives"; reps.mkdir(parents=True,exist_ok=True)
    ext=out/"daily_accounting_extension.parquet"; schema=_daily_schema(scenario)
    hashes:dict[int,str]={}; replayed:dict[int,dict[str,Any]]={}; ext_rows=0; rep_tids=[]
    baseline=by_id[1]["trial_result"] if scenario.startswith("C100_") else None
    with pq.ParquetWriter(ext,schema,compression="zstd") as writer:
        for tid in replay_ids:
            cp,recovery=monte_carlo.parse_scenario_id(scenario)
            daily=[]; partner=[]; meta=[]
            def capture(project:Any, day:date) -> None: _capture_day(daily,partner,project,day,tid,meta)
            detail=tid in roles_by_id
            project=daily_engine.run_deterministic_trial(recovery_rate_pct=recovery,trial_id=tid,scenario_id=scenario,master_seed=MASTER_SEED,collection_probability=cp,on_day_end=capture,log_events=detail)
            result=monte_carlo._trial_result_from_project(project,scenario_id=scenario,collection_probability=cp,recovery_rate_pct=recovery,trial_id=tid)
            sha=stage10_trial_result_sha256(result)
            if scenario.startswith("C100_"):
                if business_result_projection(asdict(result))!=business_result_projection(baseline): raise RuntimeError(f"C100_BUSINESS_RESULT_MISMATCH:{scenario}/{tid}")
            else:
                expected=provider.get_fingerprint(scenario,tid)
                if expected is None or sha!=expected: raise RuntimeError(f"GOLDEN_REPLAY_FINGERPRINT_MISMATCH:{scenario}/{tid}")
            hashes[tid]=sha; replayed[tid]=_jsonable(result)
            if tid in primary:
                rows=_accounting_rows(project,scenario,tid,sha,meta); table=pa.Table.from_pylist(rows,schema=schema)
                if table.num_rows==0: raise RuntimeError(f"EMPTY_REPLAY_DAILY_HISTORY:{scenario}/{tid}")
                writer.write_table(table); ext_rows+=table.num_rows
            if detail:
                close=project.final_close_date.isoformat() if project.final_close_date else None
                for d in daily: d["Final_Close_Date"]=close
                payload=_representative_payload(project,result,daily,partner)
                required={"summary","daily","partner_memo","accounting","assets","final_inventory","contracts","guarantee_claims","event_log","final_reconciliation"}
                if required-set(payload) or not payload["daily"] or payload["summary"].get("trial_id")!=tid: raise RuntimeError(f"REPRESENTATIVE_PAYLOAD_CONTRACT_FAIL:{scenario}/{tid}")
                for label in roles_by_id[tid]:
                    (reps/f"{label}.json").write_text(json.dumps(payload,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n",encoding="utf-8")
                rep_tids.append(tid)
            del project,result,daily,partner,meta
    if sorted(hashes)!=replay_ids: raise RuntimeError(f"REPLAY_TRIAL_COVERAGE_FAIL:{scenario}")
    wanted={"P10.json","P50.json","P90.json","Loss.json","Max Case.json"}
    actual={p.name for p in reps.glob("*.json")}
    if actual!=wanted: raise RuntimeError(f"REPRESENTATIVE_ROLE_FILE_COVERAGE_FAIL:{scenario}:{sorted(actual)}")
    all_rows=dict(by_id); all_rows.update(replayed)
    if sorted(all_rows)!=list(range(1,1201)): raise RuntimeError(f"FULL_DELIVERY_TRIAL_RESULTS_INCOMPLETE:{scenario}")
    results=[all_rows[i]["trial_result"] if isinstance(all_rows[i],dict) and "trial_result" in all_rows[i] else all_rows[i] for i in range(1,1201)]
    dist=_daily_distribution(historical_path,ext,results,scenario,out/"daily_distribution.parquet")
    manifest={
        "manifest_version":"cp-f-deterministic-replay-v1","status":"PASS","scenario":scenario,"source_sha":SOURCE_SHA,"master_seed":MASTER_SEED,
        "rng":"pinned source rng.py; no changes","sampling":"delivery-only replay of pre-approved trial IDs; not a new statistical cohort","schema_version":SCHEMA_VERSION,
        "reference_daily_run_id":REFERENCE_RUN_ID,"historical_daily_trials":hist_audit["trial_count"],"historical_daily_rows":hist_audit["rows"],"historical_daily_sha256":hist_audit["sha256"],
        "extension_trial_ids":sorted(primary),"extension_trial_count":len(primary),"detail_replay_trial_ids":sorted(roles_by_id),"replayed_trial_ids":replay_ids,"replayed_trial_count":len(replay_ids),
        "non_c100_gate_a_fingerprints_verified":not scenario.startswith("C100_"),"c100_business_results_verified_against_trial_1":scenario.startswith("C100_"),
        "trial_fingerprints":{str(k):hashes[k] for k in sorted(hashes)},"representative_trial_ids":{k:int(v) for k,v in selected.items()},
        "representative_payload_files":sorted(actual),"representative_payload_trial_ids":sorted(rep_tids),"daily_accounting_extension_rows":ext_rows,
        "daily_accounting_extension_sha256":hashlib.sha256(ext.read_bytes()).hexdigest(),"daily_distribution":dist,
        "historical_dataset_modified":False,"historical_parquet_modified":False,"production_monte_carlo_run":False,"source_sha_bumped":False,"main_modified":False,"release_created":False,
    }
    (out/"scenario_manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return manifest

def verify_cohort(root: Path) -> dict[str,Any]:
    expected={f"C{c:03d}_G{g:03d}" for c in (100,85,70,50,30) for g in (100,70,50,30,0)}; found={}
    for path in root.glob("cp-f-replay-*/scenario_manifest.json"):
        m=_read_json(path); scenario=m.get("scenario")
        if scenario in found or m.get("status")!="PASS" or m.get("source_sha")!=SOURCE_SHA or int(m.get("master_seed",-1))!=MASTER_SEED: raise RuntimeError(f"SCENARIO_REPLAY_MANIFEST_INVALID:{scenario}")
        base=path.parent; ext=base/"daily_accounting_extension.parquet"; dist=base/"daily_distribution.parquet"; reps=base/"representatives"
        if not ext.is_file() or not dist.is_file() or {p.name for p in reps.glob("*.json")}!={"P10.json","P50.json","P90.json","Loss.json","Max Case.json"}: raise RuntimeError(f"SCENARIO_DELIVERY_ARTIFACT_MISSING:{scenario}")
        erows=pq.read_table(ext,columns=["scenario_id","trial_id","source_sha","master_seed"]).to_pylist(); ids=sorted({int(r["trial_id"]) for r in erows})
        eids=list(range(2,1201)) if scenario.startswith("C100_") else list(range(551,1201))
        if ids!=eids or any(r["scenario_id"]!=scenario or r["source_sha"]!=SOURCE_SHA or int(r["master_seed"])!=MASTER_SEED for r in erows): raise RuntimeError(f"COHORT_EXTENSION_IDENTITY_OR_RANGE_MISMATCH:{scenario}")
        drows=pq.read_table(dist,columns=["date","quantile_name","source_sha","master_seed"]).to_pylist(); days={r["date"] for r in drows}
        if not drows or len(drows)!=len(days)*5 or {r["quantile_name"] for r in drows}!={q[0] for q in QUANTILES} or any(r["source_sha"]!=SOURCE_SHA or int(r["master_seed"])!=MASTER_SEED for r in drows): raise RuntimeError(f"COHORT_DAILY_DISTRIBUTION_SHAPE_OR_IDENTITY_MISMATCH:{scenario}")
        found[scenario]={"manifest_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),"extension_trials":len(ids),"extension_rows":len(erows),"daily_distribution_rows":len(drows),"dates":len(days),"representative_roles":5,"daily_distribution_sha256":m["daily_distribution"]["rows_sha256"]}
    if set(found)!=expected: raise RuntimeError(f"COHORT_SCENARIO_COVERAGE_MISMATCH:missing={sorted(expected-set(found))}:extra={sorted(set(found)-expected)}")
    summary={"manifest_version":"cp-f-replay-cohort-v1","status":"PASS","scenario_count":len(found),"source_sha":SOURCE_SHA,"master_seed":MASTER_SEED,"non_c100_replay_trial_histories":13000,"c100_replay_trial_histories":5995,"total_primary_daily_replay_histories":18995,"scenario_evidence":found,"historical_dataset_modified":False,"historical_parquet_modified":False,"production_monte_carlo_run":False,"main_modified":False,"source_sha_bumped":False,"release_created":False}
    (root/"CP_F_REPLAY_COHORT_VALIDATION.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return summary

def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser(); p.add_argument("--scenario"); p.add_argument("--historical-parquet"); p.add_argument("--audit"); p.add_argument("--trial-results"); p.add_argument("--output-dir"); p.add_argument("--verify-cohort-root"); a=p.parse_args(argv)
    if a.verify_cohort_root: result=verify_cohort(Path(a.verify_cohort_root))
    else:
        req=(a.scenario,a.historical_parquet,a.audit,a.trial_results,a.output_dir)
        if any(not x for x in req): p.error("scenario mode requires --scenario --historical-parquet --audit --trial-results --output-dir")
        result=run_scenario(a.scenario,Path(a.historical_parquet),Path(a.audit),Path(a.trial_results),Path(a.output_dir))
    print(json.dumps(result,ensure_ascii=False,sort_keys=True)); return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(f"CP_F_REPLAY_FAILURE: {type(exc).__name__}: {exc}",file=sys.stderr); raise
