from __future__ import annotations

import argparse
import hashlib
import json
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

import pyarrow as pa
import pyarrow.parquet as pq

import daily_engine
import monte_carlo
from entities import BikeState, ClaimStatus

SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
MASTER_SEED = 20270101
MAX_WORKERS = 8
SCHEMA_VERSION = "stage12-daily-accounting-v1"
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
TRIAL_COUNTS = {
    f"C{c:03}_G{g:03}": (1 if c == 100 else 550)
    for c in (100, 85, 70, 50, 30)
    for g in (100, 70, 50, 30, 0)
}
DAILY_FIELDS = [
    ("scenario_id", pa.string()), ("trial_id", pa.int64()), ("date", pa.string()),
    ("source_sha", pa.string()), ("master_seed", pa.int64()),
    ("Opening_Cash", pa.int64()), ("cash_inflows", pa.int64()),
    ("cash_outflows", pa.int64()), ("Closing_Cash", pa.int64()),
    ("Opening_AR", pa.int64()), ("ar_accruals", pa.int64()),
    ("ar_collections", pa.int64()), ("ar_transfers_to_guarantee", pa.int64()),
    ("Closing_AR", pa.int64()), ("Opening_Gross_Bike_Assets", pa.int64()),
    ("capitalized_purchases_and_customs", pa.int64()),
    ("gross_writeoffs_on_ownership", pa.int64()),
    ("Closing_Gross_Bike_Assets", pa.int64()),
    ("Opening_Accumulated_Depreciation", pa.int64()),
    ("depreciation_expense", pa.int64()), ("ad_removed_on_writeoff", pa.int64()),
    ("Closing_Accumulated_Depreciation", pa.int64()),
    ("Net_Bike_Assets", pa.int64()), ("Capital", pa.int64()),
    ("Retained_Earnings", pa.int64()), ("Opening_Equity", pa.int64()),
    ("Operating_Net_Profit", pa.int64()), ("Closing_Equity", pa.int64()),
    ("Guarantee_Claim_Receivable", pa.int64()), ("Total_Assets", pa.int64()),
    ("Liabilities", pa.int64()), ("Balance_Difference", pa.int64()),
    ("Final_Close_Date", pa.string()), ("Simulation_Stopped", pa.bool_()),
    ("Active_Bikes", pa.int64()), ("Owned_Transferred_Bikes", pa.int64()),
    ("Pending_Claims", pa.int64()), ("result_sha256", pa.string()),
]


def _dataset_identity(scenario_id: str) -> dict[str, object]:
    return {
        "schema_version": SCHEMA_VERSION,
        "scenario": scenario_id,
        "source_sha": SOURCE_SHA,
        "master_seed": MASTER_SEED,
        "rng_policy": RNG_POLICY,
        "sampling_policy": SAMPLING_POLICY,
        "stability_policy": STABILITY_POLICY,
        "trial_id_policy": TRIAL_ID_POLICY,
    }


