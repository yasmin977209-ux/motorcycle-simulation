#!/usr/bin/env python3
"""Generate the owner-authorized C100 Gate A Golden extension from pinned source only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
SOURCE_COMMIT = "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
MASTER_SEED = 20270101
BASE_DECISION_ID = "D-2026-10-14-01"
EXTENSION_DECISION_ID = "D-2026-10-17-07"
BASE_GOLDEN_MAP_SHA256 = "0fbe3aa87a253f9527953c77b0a122871c9344f75ece6c8a49da99b2a85c1ce1"
EXTENSION_SCHEMA_VERSION = "gate-a-golden-extension-v1"
SCENARIOS = (
    "C100_G000",
    "C100_G030",
    "C100_G050",
    "C100_G070",
    "C100_G100",
)
TRIAL_ID_START = 2
TRIAL_ID_END = 600
TRIAL_COUNT_PER_SCENARIO = TRIAL_ID_END - TRIAL_ID_START + 1
EXPECTED_RECORD_COUNT = len(SCENARIOS) * TRIAL_COUNT_PER_SCENARIO
MODEL_FILES = (
    "constants.py", "dateutils.py", "rng.py", "entities.py",
    "state_machine.py", "daily_engine.py", "accounting.py", "collection.py",
    "guarantee.py", "friday.py", "settlement.py", "closure.py",
    "partner_equity.py", "monte_carlo.py",
)
SHA256_RE = __import__("re").compile(r"^[0-9a-f]{64}$")
COMMIT_RE = __import__("re").compile(r"^[0-9a-f]{40}$")


def canonical_result_sha256(result: Any) -> str:
    """Stage 10's exact per-trial result fingerprint contract."""
    if is_dataclass(result):
        payload: Any = asdict(result)
    elif isinstance(result, Mapping):
        payload = dict(result)
    else:
        raise TypeError("trial result must be a dataclass instance or mapping")
    raw = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def ordered_extension_map_sha256(records: Iterable[Mapping[str, Any]]) -> str:
    """Hash the canonical scenario|trial_id|result_sha256 stream, sorted by key."""
    normalized: list[tuple[str, int, str]] = []
    seen: set[tuple[str, int]] = set()
    for row in records:
        scenario = row.get("scenario_id")
        trial_id = row.get("trial_id")
        digest = row.get("result_sha256")
        if scenario not in SCENARIOS:
            raise ValueError(f"UNAUTHORIZED_C100_SCENARIO:{scenario}")
        if isinstance(trial_id, bool) or not isinstance(trial_id, int):
            raise ValueError(f"INVALID_TRIAL_ID:{scenario}:{trial_id}")
        if not TRIAL_ID_START <= trial_id <= TRIAL_ID_END:
            raise ValueError(f"UNAUTHORIZED_TRIAL_ID:{scenario}:{trial_id}")
        key = (scenario, trial_id)
        if key in seen:
            raise ValueError(f"DUPLICATE_TRIAL_ID:{scenario}:{trial_id}")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise ValueError(f"INVALID_RESULT_SHA256:{scenario}:{trial_id}")
        seen.add(key)
        normalized.append((scenario, trial_id, digest))
    expected = {
        (scenario, trial_id)
        for scenario in SCENARIOS
        for trial_id in range(TRIAL_ID_START, TRIAL_ID_END + 1)
    }
    if seen != expected:
        missing = sorted(expected - seen)[:10]
        extra = sorted(seen - expected)[:10]
        raise ValueError(f"C100_EXTENSION_COVERAGE_MISMATCH:missing={missing}:extra={extra}")
    body = "".join(
        f"{scenario}|{trial_id}|{digest}\n"
        for scenario, trial_id, digest in sorted(normalized)
    ).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def verify_source_closure(source_root: Path) -> dict[str, Any]:
    source_root = source_root.resolve()
    actual_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=source_root,
        check=True, text=True, capture_output=True,
    ).stdout.strip()
    if actual_commit != SOURCE_COMMIT:
        raise RuntimeError(f"PINNED_SOURCE_COMMIT_MISMATCH:{actual_commit}")
    for candidate in (SOURCE_SHA, SOURCE_COMMIT):
        if not COMMIT_RE.fullmatch(candidate):
            raise RuntimeError(f"INVALID_SOURCE_COMMIT:{candidate}")
    blobs: dict[str, dict[str, str]] = {}
    for path in MODEL_FILES:
        values: dict[str, str] = {}
        for commit in (SOURCE_SHA, SOURCE_COMMIT):
            values[commit] = subprocess.run(
                ["git", "rev-parse", f"{commit}:{path}"], cwd=source_root,
                check=True, text=True, capture_output=True,
            ).stdout.strip()
        if values[SOURCE_SHA] != values[SOURCE_COMMIT]:
            raise RuntimeError(f"MODEL_SOURCE_CLOSURE_MISMATCH:{path}")
        worktree_blob = subprocess.run(
            ["git", "hash-object", path], cwd=source_root,
            check=True, text=True, capture_output=True,
        ).stdout.strip()
        if worktree_blob != values[SOURCE_COMMIT]:
            raise RuntimeError(f"MODEL_WORKTREE_BLOB_MISMATCH:{path}")
        blobs[path] = values
    return {
        "source_sha": SOURCE_SHA,
        "source_commit": SOURCE_COMMIT,
        "model_file_count": len(MODEL_FILES),
        "model_file_blob_sha1_by_source_sha_and_source_commit": blobs,
        "all_model_file_blobs_equal": True,
    }


