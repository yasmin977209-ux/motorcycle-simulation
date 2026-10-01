"""Chapter 6 ordinary collection formula."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from constants import PARTNER1_FINAL_SHARE_PCT, PARTNER2_FINAL_SHARE_PCT
from dateutils import is_friday


@dataclass(frozen=True)
class CollectionResult:
    collected: int
    total_paid_after: int
    outstanding_before: int
    outstanding_after: int
    prior_arrears: int
    arrears_payment: int
    cash_delta: int
    accounts_receivable_delta: int
    partner1_allocation: int
    partner2_allocation: int


def apply_ordinary_collection(
    total_due: int,
    total_paid: int,
    daily_rate: int,
    success: bool,
    current_date: date,
) -> CollectionResult:
    """Apply the reference collection rule; Friday is a strict no-collection day."""
    if total_due < 0 or total_paid < 0:
        raise ValueError("total_due and total_paid must not be negative")
    if total_paid > total_due:
        raise ValueError("total_paid must not exceed total_due")
    if daily_rate <= 0:
        raise ValueError("daily_rate must be positive")

    outstanding = total_due - total_paid
    prior_arrears = max(0, outstanding - daily_rate)

    if is_friday(current_date) or not success or outstanding == 0:
        return CollectionResult(
            collected=0,
            total_paid_after=total_paid,
            outstanding_before=outstanding,
            outstanding_after=outstanding,
            prior_arrears=prior_arrears,
            arrears_payment=0,
            cash_delta=0,
            accounts_receivable_delta=0,
            partner1_allocation=0,
            partner2_allocation=0,
        )

    arrears_payment = min(daily_rate, prior_arrears)
    collected = min(daily_rate + arrears_payment, outstanding)
    total_paid_after = total_paid + collected
    outstanding_after = total_due - total_paid_after

    return CollectionResult(
        collected=collected,
        total_paid_after=total_paid_after,
        outstanding_before=outstanding,
        outstanding_after=outstanding_after,
        prior_arrears=prior_arrears,
        arrears_payment=arrears_payment,
        cash_delta=collected,
        accounts_receivable_delta=-collected,
        partner1_allocation=(collected * PARTNER1_FINAL_SHARE_PCT) // 100,
        partner2_allocation=(collected * PARTNER2_FINAL_SHARE_PCT) // 100,
    )


__all__ = ["CollectionResult", "apply_ordinary_collection"]
