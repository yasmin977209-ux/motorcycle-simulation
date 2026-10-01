from datetime import date, timedelta

from daily_engine import create_initial_project, run_day
from entities import BikeState, Contract, ContractStatus, ContractType


def _isolated_project():
    project = create_initial_project()
    target = project.bikes[0]
    for bike in project.bikes[1:]:
        bike.current_state = BikeState.HELD_AS_ASSET
        bike.current_contract_id = None
        bike.current_tenant_id = None
    return project, target


def _activate(
    target,
    project,
    contract_type,
    start_date,
    maturity_date=None,
):
    contract = Contract(
        contract_id="CT00000001",
        bike_id=target.bike_id,
        tenant_id="TN00000001",
        guarantor_id="GR00000001",
        contract_type=contract_type,
        daily_rate=(
            1_500 if contract_type is ContractType.PRIMARY else 1_000
        ),
        start_date=start_date,
        maturity_date=maturity_date,
    )
    project.contracts[contract.contract_id] = contract
    target.current_contract_id = contract.contract_id
    target.current_tenant_id = contract.tenant_id
    target.delivery_date = start_date
    target.current_state = (
        BikeState.ACTIVE_PRIMARY
        if contract_type is ContractType.PRIMARY
        else BikeState.ACTIVE_SECONDARY
    )
    if contract_type is ContractType.SECONDARY:
        target.secondary_cycle_count = max(target.secondary_cycle_count, 1)
    return contract


def test_path2_primary_default_then_secondary() -> None:
    project, target = _isolated_project()
    _activate(
        target,
        project,
        ContractType.PRIMARY,
        date(2027, 1, 2),
    )
    current = date(2027, 1, 2)
    for _ in range(80):
        run_day(
            project,
            current,
            0.0,
            "C000_TEST",
            1,
            100,
            20270101,
        )
        if target.current_state is BikeState.AVAILABLE_FOR_SECONDARY:
            break
        current += timedelta(days=1)
    else:
        raise AssertionError(
            "path 2 did not reach AVAILABLE_FOR_SECONDARY"
        )
    current += timedelta(days=1)
    while target.current_state is BikeState.AVAILABLE_FOR_SECONDARY:
        run_day(
            project,
            current,
            1.0,
            "C100_G100",
            1,
            100,
            20270101,
        )
        current += timedelta(days=1)
        if current > date(2027, 4, 1):
            raise AssertionError("secondary activation was not reached")
    assert target.current_state is BikeState.ACTIVE_SECONDARY
    assert target.secondary_cycle_count >= 1


def test_path3_maturity_debt_then_successful_settlement() -> None:
    project, target = _isolated_project()
    maturity = date(2027, 1, 2)
    contract = _activate(
        target,
        project,
        ContractType.PRIMARY,
        date(2026, 12, 26),
        maturity,
    )
    contract.total_due = 1_500
    run_day(
        project,
        maturity,
        0.0,
        "C000_TEST",
        1,
        100,
        20270101,
    )
    assert target.current_state is BikeState.POST_MATURITY_SETTLEMENT
    current = maturity + timedelta(days=1)
    for _ in range(80):
        run_day(
            project,
            current,
            1.0,
            "C100_G100",
            1,
            100,
            20270101,
        )
        if target.current_state is BikeState.OWNED_TRANSFERRED:
            break
        current += timedelta(days=1)
    else:
        raise AssertionError(
            "path 3 did not reach OWNED_TRANSFERRED"
        )
    assert target.settlement_legacy_debt_remaining == 0


def test_path4_maturity_debt_then_failed_settlement() -> None:
    project, target = _isolated_project()
    maturity = date(2027, 1, 2)
    contract = _activate(
        target,
        project,
        ContractType.PRIMARY,
        date(2026, 12, 26),
        maturity,
    )
    contract.total_due = 1_500
    run_day(
        project,
        maturity,
        0.0,
        "C000_TEST",
        1,
        100,
        20270101,
    )
    assert target.current_state is BikeState.POST_MATURITY_SETTLEMENT
    current = maturity + timedelta(days=1)
    for _ in range(120):
        run_day(
            project,
            current,
            0.0,
            "C000_TEST",
            1,
            100,
            20270101,
        )
        if target.current_state is BikeState.AVAILABLE_FOR_SECONDARY:
            break
        current += timedelta(days=1)
    else:
        raise AssertionError(
            "path 4 did not reach AVAILABLE_FOR_SECONDARY"
        )
    assert any(
        claim.claim_source.value
        == "POST_MATURITY_SETTLEMENT_FAILURE"
        for claim in project.guarantee_claims
    )


def test_path5_repeated_secondary_default_two_cycles() -> None:
    project, target = _isolated_project()
    _activate(
        target,
        project,
        ContractType.SECONDARY,
        date(2027, 1, 2),
    )
    current = date(2027, 1, 2)
    while target.termination_count < 2:
        run_day(
            project,
            current,
            0.0,
            "C000_TEST",
            1,
            100,
            20270101,
        )
        current += timedelta(days=1)
        if current > date(2027, 5, 1):
            raise AssertionError(
                "path 5 did not reach two secondary terminations"
            )
    assert target.secondary_cycle_count >= 2
    assert target.current_state in {
        BikeState.AVAILABLE_FOR_SECONDARY,
        BikeState.ACTIVE_SECONDARY,
    }


def test_path6_dynamic_closure() -> None:
    project, target = _isolated_project()
    contract = _activate(
        target,
        project,
        ContractType.SECONDARY,
        date(2031, 1, 1),
    )
    run_day(
        project,
        date(2031, 1, 1),
        0.0,
        "C000_TEST",
        1,
        100,
        20270101,
    )
    assert project.simulation_stopped
    assert target.current_state is BikeState.HELD_AS_ASSET
    assert contract.status is ContractStatus.TERMINATED
