"""Stage 3B tests: Chapters 10–13, mandatory M1..M17 order, deterministic daily balance."""
from __future__ import annotations
from datetime import date, timedelta
from accounting import assert_balance_sheet_balanced, balance_sheet_snapshot
from closure import closure_preconditions_met
from constants import EXPANSION_CUTOFF_DATE, OPENING_BIKE_ASSETS, OPENING_RETAINED_LOSS, TOTAL_CAPITAL
from daily_engine import create_initial_project, run_day, run_deterministic_trial
from partner_equity import record_eligible_inflow

def test_ch10_opening_balance_sheet():
    p=create_initial_project()
    s=assert_balance_sheet_balanced(p,date(2027,1,1))
    assert s["Total_Assets"]==OPENING_BIKE_ASSETS
    assert s["Total_Equity"]==TOTAL_CAPITAL+OPENING_RETAINED_LOSS

def test_ch11_partner_memo_off_balance_sheet():
    p=create_initial_project(); before=balance_sheet_snapshot(p)
    assert record_eligible_inflow(p,1000)==(700,300)
    after=balance_sheet_snapshot(p)
    assert after["Total_Assets"]==before["Total_Assets"] and after["Total_Equity"]==before["Total_Equity"]

def test_ch12_exact_m1_to_m17_order():
    p=create_initial_project(); run_day(p,date(2027,1,1),1.0, "C100_G100",1,100)
    assert p.execution_trace[-1]==[f"M{i}" for i in range(1,18)]

def test_ch13_dynamic_closure_conditions():
    p=create_initial_project()
    assert not closure_preconditions_met(p,EXPANSION_CUTOFF_DATE)
    assert not closure_preconditions_met(p,EXPANSION_CUTOFF_DATE+timedelta(days=1))
    for b in p.bikes: b.current_state="OWNED_TRANSFERRED"; b.net_book_value=0
    assert closure_preconditions_met(p,EXPANSION_CUTOFF_DATE+timedelta(days=1))

def test_ch10_reference_numeric_bridge():
    p=create_initial_project(); p.revenue_primary=20000; p.bad_debt_expense=7500
    from accounting import refresh_profit
    refresh_profit(p)
    assert p.retained_earnings==OPENING_RETAINED_LOSS+12500

def test_full_deterministic_trial_daily_balance():
    p=run_deterministic_trial(100,1,"C100_G100")
    assert p.simulation_stopped and p.final_close_date is not None and p.final_close_date>EXPANSION_CUTOFF_DATE
    assert p.daily_balance_checks
    assert all(row["Balance_Difference"]==0 for row in p.daily_balance_checks)
    assert p.final_net_project_equity is not None
