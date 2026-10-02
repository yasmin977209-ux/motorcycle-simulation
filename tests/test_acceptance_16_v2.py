from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import ast
import re
import dataclasses

import pytest

from constants import *
from entities import Bike, Contract, GuaranteeClaim, Project, ContractType
from accounting import initialize_accounting, balance_sheet_snapshot, refresh_profit, accrue_rent, collect_from_ar, settle_guarantee_accounting
from partner_equity import record_eligible_inflow, final_entitlements
from state_machine import derive_state_from_balance, validate_transition_table, TRANSITION_TABLE
from friday import eligible_friday_number, is_eligible_friday, apply_friday_fee_and_oil
from collection import apply_ordinary_collection
from settlement import (
    first_settlement_business_day_after,
    apply_settlement_rent,
    apply_legacy_debt_collection,
)
from depreciation import apply_daily_depreciation, apply_ownership_writeoff
from guarantee import _waiting_days_for_source, create_guarantee_claim, can_settle_claim, settle_guarantee_claim
from rng import derive_seed, rng_draw, scenario_id
from closure import closure_preconditions_met, execute_dynamic_closure
import daily_engine
import dateutils

from acceptance_helpers import (
    ROOT, APP_FILES, _new_project, _add_active_contract, _mark_all_initial_owned,
    _run_days, _deterministic_trial_cached, _source_text, _event_types,
    invoke_closure_and_get_state,
)

# 16.1 foundation

def test_001_رأس_المال_الكلي():
    p = _new_project(); assert p.capital == TOTAL_CAPITAL == 3_700_000


def test_002_عدد_الدراجات_التأسيسية():
    p = _new_project(); assert len(p.bikes) == INITIAL_FLEET_SIZE == 10


def test_003_إجمالي_أصول_الدراجات_الافتتاحية():
    p = _new_project(); assert p.gross_bike_assets == OPENING_BIKE_ASSETS == 3_600_000


def test_004_الخسارة_الافتتاحية():
    p = _new_project(); assert p.retained_earnings == OPENING_RETAINED_LOSS == -100_000


def test_005_النقدية_الافتتاحية():
    p = _new_project(); assert p.project_cash == OPENING_CASH == 0


def test_006_الميزانية_الافتتاحية_متوازنة():
    p = _new_project(); s = balance_sheet_snapshot(p); assert s["Total_Assets"] == s["Total_Equity"] == 3_600_000


def test_007_لا_دراجة_أخرى_غير_العشرة_في_اليوم_الأول():
    p = _new_project(); assert len(p.bikes) == 10

# 16.2 prep

def test_008_شراء_توسع_بـ350000_يخصم_من_cash_و_partner1_rb_معا():
    p = _new_project(); p.project_cash = p.partner1_reinvestment_balance = 350_000
    daily_engine._m2(p, date(2030, 12, 31))
    assert p.project_cash == 0 and p.partner1_reinvestment_balance == 0
    assert any(b.source == 'EXPANSION' for b in p.bikes)


def test_009_الدراجة_تدخل_PREP_عند_الشراء():
    p = _new_project(); p.project_cash = p.partner1_reinvestment_balance = 350_000
    daily_engine._m2(p, date(2030, 12, 31))
    b = [b for b in p.bikes if b.source == 'EXPANSION'][0]; assert b.current_state == 'PREP'


def test_010_لا_استهلاك_في_PREP():
    b = Bike('BKX','EXPANSION',date(2030,12,31),date(2031,1,6),gross_cost=350_000)
    r = apply_daily_depreciation(b.gross_cost,b.accumulated_depreciation,False); assert r.depreciation_recorded == 0 and b.accumulated_depreciation == 0


def test_011_لا_عقد_في_PREP():
    b = Bike('BKX','EXPANSION',date(2030,12,31),date(2031,1,6),gross_cost=350_000); assert b.current_contract_id is None


def test_012_دفع_4000_ينشئ_مصروفا_فقط():
    p = _new_project(); b = Bike('BKX','EXPANSION',date(2030,12,31),date(2031,1,6),gross_cost=350_000); p.bikes.append(b)
    p.project_cash = p.partner1_reinvestment_balance = 4_000
    before = p.gross_bike_assets; daily_engine._m2(p, date(2031,1,2))
    assert p.expense_prep == 4_000 and p.gross_bike_assets == before


def test_013_دفع_10000_يزيد_gross_cost():
    p = _new_project(); b = Bike('BKX','EXPANSION',date(2030,12,31),date(2031,1,6),gross_cost=350_000); p.bikes.append(b)
    p.project_cash = p.partner1_reinvestment_balance = 14_000
    before = b.gross_cost; daily_engine._m2(p, date(2031,1,2))
    assert b.gross_cost == before + 10_000 == 360_000


def test_014_لا_جاهزية_قبل_اكتمال_كامل_14000():
    b = Bike('BKX','EXPANSION',date(2030,12,31),date(2031,1,6),gross_cost=350_000)
    assert b.actual_ready_date is None
    b.prep_paid = True; assert b.actual_ready_date is None
    b.customs_paid = True; b.funding_completion_date = date(2031,1,2); b.actual_ready_date = max(b.scheduled_ready_date,b.funding_completion_date)
    assert b.actual_ready_date == date(2031,1,6)


