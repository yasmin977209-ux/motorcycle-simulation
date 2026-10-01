"""Chapter 12 — daily engine, M1 through M17 in the mandatory order."""
from __future__ import annotations
from datetime import date, timedelta

from constants import (
    BIKE_BASE_PURCHASE_COST, BIKE_GROSS_ASSET_COST, BIKE_TOTAL_CASH_FLOW_COST,
    CUSTOMS_AND_REGISTRATION_COST, EXPANSION_CUTOFF_DATE, FRIDAY_FEE,
    INITIAL_FLEET_PURCHASE_DATE, INITIAL_FLEET_READY_DATE, INITIAL_FLEET_SIZE,
    OPENING_BIKE_ASSETS, OPENING_CASH, OPENING_MARKETING_EXPENSE,
    OPENING_RETAINED_LOSS, PRIMARY_DAILY_RENT, SECONDARY_DAILY_RENT,
    SETTLEMENT_DAILY_RENT, TOTAL_CAPITAL,
)
from accounting import assert_balance_sheet_balanced
from closure import execute_dynamic_closure
from collection import apply_ordinary_collection
from depreciation import apply_daily_depreciation, apply_ownership_writeoff
from dateutils import is_business_day, is_eligible_friday, primary_maturity_date, scheduled_ready_date
from entities import (
    Bike, BikeSource, ClaimStatus, Contract, ContractStatus, ContractType,
    EventLogEntry, EventType, GuaranteeClaim, Guarantor, Project,
    ReceivableEntry, ReceivableSource, ReceivableStatus, Tenant, TenantType,
)
from friday import apply_friday_fee_and_oil
from guarantee import create_guarantee_claim, settle_guarantee_claim
from partner_equity import assert_memo_nonnegative, consume_partner1_for_expansion, record_eligible_inflow
from rng import derive_seed, rng_draw
from settlement import apply_legacy_debt_collection, apply_settlement_rent
from state_machine import derive_state_from_balance

POSSESSION_STATES=frozenset({
    "ACTIVE_PRIMARY","WAITING_PRIMARY","NOTICE_PRIMARY","GRACE_PRIMARY",
    "POST_MATURITY_SETTLEMENT","ACTIVE_SECONDARY","NOTICE_SECONDARY",
})


def create_initial_project(recovery_rate_pct: int=100)->Project:
    del recovery_rate_pct
    p=Project(
        project_cash=OPENING_CASH,
        partner1_reinvestment_balance=0,
        partner2_reinvestment_balance=0,
        accounts_receivable=0,
        guarantee_claim_receivable=0,
        gross_bike_assets=OPENING_BIKE_ASSETS,
        accumulated_depreciation=0,
        capital=TOTAL_CAPITAL,
        retained_earnings=OPENING_RETAINED_LOSS,
        opening_loss=OPENING_RETAINED_LOSS,
        expense_marketing=OPENING_MARKETING_EXPENSE,
    )
    for i in range(1, INITIAL_FLEET_SIZE+1):
        p.bikes.append(Bike(
            bike_id=f"BK{i:04d}", source=BikeSource.INITIAL,
            purchase_date=INITIAL_FLEET_PURCHASE_DATE,
            scheduled_ready_date=INITIAL_FLEET_READY_DATE,
            funding_completion_date=INITIAL_FLEET_PURCHASE_DATE,
            actual_ready_date=INITIAL_FLEET_READY_DATE,
            prep_paid=True, customs_paid=True, gross_cost=BIKE_GROSS_ASSET_COST,
            net_book_value=BIKE_GROSS_ASSET_COST,
        ))
    return p


def _create_contract(p:Project,b:Bike,typ:ContractType,d:date)->Contract:
    cid=f"CT{len(p.contracts)+1:08d}"; tid=f"TN{len(p.tenants)+1:08d}"; gid=f"GR{len(p.guarantors)+1:08d}"
    rate=PRIMARY_DAILY_RENT if typ is ContractType.PRIMARY else SECONDARY_DAILY_RENT
    c=Contract(cid,b.bike_id,tid,gid,typ,rate,d,primary_maturity_date(d) if typ is ContractType.PRIMARY else None)
    p.contracts.append(c)
    p.tenants.append(Tenant(tid,TenantType.ORIGINAL if typ is ContractType.PRIMARY else TenantType.SECONDARY,cid,gid,d))
    p.guarantors.append(Guarantor(gid,cid,tid))
    return c


