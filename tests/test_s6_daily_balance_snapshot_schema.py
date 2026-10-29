from __future__ import annotations

from datetime import date

import accounting
import daily_engine
import monte_carlo


def test_daily_snapshot_persists_complete_balance_sheet_identity() -> None:
    # Construct an initial Project only; do not call run_single_trial or run_day.
    project = daily_engine.create_initial_project()
    row = monte_carlo._daily_snapshot(project, date(2027, 1, 1), trial_id=1)
    expected = accounting.balance_sheet_snapshot(project)

    assert row["daily_balance_schema_version"] == "s6-daily-balance-v1"
    for field in (
        "Cash",
        "Accounts_Receivable",
        "Guarantee_Claim_Receivable",
        "Gross_Bike_Assets",
        "Accumulated_Depreciation",
        "Net_Bike_Assets",
        "Total_Assets",
        "Total_Equity",
        "Liabilities",
        "Balance_Difference",
    ):
        assert type(row[field]) is int
        assert row[field] == expected[field]

    assert row["Net_Equity"] == row["Total_Equity"]
    assert row["Total_Assets"] == row["Total_Equity"]
    assert row["Balance_Difference"] == 0
