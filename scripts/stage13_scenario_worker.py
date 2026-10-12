#!/usr/bin/env python3
"""Materialize one isolated Stage 13 scenario; checkpoints are atomic and identity-bound."""
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import gzip
import hashlib
import json
import os
import shutil
import time
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq

import constants
import monte_carlo
import rng
import stage13_rerun_sample as base

SOURCE_SHA = base.CANONICAL_SOURCE_SHA
COHORT_ID = "STAGE13_SAMPLE_TRIAL_IDS_26_50_V2"
SCHEMA_VERSION = "stage13-scenario-cohort-v2"
TRIAL_IDS = tuple(range(26, 51))
ROLE_FILES = {
    "P10": "P10",
    "P50": "P50",
    "P90": "P90",
    "Loss Case": "Loss",
    "Max Case": "Max Case",
}


def jsonable(value: Any) -> Any:
    return base.jsonable(value)


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        jsonable(value), ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), default=str,
    ).encode("utf-8")


def stable_sha(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def file_sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_write_checkpoint(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=6) as f:
        json.dump(jsonable(payload), f, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        f.write("\n")
    os.replace(tmp, path)


def read_checkpoint(path: Path, expected_identity: dict[str, Any]) -> tuple[Any, list[dict[str, Any]]]:
    try:
        with gzip.open(path, "rt", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as exc:
        raise RuntimeError(f"CHECKPOINT_UNREADABLE: {path.name}: {exc}") from exc
    identity = payload.get("identity")
    if identity != expected_identity:
        raise RuntimeError(
            f"CHECKPOINT_IDENTITY_MISMATCH: {path.name}; refusing reuse"
        )
    result_payload = payload.get("trial_result")
    daily_rows = payload.get("daily_rows")
    checksums = payload.get("checksums", {})
    if not isinstance(result_payload, dict) or not isinstance(daily_rows, list) or not daily_rows:
        raise RuntimeError(f"CHECKPOINT_PAYLOAD_INCOMPLETE: {path.name}")
    if checksums.get("trial_result_sha256") != stable_sha(result_payload):
        raise RuntimeError(f"CHECKPOINT_RESULT_SHA_MISMATCH: {path.name}")
    if checksums.get("daily_rows_sha256") != stable_sha(daily_rows):
        raise RuntimeError(f"CHECKPOINT_DAILY_SHA_MISMATCH: {path.name}")
    computed_artifact_fingerprint = hashlib.sha256(
        f"{checksums.get('trial_result_sha256')}|{checksums.get('daily_rows_sha256')}".encode("utf-8")
    ).hexdigest()
    if checksums.get("artifact_fingerprint_sha256") != computed_artifact_fingerprint:
        raise RuntimeError(f"CHECKPOINT_ARTIFACT_FINGERPRINT_MISMATCH: {path.name}")
    result = monte_carlo.TrialResult(**result_payload)
    tid = int(result.trial_id)
    if tid != int(identity["trial_id"]) or tid not in TRIAL_IDS:
        raise RuntimeError(f"CHECKPOINT_TRIAL_ID_MISMATCH: {path.name}")
    dates = [row["date"] for row in daily_rows]
    if dates[0] != constants.PROJECT_START_DATE.isoformat():
        raise RuntimeError(f"CHECKPOINT_START_DATE_MISMATCH: {path.name}")
    if dates[-1] != result.final_close_date:
        raise RuntimeError(f"CHECKPOINT_CLOSE_DATE_MISMATCH: {path.name}")
    if len(dates) != (dt.date.fromisoformat(dates[-1]) - dt.date.fromisoformat(dates[0])).days + 1:
        raise RuntimeError(f"CHECKPOINT_DAILY_COVERAGE_MISMATCH: {path.name}")
    if len(set(dates)) != len(dates) or any(
        dt.date.fromisoformat(dates[i + 1]) != dt.date.fromisoformat(dates[i]) + dt.timedelta(days=1)
        for i in range(len(dates) - 1)
    ):
        raise RuntimeError(f"CHECKPOINT_DAILY_SEQUENCE_MISMATCH: {path.name}")
    return result, daily_rows


def identity_for(scenario_id: str, trial_id: int, head_sha: str, run_id: str, rng_sha: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "cohort_id": COHORT_ID,
        "scenario_id": scenario_id,
        "trial_id": trial_id,
        "source_sha": SOURCE_SHA,
        "implementation_head_sha": head_sha,
        "workflow_run_id": run_id,
        "master_seed": int(constants.MASTER_SEED),
        "rng_source_sha256": rng_sha,
        "trial_ids_for_scenario": list(TRIAL_IDS),
        "sampling": "fresh, one-based deterministic keys 26..50; replaces no canonical trials",
        "stability": "diagnostic 25-trial cohort; no Gate A/B statistical status inferred",
    }


def builder_payload(detail: dict[str, Any], scenario_id: str, trial_id: int) -> dict[str, Any]:
    summary = dict(detail["trial_result"])
    summary["trial_id"] = int(trial_id)
    inventory = []
    for bike in detail["bikes"]:
        inventory.append({
            "bike_id": bike["bike_id"],
            "source": bike.get("source"),
            "purchase_date": bike.get("purchase_date"),
            "delivery_date": bike.get("delivery_date"),
            "gross_cost": bike.get("gross_cost"),
            "accumulated_depreciation": bike.get("accumulated_depreciation"),
            "net_book_value": bike.get("net_book_value"),
            "termination_count": bike.get("termination_count"),
            "secondary_cycle_count": bike.get("secondary_cycle_count"),
            "state": bike.get("current_state"),
        })
    accounting = {
        "daily_balance_checks": detail["daily_balance_checks"],
        "cash_rollforward": detail["cash_rollforward"],
        "ar_rollforward": detail["ar_rollforward"],
        "asset_rollforward": detail["asset_rollforward"],
        "equity_rollforward": detail["equity_rollforward"],
    }
    final_reconciliation = {
        "trial_id": int(trial_id),
        "scenario_id": scenario_id,
        "Final_Net_Project_Equity": summary["final_net_project_equity"],
        "Partner1_Final_Entitlement": summary["partner1_final_entitlement"],
        "Partner2_Final_Entitlement": summary["partner2_final_entitlement"],
        "Final_Cash": summary["final_cash"],
    }
    return {
        "scenario_id": scenario_id,
        "trial_id": int(trial_id),
        "summary": summary,
        "daily": detail["daily"],
        "accounting": accounting,
        "final_inventory": inventory,
        "partner_memo": detail.get("partner_memo", []),
        "final_reconciliation": final_reconciliation,
        "guarantee_claims": detail.get("guarantee_claims", []),
        "contracts": detail.get("contracts", []),
        "tenants": detail.get("tenants", []),
        "guarantors": detail.get("guarantors", []),
        "receivables": detail.get("receivables", []),
        "events": detail.get("events", []),
        "partner_final": detail.get("partner_final", {}),
        "audit": detail.get("audit", {}),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--output-root", default="results_stage13/scenarios")
    parser.add_argument("--checkpoint-root", default="results_stage13/checkpoints")
    parser.add_argument("--resume-dir", default="results_stage13/previous-checkpoints")
    parser.add_argument("--source-sha", default=SOURCE_SHA)
    args = parser.parse_args()

    scenario_id = args.scenario
    if scenario_id not in base.scenario_ids():
        raise SystemExit(f"UNSUPPORTED_SCENARIO: {scenario_id}")
    if args.source_sha != SOURCE_SHA:
        raise SystemExit(f"SOURCE_SHA_MISMATCH: expected {SOURCE_SHA}, received {args.source_sha}")

    out = Path(args.output_root) / scenario_id
    checkpoint_dir = Path(args.checkpoint_root) / scenario_id
    resume_dir = Path(args.resume_dir)
    out.mkdir(parents=True, exist_ok=True)
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    head_sha = os.environ.get("GITHUB_SHA", "LOCAL_UNPINNED")
    run_id = os.environ.get("GITHUB_RUN_ID", "LOCAL_UNPINNED")
    rng_sha = file_sha(Path("rng.py"))
    scenario_start = time.perf_counter()

    results_by_id: dict[int, Any] = {}
    daily_by_trial: dict[int, list[dict[str, Any]]] = {}
    checkpoint_sources = []
    candidates: dict[int, Path] = {}
    for root in (resume_dir, checkpoint_dir):
        if root.exists():
            for p in root.glob("trial_*.json.gz"):
                filename = p.name
                if not filename.endswith(".json.gz") or not filename.startswith("trial_"):
                    raise RuntimeError(f"INVALID_CHECKPOINT_NAME: {p.name}")
                match = filename[len("trial_"):-len(".json.gz")]
                try:
                    tid = int(match)
                except ValueError as exc:
                    raise RuntimeError(f"INVALID_CHECKPOINT_NAME: {p.name}") from exc
                if tid not in TRIAL_IDS:
                    raise RuntimeError(f"CHECKPOINT_TRIAL_OUT_OF_COHORT: {p.name}")
                if tid in candidates and file_sha(candidates[tid]) != file_sha(p):
                    raise RuntimeError(f"CHECKPOINT_CONFLICT_FOR_TRIAL: {tid}")
                candidates[tid] = p

    for trial_id, path in sorted(candidates.items()):
        expected_identity = identity_for(scenario_id, trial_id, head_sha, run_id, rng_sha)
        result, rows = read_checkpoint(path, expected_identity)
        destination = checkpoint_dir / path.name
        if path.resolve() != destination.resolve():
            shutil.copy2(path, destination)
        results_by_id[trial_id] = result
        daily_by_trial[trial_id] = rows
        checkpoint_sources.append({
            "trial_id": trial_id,
            "sha256": file_sha(destination),
            "reused_from_checkpoint": True,
        })

    for trial_id in TRIAL_IDS:
        if trial_id in results_by_id:
            print(json.dumps({
                "event": "TRIAL_CHECKPOINT_REUSED",
                "scenario_id": scenario_id,
                "trial_id": trial_id,
                "cohort_id": COHORT_ID,
            }, sort_keys=True), flush=True)
            continue

        rows: list[dict[str, Any]] = []
        def capture_day(project, current_date, target=rows, tid=trial_id) -> None:
            target.append(monte_carlo._daily_snapshot(project, current_date, tid))

        result = base.run_one_summary(scenario_id, trial_id, capture_day)
        if len(rows) == 0:
            raise RuntimeError(f"TRIAL_HAS_NO_DAILY_ROWS: {scenario_id}/{trial_id}")
        if rows[0]["date"] != constants.PROJECT_START_DATE.isoformat():
            raise RuntimeError(f"TRIAL_START_DATE_MISMATCH: {scenario_id}/{trial_id}")
        if rows[-1]["date"] != result.final_close_date:
            raise RuntimeError(f"TRIAL_CLOSE_DATE_MISMATCH: {scenario_id}/{trial_id}")
        expected_days = (
            dt.date.fromisoformat(rows[-1]["date"]) -
            dt.date.fromisoformat(rows[0]["date"])
        ).days + 1
        if len(rows) != expected_days or len({r["date"] for r in rows}) != len(rows):
            raise RuntimeError(f"TRIAL_DAILY_COVERAGE_FAILURE: {scenario_id}/{trial_id}")
        results_by_id[trial_id] = result
        daily_by_trial[trial_id] = rows
        identity = identity_for(scenario_id, trial_id, head_sha, run_id, rng_sha)
        result_payload = dataclasses.asdict(result)
        checkpoint_payload = {
            "identity": identity,
            "trial_result": result_payload,
            "daily_rows": rows,
            "checksums": {
                "trial_result_sha256": stable_sha(result_payload),
                "daily_rows_sha256": stable_sha(rows),
                "artifact_fingerprint_sha256": hashlib.sha256(
                    f"{stable_sha(result_payload)}|{stable_sha(rows)}".encode("utf-8")
                ).hexdigest(),
            },
        }
        checkpoint_path = checkpoint_dir / f"trial_{trial_id:06d}.json.gz"
        atomic_write_checkpoint(checkpoint_path, checkpoint_payload)
        print(json.dumps({
            "event": "TRIAL_CHECKPOINT_SAVED",
            "scenario_id": scenario_id,
            "trial_id": trial_id,
            "trial_result_sha256": checkpoint_payload["checksums"]["trial_result_sha256"],
            "daily_rows": len(rows),
            "checkpoint_sha256": file_sha(checkpoint_path),
        }, sort_keys=True), flush=True)

    if set(results_by_id) != set(TRIAL_IDS) or set(daily_by_trial) != set(TRIAL_IDS):
        raise RuntimeError("SCENARIO_TRIAL_COVERAGE_FAILURE")
    results = [results_by_id[tid] for tid in TRIAL_IDS]
    result_rows = [dataclasses.asdict(r) for r in results]
    if len({(r["scenario_id"], int(r["trial_id"])) for r in result_rows}) != 25:
        raise RuntimeError("SCENARIO_DUPLICATE_TRIAL_KEYS")
    if any(r["final_net_project_equity"] is None or r["final_cash"] is None for r in result_rows):
        raise RuntimeError("SCENARIO_NULL_FINAL_METRIC")

    daily_distribution = [
        {**row, "scenario_id": scenario_id}
        for row in monte_carlo.build_daily_distribution(results, daily_by_trial)
    ]
    selections = base.choose_representatives(results)
    selection_rows = []
    by_id = {result.trial_id: result for result in results}
    for role in base.ROLE_ORDER:
        tid = int(selections[role])
        selected = by_id[tid]
        selection_rows.append({
            "scenario_id": scenario_id,
            "role": role,
            "trial_id": tid,
            "Final_Net_Project_Equity": selected.final_net_project_equity,
            "Absolute_Final_Net_Project_Equity": abs(selected.final_net_project_equity),
            "Final_Cash": selected.final_cash,
            "Partner1_Final_Entitlement": selected.partner1_final_entitlement,
            "Partner2_Final_Entitlement": selected.partner2_final_entitlement,
            "final_close_date": selected.final_close_date,
            "selection_sample_size": 25,
            "quantile_method": "numpy.quantile(method='linear')",
            "tie_break": "smallest trial_id",
        })

    reps_dir = out / "representatives"
    reps_dir.mkdir(parents=True, exist_ok=True)
    audit_rows = []
    payload_by_tid: dict[int, dict[str, Any]] = {}
    unique_selected_ids = sorted(set(int(v) for v in selections.values()))
    for tid in unique_selected_ids:
        detail = base.representative_project(scenario_id, tid)
        if jsonable(detail["trial_result"]) != jsonable(dataclasses.asdict(by_id[tid])):
            raise RuntimeError(f"REPRESENTATIVE_REPLAY_MISMATCH: {scenario_id}/{tid}")
        if detail["audit"]["max_absolute_balance_difference"] != 0:
            raise RuntimeError(f"REPRESENTATIVE_BALANCE_FAILURE: {scenario_id}/{tid}")
        payload_by_tid[tid] = builder_payload(detail, scenario_id, tid)
        audit_rows.append({
            "scenario_id": scenario_id,
            "trial_id": tid,
            "roles": [role for role in base.ROLE_ORDER if int(selections[role]) == tid],
            "result_matches_initial_pass": True,
            **detail["audit"],
        })
    for role in base.ROLE_ORDER:
        tid = int(selections[role])
        base.write_json(reps_dir / f"{ROLE_FILES[role]}.json", payload_by_tid[tid])

    base.write_parquet(out / "trial_results.parquet", result_rows)
    base.write_parquet(out / "daily_distribution.parquet", daily_distribution)
    base.write_parquet(out / "representative_assignments.parquet", selection_rows)
    base.write_json(out / "representative_audit.json", {
        "schema_version": SCHEMA_VERSION,
        "scenario_id": scenario_id,
        "detail_unique_trial_count": len(unique_selected_ids),
        "representatives": audit_rows,
        "all_representative_results_reproduced_exactly": all(
            row["result_matches_initial_pass"] for row in audit_rows
        ),
        "all_representative_balance_differences_zero": all(
            row["max_absolute_balance_difference"] == 0 for row in audit_rows
        ),
    })

    public_constants = {
        name: getattr(constants, name)
        for name in dir(constants)
        if name.isupper() and not name.startswith("_")
    }
    base.write_json(out / "constants.json", public_constants)
    identity = {
        "schema_version": SCHEMA_VERSION,
        "cohort_id": COHORT_ID,
        "status": "SCENARIO_COMPLETE",
        "scenario_id": scenario_id,
        "source_sha": SOURCE_SHA,
        "implementation_head_sha": head_sha,
        "workflow_run_id": run_id,
        "master_seed": int(constants.MASTER_SEED),
        "rng_source_sha256": rng_sha,
        "trial_ids": list(TRIAL_IDS),
        "trial_count": len(result_rows),
        "daily_distribution_rows": len(daily_distribution),
        "representative_role_assignments": len(selection_rows),
        "representative_unique_detail_trials": len(unique_selected_ids),
        "trial_results_fingerprint_sha256": base.canonical_rows_sha256(result_rows),
        "representative_roles": {role: int(tid) for role, tid in selections.items()},
        "checkpoint_reused_trial_ids": sorted(
            tid for tid, _ in ((int(item["trial_id"]), item) for item in checkpoint_sources)
        ),
        "checkpoint_sha256": {
            path.name: file_sha(path)
            for path in sorted(checkpoint_dir.glob("trial_*.json.gz"))
        },
        "elapsed_seconds": round(time.perf_counter() - scenario_start, 6),
        "statistical_status": "DIAGNOSTIC_ONLY; no Gate A/B PASS claimed",
    }
    base.write_json(out / "dataset_identity.json", identity)
    out_manifest = {}
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name != "artifact_manifest.json":
            out_manifest[str(path.relative_to(out))] = file_sha(path)
    base.write_json(out / "artifact_manifest.json", {
        "manifest_version": 2,
        "scenario_id": scenario_id,
        "cohort_id": COHORT_ID,
        "file_hashes_sha256": out_manifest,
        "file_count_excluding_manifest": len(out_manifest),
        "trial_results_fingerprint_sha256": identity["trial_results_fingerprint_sha256"],
    })
    print(json.dumps({
        "SCENARIO": scenario_id,
        "COHORT_ID": COHORT_ID,
        "TRIAL_IDS": list(TRIAL_IDS),
        "TRIAL_RESULTS": len(result_rows),
        "DAILY_DISTRIBUTION_ROWS": len(daily_distribution),
        "REPRESENTATIVE_ROLES": len(selection_rows),
        "UNIQUE_REPRESENTATIVE_REPLAYS": len(unique_selected_ids),
        "CHECKPOINT_REUSED": identity["checkpoint_reused_trial_ids"],
        "TRIAL_RESULTS_FINGERPRINT_SHA256": identity["trial_results_fingerprint_sha256"],
        "ELAPSED_SECONDS": identity["elapsed_seconds"],
        "STATUS": "SCENARIO_COMPLETE",
    }, ensure_ascii=False, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
