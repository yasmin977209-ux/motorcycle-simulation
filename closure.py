"""Chapter 13 dynamic closure rebuilt from the authoritative reference."""

from __future__ import annotations

from datetime import date

from accounting import settle_guarantee_accounting
from constants import (
    CLAIM_SOURCE_ADMINISTRATIVE_CLOSURE,
    CLAIM_SOURCE_FINAL_CLOSURE,
    CUSTOMS_AND_REGISTRATION_COST,
    EXPANSION_CUTOFF_DATE,
    PREP_OPERATING_EXPENSE_PER_BIKE,
)
from entities import (
    BikeState,
    ClaimStatus,
    EventLogEntry,
    EventType,
    Project,
    ReceivableStatus,
)
from guarantee import create_guarantee_claim, settle_guarantee_claim
from partner_equity import allocate_inflow


def closure_preconditions_met(project: Project, current_date: date) -> bool:
    no_prep = not any(b.current_state is BikeState.PREP for b in project.bikes)
    no_primary_active = not any(
        b.current_state
        in {
            BikeState.ACTIVE_PRIMARY,
            BikeState.WAITING_PRIMARY,
            BikeState.NOTICE_PRIMARY,
            BikeState.GRACE_PRIMARY,
        }
        for b in project.bikes
    )
    no_settlement_active = not any(
        b.current_state is BikeState.POST_MATURITY_SETTLEMENT
        for b in project.bikes
    )
    expansion_window_closed = current_date > EXPANSION_CUTOFF_DATE
    return (
        no_prep
        and no_primary_active
        and no_settlement_active
        and expansion_window_closed
    )



def _remaining_prep_funding(bike) -> int:
    return (
        (0 if bike.prep_paid else PREP_OPERATING_EXPENSE_PER_BIKE)
        + (0 if bike.customs_paid else CUSTOMS_AND_REGISTRATION_COST)
    )


def stall_detected(project: Project) -> bool:
    """Detect only a provably state-based deadlock; never use elapsed time."""
    underfunded = [
        (bike, _remaining_prep_funding(bike))
        for bike in project.bikes
        if bike.current_state is BikeState.PREP
        and _remaining_prep_funding(bike) > 0
    ]
    if not underfunded:
        return False
    if not any(
        project.project_cash < remaining
        or project.partner1_reinvestment_balance < remaining
        for _, remaining in underfunded
    ):
        return False

    cash_generating_or_reactivatable = {
        BikeState.ACTIVE_PRIMARY,
        BikeState.WAITING_PRIMARY,
        BikeState.NOTICE_PRIMARY,
        BikeState.GRACE_PRIMARY,
        BikeState.POST_MATURITY_SETTLEMENT,
        BikeState.ACTIVE_SECONDARY,
        BikeState.NOTICE_SECONDARY,
        BikeState.AVAILABLE_FOR_SECONDARY,
    }
    if any(
        bike.current_state in cash_generating_or_reactivatable
        for bike in project.bikes
    ):
        return False
    if any(claim.status is ClaimStatus.PENDING for claim in project.guarantee_claims):
        return False
    return True


def stall_state_summary(project: Project) -> dict[str, object]:
    return {
        "Cash": project.project_cash,
        "Partner1_Reinvestment_Balance": project.partner1_reinvestment_balance,
        "Partner2_Reinvestment_Balance": project.partner2_reinvestment_balance,
        "bikes": [
            {
                "bike_id": bike.bike_id,
                "current_state": bike.current_state.value,
                "prep_paid": bike.prep_paid,
                "customs_paid": bike.customs_paid,
                "remaining_prep_funding": _remaining_prep_funding(bike),
            }
            for bike in project.bikes
        ],
        "claims": [
            {
                "claim_id": claim.claim_id,
                "status": claim.status.value,
                "claim_amount": claim.claim_amount,
                "settlement_due_date": claim.settlement_due_date.isoformat(),
            }
            for claim in project.guarantee_claims
        ],
    }


class SimulationStall(RuntimeError):
    def __init__(self, state_summary: dict[str, object]):
        self.error_code = "STALL_DETECTED"
        self.state_summary = state_summary
        super().__init__(f"STALL_DETECTED: {state_summary}")


def raise_if_stalled(project: Project, current_date: date) -> None:
    if not stall_detected(project):
        return
    summary = stall_state_summary(project)
    project.error_log.append(
        {
            "date": current_date.isoformat(),
            "error_code": "STALL_DETECTED",
            "state_summary": summary,
        }
    )
    raise SimulationStall(summary)


def _metric(project: Project, key: str, amount: int) -> None:
    if hasattr(project, "_day_metrics"):
        project._day_metrics[key] += amount


