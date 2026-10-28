#!/usr/bin/env python3
"""Independently attest a source-locked stochastic Golden candidate.

This command runs in a separate verifier workflow, never in the production trial
workflow. It validates the candidate bundle, all per-scenario files, source-tree
identity, full trial coverage, and that Golden/production runs are distinct.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import shutil
import subprocess
from typing import Any

from scripts import s6_golden_gate


SOURCE_SHA = "da1a9ea9b5cd789c944de3f07b08395bb67c49e7"
COHORT_ID = "s6-v23-da1a9ea9"
MASTER_SEED = 20270101
SCHEMA_VERSION = "s6-independent-golden-map-v1"
APPROVAL_SCHEMA_VERSION = "s6-golden-approval-manifest-v1"
ALLOWED_SOURCE_ADDITIONS = {
    ".github/workflows/s6-independent-golden-candidate.yml",
    "scripts/s6_independent_golden_candidate.py",
}


class GoldenApprovalError(RuntimeError):
    pass


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


def tree_blobs(revision: str) -> dict[str, str]:
    try:
        git("cat-file", "-e", revision + "^{commit}")
    except subprocess.CalledProcessError:
        git("fetch", "--no-tags", "origin", revision)
    entries = git("ls-tree", "-r", "--format=%(objectname) %(path)", revision).splitlines()
    return {path: blob for blob, path in (entry.split(" ", 1) for entry in entries)}


def verify_full_source_tree(source_sha: str, tested_sha: str, recorded_python_blobs: dict[str, str]) -> dict[str, Any]:
    if source_sha != SOURCE_SHA:
        raise GoldenApprovalError("GOLDEN_SOURCE_SHA_NOT_OWNER_PINNED")
    source_tree = tree_blobs(source_sha)
    tested_tree = tree_blobs(tested_sha)
    missing_or_changed = sorted(
        path for path, blob in source_tree.items() if tested_tree.get(path) != blob
    )
    if missing_or_changed:
        raise GoldenApprovalError(f"GOLDEN_SOURCE_TREE_DRIFT:{missing_or_changed[:30]}")
    additions = sorted(set(tested_tree) - set(source_tree))
    unexpected = sorted(set(additions) - ALLOWED_SOURCE_ADDITIONS)
    if unexpected:
        raise GoldenApprovalError(f"GOLDEN_UNEXPECTED_SOURCE_TREE_ADDITIONS:{unexpected}")
    source_python = {path: blob for path, blob in source_tree.items() if path.endswith(".py")}
    if recorded_python_blobs != source_python:
        raise GoldenApprovalError("GOLDEN_RECORDED_SOURCE_BLOBS_MISMATCH")
    return {
        "source_tree_sha": git("rev-parse", f"{source_sha}^{{tree}}"),
        "tested_tree_sha": git("rev-parse", f"{tested_sha}^{{tree}}"),
        "source_file_count": len(source_tree),
        "source_python_file_count": len(source_python),
        "tooling_only_additions": additions,
        "source_tree_sha_verified": True,
    }


def locate_one(root: Path, filename: str) -> Path:
    matches = sorted(root.rglob(filename))
    if len(matches) != 1:
        raise GoldenApprovalError(f"GOLDEN_FILE_COUNT_MISMATCH:{filename}:{len(matches)}")
    return matches[0]


def approve(
    aggregate_input: Path,
    scenario_input: Path,
    production_run_id: str,
    output_dir: Path,
) -> dict[str, Any]:
    map_path = locate_one(aggregate_input, "independent_golden_fingerprints.json")
    manifest_path = locate_one(aggregate_input, "independent_golden_manifest.json")
    golden = json.loads(map_path.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    map_sha = sha256_file(map_path)
    manifest_sha = sha256_file(manifest_path)
    golden_run_id = str(golden.get("run_id", manifest.get("run_id", "")))
    if not golden_run_id or golden_run_id != str(manifest.get("run_id", "")):
        raise GoldenApprovalError("GOLDEN_RUN_ID_MANIFEST_MISMATCH")
    if golden_run_id == str(production_run_id):
        raise GoldenApprovalError("GOLDEN_PRODUCTION_SELF_REFERENCE_FORBIDDEN")
    if (
        golden.get("schema_version") != SCHEMA_VERSION
        or golden.get("status") != "INDEPENDENT_GOLDEN_CANDIDATE_NOT_APPROVED"
        or golden.get("golden_type") != "STOCHASTIC_FINANCIAL_TRIAL_FINGERPRINT_MAP"
        or golden.get("source_sha") != SOURCE_SHA
        or golden.get("cohort_id") != COHORT_ID
        or golden.get("master_seed") != MASTER_SEED
        or golden.get("model_schema_version") != "v2.3"
        or golden.get("scenario_count") != 20
        or golden.get("trial_id_start") != 1
        or golden.get("trial_id_end") != 2400
        or golden.get("trial_count_per_scenario") != 2400
        or golden.get("total_trial_fingerprints") != 48000
        or golden.get("independent_execution") is not True
        or golden.get("production_result_artifacts_read") is not False
    ):
        raise GoldenApprovalError("GOLDEN_MAP_IDENTITY_OR_SCOPE_MISMATCH")
    if (
        manifest.get("schema_version") != "s6-independent-golden-manifest-v1"
        or manifest.get("status") != "INDEPENDENT_GOLDEN_CANDIDATE_NOT_APPROVED"
        or manifest.get("source_sha") != SOURCE_SHA
        or manifest.get("cohort_id") != COHORT_ID
        or manifest.get("master_seed") != MASTER_SEED
        or manifest.get("model_schema_version") != "v2.3"
        or manifest.get("scenario_count") != 20
        or manifest.get("trial_count_per_scenario") != 2400
        or manifest.get("total_trial_fingerprints") != 48000
        or manifest.get("map_file") != map_path.name
        or manifest.get("map_file_sha256") != map_sha
        or manifest.get("independent_execution") is not True
        or manifest.get("production_result_artifacts_read") is not False
    ):
        raise GoldenApprovalError("GOLDEN_MANIFEST_IDENTITY_OR_SCOPE_MISMATCH")
    scenarios = golden.get("scenarios")
    expected_scenarios = s6_golden_gate.expected_stochastic_scenarios()
    if not isinstance(scenarios, dict) or set(scenarios) != expected_scenarios:
        raise GoldenApprovalError("GOLDEN_SCENARIO_COVERAGE_MISMATCH")
    if set(manifest.get("scenario_ids", [])) != expected_scenarios:
        raise GoldenApprovalError("GOLDEN_MANIFEST_SCENARIO_COVERAGE_MISMATCH")

    scenario_manifest = manifest.get("scenario_manifest")
    if not isinstance(scenario_manifest, list) or len(scenario_manifest) != 20:
        raise GoldenApprovalError("GOLDEN_SCENARIO_MANIFEST_COVERAGE_MISMATCH")
    scenario_manifest_by_id = {str(row.get("scenario_id")): row for row in scenario_manifest}
    if set(scenario_manifest_by_id) != expected_scenarios:
        raise GoldenApprovalError("GOLDEN_SCENARIO_MANIFEST_SCENARIO_SET_MISMATCH")

    verified_files: list[dict[str, Any]] = []
    for scenario_id in sorted(expected_scenarios):
        scenario_doc_path = scenario_input / scenario_manifest_by_id[scenario_id]["file"]
        if not scenario_doc_path.is_file():
            raise GoldenApprovalError(f"GOLDEN_SCENARIO_FILE_MISSING:{scenario_id}")
        scenario_sha = sha256_file(scenario_doc_path)
        scenario_manifest_entry = scenario_manifest_by_id[scenario_id]
        if scenario_sha != scenario_manifest_entry.get("file_sha256"):
            raise GoldenApprovalError(f"GOLDEN_SCENARIO_FILE_SHA256_MISMATCH:{scenario_id}")
        doc = json.loads(scenario_doc_path.read_text(encoding="utf-8"))
        fingerprints = doc.get("financial_trial_fingerprints", {})
        expected_ids = {str(i) for i in range(1, 2401)}
        if (
            doc.get("schema_version") != "s6-independent-golden-scenario-v1"
            or doc.get("status") != "INDEPENDENT_GOLDEN_CANDIDATE_NOT_APPROVED"
            or doc.get("source_sha") != SOURCE_SHA
            or doc.get("cohort_id") != COHORT_ID
            or doc.get("master_seed") != MASTER_SEED
            or doc.get("model_schema_version") != "v2.3"
            or doc.get("scenario_id") != scenario_id
            or doc.get("trial_id_start") != 1
            or doc.get("trial_id_end") != 2400
            or doc.get("trial_count") != 2400
            or doc.get("independent_execution") is not True
            or doc.get("production_result_artifacts_read") is not False
            or set(fingerprints) != expected_ids
        ):
            raise GoldenApprovalError(f"GOLDEN_SCENARIO_IDENTITY_OR_RANGE_MISMATCH:{scenario_id}")
        entry = scenarios[scenario_id]
        if (
            entry.get("trial_id_start") != 1
            or entry.get("trial_id_end") != 2400
            or entry.get("trial_count") != 2400
            or entry.get("trial_fingerprints") != fingerprints
        ):
            raise GoldenApprovalError(f"GOLDEN_FINGERPRINT_MAP_CONTENT_MISMATCH:{scenario_id}")
        financial_map_sha = s6_golden_gate.scenario_fingerprint_map_sha256(scenario_id, fingerprints)
        if (
            financial_map_sha != doc.get("financial_trial_fingerprint_map_sha256")
            or financial_map_sha != entry.get("financial_trial_fingerprint_map_sha256")
        ):
            raise GoldenApprovalError(f"GOLDEN_FINANCIAL_MAP_HASH_MISMATCH:{scenario_id}")
        rng_records = doc.get("rng_audit_records", [])
        if len(rng_records) != 2400:
            raise GoldenApprovalError(f"GOLDEN_RNG_AUDIT_COVERAGE_MISMATCH:{scenario_id}")
        if sha256_bytes(canonical_json(rng_records)) != doc.get("rng_audit_map_sha256") or doc.get("rng_audit_map_sha256") != entry.get("rng_audit_map_sha256"):
            raise GoldenApprovalError(f"GOLDEN_RNG_AUDIT_HASH_MISMATCH:{scenario_id}")
        result_records = doc.get("complete_trial_result_sha256_records", [])
        if len(result_records) != 2400:
            raise GoldenApprovalError(f"GOLDEN_COMPLETE_RESULT_COVERAGE_MISMATCH:{scenario_id}")
        if sha256_bytes(canonical_json(result_records)) != doc.get("complete_trial_result_audit_sha256") or doc.get("complete_trial_result_audit_sha256") != entry.get("complete_trial_result_audit_sha256"):
            raise GoldenApprovalError(f"GOLDEN_COMPLETE_RESULT_HASH_MISMATCH:{scenario_id}")
        verified_files.append({
            "scenario_id": scenario_id,
            "file": scenario_manifest_entry["file"],
            "file_sha256": scenario_sha,
            "financial_trial_fingerprint_map_sha256": financial_map_sha,
            "rng_audit_map_sha256": doc["rng_audit_map_sha256"],
            "complete_trial_result_audit_sha256": doc["complete_trial_result_audit_sha256"],
            "trial_count": 2400,
        })

    source_identity = verify_full_source_tree(
        SOURCE_SHA,
        str(golden.get("tested_sha", "")),
        golden.get("model_source_blobs", {}),
    )
    if manifest.get("model_source_blobs") != golden.get("model_source_blobs"):
        raise GoldenApprovalError("GOLDEN_MANIFEST_SOURCE_BLOBS_MISMATCH")
    if not golden.get("tested_sha"):
        raise GoldenApprovalError("GOLDEN_TESTED_SHA_MISSING")

    output_dir.mkdir(parents=True, exist_ok=True)
    out_map = output_dir / "independent_golden_fingerprints.json"
    out_manifest = output_dir / "independent_golden_manifest.json"
    shutil.copy2(map_path, out_map)
    shutil.copy2(manifest_path, out_manifest)
    approval = {
        "approval_schema_version": APPROVAL_SCHEMA_VERSION,
        "approval_status": "APPROVED_PRODUCTION_GOLDEN",
        "golden_schema_version": SCHEMA_VERSION,
        "candidate_map_sha256": map_sha,
        "independent_manifest_sha256": manifest_sha,
        "source_sha": SOURCE_SHA,
        "cohort_id": COHORT_ID,
        "master_seed": MASTER_SEED,
        "model_schema_version": "v2.3",
        "scenario_count": 20,
        "trial_count_per_scenario": 2400,
        "independent_execution": True,
        "production_result_artifacts_read": False,
        "source_tree_sha_verified": True,
        "source_tree_identity": source_identity,
        "golden_run_id": golden_run_id,
        "production_run_id": str(production_run_id),
        "scenario_ids": sorted(expected_scenarios),
        "verified_scenario_files": verified_files,
        "approval_basis": "SEPARATE_RUN_FULL_SOURCE_TREE_MATCH_COMPLETE_FINGERPRINT_COVERAGE_AND_SEPARATE_RNG_AUDIT",
        "approved_at_utc": datetime.now(timezone.utc).isoformat(),
        "verifier_run_id": __import__("os").environ.get("GITHUB_RUN_ID", "LOCAL"),
        "verifier_tested_sha": git("rev-parse", "HEAD"),
        "python_version": platform.python_version(),
    }
    approval_path = output_dir / "golden_approval.json"
    approval_sha = write_json(approval_path, approval)
    return {
        "status": "APPROVED_PRODUCTION_GOLDEN",
        "golden_run_id": golden_run_id,
        "production_run_id": str(production_run_id),
        "scenario_count": 20,
        "trial_count_per_scenario": 2400,
        "total_trial_fingerprints": 48000,
        "golden_map_sha256": map_sha,
        "independent_manifest_sha256": manifest_sha,
        "approval_manifest_sha256": approval_sha,
        "approval_file": str(approval_path),
        "source_tree_sha_verified": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--aggregate-input", required=True)
    parser.add_argument("--scenario-input", required=True)
    parser.add_argument("--production-run-id", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = approve(
        Path(args.aggregate_input),
        Path(args.scenario_input),
        args.production_run_id,
        Path(args.output_dir),
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
