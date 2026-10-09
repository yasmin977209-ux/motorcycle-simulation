from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

EXPECTED_CP12C_RUN_ID = "37971902520"
EXPECTED_CP12C_RUN_SHA = "d4b335926d25d4bc2c6440effc7568260ef5aeb8"
EXPECTED_CP12B_RUN_ID = "37964656154"
EXPECTED_CP12B_RUN_SHA = "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
EXPECTED_SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
EXPECTED_MASTER_SEED = 20270101
EXPECTED_ROWS = 22546465
EXPECTED_TRIALS = 11005
EXPECTED_GLOBAL_SHA = "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44"
SCHEMA_VERSION = "stage12-daily-accounting-v1"
IDENTITY_KEY = b"stage12.dataset_identity"
START_DATE = np.datetime64("2027-01-01", "D")
CUTOFF_DATE = np.datetime64("2030-12-31", "D")
TRIAL_COUNTS = {
    f"C{collection:03d}_G{recovery:03d}": (1 if collection == 100 else 550)
    for collection in (100, 85, 70, 50, 30)
    for recovery in (100, 70, 50, 30, 0)
}
RNG_POLICY = (
    "rng.py:SHA-256(seed key master_seed|scenario_id|trial_id|bike_id|date|event_type); "
    "draw=first_8_digest_bytes_big_endian/2^64; probability boundaries are deterministic"
)
SAMPLING_POLICY = (
    "one-based contiguous trial IDs; C100 scenarios use 1..1; non-C100 scenarios use 1..550; "
    "one materialization per scenario/trial; no cross-run inputs or resume"
)
STABILITY_POLICY = (
    "C100 uses one deterministic trial and no CI gate; non-C100 checkpoint N=300 then +50; "
    "95% Student-t CI half-width <1% of absolute mean for Final_Net_Project_Equity, "
    "Partner1_Final_Entitlement, Partner2_Final_Entitlement; CI_ABSOLUTE_EPSILON=1; "
    "three consecutive successful checkpoints; accepted N=550 (checkpoints 450, 500, 550)"
)
TRIAL_ID_POLICY = "one-based contiguous trial IDs from 1 to scenario target; no duplicate IDs"

EXPECTED_COLUMN_TYPES = {
    "scenario_id": "string", "trial_id": "int64", "date": "string",
    "source_sha": "string", "master_seed": "int64",
    "Opening_Cash": "int64", "cash_inflows": "int64", "cash_outflows": "int64",
    "Closing_Cash": "int64", "Opening_AR": "int64", "ar_accruals": "int64",
    "ar_collections": "int64", "ar_transfers_to_guarantee": "int64",
    "Closing_AR": "int64", "Opening_Gross_Bike_Assets": "int64",
    "capitalized_purchases_and_customs": "int64", "gross_writeoffs_on_ownership": "int64",
    "Closing_Gross_Bike_Assets": "int64", "Opening_Accumulated_Depreciation": "int64",
    "depreciation_expense": "int64", "ad_removed_on_writeoff": "int64",
    "Closing_Accumulated_Depreciation": "int64", "Net_Bike_Assets": "int64",
    "Capital": "int64", "Retained_Earnings": "int64", "Opening_Equity": "int64",
    "Operating_Net_Profit": "int64", "Closing_Equity": "int64",
    "Guarantee_Claim_Receivable": "int64", "Total_Assets": "int64",
    "Liabilities": "int64", "Balance_Difference": "int64",
    "Final_Close_Date": "string", "Simulation_Stopped": "bool",
    "Active_Bikes": "int64", "Owned_Transferred_Bikes": "int64",
    "Pending_Claims": "int64", "result_sha256": "string",
}

INT_FIELDS = [
    "trial_id", "master_seed", "Active_Bikes", "Owned_Transferred_Bikes",
    "Pending_Claims", "Closing_AR", "Guarantee_Claim_Receivable",
    "Balance_Difference", "Total_Assets", "Closing_Equity", "Liabilities",
]
STR_FIELDS = [
    "scenario_id", "date", "source_sha", "Final_Close_Date", "result_sha256",
]
BOOL_FIELDS = ["Simulation_Stopped"]
IDENTITY_FIELDS = [
    "scenario_id", "trial_id", "date", "source_sha", "master_seed",
    "Final_Close_Date", "result_sha256",
]


