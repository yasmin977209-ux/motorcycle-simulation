import json
import os
import time
from dataclasses import asdict
from datetime import date
from enum import Enum

from daily_engine import run_deterministic_trial
from rng import derive_seed


def _json_default(value):
    if isinstance(value, Enum):
        return value.value
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(f"unsupported canonical value: {type(value)!r}")


def _canonical_project(project) -> str:
    return json.dumps(
        asdict(project),
        default=_json_default,
        sort_keys=True,
        ensure_ascii=False,
    )


def _assert_rollforwards(project) -> None:
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
            "Gross_Writeoffs_On_Ownership",
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


def test_c100_three_full_repetitions_are_identical_and_report_metrics() -> None:
    results = []
    canonical_projects = []

    for trial_id in (101, 202, 303):
        started = time.perf_counter()
        project = run_deterministic_trial(
            recovery_rate_pct=100,
            trial_id=trial_id,
            scenario_id="C100_G100",
            master_seed=20270101,
        )
        elapsed = time.perf_counter() - started

        final_by_m15_formula = project.project_cash + sum(
            bike.net_book_value
            for bike in project.bikes
            if bike.current_state.value == "HELD_AS_ASSET"
        )
        assert project.final_net_project_equity == final_by_m15_formula
        assert project.final_net_project_equity == (
            project.daily_balance_checks[-1]["Total_Equity"]
        )
        assert max(
            abs(item["Balance_Difference"])
            for item in project.daily_balance_checks
        ) == 0
        _assert_rollforwards(project)

        seed_hex = derive_seed(
            20270101,
            "C100_G100",
            trial_id,
            "BK0001",
            date(2027, 1, 2),
            "PRIMARY_COLLECTION",
        ).hex()

        results.append(
            {
                "trial_id": trial_id,
                "derived_seed_hex": seed_hex,
                "days_executed": len(project.daily_balance_checks),
                "final_close_date": project.final_close_date.isoformat(),
                "bike_count": len(project.bikes),
                "Final_Net_Project_Equity": project.final_net_project_equity,
                "P1": project.partner1_final_entitlement,
                "P2": project.partner2_final_entitlement,
                "max_absolute_balance_difference": 0,
                "elapsed_seconds": elapsed,
                "cpu_count": os.cpu_count(),
            }
        )
        canonical_projects.append(_canonical_project(project))

    print(json.dumps(results, ensure_ascii=False, sort_keys=True))
    assert len({item["derived_seed_hex"] for item in results}) == 3
    assert canonical_projects[0] == canonical_projects[1] == canonical_projects[2]

    comparable = [
        (
            item["days_executed"],
            item["final_close_date"],
            item["bike_count"],
            item["Final_Net_Project_Equity"],
            item["P1"],
            item["P2"],
            item["max_absolute_balance_difference"],
        )
        for item in results
    ]
    assert comparable[0] == comparable[1] == comparable[2]
