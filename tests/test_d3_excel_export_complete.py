from __future__ import annotations

import gzip
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook

from scripts.d3_excel_export_complete import (
    load_extension,
    validate_source_dates,
    numeric_pair,
    registry_scenarios,
    trace_ids,
)
from scripts.d3_registry_extension import build_extension



def test_exporter_rejects_pre_cutoff_source_extension_even_without_archive_build():
    from scripts.d3_registry_extension import SOURCE_RUN_CREATED_AT_UTC
    from scripts.s6_artifact_reader import PINS

    extension = {
        "source_artifacts": {
            role: {"run_created_at_utc": SOURCE_RUN_CREATED_AT_UTC[pin.run_id]}
            for role, pin in PINS.items()
        }
    }
    with pytest.raises(ValueError, match="D3_SOURCE_ARTIFACT_PRE_CUTOFF_WITHOUT_OWNER_EXCEPTION"):
        validate_source_dates(extension)


def test_exporter_accepts_only_exact_three_pinned_artifacts_with_owner_exception():
    from scripts.d3_registry_extension import (
        SOURCE_RUN_CREATED_AT_UTC, OWNER_APPROVED_SOURCE_DATE_EXCEPTION,
        EXPECTED_AGGREGATE_HEAD, EXPECTED_FULL_LOGGING_HEAD, EXPECTED_C100_HEAD,
    )
    from scripts.s6_artifact_reader import PINS

    expected_heads = {
        "aggregate": EXPECTED_AGGREGATE_HEAD,
        "full_logging": EXPECTED_FULL_LOGGING_HEAD,
        "c100": EXPECTED_C100_HEAD,
    }
    sources = {}
    for role, pin in PINS.items():
        sources[role] = {
            "artifact_id": pin.artifact_id,
            "run_id": pin.run_id,
            "size_bytes": pin.size_bytes,
            "sha256": pin.sha256,
            "filename": pin.filename,
            "workflow_run_head_sha": expected_heads[role],
            "run_created_at_utc": SOURCE_RUN_CREATED_AT_UTC[pin.run_id],
            "source_date_exception": OWNER_APPROVED_SOURCE_DATE_EXCEPTION,
            "source_date_exception_scope": "D3_ONLY_EXACT_THREE_PINNED_ARTIFACTS",
            "source_date_exception_owner_approval": "APPROVED_2026-11-02",
            "evidence_status": "VERIFIED_LIVE",
        }
    assert validate_source_dates({"source_artifacts": sources}) is None


def test_exporter_accepts_only_post_cutoff_exact_pins(monkeypatch):
    from scripts import d3_registry_extension as source_module
    from scripts.d3_registry_extension import (
        EXPECTED_AGGREGATE_HEAD, EXPECTED_FULL_LOGGING_HEAD, EXPECTED_C100_HEAD,
    )
    from scripts.s6_artifact_reader import PINS

    expected_heads = {
        "aggregate": EXPECTED_AGGREGATE_HEAD,
        "full_logging": EXPECTED_FULL_LOGGING_HEAD,
        "c100": EXPECTED_C100_HEAD,
    }
    eligible_date = "2026-11-01T00:00:00Z"
    sources = {}
    for role, pin in PINS.items():
        monkeypatch.setitem(source_module.SOURCE_RUN_CREATED_AT_UTC, pin.run_id, eligible_date)
        sources[role] = {
            "artifact_id": pin.artifact_id,
            "run_id": pin.run_id,
            "size_bytes": pin.size_bytes,
            "sha256": pin.sha256,
            "filename": pin.filename,
            "workflow_run_head_sha": expected_heads[role],
            "run_created_at_utc": eligible_date,
            "evidence_status": "VERIFIED_LIVE",
        }
    assert validate_source_dates({"source_artifacts": sources}) is None


def test_exporter_rejects_source_metadata_that_does_not_match_artifact_pin(monkeypatch):
    from scripts import d3_registry_extension as source_module
    from scripts.d3_registry_extension import (
        EXPECTED_AGGREGATE_HEAD, EXPECTED_FULL_LOGGING_HEAD, EXPECTED_C100_HEAD,
    )
    from scripts.s6_artifact_reader import PINS

    expected_heads = {
        "aggregate": EXPECTED_AGGREGATE_HEAD,
        "full_logging": EXPECTED_FULL_LOGGING_HEAD,
        "c100": EXPECTED_C100_HEAD,
    }
    eligible_date = "2026-11-01T00:00:00Z"
    sources = {}
    for role, pin in PINS.items():
        monkeypatch.setitem(source_module.SOURCE_RUN_CREATED_AT_UTC, pin.run_id, eligible_date)
        sources[role] = {
            "artifact_id": pin.artifact_id,
            "run_id": pin.run_id,
            "size_bytes": pin.size_bytes,
            "sha256": pin.sha256,
            "filename": pin.filename,
            "workflow_run_head_sha": expected_heads[role],
            "run_created_at_utc": eligible_date,
            "evidence_status": "VERIFIED_LIVE",
        }
    sources["aggregate"]["artifact_id"] += 1
    with pytest.raises(ValueError, match="D3_SOURCE_ARTIFACT_PIN_MISMATCH:aggregate"):
        validate_source_dates({"source_artifacts": sources})


