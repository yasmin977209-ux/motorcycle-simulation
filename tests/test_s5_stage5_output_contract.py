from __future__ import annotations

from typing import Any

import constants
from monte_carlo import TrialResult, build_daily_distribution


def _trial(trial_id: int, equity: int, close_date: str) -> TrialResult:
    return TrialResult(
        scenario_id="C085_G100",
        collection_probability=0.85,
        recovery_rate_pct=100,
        trial_id=trial_id,
        final_close_date=close_date,
        final_net_project_equity=equity,
        final_cash=equity,
        cumulative_project_profit=equity,
        operating_net_profit=equity,
        termination_count=0,
        secondary_cycle_count=0,
        owned_bikes=1,
        held_assets=0,
        total_operating_revenue=equity,
        bad_debt=0,
        guarantee_recovered=0,
        partner1_final_entitlement=(equity * 70) // 100,
        partner2_final_entitlement=equity - ((equity * 70) // 100),
    )


def _row(day: str, trial_id: int, cash: int) -> dict[str, Any]:
    return {
        "date": day,
        "trial_id": trial_id,
        "Cash": cash,
        "Partner1_Reinvestment_Balance": 0,
        "Partner2_Reinvestment_Balance": 0,
        "Capital": cash,
        "Retained_Earnings": 0,
        "Net_Equity": cash,
        "Active_Bikes": 1,
        "Owned_Transferred_Bikes": 1,
        "Pending_Claims": 0,
        "Final_Close_Date": day,
    }


def _contains_float(value: Any) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_contains_float(item) for item in value)
    return False


def test_s5_daily_distribution_exact_active_and_carry_forward() -> None:
    first = _trial(constants.STAGE5_SMOKE_TRIAL_IDS[0], 101, "2027-01-01")
    second = _trial(constants.STAGE5_SMOKE_TRIAL_IDS[1], 200, "2027-01-02")
    slices = {
        first.trial_id: [_row("2027-01-01", first.trial_id, 101)],
        second.trial_id: [
            _row("2027-01-01", second.trial_id, 200),
            _row("2027-01-02", second.trial_id, 200),
        ],
    }

    active = build_daily_distribution(
        [first, second], slices, population_mode="ACTIVE_ONLY"
    )
    carry = build_daily_distribution(
        [first, second], slices,
        population_mode="ALL_TRIALS_CARRY_FORWARD",
    )

    active_day_two = next(
        row for row in active
        if row["date"] == "2027-01-02" and row["quantile_name"] == "P50"
    )
    carry_day_two = next(
        row for row in carry
        if row["date"] == "2027-01-02" and row["quantile_name"] == "P50"
    )
    carry_day_two_p25 = next(
        row for row in carry
        if row["date"] == "2027-01-02" and row["quantile_name"] == "P25"
    )

    assert active_day_two["population"] == "ACTIVE_ONLY"
    assert active_day_two["population_mode"] == "ACTIVE_ONLY"
    assert active_day_two["total_trials"] == 2
    assert active_day_two["population_count"] == 1
    assert active_day_two["active_trial_count"] == 1
    assert active_day_two["closed_trial_count"] == 1
    assert active_day_two["Cash"] == "200"
    assert carry_day_two["population"] == "ALL_TRIALS_CARRY_FORWARD"
    assert carry_day_two["population_mode"] == "ALL_TRIALS_CARRY_FORWARD"
    assert carry_day_two["total_trials"] == 2
    assert carry_day_two["population_count"] == 2
    assert carry_day_two["active_trial_count"] == 1
    assert carry_day_two["closed_trial_count"] == 1
    assert carry_day_two["Cash"] == "150.50"  # Appendix D: two decimals, ROUND_HALF_EVEN
    assert carry_day_two["Cash_exact_numerator"] == 301
    assert carry_day_two["Cash_exact_denominator"] == 2
    assert carry_day_two_p25["Cash"] == "125.75"
    assert carry_day_two_p25["Cash_exact_numerator"] == 503
    assert carry_day_two_p25["Cash_exact_denominator"] == 4
    assert not _contains_float(active)
    assert not _contains_float(carry)


def test_s5_summary_parquet_preserves_full_uint64_rng_checksum() -> None:
    import pyarrow as pa
    from scripts.s5_stage5_validation import _table_from_summary_records

    maximum_uint64 = (1 << 64) - 1
    table = _table_from_summary_records([
        {
            "scenario_id": "C085_G100",
            "trial_id": 1,
            "rng_checksum": maximum_uint64,
            "rng_draw_count": 1,
            "trial_fingerprint": "f" * 64,
            "rng_checksum_fingerprint_sha256": "a" * 64,
        }
    ])

    assert table.schema.field("rng_checksum").type == pa.uint64()
    assert table.column("rng_checksum").to_pylist() == [maximum_uint64]
    assert not any(pa.types.is_floating(field.type) for field in table.schema)

def test_s5_model_source_sha_is_separate_from_tested_commit_sha(monkeypatch) -> None:
    from scripts.s5_stage5_validation import _resolve_source_identities

    monkeypatch.setenv("S5_MODEL_SOURCE_SHA", "9fd34c2c4cf7250653ea6d86e33e1f939e6fba99")
    monkeypatch.setenv("GITHUB_SHA", "a" * 40)

    source_sha, tested_sha = _resolve_source_identities()
    assert source_sha == "9fd34c2c4cf7250653ea6d86e33e1f939e6fba99"
    assert tested_sha == "a" * 40
    assert source_sha != tested_sha
