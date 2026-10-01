"""Calendar/date utilities governed by Chapters 1, 2, and 5.

Model calendar rule: every day except Friday is a business day. Therefore
Saturday and Sunday are business days in this simulation.

Important reference reconciliation:
Chapter 5.2's written rule is authoritative for the Friday pattern.
The dated Friday examples printed in that section are off by one calendar day
for the actual 2027 calendar. This module follows the written rule and the
actual calendar; the discrepancy is documented in README.md and must not be
hidden by changing the rule.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Final

from dateutil.relativedelta import relativedelta

from constants import (
    BIKE_PREP_SCHEDULE_DAYS,
    CLAIM_WAITING_PERIODS_DAYS,
    EXPANSION_CUTOFF_DATE,
    INITIAL_FLEET_READY_DATE,
    INITIAL_FLEET_PURCHASE_DATE,
    PRIMARY_CONTRACT_MONTHS,
    PROJECT_START_DATE,
)


FRIDAY_WEEKDAY: Final[int] = 4


def is_friday(day: date) -> bool:
    return day.weekday() == FRIDAY_WEEKDAY


def is_business_day(day: date) -> bool:
    return not is_friday(day)


def next_business_day_on_or_after(day: date) -> date:
    current = day
    while not is_business_day(current):
        current += timedelta(days=1)
    return current


def scheduled_ready_date(purchase_date: date) -> date:
    """Reference: purchase_date + 6 calendar days."""
    return purchase_date + timedelta(days=BIKE_PREP_SCHEDULE_DAYS)


def primary_maturity_date(start_date: date) -> date:
    """Reference: primary start + 24 calendar months."""
    return start_date + relativedelta(months=PRIMARY_CONTRACT_MONTHS)


def settlement_due_date(created_date: date, waiting_period_days: int) -> date:
    """Reference: period 0 => D; otherwise D + period + 1 calendar days."""
    if waiting_period_days < 0:
        raise ValueError("waiting_period_days must not be negative")
    if waiting_period_days == 0:
        return created_date
    return created_date + timedelta(days=waiting_period_days + 1)


def claim_waiting_period_days(claim_source: str) -> int:
    try:
        return CLAIM_WAITING_PERIODS_DAYS[claim_source]
    except KeyError as exc:
        raise ValueError(f"Unknown claim source: {claim_source!r}") from exc


def first_following_friday(delivery_date: date) -> date:
    """First Friday strictly after delivery."""
    if is_friday(delivery_date):
        raise ValueError("Friday delivery is prohibited by the reference.")
    delta = (FRIDAY_WEEKDAY - delivery_date.weekday()) % 7
    if delta == 0:
        delta = 7
    return delivery_date + timedelta(days=delta)


def first_eligible_friday(delivery_date: date) -> date:
    """First eligible Friday under the exact Chapter 5.2 written rule."""
    first_friday = first_following_friday(delivery_date)
    # Tuesday, Wednesday, Thursday deliveries exempt the first Friday.
    if delivery_date.weekday() in (1, 2, 3):
        return first_friday + timedelta(days=7)
    return first_friday


def is_eligible_friday(delivery_date: date, current_date: date) -> bool:
    if not is_friday(current_date):
        return False
    first_eligible = first_eligible_friday(delivery_date)
    return current_date >= first_eligible and (
        (current_date - first_eligible).days % 7 == 0
    )


def eligible_friday_number(delivery_date: date, current_date: date) -> int:
    if not is_eligible_friday(delivery_date, current_date):
        return 0
    first_eligible = first_eligible_friday(delivery_date)
    return ((current_date - first_eligible).days // 7) + 1


def eligible_friday_dates(
    delivery_date: date, through_date: date
) -> tuple[date, ...]:
    if through_date < delivery_date:
        return ()
    first_eligible = first_eligible_friday(delivery_date)
    if first_eligible > through_date:
        return ()
    count = ((through_date - first_eligible).days // 7) + 1
    return tuple(first_eligible + timedelta(days=7 * i) for i in range(count))


def add_calendar_days(day: date, days: int) -> date:
    return day + timedelta(days=days)


# Corrected by actual 2027 calendar while preserving the written rule:
# Saturday/Sunday/Monday -> first following Friday;
# Tuesday/Wednesday/Thursday -> first following Friday exempt, next Friday eligible.
REFERENCE_FRIDAY_EXAMPLES: Final[dict[date, date]] = {
    date(2027, 1, 2): date(2027, 1, 8),
    date(2027, 1, 3): date(2027, 1, 8),
    date(2027, 1, 4): date(2027, 1, 8),
    date(2027, 1, 5): date(2027, 1, 15),
    date(2027, 1, 6): date(2027, 1, 15),
    date(2027, 1, 7): date(2027, 1, 15),
}


# Deterministic reference/date checks.
assert is_friday(PROJECT_START_DATE)
assert is_business_day(date(2027, 1, 2))
assert is_business_day(date(2027, 1, 3))
assert not is_business_day(date(2027, 1, 1))
assert scheduled_ready_date(INITIAL_FLEET_PURCHASE_DATE) == INITIAL_FLEET_READY_DATE
assert next_business_day_on_or_after(INITIAL_FLEET_READY_DATE) == date(2027, 1, 2)
assert INITIAL_FLEET_READY_DATE == PROJECT_START_DATE
assert EXPANSION_CUTOFF_DATE == date(2030, 12, 31)

for delivery, expected in REFERENCE_FRIDAY_EXAMPLES.items():
    assert first_eligible_friday(delivery) == expected
    assert is_friday(expected)

assert settlement_due_date(date(2027, 1, 15), 20) == date(2027, 2, 5)
assert settlement_due_date(date(2027, 1, 15), 30) == date(2027, 2, 15)
assert settlement_due_date(date(2027, 1, 15), 60) == date(2027, 3, 17)
assert settlement_due_date(date(2027, 1, 15), 0) == date(2027, 1, 15)