def closure_row_masks(
    columns: dict[str, np.ndarray],
    dates: np.ndarray,
    final_dates: np.ndarray,
    stopped: np.ndarray,
) -> dict[str, np.ndarray]:
    """Daily closure gates derived from CP-12-B fields and the reference closure requirements."""
    active = columns["Active_Bikes"]
    transferred = columns["Owned_Transferred_Bikes"]
    pending = columns["Pending_Claims"]
    close_ar = columns["Closing_AR"]
    guarantee_ar = columns["Guarantee_Claim_Receivable"]
    balance_diff = columns["Balance_Difference"]
    total_assets = columns["Total_Assets"]
    closing_equity = columns["Closing_Equity"]
    liabilities = columns["Liabilities"]
    return {
        "final_close_date_present": ~np.isnat(final_dates),
        "final_close_date_after_expansion_cutoff": final_dates > CUTOFF_DATE,
        "simulation_stopped_matches_final_close_date": stopped == (dates == final_dates),
        "terminal_no_active_possession_bikes": (~stopped) | (active == 0),
        "terminal_no_pending_claims": (~stopped) | (pending == 0),
        "terminal_accounts_receivable_zero": (~stopped) | (close_ar == 0),
        "terminal_guarantee_receivable_zero": (~stopped) | (guarantee_ar == 0),
        "terminal_balance_difference_zero": (~stopped) | (balance_diff == 0),
        "terminal_assets_equal_equity": (~stopped) | (total_assets == closing_equity),
        "terminal_liabilities_zero": (~stopped) | (liabilities == 0),
        "active_bikes_nonnegative": active >= 0,
        "owned_transferred_bikes_nonnegative": transferred >= 0,
        "pending_claims_nonnegative": pending >= 0,
    }


def _entry() -> dict:
    return {"rows_checked": 0, "violations": 0, "examples": []}


def _record(report: dict, name: str, mask: np.ndarray, scenario: str, trial_ids, dates, offset: int = 0) -> None:
    item = report["checks"].setdefault(name, _entry())
    mask = np.asarray(mask, dtype=bool)
    item["rows_checked"] += int(mask.size)
    failures = np.flatnonzero(~mask)
    item["violations"] += int(failures.size)
    for i in failures[: max(0, 5 - len(item["examples"]))]:
        item["examples"].append({
            "scenario": scenario, "trial_id": int(trial_ids[i]),
            "date": str(dates[i]), "batch_row": int(offset + i),
        })


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _verify_cp12c_report(path: Path) -> dict:
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report.get("overall_result") == "PASS", "CP-12-C audit report is not PASS"
    assert report.get("source_run_id") == EXPECTED_CP12B_RUN_ID
    assert report.get("source_run_head_sha") == EXPECTED_CP12B_RUN_SHA
    assert report.get("source_sha") == EXPECTED_SOURCE_SHA
    assert report.get("master_seed") == EXPECTED_MASTER_SEED
    assert report.get("expected_global_sha256_from_cp12b") == EXPECTED_GLOBAL_SHA
    assert report.get("expected_daily_rows_from_cp12b") == EXPECTED_ROWS
    assert report.get("total_daily_rows") == EXPECTED_ROWS
    assert report.get("total_trials") == EXPECTED_TRIALS
    assert report.get("scenario_count") == 25
    assert all(v.get("violations") == 0 for v in report.get("checks", {}).values())
    assert len(report.get("scenarios", {})) == 25
    return report


