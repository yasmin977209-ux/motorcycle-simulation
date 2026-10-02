from __future__ import annotations

import constants
import monte_carlo


def test_parse_canonical_scenario_id() -> None:
    probability, recovery_rate = monte_carlo.parse_scenario_id(
        "C085_G070"
    )

    assert probability == 0.85
    assert recovery_rate == 70


def test_parse_rejects_non_scenario_code() -> None:
    try:
        monte_carlo.parse_scenario_id("C000_TEST")
    except ValueError:
        return
    raise AssertionError("non-scenario code was accepted")


def test_single_trial_returns_trial_result_and_daily_rows() -> None:
    result, daily_rows = monte_carlo.run_single_trial(
        "C100_G100",
        1,
    )

    assert isinstance(result, monte_carlo.TrialResult)
    assert result.trial_id == 1
    assert result.scenario_id == "C100_G100"
    assert result.final_close_date is not None
    assert result.final_net_project_equity is not None
    assert result.partner1_final_entitlement is not None
    assert result.partner2_final_entitlement is not None

    assert daily_rows
    assert daily_rows[0]["date"] == constants.PROJECT_START_DATE.isoformat()
    assert daily_rows[-1]["Final_Close_Date"] == result.final_close_date

    assert {
        "date",
        "trial_id",
        "Cash",
        "Capital",
        "Retained_Earnings",
        "Net_Equity",
        "Active_Bikes",
        "Owned_Transferred_Bikes",
        "Pending_Claims",
        "Final_Close_Date",
    } <= set(daily_rows[0])

    assert daily_rows[-1]["Cash"] == result.final_cash
    assert (
        daily_rows[-1]["Net_Equity"]
        == result.final_net_project_equity
    )


def test_single_trial_propagates_scenario_parameters() -> None:
    result, _ = monte_carlo.run_single_trial(
        "C085_G070",
        1,
    )

    assert result.collection_probability == 0.85
    assert result.recovery_rate_pct == 70


def test_sequential_aggregation_keeps_trial_identity() -> None:
    results, daily_rows = monte_carlo.run_trials_sequentially(
        "C100_G100",
        [1, 2],
    )

    assert [result.trial_id for result in results] == [1, 2]
    assert set(daily_rows) == {1, 2}
    assert all(daily_rows[trial_id] for trial_id in (1, 2))

    first = results[0]
    second = results[1]

    assert first.final_close_date == second.final_close_date
    assert first.final_net_project_equity == second.final_net_project_equity
    assert first.final_cash == second.final_cash
    assert (
        first.partner1_final_entitlement
        == second.partner1_final_entitlement
    )
    assert (
        first.partner2_final_entitlement
        == second.partner2_final_entitlement
    )
