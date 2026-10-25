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
