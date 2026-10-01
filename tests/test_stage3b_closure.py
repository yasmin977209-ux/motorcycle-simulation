from datetime import date

from closure import closure_preconditions_met
from constants import EXPANSION_CUTOFF_DATE
from daily_engine import create_initial_project, run_day
from entities import BikeState, Contract, ContractType


def _clean_project():
    project = create_initial_project()
    for bike in project.bikes:
        bike.current_state = BikeState.HELD_AS_ASSET
        bike.current_contract_id = None
        bike.current_tenant_id = None
    return project


def test_ch13_prep_condition_is_independent() -> None:
    project = _clean_project()
    project.bikes[0].current_state = BikeState.PREP
    assert closure_preconditions_met(
        project,
        date(2031, 1, 1),
    ) is False


def test_ch13_primary_condition_is_independent() -> None:
    project = _clean_project()
    project.bikes[0].current_state = BikeState.ACTIVE_PRIMARY
    assert closure_preconditions_met(
        project,
        date(2031, 1, 1),
    ) is False


def test_ch13_settlement_condition_is_independent() -> None:
    project = _clean_project()
    project.bikes[0].current_state = BikeState.POST_MATURITY_SETTLEMENT
    assert closure_preconditions_met(
        project,
        date(2031, 1, 1),
    ) is False


def test_ch13_cutoff_condition_is_independent() -> None:
    project = _clean_project()
    assert closure_preconditions_met(
        project,
        EXPANSION_CUTOFF_DATE,
    ) is False


def test_ch13_all_four_conditions_allow_closure() -> None:
    project = _clean_project()
    assert closure_preconditions_met(
        project,
        date(2031, 1, 1),
    ) is True


def test_ch13_active_secondary_is_closed_administratively() -> None:
    project = _clean_project()
    bike = project.bikes[0]
    contract = Contract(
        contract_id="CT00000001",
        bike_id=bike.bike_id,
        tenant_id="TN00000001",
        guarantor_id="GR00000001",
        contract_type=ContractType.SECONDARY,
        daily_rate=1_000,
        start_date=date(2031, 1, 1),
    )
    project.contracts[contract.contract_id] = contract
    bike.current_state = BikeState.ACTIVE_SECONDARY
    bike.current_contract_id = contract.contract_id
    bike.current_tenant_id = contract.tenant_id
    run_day(
        project,
        date(2031, 1, 1),
        collection_probability=0.0,
        scenario_id="C000_TEST",
        trial_id=1,
        recovery_rate_pct=100,
    )
    assert project.simulation_stopped
    assert project.final_close_date == date(2031, 1, 1)
    assert project.final_net_project_equity is not None
