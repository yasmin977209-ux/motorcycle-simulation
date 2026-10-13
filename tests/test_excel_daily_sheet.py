"""Regression tests for the CP-EXCEL-DAILY-FIX serializer.

The Stage 12 binary artifact is not present in the repository tree and cannot be
read through the connected GitHub text-file interface. The 25-scenario test is
therefore fixture-based: it validates Excel serialization and date/value
integrity but does not claim to reselect or authenticate historical P50 trials.
"""
from datetime import date, datetime
from pathlib import Path
import tempfile

from openpyxl import Workbook, load_workbook

from scripts.excel_builder import write_daily_sheet


START_DATE = date(2027, 1, 1)
FINAL_CLOSE_DATE = date(2027, 1, 3)
COLLECTIONS = (30, 50, 70, 85, 100)
RECOVERIES = (0, 30, 50, 70, 100)
FIXTURE_ARTIFACT = Path(tempfile.gettempdir()) / "cp-excel-daily-fixture.xlsx"


def p50_daily_fixture(offset: int = 0) -> dict:
    """Return a preselected, synthetic representative-P50 daily payload."""
    return {
        "daily": [
            {
                "date": date(2027, 1, 1),
                "Cash": 100_000 + offset,
                "Final_Close_Date": FINAL_CLOSE_DATE,
                "Accounts_Receivable": None,
            },
            {
                "date": date(2027, 1, 2),
                "Cash": 99_000 + offset,
                "Final_Close_Date": FINAL_CLOSE_DATE,
                "Accounts_Receivable": 250 + offset,
            },
            {
                "date": date(2027, 1, 3),
                "Cash": 98_500 + offset,
                "Final_Close_Date": FINAL_CLOSE_DATE,
                "Accounts_Receivable": 0,
            },
        ]
    }


def _normalise_excel_value(value):
    # openpyxl reads an Excel date cell back as datetime at midnight.
    if isinstance(value, datetime):
        return value.date()
    return value


def _expected_scenarios():
    return [
        f"C{collection:03d}_G{recovery:03d}"
        for collection in COLLECTIONS
        for recovery in RECOVERIES
    ]


def test_write_daily_sheet_materializes_dictionary_values():
    payload = p50_daily_fixture()
    wb = Workbook()
    write_daily_sheet(wb, "C030_G000", payload)
    ws = wb["C030_G000_DAILY"]
    headers = list(payload["daily"][0])

    assert ws.max_column == len(headers)
    assert ws.max_row == len(payload["daily"]) + 1
    written_rows = list(ws.iter_rows(min_row=2, values_only=True))
    assert len(written_rows) == 3

    for actual, source in zip(written_rows, payload["daily"], strict=True):
        assert tuple(_normalise_excel_value(v) for v in actual) == tuple(
            source.get(header) for header in headers
        )
        assert all(not (isinstance(value, str) and value in headers) for value in actual)

    assert type(ws.cell(row=2, column=headers.index("Cash") + 1).value) is int
    assert isinstance(ws.cell(row=2, column=headers.index("date") + 1).value, date)
    assert ws.cell(row=2, column=headers.index("Accounts_Receivable") + 1).value is None
    assert len(set(tuple(row) for row in written_rows)) > 1


def test_empty_daily_payload_writes_header_only():
    wb = Workbook()
    write_daily_sheet(wb, "EMPTY", {"daily": []})
    ws = wb["EMPTY_DAILY"]
    assert ws.max_column == 1
    assert ws.max_row == 1
    assert ws["A1"].value == "date"


def test_fixture_integration_writes_and_reopens_all_25_daily_sheets():
    """Fixture-based acceptance substitute for the unavailable Stage 12 artifact."""
    scenarios = _expected_scenarios()
    payloads = {
        scenario: p50_daily_fixture(offset=index * 100)
        for index, scenario in enumerate(scenarios)
    }

    wb = Workbook()
    wb.remove(wb.active)
    for scenario in scenarios:
        write_daily_sheet(wb, scenario, payloads[scenario])

    assert len(wb.sheetnames) == 25
    assert set(wb.sheetnames) == {f"{scenario}_DAILY" for scenario in scenarios}
    wb.save(FIXTURE_ARTIFACT)

    inspected = load_workbook(FIXTURE_ARTIFACT, data_only=True, read_only=False)
    daily_sheets = [name for name in inspected.sheetnames if name.endswith("_DAILY")]
    assert len(daily_sheets) == 25

    for scenario in scenarios:
        payload = payloads[scenario]
        ws = inspected[f"{scenario}_DAILY"]
        headers = list(payload["daily"][0])
        assert ws.max_column == len(headers)
        assert ws.max_row == len(payload["daily"]) + 1

        actual_rows = list(
            ws.iter_rows(min_row=2, max_col=len(headers), values_only=True)
        )
        assert len(actual_rows) == len(payload["daily"])

        for actual, source in zip(actual_rows, payload["daily"], strict=True):
            normalised = tuple(_normalise_excel_value(value) for value in actual)
            assert normalised == tuple(source.get(header) for header in headers)
            assert all(
                not (isinstance(value, str) and value in headers)
                for value in actual
            )

        date_index = headers.index("date")
        dates = [_normalise_excel_value(row[date_index]) for row in actual_rows]
        assert dates == [date(2027, 1, 1), date(2027, 1, 2), date(2027, 1, 3)]
        assert dates[0] == START_DATE
        assert dates[-1] == FINAL_CLOSE_DATE
        assert all(ws.cell(row=row_index, column=date_index + 1).is_date for row_index in range(2, ws.max_row + 1))

        cash_index = headers.index("Cash")
        assert all(type(row[cash_index]) is int for row in actual_rows)
        receivable_index = headers.index("Accounts_Receivable")
        assert actual_rows[0][receivable_index] is None
        assert len(set(tuple(row) for row in actual_rows)) > 1

    inspected.close()
