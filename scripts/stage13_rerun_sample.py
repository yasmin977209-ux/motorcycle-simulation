#!/usr/bin/env python3
"""Run a user-authorized, isolated 25-trial-per-scenario cohort and materialize representative evidence.

This cohort is deliberately separate from the canonical 11,005-trial Monte Carlo dataset.
It never writes to state.json and never changes engine, RNG, reference, tests, or existing data.
"""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import gzip
import hashlib
import json
import os
import time
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

import constants
import daily_engine
import monte_carlo
import rng

CANONICAL_SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
TRIAL_IDS = tuple(range(26, 51))
ROLE_ORDER = ("P50", "P10", "P90", "Loss Case", "Max Case")


def jsonable(value: Any) -> Any:
    if dataclasses.is_dataclass(value):
        return jsonable(dataclasses.asdict(value))
    if isinstance(value, Enum):
        return jsonable(value.value)
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (tuple, list, set, frozenset)):
        return [jsonable(v) for v in value]
    if isinstance(value, np.generic):
        return jsonable(value.item())
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(jsonable(value), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def write_json_gz(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", compresslevel=6) as f:
        json.dump(jsonable(value), f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        f.write("\n")


def write_parquet(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise AssertionError(f"Refusing to write empty Parquet dataset: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist([jsonable(row) for row in rows]), path, compression="zstd")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_rows_sha256(rows: list[dict[str, Any]]) -> str:
    ordered = sorted(rows, key=lambda r: (str(r["scenario_id"]), int(r["trial_id"])))
    payload = "\n".join(
        json.dumps(jsonable(row), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        for row in ordered
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def scenario_ids() -> list[str]:
    probs = sorted(constants.COLLECTION_PROBABILITIES, reverse=True)
    recoveries = sorted(constants.GUARANTEE_RECOVERY_RATES, reverse=True)
    ids = [rng.scenario_id(probability, recovery) for probability in probs for recovery in recoveries]
    if len(ids) != 25 or len(set(ids)) != 25:
        raise AssertionError(f"Expected 25 unique canonical scenarios, found {len(ids)}")
    return ids


def run_one_summary(scenario_id: str, trial_id: int, daily_callback) -> Any:
    probability, recovery = monte_carlo.parse_scenario_id(scenario_id)
    project = daily_engine.run_deterministic_trial(
        recovery_rate_pct=recovery,
        trial_id=trial_id,
        scenario_id=scenario_id,
        master_seed=constants.MASTER_SEED,
        collection_probability=probability,
        on_day_end=daily_callback,
        log_events=False,
    )
    result = monte_carlo._trial_result_from_project(
        project,
        scenario_id=scenario_id,
        collection_probability=probability,
        recovery_rate_pct=recovery,
        trial_id=trial_id,
    )
    if not project.simulation_stopped or project.final_close_date is None:
        raise AssertionError(f"Trial did not close: {scenario_id}/{trial_id}")
    if project.final_net_project_equity != project.daily_balance_checks[-1]["Total_Equity"]:
        raise AssertionError(f"Final equity differs from closing Total_Equity: {scenario_id}/{trial_id}")
    if any(row["Balance_Difference"] != 0 for row in project.daily_balance_checks):
        raise AssertionError(f"Balance-sheet difference found: {scenario_id}/{trial_id}")
    return result


def choose_representatives(results: list[Any]) -> dict[str, int]:
    if len(results) != 25 or len({r.trial_id for r in results}) != 25:
        raise AssertionError("Representative selection requires 25 unique trial rows per scenario")
    equity = np.asarray([r.final_net_project_equity for r in results], dtype=np.float64)

    def nearest(q: float) -> int:
        target = np.quantile(equity, q, method="linear")
        return min(
            results,
            key=lambda r: (abs(r.final_net_project_equity - target), r.trial_id),
        ).trial_id

    # User-authorized semantics: Loss Case means the smallest ABSOLUTE equity,
    # and Max Case means the largest ABSOLUTE equity. Ties use the smallest trial_id.
    return {
        "P50": nearest(0.50),
        "P10": nearest(0.10),
        "P90": nearest(0.90),
        "Loss Case": min(results, key=lambda r: (abs(r.final_net_project_equity), r.trial_id)).trial_id,
        "Max Case": min(results, key=lambda r: (-abs(r.final_net_project_equity), r.trial_id)).trial_id,
    }


def representative_project(scenario_id: str, trial_id: int) -> dict[str, Any]:
    probability, recovery = monte_carlo.parse_scenario_id(scenario_id)
    daily_rows: list[dict[str, Any]] = []
    partner_memo_rows: list[dict[str, Any]] = []

    def capture_day(project, current_date) -> None:
        snapshot = monte_carlo._daily_snapshot(project, current_date, trial_id)
        snapshot["Partner1_Reinvestment_Balance"] = project.partner1_reinvestment_balance
        snapshot["Partner2_Reinvestment_Balance"] = project.partner2_reinvestment_balance
        daily_rows.append(snapshot)
        partner_memo_rows.append({
            "date": current_date.isoformat(),
            "Partner1_Reinvestment_Balance": project.partner1_reinvestment_balance,
            "Partner2_Reinvestment_Balance": project.partner2_reinvestment_balance,
        })

    project = daily_engine.run_deterministic_trial(
        recovery_rate_pct=recovery,
        trial_id=trial_id,
        scenario_id=scenario_id,
        master_seed=constants.MASTER_SEED,
        collection_probability=probability,
        on_day_end=capture_day,
        log_events=True,
    )
    result = monte_carlo._trial_result_from_project(
        project,
        scenario_id=scenario_id,
        collection_probability=probability,
        recovery_rate_pct=recovery,
        trial_id=trial_id,
    )
    if not project.simulation_stopped or project.final_close_date is None:
        raise AssertionError(f"Representative replay did not close: {scenario_id}/{trial_id}")
    if not daily_rows or daily_rows[0]["date"] != constants.PROJECT_START_DATE.isoformat():
        raise AssertionError(f"Representative daily log has wrong start: {scenario_id}/{trial_id}")
    if daily_rows[-1]["date"] != project.final_close_date.isoformat():
        raise AssertionError(f"Representative daily log has wrong end: {scenario_id}/{trial_id}")
    if any(row["Balance_Difference"] != 0 for row in project.daily_balance_checks):
        raise AssertionError(f"Representative daily balance failure: {scenario_id}/{trial_id}")
    if result.final_net_project_equity != project.daily_balance_checks[-1]["Total_Equity"]:
        raise AssertionError(f"Representative final equity mismatch: {scenario_id}/{trial_id}")

    bikes = []
    for bike in project.bikes:
        row = dataclasses.asdict(bike)
        row.pop("lifecycle_history", None)  # full events are written once to the separate event table
        bikes.append(row)
    return {
        "trial_result": dataclasses.asdict(result),
        "daily": daily_rows,
        "partner_memo": partner_memo_rows,
        "daily_balance_checks": project.daily_balance_checks,
        "cash_rollforward": project.cash_rollforward,
        "ar_rollforward": project.ar_rollforward,
        "asset_rollforward": project.asset_rollforward,
        "equity_rollforward": project.equity_rollforward,
        "bikes": bikes,
        "contracts": [dataclasses.asdict(v) for v in project.contracts.values()],
        "tenants": [dataclasses.asdict(v) for v in project.tenants],
        "guarantors": [dataclasses.asdict(v) for v in project.guarantors],
        "guarantee_claims": [dataclasses.asdict(v) for v in project.guarantee_claims],
        "receivables": [dataclasses.asdict(v) for v in project.receivables],
        "events": [dataclasses.asdict(v) for v in project.event_log],
        "partner_final": {
            "Partner1_Final_Entitlement": project.partner1_final_entitlement,
            "Partner2_Final_Entitlement": project.partner2_final_entitlement,
            "Partner1_Reinvestment_Balance": project.partner1_reinvestment_balance,
            "Partner2_Reinvestment_Balance": project.partner2_reinvestment_balance,
            "Final_Net_Project_Equity": project.final_net_project_equity,
            "Final_Cash": project.project_cash,
        },
        "audit": {
            "daily_rows": len(daily_rows),
            "daily_balance_checks": len(project.daily_balance_checks),
            "max_absolute_balance_difference": max(
                abs(row["Balance_Difference"]) for row in project.daily_balance_checks
            ),
            "event_rows": len(project.event_log),
            "contract_rows": len(project.contracts),
            "bike_rows": len(project.bikes),
            "guarantee_claim_rows": len(project.guarantee_claims),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="results_stage13/data")
    parser.add_argument("--source-sha", default=CANONICAL_SOURCE_SHA)
    args = parser.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    scenarios = scenario_ids()
    all_results: list[Any] = []
    daily_distribution: list[dict[str, Any]] = []
    by_scenario: dict[str, list[Any]] = {}
    per_scenario_runtime: dict[str, float] = {}
    t0 = time.perf_counter()

    for scenario_id in scenarios:
        start = time.perf_counter()
        rows_by_trial: dict[int, list[dict[str, Any]]] = {}
        results: list[Any] = []
        for trial_id in TRIAL_IDS:
            daily_rows: list[dict[str, Any]] = []

            def capture_day(project, current_date, target=daily_rows, tid=trial_id) -> None:
                target.append(monte_carlo._daily_snapshot(project, current_date, tid))

            result = run_one_summary(scenario_id, trial_id, capture_day)
            results.append(result)
            rows_by_trial[trial_id] = daily_rows
        if len(results) != 25 or set(rows_by_trial) != set(TRIAL_IDS):
            raise AssertionError(f"Trial coverage failure for {scenario_id}")
        daily_distribution.extend(
            {**row, "scenario_id": scenario_id}
            for row in monte_carlo.build_daily_distribution(results, rows_by_trial)
        )
        by_scenario[scenario_id] = results
        all_results.extend(results)
        per_scenario_runtime[scenario_id] = round(time.perf_counter() - start, 6)

    result_rows = [dataclasses.asdict(r) for r in all_results]
    expected = {(s, tid) for s in scenarios for tid in TRIAL_IDS}
    actual = {(r["scenario_id"], int(r["trial_id"])) for r in result_rows}
    if actual != expected or len(result_rows) != 625:
        raise AssertionError("Expected exactly 625 unique (scenario_id, trial_id) results")
    if any(r["final_net_project_equity"] is None or r["final_cash"] is None for r in result_rows):
        raise AssertionError("Null final metric in trial output")

    selections = {s: choose_representatives(by_scenario[s]) for s in scenarios}
    assignment_rows: list[dict[str, Any]] = []
    for scenario_id in scenarios:
        results_map = {r.trial_id: r for r in by_scenario[scenario_id]}
        for role in ROLE_ORDER:
            trial_id = selections[scenario_id][role]
            result = results_map[trial_id]
            assignment_rows.append({
                "scenario_id": scenario_id,
                "role": role,
                "trial_id": trial_id,
                "Final_Net_Project_Equity": result.final_net_project_equity,
                "Absolute_Final_Net_Project_Equity": abs(result.final_net_project_equity),
                "Final_Cash": result.final_cash,
                "Partner1_Final_Entitlement": result.partner1_final_entitlement,
                "Partner2_Final_Entitlement": result.partner2_final_entitlement,
                "final_close_date": result.final_close_date,
                "selection_sample_size": 25,
                "quantile_method": "numpy.quantile(method='linear')",
                "tie_break": "smallest trial_id",
            })

    details_dir = out / "representative_details"
    representative_audits: list[dict[str, Any]] = []
    detail_count = 0
    for scenario_id in scenarios:
        original_by_id = {r.trial_id: r for r in by_scenario[scenario_id]}
        unique_selected_ids = sorted(set(selections[scenario_id].values()))
        for trial_id in unique_selected_ids:
            detail = representative_project(scenario_id, trial_id)
            detail_result = detail["trial_result"]
            original_result = dataclasses.asdict(original_by_id[trial_id])
            if jsonable(detail_result) != jsonable(original_result):
                raise AssertionError(f"Representative replay differs from initial result: {scenario_id}/{trial_id}")
            roles = [role for role in ROLE_ORDER if selections[scenario_id][role] == trial_id]
            detail["roles"] = roles
            detail["scenario_id"] = scenario_id
            detail["trial_id"] = trial_id
            detail_path = details_dir / scenario_id / f"trial_{trial_id:06d}.json.gz"
            write_json_gz(detail_path, detail)
            detail_count += 1
            representative_audits.append({
                "scenario_id": scenario_id,
                "trial_id": trial_id,
                "roles": roles,
                "result_matches_initial_pass": True,
                **detail["audit"],
            })

    write_parquet(out / "trial_results.parquet", result_rows)
    write_parquet(out / "daily_distribution.parquet", daily_distribution)
    write_parquet(out / "representative_assignments.parquet", assignment_rows)

    public_constants = {
        name: getattr(constants, name)
        for name in dir(constants)
        if name.isupper() and not name.startswith("_")
    }
    write_json(out / "constants.json", public_constants)
    write_json(out / "representative_audit.json", {
        "detail_unique_trial_count": detail_count,
        "representatives": representative_audits,
        "all_representative_results_reproduced_exactly": all(
            row["result_matches_initial_pass"] for row in representative_audits
        ),
        "all_representative_balance_differences_zero": all(
            row["max_absolute_balance_difference"] == 0 for row in representative_audits
        ),
    })

    source_sha = args.source_sha
    identity_payload = {
        "cohort_id": "STAGE13_SAMPLE_TRIAL_IDS_26_50_V2",
        "cohort_status": "SEPARATE_DIAGNOSTIC_COHORT_TRIAL_IDS_26_50_NOT_CANONICAL_11005_TRIAL_DATASET",
        "source_sha": source_sha,
        "run_head_sha": os.environ.get("GITHUB_SHA"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT"),
        "master_seed": constants.MASTER_SEED,
        "rng_source_sha256": sha256_file(Path("rng.py")),
        "sampling": {"trial_ids": list(TRIAL_IDS), "trials_per_scenario": 25},
        "scenarios": scenarios,
        "scenario_count": len(scenarios),
        "trial_result_count": len(result_rows),
        "unique_scenario_trial_pairs": len(actual),
        "trial_results_fingerprint_sha256": canonical_rows_sha256(result_rows),
        "daily_distribution_rows": len(daily_distribution),
        "representative_role_assignments": len(assignment_rows),
        "representative_unique_detail_trials": detail_count,
        "canonical_11005_dataset_fingerprint_sha256": "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44",
        "canonical_dataset_relation": (
            "This is a new, explicitly requested 25-ID per-scenario cohort. It is not merged with, "
            "not a replacement for, and does not inherit Gate A/B acceptance from the canonical 11,005 trials."
        ),
    }
    identity_payload["total_elapsed_seconds"] = round(time.perf_counter() - t0, 6)
    identity_payload["per_scenario_elapsed_seconds"] = per_scenario_runtime
    write_json(out / "dataset_identity.json", identity_payload)

    gate_definition = {
        "gate_id": "STAGE13_20_POINT_PARQUET_VS_STATS_V2",
        "status": "DEFINED_NOT_EXECUTED",
        "interpretation": "20 points per scenario, 500 exact comparisons across the 25 scenarios",
        "fields": {
            "Final_Net_Project_Equity": "final_net_project_equity",
            "Partner1_Final_Entitlement": "partner1_final_entitlement",
            "Partner2_Final_Entitlement": "partner2_final_entitlement",
            "Final_Cash": "final_cash",
        },
        "statistics_per_field": ["MIN", "P10", "P50", "P90", "MAX"],
        "quantile_method": "numpy.quantile(values, q, method='linear')",
        "minimum_and_maximum": "Exact observed min and max, no interpolation",
        "expected_comparisons_per_scenario": 20,
        "expected_scenario_count": 25,
        "expected_comparisons_total": 500,
        "acceptance": "All 500 numeric Parquet-to-exported-XLSX _STATS values must be exactly equal after independent recomputation.",
        "cohort_scope": "trial_ids 26..50 for each scenario; separate from canonical 11,005-trial dataset and the interrupted IDs 1..25 attempt",
        "note": "This consistency gate is not Monte Carlo statistical stability Gate A/B and cannot claim their PASS.",
    }
    write_json(out / "20point_gate_definition.json", gate_definition)

    file_hashes = {}
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "artifact_manifest.json":
            file_hashes[str(path.relative_to(out))] = sha256_file(path)
    write_json(out / "artifact_manifest.json", {
        "manifest_version": 1,
        "file_hashes_sha256": file_hashes,
        "file_count_excluding_manifest": len(file_hashes),
        "trial_results_fingerprint_sha256": identity_payload["trial_results_fingerprint_sha256"],
    })

    print(json.dumps({
        "RUN_ID": os.environ.get("GITHUB_RUN_ID"),
        "SOURCE_SHA": source_sha,
        "RUN_HEAD_SHA": os.environ.get("GITHUB_SHA"),
        "SCENARIOS": len(scenarios),
        "TRIALS_PER_SCENARIO": 25,
        "TOTAL_TRIAL_RESULTS": len(result_rows),
        "DAILY_DISTRIBUTION_ROWS": len(daily_distribution),
        "REPRESENTATIVE_ROLE_ASSIGNMENTS": len(assignment_rows),
        "REPRESENTATIVE_UNIQUE_DETAIL_TRIALS": detail_count,
        "REPRESENTATIVE_EXACT_REPLAY_MATCHES": len(representative_audits),
        "REPRESENTATIVE_BALANCE_FAILURES": sum(
            row["max_absolute_balance_difference"] != 0 for row in representative_audits
        ),
        "TRIAL_RESULTS_FINGERPRINT_SHA256": identity_payload["trial_results_fingerprint_sha256"],
        "ELAPSED_SECONDS": identity_payload["total_elapsed_seconds"],
        "STATUS": "DATA_GENERATED_GATE_PENDING_LOCAL_WORKBOOK_EXPORT_AND_INDEPENDENT_500_POINT_CHECK",
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
