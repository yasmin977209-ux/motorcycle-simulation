from __future__ import annotations

from openpyxl import Workbook
import pytest

from scripts.stage13_assemble import (
    EXPECTED_SCENARIOS,
    _validate_representatives,
    representative_daily_value,
    write_representatives,
)


def _trial_row(scenario: str) -> dict:
    return {
        "scenario_id": scenario,
        "trial_id": 1,
        "collection_probability": int(scenario[1:4]) / 100.0,
        "recovery_rate_pct": int(scenario[6:9]),
        "final_net_project_equity": 100,
        "final_cash": 50,
        "cumulative_project_profit": 40,
        "operating_net_profit": 10,
        "final_close_date": "2027-01-01",
        "termination_count": 0,
        "secondary_cycle_count": 0,
        "owned_bikes": 1,
        "held_assets": 0,
        "total_operating_revenue": 100,
        "bad_debt": 0,
        "guarantee_recovered": 0,
    }


def _fixture_data() -> dict:
    rows_by_scenario = {}
    reps_by_scenario = {}
    for scenario in EXPECTED_SCENARIOS:
        row = _trial_row(scenario)
        rows_by_scenario[scenario] = [row]
        daily = {
            "trial_id": 1,
            "date": "2027-01-01",
            "Final_Close_Date": "2027-01-01",
            "Cash": 50,
            "Net_Equity": 100,
            "Cumulative_Project_Profit": 40,
            "Operating_Net_Profit": 10,
            "Active_Bikes": 1,
            "Owned_Transferred_Bikes": 0,
            "Pending_Claims": 0,
            "Partner1_Reinvestment_Balance": 25,
            "Partner2_Reinvestment_Balance": 15,
        }
        roles = {}
        for role in ("P10", "P50", "P90", "Loss"):
            roles[role] = {"summary": row.copy(), "daily": [daily.copy()]}
        max_daily = daily.copy()
        max_daily.pop("Partner1_Reinvestment_Balance")
        max_daily.pop("Partner2_Reinvestment_Balance")
        max_daily["Cumulative_Project_Profit"] = "PENDING_DATA_SOURCE"
        roles["Max Case"] = {"summary": row.copy(), "daily": [max_daily]}
        reps_by_scenario[scenario] = roles
    return {
        "trials_by_scenario": rows_by_scenario,
        "representative_trial_ids": {},
        "representatives_by_scenario": reps_by_scenario,
    }


def test_missing_maxcase_fields_are_explicitly_pending_not_zero_or_retained_earnings():
    assert representative_daily_value("Max Case", {}, "Partner1_Reinvestment_Balance") == "PENDING_DATA_SOURCE"
    assert representative_daily_value("Max Case", {}, "Partner2_Reinvestment_Balance") == "PENDING_DATA_SOURCE"
    assert representative_daily_value("Max Case", {}, "Cumulative_Project_Profit") == "PENDING_DATA_SOURCE"
    assert representative_daily_value("P50", {}, "Partner1_Reinvestment_Balance") is None
    assert representative_daily_value("Max Case", {"Cumulative_Project_Profit": 0}, "Cumulative_Project_Profit") == 0


def test_validator_accepts_explicit_pending_marker_only_for_maxcase_daily_cumulative_profit():
    data = _fixture_data()
    assert _validate_representatives(data, "canonical") is True

    data = _fixture_data()
    data["representatives_by_scenario"]["C100_G100"]["P50"]["daily"][0][
        "Cumulative_Project_Profit"
    ] = "PENDING_DATA_SOURCE"
    with pytest.raises(RuntimeError, match="REPRESENTATIVE_DAILY_TERMINAL_MISMATCH"):
        _validate_representatives(data, "canonical")


def test_representative_sheet_writes_pending_data_source_markers():
    workbook = Workbook()
    write_representatives(workbook, _fixture_data()["representatives_by_scenario"])
    sheet = workbook["REPRESENTATIVE_CASES"]

    # C100_G100 rows: P10 (2-3), P50 (4-5), P90 (6-7), Loss (8-9), Max Case (10-11).
    assert sheet["L11"].value == "PENDING_DATA_SOURCE"
    assert sheet["M11"].value == "PENDING_DATA_SOURCE"
    assert sheet["P11"].value == "PENDING_DATA_SOURCE"
    assert sheet["P5"].value == 40
