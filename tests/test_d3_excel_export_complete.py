from __future__ import annotations

import gzip
from pathlib import Path

import pytest
from openpyxl import Workbook

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
    with pytest.raises(ValueError, match="D3_SOURCE_ARTIFACT_PRE_CUTOFF_OR_UNPINNED"):
        validate_source_dates(extension)


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
    with pytest.raises(ValueError, match="D3_SOURCE_ARTIFACT_PRE_CUTOFF_OR_UNPINNED"):
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
