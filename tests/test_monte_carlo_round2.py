from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import monte_carlo


SCENARIO_ID = "C070_G100"
TRIAL_IDS = (1, 2, 3)
WORKER_COUNTS = (2, 4)
PYTHON_HASH_SEEDS = (1, 42, 987654)


def _distribution_probe(
    daily_rows_by_trial: dict[int, list[dict[str, object]]],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for trial_id in sorted(daily_rows_by_trial):
        for row in daily_rows_by_trial[trial_id]:
            rows.append(
                {
                    **row,
                    "quantile_name": f"TRIAL_{trial_id}",
                }
            )
    return rows


def _fingerprints(
    results: list[monte_carlo.TrialResult],
    slices: dict[int, list[dict[str, object]]],
) -> dict[str, str]:
    return {
        "trial_results": monte_carlo.fingerprint_trial_results(results),
        "daily_distribution": monte_carlo.fingerprint_daily_distribution(
            _distribution_probe(slices)
        ),
        "per_trial_slices": monte_carlo.fingerprint_per_trial_slices(slices),
    }


def _write_hashseed_probe_script(path: Path) -> None:
    path.write_text(
        """from __future__ import annotations

import json

import monte_carlo


def main() -> None:
    results, slices = monte_carlo.run_trials_parallel(
        "C070_G100",
        (1, 2, 3),
        4,
    )
    probe = []
    for trial_id in sorted(slices):
        for row in slices[trial_id]:
            probe.append({**row, "quantile_name": f"TRIAL_{trial_id}"})
    print(
        json.dumps(
            {
                "trial_results": monte_carlo.fingerprint_trial_results(results),
                "daily_distribution": monte_carlo.fingerprint_daily_distribution(
                    probe
                ),
                "per_trial_slices": monte_carlo.fingerprint_per_trial_slices(
                    slices
                ),
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
""",
        encoding="utf-8",
    )


def _run_hashseed(script_path: Path, hash_seed: int) -> dict[str, str]:
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = str(hash_seed)
    completed = subprocess.run(
        [sys.executable, str(script_path)],
        env=env,
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def test_parallel_matches_sequential_at_two_worker_counts() -> None:
    sequential_results, sequential_slices = monte_carlo.run_trials_sequentially(
        SCENARIO_ID,
        TRIAL_IDS,
    )
    sequential_fingerprints = _fingerprints(
        sequential_results,
        sequential_slices,
    )

    for workers in WORKER_COUNTS:
        parallel_results, parallel_slices = monte_carlo.run_trials_parallel(
            SCENARIO_ID,
            TRIAL_IDS,
            workers,
        )
        assert parallel_results == sequential_results
        assert _fingerprints(
            parallel_results,
            parallel_slices,
        ) == sequential_fingerprints


def test_parallel_fingerprints_match_across_python_hash_seeds(
    tmp_path: Path,
) -> None:
    script_path = tmp_path / "round2_hashseed_probe.py"
    _write_hashseed_probe_script(script_path)

    baseline = _run_hashseed(script_path, PYTHON_HASH_SEEDS[0])
    for hash_seed in PYTHON_HASH_SEEDS[1:]:
        assert _run_hashseed(script_path, hash_seed) == baseline
