from __future__ import annotations

from datetime import timedelta

import constants
import dateutils
from accounting import assert_balance_sheet_balanced
from daily_engine import create_initial_project, run_day
from entities import BikeState, ContractType


def test_path1_prep_to_active_primary_to_owned_transferred() -> None:
    project = create_initial_project(recovery_rate_pct=100)

    target = project.bikes[0]
    assert target.current_state is BikeState.PREP

    current_date = constants.PROJECT_START_DATE
    state_sequence = [target.current_state]
    maturity_date = None
    activation_date = None

    for _ in range(1000):
        opening_gross_bike_assets = project.gross_bike_assets
        states_before_run = {
            bike.bike_id: bike.current_state for bike in project.bikes
        }

        run_day(
            project,
            current_date,
            collection_probability=1.0,
            scenario_id="C100_G100",
            trial_id=1,
            recovery_rate_pct=100,
            master_seed=constants.MASTER_SEED,
        )

        assert_balance_sheet_balanced(project, current_date)

        current_state = target.current_state

        if current_state is not state_sequence[-1]:
            state_sequence.append(current_state)

        if activation_date is None:
            if current_state is BikeState.ACTIVE_PRIMARY:
                activation_date = current_date

                assert target.current_contract_id is not None
                contract = project.contracts[target.current_contract_id]

                assert contract.contract_type is ContractType.PRIMARY
                assert contract.start_date == activation_date
                assert contract.maturity_date is not None

                maturity_date = contract.maturity_date

                independently_calculated_maturity_date = (
                    dateutils.primary_maturity_date(contract.start_date)
                )
                assert (
                    maturity_date
                    == independently_calculated_maturity_date
                )

                assert state_sequence == [
                    BikeState.PREP,
                    BikeState.ACTIVE_PRIMARY,
                ]

        if maturity_date is not None:
            if current_date < maturity_date:
                assert current_state is not BikeState.OWNED_TRANSFERRED

            if current_date == maturity_date - timedelta(days=1):
                assert current_state is not BikeState.OWNED_TRANSFERRED

            if current_date == maturity_date:
                assert current_state is BikeState.OWNED_TRANSFERRED

                assert state_sequence == [
                    BikeState.PREP,
                    BikeState.ACTIVE_PRIMARY,
                    BikeState.OWNED_TRANSFERRED,
                ]

                assert target.net_book_value == 0
                assert (
                    target.accumulated_depreciation
                    == target.gross_cost
                )

                asset_rollforward = project.asset_rollforward[-1]

                newly_owned_gross = sum(
                    bike.gross_cost
                    for bike in project.bikes
                    if (
                        states_before_run.get(bike.bike_id)
                        is not BikeState.OWNED_TRANSFERRED
                        and bike.current_state
                        is BikeState.OWNED_TRANSFERRED
                    )
                )

                assert target.bike_id in {
                    bike.bike_id
                    for bike in project.bikes
                    if (
                        states_before_run.get(bike.bike_id)
                        is not BikeState.OWNED_TRANSFERRED
                        and bike.current_state
                        is BikeState.OWNED_TRANSFERRED
                    )
                }

                assert (
                    asset_rollforward["Gross_Writeoffs_On_Ownership"]
                    == newly_owned_gross
                )

                gross_change = (
                    project.gross_bike_assets
                    - opening_gross_bike_assets
                )

                assert (
                    gross_change
                    == asset_rollforward[
                        "Capitalized_Purchases_And_Customs"
                    ]
                    - asset_rollforward[
                        "Gross_Writeoffs_On_Ownership"
                    ]
                )

                assert target.gross_cost <= newly_owned_gross

                break

        current_date += timedelta(days=1)

    else:
        raise AssertionError(
            "path 1 did not reach OWNED_TRANSFERRED at the calculated "
            "maturity date within the 1000-day safety limit"
        )

    assert activation_date is not None
    assert maturity_date is not None
    assert target.current_state is BikeState.OWNED_TRANSFERRED