def test_exporter_rejects_missing_source_date_metadata():
    from scripts.s6_artifact_reader import PINS

    extension = {"source_artifacts": {role: {} for role in PINS}}
    with pytest.raises(ValueError, match="D3_SOURCE_ARTIFACT_RUN_DATE_UNPINNED"):
        validate_source_dates(extension)

def test_registry_scenarios_requires_complete_five_by_five_grid():
    scenarios = [
        f"C{c:03d}_G{g:03d}"
        for c in (30, 50, 70, 85, 100)
        for g in (0, 30, 50, 70, 100)
    ]
    registry = {"entries": [{"scenario_id": sid} for sid in scenarios], "daily_series": []}
    assert registry_scenarios(registry) == sorted(scenarios)


def test_registry_scenarios_rejects_missing_scenario():
    registry = {
        "entries": [{"scenario_id": f"C{c:03d}_G{g:03d}"} for c in (30, 50, 70, 85, 100)
                    for g in (0, 30, 50, 70, 100) if not (c == 100 and g == 100)],
        "daily_series": [],
    }
    with pytest.raises(ValueError, match="D3_SCENARIO_COVERAGE_INVALID"):
        registry_scenarios(registry)


def test_numeric_pair_is_deterministic_and_rejects_non_integer_values():
    case = {
        "scenario_id": "C030_G000",
        "trial_id": 7,
        "source_member_prefix": "stagec-output/full_logging/fixture/",
        "source_artifact_sha256": "a" * 64,
    }
    first = numeric_pair(case, "daily_snapshots.jsonl.gz", 2, "Cash", 123)
    second = numeric_pair(case, "daily_snapshots.jsonl.gz", 2, "Cash", 123)
    assert first == second
    assert first[0] == 123
    assert first[1].startswith("NR-")
    with pytest.raises(ValueError, match="D3_WORKBOOK_NUMERIC_VALUE_NOT_INTEGER"):
        numeric_pair(case, "daily_snapshots.jsonl.gz", 2, "Cash", 123.5)


def test_load_extension_fails_closed_on_unknown_schema(tmp_path: Path):
    path = tmp_path / "extension.json.gz"
    path.write_bytes(gzip.compress(b'{"schema_version":"unknown"}'))
    with pytest.raises(ValueError, match="D3_REGISTRY_EXTENSION_SCHEMA_INVALID"):
        load_extension(str(path), "b" * 64)


def test_load_extension_rejects_base_registry_mismatch(tmp_path: Path):
    path = tmp_path / "extension.json.gz"
    payload = b'{"schema_version":"d3-number-registry-extension-v1","base_registry_sha256":"wrong"}'
    path.write_bytes(gzip.compress(payload))
    with pytest.raises(ValueError, match="D3_REGISTRY_EXTENSION_BASE_PIN_MISMATCH"):
        load_extension(str(path), "b" * 64)


def test_trace_ids_accepts_paired_numeric_values(tmp_path: Path):
    path = tmp_path / "paired.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "DATA"
    ws.append(["Cash", "Cash_number_id"])
    ws.append([100, "NR-0123456789abcdef01234567"])
    wb.save(path)
    assert trace_ids([path]) == {"numeric_cells_checked": 1, "untraced_numeric_cells": 0}


def test_trace_ids_rejects_unpaired_numeric_values(tmp_path: Path):
    path = tmp_path / "unpaired.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "DATA"
    ws.append(["Cash", "Cash_number_id"])
    ws.append([100, ""])
    wb.save(path)
    with pytest.raises(ValueError, match="UNTRACED_NUMERIC_CELL"):
        trace_ids([path])


def test_build_extension_blocks_before_reading_registry_or_opening_archives(monkeypatch):
    from scripts import d3_registry_extension as module

    def forbidden(*args, **kwargs):
        raise AssertionError("SOURCE_ARCHIVE_READER_MUST_NOT_BE_OPENED")

    monkeypatch.setattr(module.S6ArtifactReader, "open_all", forbidden)
    with pytest.raises(ValueError, match="SOURCE_ARTIFACT_PRE_CUTOFF_PROHIBITED"):
        build_extension(
            {"aggregate": "unused", "full_logging": "unused", "c100": "unused"},
            "this-file-must-not-be-read.json",
        )



def test_missing_d3_requirements_block_gate():
    from scripts.d3_excel_export_complete import d3_gate_status, d3_requirement_statuses
    statuses = d3_requirement_statuses()
    assert all(statuses[f'D3-{n:02d}'] == 'MISSING_EVIDENCE' for n in range(7, 14))
    assert d3_gate_status(statuses) == 'BLOCKED_MISSING_EVIDENCE'