def _find_contract(p:Project,b:Bike)->Contract:
    if b.current_contract_id is None: raise ValueError(f"Bike {b.bike_id} has no current contract")
    return next(c for c in p.contracts if c.contract_id==b.current_contract_id)


def _find_receivable(p:Project,b:Bike)->ReceivableEntry:
    if b.active_settlement_receivable_id is None: raise ValueError(f"Bike {b.bike_id} has no settlement receivable")
    return next(r for r in p.receivables if r.receivable_id==b.active_settlement_receivable_id)


def _event(p:Project,d:date,b:Bike,kind:EventType,c:Contract|None=None,claim:GuaranteeClaim|None=None,amount:int|None=None)->None:
    e=EventLogEntry(
        event_id=f"EV{len(p.event_log)+1:08d}",date=d,bike_id=b.bike_id,event_type=kind,
        previous_state=b.current_state,new_state=b.current_state,
        contract_id=c.contract_id if c else None,tenant_id=c.tenant_id if c else None,
        guarantor_id=c.guarantor_id if c else None,claim_id=claim.claim_id if claim else None,
        amount_if_applicable=amount,
    )
    p.event_log.append(e); b.lifecycle_history.append(e)


def _success(probability:float,scenario_id:str,trial_id:int,bike_id:str,d:date,event_type:str)->bool:
    if probability>=1.0: return True
    if probability<=0.0: return False
    return rng_draw(derive_seed(20270101,scenario_id,trial_id,bike_id,d,event_type))<probability


