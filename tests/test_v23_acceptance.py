from __future__ import annotations

from dataclasses import replace
from datetime import date
from decimal import Decimal
from fractions import Fraction
from hashlib import sha256
import json
import zipfile
from io import BytesIO

import pytest

import constants
import daily_engine
import monte_carlo
import rng
import stats_integrity
from entities import format_bike_id, is_canonical_bike_id
from validation import (
    build_acceptance_registry,
    c100_path_summary,
    validate_bilingual_numeric_values,
    validate_c100_golden_identity,
    validate_cohort_identity,
    validate_daily_distribution_dates,
    validate_delivery_manifest,
    validate_number_registry_coverage,
    validate_rng_audit_records,
    validate_worker_equivalence_manifest,
)


SOURCE_SHA = "a" * 40


def _trial(trial_id: int, equity: int, *, checksum: int = 0, draws: int = 0) -> monte_carlo.TrialResult:
    return monte_carlo.TrialResult(
        scenario_id="C085_G100",
        collection_probability=0.85,
        recovery_rate_pct=100,
        trial_id=trial_id,
        final_close_date=None,
        final_net_project_equity=equity,
        final_cash=equity,
        cumulative_project_profit=equity,
        operating_net_profit=equity,
        termination_count=0,
        secondary_cycle_count=0,
        owned_bikes=10,
        held_assets=0,
        total_operating_revenue=0,
        bad_debt=0,
        guarantee_recovered=0,
        partner1_final_entitlement=(equity * 70) // 100,
        partner2_final_entitlement=equity - ((equity * 70) // 100),
        rng_checksum=checksum,
        rng_draw_count=draws,
    )


def _audit_record(trial_id: int, checksum: int, draws: int, *, scenario: str = "C085_G100") -> dict[str, object]:
    return {
        "scenario_id": scenario,
        "trial_id": trial_id,
        "rng_checksum": checksum,
        "rng_draw_count": draws,
        "rng_checksum_fingerprint_sha256": rng.rng_audit_fingerprint(
            source_sha=SOURCE_SHA,
            master_seed=constants.MASTER_SEED,
            scenario_id=scenario,
            trial_id=trial_id,
            rng_checksum=checksum,
            rng_draw_count=draws,
        ),
    }


def test_169_C100_golden_must_match_source_and_cohort_identity() -> None:
    assert validate_c100_golden_identity(
        expected_source_sha=SOURCE_SHA,
        actual_source_sha=SOURCE_SHA,
        expected_cohort_id="cohort-v23-new",
        actual_cohort_id="cohort-v23-new",
        expected_schema_version="v2.3",
        actual_schema_version="v2.3",
        expected_fingerprint_sha256="b" * 64,
        actual_fingerprint_sha256="b" * 64,
    )
    with pytest.raises(RuntimeError, match="C100_GOLDEN_SOURCE_SHA_MISMATCH"):
        validate_c100_golden_identity(
            expected_source_sha=SOURCE_SHA,
            actual_source_sha="c" * 40,
            expected_cohort_id="cohort-v23-new",
            actual_cohort_id="cohort-v23-new",
            expected_schema_version="v2.3",
            actual_schema_version="v2.3",
            expected_fingerprint_sha256="b" * 64,
            actual_fingerprint_sha256="b" * 64,
        )


def test_170_checksum_uniqueness_uses_draw_count_and_allows_zero() -> None:
    assert validate_rng_audit_records(
        [_audit_record(1, 0, 0), _audit_record(2, 0, 0)],
        source_sha=SOURCE_SHA,
        master_seed=constants.MASTER_SEED,
    ) == 2
    assert validate_rng_audit_records(
        [_audit_record(1, 0, 1)],
        source_sha=SOURCE_SHA,
        master_seed=constants.MASTER_SEED,
    ) == 1
    with pytest.raises(RuntimeError, match="DUPLICATE_RNG_CHECKSUM_DETECTED"):
        validate_rng_audit_records(
            [_audit_record(1, 0, 1), _audit_record(2, 0, 3)],
            source_sha=SOURCE_SHA,
            master_seed=constants.MASTER_SEED,
        )


def test_172_sequential_alpha_spending_is_exact_and_applied_to_gate_intervals() -> None:
    expected = (
        Fraction(1, 800),
        Fraction(1, 2400),
        Fraction(1, 4800),
        Fraction(1, 8000),
    )
    actual = tuple(stats_integrity.sequential_alpha_fraction(k) for k in range(1, 5))
    assert actual == expected
    assert all(type(value) is Fraction for value in actual)
    assert sum(actual) < Fraction(1, 400)

    from types import SimpleNamespace
    import run_batch
    mean_rows = [
        SimpleNamespace(**{field: value for field in run_batch.STABILITY_FIELDS})
        for value in (100, 102)
    ]
    mean_summary = run_batch._metric_summary(mean_rows, spending_index=3)
    expected_k3 = stats_integrity.sequential_alpha_fraction(3)
    assert all(
        metric["alpha_s_k_numerator"] == expected_k3.numerator
        and metric["alpha_s_k_denominator"] == expected_k3.denominator
        for metric in mean_summary.values()
    )

    # 600 observations have an N/2=300 check; at k=2 and k=1, respectively.
    # With zero losses, the valid upper bound -ln(alpha_s,k)/N exceeds the
    # descriptive 3/N bound; the descriptive bound alone must not PASS Gate B.
    indicator_rows = [
        SimpleNamespace(
            trial_id=i,
            cumulative_project_profit=i,
            final_cash=10000 + i,
            termination_count=i % 4,
            held_assets=i % 3,
        )
        for i in range(1, 601)
    ]
    indicator_summary = stats_integrity.time_uniform_indicator_summary(
        indicator_rows, k=2
    )
    assert set(indicator_summary["indicators"]) == {
        "P10_Cumulative_Project_Profit",
        "P50_Cumulative_Project_Profit",
        "P90_Cumulative_Project_Profit",
        "P90_Final_Cash",
        "Probability_of_Accounting_Loss",
        "P90_Termination_Count",
        "P90_Held_Assets",
    }
    loss = indicator_summary["indicators"]["Probability_of_Accounting_Loss"]
    assert loss["current_n"]["descriptive_3_over_n"] == "1/200"
    assert loss["current_n"]["upper_bound"] > 3 / 600
    assert loss["half_n"]["n"] == 300
    assert loss["half_n"]["spending_index"] == 1
    assert loss["stable"] is False

    # Three means must also evaluate accuracy at N and N/2.
    three_hundred = [
        SimpleNamespace(
            final_net_project_equity=i,
            partner1_final_entitlement=i,
            partner2_final_entitlement=i,
        )
        for i in range(1, 301)
    ]
    mean_at_n_and_half = run_batch._metric_summary(three_hundred, spending_index=1)
    for metric in mean_at_n_and_half.values():
        assert metric["half_n"]["n"] == 150
        assert metric["half_n"]["spending_index"] == 1
        assert metric["stable"] == (
            metric["stable_at_n"] and metric["stable_at_half_n"]
        )

    assert stats_integrity.p50_relative_change_exceeds_guard(Fraction(100), Fraction(106))
    assert not stats_integrity.p50_relative_change_exceeds_guard(Fraction(100), Fraction(105))
    assert stats_integrity.p50_relative_change_exceeds_guard(Fraction(0), Fraction(1))
    assert not stats_integrity.p50_relative_change_exceeds_guard(Fraction(0), Fraction(0))
    assert "P50_Cumulative_Project_Profit" in indicator_summary["indicators"]


def test_174_financial_fingerprint_is_identical_after_sharding_and_merge() -> None:
    full = [_trial(1, 100), _trial(2, 300), _trial(3, 500)]
    shard_a = full[:2]
    shard_b = full[2:]
    assert monte_carlo.fingerprint_trial_results(full) == monte_carlo.fingerprint_trial_results(
        shard_b + shard_a
    )
    assert monte_carlo.trial_fingerprint(full[1]) == monte_carlo.trial_fingerprint(
        replace(full[1], rng_checksum=123, rng_draw_count=7)
    )


def test_175_arabic_english_numeric_mappings_match_exactly() -> None:
    arabic = {"Final_Net_Project_Equity": 1234, "P50_Profit": Decimal("4.25")}
    english = {"Final_Net_Project_Equity": 1234, "P50_Profit": Decimal("4.25")}
    assert validate_bilingual_numeric_values(arabic, english) == 2


def test_176_number_registry_requires_every_reported_number_and_source() -> None:
    entries = [
        {
            "name": "mean_profit",
            "exact_numerator": 25,
            "exact_denominator": 2,
            "display_value": "12.50",
            "source": "scenario=C085_G100/N=300",
        }
    ]
    assert validate_number_registry_coverage(["mean_profit"], entries) == 1
    with pytest.raises(RuntimeError, match="NUMBER_REGISTRY_MISSING"):
        validate_number_registry_coverage(["mean_profit", "p50"], entries)


def test_179_manifest_hashes_and_provenance_are_verified() -> None:
    payload = b"synthetic unit-test bytes; not a production result"
    files = {"unit-fixture.bin": payload}
    manifest = {"files": [{
        "path": "unit-fixture.bin",
        "sha256": sha256(payload).hexdigest(),
        "size_bytes": len(payload),
        "tested_commit_sha": "d" * 40,
        "command": "python -m pytest -q tests/test_v23_acceptance.py::test_179_manifest_hashes_and_provenance_are_verified",
    }]}
    assert validate_delivery_manifest(files, manifest) == 1


def test_180_daily_mapping_round_trip_preserves_header_order_and_values() -> None:
    headers = (
        "date",
        "Cash",
        "Partner1_Reinvestment_Balance",
        "Partner2_Reinvestment_Balance",
    )
    row = {
        "date": "2027-01-02",
        "Cash": 12500,
        "Partner1_Reinvestment_Balance": 8750,
        "Partner2_Reinvestment_Balance": 3750,
    }
    encoded = json.dumps({key: row[key] for key in headers}, sort_keys=False)
    decoded = json.loads(encoded)
    assert tuple(decoded.keys()) == headers
    assert decoded == row
    assert all(type(decoded[key]) is int for key in headers[1:])


def test_181_daily_snapshot_emits_partner_balances_as_integer_evidence() -> None:
    project = daily_engine.create_initial_project()
    project.partner1_reinvestment_balance = 701
    project.partner2_reinvestment_balance = 300
    row = monte_carlo._daily_snapshot(project, date(2027, 1, 2), 1)
    assert row["Partner1_Reinvestment_Balance"] == 701
    assert row["Partner2_Reinvestment_Balance"] == 300
    assert type(row["Partner1_Reinvestment_Balance"]) is int
    assert type(row["Partner2_Reinvestment_Balance"]) is int


def test_182_financial_fraction_uses_exact_integer_or_round_half_even() -> None:
    assert stats_integrity.fraction_to_report_value(Fraction(10, 2)) == 5
    assert type(stats_integrity.fraction_to_report_value(Fraction(10, 2))) is int
    assert stats_integrity.fraction_to_report_value(Fraction(12345, 1000)) == Decimal("12.34")
    assert stats_integrity.fraction_to_report_value(Fraction(12355, 1000)) == Decimal("12.36")
    entry = stats_integrity.number_registry_entry(
        "test_value", Fraction(12345, 1000), source="synthetic exact integer observations"
    )
    assert entry["exact_numerator"] == 2469
    assert entry["exact_denominator"] == 200
    assert entry["display_value"] == "12.34"
    assert entry["rounding"] == "ROUND_HALF_EVEN"


def test_183_cohort_identity_rejects_mixed_source_or_cohort() -> None:
    valid = [
        {"source_sha": SOURCE_SHA, "cohort_id": "new-v23", "schema_version": "v2.3"},
        {"source_sha": SOURCE_SHA, "cohort_id": "new-v23", "schema_version": "v2.3"},
    ]
    assert validate_cohort_identity(valid) == (SOURCE_SHA, "new-v23", "v2.3")
    mixed = valid + [
        {"source_sha": "e" * 40, "cohort_id": "historical", "schema_version": "v2.2"}
    ]
    with pytest.raises(RuntimeError, match="COHORT_IDENTITY_MISMATCH"):
        validate_cohort_identity(mixed)


def test_184_checksum_zero_with_real_draw_is_valid_but_duplicate_is_not() -> None:
    assert validate_rng_audit_records(
        [_audit_record(1, 0, 2049)],
        source_sha=SOURCE_SHA,
        master_seed=constants.MASTER_SEED,
    ) == 1
    with pytest.raises(RuntimeError, match="DUPLICATE_RNG_CHECKSUM_DETECTED"):
        validate_rng_audit_records(
            [_audit_record(1, 0, 2049), _audit_record(2, 0, 1)],
            source_sha=SOURCE_SHA,
            master_seed=constants.MASTER_SEED,
        )


def test_185_cumulative_checkpoints_and_c100_start_at_300() -> None:
    from scripts.stage7_stability import next_statistical_checkpoint, is_statistical_checkpoint
    assert constants.C100_STATISTICAL_START_TRIALS == 300
    assert [next_statistical_checkpoint(n) for n in (0, 300, 600, 1200)] == [300, 600, 1200, 2400]
    assert all(is_statistical_checkpoint(n) for n in (300, 600, 1200, 2400))


def test_186_manifest_contract_accepts_seven_deliverables_plus_manifest() -> None:
    files = {f"deliverable-{i}.bin": f"fixture-{i}".encode("utf-8") for i in range(7)}
    manifest = {"files": [
        {
            "path": path,
            "sha256": sha256(payload).hexdigest(),
            "size_bytes": len(payload),
            "tested_commit_sha": "f" * 40,
            "command": "synthetic contract test",
        }
        for path, payload in files.items()
    ]}
    assert len(files) == 7
    assert validate_delivery_manifest(files, manifest) == 7
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w") as zf:
        for path, payload in files.items():
            zf.writestr(path, payload)
        zf.writestr("manifest.json", json.dumps(manifest, sort_keys=True))
    archive.seek(0)
    with zipfile.ZipFile(archive) as zf:
        assert len(zf.namelist()) == 8  # Seven deliverables plus manifest, all in-memory only.


def test_187_bike_ids_are_strictly_four_decimal_digits() -> None:
    assert [format_bike_id(i) for i in (1, 10, 11)] == ["BK0001", "BK0010", "BK0011"]
    assert is_canonical_bike_id("BK0001")
    assert not is_canonical_bike_id("BK1")
    assert not is_canonical_bike_id("BK011")
    assert not is_canonical_bike_id("BK00001")
    with pytest.raises(ValueError, match="BIKE_ID_SERIAL_WIDTH_EXCEEDED"):
        format_bike_id(10000)

    initial = daily_engine.create_initial_project()
    assert [bike.bike_id for bike in initial.bikes] == [
        format_bike_id(serial) for serial in range(1, 11)
    ]
    initial.project_cash = constants.EXPANSION_PURCHASE_CASH_THRESHOLD
    initial.partner1_reinvestment_balance = constants.EXPANSION_PURCHASE_CASH_THRESHOLD
    daily_engine._m2(initial, constants.EXPANSION_CUTOFF_DATE)
    expansion = [bike for bike in initial.bikes if bike.source == "EXPANSION"]
    assert [bike.bike_id for bike in expansion] == ["BK0011"]


def test_188_canonical_rng_key_vector_matches_sha256_u64_checksum_and_threshold() -> None:
    key = "20270101|C085|1|BK0001|2027-01-02|PRIMARY_COLLECTION"
    seed = rng.derive_seed(
        20270101, "C085_G070", 1, "BK0001", date(2027, 1, 2), "PRIMARY_COLLECTION"
    )
    assert key.encode("utf-8")
    assert seed.hex() == "fc2a64164208aa0f3b4d08bb75f80e950dddb803a26535ad3e344c1a5f9b8601"
    assert int.from_bytes(seed[:8], "big") == 18170445693339609615
    assert rng.rng_checksum_contribution(seed) == 8872287936200981
    assert rng.draw_success(seed, 85) is False


def test_189_financial_fingerprint_is_independent_from_rng_audit_fingerprint() -> None:
    base = _trial(10, 123456, checksum=111, draws=2)
    changed = replace(base, rng_checksum=222, rng_draw_count=3)
    assert monte_carlo.trial_fingerprint(base) == monte_carlo.trial_fingerprint(changed)
    audit_base = rng.rng_audit_fingerprint(
        source_sha=SOURCE_SHA, master_seed=constants.MASTER_SEED,
        scenario_id=base.scenario_id, trial_id=base.trial_id,
        rng_checksum=base.rng_checksum, rng_draw_count=base.rng_draw_count,
    )
    audit_changed = rng.rng_audit_fingerprint(
        source_sha=SOURCE_SHA, master_seed=constants.MASTER_SEED,
        scenario_id=changed.scenario_id, trial_id=changed.trial_id,
        rng_checksum=changed.rng_checksum, rng_draw_count=changed.rng_draw_count,
    )
    assert audit_base != audit_changed


def test_190_c100_repeated_ids_are_degenerate_not_independent() -> None:
    first = replace(_trial(1, 500), scenario_id="C100_G100", collection_probability=1.0)
    second = replace(first, trial_id=2)
    third = replace(first, trial_id=300)
    summary = c100_path_summary([first, second, third])
    assert summary == {
        "N": 3,
        "N_unique_paths": 1,
        "status": "DEGENERATE_DETERMINISTIC",
        "random_confidence_interval": False,
    }


def test_191_five_representative_roles_use_equity_extrema_and_trial_id_ties() -> None:
    trials = [_trial(9, 100), _trial(3, 300), _trial(2, 300), _trial(7, 500)]
    selected = monte_carlo.select_representative_trials(trials)
    assert selected.p50_trial_id == 2
    assert selected.p10_trial_id == 9
    assert selected.p90_trial_id == 7
    assert selected.loss_case_trial_id == 9
    assert selected.max_case_trial_id == 7


def test_192_approved_time_uniform_method_is_required_for_gate_b_acceptance(monkeypatch) -> None:
    for k in range(1, 9):
        assert stats_integrity.sequential_alpha_fraction(k) == Fraction(1, 400 * k * (k + 1))
    assert stats_integrity.cumulative_alpha_fraction(4) == Fraction(1, 500)
    assert type(stats_integrity.cumulative_alpha_fraction(4)) is Fraction
    method = stats_integrity.time_uniform_inference_status()
    assert method["approved"] is True
    assert method["method_id"] == constants.TIME_UNIFORM_METHOD_ID

    import run_batch
    mean_metrics = {name: {"stable": True} for name in run_batch.STABILITY_FIELDS}
    indicator_names = {
        "P10_Cumulative_Project_Profit", "P50_Cumulative_Project_Profit",
        "P90_Cumulative_Project_Profit", "P90_Final_Cash",
        "Probability_of_Accounting_Loss", "P90_Termination_Count", "P90_Held_Assets",
    }
    indicators = {"indicators": {name: {"stable": True} for name in indicator_names}}
    assert run_batch.evaluate_gate_b(mean_metrics, indicator_metrics=indicators)["stable"] is True

    # The same gate must fail closed if the approval is absent.
    monkeypatch.setattr(constants, "TIME_UNIFORM_METHOD_APPROVED", False)
    blocked = run_batch.evaluate_gate_b(mean_metrics, indicator_metrics=indicators)
    assert blocked["stable"] is False
    assert blocked["status"] == "K_SPEC / BLOCKED"


def test_193_historical_and_new_rng_cohorts_cannot_be_mixed() -> None:
    new_records = [
        {"source_sha": SOURCE_SHA, "cohort_id": "u3-new", "schema_version": "v2.3"},
        {"source_sha": SOURCE_SHA, "cohort_id": "u3-new", "schema_version": "v2.3"},
    ]
    historical = {"source_sha": "9" * 40, "cohort_id": "historical-v2.2", "schema_version": "v2.2"}
    assert validate_cohort_identity(new_records) == (SOURCE_SHA, "u3-new", "v2.3")
    with pytest.raises(RuntimeError, match="COHORT_IDENTITY_MISMATCH"):
        validate_cohort_identity(new_records + [historical])


def test_acceptance_registry_has_the_normative_193_rows_and_exact_class_counts() -> None:
    registry = build_acceptance_registry()
    assert len(registry) == 193
    assert sum(row["type"] == "UNIQUE" for row in registry) == 177
    assert sum(row["type"] == "ALIAS" for row in registry) == 15
    assert sum(row["type"] == "DOC" for row in registry) == 1
    assert registry[157]["id"] == 158 and registry[157]["type"] == "DOC"
    assert registry[192]["id"] == 193 and registry[192]["type"] == "UNIQUE"
    # These three existing numbered tests are in-memory logic checks, not absent
    # production Parquet checks; production artifacts have their own deferred rows.
    for test_id in (159, 160, 161):
        assert registry[test_id - 1]["logic_status"] == "NOT_RUN"
        assert registry[test_id - 1]["production_status"] == "NOT_REQUIRED"
