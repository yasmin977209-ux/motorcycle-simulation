from __future__ import annotations

import gzip
import hashlib
import io
import json
import os
import zipfile
from datetime import date, timedelta
from pathlib import Path

import pytest

from scripts.audit_s6_deliverables_bundle import (
    PACKAGE, FILES, EXPECTED, GOV_SHA, HIST_SHA, REGISTRY_PATH,
    EXTENSION_SIZE, EXTENSION_SHA, build_d3_evidence_indexes,
    scan_xlsx_xml, load_d5_pin, parse_sums, sha,
)
from scripts.s6_representative_full_logging import (
    validate_daily_balance_rows, validate_rollforward_rows,
)


@pytest.fixture(scope="session")
def d5_bundle():
    artifact_path = Path(os.environ["D5_ARTIFACT_ZIP"])
    outer_bytes = artifact_path.read_bytes()
    with zipfile.ZipFile(io.BytesIO(outer_bytes)) as outer:
        outer_names = set(outer.namelist())
        package_bytes = outer.read(PACKAGE)
        outer_manifest = outer.read("manifest.json")
        sums_raw = outer.read("SHA256SUMS.txt")
    with zipfile.ZipFile(io.BytesIO(package_bytes)) as package:
        payload = {name: package.read(name) for name in package.namelist()}
    manifest = json.loads(payload["manifest.json"])
    return {
        "artifact_path": artifact_path,
        "outer_bytes": outer_bytes,
        "outer_names": outer_names,
        "package_bytes": package_bytes,
        "payload": payload,
        "manifest": manifest,
        "outer_manifest": outer_manifest,
        "sums_raw": sums_raw,
    }


@pytest.fixture(scope="session")
def workbook_audits(d5_bundle, tmp_path_factory):
    registry = json.loads(Path(REGISTRY_PATH).read_text(encoding="utf-8"))
    indexes = build_d3_evidence_indexes(Path("."), registry)
    root = tmp_path_factory.mktemp("d6-workbooks")
    results = {}
    for name in ("Full_Results_EN.xlsx", "النتائج_الكاملة_AR.xlsx"):
        path = root / name
        path.write_bytes(d5_bundle["payload"][name])
        results[name] = scan_xlsx_xml(path, indexes[0], indexes[1], indexes[2], registry)
    return results


@pytest.fixture(scope="session")
def d3_extension():
    path = Path("deliverables/D3_NUMBER_REGISTRY_EXTENSION.json.gz")
    raw = path.read_bytes()
    assert len(raw) == EXTENSION_SIZE
    assert hashlib.sha256(raw).hexdigest() == EXTENSION_SHA
    return json.loads(gzip.decompress(raw).decode("utf-8"))


def test_175_bilingual_workbooks_have_185_ordered_sheets_and_numeric_parity(workbook_audits):
    ar = workbook_audits["النتائج_الكاملة_AR.xlsx"]
    en = workbook_audits["Full_Results_EN.xlsx"]
    assert len(ar["sheetnames"]) == len(en["sheetnames"]) == 185
    assert ar["sheetnames"] == en["sheetnames"]
    assert ar["numeric_count"] > 0 and en["numeric_count"] > 0
    assert ar["numeric_digest"] == en["numeric_digest"]


def test_179_package_manifest_pins_provenance_commit_command_runtime_and_seed(d5_bundle):
    m = d5_bundle["manifest"]
    assert m["package_status"] == "T2_INTERIM / NOT_FINAL_BLOCKED"
    assert m["repository"] == "yasmin977209-ux/motorcycle-simulation"
    assert m["branch"] == "tmp/d1-rebuild-20261101"
    assert m["spec_version"] == "2.4.0"
    assert m["current_governing_reference_sha256"] == GOV_SHA
    assert m["historical_execution_reference_sha256"] == HIST_SHA
    assert len(m["tested_build_commit_sha"]) == 40
    assert isinstance(m["build_workflow_run_id"], int) and m["build_workflow_run_id"] > 0
    assert m["source_identities"]["S6"]["MASTER_SEED"] == 20270101
    assert m["inputs"]["D4_source_run_id"] > 0
    assert len(m["inputs"]["D4_tested_sha"]) == 40
    assert len(m["inputs"]["D4_output_commit_sha"]) == 40
    assert len(m["inputs"]["D4_report_manifest_sha256"]) == 64
    assert m["runtime"]["python"] and m["runtime"]["openpyxl"] and m["runtime"]["python_docx"]


