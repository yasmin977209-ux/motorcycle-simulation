from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
from typing import Any
import pyarrow.parquet as pq
from scripts import s6_first_checkpoint as s6

SOURCE_RUN_ID = "40731224990"
SOURCE_RUN_HEAD_SHA = "a23ba71f48487f3ebead99bc30039b14ef9b7609"
SOURCE_SHA = "da1a9ea9b5cd789c944de3f07b08395bb67c49e7"
COHORT_ID = "s6-v23-da1a9ea9"
MASTER_SEED = 20270101
CHECKPOINT_N = 2400
EXPECTED_DAILY_ROWS = 98_323_918
SCENARIOS = sorted(s6.stochastic_scenario_ids())
PARTIAL_EQUITY_FIELDS = ("Cash", "Capital", "Retained_Earnings", "Net_Equity")
FULL_BALANCE_FIELDS = (
    "Accounts_Receivable", "Guarantee_Claim_Receivable",
    "Gross_Bike_Assets", "Accumulated_Depreciation", "Total_Assets",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def capture_source_api(root: Path) -> dict[str, Any]:
    api = root / "source-api"
    paths = {
        "run": api / "source_run.json",
        "jobs": api / "source_jobs.json",
        "artifacts": api / "source_artifacts.json",
    }
    if not all(path.is_file() for path in paths.values()):
        raise RuntimeError("SOURCE_RUN_API_CAPTURE_MISSING")
    run = json.loads(paths["run"].read_text(encoding="utf-8"))
    jobs = json.loads(paths["jobs"].read_text(encoding="utf-8")).get("jobs", [])
    artifacts = json.loads(paths["artifacts"].read_text(encoding="utf-8")).get("artifacts", [])
    expected_run = {
        "id": int(SOURCE_RUN_ID), "run_attempt": 1, "status": "completed",
        "conclusion": "failure", "head_sha": SOURCE_RUN_HEAD_SHA,
        "head_branch": "tmp/s6-aggregate-contract-fix-20261027",
        "path": ".github/workflows/s6-n600-checkpoint.yml",
    }
    for key, expected in expected_run.items():
        if run.get(key) != expected:
            raise RuntimeError(f"SOURCE_RUN_IDENTITY_MISMATCH:{key}:{run.get(key)}")
    expected_names = {
        f"s6-n2400-{scenario.replace('_G100', '-G100')}-{SOURCE_RUN_ID}"
        for scenario in SCENARIOS
    }
    artifact_by_name = {str(item.get("name")): item for item in artifacts}
    if len(artifacts) != 20 or set(artifact_by_name) != expected_names:
        raise RuntimeError("SOURCE_RUN_ARTIFACT_SET_INVALID")
    for name, item in artifact_by_name.items():
        if item.get("expired") is True or not item.get("digest") or int(item.get("size_in_bytes", 0)) <= 0:
            raise RuntimeError(f"SOURCE_RUN_ARTIFACT_METADATA_INVALID:{name}")
    job_by_name = {str(item.get("name")): item for item in jobs}
    scenario_jobs = {}
    for scenario in SCENARIOS:
        collection, recovery = scenario.split("_")
        job_name = f"S6 N2400 G100 base — {collection}" if recovery == "G100" else f"S6 N2400 {scenario}"
        job = job_by_name.get(job_name)
        if not job or job.get("status") != "completed" or job.get("conclusion") != "success":
            raise RuntimeError(f"SOURCE_SCENARIO_JOB_NOT_SUCCESS:{scenario}")
        scenario_jobs[scenario] = {"job_id": int(job["id"]), "name": job_name, "conclusion": job.get("conclusion")}
    return {
        "status": "VERIFIED_SCENARIO_JOBS_ARTIFACTS_PARENT_RUN_FAILED",
        "source_run_id": int(SOURCE_RUN_ID), "source_run_head_sha": SOURCE_RUN_HEAD_SHA,
        "parent_conclusion": run.get("conclusion"), "scenario_job_count": len(scenario_jobs),
        "scenario_jobs": scenario_jobs,
        "scenario_artifacts": {
            name: {"artifact_id": int(item["id"]), "size_bytes": int(item["size_in_bytes"]),
                   "digest": item["digest"], "expired": item.get("expired")}
            for name, item in sorted(artifact_by_name.items())
        },
        "api_capture_sha256": {key: sha256_file(path) for key, path in paths.items()},
    }


def run_audit(root: Path) -> dict[str, Any]:
    manifest_paths = sorted(
        (root / "scenarios").rglob("scenario_manifest.json"),
        key=lambda p: str(json.loads(p.read_text(encoding="utf-8")).get("scenario_id", "")),
    )
    if len(manifest_paths) != 20:
        raise RuntimeError(f"SCENARIO_MANIFEST_COUNT_INVALID:{len(manifest_paths)}")
    provenance = capture_source_api(root)
    expected_trial_ids = set(range(1, CHECKPOINT_N + 1))
    scenario_results: dict[str, Any] = {}
    total_rows = total_checked = total_mismatch = total_bad_integer = 0
    total_order_violation = total_duplicate_date = 0
    first_mismatches: list[dict[str, Any]] = []

    for manifest_path in manifest_paths:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        scenario = str(manifest.get("scenario_id", ""))
        if scenario not in SCENARIOS or scenario in scenario_results:
            raise RuntimeError(f"SCENARIO_ID_DUPLICATED_OR_UNKNOWN:{scenario}")
        expected_identity = {
            "schema_version": "s6-first-checkpoint-v1", "schema_version_model": "v2.3",
            "status": "EXECUTED", "exit_code": 0,
            "source_sha": SOURCE_SHA, "cohort_id": COHORT_ID, "master_seed": MASTER_SEED,
            "run_id": SOURCE_RUN_ID, "run_attempt": 1,
            "trial_count": CHECKPOINT_N, "trial_id_start": 1, "trial_id_end": CHECKPOINT_N,
            "git_commit": SOURCE_RUN_HEAD_SHA,
        }
        for key, expected in expected_identity.items():
            if manifest.get(key) != expected:
                raise RuntimeError(f"SCENARIO_MANIFEST_IDENTITY_MISMATCH:{scenario}:{key}:{manifest.get(key)}")
        snapshot_path = manifest_path.parent / "daily_snapshots.parquet"
        expected_file = manifest.get("files", {}).get("daily_snapshots.parquet")
        if not expected_file or not snapshot_path.is_file():
            raise RuntimeError(f"DAILY_SNAPSHOT_FILE_MISSING:{scenario}")
        digest = sha256_file(snapshot_path)
        size = snapshot_path.stat().st_size
        if digest != expected_file.get("sha256") or size != expected_file.get("size_bytes"):
            raise RuntimeError(f"DAILY_SNAPSHOT_HASH_OR_SIZE_MISMATCH:{scenario}")
        parquet = pq.ParquetFile(snapshot_path)
        columns = set(parquet.schema_arrow.names)
        missing_partial = sorted(set(PARTIAL_EQUITY_FIELDS) - columns)
        missing_full = sorted(set(FULL_BALANCE_FIELDS) - columns)
        if missing_partial:
            raise RuntimeError(f"PARTIAL_EQUITY_FIELDS_MISSING:{scenario}:{missing_partial}")

        seen_trials: set[int] = set()
        trial_row_counts: dict[int, int] = {}
        rows = checked = mismatches = bad_integer = order_violations = duplicate_dates = 0
        previous_trial: int | None = None
        previous_date: str | None = None
        for batch in parquet.iter_batches(batch_size=8192):
            for row in batch.to_pylist():
                rows += 1
                if (row.get("schema_version") != "v2.3" or row.get("source_sha") != SOURCE_SHA
                    or row.get("cohort_id") != COHORT_ID or str(row.get("scenario_id")) != scenario):
                    raise RuntimeError(f"DAILY_SNAPSHOT_ROW_IDENTITY_MISMATCH:{scenario}")
                trial_id = int(row["trial_id"])
                if trial_id not in expected_trial_ids:
                    raise RuntimeError(f"DAILY_SNAPSHOT_TRIAL_ID_OUT_OF_RANGE:{scenario}:{trial_id}")
                date_text = str(row.get("date", ""))
                if previous_trial is not None and trial_id < previous_trial:
                    order_violations += 1
                if trial_id != previous_trial:
                    if trial_id in seen_trials:
                        order_violations += 1
                    seen_trials.add(trial_id)
                    previous_date = None
                if not date_text:
                    order_violations += 1
                elif previous_date is not None and date_text <= previous_date:
                    order_violations += 1
                    if date_text == previous_date:
                        duplicate_dates += 1
                    if len(first_mismatches) < 25:
                        first_mismatches.append({"scenario_id": scenario, "trial_id": trial_id,
                            "date": date_text, "reason": "DAILY_DATE_NOT_STRICTLY_INCREASING"})
                previous_trial, previous_date = trial_id, date_text
                trial_row_counts[trial_id] = trial_row_counts.get(trial_id, 0) + 1
                values = [row.get(key) for key in PARTIAL_EQUITY_FIELDS]
                if any(type(value) is not int for value in values):
                    bad_integer += 1
                    if len(first_mismatches) < 25:
                        first_mismatches.append({"scenario_id": scenario, "trial_id": trial_id,
                            "date": date_text, "reason": "PARTIAL_EQUITY_FIELD_MISSING_OR_NONINTEGER",
                            "fields": {key: row.get(key) for key in PARTIAL_EQUITY_FIELDS}})
                    continue
                cash, capital, retained, net_equity = values
                checked += 1
                if net_equity != capital + retained:
                    mismatches += 1
                    if len(first_mismatches) < 25:
                        first_mismatches.append({"scenario_id": scenario, "trial_id": trial_id,
                            "date": date_text, "reason": "NET_EQUITY_IDENTITY_MISMATCH",
                            "net_equity": net_equity, "capital": capital,
                            "retained_earnings": retained, "expected_net_equity": capital + retained})

        missing_trials = sorted(expected_trial_ids - seen_trials)
        if missing_trials:
            raise RuntimeError(f"DAILY_SNAPSHOT_TRIAL_COVERAGE_INCOMPLETE:{scenario}:{missing_trials[:10]}")
        empty_trials = sorted(tid for tid in expected_trial_ids if trial_row_counts.get(tid, 0) == 0)
        total_rows += rows
        total_checked += checked
        total_mismatch += mismatches
        total_bad_integer += bad_integer
        total_order_violation += order_violations
        total_duplicate_date += duplicate_dates
        scenario_results[scenario] = {
            "scenario_manifest_sha256": sha256_file(manifest_path),
            "daily_snapshot_sha256": digest, "daily_snapshot_size_bytes": size,
            "rows": rows, "trial_ids_covered": len(seen_trials), "empty_trial_ids": empty_trials,
            "equity_identity_rows_checked": checked, "equity_identity_mismatch_count": mismatches,
            "invalid_partial_equity_integer_rows": bad_integer, "daily_order_violations": order_violations,
            "duplicate_daily_dates": duplicate_dates, "stored_columns": sorted(columns),
            "missing_full_balance_sheet_fields": missing_full,
            "full_balance_sheet_independent_check": "MISSING_EVIDENCE" if missing_full else "READY_FOR_FULL_RECHECK",
        }

    if set(scenario_results) != set(SCENARIOS):
        raise RuntimeError("SCENARIO_COVERAGE_NOT_EXACT")
    row_total_matches = total_rows == EXPECTED_DAILY_ROWS
    scoped_ok = (
        row_total_matches and total_checked == total_rows and total_mismatch == 0
        and total_bad_integer == 0 and total_order_violation == 0 and total_duplicate_date == 0
        and all(not item["empty_trial_ids"] for item in scenario_results.values())
    )
    missing_full_fields = sorted({field for item in scenario_results.values()
                                  for field in item["missing_full_balance_sheet_fields"]})
    return {
        "schema_version": "s6-n2400-daily-equity-identity-audit-v1",
        "status": "PASS_SCOPED_EQUITY_IDENTITY_ONLY" if scoped_ok else "FAIL_SCOPED_EQUITY_IDENTITY_CHECK",
        "source_run_id": int(SOURCE_RUN_ID), "source_run_head_sha": SOURCE_RUN_HEAD_SHA,
        "source_sha": SOURCE_SHA, "cohort_id": COHORT_ID, "master_seed": MASTER_SEED,
        "model_schema_version": "v2.3", "checkpoint_n": CHECKPOINT_N, "scenario_count": 20,
        "expected_daily_rows_from_prior_readonly_audit": EXPECTED_DAILY_ROWS,
        "daily_rows_seen": total_rows, "daily_row_total_matches_prior_readonly_audit": row_total_matches,
        "trial_id_range_per_scenario": "1..2400",
        "equity_identity": "Net_Equity == Capital + Retained_Earnings",
        "equity_identity_rows_checked": total_checked, "equity_identity_mismatch_count": total_mismatch,
        "invalid_partial_equity_integer_rows": total_bad_integer,
        "daily_order_violations": total_order_violation, "duplicate_daily_dates": total_duplicate_date,
        "full_balance_sheet_status": "MISSING_EVIDENCE" if missing_full_fields else "READY_FOR_FULL_RECHECK",
        "missing_full_balance_sheet_fields": missing_full_fields,
        "full_balance_sheet_note": (
            "The persisted daily_snapshots export is a reduced projection for Cash, Net_Equity, Active_Bikes, "
            "Owned_Transferred_Bikes and Pending_Claims. It retains Capital and Retained_Earnings but omits "
            "asset-side fields needed for an independent Assets == Equity calculation. No missing values are inferred."
        ),
        "scenario_evidence": scenario_results, "source_run_provenance": provenance,
        "acceptance": "NOT_GRANTED",
        "gate_a_approval": "NOT_GRANTED_CANDIDATE_REQUIRES_SEPARATE_REVIEW",
        "gate_b": "FAIL_SCOPED", "stability": "NOT_CONVERGED",
        "first_mismatches": first_mismatches,
    }


def main() -> int:
    root = Path(os.environ.get("AUDIT_INPUT_ROOT", "audit-input"))
    output = Path("audit-output")
    output.mkdir(parents=True, exist_ok=True)
    try:
        report = run_audit(root)
    except Exception as exc:
        report = {"schema_version": "s6-n2400-daily-equity-identity-audit-v1",
                  "status": "BLOCKED_AUDIT_ERROR", "error_type": type(exc).__name__,
                  "error": str(exc), "acceptance": "NOT_GRANTED"}
        write_json(output / "S6_N2400_DAILY_EQUITY_IDENTITY_AUDIT.json", report)
        (output / "S6_N2400_DAILY_EQUITY_IDENTITY_AUDIT.md").write_text(
            "# S6 N2400 Daily Equity Identity Audit\n\n"
            f"- Status: {report['status']}\n- Error type: {report['error_type']}\n"
            f"- Error: {report['error']}\n- Acceptance: NOT_GRANTED\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 1
    write_json(output / "S6_N2400_DAILY_EQUITY_IDENTITY_AUDIT.json", report)
    lines = [
        "# S6 N2400 Daily Equity Identity Audit", "",
        f"- Status: {report['status']}",
        f"- Source run / source SHA: {SOURCE_RUN_ID} / {SOURCE_SHA}",
        f"- Cohort / seed / checkpoint: {COHORT_ID} / {MASTER_SEED} / N={CHECKPOINT_N}",
        f"- Daily rows: {report['daily_rows_seen']:,}; match prior audit: {report['daily_row_total_matches_prior_readonly_audit']}",
        f"- Net Equity identity rows checked: {report['equity_identity_rows_checked']:,}",
        f"- Net Equity identity mismatches: {report['equity_identity_mismatch_count']:,}",
        f"- Invalid integer rows: {report['invalid_partial_equity_integer_rows']:,}",
        f"- Daily order violations: {report['daily_order_violations']:,}",
        f"- Duplicate dates: {report['duplicate_daily_dates']:,}",
        f"- Full balance-sheet recheck: {report['full_balance_sheet_status']}",
        f"- Missing full balance fields: {', '.join(report['missing_full_balance_sheet_fields'])}",
        "- This proves only the stored equity identity, not an independent Assets==Equity balance check.",
        "- Gate A, Gate B, convergence and final acceptance are not granted by this report.",
    ]
    (output / "S6_N2400_DAILY_EQUITY_IDENTITY_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"], "daily_rows_seen": report["daily_rows_seen"],
        "equity_identity_rows_checked": report["equity_identity_rows_checked"],
        "equity_identity_mismatch_count": report["equity_identity_mismatch_count"],
        "full_balance_sheet_status": report["full_balance_sheet_status"],
        "missing_full_balance_sheet_fields": report["missing_full_balance_sheet_fields"],
        "acceptance": report["acceptance"],
    }, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "PASS_SCOPED_EQUITY_IDENTITY_ONLY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
