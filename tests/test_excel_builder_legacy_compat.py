from __future__ import annotations

import inspect
from pathlib import Path

from openpyxl import Workbook

import scripts.excel_builder as builder


def test_legacy_public_names_and_call_signatures_remain_available():
    required = (
        "build_excel",
        "build_workbook",
        "load_scenario_trials",
        "load_scenario_daily_distribution",
        "representative_rows",
        "write_sensitivity",
        "write_daily_distribution",
        "write_representatives",
        "patch_xlsx_numeric_values",
        "save_workbook_preserving_stats_precision",
    )
    assert all(callable(getattr(builder, name, None)) for name in required)
    assert list(inspect.signature(builder.build_workbook).parameters) == [
        "dataset_root", "output_path", "manifest_path", "representatives_path", "mode"
    ]
    assert list(inspect.signature(builder.write_daily_distribution).parameters) == [
        "wb", "dataset_root"
    ]
    assert list(inspect.signature(builder.write_representatives).parameters) == [
        "wb", "manifest", "rep_path"
    ]


def test_legacy_daily_writer_signature_delegates_to_stage13(monkeypatch, tmp_path: Path):
    scenario_with_rows = "C030_G000"
    sample_rows = [{
        "date": "2026-01-01",
        "active_trial_count": 2,
        "P10_Cash": 10.0,
        "P50_Cash": 20.0,
    }]

    def fake_loader(dataset_root, scenario):
        assert Path(dataset_root) == tmp_path
        return sample_rows if scenario == scenario_with_rows else []

    monkeypatch.setattr(builder, "load_scenario_daily_distribution", fake_loader)
    workbook = Workbook()
    builder.write_daily_distribution(workbook, tmp_path)
    sheet = workbook["DAILY_DISTRIBUTION"]
    assert sheet["A2"].value == scenario_with_rows
    assert str(sheet["B2"].value).startswith("2026-01-01")
    assert sheet["D2"].value == 10.0
    workbook.close()
