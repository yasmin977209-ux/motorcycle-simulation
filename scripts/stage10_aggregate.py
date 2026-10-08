from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"


def api(path: str):
    return json.loads(
        subprocess.check_output(
            ["gh", "api", "--header", "X-GitHub-Api-Version: 2022-11-28", path],
            text=True,
        )
    )


def ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def percentile(values: list[float], q: float) -> float | None:
    if not values:
        return None
    a = sorted(values)
    k = (len(a) - 1) * q
    lo = int(k)
    hi = min(lo + 1, len(a) - 1)
    return float(a[lo] if lo == hi else a[lo] + (a[hi] - a[lo]) * (k - lo))


def main() -> int:
    run_id = int(sys.argv[1])
    root = Path("all_artifacts")
    metrics = [
        json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(root.rglob("metrics.json"))
    ]

    jobs = api(
        f"repos/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{run_id}/jobs?per_page=100"
    )["jobs"]
    matrix_jobs = [
        j for j in jobs if str(j.get("name", "")).startswith("bench-")
    ]

    artifacts = api(
        f"repos/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{run_id}/artifacts?per_page=100"
    )["artifacts"]
    chunk_artifacts = [
        a
        for a in artifacts
        if str(a.get("name", "")).startswith("stage10-bench-")
        and a.get("name") != "stage10-bench-final"
    ]

    scenarios = [
        f"C{c:03d}_G{g:03d}"
        for c in (100, 85, 70, 50, 30)
        for g in (100, 70, 50, 30, 0)
    ]

    by_scenario = {
        s: [m for m in metrics if m.get("scenario") == s]
        for s in scenarios
    }

    job_durations: dict[str, float] = {}
    conclusions: dict[str, str | None] = {}
    intervals: list[tuple[datetime, int]] = []

    for job in matrix_jobs:
        conclusions[job["name"]] = job.get("conclusion")
        if job.get("started_at") and job.get("completed_at"):
            started = ts(job["started_at"])
            completed = ts(job["completed_at"])
            duration = (completed - started).total_seconds()
            job_durations[job["name"]] = duration
            intervals.append((started, 1))
            intervals.append((completed, -1))

    active = 0
    observed_max_concurrency = 0
    for _, delta in sorted(intervals, key=lambda x: (x[0], x[1])):
        active += delta
        observed_max_concurrency = max(observed_max_concurrency, active)

    if intervals:
        matrix_wall_seconds = (
            max(t for t, _ in intervals) - min(t for t, _ in intervals)
        ).total_seconds()
    else:
        matrix_wall_seconds = 0.0

    artifact_size_by_name = {
        a["name"]: int(a["size_in_bytes"])
        for a in chunk_artifacts
    }

    scenario_rows: list[dict[str, object]] = []

    for scenario in scenarios:
        rows = by_scenario[scenario]
        durations = [
            float(d)
            for row in rows
            for d in row.get("per_execution_durations_seconds", [])
        ]

        if not rows:
            scenario_rows.append(
                {
                    "scenario": scenario,
                    "mode": "benchmark_only" if scenario.startswith("C100_") else "canonical",
                    "executions": 0,
                    "canonical_trials_added": 0,
                    "mean_trial_seconds": None,
                    "p50_seconds": None,
                    "p95_seconds": None,
                    "p99_seconds": None,
                    "peak_rss_mb": None,
                    "cpu_user_seconds": None,
                    "cpu_system_seconds": None,
                    "output_uncompressed_bytes": None,
                    "artifact_upload_size_bytes": None,
                    "fixed_job_overhead_seconds": None,
                    "baseline_statuses": [],
                }
            )
            continue

        chunk_job_durations = []
        artifact_size = 0
        for row in rows:
            chunk_id = int(row["chunk_id"])
            job_name = f"bench-{scenario}-{chunk_id}"
            if job_name in job_durations:
                chunk_job_durations.append(job_durations[job_name])
            artifact_name = f"stage10-bench-{scenario}-{chunk_id}"
            artifact_size += artifact_size_by_name.get(artifact_name, 0)

        simulation_sum = sum(
            float(row["simulation_wall_time_seconds"]) for row in rows
        )
        chunk_end_sum = sum(
            float(row["chunk_end_to_end_seconds"]) for row in rows
        )
        fixed_overhead = max(
            0.0,
            sum(chunk_job_durations) - chunk_end_sum,
        )

        scenario_rows.append(
            {
                "scenario": scenario,
                "mode": rows[0]["mode"],
                "executions": sum(
                    int(row["executions_completed"]) for row in rows
                ),
                "canonical_trials_added": sum(
                    int(row["canonical_trials_added"]) for row in rows
                ),
                "mean_trial_seconds": float(sum(durations) / len(durations)),
                "p50_seconds": percentile(durations, 0.50),
                "p95_seconds": percentile(durations, 0.95),
                "p99_seconds": percentile(durations, 0.99),
                "peak_rss_mb": max(float(row["peak_rss_mb"]) for row in rows),
                "cpu_user_seconds": sum(
                    float(row["cpu_user_seconds"]) for row in rows
                ),
                "cpu_system_seconds": sum(
                    float(row["cpu_system_seconds"]) for row in rows
                ),
                "simulation_wall_time_seconds": simulation_sum,
                "chunk_end_to_end_seconds": chunk_end_sum,
                "output_uncompressed_bytes": sum(
                    int(row["output_uncompressed_bytes"]) for row in rows
                ),
                "artifact_upload_size_bytes": artifact_size,
                "fixed_job_overhead_seconds": fixed_overhead,
                "baseline_statuses": sorted(
                    {row["baseline_state"]["final_status"] for row in rows}
                ),
            }
        )

    total_executions = sum(int(row["executions"]) for row in scenario_rows)
    canonical_added = sum(
        int(row["canonical_trials_added"]) for row in scenario_rows
    )

    fresh_current_serial = 0.0
    fresh_extended_serial = 0.0
    fresh_current_p95_serial = 0.0
    fresh_extended_p95_serial = 0.0

    for row in scenario_rows:
        mean = row["mean_trial_seconds"]
        p95 = row["p95_seconds"]
        fixed = row["fixed_job_overhead_seconds"]
        if mean is None or fixed is None:
            continue

        current_n = 1 if str(row["scenario"]).startswith("C100_") else 450
        extended_n = current_n + int(row["canonical_trials_added"])

        fresh_current_serial += fixed + current_n * mean
        fresh_extended_serial += fixed + extended_n * mean

        if p95 is not None:
            fresh_current_p95_serial += fixed + current_n * p95
            fresh_extended_p95_serial += fixed + extended_n * p95

    failures = {
        name: conclusion
        for name, conclusion in conclusions.items()
        if conclusion != "success"
    }

    warning_jobs = {
        name: duration
        for name, duration in job_durations.items()
        if duration > 35 * 60
    }

    gates = {
        "matrix_jobs_45": len(matrix_jobs) == 45,
        "scenario_count_25": sum(
            1 for row in scenario_rows if int(row["executions"]) > 0
        ) == 25,
        "execution_count_2500": total_executions == 2500,
        "canonical_added_2000": canonical_added == 2000,
        "execution_failures_zero": all(
            int(row.get("executions_failed", 0)) == 0
            for row in metrics
        ),
        "matrix_jobs_success": len(failures) == 0,
        "chunk_artifacts_45": len(chunk_artifacts) == 45,
        "model_source_drift_absent": all(
            row.get("source_sha") == SOURCE_SHA for row in metrics
        ),
        "resumable_extensions_present": all(
            (
                root
                / f"stage10-bench-{scenario}-1"
                / "resume_descriptor.json"
            ).exists()
            for scenario in scenarios
            if not scenario.startswith("C100_")
        ),
    }

    if all(gates.values()):
        verdict = "PASS"
    elif (
        gates["scenario_count_25"]
        and gates["execution_failures_zero"]
        and not failures
    ):
        verdict = "PARTIAL"
    else:
        verdict = "FAIL"

    report = {
        "schema_version": "stage10-benchmark-v1",
        "measurement_run_id": run_id,
        "matrix_jobs_expected": 45,
        "matrix_jobs_observed": len(matrix_jobs),
        "scenario_results": scenario_rows,
        "totals": {
            "benchmark_executions": total_executions,
            "canonical_trials_added": canonical_added,
            "current_total_trials": 9005,
            "final_total_trials_if_extension_accepted": 9005 + canonical_added,
        },
        "github_topology": {
            "configured_max_parallel": 10,
            "observed_max_concurrency": observed_max_concurrency,
            "matrix_wall_seconds": matrix_wall_seconds,
            "sum_job_wall_seconds": sum(job_durations.values()),
            "max_job_wall_seconds": max(job_durations.values(), default=0.0),
            "warnings_jobs_over_35m": warning_jobs,
            "job_conclusions": conclusions,
        },
        "stage11_estimates": {
            "stage11_topology_status": "NOT_DEFINED_IN_CURRENT_REPOSITORY",
            "fresh_current_dataset_9005_serial_hours": fresh_current_serial / 3600.0,
            "fresh_extended_dataset_11005_serial_hours": fresh_extended_serial / 3600.0,
            "fresh_current_dataset_9005_p95_serial_hours": fresh_current_p95_serial / 3600.0,
            "fresh_extended_dataset_11005_p95_serial_hours": fresh_extended_p95_serial / 3600.0,
            "stage10_observed_matrix_wall_hours": matrix_wall_seconds / 3600.0,
            "stage10_observed_serial_job_hours": sum(job_durations.values()) / 3600.0,
            "conditional_note": (
                "Stage 11 worker topology and final adaptive trial counts "
                "are not defined in the current repository. These values "
                "are workload estimates from the measured scenario times "
                "and measured job overhead only; they are not an invented "
                "Stage 11 execution plan."
            ),
        },
        "gates": gates,
        "failures": failures,
        "verdict": verdict,
        "generated_at": datetime.now().astimezone().isoformat(),
    }

    Path("stage10_final").mkdir(exist_ok=True)
    Path("stage10_final/STAGE10_METRICS.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True)
        + "\\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
