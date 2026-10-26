#!/usr/bin/env python3
"""Execute the full deterministic C100 cohort and build a new v2.3 Golden."""
from __future__ import annotations

from datetime import date, datetime, timezone
from hashlib import sha256
import gc
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import sys
import time
from typing import Any

import constants
import daily_engine
import monte_carlo
from entities import BikeState, ContractStatus, ContractType, format_bike_id, is_canonical_bike_id

SOURCE_SHA = os.environ["S4_SOURCE_SHA"]
COHORT_ID = os.environ["S4_COHORT_ID"]
TRIAL_COUNT = int(os.environ["S4_C100_TRIAL_COUNT"])
SCENARIOS = tuple(f"C100_G{rate:03d}" for rate in constants.GUARANTEE_RECOVERY_RATES)
REFERENCE_PATH = Path("docs/audits/S4_C100_REFERENCE_21_8.json")
R4_PATH = Path("docs/audits/R4_S4_C100_P50_GOLDEN_2026-10-26.md")
GOLDEN_PATH = Path("docs/golden/v2.3") / f"C100_GOLDEN_{SOURCE_SHA}.json"
MANIFEST_PATH = Path("docs/audits") / f"S4_C100_GOLDEN_MANIFEST_{SOURCE_SHA}.json"
REPORT_PATH = Path("docs/audits") / f"S4_C100_GOLDEN_REPORT_{SOURCE_SHA}.md"
FAILURE_DIR = Path("docs/audits")


class ReferenceMismatch(RuntimeError):
    def __init__(self, payload: dict[str, Any]):
        self.payload = payload
        super().__init__("UNDEFINED_BUSINESS_RULE §21.8: " + str(payload.get("date")) + " " + str(payload.get("field")))


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def stable_sha(value: Any) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return sha256(raw).hexdigest()


def write_json(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str) + "\n", encoding="utf-8")
    return sha256(path.read_bytes()).hexdigest()


def enum_is(value: Any, expected: Any) -> bool:
    return getattr(value, "value", value) == getattr(expected, "value", expected)


def active_primary_count(project: Any) -> int:
    return sum(
        1 for contract in project.contracts.values()
        if enum_is(contract.contract_type, ContractType.PRIMARY)
        and enum_is(contract.status, ContractStatus.ACTIVE)
    )


def compare_reference_row(expected: dict[str, Any], actual: dict[str, Any], scenario: str, trial_id: int) -> None:
    for field, exp in expected.items():
        if field in {"final_close_date", "final_net_project_equity", "final_cash",
                     "partner1_final_entitlement", "partner2_final_entitlement"}:
            continue
        act = actual.get(field)
        if act != exp:
            raise ReferenceMismatch({
                "status": "UNDEFINED_BUSINESS_RULE",
                "clauses": ["0.1", "2.7", "21.8"],
                "source_sha": SOURCE_SHA,
                "cohort_id": COHORT_ID,
                "scenario_id": scenario,
                "trial_id": trial_id,
                "date": expected.get("date"),
                "field": field,
                "expected": exp,
                "actual": act,
                "action": "Stopped at first mismatch; no model/reference modification and no Golden creation."
            })


def check_daily_accounting(project: Any, current_date: date) -> tuple[dict[str, Any], dict[str, Any]]:
    day = current_date.isoformat()
    check = project.daily_balance_checks[-1]
    if check["Total_Assets"] != check["Total_Equity"] or check["Balance_Difference"] != 0:
        raise RuntimeError(
            f"S4_BALANCE_MISMATCH date={day} assets={check['Total_Assets']} "
            f"equity={check['Total_Equity']} diff={check['Balance_Difference']}"
        )
    cash = project.cash_rollforward[-1]
    ar = project.ar_rollforward[-1]
    asset = project.asset_rollforward[-1]
    equity = project.equity_rollforward[-1]
    if cash["Outflows"] != cash["Operating_Cash_Outflows"] + cash["Investing_Cash_Outflows"]:
        raise RuntimeError(f"S4_CASH_OUTFLOW_COMPONENT_MISMATCH date={day}")
    if cash["Opening_Cash"] + cash["Inflows"] - cash["Outflows"] != cash["Closing_Cash"]:
        raise RuntimeError(f"S4_CASH_ROLLFORWARD_MISMATCH date={day}")
    if ar["Opening_AR"] + ar["Accruals"] - ar["Collections"] - ar["TransfersToGuarantee"] != ar["Closing_AR"]:
        raise RuntimeError(f"S4_AR_ROLLFORWARD_MISMATCH date={day}")
    if asset["Opening_Gross_Bike_Assets"] + asset["Capitalized_Purchases_And_Customs"] - asset["Gross_Writeoffs_On_Ownership"] != asset["Closing_Gross_Bike_Assets"]:
        raise RuntimeError(f"S4_GROSS_ASSET_ROLLFORWARD_MISMATCH date={day}")
    if asset["Opening_Accumulated_Depreciation"] + asset["Expense_Depreciation"] - asset["AD_Removed_On_Writeoff"] != asset["Closing_Accumulated_Depreciation"]:
        raise RuntimeError(f"S4_DEPRECIATION_ROLLFORWARD_MISMATCH date={day}")
    if equity["Opening_Equity"] + equity["Operating_Net_Profit"] != equity["Closing_Equity"]:
        raise RuntimeError(f"S4_EQUITY_ROLLFORWARD_MISMATCH date={day}")
    return (
        {
            "cash": cash,
            "accounts_receivable": ar,
            "gross_bike_assets_and_depreciation": asset,
            "equity": equity,
        },
        {
            "Total_Assets": check["Total_Assets"],
            "Total_Equity": check["Total_Equity"],
            "Balance_Difference": check["Balance_Difference"],
        },
    )


