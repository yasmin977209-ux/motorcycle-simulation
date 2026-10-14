from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from openpyxl import load_workbook

from scripts.stage13_assemble import (
    EXPECTED_SCENARIOS, EXPECTED_SOURCE_SHA, assemble_workbook,
    select_representative_trial_ids,
)

FOCUS_SCENARIOS = EXPECTED_SCENARIOS[:5]
START_DATE = date(2027, 1, 1)
END_DATE = date(2027, 1, 2)


def trial_row(scenario, trial_id, offset):
    equity = 1000 + offset * 100 + trial_id * 10
    return {
        "scenario_id": scenario, "trial_id": trial_id, "final_close_date": "2027-01-02",
        "final_net_project_equity": equity, "final_cash": equity + 100,
        "cumulative_project_profit": trial_id * 100 - 250,
        "operating_net_profit": trial_id * 10, "termination_count": trial_id % 4,
        "secondary_cycle_count": trial_id % 3, "owned_bikes": 8 + trial_id % 3,
        "held_assets": trial_id % 2, "total_operating_revenue": 500 + trial_id * 20,
        "bad_debt": trial_id * 2, "guarantee_recovered": trial_id,
        "partner1_final_entitlement": equity * 7 // 10,
        "partner2_final_entitlement": equity - equity * 7 // 10,
    }


def daily_rows(trial):
    equity = int(trial["final_net_project_equity"])
    return [
        {
            "date": START_DATE, "Final_Close_Date": END_DATE, "Cash": int(trial["final_cash"]) - 100,
            "Net_Equity": equity - 100, "Active_Bikes": 4, "Owned_Transferred_Bikes": 1,
            "Pending_Claims": 0, "Partner1_Reinvestment_Balance": 30, "Partner2_Reinvestment_Balance": 20,
            "Operating_Revenue": 250, "Operating_Expenses": 10, "Operating_Net_Profit": 240,
            "Cumulative_Project_Profit": int(trial["cumulative_project_profit"]) - 1,
            "Accounts_Receivable": 10, "Guarantee_Claim_Receivable": 0,
            "Gross_Bike_Assets": 1000, "Accumulated_Depreciation": 100,
        },
        {
            "date": END_DATE, "Final_Close_Date": END_DATE, "Cash": int(trial["final_cash"]),
            "Net_Equity": equity, "Active_Bikes": 0, "Owned_Transferred_Bikes": 1,
            "Pending_Claims": 0, "Partner1_Reinvestment_Balance": 0, "Partner2_Reinvestment_Balance": 0,
            "Operating_Revenue": 0, "Operating_Expenses": 0, "Operating_Net_Profit": 0,
            "Cumulative_Project_Profit": int(trial["cumulative_project_profit"]),
            "Accounts_Receivable": 0, "Guarantee_Claim_Receivable": 0,
            "Gross_Bike_Assets": 1000, "Accumulated_Depreciation": 100,
        },
    ]


def rep_payload(trial):
    return {
        "summary": dict(trial), "daily": daily_rows(trial),
        "final_inventory": [{
            "bike_id": "BIKE-001", "source": "fixture", "purchase_date": "2027-01-01",
            "delivery_date": "2027-01-01", "gross_cost": 1000, "accumulated_depreciation": 100,
            "net_book_value": 900, "termination_count": trial["termination_count"],
            "secondary_cycle_count": trial["secondary_cycle_count"], "state": "CLOSED",
        }],
        "accounting": {"daily_balance_checks": [], "cash_rollforward": [], "ar_rollforward": [],
                       "asset_rollforward": [], "equity_rollforward": []},
        "partner_memo": [
            {"date": START_DATE, "Partner1_Reinvestment_Balance": 30, "Partner2_Reinvestment_Balance": 20},
            {"date": END_DATE, "Partner1_Reinvestment_Balance": 0, "Partner2_Reinvestment_Balance": 0},
        ],
        "final_reconciliation": {}, "guarantee_claims": [], "contracts": [],
    }


def demo_data():
    trials = {scenario: [] for scenario in EXPECTED_SCENARIOS}
    distributions = {scenario: [] for scenario in EXPECTED_SCENARIOS}
    representatives, assignments = {}, {}
    total = 0
    for offset, scenario in enumerate(FOCUS_SCENARIOS):
        rows = [trial_row(scenario, trial_id, offset) for trial_id in range(1, 11)]
        trials[scenario] = rows
        total += len(rows)
        selected = select_representative_trial_ids(rows, scenario)
        assignments[scenario] = selected
        by_id = {row["trial_id"]: row for row in rows}
        representatives[scenario] = {
            role: rep_payload(by_id[trial_id]) for role, trial_id in selected.items()
        }
        distributions[scenario] = [{
            "date": START_DATE, "active_trial_count": 10,
            "P10_Cash": 100, "P25_Cash": 110, "P50_Cash": 120, "P75_Cash": 130, "P90_Cash": 140,
            "P10_Net_Equity": 90, "P25_Net_Equity": 100, "P50_Net_Equity": 110, "P75_Net_Equity": 120, "P90_Net_Equity": 130,
            "P10_Active_Bikes": 1, "P25_Active_Bikes": 2, "P50_Active_Bikes": 3, "P75_Active_Bikes": 4, "P90_Active_Bikes": 5,
            "P10_Owned_Transferred_Bikes": 0, "P25_Owned_Transferred_Bikes": 0,
            "P50_Owned_Transferred_Bikes": 1, "P75_Owned_Transferred_Bikes": 1, "P90_Owned_Transferred_Bikes": 2,
            "P10_Pending_Claims": 0, "P25_Pending_Claims": 0, "P50_Pending_Claims": 0,
            "P75_Pending_Claims": 1, "P90_Pending_Claims": 1,
        }]
    return {
        "manifest": {
            "source_sha": EXPECTED_SOURCE_SHA, "run_id": "TEST-DEMO",
            "run_head_sha": "synthetic-test-only", "master_seed": 20270101,
            "total_capital": 10000, "total_trials": total, "total_representatives": 25,
            "global_manifest_sha256": "synthetic-fixture-not-production-evidence",
            "constant_map": {"MASTER_SEED": 20270101, "TOTAL_CAPITAL": 10000},
            "scenarios": {s: {"final_status": "DEMO_ONLY"} for s in EXPECTED_SCENARIOS},
        },
        "trials_by_scenario": trials, "daily_distributions_by_scenario": distributions,
        "representatives_by_scenario": representatives, "representative_trial_ids": assignments,
        "validation": {"status": "DEMO_ONLY", "tests": []}, "errors": [],
    }


