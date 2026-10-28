#!/usr/bin/env python3
"""Generate an independent, source-pinned Gate A Golden candidate.

This workflow performs fresh full trials from IDs 1..N. It never reads production
trial-result artifacts. The candidate is not an approval decision; its output must
be reviewed and compared against the production cohort independently.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from typing import Any

import constants
import monte_carlo
import validation
import stats_integrity
from scripts import s6_first_checkpoint as s6

PINNED_SOURCE_SHA = "da1a9ea9b5cd789c944de3f07b08395bb67c49e7"
PINNED_COHORT_ID = "s6-v23-da1a9ea9"
PINNED_MASTER_SEED = 20270101
PINNED_TRIAL_COUNT = 2400
PINNED_MODEL_FILES = (
    "constants.py",
    "dateutils.py",
    "daily_engine.py",
    "entities.py",
    "monte_carlo.py",
    "rng.py",
    "validation.py",
    "stats_integrity.py",
    "scripts/s6_first_checkpoint.py",
)
COLLECTION_LEVELS = (85, 70, 50, 30)
RECOVERY_LEVELS = (100, 70, 50, 30, 0)
EXPECTED_SCENARIOS = tuple(
    f"C{collection:03d}_G{recovery:03d}"
    for collection in COLLECTION_LEVELS
    for recovery in RECOVERY_LEVELS
)
SCENARIO_FILENAME = "independent_golden_candidate.json"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_json(value: Any) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def write_json(path: Path, value: Any) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str) + "\n",
        encoding="utf-8",
    )
    return sha256_file(path)


def run_git(*args: str) -> str:
    p = subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True, encoding="utf-8"
    )
    return p.stdout.strip()


def require_source_identity(source_sha: str) -> dict[str, str]:
    if source_sha != PINNED_SOURCE_SHA:
        raise RuntimeError("S6_GOLDEN_SOURCE_SHA_NOT_OWNER_PINNED")
    if constants.MASTER_SEED != PINNED_MASTER_SEED:
        raise RuntimeError("S6_GOLDEN_MASTER_SEED_MISMATCH")
    expected_cohort = f"s6-v23-{source_sha[:8]}"
    if expected_cohort != PINNED_COHORT_ID:
        raise RuntimeError("S6_GOLDEN_COHORT_ID_MISMATCH")

    tested_sha = run_git("rev-parse", "HEAD")
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        event_sha = os.environ.get("GITHUB_SHA", "")
        if not event_sha or tested_sha != event_sha:
            raise RuntimeError("S6_GOLDEN_TESTED_SHA_CONTEXT_MISMATCH")
        ref = os.environ.get("GITHUB_REF", "")
        if not ref.startswith("refs/heads/"):
            raise RuntimeError("S6_GOLDEN_BRANCH_REF_REQUIRED")
        remote_head = run_git("ls-remote", "origin", ref).split()
        if not remote_head or remote_head[0] != tested_sha:
            raise RuntimeError("S6_GOLDEN_STALE_WORKFLOW_COMMIT")

    def tree_blobs(revision: str) -> dict[str, str]:
        entries = run_git("ls-tree", "-r", "--format=%(objectname) %(path)", revision).splitlines()
        result: dict[str, str] = {}
        for entry in entries:
            blob, file_path = entry.split(" ", 1)
            result[file_path] = blob
        return result

    source_tree = tree_blobs(source_sha)
    tested_tree = tree_blobs("HEAD")
    source_python_paths = sorted(path for path in source_tree if path.endswith(".py"))
    missing_lock_targets = sorted(set(PINNED_MODEL_FILES) - set(source_python_paths))
    if missing_lock_targets:
        raise RuntimeError(f"S6_GOLDEN_MODEL_LOCK_TARGET_MISSING:{missing_lock_targets}")
    extra_python_paths = sorted(
        path for path in set(tested_tree) - set(source_tree)
        if path.endswith(".py") and path != "scripts/s6_independent_golden_candidate.py"
    )
    if extra_python_paths:
        raise RuntimeError(f"S6_GOLDEN_UNEXPECTED_EXTRA_PYTHON_FILES:{extra_python_paths}")

    source_blobs: dict[str, str] = {}
    for path in source_python_paths:
        source_blob = source_tree[path]
        tested_blob = tested_tree.get(path)
        if source_blob != tested_blob:
            raise RuntimeError(f"S6_GOLDEN_MODEL_CODE_DRIFT:{path}")
        source_blobs[path] = source_blob
    return {"tested_sha": tested_sha, **{f"blob:{k}": v for k, v in source_blobs.items()}}


def financial_map_sha256(scenario: str, fingerprints: dict[str, str]) -> str:
    lines = [
        f"{scenario}|{trial_id}|{fingerprints[trial_id]}"
        for trial_id in sorted(fingerprints, key=lambda v: int(v))
    ]
    return sha256_bytes(("\n".join(lines) + "\n").encode("utf-8"))


def rng_audit_sha256(records: list[dict[str, int | str]]) -> str:
    return sha256_bytes(canonical_json(records))


def run_scenario(
    scenario: str, source_sha: str, trial_count: int, workers: int, output_dir: Path
) -> dict[str, Any]:
    started_at = now_utc()
    started = time.monotonic()
    if scenario not in EXPECTED_SCENARIOS:
        raise RuntimeError(f"S6_GOLDEN_UNSUPPORTED_SCENARIO:{scenario}")
    if trial_count != PINNED_TRIAL_COUNT:
        raise RuntimeError("S6_GOLDEN_TRIAL_COUNT_MUST_BE_2400")
    if not 1 <= workers <= 8:
        raise RuntimeError("S6_GOLDEN_WORKER_COUNT_OUT_OF_RANGE")
    provenance = require_source_identity(source_sha)
    trial_ids = list(range(1, trial_count + 1))

    # A fresh full run: no previous checkpoint, production artifact, or output reuse.
    results, daily = s6.run_full_trials(scenario, trial_ids, source_sha, workers)
    if set(results) != set(trial_ids) or set(daily) != set(trial_ids):
        raise RuntimeError("S6_GOLDEN_TRIAL_OR_DAILY_COVERAGE_MISMATCH")
    ordered = [results[tid] for tid in trial_ids]
    # Validate the exact expected sequence locally; the pinned stats_integrity
    # module does not expose validate_cumulative_trial_ids at this source revision.
    if [int(result.trial_id) for result in ordered] != trial_ids:
        raise RuntimeError("S6_GOLDEN_TRIAL_ID_SEQUENCE_MISMATCH")
    validation.validate_rng_audit_records(
        [asdict(result) for result in ordered],
        source_sha=source_sha,
        master_seed=constants.MASTER_SEED,
        require_audit_fingerprint=True,
    )

    financial_fingerprints: dict[str, str] = {}
    rng_records: list[dict[str, int | str]] = []
    result_sha_records: list[dict[str, int | str]] = []
    n_closed = 0
    for trial_id, result in enumerate(ordered, start=1):
        if int(result.trial_id) != trial_id:
            raise RuntimeError("S6_GOLDEN_TRIAL_ID_ORDER_MISMATCH")
        if str(result.scenario_id) != scenario:
            raise RuntimeError("S6_GOLDEN_SCENARIO_IDENTITY_MISMATCH")
        computed = monte_carlo.trial_fingerprint(result)
        recorded = getattr(result, "trial_fingerprint", "")
        if recorded and recorded != computed:
            raise RuntimeError(f"S6_GOLDEN_FINANCIAL_FINGERPRINT_SELF_MISMATCH:{trial_id}")
        if len(computed) != 64 or any(ch not in "0123456789abcdef" for ch in computed):
            raise RuntimeError(f"S6_GOLDEN_FINANCIAL_FINGERPRINT_INVALID:{trial_id}")
        financial_fingerprints[str(trial_id)] = computed
        n_closed += int(getattr(result, "final_close_date", None) is not None)
        draw_count = int(getattr(result, "rng_draw_count", 0))
        checksum = int(getattr(result, "rng_checksum", 0))
        rng_fp = str(getattr(result, "rng_checksum_fingerprint_sha256", ""))
        rng_records.append({
            "trial_id": trial_id,
            "rng_checksum": checksum,
            "rng_draw_count": draw_count,
            "rng_checksum_fingerprint_sha256": rng_fp,
        })
        # This digest covers the complete TrialResult object; it is kept separate
        # from the financial-only Gate A fingerprint and the RNG audit fields.
        result_sha_records.append({
            "trial_id": trial_id,
            "complete_trial_result_sha256": sha256_bytes(canonical_json(asdict(result))),
        })

    map_sha = financial_map_sha256(scenario, financial_fingerprints)
    rng_sha = rng_audit_sha256(rng_records)
    result_sha = sha256_bytes(canonical_json(result_sha_records))
    payload = {
        "schema_version": "s6-independent-golden-scenario-v1",
        "status": "INDEPENDENT_GOLDEN_CANDIDATE_NOT_APPROVED",
        "golden_type": "FRESH_FULL_RUN_FINANCIAL_TRIAL_FINGERPRINTS",
        "independent_execution": True,
        "production_result_artifacts_read": False,
        "source_sha": source_sha,
        "cohort_id": PINNED_COHORT_ID,
        "master_seed": constants.MASTER_SEED,
        "model_schema_version": "v2.3",
        "tested_sha": provenance["tested_sha"],
        "model_source_blobs": {k[5:]: v for k, v in provenance.items() if k.startswith("blob:")},
        "run_id": os.environ.get("GITHUB_RUN_ID", "LOCAL"),
        "run_attempt": int(os.environ.get("GITHUB_RUN_ATTEMPT", "1")),
        "scenario_id": scenario,
        "trial_id_start": 1,
        "trial_id_end": trial_count,
        "trial_count": trial_count,
        "n_closed": n_closed,
        "n_censored": trial_count - n_closed,
        "n_unique_financial_fingerprints": len(set(financial_fingerprints.values())),
        "financial_trial_fingerprint_map_sha256": map_sha,
        "rng_audit_map_sha256": rng_sha,
        "complete_trial_result_audit_sha256": result_sha,
        "financial_trial_fingerprints": financial_fingerprints,
        "rng_audit_records": rng_records,
        "complete_trial_result_sha256_records": result_sha_records,
        "started_at_utc": started_at,
        "finished_at_utc": now_utc(),
        "elapsed_seconds": time.monotonic() - started,
        "python_version": platform.python_version(),
        "gate_a_approval": "NOT_EVALUATED_REQUIRES_SEPARATE_REVIEW",
    }
    path = output_dir / scenario / SCENARIO_FILENAME
    file_sha = write_json(path, payload)
    return {
        "status": "EXECUTED_INDEPENDENT_GOLDEN_CANDIDATE",
        "scenario_id": scenario,
        "trial_count": trial_count,
        "n_closed": n_closed,
        "n_censored": trial_count - n_closed,
        "financial_trial_fingerprint_map_sha256": map_sha,
        "rng_audit_map_sha256": rng_sha,
        "complete_trial_result_audit_sha256": result_sha,
        "file": str(path),
        "file_sha256": file_sha,
    }


def aggregate(input_dir: Path, output_dir: Path, source_sha: str) -> dict[str, Any]:
    provenance = require_source_identity(source_sha)
    files = sorted(input_dir.rglob(SCENARIO_FILENAME))
    by_scenario: dict[str, tuple[dict[str, Any], Path]] = {}
    for path in files:
        doc = json.loads(path.read_text(encoding="utf-8"))
        scenario = str(doc.get("scenario_id", ""))
        if scenario not in EXPECTED_SCENARIOS or scenario in by_scenario:
            raise RuntimeError(f"S6_GOLDEN_DUPLICATE_OR_UNEXPECTED_SCENARIO:{scenario}")
        if doc.get("status") != "INDEPENDENT_GOLDEN_CANDIDATE_NOT_APPROVED":
            raise RuntimeError(f"S6_GOLDEN_SCENARIO_STATUS_INVALID:{scenario}")
        if (
            doc.get("source_sha") != source_sha
            or doc.get("cohort_id") != PINNED_COHORT_ID
            or doc.get("master_seed") != PINNED_MASTER_SEED
            or doc.get("trial_id_start") != 1
            or doc.get("trial_id_end") != PINNED_TRIAL_COUNT
            or doc.get("trial_count") != PINNED_TRIAL_COUNT
            or doc.get("production_result_artifacts_read") is not False
        ):
            raise RuntimeError(f"S6_GOLDEN_SCENARIO_PROVENANCE_MISMATCH:{scenario}")
        fingerprints = doc.get("financial_trial_fingerprints", {})
        if set(fingerprints) != {str(tid) for tid in range(1, PINNED_TRIAL_COUNT + 1)}:
            raise RuntimeError(f"S6_GOLDEN_SCENARIO_TRIAL_GAP_OR_OVERLAP:{scenario}")
        if financial_map_sha256(scenario, fingerprints) != doc.get("financial_trial_fingerprint_map_sha256"):
            raise RuntimeError(f"S6_GOLDEN_SCENARIO_FINANCIAL_MAP_HASH_MISMATCH:{scenario}")
        rng_records = doc.get("rng_audit_records", [])
        if len(rng_records) != PINNED_TRIAL_COUNT:
            raise RuntimeError(f"S6_GOLDEN_SCENARIO_RNG_COVERAGE_MISMATCH:{scenario}")
        if rng_audit_sha256(rng_records) != doc.get("rng_audit_map_sha256"):
            raise RuntimeError(f"S6_GOLDEN_SCENARIO_RNG_MAP_HASH_MISMATCH:{scenario}")
        by_scenario[scenario] = (doc, path)

    if set(by_scenario) != set(EXPECTED_SCENARIOS):
        missing = sorted(set(EXPECTED_SCENARIOS) - set(by_scenario))
        raise RuntimeError(f"S6_GOLDEN_SCENARIO_SET_INCOMPLETE:{missing}")
    combined_financial_map: dict[str, Any] = {}
    scenario_manifest: list[dict[str, Any]] = []
    for scenario in EXPECTED_SCENARIOS:
        doc, path = by_scenario[scenario]
        combined_financial_map[scenario] = {
            "trial_fingerprints": doc["financial_trial_fingerprints"],
            "trial_id_start": doc["trial_id_start"],
            "trial_id_end": doc["trial_id_end"],
            "trial_count": doc["trial_count"],
            "financial_trial_fingerprint_map_sha256": doc["financial_trial_fingerprint_map_sha256"],
            "rng_audit_map_sha256": doc["rng_audit_map_sha256"],
            "complete_trial_result_audit_sha256": doc["complete_trial_result_audit_sha256"],
        }
        scenario_manifest.append({
            "scenario_id": scenario,
            "file": path.relative_to(input_dir).as_posix(),
            "file_sha256": sha256_file(path),
            "financial_trial_fingerprint_map_sha256": doc["financial_trial_fingerprint_map_sha256"],
            "rng_audit_map_sha256": doc["rng_audit_map_sha256"],
            "complete_trial_result_audit_sha256": doc["complete_trial_result_audit_sha256"],
            "trial_count": doc["trial_count"],
            "n_closed": doc["n_closed"],
            "n_censored": doc["n_censored"],
        })

    map_payload = {
        "schema_version": "s6-independent-golden-map-v1",
        "status": "INDEPENDENT_GOLDEN_CANDIDATE_NOT_APPROVED",
        "golden_type": "STOCHASTIC_FINANCIAL_TRIAL_FINGERPRINT_MAP",
        "source_sha": source_sha,
        "cohort_id": PINNED_COHORT_ID,
        "master_seed": PINNED_MASTER_SEED,
        "model_schema_version": "v2.3",
        "tested_sha": provenance["tested_sha"],
        "trial_id_start": 1,
        "trial_id_end": PINNED_TRIAL_COUNT,
        "trial_count_per_scenario": PINNED_TRIAL_COUNT,
        "scenario_count": len(EXPECTED_SCENARIOS),
        "total_trial_fingerprints": len(EXPECTED_SCENARIOS) * PINNED_TRIAL_COUNT,
        "independent_execution": True,
        "production_result_artifacts_read": False,
        "scenarios": combined_financial_map,
    }
    map_path = output_dir / "independent_golden_fingerprints.json"
    map_sha = write_json(map_path, map_payload)
    manifest = {
        "schema_version": "s6-independent-golden-manifest-v1",
        "status": "INDEPENDENT_GOLDEN_CANDIDATE_NOT_APPROVED",
        "source_sha": source_sha,
        "cohort_id": PINNED_COHORT_ID,
        "master_seed": PINNED_MASTER_SEED,
        "model_schema_version": "v2.3",
        "tested_sha": provenance["tested_sha"],
        "run_id": os.environ.get("GITHUB_RUN_ID", "LOCAL"),
        "run_attempt": int(os.environ.get("GITHUB_RUN_ATTEMPT", "1")),
        "scenario_count": len(scenario_manifest),
        "scenario_ids": list(EXPECTED_SCENARIOS),
        "trial_count_per_scenario": PINNED_TRIAL_COUNT,
        "total_trial_fingerprints": sum(x["trial_count"] for x in scenario_manifest),
        "total_n_closed": sum(x["n_closed"] for x in scenario_manifest),
        "total_n_censored": sum(x["n_censored"] for x in scenario_manifest),
        "independent_execution": True,
        "production_result_artifacts_read": False,
        "scenario_manifest": scenario_manifest,
        "map_file": map_path.name,
        "map_file_sha256": map_sha,
        "combined_financial_trial_fingerprint_map_sha256": sha256_bytes(
            ("\n".join(
                f"{scenario}|{trial_id}|{combined_financial_map[scenario]['trial_fingerprints'][str(trial_id)]}"
                for scenario in EXPECTED_SCENARIOS
                for trial_id in range(1, PINNED_TRIAL_COUNT + 1)
            ) + "\n").encode("utf-8")
        ),
        "gate_a_approval": "NOT_EVALUATED_REQUIRES_SEPARATE_REVIEW",
        "created_at_utc": now_utc(),
        "python_version": platform.python_version(),
        "model_source_blobs": {k[5:]: v for k, v in provenance.items() if k.startswith("blob:")},
    }
    manifest_path = output_dir / "independent_golden_manifest.json"
    manifest_sha = write_json(manifest_path, manifest)
    return {
        "status": "EXECUTED_INDEPENDENT_GOLDEN_AGGREGATION_NOT_APPROVED",
        "scenario_count": len(scenario_manifest),
        "trial_count_per_scenario": PINNED_TRIAL_COUNT,
        "total_trial_fingerprints": manifest["total_trial_fingerprints"],
        "total_n_closed": manifest["total_n_closed"],
        "total_n_censored": manifest["total_n_censored"],
        "map_file": map_path.name,
        "map_file_sha256": map_sha,
        "manifest_file": manifest_path.name,
        "manifest_file_sha256": manifest_sha,
        "gate_a_approval": manifest["gate_a_approval"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("verify-source", "scenario", "aggregate"), required=True)
    parser.add_argument("--source-sha", default=PINNED_SOURCE_SHA)
    parser.add_argument("--scenario")
    parser.add_argument("--trial-count", type=int, default=PINNED_TRIAL_COUNT)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--input-dir", default="results/s6-independent-golden-input")
    parser.add_argument("--output-dir", default="results/s6-independent-golden")
    args = parser.parse_args()

    if args.mode == "verify-source":
        provenance = require_source_identity(args.source_sha)
        print(json.dumps({
            "status": "S6_GOLDEN_SOURCE_LOCK_PASS",
            "source_sha": args.source_sha,
            "cohort_id": PINNED_COHORT_ID,
            "master_seed": constants.MASTER_SEED,
            "model_source_blobs": {k[5:]: v for k, v in provenance.items() if k.startswith("blob:")},
        }, ensure_ascii=False, sort_keys=True))
    elif args.mode == "scenario":
        if not args.scenario:
            parser.error("--scenario is required in scenario mode")
        print(json.dumps(
            run_scenario(args.scenario, args.source_sha, args.trial_count, args.workers, Path(args.output_dir)),
            ensure_ascii=False, sort_keys=True,
        ))
    else:
        print(json.dumps(
            aggregate(Path(args.input_dir), Path(args.output_dir), args.source_sha),
            ensure_ascii=False, sort_keys=True,
        ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