def _validate_file(path: Path, cp12c_report: dict, report: dict) -> dict:
    scenario = path.stem
    expected_trials = TRIAL_COUNTS[scenario]
    expected_file = cp12c_report["scenarios"].get(scenario)
    if expected_file is None:
        raise ValueError(f"scenario missing from CP-12-C report: {scenario}")
    file_sha = _file_sha256(path)
    if file_sha != expected_file["content_sha256"]:
        raise ValueError(f"immutable CP-12-B/CP-12-C content SHA mismatch: {path.name}")
    parquet = pq.ParquetFile(path)
    schema = parquet.schema_arrow
    if {field.name: str(field.type) for field in schema} != EXPECTED_COLUMN_TYPES:
        raise ValueError(f"schema/type mismatch: {path.name}")
    if any(field.nullable != (field.name == "Final_Close_Date") for field in schema):
        raise ValueError(f"schema nullability mismatch: {path.name}")
    metadata = schema.metadata or {}
    expected_identity = {
        "schema_version": SCHEMA_VERSION, "scenario": scenario,
        "source_sha": EXPECTED_SOURCE_SHA, "master_seed": EXPECTED_MASTER_SEED,
        "rng_policy": RNG_POLICY, "sampling_policy": SAMPLING_POLICY,
        "stability_policy": STABILITY_POLICY, "trial_id_policy": TRIAL_ID_POLICY,
    }
    identity_raw = metadata.get(IDENTITY_KEY)
    if identity_raw is None or json.loads(identity_raw.decode("utf-8")) != expected_identity:
        raise ValueError(f"dataset identity mismatch: {path.name}")

    names = list(closure_row_masks(
        {name: np.array([], dtype=np.int64) for name in INT_FIELDS},
        np.array([], dtype="datetime64[D]"),
        np.array([], dtype="datetime64[D]"),
        np.array([], dtype=bool),
    ))
    for name in names:
        report["checks"].setdefault(name, _entry())
    for name in (
        "trial_id_sequence", "date_continuity", "final_close_date_constant",
        "owned_transferred_bikes_monotonic", "trial_closure_summary",
        "trial_result_fingerprint_constant", "row_source_identity",
        "row_scenario_identity", "row_seed_identity",
    ):
        report["checks"].setdefault(name, _entry())

    needed = INT_FIELDS + STR_FIELDS + BOOL_FIELDS
    total_rows = 0
    trial_count = 0
    current = None
    next_expected_trial = 1
    close_dates = []
    stopped_rows = 0
    row_offset = 0

    def finish_trial(state: dict) -> None:
        nonlocal trial_count, next_expected_trial
        trial_count += 1
        passed = (
            state["trial_id"] == next_expected_trial
            and state["first_date"] == "2027-01-01"
            and state["final_date"] is not None
            and state["final_date"] > "2030-12-31"
            and state["last_date"] == state["final_date"]
            and state["stopped_rows"] == 1
        )
        _record(
            report, "trial_closure_summary", np.asarray([passed], dtype=bool),
            scenario, [state["trial_id"]], [state["last_date"]], state["row_offset"],
        )
        next_expected_trial += 1
        if state["final_date"] is not None:
            close_dates.append(state["final_date"])

    for batch in parquet.iter_batches(batch_size=100_000, columns=needed):
        if not batch.num_rows:
            continue
        n = batch.num_rows
        cols = {
            name: np.asarray(batch.column(batch.schema.get_field_index(name)).to_numpy(zero_copy_only=False))
            for name in INT_FIELDS
        }
        raw_dates = batch.column(batch.schema.get_field_index("date")).to_pylist()
        raw_final_dates = batch.column(batch.schema.get_field_index("Final_Close_Date")).to_pylist()
        raw_scenarios = batch.column(batch.schema.get_field_index("scenario_id")).to_pylist()
        raw_sources = batch.column(batch.schema.get_field_index("source_sha")).to_pylist()
        fingerprints = batch.column(batch.schema.get_field_index("result_sha256")).to_pylist()
        dates = np.asarray(raw_dates, dtype="datetime64[D]")
        final_dates = np.asarray(raw_final_dates, dtype="datetime64[D]")
        ids = cols["trial_id"]
        seeds = cols["master_seed"]
        stopped = np.asarray(
            batch.column(batch.schema.get_field_index("Simulation_Stopped")).to_numpy(zero_copy_only=False),
            dtype=bool,
        )
        masks = closure_row_masks(cols, dates, final_dates, stopped)
        for name, mask in masks.items():
            _record(report, name, mask, scenario, ids, raw_dates, row_offset)
        _record(
            report, "row_source_identity",
            np.asarray([v == EXPECTED_SOURCE_SHA for v in raw_sources]),
            scenario, ids, raw_dates, row_offset,
        )
        _record(
            report, "row_scenario_identity",
            np.asarray([v == scenario for v in raw_scenarios]),
            scenario, ids, raw_dates, row_offset,
        )
        _record(
            report, "row_seed_identity", seeds == EXPECTED_MASTER_SEED,
            scenario, ids, raw_dates, row_offset,
        )

        if n > 1:
            same = ids[1:] == ids[:-1]
            _record(
                report, "date_continuity",
                (~same) | (dates[1:] == dates[:-1] + np.timedelta64(1, "D")),
                scenario, ids[1:], raw_dates[1:], row_offset + 1,
            )
            _record(
                report, "final_close_date_constant",
                (~same) | (final_dates[1:] == final_dates[:-1]),
                scenario, ids[1:], raw_dates[1:], row_offset + 1,
            )
            _record(
                report, "trial_result_fingerprint_constant",
                (~same) | (np.asarray(fingerprints[1:], dtype=object) == np.asarray(fingerprints[:-1], dtype=object)),
                scenario, ids[1:], raw_dates[1:], row_offset + 1,
            )
            _record(
                report, "owned_transferred_bikes_monotonic",
                (~same) | (cols["Owned_Transferred_Bikes"][1:] >= cols["Owned_Transferred_Bikes"][:-1]),
                scenario, ids[1:], raw_dates[1:], row_offset + 1,
            )
            boundaries = np.flatnonzero(~same) + 1
            if boundaries.size:
                sequence_ok = (ids[boundaries] == ids[boundaries - 1] + 1) & (dates[boundaries] == START_DATE)
                _record(report, "trial_id_sequence", sequence_ok, scenario, ids[boundaries], [raw_dates[i] for i in boundaries], row_offset)

        # Cross-batch/opening segment validation: retain exact per-trial terminal state.
        bounds = np.concatenate(([0], np.flatnonzero(ids[1:] != ids[:-1]) + 1, [n]))
        for left, right in zip(bounds[:-1], bounds[1:]):
            tid = int(ids[left])
            segment_stop_count = int(stopped[left:right].sum())
            segment_final_values = raw_final_dates[left:right]
            segment_final = segment_final_values[0]
            constant = all(value == segment_final for value in segment_final_values)
            if left == 0 and current is not None and current["trial_id"] == tid:
                same_trial = True
            else:
                same_trial = current is not None and current["trial_id"] == tid

            if current is None or not same_trial:
                if current is not None:
                    finish_trial(current)
                current = {
                    "trial_id": tid,
                    "first_date": raw_dates[left],
                    "last_date": raw_dates[right - 1],
                    "final_date": segment_final,
                    "stopped_rows": segment_stop_count,
                    "row_offset": row_offset + left,
                    "last_owned_transferred": int(cols["Owned_Transferred_Bikes"][right - 1]),
                }
            else:
                current["last_date"] = raw_dates[right - 1]
                current["stopped_rows"] += segment_stop_count
                if current["final_date"] != segment_final:
                    constant = False
                if int(cols["Owned_Transferred_Bikes"][left]) < current["last_owned_transferred"]:
                    _record(
                        report, "owned_transferred_bikes_monotonic", np.asarray([False]),
                        scenario, [tid], [raw_dates[left]], row_offset + left,
                    )
                current["last_owned_transferred"] = int(cols["Owned_Transferred_Bikes"][right - 1])

            _record(
                report, "final_close_date_constant", np.asarray([constant]),
                scenario, [tid], [raw_dates[right - 1]], row_offset + right - 1,
            )
            current["last_date"] = raw_dates[right - 1]
            current["last_owned_transferred"] = int(cols["Owned_Transferred_Bikes"][right - 1])
        total_rows += n
        stopped_rows += int(stopped.sum())
        row_offset += n

    if current is not None:
        finish_trial(current)
    if trial_count != expected_trials:
        raise ValueError(f"expected {expected_trials} trials for {scenario}, got {trial_count}")
    if next_expected_trial != expected_trials + 1:
        raise ValueError(f"trial IDs are not exactly 1..{expected_trials} for {scenario}")
    if total_rows != int(expected_file["daily_rows"]):
        raise ValueError(f"daily row count changed from CP-12-C report for {scenario}")
    if stopped_rows != expected_trials:
        raise ValueError(f"expected one stopped row per trial for {scenario}; got {stopped_rows}")
    if len(close_dates) != expected_trials:
        raise ValueError(f"final close-date census incomplete for {scenario}")

    return {
        "file": path.name,
        "content_sha256": file_sha,
        "content_sha256_matches_cp12c_report": True,
        "trial_count": trial_count,
        "daily_rows": total_rows,
        "stopped_rows": stopped_rows,
        "final_close_date_min": min(close_dates),
        "final_close_date_max": max(close_dates),
        "distinct_final_close_dates": len(set(close_dates)),
        "all_trials_finalized": True,
    }