def test_180_daily_rows_are_ordered_and_preserved_for_105_keys_and_25_p50_cases(d3_extension):
    p50_cases = d3_extension["representative_cases"]
    role_cases = d3_extension["representative_role_cases"]
    assert len(p50_cases) == 25
    assert len(role_cases) == 105
    assert d3_extension["full_logging_validation"]["p50_scenario_coverage"] == 25
    assert d3_extension["full_logging_validation"]["unique_trial_keys"] == 105
    for case in p50_cases + role_cases:
        rows = case["daily_rows"]
        assert rows
        dates = [row["date"] for row in rows]
        assert dates == sorted(dates)
        assert len(dates) == len(set(dates))
        assert dates[-1] == case["final_close_date"]
        assert all(row["scenario_id"] == case["scenario_id"] for row in rows)
        assert all(row["trial_id"] == case["trial_id"] for row in rows)
        assert all(type(row["Cash"]) is int and type(row["Net_Equity"]) is int for row in rows)
    for case in p50_cases:
        dates = [row["date"] for row in case["daily_rows"]]
        for rows in case["rollforwards"].values():
            assert [row["date"] for row in rows] == dates


def test_181_partner_daily_balances_and_rollforwards_cover_105_keys_and_25_p50_cases(d3_extension):
    p50_cases = d3_extension["representative_cases"]
    role_cases = d3_extension["representative_role_cases"]
    assert len(p50_cases) == 25 and len(role_cases) == 105
    checked = 0
    for case in role_cases + p50_cases:
        audit = validate_daily_balance_rows(
            case["daily_rows"],
            trial_id=case["trial_id"],
            source_sha=case["source_sha"],
            cohort_id=case["cohort_id"],
            scenario_id=case["scenario_id"],
        )
        assert audit["partner1_balance_rows"] == audit["partner2_balance_rows"] == len(case["daily_rows"])
        checked += len(case["daily_rows"])
    rollforward_checks = 0
    for case in p50_cases:
        rows = case["daily_rows"]
        dates = [row["date"] for row in rows]
        rf = case["rollforwards"]
        result = validate_rollforward_rows(
            dates, rf["cash_rollforward"], rf["ar_rollforward"],
            rf["asset_rollforward"], rf["equity_rollforward"],
        )
        assert result["rollforward_mismatch_count"] == 0
        rollforward_checks += result["rollforward_equation_checks"]
    assert checked > 0 and rollforward_checks > 0


def test_182_all_financial_cells_match_exact_registry_values(workbook_audits):
    for result in workbook_audits.values():
        assert result["financial_count"] > 0
        assert result["financial_mismatch_count"] == 0


def test_183_c100_cross_cohort_reuse_is_explicit_and_not_merged(d5_bundle):
    m = d5_bundle["manifest"]
    s6 = m["source_identities"]["S6"]
    c100 = m["source_identities"]["C100"]
    assert s6["cohort_id"] != c100["cohort_id"]
    assert c100["classification"] == "CROSS_COHORT_DETERMINISTIC_REUSE"
    assert m["package_status"] == "T2_INTERIM / NOT_FINAL_BLOCKED"


def test_186_exact_eight_member_package_outer_artifact_crc_and_sha256sums(d5_bundle):
    m = d5_bundle["manifest"]
    assert d5_bundle["outer_names"] == {PACKAGE, "manifest.json", "SHA256SUMS.txt"}
    assert d5_bundle["outer_manifest"] == d5_bundle["payload"]["manifest.json"]
    assert len(d5_bundle["payload"]) == 8
    assert set(d5_bundle["payload"]) == EXPECTED
    assert m["package_member_count"] == 8
    assert m["package_status"] == "T2_INTERIM / NOT_FINAL_BLOCKED"
    sums = parse_sums(d5_bundle["sums_raw"])
    assert len(sums) == 10
    assert set(sums) == {PACKAGE, "manifest.json", *FILES, REGISTRY_PATH}
    assert sums[PACKAGE] == sha(d5_bundle["package_bytes"])
    assert sums["manifest.json"] == sha(d5_bundle["payload"]["manifest.json"])
    for name in FILES:
        assert sums[name] == sha(d5_bundle["payload"][name])
    assert sums[REGISTRY_PATH] == hashlib.sha256(Path(REGISTRY_PATH).read_bytes()).hexdigest()
    pin = load_d5_pin(Path("."))
    assert len(d5_bundle["outer_bytes"]) == pin["artifact_bytes"]
    assert sha(d5_bundle["outer_bytes"]) == pin["artifact_sha256"]
