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


def load_trial_range(trial_id_start: int, trial_id_end: int) -> range:
    if trial_id_start < 1:
        raise ValueError("trial_id_start must be >= 1")
    if trial_id_end < trial_id_start:
        raise ValueError("trial_id_end must be >= trial_id_start")
    return range(trial_id_start, trial_id_end + 1)


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")


def _trial_result_sha256(result: monte_carlo.TrialResult) -> str:
    return hashlib.sha256(_canonical_json(asdict(result))).hexdigest()


def run_block(
    *,
    scenario_id: str,
    trial_id_start: int,
    trial_id_end: int,
    master_seed: int,
    log_events: bool,
) -> list[monte_carlo.TrialResult]:
    collection_probability, recovery_rate_pct = monte_carlo.parse_scenario_id(
        scenario_id
    )

    results: list[monte_carlo.TrialResult] = []
    for trial_id in load_trial_range(trial_id_start, trial_id_end):
        project = daily_engine.run_deterministic_trial(
            recovery_rate_pct=recovery_rate_pct,
            trial_id=trial_id,
            scenario_id=scenario_id,
            master_seed=master_seed,
            collection_probability=collection_probability,
            log_events=log_events,
        )
        results.append(
            monte_carlo._trial_result_from_project(
                project,
                scenario_id=scenario_id,
                collection_probability=collection_probability,
                recovery_rate_pct=recovery_rate_pct,
                trial_id=trial_id,
            )
        )
    return results


def fingerprint_block(results: list[monte_carlo.TrialResult]) -> str:
    return monte_carlo.fingerprint_trial_results(results)


def write_block_artifact(
    *,
    results: list[monte_carlo.TrialResult],
    scenario_id: str,
    trial_id_start: int,
    trial_id_end: int,
    output_dir: str,
    source_sha: str,
    run_id: str | None,
    elapsed_seconds: float,
    max_rss_kb: int,
    log_events: bool,
) -> tuple[Path, Path]:
    block_dir = Path(output_dir) / scenario_id / "blocks"
    block_dir.mkdir(parents=True, exist_ok=True)

    parquet_path = block_dir / f"block_{trial_id_start}_{trial_id_end}.parquet"
    metadata_path = block_dir / f"block_{trial_id_start}_{trial_id_end}_metadata.json"

    pq.write_table(
        pa.Table.from_pylist([asdict(result) for result in results]),
        parquet_path,
    )

    metadata = {
        "scenario": scenario_id,
        "trial_id_start": trial_id_start,
        "trial_id_end": trial_id_end,
        "trial_count": len(results),
        "elapsed_seconds": elapsed_seconds,
        "max_rss_kb": max_rss_kb,
        "cpu_count": os.cpu_count(),
        "fingerprint_sha256": fingerprint_block(results),
        "per_trial_sha256": [_trial_result_sha256(result) for result in results],
        "log_events": log_events,
        "source_sha": source_sha,
        "run_id": run_id,
    }

    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return parquet_path, metadata_path


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run one deterministic Stage 7 trial block."
    )
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--trial-id-start", type=int, required=True)
    parser.add_argument("--trial-id-end", type=int, required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID"))
    parser.add_argument("--log-events", action="store_true", default=False)
    parser.add_argument("--output-dir", default="results_stage7")
    parser.add_argument("--master-seed", type=int, default=constants.MASTER_SEED)
    args = parser.parse_args()

    started = time.monotonic()
    results = run_block(
        scenario_id=args.scenario,
        trial_id_start=args.trial_id_start,
        trial_id_end=args.trial_id_end,
        master_seed=args.master_seed,
        log_events=args.log_events,
    )
    elapsed_seconds = time.monotonic() - started
    max_rss_kb = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

    parquet_path, metadata_path = write_block_artifact(
        results=results,
        scenario_id=args.scenario,
        trial_id_start=args.trial_id_start,
        trial_id_end=args.trial_id_end,
        output_dir=args.output_dir,
        source_sha=args.source_sha,
        run_id=args.run_id,
        elapsed_seconds=elapsed_seconds,
        max_rss_kb=max_rss_kb,
        log_events=args.log_events,
    )

    print(
        json.dumps(
            {
                "scenario": args.scenario,
                "trial_id_start": args.trial_id_start,
                "trial_id_end": args.trial_id_end,
                "trial_count": len(results),
                "elapsed_seconds": elapsed_seconds,
                "max_rss_kb": max_rss_kb,
                "source_sha": args.source_sha,
                "run_id": args.run_id,
                "fingerprint_sha256": fingerprint_block(results),
                "parquet": str(parquet_path),
                "metadata": str(metadata_path),
                "log_events": args.log_events,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
