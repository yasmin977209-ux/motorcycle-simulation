from __future__ import annotations

import pytest

from scripts.excel_builder import resolve_build_mode


def test_adaptive_cohort_identity_selects_adaptive_mode_regardless_of_total_count():
    manifest = {
        "cohort_id": "STAGE13_ADAPTIVE_STABLE_PER_SCENARIO_V1",
        "total_trials": 15600,
    }
    assert resolve_build_mode(manifest) == "adaptive"


def test_only_approved_fixed_cohort_counts_auto_resolve():
    assert resolve_build_mode({"total_trials": 11005}) == "canonical"
    assert resolve_build_mode({
        "total_trials": 625,
        "cohort_id": "STAGE13_SAMPLE_TRIAL_IDS_26_50_V2",
    }) == "sample"


def test_unrecognized_cohort_never_falls_back_to_demo():
    with pytest.raises(ValueError, match="UNRECOGNIZED_COHORT_MODE"):
        resolve_build_mode({"total_trials": 15600})


def test_demo_mode_requires_explicit_request_for_fixture_data():
    assert resolve_build_mode({"total_trials": 50}, mode="demo") == "demo"


def test_unsupported_explicit_mode_is_rejected():
    with pytest.raises(ValueError, match="UNSUPPORTED_EXCEL_MODE"):
        resolve_build_mode({"total_trials": 11005}, mode="production")
