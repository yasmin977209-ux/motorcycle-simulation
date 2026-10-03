from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import time
from dataclasses import asdict
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

import constants
import daily_engine
import monte_carlo


def _parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise argparse.ArgumentTypeError(
        f"expected True or False, got {value!r}"
    )


def _result_sha256(result: monte_carlo.TrialResult) -> str:
    payload = json.dumps(
        asdict(result),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--chunk-id", required=True, type=int)
    parser.add_argument("--chunk-size", required=True, type=int)
    parser.add_argument("--log-events", required=True, type=_parse_bool)
    parser.add_argument("--baseline-compare", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.chunk_id < 0:
        raise ValueError("chunk_id must be >= 0")
    if args.chunk_size < 1:
        raise ValueError("chunk_size must be >= 1")
    if args.baseline_compare is not None and args.baseline_compare < 1:
        raise ValueError("baseline_compare must be >= 1")

    collection_probability, recovery_rate_pct = (
        monte_carlo.parse_scenario_id(args.scenario)
    )

    trial_id_start = args.chunk_id * args.chunk_size + 1
    trial_id_end = (args.chunk_id + 1) * args.chunk_size

    started = time.perf_counter()
    results: list[monte_carlo.TrialResult] = []
    per_trial_sha256: list[str] = []

    for trial_id in range(trial_id_start, trial_id_end + 1):
        project = daily_engine.run_deterministic_trial(
            recovery_rate_pct=recovery_rate_pct,
            trial_id=trial_id,
            scenario_id=args.scenario,
            master_seed=constants.MASTER_SEED,
            collection_probability=collection_probability,
            log_events=args.log_events,
        )

        result = monte_carlo._trial_result_from_project(
            project,
            scenario_id=args.scenario,
            collection_probability=collection_probability,
            recovery_rate_pct=recovery_rate_pct,
            trial_id=trial_id,
        )
        results.append(result)
        per_trial_sha256.append(_result_sha256(result))

    elapsed_seconds_total = time.perf_counter() - started
    rss_max_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    aggregate_sha256 = monte_carlo.fingerprint_trial_results(results)

    baseline_result = None
    if args.baseline_compare is not None:
        baseline_count = min(args.baseline_compare, len(results))
        baseline_start = trial_id_end - baseline_count + 1
        baseline_results = []

        for trial_id in range(baseline_start, trial_id_end + 1):
            project = daily_engine.run_deterministic_trial(
                recovery_rate_pct=recovery_rate_pct,
                trial_id=trial_id,
                scenario_id=args.scenario,
                master_seed=constants.MASTER_SEED,
                collection_probability=collection_probability,
                log_events=args.log_events,
            )
            baseline_results.append(
                monte_carlo._trial_result_from_project(
                    project,
                    scenario_id=args.scenario,
                    collection_probability=collection_probability,
                    recovery_rate_pct=recovery_rate_pct,
                    trial_id=trial_id,
                )
            )

        baseline_by_id = {
            result.trial_id: result
            for result in baseline_results
        }
        matrix_by_id = {
            result.trial_id: result
            for result in results
        }
        per_trial_match = {
            str(trial_id): (
                asdict(matrix_by_id[trial_id])
                == asdict(baseline_by_id[trial_id])
            )
            for trial_id in baseline_by_id
        }

        baseline_sha256 = monte_carlo.fingerprint_trial_results(
            baseline_results
        )
        baseline_result = {
            "trial_count": baseline_count,
            "trial_id_start": baseline_start,
            "trial_id_end": trial_id_end,
            "sha256": baseline_sha256,
            "all_trial_results_match": all(
                per_trial_match.values()
            ),
            "per_trial_match": per_trial_match,
        }

        if not baseline_result["all_trial_results_match"]:
            raise AssertionError(
                "baseline comparison found TrialResult mismatch"
            )

    output_dir = (
        Path("results_stage6_5")
        / f"chunk_{args.chunk_id}"
    )
    output_dir.mkdir(parents=True, exist_ok=True)

    pq.write_table(
        pa.Table.from_pylist(
            [asdict(result) for result in results]
        ),
        output_dir / "trials_summary.parquet",
    )

    metadata = {
        "chunk_id": args.chunk_id,
        "trial_id_start": trial_id_start,
        "trial_id_end": trial_id_end,
        "trials_count": len(results),
        "elapsed_seconds_total": elapsed_seconds_total,
        "cpu_count": os.cpu_count(),
        "sha256_concatenated_results": aggregate_sha256,
        "rss_max_kb": rss_max_kb,
        "log_events_value": args.log_events,
        "per_trial_sha256": per_trial_sha256,
        "baseline_compare": baseline_result,
    }

    (output_dir / "chunk_metadata.json").write_text(
        json.dumps(
            metadata,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            metadata,
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
