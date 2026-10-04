from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

import monte_carlo


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--chunks-dir",
        type=Path,
        default=Path("results_stage6_5/artifacts"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("results_stage6_5"),
    )
    parser.add_argument(
        "--max-parallel",
        type=int,
        default=16,
    )
    return parser.parse_args()


def _load_results(
    chunks_dir: Path,
) -> tuple[list[monte_carlo.TrialResult], list[float]]:
    metadata_paths = sorted(chunks_dir.rglob("chunk_metadata.json"))
    parquet_paths = sorted(chunks_dir.rglob("trials_summary.parquet"))

    if not metadata_paths:
        raise FileNotFoundError(
            f"no chunk_metadata.json found under {chunks_dir}"
        )
    if not parquet_paths:
        raise FileNotFoundError(
            f"no trials_summary.parquet found under {chunks_dir}"
        )

    elapsed_seconds: list[float] = []
    for metadata_path in metadata_paths:
        metadata = json.loads(
            metadata_path.read_text(encoding="utf-8")
        )
        elapsed_seconds.append(
            float(metadata["elapsed_seconds_total"])
        )

    results: list[monte_carlo.TrialResult] = []
    for parquet_path in parquet_paths:
        rows = pq.read_table(parquet_path).to_pylist()
        results.extend(
            monte_carlo.TrialResult(**row)
            for row in rows
        )

    results.sort(key=lambda result: result.trial_id)

    expected_trial_ids = list(range(1, 6001))
    actual_trial_ids = [result.trial_id for result in results]
    if actual_trial_ids != expected_trial_ids:
        raise AssertionError(
            "aggregate TrialResult trial_ids must be exactly 1..6000"
        )

    return results, elapsed_seconds


def _statistics(
    results: list[monte_carlo.TrialResult],
) -> dict[str, float | int]:
    equities = np.asarray(
        [
            result.final_net_project_equity
            for result in results
        ],
        dtype=np.float64,
    )
    losses = np.asarray(
        [
            result.cumulative_project_profit < 0
            for result in results
        ],
        dtype=np.float64,
    )

    return {
        "P10": float(
            np.quantile(equities, 0.10, method="linear")
        ),
        "P50": float(
            np.quantile(equities, 0.50, method="linear")
        ),
        "P90": float(
            np.quantile(equities, 0.90, method="linear")
        ),
        "Mean": float(np.mean(equities)),
        "Std": float(np.std(equities)),
        "Min": int(np.min(equities)),
        "Max": int(np.max(equities)),
        "Probability_of_Accounting_Loss": float(
            np.mean(losses)
        ),
    }


def main() -> None:
    args = parse_args()

    if args.max_parallel < 1:
        raise ValueError("max_parallel must be >= 1")

    results, elapsed_seconds = _load_results(
        args.chunks_dir
    )

    aggregate_sha256 = (
        monte_carlo.fingerprint_trial_results(results)
    )

    max_chunk_elapsed = max(elapsed_seconds)
    wave_count = (
        len(elapsed_seconds) + args.max_parallel - 1
    ) // args.max_parallel
    wall_clock_estimate = (
        wave_count * max_chunk_elapsed
    )

    payload = {
        "total_trials": len(results),
        "aggregate_sha256": aggregate_sha256,
        "max_parallel": args.max_parallel,
        "max_chunk_elapsed": max_chunk_elapsed,
        "wall_clock_estimate": wall_clock_estimate,
        "statistics": _statistics(results),
    }

    args.output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    pq.write_table(
        pa.Table.from_pylist(
            [
                asdict(result)
                for result in results
            ]
        ),
        args.output_dir
        / "trials_summary_6000.parquet",
    )

    (
        args.output_dir / "aggregate_summary.json"
    ).write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