def build_record(
    result: Any,
    *,
    scenario_id: str,
    trial_id: int,
    run_id: int,
    run_attempt: int,
) -> dict[str, Any]:
    if not is_dataclass(result):
        raise TypeError("run_single_trial must return a dataclass TrialResult")
    row = asdict(result)
    if row.get("trial_id") != trial_id:
        raise RuntimeError(f"TRIAL_RESULT_ID_MISMATCH:{scenario_id}:{trial_id}")
    if row.get("scenario_id") != scenario_id:
        raise RuntimeError(f"TRIAL_RESULT_SCENARIO_MISMATCH:{scenario_id}:{trial_id}")
    digest = canonical_result_sha256(result)
    if canonical_result_sha256(row) != digest:
        raise RuntimeError(f"TRIAL_RESULT_HASH_RECOMPUTE_MISMATCH:{scenario_id}:{trial_id}")
    return {
        "master_seed": MASTER_SEED,
        "origin": "pinned_source_reference",
        "result_sha256": digest,
        "run_attempt": run_attempt,
        "run_id": run_id,
        "scenario_id": scenario_id,
        "schema_version": EXTENSION_SCHEMA_VERSION,
        "source_commit": SOURCE_COMMIT,
        "source_sha": SOURCE_SHA,
        "trial_id": trial_id,
        "trial_result": row,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--output", default="results_gatea/c100_golden_extension.json")
    parser.add_argument("--progress", default="results_gatea/c100_golden_extension.progress.jsonl")
    args = parser.parse_args()

    run_id = int(os.environ.get("GITHUB_RUN_ID", "0"))
    run_attempt = int(os.environ.get("GITHUB_RUN_ATTEMPT", "0"))
    workflow_head_sha = os.environ.get("GITHUB_SHA", "")
    if run_id < 1 or run_attempt < 1 or not COMMIT_RE.fullmatch(workflow_head_sha):
        raise RuntimeError("GITHUB_RUN_PROVENANCE_MISSING")
    if os.environ.get("SOURCE_SHA") != SOURCE_SHA:
        raise RuntimeError("SOURCE_SHA_ENVIRONMENT_MISMATCH")
    if os.environ.get("MASTER_SEED") != str(MASTER_SEED):
        raise RuntimeError("MASTER_SEED_ENVIRONMENT_MISMATCH")

    output = Path(args.output)
    progress = Path(args.progress)
    output.parent.mkdir(parents=True, exist_ok=True)
    if progress.exists() or output.exists():
        raise RuntimeError("GOLDEN_GENERATION_OUTPUT_ALREADY_EXISTS_NO_RERUN")
    source_root = Path(args.source_root).resolve()
    source_proof = verify_source_closure(source_root)

    # Import the simulation modules only after making the pinned approved tree explicit.
    sys.path.insert(0, str(source_root))
    import constants
    import monte_carlo
    import rng

    if constants.MASTER_SEED != MASTER_SEED:
        raise RuntimeError(f"PINNED_MASTER_SEED_MISMATCH:{constants.MASTER_SEED}")
    if Path(monte_carlo.__file__).resolve().parent != source_root:
        raise RuntimeError(f"MONTE_CARLO_IMPORT_NOT_PINNED:{monte_carlo.__file__}")
    if Path(rng.__file__).resolve().parent != source_root:
        raise RuntimeError(f"RNG_IMPORT_NOT_PINNED:{rng.__file__}")
    expected_rates = {
        "C100_G000": 0,
        "C100_G030": 30,
        "C100_G050": 50,
        "C100_G070": 70,
        "C100_G100": 100,
    }
    if set(s for s in constants.SCENARIO_IDS if s in SCENARIOS) != set(SCENARIOS):
        raise RuntimeError("C100_SCENARIO_SET_MISMATCH")
    for scenario, recovery in expected_rates.items():
        probability, recovery_rate = monte_carlo.parse_scenario_id(scenario)
        if probability != 1.0 or recovery_rate != recovery:
            raise RuntimeError(f"C100_SCENARIO_PARAMETER_MISMATCH:{scenario}")

    records: list[dict[str, Any]] = []
    seen_ids: set[tuple[str, int]] = set()
    # Append each completed ID before starting another, so a failed run leaves inspectable
    # evidence and must be reconciled rather than silently repeating already-computed IDs.
    with progress.open("x", encoding="utf-8", newline="\n") as stream:
        for scenario in SCENARIOS:
            for trial_id in range(TRIAL_ID_START, TRIAL_ID_END + 1):
                key = (scenario, trial_id)
                if key in seen_ids:
                    raise RuntimeError(f"DUPLICATE_TRIAL_ID_BEFORE_RUN:{scenario}:{trial_id}")
                result, _daily_rows = monte_carlo.run_single_trial(
                    scenario, trial_id, master_seed=MASTER_SEED
                )
                record = build_record(
                    result,
                    scenario_id=scenario,
                    trial_id=trial_id,
                    run_id=run_id,
                    run_attempt=run_attempt,
                )
                stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str) + "\n")
                stream.flush()
                records.append(record)
                seen_ids.add(key)

    if len(records) != EXPECTED_RECORD_COUNT:
        raise RuntimeError(f"C100_EXTENSION_RECORD_COUNT_MISMATCH:{len(records)}")
    extension_sha = ordered_extension_map_sha256(records)
    payload = {
        "base_decision_id": BASE_DECISION_ID,
        "base_golden_map_sha256": BASE_GOLDEN_MAP_SHA256,
        "extension_decision_id": EXTENSION_DECISION_ID,
        "extension_map_sha256": extension_sha,
        "historical_dataset_modified": False,
        "historical_ids_rerun": False,
        "historical_parquet_modified": False,
        "master_seed": MASTER_SEED,
        "model_source_closure": source_proof,
        "origin": "pinned_approved_source_reference",
        "production_checkpoint_accepted": False,
        "records": records,
        "run_attempt": run_attempt,
        "run_id": run_id,
        "scenario_ids": list(SCENARIOS),
        "schema_version": EXTENSION_SCHEMA_VERSION,
        "source_commit": SOURCE_COMMIT,
        "source_sha": SOURCE_SHA,
        "source_sha_bumped": False,
        "status": "PASS",
        "trial_count": len(records),
        "trial_id_end": TRIAL_ID_END,
        "trial_id_start": TRIAL_ID_START,
        "workflow_head_sha": workflow_head_sha,
    }
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    # Verify persisted JSON independently from the in-memory Python objects before success.
    roundtrip = json.loads(output.read_text(encoding="utf-8"))
    if roundtrip.get("status") != "PASS" or roundtrip.get("trial_count") != EXPECTED_RECORD_COUNT:
        raise RuntimeError("C100_EXTENSION_WRITTEN_PAYLOAD_INVALID")
    rows = roundtrip.get("records")
    if not isinstance(rows, list) or len(rows) != EXPECTED_RECORD_COUNT:
        raise RuntimeError("C100_EXTENSION_WRITTEN_RECORD_COUNT_INVALID")
    for row in rows:
        if canonical_result_sha256(row.get("trial_result")) != row.get("result_sha256"):
            raise RuntimeError(f"PERSISTED_RESULT_HASH_MISMATCH:{row.get('scenario_id')}:{row.get('trial_id')}")
        if row.get("source_sha") != SOURCE_SHA or row.get("source_commit") != SOURCE_COMMIT:
            raise RuntimeError(f"PERSISTED_RESULT_SOURCE_IDENTITY_MISMATCH:{row.get('scenario_id')}:{row.get('trial_id')}")
    if ordered_extension_map_sha256(rows) != extension_sha:
        raise RuntimeError("C100_EXTENSION_PERSISTED_MAP_SHA_MISMATCH")
    print(json.dumps({
        "status": "PASS",
        "decision_id": EXTENSION_DECISION_ID,
        "source_sha": SOURCE_SHA,
        "source_commit": SOURCE_COMMIT,
        "master_seed": MASTER_SEED,
        "scenario_count": len(SCENARIOS),
        "scenarios": {
            scenario: {"trial_id_start": TRIAL_ID_START, "trial_id_end": TRIAL_ID_END,
                       "count": TRIAL_COUNT_PER_SCENARIO}
            for scenario in SCENARIOS
        },
        "trial_count": len(records),
        "extension_map_sha256": extension_sha,
        "workflow_run_id": run_id,
        "workflow_head_sha": workflow_head_sha,
        "output_bytes": output.stat().st_size,
        "progress_bytes": progress.stat().st_size,
        "historical_dataset_modified": False,
        "historical_parquet_modified": False,
        "production_checkpoint_accepted": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