def snapshot(project: Any, current_date: date) -> dict[str, Any]:
    check = project.daily_balance_checks[-1]
    return {
        "date": current_date.isoformat(),
        "cash": project.project_cash,
        "partner1_reinvestment_balance": project.partner1_reinvestment_balance,
        "partner2_reinvestment_balance": project.partner2_reinvestment_balance,
        "bikes": len(project.bikes),
        "prep": sum(1 for bike in project.bikes if enum_is(bike.current_state, BikeState.PREP)),
        "active_primary_contracts": active_primary_count(project),
        "owned_transferred_bikes": sum(1 for bike in project.bikes if enum_is(bike.current_state, BikeState.OWNED_TRANSFERRED)),
        "net_equity": check["Total_Equity"],
    }


def check_final_values(project: Any, expected: dict[str, Any], scenario: str, trial_id: int) -> dict[str, Any]:
    actual = {
        "final_close_date": project.final_close_date.isoformat() if project.final_close_date else None,
        "final_net_project_equity": project.final_net_project_equity,
        "final_cash": project.project_cash,
        "partner1_final_entitlement": project.partner1_final_entitlement,
        "partner2_final_entitlement": project.partner2_final_entitlement,
        "bikes": len(project.bikes),
        "held_assets": sum(1 for bike in project.bikes if enum_is(bike.current_state, BikeState.HELD_AS_ASSET)),
        "pending_claims": sum(1 for claim in project.guarantee_claims if enum_is(claim.status, "PENDING")),
        "cumulative_project_profit": project.cumulative_project_profit,
        "operating_net_profit": project.operating_net_profit,
    }
    for field, exp in expected.items():
        if actual.get(field) != exp:
            raise ReferenceMismatch({
                "status": "UNDEFINED_BUSINESS_RULE",
                "clauses": ["0.1", "21.8"],
                "source_sha": SOURCE_SHA,
                "cohort_id": COHORT_ID,
                "scenario_id": scenario,
                "trial_id": trial_id,
                "date": actual["final_close_date"],
                "field": field,
                "expected": exp,
                "actual": actual.get(field),
                "action": "Stopped at first mismatch; no model/reference modification and no Golden creation."
            })
    return actual


def check_first_expansions(project: Any, expected_rows: list[dict[str, Any]], scenario: str, trial_id: int) -> list[dict[str, Any]]:
    by_id = {bike.bike_id: bike for bike in project.bikes}
    actual_rows = []
    for exp in expected_rows:
        bike = by_id.get(exp["bike_id"])
        actual = None if bike is None else {
            "bike_id": bike.bike_id,
            "purchase_date": bike.purchase_date.isoformat(),
            "actual_ready_date": bike.actual_ready_date.isoformat() if bike.actual_ready_date else None,
            "delivery_date": bike.delivery_date.isoformat() if bike.delivery_date else None,
        }
        if actual != exp:
            raise ReferenceMismatch({
                "status": "UNDEFINED_BUSINESS_RULE",
                "clauses": ["0.1", "2.7", "21.8"],
                "source_sha": SOURCE_SHA,
                "cohort_id": COHORT_ID,
                "scenario_id": scenario,
                "trial_id": trial_id,
                "date": exp.get("purchase_date"),
                "field": "first_expansion_bike:" + exp["bike_id"],
                "expected": exp,
                "actual": actual,
                "action": "Stopped at first mismatch; no model/reference modification and no Golden creation."
            })
        actual_rows.append(actual)
    ids = [bike.bike_id for bike in project.bikes]
    expected_ids = [format_bike_id(serial) for serial in range(1, len(project.bikes) + 1)]
    if ids != expected_ids or not all(is_canonical_bike_id(bike_id) for bike_id in ids):
        raise RuntimeError(f"S4_NONCANONICAL_OR_NONCONTIGUOUS_BIKE_IDS scenario={scenario} trial_id={trial_id}")
    return actual_rows


