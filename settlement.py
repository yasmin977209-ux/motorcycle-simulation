"""Chapter 7 post-maturity settlement rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum

from constants import SETTLEMENT_DAILY_RENT, SETTLEMENT_PERIOD_DAYS
from dateutils import is_business_day, is_friday


class SettlementStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class SettlementRentResult:
    due: int
    collected: int
    cash_delta: int
    accounts_receivable_delta: int


@dataclass(frozen=True)
class LegacyDebtCollectionResult:
    payment: int
    remaining_after: int
    completed: bool
    cash_delta: int
    accounts_receivable_delta: int


def first_settlement_business_day_after(maturity_date: date) -> date:
    """Return the first business day strictly after maturity."""
    current = maturity_date + timedelta(days=1)
    while not is_business_day(current):
        current += timedelta(days=1)
    return current


def settlement_legacy_debt(total_due: int, total_paid: int) -> int:
    """Freeze the legacy debt at settlement entry."""
    if total_due < 0 or total_paid < 0 or total_paid > total_due:
        raise ValueError("Invalid contract due/paid amounts")
    return total_due - total_paid


def settlement_business_days_elapsed(
    settlement_start_date: date,
    current_date: date,
) -> int:
    """Return elapsed settlement business days using the reference day-1 convention."""
    if current_date < settlement_start_date:
        raise ValueError("current_date must not precede settlement_start_date")
    if current_date == settlement_start_date:
        return 0

    business_days = 0
    current = settlement_start_date
    while current <= current_date:
        if is_business_day(current):
            business_days += 1
        current += timedelta(days=1)
    return max(0, business_days - 1)


def apply_settlement_rent(current_date: date) -> SettlementRentResult:
    """Collect deterministic settlement rent on business days only."""
    if is_friday(current_date):
        return SettlementRentResult(0, 0, 0, 0)
    return SettlementRentResult(
        due=SETTLEMENT_DAILY_RENT,
        collected=SETTLEMENT_DAILY_RENT,
        cash_delta=SETTLEMENT_DAILY_RENT,
        accounts_receivable_delta=0,
    )


def apply_legacy_debt_collection(
    remaining_debt: int,
    success: bool,
) -> LegacyDebtCollectionResult:
    """Apply one successful independent legacy-debt payment, capped at the daily rate."""
    if remaining_debt < 0:
        raise ValueError("remaining_debt must not be negative")
    if not success or remaining_debt == 0:
        return LegacyDebtCollectionResult(
            payment=0,
            remaining_after=remaining_debt,
            completed=remaining_debt == 0,
            cash_delta=0,
            accounts_receivable_delta=0,
        )

    payment = min(SETTLEMENT_DAILY_RENT, remaining_debt)
    remaining_after = remaining_debt - payment
    return LegacyDebtCollectionResult(
        payment=payment,
        remaining_after=remaining_after,
        completed=remaining_after == 0,
        cash_delta=payment,
        accounts_receivable_delta=-payment,
    )


def _settlement_status(
    settlement_start_date: date | None,
    current_date: date,
    remaining_debt: int,
) -> SettlementStatus:
    """Internal lifecycle helper; not a public Stage 3A contract."""
    if remaining_debt < 0:
        raise ValueError("remaining_debt must not be negative")
    if settlement_start_date is None or current_date < settlement_start_date:
        return SettlementStatus.NOT_STARTED
    if remaining_debt == 0:
        return SettlementStatus.COMPLETED
    if is_friday(current_date):
        return SettlementStatus.ACTIVE
    if settlement_business_days_elapsed(
        settlement_start_date,
        current_date,
    ) >= SETTLEMENT_PERIOD_DAYS:
        return SettlementStatus.EXPIRED
    return SettlementStatus.ACTIVE


__all__ = [
    "SettlementStatus",
    "SettlementRentResult",
    "LegacyDebtCollectionResult",
    "first_settlement_business_day_after",
    "settlement_legacy_debt",
    "settlement_business_days_elapsed",
    "apply_settlement_rent",
    "apply_legacy_debt_collection",
]
