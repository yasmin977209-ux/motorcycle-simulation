"""Chapter 9 — guarantee claims and deterministic recovery, isolated."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from constants import CLAIM_WAITING_PERIODS_DAYS, GUARANTEE_RECOVERY_RATES
from dateutils import settlement_due_date
from entities import ClaimSource, ClaimStatus, GuaranteeClaim


@dataclass(frozen=True)
class GuaranteeSettlementResult:
    settled_now: bool
    recovered_amount: int
    bad_debt_amount: int
    claim_amount: int


def waiting_days_for_source(claim_source: str | ClaimSource) -> int:
    source = ClaimSource(claim_source)
    return CLAIM_WAITING_PERIODS_DAYS[source.value]


def create_guarantee_claim(
    claim_id: str,
    bike_id: str,
    contract_id: str,
    tenant_id: str,
    guarantor_id: str,
    claim_source: str | ClaimSource,
    outstanding_rent: int,
    created_date: date,
    recovery_rate_pct: int,
) -> GuaranteeClaim:
    """Create one pending claim using outstanding rent only as its amount."""

    source = ClaimSource(claim_source)

    if outstanding_rent < 0:
        raise ValueError("outstanding_rent must not be negative")
    if isinstance(recovery_rate_pct, bool) or not isinstance(recovery_rate_pct, int):
        raise ValueError("recovery_rate_pct must be an integer percentage")
    if recovery_rate_pct not in GUARANTEE_RECOVERY_RATES:
        raise ValueError(
            f"Unsupported recovery rate: {recovery_rate_pct!r}"
        )

    waiting_days = waiting_days_for_source(source)
    due_date = settlement_due_date(created_date, waiting_days)

    return GuaranteeClaim(
        claim_id=claim_id,
        bike_id=bike_id,
        contract_id=contract_id,
        tenant_id=tenant_id,
        guarantor_id=guarantor_id,
        claim_source=source,
        claim_amount=outstanding_rent,
        created_date=created_date,
        waiting_period_days=waiting_days,
        settlement_due_date=due_date,
        recovery_rate_pct=recovery_rate_pct,
    )


def can_settle_claim(claim: GuaranteeClaim, current_date: date) -> bool:
    """Normal (non-forced) settlement eligibility."""

    return (
        claim.status is ClaimStatus.PENDING
        and current_date >= claim.settlement_due_date
    )


def settle_guarantee_claim(
    claim: GuaranteeClaim,
    current_date: date,
) -> GuaranteeSettlementResult:
    """Settle one pending claim once, using the deterministic percentage."""

    if claim.status is ClaimStatus.SETTLED:
        recovered = claim.recovered_amount or 0
        bad_debt = claim.bad_debt_amount or 0
        return GuaranteeSettlementResult(
            settled_now=False,
            recovered_amount=recovered,
            bad_debt_amount=bad_debt,
            claim_amount=claim.claim_amount,
        )

    if not can_settle_claim(claim, current_date):
        return GuaranteeSettlementResult(
            settled_now=False,
            recovered_amount=0,
            bad_debt_amount=0,
            claim_amount=claim.claim_amount,
        )

    recovered = (claim.claim_amount * claim.recovery_rate_pct) // 100
    bad_debt = claim.claim_amount - recovered

    claim.recovered_amount = recovered
    claim.bad_debt_amount = bad_debt
    claim.settlement_date = current_date
    claim.status = ClaimStatus.SETTLED

    return GuaranteeSettlementResult(
        settled_now=True,
        recovered_amount=recovered,
        bad_debt_amount=bad_debt,
        claim_amount=claim.claim_amount,
    )


__all__ = [
    "GuaranteeSettlementResult",
    "can_settle_claim",
    "create_guarantee_claim",
    "settle_guarantee_claim",
    "waiting_days_for_source",
]
