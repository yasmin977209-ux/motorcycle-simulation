"""Stage 3A unit tests for Chapters 5–9; no daily loop."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

import constants
import dateutils
from collection import apply_ordinary_collection
from depreciation import apply_daily_depreciation, apply_ownership_writeoff
from entities import ClaimStatus
from friday import apply_friday_fee_and_oil
from guarantee import can_settle_claim, create_guarantee_claim, settle_guarantee_claim
from settlement import (
    SettlementStatus,
    _settlement_status,
    apply_legacy_debt_collection,
    apply_settlement_rent,
    first_settlement_business_day_after,
    settlement_business_days_elapsed,
    settlement_legacy_debt,
)


def _next_business_day() -> date:
    return dateutils.next_business_day_on_or_after(constants.PROJECT_START_DATE)


def _nth_business_day(start: date, n: int) -> date:
    current = start
    count = 0
    while True:
        if dateutils.is_business_day(current):
            count += 1
        if count == n:
            return current
        current += timedelta(days=1)


# Chapter 5

def test_ch5_2_six_delivery_weekdays_use_dateutils_for_all_fridays() -> None:
    deliveries = tuple(date(2027, 1, day) for day in range(2, 8))
    for delivery in deliveries:
        first_following = dateutils.first_following_friday(delivery)
        eligible = dateutils.first_eligible_friday(delivery)

        first_result = apply_friday_fee_and_oil(delivery, eligible, 0, True)
        assert first_result.eligible
        assert first_result.friday_counter_after == 1

        if delivery.weekday() in (1, 2, 3):
            assert eligible != first_following
            assert not dateutils.is_eligible_friday(delivery, first_following)
        else:
            assert eligible == first_following
            assert dateutils.is_eligible_friday(delivery, first_following)


def test_ch5_3_counter_continues_on_same_contract_and_new_contract_resets() -> None:
    delivery = date(2027, 1, 2)
    first = dateutils.first_eligible_friday(delivery)
    fridays = dateutils.eligible_friday_dates(delivery, first + timedelta(days=21))

    one = apply_friday_fee_and_oil(delivery, fridays[0], 0, True)
    two = apply_friday_fee_and_oil(delivery, fridays[1], one.friday_counter_after, True)
    new_contract = apply_friday_fee_and_oil(
        delivery,
        fridays[2],
        0,
        True,
    )

    assert one.friday_counter_after == 1
    assert two.friday_counter_after == 2
    assert new_contract.friday_counter_after == 1


def test_ch5_4_fee_is_deterministic_and_allocated_seventy_thirty() -> None:
    delivery = date(2027, 1, 2)
    eligible = dateutils.first_eligible_friday(delivery)
    result = apply_friday_fee_and_oil(delivery, eligible, 0, True)

    assert result.revenue_friday_fee == constants.FRIDAY_FEE
    assert result.oil_service_expense == 0
    assert result.partner1_allocation == (constants.FRIDAY_FEE * constants.PARTNER1_FINAL_SHARE_PCT) // 100
    assert result.partner2_allocation == (constants.FRIDAY_FEE * constants.PARTNER2_FINAL_SHARE_PCT) // 100
    assert result.cash_delta == constants.FRIDAY_FEE
    assert result.operating_rent_due == 0
    assert result.operating_rent_revenue == 0


def test_ch5_5_even_counter_runs_oil_service_with_full_gross_entries() -> None:
    delivery = date(2027, 1, 2)
    first = dateutils.first_eligible_friday(delivery)
    second = dateutils.eligible_friday_dates(
        delivery,
        first + timedelta(days=7),
    )[1]
    result = apply_friday_fee_and_oil(delivery, second, 1, True)

    assert result.friday_counter_after == 2
    assert result.oil_service_expense == constants.OIL_SERVICE_COST
    assert result.cash_delta == constants.FRIDAY_FEE - constants.OIL_SERVICE_COST


def test_ch5_non_possession_has_no_friday_effect() -> None:
    delivery = date(2027, 1, 2)
    eligible = dateutils.first_eligible_friday(delivery)
    result = apply_friday_fee_and_oil(delivery, eligible, 0, False)
    assert not result.eligible
    assert result.friday_counter_after == 0
    assert result.cash_delta == 0


# Chapter 6

def test_ch6_2_five_reference_rows_exact() -> None:
    current = _next_business_day()
    rows = (
        (1500, 0, 1500, 0, 0, 1500, 0),
        (3000, 0, 1500, 1500, 1500, 3000, 0),
        (2300, 0, 1500, 800, 800, 2300, 0),
        (16500, 0, 1500, 15000, 1500, 3000, 13500),
        (11000, 0, 1000, 10000, 1000, 2000, 9000),
    )
    for total_due, total_paid, rate, arrears, payment, collected, remaining in rows:
        result = apply_ordinary_collection(
            total_due,
            total_paid,
            rate,
            True,
            current,
        )
        assert result.prior_arrears == arrears
        assert result.arrears_payment == payment
        assert result.collected == collected
        assert result.outstanding_after == remaining
        assert result.total_paid_after == total_paid + collected
        assert result.total_paid_after <= total_due


def test_ch6_3_friday_has_zero_collection_effect_and_failed_attempt_has_none() -> None:
    friday = dateutils.first_following_friday(_next_business_day())
    friday_result = apply_ordinary_collection(3000, 0, 1500, True, friday)
    failed = apply_ordinary_collection(3000, 0, 1500, False, _next_business_day())

    assert friday_result.collected == 0
    assert friday_result.total_paid_after == 0
    assert friday_result.cash_delta == 0
    assert friday_result.accounts_receivable_delta == 0
    assert failed.collected == 0
    assert failed.outstanding_after == 3000


# Chapter 7

def test_ch7_1_first_business_day_after_maturity_and_thirty_day_boundary() -> None:
    maturity = constants.PROJECT_START_DATE
    first = first_settlement_business_day_after(maturity)
    assert first == dateutils.next_business_day_on_or_after(maturity + timedelta(days=1))

    day30 = _nth_business_day(first, constants.SETTLEMENT_PERIOD_DAYS)
    day31 = _nth_business_day(day30 + timedelta(days=1), 1)

    assert settlement_business_days_elapsed(first, first) == 0
    assert settlement_business_days_elapsed(first, day30) == constants.SETTLEMENT_PERIOD_DAYS - 1
    assert settlement_business_days_elapsed(first, day31) == constants.SETTLEMENT_PERIOD_DAYS


def test_ch7_2_settlement_rent_is_fixed_and_ar_neutral() -> None:
    business = _next_business_day()
    friday = dateutils.first_following_friday(business)
    rent = apply_settlement_rent(business)
    friday_rent = apply_settlement_rent(friday)

    assert rent.due == constants.SETTLEMENT_DAILY_RENT
    assert rent.collected == constants.SETTLEMENT_DAILY_RENT
    assert rent.cash_delta == constants.SETTLEMENT_DAILY_RENT
    assert rent.accounts_receivable_delta == 0
    assert friday_rent == type(rent)(0, 0, 0, 0)


def test_ch7_3_legacy_debt_is_frozen_and_each_success_pays_at_most_one_day() -> None:
    remaining = settlement_legacy_debt(16500, 3000)
    success = apply_legacy_debt_collection(remaining, True)
    failure = apply_legacy_debt_collection(success.remaining_after, False)

    assert remaining == 13500
    assert success.payment == constants.SETTLEMENT_DAILY_RENT
    assert success.remaining_after == remaining - constants.SETTLEMENT_DAILY_RENT
    assert success.accounts_receivable_delta == -success.payment
    assert failure.payment == 0
    assert failure.remaining_after == success.remaining_after


def test_ch7_4_full_legacy_payment_completes_immediately() -> None:
    result = apply_legacy_debt_collection(constants.SETTLEMENT_DAILY_RENT - 600, True)
    assert result.payment == constants.SETTLEMENT_DAILY_RENT - 600
    assert result.completed


def test_ch7_5_expiry_happens_after_the_thirtieth_working_day() -> None:
    start = _next_business_day()
    day30 = _nth_business_day(start, constants.SETTLEMENT_PERIOD_DAYS)
    day31 = _nth_business_day(day30 + timedelta(days=1), 1)

    assert _settlement_status(start, day30, 1000) is SettlementStatus.ACTIVE
    assert _settlement_status(start, day31, 1000) is SettlementStatus.EXPIRED
    assert _settlement_status(start, day31, 0) is SettlementStatus.COMPLETED


def test_ch7_6_friday_counter_and_depreciation_continue_during_settlement() -> None:
    delivery = date(2027, 1, 2)
    first = dateutils.first_eligible_friday(delivery)
    second = dateutils.eligible_friday_dates(
        delivery,
        first + timedelta(days=7),
    )[1]

    friday = apply_friday_fee_and_oil(delivery, second, 1, True)
    depreciation = apply_daily_depreciation(
        constants.BIKE_GROSS_ASSET_COST,
        0,
        True,
    )

    assert friday.friday_counter_after == 2
    assert depreciation.depreciation_recorded == constants.DEPRECIATION_RATE_PER_DAY


# Chapter 8

def test_ch8_1_full_gross_cost_is_basis_and_cap_is_hard() -> None:
    one_day = apply_daily_depreciation(constants.BIKE_GROSS_ASSET_COST, 0, True)
    at_cap = apply_daily_depreciation(
        constants.BIKE_GROSS_ASSET_COST,
        constants.BIKE_GROSS_ASSET_COST,
        True,
    )

    assert one_day.depreciation_recorded == constants.DEPRECIATION_RATE_PER_DAY
    assert one_day.accumulated_depreciation_after == constants.DEPRECIATION_RATE_PER_DAY
    assert at_cap.depreciation_recorded == 0
    assert at_cap.net_book_value_after == 0


def test_ch8_2_four_non_depreciable_states_are_mapped_to_no_possession() -> None:
    for _state in (
        "PREP",
        "AVAILABLE_FOR_SECONDARY",
        "OWNED_TRANSFERRED",
        "HELD_AS_ASSET",
    ):
        result = apply_daily_depreciation(
            constants.BIKE_GROSS_ASSET_COST,
            0,
            False,
        )
        assert result.depreciation_recorded == 0
        assert result.usage_days_after == 0


def test_ch8_3_daily_entry_increments_use_and_expense() -> None:
    result = apply_daily_depreciation(constants.BIKE_GROSS_ASSET_COST, 100, True)

    assert result.depreciation_recorded == constants.DEPRECIATION_RATE_PER_DAY
    assert result.accumulated_depreciation_after == 100 + constants.DEPRECIATION_RATE_PER_DAY
    assert result.usage_days_after == 1
    assert result.net_book_value_after == constants.BIKE_GROSS_ASSET_COST - 100 - constants.DEPRECIATION_RATE_PER_DAY
    assert result.project_accumulated_depreciation_delta == constants.DEPRECIATION_RATE_PER_DAY
    assert result.depreciation_expense == constants.DEPRECIATION_RATE_PER_DAY


def test_ch8_4_writeoff_captures_old_accumulated_before_releasing_it() -> None:
    result = apply_ownership_writeoff(constants.BIKE_GROSS_ASSET_COST, 120000)

    assert result.old_accumulated_depreciation == 120000
    assert result.writeoff_amount == constants.BIKE_GROSS_ASSET_COST - 120000
    assert result.project_accumulated_depreciation_delta == -120000
    assert result.project_gross_asset_delta == -constants.BIKE_GROSS_ASSET_COST
    assert result.expense_asset_writeoff == constants.BIKE_GROSS_ASSET_COST - 120000
    assert result.bike_accumulated_depreciation_after == constants.BIKE_GROSS_ASSET_COST
    assert result.bike_net_book_value_after == 0


# Chapter 9

def test_ch9_2_claim_amount_is_outstanding_rent_only_and_waiting_sources_are_exact() -> None:
    created = _next_business_day()
    sources = (
        "PRIMARY_EARLY_TERMINATION",
        "SECONDARY_EARLY_TERMINATION",
        "POST_MATURITY_SETTLEMENT_FAILURE",
        "ADMINISTRATIVE_CLOSURE",
        "FINAL_CLOSURE",
    )
    expected_waits = (30, 20, 60, 0, 0)

    for index, (source, wait) in enumerate(zip(sources, expected_waits), start=1):
        claim = create_guarantee_claim(
            f"CL{index:02d}",
            "BKTEST",
            "CTTEST",
            "TNTEST",
            "GRTEST",
            source,
            45000,
            created,
            70,
        )
        assert claim.claim_amount == 45000
        assert claim.waiting_period_days == wait
        assert claim.settlement_due_date == dateutils.settlement_due_date(created, wait)
        assert claim.status is ClaimStatus.PENDING


def test_ch9_1_all_five_recovery_percentages_are_deterministic() -> None:
    created = _next_business_day()
    claim_amount = 45000

    for rate in constants.GUARANTEE_RECOVERY_RATES:
        claim = create_guarantee_claim(
            f"CL{rate:03d}",
            "BKTEST",
            "CTTEST",
            "TNTEST",
            "GRTEST",
            "PRIMARY_EARLY_TERMINATION",
            claim_amount,
            created,
            rate,
        )
        assert not can_settle_claim(
            claim,
            claim.settlement_due_date - timedelta(days=1),
        )
        result = settle_guarantee_claim(claim, claim.settlement_due_date)
        expected_recovered = (claim_amount * rate) // 100

        assert result.settled_now
        assert result.recovered_amount == expected_recovered
        assert result.bad_debt_amount == claim_amount - expected_recovered
        assert claim.status is ClaimStatus.SETTLED


def test_ch9_repeated_settlement_raises_value_error() -> None:
    claim = create_guarantee_claim(
        "CLDOUBLE",
        "BKTEST",
        "CTTEST",
        "TNTEST",
        "GRTEST",
        "PRIMARY_EARLY_TERMINATION",
        1000,
        _next_business_day(),
        100,
    )
    settle_guarantee_claim(claim, claim.settlement_due_date)

    with pytest.raises(ValueError, match="already been settled"):
        settle_guarantee_claim(
            claim,
            claim.settlement_due_date + timedelta(days=1),
        )
