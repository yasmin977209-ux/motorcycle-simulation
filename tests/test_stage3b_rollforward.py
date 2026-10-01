from daily_engine import run_deterministic_trial


def test_ch10_rollforward_equations_and_fixed_fields() -> None:
    project = run_deterministic_trial(
        recovery_rate_pct=100,
        trial_id=1,
        scenario_id="C100_G100",
        master_seed=20270101,
    )
    assert project.cash_rollforward
    assert len(project.cash_rollforward) == len(project.daily_balance_checks)
    assert len(project.ar_rollforward) == len(project.daily_balance_checks)
    assert len(project.asset_rollforward) == len(project.daily_balance_checks)
    assert len(project.equity_rollforward) == len(project.daily_balance_checks)

    for cash in project.cash_rollforward:
        assert set(cash) == {
            "Opening_Cash",
            "Inflows",
            "Outflows",
            "Closing_Cash",
        }
        assert (
            cash["Opening_Cash"] + cash["Inflows"] - cash["Outflows"]
            == cash["Closing_Cash"]
        )

    for ar in project.ar_rollforward:
        assert set(ar) == {
            "Opening_AR",
            "Accruals",
            "Collections",
            "TransfersToGuarantee",
            "Closing_AR",
        }
        assert (
            ar["Opening_AR"]
            + ar["Accruals"]
            - ar["Collections"]
            - ar["TransfersToGuarantee"]
            == ar["Closing_AR"]
        )

    for asset in project.asset_rollforward:
        assert set(asset) == {
            "Opening_Gross_Bike_Assets",
            "Capitalized_Purchases_And_Customs",
            "Gross_Writeoffs_On_OwnERSHIP",
            "Closing_Gross_Bike_Assets",
            "Opening_Accumulated_Depreciation",
            "Depreciation_Expense",
            "AD_Removed_On_Writeoff",
            "Closing_Accumulated_Depreciation",
        }
        assert (
            asset["Opening_Gross_Bike_Assets"]
            + asset["Capitalized_Purchases_And_Customs"]
            - asset["Gross_Writeoffs_On_Ownership"]
            == asset["Closing_Gross_Bike_Assets"]
        )
        assert (
            asset["Opening_Accumulated_Depreciation"]
            + asset["Depreciation_Expense"]
            - asset["AD_Removed_On_Writeoff"]
            == asset["Closing_Accumulated_Depreciation"]
        )
        assert "Net_Bike_Assets" not in asset

    for equity in project.equity_rollforward:
        assert set(equity) == {
            "Opening_Equity",
            "Operating_Net_Profit",
            "Closing_Equity",
        }
        assert (
            equity["Opening_Equity"] + equity["Operating_Net_Profit"]
            == equity["Closing_Equity"]
        )