def perform_trial(scenario: str, trial_id: int, reference: dict[str, Any]) -> dict[str, Any]:
    collection_probability, recovery_rate_pct = monte_carlo.parse_scenario_id(scenario)
    expected_by_date = {row["date"]: row for row in reference["snapshots"]}
    rows: list[dict[str, Any]] = []
    selected: dict[str, dict[str, Any]] = {}

    def capture_day(project: Any, current_date: date) -> None:
        rollforwards, balance = check_daily_accounting(project, current_date)
        current = snapshot(project, current_date)
        if current["date"] in expected_by_date:
            compare_reference_row(expected_by_date[current["date"]], current, scenario, trial_id)
            selected[current["date"]] = current
        daily_snapshot = monte_carlo._daily_snapshot(project, current_date, trial_id)
        daily_snapshot.pop("trial_id", None)
        rows.append({
            "snapshot": current,
            "daily_snapshot": daily_snapshot,
            "balance_check": balance,
            "rollforwards": rollforwards,
        })

    started = time.perf_counter()
    project = daily_engine.run_deterministic_trial(
        recovery_rate_pct=recovery_rate_pct,
        trial_id=trial_id,
        scenario_id=scenario,
        master_seed=constants.MASTER_SEED,
        collection_probability=collection_probability,
        on_day_end=capture_day,
        log_events=True,
    )
    if not project.simulation_stopped or project.final_close_date is None:
        raise RuntimeError(f"S4_TRIAL_DID_NOT_CLOSE scenario={scenario} trial_id={trial_id}")
    if set(selected) != set(expected_by_date):
        raise RuntimeError(f"S4_REQUIRED_SNAPSHOT_MISSING scenario={scenario} trial_id={trial_id} selected={sorted(selected)}")
    if not rows or len(rows) != len(project.daily_balance_checks):
        raise RuntimeError(f"S4_DAILY_ROW_COUNT_MISMATCH scenario={scenario} trial_id={trial_id}")
    if any(len(series) != len(rows) for series in (
        project.cash_rollforward, project.ar_rollforward,
        project.asset_rollforward, project.equity_rollforward
    )):
        raise RuntimeError(f"S4_ROLLFORWARD_ROW_COUNT_MISMATCH scenario={scenario} trial_id={trial_id}")

    final = check_final_values(project, reference["final_values"], scenario, trial_id)
    expansions = check_first_expansions(project, reference["first_expansion_bikes"], scenario, trial_id)
    if project.rng_draw_count != 0 or project.rng_checksum != 0:
        raise RuntimeError(f"S4_RNG_NOT_ZERO scenario={scenario} trial_id={trial_id} draw_count={project.rng_draw_count} checksum={project.rng_checksum}")
    if project.guarantee_claims:
        raise RuntimeError(f"S4_G_NOT_INERT scenario={scenario} trial_id={trial_id} claims={len(project.guarantee_claims)}")

    result = monte_carlo._trial_result_from_project(
        project, scenario_id=scenario, collection_probability=collection_probability,
        recovery_rate_pct=recovery_rate_pct, trial_id=trial_id,
        master_seed=constants.MASTER_SEED, source_sha=SOURCE_SHA,
    )
    return {
        "trial_id": trial_id,
        "trial_fingerprint": result.trial_fingerprint,
        "financial_path_fingerprint_sha256": monte_carlo.financial_path_fingerprint(result),
        "rng_checksum": result.rng_checksum,
        "rng_draw_count": result.rng_draw_count,
        "rng_checksum_fingerprint_sha256": result.rng_checksum_fingerprint_sha256,
        "financial_values": {
            "final_close_date": result.final_close_date,
            "final_net_project_equity": result.final_net_project_equity,
            "final_cash": result.final_cash,
            "cumulative_project_profit": result.cumulative_project_profit,
            "operating_net_profit": result.operating_net_profit,
            "termination_count": result.termination_count,
            "secondary_cycle_count": result.secondary_cycle_count,
            "owned_bikes": result.owned_bikes,
            "held_assets": result.held_assets,
            "total_operating_revenue": result.total_operating_revenue,
            "bad_debt": result.bad_debt,
            "guarantee_recovered": result.guarantee_recovered,
            "partner1_final_entitlement": result.partner1_final_entitlement,
            "partner2_final_entitlement": result.partner2_final_entitlement,
        },
        "daily_path_fingerprint_sha256": stable_sha(rows),
        "daily_rows": len(rows),
        "daily_balance_checks": len(project.daily_balance_checks),
        "daily_rollforward_equation_checks": len(rows) * 5,
        "max_abs_balance_difference": max(abs(row["balance_check"]["Balance_Difference"]) for row in rows),
        "guarantee_claim_count": len(project.guarantee_claims),
        "held_asset_count": final["held_assets"],
        "elapsed_seconds": time.perf_counter() - started,
        "_daily_evidence": rows if scenario == SCENARIOS[0] and trial_id == 1 else None,
        "_selected_snapshots": selected if trial_id == 1 else None,
        "_expansions": expansions if trial_id == 1 else None,
    }


