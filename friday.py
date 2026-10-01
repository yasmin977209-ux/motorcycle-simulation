"""Chapter 5 Friday fee and oil-service rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from constants import (
    FRIDAY_FEE,
    OIL_SERVICE_COST,
    PARTNER1_FINAL_SHARE_PCT,
    PARTNER2_FINAL_SHARE_PCT,
)
from dateutils import is_eligible_friday


@dataclass(frozen=True)
class FridayResult:
    eligible: bool
    revenue_friday_fee: int
    oil_service_expense: int
    cash_delta: int
    partner1_allocation: int
    partner2_allocation: int
    friday_counter_after: int
    operating_rent_due: int = 0
    operating_rent_revenue: int = 0


def apply_friday_fee_and_oil(
    delivery_date: date,
    current_date: date,
    friday_counter: int,
    in_tenant_possession: bool,
) -> FridayResult:
    """Apply one eligible-Friday snapshot without touching daily-engine state."""
    if friday_counter < 0:
        raise ValueError("friday_counter must not be negative")

    eligible = (
        in_tenant_possession
        and is_eligible_friday(delivery_date, current_date)
    )
    if not eligible:
        return FridayResult(
            eligible=False,
            revenue_friday_fee=0,
            oil_service_expense=0,
            cash_delta=0,
            partner1_allocation=0,
            partner2_allocation=0,
            friday_counter_after=friday_counter,
        )

    counter_after = friday_counter + 1
    fee = FRIDAY_FEE
    oil = OIL_SERVICE_COST if counter_after % 2 == 0 else 0
    return FridayResult(
        eligible=True,
        revenue_friday_fee=fee,
        oil_service_expense=oil,
        cash_delta=fee - oil,
        partner1_allocation=(fee * PARTNER1_FINAL_SHARE_PCT) // 100,
        partner2_allocation=(fee * PARTNER2_FINAL_SHARE_PCT) // 100,
        friday_counter_after=counter_after,
    )


__all__ = ["FridayResult", "apply_friday_fee_and_oil"]
