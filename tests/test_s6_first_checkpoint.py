from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from scripts.s6_first_checkpoint import (
    current_git_commit,
    daily_path_fingerprints,
    validate_golden_approval_combined_map_pin,
    validate_required_scenario_files,
    validate_unique_trial_ids,
)
from scripts.audit_s6_daily_balance_artifact import validate_daily_balance_contract_record
from stats_integrity import validate_daily_distribution_rows


def _valid_distribution_rows():
    rows = []
    for mode in ("ACTIVE_ONLY", "ALL_TRIALS_CARRY_FORWARD"):
        for metric in ("Cash", "Net_Equity", "Active_Bikes", "Owned_Transferred_Bikes", "Pending_Claims"):
            for quantile in ("P10", "P25", "P50", "P75", "P90"):
                rows.append({
                    "source_sha": "a" * 40,
                    "cohort_id": "s6-v23-aaaaaaaa",
                    "scenario_id": "C085_G100",
                    "date": "2021-01-01",
                    "mode": mode,
                    "quantile_name": quantile,
                    "active_trial_count": 2,
                    "sample_trial_count": 2,
                    "metric_name": metric,
                    "exact_numerator": 7,
                    "exact_denominator": 2,
                    "display_value": "3.5",
                })
    return rows


def test_t01_duplicate_trial_ids_are_rejected_before_mapping():
    with pytest.raises(RuntimeError, match="S6_DUPLICATE_TRIAL_ID"):
        validate_unique_trial_ids([{"trial_id": 1}, {"trial_id": 1}], 2, context="T01")


def test_t02_required_manifest_file_inventory_must_be_complete(tmp_path: Path):
    (tmp_path / "trials_summary.parquet").write_bytes(b"x")
    manifest = {"files": {"trials_summary.parquet": {"size_bytes": 1, "sha256": hashlib.sha256(b"x").hexdigest()}}}
    with pytest.raises(RuntimeError, match="S6_SCENARIO_REQUIRED_FILE_MANIFEST_INCOMPLETE"):
        validate_required_scenario_files(tmp_path, manifest)


def test_t03_legacy_daily_path_rejects_duplicate_trial_date_rows():
    rows = [
        {"trial_id": 1, "date": "2021-01-01", "Cash": 10},
        {"trial_id": 1, "date": "2021-01-01", "Cash": 10},
    ]
    with pytest.raises(RuntimeError, match="S6_LEGACY_DAILY_DUPLICATE_TRIAL_DATE"):
        daily_path_fingerprints(rows)


def test_t04_daily_balance_contract_requires_complete_scope_and_row_counts():
    manifest = {
        "source_sha": "a" * 40,
        "cohort_id": "s6-v23-aaaaaaaa",
        "daily_balance_contract": {
            "schema_version": "s6-daily-balance-v1",
            "status": "PASS_SCOPED_POST_WRITE_BALANCE_CHECK",
            "rows_checked": 10,
            "balance_mismatch_count": 0,
            "required_integer_fields": [],
        },
    }
    with pytest.raises(RuntimeError, match="S6_DAILY_AUDIT_BALANCE_CONTRACT_MISMATCH"):
        validate_daily_balance_contract_record(manifest, {"balance_rows_checked": 10})


def test_t05_daily_distribution_missing_quantile_key_fails_coverage():
    rows = _valid_distribution_rows()
    rows.pop()
    with pytest.raises(RuntimeError, match="S6_DAILY_DISTRIBUTION_KEY_COVERAGE_MISMATCH"):
        validate_daily_distribution_rows(
            rows, scenario_id="C085_G100", source_sha="a" * 40,
            cohort_id="s6-v23-aaaaaaaa", expected_dates=["2021-01-01"],
            expected_trial_count=2,
        )


def test_t06_git_commit_is_not_fabricated_from_source_sha(monkeypatch):
    monkeypatch.delenv("GITHUB_SHA", raising=False)
    def unavailable(*args, **kwargs):
        raise FileNotFoundError("git executable unavailable")
    monkeypatch.setattr("scripts.s6_first_checkpoint.subprocess.run", unavailable)
    assert current_git_commit("a" * 40) is None


def test_t07_golden_approval_combined_map_pin_is_checked():
    with pytest.raises(RuntimeError, match="S6_GATE_A_GOLDEN_APPROVAL_COMBINED_MAP_PIN_MISMATCH"):
        validate_golden_approval_combined_map_pin(
            {"combined_financial_trial_fingerprint_map_sha256": "0" * 64},
            {"combined_financial_trial_fingerprint_map_sha256": "1" * 64},
            "1" * 64,
        )


def test_t08_manifest_file_hash_mismatch_is_rejected(tmp_path: Path):
    names = ("trials_summary.parquet", "daily_snapshots.parquet", "daily_distribution.parquet", "opt1_provenance.json")
    files = {}
    for name in names:
        (tmp_path / name).write_bytes(b"valid")
        files[name] = {"size_bytes": 5, "sha256": "0" * 64}
    with pytest.raises(RuntimeError, match="S6_SCENARIO_FILE_HASH_MISMATCH"):
        validate_required_scenario_files(tmp_path, {"files": files})


def test_t09_daily_distribution_source_cohort_identity_is_enforced():
    rows = _valid_distribution_rows()
    rows[0]["source_sha"] = "b" * 40
    with pytest.raises(RuntimeError, match="S6_DAILY_DISTRIBUTION_IDENTITY_MISMATCH"):
        validate_daily_distribution_rows(
            rows, scenario_id="C085_G100", source_sha="a" * 40,
            cohort_id="s6-v23-aaaaaaaa", expected_dates=["2021-01-01"],
            expected_trial_count=2,
        )


def test_t10_duplicate_daily_distribution_key_is_rejected():
    rows = _valid_distribution_rows()
    rows.append(dict(rows[0]))
    with pytest.raises(RuntimeError, match="S6_DAILY_DISTRIBUTION_DUPLICATE_KEY"):
        validate_daily_distribution_rows(
            rows, scenario_id="C085_G100", source_sha="a" * 40,
            cohort_id="s6-v23-aaaaaaaa", expected_dates=["2021-01-01"],
            expected_trial_count=2,
        )
