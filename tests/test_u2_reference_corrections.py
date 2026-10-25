from datetime import date

import daily_engine
from entities import ContractType


def test_168_first_eligible_friday_is_stored_per_secondary_contract() -> None:
    project = daily_engine.create_initial_project()
    bike = project.bikes[0]

    saturday = daily_engine._new_contract(
        project, bike, ContractType.SECONDARY, date(2027, 1, 2)
    )
    tuesday = daily_engine._new_contract(
        project, bike, ContractType.SECONDARY, date(2027, 1, 5)
    )

    assert saturday.first_eligible_friday_date == date(2027, 1, 8)
    assert tuesday.first_eligible_friday_date == date(2027, 1, 15)
    assert saturday.friday_counter == 0
    assert tuesday.friday_counter == 0

import dateutils
from datetime import timedelta
from entities import BikeState, ContractStatus


def _m12_settlement_fixture(maturity_date: date):
    project = daily_engine.create_initial_project()
    bike = project.bikes[0]
    contract = daily_engine._new_contract(
        project, bike, ContractType.PRIMARY, date(2029, 1, 2)
    )
    contract.maturity_date = maturity_date
    contract.total_due = 1
    contract.total_paid = 0
    bike.current_contract_id = contract.contract_id
    bike.current_tenant_id = contract.tenant_id
    bike.current_state = BikeState.ACTIVE_PRIMARY
    daily_engine._m12(project, maturity_date)
    return project, bike, contract


def test_165_settlement_start_date_is_set_in_m12_for_maturity_weekdays() -> None:
    for maturity_date in (
        date(2031, 1, 2),  # Thursday -> Saturday
        date(2031, 1, 3),  # Friday -> Saturday
        date(2031, 1, 4),  # Saturday -> Sunday
        date(2031, 1, 6),  # Monday -> Tuesday
    ):
        project, bike, contract = _m12_settlement_fixture(maturity_date)
        assert bike.current_state is BikeState.POST_MATURITY_SETTLEMENT
        assert bike.settlement_start_date == dateutils.next_business_day(maturity_date)
        assert bike.settlement_start_date > maturity_date
        assert contract.status is ContractStatus.MATURED


def test_164_settlement_failure_occurs_on_business_day_30() -> None:
    project, bike, contract = _m12_settlement_fixture(date(2031, 1, 2))
    start = bike.settlement_start_date
    assert start is not None
    receivable = daily_engine._receivable_of(project, bike)
    assert receivable is not None

    day30 = start
    count = 0
    while count < daily_engine.constants.SETTLEMENT_PERIOD_DAYS:
        if dateutils.is_business_day(day30):
            count += 1
        if count < daily_engine.constants.SETTLEMENT_PERIOD_DAYS:
            day30 += timedelta(days=1)

    bike.settlement_business_days_elapsed = daily_engine.constants.SETTLEMENT_PERIOD_DAYS - 1
    bike.settlement_legacy_debt_remaining = 1
    project.accounts_receivable = 1
    receivable.remaining_amount = 1
    daily_engine._ensure_day_metrics(project)
    daily_engine._m13(project, day30, recovery_rate_pct=100)

    assert bike.current_state is BikeState.AVAILABLE_FOR_SECONDARY
    assert project.guarantee_claims[-1].claim_source == "POST_MATURITY_SETTLEMENT_FAILURE"
    assert project.guarantee_claims[-1].created_date == day30
    assert bike.active_settlement_receivable_id is None
    assert bike.settlement_business_days_elapsed == daily_engine.constants.SETTLEMENT_PERIOD_DAYS

from constants import EXPANSION_PURCHASE_CASH_THRESHOLD, BIKE_BASE_PURCHASE_COST


def test_166_m2_purchases_at_most_one_expansion_bike_per_day() -> None:
    project = daily_engine.create_initial_project()
    starting_count = len(project.bikes)
    starting_cash = EXPANSION_PURCHASE_CASH_THRESHOLD * 2
    project.project_cash = starting_cash
    project.partner1_reinvestment_balance = starting_cash

    daily_engine._m2(project, date(2027, 1, 2))

    assert len(project.bikes) == starting_count + 1
    assert project.project_cash == starting_cash - BIKE_BASE_PURCHASE_COST
    assert project.partner1_reinvestment_balance == (
        starting_cash - BIKE_BASE_PURCHASE_COST
    )

def test_167_customs_are_in_investing_cash_outflows_and_cash_rollforward() -> None:
    project = daily_engine.run_deterministic_trial(
        recovery_rate_pct=100,
        trial_id=1,
        scenario_id="C100_G100",
        master_seed=daily_engine.constants.MASTER_SEED,
    )

    investing_outflows = sum(
        row["Investing_Cash_Outflows"] for row in project.cash_rollforward
    )
    capitalized_purchases_and_customs = sum(
        row["Capitalized_Purchases_And_Customs"]
        for row in project.asset_rollforward
    )

    assert investing_outflows > 0
    assert investing_outflows == capitalized_purchases_and_customs
    for cash in project.cash_rollforward:
        assert cash["Outflows"] == (
            cash["Operating_Cash_Outflows"] + cash["Investing_Cash_Outflows"]
        )
        assert cash["Opening_Cash"] + cash["Inflows"] - cash["Outflows"] == cash["Closing_Cash"]



def test_partner_split_has_one_algorithm_and_inflows_use_allocator() -> None:
    from partner_equity import split_70_30, allocate_inflow
    project = daily_engine.create_initial_project()
    assert split_70_30(1001) == (700, 301)
    before1 = project.partner1_reinvestment_balance
    before2 = project.partner2_reinvestment_balance
    allocate_inflow(project, 1001)
    assert project.partner1_reinvestment_balance - before1 == 700
    assert project.partner2_reinvestment_balance - before2 == 301