def validate(root: Path, cp12c_path: Path) -> dict:
    cp12c = _verify_cp12c_report(cp12c_path)
    report = {
        "created_by_cp": "CP-12-D",
        "source_cp": "CP-12-C",
        "cp12c_run_id": EXPECTED_CP12C_RUN_ID,
        "cp12c_run_sha": EXPECTED_CP12C_RUN_SHA,
        "cp12b_run_id": EXPECTED_CP12B_RUN_ID,
        "cp12b_run_sha": EXPECTED_CP12B_RUN_SHA,
        "source_sha": EXPECTED_SOURCE_SHA,
        "master_seed": EXPECTED_MASTER_SEED,
        "schema_version": SCHEMA_VERSION,
        "expected_global_sha256": EXPECTED_GLOBAL_SHA,
        "overall_result": "FAIL",
        "scenario_count": 0,
        "total_trials": 0,
        "total_daily_rows": 0,
        "terminal_stopped_rows": 0,
        "checks": {},
        "scenarios": {},
        "scope_limitations": [
            "The pinned daily schema contains Active_Bikes, Owned_Transferred_Bikes and Pending_Claims, but not per-bike lifecycle states or per-bike settlement start/due timestamps. This audit does not claim a per-bike settlement-duration census.",
            "Dynamic closure preconditions and the successful/failed post-maturity settlement paths are supported by the pinned CP-12-B acceptance/regression evidence; the current daily schema independently verifies final closure outcomes, not every bike's historical state transition."
        ],
        "failure": None,
    }
    files = sorted(root.rglob("*.parquet"))
    if len(files) != 25 or {path.stem for path in files} != set(TRIAL_COUNTS):
        raise ValueError(f"expected exact 25 CP-12-B parquet files, got {len(files)}")

    trials = rows = stopped = 0
    for path in files:
        scenario = path.stem
        item = _validate_file(path, cp12c, report)
        report["scenarios"][scenario] = item
        trials += item["trial_count"]
        rows += item["daily_rows"]
        stopped += item["stopped_rows"]
    report["scenario_count"] = len(files)
    report["total_trials"] = trials
    report["total_daily_rows"] = rows
    report["terminal_stopped_rows"] = stopped

    if trials != EXPECTED_TRIALS:
        raise ValueError(f"expected {EXPECTED_TRIALS} trials, got {trials}")
    if rows != EXPECTED_ROWS:
        raise ValueError(f"expected {EXPECTED_ROWS} daily rows, got {rows}")
    if stopped != EXPECTED_TRIALS:
        raise ValueError(f"expected {EXPECTED_TRIALS} terminal rows, got {stopped}")

    violations = {name: value["violations"] for name, value in report["checks"].items() if value["violations"]}
    if violations:
        report["failure"] = {"closure_or_identity_violations": violations}
        return report
    report["overall_result"] = "PASS"
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit closure and terminal settlement outcomes from the pinned CP-12-B daily dataset.")
    parser.add_argument("--root", required=True, help="directory containing the exact 25 CP-12-B Parquet files")
    parser.add_argument("--cp12c-report", required=True, help="successful CP-12-C rollforward_result.json")
    parser.add_argument("--output", required=True, help="output path for closure evidence JSON")
    args = parser.parse_args()
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        report = validate(Path(args.root), Path(args.cp12c_report))
    except Exception as exc:
        report = {
            "created_by_cp": "CP-12-D",
            "source_cp": "CP-12-C",
            "cp12c_run_id": EXPECTED_CP12C_RUN_ID,
            "cp12c_run_sha": EXPECTED_CP12C_RUN_SHA,
            "source_sha": EXPECTED_SOURCE_SHA,
            "master_seed": EXPECTED_MASTER_SEED,
            "overall_result": "FAIL",
            "failure": {"type": type(exc).__name__, "message": str(exc)},
        }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report.get("overall_result") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
