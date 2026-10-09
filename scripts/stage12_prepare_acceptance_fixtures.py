from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

import monte_carlo

RESULTS = Path("results_stage5")
MASTER_SEED = 20270101


def stable_sha(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _write_daily_fixture(result, daily_rows) -> None:
    selection = monte_carlo.select_representative_trials([result])
    with (RESULTS / f"C100_G100_trial_{selection.p50_trial_id:06d}_daily.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(daily_rows, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

    long_distribution = monte_carlo.build_daily_distribution([result], {1: daily_rows})
    wide_by_date = {}
    metrics = (
        "Cash",
        "Net_Equity",
        "Active_Bikes",
        "Owned_Transferred_Bikes",
        "Pending_Claims",
    )
    for row in long_distribution:
        current = wide_by_date.setdefault(
            row["date"],
            {"date": row["date"], "active_trial_count": row["active_trial_count"]},
        )
        for metric in metrics:
            current[f"{row['quantile_name']}_{metric}"] = row[metric]

    daily_distribution = [wide_by_date[key] for key in sorted(wide_by_date)]
    pq.write_table(
        pa.Table.from_pylist(daily_distribution),
        RESULTS / "daily_distribution.parquet",
    )


def _write_worker_equivalence_manifest() -> dict[str, object]:
    trial_ids = (1, 2, 3)
    sequential_results, sequential_slices = monte_carlo.run_trials_sequentially(
        "C070_G100", trial_ids
    )
    parallel2_results, parallel2_slices = monte_carlo.run_trials_parallel(
        "C070_G100", trial_ids, 2
    )
    parallel4_results, parallel4_slices = monte_carlo.run_trials_parallel(
        "C070_G100", trial_ids, 4
    )

    def by_id(results):
        return {result.trial_id: result for result in results}

    sequential_by_id = by_id(sequential_results)
    parallel2_by_id = by_id(parallel2_results)
    parallel4_by_id = by_id(parallel4_results)
    manifest = []

    for trial_id in trial_ids:
        sequential_result = asdict(sequential_by_id[trial_id])
        parallel2_result = asdict(parallel2_by_id[trial_id])
        parallel4_result = asdict(parallel4_by_id[trial_id])
        sequential_daily = sequential_slices[trial_id]
        parallel2_daily = parallel2_slices[trial_id]
        parallel4_daily = parallel4_slices[trial_id]
        manifest.append({
            "scenario_id": "C070_G100",
            "trial_id": trial_id,
            "exact_1_eq_2": (
                sequential_result == parallel2_result
                and sequential_daily == parallel2_daily
            ),
            "exact_1_eq_4": (
                sequential_result == parallel4_result
                and sequential_daily == parallel4_daily
            ),
            "trial_result_sha256_1": stable_sha(sequential_result),
            "trial_result_sha256_2": stable_sha(parallel2_result),
            "trial_result_sha256_4": stable_sha(parallel4_result),
            "daily_slice_sha256_1": stable_sha(sequential_daily),
            "daily_slice_sha256_2": stable_sha(parallel2_daily),
            "daily_slice_sha256_4": stable_sha(parallel4_daily),
        })

    if not all(row["exact_1_eq_2"] and row["exact_1_eq_4"] for row in manifest):
        raise SystemExit("WORKER_EQUIVALENCE_FIXTURE_MISMATCH")

    (RESULTS / "worker_equivalence_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return {"worker_manifest_rows": len(manifest), "exact_all": True}


def main() -> None:
    if RESULTS.exists():
        shutil.rmtree(RESULTS)
    RESULTS.mkdir(parents=True)

    result, daily_rows = monte_carlo.run_single_trial(
        "C100_G100", 1, master_seed=MASTER_SEED
    )
    expected = {
        "final_net_project_equity": 209671000,
        "partner1_final_entitlement": 146769700,
        "partner2_final_entitlement": 62901300,
        "final_cash": 209671000,
        "final_close_date": "2033-01-06",
        "daily_balance_checks": 2198,
    }
    actual = {
        "final_net_project_equity": result.final_net_project_equity,
        "partner1_final_entitlement": result.partner1_final_entitlement,
        "partner2_final_entitlement": result.partner2_final_entitlement,
        "final_cash": result.final_cash,
        "final_close_date": result.final_close_date,
        "daily_balance_checks": len(daily_rows),
    }
    if actual != expected:
        raise SystemExit(f"C100_FIXTURE_GOLDEN_MISMATCH: {actual!r}")

    results = [result]
    selection = monte_carlo.select_representative_trials(results)
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
    _write_daily_fixture(result, daily_rows)
    worker_manifest = _write_worker_equivalence_manifest()

    print(json.dumps({
        "fixtures": [
            "results_stage5/trials_summary.parquet",
            "results_stage5/selection.parquet",
            "results_stage5/daily_distribution.parquet",
            "results_stage5/worker_equivalence_manifest.json",
            f"results_stage5/C100_G100_trial_{selection.p50_trial_id:06d}_daily.json",
        ],
        "c100_golden": actual,
        "worker_equivalence": worker_manifest,
        "origin": "freshly generated in this run; no prior run artifact was consumed",
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
