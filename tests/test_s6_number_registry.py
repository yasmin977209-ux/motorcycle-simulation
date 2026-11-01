from decimal import Decimal

import pytest

from scripts.s6_number_registry import (
    CURRENT_REFERENCE_SHA256,
    _daily_resolution_indexes,
    _resolve_daily_number,
    HISTORICAL_EXECUTION_REFERENCE_SHA256,
    daily_number_id,
    display_fraction,
    no_floats,
    original_historical_report,
    resolve_number,
    source_number,
    stable_id,
    unit,
)


def make_daily_registry():
    series_id = stable_id(
        "D2S6-",
        ["C030_G000", "source", "cohort", "ACTIVE_ONLY", "Cash", "P50", "artifact"],
        20,
    )
    registry = {
        "entries": [],
        "daily_date_indexes": [{
            "scenario_id": "C030_G000",
            "first_date": "2027-01-01",
            "date_count": 2,
            "active_trial_counts": [2400, 2399],
        }],
        "daily_series": [{
            "series_id": series_id,
            "scenario_id": "C030_G000",
            "mode": "ACTIVE_ONLY",
            "metric_name": "Cash",
            "quantile_name": "P50",
            "first_date": "2027-01-01",
            "date_count": 2,
            "values": [[10, 1], [25, 2]],
            "unit": "YER",
            "source_artifact_id": 12852969854,
            "source_run_id": 40773412377,
            "source_member": "daily_distribution.parquet",
            "source_member_sha256": "c" * 64,
            "source_member_size_bytes": 4881090,
            "source_artifact_sha256": "d" * 64,
            "source_file_path": "results_stage7_s6/aggregate/daily_distribution.parquet",
            "source_commit": "4f2f2cc16d0cb5125262088704febccbae6f50ed",
            "source_sha": "da1a9ea9b5cd789c944de3f07b08395bb67c49e7",
            "cohort_id": "s6-v23-da1a9ea9",
            "N_total": 2400,
            "N_closed": 2400,
            "N_censored": 0,
            "N_unique_paths": 2400,
            "gate_status": {"gate_a": "NOT_DECLARED", "gate_b": "FAIL_SCOPED"},
            "evidence_status": "VERIFIED_LIVE",
            "calculation_method": "LINEAR_QUANTILE_FRACTION",
            "rounding_method": "ROUND_HALF_EVEN_IF_NON_INTEGER_ELSE_EXACT_INTEGER",
        }],
    }
    return registry, series_id


def test_exact_fraction_display_and_half_even():
    assert display_fraction(7, 1) == "7"
    assert display_fraction(1, 8) == "0.12"
    assert display_fraction(3, 8) == "0.38"
    assert display_fraction(5, 2) == "2.50"


def test_non_reduced_fraction_is_rejected():
    with pytest.raises(ValueError, match="NOT_REDUCED"):
        display_fraction(2, 4)


def test_source_decimal_preserves_exact_ratio_without_float():
    assert source_number(Decimal("0.30")) == (3, 10, "0.30", "SOURCE_DECIMAL_EXACT")
    assert source_number(7) == (7, 1, "7", "EXACT_INTEGER")
    with pytest.raises(ValueError):
        source_number(0.3)
    with pytest.raises(ValueError):
        source_number(True)


def test_stable_number_id_is_deterministic_and_keyed():
    key = ["aggregate", "artifact-sha", "metric", "source"]
    assert stable_id("NR-", key) == stable_id("NR-", list(key))
    assert stable_id("NR-", key) != stable_id("NR-", key + ["other"])


def test_daily_number_id_uses_stable_series_and_offset():
    registry, series_id = make_daily_registry()
    first = daily_number_id(series_id, 0)
    second = daily_number_id(series_id, 1)
    assert first == daily_number_id(series_id, 0)
    assert first.startswith("D2D-")
    assert first != second
    with pytest.raises(ValueError):
        daily_number_id(series_id, -1)
    with pytest.raises(ValueError):
        daily_number_id("D2S6-invalid", 0)


