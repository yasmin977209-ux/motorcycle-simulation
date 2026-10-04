from __future__ import annotations

import argparse
import hashlib
import json
import resource
import subprocess
import sys
import time
from dataclasses import asdict
from pathlib import Path

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
    parser.add_argument("--trial-ids", nargs="+", type=int, required=True)
    parser.add_argument("--log-events", required=True, type=_parse_bool)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--_worker-trial-id", type=int, default=None, help=argparse.SUPPRESS)
    return parser.parse_args()


def _run_worker(args: argparse.Namespace) -> None:
    if args._worker_trial_id is None:
        raise ValueError("_worker-trial-id is required in worker mode")

    trial_id = args._worker_trial_id
    started = time.perf_counter()
    project = daily_engine.run_deterministic_trial(
        scenario_id=args.scenario,
        trial_id=trial_id,
        log_events=args.log_events,
    )
    elapsed_seconds = time.perf_counter() - started

    collection_probability, recovery_rate_pct = (
        monte_carlo.parse_scenario_id(args.scenario)
    )
    result = monte_carlo._trial_result_from_project(
        project,
        scenario_id=args.scenario,
        collection_probability=collection_probability,
        recovery_rate_pct=recovery_rate_pct,
        trial_id=trial_id,
    )

    payload = {
        "trial_id": trial_id,
        "log_events": args.log_events,
        "elapsed_seconds": elapsed_seconds,
        "rss_max_kb": int(
            resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        ),
        "event_log_len": len(project.event_log),
        "trial_result_sha256": _result_sha256(result),
    }
    print(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
        )
    )


def _run_measurement(args: argparse.Namespace) -> dict[str, object]:
    trial_ids = list(args.trial_ids)
    if len(trial_ids) != 5:
        raise ValueError("CP4 requires exactly five trial_ids")
    if len(set(trial_ids)) != 5:
        raise ValueError("trial_ids must be unique")
    if any(trial_id < 1 for trial_id in trial_ids):
        raise ValueError("trial_ids must be >= 1")

    rows: list[dict[str, object]] = []
    for trial_id in trial_ids:
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "scripts.stage6_5_measure_heavy",
                "--scenario",
                args.scenario,
                "--trial-ids",
                str(trial_id),
                "--log-events",
                str(args.log_events),
                "--output-dir",
                str(args.output_dir),
                "--_worker-trial-id",
                str(trial_id),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        line = proc.stdout.strip().splitlines()[-1]
        rows.append(json.loads(line))

    rows.sort(key=lambda row: int(row["trial_id"]))
    expected_ids = sorted(trial_ids)
    actual_ids = [int(row["trial_id"]) for row in rows]
    if actual_ids != expected_ids:
        raise AssertionError(
            f"unexpected trial IDs: expected={expected_ids} actual={actual_ids}"
        )

    mean_elapsed = sum(
        float(row["elapsed_seconds"]) for row in rows
    ) / len(rows)
    mean_rss = sum(
        int(row["rss_max_kb"]) for row in rows
    ) / len(rows)

    payload: dict[str, object] = {
        "scenario_id": args.scenario,
        "log_events": args.log_events,
        "trial_ids": expected_ids,
        "trials": rows,
        "trial_count": len(rows),
        "mean_elapsed_seconds": mean_elapsed,
        "mean_rss_max_kb": mean_rss,
        "all_event_log_positive": all(
            int(row["event_log_len"]) > 0 for row in rows
        ) if args.log_events else None,
        "all_event_log_zero": all(
            int(row["event_log_len"]) == 0 for row in rows
        ) if not args.log_events else None,
    }

    args.output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )
    output_path = (
        Path(args.output_dir)
        / f"cp4_measure_{args.log_events}.json"
    )
    output_path.write_text(
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
    return payload


def main() -> None:
    args = parse_args()
    if args._worker_trial_id is not None:
        _run_worker(args)
        return

    _run_measurement(args)


if __name__ == "__main__":
    main()
