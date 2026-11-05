"""Build ephemeral, bounded fixtures for acceptance tests only.

These deterministic/seeded checks are not an official Monte Carlo cohort.
They must not be uploaded as canonical data, used for Gate A/ Gate B, or
merged back into the repository. The workflow recreates and deletes the
results_stage5 directory on each CI run.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

import monte_carlo

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results_stage5"
MASTER_SEED = 20270101


def stable_sha(value) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_c100_fixtures() -> None:
    result, daily = monte_carlo.run_single_trial(
        "C100_G100", 1, master_seed=MASTER_SEED
    )
    results = [result]
    slices = {1: daily}
    selection = monte_carlo.select_representative_trials(results)

    # Exact canonical deterministic acceptance values, unchanged by RNG changes
    # because collection probability 1.0 is deterministic.
    assert result.final_net_project_equity == 209671000
    assert result.partner1_final_entitlement == 146769700
    assert result.partner2_final_entitlement == 62901300
    assert result.final_cash == 209671000
    assert result.final_close_date == "2033-01-06"
    assert len(daily) == 2198

    pq.write_table(
        pa.Table.from_pylist([asdict(result)]),
        RESULTS / "trials_summary.parquet",
    )
    pq.write_table(
        pa.Table.from_pylist([
            {"selection_key": key, "trial_id": int(trial_id)}
            for key, trial_id in selection.items()
        ]),
        RESULTS / "selection.parquet",
    )

    daily_path = RESULTS / f"C100_G100_trial_{selection.p50_trial_id:06d}_daily.json"
    daily_path.write_text(
        json.dumps(daily, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    long_distribution = monte_carlo.build_daily_distribution(results, slices)
    wide_by_date = {}
    for row in long_distribution:
        current = wide_by_date.setdefault(
            row["date"],
            {
                "date": row["date"],
                "active_trial_count": row["active_trial_count"],
            },
        )
        for metric in (
            "Cash",
            "Net_Equity",
            "Active_Bikes",
            "Owned_Transferred_Bikes",
            "Pending_Claims",
        ):
            current[f"{row['quantile_name']}_{metric}"] = row[metric]

    pq.write_table(
        pa.Table.from_pylist(
            [wide_by_date[key] for key in sorted(wide_by_date)]
        ),
        RESULTS / "daily_distribution.parquet",
    )


def build_worker_equivalence_fixture() -> None:
    trial_ids = (1, 2, 3)
    sequential_results, sequential_daily = monte_carlo.run_trials_sequentially(
        "C070_G100", trial_ids, master_seed=MASTER_SEED
    )
    parallel2_results, parallel2_daily = monte_carlo.run_trials_parallel(
        "C070_G100", trial_ids, 2, master_seed=MASTER_SEED
    )
    parallel4_results, parallel4_daily = monte_carlo.run_trials_parallel(
        "C070_G100", trial_ids, 4, master_seed=MASTER_SEED
    )

    def by_id(results):
        return {result.trial_id: result for result in results}

    seq = by_id(sequential_results)
    p2 = by_id(parallel2_results)
    p4 = by_id(parallel4_results)
    manifest = []

    for trial_id in trial_ids:
        seq_result = asdict(seq[trial_id])
        p2_result = asdict(p2[trial_id])
        p4_result = asdict(p4[trial_id])
        seq_daily = sequential_daily[trial_id]
        p2_daily = parallel2_daily[trial_id]
        p4_daily = parallel4_daily[trial_id]

        manifest.append({
            "scenario_id": "C070_G100",
            "trial_id": trial_id,
            "exact_1_eq_2": seq_result == p2_result and seq_daily == p2_daily,
            "exact_1_eq_4": seq_result == p4_result and seq_daily == p4_daily,
            "trial_result_sha256_1": stable_sha(seq_result),
            "trial_result_sha256_2": stable_sha(p2_result),
            "trial_result_sha256_4": stable_sha(p4_result),
            "daily_slice_sha256_1": stable_sha(seq_daily),
            "daily_slice_sha256_2": stable_sha(p2_daily),
            "daily_slice_sha256_4": stable_sha(p4_daily),
        })

    assert all(row["exact_1_eq_2"] and row["exact_1_eq_4"] for row in manifest)
    (RESULTS / "worker_equivalence_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(json.dumps({
        "fixture_only": True,
        "no_canonical_artifacts": True,
        "c100_deterministic_trial_rows": 1,
        "worker_equivalence_trial_ids": list(trial_ids),
        "serial_parallel_exact": True,
        "files": sorted(path.name for path in RESULTS.iterdir()),
    }, ensure_ascii=False, sort_keys=True))


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    build_c100_fixtures()
    build_worker_equivalence_fixture()


if __name__ == "__main__":
    main()
