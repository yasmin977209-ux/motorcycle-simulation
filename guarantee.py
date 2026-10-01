"""Chapter 9 guarantee claims and deterministic percentage recovery."""

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


def _waiting_days_for_source(claim_source: str | ClaimSource) -> int:
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
    """Create a pending claim from outstanding rent only."""
    source = ClaimSource(claim_source)
    if outstanding_rent < 0:
        raise ValueError("outstanding_rent must not be negative")
    if isinstance(recovery_rate_pct, bool) or not isinstance(recovery_rate_pct, int):
        raise ValueError("recovery_rate_pct must be an integer percentage")
    if recovery_rate_pct not in GUARANTEE_RECOVERY_RATES:
        raise ValueError("recovery_rate_pct is outside the authoritative rates")

    waiting_days = _waiting_days_for_source(source)
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
        settlement_due_date=settlement_due_date(created_date, waiting_days),
        recovery_rate_pct=recovery_rate_pct,
    )


def can_settle_claim(
    claim: GuaranteeClaim,
    current_date: date,
) -> bool:
    """Return whether an unsettled claim has reached its stored due date."""
    return (
        claim.status is ClaimStatus.PENDING
        and current_date >= claim.settlement_due_date
    )


def settle_guarantee_claim(
    claim: GuaranteeClaim,
    current_date: date,
) -> GuaranteeSettlementResult:
    """Settle once; a second settlement attempt raises ValueError explicitly."""
    if claim.status is ClaimStatus.SETTLED:
        raise ValueError("guarantee claim has already been settled")

    if not can_settle_claim(claim, current_date):
        return GuaranteeSettlementResult(
            settled_now=False,
            recovered_amount=0,
            bad_debt_amount=0,
            claim_amount=claim.claim_amount,
        )

    recovered_amount = (claim.claim_amount * claim.recovery_rate_pct) // 100
    bad_debt_amount = claim.claim_amount - recovered_amount

    claim.recovered_amount = recovered_amount
    claim.bad_debt_amount = bad_debt_amount
    claim.settlement_date = current_date
    claim.status = ClaimStatus.SETTLED

    return GuaranteeSettlementResult(
        settled_now=True,
        recovered_amount=recovered_amount,
        bad_debt_amount=bad_debt_amount,
        claim_amount=claim.claim_amount,
    )


__all__ = [
    "GuaranteeSettlementResult",
    "can_settle_claim",
    "create_guarantee_claim",
    "settle_guarantee_claim",
]
