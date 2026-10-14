#!/usr/bin/env python3
"""Read-only, full-population content audit for CP-F Run 38619859394.

No source Dataset/Parquet is modified. Evidence is emitted only as audit JSON.
Reference rules: §§10.4, 10.6 and 14.7; governance decision D-2026-10-15-04.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

REPO_DEFAULT = "yasmin977209-ux/motorcycle-simulation"
CP_F_RUN_ID = 38619859394
HISTORICAL_RUN_ID = 37964656154
SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
MASTER_SEED = 20270101
SCHEMA_VERSION = "stage12-daily-accounting-v1"
IDENTITY_KEY = b"stage12.dataset_identity"
START_DATE = date(2027, 1, 1)
SCENARIOS = [
    f"C{c:03d}_G{g:03d}"
    for c in (100, 85, 70, 50, 30)
    for g in (100, 70, 50, 30, 0)
]
QUANTILES = (("P10", 0.10), ("P25", 0.25), ("P50", 0.50), ("P75", 0.75), ("P90", 0.90))
DAILY_METRICS = ("Cash", "Net_Equity", "Active_Bikes", "Owned_Transferred_Bikes", "Pending_Claims")
DISTRIBUTION_FIELDS = (
    "scenario_id", "date", "quantile_name", "active_trial_count",
    "source_sha", "master_seed", "schema_version",
    "Cash", "Net_Equity", "Active_Bikes", "Owned_Transferred_Bikes", "Pending_Claims",
)
ACCOUNTING_FIELDS = (
    "scenario_id", "trial_id", "date", "source_sha", "master_seed",
    "Opening_Cash", "cash_inflows", "cash_outflows", "Closing_Cash",
    "Opening_AR", "ar_accruals", "ar_collections", "ar_transfers_to_guarantee", "Closing_AR",
    "Opening_Gross_Bike_Assets", "capitalized_purchases_and_customs",
    "gross_writeoffs_on_ownership", "Closing_Gross_Bike_Assets",
    "Opening_Accumulated_Depreciation", "depreciation_expense",
    "ad_removed_on_writeoff", "Closing_Accumulated_Depreciation",
    "Net_Bike_Assets", "Capital", "Retained_Earnings", "Opening_Equity",
    "Operating_Net_Profit", "Closing_Equity", "Guarantee_Claim_Receivable",
    "Total_Assets", "Liabilities", "Balance_Difference", "Final_Close_Date",
    "Simulation_Stopped", "Active_Bikes", "Owned_Transferred_Bikes",
    "Pending_Claims", "result_sha256",
)
REPRESENTATIVE_FILES = {
    "P10": "P10.json",
    "P50": "P50.json",
    "P90": "P90.json",
    "LossCase": "Loss.json",
    "MaxCase": "Max Case.json",
}
RNG_POLICY = (
    "rng.py:SHA-256(seed key master_seed|scenario_id|trial_id|bike_id|date|event_type); "
    "draw=first_8_digest_bytes_big_endian/2^64; probability boundaries are deterministic"
)
CURRENT_IDENTITY = {
    "schema_version": SCHEMA_VERSION,
    "source_sha": SOURCE_SHA,
    "master_seed": MASTER_SEED,
}
CURRENT_SAMPLING_POLICY = "delivery-only deterministic replay; no new statistical cohort; no historical dataset mutation"
CURRENT_TRIAL_POLICY = "preserve original one-based scenario/trial identities; no duplicates"
HISTORICAL_SAMPLING_POLICY = (
    "one-based contiguous trial IDs; C100 scenarios use 1..1; non-C100 scenarios use 1..550; "
    "one materialization per scenario/trial; no cross-run inputs or resume"
)
HISTORICAL_STABILITY_POLICY = (
    "C100 uses one deterministic trial and no CI gate; non-C100 checkpoint N=300 then +50; "
    "95% Student-t CI half-width <1% of absolute mean for Final_Net_Project_Equity, "
    "Partner1_Final_Entitlement, Partner2_Final_Entitlement; CI_ABSOLUTE_EPSILON=1; "
    "three consecutive successful checkpoints; accepted N=550 (checkpoints 450, 500, 550)"
)

class AuditIssue(Exception):
    status = "FAIL"
    code = "AUDIT_FAILURE"

    def __init__(self, message: str, details: Any = None):
        super().__init__(message)
        self.details = details

class UndefinedBusinessRule(AuditIssue):
    status = "UNDEFINED_BUSINESS_RULE"
    code = "UNDEFINED_BUSINESS_RULE"

class InputBlocked(AuditIssue):
    status = "BLOCKED"
    code = "AUDIT_INPUT_BLOCKED"

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def token_value() -> str:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise InputBlocked("GH_TOKEN/GITHUB_TOKEN is unavailable; artifact access cannot be verified")
    return token

def repo_value() -> str:
    return os.environ.get("GITHUB_REPOSITORY", REPO_DEFAULT)

def api_json(path: str) -> dict[str, Any]:
    token = token_value()
    url = f"https://api.github.com/repos/{repo_value()}/{path.lstrip('/')}"
    result = subprocess.run(
        [
            "curl", "--fail", "--silent", "--show-error", "--location",
            "--connect-timeout", "30", "--max-time", "120",
            "-H", f"Authorization: Bearer {token}",
            "-H", "Accept: application/vnd.github+json",
            "-H", "X-GitHub-Api-Version: 2022-11-28",
            url,
        ],
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise InputBlocked(f"GITHUB_API_READ_FAILED path={path}; curl_exit={result.returncode}; stderr={result.stderr[-500:]}")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise InputBlocked(f"GITHUB_API_JSON_INVALID path={path}") from exc
    if not isinstance(value, dict):
        raise InputBlocked(f"GITHUB_API_SCHEMA_INVALID path={path}")
    return value

def safe_extract(zip_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    base = destination.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        members = archive.infolist()
        if not members:
            raise InputBlocked(f"EMPTY_ARTIFACT_ARCHIVE: {zip_path.name}")
        for member in members:
            target = (destination / member.filename).resolve()
            if target != base and base not in target.parents:
                raise InputBlocked(f"UNSAFE_ARCHIVE_PATH: {member.filename}")
        archive.extractall(destination)

def download_verified_artifact(run_id: int, artifact_name: str, root: Path) -> tuple[dict[str, Any], Path]:
    listing = api_json(f"actions/runs/{run_id}/artifacts?per_page=100")
    matches = [a for a in listing.get("artifacts", []) if a.get("name") == artifact_name]
    if len(matches) != 1:
        raise InputBlocked(f"ARTIFACT_NOT_UNIQUE run={run_id} name={artifact_name} count={len(matches)}")
    artifact = matches[0]
    if artifact.get("expired") is True:
        raise InputBlocked(f"ARTIFACT_EXPIRED run={run_id} name={artifact_name}")
    expected_digest = artifact.get("digest")
    if not isinstance(expected_digest, str) or not expected_digest.startswith("sha256:"):
        raise UndefinedBusinessRule(f"ARTIFACT_SHA256_MISSING run={run_id} name={artifact_name}")
    safe_name = "".join(c if c.isalnum() or c in "-_." else "_" for c in artifact_name)
    downloads = root / "downloads"
    downloads.mkdir(parents=True, exist_ok=True)
    zip_path = downloads / f"run-{run_id}-{safe_name}.zip"
    url = f"https://api.github.com/repos/{repo_value()}/actions/artifacts/{int(artifact['id'])}/zip"
    result = subprocess.run(
        [
            "curl", "--fail", "--silent", "--show-error", "--location",
            "--connect-timeout", "30", "--max-time", "900",
            "-H", f"Authorization: Bearer {token_value()}",
            "-H", "Accept: application/vnd.github+json",
            "--output", str(zip_path), url,
        ],
        capture_output=True, text=True, check=False,
    )
    if result.returncode:
        raise InputBlocked(
            f"ARTIFACT_DOWNLOAD_FAILED run={run_id} name={artifact_name}; "
            f"curl_exit={result.returncode}; stderr={result.stderr[-500:]}"
        )
    actual_bytes = zip_path.stat().st_size
    actual_digest = "sha256:" + sha256_file(zip_path)
    expected_size = artifact.get("size_in_bytes")
    if expected_size is not None and actual_bytes != int(expected_size):
        raise AuditIssue(
            f"ARTIFACT_SIZE_MISMATCH run={run_id} name={artifact_name}",
            {"expected": int(expected_size), "actual": actual_bytes},
        )
    if actual_digest != expected_digest:
        raise AuditIssue(
            f"ARTIFACT_ARCHIVE_SHA256_MISMATCH run={run_id} name={artifact_name}",
            {"expected": expected_digest, "actual": actual_digest},
        )
    extracted = root / "extracted" / f"run-{run_id}-{safe_name}"
    safe_extract(zip_path, extracted)
    evidence = {
        "run_id": run_id, "artifact_id": int(artifact["id"]), "name": artifact_name,
        "archive_sha256": actual_digest, "archive_size_bytes": actual_bytes,
        "created_at": artifact.get("created_at"),
    }
    return evidence, extracted

def find_exact_file(root: Path, basename: str, suffix: str | None = None) -> Path:
    paths = [p for p in root.rglob("*") if p.is_file() and p.name == basename]
    if suffix is not None:
        paths = [p for p in paths if p.suffix.lower() == suffix.lower()]
    if len(paths) != 1:
        raise InputBlocked(f"ARTIFACT_MEMBER_NOT_UNIQUE root={root.name} name={basename} count={len(paths)}")
    return paths[0]

def find_single_parquet(root: Path) -> Path:
    paths = sorted(p for p in root.rglob("*.parquet") if p.is_file())
    if len(paths) != 1:
        raise InputBlocked(f"HISTORICAL_PARQUET_NOT_UNIQUE root={root.name} count={len(paths)} names={[p.name for p in paths[:10]]}")
    return paths[0]

def json_load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise AuditIssue(f"JSON_READ_FAILED path={path.name}: {type(exc).__name__}: {exc}") from exc
    if not isinstance(value, dict):
        raise AuditIssue(f"JSON_ROOT_NOT_OBJECT path={path.name}")
    return value

def expected_ids(scenario: str, historical: bool) -> list[int]:
    if scenario.startswith("C100_"):
        return [1] if historical else list(range(2, 1201))
    return list(range(1, 551)) if historical else list(range(551, 1201))

def check_identity_metadata(path: Path, scenario: str, historical: bool) -> dict[str, Any]:
    parquet = pq.ParquetFile(path)
    metadata = parquet.schema_arrow.metadata or {}
    raw = metadata.get(IDENTITY_KEY)
    if raw is None:
        raise UndefinedBusinessRule(f"PARQUET_IDENTITY_METADATA_MISSING file={path.name}")
    try:
        identity = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise AuditIssue(f"PARQUET_IDENTITY_METADATA_INVALID file={path.name}") from exc
    required = ("schema_version", "scenario", "source_sha", "master_seed", "rng_policy", "sampling_policy", "trial_id_policy")
    missing = [key for key in required if key not in identity]
    if missing:
        raise UndefinedBusinessRule(f"PARQUET_IDENTITY_FIELDS_MISSING file={path.name} fields={missing}")
    expected = {
        "schema_version": SCHEMA_VERSION, "scenario": scenario,
        "source_sha": SOURCE_SHA, "master_seed": MASTER_SEED, "rng_policy": RNG_POLICY,
    }
    if any(identity.get(k) != v for k, v in expected.items()):
        raise AuditIssue(
            f"PARQUET_IDENTITY_MISMATCH file={path.name}",
            {"expected": expected, "actual": {k: identity.get(k) for k in expected}},
        )
    if historical:
        if identity.get("sampling_policy") != HISTORICAL_SAMPLING_POLICY or identity.get("trial_id_policy") != (
            "one-based contiguous trial IDs from 1 to scenario target; no duplicate IDs"
        ):
            raise AuditIssue(f"HISTORICAL_SAMPLING_IDENTITY_MISMATCH scenario={scenario}")
        if identity.get("stability_policy") != HISTORICAL_STABILITY_POLICY:
            raise AuditIssue(f"HISTORICAL_STABILITY_IDENTITY_MISMATCH scenario={scenario}")
    else:
        if identity.get("sampling_policy") != CURRENT_SAMPLING_POLICY or identity.get("trial_id_policy") != CURRENT_TRIAL_POLICY:
            raise AuditIssue(f"REPLAY_SAMPLING_IDENTITY_MISMATCH scenario={scenario}")
    return {
        "rows": int(parquet.metadata.num_rows),
        "columns": list(parquet.schema_arrow.names),
        "schema_identity": identity,
        "file_sha256": sha256_file(path),
    }

def require_columns(path: Path, required: tuple[str, ...]) -> None:
    schema = set(pq.ParquetFile(path).schema_arrow.names)
    missing = sorted(set(required) - schema)
    if missing:
        raise UndefinedBusinessRule(
            f"UNDEFINED_BUSINESS_RULE: required Parquet columns absent in {path.name}: {missing}",
            {"file": path.name, "missing_columns": missing, "required_columns": list(required)},
        )

def preflight(output_dir: Path) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {
        "status": "RUNNING", "scope": "preflight for independent read-only audit",
        "source_run_id": CP_F_RUN_ID, "historical_run_id": HISTORICAL_RUN_ID,
        "source_sha": SOURCE_SHA, "master_seed": MASTER_SEED, "expected_scenario_count": 25,
    }
    try:
        cohort_evidence, cohort_dir = download_verified_artifact(
            CP_F_RUN_ID, "cp-f-replay-cohort-validation", output_dir / "download-work"
        )
        source_evidence, source_dir = download_verified_artifact(
            CP_F_RUN_ID, "cp-f-source-readiness-evidence", output_dir / "download-work"
        )
        cohort_path = find_exact_file(cohort_dir, "CP_F_REPLAY_COHORT_VALIDATION.json")
        source_audit_path = find_exact_file(source_dir, "CP_F_N1200_SOURCE_READINESS.json")
        trial_path = find_exact_file(source_dir, "CP_F_N1200_TRIAL_RESULTS.json")
        cohort = json_load(cohort_path)
        source_audit = json_load(source_audit_path)
        trial_results = json_load(trial_path)

        if cohort.get("status") != "PASS" or cohort.get("manifest_version") != "cp-f-replay-cohort-v1":
            raise AuditIssue("CP_F_COHORT_MANIFEST_NOT_PASS")
        if cohort.get("scenario_count") != 25 or set(cohort.get("scenario_evidence", {})) != set(SCENARIOS):
            raise AuditIssue("CP_F_COHORT_SCENARIO_COVERAGE_MISMATCH")
        if cohort.get("source_sha") != SOURCE_SHA or cohort.get("master_seed") != MASTER_SEED:
            raise AuditIssue("CP_F_COHORT_SOURCE_IDENTITY_MISMATCH")
        if source_audit.get("status") != "READY_FOR_DETERMINISTIC_REPLAY":
            raise AuditIssue(f"CP_F_SOURCE_READINESS_NOT_READY status={source_audit.get('status')}")
        dataset = source_audit.get("dataset", {})
        if dataset.get("source_sha") != SOURCE_SHA or dataset.get("master_seed") != MASTER_SEED:
            raise AuditIssue("CP_F_SOURCE_READINESS_IDENTITY_MISMATCH")
        if set(trial_results.get("scenarios", {})) != set(SCENARIOS):
            raise AuditIssue("CP_F_TRIAL_RESULT_SCENARIO_COVERAGE_MISMATCH")
        scenario_trial_counts = {}
        for scenario in SCENARIOS:
            rows = trial_results["scenarios"][scenario]
            expected = [1] if scenario.startswith("C100_") else list(range(1, 1201))
            ids = [int(row.get("trial_id", -1)) for row in rows]
            if sorted(ids) != expected or len(set(ids)) != len(expected):
                raise AuditIssue(
                    f"CP_F_TRIAL_RESULT_TRIAL_ID_COVERAGE_MISMATCH scenario={scenario}",
                    {"expected_count": len(expected), "actual_count": len(ids)},
                )
            for row in rows:
                if row.get("scenario_id") != scenario or row.get("source_sha") != SOURCE_SHA or int(row.get("master_seed", -1)) != MASTER_SEED:
                    raise AuditIssue(f"CP_F_TRIAL_RESULT_IDENTITY_MISMATCH scenario={scenario}")
                result = row.get("trial_result")
                if not isinstance(result, dict) or result.get("scenario_id") != scenario or int(result.get("trial_id", -1)) != int(row["trial_id"]):
                    raise AuditIssue(f"CP_F_TRIAL_RESULT_PAYLOAD_MISMATCH scenario={scenario}")
            scenario_trial_counts[scenario] = len(ids)

        target_cohort = output_dir / "CP_F_REPLAY_COHORT_VALIDATION.json"
        target_source_audit = output_dir / "CP_F_N1200_SOURCE_READINESS.json"
        target_trial_results = output_dir / "CP_F_N1200_TRIAL_RESULTS.json"
        shutil.copy2(cohort_path, target_cohort)
        shutil.copy2(source_audit_path, target_source_audit)
        shutil.copy2(trial_path, target_trial_results)
        report.update({
            "status": "PASS",
            "artifact_evidence": {
                "cohort_validation": cohort_evidence,
                "source_readiness": source_evidence,
            },
            "embedded_files": {
                "cohort_validation_sha256": sha256_file(target_cohort),
                "source_readiness_sha256": sha256_file(target_source_audit),
                "trial_results_sha256": sha256_file(target_trial_results),
            },
            "scenario_trial_counts": scenario_trial_counts,
            "cohort_manifest_totals": {
                "non_c100_replay_trial_histories": cohort.get("non_c100_replay_trial_histories"),
                "c100_replay_trial_histories": cohort.get("c100_replay_trial_histories"),
                "total_primary_daily_replay_histories": cohort.get("total_primary_daily_replay_histories"),
                "extension_rows_sum_from_scenario_manifests": sum(
                    int(item.get("extension_rows", 0)) for item in cohort["scenario_evidence"].values()
                ),
                "daily_distribution_rows_sum": sum(
                    int(item.get("daily_distribution_rows", 0)) for item in cohort["scenario_evidence"].values()
                ),
            },
        })
    except UndefinedBusinessRule as exc:
        report.update({"status": "UNDEFINED_BUSINESS_RULE", "error": str(exc), "details": exc.details})
        write_json(output_dir / "CP_CONTENT_AUDIT_PREFLIGHT.json", report)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 2
    except AuditIssue as exc:
        report.update({"status": exc.status, "error": str(exc), "details": exc.details})
        write_json(output_dir / "CP_CONTENT_AUDIT_PREFLIGHT.json", report)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 1
    except Exception as exc:
        report.update({"status": "BLOCKED", "error": f"{type(exc).__name__}: {exc}"})
        write_json(output_dir / "CP_CONTENT_AUDIT_PREFLIGHT.json", report)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 1
    write_json(output_dir / "CP_CONTENT_AUDIT_PREFLIGHT.json", report)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0

class RowAudit:
    def __init__(self, scenario: str, manifest: dict[str, Any]):
        self.scenario = scenario
        self.manifest = manifest
        self.checks: Counter[str] = Counter()
        self.failures: Counter[str] = Counter()
        self.examples: list[dict[str, Any]] = []
        self.rows_by_file: dict[str, int] = {}
        self.bounds: dict[int, dict[str, Any]] = {}
        self.row_sha_by_trial: dict[int, str] = {}
        self.grouped: dict[str, dict[str, list[float]]] = {}
        self.seen_ids_by_file: dict[str, set[int]] = {}

    def check(self, name: str, passed: bool, context: dict[str, Any] | None = None) -> None:
        self.checks[name] += 1
        if not passed:
            self.failures[name] += 1
            if len(self.examples) < 25:
                self.examples.append({"check": name, **(context or {})})

    def add_row(self, row: dict[str, Any], source_file: str, expected_hashes: dict[str, Any]) -> None:
        scenario = self.scenario
        try:
            scenario_id = row.get("scenario_id")
            tid = int(row.get("trial_id", -1))
            day_text = str(row.get("date"))
            day = date.fromisoformat(day_text)
        except Exception as exc:
            self.check("row_identity_parse", False, {"file": source_file, "error": str(exc)})
            return
        self.check("scenario_identity", scenario_id == scenario, {"file": source_file, "trial_id": tid, "actual": scenario_id})
        self.check("source_identity", row.get("source_sha") == SOURCE_SHA, {"file": source_file, "trial_id": tid, "actual": row.get("source_sha")})
        try:
            seed = int(row.get("master_seed", -1))
        except (TypeError, ValueError):
            seed = -1
        self.check("master_seed_identity", seed == MASTER_SEED, {"file": source_file, "trial_id": tid, "actual": seed})
        self.check("trial_id_range", 1 <= tid <= 1200, {"file": source_file, "trial_id": tid})
        if not 1 <= tid <= 1200:
            return
        close_raw = row.get("Final_Close_Date")
        try:
            close = date.fromisoformat(str(close_raw)) if close_raw not in (None, "") else None
        except ValueError:
            close = None
            self.check("final_close_date_format", False, {"file": source_file, "trial_id": tid, "value": close_raw})
        if close is not None:
            self.check("row_not_after_final_close", day <= close, {"file": source_file, "trial_id": tid, "date": day_text, "close_date": str(close)})
        bounds = self.bounds.get(tid)
        result_hash = row.get("result_sha256")
        self.check("result_sha256_non_null", isinstance(result_hash, str) and bool(result_hash), {"file": source_file, "trial_id": tid, "date": day_text})
        if bounds is None:
            self.bounds[tid] = {"first": day, "last": day, "count": 1, "close": close}
            self.row_sha_by_trial[tid] = str(result_hash)
        else:
            self.check("final_close_date_consistency", bounds["close"] == close, {"trial_id": tid, "date": day_text})
            self.check("result_sha256_consistency", self.row_sha_by_trial.get(tid) == str(result_hash), {"trial_id": tid, "date": day_text})
            previous = bounds["last"]
            self.check("daily_date_step", day == previous + timedelta(days=1), {"trial_id": tid, "previous_date": previous.isoformat(), "date": day_text})
            bounds["last"] = day
            bounds["count"] += 1

        for field in (
            "Opening_Cash", "cash_inflows", "cash_outflows", "Closing_Cash",
            "Opening_AR", "ar_accruals", "ar_collections", "ar_transfers_to_guarantee", "Closing_AR",
            "Opening_Gross_Bike_Assets", "capitalized_purchases_and_customs", "gross_writeoffs_on_ownership", "Closing_Gross_Bike_Assets",
            "Opening_Accumulated_Depreciation", "depreciation_expense", "ad_removed_on_writeoff", "Closing_Accumulated_Depreciation",
            "Net_Bike_Assets", "Capital", "Retained_Earnings", "Opening_Equity", "Operating_Net_Profit",
            "Closing_Equity", "Guarantee_Claim_Receivable", "Total_Assets", "Liabilities", "Balance_Difference",
            "Active_Bikes", "Owned_Transferred_Bikes", "Pending_Claims",
        ):
            value = row.get(field)
            if value is None:
                self.check("required_row_value_non_null", False, {"file": source_file, "trial_id": tid, "date": day_text, "field": field})

        try:
            op_cash = int(row["Opening_Cash"]) + int(row["cash_inflows"]) - int(row["cash_outflows"])
            op_ar = int(row["Opening_AR"]) + int(row["ar_accruals"]) - int(row["ar_collections"]) - int(row["ar_transfers_to_guarantee"])
            op_gross = int(row["Opening_Gross_Bike_Assets"]) + int(row["capitalized_purchases_and_customs"]) - int(row["gross_writeoffs_on_ownership"])
            op_ad = int(row["Opening_Accumulated_Depreciation"]) + int(row["depreciation_expense"]) - int(row["ad_removed_on_writeoff"])
            op_equity = int(row["Opening_Equity"]) + int(row["Operating_Net_Profit"])
            net_assets = int(row["Closing_Gross_Bike_Assets"]) - int(row["Closing_Accumulated_Depreciation"])
            equity_components = int(row["Capital"]) + int(row["Retained_Earnings"])
            assets = int(row["Closing_Cash"]) + int(row["Closing_AR"]) + int(row["Guarantee_Claim_Receivable"]) + int(row["Net_Bike_Assets"])
            self.check("rollforward_cash", op_cash == int(row["Closing_Cash"]), {"file": source_file, "trial_id": tid, "date": day_text})
            self.check("rollforward_ar", op_ar == int(row["Closing_AR"]), {"file": source_file, "trial_id": tid, "date": day_text})
            self.check("rollforward_gross_assets", op_gross == int(row["Closing_Gross_Bike_Assets"]), {"file": source_file, "trial_id": tid, "date": day_text})
            self.check("rollforward_accumulated_depreciation", op_ad == int(row["Closing_Accumulated_Depreciation"]), {"file": source_file, "trial_id": tid, "date": day_text})
            self.check("rollforward_equity", op_equity == int(row["Closing_Equity"]), {"file": source_file, "trial_id": tid, "date": day_text})
            self.check("derived_net_bike_assets", net_assets == int(row["Net_Bike_Assets"]), {"file": source_file, "trial_id": tid, "date": day_text})
            self.check("equity_components", equity_components == int(row["Closing_Equity"]), {"file": source_file, "trial_id": tid, "date": day_text})
            self.check("total_assets_formula", assets == int(row["Total_Assets"]), {"file": source_file, "trial_id": tid, "date": day_text})
            self.check("liabilities_zero", int(row["Liabilities"]) == 0, {"file": source_file, "trial_id": tid, "date": day_text, "actual": int(row["Liabilities"])})
            self.check("balance_sheet_equation", int(row["Total_Assets"]) == int(row["Closing_Equity"]), {"file": source_file, "trial_id": tid, "date": day_text})
            self.check("balance_difference_zero", int(row["Balance_Difference"]) == 0, {"file": source_file, "trial_id": tid, "date": day_text, "actual": int(row["Balance_Difference"])})
        except (TypeError, ValueError, KeyError, OverflowError) as exc:
            self.check("accounting_values_are_complete_integers", False, {"file": source_file, "trial_id": tid, "date": day_text, "error": str(exc)})

        if source_file == "daily_accounting_extension.parquet":
            expected_hash = expected_hashes.get(str(tid))
            self.check("extension_trial_hash_approved", isinstance(expected_hash, str) and expected_hash == str(result_hash), {"trial_id": tid, "date": day_text})
        target = self.grouped.setdefault(day_text, {metric: [] for metric in DAILY_METRICS})
        metrics = {
            "Cash": row.get("Closing_Cash"),
            "Net_Equity": row.get("Closing_Equity"),
            "Active_Bikes": row.get("Active_Bikes"),
            "Owned_Transferred_Bikes": row.get("Owned_Transferred_Bikes"),
            "Pending_Claims": row.get("Pending_Claims"),
        }
        for metric, value in metrics.items():
            try:
                numeric = float(value)
                self.check("daily_distribution_source_numeric", np.isfinite(numeric), {"trial_id": tid, "date": day_text, "metric": metric})
                target[metric].append(numeric)
            except (TypeError, ValueError):
                self.check("daily_distribution_source_numeric", False, {"trial_id": tid, "date": day_text, "metric": metric, "value": value})

def scan_parquet(path: Path, scenario: str, historical: bool, audit: RowAudit, manifest: dict[str, Any]) -> dict[str, Any]:
    meta_report = check_identity_metadata(path, scenario, historical)
    require_columns(path, ACCOUNTING_FIELDS)
    pf = pq.ParquetFile(path)
    seen: set[int] = set()
    current_tid: int | None = None
    previous_day: date | None = None
    last_tid = 0
    row_count = 0
    expected_hashes = manifest.get("trial_fingerprints", {})
    for batch in pf.iter_batches(batch_size=25000, columns=list(ACCOUNTING_FIELDS)):
        columns = batch.to_pydict()
        for index in range(batch.num_rows):
            row = {name: columns[name][index] for name in ACCOUNTING_FIELDS}
            tid = int(row.get("trial_id", -1))
            day = date.fromisoformat(str(row.get("date")))
            if tid < last_tid:
                audit.check("trial_order", False, {"file": path.name, "previous_trial_id": last_tid, "trial_id": tid})
            if current_tid is None or tid != current_tid:
                if tid in seen:
                    audit.check("trial_noncontiguous_reappearance", False, {"file": path.name, "trial_id": tid})
                seen.add(tid)
                current_tid = tid
                previous_day = day
            else:
                if previous_day is None or day != previous_day + timedelta(days=1):
                    audit.check("daily_date_step", False, {"file": path.name, "trial_id": tid, "previous_date": previous_day.isoformat() if previous_day else None, "date": str(day)})
                previous_day = day
            last_tid = max(last_tid, tid)
            row_count += 1
            audit.add_row(row, path.name, expected_hashes)
    expected = set(expected_ids(scenario, historical))
    if seen != expected:
        audit.check(
            "trial_coverage",
            False,
            {"file": path.name, "expected_count": len(expected), "actual_count": len(seen),
             "missing_ids_first": sorted(expected - seen)[:20], "extra_ids_first": sorted(seen - expected)[:20]},
        )
    audit.rows_by_file[path.name] = row_count
    return {**meta_report, "rows_scanned": row_count, "trial_ids_seen": len(seen), "trial_ids_expected": len(expected)}

def audit_daily_distribution(path: Path, scenario: str, audit: RowAudit) -> dict[str, Any]:
    require_columns(path, DISTRIBUTION_FIELDS)
    pf = pq.ParquetFile(path)
    meta = pf.schema_arrow.metadata or {}
    raw = meta.get(IDENTITY_KEY)
    if raw is None:
        raise UndefinedBusinessRule(f"DAILY_DISTRIBUTION_IDENTITY_METADATA_MISSING scenario={scenario}")
    try:
        identity = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise AuditIssue(f"DAILY_DISTRIBUTION_IDENTITY_METADATA_INVALID scenario={scenario}") from exc
    for key, expected in CURRENT_IDENTITY.items():
        if key not in identity:
            raise UndefinedBusinessRule(f"DAILY_DISTRIBUTION_IDENTITY_FIELD_MISSING scenario={scenario} field={key}")
        audit.check("daily_distribution_schema_identity", identity.get(key) == expected, {"scenario": scenario, "field": key, "actual": identity.get(key)})
    if "scenario" not in identity:
        raise UndefinedBusinessRule(f"DAILY_DISTRIBUTION_IDENTITY_FIELD_MISSING scenario={scenario} field=scenario")
    audit.check("daily_distribution_schema_scenario", identity.get("scenario") == scenario, {"scenario": scenario, "actual": identity.get("scenario")})
    expected_map: dict[tuple[str, str], dict[str, Any]] = {}
    row_count = 0
    for batch in pf.iter_batches(batch_size=25000, columns=list(DISTRIBUTION_FIELDS)):
        cols = batch.to_pydict()
        for i in range(batch.num_rows):
            row = {name: cols[name][i] for name in DISTRIBUTION_FIELDS}
            key = (str(row["date"]), str(row["quantile_name"]))
            if key in expected_map:
                audit.check("daily_distribution_key_unique", False, {"scenario": scenario, "date": key[0], "quantile_name": key[1]})
            expected_map[key] = row
            row_count += 1
            audit.check("daily_distribution_scenario_identity", row.get("scenario_id") == scenario, {"scenario": scenario, "date": key[0]})
            audit.check("daily_distribution_source_identity", row.get("source_sha") == SOURCE_SHA, {"scenario": scenario, "date": key[0]})
            try:
                audit.check("daily_distribution_seed_identity", int(row.get("master_seed", -1)) == MASTER_SEED, {"scenario": scenario, "date": key[0]})
            except (TypeError, ValueError):
                audit.check("daily_distribution_seed_identity", False, {"scenario": scenario, "date": key[0]})
            audit.check("daily_distribution_schema_version", row.get("schema_version") == SCHEMA_VERSION, {"scenario": scenario, "date": key[0]})
    expected_days = sorted(audit.grouped.keys(), key=date.fromisoformat)
    quantile_checks = 0
    for day_text in expected_days:
        day = date.fromisoformat(day_text)
        close_dates = [bounds["close"] for bounds in audit.bounds.values()]
        active_count = sum(1 for close in close_dates if close is None or close >= day)
        lists = audit.grouped[day_text]
        for metric in DAILY_METRICS:
            audit.check(
                "daily_distribution_full_active_population",
                len(lists[metric]) == active_count,
                {"scenario": scenario, "date": day_text, "metric": metric,
                 "values_count": len(lists[metric]), "active_trial_count": active_count},
            )
        for quantile_name, quantile in QUANTILES:
            key = (day_text, quantile_name)
            row = expected_map.get(key)
            if row is None:
                audit.check("daily_distribution_expected_row_present", False, {"scenario": scenario, "date": day_text, "quantile_name": quantile_name})
                continue
            audit.check("daily_distribution_active_trial_count", int(row["active_trial_count"]) == active_count, {"scenario": scenario, "date": day_text, "quantile_name": quantile_name})
            for metric in DAILY_METRICS:
                values = lists[metric]
                if not values:
                    audit.check("daily_distribution_quantile_recomputed", False, {"scenario": scenario, "date": day_text, "quantile_name": quantile_name, "metric": metric, "error": "empty active population"})
                    continue
                calculated = float(np.quantile(np.asarray(values, dtype=np.float64), quantile, method="linear"))
                try:
                    actual = float(row[metric])
                    match = np.isfinite(actual) and actual == calculated
                except (TypeError, ValueError):
                    actual, match = row.get(metric), False
                audit.check(
                    "daily_distribution_quantile_exact",
                    bool(match),
                    {"scenario": scenario, "date": day_text, "quantile_name": quantile_name, "metric": metric,
                     "expected": calculated, "actual": actual},
                )
                quantile_checks += 1
    expected_keys = {(day, qname) for day in expected_days for qname, _ in QUANTILES}
    actual_keys = set(expected_map)
    audit.check(
        "daily_distribution_key_coverage",
        actual_keys == expected_keys,
        {"expected_rows": len(expected_keys), "actual_rows": len(actual_keys),
         "missing_first": sorted(expected_keys - actual_keys)[:20], "extra_first": sorted(actual_keys - expected_keys)[:20]},
    )
    return {
        "rows": row_count, "dates": len(expected_days), "expected_rows": len(expected_keys),
        "quantile_value_comparisons": quantile_checks, "file_sha256": sha256_file(path),
        "unique_output_keys": len(expected_map),
    }

def audit_representatives(root: Path, scenario: str, manifest: dict[str, Any], audit: RowAudit) -> dict[str, Any]:
    rep_dir = root / "representatives"
    paths = {p.name for p in rep_dir.glob("*.json")}
    expected_files = set(REPRESENTATIVE_FILES.values())
    if paths != expected_files:
        raise AuditIssue(f"REPRESENTATIVE_FILE_COVERAGE_MISMATCH scenario={scenario}", {"expected": sorted(expected_files), "actual": sorted(paths)})
    selected = manifest.get("representative_trial_ids", {})
    reports = {}
    role_balance_checks = 0
    role_rollforward_checks = 0
    for role, filename in REPRESENTATIVE_FILES.items():
        payload = json_load(rep_dir / filename)
        summary = payload.get("summary", {})
        tid = int(selected.get(role, -1))
        audit.check("representative_role_trial_id", int(summary.get("trial_id", -2)) == tid, {"scenario": scenario, "role": role, "expected_trial_id": tid, "actual_trial_id": summary.get("trial_id")})
        audit.check("representative_role_scenario", summary.get("scenario_id") == scenario, {"scenario": scenario, "role": role, "actual": summary.get("scenario_id")})
        daily = payload.get("daily")
        accounting = payload.get("accounting", {})
        if not isinstance(daily, list) or not daily:
            raise AuditIssue(f"REPRESENTATIVE_DAILY_PAYLOAD_MISSING scenario={scenario} role={role}")
        series = {
            "cash_rollforward": accounting.get("cash_rollforward"),
            "ar_rollforward": accounting.get("ar_rollforward"),
            "asset_rollforward": accounting.get("asset_rollforward"),
            "equity_rollforward": accounting.get("equity_rollforward"),
            "daily_balance_checks": accounting.get("daily_balance_checks"),
        }
        for key, values in series.items():
            if not isinstance(values, list):
                raise UndefinedBusinessRule(f"UNDEFINED_BUSINESS_RULE: representative accounting field missing scenario={scenario} role={role} field={key}")
            audit.check("representative_accounting_length", len(values) == len(daily), {"scenario": scenario, "role": role, "field": key, "daily": len(daily), "accounting": len(values)})
        if any(len(values) != len(daily) for values in series.values()):
            reports[role] = {"trial_id": tid, "daily_rows": len(daily), "accounting_lengths": {k: len(v) for k, v in series.items()}}
            continue
        dates = []
        for i, day_row in enumerate(daily):
            try:
                day_text = str(day_row["date"])
                day = date.fromisoformat(day_text)
            except Exception as exc:
                audit.check("representative_date_valid", False, {"scenario": scenario, "role": role, "index": i, "error": str(exc)})
                continue
            dates.append(day)
            audit.check("representative_trial_id_consistent", int(day_row.get("trial_id", -1)) == tid, {"scenario": scenario, "role": role, "date": day_text})
            if i:
                audit.check("representative_date_step", day == dates[i - 1] + timedelta(days=1), {"scenario": scenario, "role": role, "previous_date": dates[i - 1].isoformat(), "date": day_text})
            cash = series["cash_rollforward"][i]
            ar = series["ar_rollforward"][i]
            asset = series["asset_rollforward"][i]
            equity = series["equity_rollforward"][i]
            balance = series["daily_balance_checks"][i]
            if i == 0:
                audit.check("representative_start_date", day == START_DATE, {"scenario": scenario, "role": role, "actual": day_text})
            checks = (
                ("representative_rollforward_cash", int(cash["Opening_Cash"]) + int(cash["Inflows"]) - int(cash["Outflows"]) == int(cash["Closing_Cash"])),
                ("representative_rollforward_ar", int(ar["Opening_AR"]) + int(ar["Accruals"]) - int(ar["Collections"]) - int(ar["TransfersToGuarantee"]) == int(ar["Closing_AR"])),
                ("representative_rollforward_gross_assets", int(asset["Opening_Gross_Bike_Assets"]) + int(asset["Capitalized_Purchases_And_Customs"]) - int(asset["Gross_Writeoffs_On_Ownership"]) == int(asset["Closing_Gross_Bike_Assets"])),
                ("representative_rollforward_accumulated_depreciation", int(asset["Opening_Accumulated_Depreciation"]) + int(asset["Depreciation_Expense"]) - int(asset["AD_Removed_On_Writeoff"]) == int(asset["Closing_Accumulated_Depreciation"])),
                ("representative_rollforward_equity", int(equity["Opening_Equity"]) + int(equity["Operating_Net_Profit"]) == int(equity["Closing_Equity"])),
                ("representative_net_bike_assets", int(asset["Closing_Gross_Bike_Assets"]) - int(asset["Closing_Accumulated_Depreciation"]) == int(balance["Net_Bike_Assets"])),
                ("representative_equity_components", int(day_row["Capital"]) + int(day_row["Retained_Earnings"]) == int(equity["Closing_Equity"])),
                ("representative_total_assets_formula", int(balance["Cash"]) + int(balance["Accounts_Receivable"]) + int(balance["Guarantee_Claim_Receivable"]) + int(balance["Net_Bike_Assets"]) == int(balance["Total_Assets"])),
                ("representative_balance_sheet", int(balance["Total_Assets"]) == int(balance["Total_Equity"])),
                ("representative_liabilities_zero", int(balance["Liabilities"]) == 0),
                ("representative_balance_difference_zero", int(balance["Balance_Difference"]) == 0),
                ("representative_snapshot_cash_alignment", int(day_row["Cash"]) == int(cash["Closing_Cash"]) == int(balance["Cash"])),
                ("representative_snapshot_ar_alignment", int(day_row["Accounts_Receivable"]) == int(ar["Closing_AR"]) == int(balance["Accounts_Receivable"])),
                ("representative_snapshot_gross_asset_alignment", int(day_row["Gross_Bike_Assets"]) == int(asset["Closing_Gross_Bike_Assets"]) == int(balance["Gross_Bike_Assets"])),
                ("representative_snapshot_equity_alignment", int(day_row["Net_Equity"]) == int(equity["Closing_Equity"]) == int(balance["Total_Equity"])),
            )
            for name, passed in checks:
                audit.check(name, passed, {"scenario": scenario, "role": role, "trial_id": tid, "date": day_text})
                role_rollforward_checks += int("rollforward" in name)
                role_balance_checks += int("balance" in name or "total_assets" in name or "net_bike_assets" in name)
            # The representative daily snapshot's final-close field must agree on every row.
            audit.check("representative_close_date_constant", day_row.get("Final_Close_Date") == daily[0].get("Final_Close_Date"), {"scenario": scenario, "role": role, "date": day_text})
        audit.check("representative_start_to_finish_dates", bool(dates) and dates[0] == START_DATE, {"scenario": scenario, "role": role})
        if summary.get("final_close_date") is not None:
            audit.check("representative_final_close_date", dates[-1].isoformat() == str(summary["final_close_date"]), {"scenario": scenario, "role": role, "daily_last": dates[-1].isoformat() if dates else None, "summary_close": summary.get("final_close_date")})
        reports[role] = {"trial_id": tid, "daily_rows": len(daily), "payload_sha256": sha256_file(rep_dir / filename)}
    return {
        "roles": reports, "role_count": len(reports),
        "daily_balance_checks": role_balance_checks, "rollforward_checks": role_rollforward_checks,
    }

def run_scenario_audit(scenario: str, input_index: Path, output_path: Path) -> int:
    report: dict[str, Any] = {
        "status": "RUNNING", "scenario": scenario, "source_run_id": CP_F_RUN_ID,
        "historical_run_id": HISTORICAL_RUN_ID, "source_sha": SOURCE_SHA, "master_seed": MASTER_SEED,
        "scope": "all historical plus extension daily rows; all daily-distribution rows; five representative payloads",
    }
    scratch = output_path.parent / f".{scenario}-work"
    try:
        if scenario not in SCENARIOS:
            raise InputBlocked(f"UNSUPPORTED_SCENARIO {scenario}")
        preflight_path = input_index / "CP_CONTENT_AUDIT_PREFLIGHT.json"
        if not preflight_path.is_file():
            raise InputBlocked("PREFLIGHT_REPORT_MISSING")
        preflight_report = json_load(preflight_path)
        if preflight_report.get("status") != "PASS":
            raise InputBlocked(f"PREFLIGHT_NOT_PASS status={preflight_report.get('status')}")
        cohort_path = input_index / "CP_F_REPLAY_COHORT_VALIDATION.json"
        if not cohort_path.is_file():
            raise InputBlocked("COHORT_INDEX_MISSING")
        cohort = json_load(cohort_path)
        expected_cohort_scenario = cohort.get("scenario_evidence", {}).get(scenario)
        if not isinstance(expected_cohort_scenario, dict):
            raise AuditIssue(f"COHORT_INDEX_SCENARIO_MISSING scenario={scenario}")
        scratch.mkdir(parents=True, exist_ok=True)
        cp_evidence, cp_dir = download_verified_artifact(CP_F_RUN_ID, f"cp-f-replay-{scenario}", scratch)
        hist_evidence, hist_dir = download_verified_artifact(HISTORICAL_RUN_ID, f"stage12-daily-{scenario}", scratch)
        manifest_path = find_exact_file(cp_dir, "scenario_manifest.json")
        extension_path = find_exact_file(cp_dir, "daily_accounting_extension.parquet", ".parquet")
        distribution_path = find_exact_file(cp_dir, "daily_distribution.parquet", ".parquet")
        historical_path = find_single_parquet(hist_dir)
        manifest = json_load(manifest_path)
        if manifest.get("status") != "PASS" or manifest.get("scenario") != scenario:
            raise AuditIssue(f"SCENARIO_MANIFEST_NOT_PASS_OR_WRONG_SCENARIO scenario={scenario}")
        if manifest.get("source_sha") != SOURCE_SHA or manifest.get("master_seed") != MASTER_SEED:
            raise AuditIssue(f"SCENARIO_MANIFEST_SOURCE_IDENTITY_MISMATCH scenario={scenario}")
        if manifest.get("schema_version") != SCHEMA_VERSION:
            raise AuditIssue(f"SCENARIO_MANIFEST_SCHEMA_MISMATCH scenario={scenario}")
        manifest_sha = sha256_file(manifest_path)
        if manifest_sha != expected_cohort_scenario.get("manifest_sha256"):
            raise AuditIssue(f"SCENARIO_MANIFEST_SHA256_MISMATCH scenario={scenario}", {"actual": manifest_sha, "expected": expected_cohort_scenario.get("manifest_sha256")})
        extension_sha = sha256_file(extension_path)
        if extension_sha != manifest.get("daily_accounting_extension_sha256"):
            raise AuditIssue(f"DAILY_ACCOUNTING_EXTENSION_SHA256_MISMATCH scenario={scenario}")
        distribution_sha = sha256_file(distribution_path)
        if distribution_sha != manifest.get("daily_distribution", {}).get("rows_sha256"):
            raise AuditIssue(f"DAILY_DISTRIBUTION_SHA256_MISMATCH scenario={scenario}")
        historical_sha = sha256_file(historical_path)
        if historical_sha != manifest.get("historical_daily_sha256"):
            raise AuditIssue(f"HISTORICAL_DAILY_SHA256_MISMATCH scenario={scenario}", {"actual": historical_sha, "expected": manifest.get("historical_daily_sha256")})
        if sha256_file(extension_path) != extension_sha or sha256_file(distribution_path) != distribution_sha:
            raise AuditIssue(f"PARQUET_FILE_SHA256_UNSTABLE scenario={scenario}")
        ext_pf = pq.ParquetFile(extension_path)
        ext_trial_ids = sorted(set(int(x) for x in ext_pf.read(columns=["trial_id"])["trial_id"].to_pylist()))
        if ext_trial_ids != expected_ids(scenario, historical=False):
            raise AuditIssue(
                f"EXTENSION_TRIAL_ID_COVERAGE_MISMATCH scenario={scenario}",
                {"expected_count": len(expected_ids(scenario, False)), "actual_count": len(ext_trial_ids),
                 "missing_first": sorted(set(expected_ids(scenario, False)) - set(ext_trial_ids))[:20],
                 "extra_first": sorted(set(ext_trial_ids) - set(expected_ids(scenario, False)))[:20]},
            )
        if int(manifest.get("extension_trial_count", -1)) != len(ext_trial_ids):
            raise AuditIssue(f"EXTENSION_TRIAL_COUNT_MISMATCH scenario={scenario}")
        if int(manifest.get("daily_accounting_extension_rows", -1)) != int(ext_pf.metadata.num_rows):
            raise AuditIssue(f"EXTENSION_ROW_COUNT_MISMATCH scenario={scenario}")
        if int(manifest.get("daily_distribution", {}).get("daily_distribution_rows", -1)) != int(pq.ParquetFile(distribution_path).metadata.num_rows):
            raise AuditIssue(f"DAILY_DISTRIBUTION_ROW_COUNT_MISMATCH scenario={scenario}")
        if int(manifest.get("historical_daily_trials", -1)) != (1 if scenario.startswith("C100_") else 550):
            raise AuditIssue(f"HISTORICAL_TRIAL_COUNT_MISMATCH scenario={scenario}")
        if int(manifest.get("historical_daily_rows", -1)) != int(pq.ParquetFile(historical_path).metadata.num_rows):
            raise AuditIssue(f"HISTORICAL_ROW_COUNT_MISMATCH scenario={scenario}")
        if int(expected_cohort_scenario.get("extension_rows", -1)) != int(ext_pf.metadata.num_rows):
            raise AuditIssue(f"COHORT_EXTENSION_ROW_COUNT_MISMATCH scenario={scenario}")
        if int(expected_cohort_scenario.get("daily_distribution_rows", -1)) != int(pq.ParquetFile(distribution_path).metadata.num_rows):
            raise AuditIssue(f"COHORT_DAILY_DISTRIBUTION_ROW_COUNT_MISMATCH scenario={scenario}")
        if expected_cohort_scenario.get("daily_distribution_sha256") != distribution_sha:
            raise AuditIssue(f"COHORT_DAILY_DISTRIBUTION_SHA256_MISMATCH scenario={scenario}")

        audit = RowAudit(scenario, manifest)
        hist_report = scan_parquet(historical_path, scenario, True, audit, manifest)
        ext_report = scan_parquet(extension_path, scenario, False, audit, manifest)
        expected_full_ids = set(range(1, 1201))
        observed_full_ids = set(audit.bounds)
        audit.check(
            "full_1200_trial_history_coverage",
            observed_full_ids == expected_full_ids,
            {"expected_count": 1200, "actual_count": len(observed_full_ids),
             "missing_first": sorted(expected_full_ids - observed_full_ids)[:20],
             "extra_first": sorted(observed_full_ids - expected_full_ids)[:20]},
        )
        for tid, bounds in audit.bounds.items():
            audit.check("trial_history_starts_on_reference_day", bounds["first"] == START_DATE, {"scenario": scenario, "trial_id": tid, "first_date": bounds["first"].isoformat()})
            audit.check(
                "trial_history_has_no_day_gap",
                (bounds["last"] - bounds["first"]).days + 1 == bounds["count"],
                {"scenario": scenario, "trial_id": tid, "first": bounds["first"].isoformat(),
                 "last": bounds["last"].isoformat(), "rows": bounds["count"]},
            )
            if bounds["close"] is not None:
                audit.check("trial_history_ends_on_close_date", bounds["last"] == bounds["close"], {"scenario": scenario, "trial_id": tid, "last": bounds["last"].isoformat(), "close": bounds["close"].isoformat()})
        max_day = max((bounds["last"] for bounds in audit.bounds.values()), default=None)
        for tid, bounds in audit.bounds.items():
            if bounds["close"] is None and max_day is not None:
                audit.check("unclosed_trial_history_reaches_last_recorded_day", bounds["last"] == max_day, {"scenario": scenario, "trial_id": tid, "last": bounds["last"].isoformat(), "max_day": max_day.isoformat()})
        distribution_report = audit_daily_distribution(distribution_path, scenario, audit)
        representative_report = audit_representatives(cp_dir, scenario, manifest, audit)

        for cohort_key, expected in (
            ("extension_trials", len(ext_trial_ids)),
            ("extension_rows", ext_report["rows_scanned"]),
            ("daily_distribution_rows", distribution_report["rows"]),
            ("dates", distribution_report["dates"]),
        ):
            audit.check("cohort_manifest_summary_consistency", int(expected_cohort_scenario.get(cohort_key, -1)) == int(expected), {"scenario": scenario, "field": cohort_key, "expected": expected, "actual": expected_cohort_scenario.get(cohort_key)})
        mismatch_total = sum(audit.failures.values())
        report.update({
            "status": "PASS" if mismatch_total == 0 else "FAIL",
            "artifact_evidence": {"cp_f_scenario_artifact": cp_evidence, "historical_daily_artifact": hist_evidence},
            "files": {
                "scenario_manifest": {"sha256": manifest_sha, "bytes": manifest_path.stat().st_size},
                "daily_accounting_extension": {"sha256": extension_sha, "bytes": extension_path.stat().st_size, **ext_report},
                "daily_distribution": {"sha256": distribution_sha, "bytes": distribution_path.stat().st_size, **distribution_report},
                "historical_daily": {"sha256": historical_sha, "bytes": historical_path.stat().st_size, **hist_report},
            },
            "rows_checked": {
                "historical_daily_rows": hist_report["rows_scanned"],
                "extension_daily_rows": ext_report["rows_scanned"],
                "total_daily_accounting_rows": hist_report["rows_scanned"] + ext_report["rows_scanned"],
                "daily_distribution_rows": distribution_report["rows"],
            },
            "trials_checked": len(observed_full_ids),
            "daily_dates": distribution_report["dates"],
            "representatives": representative_report,
            "check_counts": dict(sorted(audit.checks.items())),
            "mismatch_counts": dict(sorted(audit.failures.items())),
            "mismatch_total": mismatch_total,
            "mismatch_examples": audit.examples,
        })
    except UndefinedBusinessRule as exc:
        report.update({"status": "UNDEFINED_BUSINESS_RULE", "error": str(exc), "details": exc.details})
        write_json(output_path, report)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 2
    except InputBlocked as exc:
        report.update({"status": "BLOCKED", "error": str(exc), "details": exc.details})
        write_json(output_path, report)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 3
    except AuditIssue as exc:
        report.update({"status": "FAIL", "error": str(exc), "details": exc.details})
        write_json(output_path, report)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 1
    except Exception as exc:
        report.update({"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"})
        write_json(output_path, report)
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        return 1
    write_json(output_path, report)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] in ("PASS", "FAIL") else 2

def aggregate_reports(reports_dir: Path, output_path: Path) -> int:
    reports = {};
    preflight_files = sorted(reports_dir.rglob("CP_CONTENT_AUDIT_PREFLIGHT.json"))
    preflight_report = json_load(preflight_files[0]) if preflight_files else None
    preflight_status = preflight_report.get("status") if preflight_report else "MISSING"
    for path in sorted(reports_dir.glob("*.json")):
        try:
            data = json_load(path)
        except Exception:
            continue
        scenario = data.get("scenario")
        if scenario in SCENARIOS:
            reports[scenario] = data
    missing = sorted(set(SCENARIOS) - set(reports))
    statuses = {scenario: data.get("status") for scenario, data in reports.items()}
    has_undefined = any(status == "UNDEFINED_BUSINESS_RULE" for status in statuses.values()) or preflight_status == "UNDEFINED_BUSINESS_RULE"
    has_fail = any(status == "FAIL" for status in statuses.values())
    has_blocked = (
        any(status not in ("PASS", "FAIL", "UNDEFINED_BUSINESS_RULE") for status in statuses.values())
        or bool(missing) or preflight_status != "PASS"
    )
    if has_undefined:
        overall = "UNDEFINED_BUSINESS_RULE"
    elif has_fail:
        overall = "FAIL"
    elif has_blocked:
        overall = "BLOCKED"
    elif len(reports) == 25 and all(status == "PASS" for status in statuses.values()):
        overall = "PASS"
    else:
        overall = "BLOCKED"
    totals = Counter()
    total_checks = Counter()
    total_mismatches = Counter()
    for data in reports.values():
        for key, value in data.get("rows_checked", {}).items():
            if isinstance(value, int):
                totals[key] += value
        total_checks.update(data.get("check_counts", {}))
        total_mismatches.update(data.get("mismatch_counts", {}))
    output = {
        "status": overall,
        "scope": "independent full-population accounting and DAILY_DISTRIBUTION audit",
        "source_run_id": CP_F_RUN_ID,
        "historical_run_id": HISTORICAL_RUN_ID,
        "source_sha": SOURCE_SHA,
        "master_seed": MASTER_SEED,
        "preflight_status": preflight_status,
        "preflight_report": preflight_report,
        "expected_scenario_count": 25,
        "scenario_reports_received": len(reports),
        "missing_scenarios": missing,
        "scenario_statuses": statuses,
        "rows_checked": dict(sorted(totals.items())),
        "check_counts": dict(sorted(total_checks.items())),
        "mismatch_counts": dict(sorted(total_mismatches.items())),
        "all_scenarios_passed": overall == "PASS" and len(reports) == 25 and not missing,
        "scenario_evidence": {scenario: {
            "status": reports[scenario].get("status"),
            "rows_checked": reports[scenario].get("rows_checked"),
            "daily_dates": reports[scenario].get("daily_dates"),
            "files": reports[scenario].get("files"),
            "check_counts": reports[scenario].get("check_counts"),
            "mismatch_counts": reports[scenario].get("mismatch_counts"),
            "error": reports[scenario].get("error"),
            "details": reports[scenario].get("details"),
        } for scenario in sorted(reports)},
    }
    write_json(output_path, output)
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0 if overall == "PASS" else 1

def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p_pre = sub.add_parser("preflight")
    p_pre.add_argument("--output-dir", required=True, type=Path)
    p_scenario = sub.add_parser("scenario")
    p_scenario.add_argument("--scenario", required=True)
    p_scenario.add_argument("--input-index", required=True, type=Path)
    p_scenario.add_argument("--output", required=True, type=Path)
    p_aggregate = sub.add_parser("aggregate")
    p_aggregate.add_argument("--reports-dir", required=True, type=Path)
    p_aggregate.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "preflight":
        return preflight(args.output_dir)
    if args.command == "scenario":
        return run_scenario_audit(args.scenario, args.input_index, args.output)
    return aggregate_reports(args.reports_dir, args.output)

if __name__ == "__main__":
    raise SystemExit(main())
