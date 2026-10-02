from __future__ import annotations

from datetime import date, timedelta

from collection import apply_ordinary_collection
from daily_engine import create_initial_project, run_day
from entities import BikeState, ContractType
from settlement import apply_legacy_debt_collection, apply_settlement_rent


def _activate_single_contract(contract_type: ContractType, start_date: date):
    project = create_initial_project(recovery_rate_pct=100)
    target = project.bikes[0]
    for bike in project.bikes[1:]:
        bike.current_state = BikeState.HELD_AS_ASSET
        bike.current_contract_id = None
        bike.current_tenant_id = None
    contract = __import__("daily_engine")._new_contract(
        project,
        target,
        contract_type,
        start_date,
    )
    target.current_state = (
        BikeState.ACTIVE_PRIMARY
        if contract_type is ContractType.PRIMARY
        else BikeState.ACTIVE_SECONDARY
    )
    target.delivery_date = start_date
    target.current_contract_id = contract.contract_id
    target.current_tenant_id = contract.tenant_id
    return project, target, contract


def test_m8_primary_three_days_arrears_pays_today_plus_one_day():
    project, _, contract = _activate_single_contract(
        ContractType.PRIMARY,
        date(2027, 1, 2),
    )
    contract.total_due = 3 * contract.daily_rate
    project.accounts_receivable = contract.total_due

    run_day(
        project,
        date(2027, 1, 4),
        collection_probability=1.0,
        scenario_id="C100_G100",
        trial_id=1,
        recovery_rate_pct=100,
    )

    assert contract.total_due - contract.total_paid == 2 * contract.daily_rate


def test_m8_secondary_three_days_arrears_pays_today_plus_one_day():
    project, _, contract = _activate_single_contract(
        ContractType.SECONDARY,
        date(2027, 1, 2),
    )
    contract.total_due = 3 * contract.daily_rate
    project.accounts_receivable = contract.total_due

    run_day(
        project,
        date(2027, 1, 4),
        collection_probability=1.0,
        scenario_id="C100_G100",
        trial_id=1,
        recovery_rate_pct=100,
    )

    assert contract.total_due - contract.total_paid == 2 * contract.daily_rate


def test_m8_p1_without_arrears_collects_exactly_one_day():
    project, _, contract = _activate_single_contract(
        ContractType.PRIMARY,
        date(2027, 1, 2),
    )

    run_day(
        project,
        date(2027, 1, 4),
        collection_probability=1.0,
        scenario_id="C100_G100",
        trial_id=1,
        recovery_rate_pct=100,
    )

    assert contract.total_due == contract.daily_rate
    assert contract.total_paid == contract.daily_rate
    assert contract.total_due - contract.total_paid == 0


def test_collection_api_cash_and_ar_signals_are_exact():
    ordinary = apply_ordinary_collection(
        total_due=4_500,
        total_paid=1_500,
        daily_rate=1_500,
        success=True,
        current_date=date(2027, 1, 4),
    )
    legacy = apply_legacy_debt_collection(
        remaining_debt=2_000,
        success=True,
    )
    settlement = apply_settlement_rent(date(2027, 1, 4))

    print(
        "ordinary:",
        {
            "cash_delta": ordinary.cash_delta,
            "collected": ordinary.collected,
            "accounts_receivable_delta": ordinary.accounts_receivable_delta,
        },
    )
    print(
        "legacy:",
        {
            "cash_delta": legacy.cash_delta,
            "payment": legacy.payment,
            "accounts_receivable_delta": legacy.accounts_receivable_delta,
        },
    )
    print(
        "settlement:",
        {
            "cash_delta": settlement.cash_delta,
            "collected": settlement.collected,
            "accounts_receivable_delta": settlement.accounts_receivable_delta,
        },
    )

    assert ordinary.cash_delta == ordinary.collected
    assert ordinary.accounts_receivable_delta == -ordinary.collected
    assert legacy.cash_delta == legacy.payment
    assert legacy.accounts_receivable_delta == -legacy.payment
    assert settlement.cash_delta == settlement.collected


def test_run_day_balance_sheet_zero_difference_for_400_days_at_p030():
    project = create_initial_project(recovery_rate_pct=0)

    current = date(2027, 1, 1)
    for _ in range(400):
        run_day(
            project,
            current,
            collection_probability=0.30,
            scenario_id="C030_G000",
            trial_id=1,
            recovery_rate_pct=0,
        )
        assert not project.simulation_stopped
        current += timedelta(days=1)

    assert len(project.daily_balance_checks) == 400
    assert all(
        row["Balance_Difference"] == 0
        for row in project.daily_balance_checks
    )
