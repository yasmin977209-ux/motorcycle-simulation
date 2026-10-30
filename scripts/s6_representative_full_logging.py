from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import tempfile
import time
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq

import constants
import monte_carlo
from entities import EventType
from scripts.audit_s6_daily_balance_artifact import audit_representative_full_logging_trial
from scripts.s6_daily_path_identity import (
    DAILY_BALANCE_INTEGER_FIELDS,
    DAILY_BALANCE_SCHEMA_VERSION,
    MODEL_SCHEMA_VERSION,
    build_daily_path_identity_evidence,
)

EXPECTED_SUMMARY_SHA256 = "66c8c4530073dba14e4082eb13ab492d304fa6841e3db08ae6c38509de66d522"
EXPECTED_SOURCE_SHA = "da1a9ea9b5cd789c944de3f07b08395bb67c49e7"
EXPECTED_COHORT_ID = "s6-v23-da1a9ea9"
EXPECTED_C100_SOURCE_SHA = "965281d52441cd0d4b744e211c9f68ee4cdc3753"
EXPECTED_C100_COHORT_ID = "c100-v23-s4-20261026-965281d5"
EXPECTED_C100_GOLDEN_SHA256 = "39950d91c3b40b11bea0997b8504ac932a57bcc0ef8e0c51e12d031342a53327"
EXPECTED_C100_MANIFEST_SHA256 = "2097284d77ead6b00492bf75830d09aeef8dbde4aaa1c15dae6a877dc7e9ff04"
EXPECTED_AGGREGATE_RUN_ID = 40773412377
EXPECTED_C100_RUN_ID = 40263424595
EXPECTED_MASTER_SEED = 20270101
STOCHASTIC_COLLECTIONS = (30, 50, 70, 85)
RECOVERY_LEVELS = (100, 70, 50, 30, 0)
C100_SCENARIOS = ("C100_G100", "C100_G070", "C100_G050", "C100_G030", "C100_G000")
ROLES = ("P50", "P10", "P90", "LossCase", "MaxCase")
ROLLFORWARD_FILES = {
    "cash_rollforward": "cash_rollforward.jsonl.gz",
    "ar_rollforward": "ar_rollforward.jsonl.gz",
    "asset_rollforward": "asset_rollforward.jsonl.gz",
    "equity_rollforward": "equity_rollforward.jsonl.gz",
}
EVENT_TYPES = {item.value for item in EventType}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if is_dataclass(value):
        return jsonable(asdict(value))
    if isinstance(value, dict):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"REPRESENTATIVE_JSON_TYPE_UNSUPPORTED:{type(value).__name__}")


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(jsonable(value), ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def write_jsonl_gzip(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="\n", compresslevel=6) as handle:
        for row in rows:
            handle.write(json.dumps(jsonable(row), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
            handle.write("\n")


def read_jsonl_gzip(path: Path) -> list[dict[str, Any]]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def exact_linear_target(values: list[int], q_num: int, q_den: int = 100) -> tuple[int, int]:
    """Return the exact rational target for numpy's linear quantile definition."""
    from fractions import Fraction

    if not values:
        raise RuntimeError("REPRESENTATIVE_SELECTION_EMPTY_COHORT")
    ordered = sorted(values)
    position = Fraction((len(ordered) - 1) * q_num, q_den)
    lower = position.numerator // position.denominator
    remainder = position - lower
    upper = min(lower + 1, len(ordered) - 1)
    target = Fraction(ordered[lower]) * (1 - remainder) + Fraction(ordered[upper]) * remainder
    # Cross-check against the explicitly named NumPy linear quantile method.
    numpy_target = Fraction(str(float(np.quantile(np.asarray(ordered, dtype=np.int64), q_num / q_den, method="linear"))))
    if abs(float(target - numpy_target)) > 1e-7:
        raise RuntimeError("REPRESENTATIVE_LINEAR_QUANTILE_IMPLEMENTATION_MISMATCH")
    return target.numerator, target.denominator


def validate_trial_fingerprint_match(expected: str, actual: str) -> dict[str, Any]:
    if not isinstance(expected, str) or len(expected) != 64 or expected != actual:
        raise RuntimeError("REPRESENTATIVE_FINANCIAL_FINGERPRINT_MISMATCH")
    return {"status": "PASS_SCOPED_FINGERPRINT_MATCH", "expected": expected, "actual": actual}


def select_five_roles(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if not rows:
        raise RuntimeError("REPRESENTATIVE_SELECTION_EMPTY_COHORT")
    ids = [row.get("trial_id") for row in rows]
    if any(type(value) is not int or value < 1 for value in ids) or len(ids) != len(set(ids)):
        raise RuntimeError("REPRESENTATIVE_TRIAL_IDS_INVALID_OR_DUPLICATE")
    if any(type(row.get("final_net_project_equity")) is not int for row in rows):
        raise RuntimeError("REPRESENTATIVE_FINAL_EQUITY_MISSING_OR_NON_INTEGER")
    equities = [row["final_net_project_equity"] for row in rows]
    selections: dict[str, tuple[int, int] | int] = {}
    for role, q_num in (("P10", 10), ("P50", 50), ("P90", 90)):
        numerator, denominator = exact_linear_target(equities, q_num)
        from fractions import Fraction
        target = Fraction(numerator, denominator)
        selected = min(
            rows,
            key=lambda row: (abs(Fraction(row["final_net_project_equity"]) - target), row["trial_id"]),
        )
        selections[role] = (selected["trial_id"], numerator, denominator)
    selections["LossCase"] = min(
        rows, key=lambda row: (row["final_net_project_equity"], row["trial_id"])
    )["trial_id"]
    selections["MaxCase"] = min(
        rows, key=lambda row: (-row["final_net_project_equity"], row["trial_id"])
    )["trial_id"]
    by_id = {row["trial_id"]: row for row in rows}
    output: dict[str, dict[str, Any]] = {}
    for role in ROLES:
        selected = selections[role]
        if role in ("P10", "P50", "P90"):
            trial_id, numerator, denominator = selected
            target = {"numerator": numerator, "denominator": denominator}
        else:
            trial_id = selected
            target = None
        row = by_id[trial_id]
        output[role] = {
            "role": role,
            "scenario_id": row["scenario_id"],
            "trial_id": trial_id,
            "final_net_project_equity": row["final_net_project_equity"],
            "trial_fingerprint": row["trial_fingerprint"],
            "source_sha": row["source_sha"],
            "cohort_id": row["cohort_id"],
            "schema_version": row["schema_version"],
            "rng_checksum": row.get("rng_checksum"),
            "rng_draw_count": row.get("rng_draw_count"),
            "rng_checksum_fingerprint_sha256": row.get("rng_checksum_fingerprint_sha256"),
            "quantile_target_exact": target,
            "selection_rule": (
                "nearest_to_linear_quantile_Final_Net_Project_Equity"
                if target is not None
                else ("argmin_Final_Net_Project_Equity" if role == "LossCase" else "argmax_Final_Net_Project_Equity")
            ),
            "tie_break": "smallest_trial_id",
        }
    return output


def expected_stochastic_scenarios() -> set[str]:
    return {
        f"C{collection:03d}_G{recovery:03d}"
        for collection in STOCHASTIC_COLLECTIONS
        for recovery in RECOVERY_LEVELS
    }


def load_s6_selection(aggregate_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    parquet_path = aggregate_dir / "trials_summary.parquet"
    manifest_path = aggregate_dir / "manifest.json"
    if not parquet_path.is_file() or not manifest_path.is_file():
        raise RuntimeError("REPRESENTATIVE_S6_AGGREGATE_INPUT_MISSING")
    if sha256_file(parquet_path) != EXPECTED_SUMMARY_SHA256:
        raise RuntimeError("REPRESENTATIVE_S6_TRIALS_SUMMARY_SHA256_MISMATCH")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        manifest.get("run_id") != str(EXPECTED_AGGREGATE_RUN_ID)
        or manifest.get("source_sha") != EXPECTED_SOURCE_SHA
        or manifest.get("cohort_id") != EXPECTED_COHORT_ID
        or manifest.get("checkpoint_n") != 2400
        or manifest.get("master_seed") != EXPECTED_MASTER_SEED
        or manifest.get("scenario_count") != 20
        or manifest.get("total_scenario_combinations") != 25
        or manifest.get("status") != "EXECUTED"
        or manifest.get("files", {}).get("trials_summary.parquet", {}).get("sha256") != EXPECTED_SUMMARY_SHA256
    ):
        raise RuntimeError("REPRESENTATIVE_S6_AGGREGATE_MANIFEST_IDENTITY_MISMATCH")
    table = pq.read_table(parquet_path)
    required = {
        "scenario_id", "trial_id", "final_net_project_equity", "trial_fingerprint",
        "source_sha", "cohort_id", "schema_version",
    }
    if not required.issubset(set(table.schema.names)):
        raise RuntimeError("REPRESENTATIVE_S6_SUMMARY_SCHEMA_MISSING_FIELDS")
    rows = table.to_pylist()
    if len(rows) != 48000:
        raise RuntimeError(f"REPRESENTATIVE_S6_SUMMARY_ROW_COUNT_MISMATCH:{len(rows)}")
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if (
            row.get("source_sha") != EXPECTED_SOURCE_SHA
            or row.get("cohort_id") != EXPECTED_COHORT_ID
            or row.get("schema_version") != MODEL_SCHEMA_VERSION
            or not isinstance(row.get("trial_fingerprint"), str)
            or len(row["trial_fingerprint"]) != 64
        ):
            raise RuntimeError("REPRESENTATIVE_S6_SUMMARY_ROW_IDENTITY_MISMATCH")
        grouped.setdefault(str(row["scenario_id"]), []).append(row)
    if set(grouped) != expected_stochastic_scenarios():
        raise RuntimeError("REPRESENTATIVE_S6_SCENARIO_SET_MISMATCH")
    selected: list[dict[str, Any]] = []
    for scenario in sorted(grouped):
        scenario_rows = grouped[scenario]
        if len(scenario_rows) != 2400 or sorted(row["trial_id"] for row in scenario_rows) != list(range(1, 2401)):
            raise RuntimeError(f"REPRESENTATIVE_S6_TRIAL_COVERAGE_MISMATCH:{scenario}")
        role_map = select_five_roles(scenario_rows)
        for role in ROLES:
            entry = dict(role_map[role])
            entry.update(
                selection_source="S6_N2400_TRIALS_SUMMARY_PARQUET",
                source_run_id=40731224990,
                source_run_attempt=1,
                aggregate_run_id=EXPECTED_AGGREGATE_RUN_ID,
                aggregate_artifact_id=12852969854,
                aggregate_manifest_sha256=sha256_file(manifest_path),
                summary_file_sha256=EXPECTED_SUMMARY_SHA256,
                cohort_trial_count=2400,
            )
            selected.append(entry)
    return selected, manifest


def load_c100_selection(c100_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    golden_path = c100_root / "docs/golden/v2.3/C100_GOLDEN_965281d52441cd0d4b744e211c9f68ee4cdc3753.json"
    c100_manifest_path = c100_root / "docs/audits/S4_C100_GOLDEN_MANIFEST_965281d52441cd0d4b744e211c9f68ee4cdc3753.json"
    if not golden_path.is_file() or not c100_manifest_path.is_file():
        raise RuntimeError("REPRESENTATIVE_C100_GOLDEN_INPUT_MISSING")
    if sha256_file(golden_path) != EXPECTED_C100_GOLDEN_SHA256:
        raise RuntimeError("REPRESENTATIVE_C100_GOLDEN_SHA256_MISMATCH")
    if sha256_file(c100_manifest_path) != EXPECTED_C100_MANIFEST_SHA256:
        raise RuntimeError("REPRESENTATIVE_C100_MANIFEST_SHA256_MISMATCH")
    golden = json.loads(golden_path.read_text(encoding="utf-8"))
    if (
        golden.get("source_sha") != EXPECTED_C100_SOURCE_SHA
        or golden.get("cohort_id") != EXPECTED_C100_COHORT_ID
        or golden.get("master_seed") != EXPECTED_MASTER_SEED
        or golden.get("schema_version") != MODEL_SCHEMA_VERSION
        or golden.get("historical_golden_mutated") is not False
        or golden.get("historical_results_mutated") is not False
        or set(golden.get("scenarios", {})) != set(C100_SCENARIOS)
    ):
        raise RuntimeError("REPRESENTATIVE_C100_GOLDEN_IDENTITY_MISMATCH")
    selected: list[dict[str, Any]] = []
    for scenario in C100_SCENARIOS:
        scenario_entry = golden["scenarios"][scenario]
        records = scenario_entry.get("trial_records", [])
        if (
            len(records) != 300
            or sorted(record.get("trial_id") for record in records) != list(range(1, 301))
            or scenario_entry.get("scenario_summary", {}).get("trial_fingerprint_unique_count") != 1
            or scenario_entry.get("scenario_summary", {}).get("N_unique_paths") != 1
        ):
            raise RuntimeError(f"REPRESENTATIVE_C100_TRIAL_COVERAGE_OR_DEGENERACY_INVALID:{scenario}")
        normalized = []
        for record in records:
            values = record.get("financial_values", {})
            normalized.append({
                "scenario_id": scenario,
                "trial_id": record["trial_id"],
                "final_net_project_equity": values.get("final_net_project_equity"),
                "trial_fingerprint": record.get("trial_fingerprint"),
                "source_sha": EXPECTED_C100_SOURCE_SHA,
                "cohort_id": EXPECTED_C100_COHORT_ID,
                "schema_version": MODEL_SCHEMA_VERSION,
                "rng_checksum": record.get("rng_checksum"),
                "rng_draw_count": record.get("rng_draw_count"),
                "rng_checksum_fingerprint_sha256": record.get("rng_checksum_fingerprint_sha256"),
                "financial_values": values,
            })
        role_map = select_five_roles(normalized)
        for role in ROLES:
            entry = dict(role_map[role])
            record = next(item for item in normalized if item["trial_id"] == entry["trial_id"])
            entry.update(
                selection_source="CROSS_COHORT_DETERMINISTIC_REUSE",
                source_run_id=EXPECTED_C100_RUN_ID,
                source_run_attempt=1,
                c100_artifact_id=12630457193,
                golden_file_sha256=EXPECTED_C100_GOLDEN_SHA256,
                c100_manifest_sha256=EXPECTED_C100_MANIFEST_SHA256,
                cohort_trial_count=300,
                rng_checksum=record["rng_checksum"],
                rng_draw_count=record["rng_draw_count"],
                rng_checksum_fingerprint_sha256=record["rng_checksum_fingerprint_sha256"],
                financial_values=record["financial_values"],
            )
            selected.append(entry)
    return selected, golden


def build_unique_keys(assignments: list[dict[str, Any]]) -> dict[str, Any]:
    if len(assignments) != 125:
        raise RuntimeError(f"REPRESENTATIVE_ROLE_ASSIGNMENT_COUNT_MISMATCH:{len(assignments)}")
    by_key: dict[tuple[str, int], dict[str, Any]] = {}
    for assignment in assignments:
        key = (assignment["scenario_id"], assignment["trial_id"])
        current = by_key.get(key)
        identity = (assignment["source_sha"], assignment["cohort_id"], assignment["trial_fingerprint"])
        if current is None:
            by_key[key] = {
                "scenario_id": key[0],
                "trial_id": key[1],
                "source_sha": assignment["source_sha"],
                "cohort_id": assignment["cohort_id"],
                "schema_version": assignment["schema_version"],
                "trial_fingerprint": assignment["trial_fingerprint"],
                "selection_source": assignment["selection_source"],
                "role_assignments": [],
            }
        else:
            previous = (current["source_sha"], current["cohort_id"], current["trial_fingerprint"])
            if identity != previous:
                raise RuntimeError(f"REPRESENTATIVE_KEY_CROSS_COHORT_IDENTITY_COLLISION:{key}")
        by_key[key]["role_assignments"].append(assignment["role"])
    unique = []
    for key in sorted(by_key):
        item = by_key[key]
        item["role_assignments"] = sorted(item["role_assignments"], key=ROLES.index)
        item["role_assignment_count"] = len(item["role_assignments"])
        item["duplicate_role_assignment_count"] = len(item["role_assignments"]) - 1
        unique.append(item)
    return {
        "schema_version": "s6-representative-unique-keys-v1",
        "key_definition": "(scenario_id, trial_id); source/cohort/fingerprint mismatches for same key fail closed",
        "role_assignment_count": len(assignments),
        "unique_key_count": len(unique),
        "duplicate_role_assignment_count": len(assignments) - len(unique),
        "unique_keys": unique,
    }


def validate_daily_balance_rows(rows: list[dict[str, Any]], *, trial_id: int, source_sha: str, cohort_id: str, scenario_id: str) -> dict[str, Any]:
    if not rows:
        raise RuntimeError("REPRESENTATIVE_DAILY_ROWS_MISSING")
    dates = []
    for row in rows:
        if (
            row.get("trial_id") != trial_id
            or row.get("source_sha") != source_sha
            or row.get("cohort_id") != cohort_id
            or row.get("scenario_id") != scenario_id
            or row.get("schema_version") != MODEL_SCHEMA_VERSION
            or row.get("daily_balance_schema_version") != DAILY_BALANCE_SCHEMA_VERSION
        ):
            raise RuntimeError("REPRESENTATIVE_DAILY_IDENTITY_MISMATCH")
        for field in DAILY_BALANCE_INTEGER_FIELDS:
            if type(row.get(field)) is not int:
                raise RuntimeError(f"REPRESENTATIVE_DAILY_REQUIRED_INTEGER_MISSING:{field}")
        if row["Partner1_Reinvestment_Balance"] is None or row["Partner2_Reinvestment_Balance"] is None:
            raise RuntimeError("REPRESENTATIVE_PARTNER_DAILY_BALANCE_MISSING")
        if row["Total_Assets"] != row["Total_Equity"] or row["Balance_Difference"] != 0:
            raise RuntimeError("REPRESENTATIVE_DAILY_BALANCE_MISMATCH")
        dates.append(date.fromisoformat(row["date"]))
    if dates != sorted(dates) or dates != [dates[0] + timedelta(days=i) for i in range(len(dates))]:
        raise RuntimeError("REPRESENTATIVE_DAILY_DATE_GAP_OR_ORDER_MISMATCH")
    return {
        "daily_rows_checked": len(rows),
        "balance_rows_checked": len(rows),
        "balance_mismatch_count": 0,
        "partner1_balance_rows": len(rows),
        "partner2_balance_rows": len(rows),
        "first_date": dates[0].isoformat(),
        "last_date": dates[-1].isoformat(),
    }


def validate_rollforward_rows(daily_dates: list[str], cash: list[dict[str, Any]], ar: list[dict[str, Any]], assets: list[dict[str, Any]], equity: list[dict[str, Any]]) -> dict[str, Any]:
    if not daily_dates or any(len(items) != len(daily_dates) for items in (cash, ar, assets, equity)):
        raise RuntimeError("REPRESENTATIVE_ROLLFORWARD_ROW_COUNT_MISMATCH")
    checks = 0
    for c, a, b, e in zip(cash, ar, assets, equity):
        if c["Opening_Cash"] + c["Inflows"] - c["Outflows"] != c["Closing_Cash"]:
            raise RuntimeError("REPRESENTATIVE_CASH_ROLLFORWARD_MISMATCH")
        if c["Outflows"] != c["Operating_Cash_Outflows"] + c["Investing_Cash_Outflows"]:
            raise RuntimeError("REPRESENTATIVE_CASH_OUTFLOW_COMPONENT_MISMATCH")
        if a["Opening_AR"] + a["Accruals"] - a["Collections"] - a["TransfersToGuarantee"] != a["Closing_AR"]:
            raise RuntimeError("REPRESENTATIVE_AR_ROLLFORWARD_MISMATCH")
        if b["Opening_Gross_Bike_Assets"] + b["Capitalized_Purchases_And_Customs"] - b["Gross_Writeoffs_On_Ownership"] != b["Closing_Gross_Bike_Assets"]:
            raise RuntimeError("REPRESENTATIVE_GROSS_ASSET_ROLLFORWARD_MISMATCH")
        if b["Opening_Accumulated_Depreciation"] + b["Expense_Depreciation"] - b["AD_Removed_On_Writeoff"] != b["Closing_Accumulated_Depreciation"]:
            raise RuntimeError("REPRESENTATIVE_DEPRECIATION_ROLLFORWARD_MISMATCH")
        if e["Opening_Equity"] + e["Operating_Net_Profit"] != e["Closing_Equity"]:
            raise RuntimeError("REPRESENTATIVE_EQUITY_ROLLFORWARD_MISMATCH")
        checks += 6
    return {"rollforward_days_checked": len(daily_dates), "rollforward_equation_checks": checks, "rollforward_mismatch_count": 0}


def validate_event_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ids = [row.get("event_id") for row in rows]
    if len(ids) != len(set(ids)):
        raise RuntimeError("REPRESENTATIVE_EVENT_ID_DUPLICATE")
    if any(row.get("event_type") not in EVENT_TYPES for row in rows):
        raise RuntimeError("REPRESENTATIVE_EVENT_TYPE_INVALID")
    return {"event_count": len(rows), "event_ids_unique": True, "event_types_valid": True}


def _write_trial_payload(folder: Path, key: dict[str, Any], execution_commit: str) -> dict[str, Any]:
    result, raw_daily, project = monte_carlo.run_single_trial_full_logging(
        key["scenario_id"], key["trial_id"], master_seed=EXPECTED_MASTER_SEED,
        source_sha=key["source_sha"],
    )
    if project.log_events is not True:
        raise RuntimeError("REPRESENTATIVE_FULL_LOGGING_EVENT_MODE_NOT_ENABLED")
    validate_trial_fingerprint_match(key["trial_fingerprint"], result.trial_fingerprint)
    if key.get("rng_checksum") is not None and result.rng_checksum != key["rng_checksum"]:
        raise RuntimeError("REPRESENTATIVE_RNG_CHECKSUM_MISMATCH")
    if key.get("rng_draw_count") is not None and result.rng_draw_count != key["rng_draw_count"]:
        raise RuntimeError("REPRESENTATIVE_RNG_DRAW_COUNT_MISMATCH")
    if key.get("rng_checksum_fingerprint_sha256") and result.rng_checksum_fingerprint_sha256 != key["rng_checksum_fingerprint_sha256"]:
        raise RuntimeError("REPRESENTATIVE_RNG_AUDIT_FINGERPRINT_MISMATCH")

    daily = []
    for raw in raw_daily:
        row = dict(raw)
        row.update(
            scenario_id=key["scenario_id"], source_sha=key["source_sha"],
            cohort_id=key["cohort_id"], schema_version=MODEL_SCHEMA_VERSION,
        )
        daily.append(row)
    identity = build_daily_path_identity_evidence(
        daily, source_sha=key["source_sha"], cohort_id=key["cohort_id"],
        master_seed=EXPECTED_MASTER_SEED, scenario_id=key["scenario_id"],
        expected_trial_ids=[key["trial_id"]],
        expected_start_date=constants.PROJECT_START_DATE.isoformat(),
        model_schema_version=MODEL_SCHEMA_VERSION,
    )
    daily_audit = validate_daily_balance_rows(
        daily, trial_id=key["trial_id"], source_sha=key["source_sha"],
        cohort_id=key["cohort_id"], scenario_id=key["scenario_id"],
    )
    dates = [row["date"] for row in daily]
    cash = [dict(row, date=dates[i]) for i, row in enumerate(project.cash_rollforward)]
    ar = [dict(row, date=dates[i]) for i, row in enumerate(project.ar_rollforward)]
    assets = [dict(row, date=dates[i]) for i, row in enumerate(project.asset_rollforward)]
    equity = [dict(row, date=dates[i]) for i, row in enumerate(project.equity_rollforward)]
    rollforward_audit = validate_rollforward_rows(dates, cash, ar, assets, equity)
    events = [jsonable(row) for row in project.event_log]
    event_audit = validate_event_rows(events)

    folder.mkdir(parents=True, exist_ok=False)
    trial_result = jsonable(asdict(result))
    trial_result.update(
        source_sha=key["source_sha"], cohort_id=key["cohort_id"],
        schema_version=MODEL_SCHEMA_VERSION, execution_git_commit=execution_commit,
    )
    write_json(folder / "trial_result.json", trial_result)
    write_jsonl_gzip(folder / "daily_snapshots.jsonl.gz", daily)
    write_jsonl_gzip(folder / "events.jsonl.gz", events)
    write_jsonl_gzip(folder / "contracts.jsonl.gz", [jsonable(x) for x in project.contracts.values()])
    write_jsonl_gzip(folder / "claims.jsonl.gz", [jsonable(x) for x in project.guarantee_claims])
    write_jsonl_gzip(folder / "assets.jsonl.gz", [jsonable(x) for x in project.bikes])
    write_jsonl_gzip(folder / "tenants.jsonl.gz", [jsonable(x) for x in project.tenants])
    write_jsonl_gzip(folder / "guarantors.jsonl.gz", [jsonable(x) for x in project.guarantors])
    write_jsonl_gzip(folder / "receivables.jsonl.gz", [jsonable(x) for x in project.receivables])
    for name, values in (
        ("cash_rollforward.jsonl.gz", cash),
        ("ar_rollforward.jsonl.gz", ar),
        ("asset_rollforward.jsonl.gz", assets),
        ("equity_rollforward.jsonl.gz", equity),
    ):
        write_jsonl_gzip(folder / name, values)

    file_names = [
        "trial_result.json", "daily_snapshots.jsonl.gz", "events.jsonl.gz",
        "contracts.jsonl.gz", "claims.jsonl.gz", "assets.jsonl.gz",
        "tenants.jsonl.gz", "guarantors.jsonl.gz", "receivables.jsonl.gz",
        *ROLLFORWARD_FILES.values(),
    ]
    files = {
        name: {"sha256": sha256_file(folder / name), "size_bytes": (folder / name).stat().st_size}
        for name in file_names
    }
    manifest = {
        "schema_version": "s6-representative-full-logging-trial-v1",
        "status": "WRITTEN_PENDING_POST_WRITE_AUDIT",
        "scenario_id": key["scenario_id"],
        "trial_id": key["trial_id"],
        "source_sha": key["source_sha"],
        "cohort_id": key["cohort_id"],
        "selection_source": key["selection_source"],
        "role_assignments": key["role_assignments"],
        "master_seed": EXPECTED_MASTER_SEED,
        "model_schema_version": MODEL_SCHEMA_VERSION,
        "daily_balance_schema_version": DAILY_BALANCE_SCHEMA_VERSION,
        "execution_git_commit": execution_commit,
        "expected_trial_fingerprint": key["trial_fingerprint"],
        "actual_trial_fingerprint": result.trial_fingerprint,
        "daily_rows": len(daily),
        "event_rows": len(events),
        "contract_rows": len(project.contracts),
        "claim_rows": len(project.guarantee_claims),
        "asset_rows": len(project.bikes),
        "files": files,
    }
    write_json(folder / "trial_manifest.json", manifest)

    # Independent read-back: do not trust in-memory rows or pre-write checks.
    read_daily = read_jsonl_gzip(folder / "daily_snapshots.jsonl.gz")
    read_cash = read_jsonl_gzip(folder / "cash_rollforward.jsonl.gz")
    read_ar = read_jsonl_gzip(folder / "ar_rollforward.jsonl.gz")
    read_assets = read_jsonl_gzip(folder / "asset_rollforward.jsonl.gz")
    read_equity = read_jsonl_gzip(folder / "equity_rollforward.jsonl.gz")
    read_events = read_jsonl_gzip(folder / "events.jsonl.gz")
    read_result = json.loads((folder / "trial_result.json").read_text(encoding="utf-8"))
    for name, entry in files.items():
        path = folder / name
        if not path.is_file() or path.stat().st_size != entry["size_bytes"] or sha256_file(path) != entry["sha256"]:
            raise RuntimeError(f"REPRESENTATIVE_POST_WRITE_FILE_HASH_MISMATCH:{name}")
    read_daily_audit = validate_daily_balance_rows(
        read_daily, trial_id=key["trial_id"], source_sha=key["source_sha"],
        cohort_id=key["cohort_id"], scenario_id=key["scenario_id"],
    )
    read_rollforward_audit = validate_rollforward_rows(
        [row["date"] for row in read_daily], read_cash, read_ar, read_assets, read_equity
    )
    read_event_audit = validate_event_rows(read_events)
    if read_result.get("trial_fingerprint") != key["trial_fingerprint"]:
        raise RuntimeError("REPRESENTATIVE_POST_WRITE_TRIAL_FINGERPRINT_MISMATCH")
    read_identity = build_daily_path_identity_evidence(
        read_daily, source_sha=key["source_sha"], cohort_id=key["cohort_id"],
        master_seed=EXPECTED_MASTER_SEED, scenario_id=key["scenario_id"],
        expected_trial_ids=[key["trial_id"]],
        expected_start_date=constants.PROJECT_START_DATE.isoformat(),
        model_schema_version=MODEL_SCHEMA_VERSION,
    )
    report = audit_representative_full_logging_trial(
        folder,
        expected_scenario_id=key["scenario_id"],
        expected_trial_id=key["trial_id"],
        expected_source_sha=key["source_sha"],
        expected_cohort_id=key["cohort_id"],
        expected_trial_fingerprint=key["trial_fingerprint"],
    )
    write_json(folder / "post_write_audit.json", report)
    return {
        "scenario_id": key["scenario_id"],
        "trial_id": key["trial_id"],
        "status": report["status"],
        "trial_fingerprint": result.trial_fingerprint,
        "daily_rows": len(read_daily),
        "event_rows": len(read_events),
        "post_write_audit_sha256": sha256_file(folder / "post_write_audit.json"),
        "trial_manifest_sha256": sha256_file(folder / "trial_manifest.json"),
        "daily_identity_map_sha256": read_identity["summary"]["identity_bound_daily_path_map_sha256"],
        "folder": folder.name,
    }


def run_all(aggregate_dir: Path, c100_root: Path, output_dir: Path) -> dict[str, Any]:
    started = time.monotonic()
    assignments, aggregate_manifest = load_s6_selection(aggregate_dir)
    c100_assignments, c100_golden = load_c100_selection(c100_root)
    assignments.extend(c100_assignments)
    unique_doc = build_unique_keys(assignments)
    assignment_map = {
        "schema_version": "s6-representative-selection-map-v1",
        "governing_decision_id": "D-2026-10-30-REFERENCE-V2.4.0",
        "governing_reference_sha256": "225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b",
        "selection_rule": "v2.4.0 §§14.5-14.6; linear quantiles of Final_Net_Project_Equity; tie smallest trial_id",
        "role_assignment_count": len(assignments),
        "scenario_count": len({item["scenario_id"] for item in assignments}),
        "roles_per_scenario": list(ROLES),
        "assignments": sorted(assignments, key=lambda item: (item["scenario_id"], ROLES.index(item["role"]))),
        "s6_source": {
            "aggregate_run_id": EXPECTED_AGGREGATE_RUN_ID,
            "aggregate_artifact_id": 12852969854,
            "source_run_id": 40731224990,
            "source_sha": EXPECTED_SOURCE_SHA,
            "cohort_id": EXPECTED_COHORT_ID,
            "trials_summary_sha256": EXPECTED_SUMMARY_SHA256,
            "row_count": 48000,
        },
        "c100_reuse": {
            "source_run_id": EXPECTED_C100_RUN_ID,
            "artifact_id": 12630457193,
            "source_sha": EXPECTED_C100_SOURCE_SHA,
            "cohort_id": EXPECTED_C100_COHORT_ID,
            "golden_sha256": EXPECTED_C100_GOLDEN_SHA256,
            "manifest_sha256": EXPECTED_C100_MANIFEST_SHA256,
            "reuse_status": "CROSS_COHORT_DETERMINISTIC_REUSE",
            "rerun_of_original_300_trial_cohort": False,
        },
    }

    parent = output_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    if output_dir.exists():
        raise RuntimeError("REPRESENTATIVE_OUTPUT_TARGET_ALREADY_EXISTS")
    staging = Path(tempfile.mkdtemp(prefix=f"{output_dir.name}.staging-", dir=parent))
    try:
        write_json(staging / "representative_selection_map.json", assignment_map)
        write_json(staging / "representative_unique_keys.json", unique_doc)
        execution_commit = os.environ.get("GITHUB_SHA", "LOCAL_COMMIT_NOT_AVAILABLE")
        results = []
        for index, key in enumerate(unique_doc["unique_keys"], start=1):
            folder_name = f"{key['scenario_id']}__trial_{key['trial_id']:06d}"
            results.append(_write_trial_payload(staging / "full_logging" / folder_name, key, execution_commit))
            print(json.dumps({"progress": index, "total": unique_doc["unique_key_count"], "key": folder_name, "status": results[-1]["status"]}, sort_keys=True), flush=True)

        map_files = {}
        for name in ("representative_selection_map.json", "representative_unique_keys.json"):
            path = staging / name
            map_files[name] = {"sha256": sha256_file(path), "size_bytes": path.stat().st_size}
        full_manifest = {
            "schema_version": "s6-representative-full-logging-manifest-v1",
            "status": "PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING",
            "governing_decision_id": "D-2026-10-30-REFERENCE-V2.4.0",
            "governing_reference_sha256": "225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b",
            "aggregate_run_id": EXPECTED_AGGREGATE_RUN_ID,
            "aggregate_artifact_id": 12852969854,
            "c100_source_run_id": EXPECTED_C100_RUN_ID,
            "c100_artifact_id": 12630457193,
            "master_seed": EXPECTED_MASTER_SEED,
            "role_assignment_count": len(assignments),
            "unique_key_count": unique_doc["unique_key_count"],
            "duplicate_role_assignment_count": unique_doc["duplicate_role_assignment_count"],
            "full_logging_keys_completed": len(results),
            "full_logging_keys_failed": 0,
            "results": results,
            "selection_files": map_files,
            "historical_48000_trial_daily_artifacts": "MISSING_EVIDENCE_NOT_AUDITED_OR_MODIFIED",
            "gate_b_status": "FAIL_SCOPED",
            "stability_status": "NOT_CONVERGED",
            "final_acceptance": "NOT_GRANTED",
            "elapsed_seconds": time.monotonic() - started,
        }
        write_json(staging / "representative_full_logging_manifest.json", full_manifest)
        # Re-read root-level selection and unique-key files before atomic publication.
        reread_map = json.loads((staging / "representative_selection_map.json").read_text(encoding="utf-8"))
        reread_unique = json.loads((staging / "representative_unique_keys.json").read_text(encoding="utf-8"))
        for name, entry in map_files.items():
            path = staging / name
            if path.stat().st_size != entry["size_bytes"] or sha256_file(path) != entry["sha256"]:
                raise RuntimeError(f"REPRESENTATIVE_SELECTION_FILE_READBACK_HASH_MISMATCH:{name}")
        if reread_map["role_assignment_count"] != 125 or reread_unique["unique_key_count"] != len(results):
            raise RuntimeError("REPRESENTATIVE_ROOT_READBACK_MISMATCH")
        if len(results) != unique_doc["unique_key_count"] or any(row["status"] != "PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING" for row in results):
            raise RuntimeError("REPRESENTATIVE_FULL_LOGGING_COMPLETION_MISMATCH")
        if output_dir.exists():
            raise RuntimeError("REPRESENTATIVE_OUTPUT_TARGET_APPEARED_DURING_RUN")
        os.replace(staging, output_dir)
        return full_manifest
    except Exception as exc:
        try:
            write_json(staging / "ERROR_LOG.json", {
                "status": "FAIL_OR_BLOCKED",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "started_at_utc": datetime.utcnow().isoformat() + "Z",
            })
        except Exception:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--aggregate-dir", type=Path, required=True)
    parser.add_argument("--c100-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    manifest = run_all(args.aggregate_dir, args.c100_root, args.output_dir)
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