def test_daily_number_resolves_exact_value_date_and_full_provenance():
    registry, series_id = make_daily_registry()
    number = resolve_number(registry, daily_number_id(series_id, 1))
    assert number["date"] == "2027-01-02"
    assert number["metric_name"] == "Cash"
    assert number["scenario_id"] == "C030_G000"
    assert number["numerator"] == 25
    assert number["denominator"] == 2
    assert number["exact_value"] == {"numerator": 25, "denominator": 2}
    assert number["display_value"] == "12.50"
    assert number["sample_trial_count"] == 2399
    assert number["source_artifact_id"] == 12852969854
    assert number["source_member_sha256"] == "c" * 64
    assert number["source_file_path"].endswith("daily_distribution.parquet")
    assert number["evidence_status"] == "VERIFIED_LIVE"


def test_daily_number_resolver_rejects_unknown_series_and_out_of_range():
    registry, series_id = make_daily_registry()
    with pytest.raises(KeyError):
        resolve_number(registry, "D2D-" + "f" * 20 + "-000000")
    with pytest.raises(KeyError):
        resolve_number(registry, daily_number_id(series_id, 2))


def test_no_floats_rejects_nested_financial_values():
    with pytest.raises(ValueError, match="FLOAT_FORBIDDEN"):
        no_floats({"values": [1, {"nested": 1.0}]})


def test_units_are_not_guessed_for_unknown_metrics():
    assert unit("Final_Net_Project_Equity") == "YER"
    assert unit("Probability_of_Accounting_Loss") == "probability"
    assert unit("Active_Bikes") == "count"
    assert unit("unknown_custom_metric") is None


def test_governing_and_historical_reference_identities_are_separate():
    assert CURRENT_REFERENCE_SHA256 == "225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b"
    assert HISTORICAL_EXECUTION_REFERENCE_SHA256 == "e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f"
    assert CURRENT_REFERENCE_SHA256 != HISTORICAL_EXECUTION_REFERENCE_SHA256



def test_daily_resolver_all_trials_mode_uses_total_sample_count():
    registry, series_id = make_daily_registry()
    registry["daily_series"][0]["mode"] = "ALL_TRIALS_CARRY_FORWARD"
    series_by_id, indexes_by_scenario = _daily_resolution_indexes(registry)
    number_id = daily_number_id(series_id, 1)
    resolved = _resolve_daily_number(registry, number_id, series_by_id, indexes_by_scenario)
    assert resolved["date"] == "2027-01-02"
    assert resolved["active_trial_count"] == 2399
    assert resolved["sample_trial_count"] == 2400
    assert resolved["numerator"] == 25
    assert resolved["denominator"] == 2
    assert resolved["locator"].endswith("2027-01-02/ALL_TRIALS_CARRY_FORWARD/Cash/P50")


def test_daily_resolver_rejects_invalid_sample_provenance_and_unknown_id():
    registry, series_id = make_daily_registry()
    series_by_id, indexes_by_scenario = _daily_resolution_indexes(registry)
    registry["daily_date_indexes"][0]["active_trial_counts"][1] = True
    with pytest.raises(ValueError, match="DAILY_NUMBER_SAMPLE_PROVENANCE_INVALID"):
        _resolve_daily_number(registry, daily_number_id(series_id, 1), series_by_id, indexes_by_scenario)
    with pytest.raises(KeyError):
        resolve_number(registry, "D2D-" + "f" * 20 + "-000000")


def test_historical_local_report_is_unwrapped_without_loss():
    original = {"audit_id": "D2-LOCAL-2026-10-31", "entry_count": 13954, "status": "REPORTED_ONLY_LOCAL_ONLY"}
    prior = {"audit_id": "D2-CANONICAL-OLD", "entry_count": 2640, "historical_local_report": {"original_report": original}}
    current = {"audit_id": "D2-CANONICAL-NEW", "entry_count": 2640, "historical_local_report": {"original_report": prior}}
    assert original_historical_report(current) == original
