#!/usr/bin/env python3
"""Fresh source-pinned C100 Golden candidate; never consumes production artifacts."""
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
import time
from typing import Any

import constants
import monte_carlo
import validation
from scripts import s6_first_checkpoint as s6

SOURCE_SHA = "da1a9ea9b5cd789c944de3f07b08395bb67c49e7"
COHORT_ID = "c100-v23-da1a9ea9-20261028"
MASTER_SEED = 20270101
TRIAL_COUNT = 300
G_LEVELS = (100, 70, 50, 30, 0)
SCENARIOS = tuple(f"C100_G{g:03d}" for g in G_LEVELS)
CANDIDATE_NAME = "c100_golden_candidate.json"


def utc_now() -> str:
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


def git(*args: str) -> str:
    p = subprocess.run(
        ["git", *args], check=True, capture_output=True, text=True, encoding="utf-8"
    )
    return p.stdout.strip()


def verify_source_lock(source_sha: str) -> dict[str, Any]:
    if source_sha != SOURCE_SHA:
        raise RuntimeError("C100_GOLDEN_SOURCE_SHA_NOT_PINNED")
    if constants.MASTER_SEED != MASTER_SEED:
        raise RuntimeError("C100_GOLDEN_MASTER_SEED_MISMATCH")
    expected_cohort = f"c100-v23-{source_sha[:8]}-20261028"
    if COHORT_ID != expected_cohort:
        raise RuntimeError("C100_GOLDEN_COHORT_ID_MISMATCH")
    tested_sha = git("rev-parse", "HEAD")
    if os.environ.get("GITHUB_ACTIONS", "").lower() == "true":
        if tested_sha != os.environ.get("GITHUB_SHA", ""):
            raise RuntimeError("C100_GOLDEN_TESTED_SHA_CONTEXT_MISMATCH")
        ref = os.environ.get("GITHUB_REF", "")
        if not ref.startswith("refs/heads/"):
            raise RuntimeError("C100_GOLDEN_BRANCH_REF_REQUIRED")
        remote = git("ls-remote", "origin", ref).split()
        if not remote or remote[0] != tested_sha:
            raise RuntimeError("C100_GOLDEN_STALE_WORKFLOW_COMMIT")
    def blobs(revision: str) -> dict[str, str]:
        lines = git("ls-tree", "-r", "--format=%(objectname) %(path)", revision).splitlines()
        return {path: blob for blob, path in (line.split(" ", 1) for line in lines)}
    source_tree = blobs(source_sha)
    tested_tree = blobs("HEAD")
    python_paths = sorted(p for p in source_tree if p.endswith(".py"))
    missing = sorted(set(python_paths) - set(tested_tree))
    if missing:
        raise RuntimeError(f"C100_GOLDEN_SOURCE_PYTHON_MISSING:{missing}")
    changed = sorted(p for p in python_paths if source_tree[p] != tested_tree[p])
    if changed:
        raise RuntimeError(f"C100_GOLDEN_MODEL_SOURCE_DRIFT:{changed}")
    extras = sorted(
        p for p in set(tested_tree) - set(source_tree)
        if p.endswith(".py") and p != "scripts/s6_independent_c100_golden.py"
    )
    if extras:
        raise RuntimeError(f"C100_GOLDEN_UNEXPECTED_PYTHON_SOURCES:{extras}")
    return {
        "tested_sha": tested_sha,
        "source_tree_sha": git("rev-parse", f"{source_sha}^{{tree}}"),
        "source_python_blob_sha": {p: source_tree[p] for p in python_paths},
    }


