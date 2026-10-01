"""Full daily-engine integration tests for Chapter 4.4 paths 2-6."""

from datetime import date, timedelta

import daily_engine
from entities import ContractStatus, ContractType, Project


def _isolated_project(*, blocker=True) -> tuple[Project, object, object]:
    project = daily_engine.create_initial_project(recovery_rate_pct=100)
    target = project.bikes[0]
    for bike in project.bikes[1:]:
        bike.current_state = "HELD_AS_ASSET"
        bike.current_contract_id = None
        bike.current_tenant_id = None
    if blocker:
        spare = project.bikes[1]
        spare.current_state = "PREP"
        spare.prep_paid = True
        spare.customs_paid = True
        spare.actual_ready_date = date(2099, 1, 1)
        spare.scheduled_ready_date = date(2099, 1, 1)
    return project, target, project.bikes[1] if blocker else None


def _activate_contract(project: Project, bike, contract_type: ContractType, start_date: date):
    contract = daily_engine._create_contract(project, bike, contract_type, start_date)
    bike.current_state = (
        "ACTIVE_PRIMARY"
        if contract_type is ContractType.PRIMARY
        else "ACTIVE_SECONDARY"
    )
    bike.current_contract_id = contract.contract_id
    bike.current_tenant_id = contract.tenant_id
    bike.delivery_date = start_date
    return contract


def _run_until(project, start_date, predicate, *, probability, trial_id=1, recovery=100, limit_days=120):
    current = start_date
    for _ in range(limit_days):
        daily_engine.run_day(
            project,
            current,
            collection_probability=probability,
            scenario_id="C000_TEST" if probability == 0 else "C100_G100",
            trial_id=trial_id,
            recovery_rate_pct=recovery,
        )
        target_state = predicate()
        if target_state:
            return current
        current += timedelta(days=1)
    raise AssertionError(f"target path condition not reached by {current}")


def test_path2_primary_early_default_to_secondary_activation():
    project, target, _ = _isolated_project(blocker=True)
    start = date(2027, 1, 2)
    _activate_contract(project, target, ContractType.PRIMARY, start)

    _run_until(
        project,
        start,
        lambda: target.current_state == "AVAILABLE_FOR_SECONDARY",
        probability=0.0,
    )
    assert target.termination_count >= 1
    assert target.current_state == "AVAILABLE_FOR_SECONDARY"

    next_business = start
    while True:
        next_business += timedelta(days=1)
        if next_business.weekday() != 4:
            daily_engine.run_day(
                project,
                next_business,
                collection_probability=1.0,
                scenario_id="C100_G100",
                trial_id=1,
                recovery_rate_pct=100,
            )
            if target.current_state == "ACTIVE_SECONDARY":
                break

    assert target.current_state == BikeState.ACTIVE_SECONDARY.value
    assert target.secondary_cycle_count >= 1
    assert any(
        event.event_type.value == "SECONDARY_CONTRACT_STARTED"
        for event in target.lifecycle_history
    )


def _mature_with_debt(project, target, maturity=date(2031, 1, 2)):
    start = date(2029, 1, 2)
    contract = _activate_contract(project, target, ContractType.PRIMARY, start)
    contract.maturity_date = maturity
    contract.total_due = 0
    contract.total_paid = 0
    return contract


def test_path3_maturity_with_debt_then_successful_settlement():
    project, target, _ = _isolated_project(blocker=True)
    contract = _mature_with_debt(project, target)

    daily_engine.run_day(
        project,
        contract.maturity_date,
        collection_probability=0.0,
        scenario_id="C000_TEST",
        trial_id=1,
        recovery_rate_pct=100,
    )
    assert target.current_state == "POST_MATURITY_SETTLEMENT"

    current = contract.maturity_date + timedelta(days=1)
    while target.current_state == "POST_MATURITY_SETTLEMENT":
        daily_engine.run_day(
            project,
            current,
            collection_probability=1.0,
            scenario_id="C100_G100",
            trial_id=1,
            recovery_rate_pct=100,
        )
        current += timedelta(days=1)

    assert target.current_state == "OWNED_TRANSFERRED"
    assert contract.status in (ContractStatus.SETTLED, ContractStatus.TERMINATED)
    assert target.settlement_legacy_debt_remaining == 0


def test_path4_maturity_with_debt_then_failed_settlement_to_secondary():
    project, target, _ = _isolated_project(blocker=True)
    contract = _mature_with_debt(project, target)

    daily_engine.run_day(
        project,
        contract.maturity_date,
        collection_probability=0.0,
        scenario_id="C000_TEST",
        trial_id=1,
        recovery_rate_pct=100,
    )
    assert target.current_state == BikeState.POST_MATURITY_SETTLEMENT.value

    current = contract.maturity_date + timedelta(days=1)
    while target.current_state == BikeState.POST_MATURITY_SETTLEMENT.value:
        daily_engine.run_day(
            project,
            current,
            collection_probability=0.0,
            scenario_id="C000_TEST",
            trial_id=1,
            recovery_rate_pct=100,
        )
        current += timedelta(days=1)

    assert target.current_state == BikeState.AVAILABLE_FOR_SECONDARY.value
    assert any(
        claim.claim_source.value == "POST_MATURITY_SETTLEMENT_FAILURE"
        for claim in project.guarantee_claims
    )


def test_path5_repeated_secondary_default_two_cycles():
    project, target, _ = _isolated_project(blocker=True)
    start = date(2030, 1, 2)
    _activate_contract(project, target, ContractType.SECONDARY, start)
    target.secondary_cycle_count = 1

    current = start
    while target.termination_count < 2:
        daily_engine.run_day(
            project,
            current,
            collection_probability=0.0,
            scenario_id="C000_TEST",
            trial_id=1,
            recovery_rate_pct=100,
        )
        current += timedelta(days=1)
        if current > date(2031, 1, 1):
            raise AssertionError("second secondary termination was not reached")

    assert target.secondary_cycle_count >= 2
    assert target.termination_count >= 2
    assert target.current_state in {
        BikeState.AVAILABLE_FOR_SECONDARY.value,
        BikeState.ACTIVE_SECONDARY.value,
    }
    secondary_starts = sum(
        1 for event in target.lifecycle_history
        if event.event_type.value == "SECONDARY_CONTRACT_STARTED"
    )
    secondary_terminations = sum(
        1 for event in target.lifecycle_history
        if event.event_type.value == "SECONDARY_TERMINATED"
    )
    assert secondary_starts >= 2
    assert secondary_terminations >= 2


def test_path6_dynamic_closure_with_active_secondary_holds_asset():
    project, target, _ = _isolated_project(blocker=False)
    start = date(2031, 1, 1)
    contract = _activate_contract(project, target, ContractType.SECONDARY, start)

    daily_engine.run_day(
        project,
        start,
        collection_probability=0.0,
        scenario_id="C000_TEST",
        trial_id=1,
        recovery_rate_pct=100,
    )

    assert project.simulation_stopped is True
    assert project.final_close_date == start
    assert target.current_state == "HELD_AS_ASSET"
    assert contract.status is ContractStatus.TERMINATED
    assert project.final_net_project_equity is not None
