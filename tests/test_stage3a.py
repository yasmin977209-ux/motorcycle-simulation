"""Stage 3A unit tests for Chapters 5–9; no daily engine or Monte Carlo."""

from __future__ import annotations

from datetime import date

import constants
from entities import ClaimStatus
from friday import apply_friday_fee_and_oil, eligible_friday_number, is_eligible_friday
from collection import apply_ordinary_collection
from settlement import (
    SettlementStatus,
    apply_legacy_debt_collection,
    apply_settlement_rent,
    first_settlement_business_day_after,
    settlement_business_days_elapsed,
    settlement_legacy_debt,
    settlement_status,
)
from depreciation import apply_daily_depreciation, apply_ownership_writeoff
from guarantee import (
    can_settle_claim,
    create_guarantee_claim,
    settle_guarantee_claim,
    waiting_days_for_source,
)


# Chapter 5

def test_ch5_friday_eligibility_and_counter() -> None:
    assert eligible_friday_number(date(2027, 1, 2), date(2027, 1, 8)) == 1
    assert is_eligible_friday(date(2027, 1, 2), date(2027, 1, 8))
    assert eligible_friday_number(date(2027, 1, 5), date(2027, 1, 8)) == 0
    assert eligible_friday_number(date(2027, 1, 5), date(2027, 1, 15)) == 1


def test_ch5_friday_fee_oil_and_no_operating_rent() -> None:
    first = apply_friday_fee_and_oil(
        date(2027, 1, 2), date(2027, 1, 8), 0, True
    )
    assert first.revenue_friday_fee == constants.FRIDAY_FEE
    assert first.oil_service_expense == 0
    assert first.cash_delta == 1000
    assert first.partner1_allocation == 700
    assert first.partner2_allocation == 300
    assert first.friday_counter_after == 1
    assert first.operating_rent_due == 0
    assert first.operating_rent_revenue == 0

    second = apply_friday_fee_and_oil(
        date(2027, 1, 2), date(2027, 1, 16), 1, True
    )
    assert second.revenue_friday_fee == 1000
    assert second.oil_service_expense == constants.OIL_SERVICE_COST
    assert second.cash_delta == -1000
    assert second.friday_counter_after == 2

    no_possession = apply_friday_fee_and_oil(
        date(2027, 1, 2), date(2027, 1, 16), 1, False
    )
    assert no_possession.friday_counter_after == 1
    assert no_possession.cash_delta == 0


# Chapter 6

def test_ch6_collection_exact_formula() -> None:
    result = apply_ordinary_collection(3000, 0, 1500, True)
    assert result.prior_arrears == 1500
    assert result.arrears_payment == 1500
    assert result.collected == 3000
    assert result.total_paid_after == 3000
    assert result.outstanding_after == 0
    assert result.accounts_receivable_delta == -3000
    assert result.partner1_allocation == 2100
    assert result.partner2_allocation == 900


def test_ch6_collection_secondary_and_cap() -> None:
    result = apply_ordinary_collection(11000, 0, 1000, True)
    assert result.arrears_payment == 1000
    assert result.collected == 2000
    assert result.total_paid_after == 2000
    assert result.outstanding_after == 9000

    capped = apply_ordinary_collection(2300, 0, 1500, True)
    assert capped.collected == 2300
    assert capped.outstanding_after == 0

    friday = apply_ordinary_collection(
        1500, 0, 1500, True, current_date=date(2027, 1, 1)
    )
    assert friday.collected == 0
    assert friday.total_paid_after == 0


# Chapter 7

def test_ch7_settlement_start_and_legacy_freeze() -> None:
    assert first_settlement_business_day_after(date(2027, 1, 7)) == date(2027, 1, 9)
    assert settlement_legacy_debt(16500, 3000) == 13500


def test_ch7_settlement_rent_and_legacy_payment() -> None:
    rent = apply_settlement_rent(date(2027, 1, 10))
    assert rent.due == 1500
    assert rent.collected == 1500
    assert rent.accounts_receivable_delta == 0

    friday = apply_settlement_rent(date(2027, 1, 15))
    assert friday.due == 0

    step = apply_legacy_debt_collection(3200, True)
    assert step.payment == 1500
    assert step.remaining_after == 1700
    assert not step.completed

    final = apply_legacy_debt_collection(900, True)
    assert final.payment == 900
    assert final.remaining_after == 0
    assert final.completed


