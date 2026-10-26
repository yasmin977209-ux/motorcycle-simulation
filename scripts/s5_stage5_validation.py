from __future__ import annotations

import hashlib
import json
import os
import re
import time
from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_EVEN
from fractions import Fraction
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

import constants
import monte_carlo
import stats_integrity


OUTPUT = Path("results_stage5")
METRIC_NAMES = (
    "Cash",
    "Net_Equity",
    "Active_Bikes",
    "Owned_Transferred_Bikes",
    "Pending_Claims",
)
ROLE_NAMES = {
    "p50_trial_id": "P50",
    "p10_trial_id": "P10",
    "p90_trial_id": "P90",
    "loss_case_trial_id": "LossCase",
    "max_case_trial_id": "MaxCase",
}


def _assert_no_float(value: Any, *, path: str = "root") -> None:
    if isinstance(value, float):
        raise AssertionError(f"FLOAT_LEAK_DETECTED:{path}")
    if isinstance(value, dict):
        for key, item in value.items():
            _assert_no_float(item, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _assert_no_float(item, path=f"{path}[{index}]")


def _canonical_json(value: Any) -> str:
    return json.dumps(
        monte_carlo._canonical_jsonable(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _write_json(path: Path, payload: Any) -> None:
    _assert_no_float(payload, path=str(path))
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _display_fraction(value: Fraction) -> str:
    display = stats_integrity.fraction_to_report_value(value)
    return str(display)


def _seconds_display(elapsed_ns: int) -> str:
    with_decimal = Decimal(elapsed_ns) / Decimal(constants.NANOSECONDS_PER_SECOND)
    places = Decimal(1).scaleb(-constants.TIMING_REPORT_DECIMAL_PLACES)
    return str(with_decimal.quantize(places, rounding=ROUND_HALF_EVEN))


def _assert_integer_daily_slices(slices: dict[int, list[dict[str, object]]]) -> None:
    for trial_id, rows in slices.items():
        if not rows:
            raise AssertionError(f"DAILY_SLICES_EMPTY:trial_id={trial_id}")
        for row_index, row in enumerate(rows):
            for field in (
                "Cash",
                "Partner1_Reinvestment_Balance",
                "Partner2_Reinvestment_Balance",
                "Capital",
                "Retained_Earnings",
                "Net_Equity",
                "Active_Bikes",
                "Owned_Transferred_Bikes",
                "Pending_Claims",
            ):
                if type(row[field]) is not int:
                    raise AssertionError(
                        f"DAILY_FINANCIAL_FIELD_NOT_INT:trial_id={trial_id}:"
                        f"row={row_index}:field={field}"
                    )
            _assert_no_float(row, path=f"daily[{trial_id}][{row_index}]")


def _scenario_ids() -> list[str]:
    return [
        f"C{collection_pct:03d}_G{recovery_pct:03d}"
        for collection_pct in constants.STAGE5_STOCHASTIC_COLLECTION_PERCENTAGES
        for recovery_pct in constants.GUARANTEE_RECOVERY_RATES
    ]


def _summary_metrics(
    scenario_id: str,
    results: list[monte_carlo.TrialResult],
    register_number: Any,
) -> dict[str, Any]:
    metrics: dict[str, Any] = {}
    definitions = (
        ("Final_Net_Project_Equity", "final_net_project_equity", True),
        ("Final_Cash", "final_cash", True),
        ("Cumulative_Project_Profit", "cumulative_project_profit", True),
        ("Termination_Count", "termination_count", False),
        ("Held_Assets", "held_assets", False),
    )
    for display_name, field_name, include_mean in definitions:
        values = [getattr(result, field_name) for result in results]
        if include_mean:
            exact = stats_integrity.mean_fraction(values)
            registry_name = f"scenario/{scenario_id}/Mean/{display_name}"
            register_number(registry_name, exact, "results_stage5/trials_summary.parquet")
            metrics[f"Mean_{display_name}"] = {
                "exact_numerator": exact.numerator,
                "exact_denominator": exact.denominator,
                "display_value": _display_fraction(exact),
            }
        for quantile_name, quantile_pct in constants.DAILY_DISTRIBUTION_PERCENTILES:
            quantile = Fraction(quantile_pct, constants.REPORT_PERCENT_DENOMINATOR)
            exact = stats_integrity.linear_quantile_fraction(values, quantile)
            registry_name = f"scenario/{scenario_id}/{quantile_name}/{display_name}"
            register_number(registry_name, exact, "results_stage5/trials_summary.parquet")
            metrics[f"{quantile_name}_{display_name}"] = {
                "exact_numerator": exact.numerator,
                "exact_denominator": exact.denominator,
                "display_value": _display_fraction(exact),
            }
    return metrics


def _distribution_schema() -> pa.Schema:
    fields = [
        pa.field("scenario_id", pa.string()),
        pa.field("date", pa.string()),
        pa.field("quantile_name", pa.string()),
        pa.field("population", pa.string()),
        pa.field("population_mode", pa.string()),
        pa.field("total_trials", pa.int64()),
        pa.field("population_count", pa.int64()),
        pa.field("active_trial_count", pa.int64()),
        pa.field("closed_trial_count", pa.int64()),
    ]
    for metric in METRIC_NAMES:
        fields.extend(
            [
                pa.field(metric, pa.string()),
                pa.field(f"{metric}_exact_numerator", pa.int64()),
                pa.field(f"{metric}_exact_denominator", pa.int64()),
            ]
        )
    return pa.schema(fields)


def _assert_no_float_schema(schema: pa.Schema, *, artifact: str) -> None:
    for field in schema:
        if pa.types.is_floating(field.type):
            raise AssertionError(
                f"PARQUET_FLOAT_COLUMN_FORBIDDEN:{artifact}:{field.name}:{field.type}"
            )



def _table_from_summary_records(records: list[dict[str, Any]]) -> pa.Table:
    """Build the summary with rng_checksum as UInt64, preserving all 64 bits.

    Arrow otherwise infers a signed int64 from Python integers and rejects valid
    checksums in the upper half of the unsigned 64-bit range.
    """
    if not records:
        raise ValueError("TRIALS_SUMMARY_RECORDS_EMPTY")
    field_names = list(records[0])
    expected_fields = set(field_names)
    if any(set(record) != expected_fields for record in records):
        raise ValueError("TRIALS_SUMMARY_SCHEMA_DRIFT")
    fields = []
    for name in field_names:
        values = [record[name] for record in records]
        if name == "rng_checksum":
            if any(type(value) is not int or not 0 <= value < constants.RNG_CHECKSUM_MODULUS for value in values):
                raise ValueError("RNG_CHECKSUM_OUT_OF_UINT64_RANGE")
            fields.append(pa.field(name, pa.uint64(), nullable=False))
        else:
            fields.append(pa.field(name, pa.array(values).type))
    return pa.Table.from_pylist(records, schema=pa.schema(fields))

def _resolve_source_identities() -> tuple[str, str]:
    """Keep the pinned engine SOURCE_SHA distinct from the tested Git commit."""
    source_sha = os.environ.get("S5_MODEL_SOURCE_SHA", "")
    tested_commit_sha = os.environ.get("GITHUB_SHA", "")
    if re.fullmatch(r"[0-9a-f]{40}", source_sha) is None:
        raise RuntimeError("S5_MODEL_SOURCE_SHA_MISSING_OR_INVALID")
    if re.fullmatch(r"[0-9a-f]{40}", tested_commit_sha) is None:
        raise RuntimeError("S5_TESTED_COMMIT_SHA_MISSING_OR_INVALID")
    return source_sha, tested_commit_sha


def main() -> int:
    source_sha, tested_commit_sha = _resolve_source_identities()
    run_id = os.environ.get("GITHUB_RUN_ID", "LOCAL_NOT_GITHUB")
    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise RuntimeError("S5_OUTPUT_DIRECTORY_NOT_EMPTY; refusing to overwrite existing evidence")
    OUTPUT.mkdir(parents=True, exist_ok=True)

    started_ns = time.perf_counter_ns()
    trial_ids = list(constants.STAGE5_SMOKE_TRIAL_IDS)
    scenarios = _scenario_ids()
    if len(scenarios) != constants.NON_C100_STATISTICAL_START_TRIALS // constants.NON_C100_STATISTICAL_START_TRIALS * len(scenarios):
        raise AssertionError("UNEXPECTED_SCENARIO_CARDINALITY")
    if len(scenarios) != len(constants.STAGE5_STOCHASTIC_COLLECTION_PERCENTAGES) * len(constants.GUARANTEE_RECOVERY_RATES):
        raise AssertionError("UNEXPECTED_STOCHASTIC_SCENARIO_COUNT")
    if any(scenario.startswith("C100_") for scenario in scenarios):
        raise AssertionError("S5_MUST_NOT_RERUN_C100")

    first_results_by_scenario: dict[str, dict[int, monte_carlo.TrialResult]] = {}
    first_daily_by_scenario: dict[str, dict[int, list[dict[str, object]]]] = {}
    worker_manifest: list[dict[str, Any]] = []
    timing: dict[str, Any] = {
        "run_id": run_id,
        "source_sha": source_sha,
        "tested_commit_sha": tested_commit_sha,
        "scope": "S5_MINI_VALIDATION_ONLY",
        "n_scenarios": len(scenarios),
        "trial_ids_per_scenario": trial_ids,
        "worker_counts": list(constants.STAGE5_PARALLEL_WORKER_COUNTS),
        "elapsed_ns_by_scenario": {},
    }
    sequential_elapsed_ns = 0
    parallel_elapsed_ns = {worker_count: 0 for worker_count in constants.STAGE5_PARALLEL_WORKER_COUNTS}
    sequential_trials_count = 0

    for scenario_id in scenarios:
        print(f"S5_SCENARIO_START {scenario_id}", flush=True)
        elapsed_start = time.perf_counter_ns()
        seq_results, seq_daily = monte_carlo.run_trials_sequentially(
            scenario_id,
            trial_ids,
            master_seed=constants.MASTER_SEED,
            source_sha=source_sha,
        )
        seq_elapsed = time.perf_counter_ns() - elapsed_start
        sequential_elapsed_ns += seq_elapsed
        sequential_trials_count += len(seq_results)
        seq_by_id = {result.trial_id: result for result in seq_results}
        _assert_integer_daily_slices(seq_daily)
        first_results_by_scenario[scenario_id] = seq_by_id
        first_daily_by_scenario[scenario_id] = seq_daily

        timing["elapsed_ns_by_scenario"][scenario_id] = {
            "sequential_total_ns": seq_elapsed,
            "sequential_mean_ns_per_trial": seq_elapsed // len(seq_results),
            "sequential_total_seconds_display": _seconds_display(seq_elapsed),
        }

        by_worker: dict[int, tuple[dict[int, monte_carlo.TrialResult], dict[int, list[dict[str, object]]], int]] = {}
        for worker_count in constants.STAGE5_PARALLEL_WORKER_COUNTS:
            elapsed_start = time.perf_counter_ns()
            parallel_results, parallel_daily = monte_carlo.run_trials_parallel(
                scenario_id,
                trial_ids,
                worker_count,
                master_seed=constants.MASTER_SEED,
                source_sha=source_sha,
            )
            elapsed = time.perf_counter_ns() - elapsed_start
            parallel_elapsed_ns[worker_count] += elapsed
            parallel_by_id = {result.trial_id: result for result in parallel_results}
            _assert_integer_daily_slices(parallel_daily)
            by_worker[worker_count] = (parallel_by_id, parallel_daily, elapsed)
            timing["elapsed_ns_by_scenario"][scenario_id][f"workers_{worker_count}_total_ns"] = elapsed
            timing["elapsed_ns_by_scenario"][scenario_id][f"workers_{worker_count}_mean_ns_per_trial"] = elapsed // len(parallel_results)

        for trial_id in trial_ids:
            seq_result = seq_by_id[trial_id]
            seq_slice = seq_daily[trial_id]
            seq_record_hash = _sha256_text(_canonical_json(asdict(seq_result)))
            seq_daily_hash = _sha256_text(_canonical_json(seq_slice))
            row: dict[str, Any] = {
                "scenario_id": scenario_id,
                "trial_id": trial_id,
                "source_sha": source_sha,
                "tested_commit_sha": tested_commit_sha,
                "trial_fingerprint_sequential": seq_result.trial_fingerprint,
                "trial_record_sha256_sequential": seq_record_hash,
                "daily_slice_sha256_sequential": seq_daily_hash,
            }
            for worker_count in constants.STAGE5_PARALLEL_WORKER_COUNTS:
                parallel_by_id, parallel_daily, _ = by_worker[worker_count]
                parallel_result = parallel_by_id[trial_id]
                parallel_slice = parallel_daily[trial_id]
                exact_record = _canonical_json(asdict(seq_result)) == _canonical_json(asdict(parallel_result))
                exact_daily = _canonical_json(seq_slice) == _canonical_json(parallel_slice)
                fingerprint_match = seq_result.trial_fingerprint == parallel_result.trial_fingerprint
                daily_fingerprint_match = (
                    monte_carlo.fingerprint_per_trial_slices({trial_id: seq_slice})
                    == monte_carlo.fingerprint_per_trial_slices({trial_id: parallel_slice})
                )
                exact_all = exact_record and exact_daily and fingerprint_match and daily_fingerprint_match
                if not exact_all:
                    raise AssertionError(
                        f"WORKER_EQUIVALENCE_FAILED:{scenario_id}:trial_id={trial_id}:workers={worker_count}"
                    )
                row[f"trial_fingerprint_workers_{worker_count}"] = parallel_result.trial_fingerprint
                row[f"trial_record_sha256_workers_{worker_count}"] = _sha256_text(_canonical_json(asdict(parallel_result)))
                row[f"daily_slice_sha256_workers_{worker_count}"] = _sha256_text(_canonical_json(parallel_slice))
                row[f"exact_1_eq_{worker_count}"] = exact_all
            worker_manifest.append(row)
        timing["elapsed_ns_by_scenario"][scenario_id]["worker_equivalence"] = "PASS_EXACT_RECORD_AND_DAILY_SLICE"

        seen_checksums: dict[int, int] = {}
        for trial_id, result in seq_by_id.items():
            if result.rng_draw_count == 0:
                if result.rng_checksum != 0:
                    raise AssertionError(f"RNG_CHECKSUM_NONZERO_WITH_ZERO_DRAWS:{scenario_id}:{trial_id}")
            else:
                if not 0 <= result.rng_checksum < constants.RNG_CHECKSUM_MODULUS:
                    raise AssertionError(f"RNG_CHECKSUM_OUT_OF_RANGE:{scenario_id}:{trial_id}")
                if result.rng_checksum in seen_checksums:
                    raise AssertionError(
                        f"DUPLICATE_RNG_CHECKSUM_DETECTED:{scenario_id}:"
                        f"trial_ids={seen_checksums[result.rng_checksum]},{trial_id}"
                    )
                seen_checksums[result.rng_checksum] = trial_id
        print(f"S5_SCENARIO_EQUIVALENCE_PASS {scenario_id}", flush=True)

    summary_records: list[dict[str, Any]] = []
    for scenario_id in scenarios:
        for trial_id in trial_ids:
            result = first_results_by_scenario[scenario_id][trial_id]
            record = asdict(result)
            record.pop("collection_probability", None)
            record["collection_pct"] = int(scenario_id.split("_", maxsplit=1)[0][1:])
            record["source_sha"] = source_sha
            record["tested_commit_sha"] = tested_commit_sha
            _assert_no_float(record, path=f"trials_summary.{scenario_id}.{trial_id}")
            summary_records.append(record)
    summary_records.sort(key=lambda row: (row["scenario_id"], row["trial_id"]))
    trials_summary_path = OUTPUT / "trials_summary.parquet"
    summary_table = _table_from_summary_records(summary_records)
    _assert_no_float_schema(summary_table.schema, artifact=trials_summary_path.name)
    pq.write_table(summary_table, trials_summary_path, compression="zstd")

    registry_path = OUTPUT / "number_registry.json"
    registry_handle = registry_path.open("w", encoding="utf-8", newline="\n")
    registry_handle.write("[\n")
    registry_first = True

    def register_number(name: str, value: Fraction, source: str) -> dict[str, Any]:
        nonlocal registry_first
        entry = stats_integrity.number_registry_entry(name, value, source=source)
        if not registry_first:
            registry_handle.write(",\n")
        registry_handle.write(json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        registry_first = False
        return entry

    selection_records: list[dict[str, Any]] = []
    representative_daily_records: list[dict[str, Any]] = []
    replay_manifest: list[dict[str, Any]] = []
    stability_scenarios: list[dict[str, Any]] = []
    replay_elapsed_ns = 0
    replay_executions = 0

    for scenario_id in scenarios:
        results_by_id = first_results_by_scenario[scenario_id]
        results = [results_by_id[trial_id] for trial_id in trial_ids]
        exact_statistics = _summary_metrics(scenario_id, results, register_number)
        selection = monte_carlo.select_representative_trials(results)
        selected_roles: dict[int, list[str]] = {}
        for selection_key, trial_id in selection.items():
            selected_roles.setdefault(trial_id, []).append(ROLE_NAMES[selection_key])
            result = results_by_id[trial_id]
            selection_records.append({
                "scenario_id": scenario_id,
                "selection_role": ROLE_NAMES[selection_key],
                "trial_id": trial_id,
                "final_net_project_equity": result.final_net_project_equity,
                "trial_fingerprint": result.trial_fingerprint,
                "source_sha": source_sha,
                "tested_commit_sha": tested_commit_sha,
            })

        replay_by_id: dict[int, tuple[monte_carlo.TrialResult, list[dict[str, object]]]] = {}
        for trial_id in sorted(selected_roles):
            replay_start = time.perf_counter_ns()
            replay_result, replay_daily = monte_carlo.run_single_trial(
                scenario_id,
                trial_id,
                master_seed=constants.MASTER_SEED,
                source_sha=source_sha,
            )
            replay_elapsed_ns += time.perf_counter_ns() - replay_start
            replay_executions += 1
            original_result = results_by_id[trial_id]
            original_daily = first_daily_by_scenario[scenario_id][trial_id]
            result_match = _canonical_json(asdict(original_result)) == _canonical_json(asdict(replay_result))
            daily_match = _canonical_json(original_daily) == _canonical_json(replay_daily)
            fingerprint_match = original_result.trial_fingerprint == replay_result.trial_fingerprint
            if not (result_match and daily_match and fingerprint_match):
                raise AssertionError(f"SECOND_PASS_FINGERPRINT_MISMATCH:{scenario_id}:{trial_id}")
            _assert_integer_daily_slices({trial_id: replay_daily})
            replay_by_id[trial_id] = (replay_result, replay_daily)

        for trial_id, roles in selected_roles.items():
            original = results_by_id[trial_id]
            replay_result, replay_daily = replay_by_id[trial_id]
            replay_manifest.append({
                "scenario_id": scenario_id,
                "trial_id": trial_id,
                "selection_roles": sorted(roles),
                "source_sha": source_sha,
                "tested_commit_sha": tested_commit_sha,
                "first_pass_trial_fingerprint": original.trial_fingerprint,
                "second_pass_trial_fingerprint": replay_result.trial_fingerprint,
                "trial_fingerprint_match": original.trial_fingerprint == replay_result.trial_fingerprint,
                "full_trial_record_match": _canonical_json(asdict(original)) == _canonical_json(asdict(replay_result)),
                "daily_slice_match": _canonical_json(first_daily_by_scenario[scenario_id][trial_id]) == _canonical_json(replay_daily),
                "daily_row_count": len(replay_daily),
                "partner_reinvestment_balances_integer": all(
                    type(row["Partner1_Reinvestment_Balance"]) is int
                    and type(row["Partner2_Reinvestment_Balance"]) is int
                    for row in replay_daily
                ),
            })
            for role in sorted(roles):
                for daily_row in replay_daily:
                    representative_daily_records.append({
                        "scenario_id": scenario_id,
                        "selection_role": role,
                        "source_sha": source_sha,
                        "tested_commit_sha": tested_commit_sha,
                        **daily_row,
                    })

        stability_scenarios.append({
            "scenario_id": scenario_id,
            "n": len(results),
            "n_unique_financial_trial_fingerprints": len({result.trial_fingerprint for result in results}),
            "status": "SMOKE_ONLY_NOT_A_STATISTICAL_CHECKPOINT",
            "formal_stability_declared": False,
            "selection": {ROLE_NAMES[key]: value for key, value in selection.items()},
            "descriptive_statistics": exact_statistics,
        })

    selection_path = OUTPUT / "selection.parquet"
    selection_table = pa.Table.from_pylist(selection_records)
    _assert_no_float_schema(selection_table.schema, artifact=selection_path.name)
    pq.write_table(selection_table, selection_path, compression="zstd")

    representative_daily_path = OUTPUT / "representative_daily.parquet"
    representative_table = pa.Table.from_pylist(representative_daily_records)
    _assert_no_float_schema(representative_table.schema, artifact=representative_daily_path.name)
    pq.write_table(representative_table, representative_daily_path, compression="zstd")

    distribution_path = OUTPUT / "daily_distribution.parquet"
    distribution_schema = _distribution_schema()
    distribution_writer = pq.ParquetWriter(distribution_path, distribution_schema, compression="zstd")
    distribution_dates: dict[tuple[str, str], set[str]] = {}
    distribution_rows_count = 0
    for scenario_id in scenarios:
        results = [first_results_by_scenario[scenario_id][trial_id] for trial_id in trial_ids]
        slices = first_daily_by_scenario[scenario_id]
        for population_mode in constants.DAILY_DISTRIBUTION_POPULATION_MODES:
            rows = monte_carlo.build_daily_distribution(
                results,
                slices,
                population_mode=population_mode,
            )
            _assert_no_float(rows, path=f"daily_distribution.{scenario_id}.{population_mode}")
            table = pa.Table.from_pylist(rows, schema=distribution_schema)
            _assert_no_float_schema(table.schema, artifact=distribution_path.name)
            distribution_writer.write_table(table)
            distribution_rows_count += len(rows)
            distribution_dates[(scenario_id, population_mode)] = {str(row["date"]) for row in rows}
            for row in rows:
                for metric in METRIC_NAMES:
                    exact = Fraction(
                        row[f"{metric}_exact_numerator"],
                        row[f"{metric}_exact_denominator"],
                    )
                    register_number(
                        f"daily_distribution/{scenario_id}/{population_mode}/{row['date']}/{row['quantile_name']}/{metric}",
                        exact,
                        distribution_path.name,
                    )
    distribution_writer.close()

    for scenario_id in scenarios:
        for population_mode in constants.DAILY_DISTRIBUTION_POPULATION_MODES:
            dates = sorted(distribution_dates[(scenario_id, population_mode)])
            if not dates:
                raise AssertionError(f"DAILY_DISTRIBUTION_EMPTY:{scenario_id}:{population_mode}")
            if len(dates) != (datetime.fromisoformat(dates[-1]).date() - datetime.fromisoformat(dates[0]).date()).days + 1:
                raise AssertionError(f"DAILY_DISTRIBUTION_DATE_GAP:{scenario_id}:{population_mode}")

    registry_handle.write("\n]\n")
    registry_handle.close()

    worker_manifest_payload = {
        "schema_version": "s5-worker-equivalence-v1",
        "source_sha": source_sha,
        "tested_commit_sha": tested_commit_sha,
        "run_id": run_id,
        "cohort_id": f"s5-v23-smoke-{source_sha[:12]}",
        "scenarios": scenarios,
        "trial_ids": trial_ids,
        "worker_counts": list(constants.STAGE5_PARALLEL_WORKER_COUNTS),
        "rows": worker_manifest,
        "row_count": len(worker_manifest),
        "exact_all": all(
            row[f"exact_1_eq_{worker_count}"]
            for row in worker_manifest
            for worker_count in constants.STAGE5_PARALLEL_WORKER_COUNTS
        ),
    }
    _write_json(OUTPUT / "worker_equivalence_manifest.json", worker_manifest_payload)
    _write_json(OUTPUT / "representative_replay_manifest.json", {
        "schema_version": "s5-representative-replay-v1",
        "source_sha": source_sha,
        "tested_commit_sha": tested_commit_sha,
        "run_id": run_id,
        "scenario_count": len(scenarios),
        "role_count": len(selection_records),
        "unique_replay_count": replay_executions,
        "all_trial_fingerprints_match": all(row["trial_fingerprint_match"] for row in replay_manifest),
        "all_full_trial_records_match": all(row["full_trial_record_match"] for row in replay_manifest),
        "all_daily_slices_match": all(row["daily_slice_match"] for row in replay_manifest),
        "all_partner_balances_are_integer": all(row["partner_reinvestment_balances_integer"] for row in replay_manifest),
        "rows": replay_manifest,
    })

    stability_history = {
        "schema_version": "s5-stability-smoke-v1",
        "source_sha": source_sha,
        "tested_commit_sha": tested_commit_sha,
        "run_id": run_id,
        "cohort_id": f"s5-v23-smoke-{source_sha[:12]}",
        "sample_kind": "FUNCTIONAL_SMOKE_ONLY",
        "n_per_scenario": len(trial_ids),
        "required_first_stochastic_checkpoint_n": constants.NON_C100_STATISTICAL_START_TRIALS,
        "time_uniform_method_id": constants.TIME_UNIFORM_METHOD_ID,
        "production_convergence_declared": False,
        "status": "SMOKE_ONLY_NOT_A_STATISTICAL_CHECKPOINT",
        "scenarios": stability_scenarios,
    }
    _write_json(OUTPUT / "stability_history.json", stability_history)

    representative_trial_count = replay_executions
    total_elapsed_ns = time.perf_counter_ns() - started_ns
    benchmark = {
        **timing,
        "sequential_trial_executions": sequential_trials_count,
        "sequential_elapsed_ns": sequential_elapsed_ns,
        "sequential_elapsed_seconds_display": _seconds_display(sequential_elapsed_ns),
        "sequential_mean_ns_per_trial": sequential_elapsed_ns // sequential_trials_count,
        "parallel_elapsed_ns_by_worker_count": {
            str(worker_count): elapsed
            for worker_count, elapsed in parallel_elapsed_ns.items()
        },
        "parallel_mean_ns_per_trial_by_worker_count": {
            str(worker_count): elapsed // sequential_trials_count
            for worker_count, elapsed in parallel_elapsed_ns.items()
        },
        "representative_role_count": len(selection_records),
        "unique_representative_replay_executions": representative_trial_count,
        "representative_replay_elapsed_ns": replay_elapsed_ns,
        "representative_replay_elapsed_seconds_display": _seconds_display(replay_elapsed_ns),
        "representative_replay_mean_ns_per_trial": (
            replay_elapsed_ns // representative_trial_count
            if representative_trial_count
            else None
        ),
        "total_elapsed_ns": total_elapsed_ns,
        "total_elapsed_seconds_display": _seconds_display(total_elapsed_ns),
        "measurement_clock": "time.perf_counter_ns",
    }
    _write_json(OUTPUT / "benchmark.json", benchmark)

    evidence = {
        "status": "PASS_MINI_INTEGRITY_ONLY",
        "scope": "S5 smoke evidence; not N=300 Gate A/B or convergence acceptance",
        "run_id": run_id,
        "source_sha": source_sha,
        "tested_commit_sha": tested_commit_sha,
        "branch": os.environ.get("GITHUB_REF_NAME", "LOCAL"),
        "cohort_id": f"s5-v23-smoke-{source_sha[:12]}",
        "stochastic_scenario_count": len(scenarios),
        "trial_ids_per_scenario": trial_ids,
        "worker_equivalence_manifest_rows": len(worker_manifest),
        "worker_equivalence_all_exact": worker_manifest_payload["exact_all"],
        "representative_role_rows": len(selection_records),
        "unique_representative_replay_executions": representative_trial_count,
        "representative_trial_fingerprint_match": all(row["trial_fingerprint_match"] for row in replay_manifest),
        "representative_daily_memo_balances_integer": all(row["partner_reinvestment_balances_integer"] for row in replay_manifest),
        "daily_distribution_rows": distribution_rows_count,
        "daily_distribution_populations": list(constants.DAILY_DISTRIBUTION_POPULATION_MODES),
        "parquet_float_columns": False,
        "json_float_leakage": False,
        "c100_rerun": False,
        "formal_stability_declared": False,
        "final_delivery_accepted": False,
        "timing_measured_in_run": True,
    }
    _write_json(OUTPUT / "S5_evidence.json", evidence)

    for json_name in (
        "worker_equivalence_manifest.json",
        "representative_replay_manifest.json",
        "stability_history.json",
        "benchmark.json",
        "S5_evidence.json",
    ):
        payload = json.loads((OUTPUT / json_name).read_text(encoding="utf-8"))
        _assert_no_float(payload, path=json_name)

    for parquet_name in (
        "trials_summary.parquet",
        "selection.parquet",
        "representative_daily.parquet",
        "daily_distribution.parquet",
    ):
        table = pq.read_table(OUTPUT / parquet_name)
        _assert_no_float_schema(table.schema, artifact=parquet_name)

    sums_path = OUTPUT / "SHA256SUMS.txt"
    entries = []
    for path in sorted(OUTPUT.iterdir()):
        if path.is_file() and path != sums_path:
            entries.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")
    sums_path.write_text("\n".join(entries) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": evidence["status"],
        "run_id": run_id,
        "source_sha": source_sha,
        "tested_commit_sha": tested_commit_sha,
        "scenarios": len(scenarios),
        "trials_per_scenario": len(trial_ids),
        "worker_manifest_rows": len(worker_manifest),
        "representative_role_rows": len(selection_records),
        "representative_replay_executions": representative_trial_count,
        "daily_distribution_rows": distribution_rows_count,
        "sequential_mean_ns_per_trial": benchmark["sequential_mean_ns_per_trial"],
        "sequential_mean_seconds_per_trial_display": _seconds_display(benchmark["sequential_mean_ns_per_trial"]),
        "parallel_mean_ns_per_trial_by_worker_count": benchmark["parallel_mean_ns_per_trial_by_worker_count"],
        "total_elapsed_ns": total_elapsed_ns,
        "total_elapsed_seconds_display": _seconds_display(total_elapsed_ns),
        "artifact_sha256_manifest": str(sums_path),
        "c100_rerun": False,
        "formal_stability_declared": False,
    }, ensure_ascii=False, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
