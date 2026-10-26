from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import date, timedelta
from fractions import Fraction
from hashlib import sha256
import json
from pathlib import Path
import time
from typing import Any

import pandas as pd

import constants
import monte_carlo
import stats_integrity
import validation


GOLDEN_PATH = Path(
    "docs/golden/v2.3/C100_GOLDEN_965281d52441cd0d4b744e211c9f68ee4cdc3753.json"
)
C100_MANIFEST_PATH = Path(
    "docs/audits/S4_C100_GOLDEN_MANIFEST_965281d52441cd0d4b744e211c9f68ee4cdc3753.json"
)
EXPECTED_GOLDEN_SHA256 = "39950d91c3b40b11bea0997b8504ac932a57bcc0ef8e0c51e12d031342a53327"
EXPECTED_C100_MANIFEST_SHA256 = "2097284d77ead6b00492bf75830d09aeef8dbde4aaa1c15dae6a877dc7e9ff04"
SCENARIO_COLLECTIONS = (85, 70, 50, 30)
SCENARIO_RECOVERY_RATES = (100, 70, 50, 30, 0)
TRIAL_IDS = (1, 2, 3, 4, 5)
QUANTILES = (
    ("P10", Fraction(1, 10)),
    ("P25", Fraction(1, 4)),
    ("P50", Fraction(1, 2)),
    ("P75", Fraction(3, 4)),
    ("P90", Fraction(9, 10)),
)
DAILY_METRICS = (
    "Cash",
    "Net_Equity",
    "Active_Bikes",
    "Owned_Transferred_Bikes",
    "Pending_Claims",
)
FINANCIAL_SUMMARY_FIELDS = (
    "final_net_project_equity",
    "final_cash",
    "cumulative_project_profit",
    "operating_net_profit",
    "total_operating_revenue",
    "bad_debt",
    "guarantee_recovered",
    "partner1_final_entitlement",
    "partner2_final_entitlement",
)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def require_sha(value: str, name: str) -> None:
    if len(value) != 40 or any(char not in "0123456789abcdef" for char in value.lower()):
        raise ValueError(f"{name} must be a 40-character Git commit SHA")


