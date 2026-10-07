from __future__ import annotations

import argparse
import dataclasses
import json
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

import constants
import daily_engine
import monte_carlo


def jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if dataclasses.is_dataclass(value):
        return jsonable(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(v) for v in value]
    return value


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(jsonable(value), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def load_official_trial_hashes(
    artifact_dir: Path,
    expected_scenario: str,
    expected_run_id: str,
    expected_source_sha: str,
) -> tuple[dict[int, str], dict[str, str]]:
    hashes: dict[int, str] = {}
    blocks: dict[str, str] = {}
    metadata_files = sorted(artifact_dir.rglob("*_metadata.json"))
    if not metadata_files:
        raise RuntimeError("No block metadata files found")
    for path in metadata_files:
        meta = json.loads(path.read_text(encoding="utf-8"))
        if meta.get("scenario") != expected_scenario:
            raise RuntimeError(f"scenario mismatch: {meta.get('scenario')!r}")
        if str(meta.get("run_id")) != expected_run_id:
            raise RuntimeError(f"run_id mismatch: {meta.get('run_id')!r}")
        if meta.get("source_sha") != expected_source_sha:
            raise RuntimeError(f"source_sha mismatch: {meta.get('source_sha')!r}")
        start = int(meta["trial_id_start"])
        end = int(meta["trial_id_end"])
        entries = meta["per_trial_sha256"]
        if len(entries) != end - start + 1:
            raise RuntimeError(f"per-trial hash count mismatch in {path}")
        blocks[f"{start}-{end}"] = meta["fingerprint_sha256"]
        for offset, digest in enumerate(entries):
            trial_id = start + offset
            if trial_id in hashes:
                raise RuntimeError(f"duplicate official trial_id {trial_id}")
            hashes[trial_id] = digest
    return hashes, blocks


def scenario_result(project: Any, scenario_id: str, collection_probability: float, recovery_rate_pct: int, trial_id: int) -> monte_carlo.TrialResult:
    return monte_carlo._trial_result_from_project(
        project,
        scenario_id=scenario_id,
        collection_probability=collection_probability,
        recovery_rate_pct=recovery_rate_pct,
        trial_id=trial_id,
    )


def daily_snapshot(project: Any, current_date: date, trial_id: int) -> dict[str, Any]:
    return {
        "date": current_date.isoformat(),
        "trial_id": trial_id,
        "Cash": int(project.project_cash),
        "Capital": int(project.capital),
        "Retained_Earnings": int(project.retained_earnings),
        "Net_Equity": int(project.capital + project.retained_earnings),
        "Active_Bikes": int(sum(1 for bike in project.bikes if bike.current_state in daily_engine.POSSESSION_STATES)),
        "Owned_Transferred_Bikes": int(sum(1 for bike in project.bikes if bike.current_state.value == "OWNED_TRANSFERRED")),
        "Pending_Claims": int(sum(1 for claim in project.guarantee_claims if claim.status.value == "PENDING")),
        "Partner1_Reinvestment_Balance": int(project.partner1_reinvestment_balance),
        "Partner2_Reinvestment_Balance": int(project.partner2_reinvestment_balance),
        "Accounts_Receivable": int(project.accounts_receivable),
        "Guarantee_Claim_Receivable": int(project.guarantee_claim_receivable),
        "Gross_Bike_Assets": int(project.gross_bike_assets),
        "Accumulated_Depreciation": int(project.accumulated_depreciation),
        "Operating_Revenue": int(project.operating_revenue),
        "Operating_Expenses": int(project.operating_expenses),
        "Operating_Net_Profit": int(project.operating_net_profit),
        "Cumulative_Project_Profit": int(project.cumulative_project_profit),
        "Final_Close_Date": None,
    }


def build_representative_payload(project: Any, result: monte_carlo.TrialResult, daily_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "summary": dataclasses.asdict(result),
        "daily": daily_rows,
        "assets": project.bikes,
        "contracts": list(project.contracts.values()),
        "tenants": project.tenants,
        "guarantors": project.guarantors,
        "guarantee_claims": project.guarantee_claims,
        "receivables": project.receivables,
        "accounting": {
            "daily_balance_checks": project.daily_balance_checks,
            "cash_rollforward": project.cash_rollforward,
            "ar_rollforward": project.ar_rollforward,
            "asset_rollforward": project.asset_rollforward,
            "equity_rollforward": project.equity_rollforward,
        },
        "partner_memo": [
            {
                "date": row["date"],
                "Partner1_Reinvestment_Balance": row["Partner1_Reinvestment_Balance"],
                "Partner2_Reinvestment_Balance": row["Partner2_Reinvestment_Balance"],
            }
            for row in daily_rows
        ],
        "final_reconciliation": {
            "final_close_date": project.final_close_date,
            "final_net_project_equity": project.final_net_project_equity,
            "final_cash": project.project_cash,
            "final_equity_from_m17": project.daily_balance_checks[-1]["Total_Equity"] if project.daily_balance_checks else None,
        },
        "final_inventory": [
            {
                "bike_id": bike.bike_id,
                "source": bike.source,
                "gross_cost": bike.gross_cost,
                "state": bike.current_state,
                "net_book_value": bike.net_book_value,
                "accumulated_depreciation": bike.accumulated_depreciation,
                "termination_count": bike.termination_count,
                "secondary_cycle_count": bike.secondary_cycle_count,
                "purchase_date": bike.purchase_date,
                "delivery_date": bike.delivery_date,
            }
            for bike in project.bikes
        ],
        "event_log": project.event_log,
        "error_log": project.error_log,
    }


def build_daily_distribution(
    rows_by_trial: dict[int, list[dict[str, Any]]],
    final_close_dates: dict[int, str | None],
) -> list[dict[str, Any]]:
    metrics = ("Cash", "Net_Equity", "Active_Bikes", "Owned_Transferred_Bikes", "Pending_Claims")
    all_dates = sorted({row["date"] for rows in rows_by_trial.values() for row in rows})
    if not all_dates:
        return []
    start = date.fromisoformat(all_dates[0])
    end = date.fromisoformat(all_dates[-1])
    expected_dates = [(start + timedelta(days=i)).isoformat() for i in range((end - start).days + 1)]
    if all_dates != expected_dates:
        raise AssertionError("daily dates contain gaps")
    by_date = {d: {m: [] for m in metrics} for d in expected_dates}
    for trial_id, rows in rows_by_trial.items():
        final_close = final_close_dates[trial_id]
        if final_close is None:
            raise AssertionError(f"missing final_close_date for trial {trial_id}")
        for row in rows:
            if final_close >= row["date"]:
                for metric in metrics:
                    by_date[row["date"]][metric].append(row[metric])
    output = []
    quantiles = (("P10", 0.10), ("P25", 0.25), ("P50", 0.50), ("P75", 0.75), ("P90", 0.90))
    for d in expected_dates:
        active_count = len(by_date[d]["Cash"])
        if active_count == 0:
            raise AssertionError(f"no active trials on {d}")
        record = {"date": d, "active_trial_count": active_count}
        for label, q in quantiles:
            for metric in metrics:
                record[f"{label}_{metric}"] = float(np.quantile(np.asarray(by_date[d][metric]), q, method="linear"))
        output.append(record)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--trial-count", required=True, type=int)
    parser.add_argument("--official-run-id", required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--artifact-dir", required=True)
    parser.add_argument("--representatives", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    scenario_id = args.scenario
    collection_probability, recovery_rate_pct = monte_carlo.parse_scenario_id(scenario_id)
    if args.trial_count not in (1, 450):
        raise RuntimeError(f"unsupported trial_count={args.trial_count}")

    official_hashes, block_fingerprints = load_official_trial_hashes(
        Path(args.artifact_dir), scenario_id, args.official_run_id, args.source_sha
    )
    if sorted(official_hashes) != list(range(1, args.trial_count + 1)):
        raise RuntimeError(f"official trial range is not 1..N for {scenario_id}")

    reps_all = json.loads(Path(args.representatives).read_text(encoding="utf-8"))
    reps = reps_all["scenarios"][scenario_id]
    representative_ids = {k: int(reps[k]) for k in ("P10", "P50", "P90", "Loss")}

    output = Path(args.output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rep_dir = output / "representatives"
    rep_dir.mkdir(parents=True, exist_ok=True)

    trial_results = []
    trial_fingerprints = {}
    rows_by_trial = {}
    final_close_dates = {}
    fingerprint_matches = 0

    for trial_id in range(1, args.trial_count + 1):
        day_rows = []

        def capture(project: Any, current_date: date) -> None:
            day_rows.append(daily_snapshot(project, current_date, trial_id))

        project = daily_engine.run_deterministic_trial(
            recovery_rate_pct=recovery_rate_pct,
            trial_id=trial_id,
            scenario_id=scenario_id,
            master_seed=constants.MASTER_SEED,
            collection_probability=collection_probability,
            on_day_end=capture,
            log_events=True,
        )
        result = scenario_result(project, scenario_id, collection_probability, recovery_rate_pct, trial_id)
        if result.final_close_date is None:
            raise AssertionError(f"trial {trial_id} has no final_close_date")
        digest = monte_carlo.fingerprint_trial_results([result])
        if digest != official_hashes[trial_id]:
            raise RuntimeError(
                f"DATASET_INTEGRITY_FAILURE: scenario={scenario_id} trial_id={trial_id} "
                f"official={official_hashes[trial_id]} reenriched={digest}"
            )
        fingerprint_matches += 1
        for row in day_rows:
            row["Final_Close_Date"] = result.final_close_date
        rows_by_trial[trial_id] = day_rows
        final_close_dates[trial_id] = result.final_close_date
        trial_fingerprints[str(trial_id)] = digest
        trial_results.append(dataclasses.asdict(result))

        for label, rep_trial_id in representative_ids.items():
            if trial_id == rep_trial_id:
                write_json(rep_dir / f"{label}.json", build_representative_payload(project, result, day_rows))

    if fingerprint_matches != args.trial_count:
        raise RuntimeError(f"per-trial fingerprint reconciliation failed: {fingerprint_matches}/{args.trial_count}")

    daily_distribution = build_daily_distribution(rows_by_trial, final_close_dates)
    pq.write_table(pa.Table.from_pylist(daily_distribution), output / "daily_distribution.parquet", compression="zstd")
    pq.write_table(pa.Table.from_pylist(trial_results), output / "trial_results.parquet", compression="zstd")

    write_json(
        output / "trial_fingerprints.json",
        {
            "scenario": scenario_id,
            "source_sha": args.source_sha,
            "run_id": args.official_run_id,
            "trial_count": args.trial_count,
            "fingerprint_algorithm": "monte_carlo.fingerprint_trial_results(single_trial_result)",
            "fingerprints": trial_fingerprints,
        },
    )

    write_json(
        output / "scenario_metadata.json",
        {
            "schema_version": "1.0",
            "scenario": scenario_id,
            "collection_probability": collection_probability,
            "recovery_rate_pct": recovery_rate_pct,
            "trial_count": args.trial_count,
            "source_sha": args.source_sha,
            "run_id": args.official_run_id,
            "official_block_fingerprints": block_fingerprints,
            "fingerprint_reconciliation": {"matched": fingerprint_matches, "expected": args.trial_count},
            "representative_trials": representative_ids,
            "daily_date_start": daily_distribution[0]["date"],
            "daily_date_end": daily_distribution[-1]["date"],
            "daily_row_count": len(daily_distribution),
            "log_events": True,
        },
    )


if __name__ == "__main__":
    main()
