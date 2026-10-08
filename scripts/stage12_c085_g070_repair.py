import argparse,json,hashlib,subprocess
import dateutils
from datetime import datetime,timezone
from pathlib import Path
import pyarrow as pa, pyarrow.parquet as pq
import constants,daily_engine,monte_carlo
from closure import closure_preconditions_met
from entities import BikeState,ClaimStatus
from settlement import first_settlement_business_day_after,settlement_business_days_elapsed
SOURCE_SHA="f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
MASTER_SEED=20270101
FORBIDDEN={"MINI_PREP","PENDING_RECALL","TERMINATION_PENDING"}

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--scenario",required=True);ap.add_argument("--start",type=int,required=True);ap.add_argument("--end",type=int,required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
 subprocess.run(["git","cat-file","-e",f"{SOURCE_SHA}^{{commit}}"],check=True)
 files="constants.py dateutils.py rng.py entities.py state_machine.py daily_engine.py accounting.py collection.py guarantee.py friday.py settlement.py closure.py partner_equity.py monte_carlo.py".split()
 subprocess.run(["git","diff","--quiet",SOURCE_SHA,"HEAD","--",*files],check=True)
 cp,rr=monte_carlo.parse_scenario_id(a.scenario)
 if a.scenario.startswith("C100_") and (a.start,a.end)!=(1,1): raise SystemExit("bad C100 range")
 if not a.scenario.startswith("C100_") and a.end-a.start+1>400: raise SystemExit("chunk>400")
 out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
 schema=pa.schema([( "scenario_id",pa.string()),("trial_id",pa.int64()),("date",pa.string()),("source_sha",pa.string()),("master_seed",pa.int64()),("Opening_Cash",pa.int64()),("cash_inflows",pa.int64()),("cash_outflows",pa.int64()),("Closing_Cash",pa.int64()),("Opening_AR",pa.int64()),("ar_accruals",pa.int64()),("ar_collections",pa.int64()),("ar_transfers_to_guarantee",pa.int64()),("Closing_AR",pa.int64()),("Opening_Gross_Bike_Assets",pa.int64()),("capitalized_purchases_and_customs",pa.int64()),("gross_writeoffs_on_ownership",pa.int64()),("Closing_Gross_Bike_Assets",pa.int64()),("Opening_Accumulated_Depreciation",pa.int64()),("depreciation_expense",pa.int64()),("ad_removed_on_writeoff",pa.int64()),("Closing_Accumulated_Depreciation",pa.int64()),("Net_Bike_Assets",pa.int64()),("Capital",pa.int64()),("Retained_Earnings",pa.int64()),("Opening_Equity",pa.int64()),("Operating_Net_Profit",pa.int64()),("Closing_Equity",pa.int64()),("Guarantee_Claim_Receivable",pa.int64()),("Total_Assets",pa.int64()),("Liabilities",pa.int64()),("Balance_Difference",pa.int64()),("Final_Close_Date",pa.string()),("Simulation_Stopped",pa.bool_()),("Active_Bikes",pa.int64()),("Owned_Transferred_Bikes",pa.int64()),("Pending_Claims",pa.int64())])
 writer=pq.ParquetWriter(out/f"part_{a.start}_{a.end}.parquet",schema,compression="zstd");summaries=[]
 try:
  for tid in range(a.start,a.end+1):
   rows=[];forbidden=[];settlement_bad=[];cashflow_bad=[]
   prev={"cash":constants.OPENING_CASH,"ar":0,"gross":constants.OPENING_BIKE_ASSETS,"ad":0,"equity":constants.TOTAL_CAPITAL+constants.OPENING_RETAINED_LOSS,"oil":0,"prep":0}
   def cap(p,d):
    nonlocal prev
    m=dict(getattr(p,"_day_metrics",{}));cc=p.project_cash;ca=p.accounts_receivable;cg=p.gross_bike_assets;cad=p.accumulated_depreciation;ce=p.capital+p.retained_earnings;na=cg-cad;ta=cc+ca+p.guarantee_claim_receivable+na
    residual=m.get("cash_outflows",0)-((p.expense_oil_service-prev["oil"])+(p.expense_prep-prev["prep"])+m.get("capitalized_purchases_and_customs",0))
    if residual!=0: cashflow_bad.append({"date":d.isoformat(),"residual":residual})
    for b in p.bikes:
      if b.current_state.value in FORBIDDEN: forbidden.append({"date":d.isoformat(),"bike_id":b.bike_id,"state":b.current_state.value})
      if b.current_state is BikeState.POST_MATURITY_SETTLEMENT:
       c=p.contracts.get(b.current_contract_id) if b.current_contract_id else None
       if c is None or c.maturity_date is None:
        settlement_bad.append({"date":d.isoformat(),"bike_id":b.bike_id,"reason":"missing settlement contract metadata"})
       elif b.settlement_start_date is None:
        # Per reference M12/M13: same-day entry may legitimately retain None;
        # Friday/non-business days do not advance the settlement clock.
        if d > c.maturity_date and dateutils.is_business_day(d):
         settlement_bad.append({"date":d.isoformat(),"bike_id":b.bike_id,"reason":"missing settlement_start_date after first eligible business day"})
       else:
        es=first_settlement_business_day_after(c.maturity_date)
        ee=settlement_business_days_elapsed(b.settlement_start_date,d)
        expected_elapsed=ee+1
        if b.settlement_start_date!=es or b.settlement_business_days_elapsed!=expected_elapsed:
         settlement_bad.append({"date":d.isoformat(),"bike_id":b.bike_id,"reason":"settlement clock mismatch"})
    rows.append({"scenario_id":a.scenario,"trial_id":tid,"date":d.isoformat(),"source_sha":SOURCE_SHA,"master_seed":MASTER_SEED,"Opening_Cash":prev["cash"],"cash_inflows":m.get("cash_inflows",0),"cash_outflows":m.get("cash_outflows",0),"Closing_Cash":cc,"Opening_AR":prev["ar"],"ar_accruals":m.get("ar_accruals",0),"ar_collections":m.get("ar_collections",0),"ar_transfers_to_guarantee":m.get("ar_transfers_to_guarantee",0),"Closing_AR":ca,"Opening_Gross_Bike_Assets":prev["gross"],"capitalized_purchases_and_customs":m.get("capitalized_purchases_and_customs",0),"gross_writeoffs_on_ownership":m.get("gross_writeoffs_on_ownership",0),"Closing_Gross_Bike_Assets":cg,"Opening_Accumulated_Depreciation":prev["ad"],"depreciation_expense":m.get("depreciation_expense",0),"ad_removed_on_writeoff":m.get("ad_removed_on_writeoff",0),"Closing_Accumulated_Depreciation":cad,"Net_Bike_Assets":na,"Capital":p.capital,"Retained_Earnings":p.retained_earnings,"Opening_Equity":prev["equity"],"Operating_Net_Profit":ce-prev["equity"],"Closing_Equity":ce,"Guarantee_Claim_Receivable":p.guarantee_claim_receivable,"Total_Assets":ta,"Liabilities":0,"Balance_Difference":ta-ce,"Final_Close_Date":p.final_close_date.isoformat() if p.final_close_date else None,"Simulation_Stopped":bool(p.simulation_stopped),"Active_Bikes":sum(1 for x in p.bikes if x.current_state in daily_engine.POSSESSION_STATES),"Owned_Transferred_Bikes":sum(1 for x in p.bikes if x.current_state is BikeState.OWNED_TRANSFERRED),"Pending_Claims":sum(1 for x in p.guarantee_claims if x.status is ClaimStatus.PENDING)})
    prev={"cash":cc,"ar":ca,"gross":cg,"ad":cad,"equity":ce,"oil":p.expense_oil_service,"prep":p.expense_prep}
   p=daily_engine.run_deterministic_trial(recovery_rate_pct=rr,trial_id=tid,scenario_id=a.scenario,master_seed=MASTER_SEED,collection_probability=cp,on_day_end=cap,log_events=False)
   if not rows or not p.final_close_date or not p.simulation_stopped: raise SystemExit(f"trial {tid} did not close")
   if len(rows)!=(p.final_close_date-constants.PROJECT_START_DATE).days+1: raise SystemExit(f"daily row count mismatch trial {tid}")
   if len({(r["scenario_id"],r["trial_id"],r["date"]) for r in rows})!=len(rows): raise SystemExit(f"duplicate pk trial {tid}")
   final_eq=p.capital+p.retained_earnings
   claims_ok=all(isinstance(x.recovery_rate_pct,int) and not isinstance(x.recovery_rate_pct,bool) and x.status is ClaimStatus.SETTLED and x.recovered_amount is not None and x.bad_debt_amount is not None and x.recovered_amount==(x.claim_amount*x.recovery_rate_pct)//100 and x.bad_debt_amount==x.claim_amount-x.recovered_amount for x in p.guarantee_claims)
   owned_ok=all(x.current_state is not BikeState.OWNED_TRANSFERRED or x.net_book_value==0 for x in p.bikes)
   closure_ok=closure_preconditions_met(p,p.final_close_date)
   equity_ok=p.final_net_project_equity==final_eq
   tr=monte_carlo._trial_result_from_project(p,scenario_id=a.scenario,collection_probability=cp,recovery_rate_pct=rr,trial_id=tid)
   h=monte_carlo.fingerprint_trial_results([tr])
   writer.write_table(pa.Table.from_pylist(rows,schema=schema))
   summaries.append({"scenario_id":a.scenario,"trial_id":tid,"row_count":len(rows),"start_date":rows[0]["date"],"final_close_date":p.final_close_date.isoformat(),"source_sha":SOURCE_SHA,"master_seed":MASTER_SEED,"result_sha256":h,"forbidden":forbidden,"settlement_bad":settlement_bad,"cashflow_bad":cashflow_bad,"dynamic_closure":closure_ok,"guarantee":claims_ok,"ownership_writeoff":owned_ok,"final_equity_after_m17":equity_ok,"trial_pass":closure_ok and claims_ok and owned_ok and equity_ok and not forbidden and not settlement_bad and not cashflow_bad})
 finally: writer.close()
 (out/f"trials_{a.start}_{a.end}.json").write_text(json.dumps({"trial_summaries":summaries,"scenario":a.scenario,"range":[a.start,a.end],"source_sha":SOURCE_SHA,"master_seed":MASTER_SEED},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
if __name__=="__main__": main()
