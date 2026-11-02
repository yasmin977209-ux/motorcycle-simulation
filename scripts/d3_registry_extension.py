"""Build the D3 supplemental Number Registry from existing, pinned source artifacts only.

No simulation, trial, Monte Carlo, N expansion, backfill, or zero-fill is performed.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

import pyarrow.parquet as pq

from scripts.s6_artifact_reader import (
    S6ArtifactReader, PINS, S6_SOURCE, S6_COHORT, C100_SOURCE, C100_COHORT, MASTER_SEED,
)
from scripts.s6_number_registry import (
    CURRENT_REFERENCE_SHA256, stable_id, display_fraction, unit, no_floats, blob_sha1,
)

SOURCE_DATE_CUTOFF_UTC = "2026-10-31T00:00:00Z"
OWNER_APPROVED_SOURCE_DATE_EXCEPTION = "D3_ONLY_PINNED_ARTIFACTS_2026-11-02"
SOURCE_RUN_CREATED_AT_UTC = {
    40773412377: "2026-10-28T21:36:57Z",
    41098699740: "2026-10-30T17:25:30Z",
    40263424595: "2026-10-26T03:18:29Z",
}


def enforce_source_date_cutoff(source_date_exception: str | None = None) -> None:
    """Fail closed unless the exact three pinned artifacts have an explicit D3-only owner waiver."""
    if source_date_exception not in (None, OWNER_APPROVED_SOURCE_DATE_EXCEPTION):
        raise ValueError("D3_SOURCE_DATE_EXCEPTION_TOKEN_INVALID")
    for key, pin in PINS.items():
        created_at = SOURCE_RUN_CREATED_AT_UTC.get(pin.run_id)
        if created_at is None:
            raise ValueError("SOURCE_ARTIFACT_RUN_DATE_MISSING:" + key)
        if created_at < SOURCE_DATE_CUTOFF_UTC and source_date_exception != OWNER_APPROVED_SOURCE_DATE_EXCEPTION:
            raise ValueError(
                "SOURCE_ARTIFACT_PRE_CUTOFF_PROHIBITED:"
                + key + ":run_id=" + str(pin.run_id)
                + ":created_at=" + str(created_at)
                + ":cutoff=" + SOURCE_DATE_CUTOFF_UTC
            )


BASE_REGISTRY_SHA256 = "743ffcced8de09a766870f201c352aabcf5789c43c84bfeae654a939700e4f87"
BASE_REGISTRY_BYTES = 24137036
EXPECTED_AGGREGATE_HEAD = "4f2f2cc16d0cb5125262088704febccbae6f50ed"
EXPECTED_FULL_LOGGING_HEAD = "e3c2098df9fc5dbc126eb1e77ad35c493ff3ac70"
EXPECTED_C100_HEAD = "24050f15bc7eb3097e20f76785a45c5d177643dd"
EXPECTED_SUMMARY_SHA256 = "66c8c4530073dba14e4082eb13ab492d304fa6841e3db08ae6c38509de66d522"
EXPECTED_C100_GOLDEN_SHA256 = "39950d91c3b40b11bea0997b8504ac932a57bcc0ef8e0c51e12d031342a53327"
EXPECTED_C100_MANIFEST_SHA256 = "2097284d77ead6b00492bf75830d09aeef8dbde4aaa1c15dae6a877dc7e9ff04"
GOLDEN_MEMBER = "docs/golden/v2.3/C100_GOLDEN_965281d52441cd0d4b744e211c9f68ee4cdc3753.json"
C100_MANIFEST_MEMBER = "docs/audits/S4_C100_GOLDEN_MANIFEST_965281d52441cd0d4b744e211c9f68ee4cdc3753.json"
ROOT_MANIFEST_MEMBER = "stagec-output/representative_full_logging_manifest.json"
SELECTION_MEMBER = "stagec-output/representative_selection_map.json"
UNIQUE_MEMBER = "stagec-output/representative_unique_keys.json"
ROLES = ("P50", "P10", "P90", "LossCase", "MaxCase")
FULL_LOGGING_NORMALIZED_STATUS = "NOT_VERIFIED_105_OF_105"
DAILY_METRICS = ("Cash", "Net_Equity", "Active_Bikes", "Owned_Transferred_Bikes", "Pending_Claims")
ACCOUNTING_FIELDS = (
    "Accounts_Receivable", "Accumulated_Depreciation", "Gross_Bike_Assets",
    "Guarantee_Claim_Receivable", "Total_Assets",
)
ASSET_FIELDS = (
    "bike_id", "purchase_date", "funding_completion_date", "actual_ready_date",
    "scheduled_ready_date", "delivery_date", "gross_cost", "accumulated_depreciation",
    "net_book_value", "current_state", "lifecycle_cycle_number", "termination_count",
    "secondary_cycle_count", "usage_days", "prep_paid", "customs_paid",
    "current_contract_id", "current_tenant_id", "active_settlement_receivable_id",
    "settlement_business_days_elapsed", "settlement_legacy_debt_original",
    "settlement_legacy_debt_remaining", "settlement_rent_collected_total",
    "settlement_rent_due_total", "settlement_start_date", "pending_writeoff_today", "source",
)
LEDGER_FILES = (
    "daily_snapshots.jsonl.gz", "assets.jsonl.gz", "claims.jsonl.gz",
    "contracts.jsonl.gz", "ar_rollforward.jsonl.gz", "asset_rollforward.jsonl.gz",
    "cash_rollforward.jsonl.gz", "equity_rollforward.jsonl.gz",
)
ROLLFORWARD_KEYS = ("ar_rollforward", "asset_rollforward", "cash_rollforward", "equity_rollforward")
C100_COMMON_DAILY_FIELDS = (
    "Active_Bikes", "Capital", "Cash", "Final_Close_Date", "Net_Equity",
    "Owned_Transferred_Bikes", "Partner1_Reinvestment_Balance",
    "Partner2_Reinvestment_Balance", "Pending_Claims", "Retained_Earnings", "date",
)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def json_bytes(value: object) -> bytes:
    no_floats(value)
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def ledger_number_id(artifact_sha256: str, scenario_id: str, trial_id: int, member: str, row_index: int, field: str) -> str:
    return stable_id("NR-", [
        "D3_LEDGER_NUMBER_V1", artifact_sha256, scenario_id, trial_id, member, row_index, field,
    ])


def source_entry(
    *, scenario_id: str, sample_n: int, metric_name: str, value: Fraction,
    artifact: dict, member: str, member_sha256: str, member_size_bytes: int,
    source_commit: str, source_sha: str, cohort_id: str,
    n_total: int, n_closed: int, n_censored: int, n_unique_paths: int,
    calculation_method: str,
) -> dict:
    n, d = value.numerator, value.denominator
    number_id = stable_id("NR-", [
        "D3_AGGREGATE_NUMBER_V1", artifact["sha256"], scenario_id, sample_n,
        metric_name, member, n, d,
    ])
    return {
        "number_id": number_id,
        "metric_name": metric_name,
        "scenario_id": scenario_id,
        "sample_n": sample_n,
        "source_artifact_id": artifact["artifact_id"],
        "source_run_id": artifact["run_id"],
        "source_member": member,
        "source_member_sha256": member_sha256,
        "source_member_size_bytes": member_size_bytes,
        "source_artifact_sha256": artifact["sha256"],
        "source_file_path": member,
        "source_commit": source_commit,
        "source_sha": source_sha,
        "cohort_id": cohort_id,
        "numerator": n,
        "denominator": d,
        "exact_value": {"numerator": n, "denominator": d},
        "display_value": display_fraction(n, d),
        "unit": unit(metric_name.split(".")[-1]),
        "calculation_method": calculation_method,
        "rounding_method": "ROUND_HALF_EVEN_IF_NON_INTEGER_ELSE_EXACT_INTEGER",
        "N_total": n_total,
        "N_closed": n_closed,
        "N_censored": n_censored,
        "N_unique_paths": n_unique_paths,
        "gate_status": None,
        "evidence_status": "VERIFIED_LIVE",
        "locator": f"{member}#{scenario_id}/N{sample_n}/{metric_name}",
    }


def read_rows(archive, member: str) -> list[dict]:
    return list(archive.iter_jsonl_gzip(member))


def validate_int_fields(rows: list[dict], fields: tuple[str, ...], context: str) -> None:
    for i, row in enumerate(rows):
        for field in fields:
            if field not in row or type(row[field]) is not int:
                raise ValueError(f"REPRESENTATIVE_INTEGER_FIELD_INVALID:{context}:{i}:{field}")


def filtered_asset(row: dict) -> dict:
    # Deliberately exclude lifecycle_history and receivables_ledger: those nested histories
    # are not required in the D3 per-bike asset schedule and are preserved in the source ZIP.
    return {key: row.get(key) for key in ASSET_FIELDS}


def close_date_rows(
    scenario_id: str, dates: list[str], *, source_sha: str, cohort_id: str,
    artifact: dict, member: str, member_sha256: str, member_size_bytes: int,
    source_commit: str, n_total: int, n_unique_paths: int,
) -> list[dict]:
    counts = Counter(dates)
    if not dates or any(not isinstance(x, str) or len(x) != 10 for x in dates):
        raise ValueError("FINAL_CLOSE_DATE_SOURCE_INVALID:" + scenario_id)
    if sum(counts.values()) != n_total:
        raise ValueError("FINAL_CLOSE_DATE_TOTAL_MISMATCH:" + scenario_id)
    out = []
    for close_date, count in sorted(counts.items()):
        number_id = stable_id("NR-", [
            "D3_CLOSE_DATE_COUNT_V1", artifact["sha256"], scenario_id, close_date, count, member,
        ])
        out.append({
            "scenario_id": scenario_id, "source_sha": source_sha, "cohort_id": cohort_id,
            "final_close_date": close_date, "trial_count": count, "trial_count_number_id": number_id,
            "N_total": n_total, "N_closed": n_total, "N_censored": 0,
            "N_unique_paths": n_unique_paths, "source_artifact_id": artifact["artifact_id"],
            "source_run_id": artifact["run_id"], "source_artifact_sha256": artifact["sha256"],
            "source_member": member, "source_member_sha256": member_sha256,
            "source_member_size_bytes": member_size_bytes, "source_commit": source_commit,
            "evidence_status": "VERIFIED_LIVE", "locator": f"{member}#{scenario_id}/{close_date}",
        })
    return out


def verify_all_full_logging_members(full, root: dict) -> tuple[int, int]:
    verified = 0
    audit_pass = 0
    if (
        root.get("role_assignment_count") != 125
        or root.get("unique_key_count") != 105
        or root.get("full_logging_keys_completed") != 105
        or root.get("full_logging_keys_failed") != 0
        or len(root.get("results", [])) != 105
    ):
        raise ValueError("FULL_LOGGING_ROOT_COUNTS_INVALID")
    for result in root["results"]:
        folder = result["folder"]
        prefix = f"stagec-output/full_logging/{folder}/"
        tm_raw = full.read_bytes(prefix + "trial_manifest.json")
        audit_raw = full.read_bytes(prefix + "post_write_audit.json")
        if sha256(tm_raw) != result["trial_manifest_sha256"] or sha256(audit_raw) != result["post_write_audit_sha256"]:
            raise ValueError("REPRESENTATIVE_SIDECAR_HASH_MISMATCH:" + folder)
        tm = json.loads(tm_raw.decode("utf-8"))
        audit = json.loads(audit_raw.decode("utf-8"))
        for member, meta in tm.get("files", {}).items():
            raw = full.read_bytes(prefix + member)
            if len(raw) != meta.get("size_bytes") or sha256(raw) != meta.get("sha256"):
                raise ValueError("REPRESENTATIVE_MEMBER_HASH_MISMATCH:" + folder + ":" + member)
            verified += 1
        if (
            audit.get("status") != "PASS_SCOPED_REPRESENTATIVE_FULL_LOGGING"
            or audit.get("rollforward_mismatch_count") != 0
            or audit.get("balance_mismatch_count") != 0
            or audit.get("trial_fingerprint_match") is not True
        ):
            raise ValueError("REPRESENTATIVE_POST_WRITE_AUDIT_MISMATCH:" + folder)
        audit_pass += 1
    return verified, audit_pass


def extract_case(full, result: dict, role_map: dict, artifact: dict) -> dict:
    scenario_id, trial_id, folder = result["scenario_id"], int(result["trial_id"]), result["folder"]
    prefix = f"stagec-output/full_logging/{folder}/"
    tm = full.read_json(prefix + "trial_manifest.json")
    trial_result = full.read_json(prefix + "trial_result.json")
    audit = full.read_json(prefix + "post_write_audit.json")
    roles = sorted(role_map.get((scenario_id, trial_id), []))
    if "P50" not in roles:
        raise ValueError("P50_ROLE_ASSIGNMENT_MISSING:" + scenario_id)
    if (
        trial_result.get("scenario_id") != scenario_id
        or trial_result.get("trial_id") != trial_id
        or trial_result.get("source_sha") != tm.get("source_sha")
        or trial_result.get("cohort_id") != tm.get("cohort_id")
        or trial_result.get("trial_fingerprint") != tm.get("actual_trial_fingerprint")
        or tm.get("actual_trial_fingerprint") != tm.get("expected_trial_fingerprint")
        or audit.get("trial_fingerprint") != trial_result.get("trial_fingerprint")
    ):
        raise ValueError("P50_TRIAL_IDENTITY_INVALID:" + scenario_id)
    members = {}
    for member in LEDGER_FILES + ("trial_result.json",):
        meta = tm.get("files", {}).get(member)
        if not isinstance(meta, dict):
            raise ValueError("P50_SOURCE_MEMBER_METADATA_MISSING:" + scenario_id + ":" + member)
        members[member] = {"sha256": meta["sha256"], "size_bytes": meta["size_bytes"]}

    daily = read_rows(full, prefix + "daily_snapshots.jsonl.gz")
    assets_raw = read_rows(full, prefix + "assets.jsonl.gz")
    claims = read_rows(full, prefix + "claims.jsonl.gz")
    contracts = read_rows(full, prefix + "contracts.jsonl.gz")
    rollforwards = {
        "ar_rollforward": read_rows(full, prefix + "ar_rollforward.jsonl.gz"),
        "asset_rollforward": read_rows(full, prefix + "asset_rollforward.jsonl.gz"),
        "cash_rollforward": read_rows(full, prefix + "cash_rollforward.jsonl.gz"),
        "equity_rollforward": read_rows(full, prefix + "equity_rollforward.jsonl.gz"),
    }
    if len(daily) != tm.get("daily_rows") or len(assets_raw) != tm.get("asset_rows"):
        raise ValueError("P50_DAILY_OR_ASSET_ROW_COUNT_INVALID:" + scenario_id)
    if len(claims) != tm.get("claim_rows") or len(contracts) != tm.get("contract_rows"):
        raise ValueError("P50_CLAIM_OR_CONTRACT_ROW_COUNT_INVALID:" + scenario_id)
    if any(len(rows) != len(daily) for rows in rollforwards.values()):
        raise ValueError("P50_ROLLFORWARD_ROW_COUNT_INVALID:" + scenario_id)
    dates = [row.get("date") for row in daily]
    if not dates or dates != sorted(dates) or dates[-1] != trial_result.get("final_close_date"):
        raise ValueError("P50_DAILY_DATE_RANGE_INVALID:" + scenario_id)
    if any(not isinstance(x, str) or len(x) != 10 for x in dates):
        raise ValueError("P50_DAILY_DATE_INVALID:" + scenario_id)
    for row in daily:
        if (
            row.get("scenario_id") != scenario_id
            or row.get("trial_id") != trial_id
            or row.get("source_sha") != tm.get("source_sha")
            or row.get("cohort_id") != tm.get("cohort_id")
        ):
            raise ValueError("P50_DAILY_IDENTITY_MISMATCH:" + scenario_id)
    validate_int_fields(daily, ACCOUNTING_FIELDS + DAILY_METRICS + (
        "Balance_Difference", "Capital", "Liabilities", "Net_Bike_Assets",
        "Net_Equity", "Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance",
        "Retained_Earnings", "Total_Equity",
    ), scenario_id)
    if any(row.get(field) is None for row in daily for field in ACCOUNTING_FIELDS):
        raise ValueError("P50_ACCOUNTING_FIELD_NULL:" + scenario_id)
    assets = [filtered_asset(row) for row in assets_raw]
    bike_ids = [row.get("bike_id") for row in assets]
    if len(bike_ids) != len(set(bike_ids)) or any(not isinstance(x, str) for x in bike_ids):
        raise ValueError("P50_ASSET_ID_DUPLICATE_OR_INVALID:" + scenario_id)
    for i, row in enumerate(assets):
        for field in ("gross_cost", "accumulated_depreciation", "net_book_value", "lifecycle_cycle_number", "termination_count", "secondary_cycle_count", "usage_days"):
            if type(row.get(field)) is not int:
                raise ValueError(f"P50_ASSET_NUMERIC_FIELD_INVALID:{scenario_id}:{i}:{field}")
    for key, rows in rollforwards.items():
        if [x.get("date") for x in rows] != dates:
            raise ValueError("P50_ROLLFORWARD_DATE_ALIGNMENT_INVALID:" + scenario_id + ":" + key)
        for i, row in enumerate(rows):
            for field, value in row.items():
                if field != "date" and type(value) is not int:
                    raise ValueError(f"P50_ROLLFORWARD_INTEGER_FIELD_INVALID:{scenario_id}:{key}:{i}:{field}")
    for i, row in enumerate(claims):
        for field, value in row.items():
            if field not in ("claim_id", "bike_id", "claim_source", "contract_id", "created_date", "guarantor_id", "settlement_date", "settlement_due_date", "status", "tenant_id") and value is not None and type(value) is not int:
                raise ValueError(f"P50_CLAIM_NUMERIC_FIELD_INVALID:{scenario_id}:{i}:{field}")
    for i, row in enumerate(contracts):
        for field, value in row.items():
            if field not in ("bike_id", "contract_id", "contract_type", "first_eligible_friday_date", "guarantor_id", "maturity_date", "start_date", "status", "tenant_id") and value is not None and type(value) is not int:
                raise ValueError(f"P50_CONTRACT_NUMERIC_FIELD_INVALID:{scenario_id}:{i}:{field}")
    summary_fields = (
        "bad_debt", "claims_created", "cumulative_project_profit", "final_cash",
        "final_net_project_equity", "guarantee_recovered", "held_assets",
        "operating_net_profit", "owned_bikes", "partner1_final_entitlement",
        "partner2_final_entitlement", "secondary_cycle_count", "termination_count",
        "total_operating_revenue",
    )
    summary = {key: trial_result.get(key) for key in summary_fields}
    for key, value in summary.items():
        if type(value) is not int:
            raise ValueError("P50_TRIAL_SUMMARY_FIELD_INVALID:" + scenario_id + ":" + key)
    return {
        "scenario_id": scenario_id, "cohort_id": tm["cohort_id"], "source_sha": tm["source_sha"],
        "trial_id": trial_id, "role_assignments": roles,
        "trial_fingerprint": trial_result["trial_fingerprint"],
        "final_close_date": trial_result["final_close_date"],
        "source_commit": trial_result.get("execution_git_commit") or EXPECTED_FULL_LOGGING_HEAD,
        "source_artifact_id": artifact["artifact_id"], "source_run_id": artifact["run_id"],
        "source_artifact_sha256": artifact["sha256"], "source_folder": folder,
        "source_member_prefix": prefix, "source_members": members,
        "daily_rows": daily, "assets": assets, "claims": claims, "contracts": contracts,
        "rollforwards": rollforwards, "trial_summary": summary,
    }



def extract_daily_case(full, result: dict, role_map: dict, artifact: dict) -> dict:
    """Read every selected representative role key's raw daily log and summary.

    This is a read-only extraction from the pinned 105-key Full Logging artifact.
    It does not create or replay any Trial.
    """
    scenario_id, trial_id, folder = result["scenario_id"], int(result["trial_id"]), result["folder"]
    prefix = f"stagec-output/full_logging/{folder}/"
    tm = full.read_json(prefix + "trial_manifest.json")
    trial_result = full.read_json(prefix + "trial_result.json")
    audit = full.read_json(prefix + "post_write_audit.json")
    roles = sorted(role_map.get((scenario_id, trial_id), []))
    if not roles:
        raise ValueError("REPRESENTATIVE_ROLE_ASSIGNMENT_MISSING:" + scenario_id)
    if (
        trial_result.get("scenario_id") != scenario_id
        or trial_result.get("trial_id") != trial_id
        or trial_result.get("source_sha") != tm.get("source_sha")
        or trial_result.get("cohort_id") != tm.get("cohort_id")
        or trial_result.get("trial_fingerprint") != tm.get("actual_trial_fingerprint")
        or tm.get("actual_trial_fingerprint") != tm.get("expected_trial_fingerprint")
        or audit.get("trial_fingerprint") != trial_result.get("trial_fingerprint")
    ):
        raise ValueError("REPRESENTATIVE_TRIAL_IDENTITY_INVALID:" + scenario_id)
    member = "daily_snapshots.jsonl.gz"
    meta = tm.get("files", {}).get(member)
    if not isinstance(meta, dict):
        raise ValueError("REPRESENTATIVE_DAILY_MEMBER_METADATA_MISSING:" + scenario_id)
    daily = read_rows(full, prefix + member)
    if len(daily) != tm.get("daily_rows"):
        raise ValueError("REPRESENTATIVE_DAILY_ROW_COUNT_INVALID:" + scenario_id)
    dates = [row.get("date") for row in daily]
    if not dates or dates != sorted(dates) or dates[-1] != trial_result.get("final_close_date"):
        raise ValueError("REPRESENTATIVE_DAILY_DATE_RANGE_INVALID:" + scenario_id)
    if any(not isinstance(x, str) or len(x) != 10 for x in dates):
        raise ValueError("REPRESENTATIVE_DAILY_DATE_INVALID:" + scenario_id)
    for row in daily:
        if (
            row.get("scenario_id") != scenario_id
            or row.get("trial_id") != trial_id
            or row.get("source_sha") != tm.get("source_sha")
            or row.get("cohort_id") != tm.get("cohort_id")
        ):
            raise ValueError("REPRESENTATIVE_DAILY_IDENTITY_MISMATCH:" + scenario_id)
    validate_int_fields(daily, ACCOUNTING_FIELDS + DAILY_METRICS + (
        "Balance_Difference", "Capital", "Liabilities", "Net_Bike_Assets",
        "Net_Equity", "Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance",
        "Retained_Earnings", "Total_Equity",
    ), scenario_id)
    summary_fields = (
        "bad_debt", "claims_created", "cumulative_project_profit", "final_cash",
        "final_net_project_equity", "guarantee_recovered", "held_assets",
        "operating_net_profit", "owned_bikes", "partner1_final_entitlement",
        "partner2_final_entitlement", "secondary_cycle_count", "termination_count",
        "total_operating_revenue",
    )
    summary = {key: trial_result.get(key) for key in summary_fields}
    if any(type(value) is not int for value in summary.values()):
        raise ValueError("REPRESENTATIVE_TRIAL_SUMMARY_FIELD_INVALID:" + scenario_id)
    return {
        "scenario_id": scenario_id, "cohort_id": tm["cohort_id"], "source_sha": tm["source_sha"],
        "trial_id": trial_id, "role_assignments": roles,
        "trial_fingerprint": trial_result["trial_fingerprint"],
        "final_close_date": trial_result["final_close_date"],
        "source_commit": trial_result.get("execution_git_commit") or EXPECTED_FULL_LOGGING_HEAD,
        "source_artifact_id": artifact["artifact_id"], "source_run_id": artifact["run_id"],
        "source_artifact_sha256": artifact["sha256"], "source_folder": folder,
        "source_member_prefix": prefix,
        "source_member": prefix + member, "source_member_sha256": meta["sha256"],
        "source_member_size_bytes": meta["size_bytes"],
        "daily_rows": daily, "trial_summary": summary,
    }


def build_sensitivity_entries(entries: list[dict]) -> list[dict]:
    mean_entries = {
        item["scenario_id"]: item for item in entries
        if item.get("metric_name", "").endswith(".mean.Cumulative_Project_Profit")
    }
    if len(mean_entries) != 25:
        raise ValueError("D3_SENSITIVITY_MEAN_PROFIT_COVERAGE_INVALID")
    output = []
    c_levels, g_levels = (30, 50, 70, 85, 100), (0, 30, 50, 70, 100)

    def add(dimension: str, held_fixed: str, left_sid: str, right_sid: str) -> None:
        left, right = mean_entries[left_sid], mean_entries[right_sid]
        left_value = Fraction(left["numerator"], left["denominator"])
        right_value = Fraction(right["numerator"], right["denominator"])
        delta = right_value - left_value
        n, d = delta.numerator, delta.denominator
        number_id = stable_id("NR-", [
            "D3_SENSITIVITY_DELTA_V1", left["number_id"], right["number_id"],
            dimension, held_fixed, n, d,
        ])
        output.append({
            "number_id": number_id, "dimension": dimension, "held_fixed": held_fixed,
            "from_scenario_id": left_sid, "to_scenario_id": right_sid,
            "from_number_id": left["number_id"], "to_number_id": right["number_id"],
            "numerator": n, "denominator": d, "exact_value": {"numerator": n, "denominator": d},
            "display_value": display_fraction(n, d), "unit": "YER",
            "calculation_method": "EXACT_FRACTION_DIFFERENCE_OF_REGISTERED_MEAN_CUMULATIVE_PROJECT_PROFIT",
            "source_number_ids": [left["number_id"], right["number_id"]],
            "evidence_status": "VERIFIED_LIVE",
        })

    for g in g_levels:
        for left_c, right_c in zip(c_levels, c_levels[1:]):
            add("COLLECTION", f"G={g:03d}", f"C{left_c:03d}_G{g:03d}", f"C{right_c:03d}_G{g:03d}")
    for c_level in c_levels:
        for left_g, right_g in zip(g_levels, g_levels[1:]):
            add("GUARANTEE", f"C={c_level:03d}", f"C{c_level:03d}_G{left_g:03d}", f"C{c_level:03d}_G{right_g:03d}")
    if len(output) != 40 or len({x["number_id"] for x in output}) != 40:
        raise ValueError("D3_SENSITIVITY_ENTRY_COUNT_INVALID")
    return output


def build_extension(paths: dict[str, str], base_registry_path: str, source_date_exception: str | None = None) -> dict:
    enforce_source_date_cutoff(source_date_exception)
    base_raw = Path(base_registry_path).read_bytes()
    if len(base_raw) != BASE_REGISTRY_BYTES or sha256(base_raw) != BASE_REGISTRY_SHA256:
        raise ValueError("BASE_NUMBER_REGISTRY_PIN_MISMATCH")
    reader = S6ArtifactReader(paths).open_all()
    try:
        aggregate = reader.archives["aggregate"]
        full = reader.archives["full_logging"]
        c100 = reader.archives["c100"]
        artifact_meta = {}
        expected_heads = {
            "aggregate": EXPECTED_AGGREGATE_HEAD,
            "full_logging": EXPECTED_FULL_LOGGING_HEAD,
            "c100": EXPECTED_C100_HEAD,
        }
        for key, pin in PINS.items():
            artifact_meta[key] = {
                "artifact_id": pin.artifact_id, "run_id": pin.run_id,
                "size_bytes": pin.size_bytes, "sha256": pin.sha256,
                "workflow_run_head_sha": expected_heads[key],
                "run_created_at_utc": SOURCE_RUN_CREATED_AT_UTC[pin.run_id],
                "source_date_exception": source_date_exception or "NONE",
                "source_date_exception_scope": "D3_ONLY_EXACT_THREE_PINNED_ARTIFACTS" if source_date_exception else "NONE",
                "source_date_exception_owner_approval": "APPROVED_2026-11-02" if source_date_exception else "NONE",
                "filename": pin.filename,
                "evidence_status": "VERIFIED_LIVE",
            }

        manifest = aggregate.read_json("manifest.json")
        if (
            manifest.get("source_sha") != S6_SOURCE or manifest.get("cohort_id") != S6_COHORT
            or manifest.get("master_seed") != MASTER_SEED or manifest.get("run_id") != str(PINS["aggregate"].run_id)
            or manifest.get("git_commit") != EXPECTED_AGGREGATE_HEAD or manifest.get("checkpoint_n") != 2400
            or manifest.get("scenario_count") != 20 or manifest.get("status") != "EXECUTED"
        ):
            raise ValueError("S6_AGGREGATE_MANIFEST_IDENTITY_MISMATCH")
        summary_meta = manifest.get("files", {}).get("trials_summary.parquet", {})
        summary_raw = aggregate.read_bytes("trials_summary.parquet")
        if (
            len(summary_raw) != summary_meta.get("size_bytes")
            or sha256(summary_raw) != summary_meta.get("sha256")
            or sha256(summary_raw) != EXPECTED_SUMMARY_SHA256
        ):
            raise ValueError("S6_TRIALS_SUMMARY_MEMBER_PIN_MISMATCH")
        table = pq.read_table(io.BytesIO(summary_raw))
        required = {
            "scenario_id", "trial_id", "cumulative_project_profit", "final_close_date",
            "final_net_project_equity", "trial_fingerprint", "source_sha", "cohort_id", "schema_version",
        }
        if not required.issubset(set(table.schema.names)):
            raise ValueError("S6_TRIALS_SUMMARY_SCHEMA_MISSING")
        s6_rows = table.to_pylist()
        if len(s6_rows) != 48000:
            raise ValueError("S6_TRIALS_SUMMARY_ROW_COUNT_INVALID")
        summaries = {x["scenario_id"]: x for x in manifest["scenario_summaries"]}
        if len(summaries) != 20:
            raise ValueError("S6_SCENARIO_SUMMARY_COUNT_INVALID")
        grouped = defaultdict(list)
        seen = set()
        for row in s6_rows:
            sid, tid = row["scenario_id"], row["trial_id"]
            if (
                row["source_sha"] != S6_SOURCE or row["cohort_id"] != S6_COHORT
                or not isinstance(row["trial_fingerprint"], str) or len(row["trial_fingerprint"]) != 64
                or (sid, tid) in seen or sid not in summaries or type(tid) is not int
                or type(row["cumulative_project_profit"]) is not int
                or not isinstance(row["final_close_date"], str)
            ):
                raise ValueError("S6_TRIALS_SUMMARY_ROW_IDENTITY_OR_FIELD_INVALID")
            seen.add((sid, tid))
            grouped[sid].append(row)
        aggregate_entries = []
        close_dates = []
        for sid, rows in sorted(grouped.items()):
            sm = summaries[sid]
            if (
                len(rows) != 2400 or sorted(x["trial_id"] for x in rows) != list(range(1, 2401))
                or sm.get("n_total") != 2400 or sm.get("n_closed") != 2400 or sm.get("n_censored") != 0
            ):
                raise ValueError("S6_TRIALS_SUMMARY_SCENARIO_COVERAGE_INVALID:" + sid)
            mean_profit = Fraction(sum(x["cumulative_project_profit"] for x in rows), len(rows))
            aggregate_entries.append(source_entry(
                scenario_id=sid, sample_n=2400, metric_name=f"{sid}.N2400.mean.Cumulative_Project_Profit",
                value=mean_profit, artifact=artifact_meta["aggregate"], member="trials_summary.parquet",
                member_sha256=sha256(summary_raw), member_size_bytes=len(summary_raw),
                source_commit=EXPECTED_AGGREGATE_HEAD, source_sha=S6_SOURCE, cohort_id=S6_COHORT,
                n_total=2400, n_closed=2400, n_censored=0, n_unique_paths=int(sm["n_unique_paths"]),
                calculation_method="EXACT_FRACTION_MEAN_FROM_ALL_2400_TRIALS",
            ))
            close_dates.extend(close_date_rows(
                sid, [x["final_close_date"] for x in rows], source_sha=S6_SOURCE, cohort_id=S6_COHORT,
                artifact=artifact_meta["aggregate"], member="trials_summary.parquet",
                member_sha256=sha256(summary_raw), member_size_bytes=len(summary_raw),
                source_commit=EXPECTED_AGGREGATE_HEAD, n_total=2400, n_unique_paths=int(sm["n_unique_paths"]),
            ))

        cmeta_raw = c100.read_bytes(C100_MANIFEST_MEMBER)
        golden_raw = c100.read_bytes(GOLDEN_MEMBER)
        if sha256(cmeta_raw) != EXPECTED_C100_MANIFEST_SHA256 or sha256(golden_raw) != EXPECTED_C100_GOLDEN_SHA256:
            raise ValueError("C100_GOLDEN_OR_MANIFEST_HASH_MISMATCH")
        cmeta = json.loads(cmeta_raw.decode("utf-8"))
        golden = json.loads(golden_raw.decode("utf-8"))
        if (
            cmeta.get("source_sha") != C100_SOURCE or cmeta.get("cohort_id") != C100_COHORT
            or cmeta.get("trial_count_total") != 1500 or cmeta.get("trial_ids_per_scenario") != [1, 300]
            or cmeta.get("N_unique_paths") != 1 or cmeta.get("workflow_run_id") != str(PINS["c100"].run_id)
            or golden.get("source_sha") != C100_SOURCE or golden.get("cohort_id") != C100_COHORT
            or golden.get("master_seed") != MASTER_SEED or golden.get("historical_golden_mutated") is not False
            or golden.get("historical_results_mutated") is not False or golden.get("N_unique_paths") != 1
            or golden.get("trial_count_total") != 1500 or golden.get("trial_count_per_scenario") != 300
        ):
            raise ValueError("C100_GOLDEN_IDENTITY_INVALID")

        c100_member_meta = {
            GOLDEN_MEMBER: {"sha256": sha256(golden_raw), "size_bytes": len(golden_raw)},
            C100_MANIFEST_MEMBER: {"sha256": sha256(cmeta_raw), "size_bytes": len(cmeta_raw)},
        }
        c100_scenarios = golden.get("scenarios", {})
        if len(c100_scenarios) != 5:
            raise ValueError("C100_SCENARIO_COVERAGE_INVALID")
        for sid, scenario_data in sorted(c100_scenarios.items()):
            records = scenario_data.get("trial_records", [])
            ss = scenario_data.get("scenario_summary", {})
            if (
                len(records) != 300 or sorted(x.get("trial_id") for x in records) != list(range(1, 301))
                or ss.get("trial_count") != 300 or ss.get("N_unique_paths") != 1
                or ss.get("trial_fingerprint_unique_count") != 1 or ss.get("G_status") != "G_INERT"
                or ss.get("degeneracy_status") != "DEGENERATE_DETERMINISTIC"
            ):
                raise ValueError("C100_SCENARIO_DEGENERACY_OR_COVERAGE_INVALID:" + sid)
            values = [x.get("financial_values", {}) for x in records]
            fingerprints = {x.get("trial_fingerprint") for x in records}
            dates = [x.get("final_close_date") for x in (v for v in values)]
            if len(fingerprints) != 1 or None in fingerprints or len(set(dates)) != 1 or not dates[0]:
                raise ValueError("C100_TRIAL_RECORD_IDENTITY_INVALID:" + sid)
            fields = ("cumulative_project_profit", "final_net_project_equity", "final_cash",
                      "partner1_final_entitlement", "partner2_final_entitlement", "held_assets",
                      "termination_count", "bad_debt")
            for field in fields:
                if any(type(v.get(field)) is not int for v in values):
                    raise ValueError("C100_FINANCIAL_FIELD_INVALID:" + sid + ":" + field)
            def mean(field: str) -> Fraction:
                return Fraction(sum(v[field] for v in values), len(values))
            def quantile(field: str, q: int) -> Fraction:
                # The source explicitly proves one unique financial path across all 300 records.
                vals = [v[field] for v in values]
                if len(set(vals)) != 1:
                    raise ValueError("C100_DETERMINISTIC_QUANTILE_CONFLICT:" + sid + ":" + field)
                return Fraction(vals[0], 1)
            probability = Fraction(sum(1 for v in values if v["final_net_project_equity"] < 0), len(values))
            metrics = [
                ("P50_Cumulative_Project_Profit", quantile("cumulative_project_profit", 50)),
                ("Probability_of_Accounting_Loss", probability),
                ("indicator.P10_Cumulative_Project_Profit", quantile("cumulative_project_profit", 10)),
                ("indicator.P50_Cumulative_Project_Profit", quantile("cumulative_project_profit", 50)),
                ("indicator.P90_Cumulative_Project_Profit", quantile("cumulative_project_profit", 90)),
                ("indicator.P90_Final_Cash", quantile("final_cash", 90)),
                ("indicator.P90_Held_Assets", quantile("held_assets", 90)),
                ("indicator.P90_Termination_Count", quantile("termination_count", 90)),
                ("indicator.Probability_of_Accounting_Loss", probability),
                ("mean.Final_Net_Project_Equity", mean("final_net_project_equity")),
                ("mean.Partner1_Final_Entitlement", mean("partner1_final_entitlement")),
                ("mean.Partner2_Final_Entitlement", mean("partner2_final_entitlement")),
                ("mean.Cumulative_Project_Profit", mean("cumulative_project_profit")),
            ]
            for metric, value in metrics:
                aggregate_entries.append(source_entry(
                    scenario_id=sid, sample_n=300, metric_name=f"{sid}.N300.{metric}",
                    value=value, artifact=artifact_meta["c100"], member=GOLDEN_MEMBER,
                    member_sha256=sha256(golden_raw), member_size_bytes=len(golden_raw),
                    source_commit=EXPECTED_C100_HEAD, source_sha=C100_SOURCE, cohort_id=C100_COHORT,
                    n_total=300, n_closed=300, n_censored=0, n_unique_paths=1,
                    calculation_method="SOURCE_C100_GOLDEN_300_IDENTICAL_TRIAL_RECORDS",
                ))
            close_dates.extend(close_date_rows(
                sid, dates, source_sha=C100_SOURCE, cohort_id=C100_COHORT,
                artifact=artifact_meta["c100"], member=GOLDEN_MEMBER,
                member_sha256=sha256(golden_raw), member_size_bytes=len(golden_raw),
                source_commit=EXPECTED_C100_HEAD, n_total=300, n_unique_paths=1,
            ))

        root = full.read_json(ROOT_MANIFEST_MEMBER)
        select = full.read_json(SELECTION_MEMBER)
        unique = full.read_json(UNIQUE_MEMBER)
        if (
            root.get("governing_decision_id") != "D-2026-10-30-REFERENCE-V2.4.0"
            or root.get("governing_reference_sha256") != CURRENT_REFERENCE_SHA256
            or select.get("governing_decision_id") != "D-2026-10-30-REFERENCE-V2.4.0"
            or select.get("governing_reference_sha256") != CURRENT_REFERENCE_SHA256
            or len(select.get("assignments", [])) != 125 or len(unique.get("unique_keys", [])) != 105
        ):
            raise ValueError("FULL_LOGGING_REFERENCE_OR_SELECTION_IDENTITY_INVALID")
        verified_members, audit_pass = verify_all_full_logging_members(full, root)
        role_map = defaultdict(list)
        for assignment in select["assignments"]:
            role_map[(assignment["scenario_id"], int(assignment["trial_id"]))].append(assignment["role"])
        root_by_key = {(x["scenario_id"], int(x["trial_id"])): x for x in root["results"]}
        if len(root_by_key) != 105:
            raise ValueError("FULL_LOGGING_ROOT_KEY_DUPLICATE")
        representative_role_cases = [
            extract_daily_case(full, result, role_map, artifact_meta["full_logging"])
            for _, result in sorted(root_by_key.items())
        ]
        if (
            len(representative_role_cases) != 105
            or len({(x["scenario_id"], x["trial_id"]) for x in representative_role_cases}) != 105
            or sum(len(x["role_assignments"]) for x in representative_role_cases) != 125
        ):
            raise ValueError("REPRESENTATIVE_ROLE_CASE_COVERAGE_INVALID")

        cases = []
        for sid in sorted(set(s["scenario_id"] for s in select["assignments"])):
            p50_assignments = [x for x in select["assignments"] if x["scenario_id"] == sid and x["role"] == "P50"]
            if len(p50_assignments) != 1:
                raise ValueError("P50_SELECTION_COUNT_INVALID:" + sid)
            assignment = p50_assignments[0]
            key = (sid, int(assignment["trial_id"]))
            result = root_by_key.get(key)
            if result is None or result.get("trial_fingerprint") != assignment.get("trial_fingerprint"):
                raise ValueError("P50_SELECTION_ROOT_MISMATCH:" + sid)
            case = extract_case(full, result, role_map, artifact_meta["full_logging"])
            if case["trial_fingerprint"] != assignment["trial_fingerprint"]:
                raise ValueError("P50_SELECTION_FINGERPRINT_MISMATCH:" + sid)
            cases.append(case)
        if len(cases) != 25 or len({x["scenario_id"] for x in cases}) != 25:
            raise ValueError("P50_SCENARIO_COVERAGE_INVALID")
        c100_case_map = {x["scenario_id"]: x for x in cases if x["cohort_id"] == C100_COHORT}
        golden_rows = golden["canonical_daily_ledger"]["rows"]
        c100_matches = 0
        for sid, case in c100_case_map.items():
            if len(case["daily_rows"]) != len(golden_rows) or len(golden_rows) != 2198:
                raise ValueError("C100_CANONICAL_DAILY_ROW_COUNT_INVALID:" + sid)
            record = next(x for x in c100_scenarios[sid]["trial_records"] if x["trial_id"] == 1)
            if record["trial_fingerprint"] != case["trial_fingerprint"]:
                raise ValueError("C100_GOLDEN_TRIAL_FINGERPRINT_MISMATCH:" + sid)
            for i, (golden_row, full_row) in enumerate(zip(golden_rows, case["daily_rows"])):
                source_snapshot = golden_row["daily_snapshot"]
                if any(source_snapshot.get(field) != full_row.get(field) for field in C100_COMMON_DAILY_FIELDS):
                    raise ValueError(f"C100_GOLDEN_DAILY_PATH_MISMATCH:{sid}:{i}")
            c100_matches += 1

        close_total = sum(x["trial_count"] for x in close_dates)
        if close_total != 49500 or len({x["scenario_id"] for x in close_dates}) != 25:
            raise ValueError("FINAL_CLOSE_DATE_TOTAL_OR_SCENARIO_COVERAGE_INVALID")
        if sum(1 for x in close_dates if x["cohort_id"] == S6_COHORT) != sum(
            len({row["final_close_date"] for row in grouped[sid]}) for sid in grouped
        ):
            raise ValueError("S6_FINAL_CLOSE_DATE_DISTRIBUTION_COVERAGE_INVALID")

        sensitivity_entries = build_sensitivity_entries(aggregate_entries)
        extension = {
            "schema_version": "d3-number-registry-extension-v1",
            "extension_id": stable_id("D3NRX-", [BASE_REGISTRY_SHA256, PINS["aggregate"].sha256, PINS["full_logging"].sha256, PINS["c100"].sha256]),
            "base_registry_sha256": BASE_REGISTRY_SHA256,
            "base_registry_size_bytes": BASE_REGISTRY_BYTES,
            "current_governing_reference_sha256": CURRENT_REFERENCE_SHA256,
            "source_artifacts": artifact_meta,
            "aggregate_entries": aggregate_entries,
            "sensitivity_entries": sensitivity_entries,
            "representative_cases": cases,
            "representative_role_cases": representative_role_cases,
            "final_close_date_distribution": sorted(close_dates, key=lambda x: (x["scenario_id"], x["final_close_date"])),
            "full_logging_validation": {
                "unique_trial_keys": 105, "role_assignments": 125, "completed_keys": 105,
                "failed_keys": 0, "verified_member_count": verified_members,
                "post_write_audit_pass_count": audit_pass, "p50_case_count": len(cases),
                "representative_role_case_count": len(representative_role_cases),
                "role_assignments_covered": sum(len(x["role_assignments"]) for x in representative_role_cases),
                "p50_scenario_coverage": 25, "normalized_status": FULL_LOGGING_NORMALIZED_STATUS,
                "scope": "105_REPRESENTATIVE_KEYS_ONLY_NOT_48000",
            },
            "c100_validation": {
                "scenario_count": 5, "trial_count_per_scenario": 300, "N_unique_paths": 1,
                "G_status": "G_INERT", "degeneracy_status": "DEGENERATE_DETERMINISTIC",
                "daily_rows_per_scenario": 2198, "golden_common_field_path_matches": c100_matches,
                "golden_trial_fingerprint_matches": 5, "golden_revalidation": "NOT_RUN",
                "daily_reuse_status": "PASS_SCOPED_C100_DAILY_REUSE",
            },
            "close_date_validation": {
                "S6_trial_count": 48000, "C100_trial_count": 1500, "total_trial_count": close_total,
                "scenario_count": 25, "S6_scenarios": 20, "C100_scenarios": 5,
                "S6_summary_member_sha256": sha256(summary_raw),
                "C100_golden_member_sha256": sha256(golden_raw),
            },
            "representative_accounting_fields": {
                "status": "VERIFIED_SCOPED_25_P50_CASES",
                "fields": list(ACCOUNTING_FIELDS),
                "historical_48k_status": "MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS",
                "do_not_infer_or_zero_fill": True,
            },
            "number_id_scheme": "NR-{sha256(D3_LEDGER_NUMBER_V1, artifact_sha256, scenario_id, trial_id, source_member, row_index, field)[:24]}",
            "limitations": [
                "Full Logging is 105 representative keys only, not 48,000 trial daily logs.",
                "The five historical accounting fields remain missing for the full 48,000-trial cohort; representative P50 values are source-backed only.",
                "C100 Golden revalidation remains NOT_RUN; daily reuse is separately identity- and content-checked.",
                "Financial Gate A remains PASS_SCOPED only; Production Gate A remains NOT_DECLARED.",
                "Gate B N=2400 remains FAIL_SCOPED (10/10); Stability remains NOT_CONVERGED (0/60); N=4800 remains NOT_EXECUTED.",
            ],
        }
        no_floats(extension)
        return extension
    finally:
        reader.close()


def build(args) -> dict:
    extension = build_extension(
        {"aggregate": args.aggregate, "full_logging": args.full_logging, "c100": args.c100},
        args.base_registry,
        args.source_date_exception,
    )
    raw = json_bytes(extension)
    compressed = gzip.compress(raw, compresslevel=9, mtime=0)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_bytes(compressed)
    audit = {
        "status": "PASS_SCOPED_D3_REGISTRY_EXTENSION",
        "extension_path": args.output,
        "extension_bytes": len(compressed),
        "extension_sha256": sha256(compressed),
        "extension_git_blob_sha1": blob_sha1(compressed),
        "uncompressed_bytes": len(raw),
        "extension_id": extension["extension_id"],
        "sensitivity_entry_count": len(extension.get("sensitivity_entries", [])),
        "base_registry_sha256": extension["base_registry_sha256"],
        "source_artifacts": extension["source_artifacts"],
        "full_logging_validation": extension["full_logging_validation"],
        "c100_validation": extension["c100_validation"],
        "close_date_validation": extension["close_date_validation"],
        "representative_accounting_fields": extension["representative_accounting_fields"],
        "no_trials_or_simulation_executed": True,
    }
    Path(args.audit).parent.mkdir(parents=True, exist_ok=True)
    Path(args.audit).write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False, sort_keys=True))
    return audit


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    for name in ("aggregate", "full-logging", "c100", "base-registry", "output", "audit"):
        b.add_argument("--" + name, required=True)
    b.add_argument("--source-date-exception", choices=(OWNER_APPROVED_SOURCE_DATE_EXCEPTION,), default=None)
    args = parser.parse_args()
    build(args)


if __name__ == "__main__":
    main()