def test_verified_extension_promotes_only_source_backed_scoped_requirements():
    from scripts.d3_excel_export_complete import d3_requirement_statuses, d3_gate_status
    from scripts.d3_registry_extension import LEDGER_FILES, ROLLFORWARD_KEYS, FULL_LOGGING_NORMALIZED_STATUS
    from scripts.s6_artifact_reader import S6_COHORT, C100_COHORT

    scenarios = [
        f"C{c:03d}_G{g:03d}"
        for c in (30, 50, 70, 85, 100)
        for g in (0, 30, 50, 70, 100)
    ]
    member_meta = {"sha256": "a" * 64, "size_bytes": 10}
    cases = []
    distribution = []
    for sid in scenarios:
        is_c100 = sid.startswith("C100_")
        cohort = C100_COHORT if is_c100 else S6_COHORT
        trial_count = 300 if is_c100 else 2400
        cases.append({
            "scenario_id": sid,
            "cohort_id": cohort,
            "daily_rows": [{
                "Partner1_Reinvestment_Balance": 0,
                "Partner2_Reinvestment_Balance": 0,
            }],
            "source_members": {name: dict(member_meta) for name in LEDGER_FILES + ("trial_result.json",)},
            "assets": [],
            "claims": [],
            "contracts": [],
            "rollforwards": {key: [{}] for key in ROLLFORWARD_KEYS},
        })
        distribution.append({
            "scenario_id": sid,
            "trial_count": trial_count,
            "evidence_status": "VERIFIED_LIVE",
            "source_member_sha256": "b" * 64,
            "source_member_size_bytes": 20,
        })
    extension = {
        "representative_cases": cases,
        "representative_role_cases": [{} for _ in range(105)],
        "full_logging_validation": {
            "unique_trial_keys": 105, "role_assignments": 125, "completed_keys": 105,
            "failed_keys": 0, "post_write_audit_pass_count": 105,
            "normalized_status": FULL_LOGGING_NORMALIZED_STATUS,
        },
        "c100_validation": {
            "daily_reuse_status": "PASS_SCOPED_C100_DAILY_REUSE",
            "daily_rows_per_scenario": 2198, "golden_common_field_path_matches": 5,
            "golden_revalidation": "NOT_RUN",
        },
        "final_close_date_distribution": distribution,
        "close_date_validation": {
            "total_trial_count": 49500, "scenario_count": 25,
            "S6_trial_count": 48000, "C100_trial_count": 1500,
        },
    }
    statuses = d3_requirement_statuses(extension)
    assert all(statuses[f"D3-{n:02d}"] == "PASS_SCOPED_WITH_LIMITATIONS" for n in range(5, 13))
    assert statuses["D3-13"] == "PASS_SCOPED"
    assert statuses["D3-18"] == "NOT_RUN"
    assert d3_gate_status(statuses) == "BLOCKED_MISSING_EVIDENCE"



def test_saved_d3_status_sheets_match_blocked_gate(tmp_path: Path):
    from scripts import d3_excel_export_complete as exporter

    wb = Workbook()
    ws = wb.active
    ws.title = "README"
    ws.append(["field", "value"])
    exporter.write_d3_readme_status_rows(ws)
    exporter.write_validation_summary(wb, "en")
    path = tmp_path / "d3-status.xlsx"
    wb.save(path)
    wb.close()

    checked = load_workbook(path, read_only=True, data_only=True)
    try:
        readme = {r[0]: r[1] for r in checked["README"].iter_rows(values_only=True) if r[0]}
        summary = {r[0]: r[1] for r in checked["VALIDATION_SUMMARY"].iter_rows(values_only=True) if r[0]}
        assert readme["D3 gate"] == "BLOCKED_MISSING_EVIDENCE"
        assert readme["Full Logging"].startswith("NOT_VERIFIED_105_OF_105")
        assert summary["D3 gate"] == "BLOCKED_MISSING_EVIDENCE"
        assert summary["D3 source coverage"] == "BLOCKED_MISSING_EVIDENCE"
        assert all(summary[f"D3-{i:02d}"] == "MISSING_EVIDENCE" for i in range(7, 14))
        assert summary["D3-18"] == "NOT_RUN"
    finally:
        checked.close()



def test_write_detail_sheet_serializes_trial_id_as_text(tmp_path: Path):
    from scripts.d3_excel_export_complete import DAILY_DETAIL_FIELDS, write_detail_sheet

    case = {
        "scenario_id": "C030_G000",
        "cohort_id": "s6-v23-test",
        "trial_id": 17,
        "source_member_prefix": "stagec-output/full_logging/fixture/",
        "source_artifact_sha256": "a" * 64,
        "daily_rows": [{
            "date": "2026-10-30",
            **{field: index + 1 for index, field in enumerate(DAILY_DETAIL_FIELDS)},
        }],
    }
    wb = Workbook(write_only=True)
    write_detail_sheet(wb, "DAILY", case, "en")
    path = tmp_path / "trial-id-text.xlsx"
    wb.save(path)
    wb.close()

    checked = load_workbook(path, read_only=True, data_only=False)
    try:
        ws = checked["C030_G000_DAILY"]
        assert ws["C2"].value == "trial_id=17"
        assert ws["C2"].data_type == "s"
        assert trace_ids([path]) == {"numeric_cells_checked": len(DAILY_DETAIL_FIELDS), "untraced_numeric_cells": 0}
    finally:
        checked.close()
