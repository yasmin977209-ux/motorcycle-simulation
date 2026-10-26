from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from datetime import datetime, timezone
from multiprocessing import get_context
from pathlib import Path
from typing import Any, Iterable

import constants
import daily_engine
import monte_carlo
import rng
from entities import format_bike_id, is_canonical_bike_id


SCHEMA_VERSION = "s6-stochastic-gate-a-golden-v1"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def _canonical_json(value: Any) -> str:
    return json.dumps(
        monte_carlo._canonical_jsonable(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _assert_no_float(value: Any, *, path: str = "root") -> None:
    if isinstance(value, float):
        raise AssertionError(f"FLOAT_LEAK_DETECTED:{path}")
    if isinstance(value, dict):
        for key, item in value.items():
            _assert_no_float(item, path=f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _assert_no_float(item, path=f"{path}[{index}]")


def _write_json(path: Path, payload: Any) -> None:
    _assert_no_float(payload, path=str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _resolve_identities() -> tuple[str, str, str]:
    source_sha = os.environ.get("S6_MODEL_SOURCE_SHA", "")
    tested_commit_sha = os.environ.get("GITHUB_SHA", "")
    run_id = os.environ.get("GITHUB_RUN_ID", "LOCAL_NOT_GITHUB")
    if COMMIT_SHA_RE.fullmatch(source_sha) is None:
        raise RuntimeError("S6_MODEL_SOURCE_SHA_MISSING_OR_INVALID")
    if COMMIT_SHA_RE.fullmatch(tested_commit_sha) is None:
        raise RuntimeError("S6_TESTED_COMMIT_SHA_MISSING_OR_INVALID")
    return source_sha, tested_commit_sha, run_id


def _validate_checkpoint(n: int) -> None:
    if type(n) is not int or n < constants.STATISTICAL_CHECK_START_N:
        raise ValueError("S6_N_MUST_BE_AN_APPROVED_STATISTICAL_CHECKPOINT")
    expected = constants.STATISTICAL_CHECK_START_N
    while expected < n:
        expected *= constants.STATISTICAL_ESCALATION_MULTIPLIER
    if expected != n:
        raise ValueError("S6_N_MUST_FOLLOW_THE_APPROVED_DOUBLING_SCHEDULE")


def _scenario_ids() -> tuple[str, ...]:
    scenarios = tuple(
        f"C{collection:03d}_G{recovery:03d}"
        for collection in constants.STAGE5_STOCHASTIC_COLLECTION_PERCENTAGES
        for recovery in constants.GUARANTEE_RECOVERY_RATES
    )
    if len(scenarios) != constants.STAGE5_STOCHASTIC_SCENARIO_COUNT:
        raise AssertionError("S6_STOCHASTIC_SCENARIO_COUNT_MISMATCH")
    if any(scenario.startswith("C100_") for scenario in scenarios):
        raise AssertionError("S6_MUST_REUSE_C100_NOT_RUN_IT")
    return scenarios


def _check_day(
    project: Any,
    current_date: Any,
    trial_id: int,
    daily_hasher: Any,
    counters: dict[str, int],
) -> None:
    day = current_date.isoformat()
    day_index = counters["daily_row_count"] + 1
    if len(project.daily_balance_checks) != day_index:
        raise RuntimeError(f"S6_DAILY_BALANCE_ROW_COUNT_MISMATCH:{trial_id}:{day}")
    series = (
        project.cash_rollforward,
        project.ar_rollforward,
        project.asset_rollforward,
        project.equity_rollforward,
    )
    if any(len(rows) != day_index for rows in series):
        raise RuntimeError(f"S6_ROLLFORWARD_ROW_COUNT_MISMATCH:{trial_id}:{day}")

    balance = project.daily_balance_checks[-1]
    if (
        balance["Total_Assets"] != balance["Total_Equity"]
        or balance["Balance_Difference"] != 0
    ):
        raise RuntimeError(f"S6_ASSETS_EQUITY_MISMATCH:{trial_id}:{day}")

    cash = project.cash_rollforward[-1]
    ar = project.ar_rollforward[-1]
    asset = project.asset_rollforward[-1]
    equity = project.equity_rollforward[-1]
    if cash["Outflows"] != (
        cash["Operating_Cash_Outflows"] + cash["Investing_Cash_Outflows"]
    ):
        raise RuntimeError(f"S6_CASH_OUTFLOW_COMPONENT_MISMATCH:{trial_id}:{day}")

    equations = (
        (
            "CASH",
            cash["Opening_Cash"] + cash["Inflows"] - cash["Outflows"]
            == cash["Closing_Cash"],
        ),
        (
            "AR",
            ar["Opening_AR"] + ar["Accruals"] - ar["Collections"]
            - ar["TransfersToGuarantee"] == ar["Closing_AR"],
        ),
        (
            "GROSS_ASSETS",
            asset["Opening_Gross_Bike_Assets"]
            + asset["Capitalized_Purchases_And_Customs"]
            - asset["Gross_Writeoffs_On_Ownership"]
            == asset["Closing_Gross_Bike_Assets"],
        ),
        (
            "DEPRECIATION",
            asset["Opening_Accumulated_Depreciation"]
            + asset["Expense_Depreciation"]
            - asset["AD_Removed_On_Writeoff"]
            == asset["Closing_Accumulated_Depreciation"],
        ),
        (
            "EQUITY",
            equity["Opening_Equity"] + equity["Operating_Net_Profit"]
            == equity["Closing_Equity"],
        ),
    )
    for name, passed in equations:
        if passed is not True:
            raise RuntimeError(f"S6_{name}_ROLLFORWARD_MISMATCH:{trial_id}:{day}")

    row = monte_carlo._daily_snapshot(project, current_date, trial_id)
    _assert_no_float(row, path=f"daily_snapshot.{trial_id}.{day}")
    daily_hasher.update(_canonical_json(row).encode("utf-8"))
    daily_hasher.update(b"\n")
    counters["daily_row_count"] += 1
    counters["daily_balance_check_count"] += 1
    counters["rollforward_equation_checks"] += len(equations)
    counters["max_abs_balance_difference"] = max(
        counters["max_abs_balance_difference"],
        abs(balance["Balance_Difference"]),
    )


def _run_trial_task(task: tuple[str, int, str, int]) -> dict[str, Any]:
    scenario_id, trial_id, source_sha, master_seed = task
    collection_probability, recovery_rate_pct = monte_carlo.parse_scenario_id(
        scenario_id
    )
    daily_hasher = hashlib.sha256()
    counters = {
        "daily_row_count": 0,
        "daily_balance_check_count": 0,
        "rollforward_equation_checks": 0,
        "max_abs_balance_difference": 0,
    }

    def capture_day(project: Any, current_date: Any) -> None:
        _check_day(project, current_date, trial_id, daily_hasher, counters)

    project = daily_engine.run_deterministic_trial(
        recovery_rate_pct=recovery_rate_pct,
        trial_id=trial_id,
        scenario_id=scenario_id,
        master_seed=master_seed,
        collection_probability=collection_probability,
        on_day_end=capture_day,
        log_events=False,
    )
    if not project.simulation_stopped or project.final_close_date is None:
        raise RuntimeError(f"S6_TRIAL_DID_NOT_CLOSE:{scenario_id}:{trial_id}")
    if counters["daily_row_count"] == 0:
        raise RuntimeError(f"S6_DAILY_EVIDENCE_EMPTY:{scenario_id}:{trial_id}")
    if len(project.daily_balance_checks) != counters["daily_row_count"]:
        raise RuntimeError(f"S6_DAILY_BALANCE_TOTAL_MISMATCH:{scenario_id}:{trial_id}")
    if any(
        len(rows) != counters["daily_row_count"]
        for rows in (
            project.cash_rollforward,
            project.ar_rollforward,
            project.asset_rollforward,
            project.equity_rollforward,
        )
    ):
        raise RuntimeError(f"S6_ROLLFORWARD_TOTAL_MISMATCH:{scenario_id}:{trial_id}")

    actual_bike_ids = [bike.bike_id for bike in project.bikes]
    expected_bike_ids = [
        format_bike_id(serial)
        for serial in range(1, len(project.bikes) + 1)
    ]
    if actual_bike_ids != expected_bike_ids or not all(
        is_canonical_bike_id(bike_id) for bike_id in actual_bike_ids
    ):
        raise RuntimeError(f"S6_BIKE_ID_SEQUENCE_INVALID:{scenario_id}:{trial_id}")

    result = monte_carlo._trial_result_from_project(
        project,
        scenario_id=scenario_id,
        collection_probability=collection_probability,
        recovery_rate_pct=recovery_rate_pct,
        trial_id=trial_id,
        master_seed=master_seed,
        source_sha=source_sha,
    )
    if result.rng_draw_count == 0 and result.rng_checksum != 0:
        raise RuntimeError(f"RNG_CHECKSUM_NONZERO_WITH_ZERO_DRAWS:{scenario_id}:{trial_id}")
    if not 0 <= result.rng_checksum < constants.RNG_CHECKSUM_MODULUS:
        raise RuntimeError(f"RNG_CHECKSUM_OUT_OF_RANGE:{scenario_id}:{trial_id}")
    expected_rng_audit = rng.rng_audit_fingerprint(
        source_sha=source_sha,
        master_seed=master_seed,
        scenario_id=scenario_id,
        trial_id=trial_id,
        rng_checksum=result.rng_checksum,
        rng_draw_count=result.rng_draw_count,
    )
    if result.rng_checksum_fingerprint_sha256 != expected_rng_audit:
        raise RuntimeError(f"RNG_AUDIT_FINGERPRINT_MISMATCH:{scenario_id}:{trial_id}")

    return {
        "scenario_id": scenario_id,
        "trial_id": trial_id,
        "trial_fingerprint": result.trial_fingerprint,
        "trial_result_sha256": _sha256_text(_canonical_json(asdict(result))),
        "daily_slice_sha256": daily_hasher.hexdigest(),
        "final_close_date": result.final_close_date,
        "final_net_project_equity": result.final_net_project_equity,
        "final_cash": result.final_cash,
        "cumulative_project_profit": result.cumulative_project_profit,
        "termination_count": result.termination_count,
        "secondary_cycle_count": result.secondary_cycle_count,
        "owned_bikes": result.owned_bikes,
        "held_assets": result.held_assets,
        "claims_created": len(project.guarantee_claims),
        "rng_checksum": result.rng_checksum,
        "rng_draw_count": result.rng_draw_count,
        "rng_checksum_fingerprint_sha256": result.rng_checksum_fingerprint_sha256,
        **counters,
        "canonical_bike_ids_valid": True,
    }


def _validate_rng_uniqueness(records: list[dict[str, Any]], scenario_id: str) -> None:
    seen: dict[int, int] = {}
    for row in records:
        checksum = row["rng_checksum"]
        draws = row["rng_draw_count"]
        trial_id = row["trial_id"]
        if draws == 0:
            if checksum != 0:
                raise RuntimeError(
                    f"RNG_CHECKSUM_NONZERO_WITH_ZERO_DRAWS:{scenario_id}:{trial_id}"
                )
            continue
        if checksum in seen:
            raise RuntimeError(
                f"DUPLICATE_RNG_CHECKSUM_DETECTED:{scenario_id}:"
                f"trial_ids={seen[checksum]},{trial_id}"
            )
        seen[checksum] = trial_id


def _map_sha256(scenario_id: str, records: Iterable[dict[str, Any]]) -> str:
    payload = "".join(
        f"{scenario_id}|{row['trial_id']}|{row['trial_fingerprint']}\n"
        for row in sorted(records, key=lambda item: item["trial_id"])
    )
    return _sha256_text(payload)


def _run_scenario(
    *,
    scenario_id: str,
    n: int,
    source_sha: str,
    tested_commit_sha: str,
    run_id: str,
    output_dir: Path,
) -> tuple[Path, Path]:
    _validate_checkpoint(n)
    if scenario_id not in _scenario_ids():
        raise ValueError(f"S6_SCENARIO_NOT_IN_V23_STOCHASTIC_FAMILY:{scenario_id}")
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError("S6_OUTPUT_DIRECTORY_NOT_EMPTY; refusing to overwrite evidence")
    output_dir.mkdir(parents=True, exist_ok=True)

    trial_ids = list(range(1, n + 1))
    tasks = [
        (scenario_id, trial_id, source_sha, constants.MASTER_SEED)
        for trial_id in trial_ids
    ]
    started_ns = time.perf_counter_ns()
    serial_start_ns = time.perf_counter_ns()
    serial_records = [_run_trial_task(task) for task in tasks]
    serial_elapsed_ns = time.perf_counter_ns() - serial_start_ns
    serial_records.sort(key=lambda row: row["trial_id"])
    if [row["trial_id"] for row in serial_records] != trial_ids:
        raise RuntimeError(f"S6_SERIAL_TRIAL_ID_COVERAGE_MISMATCH:{scenario_id}")
    _validate_rng_uniqueness(serial_records, scenario_id)

    serial_by_id = {row["trial_id"]: row for row in serial_records}
    worker_manifest: list[dict[str, Any]] = []
    parallel_elapsed_ns: dict[str, int] = {}
    for worker_count in constants.STAGE5_PARALLEL_WORKER_COUNTS:
        worker_start_ns = time.perf_counter_ns()
        with ProcessPoolExecutor(
            max_workers=worker_count,
            mp_context=get_context("spawn"),
        ) as pool:
            parallel_records = list(pool.map(_run_trial_task, tasks, chunksize=1))
        parallel_elapsed_ns[str(worker_count)] = (
            time.perf_counter_ns() - worker_start_ns
        )
        parallel_records.sort(key=lambda row: row["trial_id"])
        if [row["trial_id"] for row in parallel_records] != trial_ids:
            raise RuntimeError(
                f"S6_PARALLEL_TRIAL_ID_COVERAGE_MISMATCH:{scenario_id}:{worker_count}"
            )
        _validate_rng_uniqueness(parallel_records, scenario_id)
        parallel_by_id = {row["trial_id"]: row for row in parallel_records}
        for trial_id in trial_ids:
            serial_row = serial_by_id[trial_id]
            parallel_row = parallel_by_id[trial_id]
            exact = _canonical_json(serial_row) == _canonical_json(parallel_row)
            if exact is not True:
                raise RuntimeError(
                    f"S6_WORKER_EQUIVALENCE_FAILED:{scenario_id}:"
                    f"trial_id={trial_id}:workers={worker_count}"
                )
            worker_manifest.append({
                "scenario_id": scenario_id,
                "trial_id": trial_id,
                "worker_count": worker_count,
                "trial_fingerprint_serial": serial_row["trial_fingerprint"],
                "trial_fingerprint_parallel": parallel_row["trial_fingerprint"],
                "trial_result_sha256_serial": serial_row["trial_result_sha256"],
                "trial_result_sha256_parallel": parallel_row["trial_result_sha256"],
                "daily_slice_sha256_serial": serial_row["daily_slice_sha256"],
                "daily_slice_sha256_parallel": parallel_row["daily_slice_sha256"],
                "exact_result_and_daily_match": exact,
            })

    elapsed_ns = time.perf_counter_ns() - started_ns
    golden_map_sha256 = _map_sha256(scenario_id, serial_records)
    golden = {
        "schema_version": SCHEMA_VERSION,
        "status": "PREPARED_PENDING_REVIEW",
        "scope": "Gate A fingerprint preparation; not production Gate A/B PASS",
        "source_sha": source_sha,
        "tested_commit_sha": tested_commit_sha,
        "run_id": run_id,
        "master_seed": constants.MASTER_SEED,
        "rng_stream_id": scenario_id.split("_", maxsplit=1)[0],
        "scenario_id": scenario_id,
        "cohort_id": f"s6-v23-gatea-{source_sha[:12]}-N{n}",
        "checkpoint_n": n,
        "trial_ids": trial_ids,
        "trial_count": len(serial_records),
        "golden_map_sha256": golden_map_sha256,
        "records": serial_records,
        "production_gate_a_pass": False,
        "production_gate_b_pass": False,
        "scenario_stability_declared": False,
        "final_delivery_accepted": False,
    }
    audit = {
        "schema_version": "s6-gate-a-integrity-audit-v1",
        "source_sha": source_sha,
        "tested_commit_sha": tested_commit_sha,
        "run_id": run_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "command": " ".join(sys.argv),
        "python_version": sys.version.split()[0],
        "scenario_id": scenario_id,
        "checkpoint_n": n,
        "master_seed": constants.MASTER_SEED,
        "trial_ids_covered": len(serial_records),
        "daily_balance_checks": sum(row["daily_balance_check_count"] for row in serial_records),
        "daily_rollforward_equation_checks": sum(row["rollforward_equation_checks"] for row in serial_records),
        "max_abs_balance_difference": max(row["max_abs_balance_difference"] for row in serial_records),
        "canonical_bike_ids_all_valid": all(row["canonical_bike_ids_valid"] for row in serial_records),
        "rng_checksum_uniqueness_pass": True,
        "serial_elapsed_ns": serial_elapsed_ns,
        "parallel_elapsed_ns_by_worker_count": parallel_elapsed_ns,
        "total_elapsed_ns": elapsed_ns,
        "worker_manifest_rows": len(worker_manifest),
        "worker_equivalence_all_exact": all(row["exact_result_and_daily_match"] for row in worker_manifest),
        "worker_equivalence_manifest": worker_manifest,
        "golden_map_sha256": golden_map_sha256,
        "gate_a_status": "PREPARED_PENDING_REVIEW",
        "gate_b_status": "NOT_EVALUATED_BY_GOLDEN_PREPARER",
        "production_acceptance_allowed_by_this_artifact": False,
    }
    golden_path = output_dir / f"{scenario_id}.golden.json"
    audit_path = output_dir / f"{scenario_id}.audit.json"
    _write_json(golden_path, golden)
    _write_json(audit_path, audit)
    return golden_path, audit_path


def _merge_scenarios(
    *,
    input_dir: Path,
    output_dir: Path,
    source_sha: str,
    tested_commit_sha: str,
    run_id: str,
    n: int,
) -> list[Path]:
    _validate_checkpoint(n)
    if output_dir.exists() and any(output_dir.iterdir()):
        raise RuntimeError("S6_MERGE_OUTPUT_DIRECTORY_NOT_EMPTY; refusing to overwrite evidence")
    output_dir.mkdir(parents=True, exist_ok=True)
    expected_scenarios = _scenario_ids()
    golden_paths = sorted(input_dir.rglob("*.golden.json"))
    audit_paths = sorted(input_dir.rglob("*.audit.json"))
    if len(golden_paths) != len(expected_scenarios) or len(audit_paths) != len(expected_scenarios):
        raise RuntimeError("S6_SCENARIO_ARTIFACT_COUNT_MISMATCH")

    golden_by_scenario: dict[str, dict[str, Any]] = {}
    audit_by_scenario: dict[str, dict[str, Any]] = {}
    for path in golden_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        scenario_id = payload.get("scenario_id")
        if scenario_id in golden_by_scenario:
            raise RuntimeError(f"S6_DUPLICATE_SCENARIO_GOLDEN:{scenario_id}")
        if payload.get("schema_version") != SCHEMA_VERSION:
            raise RuntimeError(f"S6_GOLDEN_SCHEMA_MISMATCH:{scenario_id}")
        if payload.get("source_sha") != source_sha:
            raise RuntimeError(f"S6_SOURCE_SHA_MISMATCH:{scenario_id}")
        if payload.get("tested_commit_sha") != tested_commit_sha:
            raise RuntimeError(f"S6_TESTED_COMMIT_MISMATCH:{scenario_id}")
        if payload.get("run_id") != run_id or payload.get("checkpoint_n") != n:
            raise RuntimeError(f"S6_GOLDEN_RUN_OR_N_MISMATCH:{scenario_id}")
        records = payload.get("records")
        trial_ids = [row.get("trial_id") for row in records] if isinstance(records, list) else []
        if trial_ids != list(range(1, n + 1)):
            raise RuntimeError(f"S6_GOLDEN_TRIAL_COVERAGE_MISMATCH:{scenario_id}")
        if _map_sha256(scenario_id, records) != payload.get("golden_map_sha256"):
            raise RuntimeError(f"S6_GOLDEN_MAP_SHA256_MISMATCH:{scenario_id}")
        golden_by_scenario[scenario_id] = payload

    for path in audit_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        scenario_id = payload.get("scenario_id")
        if scenario_id in audit_by_scenario:
            raise RuntimeError(f"S6_DUPLICATE_SCENARIO_AUDIT:{scenario_id}")
        if (
            payload.get("source_sha") != source_sha
            or payload.get("tested_commit_sha") != tested_commit_sha
            or payload.get("run_id") != run_id
            or payload.get("checkpoint_n") != n
        ):
            raise RuntimeError(f"S6_SCENARIO_AUDIT_IDENTITY_MISMATCH:{scenario_id}")
        if payload.get("worker_equivalence_all_exact") is not True:
            raise RuntimeError(f"S6_SCENARIO_WORKER_EQUIVALENCE_NOT_PASS:{scenario_id}")
        if payload.get("max_abs_balance_difference") != 0:
            raise RuntimeError(f"S6_SCENARIO_BALANCE_NOT_ZERO:{scenario_id}")
        audit_by_scenario[scenario_id] = payload

    if set(golden_by_scenario) != set(expected_scenarios):
        raise RuntimeError("S6_SCENARIO_GOLDEN_COVERAGE_MISMATCH")
    if set(audit_by_scenario) != set(expected_scenarios):
        raise RuntimeError("S6_SCENARIO_AUDIT_COVERAGE_MISMATCH")

    for collection_pct in constants.STAGE5_STOCHASTIC_COLLECTION_PERCENTAGES:
        scenario_group = [
            golden_by_scenario[f"C{collection_pct:03d}_G{recovery:03d}"]
            for recovery in constants.GUARANTEE_RECOVERY_RATES
        ]
        for trial_id in range(1, n + 1):
            rows = [next(row for row in item["records"] if row["trial_id"] == trial_id) for item in scenario_group]
            if all(row["claims_created"] == 0 for row in rows):
                if len({row["trial_fingerprint"] for row in rows}) != 1:
                    raise RuntimeError(f"S6_G_INERT_TRIAL_FINANCIAL_MISMATCH:C{collection_pct:03d}:{trial_id}")
                if len({row["daily_slice_sha256"] for row in rows}) != 1:
                    raise RuntimeError(f"S6_G_INERT_TRIAL_DAILY_MISMATCH:C{collection_pct:03d}:{trial_id}")

    total_records = sum(len(item["records"]) for item in golden_by_scenario.values())
    map_payload = "".join(
        f"{scenario_id}|{row['trial_id']}|{row['trial_fingerprint']}\n"
        for scenario_id in sorted(golden_by_scenario)
        for row in sorted(golden_by_scenario[scenario_id]["records"], key=lambda item: item["trial_id"])
    )
    global_map_sha256 = _sha256_text(map_payload)
    scenarios_summary = []
    global_g_inert: dict[str, bool] = {}
    for collection_pct in constants.STAGE5_STOCHASTIC_COLLECTION_PERCENTAGES:
        scenario_group = [
            golden_by_scenario[f"C{collection_pct:03d}_G{recovery:03d}"]
            for recovery in constants.GUARANTEE_RECOVERY_RATES
        ]
        all_claims_absent = all(
            row["claims_created"] == 0
            for item in scenario_group
            for row in item["records"]
        )
        outputs_equal = all(
            len({
                next(row for row in item["records"] if row["trial_id"] == trial_id)["trial_fingerprint"]
                for item in scenario_group
            }) == 1
            and len({
                next(row for row in item["records"] if row["trial_id"] == trial_id)["daily_slice_sha256"]
                for item in scenario_group
            }) == 1
            for trial_id in range(1, n + 1)
        )
        global_g_inert[f"C{collection_pct:03d}"] = all_claims_absent and outputs_equal

    for scenario_id in sorted(golden_by_scenario):
        payload = golden_by_scenario[scenario_id]
        records = payload["records"]
        daily_paths = {row["daily_slice_sha256"] for row in records}
        scenarios_summary.append({
            "scenario_id": scenario_id,
            "N_total": n,
            "N_closed": sum(row["final_close_date"] is not None for row in records),
            "N_censored": sum(row["final_close_date"] is None for row in records),
            "N_unique_paths": len(daily_paths),
            "DEGENERATE_DETERMINISTIC": len(daily_paths) == 1,
            "G_INERT": global_g_inert[scenario_id.split("_", maxsplit=1)[0]],
            "golden_map_sha256": payload["golden_map_sha256"],
            "scenario_artifact_sha256": _sha256_file(next(p for p in golden_paths if p.name == f"{scenario_id}.golden.json")),
            "audit_artifact_sha256": _sha256_file(next(p for p in audit_paths if p.name == f"{scenario_id}.audit.json")),
        })

    combined = {
        "schema_version": SCHEMA_VERSION,
        "status": "PREPARED_PENDING_REVIEW",
        "scope": "Twenty stochastic v2.3 scenarios only; C100 is reused as separate S4 evidence and was not rerun",
        "source_sha": source_sha,
        "tested_commit_sha": tested_commit_sha,
        "run_id": run_id,
        "master_seed": constants.MASTER_SEED,
        "checkpoint_n": n,
        "cohort_id": f"s6-v23-gatea-{source_sha[:12]}-N{n}",
        "scenario_count": len(expected_scenarios),
        "trial_record_count": total_records,
        "scenario_map_sha256": global_map_sha256,
        "scenario_matrix": scenarios_summary,
        "records_by_scenario": {
            scenario_id: golden_by_scenario[scenario_id]["records"]
            for scenario_id in sorted(golden_by_scenario)
        },
        "production_gate_a_pass": False,
        "production_gate_b_pass": False,
        "scenario_stability_declared": False,
        "final_delivery_accepted": False,
    }
    combined_path = output_dir / f"STOCHASTIC_GATE_A_GOLDEN_{source_sha}_{n}.json"
    index_path = output_dir / "STOCHASTIC_GATE_A_GOLDEN_INDEX.json"
    _write_json(combined_path, combined)
    index = {
        "schema_version": "s6-gate-a-golden-index-v1",
        "status": "PREPARED_PENDING_REVIEW",
        "source_sha": source_sha,
        "tested_commit_sha": tested_commit_sha,
        "run_id": run_id,
        "master_seed": constants.MASTER_SEED,
        "checkpoint_n": n,
        "scenario_count": len(expected_scenarios),
        "trial_record_count": total_records,
        "scenario_map_sha256": global_map_sha256,
        "combined_golden_file": combined_path.name,
        "combined_golden_sha256": _sha256_file(combined_path),
        "scenario_matrix": scenarios_summary,
        "production_gate_a_pass": False,
        "production_gate_b_pass": False,
        "scenario_stability_declared": False,
        "final_delivery_accepted": False,
    }
    _write_json(index_path, index)
    manifest = [
        f"{_sha256_file(path)}  {path.name}"
        for path in sorted(output_dir.iterdir())
        if path.is_file() and path.name != "SHA256SUMS.txt"
    ]
    sums_path = output_dir / "SHA256SUMS.txt"
    sums_path.write_text("\n".join(manifest) + "\n", encoding="utf-8")
    return [combined_path, index_path, sums_path]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare independently audited Gate A fingerprints for the twenty v2.3 stochastic scenarios."
    )
    parser.add_argument("--scenario", default=None)
    parser.add_argument("--n", type=int, default=constants.STATISTICAL_CHECK_START_N)
    parser.add_argument("--output-dir", default="results_s6")
    parser.add_argument("--merge-dir", default=None)
    args = parser.parse_args()

    source_sha, tested_commit_sha, run_id = _resolve_identities()
    _validate_checkpoint(args.n)
    output_dir = Path(args.output_dir)

    if args.merge_dir is not None:
        outputs = _merge_scenarios(
            input_dir=Path(args.merge_dir),
            output_dir=output_dir,
            source_sha=source_sha,
            tested_commit_sha=tested_commit_sha,
            run_id=run_id,
            n=args.n,
        )
        print(json.dumps({
            "status": "PREPARED_PENDING_REVIEW",
            "source_sha": source_sha,
            "tested_commit_sha": tested_commit_sha,
            "run_id": run_id,
            "checkpoint_n": args.n,
            "outputs": [str(path) for path in outputs],
            "production_gate_a_pass": False,
            "production_gate_b_pass": False,
        }, ensure_ascii=False, sort_keys=True))
        return 0

    if args.scenario is None:
        raise SystemExit("S6_SCENARIO_REQUIRED_UNLESS_MERGING")
    started_at = datetime.now(timezone.utc).isoformat()
    golden_path, audit_path = _run_scenario(
        scenario_id=args.scenario,
        n=args.n,
        source_sha=source_sha,
        tested_commit_sha=tested_commit_sha,
        run_id=run_id,
        output_dir=output_dir,
    )
    print(json.dumps({
        "status": "PREPARED_PENDING_REVIEW",
        "scenario_id": args.scenario,
        "source_sha": source_sha,
        "tested_commit_sha": tested_commit_sha,
        "run_id": run_id,
        "checkpoint_n": args.n,
        "started_at": started_at,
        "golden_file": str(golden_path),
        "golden_sha256": _sha256_file(golden_path),
        "audit_file": str(audit_path),
        "audit_sha256": _sha256_file(audit_path),
        "production_gate_a_pass": False,
        "production_gate_b_pass": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