def test_ch7_settlement_expiry_starts_after_30_working_days() -> None:
    start = date(2027, 1, 9)
    day_30 = start
    working_days = 1
    while working_days < constants.SETTLEMENT_PERIOD_DAYS:
        day_30 = day_30.fromordinal(day_30.toordinal() + 1)
        if day_30.weekday() != 4:
            working_days += 1
    day_31 = day_30.fromordinal(day_30.toordinal() + 1)
    while day_31.weekday() == 4:
        day_31 = day_31.fromordinal(day_31.toordinal() + 1)

    assert settlement_business_days_elapsed(start, day_30) == 29
    assert settlement_status(start, day_30, 1000) is SettlementStatus.ACTIVE
    assert settlement_business_days_elapsed(start, day_31) == 30
    assert settlement_status(start, day_31, 1000) is SettlementStatus.EXPIRED
    assert settlement_status(start, day_31, 0) is SettlementStatus.COMPLETED


# Chapter 8

def test_ch8_daily_depreciation_includes_use_on_friday() -> None:
    result = apply_daily_depreciation(360000, 0, True)
    assert result.depreciation_recorded == constants.DEPRECIATION_RATE_PER_DAY
    assert result.accumulated_depreciation_after == 50
    assert result.usage_days_after == 1
    assert result.net_book_value_after == 359950


def test_ch8_no_depreciation_outside_tenant_possession_or_after_cap() -> None:
    idle = apply_daily_depreciation(360000, 0, False)
    assert idle.depreciation_recorded == 0

    capped = apply_daily_depreciation(360000, 360000, True)
    assert capped.depreciation_recorded == 0

    partial = apply_daily_depreciation(360000, 359990, True)
    assert partial.depreciation_recorded == 10
    assert partial.accumulated_depreciation_after == 360000
    assert partial.net_book_value_after == 0


def test_ch8_ownership_writeoff_uses_gross_cost_and_does_not_readd_project_depr() -> None:
    result = apply_ownership_writeoff(360000, 120000)
    assert result.old_accumulated_depreciation == 120000
    assert result.writeoff_amount == 240000
    assert result.project_accumulated_depreciation_delta == -120000
    assert result.project_gross_asset_delta == -360000
    assert result.expense_asset_writeoff == 240000
    assert result.bike_accumulated_depreciation_after == 360000
    assert result.bike_net_book_value_after == 0


# Chapter 9

def test_ch9_claim_components_waiting_periods_and_due_dates() -> None:
    assert waiting_days_for_source("PRIMARY_EARLY_TERMINATION") == 30
    assert waiting_days_for_source("SECONDARY_EARLY_TERMINATION") == 20
    assert waiting_days_for_source("POST_MATURITY_SETTLEMENT_FAILURE") == 60
    assert waiting_days_for_source("ADMINISTRATIVE_CLOSURE") == 0
    assert waiting_days_for_source("FINAL_CLOSURE") == 0

    claim = create_guarantee_claim(
        "CL1", "B1", "C1", "T1", "G1",
        "PRIMARY_EARLY_TERMINATION", 45000,
        date(2027, 1, 15), 70
    )
    assert claim.claim_amount == 45000
    assert claim.settlement_due_date == date(2027, 2, 15)
    assert claim.status is ClaimStatus.PENDING


def test_ch9_deterministic_recovery_and_no_double_settlement() -> None:
    for rate, expected_recovered in (
        (100, 45000),
        (70, 31500),
        (50, 22500),
        (30, 13500),
        (0, 0),
    ):
        claim = create_guarantee_claim(
            f"CL{rate}", "B1", "C1", "T1", "G1",
            "PRIMARY_EARLY_TERMINATION", 45000,
            date(2027, 1, 15), rate
        )
        assert not can_settle_claim(claim, date(2027, 2, 14))
        settled = settle_guarantee_claim(claim, date(2027, 2, 15))
        assert settled.settled_now
        assert settled.recovered_amount == expected_recovered
        assert settled.bad_debt_amount == 45000 - expected_recovered
        assert claim.status is ClaimStatus.SETTLED

        second = settle_guarantee_claim(claim, date(2027, 2, 16))
        assert not second.settled_now
        assert second.recovered_amount == expected_recovered
        assert second.bad_debt_amount == 45000 - expected_recovered
