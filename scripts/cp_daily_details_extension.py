#!/usr/bin/env python3
"""Delivery-only deterministic replay for missing Stage 12 daily/detail outputs."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import sys
import shutil
import re
import os
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
from scripts.golden_reference_provider import APPROVED_SOURCE_SHA, APPROVED_SOURCE_COMMIT, MASTER_SEED, GoldenReferenceProvider, _ordered_map_sha256, stage10_trial_result_sha256

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
    for batch in pf.iter_batches(batch_size=50000, columns=["scenario_id","trial_id","date","source_sha","master_seed","Balance_Difference"]):
        for r in batch.to_pylist():
            rows+=1
            if r.get("scenario_id")!=scenario or r.get("source_sha")!=SOURCE_SHA or int(r.get("master_seed",-1))!=MASTER_SEED:
                raise RuntimeError(f"HISTORICAL_DAILY_ROW_IDENTITY_MISMATCH:{scenario}")
            if r.get("Balance_Difference") is None or int(r["Balance_Difference"]) != 0:
                raise RuntimeError(f"HISTORICAL_BALANCE_DIFFERENCE_NONZERO:{scenario}/{r.get('trial_id')}/{r.get('date')}")
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

def _daily_distribution(historical_path: Path, prior_extension_path: Path, extension_path: Path, result_rows: list[dict[str,Any]], scenario: str, out: Path) -> dict[str,Any]:
    closes={int(r["trial_id"]):r.get("final_close_date") for r in result_rows}
    tids=list(range(1,2401))
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
    for path in (historical_path,prior_extension_path,extension_path):
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


TARGET_SCENARIO = "C030_G030"
N1200_RUN_ID = 38619859394
N1200_SOURCE_ARTIFACT_ID = 11921491181
N1200_SOURCE_ARCHIVE_SHA256 = "694460ed60bf092f1b2fb431cdfae538dd0a584b1cc5d655488263d348dae29e"
PRIOR_REPLAY_RUN_ID = 38619859394
PRIOR_REPLAY_ARTIFACT_ID = 11922303249
PRIOR_REPLAY_ARCHIVE_SHA256 = "fff34ded9a85da5f0340cc98e089bd6d66cc9af2ecd28ce35f93f64293b0660d"
PRIOR_MANIFEST_SHA256 = "5e1890e519e6853bb6f72f484517d4d5edb5ddcff88078af6c4a55eb2db2bbd3"
PRIOR_EXTENSION_SHA256 = "21089e3ae6759da17324ca0903d968b6d64d91715fd7067da7b6576cdc4be0da"
PRIOR_EXTENSION_ROWS = 1_014_976
PRIOR_DISTRIBUTION_SHA256 = "83d93319e553f9680fec75ab9b21e96184182d3a0aee45246cbe0018d7861296"
N2400_RUN_ID = 38783578243
N2400_ARTIFACT_ID = 11997801781
N2400_ARCHIVE_SHA256 = "22af149504b242d98e155112e7d098af75a72e0d802f0e7bda742029d207fc76"
N2400_TESTED_HEAD_SHA = "ab0dfa53efade5951118ebcee50460699090835b"
N2400_JSONL_SHA256 = "4d430f4ad9482bb0ade414ea6ec773aafc5ae47375c30de0399d743cdbf0f255"
N1200_MAP_SHA256 = "eaf1f8f3060aac6967b064d3199c082d2a9b47027c865628986f56cbb23c1fc3"
COMBINED_PROVIDER_MAP_SHA256 = "0fbe3aa87a253f9527953c77b0a122871c9344f75ece6c8a49da99b2a85c1ce1"
N2400_TARGET_MAP_SHA256 = "1ef2bc78622a5b8b83639290bfcf38ac8438b00f1d2a986c55595789511e60c7"
EXPECTED_HISTORICAL_ROWS = 859_478
EXPECTED_HISTORICAL_SHA256 = "2b95f26624abb6c4f3a7145e457c3f2f8764a9d037e2de326a9dd768d42d40c9"
EXPECTED_TOTAL_TRIALS = 2400

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def validate_trial_id_coverage(actual_ids: list[int], expected_ids: list[int], code: str) -> None:
    normalized = [int(value) for value in actual_ids]
    if len(normalized) != len(set(normalized)) or sorted(normalized) != expected_ids:
        raise RuntimeError(f"{code}:count={len(normalized)}:unique={len(set(normalized))}:first={sorted(set(normalized))[:5]}:last={sorted(set(normalized))[-5:]}")

def _validate_n2400_record(row: dict[str, Any], *, trial_id: int, provider: GoldenReferenceProvider) -> dict[str, Any]:
    scenario = TARGET_SCENARIO
    if row.get("scenario_id") != scenario or int(row.get("trial_id", -1)) != trial_id:
        raise RuntimeError(f"N2400_TRIAL_KEY_MISMATCH:{trial_id}")
    if row.get("source_sha") != SOURCE_SHA or int(row.get("master_seed", -1)) != MASTER_SEED:
        raise RuntimeError(f"N2400_SOURCE_IDENTITY_MISMATCH:{trial_id}")
    if row.get("source_commit") != APPROVED_SOURCE_COMMIT:
        raise RuntimeError(f"N2400_PINNED_SOURCE_COMMIT_MISMATCH:{trial_id}")
    if int(row.get("run_id", -1)) != N2400_RUN_ID or int(row.get("run_attempt", -1)) != 1:
        raise RuntimeError(f"N2400_RUN_PROVENANCE_MISMATCH:{trial_id}")
    if row.get("tested_head_sha") != N2400_TESTED_HEAD_SHA:
        raise RuntimeError(f"N2400_TESTED_HEAD_MISMATCH:{trial_id}")
    if row.get("exact_golden_match") is not True:
        raise RuntimeError(f"N2400_PRIOR_GOLDEN_MATCH_NOT_TRUE:{trial_id}")
    result = row.get("trial_result")
    if not isinstance(result, dict) or result.get("scenario_id") != scenario or int(result.get("trial_id", -1)) != trial_id:
        raise RuntimeError(f"N2400_TRIAL_PAYLOAD_KEY_MISMATCH:{trial_id}")
    actual_hash = stage10_trial_result_sha256(result)
    expected_hash = provider.get_fingerprint(scenario, trial_id)
    if row.get("result_sha256") != actual_hash or row.get("approved_golden_sha256") != actual_hash or expected_hash != actual_hash:
        raise RuntimeError(f"N2400_PRIOR_RESULT_OR_GOLDEN_HASH_MISMATCH:{trial_id}")
    return {"scenario_id": scenario, "trial_id": trial_id, "source_sha": SOURCE_SHA,
            "master_seed": MASTER_SEED, "result_sha256": actual_hash, "trial_result": result}

def _validate_daily_segment(path: Path, *, scenario: str, expected_ids: list[int],
                            expected_sha256: str, expected_rows: int | None = None,
                            close_dates: dict[int, Any] | None = None) -> dict[str, Any]:
    if _sha256_file(path) != expected_sha256:
        raise RuntimeError(f"DAILY_SEGMENT_FILE_SHA256_MISMATCH:{path.name}")
    parquet = pq.ParquetFile(path)
    if parquet.schema_arrow.names != [name for name, _ in DAILY_FIELDS]:
        raise RuntimeError(f"DAILY_SEGMENT_SCHEMA_COLUMNS_MISMATCH:{path.name}")
    raw_identity = (parquet.schema_arrow.metadata or {}).get(b"stage12.dataset_identity")
    if raw_identity is None or json.loads(raw_identity.decode("utf-8")) != _identity(scenario):
        raise RuntimeError(f"DAILY_SEGMENT_SCHEMA_IDENTITY_MISMATCH:{path.name}")
    seen: list[int] = []
    current_tid: int | None = None
    previous_date: date | None = None
    count_for_trial = rows_count = 0
    for batch in parquet.iter_batches(batch_size=50000, columns=[
        "scenario_id", "trial_id", "date", "source_sha", "master_seed", "Balance_Difference"
    ]):
        for row in batch.to_pylist():
            rows_count += 1
            if (row.get("scenario_id") != scenario or row.get("source_sha") != SOURCE_SHA
                    or int(row.get("master_seed", -1)) != MASTER_SEED):
                raise RuntimeError(f"DAILY_SEGMENT_ROW_IDENTITY_MISMATCH:{path.name}")
            if row.get("Balance_Difference") is None or int(row["Balance_Difference"]) != 0:
                raise RuntimeError(f"DAILY_SEGMENT_BALANCE_DIFFERENCE_NONZERO:{path.name}/{row.get('trial_id')}/{row.get('date')}")
            tid, day = int(row["trial_id"]), date.fromisoformat(str(row["date"]))
            if tid != current_tid:
                if current_tid is not None:
                    if previous_date is None or count_for_trial < 1:
                        raise RuntimeError(f"DAILY_SEGMENT_EMPTY_TRIAL:{path.name}/{current_tid}")
                    if close_dates and close_dates.get(current_tid) is not None and str(close_dates[current_tid]) != previous_date.isoformat():
                        raise RuntimeError(f"DAILY_SEGMENT_CLOSE_DATE_MISMATCH:{path.name}/{current_tid}")
                if current_tid is not None and tid <= current_tid:
                    raise RuntimeError(f"DAILY_SEGMENT_TRIAL_ORDER_INVALID:{path.name}/{tid}")
                seen.append(tid); current_tid = tid; previous_date = day; count_for_trial = 1
            else:
                if previous_date is None or (day - previous_date).days != 1:
                    raise RuntimeError(f"DAILY_SEGMENT_DATE_GAP_OR_DUPLICATE:{path.name}/{tid}/{day}")
                previous_date = day; count_for_trial += 1
    if current_tid is not None and close_dates and close_dates.get(current_tid) is not None:
        if previous_date is None or str(close_dates[current_tid]) != previous_date.isoformat():
            raise RuntimeError(f"DAILY_SEGMENT_CLOSE_DATE_MISMATCH:{path.name}/{current_tid}")
    if seen != expected_ids:
        raise RuntimeError(f"DAILY_SEGMENT_TRIAL_COVERAGE_MISMATCH:{path.name}:expected={len(expected_ids)}:actual={len(seen)}:first={seen[:3]}:last={seen[-3:]}")
    if expected_rows is not None and rows_count != expected_rows:
        raise RuntimeError(f"DAILY_SEGMENT_ROW_COUNT_MISMATCH:{path.name}:expected={expected_rows}:actual={rows_count}")
    if rows_count <= 0:
        raise RuntimeError(f"DAILY_SEGMENT_EMPTY:{path.name}")
    return {"status": "PASS", "trial_count": len(seen), "first_trial_id": seen[0], "last_trial_id": seen[-1],
            "rows": rows_count, "sha256": expected_sha256, "nonzero_balance_difference_rows": 0}

def _verify_distribution_file(path: Path, scenario: str, closes: dict[int, Any]) -> dict[str, Any]:
    parquet = pq.ParquetFile(path)
    table = pq.read_table(path)
    raw_identity = (parquet.schema_arrow.metadata or {}).get(b"stage12.dataset_identity")
    if raw_identity is None or json.loads(raw_identity.decode("utf-8")) != _identity(scenario):
        raise RuntimeError("DAILY_DISTRIBUTION_SCHEMA_IDENTITY_MISMATCH")
    rows = table.to_pylist()
    if not rows:
        raise RuntimeError("DAILY_DISTRIBUTION_EMPTY")
    days = sorted({str(row["date"]) for row in rows})
    if len(rows) != len(days) * len(QUANTILES):
        raise RuntimeError(f"DAILY_DISTRIBUTION_QUANTILE_ROW_COUNT_MISMATCH:{len(rows)}:{len(days)}")
    expected_names = {name for name, _ in QUANTILES}
    for day in days:
        items = [row for row in rows if str(row["date"]) == day]
        if {row["quantile_name"] for row in items} != expected_names or len(items) != len(QUANTILES):
            raise RuntimeError(f"DAILY_DISTRIBUTION_QUANTILE_COVERAGE_MISMATCH:{day}")
        active = sum(1 for close in closes.values() if close is None or date.fromisoformat(str(close)) >= date.fromisoformat(day))
        for row in items:
            if row.get("scenario_id") != scenario or row.get("source_sha") != SOURCE_SHA or int(row.get("master_seed", -1)) != MASTER_SEED:
                raise RuntimeError(f"DAILY_DISTRIBUTION_ROW_IDENTITY_MISMATCH:{day}")
            if int(row.get("active_trial_count", -1)) != active:
                raise RuntimeError(f"DAILY_DISTRIBUTION_ACTIVE_TRIAL_COUNT_MISMATCH:{day}")
            for metric in DAILY_METRICS:
                if row.get(metric) is None or not math.isfinite(float(row[metric])):
                    raise RuntimeError(f"DAILY_DISTRIBUTION_METRIC_NONFINITE:{day}/{metric}")
        qmap = {row["quantile_name"]: row for row in items}
        ordered = sorted(QUANTILES, key=lambda item: item[1])
        for left, right in zip(ordered, ordered[1:]):
            for metric in DAILY_METRICS:
                if float(qmap[left[0]][metric]) > float(qmap[right[0]][metric]):
                    raise RuntimeError(f"DAILY_DISTRIBUTION_QUANTILE_ORDER_INVALID:{day}/{metric}")
    return {"status": "PASS", "rows": len(rows), "dates": len(days), "quantiles_per_date": len(QUANTILES),
            "sha256": _sha256_file(path), "schema_identity_checked": True, "finite_metrics_checked": len(rows) * len(DAILY_METRICS)}

def _combine_representative_audit_statuses(statuses: list[str]) -> str:
    """Fail closed: a proven failure outranks missing evidence; PASS requires every check."""
    if any(status == "FAIL" for status in statuses):
        return "FAIL"
    if statuses and all(status == "PASS" for status in statuses):
        return "PASS"
    return "NOT_VERIFIABLE"


def _audit_representative_balance_checks(payload: Any) -> dict[str, Any]:
    """Verify the accounting balance ledger attached to one representative payload.

    Raw daily rows and accounting.daily_balance_checks are distinct parts of the
    existing representative schema. Empty/missing/malformed evidence is never PASS.
    """
    reasons: set[str] = set()
    failures: list[dict[str, Any]] = []
    daily = payload.get("daily") if isinstance(payload, dict) else None
    accounting = payload.get("accounting") if isinstance(payload, dict) else None
    checks = accounting.get("daily_balance_checks") if isinstance(accounting, dict) else None
    summary = payload.get("summary") if isinstance(payload, dict) else None

    daily_count = len(daily) if isinstance(daily, list) else 0
    check_count = len(checks) if isinstance(checks, list) else 0
    numeric_checks = 0
    verified_checks = 0
    nonzero_balance_difference_rows = 0
    assets_equity_mismatch_rows = 0
    difference_formula_mismatch_rows = 0

    if not isinstance(daily, list) or not daily:
        reasons.add("DAILY_ROWS_MISSING_OR_EMPTY")
    if not isinstance(accounting, dict):
        reasons.add("ACCOUNTING_SECTION_MISSING_OR_INVALID")
    if not isinstance(checks, list) or not checks:
        reasons.add("DAILY_BALANCE_CHECKS_MISSING_OR_EMPTY")
    if not isinstance(summary, dict) or not isinstance(summary.get("final_close_date"), str):
        reasons.add("SUMMARY_FINAL_CLOSE_DATE_MISSING_OR_INVALID")

    expected_close = None
    if isinstance(summary, dict) and isinstance(summary.get("final_close_date"), str):
        try:
            expected_close = date.fromisoformat(summary["final_close_date"])
        except (TypeError, ValueError):
            reasons.add("SUMMARY_FINAL_CLOSE_DATE_INVALID")

    if isinstance(daily, list) and daily:
        parsed_dates: list[date] = []
        for row in daily:
            if not isinstance(row, dict) or not isinstance(row.get("date"), str):
                reasons.add("DAILY_DATE_MISSING_OR_INVALID")
                continue
            try:
                parsed_dates.append(date.fromisoformat(row["date"]))
            except (TypeError, ValueError):
                reasons.add("DAILY_DATE_MISSING_OR_INVALID")
        if len(parsed_dates) == len(daily):
            if parsed_dates[0] != date(2027, 1, 1):
                reasons.add("DAILY_START_DATE_MISMATCH")
            if any((right - left).days != 1 for left, right in zip(parsed_dates, parsed_dates[1:])):
                reasons.add("DAILY_DATE_SEQUENCE_INVALID")
            if expected_close is not None and parsed_dates[-1] != expected_close:
                reasons.add("DAILY_FINAL_DATE_MISMATCH")

    if isinstance(daily, list) and isinstance(checks, list) and len(checks) != len(daily):
        reasons.add("DAILY_BALANCE_CHECK_COUNT_MISMATCH")

    required = {"Total_Assets", "Total_Equity", "Balance_Difference"}
    if isinstance(checks, list):
        for index, row in enumerate(checks):
            if not isinstance(row, dict):
                reasons.add("BALANCE_CHECK_ROW_INVALID")
                continue
            if required - set(row):
                reasons.add("BALANCE_CHECK_FIELDS_MISSING")
                continue
            values = [row.get("Total_Assets"), row.get("Total_Equity"), row.get("Balance_Difference")]
            if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
                reasons.add("BALANCE_CHECK_VALUES_INVALID")
                continue
            numeric_checks += 1
            assets, equity, difference = values
            row_failures: list[str] = []
            if assets != equity:
                assets_equity_mismatch_rows += 1
                row_failures.append("ASSETS_NOT_EQUAL_EQUITY")
            if difference != 0:
                nonzero_balance_difference_rows += 1
                row_failures.append("BALANCE_DIFFERENCE_NONZERO")
            if difference != assets - equity:
                difference_formula_mismatch_rows += 1
                row_failures.append("BALANCE_DIFFERENCE_FORMULA_MISMATCH")
            if row_failures:
                daily_row = daily[index] if isinstance(daily, list) and index < len(daily) else None
                failures.append({
                    "index": index,
                    "date": daily_row.get("date") if isinstance(daily_row, dict) else None,
                    "failure_codes": sorted(set(row_failures)),
                    "Total_Assets": assets,
                    "Total_Equity": equity,
                    "Balance_Difference": difference,
                })
            elif index < daily_count:
                verified_checks += 1

    if failures:
        status = "FAIL"
    elif reasons:
        status = "NOT_VERIFIABLE"
    else:
        status = "PASS"
    return {
        "status": status,
        "daily_row_count": daily_count,
        "balance_checks": check_count,
        "numeric_balance_checks": numeric_checks,
        "verified_balance_checks": verified_checks,
        "nonzero_balance_difference_rows": nonzero_balance_difference_rows,
        "assets_equity_mismatch_rows": assets_equity_mismatch_rows,
        "difference_formula_mismatch_rows": difference_formula_mismatch_rows,
        "failure_count": len(failures),
        "failures": failures[:25],
        "reason_codes": sorted(reasons),
    }


def _audit_prior_representatives(representative_dir: Path, prior_manifest: dict[str, Any],
                                 provider: GoldenReferenceProvider) -> dict[str, Any]:
    required = {"P10.json", "P50.json", "P90.json", "Loss.json", "Max Case.json"}
    found = {path.name for path in representative_dir.glob("*.json")}
    if found != required:
        raise RuntimeError(f"PRIOR_REPRESENTATIVE_FILE_COVERAGE_MISMATCH:{sorted(found)}")
    roles = {"P10.json": "P10", "P50.json": "P50", "P90.json": "P90", "Loss.json": "LossCase", "Max Case.json": "MaxCase"}
    selected, hashes = prior_manifest.get("representative_trial_ids", {}), prior_manifest.get("trial_fingerprints", {})
    evidence = {}
    for filename, role in roles.items():
        path = representative_dir / filename
        payload = _read_json(path)
        if not isinstance(payload, dict):
            raise RuntimeError(f"PRIOR_REPRESENTATIVE_PAYLOAD_INVALID:{filename}")
        summary = payload.get("summary")
        if not isinstance(summary, dict):
            raise RuntimeError(f"PRIOR_REPRESENTATIVE_SUMMARY_MISSING:{filename}")
        tid = int(summary.get("trial_id", -1))
        if tid != int(selected.get(role, -2)) or summary.get("scenario_id") != TARGET_SCENARIO:
            raise RuntimeError(f"PRIOR_REPRESENTATIVE_ROLE_IDENTITY_MISMATCH:{filename}")
        digest = stage10_trial_result_sha256(summary)
        if digest != hashes.get(str(tid)) or digest != provider.get_fingerprint(TARGET_SCENARIO, tid):
            raise RuntimeError(f"PRIOR_REPRESENTATIVE_GOLDEN_MISMATCH:{filename}/{tid}")
        balance_audit = _audit_representative_balance_checks(payload)
        evidence[filename] = {
            "trial_id": tid, "role": role, "bytes": path.stat().st_size,
            "sha256": _sha256_file(path), "golden_fingerprint": digest,
            "daily_row_count": balance_audit["daily_row_count"],
            "balance_checks": balance_audit["balance_checks"],
            "balance_audit": balance_audit,
        }
    overall_status = _combine_representative_audit_statuses(
        [item["balance_audit"]["status"] for item in evidence.values()]
    )
    return {"status": overall_status, "role_count": len(evidence), "files": evidence,
            "provenance": {"run_id": PRIOR_REPLAY_RUN_ID, "artifact_id": PRIOR_REPLAY_ARTIFACT_ID,
                           "artifact_sha256": PRIOR_REPLAY_ARCHIVE_SHA256}}

def _validate_preflight(source_report_path: Path, provider_report_path: Path,
                        provider: GoldenReferenceProvider) -> dict[str, Any]:
    source_report, provider_report = _read_json(source_report_path), _read_json(provider_report_path)
    if (source_report.get("status") != "PASS" or source_report.get("source_sha") != SOURCE_SHA
            or source_report.get("candidate_without_adapter_sha256") != source_report.get("pinned_daily_engine_sha256")
            or source_report.get("source_sha_bumped") is not False
            or source_report.get("historical_dataset_modified") is not False
            or source_report.get("parquet_modified") is not False):
        raise RuntimeError("SOURCE_IDENTITY_EXCEPTION_PREFLIGHT_NOT_PASS")
    if (provider_report.get("status") != "PASS" or provider_report.get("source_sha") != SOURCE_SHA
            or int(provider_report.get("master_seed", -1)) != MASTER_SEED
            or int(provider_report.get("scenario_count", -1)) != 25
            or int(provider_report.get("trial_count", -1)) != 25205
            or provider_report.get("source_map_sha256") != COMBINED_PROVIDER_MAP_SHA256):
        raise RuntimeError("GOLDEN_PROVIDER_FULL_COVERAGE_PREFLIGHT_NOT_PASS")
    if (provider.load_error is not None or not provider.verify_source_identity(SOURCE_SHA)
            or provider.master_seed != MASTER_SEED or provider.source_map_sha256 != COMBINED_PROVIDER_MAP_SHA256):
        raise RuntimeError(f"GOLDEN_PROVIDER_IDENTITY_OR_MAP_MISMATCH:{provider.load_error}")
    coverage = provider.get_coverage(TARGET_SCENARIO)
    if coverage != set(range(1, EXPECTED_TOTAL_TRIALS + 1)):
        raise RuntimeError(f"GOLDEN_TARGET_SCENARIO_COVERAGE_MISMATCH:{len(coverage)}")
    return {"status": "PASS", "source_identity_report_sha256": _sha256_file(source_report_path),
            "provider_preflight_report_sha256": _sha256_file(provider_report_path),
            "provider_map_sha256": provider.source_map_sha256, "provider_trial_count": provider.trial_count,
            "target_scenario_trial_count": len(coverage)}

def run_c030_daily_extension(*, historical_path: Path, prior_extension_path: Path,
    prior_manifest_path: Path, prior_representatives_dir: Path, n1200_audit_path: Path,
    n1200_results_path: Path, n2400_report_path: Path, n2400_results_path: Path,
    source_identity_report_path: Path, provider_preflight_report_path: Path, out: Path) -> dict[str, Any]:
    scenario = TARGET_SCENARIO
    out.mkdir(parents=True, exist_ok=True)
    evidence_dir = out / "evidence"; evidence_dir.mkdir(parents=True, exist_ok=True)
    provider = GoldenReferenceProvider()
    preflight = _validate_preflight(source_identity_report_path, provider_preflight_report_path, provider)

    audit, source = _read_json(n1200_audit_path), _read_json(n1200_results_path)
    if audit.get("status") != "READY_FOR_DETERMINISTIC_REPLAY":
        raise RuntimeError(f"N1200_SOURCE_READINESS_NOT_READY:{audit.get('status')}")
    dataset = audit.get("dataset", {})
    if (dataset.get("source_sha") != SOURCE_SHA or int(dataset.get("master_seed", -1)) != MASTER_SEED
            or dataset.get("source_commit_for_new_trials") != APPROVED_SOURCE_COMMIT
            or dataset.get("schema_version") != SCHEMA_VERSION
            or dataset.get("n1200_ordered_trial_hash_map_sha256") != N1200_MAP_SHA256):
        raise RuntimeError("N1200_SOURCE_AUDIT_IDENTITY_OR_HASH_MAP_MISMATCH")
    if source.get("source_sha") != SOURCE_SHA or int(source.get("master_seed", -1)) != MASTER_SEED:
        raise RuntimeError("N1200_RESULT_SET_SOURCE_IDENTITY_MISMATCH")
    base_records = source.get("scenarios", {}).get(scenario)
    if not isinstance(base_records, list):
        raise RuntimeError("N1200_TARGET_SCENARIO_RESULTS_MISSING")
    validate_trial_id_coverage([int(r.get("trial_id", -1)) for r in base_records], list(range(1, 1201)), "N1200_TARGET_TRIAL_COVERAGE_FAIL")
    all_results: dict[int, dict[str, Any]] = {}
    for row in base_records:
        tid = int(row["trial_id"]); _check_trial_source_row(row, scenario, tid)
        payload = row["trial_result"]; digest = stage10_trial_result_sha256(payload)
        if row.get("result_sha256") != digest or provider.get_fingerprint(scenario, tid) != digest:
            raise RuntimeError(f"N1200_TARGET_RESULT_OR_GOLDEN_MISMATCH:{tid}")
        all_results[tid] = {"trial_id": tid, "trial_result": payload, "result_sha256": digest}

    report = _read_json(n2400_report_path)
    if (int(report.get("checkpoint_run_id", -1)) != N2400_RUN_ID
            or report.get("checkpoint_status") != "PASS_AT_N2400_ONLY"
            or report.get("target_scenario") != scenario or report.get("source_sha") != SOURCE_SHA
            or int(report.get("master_seed", -1)) != MASTER_SEED
            or report.get("pinned_source_commit") != APPROVED_SOURCE_COMMIT
            or report.get("trial_id_start") != 1201 or report.get("trial_id_end") != 2400
            or report.get("new_trial_ids") != "1201..2400"
            or report.get("checkpoint_workflow_head_sha") != N2400_TESTED_HEAD_SHA):
        raise RuntimeError("N2400_CHECKPOINT_REPORT_IDENTITY_MISMATCH")
    if report.get("approved_artifact_provenance", {}).get("provider_combined_map_sha256") != COMBINED_PROVIDER_MAP_SHA256:
        raise RuntimeError("N2400_CHECKPOINT_PROVIDER_MAP_PROVENANCE_MISMATCH")
    gate_a = report.get("gate_a", {})
    if (gate_a.get("status") != "PASS" or int(gate_a.get("trial_count_compared", -1)) != 2400
            or gate_a.get("trial_id_coverage") != "1..2400"
            or gate_a.get("actual_target_map_sha256") != N2400_TARGET_MAP_SHA256
            or gate_a.get("approved_target_map_sha256") != N2400_TARGET_MAP_SHA256
            or int(gate_a.get("mismatch_count", -1)) != 0):
        raise RuntimeError("N2400_CHECKPOINT_GATE_A_EVIDENCE_MISMATCH")
    jsonl_sha = _sha256_file(n2400_results_path)
    if jsonl_sha != N2400_JSONL_SHA256 or report.get("new_trials_result_jsonl_sha256") != jsonl_sha:
        raise RuntimeError("N2400_TRIAL_RESULTS_JSONL_SHA256_MISMATCH")
    new_records = []
    with n2400_results_path.open("r", encoding="utf-8") as stream:
        for line_num, line in enumerate(stream, 1):
            if not line.strip():
                raise RuntimeError(f"N2400_TRIAL_RESULTS_BLANK_LINE:{line_num}")
            row = json.loads(line); tid = int(row.get("trial_id", -1))
            new_records.append(_validate_n2400_record(row, trial_id=tid, provider=provider))
    validate_trial_id_coverage([int(r["trial_id"]) for r in new_records], list(range(1201, 2401)), "N2400_NEW_TRIAL_COVERAGE_FAIL")
    for row in new_records:
        tid = int(row["trial_id"])
        if tid in all_results:
            raise RuntimeError(f"TRIAL_RESULT_DUPLICATED_ACROSS_N1200_AND_N2400:{tid}")
        all_results[tid] = row
    if sorted(all_results) != list(range(1, 2401)):
        raise RuntimeError("COMBINED_RESULT_SET_COVERAGE_NOT_1_TO_2400")
    result_hash_map = {tid: str(all_results[tid]["result_sha256"]) for tid in range(1, 2401)}
    target_map_sha = _ordered_map_sha256({scenario: result_hash_map})
    if target_map_sha != N2400_TARGET_MAP_SHA256:
        raise RuntimeError("COMBINED_TARGET_TRIAL_HASH_MAP_MISMATCH")
    closes = {tid: all_results[tid]["trial_result"].get("final_close_date") for tid in range(1, 2401)}

    hist_audit = _validate_historical_daily(historical_path, scenario)
    if (hist_audit.get("trial_count") != 550 or hist_audit.get("rows") != EXPECTED_HISTORICAL_ROWS
            or hist_audit.get("sha256") != EXPECTED_HISTORICAL_SHA256):
        raise RuntimeError("HISTORICAL_DAILY_LEDGER_IDENTITY_MISMATCH")
    prior_manifest_sha = _sha256_file(prior_manifest_path)
    if prior_manifest_sha != PRIOR_MANIFEST_SHA256:
        raise RuntimeError("PRIOR_CP_F_MANIFEST_SHA256_MISMATCH")
    prior_manifest = _read_json(prior_manifest_path)
    if (prior_manifest.get("status") != "PASS" or prior_manifest.get("scenario") != scenario
            or prior_manifest.get("source_sha") != SOURCE_SHA or int(prior_manifest.get("master_seed", -1)) != MASTER_SEED
            or prior_manifest.get("schema_version") != SCHEMA_VERSION
            or prior_manifest.get("historical_daily_sha256") != EXPECTED_HISTORICAL_SHA256
            or prior_manifest.get("daily_accounting_extension_sha256") != PRIOR_EXTENSION_SHA256
            or int(prior_manifest.get("daily_accounting_extension_rows", -1)) != PRIOR_EXTENSION_ROWS
            or prior_manifest.get("daily_distribution", {}).get("rows_sha256") != PRIOR_DISTRIBUTION_SHA256):
        raise RuntimeError("PRIOR_CP_F_DELIVERY_MANIFEST_IDENTITY_MISMATCH")
    prior_segment = _validate_daily_segment(prior_extension_path, scenario=scenario,
        expected_ids=list(range(551, 1201)), expected_sha256=PRIOR_EXTENSION_SHA256,
        expected_rows=PRIOR_EXTENSION_ROWS, close_dates=closes)
    prior_distribution_path = prior_manifest_path.parent / "daily_distribution.parquet"
    if not prior_distribution_path.is_file() or _sha256_file(prior_distribution_path) != PRIOR_DISTRIBUTION_SHA256:
        raise RuntimeError("PRIOR_CP_F_DISTRIBUTION_FILE_SHA256_MISMATCH")
    if int(prior_manifest.get("daily_distribution", {}).get("daily_distribution_rows", -1)) != 8325:
        raise RuntimeError("PRIOR_CP_F_DISTRIBUTION_ROW_COUNT_MISMATCH")
    representative_audit = _audit_prior_representatives(prior_representatives_dir, prior_manifest, provider)
    representative_evidence = {"replayed": False, **representative_audit}
    (out / "representative_details_audit.json").write_text(
        json.dumps(representative_evidence, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if representative_audit["status"] != "PASS":
        raise RuntimeError(f"PRIOR_REPRESENTATIVE_ACCOUNTING_AUDIT_{representative_audit['status']}")

    extension_path = out / "daily_accounting_extension.parquet"
    schema = _daily_schema(scenario); extension_rows = 0; replay_hashes: dict[int, str] = {}
    with pq.ParquetWriter(extension_path, schema, compression="zstd") as writer:
        for tid in range(1201, 2401):
            cp, recovery = monte_carlo.parse_scenario_id(scenario)
            daily: list[dict[str, Any]] = []; partner: list[dict[str, Any]] = []; meta: list[dict[str, Any]] = []
            def capture(project: Any, day: date) -> None:
                _capture_day(daily, partner, project, day, tid, meta)
            project = daily_engine.run_deterministic_trial(recovery_rate_pct=recovery, trial_id=tid,
                scenario_id=scenario, master_seed=MASTER_SEED, collection_probability=cp,
                on_day_end=capture, log_events=False)
            result = monte_carlo._trial_result_from_project(project, scenario_id=scenario,
                collection_probability=cp, recovery_rate_pct=recovery, trial_id=tid)
            actual_hash = stage10_trial_result_sha256(result); expected_hash = result_hash_map[tid]
            if actual_hash != expected_hash or provider.get_fingerprint(scenario, tid) != actual_hash:
                raise RuntimeError(f"DAILY_DETAIL_REPLAY_FINGERPRINT_MISMATCH:{tid}")
            if not daily or not project.daily_snapshots or not project.cash_rollforward:
                raise RuntimeError(f"DAILY_DETAIL_REPLAY_EMPTY:{tid}")
            replay_hashes[tid] = actual_hash
            rows = _accounting_rows(project, scenario, tid, actual_hash, meta)
            if not rows:
                raise RuntimeError(f"DAILY_ACCOUNTING_ROWS_EMPTY:{tid}")
            writer.write_table(pa.Table.from_pylist(rows, schema=schema)); extension_rows += len(rows)
            del project, result, daily, partner, meta
    if extension_rows <= 0 or set(replay_hashes) != set(range(1201, 2401)):
        raise RuntimeError("DAILY_DETAIL_REPLAY_COVERAGE_INCOMPLETE")
    extension_sha = _sha256_file(extension_path)
    generated_segment = _validate_daily_segment(extension_path, scenario=scenario,
        expected_ids=list(range(1201, 2401)), expected_sha256=extension_sha,
        expected_rows=extension_rows, close_dates=closes)

    distribution_path = out / "daily_distribution.parquet"
    distribution_written = _daily_distribution(historical_path, prior_extension_path, extension_path,
        [all_results[tid]["trial_result"] for tid in range(1, 2401)], scenario, distribution_path)
    distribution_verified = _verify_distribution_file(distribution_path, scenario, closes)
    representative_evidence = {"replayed": False, **representative_audit}
    (out / "representative_details_audit.json").write_text(
        json.dumps(representative_evidence, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    shutil.copyfile(source_identity_report_path, evidence_dir / "source_identity_exception_report.json")
    shutil.copyfile(provider_preflight_report_path, evidence_dir / "gatea_provider_preflight_report.json")

    file_records = []
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name not in {"scenario_manifest.json", "artifact_inventory.json", "SHA256SUMS.txt"}:
            file_records.append({"path": path.relative_to(out).as_posix(), "size_bytes": path.stat().st_size, "sha256": _sha256_file(path)})
    producer_sha = os.environ.get("GITHUB_SHA", "")
    if producer_sha and not re.fullmatch(r"[0-9a-f]{40}", producer_sha):
        raise RuntimeError("PRODUCER_TESTED_SHA_INVALID")
    manifest = {
        "manifest_version": "cp-daily-details-c030-g1201-2400-v1", "status": "PASS",
        "scope_authorization": "Owner chat authorization 2026-10-16: delivery-only Daily Accounting Details for C030_G030 trial IDs 1201..2400; not a new statistical checkpoint and not a modification to historical trial data.",
        "scenario": scenario, "source_sha": SOURCE_SHA, "source_commit": APPROVED_SOURCE_COMMIT,
        "master_seed": MASTER_SEED, "rng_policy": _identity(scenario)["rng_policy"],
        "sampling_policy": "delivery-only deterministic detail replay of approved trial IDs 1201..2400; no statistical checkpoint or new statistical cohort",
        "schema_version": SCHEMA_VERSION,
        "producer": {"branch": os.environ.get("GITHUB_REF_NAME", ""), "tested_sha": producer_sha,
                     "run_id": os.environ.get("GITHUB_RUN_ID", ""), "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "")},
        "input_provenance": {
            "historical_daily": {"run_id": 37964656154, "artifact_id": 11633466266,
                "archive_sha256": "02c751c484cec7820767022b7423770916d974281f74bd087ef5bb750ec17380",
                "trial_ids": "1..550", **hist_audit},
            "prior_n1200_source": {"run_id": N1200_RUN_ID, "artifact_id": N1200_SOURCE_ARTIFACT_ID,
                "archive_sha256": N1200_SOURCE_ARCHIVE_SHA256, "checkpoint_map_sha256": N1200_MAP_SHA256,
                "target_trial_ids": "1..1200"},
            "prior_cp_f_detail": {"run_id": PRIOR_REPLAY_RUN_ID, "artifact_id": PRIOR_REPLAY_ARTIFACT_ID,
                "archive_sha256": PRIOR_REPLAY_ARCHIVE_SHA256, "manifest_sha256": prior_manifest_sha,
                "extension_sha256": PRIOR_EXTENSION_SHA256, "extension_rows": PRIOR_EXTENSION_ROWS,
                "extension_trial_ids": "551..1200", "distribution_sha256": PRIOR_DISTRIBUTION_SHA256,
                "validated_segment": prior_segment},
            "n2400_source": {"run_id": N2400_RUN_ID, "artifact_id": N2400_ARTIFACT_ID,
                "archive_sha256": N2400_ARCHIVE_SHA256, "tested_sha": N2400_TESTED_HEAD_SHA,
                "trial_results_jsonl_sha256": jsonl_sha, "target_trial_ids": "1201..2400",
                "checkpoint_status": report.get("checkpoint_status"), "gate_a_target_map_sha256": target_map_sha},
            "golden_provider": {"source_map_sha256": provider.source_map_sha256,
                "base_map_sha256": provider.base_source_map_sha256, "extension_map_sha256": provider.extension_map_sha256,
                "golden_reference_id": provider.get_golden_reference_id(), "source_identity_preflight": preflight},
        },
        "daily_accounting_extension": {"file": "daily_accounting_extension.parquet", "trial_ids": "1201..2400",
            "trial_count": 1200, "row_count": extension_rows, "sha256": extension_sha,
            "post_write_validation": generated_segment, "fingerprint_count_verified": len(replay_hashes),
            "fingerprint_map_sha256": _ordered_map_sha256({scenario: replay_hashes})},
        "daily_distribution": {"file": "daily_distribution.parquet", **distribution_written,
            "post_write_validation": distribution_verified},
        "representative_details": {"status": representative_audit["status"], "replayed": False, "evidence_file": "representative_details_audit.json",
            "prior_manifest_sha256": prior_manifest_sha, "files": representative_audit["files"]},
        "historic_failures_preserved": {
            "n300_to_n600": {"status": "FAIL", "metric": "P90_Final_Cash",
                "relative_change_percent": 1.5715059334983579, "threshold_percent": 1.0, "scenario": scenario},
            "n2400_overall_stability_claim": "not established by this daily-details CP; statistical gates were not executed or promoted here"},
        "side_effects": {"statistical_checkpoint_executed": False, "historical_trial_ids_1_to_1200_replayed": False,
            "approved_trial_ids_1201_to_2400_detail_replayed": True, "historical_dataset_modified": False,
            "historical_parquet_modified": False, "source_sha_bumped": False, "master_seed_changed": False,
            "rng_changed": False, "main_modified": False, "release_created": False},
        "files_sha256_and_bytes": file_records,
    }
    (out / "scenario_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    inventory = []
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name not in {"artifact_inventory.json", "SHA256SUMS.txt"}:
            inventory.append({"path": path.relative_to(out).as_posix(), "size_bytes": path.stat().st_size, "sha256": _sha256_file(path)})
    (out / "artifact_inventory.json").write_text(
        json.dumps({"status": "PASS", "file_count": len(inventory), "files": inventory}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8")
    sum_paths = sorted(path for path in out.rglob("*") if path.is_file() and path.name != "SHA256SUMS.txt")
    (out / "SHA256SUMS.txt").write_text(
        "".join(f"{_sha256_file(path)}  {path.relative_to(out).as_posix()}\n" for path in sum_paths), encoding="utf-8")
    return manifest

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Delivery-only Stage 12 daily-detail extension for C030_G030 trial IDs 1201..2400.")
    parser.add_argument("--historical-parquet", required=True)
    parser.add_argument("--prior-extension-parquet", required=True)
    parser.add_argument("--prior-manifest", required=True)
    parser.add_argument("--prior-representatives-dir", required=True)
    parser.add_argument("--n1200-audit", required=True)
    parser.add_argument("--n1200-results", required=True)
    parser.add_argument("--n2400-report", required=True)
    parser.add_argument("--n2400-results", required=True)
    parser.add_argument("--source-identity-report", required=True)
    parser.add_argument("--provider-preflight-report", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)
    try:
        report = run_c030_daily_extension(
            historical_path=Path(args.historical_parquet), prior_extension_path=Path(args.prior_extension_parquet),
            prior_manifest_path=Path(args.prior_manifest), prior_representatives_dir=Path(args.prior_representatives_dir),
            n1200_audit_path=Path(args.n1200_audit), n1200_results_path=Path(args.n1200_results),
            n2400_report_path=Path(args.n2400_report), n2400_results_path=Path(args.n2400_results),
            source_identity_report_path=Path(args.source_identity_report),
            provider_preflight_report_path=Path(args.provider_preflight_report), out=Path(args.output_dir))
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 0
    except Exception as exc:
        print(f"CP_DAILY_DETAILS_FAILURE: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise

if __name__ == "__main__":
    raise SystemExit(main())