def _event(project: Project, current_date: date, bike_id: str, event_type: EventType, contract_id: str | None = None, amount: int | None = None) -> None:
    if not project.log_events:
        return

    event = EventLogEntry(
        event_id=f"EV{len(project.event_log) + 1:08d}",
        date=current_date,
        bike_id=bike_id,
        event_type=event_type,
        contract_id=contract_id,
        amount_if_applicable=amount,
    )
    project.event_log.append(event)
    bike = next((b for b in project.bikes if b.bike_id == bike_id), None)
    if bike is not None:
        bike.lifecycle_history.append(event)


def _force_settle(project: Project, claim, current_date: date) -> None:
    if claim.status is ClaimStatus.SETTLED:
        return
    result = settle_guarantee_claim(claim, current_date)
    if not result.settled_now:
        recovered = (claim.claim_amount * claim.recovery_rate_pct) // 100
        bad_debt = claim.claim_amount - recovered
        claim.recovered_amount = recovered
        claim.bad_debt_amount = bad_debt
        claim.settlement_date = current_date
        claim.status = ClaimStatus.SETTLED
    else:
        recovered = result.recovered_amount
        bad_debt = result.bad_debt_amount
    settle_guarantee_accounting(
        project,
        claim.claim_amount,
        recovered,
        bad_debt,
    )
    _metric(project, "cash_inflows", recovered)
    allocate_inflow(project, recovered)


def execute_dynamic_closure(
    project: Project,
    current_date: date,
    recovery_rate_pct: int,
) -> bool:
    if not closure_preconditions_met(project, current_date):
        return False

    for bike in project.bikes:
        if bike.current_state not in {
            BikeState.ACTIVE_SECONDARY,
            BikeState.NOTICE_SECONDARY,
        }:
            continue
        if bike.current_contract_id is None:
            continue
        contract = project.contracts.get(bike.current_contract_id)
        if contract is None:
            raise AssertionError("secondary bike lost its current contract")
        outstanding = contract.total_due - contract.total_paid
        if outstanding > 0:
            claim_id = f"CL{len(project.guarantee_claims) + 1:08d}"
            claim = create_guarantee_claim(
                claim_id,
                bike.bike_id,
                contract.contract_id,
                contract.tenant_id,
                contract.guarantor_id,
                CLAIM_SOURCE_ADMINISTRATIVE_CLOSURE,
                outstanding,
                current_date,
                recovery_rate_pct,
            )
            project.guarantee_claims.append(claim)
            project.accounts_receivable -= outstanding
            project.guarantee_claim_receivable += outstanding
            _metric(project, "ar_transfers_to_guarantee", outstanding)
        contract.status = contract.status.TERMINATED
        previous = bike.current_state
        bike.current_state = BikeState.HELD_AS_ASSET
        bike.current_contract_id = None
        bike.current_tenant_id = None
        _event(
            project,
            current_date,
            bike.bike_id,
            EventType.ADMINISTRATIVE_CLOSURE,
            contract.contract_id,
            outstanding,
        )

    for claim in project.guarantee_claims:
        if claim.status is ClaimStatus.PENDING:
            _force_settle(project, claim, current_date)

    for receivable in project.receivables:
        if receivable.status is not ReceivableStatus.OUTSTANDING:
            continue
        remaining = receivable.remaining_amount
        if remaining <= 0:
            receivable.status = ReceivableStatus.SETTLED
            continue
        contract = project.contracts.get(receivable.contract_id)
        guarantor_id = contract.guarantor_id if contract is not None else ""
        claim_id = f"CL{len(project.guarantee_claims) + 1:08d}"
        claim = create_guarantee_claim(
            claim_id,
            receivable.bike_id,
            receivable.contract_id,
            receivable.tenant_id,
            guarantor_id,
            CLAIM_SOURCE_FINAL_CLOSURE,
            remaining,
            current_date,
            recovery_rate_pct,
        )
        project.guarantee_claims.append(claim)
        project.accounts_receivable -= remaining
        project.guarantee_claim_receivable += remaining
        _metric(project, "ar_transfers_to_guarantee", remaining)
        receivable.status = ReceivableStatus.SETTLED
        receivable.remaining_amount = 0
        _force_settle(project, claim, current_date)

    if project.accounts_receivable > 0:
        project.bad_debt_expense += project.accounts_receivable
        project.accounts_receivable = 0

    for bike in project.bikes:
        if bike.current_state in {
            BikeState.OWNED_TRANSFERRED,
            BikeState.HELD_AS_ASSET,
        }:
            continue
        previous = bike.current_state
        bike.current_state = BikeState.HELD_AS_ASSET
        _event(
            project,
            current_date,
            bike.bike_id,
            EventType.FINAL_ASSET_HELD,
        )

    project.final_close_date = current_date
    project.simulation_stopped = True
    return True


__all__ = [
    "closure_preconditions_met",
    "execute_dynamic_closure",
    "stall_detected",
    "stall_state_summary",
    "SimulationStall",
    "raise_if_stalled",
]