def append_r4(text: str) -> None:
    previous = R4_PATH.read_text(encoding="utf-8")
    if "## S4 runtime evidence" not in previous and "## S4 STOP" not in previous and "## S4 execution failure" not in previous:
        R4_PATH.write_text(previous.rstrip() + "\n\n" + text.strip() + "\n", encoding="utf-8")


def package_exists(name: str) -> bool:
    try:
        importlib.metadata.version(name)
        return True
    except importlib.metadata.PackageNotFoundError:
        return False


def main() -> int:
    started_at = now_utc()
    run_id = os.environ.get("GITHUB_RUN_ID", "LOCAL_NOT_GITHUB_ACTIONS")
    tested_sha = os.environ.get("GITHUB_SHA", "LOCAL_NOT_GITHUB_ACTIONS")
    run_url = os.environ.get("S4_RUN_URL", "")
    reference = json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))
    if reference.get("historical_comparison_only") is not True:
        raise RuntimeError("S4_REFERENCE_FIXTURE_MUST_BE_HISTORICAL_ONLY")
    if TRIAL_COUNT != constants.C100_STATISTICAL_START_TRIALS:
        raise RuntimeError(f"S4_EXPECTED_N0_{constants.C100_STATISTICAL_START_TRIALS}_GOT_{TRIAL_COUNT}")

    all_records: dict[str, list[dict[str, Any]]] = {}
    scenario_summaries: dict[str, dict[str, Any]] = {}
    baseline_path: str | None = None
    baseline_fingerprint: str | None = None
    baseline_values: dict[str, Any] | None = None
    canonical_ledger: list[dict[str, Any]] | None = None
    canonical_snapshots: dict[str, Any] | None = None
    canonical_expansions: list[dict[str, Any]] | None = None
    path_fingerprints: set[str] = set()
    financial_fingerprints: set[str] = set()
    audit_fingerprints: set[str] = set()
    total_rows = total_balance_checks = total_equations = total_claims = 0
    try:
        for scenario in SCENARIOS:
            scenario_records = []
            scenario_paths: set[str] = set()
            scenario_financial: set[str] = set()
            scenario_audit: set[str] = set()
            scenario_rows = scenario_balances = scenario_equations = scenario_claims = 0
            scenario_started = time.perf_counter()
            print(json.dumps({"S4_SCENARIO_START": scenario, "trial_count": TRIAL_COUNT, "source_sha": SOURCE_SHA, "cohort_id": COHORT_ID}), flush=True)
            for trial_id in range(1, TRIAL_COUNT + 1):
                record = perform_trial(scenario, trial_id, reference)
                daily = record.pop("_daily_evidence")
                selected = record.pop("_selected_snapshots")
                expansions = record.pop("_expansions")
                scenario_paths.add(record["daily_path_fingerprint_sha256"])
                scenario_financial.add(record["trial_fingerprint"])
                scenario_audit.add(record["rng_checksum_fingerprint_sha256"])
                path_fingerprints.add(record["daily_path_fingerprint_sha256"])
                financial_fingerprints.add(record["trial_fingerprint"])
                audit_fingerprints.add(record["rng_checksum_fingerprint_sha256"])
                scenario_rows += record["daily_rows"]
                scenario_balances += record["daily_balance_checks"]
                scenario_equations += record["daily_rollforward_equation_checks"]
                scenario_claims += record["guarantee_claim_count"]
                if scenario == SCENARIOS[0] and trial_id == 1:
                    canonical_ledger, canonical_snapshots, canonical_expansions = daily, selected, expansions
                    baseline_path = record["daily_path_fingerprint_sha256"]
                    baseline_fingerprint = record["trial_fingerprint"]
                    baseline_values = record["financial_values"]
                else:
                    if record["daily_path_fingerprint_sha256"] != baseline_path:
                        raise RuntimeError(f"S4_PATH_FINGERPRINT_MISMATCH scenario={scenario} trial_id={trial_id}")
                    if record["trial_fingerprint"] != baseline_fingerprint:
                        raise RuntimeError(f"S4_FINANCIAL_FINGERPRINT_MISMATCH scenario={scenario} trial_id={trial_id}")
                    if record["financial_values"] != baseline_values:
                        raise RuntimeError(f"S4_FINANCIAL_VALUES_MISMATCH scenario={scenario} trial_id={trial_id}")
                if record["rng_draw_count"] != 0 or record["rng_checksum"] != 0:
                    raise RuntimeError(f"S4_RNG_NOT_ZERO scenario={scenario} trial_id={trial_id}")
                if record["max_abs_balance_difference"] != 0:
                    raise RuntimeError(f"S4_BALANCE_DIFFERENCE_NOT_ZERO scenario={scenario} trial_id={trial_id}")
                scenario_records.append(record)
                if trial_id % 25 == 0:
                    print(json.dumps({
                        "S4_PROGRESS": scenario, "trial_id": trial_id,
                        "trial_count": TRIAL_COUNT,
                        "elapsed_seconds": time.perf_counter() - scenario_started,
                        "daily_rows": record["daily_rows"],
                        "max_abs_balance_difference": record["max_abs_balance_difference"],
                    }, sort_keys=True), flush=True)
                    gc.collect()
            if len(scenario_paths) != 1 or len(scenario_financial) != 1:
                raise RuntimeError(f"S4_SCENARIO_NOT_DEGENERATE scenario={scenario} paths={len(scenario_paths)} fingerprints={len(scenario_financial)}")
            if len(scenario_audit) != TRIAL_COUNT:
                raise RuntimeError(f"S4_AUDIT_FINGERPRINT_COLLISION scenario={scenario}")
            if scenario_claims != 0:
                raise RuntimeError(f"S4_G_NOT_INERT scenario={scenario} claims={scenario_claims}")
            all_records[scenario] = scenario_records
            scenario_summaries[scenario] = {
                "trial_count": TRIAL_COUNT,
                "trial_ids": [1, TRIAL_COUNT],
                "trial_fingerprint_unique_count": 1,
                "N_unique_paths": 1,
                "degeneracy_status": "DEGENERATE_DETERMINISTIC",
                "G_status": "G_INERT",
                "rng_draw_count_values": [0],
                "rng_checksum_values": [0],
                "rng_audit_fingerprint_unique_count": len(scenario_audit),
                "daily_rows_total": scenario_rows,
                "daily_balance_checks_total": scenario_balances,
                "daily_rollforward_equation_checks_total": scenario_equations,
                "max_abs_balance_difference": 0,
                "claim_count_total_across_trials": scenario_claims,
                "elapsed_seconds": time.perf_counter() - scenario_started,
            }
            total_rows += scenario_rows
            total_balance_checks += scenario_balances
            total_equations += scenario_equations
            total_claims += scenario_claims
            print(json.dumps({"S4_SCENARIO_COMPLETE": scenario, **scenario_summaries[scenario]}, sort_keys=True), flush=True)

        if len(path_fingerprints) != 1 or len(financial_fingerprints) != 1:
            raise RuntimeError(f"S4_C100_G_INERTNESS_FAILURE paths={len(path_fingerprints)} financial_fingerprints={len(financial_fingerprints)}")
        if len(audit_fingerprints) != len(SCENARIOS) * TRIAL_COUNT:
            raise RuntimeError("S4_RNG_AUDIT_FINGERPRINT_COLLISION")
        if canonical_ledger is None or canonical_snapshots is None or canonical_expansions is None or baseline_values is None:
            raise RuntimeError("S4_CANONICAL_EVIDENCE_MISSING")

        finished_at = now_utc()
        test_log = Path("s4_evidence/full-suite.log")
        test_junit = Path("s4_evidence/junit.xml")
        test_exit = Path("s4_evidence/pytest-exit-code.txt")
        log_hash = sha256(test_log.read_bytes()).hexdigest() if test_log.exists() else None
        junit_hash = sha256(test_junit.read_bytes()).hexdigest() if test_junit.exists() else None
        pytest_exit = int(test_exit.read_text().strip()) if test_exit.exists() else None
        reference_hash = sha256(REFERENCE_PATH.read_bytes()).hexdigest()

        golden = {
            "schema_version": "v2.3",
            "golden_type": "C100_DETERMINISTIC",
            "source_sha": SOURCE_SHA,
            "cohort_id": COHORT_ID,
            "master_seed": constants.MASTER_SEED,
            "rng_algorithm": "RNG_SHA256_DERIVED_V1",
            "trial_id_policy": "IDs 1..N0; identical paths are not independent stochastic samples",
            "trial_count_per_scenario": TRIAL_COUNT,
            "trial_count_total": len(SCENARIOS) * TRIAL_COUNT,
            "scenarios": {
                scenario: {
                    "scenario_summary": scenario_summaries[scenario],
                    "trial_records": all_records[scenario],
                } for scenario in SCENARIOS
            },
            "N_unique_paths": 1,
            "degeneracy_status": "DEGENERATE_DETERMINISTIC",
            "G_status": "G_INERT",
            "financial_trial_fingerprint_sha256": baseline_fingerprint,
            "daily_path_fingerprint_sha256": baseline_path,
            "final_financial_values": baseline_values,
            "reference_snapshot_comparison": {
                "authority": reference["authority"],
                "historical_comparison_only": True,
                "status": "PASS",
                "snapshots": list(canonical_snapshots.values()),
                "first_expansion_bikes_checked": canonical_expansions,
            },
            "canonical_daily_ledger": {
                "row_count": len(canonical_ledger),
                "rows": canonical_ledger,
                "sha256": stable_sha(canonical_ledger),
            },
            "accounting_validation": {
                "balance_checks_total": total_balance_checks,
                "rollforward_equation_checks_total": total_equations,
                "rollforward_equations": [
                    "Cash: Opening_Cash + Inflows - Outflows == Closing_Cash",
                    "Accounts receivable: Opening_AR + Accruals - Collections - TransfersToGuarantee == Closing_AR",
                    "Gross bike assets: Opening_Gross_Bike_Assets + Capitalized_Purchases_And_Customs - Gross_Writeoffs_On_Ownership == Closing_Gross_Bike_Assets",
                    "Accumulated depreciation: Opening_Accumulated_Depreciation + Expense_Depreciation - AD_Removed_On_Writeoff == Closing_Accumulated_Depreciation",
                    "Equity: Opening_Equity + Operating_Net_Profit == Closing_Equity",
                    "Every day: Total_Assets == Total_Equity and Balance_Difference == 0",
                ],
                "max_abs_balance_difference": 0,
            },
            "rng_audit": {
                "rng_draw_count": 0,
                "rng_checksum": 0,
                "all_records_zero": True,
                "rng_audit_fingerprint_unique_count": len(audit_fingerprints),
                "duplicate_checksum_rule": "Check only rows with rng_draw_count > 0",
            },
            "execution": {
                "workflow_run_id": run_id,
                "workflow_run_url": run_url,
                "tested_workflow_head_sha": tested_sha,
                "source_sha": SOURCE_SHA,
                "pytest_command": "python -m pytest -q tests --junitxml=s4_evidence/junit.xml",
                "pytest_exit_code": pytest_exit,
                "pytest_log_sha256": log_hash,
                "pytest_junit_sha256": junit_hash,
                "started_at_utc": started_at,
                "finished_at_utc": finished_at,
                "python_version": platform.python_version(),
                "packages": {name: (importlib.metadata.version(name) if package_exists(name) else None) for name in ("pytest", "scipy", "numpy", "openpyxl", "pyarrow")},
                "reference_fixture_sha256": reference_hash,
            },
            "historical_golden_mutated": False,
            "historical_results_mutated": False,
            "status": "PASS_S4_C100_NEW_SOURCE_GOLDEN",
        }
        golden_hash = write_json(GOLDEN_PATH, golden)
        golden_bytes = GOLDEN_PATH.stat().st_size
        if sha256(GOLDEN_PATH.read_bytes()).hexdigest() != golden_hash:
            raise RuntimeError("S4_GOLDEN_HASH_READBACK_MISMATCH")

        manifest = {
            "schema_version": "s4-c100-golden-manifest-v1",
            "source_sha": SOURCE_SHA,
            "cohort_id": COHORT_ID,
            "model_schema_version": "v2.3",
            "master_seed": constants.MASTER_SEED,
            "scenario_ids": list(SCENARIOS),
            "trial_ids_per_scenario": [1, TRIAL_COUNT],
            "trial_count_total": len(SCENARIOS) * TRIAL_COUNT,
            "N_unique_paths": 1,
            "degeneracy_status": "DEGENERATE_DETERMINISTIC",
            "G_status": "G_INERT",
            "golden_path": str(GOLDEN_PATH),
            "golden_bytes": golden_bytes,
            "golden_sha256": golden_hash,
            "golden_content_sha256": stable_sha(golden),
            "workflow_run_id": run_id,
            "workflow_run_url": run_url,
            "tested_workflow_head_sha": tested_sha,
            "reference_fixture_git_blob_sha": os.environ.get("S4_REFERENCE_BLOB_SHA"),
            "reference_fixture_sha256": reference_hash,
            "pytest_exit_code": pytest_exit,
            "pytest_log_sha256": log_hash,
            "pytest_junit_sha256": junit_hash,
            "started_at_utc": started_at,
            "finished_at_utc": finished_at,
            "daily_rows_per_trial": len(canonical_ledger),
            "daily_rows_total_across_all_trials": total_rows,
            "daily_balance_checks_total": total_balance_checks,
            "daily_rollforward_equation_checks_total": total_equations,
            "max_abs_balance_difference": 0,
            "rng_draw_count": 0,
            "rng_checksum": 0,
            "historical_files_modified": False,
        }
        manifest_hash = write_json(MANIFEST_PATH, manifest)
        snapshot_rows = [
            "| {date} | {cash} | {partner1_reinvestment_balance} | {partner2_reinvestment_balance} | {bikes} | {prep} | {active_primary_contracts} | {owned_transferred_bikes} | {net_equity} | PASS |".format(**canonical_snapshots[row["date"]])
            for row in reference["snapshots"]
        ]
        table = "\n".join([
            "| التاريخ | النقد | Partner1_RB | Partner2_RB | الدراجات | PREP | عقد أساسي نشط | مملوكة | صافي الحقوق | الحكم |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
            *snapshot_rows,
        ])
        report = f"""# S4 — C100 v2.3 Golden execution report

Status: PASS_S4_C100_NEW_SOURCE_GOLDEN

Source SHA: {SOURCE_SHA}
Cohort ID: {COHORT_ID}
Tested workflow HEAD: {tested_sha}
GitHub Actions Run: {run_id} ({run_url})
Test command: python -m pytest -q tests --junitxml=s4_evidence/junit.xml
Pytest exit code: {pytest_exit}
Full-suite log SHA-256: {log_hash}
JUnit SHA-256: {junit_hash}
Golden: {GOLDEN_PATH}
Golden bytes: {golden_bytes}
Golden SHA-256: {golden_hash}
Manifest: {MANIFEST_PATH}
Manifest SHA-256: {manifest_hash}
Run count: {len(SCENARIOS)} scenarios × {TRIAL_COUNT} complete runs = {len(SCENARIOS) * TRIAL_COUNT}

All trial_fingerprint values are equal across 1,500 trials and G levels: {baseline_fingerprint}
All financial path fingerprints are equal: {baseline_path}
Every run has rng_draw_count=0 and rng_checksum=0.
Every scenario has DEGENERATE_DETERMINISTIC, N_unique_paths=1, and G_INERT.
Daily accounting checks: {total_balance_checks}; roll-forward equations: {total_equations}; maximum absolute balance difference: 0.
Historical Golden and historical results remain unchanged.

## §21.8 snapshot comparison

{table}

## Final values

{json.dumps(baseline_values, ensure_ascii=False, indent=2, sort_keys=True)}

## Judgment

S4 generated a new source-specific C100 Golden and retained the §21.8 history as a comparison oracle only. This result does not by itself establish stochastic convergence, production Gate A/B for non-C100, or final delivery/release acceptance.
"""
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(report, encoding="utf-8")
        report_hash = sha256(REPORT_PATH.read_bytes()).hexdigest()
        summary = {
            "status": "PASS_S4_C100_NEW_SOURCE_GOLDEN",
            "source_sha": SOURCE_SHA,
            "cohort_id": COHORT_ID,
            "trial_count_total": len(SCENARIOS) * TRIAL_COUNT,
            "N_unique_paths": 1,
            "financial_trial_fingerprint_sha256": baseline_fingerprint,
            "daily_path_fingerprint_sha256": baseline_path,
            "golden_sha256": golden_hash,
            "manifest_sha256": manifest_hash,
            "report_sha256": report_hash,
            "pytest_exit_code": pytest_exit,
            "pytest_log_sha256": log_hash,
            "pytest_junit_sha256": junit_hash,
            "workflow_run_id": run_id,
        }
        Path("s4_evidence").mkdir(parents=True, exist_ok=True)
        write_json(Path("s4_evidence/acceptance-summary.json"), summary)
        append_r4(f"""## S4 runtime evidence

Run ID: {run_id} ({run_url})
Source SHA: {SOURCE_SHA}
Cohort ID: {COHORT_ID}
Full executions: {len(SCENARIOS) * TRIAL_COUNT}
Pytest exit code: {pytest_exit}; 177 UNIQUE must pass in the recorded log.
Full-suite log SHA-256: {log_hash}
JUnit SHA-256: {junit_hash}
trial_fingerprint: {baseline_fingerprint}
daily path SHA-256: {baseline_path}
Daily balance checks: {total_balance_checks}
Five roll-forward equations checked: {total_equations}
Maximum absolute balance difference: 0
RNG: every run has rng_draw_count=0 and rng_checksum=0
Status: PASS_S4_C100_NEW_SOURCE_GOLDEN
Golden: {GOLDEN_PATH}; bytes {golden_bytes}; SHA-256 {golden_hash}
Manifest: {MANIFEST_PATH}; SHA-256 {manifest_hash}
Report: {REPORT_PATH}; SHA-256 {report_hash}
Historical Golden and historical outputs: unchanged.
""")
        print(json.dumps({"S4_RESULT": summary, "daily_balance_checks": total_balance_checks, "rollforward_equation_checks": total_equations, "max_abs_balance_difference": 0}, ensure_ascii=False, sort_keys=True), flush=True)
        return 0

    except ReferenceMismatch as exc:
        failure_path = FAILURE_DIR / f"UNDEFINED_BUSINESS_RULE_S4_C100_{SOURCE_SHA}.json"
        failure_hash = write_json(failure_path, exc.payload)
        append_r4(f"""## S4 STOP — UNDEFINED_BUSINESS_RULE

Run ID: {run_id}; source SHA: {SOURCE_SHA}; cohort: {COHORT_ID}
First mismatch: date={exc.payload.get("date")}, field={exc.payload.get("field")}, expected={exc.payload.get("expected")}, actual={exc.payload.get("actual")}.
Failure record: {failure_path}; SHA-256: {failure_hash}
Stopped immediately; no Golden was created/promoted; no reference or model values were changed.
""")
        print(json.dumps({"S4_STATUS": "UNDEFINED_BUSINESS_RULE", "failure_path": str(failure_path), "failure_sha256": failure_hash, **exc.payload}, ensure_ascii=False, sort_keys=True), flush=True)
        return 3
    except Exception as exc:
        failure_path = FAILURE_DIR / f"S4_EXECUTION_FAILURE_C100_{SOURCE_SHA}.json"
        payload = {
            "status": "S4_EXECUTION_FAILURE",
            "source_sha": SOURCE_SHA,
            "cohort_id": COHORT_ID,
            "workflow_run_id": run_id,
            "tested_workflow_head_sha": tested_sha,
            "started_at_utc": started_at,
            "failed_at_utc": now_utc(),
            "exception_type": type(exc).__name__,
            "error": str(exc),
            "note": "No Golden may be accepted on this failure.",
        }
        failure_hash = write_json(failure_path, payload)
        append_r4(f"""## S4 execution failure — no Golden acceptance

Run ID: {run_id}; source SHA: {SOURCE_SHA}; cohort: {COHORT_ID}
Exception: {type(exc).__name__}: {str(exc)}
Failure record: {failure_path}; SHA-256: {failure_hash}
No Golden was accepted. Review the exact Run log before retry.
""")
        print(json.dumps({"S4_STATUS": "S4_EXECUTION_FAILURE", "failure_path": str(failure_path), "failure_sha256": failure_hash, **payload}, ensure_ascii=False, sort_keys=True), file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