def test_assemble_185_sheets_and_five_representative_roles(tmp_path: Path):
    data = demo_data()
    output = tmp_path / "demo.xlsx"
    result = assemble_workbook(data, output, mode="demo")
    assert result["success"] is True
    assert result["trial_count"] == 50
    assert (result["sheets_count"], result["stats_sheets"], result["daily_sheets"]) == (185, 25, 25)
    assert result["excel_errors"] == 0
    assert result["formula_cells"] == 0
    wb = load_workbook(output, data_only=False)
    assert len(wb.sheetnames) == 185
    assert wb["C100_G100_STATS"]["A2"].value == "Final_Net_Project_Equity"
    assert wb["C100_G100_DAILY"].max_row == 3
    rep = wb["REPRESENTATIVE_CASES"]
    summaries = [tuple(row) for row in rep.iter_rows(min_row=2, values_only=True)
                 if row[0] in FOCUS_SCENARIOS and row[2] == "SUMMARY"]
    assert len(summaries) == 25
    assert {row[1] for row in summaries} == {"P10", "P50", "P90", "Loss Case", "Max Case"}
    assert all(cell.data_type not in {"f", "e"} for ws in wb.worksheets
               for row in ws.iter_rows() for cell in row)
    wb.close()


def test_loss_and_max_case_selection_matches_normative_decision():
    rows = [trial_row("C100_G100", i, 0) for i in range(1, 11)]
    selected = select_representative_trial_ids(rows, "C100_G100")
    assert selected["Loss"] == 1
    assert selected["Max Case"] == 10


def test_max_case_without_positive_equity_is_undefined_business_rule():
    rows = [trial_row("C100_G100", i, 0) for i in range(1, 4)]
    for row in rows:
        row["final_net_project_equity"] = -abs(row["final_net_project_equity"])
    with pytest.raises(RuntimeError, match="UNDEFINED_BUSINESS_RULE: MaxCase has no positive"):
        select_representative_trial_ids(rows, "C100_G100")


def test_incorrect_recorded_representative_trial_id_is_rejected():
    data = demo_data()
    data["representative_trial_ids"]["C100_G100"]["P50"] = 999
    with pytest.raises(RuntimeError, match="REPRESENTATIVE_TRIAL_ID_MISMATCH"):
        assemble_workbook(data, Path("unused.xlsx"), mode="demo")


def test_canonical_mode_rejects_demo_subset(tmp_path: Path):
    data = demo_data()
    output = tmp_path / "must-not-exist.xlsx"
    with pytest.raises(RuntimeError):
        assemble_workbook(data, output, mode="canonical")
    assert not output.exists()

def test_sensitivity_sheet_holds_other_dimension_fixed_and_daily_stats_are_values(tmp_path: Path):
    data = demo_data()
    output = tmp_path / "sensitivity.xlsx"
    result = assemble_workbook(data, output, mode="demo")
    assert result["success"] is True
    assert result["sheets_count"] == 185

    wb = load_workbook(output, data_only=True)
    assert wb.sheetnames.count("SENSITIVITY") == 1
    ws = wb["SENSITIVITY"]
    assert [cell.value for cell in ws[1]] == [
        "varied_dimension", "fixed_dimension", "fixed_value_pct",
        "varied_value_pct", "scenario", "mean_cumulative_project_profit",
    ]
    rows = list(ws.iter_rows(min_row=2, values_only=True))
    assert len(rows) == 50
    collection_rows = [row for row in rows if row[0] == "collection_probability_pct"]
    recovery_rows = [row for row in rows if row[0] == "guarantee_recovery_rate_pct"]
    assert len(collection_rows) == 25
    assert len(recovery_rows) == 25
    for row in collection_rows:
        collection_pct = int(row[4].split("_")[0][1:])
        recovery_pct = int(row[4].split("_")[1][1:])
        assert row[1] == "guarantee_recovery_rate_pct"
        assert row[2] == recovery_pct
        assert row[3] == collection_pct
    for row in recovery_rows:
        collection_pct = int(row[4].split("_")[0][1:])
        recovery_pct = int(row[4].split("_")[1][1:])
        assert row[1] == "collection_probability_pct"
        assert row[2] == collection_pct
        assert row[3] == recovery_pct

    target = [row for row in rows if row[4] == "C100_G100"]
    assert len(target) == 2
    assert all(row[5] == 300 for row in target)

    stats = wb["C100_G100_STATS"]
    assert stats["A2"].value == "Final_Net_Project_Equity"
    assert stats["B2"].value == 1055.0
    daily = wb["C100_G100_DAILY"]
    assert daily["A2"].value.date() == START_DATE
    assert daily["B2"].value.date() == END_DATE
    assert daily["C2"].value == 1050
    wb.close()