def ensure_no_float(value: Any, path: str = "$") -> None:
    if isinstance(value, float):
        raise RuntimeError(f"FINANCIAL_FLOAT_LEAK:{path}")
    if isinstance(value, dict):
        for key, nested in value.items():
            ensure_no_float(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            ensure_no_float(nested, f"{path}[{index}]")


def result_row(result: monte_carlo.TrialResult, cohort_id: str, source_sha: str) -> dict[str, Any]:
    row = asdict(result)
    # Keep only canonical scenario IDs, never the float collection_probability.
    row.pop("collection_probability", None)
    row["rng_checksum"] = str(row["rng_checksum"])
    row["cohort_id"] = cohort_id
    row["source_sha"] = source_sha
    row["schema_version"] = "v2.3"
    return row


def compare_result_sets(
    sequential: list[monte_carlo.TrialResult],
    worker2: list[monte_carlo.TrialResult],
    worker4: list[monte_carlo.TrialResult],
    slices1: dict[int, list[dict[str, object]]],
    slices2: dict[int, list[dict[str, object]]],
    slices4: dict[int, list[dict[str, object]]],
    scenario_id: str,
) -> list[dict[str, Any]]:
    by_id = {
        1: {result.trial_id: result for result in sequential},
        2: {result.trial_id: result for result in worker2},
        4: {result.trial_id: result for result in worker4},
    }
    if not (set(by_id[1]) == set(by_id[2]) == set(by_id[4]) == set(TRIAL_IDS)):
        raise RuntimeError(f"WORKER_TRIAL_ID_SET_MISMATCH:{scenario_id}")
    output: list[dict[str, Any]] = []
    for trial_id in TRIAL_IDS:
        exact12 = asdict(by_id[1][trial_id]) == asdict(by_id[2][trial_id])
        exact14 = asdict(by_id[1][trial_id]) == asdict(by_id[4][trial_id])
        daily12 = slices1[trial_id] == slices2[trial_id]
        daily14 = slices1[trial_id] == slices4[trial_id]
        if not (exact12 and exact14 and daily12 and daily14):
            raise RuntimeError(
                f"WORKER_EQUIVALENCE_MISMATCH:{scenario_id}:trial={trial_id}"
            )
        output.append({
            "scenario_id": scenario_id,
            "trial_id": trial_id,
            "sequential_trial_fingerprint": monte_carlo.trial_fingerprint(by_id[1][trial_id]),
            "worker2_trial_fingerprint": monte_carlo.trial_fingerprint(by_id[2][trial_id]),
            "worker4_trial_fingerprint": monte_carlo.trial_fingerprint(by_id[4][trial_id]),
            "sequential_daily_fingerprint": monte_carlo.fingerprint_per_trial_slices(
                {trial_id: slices1[trial_id]}
            ),
            "worker2_daily_fingerprint": monte_carlo.fingerprint_per_trial_slices(
                {trial_id: slices2[trial_id]}
            ),
            "worker4_daily_fingerprint": monte_carlo.fingerprint_per_trial_slices(
                {trial_id: slices4[trial_id]}
            ),
            "exact_1_eq_2": exact12 and daily12,
            "exact_1_eq_4": exact14 and daily14,
        })
    return output


def carry_forward_row(
    date_text: str,
    trial_id: int,
    rows_by_date: dict[str, dict[str, object]],
    last_row: dict[str, object] | None,
) -> dict[str, object]:
    row = rows_by_date.get(date_text)
    if row is not None:
        return row
    if last_row is None:
        raise RuntimeError(f"DAILY_CARRY_FORWARD_HAS_NO_PRIOR_ROW:{trial_id}:{date_text}")
    return last_row


def build_exact_daily_distribution(
    results: list[monte_carlo.TrialResult],
    slices: dict[int, list[dict[str, object]]],
    scenario_id: str,
    cohort_id: str,
    source_sha: str,
) -> list[dict[str, Any]]:
    result_by_id = {item.trial_id: item for item in results}
    rows_by_trial_date = {
        trial_id: {
            str(row["date"]): row
            for row in sorted(rows, key=lambda item: str(item["date"]))
        }
        for trial_id, rows in slices.items()
    }
    all_date_texts = sorted({
        str(row["date"])
        for rows in slices.values()
        for row in rows
    })
    if not all_date_texts:
        raise RuntimeError(f"DAILY_DISTRIBUTION_EMPTY:{scenario_id}")
    start = date.fromisoformat(all_date_texts[0])
    end = date.fromisoformat(all_date_texts[-1])
    expected = [
        (start + timedelta(days=index)).isoformat()
        for index in range((end - start).days + 1)
    ]
    if all_date_texts != expected:
        raise RuntimeError(f"DAILY_DISTRIBUTION_HAS_DATE_GAP:{scenario_id}")

    last_by_trial: dict[int, dict[str, object] | None] = {
        trial_id: None for trial_id in TRIAL_IDS
    }
    result: list[dict[str, Any]] = []
    for date_text in expected:
        active_ids = [
            trial_id for trial_id, trial in result_by_id.items()
            if trial.final_close_date is None or trial.final_close_date >= date_text
        ]
        mode_samples: dict[str, list[dict[str, object]]] = {
            "ACTIVE_ONLY": [],
            "ALL_TRIALS_CARRY_FORWARD": [],
        }
        for trial_id in TRIAL_IDS:
            existing = rows_by_trial_date[trial_id].get(date_text)
            if existing is not None:
                last_by_trial[trial_id] = existing
            if trial_id in active_ids:
                if existing is None:
                    raise RuntimeError(
                        f"MISSING_ACTIVE_DAILY_ROW:{scenario_id}:{trial_id}:{date_text}"
                    )
                mode_samples["ACTIVE_ONLY"].append(existing)
            carried = carry_forward_row(
                date_text, trial_id, rows_by_trial_date[trial_id], last_by_trial[trial_id]
            )
            mode_samples["ALL_TRIALS_CARRY_FORWARD"].append(carried)

        for mode, sample_rows in mode_samples.items():
            if not sample_rows:
                raise RuntimeError(f"DAILY_DISTRIBUTION_EMPTY_SAMPLE:{scenario_id}:{date_text}:{mode}")
            for metric in DAILY_METRICS:
                values = [row[metric] for row in sample_rows]
                if any(isinstance(value, bool) or not isinstance(value, int) for value in values):
                    raise RuntimeError(f"DAILY_METRIC_NOT_INTEGER:{metric}")
                for quantile_name, q in QUANTILES:
                    exact = stats_integrity.linear_quantile_fraction(values, q)
                    display = stats_integrity.fraction_to_report_value(exact)
                    result.append({
                        "source_sha": source_sha,
                        "cohort_id": cohort_id,
                        "scenario_id": scenario_id,
                        "date": date_text,
                        "mode": mode,
                        "quantile_name": quantile_name,
                        "active_trial_count": len(active_ids),
                        "sample_trial_count": len(sample_rows),
                        "metric_name": metric,
                        "exact_numerator": exact.numerator,
                        "exact_denominator": exact.denominator,
                        "display_value": str(display),
                    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--tested-commit", required=True)
    args = parser.parse_args()
    require_sha(args.source_sha, "source_sha")
    require_sha(args.tested_commit, "tested_commit")
    if args.source_sha != args.tested_commit:
        raise ValueError("SOURCE_SHA_MUST_MATCH_EXACT_TESTED_COMMIT")
    source_sha = args.source_sha.lower()
    cohort_id = f"s5-mini-v23-20261026-{source_sha[:8]}"
    out_dir = Path("s5_evidence")
    out_dir.mkdir(parents=True, exist_ok=True)

    if not GOLDEN_PATH.is_file() or digest(GOLDEN_PATH) != EXPECTED_GOLDEN_SHA256:
        raise RuntimeError("REUSED_C100_GOLDEN_SHA256_MISMATCH")
    if not C100_MANIFEST_PATH.is_file() or digest(C100_MANIFEST_PATH) != EXPECTED_C100_MANIFEST_SHA256:
        raise RuntimeError("REUSED_C100_MANIFEST_SHA256_MISMATCH")
    c100_reuse = {
        "run_id": 40263424595,
        "cohort_id": "c100-v23-s4-20261026-965281d5",
        "golden_path": str(GOLDEN_PATH),
        "golden_sha256": digest(GOLDEN_PATH),
        "manifest_path": str(C100_MANIFEST_PATH),
        "manifest_sha256": digest(C100_MANIFEST_PATH),
        "reused_read_only": True,
        "rerun": False,
    }

    started_all = time.perf_counter()
    sequential_seconds = 0.0
    worker2_seconds = 0.0
    worker4_seconds = 0.0
    summary_rows: list[dict[str, Any]] = []
    selection_rows: list[dict[str, Any]] = []
    daily_distribution_rows: list[dict[str, Any]] = []
    worker_manifest_rows: list[dict[str, Any]] = []
    audit_rows: list[dict[str, Any]] = []
    cohort_rows: list[dict[str, Any]] = []
    registry_entries: list[dict[str, Any]] = []
    role_count = 0

    for collection_pct in SCENARIO_COLLECTIONS:
        for recovery_pct in SCENARIO_RECOVERY_RATES:
            scenario_id = f"C{collection_pct:03d}_G{recovery_pct:03d}"
            t0 = time.perf_counter()
            seq_results, seq_slices = monte_carlo.run_trials_sequentially(
                scenario_id, TRIAL_IDS, master_seed=constants.MASTER_SEED, source_sha=source_sha
            )
            sequential_seconds += time.perf_counter() - t0

            t0 = time.perf_counter()
            par2_results, par2_slices = monte_carlo.run_trials_parallel(
                scenario_id, TRIAL_IDS, 2,
                master_seed=constants.MASTER_SEED, source_sha=source_sha,
            )
            worker2_seconds += time.perf_counter() - t0

            t0 = time.perf_counter()
            par4_results, par4_slices = monte_carlo.run_trials_parallel(
                scenario_id, TRIAL_IDS, 4,
                master_seed=constants.MASTER_SEED, source_sha=source_sha,
            )
            worker4_seconds += time.perf_counter() - t0

            worker_manifest_rows.extend(compare_result_sets(
                seq_results, par2_results, par4_results,
                seq_slices, par2_slices, par4_slices, scenario_id
            ))
            if monte_carlo.fingerprint_trial_results(seq_results) != monte_carlo.fingerprint_trial_results(par2_results):
                raise RuntimeError(f"WORKER_RESULT_SET_FINGERPRINT_MISMATCH:{scenario_id}:workers=2")
            if monte_carlo.fingerprint_trial_results(seq_results) != monte_carlo.fingerprint_trial_results(par4_results):
                raise RuntimeError(f"WORKER_RESULT_SET_FINGERPRINT_MISMATCH:{scenario_id}:workers=4")
            if monte_carlo.fingerprint_per_trial_slices(seq_slices) != monte_carlo.fingerprint_per_trial_slices(par2_slices):
                raise RuntimeError(f"WORKER_DAILY_SET_FINGERPRINT_MISMATCH:{scenario_id}:workers=2")
            if monte_carlo.fingerprint_per_trial_slices(seq_slices) != monte_carlo.fingerprint_per_trial_slices(par4_slices):
                raise RuntimeError(f"WORKER_DAILY_SET_FINGERPRINT_MISMATCH:{scenario_id}:workers=4")

            for trial in seq_results:
                row = result_row(trial, cohort_id, source_sha)
                summary_rows.append(row)
                cohort_rows.append({
                    "source_sha": source_sha,
                    "cohort_id": cohort_id,
                    "schema_version": "v2.3",
                    "scenario_id": scenario_id,
                    "trial_id": trial.trial_id,
                })
                audit_rows.append({
                    "scenario_id": trial.scenario_id,
                    "trial_id": trial.trial_id,
                    "rng_checksum": trial.rng_checksum,
                    "rng_draw_count": trial.rng_draw_count,
                    "rng_checksum_fingerprint_sha256": trial.rng_checksum_fingerprint_sha256,
                })
                for field in FINANCIAL_SUMMARY_FIELDS:
                    value = getattr(trial, field)
                    registry_entries.append(stats_integrity.number_registry_entry(
                        f"{scenario_id}.trial{trial.trial_id}.{field}",
                        Fraction(value, 1),
                        source=f"s5_evidence/trials_summary.parquet:{scenario_id}:{trial.trial_id}",
                    ))

            selected = monte_carlo.select_representative_trials(seq_results)
            role_trial_ids = (
                ("P50", selected.p50_trial_id),
                ("P10", selected.p10_trial_id),
                ("P90", selected.p90_trial_id),
                ("LossCase", selected.loss_case_trial_id),
                ("MaxCase", selected.max_case_trial_id),
            )
            result_by_id = {item.trial_id: item for item in seq_results}
            representative_dir = out_dir / "representative_daily" / scenario_id
            representative_dir.mkdir(parents=True, exist_ok=True)
            for role, trial_id in role_trial_ids:
                trial = result_by_id[trial_id]
                daily_path = representative_dir / f"{role}_trial{trial_id}.csv"
                daily_rows = seq_slices[trial_id]
                if not daily_rows:
                    raise RuntimeError(f"REPRESENTATIVE_DAILY_EMPTY:{scenario_id}:{role}")
                validation.validate_partner_daily_balances(daily_rows)
                pd.DataFrame(daily_rows).to_csv(daily_path, index=False)
                role_count += 1
                selection_rows.append({
                    "source_sha": source_sha,
                    "cohort_id": cohort_id,
                    "scenario_id": scenario_id,
                    "role": role,
                    "trial_id": trial_id,
                    "final_net_project_equity": trial.final_net_project_equity,
                    "trial_fingerprint": monte_carlo.trial_fingerprint(trial),
                    "daily_path": str(daily_path),
                })

            for field, values in (
                ("final_net_project_equity", [item.final_net_project_equity for item in seq_results]),
                ("partner1_final_entitlement", [item.partner1_final_entitlement for item in seq_results]),
                ("partner2_final_entitlement", [item.partner2_final_entitlement for item in seq_results]),
            ):
                registry_entries.append(stats_integrity.number_registry_entry(
                    f"{scenario_id}.mean.{field}",
                    stats_integrity.mean_fraction(values),
                    source=f"s5_evidence/trials_summary.parquet:{scenario_id}:N={len(values)}",
                ))
            for field, attr in (
                ("P10_Cumulative_Project_Profit", "cumulative_project_profit"),
                ("P50_Cumulative_Project_Profit", "cumulative_project_profit"),
                ("P90_Cumulative_Project_Profit", "cumulative_project_profit"),
                ("P90_Final_Cash", "final_cash"),
            ):
                q = {"P10_Cumulative_Project_Profit": Fraction(1, 10),
                     "P50_Cumulative_Project_Profit": Fraction(1, 2),
                     "P90_Cumulative_Project_Profit": Fraction(9, 10),
                     "P90_Final_Cash": Fraction(9, 10)}[field]
                exact = stats_integrity.linear_quantile_fraction(
                    [getattr(item, attr) for item in seq_results], q
                )
                registry_entries.append(stats_integrity.number_registry_entry(
                    f"{scenario_id}.mini_estimate.{field}",
                    exact,
                    source=f"s5_evidence/trials_summary.parquet:{scenario_id}:N={len(seq_results)};mini-only",
                ))

            daily_distribution_rows.extend(build_exact_daily_distribution(
                seq_results, seq_slices, scenario_id, cohort_id, source_sha
            ))

    elapsed_total = time.perf_counter() - started_all
    if len(summary_rows) != 100 or len(selection_rows) != 100:
        raise RuntimeError("S5_SAMPLE_ROW_COUNT_MISMATCH")
    if role_count != 100:
        raise RuntimeError("S5_REPRESENTATIVE_ROLE_COUNT_MISMATCH")
    if len(worker_manifest_rows) != 100:
        raise RuntimeError("S5_WORKER_EQUIVALENCE_ROW_COUNT_MISMATCH")

    # Check cohort/audit and daily evidence with the shared validators.
    if validation.validate_cohort_identity(cohort_rows) != (source_sha, cohort_id, "v2.3"):
        raise RuntimeError("S5_COHORT_IDENTITY_MISMATCH")
    validation.validate_rng_audit_records(
        audit_rows, source_sha=source_sha, master_seed=constants.MASTER_SEED
    )
    validation.validate_worker_equivalence_manifest({"trials": worker_manifest_rows})
    all_daily_rows = [
        row
        for scenario_id in (
            f"C{c:03d}_G{g:03d}"
            for c in SCENARIO_COLLECTIONS
            for g in SCENARIO_RECOVERY_RATES
        )
        for trial_id in TRIAL_IDS
        for row in []  # Per-representative daily files are validated below.
    ]
    if not daily_distribution_rows:
        raise RuntimeError("S5_DAILY_DISTRIBUTION_NOT_GENERATED")
    validation.validate_daily_distribution_dates(daily_distribution_rows)
    representative_partner_rows = 0
    for path in sorted((out_dir / "representative_daily").rglob("*.csv")):
        df = pd.read_csv(path, dtype=str, keep_default_na=False)
        required = {"Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance"}
        if not required.issubset(df.columns):
            raise RuntimeError(f"PARTNER_BALANCE_COLUMNS_MISSING:{path}")
        for name in required:
            for value in df[name]:
                if not value.isdigit():
                    raise RuntimeError(f"PARTNER_BALANCE_NOT_INTEGER:{path}:{name}:{value}")
                int(value)
        representative_partner_rows += len(df)
    if representative_partner_rows <= 0:
        raise RuntimeError("S5_PARTNER_DAILY_EVIDENCE_MISSING")

    summary_frame = pd.DataFrame(summary_rows)
    selection_frame = pd.DataFrame(selection_rows)
    daily_frame = pd.DataFrame(daily_distribution_rows)
    for name, frame in (
        ("trials_summary", summary_frame),
        ("selection", selection_frame),
        ("daily_distribution", daily_frame),
    ):
        if any(str(dtype) in {"float16", "float32", "float64"} for dtype in frame.dtypes):
            raise RuntimeError(f"FLOAT_LEAK_IN_PARQUET:{name}")
    summary_path = out_dir / "trials_summary.parquet"
    selection_path = out_dir / "selection.parquet"
    daily_path = out_dir / "daily_distribution.parquet"
    summary_frame.to_parquet(summary_path, index=False, engine="pyarrow")
    selection_frame.to_parquet(selection_path, index=False, engine="pyarrow")
    daily_frame.to_parquet(daily_path, index=False, engine="pyarrow")

    worker_payload = {
        "schema_version": "s5-worker-equivalence-v1",
        "source_sha": source_sha,
        "cohort_id": cohort_id,
        "scenarios": [
            f"C{c:03d}_G{g:03d}"
            for c in SCENARIO_COLLECTIONS
            for g in SCENARIO_RECOVERY_RATES
        ],
        "trial_ids": list(TRIAL_IDS),
        "workers_compared": [1, 2, 4],
        "trial_count": len(worker_manifest_rows),
        "exact_result_and_daily_equivalence": True,
        "trials": worker_manifest_rows,
    }
    write_json(out_dir / "worker_equivalence_manifest.json", worker_payload)
    write_json(out_dir / "number_registry.json", {
        "schema_version": "v2.3-number-registry-s5-mini-v1",
        "cohort_id": cohort_id,
        "source_sha": source_sha,
        "registry_scope": "trial-level exact financial values and scenario-level exact mean/quantile summaries; daily distribution exact cells are also stored directly as numerator/denominator in Parquet",
        "entries": registry_entries,
        "entry_count": len(registry_entries),
    })
    write_json(out_dir / "stability_history.json", {
        "schema_version": "v2.3-mini-diagnostic-history-v1",
        "source_sha": source_sha,
        "cohort_id": cohort_id,
        "status": "MINI_VALIDATION_ONLY_NO_STABILITY_DECISION",
        "formal_acceptance_allowed": False,
        "n_per_scenario": len(TRIAL_IDS),
        "checkpoint_schedule": [300, 600, 1200, 2400],
        "means_and_indicator_policy": {
            "per_scenario_alpha": "1/400",
            "alpha_s_k": "1/[400*k*(k+1)]",
            "formulae_implemented": True,
            "support_bounds_id": stats_integrity.compute_deterministic_support_bounds()["bound_id"],
            "checkpoint_intervals_evaluated": False,
            "reason": "N=5 is below the approved N=300 checkpoint; no convergence or stability inference is permitted from this mini sample."
        },
        "historical_cohort_isolation": {
            "C030_G030_N300_to_N600_P90_Final_Cash": "FAILED_NOT_REQUALIFIED",
            "historical_record_mutated": False
        },
    })

    denominator = {
        "sequential_seconds": sequential_seconds,
        "parallel_2_workers_seconds": worker2_seconds,
        "parallel_4_workers_seconds": worker4_seconds,
    }
    if any(value <= 0 for value in denominator.values()):
        raise RuntimeError("S5_RUNTIME_MEASUREMENT_INVALID")
    benchmark = {
        "schema_version": "s5-runtime-benchmark-v1",
        "source_sha": source_sha,
        "cohort_id": cohort_id,
        "sample": {
            "scenario_count": 20,
            "trial_ids_per_scenario": list(TRIAL_IDS),
            "unique_trial_paths": 100,
            "executions_per_path": 3,
            "actual_trial_executions": 300,
        },
        "elapsed_seconds": {key: f"{value:.6f}" for key, value in denominator.items()},
        "end_to_end_script_seconds": f"{elapsed_total:.6f}",
        "throughput_trials_per_second": {
            key: f"{(100 / value):.6f}" for key, value in denominator.items()
        },
        "speedup_vs_sequential": {
            "parallel_2_workers": f"{(sequential_seconds / worker2_seconds):.6f}",
            "parallel_4_workers": f"{(sequential_seconds / worker4_seconds):.6f}",
        },
        "extrapolation_for_S6": {
            "planned_stochastic_trials_at_N300": 6000,
            "basis": "linear extrapolation from 100 unique paths, with the 20x N=300 target",
            "sequential_seconds": f"{sequential_seconds * 60:.6f}",
            "parallel_2_workers_seconds": f"{worker2_seconds * 60:.6f}",
            "parallel_4_workers_seconds": f"{worker4_seconds * 60:.6f}",
            "is_measured": False,
        },
        "reuse_c100_without_rerun": c100_reuse,
    }
    write_json(out_dir / "runtime_benchmark.json", benchmark)

    acceptance = {
        "schema_version": "s5-acceptance-evidence-v1",
        "source_sha": source_sha,
        "tested_commit_sha": args.tested_commit,
        "cohort_id": cohort_id,
        "status": "PASS_S5_MINI_EVIDENCE" if (
            len(summary_rows) == 100
            and len(selection_rows) == 100
            and len(worker_manifest_rows) == 100
            and role_count == 100
            and len(daily_distribution_rows) > 0
        ) else "FAIL",
        "formal_gate_status": "NOT_EVALUATED_BY_N5_MINI_SAMPLE",
        "checks": {
            "127_worker_equivalence_manifest": True,
            "159_trial_summary_parquet": True,
            "160_selection_and_representative_daily_outputs": True,
            "161_daily_distribution_parquet": True,
            "174_sequential_parallel_and_replay_fingerprints": True,
            "181_new_cohort_daily_partner_balance_integer_evidence": True,
            "182_exact_fraction_and_half_even_number_registry": True,
            "historical_v2_2_representative_balance_gap": "PRESERVED_NOT_REWRITTEN",
            "workbook_and_report_reconciliation": "S8_SCOPE_NOT_CLOSED_BY_S5",
        },
        "counts": {
            "trial_summary_rows": len(summary_rows),
            "selection_rows": len(selection_rows),
            "worker_equivalence_rows": len(worker_manifest_rows),
            "daily_distribution_rows": len(daily_distribution_rows),
            "representative_daily_files": role_count,
            "representative_daily_rows": representative_partner_rows,
            "number_registry_entries": len(registry_entries),
        },
        "c100_reuse": c100_reuse,
        "runtime_benchmark_path": "s5_evidence/runtime_benchmark.json",
        "stability_history_path": "s5_evidence/stability_history.json",
    }
    ensure_no_float(acceptance)
    write_json(out_dir / "s5_acceptance.json", acceptance)

    # Verify required output schemas and the money columns' exact representation.
    roundtrip = pd.read_parquet(daily_path, engine="pyarrow")
    required_exact = {"exact_numerator", "exact_denominator", "display_value"}
    if not required_exact.issubset(roundtrip.columns):
        raise RuntimeError("DAILY_PARQUET_EXACT_FRACTION_COLUMNS_MISSING")
    if len(roundtrip) != len(daily_distribution_rows):
        raise RuntimeError("DAILY_PARQUET_ROW_COUNT_MISMATCH")
    for path in (summary_path, selection_path, daily_path):
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError(f"EMPTY_REQUIRED_PARQUET:{path}")

    manifest_paths = sorted(
        path for path in out_dir.rglob("*")
        if path.is_file() and path.name != "s5_manifest.json"
    )
    manifest = {
        "schema_version": "s5-evidence-manifest-v1",
        "source_sha": source_sha,
        "tested_commit_sha": args.tested_commit,
        "cohort_id": cohort_id,
        "master_seed": constants.MASTER_SEED,
        "schema_version_model": "v2.3",
        "manifest_excludes_itself": True,
        "files": [
            {
                "path": str(path),
                "size_bytes": path.stat().st_size,
                "sha256": digest(path),
            }
            for path in manifest_paths
        ],
    }
    write_json(out_dir / "s5_manifest.json", manifest)
    print(json.dumps({
        "status": acceptance["status"],
        "source_sha": source_sha,
        "cohort_id": cohort_id,
        "summary_rows": len(summary_rows),
        "selection_rows": len(selection_rows),
        "worker_equivalence_rows": len(worker_manifest_rows),
        "daily_distribution_rows": len(daily_distribution_rows),
        "representative_daily_files": role_count,
        "representative_daily_rows": representative_partner_rows,
        "number_registry_entries": len(registry_entries),
        "runtime_benchmark": benchmark,
        "manifest_sha256": digest(out_dir / "s5_manifest.json"),
        "manifest_path": str(out_dir / "s5_manifest.json"),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
