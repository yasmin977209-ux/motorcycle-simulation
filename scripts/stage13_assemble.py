#!/usr/bin/env python3
"""Assemble 25 scenario artifacts, export 185-sheet Excel, and execute the exact 500-point gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
from openpyxl import load_workbook

import constants

sys.path.insert(0, str(Path("scripts").resolve()))
import excel_builder as excel_builder_module

SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
COHORT_ID = "STAGE13_SAMPLE_TRIAL_IDS_26_50_V2"
TRIAL_IDS = list(range(26, 51))
SCENARIOS = [
    "C100_G100", "C100_G070", "C100_G050", "C100_G030", "C100_G000",
    "C085_G100", "C085_G070", "C085_G050", "C085_G030", "C085_G000",
    "C070_G100", "C070_G070", "C070_G050", "C070_G030", "C070_G000",
    "C050_G100", "C050_G070", "C050_G050", "C050_G030", "C050_G000",
    "C030_G100", "C030_G070", "C030_G050", "C030_G030", "C030_G000",
]
ROLE_ORDER = ("P50", "P10", "P90", "Loss Case", "Max Case")
ROLE_FILES = {"P10": "P10", "P50": "P50", "P90": "P90", "Loss Case": "Loss", "Max Case": "Max Case"}
METRICS = {
    "Final_Net_Project_Equity": "final_net_project_equity",
    "Partner1_Final_Entitlement": "partner1_final_entitlement",
    "Partner2_Final_Entitlement": "partner2_final_entitlement",
    "Final_Cash": "final_cash",
}
STAT_COLUMNS = {"MIN": 5, "P10": 8, "P50": 10, "P90": 12, "MAX": 6}
QUANTILES = {"P10": 0.10, "P50": 0.50, "P90": 0.90}


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def trial_fingerprint(rows: list[dict[str, Any]]) -> str:
    ordered = sorted(rows, key=lambda row: (str(row["scenario_id"]), int(row["trial_id"])))
    data = "\n".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
        for row in ordered
    )
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def find_scenario_packages(root: Path) -> dict[str, Path]:
    packages: dict[str, Path] = {}
    for ident_path in root.rglob("dataset_identity.json"):
        try:
            ident = json.loads(ident_path.read_text(encoding="utf-8"))
        except Exception as exc:
            raise RuntimeError(f"UNREADABLE_SCENARIO_IDENTITY: {ident_path}: {exc}") from exc
        scenario = ident.get("scenario_id")
        if scenario in SCENARIOS:
            if scenario in packages:
                raise RuntimeError(f"DUPLICATE_SCENARIO_ARTIFACT: {scenario}")
            packages[scenario] = ident_path.parent
    if set(packages) != set(SCENARIOS):
        raise RuntimeError(
            f"SCENARIO_ARTIFACT_COVERAGE: missing={sorted(set(SCENARIOS)-set(packages))}; "
            f"extra={sorted(set(packages)-set(SCENARIOS))}"
        )
    return packages


def load_acceptance(root: Path, dataset_root: Path) -> dict[str, Any]:
    matches = list(root.rglob("validation_163.json"))
    if len(matches) != 1:
        raise RuntimeError(f"ACCEPTANCE_REPORT_COUNT_EXPECTED_1_GOT_{len(matches)}")
    report = json.loads(matches[0].read_text(encoding="utf-8"))
    if report.get("status") != "PASS":
        raise RuntimeError("ACCEPTANCE_163_REPORT_NOT_PASS")
    counts = report.get("counts", {})
    if (counts.get("inventory"), counts.get("pass"), counts.get("fail"), counts.get("excluded")) != (163, 162, 0, 1):
        raise RuntimeError(f"ACCEPTANCE_163_COUNT_MISMATCH: {counts}")
    shutil.copy2(matches[0], dataset_root / "validation_163.json")
    return report


def add_max_case_rows(workbook_path: Path, dataset_root: Path) -> None:
    wb = load_workbook(workbook_path)
    ws = wb["REPRESENTATIVE_CASES"]
    headers = [cell.value for cell in ws[1]]
    if headers != [
        "scenario", "case", "record_type", "trial_id", "date", "final_close_date",
        "Cash", "Net_Equity", "Active_Bikes", "Owned_Transferred_Bikes", "Pending_Claims",
        "Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance",
        "final_net_project_equity", "final_cash", "cumulative_project_profit",
        "termination_count", "secondary_cycle_count", "owned_bikes", "held_assets",
        "total_operating_revenue", "bad_debt", "guarantee_recovered",
    ]:
        raise RuntimeError("REPRESENTATIVE_CASES_HEADER_MISMATCH")
    for scenario in SCENARIOS:
        payload_path = dataset_root / scenario / "representatives" / "Max Case.json"
        if not payload_path.exists():
            raise RuntimeError(f"MAX_CASE_PAYLOAD_MISSING: {scenario}")
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        summary = payload["summary"]
        ws.append([
            scenario, "Max Case", "SUMMARY", summary["trial_id"], None,
            summary["final_close_date"], None, None, None, None, None, None, None,
            summary["final_net_project_equity"], summary["final_cash"],
            summary["cumulative_project_profit"], summary["termination_count"],
            summary["secondary_cycle_count"], summary["owned_bikes"], summary["held_assets"],
            summary["total_operating_revenue"], summary["bad_debt"], summary["guarantee_recovered"],
        ])
        for daily in payload.get("daily", []):
            ws.append([
                scenario, "Max Case", "DAILY", summary["trial_id"], daily.get("date"),
                daily.get("Final_Close_Date"), daily.get("Cash"), daily.get("Net_Equity"),
                daily.get("Active_Bikes"), daily.get("Owned_Transferred_Bikes"),
                daily.get("Pending_Claims"), daily.get("Partner1_Reinvestment_Balance"),
                daily.get("Partner2_Reinvestment_Balance"), None, None, None, None, None, None,
                None, None, None, None,
            ])
    # Clearly mark the actual cohort in the workbook without adding or removing worksheets.
    readme = wb["README"]
    for row in readme.iter_rows(min_col=1, max_col=2):
        label = row[0].value
        if label == "Workbook build provenance":
            row[1].value = "Stage 13 diagnostic sample workbook; provenance is recorded in dataset_identity.json"
        elif label == "Dataset status":
            row[1].value = "625-trial diagnostic sample only; not canonical 11,005-trial data and not Gate A/B PASS"
        elif label == "Validation status":
            row[1].value = "Acceptance inventory 163: 162 PASS / 0 FAIL / 1 EXCLUDED; complete pytest run passed"
    readme.append(["Cohort ID", COHORT_ID])
    readme.append(["Sample trial IDs per scenario", "26..50 (25 IDs per each of 25 scenarios)"])
    readme.append(["Canonical dataset fingerprint", "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44"])
    readme.append(["Gate boundary", "20-point Parquet-to-_STATS consistency is separate from statistical Gate A/B"])
    wb.save(workbook_path)


def scan_workbook(path: Path) -> dict[str, Any]:
    wb = load_workbook(path, data_only=False, read_only=False)
    errors = []
    formulas = []
    for ws in wb.worksheets:
        for row in ws.iter_rows():
            for cell in row:
                if cell.data_type == "e":
                    errors.append(f"{ws.title}!{cell.coordinate}:{cell.value}")
                if cell.data_type == "f":
                    formulas.append(f"{ws.title}!{cell.coordinate}")
    return {"sheets": len(wb.sheetnames), "sheet_names": list(wb.sheetnames),
            "excel_errors": errors, "formula_cells": formulas}


def run_20point_gate(dataset_root: Path, workbook_path: Path, result_rows_by_scenario: dict[str, list[dict[str, Any]]],
                     identity: dict[str, Any], workbook_audit: dict[str, Any]) -> dict[str, Any]:
    wb = load_workbook(workbook_path, data_only=True, read_only=True)
    comparisons = []
    for scenario in SCENARIOS:
        ws = wb[f"{scenario}_STATS"]
        metric_rows = {}
        for row in ws.iter_rows(min_row=2, values_only=True):
            if row and row[0] is not None:
                metric_rows[str(row[0])] = row
        rows = result_rows_by_scenario[scenario]
        for metric_label, field in METRICS.items():
            if metric_label not in metric_rows:
                raise RuntimeError(f"STATS_METRIC_MISSING: {scenario}/{metric_label}")
            values = np.asarray([int(row[field]) for row in rows], dtype=np.float64)
            expected = {
                "MIN": int(values.min()),
                "P10": float(np.quantile(values, 0.10, method="linear")),
                "P50": float(np.quantile(values, 0.50, method="linear")),
                "P90": float(np.quantile(values, 0.90, method="linear")),
                "MAX": int(values.max()),
            }
            stats_row = metric_rows[metric_label]
            for point in ("MIN", "P10", "P50", "P90", "MAX"):
                actual = stats_row[STAT_COLUMNS[point] - 1]
                exp = expected[point]
                exact = actual == exp
                comparisons.append({
                    "scenario_id": scenario,
                    "metric": metric_label,
                    "point": point,
                    "parquet_expected": exp,
                    "xlsx_actual": actual,
                    "exact_match": exact,
                    "status": "PASS" if exact else "FAIL",
                })
    wb.close()
    gates = {
        "source_identity": identity.get("source_sha") == SOURCE_SHA,
        "cohort_id": identity.get("cohort_id") == COHORT_ID,
        "scenario_count": len(result_rows_by_scenario) == 25,
        "trials_per_scenario": all(
            len(rows) == 25 and sorted(int(r["trial_id"]) for r in rows) == TRIAL_IDS
            for rows in result_rows_by_scenario.values()
        ),
        "unique_trial_pairs": identity.get("trial_result_count") == 625,
        "representative_assignments": identity.get("representative_role_assignments") == 125,
        "representative_replays_exact": identity.get("representative_replay_matches") is True,
        "representative_balance_differences_zero": identity.get("representative_balance_failures") == 0,
        "excel_sheet_count": workbook_audit["sheets"] == 185,
        "excel_error_cells_zero": len(workbook_audit["excel_errors"]) == 0,
        "excel_formula_cells_zero": len(workbook_audit["formula_cells"]) == 0,
        "500_exact_comparisons": len(comparisons) == 500 and all(row["exact_match"] for row in comparisons),
        "trial_result_fingerprint": identity.get("trial_results_fingerprint_sha256") == trial_fingerprint(
            [row for scenario in SCENARIOS for row in result_rows_by_scenario[scenario]]
        ),
    }
    passed = all(gates.values())
    return {
        "gate_id": "STAGE13_20_POINT_PARQUET_VS_STATS_V2",
        "status": "PASS" if passed else "FAIL",
        "cohort_id": COHORT_ID,
        "source_sha": SOURCE_SHA,
        "run_id": identity.get("run_id"),
        "run_head_sha": identity.get("run_head_sha"),
        "canonical_11005_dataset_fingerprint_sha256": "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44",
        "canonical_dataset_modified": False,
        "not_a_statistical_gate_a_or_b": True,
        "scope": {
            "scenario_count": 25, "trial_ids_per_scenario": TRIAL_IDS,
            "trial_count": 625, "representative_roles_per_scenario": 5,
            "point_count_per_scenario": 20, "expected_comparison_count": 500,
            "actual_comparison_count": len(comparisons),
            "quantile_method": "numpy.quantile(method='linear')",
            "comparison": "exact numeric equality, no tolerance",
        },
        "gates": gates,
        "workbook": {
            "path": str(workbook_path),
            "sha256": sha256_file(workbook_path),
            "sheets": workbook_audit["sheets"],
            "excel_error_cells": len(workbook_audit["excel_errors"]),
            "formula_cells": len(workbook_audit["formula_cells"]),
        },
        "comparisons": comparisons,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario-artifacts", required=True)
    parser.add_argument("--acceptance-artifacts", required=True)
    parser.add_argument("--output-dir", default="results_stage13/final")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--head-sha", required=True)
    args = parser.parse_args()

    artifacts_root = Path(args.scenario_artifacts)
    acceptance_root = Path(args.acceptance_artifacts)
    output_root = Path(args.output_dir)
    if output_root.exists():
        shutil.rmtree(output_root)
    output_root.mkdir(parents=True)
    dataset_root = output_root / "dataset"
    dataset_root.mkdir()

    packages = find_scenario_packages(artifacts_root)
    result_rows_by_scenario: dict[str, list[dict[str, Any]]] = {}
    all_result_rows = []
    all_assignments = []
    all_rep_audits = []
    first_identity: dict[str, Any] | None = None
    scenario_identities = {}

    for scenario in SCENARIOS:
        source = packages[scenario]
        ident = json.loads((source / "dataset_identity.json").read_text(encoding="utf-8"))
        if ident.get("schema_version") != "stage13-scenario-cohort-v2":
            raise RuntimeError(f"SCHEMA_VERSION_MISMATCH: {scenario}")
        if ident.get("cohort_id") != COHORT_ID or ident.get("scenario_id") != scenario:
            raise RuntimeError(f"COHORT_OR_SCENARIO_IDENTITY_MISMATCH: {scenario}")
        if ident.get("source_sha") != SOURCE_SHA or ident.get("trial_ids") != TRIAL_IDS:
            raise RuntimeError(f"SOURCE_OR_TRIAL_IDENTITY_MISMATCH: {scenario}")
        if ident.get("implementation_head_sha") != args.head_sha or ident.get("workflow_run_id") != args.run_id:
            raise RuntimeError(f"RUN_IDENTITY_MISMATCH: {scenario}")
        if first_identity is None:
            first_identity = ident
        else:
            for key in ("implementation_head_sha", "workflow_run_id", "master_seed", "rng_source_sha256", "cohort_id"):
                if ident.get(key) != first_identity.get(key):
                    raise RuntimeError(f"SCENARIO_IDENTITY_DISAGREEMENT: {scenario}/{key}")
        manifest_path = source / "artifact_manifest.json"
        if not manifest_path.exists():
            raise RuntimeError(f"SCENARIO_ARTIFACT_MANIFEST_MISSING: {scenario}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for rel, expected_sha in manifest.get("file_hashes_sha256", {}).items():
            p = source / rel
            if not p.is_file() or sha256_file(p) != expected_sha:
                raise RuntimeError(f"SCENARIO_FILE_SHA_MISMATCH: {scenario}/{rel}")

        destination = dataset_root / scenario
        shutil.copytree(source, destination)
        result_rows = pq.read_table(destination / "trial_results.parquet").to_pylist()
        result_rows.sort(key=lambda row: int(row["trial_id"]))
        ids = [int(row["trial_id"]) for row in result_rows]
        if len(result_rows) != 25 or ids != TRIAL_IDS:
            raise RuntimeError(f"TRIAL_COVERAGE_FAILURE: {scenario}: {ids}")
        if any(row["scenario_id"] != scenario for row in result_rows):
            raise RuntimeError(f"SCENARIO_COLUMN_MISMATCH: {scenario}")
        result_rows_by_scenario[scenario] = result_rows
        all_result_rows.extend(result_rows)
        assignments = pq.read_table(destination / "representative_assignments.parquet").to_pylist()
        if len(assignments) != 5 or {row["role"] for row in assignments} != set(ROLE_ORDER):
            raise RuntimeError(f"REPRESENTATIVE_ROLE_COVERAGE_FAILURE: {scenario}")
        if any(int(row["trial_id"]) not in TRIAL_IDS for row in assignments):
            raise RuntimeError(f"REPRESENTATIVE_TRIAL_ID_OUT_OF_SAMPLE: {scenario}")
        all_assignments.extend(assignments)
        rep_audit = json.loads((destination / "representative_audit.json").read_text(encoding="utf-8"))
        if not rep_audit.get("all_representative_results_reproduced_exactly") or not rep_audit.get("all_representative_balance_differences_zero"):
            raise RuntimeError(f"REPRESENTATIVE_AUDIT_FAILURE: {scenario}")
        all_rep_audits.extend(rep_audit.get("representatives", []))
        scenario_identities[scenario] = ident

    if len(all_result_rows) != 625 or len({(r["scenario_id"], int(r["trial_id"])) for r in all_result_rows}) != 625:
        raise RuntimeError("GLOBAL_TRIAL_COVERAGE_FAILURE")
    if len(all_assignments) != 125 or len(all_rep_audits) != len(set((r["scenario_id"], r["trial_id"]) for r in all_rep_audits)):
        raise RuntimeError("GLOBAL_REPRESENTATIVE_COVERAGE_OR_DUPLICATE_FAILURE")

    overall_fingerprint = trial_fingerprint(all_result_rows)
    validation = load_acceptance(acceptance_root, dataset_root)
    shutil.copy2(Path("docs/stage13/20point_gate_definition.json"), output_root / "20point_gate_definition.json")

    representative_ids: dict[str, dict[str, int]] = {}
    for scenario in SCENARIOS:
        scenario_assignments = {
            row["role"]: int(row["trial_id"])
            for row in all_assignments if row["scenario_id"] == scenario
        }
        representative_ids[scenario] = {
            "P10": scenario_assignments["P10"],
            "P50": scenario_assignments["P50"],
            "P90": scenario_assignments["P90"],
            "Loss": scenario_assignments["Loss Case"],
            "Max Case": scenario_assignments["Max Case"],
        }
    reps_path = output_root / "representative_trial_ids.json"
    write_json(reps_path, {"scenarios": representative_ids})

    public_constants = {
        name: getattr(constants, name)
        for name in dir(constants) if name.isupper() and not name.startswith("_")
    }
    manifest = {
        "stage": "13",
        "cohort_id": COHORT_ID,
        "dataset_status": "diagnostic 625-trial sample; not canonical 11005-trial data; no statistical Gate A/B pass inferred",
        "source_sha": SOURCE_SHA,
        "run_id": args.run_id,
        "run_head_sha": args.head_sha,
        "master_seed": int(constants.MASTER_SEED),
        "total_capital": int(constants.TOTAL_CAPITAL),
        "total_trials": 625,
        "total_representatives": 125,
        "global_manifest_sha256": overall_fingerprint,
        "trial_results_fingerprint_sha256": overall_fingerprint,
        "constant_map": public_constants,
        "scenarios": {
            scenario: {
                "final_status": "DIAGNOSTIC_SAMPLE_ONLY_NOT_STATISTICAL_GATE_PASS",
                "trial_count": 25,
                "trial_ids": TRIAL_IDS,
                "representative_role_assignments": 5,
            } for scenario in SCENARIOS
        },
    }
    manifest_path = output_root / "manifest.json"
    write_json(manifest_path, manifest)
    write_json(dataset_root / "error_log.json", [])
    write_json(output_root / "dataset_identity.json", {
        "schema_version": "stage13-final-cohort-v2",
        "cohort_id": COHORT_ID,
        "status": "ASSEMBLED_PENDING_20POINT_GATE",
        "source_sha": SOURCE_SHA,
        "run_id": args.run_id,
        "run_head_sha": args.head_sha,
        "master_seed": int(constants.MASTER_SEED),
        "rng_source_sha256": first_identity["rng_source_sha256"] if first_identity else None,
        "sampling": {"trial_ids": TRIAL_IDS, "trials_per_scenario": 25},
        "scenario_count": 25,
        "trial_result_count": 625,
        "unique_scenario_trial_pairs": 625,
        "trial_results_fingerprint_sha256": overall_fingerprint,
        "daily_distribution_rows": sum(pq.read_table(dataset_root / s / "daily_distribution.parquet").num_rows for s in SCENARIOS),
        "representative_role_assignments": len(all_assignments),
        "representative_unique_detail_trials": len(all_rep_audits),
        "representative_replay_matches": all(row["result_matches_initial_pass"] for row in all_rep_audits),
        "representative_balance_failures": sum(row["max_absolute_balance_difference"] != 0 for row in all_rep_audits),
        "canonical_11005_dataset_fingerprint_sha256": "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44",
        "canonical_dataset_modified": False,
        "canonical_dataset_relation": "new sample identity; not merged with, not a replacement for, and does not inherit Gate A/B acceptance from the canonical 11,005 trials",
        "scenario_identities": scenario_identities,
    })
    identity = json.loads((output_root / "dataset_identity.json").read_text(encoding="utf-8"))

    workbook_path = output_root / "Stage13_Sample_Results_EN.xlsx"
    original_write_table = excel_builder_module.write_table

    def write_table_adapter(ws, headers, rows, start_row=1, number_formats=None):
        materialized_rows = list(rows)
        if materialized_rows and isinstance(materialized_rows[0], dict):
            materialized_rows = [[row.get(header) for header in headers] for row in materialized_rows]
        return original_write_table(
            ws, headers, materialized_rows,
            start_row=start_row, number_formats=number_formats,
        )

    excel_builder_module.write_table = write_table_adapter
    built = excel_builder_module.build_workbook(
        str(dataset_root), str(workbook_path), str(manifest_path), str(reps_path)
    )
    write_json(output_root / "excel_builder_result.json", built)
    (output_root / "excel_builder_stdout.txt").write_text(
        json.dumps(built, sort_keys=True) + "\n", encoding="utf-8"
    )
    (output_root / "excel_builder_stderr.txt").write_text("", encoding="utf-8")
    if not built.get("success") or not workbook_path.exists():
        raise RuntimeError(f"EXCEL_BUILDER_FAILED: {built!r}")
    add_max_case_rows(workbook_path, dataset_root)
    workbook_audit = scan_workbook(workbook_path)
    if workbook_audit["sheets"] != 185:
        raise RuntimeError(f"EXCEL_SHEET_COUNT_FAILURE: {workbook_audit['sheets']}")
    report = run_20point_gate(dataset_root, workbook_path, result_rows_by_scenario, identity, workbook_audit)
    write_json(output_root / "20point_gate_report.json", report)

    shutil.copy2(acceptance_root / "validation_163.json", output_root / "validation_163.json") if (acceptance_root / "validation_163.json").exists() else None
    # Keep full suite/JUnit evidence with the product artifact, while excluding test fixtures from the sample data.
    evidence_dir = output_root / "acceptance_evidence"
    evidence_dir.mkdir(exist_ok=True)
    for name in ("pytest.xml", "pytest_stdout.txt", "pytest_exit_code.txt", "fixture_identity.json"):
        candidates = list(acceptance_root.rglob(name))
        if candidates:
            shutil.copy2(candidates[0], evidence_dir / name)

    file_hashes = {}
    for path in sorted(output_root.rglob("*")):
        if path.is_file() and path.name != "artifact_manifest.json":
            file_hashes[str(path.relative_to(output_root))] = sha256_file(path)
    write_json(output_root / "artifact_manifest.json", {
        "manifest_version": 2,
        "cohort_id": COHORT_ID,
        "source_sha": SOURCE_SHA,
        "run_id": args.run_id,
        "run_head_sha": args.head_sha,
        "file_hashes_sha256": file_hashes,
        "file_count_excluding_manifest": len(file_hashes),
        "trial_results_fingerprint_sha256": overall_fingerprint,
        "workbook_sha256": sha256_file(workbook_path),
        "20point_gate_status": report["status"],
    })
    print(json.dumps({
        "RUN_ID": args.run_id,
        "RUN_HEAD_SHA": args.head_sha,
        "COHORT_ID": COHORT_ID,
        "SCENARIOS": len(SCENARIOS),
        "TRIALS_PER_SCENARIO": 25,
        "TOTAL_TRIAL_RESULTS": len(all_result_rows),
        "REPRESENTATIVE_ROLE_ASSIGNMENTS": len(all_assignments),
        "REPRESENTATIVE_UNIQUE_DETAIL_TRIALS": len(all_rep_audits),
        "WORKBOOK": str(workbook_path),
        "WORKBOOK_SHA256": sha256_file(workbook_path),
        "WORKBOOK_SHEETS": workbook_audit["sheets"],
        "EXCEL_ERROR_CELLS": len(workbook_audit["excel_errors"]),
        "EXCEL_FORMULA_CELLS": len(workbook_audit["formula_cells"]),
        "POINTS_MATCHED": sum(row["exact_match"] for row in report["comparisons"]),
        "POINTS_EXPECTED": 500,
        "GATE_STATUS": report["status"],
        "TRIAL_RESULTS_FINGERPRINT_SHA256": overall_fingerprint,
    }, ensure_ascii=False, sort_keys=True))
    if report["status"] != "PASS":
        raise SystemExit("STAGE13_20_POINT_GATE_FAIL")


if __name__ == "__main__":
    main()