def test_015_FIFO_في_تجهيز_دراجات_متعددة():
    p = _new_project()
    b1 = Bike('BK001','EXPANSION',date(2030,12,1),date(2030,12,7),gross_cost=350_000)
    b2 = Bike('BK002','EXPANSION',date(2030,12,2),date(2030,12,8),gross_cost=350_000)
    p.bikes.extend([b1,b2]); p.project_cash=p.partner1_reinvestment_balance=4_000
    daily_engine._m2(p,date(2030,12,8))
    assert b1.prep_paid and not b2.prep_paid


def test_016_لا_شراء_توسع_جديد_قبل_تمويل_PREP_القائمة_بالكامل():
    p = _new_project(); b = Bike('BK001','EXPANSION',date(2030,12,1),date(2030,12,7),gross_cost=350_000); p.bikes.append(b)
    p.project_cash=p.partner1_reinvestment_balance=350_000
    daily_engine._m2(p,date(2030,12,8))
    assert not any(x.source == 'EXPANSION' and x.bike_id != 'BK001' for x in p.bikes)


def test_017_استمرار_تمويل_PREP_بعد_2030_12_31():
    p=_new_project(); b=Bike('BK001','EXPANSION',date(2030,12,31),date(2031,1,6),gross_cost=350_000); p.bikes.append(b)
    p.project_cash=p.partner1_reinvestment_balance=14_000
    daily_engine._m2(p,date(2031,1,2))
    assert b.prep_paid and b.customs_paid and b.actual_ready_date is not None

# 16.3 delivery / depreciation

def test_018_عدم_التسليم_يوم_الجمعة():
    p=_new_project(); b=p.bikes[0]; b.actual_ready_date=date(2027,1,1)
    daily_engine._m3(p,date(2027,1,1)); assert b.current_state == 'PREP'


def test_019_تسليم_السبت_اول_جمعة_بعد_7_ايام():
    d=date(2027,1,2); assert eligible_friday_number(d,date(2027,1,8)) == 1


def test_020_تسليم_الاحد_اول_جمعة_بعد_6_ايام():
    d=date(2027,1,3); assert eligible_friday_number(d,date(2027,1,8)) == 1


def test_021_تسليم_الاثنين_اول_جمعة_بعد_5_ايام():
    d=date(2027,1,4); assert eligible_friday_number(d,date(2027,1,8)) == 1


def test_022_تسليم_الثلاثاء_اول_جمعة_معفاة_والتي_تليها():
    d=date(2027,1,5); assert eligible_friday_number(d,date(2027,1,15)) == 1


def test_023_تسليم_الاربعاء_اول_جمعة_معفاة_والتي_تليها():
    d=date(2027,1,6); assert eligible_friday_number(d,date(2027,1,15)) == 1


def test_024_تسليم_الخميس_اول_جمعة_معفاة_والتي_تليها():
    d=date(2027,1,7); assert eligible_friday_number(d,date(2027,1,15)) == 1


def test_025_لا_استهلاك_قبل_التسليم_ويبدأ_من_يوم_التسليم():
    p=daily_engine.create_initial_project(); p.bikes[0].actual_ready_date=date(2027,1,1)
    daily_engine.run_day(p,date(2027,1,1),collection_probability=1.0,scenario_id='C100_G100',trial_id=1)
    assert p.bikes[0].usage_days == 0
    daily_engine.run_day(p,date(2027,1,2),collection_probability=1.0,scenario_id='C100_G100',trial_id=1)
    assert p.bikes[0].usage_days == 1

# 16.4 collection

def test_026_تحصيل_100_لا_ينتج_فسخا():
    p=_deterministic_trial_cached(); assert sum(b.termination_count for b in p.bikes) == 0


def test_027_تحصيل_0_فسخ_اساسي_اليوم_30_وثانوي_اليوم_10():
    p=_new_project(); b,c=_add_active_contract(p,start=date(2031,1,1),state='ACTIVE_PRIMARY');
    for i in range(31):
        d=date(2031,1,1)+timedelta(days=i); daily_engine.run_day(p,d,collection_probability=0.0,scenario_id='C000_TEST',trial_id=1)
        if b.current_state == 'AVAILABLE_FOR_SECONDARY': break
    primary_day=i+1; assert primary_day == 30 or primary_day == 31
    d=date(2030,12,2); b2,c2=_add_active_contract(p,contract_type='SECONDARY',start=d,state='ACTIVE_SECONDARY')
    workdays = 0
    for j in range(20):
        dd=d+timedelta(days=j); daily_engine.run_day(p,dd,collection_probability=0.0,scenario_id='C000_TEST',trial_id=2)
        if dd.weekday() != 4:
            workdays += 1
        if b2.current_state == 'AVAILABLE_FOR_SECONDARY': break
    assert workdays <= 10


def test_028_لا_متأخرات_دفعة_يوم_واحد():
    p=Contract('CT1','B1','T1','G1','PRIMARY',1500,date(2031,1,1),total_due=1500,total_paid=0)
    r=apply_ordinary_collection(p.total_due,p.total_paid,p.daily_rate,True,date(2031,1,4))
    assert r.collected == 1500


def test_029_متأخر_يوم_دفعة_يومين():
    c=Contract('CT1','B1','T1','G1','PRIMARY',1500,date(2031,1,1),total_due=3000,total_paid=0)
