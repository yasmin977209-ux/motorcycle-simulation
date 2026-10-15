#!/usr/bin/env python3
"""Create source-pinned Gate A goldens for C030_G030 IDs 1201..2400 only.

This creates a reference artifact, not an accepted N=2400 statistical checkpoint.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

SCENARIO = "C030_G030"
SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
SOURCE_COMMIT = "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
MASTER_SEED = 20270101
TRIAL_IDS = tuple(range(1201, 2401))
BASE_MAP_SHA256 = "166cae242d972c597f1a4466d184062f3d959649eb5e2440ad8de8b75663ff2c"
EXTENSION_DECISION_ID = "D-2026-10-15-10"


def canonical_trial_sha256(row: dict[str, Any]) -> str:
    payload = json.dumps(
        row,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _fail(message: str) -> None:
    raise RuntimeError(message)


def validate_record(record: dict[str, Any], *, run_id: int, run_attempt: int) -> None:
    trial_id = int(record.get("trial_id", -1))
    row = record.get("trial_result")
    if not isinstance(row, dict):
        _fail(f"TRIAL_RESULT_MISSING:{trial_id}")
    if (
        record.get("scenario_id") != SCENARIO
        or row.get("scenario_id") != SCENARIO
        or int(row.get("trial_id", -1)) != trial_id
        or record.get("source_sha") != SOURCE_SHA
        or record.get("source_commit") != SOURCE_COMMIT
        or int(record.get("master_seed", -1)) != MASTER_SEED
        or int(record.get("run_id", -1)) != run_id
        or int(record.get("run_attempt", -1)) != run_attempt
        or record.get("origin") != "pinned_source_reference"
    ):
        _fail(f"TRIAL_PROVENANCE_MISMATCH:{SCENARIO}/{trial_id}")
    if record.get("result_sha256") != canonical_trial_sha256(row):
        _fail(f"TRIAL_RESULT_SHA_MISMATCH:{SCENARIO}/{trial_id}")


def extension_map_sha(records: list[dict[str, Any]]) -> str:
    indexed: dict[int, str] = {}
    for record in records:
        trial_id = int(record["trial_id"])
        if trial_id in indexed:
            _fail(f"DUPLICATE_TRIAL_ID:{trial_id}")
        indexed[trial_id] = str(record["result_sha256"])
    payload = "".join(
        f"{SCENARIO}|{trial_id}|{indexed[trial_id]}\n"
        for trial_id in sorted(indexed)
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def validate_extension_records(
    records: list[dict[str, Any]], *, run_id: int, run_attempt: int
) -> dict[int, str]:
    indexed: dict[int, str] = {}
    for record in records:
        validate_record(record, run_id=run_id, run_attempt=run_attempt)
        trial_id = int(record["trial_id"])
        if trial_id in indexed:
            _fail(f"DUPLICATE_TRIAL_ID:{trial_id}")
        indexed[trial_id] = str(record["result_sha256"])
    if len(records) != len(TRIAL_IDS):
        _fail(f"EXTENSION_RECORD_COUNT_MISMATCH:{len(records)}")
    if sorted(indexed) != list(TRIAL_IDS):
        _fail("EXTENSION_TRIAL_COVERAGE_MISMATCH")
    return indexed


def generate(source_root: Path, output_file: Path) -> dict[str, Any]:
    source_head = subprocess.run(
        ["git", "-C", str(source_root), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    if source_head != SOURCE_COMMIT:
        _fail(f"PINNED_SOURCE_COMMIT_MISMATCH:{source_head}")

    run_id = int(os.environ["GITHUB_RUN_ID"])
    run_attempt = int(os.environ["GITHUB_RUN_ATTEMPT"])
    workflow_head_sha = os.environ["GITHUB_SHA"]
    if len(workflow_head_sha) != 40:
        _fail("WORKFLOW_HEAD_SHA_INVALID")

    # Load only the pinned model source tree after checking its exact Git commit.
    sys.path.insert(0, str(source_root))
    import monte_carlo  # type: ignore[import-not-found]  # noqa: E402
    import daily_engine  # type: ignore[import-not-found]  # noqa: E402

    collection_probability, recovery_rate_pct = monte_carlo.parse_scenario_id(SCENARIO)
    records: list[dict[str, Any]] = []
    for trial_id in TRIAL_IDS:
        project = daily_engine.run_deterministic_trial(
            recovery_rate_pct=recovery_rate_pct,
            trial_id=trial_id,
            scenario_id=SCENARIO,
            master_seed=MASTER_SEED,
            collection_probability=collection_probability,
            log_events=False,
        )
        trial = monte_carlo._trial_result_from_project(
            project,
            scenario_id=SCENARIO,
            collection_probability=collection_probability,
            recovery_rate_pct=recovery_rate_pct,
            trial_id=trial_id,
        )
        row = dataclasses.asdict(trial)
        records.append({
            "scenario_id": SCENARIO,
            "trial_id": trial_id,
            "trial_result": row,
            "result_sha256": canonical_trial_sha256(row),
            "source_sha": SOURCE_SHA,
            "source_commit": SOURCE_COMMIT,
            "master_seed": MASTER_SEED,
            "run_id": run_id,
            "run_attempt": run_attempt,
            "origin": "pinned_source_reference",
        })
        if trial_id % 100 == 0:
            print(f"GOLDEN_REFERENCE_PROGRESS={trial_id - 1200}/1200")

    hashes = validate_extension_records(records, run_id=run_id, run_attempt=run_attempt)
    extension_digest = extension_map_sha(records)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": "gate-a-golden-extension-v1",
        "status": "PASS",
        "extension_decision_id": EXTENSION_DECISION_ID,
        "base_decision_id": "D-2026-10-14-01",
        "scenario_id": SCENARIO,
        "source_sha": SOURCE_SHA,
        "source_commit": SOURCE_COMMIT,
        "master_seed": MASTER_SEED,
        "trial_id_start": TRIAL_IDS[0],
        "trial_id_end": TRIAL_IDS[-1],
        "trial_count": len(records),
        "run_id": run_id,
        "run_attempt": run_attempt,
        "workflow_head_sha": workflow_head_sha,
        "origin": "pinned_approved_source_reference",
        "historical_ids_rerun": False,
        "historical_dataset_modified": False,
        "historical_parquet_modified": False,
        "source_sha_bumped": False,
        "production_checkpoint_accepted": False,
        "base_golden_map_sha256": BASE_MAP_SHA256,
        "extension_map_sha256": extension_digest,
        "records": records,
    }
    output_file.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "PASS",
        "scenario": SCENARIO,
        "source_sha": SOURCE_SHA,
        "source_commit": SOURCE_COMMIT,
        "master_seed": MASTER_SEED,
        "trial_ids": [TRIAL_IDS[0], TRIAL_IDS[-1]],
        "records": len(records),
        "run_id": run_id,
        "run_attempt": run_attempt,
        "workflow_head_sha": workflow_head_sha,
        "base_golden_map_sha256": BASE_MAP_SHA256,
        "extension_map_sha256": extension_digest,
        "production_checkpoint_accepted": False,
    }, ensure_ascii=False, sort_keys=True))
    return payload


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output-file", default="results_gatea/golden_extension.json")
    args = parser.parse_args()
    generate(Path(args.source_root).resolve(), Path(args.output_file))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