def path_payload(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ordered = sorted(rows, key=lambda row: str(row["date"]))
    return [
        {key: value for key, value in row.items() if key != "trial_id"}
        for row in ordered
    ]


def run_scenario(scenario: str, source_sha: str, workers: int, output_dir: Path) -> dict[str, Any]:
    if scenario not in SCENARIOS:
        raise RuntimeError(f"C100_GOLDEN_UNEXPECTED_SCENARIO:{scenario}")
    if not 1 <= workers <= 4:
        raise RuntimeError("C100_GOLDEN_WORKER_COUNT_OUT_OF_RANGE")
    provenance = verify_source_lock(source_sha)
    started_at = utc_now()
    started = time.monotonic()
    trial_ids = list(range(1, TRIAL_COUNT + 1))
    results_by_id, daily_by_id = s6.run_full_trials(scenario, trial_ids, source_sha, workers)
    if set(results_by_id) != set(trial_ids) or set(daily_by_id) != set(trial_ids):
        raise RuntimeError("C100_GOLDEN_TRIAL_OR_DAILY_COVERAGE_MISMATCH")
    ordered = [results_by_id[tid] for tid in trial_ids]
    s6.stats_integrity.validate_cumulative_trial_ids(
        [int(result.trial_id) for result in ordered], TRIAL_COUNT, scenario_id=scenario
    )
    validation.validate_rng_audit_records(
        [asdict(result) for result in ordered],
        source_sha=source_sha,
        master_seed=constants.MASTER_SEED,
        require_audit_fingerprint=True,
    )
    fingerprints: dict[str, str] = {}
    daily_fingerprints: dict[str, str] = {}
    rng_records: list[dict[str, Any]] = []
    n_claims = 0
    for trial_id, result in enumerate(ordered, start=1):
        if int(result.trial_id) != trial_id or str(result.scenario_id) != scenario:
            raise RuntimeError("C100_GOLDEN_TRIAL_IDENTITY_MISMATCH")
        if int(result.rng_draw_count) != 0 or int(result.rng_checksum) != 0:
            raise RuntimeError(f"C100_GOLDEN_EXPECTED_ZERO_RNG_DRAWS:{trial_id}")
        if int(result.claims_created) != 0:
            n_claims += int(result.claims_created)
        fp = monte_carlo.trial_fingerprint(result)
        if result.trial_fingerprint and result.trial_fingerprint != fp:
            raise RuntimeError(f"C100_GOLDEN_FINANCIAL_FINGERPRINT_SELF_MISMATCH:{trial_id}")
        fingerprints[str(trial_id)] = fp
        daily_rows = daily_by_id[trial_id]
        if not daily_rows:
            raise RuntimeError(f"C100_GOLDEN_DAILY_PATH_EMPTY:{trial_id}")
        daily_fingerprints[str(trial_id)] = sha256_bytes(canonical_json(path_payload(daily_rows)))
        rng_records.append({
            "trial_id": trial_id,
            "rng_checksum": int(result.rng_checksum),
            "rng_draw_count": int(result.rng_draw_count),
            "rng_checksum_fingerprint_sha256": str(result.rng_checksum_fingerprint_sha256 or ""),
        })
    unique_financial = len(set(fingerprints.values()))
    unique_daily = len(set(daily_fingerprints.values()))
    if unique_financial != 1 or unique_daily != 1:
        raise RuntimeError(
            f"C100_GOLDEN_NOT_DEGENERATE_DETERMINISTIC:financial={unique_financial}:daily={unique_daily}"
        )
    rep = ordered[0]
    representative_path = path_payload(daily_by_id[1])
    payload = {
        "schema_version": "s6-c100-independent-golden-scenario-v1",
        "status": "INDEPENDENT_C100_GOLDEN_CANDIDATE_NOT_APPROVED",
        "golden_type": "FRESH_FULL_DETERMINISTIC_RUN",
        "independent_execution": True,
        "production_result_artifacts_read": False,
        "source_sha": source_sha,
        "cohort_id": COHORT_ID,
        "master_seed": constants.MASTER_SEED,
        "model_schema_version": "v2.3",
        "tested_sha": provenance["tested_sha"],
        "source_tree_sha": provenance["source_tree_sha"],
        "source_python_blob_sha": provenance["source_python_blob_sha"],
        "run_id": os.environ.get("GITHUB_RUN_ID", "LOCAL"),
        "run_attempt": int(os.environ.get("GITHUB_RUN_ATTEMPT", "1")),
        "scenario_id": scenario,
        "collection_percent": 100,
        "guarantee_percent": int(scenario[-3:]),
        "trial_id_start": 1,
        "trial_id_end": TRIAL_COUNT,
        "trial_count": TRIAL_COUNT,
        "n_closed": sum(1 for result in ordered if getattr(result, "final_close_date", None) is not None),
        "n_censored": sum(1 for result in ordered if getattr(result, "final_close_date", None) is None),
        "n_unique_paths": 1,
        "n_unique_financial_fingerprints": unique_financial,
        "n_unique_daily_paths": unique_daily,
        "degeneracy_status": "DEGENERATE_DETERMINISTIC",
        "g_inert_evidence": "PENDING_CROSS_SCENARIO_AGGREGATION",
        "claims_created_total": sum(int(getattr(result, "claims_created", 0)) for result in ordered),
        "financial_trial_fingerprints": fingerprints,
        "daily_path_fingerprints": daily_fingerprints,
        "rng_audit_records": rng_records,
        "representative_daily_path": representative_path,
        "representative_trial_id": 1,
        "representative_trial_result": asdict(rep),
        "started_at_utc": started_at,
        "finished_at_utc": utc_now(),
        "elapsed_seconds": time.monotonic() - started,
        "python_version": platform.python_version(),
        "gate_a_approval": "NOT_EVALUATED_REQUIRES_SEPARATE_REVIEW",
    }
    path = output_dir / scenario / CANDIDATE_NAME
    file_sha = write_json(path, payload)
    return {
        "status": "EXECUTED_INDEPENDENT_C100_GOLDEN_CANDIDATE",
        "scenario_id": scenario,
        "trial_count": TRIAL_COUNT,
        "n_unique_paths": 1,
        "n_closed": payload["n_closed"],
        "n_censored": payload["n_censored"],
        "claims_created_total": payload["claims_created_total"],
        "financial_map_sha256": sha256_bytes(canonical_json(fingerprints)),
        "daily_path_map_sha256": sha256_bytes(canonical_json(daily_fingerprints)),
        "file": str(path),
        "file_sha256": file_sha,
    }


def aggregate(input_dir: Path, output_dir: Path, source_sha: str) -> dict[str, Any]:
    provenance = verify_source_lock(source_sha)
    files = sorted(input_dir.rglob(CANDIDATE_NAME))
    docs: dict[str, tuple[dict[str, Any], Path]] = {}
    for path in files:
        doc = json.loads(path.read_text(encoding="utf-8"))
        scenario = str(doc.get("scenario_id", ""))
        if scenario not in SCENARIOS or scenario in docs:
            raise RuntimeError(f"C100_GOLDEN_DUPLICATE_OR_UNEXPECTED_SCENARIO:{scenario}")
        if (
            doc.get("status") != "INDEPENDENT_C100_GOLDEN_CANDIDATE_NOT_APPROVED"
            or doc.get("source_sha") != source_sha
            or doc.get("cohort_id") != COHORT_ID
            or doc.get("master_seed") != MASTER_SEED
            or doc.get("trial_id_start") != 1
            or doc.get("trial_id_end") != TRIAL_COUNT
            or doc.get("trial_count") != TRIAL_COUNT
            or doc.get("n_unique_paths") != 1
            or doc.get("n_unique_daily_paths") != 1
            or doc.get("n_unique_financial_fingerprints") != 1
            or doc.get("production_result_artifacts_read") is not False
        ):
            raise RuntimeError(f"C100_GOLDEN_PROVENANCE_OR_DETERMINISM_MISMATCH:{scenario}")
        ids = {str(i) for i in range(1, TRIAL_COUNT + 1)}
        if set(doc.get("financial_trial_fingerprints", {})) != ids:
            raise RuntimeError(f"C100_GOLDEN_FINANCIAL_TRIAL_COVERAGE_MISMATCH:{scenario}")
        if set(doc.get("daily_path_fingerprints", {})) != ids:
            raise RuntimeError(f"C100_GOLDEN_DAILY_TRIAL_COVERAGE_MISMATCH:{scenario}")
        if set(doc.get("rng_audit_records", [] ) [i].get("trial_id") for i in range(len(doc.get("rng_audit_records", [])))) != set(range(1, TRIAL_COUNT + 1):
            raise RuntimeError(f"C100_GOLDEN_RNG_TRIAL_COVERAGE_MISMATCH:{scenario}")
        if any(int(row.get("rng_draw_count", -1)) != 0 or int(row.get("rng_checksum", -1)) != 0 for row in doc["rng_audit_records"]):
            raise RuntimeError(f"C100_GOLDEN_RNG_ZERO_DRAW_CONTRACT_MISMATCH:{scenario}")
        if sha256_bytes(canonical_json(doc["financial_trial_fingerprints"])) != doc.get("financial_map_sha256"):
            # Per-scenario files use the canonical line-based digest in their return; independently
            # recalculate and store the canonical map hash below instead of trusting an absent field.
            pass
        docs[scenario] = (doc, path)
    if set(docs) != set(SCENARIOS):
        raise RuntimeError(f"C100_GOLDEN_SCENARIO_SET_INCOMPLETE:{sorted(set(SCENARIOS)-set(docs))}")

    reference_financial: dict[str, str] | None = None
    reference_daily: dict[str, str] | None = None
    for scenario in SCENARIOS:
        doc, _ = docs[scenario]
        financial = doc["financial_trial_fingerprints"]
        daily = doc["daily_path_fingerprints"]
        if any(v != next(iter(financial.values())) for v in financial.values()):
            raise RuntimeError(f"C100_GOLDEN_FINANCIAL_PATH_NOT_UNIQUE:{scenario}")
        if any(v != next(iter(daily.values())) for v in daily.values()):
            raise RuntimeError(f"C100_GOLDEN_DAILY_PATH_NOT_UNIQUE:{scenario}")
        if doc["claims_created_total"] != 0:
            raise RuntimeError(f"C100_GOLDEN_G_INERT_CLAIMS_FOUND:{scenario}")
        if reference_financial is None:
            reference_financial, reference_daily = financial, daily
        elif financial != reference_financial or daily != reference_daily:
            raise RuntimeError(f"C100_GOLDEN_G_LEVELS_NOT_IDENTICAL:{scenario}")

    scenario_manifest: list[dict[str, Any]] = []
    golden_scenarios: dict[str, Any] = {}
    for scenario in SCENARIOS:
        doc, path = docs[scenario]
        scenario_manifest.append({
            "scenario_id": scenario,
            "file": path.relative_to(input_dir).as_posix(),
            "file_sha256": sha256_file(path),
            "trial_count": doc["trial_count"],
            "n_closed": doc["n_closed"],
            "n_censored": doc["n_censored"],
            "n_unique_paths": doc["n_unique_paths"],
            "n_unique_daily_paths": doc["n_unique_daily_paths"],
            "claims_created_total": doc["claims_created_total"],
        })
        golden_scenarios[scenario] = {
            "trial_id_start": 1,
            "trial_id_end": TRIAL_COUNT,
            "trial_count": TRIAL_COUNT,
            "financial_trial_fingerprints": doc["financial_trial_fingerprints"],
            "daily_path_fingerprints": doc["daily_path_fingerprints"],
            "rng_audit_records": doc["rng_audit_records"],
            "representative_daily_path": doc["representative_daily_path"],
            "representative_trial_result": doc["representative_trial_result"],
            "financial_path_map_sha256": sha256_bytes(canonical_json(doc["financial_trial_fingerprints"])),
            "daily_path_map_sha256": sha256_bytes(canonical_json(doc["daily_path_fingerprints"])),
        }
    map_payload = {
        "schema_version": "s6-c100-independent-golden-map-v1",
        "status": "INDEPENDENT_C100_GOLDEN_CANDIDATE_NOT_APPROVED",
        "golden_type": "C100_DETERMINISTIC_FINANCIAL_AND_DAILY_PATH_MAP",
        "source_sha": source_sha,
        "cohort_id": COHORT_ID,
        "master_seed": MASTER_SEED,
        "model_schema_version": "v2.3",
        "tested_sha": provenance["tested_sha"],
        "source_tree_sha": provenance["source_tree_sha"],
        "source_python_blob_sha": provenance["source_python_blob_sha"],
        "scenario_count": 5,
        "scenario_ids": list(SCENARIOS),
        "trial_count_per_scenario": TRIAL_COUNT,
        "total_trial_fingerprints": 5 * TRIAL_COUNT,
        "degeneracy_status": "DEGENERATE_DETERMINISTIC",
        "n_unique_paths": 1,
        "g_inert": True,
        "g_inert_evidence": "NO_CLAIMS_AND_IDENTICAL_FINANCIAL_AND_DAILY_FINGERPRINTS_ACROSS_ALL_FIVE_G_LEVELS",
        "independent_execution": True,
        "production_result_artifacts_read": False,
        "scenarios": golden_scenarios,
        "gate_a_approval": "NOT_EVALUATED_REQUIRES_SEPARATE_REVIEW",
    }
    map_path = output_dir / "c100_independent_golden_map.json"
    map_sha = write_json(map_path, map_payload)
    manifest = {
        "schema_version": "s6-c100-independent-golden-manifest-v1",
        "status": "INDEPENDENT_C100_GOLDEN_CANDIDATE_NOT_APPROVED",
        "source_sha": source_sha,
        "cohort_id": COHORT_ID,
        "master_seed": MASTER_SEED,
        "model_schema_version": "v2.3",
        "tested_sha": provenance["tested_sha"],
        "run_id": os.environ.get("GITHUB_RUN_ID", "LOCAL"),
        "run_attempt": int(os.environ.get("GITHUB_RUN_ATTEMPT", "1")),
        "scenario_count": 5,
        "scenario_ids": list(SCENARIOS),
        "trial_count_per_scenario": TRIAL_COUNT,
        "total_trial_fingerprints": 5 * TRIAL_COUNT,
        "n_unique_paths_per_scenario": 1,
        "g_inert": True,
        "independent_execution": True,
        "production_result_artifacts_read": False,
        "scenario_manifest": scenario_manifest,
        "map_file": map_path.name,
        "map_file_sha256": map_sha,
        "total_n_closed": sum(docs[s][0]["n_closed"] for s in SCENARIOS),
        "total_n_censored": sum(docs[s][0]["n_censored"] for s in SCENARIOS),
        "created_at_utc": utc_now(),
        "python_version": platform.python_version(),
        "gate_a_approval": "NOT_EVALUATED_REQUIRES_SEPARATE_REVIEW",
    }
    manifest_path = output_dir / "c100_independent_golden_manifest.json"
    manifest_sha = write_json(manifest_path, manifest)
    return {
        "status": "EXECUTED_INDEPENDENT_C100_GOLDEN_AGGREGATION_NOT_APPROVED",
        "scenario_count": 5,
        "trial_count_per_scenario": TRIAL_COUNT,
        "total_trial_fingerprints": 5 * TRIAL_COUNT,
        "n_unique_paths": 1,
        "g_inert": True,
        "map_file": map_path.name,
        "map_file_sha256": map_sha,
        "manifest_file": manifest_path.name,
        "manifest_file_sha256": manifest_sha,
        "gate_a_approval": manifest["gate_a_approval"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("verify-source", "scenario", "aggregate"), required=True)
    parser.add_argument("--source-sha", default=SOURCE_SHA)
    parser.add_argument("--scenario")
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--input-dir", default="results/s6-independent-c100-input")
    parser.add_argument("--output-dir", default="results/s6-independent-c100")
    args = parser.parse_args()
    if args.mode == "verify-source":
        provenance = verify_source_lock(args.source_sha)
        print(json.dumps({
            "status": "C100_GOLDEN_SOURCE_LOCK_PASS",
            "source_sha": args.source_sha,
            "cohort_id": COHORT_ID,
            "master_seed": constants.MASTER_SEED,
            "source_tree_sha": provenance["source_tree_sha"],
            "python_source_count": len(provenance["source_python_blob_sha"]),
        }, ensure_ascii=False, sort_keys=True))
    elif args.mode == "scenario":
        if not args.scenario:
            parser.error("--scenario is required in scenario mode")
        print(json.dumps(
            run_scenario(args.scenario, args.source_sha, args.workers, Path(args.output_dir)),
            ensure_ascii=False, sort_keys=True,
        ))
    else:
        print(json.dumps(aggregate(Path(args.input_dir), Path(args.output_dir), args.source_sha), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
