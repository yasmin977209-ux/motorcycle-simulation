"""Chapter 7 — post-maturity settlement rules, isolated from the daily engine."""

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
    """Freeze the old debt at settlement entry."""

    if total_due < 0 or total_paid < 0 or total_paid > total_due:
        raise ValueError("Invalid contract due/paid amounts")
    return total_due - total_paid


def settlement_business_days_elapsed(
    settlement_start_date: date,
    current_date: date,
) -> int:
    """Count completed settlement business days before current_date.

    The settlement start day is day 1 of the period but has zero elapsed
    days at its beginning. Thus the 30th working day has elapsed=29; the
    next working day has elapsed=30 and is the first day eligible for the
    expiry transition.
    """

    if current_date <= settlement_start_date:
        return 0

    if is_friday(current_date):
        current = settlement_start_date
        business_days = 0
        while current < current_date:
            if is_business_day(current):
                business_days += 1
            current += timedelta(days=1)
        return max(0, business_days - 1)

    current = settlement_start_date
    business_days = 0
    while current <= current_date:
        if is_business_day(current):
            business_days += 1
        current += timedelta(days=1)
    return max(0, business_days - 1)


def apply_settlement_rent(current_date: date) -> SettlementRentResult:
    """Apply the deterministic 1,500 settlement rent on business days only."""

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
    """Apply one independent 1,500 legacy-debt payment attempt."""

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


def settlement_status(
    settlement_start_date: date | None,
    current_date: date,
    remaining_debt: int,
) -> SettlementStatus:
    """Classify settlement status without mutating bike/contract state."""

    if remaining_debt < 0:
        raise ValueError("remaining_debt must not be negative")
    if settlement_start_date is None:
        return SettlementStatus.NOT_STARTED
    if current_date < settlement_start_date:
        return SettlementStatus.NOT_STARTED
    if remaining_debt == 0:
        return SettlementStatus.COMPLETED

    elapsed = settlement_business_days_elapsed(
        settlement_start_date,
        current_date,
    )

    # M13 only runs on working days. A Friday between working days leaves
    # the lifecycle state unchanged until the next working day.
    if not is_business_day(current_date):
        return SettlementStatus.ACTIVE

    if elapsed >= SETTLEMENT_PERIOD_DAYS:
        return SettlementStatus.EXPIRED
    return SettlementStatus.ACTIVE


__all__ = [
    "LegacyDebtCollectionResult",
    "SettlementRentResult",
    "SettlementStatus",
    "apply_legacy_debt_collection",
    "apply_settlement_rent",
    "first_settlement_business_day_after",
    "settlement_business_days_elapsed",
    "settlement_legacy_debt",
    "settlement_status",
]
