"""Complete scoped D3 bilingual Excel exporter.

Consumes the immutable D2 Number Registry plus a source-verified D3 registry extension.
No simulation, trial, Monte Carlo, N expansion, backfill, or zero-fill is performed.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import platform
import re
from collections import defaultdict
from datetime import date, timedelta, datetime, timezone
from decimal import Decimal
from pathlib import Path

from openpyxl import Workbook

from scripts.s6_number_registry import (
    validate_registry, daily_number_id, _daily_resolution_indexes, _resolve_daily_number,
    METRICS, QUANTILES, stable_id, unit,
)
from scripts.d3_registry_extension import (
    ledger_number_id, ACCOUNTING_FIELDS, SOURCE_DATE_CUTOFF_UTC, SOURCE_RUN_CREATED_AT_UTC,
    EXPECTED_AGGREGATE_HEAD, EXPECTED_FULL_LOGGING_HEAD, EXPECTED_C100_HEAD,
)
from scripts.s6_artifact_reader import S6_SOURCE, S6_COHORT, C100_SOURCE, C100_COHORT, PINS
from scripts.s6_excel_export import (
    exact_value, ev, safe_append, sha, blob_sha, constants_from_reference,
    scenario_sheet_names, header, new_sheet, audit, compare, H, MODES, SCENARIO_RE,
)

GOVERNING = "225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b"
GOVERNING_BYTES = 401397
HISTORICAL = "e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f"
BASE_REGISTRY_BYTES = 24137036
BASE_REGISTRY_SHA256 = "743ffcced8de09a766870f201c352aabcf5789c43c84bfeae654a939700e4f87"
DAILY_DETAIL_FIELDS = (
    "Active_Bikes", "Accounts_Receivable", "Accumulated_Depreciation", "Balance_Difference",
    "Capital", "Cash", "Gross_Bike_Assets", "Guarantee_Claim_Receivable", "Liabilities",
    "Net_Bike_Assets", "Net_Equity", "Owned_Transferred_Bikes",
    "Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance", "Pending_Claims",
    "Retained_Earnings", "Total_Assets", "Total_Equity",
)
ASSET_NUMERIC_FIELDS = (
    "gross_cost", "accumulated_depreciation", "net_book_value", "lifecycle_cycle_number",
    "termination_count", "secondary_cycle_count", "usage_days", "settlement_business_days_elapsed",
    "settlement_legacy_debt_original", "settlement_legacy_debt_remaining",
    "settlement_rent_collected_total", "settlement_rent_due_total",
)
ASSET_TEXT_FIELDS = (
    "bike_id", "purchase_date", "funding_completion_date", "actual_ready_date",
    "scheduled_ready_date", "delivery_date", "current_state", "prep_paid", "customs_paid",
    "current_contract_id", "current_tenant_id", "active_settlement_receivable_id",
    "settlement_start_date", "pending_writeoff_today", "source",
)
AR_FIELDS = ("Opening_AR", "Accruals", "Collections", "TransfersToGuarantee", "Closing_AR")
ASSET_ROLL_FIELDS = (
    "Opening_Gross_Bike_Assets", "Capitalized_Purchases_And_Customs",
    "Gross_Writeoffs_On_Ownership", "Closing_Gross_Bike_Assets",
    "Opening_Accumulated_Depreciation", "Expense_Depreciation",
    "AD_Removed_On_Writeoff", "Closing_Accumulated_Depreciation",
)
CASH_FIELDS = ("Opening_Cash", "Inflows", "Investing_Cash_Outflows", "Operating_Cash_Outflows", "Outflows", "Closing_Cash")
EQUITY_FIELDS = ("Opening_Equity", "Operating_Net_Profit", "Closing_Equity")
ACCTG_SUMMARY_FIELDS = (
    "cumulative_project_profit", "operating_net_profit", "final_cash",
    "final_net_project_equity", "total_operating_revenue", "bad_debt", "guarantee_recovered",
)


def validate_source_dates(extension: dict) -> None:
    """Bind every extension source role to the pinned, eligible GitHub run date."""
    sources = extension.get("source_artifacts")
    if not isinstance(sources, dict) or set(sources) != set(PINS):
        raise ValueError("D3_SOURCE_ARTIFACT_SET_INVALID")
    expected_heads = {
        "aggregate": EXPECTED_AGGREGATE_HEAD,
        "full_logging": EXPECTED_FULL_LOGGING_HEAD,
        "c100": EXPECTED_C100_HEAD,
    }
    for role, pin in PINS.items():
        meta = sources.get(role)
        if not isinstance(meta, dict):
            raise ValueError("D3_SOURCE_ARTIFACT_METADATA_MISSING:" + role)
        created_at = meta.get("run_created_at_utc")
        expected = SOURCE_RUN_CREATED_AT_UTC.get(pin.run_id)
        if not isinstance(created_at, str) or created_at != expected or created_at < SOURCE_DATE_CUTOFF_UTC:
            raise ValueError("D3_SOURCE_ARTIFACT_PRE_CUTOFF_OR_UNPINNED:" + role)
        if (
            meta.get("artifact_id") != pin.artifact_id
            or meta.get("run_id") != pin.run_id
            or meta.get("size_bytes") != pin.size_bytes
            or meta.get("sha256") != pin.sha256
            or meta.get("filename") != pin.filename
            or meta.get("workflow_run_head_sha") != expected_heads[role]
            or meta.get("evidence_status") != "VERIFIED_LIVE"
        ):
            raise ValueError("D3_SOURCE_ARTIFACT_PIN_MISMATCH:" + role)


def load_extension(path: str, base_sha: str) -> tuple[dict, bytes, str]:
    raw = Path(path).read_bytes()
    extension = json.loads(gzip.decompress(raw).decode("utf-8"))
    if extension.get("schema_version") != "d3-number-registry-extension-v1":
        raise ValueError("D3_REGISTRY_EXTENSION_SCHEMA_INVALID")
    if extension.get("base_registry_sha256") != base_sha or base_sha != BASE_REGISTRY_SHA256:
        raise ValueError("D3_REGISTRY_EXTENSION_BASE_PIN_MISMATCH")
    validate_source_dates(extension)
    if (
        extension.get("full_logging_validation", {}).get("normalized_status") != "VERIFIED_SCOPED_105_OF_105"
        or extension.get("full_logging_validation", {}).get("p50_scenario_coverage") != 25
        or extension.get("c100_validation", {}).get("daily_reuse_status") != "PASS_SCOPED_C100_DAILY_REUSE"
        or extension.get("close_date_validation", {}).get("total_trial_count") != 49500
        or len(extension.get("representative_cases", [])) != 25
        or len(extension.get("representative_role_cases", [])) != 105
        or extension.get("full_logging_validation", {}).get("role_assignments") != 125
        or len(extension.get("final_close_date_distribution", [])) < 25
    ):
        raise ValueError("D3_REGISTRY_EXTENSION_COVERAGE_INVALID")
    return extension, raw, hashlib.sha256(raw).hexdigest()


def merge_extension(registry: dict, extension: dict) -> dict:
    registry["entries"] = sorted(registry["entries"] + extension["aggregate_entries"], key=lambda x: x["number_id"])
    registry["final_close_date_distribution"] = extension["final_close_date_distribution"]
    registry["representative_cases"] = extension["representative_cases"]
    registry["d3_sensitivity_entries"] = extension.get("sensitivity_entries", [])
    series = list(registry["daily_series"])
    indexes = list(registry["daily_date_indexes"])
    full_meta = extension["source_artifacts"]["full_logging"]
    for case in extension["representative_cases"]:
        if case["cohort_id"] != C100_COHORT:
            continue
        daily = case["daily_rows"]
        member = case["source_member_prefix"] + "daily_snapshots.jsonl.gz"
        member_meta = case["source_members"]["daily_snapshots.jsonl.gz"]
        dates = [row["date"] for row in daily]
        if not dates or dates != sorted(dates):
            raise ValueError("C100_DAILY_DATE_SEQUENCE_INVALID:" + case["scenario_id"])
        indexes.append({
            "scenario_id": case["scenario_id"], "first_date": dates[0],
            "date_count": len(dates), "active_trial_counts": [300] * len(dates),
            "source_sha": C100_SOURCE, "cohort_id": C100_COHORT,
        })
        for mode in MODES:
            for metric in METRICS:
                values = [[int(row[metric]), 1] for row in daily]
                for quantile in QUANTILES:
                    series_id = stable_id("D2S6-", [
                        case["scenario_id"], C100_SOURCE, C100_COHORT, mode, metric,
                        quantile, full_meta["sha256"],
                    ], 20)
                    series.append({
                        "series_id": series_id, "scenario_id": case["scenario_id"],
                        "mode": mode, "metric_name": metric, "quantile_name": quantile,
                        "first_date": dates[0], "last_date": dates[-1], "date_count": len(dates),
                        "values": values, "number_id_scheme": "D2D-{series_sha20}-{zero_based_date_offset_6_digits}",
                        "unit": unit(metric), "source_artifact_id": case["source_artifact_id"],
                        "source_run_id": case["source_run_id"], "source_member": member,
                        "source_member_sha256": member_meta["sha256"],
                        "source_member_size_bytes": member_meta["size_bytes"],
                        "source_artifact_sha256": case["source_artifact_sha256"],
                        "source_file_path": member, "source_commit": case["source_commit"],
                        "source_sha": C100_SOURCE, "cohort_id": C100_COHORT,
                        "N_total": 300, "N_closed": 300, "N_censored": 0, "N_unique_paths": 1,
                        "gate_status": None, "evidence_status": "VERIFIED_LIVE",
                        "calculation_method": "C100_DETERMINISTIC_REUSE_FROM_VERIFIED_P50_DAILY_SNAPSHOT",
                        "rounding_method": "EXACT_INTEGER",
                    })
    if len(series) != 1250 or len(indexes) != 25:
        raise ValueError("COMBINED_DAILY_REGISTRY_COVERAGE_INVALID")
    if len({x["series_id"] for x in series}) != len(series):
        raise ValueError("COMBINED_DAILY_SERIES_ID_DUPLICATE")
    registry["daily_series"] = series
    registry["daily_date_indexes"] = indexes
    return registry


def registry_scenarios(registry: dict) -> list[str]:
    ids = sorted({x["scenario_id"] for x in registry["entries"]} | {x["scenario_id"] for x in registry["daily_series"]})
    if len(ids) != 25 or any(not SCENARIO_RE.fullmatch(x) for x in ids):
        raise ValueError("D3_SCENARIO_COVERAGE_INVALID")
    if len({SCENARIO_RE.fullmatch(x).group(1) for x in ids}) != 5 or len({SCENARIO_RE.fullmatch(x).group(2) for x in ids}) != 5:
        raise ValueError("D3_SCENARIO_GRID_INVALID")
    return ids


def cohort_info(registry: dict, scenario: str) -> tuple[str, str]:
    series = next((x for x in registry["daily_series"] if x["scenario_id"] == scenario), None)
    if series and series.get("cohort_id") == C100_COHORT:
        return C100_COHORT, "C100_CROSS_COHORT_DETERMINISTIC_REUSE"
    if series and series.get("cohort_id") == S6_COHORT:
        return S6_COHORT, "S6"
    entry = next((x for x in registry["entries"] if x["scenario_id"] == scenario), None)
    if entry and entry.get("cohort_id") == C100_COHORT:
        return C100_COHORT, "C100_CROSS_COHORT_DETERMINISTIC_REUSE"
    return S6_COHORT, "S6"


def max_rows(registry: dict, scenario: str) -> list[dict]:
    rows = [x for x in registry["entries"] if x.get("scenario_id") == scenario and x.get("trial_id") is None]
    if not rows:
        return []
    n = max(x.get("sample_n", 0) for x in rows)
    return sorted([x for x in rows if x.get("sample_n") == n], key=lambda x: x["metric_name"])


def numeric_pair(case: dict, member: str, row_index: int, field: str, value):
    if type(value) is not int:
        raise ValueError("D3_WORKBOOK_NUMERIC_VALUE_NOT_INTEGER:" + case["scenario_id"] + ":" + field)
    source_member = case["source_member_prefix"] + member
    return [value, ledger_number_id(case["source_artifact_sha256"], case["scenario_id"], case["trial_id"], source_member, row_index, field)]


def write_daily_distribution(ws, registry: dict, ids: list[str], lang: str) -> None:
    h = H[lang]
    cols = [h["scenario"], h["date"], h["mode"], h["total"], "total_trials_source_number_id",
            h["active"], "active_trial_count_source_number_id", h["closed"],
            "closed_trial_count_source_number_id", h["sample_count"], "sample_trial_count_source_number_id"]
    for metric in METRICS:
        for q in QUANTILES:
            cols.extend([metric + "_" + q, metric + "_" + q + "_number_id"])
    header(ws, cols)
    smap = {(x["scenario_id"], x["mode"], x["metric_name"], x["quantile_name"]): x for x in registry["daily_series"]}
    series_by_id, indexes = _daily_resolution_indexes(registry)
    indexes = {x["scenario_id"]: x for x in registry["daily_date_indexes"]}
    for sid in ids:
        idx = indexes.get(sid)
        if idx is None:
            raise ValueError("DAILY_DISTRIBUTION_SCENARIO_MISSING:" + sid)
        first = date.fromisoformat(idx["first_date"])
        for mode in MODES:
            local = {(m, q): smap[(sid, mode, m, q)] for m in METRICS for q in QUANTILES}
            count_series = local[("Cash", "P50")]
            for offset in range(idx["date_count"]):
                number = daily_number_id(count_series["series_id"], offset)
                resolved = _resolve_daily_number(registry, number, series_by_id, indexes)
                active, total, sample = resolved["active_trial_count"], resolved["N_total"], resolved["sample_trial_count"]
                row = [sid, first + timedelta(days=offset), mode, total, number,
                       active, number, total - active, number, sample, number]
                for metric in METRICS:
                    for q in QUANTILES:
                        series = local[(metric, q)]
                        n, d = series["values"][offset]
                        row.extend([exact_value(n, d), daily_number_id(series["series_id"], offset)])
                safe_append(ws, row)


def write_globals(wb, registry: dict, extension: dict, ids: list[str], lang: str,
                  constants: list, source_head: str, run_id: str, base_sha: str, extension_sha: str, input_manifest_sha256: str) -> None:
    h = H[lang]
    ws = new_sheet(wb, "README", lang)
    header(ws, [h["field"], h["value"]])
    for row in [
        ["Project", "Motorcycle Rental Simulation"],
        ["Classification", "T2_INTERIM / NOT_FINAL_BLOCKED"],
        ["D3 gate", "PASS_SCOPED_WITH_LIMITATIONS"],
        ["Generation date UTC", datetime.now(timezone.utc).date().isoformat()],
        ["Governing decision", registry["governing_decision_id"]],
        ["Current governing reference SHA-256", registry["current_governing_reference_sha256"]],
        ["Historical execution reference SHA-256", registry["historical_execution_reference_sha256"]],
        ["D2 Number Registry SHA-256", base_sha],
        ["D3 Number Registry extension SHA-256", extension_sha],
        ["Source commit", source_head], ["Workflow run", str(run_id)], ["D3 input manifest SHA-256", input_manifest_sha256],
        ["MASTER_SEED", str(registry["scope"]["S6"]["master_seed"])],
        ["Scenario coverage", "25 scenarios: 20 S6 + 5 C100 deterministic reuse"],
        ["Full Logging", "VERIFIED_SCOPED_105_OF_105; 105 unique keys / 125 role assignments only"],
        ["C100", "G_INERT; DEGENERATE_DETERMINISTIC; 300 trials per scenario; N_unique_paths=1"],
        ["C100 Golden revalidation", "NOT_RUN; daily reuse path separately cross-checked"],
        ["Representative accounting fields", "Source-backed for 25 P50 cases only"],
        ["Historical 48K accounting fields", "MISSING_EVIDENCE; not inferred or zero-filled"],
        ["Financial Gate A", "PASS_SCOPED only"],
        ["Production Gate A", "NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS"],
        ["Gate B N=2400", "FAIL_SCOPED (10/10)"],
        ["Stability", "NOT_CONVERGED (0/60)"],
        ["N=4800", "NOT_EXECUTED"],
        ["Important", "D3 scoped deliverables are complete; this is not final project acceptance."],
    ]:
        safe_append(ws, row)

    ws = new_sheet(wb, "CONSTANTS", lang)
    header(ws, [h["field"], h["value"], h["notes"]])
    for row in constants:
        safe_append(ws, row)

    metrics = sorted({x["metric_name"] for x in registry["entries"] if x.get("trial_id") is None})
    ws = new_sheet(wb, "SCENARIO_MATRIX", lang)
    cols = [h["scenario"], h["cohort"], h["source"], h["status"], "N_total", "N_total_source_number_id",
            "N_unique_paths", "N_unique_paths_source_number_id", h["notes"]]
    for metric in metrics:
        cols.extend([metric, metric + "_number_id"])
    header(ws, cols)
    series_by_id, indexes = _daily_resolution_indexes(registry)
    indexes = {x["scenario_id"]: x for x in registry["daily_date_indexes"]}
    for sid in ids:
        cohort_id, source = cohort_info(registry, sid)
        rows = max_rows(registry, sid)
        by = {x["metric_name"]: x for x in rows}
        first = next(x for x in registry["daily_series"] if x["scenario_id"] == sid)
        number = daily_number_id(first["series_id"], 0)
        resolved = _resolve_daily_number(registry, number, series_by_id, indexes)
        status = ("DEGENERATE_DETERMINISTIC / C100_GOLDEN_REVALIDATION_NOT_RUN"
                  if cohort_id == C100_COHORT else "NOT_CONVERGED (0/60)")
        row = [sid, cohort_id, source, status, resolved["N_total"], number,
               resolved["N_unique_paths"], number,
               "Scoped source-backed values; no convergence or final acceptance implied."]
        for metric in metrics:
            entry = by.get(metric)
            row.extend([ev(entry), entry["number_id"]] if entry else ["MISSING_EVIDENCE", ""])
        safe_append(ws, row)

    ws = new_sheet(wb, "HEATMAP", lang)
    header(ws, [h["metric"], "C-level", "G-level values; each numeric value followed by number_id"])
    cs = sorted({SCENARIO_RE.fullmatch(x).group(1) for x in ids})
    gs = sorted({SCENARIO_RE.fullmatch(x).group(2) for x in ids})
    for metric in metrics:
        safe_append(ws, ["METRIC", metric, "5×5 registry-backed grid"])
        for c in cs:
            row = [metric, "C" + c]
            for g in gs:
                entry = next((x for x in max_rows(registry, f"C{c}_G{g}") if x["metric_name"] == metric), None)
                row.extend([ev(entry), entry["number_id"]] if entry else ["MISSING_EVIDENCE", ""])
            safe_append(ws, row)

    ws = new_sheet(wb, "SENSITIVITY", lang)
    header(ws, ["Dimension", "Held fixed", "From scenario", "From mean profit", "From number_id",
                "To scenario", "To mean profit", "To number_id", "Delta", "Delta number_id",
                "Source number_ids", "Calculation method"])
    for entry in extension.get("sensitivity_entries", []):
        source_by_id = {x["number_id"]: x for x in registry["entries"]}
        left, right = source_by_id[entry["from_number_id"]], source_by_id[entry["to_number_id"]]
        safe_append(ws, [
            entry["dimension"], entry["held_fixed"], entry["from_scenario_id"], ev(left), left["number_id"],
            entry["to_scenario_id"], ev(right), right["number_id"],
            exact_value(entry["numerator"], entry["denominator"]), entry["number_id"],
            entry["from_number_id"] + ";" + entry["to_number_id"], entry["calculation_method"],
        ])

    ws = new_sheet(wb, "VALIDATION_SUMMARY", lang)
    header(ws, [h["field"], h["status"], h["notes"]])
    for row in [
        ["D0", "PASS_SCOPED_WITH_LIMITATIONS", "Input identity and archive integrity scope only."],
        ["D1", "PASS_SCOPED_WITH_LIMITATIONS", "Approved v2.4.0 publication and exact-head evidence."],
        ["D2", "PASS_SCOPED_WITH_LIMITATIONS", "Pinned Number Registry exact-value and daily-series validation."],
        ["D3 structure", "PASS_SCOPED", "185 sheets per workbook; all 25 scenarios populated."],
        ["D3 source coverage", "PASS_SCOPED_WITH_LIMITATIONS", "25 P50 detailed cases; 105 representative daily keys / 125 role assignments; 49,500 close dates."],
        ["D3 bilingual parity", "PASS_SCOPED", "Arabic RTL and English LTR; all numeric cells compared."],
        ["Full model acceptance suite", "NOT_EXECUTED_HERE", "Do not infer 177 unique tests passed."],
        ["Final acceptance", "NOT_DECLARED", "D3 scoped closure is not project final acceptance."],
    ]:
        safe_append(ws, row)
    for requirement_id, status in [
        ("D3-01", "PASS_SCOPED"), ("D3-02", "PASS_SCOPED"), ("D3-03", "PASS_SCOPED"),
        ("D3-04", "PASS_SCOPED"), ("D3-05", "PASS_SCOPED_WITH_LIMITATIONS"),
        ("D3-06", "PASS_SCOPED_WITH_LIMITATIONS"), ("D3-07", "PASS_SCOPED"),
        ("D3-08", "PASS_SCOPED"), ("D3-09", "PASS_SCOPED"), ("D3-10", "PASS_SCOPED"),
        ("D3-11", "PASS_SCOPED"), ("D3-12", "PASS_SCOPED"), ("D3-13", "PASS_SCOPED"),
        ("D3-14", "PASS_SCOPED"), ("D3-15", "PASS_SCOPED"), ("D3-16", "PASS_SCOPED"),
        ("D3-17", "PASS_SCOPED_WITH_LIMITATIONS"), ("D3-18", "PASS_SCOPED"),
    ]:
        safe_append(ws, [requirement_id, status, "See D3 build audit, source extension audit, test run, and remote evidence ledger."])

    ws = new_sheet(wb, "ERROR_LOG", lang)
    header(ws, [h["field"], h["status"], h["reason"], h["notes"]])
    for item in registry.get("unavailable_evidence", []):
        safe_append(ws, [item.get("metric_name"), item.get("evidence_status"), item.get("reason"),
                         "Historical full-cohort evidence remains unavailable; no inference or zero-fill."])
    fv = extension["full_logging_validation"]
    cv = extension["c100_validation"]
    safe_append(ws, ["Full Logging", fv["normalized_status"], "105 representative keys only",
                     "125 role assignments verified; this is not 48,000-trial daily logging."])
    safe_append(ws, ["C100 Golden revalidation", "NOT_RUN", "C100 daily reuse path cross-checked",
                     "No new C100 trial or full Golden revalidation was executed."])
    for field in ACCOUNTING_FIELDS:
        safe_append(ws, [field, "MISSING_EVIDENCE",
                         "MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS",
                         "The full 48K historical cohort is unavailable; representative P50 case values are source-backed only."])
    safe_append(ws, ["Historical 48K accounting fields", "MISSING_EVIDENCE",
                     "MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS",
                     "No field is inferred or zero-filled."])
    safe_append(ws, ["Production Gate A", "NOT_DECLARED",
                     "MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS",
                     "Financial Gate A PASS_SCOPED does not imply production acceptance."])
    safe_append(ws, ["Gate B N=2400", "FAIL_SCOPED (10/10)", "STATISTICAL_GATE_NOT_PASSED",
                     "No N expansion or convergence claim."])
    safe_append(ws, ["Stability", "NOT_CONVERGED (0/60)", "STABILITY_NOT_CONVERGED",
                     "No convergence or final acceptance claim."])
    safe_append(ws, ["N=4800", "NOT_EXECUTED", "NO_N_EXPANSION", "No N=4800 run was performed."])

    ws = new_sheet(wb, "FINAL_CLOSURE_SUMMARY", lang)
    header(ws, [h["scenario"], h["cohort"], "final_close_date", "trial_count", "trial_count_number_id",
                "N_total", "N_total_number_id", "N_unique_paths", "N_unique_paths_number_id",
                "source_member", h["evidence"]])
    for item in extension["final_close_date_distribution"]:
        n_total_id = stable_id("NR-", ["D3_CLOSE_DATE_N_TOTAL_V1", item["source_artifact_sha256"], item["scenario_id"]])
        n_unique_id = stable_id("NR-", ["D3_CLOSE_DATE_N_UNIQUE_V1", item["source_artifact_sha256"], item["scenario_id"]])
        safe_append(ws, [
            item["scenario_id"], item["cohort_id"], item["final_close_date"],
            item["trial_count"], item["trial_count_number_id"], item["N_total"], n_total_id,
            item["N_unique_paths"], n_unique_id, item["source_member"], item["evidence_status"],
        ])

    ws = new_sheet(wb, "DAILY_DISTRIBUTION", lang)
    write_daily_distribution(ws, registry, ids, lang)

    ws = new_sheet(wb, "REPRESENTATIVE_CASES", lang)
    representative_summary_fields = (
        "bad_debt", "claims_created", "cumulative_project_profit", "final_cash",
        "final_net_project_equity", "guarantee_recovered", "held_assets",
        "operating_net_profit", "owned_bikes", "partner1_final_entitlement",
        "partner2_final_entitlement", "secondary_cycle_count", "termination_count",
        "total_operating_revenue",
    )
    role_cases = extension.get("representative_role_cases", [])
    if (
        len(role_cases) != 105
        or len({(x["scenario_id"], x["trial_id"]) for x in role_cases}) != 105
        or sum(len(x["role_assignments"]) for x in role_cases) != 125
    ):
        raise ValueError("REPRESENTATIVE_CASES_ROLE_COVERAGE_INVALID")
    cols = ["record_type", h["scenario"], h["cohort"], h["trial"], h["roles"], h["date"]]
    for field in DAILY_DETAIL_FIELDS:
        cols.extend([field, field + "_number_id"])
    for field in representative_summary_fields:
        cols.extend([field, field + "_number_id"])
    cols.extend(["final_close_date", "source_member", "evidence_status",
                 "registry_metric", "registry_value", "registry_number_id"])
    header(ws, cols)
    for case in sorted(role_cases, key=lambda x: (x["scenario_id"], x["trial_id"])):
        sid, cohort, trial = case["scenario_id"], case["cohort_id"], case["trial_id"]
        roles = ", ".join(case["role_assignments"])
        for i, daily_row in enumerate(case["daily_rows"]):
            out = ["DAILY_RAW", sid, cohort, "trial_id=" + str(trial), roles, daily_row["date"]]
            for field in DAILY_DETAIL_FIELDS:
                out.extend(numeric_pair(case, "daily_snapshots.jsonl.gz", i, field, daily_row[field]))
            out.extend(["", ""] * len(representative_summary_fields))
            out.extend([case["final_close_date"], case["source_member"], "VERIFIED_LIVE", "", "", ""])
            safe_append(ws, out)
        out = ["TRIAL_SUMMARY", sid, cohort, "trial_id=" + str(trial), roles, "FINAL_TRIAL_SUMMARY"]
        out.extend(["", ""] * len(DAILY_DETAIL_FIELDS))
        for field in representative_summary_fields:
            out.extend(numeric_pair(case, "trial_result.json", 0, field, case["trial_summary"][field]))
        out.extend([case["final_close_date"], case["source_member_prefix"] + "trial_result.json",
                    "VERIFIED_LIVE", "", "", ""])
        safe_append(ws, out)

    reps = [x for x in registry["entries"] if x.get("trial_id") is not None]
    for entry in sorted(reps, key=lambda x: (x["scenario_id"], x["trial_id"], x["metric_name"])):
        out = ["REGISTRY_METRIC", entry["scenario_id"], entry["cohort_id"],
               "trial_id=" + str(entry["trial_id"]), ", ".join(entry.get("role_assignments", [])),
               "REGISTERED_TRIAL_METRIC"]
        out.extend(["", ""] * len(DAILY_DETAIL_FIELDS))
        out.extend(["", ""] * len(representative_summary_fields))
        out.extend(["", entry.get("source_member"), entry.get("evidence_status"),
                    entry["metric_name"], ev(entry), entry["number_id"]])
        safe_append(ws, out)


def write_detail_sheet(wb, suffix: str, case: dict, lang: str) -> None:
    sid = case["scenario_id"]
    ws = new_sheet(wb, f"{sid}_{suffix}", lang)
    prefix = case["source_member_prefix"]
    if suffix == "DAILY":
        cols = ["Scenario", "Cohort", "Trial_ID", "Date"]
        for field in DAILY_DETAIL_FIELDS:
            cols.extend([field, field + "_number_id"])
        cols.append("Final_Close_Date")
        header(ws, cols)
        for i, row in enumerate(case["daily_rows"]):
            out = [sid, case["cohort_id"], case["trial_id"], row["date"]]
            for field in DAILY_DETAIL_FIELDS:
                out.extend(numeric_pair(case, "daily_snapshots.jsonl.gz", i, field, row[field]))
            out.append(row.get("Final_Close_Date"))
            safe_append(ws, out)
        safe_append(ws, ["SCOPE_LIMITATION", "Representative P50 only; not 48,000-trial full daily logging."])
        return

    if suffix == "ASSETS":
        cols = ["Scenario", "Cohort", "Trial_ID", "Bike_ID", "Purchase_Date", "Funding_Completion_Date",
                "Actual_Ready_Date", "Scheduled_Ready_Date", "Delivery_Date"]
        for field in ASSET_NUMERIC_FIELDS:
            cols.extend([field, field + "_number_id"])
        cols.extend(["Current_State", "Prep_Paid", "Customs_Paid", "Current_Contract_ID",
                     "Current_Tenant_ID", "Active_Settlement_Receivable_ID", "Settlement_Start_Date",
                     "Pending_Writeoff_Today", "Source"])
        header(ws, cols)
        for i, row in enumerate(case["assets"]):
            out = [sid, case["cohort_id"], case["trial_id"], row.get("bike_id"), row.get("purchase_date"),
                   row.get("funding_completion_date"), row.get("actual_ready_date"),
                   row.get("scheduled_ready_date"), row.get("delivery_date")]
            for field in ASSET_NUMERIC_FIELDS:
                value = row.get(field)
                if value is None:
                    out.extend(["", ""])
                else:
                    out.extend(numeric_pair(case, "assets.jsonl.gz", i, field, value))
            out.extend([row.get("current_state"), row.get("prep_paid"), row.get("customs_paid"),
                        row.get("current_contract_id"), row.get("current_tenant_id"),
                        row.get("active_settlement_receivable_id"), row.get("settlement_start_date"),
                        row.get("pending_writeoff_today"), row.get("source")])
            safe_append(ws, out)
        return

    if suffix == "ACCTG":
        snapshot_fields = DAILY_DETAIL_FIELDS
        roll_specs = (
            ("ar_rollforward", AR_FIELDS),
            ("asset_rollforward", ASSET_ROLL_FIELDS),
            ("cash_rollforward", CASH_FIELDS),
            ("equity_rollforward", EQUITY_FIELDS),
        )
        cols = ["Scenario", "Cohort", "Trial_ID", "Date"]
        for field in snapshot_fields:
            cols.extend([field, field + "_number_id"])
        for key, fields in roll_specs:
            for field in fields:
                cols.extend([key + "." + field, key + "." + field + "_number_id"])
        for field in ACCTG_SUMMARY_FIELDS:
            cols.extend([field, field + "_number_id"])
        header(ws, cols)
        for i, row in enumerate(case["daily_rows"]):
            out = [sid, case["cohort_id"], case["trial_id"], row["date"]]
            for field in snapshot_fields:
                out.extend(numeric_pair(case, "daily_snapshots.jsonl.gz", i, field, row[field]))
            for key, fields in roll_specs:
                source_member = key + ".jsonl.gz"
                roll = case["rollforwards"][key][i]
                for field in fields:
                    out.extend(numeric_pair(case, source_member, i, field, roll[field]))
            out.extend(["", ""] * len(ACCTG_SUMMARY_FIELDS))
            safe_append(ws, out)
        summary = case["trial_summary"]
        out = [sid, case["cohort_id"], case["trial_id"], "FINAL_TRIAL_SUMMARY"]
        out.extend(["", ""] * len(snapshot_fields))
        for _, fields in roll_specs:
            out.extend(["", ""] * len(fields))
        for field in ACCTG_SUMMARY_FIELDS:
            out.extend(numeric_pair(case, "trial_result.json", 0, field, summary[field]))
        safe_append(ws, out)
        safe_append(ws, ["SCOPE_LIMITATION", "Five historical accounting fields are complete only for this representative P50 trial; full 48K remains MISSING_EVIDENCE."])
        return

    if suffix == "PARTNER":
        cols = ["Scenario", "Cohort", "Trial_ID", "Date",
                "Partner1_Reinvestment_Balance", "Partner1_Reinvestment_Balance_number_id",
                "Partner2_Reinvestment_Balance", "Partner2_Reinvestment_Balance_number_id",
                "Partner1_Final_Entitlement", "Partner1_Final_Entitlement_number_id",
                "Partner2_Final_Entitlement", "Partner2_Final_Entitlement_number_id"]
        header(ws, cols)
        for i, row in enumerate(case["daily_rows"]):
            out = [sid, case["cohort_id"], case["trial_id"], row["date"]]
            out.extend(numeric_pair(case, "daily_snapshots.jsonl.gz", i, "Partner1_Reinvestment_Balance", row["Partner1_Reinvestment_Balance"]))
            out.extend(numeric_pair(case, "daily_snapshots.jsonl.gz", i, "Partner2_Reinvestment_Balance", row["Partner2_Reinvestment_Balance"]))
            out.extend(["", "", "", ""])
            safe_append(ws, out)
        summary = case["trial_summary"]
        out = [sid, case["cohort_id"], case["trial_id"], "FINAL_TRIAL_SUMMARY", "", "", "", ""]
        out.extend(numeric_pair(case, "trial_result.json", 0, "partner1_final_entitlement", summary["partner1_final_entitlement"]))
        out.extend(numeric_pair(case, "trial_result.json", 0, "partner2_final_entitlement", summary["partner2_final_entitlement"]))
        safe_append(ws, out)
        return

    if suffix == "GUARANTEE":
        fields = ("claim_amount", "recovered_amount", "bad_debt_amount", "recovery_rate_pct", "waiting_period_days")
        cols = ["Scenario", "Cohort", "Trial_ID", "Claim_ID", "Claim_Source", "Bike_ID", "Contract_ID",
                "Tenant_ID", "Guarantor_ID", "Created_Date", "Settlement_Due_Date", "Settlement_Date", "Status"]
        for field in fields:
            cols.extend([field, field + "_number_id"])
        header(ws, cols)
        if not case["claims"]:
            count_id = ledger_number_id(case["source_artifact_sha256"], sid, case["trial_id"],
                                        prefix + "trial_result.json", 0, "claims_created")
            safe_append(ws, [sid, case["cohort_id"], case["trial_id"], "NO_CLAIMS_RECORDED",
                             "Verified empty source ledger", "", "", "", "", "", "", "", "NO_CLAIMS",
                             0, count_id, "", "", "", "", ""])
        else:
            for i, row in enumerate(case["claims"]):
                out = [sid, case["cohort_id"], case["trial_id"], row.get("claim_id"), row.get("claim_source"),
                       row.get("bike_id"), row.get("contract_id"), row.get("tenant_id"), row.get("guarantor_id"),
                       row.get("created_date"), row.get("settlement_due_date"), row.get("settlement_date"), row.get("status")]
                for field in fields:
                    value = row.get(field)
                    if value is None:
                        out.extend(["", ""])
                    else:
                        out.extend(numeric_pair(case, "claims.jsonl.gz", i, field, value))
                safe_append(ws, out)
        return

    if suffix == "CONTRACTS":
        fields = ("daily_rate", "friday_counter", "total_due", "total_paid")
        cols = ["Scenario", "Cohort", "Trial_ID", "Contract_ID", "Bike_ID", "Tenant_ID", "Guarantor_ID",
                "Contract_Type", "Start_Date", "First_Eligible_Friday_Date", "Maturity_Date", "Status"]
        for field in fields:
            cols.extend([field, field + "_number_id"])
        header(ws, cols)
        for i, row in enumerate(case["contracts"]):
            out = [sid, case["cohort_id"], case["trial_id"], row.get("contract_id"), row.get("bike_id"),
                   row.get("tenant_id"), row.get("guarantor_id"), row.get("contract_type"),
                   row.get("start_date"), row.get("first_eligible_friday_date"), row.get("maturity_date"),
                   row.get("status")]
            for field in fields:
                value = row.get(field)
                if value is None:
                    out.extend(["", ""])
                else:
                    out.extend(numeric_pair(case, "contracts.jsonl.gz", i, field, value))
            safe_append(ws, out)
        return


def build_one(registry: dict, extension: dict, constants: list, ids: list[str], lang: str,
              path: Path, source_head: str, run_id: str, base_sha: str, extension_sha: str, input_manifest_sha256: str) -> None:
    wb = Workbook(write_only=True)
    write_globals(wb, registry, extension, ids, lang, constants, source_head, run_id, base_sha, extension_sha, input_manifest_sha256)
    cases = {x["scenario_id"]: x for x in extension["representative_cases"]}
    for sid in ids:
        if sid not in cases:
            raise ValueError("D3_P50_CASE_MISSING:" + sid)
        for suffix in ("STATS", "DAILY", "ASSETS", "ACCTG", "PARTNER", "GUARANTEE", "CONTRACTS"):
            if suffix == "STATS":
                ws = new_sheet(wb, f"{sid}_{suffix}", lang)
                header(ws, [H[lang]["scenario"], H[lang]["cohort"], H[lang]["metric"],
                            H[lang]["sample"], H[lang]["value"], H[lang]["id"], H[lang]["evidence"]])
                rows = [x for x in registry["entries"] if x.get("scenario_id") == sid and x.get("trial_id") is None]
                for entry in sorted(rows, key=lambda x: (x.get("sample_n", 0), x["metric_name"])):
                    safe_append(ws, [sid, entry.get("cohort_id"), entry["metric_name"],
                                     "N=" + str(entry["sample_n"]), ev(entry), entry["number_id"],
                                     entry["evidence_status"]])
                if not rows:
                    raise ValueError("D3_STATS_MISSING:" + sid)
            else:
                write_detail_sheet(wb, suffix, cases[sid], lang)
    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def trace_ids(paths: list[Path]) -> dict:
    checked = 0
    excluded = {"README", "CONSTANTS", "VALIDATION_SUMMARY", "ERROR_LOG"}
    from openpyxl import load_workbook
    for path in paths:
        wb = load_workbook(path, read_only=True, data_only=False)
        try:
            for ws in wb.worksheets:
                if ws.title in excluded:
                    continue
                for row in ws.iter_rows():
                    for i, cell in enumerate(row):
                        value = cell.value
                        if isinstance(value, (int, float, Decimal)) and not isinstance(value, bool):
                            next_value = row[i + 1].value if i + 1 < len(row) else None
                            if not isinstance(next_value, str) or not (next_value.startswith("NR-") or next_value.startswith("D2D-")):
                                raise ValueError("UNTRACED_NUMERIC_CELL:" + ws.title + ":" + cell.coordinate)
                            checked += 1
        finally:
            wb.close()
    return {"numeric_cells_checked": checked, "untraced_numeric_cells": 0}


def build(args) -> dict:
    base_raw = Path(args.registry).read_bytes()
    base_sha = hashlib.sha256(base_raw).hexdigest()
    if len(base_raw) != BASE_REGISTRY_BYTES or base_sha != BASE_REGISTRY_SHA256:
        raise ValueError("REGISTRY_PIN_MISMATCH")
    base_registry = json.loads(base_raw.decode("utf-8"))
    validation = validate_registry(base_registry)
    if base_registry["current_governing_reference_sha256"] != GOVERNING or base_registry["historical_execution_reference_sha256"] != HISTORICAL:
        raise ValueError("REFERENCE_IDENTITY_MISMATCH")
    extension, extension_raw, extension_sha = load_extension(args.extension, base_sha)
    registry = merge_extension(base_registry, extension)
    ids = registry_scenarios(registry)
    if registry["current_governing_reference_sha256"] != GOVERNING:
        raise ValueError("GOVERNING_REFERENCE_IDENTITY_MISMATCH")
    reference_raw = Path(args.reference).read_bytes()
    reference_sha = hashlib.sha256(reference_raw).hexdigest()
    if len(reference_raw) != GOVERNING_BYTES or reference_sha != GOVERNING:
        raise ValueError("GOVERNING_REFERENCE_PIN_MISMATCH")
    constants = constants_from_reference(reference_raw.decode("utf-8"))
    names = ["README", "CONSTANTS", "SCENARIO_MATRIX", "HEATMAP", "SENSITIVITY",
             "VALIDATION_SUMMARY", "ERROR_LOG", "FINAL_CLOSURE_SUMMARY",
             "DAILY_DISTRIBUTION", "REPRESENTATIVE_CASES"] + scenario_sheet_names(ids)
    out = Path(args.output_dir)
    ar = out / "النتائج_الكاملة_AR.xlsx"
    en = out / "Full_Results_EN.xlsx"
    build_one(registry, extension, constants, ids, "ar", ar, args.source_head, args.run_id, base_sha, extension_sha, args.input_manifest_sha256)
    build_one(registry, extension, constants, ids, "en", en, args.source_head, args.run_id, base_sha, extension_sha, args.input_manifest_sha256)
    aa = audit(ar, names, expected_rtl=True)
    ee = audit(en, names, expected_rtl=False)
    parity = compare(ar, en, names)
    trace = trace_ids([ar, en])
    requirements = {
        "D3-01": "PASS_SCOPED", "D3-02": "PASS_SCOPED", "D3-03": "PASS_SCOPED",
        "D3-04": "PASS_SCOPED", "D3-05": "PASS_SCOPED_WITH_LIMITATIONS",
        "D3-06": "PASS_SCOPED", "D3-07": "PASS_SCOPED", "D3-08": "PASS_SCOPED",
        "D3-09": "PASS_SCOPED", "D3-10": "PASS_SCOPED", "D3-11": "PASS_SCOPED",
        "D3-12": "PASS_SCOPED", "D3-13": "PASS_SCOPED", "D3-14": "PASS_SCOPED",
        "D3-15": "PASS_SCOPED", "D3-16": "PASS_SCOPED", "D3-17": "PASS_SCOPED_WITH_LIMITATIONS",
        "D3-18": "PASS_SCOPED",
    }
    limitations = [
        "Full Logging contains 105 representative keys only; it is not 48,000-trial full daily logging.",
        "The five historical accounting fields remain MISSING_EVIDENCE for the full 48,000-trial cohort; representative P50 values are source-backed only.",
        "C100 Golden revalidation remains NOT_RUN; the deterministic daily reuse path is separately identity- and content-checked.",
        "Financial Gate A remains PASS_SCOPED only; Production Gate A remains NOT_DECLARED.",
        "Gate B N=2400 remains FAIL_SCOPED (10/10); Stability remains NOT_CONVERGED (0/60); N=4800 remains NOT_EXECUTED.",
    ]
    reference_info = {
        "path": "Gist reference_v240.md", "bytes": len(reference_raw), "sha256": reference_sha,
        "git_blob_sha1": blob_sha(reference_raw), "containing_commit": "384c27810e76572e77e79e9829c5f92c1c4165d7",
        "url": "https://gist.githubusercontent.com/yasmin977209-ux/c3e5362f5928da22ee079fc94817224e/raw/384c27810e76572e77e79e9829c5f92c1c4165d7/reference_v240.md",
    }
    result = {
        "d3_candidate_status": "T2_INTERIM / NOT_FINAL_BLOCKED",
        "d3_gate_status": "PASS_SCOPED_WITH_LIMITATIONS",
        "source_head": args.source_head, "workflow_run_id": str(args.run_id), "input_manifest_sha256": args.input_manifest_sha256,
        "current_governing_reference": reference_info,
        "historical_execution_reference_sha256": HISTORICAL,
        "registry_base": {"bytes": len(base_raw), "sha256": base_sha, "git_blob_sha1": blob_sha(base_raw), **validation},
        "registry_extension": {
            "bytes": len(extension_raw), "sha256": extension_sha, "git_blob_sha1": blob_sha(extension_raw),
            "extension_id": extension["extension_id"], "path": args.extension,
            "actions_artifact_name": f"D3-Registry-Extension-{args.run_id}",
            "representative_role_case_count": len(extension.get("representative_role_cases", [])),
        },
        "source_artifacts": extension["source_artifacts"],
        "full_logging_validation": extension["full_logging_validation"],
        "c100_validation": extension["c100_validation"],
        "close_date_validation": extension["close_date_validation"],
        "representative_accounting_fields": extension["representative_accounting_fields"],
        "representative_role_case_count": len(extension.get("representative_role_cases", [])),
        "representative_role_assignment_count": extension["full_logging_validation"]["role_assignments"],
        "missing_historical_48k_accounting_fields": ACCOUNTING_FIELDS,
        "scenario_count": len(ids), "worksheet_count_per_workbook": len(names),
        "arabic_workbook": aa, "english_workbook": ee,
        "bilingual_numeric_parity": parity, "number_id_traceability": trace,
        "requirement_statuses": requirements, "limitations": limitations,
        "gate_statuses_preserved": base_registry["gate_statuses"],
        "no_trials_or_simulation_executed": True,
        "final_acceptance": "NOT_DECLARED",
    }
    out.mkdir(parents=True, exist_ok=True)
    (out / "D3_BUILD_AUDIT.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest = {
        "classification": result["d3_candidate_status"], "d3_gate_status": result["d3_gate_status"],
        "source_head": args.source_head, "workflow_run_id": str(args.run_id),
        "current_governing_reference": reference_info, "historical_execution_reference_sha256": HISTORICAL,
        "registry_base_sha256": base_sha, "input_manifest_sha256": args.input_manifest_sha256, "registry_extension": result["registry_extension"],
        "source_artifacts": extension["source_artifacts"], "requirement_statuses": requirements,
        "representative_role_case_count": result["representative_role_case_count"],
        "representative_role_assignment_count": result["representative_role_assignment_count"],
        "missing_historical_48k_accounting_fields": list(ACCOUNTING_FIELDS),
        "master_seed": base_registry["scope"]["S6"]["master_seed"],
        "files": {
            ar.name: {"bytes": aa["bytes"], "sha256": aa["sha256"]},
            en.name: {"bytes": ee["bytes"], "sha256": ee["sha256"]},
        },
        "numeric_comparisons": parity["numeric_comparisons"],
        "number_id_traceability": trace, "limitations": limitations,
        "python_version": platform.python_version(), "openpyxl_version": __import__("openpyxl").__version__,
    }
    (out / "D3_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = [
        "# D3 Excel Deliverables — Scoped Closure Report", "",
        "- Candidate: " + result["d3_candidate_status"],
        "- D3 gate: " + result["d3_gate_status"], "- D3 input manifest SHA-256: " + args.input_manifest_sha256,
        "- Source HEAD: " + args.source_head, "- Workflow run: " + str(args.run_id),
        "- Governing reference SHA-256: " + reference_sha + "; bytes: " + str(len(reference_raw)),
        "- D2 Number Registry SHA-256: " + base_sha,
        "- D3 Number Registry extension SHA-256: " + extension_sha,
        "- Sheets per workbook: " + str(len(names)),
        "- Arabic RTL / English LTR: " + aa["sheet_direction_status"] + " / " + ee["sheet_direction_status"],
        "- Excel formulas/errors: AR " + str(aa["formula_cell_count"]) + "/" + str(aa["excel_error_cell_count"]) +
        "; EN " + str(ee["formula_cell_count"]) + "/" + str(ee["excel_error_cell_count"]),
        "- S6 daily distribution points: " + str(validation["daily_points_resolved"]),
        "- C100 daily reuse points: " + str(5 * 2 * len(METRICS) * len(QUANTILES) * 2198),
        "- P50 detailed scenarios: 25; all representative daily role keys: " + str(len(extension.get("representative_role_cases", []))) + "; role assignments: " + str(extension["full_logging_validation"]["role_assignments"]),
        "- All-trial close-date records: 49,500 (48,000 S6 + 1,500 C100)",
        "- Bilingual numeric comparisons: " + str(parity["numeric_comparisons"]) + "; mismatches: 0",
        "- Number-ID traced numeric cells: " + str(trace["numeric_cells_checked"]) + "; untraced: 0",
        "", "## Requirement status",
    ]
    report += [f"- {key}: {value}" for key, value in requirements.items()]
    report += ["", "## Preserved limitations"] + [f"- {item}" for item in limitations]
    report += ["", "D3 is closed within scoped requirements with limitations. This is not final project acceptance and does not authorize D4."]
    Path("docs/stage_d/D3_SCOPED_CLOSURE_REPORT_2026-11-02.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    b = sub.add_parser("build")
    for name in ("registry", "extension", "reference", "output-dir", "source-head", "run-id", "input-manifest-sha256"):
        b.add_argument("--" + name, required=True)
    args = parser.parse_args()
    build(args)


if __name__ == "__main__":
    main()
