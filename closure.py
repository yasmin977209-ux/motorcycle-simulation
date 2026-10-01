"""Chapter 13 — dynamic closure."""
from __future__ import annotations
from datetime import date
from constants import EXPANSION_CUTOFF_DATE
from entities import ClaimStatus, ClaimSource, ContractStatus, Project, ReceivableStatus
from guarantee import create_guarantee_claim

def closure_preconditions_met(project: Project, current_date: date) -> bool:
    return (
        not any(b.current_state=="PREP" for b in project.bikes)
        and not any(b.current_state in {"ACTIVE_PRIMARY","WAITING_PRIMARY","NOTICE_PRIMARY","GRACE_PRIMARY"} for b in project.bikes)
        and not any(b.current_state=="POST_MATURITY_SETTLEMENT" for b in project.bikes)
        and current_date > EXPANSION_CUTOFF_DATE
    )

def _force_settle(project: Project, claim, current_date: date) -> None:
    if claim.status is not ClaimStatus.PENDING: return
    recovered=(claim.claim_amount*claim.recovery_rate_pct)//100
    bad_debt=claim.claim_amount-recovered
    project.project_cash += recovered
    project.guarantee_claim_receivable -= claim.claim_amount
    project.bad_debt_expense += bad_debt
    claim.recovered_amount=recovered
    claim.bad_debt_amount=bad_debt
    claim.status=ClaimStatus.SETTLED
    claim.settlement_date=current_date

def execute_dynamic_closure(project: Project,current_date: date,recovery_rate_pct:int)->bool:
    if not closure_preconditions_met(project,current_date): return False
    for bike in list(project.bikes):
        if bike.current_state not in {"ACTIVE_SECONDARY","NOTICE_SECONDARY"}: continue
        contract=next(c for c in project.contracts if c.contract_id==bike.current_contract_id)
        outstanding=contract.total_due-contract.total_paid
        if outstanding>0:
            claim=create_guarantee_claim(f"CL{len(project.guarantee_claims)+1:08d}",bike.bike_id,contract.contract_id,contract.tenant_id,contract.guarantor_id,ClaimSource.ADMINISTRATIVE_CLOSURE,outstanding,current_date,recovery_rate_pct)
            project.guarantee_claims.append(claim)
            project.accounts_receivable-=outstanding
            project.guarantee_claim_receivable+=outstanding
        contract.status=ContractStatus.TERMINATED
        bike.current_contract_id=None
        bike.current_tenant_id=None
        bike.current_state="HELD_AS_ASSET"
    for claim in project.guarantee_claims:
        _force_settle(project,claim,current_date)
    for recv in project.receivables:
        if recv.status is not ReceivableStatus.OUTSTANDING: continue
        remaining=recv.remaining_amount
        if remaining<=0:
            recv.status=ReceivableStatus.SETTLED
            continue
        claim=create_guarantee_claim(f"CL{len(project.guarantee_claims)+1:08d}",recv.bike_id,recv.contract_id,recv.tenant_id,"",ClaimSource.FINAL_CLOSURE,remaining,current_date,recovery_rate_pct)
        project.guarantee_claims.append(claim)
        project.accounts_receivable-=remaining
        project.guarantee_claim_receivable+=remaining
        _force_settle(project,claim,current_date)
        recv.remaining_amount=0
        recv.status=ReceivableStatus.SETTLED
        recv.settlement_date=current_date
    for bike in project.bikes:
        if bike.current_state not in {"OWNED_TRANSFERRED","HELD_AS_ASSET"}:
            bike.current_state="HELD_AS_ASSET"
            bike.net_book_value=max(0,bike.gross_cost-bike.accumulated_depreciation)
    project.final_close_date=current_date
    project.final_net_project_equity=project.project_cash+sum(b.net_book_value for b in project.bikes if b.current_state=="HELD_AS_ASSET")
    project.partner1_final_entitlement=(project.final_net_project_equity*70)//100
    project.partner2_final_entitlement=project.final_net_project_equity-project.partner1_final_entitlement
    project.simulation_stopped=True
    return True
