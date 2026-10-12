#!/usr/bin/env python3
"""Create isolated, run-local fixtures required by the repository acceptance contract.

These are test inputs only; they are never merged into the Stage 13 sample or canonical data.
The fixture builder verifies the historical deterministic C100 golden before writing anything.
"""
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
C100_GOLDEN = {
    "final_net_project_equity": 209671000,
    "partner1_final_entitlement": 146769700,
    "partner2_final_entitlement": 62901300,
    "final_cash": 209671000,
    "final_close_date": "2033-01-06",
    "daily_rows": 2198,
}


def stable_sha(value: object) -> str:
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )


def worker_equivalence() -> list[dict[str, object]]:
    scenario_id = "C070_G100"
    trial_ids = (1, 2, 3)
    seq_results, seq_daily = monte_carlo.run_trials_sequentially(scenario_id, trial_ids)
    p2_results, p2_daily = monte_carlo.run_trials_parallel(scenario_id, trial_ids, 2)
    p4_results, p4_daily = monte_carlo.run_trials_parallel(scenario_id, trial_ids, 4)
    by_id = lambda items: {item.trial_id: item for item in items}
    seq_r, p2_r, p4_r = map(by_id, (seq_results, p2_results, p4_results))
    manifest = []
    for tid in trial_ids:
        s, p2, p4 = asdict(seq_r[tid]), asdict(p2_r[tid]), asdict(p4_r[tid])
        d1, d2, d4 = seq_daily[tid], p2_daily[tid], p4_daily[tid]
        manifest.append({
            "scenario_id": scenario_id,
            "trial_id": tid,
            "exact_1_eq_2": s == p2 and d1 == d2,
            "exact_1_eq_4": s == p4 and d1 == d4,
            "trial_result_sha256_1": stable_sha(s),
            "trial_result_sha256_2": stable_sha(p2),
            "trial_result_sha256_4": stable_sha(p4),
            "daily_slice_sha256_1": stable_sha(d1),
            "daily_slice_sha256_2": stable_sha(d2),
            "daily_slice_sha256_4": stable_sha(d4),
        })
    if len(manifest) != 3 or not all(
        row["exact_1_eq_2"] and row["exact_1_eq_4"] for row in manifest
    ):
        raise AssertionError("WORKER_EQUIVALENCE_FIXTURE_MISMATCH")
    return manifest


def main() -> None:
    if RESULTS.exists():
        shutil.rmtree(RESULTS)
    RESULTS.mkdir(parents=True)

    result, daily_rows = monte_carlo.run_single_trial(
        "C100_G100", 1, master_seed=MASTER_SEED
    )
    actual = {
        "final_net_project_equity": result.final_net_project_equity,
        "partner1_final_entitlement": result.partner1_final_entitlement,
        "partner2_final_entitlement": result.partner2_final_entitlement,
        "final_cash": result.final_cash,
        "final_close_date": result.final_close_date,
        "daily_rows": len(daily_rows),
    }
    if actual != C100_GOLDEN:
        raise AssertionError(f"C100_FIXTURE_GOLDEN_MISMATCH: {actual!r}")

    selection = monte_carlo.select_representative_trials([result])
    pq.write_table(
        pa.Table.from_pylist([asdict(result)]),
        RESULTS / "trials_summary.parquet",
    )
    pq.write_table(
        pa.Table.from_pylist([
            {"selection_key": key, "trial_id": int(tid)}
            for key, tid in selection.items()
        ]),
        RESULTS / "selection.parquet",
    )
    with (RESULTS / "C100_G100_trial_000001_daily.json").open("w", encoding="utf-8") as f:
        json.dump(daily_rows, f, ensure_ascii=False, sort_keys=True, indent=2)
        f.write("\n")

    long_distribution = monte_carlo.build_daily_distribution([result], {1: daily_rows})
    wide_by_date: dict[str, dict[str, object]] = {}
    metrics = ("Cash", "Net_Equity", "Active_Bikes", "Owned_Transferred_Bikes", "Pending_Claims")
    for row in long_distribution:
        key = row["date"]
        wide = wide_by_date.setdefault(
            key, {"date": key, "active_trial_count": row.get("active_trial_count")}
        )
        for metric in metrics:
            wide[f"{row['quantile_name']}_{metric}"] = row[metric]
    daily_distribution = [wide_by_date[key] for key in sorted(wide_by_date)]
    if not daily_distribution or daily_distribution[0]["date"] != "2027-01-01" or daily_distribution[-1]["date"] != "2033-01-06":
        raise AssertionError("DAILY_DISTRIBUTION_FIXTURE_DATE_RANGE_MISMATCH")
    if len({row["date"] for row in daily_distribution}) != len(daily_distribution):
        raise AssertionError("DAILY_DISTRIBUTION_FIXTURE_DUPLICATE_DATE")
    pq.write_table(
        pa.Table.from_pylist(daily_distribution),
        RESULTS / "daily_distribution.parquet",
    )

    worker_manifest = worker_equivalence()
    write_json(RESULTS / "worker_equivalence_manifest.json", worker_manifest)
    fixture_identity = {
        "fixture_only": True,
        "not_part_of_stage13_sample": True,
        "not_part_of_canonical_11005_dataset": True,
        "master_seed": MASTER_SEED,
        "c100_trial_id": 1,
        "worker_equivalence_scenario": "C070_G100",
        "worker_equivalence_trial_ids": [1, 2, 3],
        "c100_golden": actual,
        "worker_manifest_rows": len(worker_manifest),
        "worker_equivalence_exact": True,
    }
    write_json(RESULTS / "fixture_identity.json", fixture_identity)
    print(json.dumps({
        "status": "PASS",
        "fixtures": sorted(path.name for path in RESULTS.iterdir()),
        "identity": fixture_identity,
    }, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
