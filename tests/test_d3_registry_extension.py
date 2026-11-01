from fractions import Fraction

import pytest

from scripts.d3_registry_extension import (
    ledger_number_id, source_entry, filtered_asset, close_date_rows, json_bytes,
)


def test_ledger_number_id_is_stable_and_field_specific():
    a = ledger_number_id("a" * 64, "C030_G000", 7, "daily_snapshots.jsonl.gz", 3, "Cash")
    b = ledger_number_id("a" * 64, "C030_G000", 7, "daily_snapshots.jsonl.gz", 3, "Cash")
    c = ledger_number_id("a" * 64, "C030_G000", 7, "daily_snapshots.jsonl.gz", 3, "Net_Equity")
    assert a == b
    assert a.startswith("NR-")
    assert a != c


def test_filtered_asset_omits_nested_histories_but_preserves_required_fields():
    row = {
        "bike_id": "BK0001", "gross_cost": 360000, "accumulated_depreciation": 500,
        "net_book_value": 359500, "current_state": "ACTIVE_PRIMARY",
        "lifecycle_history": [{"large": "history"}], "receivables_ledger": [{"large": "ledger"}],
    }
    result = filtered_asset(row)
    assert result["bike_id"] == "BK0001"
    assert result["gross_cost"] == 360000
    assert result["accumulated_depreciation"] == 500
    assert "lifecycle_history" not in result
    assert "receivables_ledger" not in result


def test_source_entry_preserves_exact_fraction_and_provenance():
    artifact = {"artifact_id": 1, "run_id": 2, "sha256": "b" * 64}
    entry = source_entry(
        scenario_id="C030_G000", sample_n=2400,
        metric_name="C030_G000.N2400.mean.Cumulative_Project_Profit",
        value=Fraction(7, 3), artifact=artifact, member="trials_summary.parquet",
        member_sha256="c" * 64, member_size_bytes=123,
        source_commit="d" * 40, source_sha="e" * 40, cohort_id="s6-v23-test",
        n_total=2400, n_closed=2400, n_censored=0, n_unique_paths=2400,
        calculation_method="EXACT_FRACTION_MEAN_FROM_ALL_2400_TRIALS",
    )
    assert entry["exact_value"] == {"numerator": 7, "denominator": 3}
    assert entry["display_value"] == "2.33"
    assert entry["evidence_status"] == "VERIFIED_LIVE"
    assert entry["source_member_sha256"] == "c" * 64
    assert entry["number_id"].startswith("NR-")


def test_close_date_distribution_counts_every_trial_and_assigns_number_id():
    artifact = {"artifact_id": 3, "run_id": 4, "sha256": "f" * 64}
    rows = close_date_rows(
        "C100_G000", ["2033-01-06"] * 300, source_sha="1" * 40,
        cohort_id="c100-test", artifact=artifact, member="golden.json",
        member_sha256="2" * 64, member_size_bytes=456, source_commit="3" * 40,
        n_total=300, n_unique_paths=1,
    )
    assert len(rows) == 1
    assert rows[0]["trial_count"] == 300
    assert rows[0]["trial_count_number_id"].startswith("NR-")
    assert rows[0]["N_total"] == 300


def test_json_bytes_rejects_float_values():
    with pytest.raises(ValueError, match="FLOAT_FORBIDDEN"):
        json_bytes({"not_exact": 1.25})
