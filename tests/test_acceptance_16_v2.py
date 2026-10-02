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