def _daily_schema(scenario_id: str) -> pa.Schema:
    identity = json.dumps(
        _dataset_identity(scenario_id),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    fields = [
        pa.field(name, field_type, nullable=(name == "Final_Close_Date"))
        for name, field_type in DAILY_FIELDS
    ]
    return pa.schema(fields, metadata={b"stage12.dataset_identity": identity})


def _materialize_trial(task: tuple[str, int, str]) -> int:
    scenario_id, trial_id, scratch_dir = task
    collection_probability, recovery_rate_pct = monte_carlo.parse_scenario_id(scenario_id)
    daily_meta = []

    def capture(project, day):
        daily_meta.append({
            "date": day.isoformat(),
            "Capital": project.capital,
            "Retained_Earnings": project.retained_earnings,
            "Simulation_Stopped": project.simulation_stopped,
            "Active_Bikes": sum(
                bike.current_state in daily_engine.POSSESSION_STATES
                for bike in project.bikes
            ),
            "Owned_Transferred_Bikes": sum(
                bike.current_state is BikeState.OWNED_TRANSFERRED
                for bike in project.bikes
            ),
            "Pending_Claims": sum(
                claim.status is ClaimStatus.PENDING
                for claim in project.guarantee_claims
            ),
        })

    project = daily_engine.run_deterministic_trial(
        recovery_rate_pct=recovery_rate_pct,
        trial_id=trial_id,
        scenario_id=scenario_id,
        master_seed=MASTER_SEED,
        collection_probability=collection_probability,
        on_day_end=capture,
        log_events=False,
    )
    result = monte_carlo._trial_result_from_project(
        project,
        scenario_id=scenario_id,
        collection_probability=collection_probability,
        recovery_rate_pct=recovery_rate_pct,
        trial_id=trial_id,
    )
    result_payload = json.dumps(
        asdict(result), ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), default=str,
    ).encode("utf-8")
    trial_sha = hashlib.sha256(result_payload).hexdigest()

    series = (
        project.daily_snapshots, project.cash_rollforward, project.ar_rollforward,
        project.asset_rollforward, project.equity_rollforward, daily_meta,
    )
    if len({len(values) for values in series}) != 1:
        raise RuntimeError(f"daily accounting length mismatch trial {trial_id}")

    rows = []
    for snap, cash, ar, asset, equity, meta in zip(*series):
        snapshot_date = snap["date"].isoformat()
        if meta["date"] != snapshot_date:
            raise RuntimeError(
                f"daily date alignment mismatch trial {trial_id}: "
                f"{meta['date']} != {snapshot_date}"
            )
        rows.append({
            "scenario_id": scenario_id, "trial_id": trial_id, "date": snapshot_date,
            "source_sha": SOURCE_SHA, "master_seed": MASTER_SEED,
            "Opening_Cash": cash["Opening_Cash"], "cash_inflows": cash["Inflows"],
            "cash_outflows": cash["Outflows"], "Closing_Cash": cash["Closing_Cash"],
            "Opening_AR": ar["Opening_AR"], "ar_accruals": ar["Accruals"],
            "ar_collections": ar["Collections"],
            "ar_transfers_to_guarantee": ar["TransfersToGuarantee"],
            "Closing_AR": ar["Closing_AR"],
            "Opening_Gross_Bike_Assets": asset["Opening_Gross_Bike_Assets"],
            "capitalized_purchases_and_customs": asset["Capitalized_Purchases_And_Customs"],
            "gross_writeoffs_on_ownership": asset["Gross_Writeoffs_On_Ownership"],
            "Closing_Gross_Bike_Assets": asset["Closing_Gross_Bike_Assets"],
            "Opening_Accumulated_Depreciation": asset["Opening_Accumulated_Depreciation"],
            "depreciation_expense": asset["Depreciation_Expense"],
            "ad_removed_on_writeoff": asset["AD_Removed_On_Writeoff"],
            "Closing_Accumulated_Depreciation": asset["Closing_Accumulated_Depreciation"],
            "Net_Bike_Assets": snap["Net_Bike_Assets"],
            "Capital": meta["Capital"], "Retained_Earnings": meta["Retained_Earnings"],
            "Opening_Equity": equity["Opening_Equity"],
            "Operating_Net_Profit": equity["Operating_Net_Profit"],
            "Closing_Equity": equity["Closing_Equity"],
            "Guarantee_Claim_Receivable": snap["Guarantee_Claim_Receivable"],
            "Total_Assets": snap["Total_Assets"], "Liabilities": snap["Liabilities"],
            "Balance_Difference": snap["Balance_Difference"],
            "Final_Close_Date": (
                project.final_close_date.isoformat() if project.final_close_date else None
            ),
            "Simulation_Stopped": meta["Simulation_Stopped"],
            "Active_Bikes": meta["Active_Bikes"],
            "Owned_Transferred_Bikes": meta["Owned_Transferred_Bikes"],
            "Pending_Claims": meta["Pending_Claims"], "result_sha256": trial_sha,
        })

    if not rows:
        raise RuntimeError(f"no daily accounting rows for trial {trial_id}")
    trial_path = Path(scratch_dir) / f"trial_{trial_id:05d}.parquet"
    pq.write_table(pa.Table.from_pylist(rows, schema=_daily_schema(scenario_id)), trial_path)
    return trial_id


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Materialize the full daily-accounting dataset for one scenario."
    )
    parser.add_argument("--scenario", required=True)
    args = parser.parse_args()
    if args.scenario not in TRIAL_COUNTS:
        raise SystemExit(f"unsupported scenario: {args.scenario}")

    trial_count = TRIAL_COUNTS[args.scenario]
    worker_count = min(MAX_WORKERS, os.cpu_count() or 1, trial_count)
    trial_ids = list(range(1, trial_count + 1))
    output_path = Path("docs/stage12/daily_accounting") / f"{args.scenario}.parquet"
    schema = _daily_schema(args.scenario)

    with TemporaryDirectory(prefix=f"stage12-{args.scenario}-") as scratch_dir:
        tasks = [(args.scenario, trial_id, scratch_dir) for trial_id in trial_ids]
        with ProcessPoolExecutor(max_workers=worker_count) as executor:
            futures = [executor.submit(_materialize_trial, task) for task in tasks]
            completed = [future.result() for future in as_completed(futures)]
        if sorted(completed) != trial_ids:
            raise RuntimeError("trial coverage failure inside materializer")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with pq.ParquetWriter(output_path, schema) as writer:
            for trial_id in trial_ids:
                trial_path = Path(scratch_dir) / f"trial_{trial_id:05d}.parquet"
                table = pq.read_table(trial_path)
                if table.num_rows == 0:
                    raise RuntimeError(f"empty trial artifact: {trial_id}")
                if table.schema.names != schema.names:
                    raise RuntimeError(f"trial schema mismatch: {trial_id}")
                writer.write_table(table)

    print(json.dumps({
        "scenario": args.scenario, "trial_count": trial_count,
        "workers": worker_count, "source_sha": SOURCE_SHA,
        "master_seed": MASTER_SEED, "parquet": str(output_path),
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