def run_day(p:Project,current_date:date,collection_probability:float=1.0,scenario_id:str="C100_G100",trial_id:int=1,recovery_rate_pct:int=100)->None:
    if p.simulation_stopped: raise RuntimeError("simulation already stopped")
    trace=[]; p.execution_trace.append(trace)
    business=is_business_day(current_date)

    trace.append("M1")
    trace.append("M2")
    if business:
        for b in sorted((x for x in p.bikes if x.current_state=="PREP"),key=lambda x:(x.purchase_date,x.bike_id)):
            if not b.prep_paid and p.project_cash>=4000 and p.partner1_reinvestment_balance>=4000:
                p.project_cash-=4000; p.partner1_reinvestment_balance-=4000; p.expense_prep+=4000; b.prep_paid=True
            if not b.customs_paid and p.project_cash>=CUSTOMS_AND_REGISTRATION_COST and p.partner1_reinvestment_balance>=CUSTOMS_AND_REGISTRATION_COST:
                p.project_cash-=CUSTOMS_AND_REGISTRATION_COST; p.partner1_reinvestment_balance-=CUSTOMS_AND_REGISTRATION_COST
                p.gross_bike_assets+=CUSTOMS_AND_REGISTRATION_COST; b.gross_cost+=CUSTOMS_AND_REGISTRATION_COST; b.customs_paid=True
            if b.prep_paid and b.customs_paid and b.actual_ready_date is None:
                b.funding_completion_date=current_date; b.actual_ready_date=max(b.scheduled_ready_date,current_date)
        if current_date<=EXPANSION_CUTOFF_DATE and not any(x.current_state=="PREP" and (not x.prep_paid or not x.customs_paid) for x in p.bikes):
            while p.project_cash>=BIKE_BASE_PURCHASE_COST and p.partner1_reinvestment_balance>=BIKE_BASE_PURCHASE_COST:
                consume_partner1_for_expansion(p,BIKE_BASE_PURCHASE_COST)
                p.gross_bike_assets += BIKE_BASE_PURCHASE_COST
                n=len(p.bikes)+1
                b=Bike(f"BK{n:04d}",BikeSource.EXPANSION,current_date,scheduled_ready_date(current_date),gross_cost=BIKE_BASE_PURCHASE_COST,net_book_value=BIKE_BASE_PURCHASE_COST)
                p.bikes.append(b); _event(p,current_date,b,EventType.EXPANSION_PURCHASE,amount=BIKE_BASE_PURCHASE_COST)

    trace.append("M3")
    if business:
        for b in sorted((x for x in p.bikes if x.current_state=="PREP"),key=lambda x:(x.purchase_date,x.bike_id)):
            if b.actual_ready_date is not None and current_date>=b.actual_ready_date:
                b.delivery_date=current_date; c=_create_contract(p,b,ContractType.PRIMARY,current_date)
                b.current_contract_id=c.contract_id; b.current_tenant_id=c.tenant_id; b.current_state="ACTIVE_PRIMARY"; b.lifecycle_cycle_number=1
                _event(p,current_date,b,EventType.PRIMARY_CONTRACT_STARTED,c)
        for b in sorted((x for x in p.bikes if x.current_state=="AVAILABLE_FOR_SECONDARY"),key=lambda x:x.bike_id):
            b.delivery_date=current_date; c=_create_contract(p,b,ContractType.SECONDARY,current_date)
            b.current_contract_id=c.contract_id; b.current_tenant_id=c.tenant_id; b.secondary_cycle_count+=1; b.lifecycle_cycle_number+=1; b.current_state="ACTIVE_SECONDARY"
            _event(p,current_date,b,EventType.SECONDARY_CONTRACT_STARTED,c)

    trace.append("M4")
    possession={b.bike_id:b.current_state in POSSESSION_STATES for b in p.bikes}

    trace.append("M5")
    if business:
        for b in p.bikes:
            if b.current_state in {"ACTIVE_PRIMARY","WAITING_PRIMARY","NOTICE_PRIMARY","GRACE_PRIMARY"}:
                c=_find_contract(p,b); c.total_due+=PRIMARY_DAILY_RENT; p.revenue_primary+=PRIMARY_DAILY_RENT; p.accounts_receivable+=PRIMARY_DAILY_RENT
            elif b.current_state in {"ACTIVE_SECONDARY","NOTICE_SECONDARY"}:
                c=_find_contract(p,b); c.total_due+=SECONDARY_DAILY_RENT; p.revenue_secondary+=SECONDARY_DAILY_RENT; p.accounts_receivable+=SECONDARY_DAILY_RENT
            elif b.current_state=="POST_MATURITY_SETTLEMENT":
                r=apply_settlement_rent(current_date)
                if r.collected:
                    b.settlement_rent_due_total+=r.due; b.settlement_rent_collected_total+=r.collected; p.revenue_settlement+=r.collected; p.project_cash+=r.cash_delta; record_eligible_inflow(p,r.collected)

    trace.append("M6")
    if not business:
        for b in p.bikes:
            if not possession.get(b.bike_id): continue
            c=_find_contract(p,b)
            r=apply_friday_fee_and_oil(c.start_date,current_date,c.friday_counter,True)
            if r.eligible:
                p.revenue_friday_fee+=r.revenue_friday_fee; p.project_cash+=r.revenue_friday_fee; c.friday_counter=r.friday_counter_after
                p.expense_oil_service+=r.oil_service_expense; p.project_cash-=r.oil_service_expense; record_eligible_inflow(p,r.revenue_friday_fee)

    trace.append("M7")
    for b in p.bikes:
        if not possession.get(b.bike_id): continue
        r=apply_daily_depreciation(b.gross_cost,b.accumulated_depreciation,True)
        b.accumulated_depreciation=r.accumulated_depreciation_after; b.net_book_value=r.net_book_value_after; b.usage_days+=r.usage_days_after
        p.accumulated_depreciation+=r.project_accumulated_depreciation_delta; p.expense_depreciation+=r.depreciation_expense

    trace.append("M8")
    if business:
        for b in p.bikes:
            if b.current_state in {"ACTIVE_PRIMARY","WAITING_PRIMARY","NOTICE_PRIMARY","GRACE_PRIMARY"}:
                c=_find_contract(p,b); ok=_success(collection_probability,scenario_id,trial_id,b.bike_id,current_date,"PRIMARY_COLLECTION")
                r=apply_ordinary_collection(c.total_due,c.total_paid,PRIMARY_DAILY_RENT,ok,current_date); c.total_paid=r.total_paid_after
                p.project_cash+=r.cash_delta; p.accounts_receivable+=r.accounts_receivable_delta; record_eligible_inflow(p,r.collected)
            elif b.current_state in {"ACTIVE_SECONDARY","NOTICE_SECONDARY"}:
                c=_find_contract(p,b); ok=_success(collection_probability,scenario_id,trial_id,b.bike_id,current_date,"SECONDARY_COLLECTION")
                r=apply_ordinary_collection(c.total_due,c.total_paid,SECONDARY_DAILY_RENT,ok,current_date); c.total_paid=r.total_paid_after
                p.project_cash+=r.cash_delta; p.accounts_receivable+=r.accounts_receivable_delta; record_eligible_inflow(p,r.collected)
            elif b.current_state=="POST_MATURITY_SETTLEMENT":
                remaining=b.settlement_legacy_debt_remaining or 0
                if remaining>0:
                    ok=_success(collection_probability,scenario_id,trial_id,b.bike_id,current_date,"LEGACY_DEBT_COLLECTION")
                    r=apply_legacy_debt_collection(remaining,ok); b.settlement_legacy_debt_remaining=r.remaining_after
                    p.project_cash+=r.cash_delta; p.accounts_receivable+=r.accounts_receivable_delta
                    recv=_find_receivable(p,b); recv.collected_amount+=r.payment; recv.remaining_amount=r.remaining_after
                    if r.completed: recv.status=ReceivableStatus.SETTLED
                    record_eligible_inflow(p,r.payment)

    trace.append("M9")
    for b in p.bikes:
        if b.current_state in {"ACTIVE_PRIMARY","WAITING_PRIMARY","NOTICE_PRIMARY","GRACE_PRIMARY"}:
            c=_find_contract(p,b); s=derive_state_from_balance(c.total_due-c.total_paid,PRIMARY_DAILY_RENT,"PRIMARY")
            if s is not None: b.current_state=s
        elif b.current_state in {"ACTIVE_SECONDARY","NOTICE_SECONDARY"}:
            c=_find_contract(p,b); s=derive_state_from_balance(c.total_due-c.total_paid,SECONDARY_DAILY_RENT,"SECONDARY")
            if s is not None: b.current_state=s

    trace.append("M10")

    trace.append("M11")
    for b in list(p.bikes):
        if b.current_state=="GRACE_PRIMARY":
            c=_find_contract(p,b); outstanding=c.total_due-c.total_paid
            if outstanding>=45000:
                claim=create_guarantee_claim(f"CL{len(p.guarantee_claims)+1:08d}",b.bike_id,c.contract_id,c.tenant_id,c.guarantor_id,"PRIMARY_EARLY_TERMINATION",outstanding,current_date,recovery_rate_pct)
                p.guarantee_claims.append(claim); p.accounts_receivable-=outstanding; p.guarantee_claim_receivable+=outstanding; c.status=ContractStatus.TERMINATED
                b.current_contract_id=None; b.current_tenant_id=None; b.termination_count+=1; b.current_state="AVAILABLE_FOR_SECONDARY"; _event(p,current_date,b,EventType.PRIMARY_TERMINATED,c,claim,outstanding)
        elif b.current_state=="NOTICE_SECONDARY":
            c=_find_contract(p,b); outstanding=c.total_due-c.total_paid
            if outstanding>=10000:
                claim=create_guarantee_claim(f"CL{len(p.guarantee_claims)+1:08d}",b.bike_id,c.contract_id,c.tenant_id,c.guarantor_id,"SECONDARY_EARLY_TERMINATION",outstanding,current_date,recovery_rate_pct)
                p.guarantee_claims.append(claim); p.accounts_receivable-=outstanding; p.guarantee_claim_receivable+=outstanding; c.status=ContractStatus.TERMINATED
                b.current_contract_id=None; b.current_tenant_id=None; b.termination_count+=1; b.current_state="AVAILABLE_FOR_SECONDARY"; _event(p,current_date,b,EventType.SECONDARY_TERMINATED,c,claim,outstanding)

    trace.append("M12")
    for b in list(p.bikes):
        if b.current_state not in {"ACTIVE_PRIMARY","WAITING_PRIMARY","NOTICE_PRIMARY","GRACE_PRIMARY"}: continue
        c=_find_contract(p,b)
        if c.status is ContractStatus.ACTIVE and current_date==c.maturity_date:
            outstanding=c.total_due-c.total_paid; _event(p,current_date,b,EventType.PRIMARY_CONTRACT_MATURED,c)
            if outstanding==0:
                c.status=ContractStatus.SETTLED; b.current_state="OWNED_TRANSFERRED"; b.current_contract_id=None; b.current_tenant_id=None; b.pending_writeoff_today=True; _event(p,current_date,b,EventType.OWNERSHIP_TRANSFERRED,c)
            else:
                c.status=ContractStatus.MATURED; b.current_state="POST_MATURITY_SETTLEMENT"; b.settlement_legacy_debt_original=outstanding; b.settlement_legacy_debt_remaining=outstanding
                b.settlement_business_days_elapsed=0; b.settlement_start_date=None
                recv=ReceivableEntry(f"RC{len(p.receivables)+1:08d}",b.bike_id,c.contract_id,c.tenant_id,ReceivableSource.SETTLEMENT_LEGACY_DEBT,outstanding,0,outstanding,ReceivableStatus.OUTSTANDING,None)
                p.receivables.append(recv); b.active_settlement_receivable_id=recv.receivable_id; _event(p,current_date,b,EventType.SETTLEMENT_STARTED,c,amount=outstanding)

    trace.append("M13")
    for b in p.bikes:
        if b.current_state!="POST_MATURITY_SETTLEMENT": continue
        recv=_find_receivable(p,b)
        if b.settlement_start_date is None:
            b.settlement_start_date=current_date; recv.created_date=current_date; continue
        if not business: continue
        b.settlement_business_days_elapsed+=1
        c=next(x for x in p.contracts if x.contract_id==recv.contract_id)
        if b.settlement_legacy_debt_remaining==0:
            c.status=ContractStatus.SETTLED; b.current_state="OWNED_TRANSFERRED"; b.current_contract_id=None; b.current_tenant_id=None; b.pending_writeoff_today=True; _event(p,current_date,b,EventType.SETTLEMENT_COMPLETED,c); _event(p,current_date,b,EventType.OWNERSHIP_TRANSFERRED,c)
        elif b.settlement_business_days_elapsed>30:
            remaining=b.settlement_legacy_debt_remaining
            claim=create_guarantee_claim(f"CL{len(p.guarantee_claims)+1:08d}",b.bike_id,c.contract_id,c.tenant_id,c.guarantor_id,"POST_MATURITY_SETTLEMENT_FAILURE",remaining,current_date,recovery_rate_pct)
            p.guarantee_claims.append(claim); p.accounts_receivable-=remaining; p.guarantee_claim_receivable+=remaining; recv.status=ReceivableStatus.TRANSFERRED_TO_GUARANTEE; recv.remaining_amount=0
            b.settlement_legacy_debt_remaining=0; c.status=ContractStatus.TERMINATED; b.current_contract_id=None; b.current_tenant_id=None; b.current_state="AVAILABLE_FOR_SECONDARY"; b.termination_count+=1
            _event(p,current_date,b,EventType.SETTLEMENT_FAILED,c,claim,remaining)

    trace.append("M14")
    for claim in list(p.guarantee_claims):
        if claim.status is ClaimStatus.PENDING and current_date>=claim.settlement_due_date:
            r=settle_guarantee_claim(claim,current_date)
            if r.settled_now:
                p.project_cash+=r.recovered_amount; p.guarantee_claim_receivable-=r.claim_amount; p.bad_debt_expense+=r.bad_debt_amount; record_eligible_inflow(p,r.recovered_amount)

    trace.append("M15")
    execute_dynamic_closure(p,current_date,recovery_rate_pct)

    trace.append("M16")
    for b in p.bikes:
        if not b.pending_writeoff_today: continue
        r=apply_ownership_writeoff(b.gross_cost,b.accumulated_depreciation)
        p.accumulated_depreciation+=r.project_accumulated_depreciation_delta
        p.asset_writeoff_expense+=r.expense_asset_writeoff
        p.gross_bike_assets+=r.project_gross_asset_delta
        b.net_book_value=0; b.accumulated_depreciation=r.bike_accumulated_depreciation_after; b.pending_writeoff_today=False

    trace.append("M17")
    assert_memo_nonnegative(p)
    snap=assert_balance_sheet_balanced(p,current_date)
    p.daily_balance_checks.append({"date":current_date.isoformat(),**snap})
    if p.simulation_stopped and p.final_net_project_equity!=snap["Total_Equity"]:
        raise AssertionError("final equity differs from M17 equity")


def run_days(p:Project,start_date:date,end_date:date,**kwargs)->Project:
    d=start_date
    while d<=end_date and not p.simulation_stopped:
        run_day(p,d,**kwargs); d+=timedelta(days=1)
    return p


def run_deterministic_trial(recovery_rate_pct:int=100,trial_id:int=1,scenario_id:str="C100_G100")->Project:
    p=create_initial_project(recovery_rate_pct)
    d=date(2027,1,1)
    while not p.simulation_stopped:
        run_day(p,d,1.0,scenario_id,trial_id,recovery_rate_pct); d+=timedelta(days=1)
    return p
