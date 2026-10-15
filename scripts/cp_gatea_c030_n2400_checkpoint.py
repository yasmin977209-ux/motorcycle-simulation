#!/usr/bin/env python3
"""One-time, pinned-source C030_G030 N=2400 checkpoint.

Reference: docs/governance/DECISIONS_LOG.md, D-2026-10-15-10.
Only IDs 1201..2400 are generated. Historical N=1200 data is read-only.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from dataclasses import asdict
from pathlib import Path
from typing import Any
from datetime import datetime, timezone

REPOSITORY = "yasmin977209-ux/motorcycle-simulation"
SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
SOURCE_COMMIT = "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
MASTER_SEED = 20270101
SCENARIO = "C030_G030"
TRIAL_START = 1201
TRIAL_END = 2400
BASE_RUN_ID = 38619859394
BASE_RUN_HEAD = "f7096bcc9f910df54a60d5a4329a7ebbcd2a43ae"
BASE_RUN_BRANCH = "tmp/cp-f-delivery-20261014"
BASE_ARTIFACT_ID = 11921491181
BASE_ARTIFACT_NAME = "cp-f-source-readiness-evidence"
BASE_ARTIFACT_SHA256 = "694460ed60bf092f1b2fb431cdfae538dd0a584b1cc5d655488263d348dae29e"
EXTENSION_RUN_ID = 38662076725
EXTENSION_RUN_HEAD = "aafe5946a8a51c991471057d71f5643c46087086"
EXTENSION_ARTIFACT_ID = 11940485523
EXTENSION_ARTIFACT_NAME = "gatea-golden-c030-g1201-2400-attempt-1"
EXTENSION_ARTIFACT_SHA256 = "049af21733b59d753967f27f251cb88fec122b5e1ff4f99d77b9215114c9d3e3"
EXTENSION_MAP_SHA256 = "0c7679edfbee54797d64fc66e17116f0db617d1e0fa5f7ee21395fe98a628c65"
EXTENDED_FULL_MAP_SHA256 = "0fbe3aa87a253f9527953c77b0a122871c9344f75ece6c8a49da99b2a85c1ce1"
BASE_N1200_MAP_SHA256 = "eaf1f8f3060aac6967b064d3199c082d2a9b47027c865628986f56cbb23c1fc3"
PROVIDER_VALIDATION_RUN_ID = 38769171093
PROVIDER_VALIDATION_HEAD = "7d93948cb712f182be51d8aecc3cc2cec0f53175"
PROVIDER_VALIDATION_ARTIFACT_ID = 11989613915
PROVIDER_VALIDATION_ARTIFACT_NAME = "gatea-provider-extension-validation-attempt-1"
PROVIDER_VALIDATION_ARTIFACT_SHA256 = "e40825c67bf6322b48633d89e43d00314c996d24143ba68469ae94b5375d92d8"
GATE_A_DECISION_ID = "D-2026-10-15-10"
ARTIFACT_SCHEMA = "gateb-delivery-trial-results-v1"
CHECKPOINT_SCHEMA = "cp-gatea-c030-n2400-checkpoint-v1"
SCENARIOS = tuple(
    f"C{collection:03d}_G{recovery:03d}"
    for collection in (100, 85, 70, 50, 30)
    for recovery in (100, 70, 50, 30, 0)
)
NON_C100_SCENARIOS = tuple(s for s in SCENARIOS if not s.startswith("C100_"))

class _NoFollowRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _token() -> str:
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN_MISSING")
    return token

def _api_json(path: str) -> dict[str, Any]:
    request = urllib.request.Request(
        "https://api.github.com/" + path.lstrip("/"),
        headers={
            "Authorization": f"Bearer {_token()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "motorcycle-simulation-cp-gatea-n2400",
        },
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"GITHUB_API_RESPONSE_NOT_OBJECT:{path}")
    return data

def _verify_run(run_id: int, expected_head: str, expected_branch: str) -> dict[str, Any]:
    run = _api_json(f"repos/{REPOSITORY}/actions/runs/{run_id}")
    checks = {
        "id": int(run.get("id", -1)) == run_id,
        "head_sha": run.get("head_sha") == expected_head,
        "head_branch": run.get("head_branch") == expected_branch,
        "status": run.get("status") == "completed",
        "conclusion": run.get("conclusion") == "success",
    }
    if not all(checks.values()):
        raise RuntimeError(f"APPROVED_RUN_IDENTITY_FAIL:{run_id}:{json.dumps(checks, sort_keys=True)}")
    return {
        "run_id": run_id,
        "head_sha": run.get("head_sha"),
        "head_branch": run.get("head_branch"),
        "status": run.get("status"),
        "conclusion": run.get("conclusion"),
        "html_url": run.get("html_url"),
    }

def _artifact_metadata(artifact_id: int, *, expected_name: str, expected_digest: str,
                       expected_run_id: int) -> dict[str, Any]:
    item = _api_json(f"repos/{REPOSITORY}/actions/artifacts/{artifact_id}")
    workflow_run = item.get("workflow_run") or {}
    checks = {
        "id": int(item.get("id", -1)) == artifact_id,
        "name": item.get("name") == expected_name,
        "digest": str(item.get("digest", "")).removeprefix("sha256:") == expected_digest,
        "not_expired": item.get("expired") is False,
        "run_id": int(workflow_run.get("id", -1)) == expected_run_id,
    }
    if not all(checks.values()):
        raise RuntimeError(f"APPROVED_ARTIFACT_IDENTITY_FAIL:{artifact_id}:{json.dumps(checks, sort_keys=True)}")
    return item

def _download_artifact_zip(artifact_id: int, expected_digest: str) -> bytes:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{REPOSITORY}/actions/artifacts/{artifact_id}/zip",
        headers={
            "Authorization": f"Bearer {_token()}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "motorcycle-simulation-cp-gatea-n2400",
        },
    )
    opener = urllib.request.build_opener(_NoFollowRedirect())
    try:
        with opener.open(request, timeout=180) as response:
            raw = response.read()
    except urllib.error.HTTPError as response:
        if response.code not in (301, 302, 303, 307, 308):
            raise
        location = response.headers.get("Location")
        if not location:
            raise RuntimeError(f"ARTIFACT_REDIRECT_LOCATION_MISSING:{artifact_id}")
        with urllib.request.urlopen(
            urllib.request.Request(location, headers={"User-Agent": "motorcycle-simulation-cp-gatea-n2400"}),
            timeout=180,
        ) as storage_response:
            raw = storage_response.read()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != expected_digest:
        raise RuntimeError(f"ARTIFACT_ARCHIVE_SHA256_MISMATCH:{artifact_id}:expected={expected_digest}:actual={actual}")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        damaged = archive.testzip()
        if damaged:
            raise RuntimeError(f"ARTIFACT_ZIP_CORRUPT:{artifact_id}:{damaged}")
    return raw

def _json_member(raw_zip: bytes, member_suffix: str) -> dict[str, Any]:
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as archive:
        matches = [name for name in archive.namelist() if name == member_suffix or name.endswith("/" + member_suffix)]
        if len(matches) != 1:
            raise RuntimeError(f"ARTIFACT_MEMBER_LOOKUP_NOT_UNIQUE:{member_suffix}:{matches[:8]}")
        value = json.loads(archive.read(matches[0]).decode("utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"ARTIFACT_MEMBER_JSON_ROOT_INVALID:{member_suffix}")
    return value

def _canonical_result_sha256(value: dict[str, Any]) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()

def _ordered_map_sha256(rows_by_scenario: dict[str, dict[int, str]]) -> str:
    payload = "".join(
        f"{scenario}|{trial_id}|{rows_by_scenario[scenario][trial_id]}\n"
        for scenario in sorted(rows_by_scenario)
        for trial_id in sorted(rows_by_scenario[scenario])
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def _target_map_sha256(hashes: dict[int, str]) -> str:
    payload = "".join(f"{SCENARIO}|{trial_id}|{hashes[trial_id]}\n" for trial_id in sorted(hashes))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()

def _atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)

def _write_report(outdir: Path, report: dict[str, Any]) -> None:
    report["updated_at_utc"] = _now()
    _atomic_json(outdir / "checkpoint_report.json", report)
    print("CP_GATEA_N2400_REPORT=" + json.dumps(report, ensure_ascii=False, sort_keys=True), flush=True)

def _candidate_constants(repo_root: Path):
    path = repo_root / "constants.py"
    spec = importlib.util.spec_from_file_location("cp_gatea_candidate_constants", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("CANDIDATE_CONSTANTS_IMPORT_SPEC_MISSING")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def _load_pinned_model(source_root: Path):
    root = source_root.resolve(strict=True)
    head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()
    if head != SOURCE_COMMIT:
        raise RuntimeError(f"PINNED_SOURCE_COMMIT_MISMATCH:{head}")
    dirty = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"],
        check=True, capture_output=True, text=True
    ).stdout.strip()
    if dirty:
        raise RuntimeError("PINNED_SOURCE_WORKTREE_NOT_CLEAN")
    source_text = str(root)
    sys.path[:] = [source_text] + [
        item for item in sys.path
        if not item or Path(item).resolve() != root
    ]
    import monte_carlo
    import constants as source_constants
    origin = Path(monte_carlo.__file__).resolve(strict=True)
    if not origin.is_relative_to(root):
        raise RuntimeError(f"PINNED_MONTE_CARLO_ORIGIN_MISMATCH:{origin}")
    if int(source_constants.MASTER_SEED) != MASTER_SEED:
        raise RuntimeError(f"PINNED_SOURCE_MASTER_SEED_MISMATCH:{source_constants.MASTER_SEED}")
    return monte_carlo, source_constants, root

def _load_approved_provider():
    from scripts.golden_reference_provider import GoldenReferenceProvider
    provider = GoldenReferenceProvider()
    reference_id = provider.get_golden_reference_id()
    if not reference_id:
        raise RuntimeError(f"GOLDEN_PROVIDER_REFERENCE_ID_MISSING:{getattr(provider, 'load_error', None)}")
    if provider.source_sha != SOURCE_SHA:
        raise RuntimeError(f"GOLDEN_PROVIDER_SOURCE_SHA_MISMATCH:{provider.source_sha}")
    if int(provider.master_seed) != MASTER_SEED:
        raise RuntimeError(f"GOLDEN_PROVIDER_MASTER_SEED_MISMATCH:{provider.master_seed}")
    return provider, reference_id

def _load_and_verify_source_inputs(outdir: Path, provider) -> tuple[dict[str, Any], dict[str, Any]]:
    base_run = _verify_run(BASE_RUN_ID, BASE_RUN_HEAD, BASE_RUN_BRANCH)
    extension_run = _verify_run(EXTENSION_RUN_ID, EXTENSION_RUN_HEAD, "tmp/cp-gatea-c030-n2400-20261015")
    provider_run = _verify_run(
        PROVIDER_VALIDATION_RUN_ID,
        PROVIDER_VALIDATION_HEAD,
        "tmp/cp-gatea-c030-n2400-20261015",
    )
    provider_artifact_meta = _artifact_metadata(
        PROVIDER_VALIDATION_ARTIFACT_ID,
        expected_name=PROVIDER_VALIDATION_ARTIFACT_NAME,
        expected_digest=PROVIDER_VALIDATION_ARTIFACT_SHA256,
        expected_run_id=PROVIDER_VALIDATION_RUN_ID,
    )
    provider_artifact = _json_member(
        _download_artifact_zip(PROVIDER_VALIDATION_ARTIFACT_ID, PROVIDER_VALIDATION_ARTIFACT_SHA256),
        "provider_extension_validation.json",
    )
    if not (
        provider_artifact.get("status") == "PASS"
        and provider_artifact.get("source_sha") == SOURCE_SHA
        and provider_artifact.get("source_commit") == SOURCE_COMMIT
        and provider_artifact.get("master_seed") == MASTER_SEED
        and provider_artifact.get("extension_decision_id") == GATE_A_DECISION_ID
        and provider_artifact.get("combined_map_sha256") == EXTENDED_FULL_MAP_SHA256
        and provider_artifact.get("checkpoint_status") == "NOT_STARTED"
        and provider_artifact.get("statistical_checkpoint_executed") is False
    ):
        raise RuntimeError("LIVE_PROVIDER_VALIDATION_ARTIFACT_CONTRACT_FAIL")

    base_artifact_meta = _artifact_metadata(
        BASE_ARTIFACT_ID,
        expected_name=BASE_ARTIFACT_NAME,
        expected_digest=BASE_ARTIFACT_SHA256,
        expected_run_id=BASE_RUN_ID,
    )
    base_zip = _download_artifact_zip(BASE_ARTIFACT_ID, BASE_ARTIFACT_SHA256)
    source_readiness = _json_member(base_zip, "CP_F_N1200_SOURCE_READINESS.json")
    trial_payload = _json_member(base_zip, "CP_F_N1200_TRIAL_RESULTS.json")
    if not (
        source_readiness.get("status") == "READY_FOR_DETERMINISTIC_REPLAY"
        and source_readiness.get("dataset", {}).get("source_sha") == SOURCE_SHA
        and source_readiness.get("dataset", {}).get("master_seed") == MASTER_SEED
        and source_readiness.get("dataset", {}).get("total_trial_outcomes") == 24005
        and source_readiness.get("n1200_checkpoint", {}).get("ordered_scenario_trial_hash_map_sha256_n1200") == BASE_N1200_MAP_SHA256
        and trial_payload.get("schema_version") == ARTIFACT_SCHEMA
        and trial_payload.get("source_sha") == SOURCE_SHA
        and trial_payload.get("master_seed") == MASTER_SEED
    ):
        raise RuntimeError("N1200_SOURCE_READINESS_CONTRACT_FAIL")

    scenarios = trial_payload.get("scenarios")
    if not isinstance(scenarios, dict) or set(scenarios) != set(SCENARIOS):
        raise RuntimeError("N1200_SOURCE_SCENARIO_COVERAGE_FAIL")
    actual_by_scenario: dict[str, dict[int, str]] = {}
    total = 0
    target_base_rows: list[dict[str, Any]] = []
    for scenario in SCENARIOS:
        rows = scenarios[scenario]
        expected_ids = [1] if scenario.startswith("C100_") else list(range(1, 1201))
        indexed: dict[int, str] = {}
        for row in rows:
            if not isinstance(row, dict):
                raise RuntimeError(f"N1200_SOURCE_ROW_NOT_OBJECT:{scenario}")
            try:
                trial_id = int(row.get("trial_id", -1))
            except (TypeError, ValueError) as exc:
                raise RuntimeError(f"N1200_SOURCE_TRIAL_ID_INVALID:{scenario}") from exc
            trial_result = row.get("trial_result")
            if not isinstance(trial_result, dict):
                raise RuntimeError(f"N1200_SOURCE_RESULT_MISSING:{scenario}/{trial_id}")
            if (
                row.get("scenario_id") != scenario
                or row.get("source_sha") != SOURCE_SHA
                or int(row.get("master_seed", -1)) != MASTER_SEED
                or trial_result.get("scenario_id") != scenario
                or int(trial_result.get("trial_id", -1)) != trial_id
                or _canonical_result_sha256(trial_result) != row.get("result_sha256")
                or trial_id in indexed
            ):
                raise RuntimeError(f"N1200_SOURCE_TRIAL_IDENTITY_OR_HASH_FAIL:{scenario}/{trial_id}")
            golden = provider.get_fingerprint(scenario, trial_id)
            if not golden:
                raise RuntimeError(f"N1200_SOURCE_GOLDEN_FINGERPRINT_MISSING:{scenario}/{trial_id}")
            if row["result_sha256"] != golden:
                raise RuntimeError(f"N1200_SOURCE_GOLDEN_MISMATCH:{scenario}/{trial_id}")
            indexed[trial_id] = row["result_sha256"]
            total += 1
            if scenario == SCENARIO:
                target_base_rows.append({
                    "scenario_id": scenario,
                    "trial_id": trial_id,
                    "source_sha": SOURCE_SHA,
                    "master_seed": MASTER_SEED,
                    "result_sha256": row["result_sha256"],
                    "trial_result": trial_result,
                })
        if sorted(indexed) != expected_ids:
            raise RuntimeError(f"N1200_SOURCE_TRIAL_COVERAGE_FAIL:{scenario}")
        actual_by_scenario[scenario] = indexed

    non_c100_map = _ordered_map_sha256({s: actual_by_scenario[s] for s in NON_C100_SCENARIOS})
    if total != 24005 or non_c100_map != BASE_N1200_MAP_SHA256:
        raise RuntimeError(f"N1200_SOURCE_AGGREGATE_MISMATCH:total={total}:map={non_c100_map}")
    target_base_rows.sort(key=lambda row: row["trial_id"])
    if [row["trial_id"] for row in target_base_rows] != list(range(1, 1201)):
        raise RuntimeError("TARGET_BASE_TRIAL_COVERAGE_NOT_1_TO_1200")

    golden_extension_artifact_meta = _artifact_metadata(
        EXTENSION_ARTIFACT_ID,
        expected_name=EXTENSION_ARTIFACT_NAME,
        expected_digest=EXTENSION_ARTIFACT_SHA256,
        expected_run_id=EXTENSION_RUN_ID,
    )
    extension = _json_member(
        _download_artifact_zip(EXTENSION_ARTIFACT_ID, EXTENSION_ARTIFACT_SHA256),
        "golden_extension.json",
    )
    if not (
        extension.get("status") == "PASS"
        and extension.get("schema_version") == "gate-a-golden-extension-v1"
        and extension.get("extension_decision_id") == GATE_A_DECISION_ID
        and extension.get("base_decision_id") == "D-2026-10-14-01"
        and extension.get("scenario_id") == SCENARIO
        and extension.get("source_sha") == SOURCE_SHA
        and extension.get("source_commit") == SOURCE_COMMIT
        and extension.get("master_seed") == MASTER_SEED
        and extension.get("trial_id_start") == TRIAL_START
        and extension.get("trial_id_end") == TRIAL_END
        and extension.get("trial_count") == 1200
        and extension.get("run_id") == EXTENSION_RUN_ID
        and extension.get("workflow_head_sha") == EXTENSION_RUN_HEAD
        and extension.get("origin") == "pinned_approved_source_reference"
        and extension.get("run_attempt") == 1
        and extension.get("base_golden_map_sha256") == "166cae242d972c597f1a4466d184062f3d959649eb5e2440ad8de8b75663ff2c"
        and extension.get("extension_map_sha256") == EXTENSION_MAP_SHA256
        and extension.get("historical_ids_rerun") is False
        and extension.get("historical_dataset_modified") is False
        and extension.get("source_sha_bumped") is False
        and extension.get("production_checkpoint_accepted") is False
    ):
        raise RuntimeError("GOLDEN_EXTENSION_ARTIFACT_CONTRACT_FAIL")
    extension_rows = extension.get("records")
    if not isinstance(extension_rows, list) or len(extension_rows) != 1200:
        raise RuntimeError("GOLDEN_EXTENSION_ROW_COUNT_FAIL")
    ext_hashes: dict[int, str] = {}
    for row in extension_rows:
        trial_id = int(row.get("trial_id", -1))
        trial_result = row.get("trial_result")
        digest = row.get("result_sha256")
        if (
            not isinstance(trial_result, dict)
            or row.get("scenario_id") != SCENARIO
            or row.get("source_sha") != SOURCE_SHA
            or row.get("source_commit") != SOURCE_COMMIT
            or int(row.get("master_seed", -1)) != MASTER_SEED
            or int(row.get("run_id", -1)) != EXTENSION_RUN_ID
            or int(row.get("run_attempt", -1)) != 1
            or row.get("origin") != "pinned_source_reference"
            or int(trial_result.get("trial_id", -1)) != trial_id
            or trial_result.get("scenario_id") != SCENARIO
            or _canonical_result_sha256(trial_result) != digest
            or trial_id in ext_hashes
            or provider.get_fingerprint(SCENARIO, trial_id) != digest
        ):
            raise RuntimeError(f"GOLDEN_EXTENSION_RECORD_PROVENANCE_OR_HASH_FAIL:{SCENARIO}/{trial_id}")
        ext_hashes[trial_id] = digest
    if sorted(ext_hashes) != list(range(TRIAL_START, TRIAL_END + 1)):
        raise RuntimeError("GOLDEN_EXTENSION_ID_COVERAGE_FAIL")
    extension_map = _target_map_sha256(ext_hashes)
    if extension_map != EXTENSION_MAP_SHA256:
        raise RuntimeError(f"GOLDEN_EXTENSION_MAP_SHA_MISMATCH:{extension_map}")

    provider_coverage = sorted(int(x) for x in provider.get_coverage(SCENARIO))
    if provider_coverage != list(range(1, TRIAL_END + 1)):
        raise RuntimeError("LIVE_PROVIDER_TARGET_COVERAGE_NOT_1_TO_2400")
    provider_maps: dict[str, dict[int, str]] = {}
    for scenario in SCENARIOS:
        coverage = sorted(int(x) for x in provider.get_coverage(scenario))
        expected = [1] if scenario.startswith("C100_") else (
            list(range(1, TRIAL_END + 1)) if scenario == SCENARIO else list(range(1, 1201))
        )
        if coverage != expected:
            raise RuntimeError(f"LIVE_PROVIDER_SCENARIO_COVERAGE_FAIL:{scenario}")
        provider_maps[scenario] = {}
        for trial_id in coverage:
            fingerprint = provider.get_fingerprint(scenario, trial_id)
            if not isinstance(fingerprint, str) or len(fingerprint) != 64:
                raise RuntimeError(f"LIVE_PROVIDER_FINGERPRINT_INVALID:{scenario}/{trial_id}")
            provider_maps[scenario][trial_id] = fingerprint
    provider_map_sha = _ordered_map_sha256(provider_maps)
    if provider_map_sha != EXTENDED_FULL_MAP_SHA256:
        raise RuntimeError(f"LIVE_PROVIDER_FULL_MAP_SHA_MISMATCH:{provider_map_sha}")

    # Keep only the selected scenario's immutable N=1200 inputs and its independent
    # reference extension; no historical dataset or Parquet file is edited.
    inputs = {
        "schema_version": CHECKPOINT_SCHEMA,
        "decision_id": GATE_A_DECISION_ID,
        "source_sha": SOURCE_SHA,
        "source_commit": SOURCE_COMMIT,
        "master_seed": MASTER_SEED,
        "scenario": SCENARIO,
        "base_trial_ids": "1..1200",
        "extension_trial_ids": "1201..2400",
        "base_n1200_map_sha256": non_c100_map,
        "extension_map_sha256": extension_map,
        "approved_extended_provider_map_sha256": provider_map_sha,
        "golden_reference_id": provider.get_golden_reference_id(),
        "base_source_run_id": BASE_RUN_ID,
        "base_source_artifact_id": BASE_ARTIFACT_ID,
        "base_source_artifact_sha256": BASE_ARTIFACT_SHA256,
        "reference_run_id": EXTENSION_RUN_ID,
        "reference_workflow_head_sha": EXTENSION_RUN_HEAD,
        "reference_artifact_id": EXTENSION_ARTIFACT_ID,
        "reference_artifact_sha256": EXTENSION_ARTIFACT_SHA256,
        "provider_validation_run_id": PROVIDER_VALIDATION_RUN_ID,
        "provider_validation_artifact_id": PROVIDER_VALIDATION_ARTIFACT_ID,
        "provider_validation_artifact_sha256": PROVIDER_VALIDATION_ARTIFACT_SHA256,
        "base_results": target_base_rows,
        "golden_extension_records": extension_rows,
        "target_reference_hashes": {
            str(trial_id): provider.get_fingerprint(SCENARIO, trial_id)
            for trial_id in range(1, TRIAL_END + 1)
        },
    }
    _atomic_json(outdir / "checkpoint_inputs.json", inputs)
    report = {
        "schema_version": CHECKPOINT_SCHEMA,
        "decision_id": GATE_A_DECISION_ID,
        "preflight_status": "PASS",
        "checkpoint_status": "NOT_STARTED",
        "checkpoint_executed": False,
        "source_identity": {
            "source_sha": SOURCE_SHA,
            "source_commit": SOURCE_COMMIT,
            "master_seed": MASTER_SEED,
            "scenario": SCENARIO,
        },
        "n1200_source": {
            "run_id": BASE_RUN_ID,
            "artifact_id": BASE_ARTIFACT_ID,
            "artifact_sha256": BASE_ARTIFACT_SHA256,
            "trial_count_all_scenarios": total,
            "non_c100_ordered_hash_map_sha256": non_c100_map,
            "target_trial_ids_verified": 1200,
        },
        "golden_extension": {
            "run_id": EXTENSION_RUN_ID,
            "tested_workflow_head_sha": EXTENSION_RUN_HEAD,
            "artifact_id": EXTENSION_ARTIFACT_ID,
            "artifact_sha256": EXTENSION_ARTIFACT_SHA256,
            "extension_map_sha256": extension_map,
            "rows_verified": len(extension_rows),
        },
        "provider_validation": {
            "run_id": PROVIDER_VALIDATION_RUN_ID,
            "tested_workflow_head_sha": PROVIDER_VALIDATION_HEAD,
            "artifact_id": PROVIDER_VALIDATION_ARTIFACT_ID,
            "artifact_sha256": PROVIDER_VALIDATION_ARTIFACT_SHA256,
            "combined_map_sha256": provider_map_sha,
            "scenario_coverage": 25,
            "target_coverage": "1..2400",
        },
        "historical_trial_ids_rerun": False,
        "dataset_or_parquet_modified": False,
        "source_sha_bumped": False,
        "main_modified": False,
        "release_created": False,
        "input_contract_verified": True,
    }
    _write_report(outdir, report)
    return inputs, report

def _reference_metrics(results: list[Any], numpy_module, constants_module) -> dict[str, float]:
    by_name = {
        "P10_Cumulative_Project_Profit": (
            [float(r.cumulative_project_profit) for r in results], 0.10
        ),
        "P50_Cumulative_Project_Profit": (
            [float(r.cumulative_project_profit) for r in results], 0.50
        ),
        "P90_Cumulative_Project_Profit": (
            [float(r.cumulative_project_profit) for r in results], 0.90
        ),
        "P90_Final_Cash": ([float(r.final_cash) for r in results], 0.90),
        "P90_Termination_Count": ([float(r.termination_count) for r in results], 0.90),
        "P90_Held_Assets": ([float(r.held_assets) for r in results], 0.90),
    }
    out = {
        key: float(numpy_module.quantile(numpy_module.asarray(values, dtype=numpy_module.float64), q, method="linear"))
        for key, (values, q) in by_name.items()
    }
    profits = [float(r.cumulative_project_profit) for r in results]
    out["Probability_of_Accounting_Loss"] = sum(1 for value in profits if value < 0) / len(profits)
    expected = tuple(constants_module.REFERENCE_STABILITY_INDICATORS)
    if set(out) != set(expected) or len(expected) != 7:
        raise RuntimeError(f"REFERENCE_2_5_INDICATOR_CONTRACT_MISMATCH:expected={expected}:actual={sorted(out)}")
    return {key: out[key] for key in expected}

def _gate_b_metrics(results: list[Any], numpy_module, constants_module, scipy_t) -> dict[str, Any]:
    n = len(results)
    if n < 2:
        raise RuntimeError("GATE_B_REQUIRES_AT_LEAST_TWO_TRIALS")
    t_critical = float(scipy_t.ppf(1.0 - (1.0 - constants_module.CI_CONFIDENCE_LEVEL) / 2.0, n - 1))
    metrics: dict[str, Any] = {}
    for field_name in (
        "final_net_project_equity",
        "partner1_final_entitlement",
        "partner2_final_entitlement",
    ):
        sample = numpy_module.asarray([getattr(row, field_name) for row in results], dtype=numpy_module.float64)
        mean = float(sample.mean())
        sample_std = float(sample.std(ddof=1))
        half_ci = float(t_critical * sample_std / (n ** 0.5))
        limit = max(
            float(constants_module.CI_ABSOLUTE_EPSILON),
            float(constants_module.CI_RELATIVE_TOLERANCE) * abs(mean),
        )
        metrics[field_name] = {
            "n": n,
            "mean": mean,
            "sample_std": sample_std,
            "t_critical": t_critical,
            "half_ci_95": half_ci,
            "limit": limit,
            "stable": half_ci < limit,
        }
    return {
        "checked": True,
        "stable": all(value["stable"] for value in metrics.values()),
        "metrics": metrics,
    }

def _reference_transition(previous: dict[str, float], current: dict[str, float], constants_module) -> dict[str, Any]:
    output = {}
    for name in tuple(constants_module.REFERENCE_STABILITY_INDICATORS):
        old = float(previous[name])
        new = float(current[name])
        absolute_change = abs(new - old)
        if abs(old) < float(constants_module.REFERENCE_EPSILON):
            stable = absolute_change < float(constants_module.ABSOLUTE_EPSILON)
            output[name] = {
                "checked": True, "stable": stable, "status": "PASS" if stable else "FAIL",
                "previous": old, "current": new, "absolute_change": absolute_change,
                "relative_change": None, "comparison": "ABSOLUTE_NEAR_ZERO",
                "threshold": float(constants_module.ABSOLUTE_EPSILON),
                "inequality": "absolute_change < ABSOLUTE_EPSILON",
            }
        else:
            relative = absolute_change / abs(old)
            stable = relative < float(constants_module.REFERENCE_STABILITY_RELATIVE_TOLERANCE)
            output[name] = {
                "checked": True, "stable": stable, "status": "PASS" if stable else "FAIL",
                "previous": old, "current": new, "absolute_change": absolute_change,
                "relative_change": relative, "comparison": "RELATIVE",
                "threshold": float(constants_module.REFERENCE_STABILITY_RELATIVE_TOLERANCE),
                "inequality": "relative_change < REFERENCE_STABILITY_RELATIVE_TOLERANCE",
            }
    return {
        "checked": True,
        "stable": all(value["stable"] for value in output.values()),
        "status": "PASS" if all(value["stable"] for value in output.values()) else "FAIL",
        "metrics": output,
    }

def _execute_checkpoint(source_root: Path, outdir: Path, time_budget_seconds: int) -> int:
    outdir.mkdir(parents=True, exist_ok=True)
    run_id = int(os.environ.get("GITHUB_RUN_ID", "0"))
    run_attempt = int(os.environ.get("GITHUB_RUN_ATTEMPT", "1"))
    tested_head = os.environ.get("GITHUB_SHA", "")
    branch = os.environ.get("GITHUB_REF_NAME", "")
    report_path = outdir / "checkpoint_report.json"
    results_path = outdir / "actual_trial_results.jsonl"
    progress_path = outdir / "checkpoint_progress.json"

    report_base = {
        "schema_version": CHECKPOINT_SCHEMA,
        "decision_id": GATE_A_DECISION_ID,
        "checkpoint_run_id": run_id,
        "checkpoint_run_attempt": run_attempt,
        "checkpoint_workflow_head_sha": tested_head,
        "branch": branch,
        "target_scenario": SCENARIO,
        "trial_id_start": TRIAL_START,
        "trial_id_end": TRIAL_END,
        "target_checkpoint_n": TRIAL_END,
        "source_sha": SOURCE_SHA,
        "pinned_source_commit": SOURCE_COMMIT,
        "master_seed": MASTER_SEED,
        "historical_trial_ids_rerun": False,
        "dataset_or_parquet_modified": False,
        "source_sha_bumped": False,
        "main_modified": False,
        "release_created": False,
        "statistical_checkpoint_executed": False,
        "historical_n300_to_n600_failure_preserved": True,
        "historic_failure": {
            "scenario": SCENARIO,
            "metric": "P90_Final_Cash",
            "transition": "N=300 to N=600",
            "relative_change_percent": 1.5715059334983579,
            "strict_limit_percent": 1.0,
            "status": "FAIL",
        },
    }
    if run_attempt != 1:
        report = {**report_base, "checkpoint_status": "BLOCKED_RERUN_ATTEMPT", "reason": "workflow reruns are disallowed to protect one-time trial IDs"}
        _write_report(outdir, report)
        return 1
    if results_path.exists() or progress_path.exists():
        report = {**report_base, "checkpoint_status": "BLOCKED_EXISTING_PROGRESS", "reason": "output already contains trial progress; refusing to generate any trial ID again"}
        _write_report(outdir, report)
        return 1

    try:
        source_meta = json.loads((outdir / "source_identity.json").read_text(encoding="utf-8"))
        if not (
            source_meta.get("status") == "PASS"
            and source_meta.get("source_commit") == SOURCE_COMMIT
            and source_meta.get("source_sha") == SOURCE_SHA
            and source_meta.get("master_seed") == MASTER_SEED
            and source_meta.get("source_worktree_clean") is True
            and source_meta.get("trial_generation_executed") is False
            and int(source_meta.get("module_count", 0)) == 14
            and all(item.get("origin_matches_pinned_source") is True for item in source_meta.get("modules", []))
        ):
            raise RuntimeError("PINNED_SOURCE_IMPORT_IDENTITY_EVIDENCE_FAIL")

        repo_root = Path.cwd().resolve()
        monte_carlo, source_constants, source_root = _load_pinned_model(source_root)
        candidate_constants = _candidate_constants(repo_root)
        import numpy as np
        from scipy.stats import t as scipy_t

        if tuple(candidate_constants.REFERENCE_STABILITY_INDICATORS) != tuple(source_constants.REFERENCE_STABILITY_INDICATORS):
            raise RuntimeError("REFERENCE_STABILITY_INDICATOR_SET_DIFFERS_FROM_PINNED_SOURCE")
        required_indicators = (
            "P10_Cumulative_Project_Profit", "P50_Cumulative_Project_Profit",
            "P90_Cumulative_Project_Profit", "P90_Final_Cash",
            "Probability_of_Accounting_Loss", "P90_Termination_Count", "P90_Held_Assets",
        )
        if tuple(candidate_constants.REFERENCE_STABILITY_INDICATORS) != required_indicators:
            raise RuntimeError("APPROVED_REFERENCE_2_5_INDICATOR_ORDER_MISMATCH")

        from scripts.golden_reference_provider import stage10_trial_result_sha256
        provider, reference_id = _load_approved_provider()
        inputs, preflight_report = _load_and_verify_source_inputs(outdir, provider)
        base_results = [
            monte_carlo.TrialResult(**row["trial_result"])
            for row in inputs["base_results"]
        ]
        if len(base_results) != 1200 or [int(row.trial_id) for row in base_results] != list(range(1, 1201)):
            raise RuntimeError("TARGET_BASE_DATASET_NOT_EXACTLY_1_TO_1200")

        if (
            not tested_head or len(tested_head) != 40
            or branch != "tmp/cp-gatea-c030-n2400-20261015"
            or not reference_id
        ):
            raise RuntimeError("CHECKPOINT_WORKFLOW_IDENTITY_INVALID")

        _atomic_json(progress_path, {
            "schema_version": CHECKPOINT_SCHEMA,
            "status": "RUNNING",
            "run_id": run_id,
            "run_attempt": run_attempt,
            "tested_head_sha": tested_head,
            "branch": branch,
            "scenario": SCENARIO,
            "source_sha": SOURCE_SHA,
            "source_commit": SOURCE_COMMIT,
            "master_seed": MASTER_SEED,
            "target_trial_ids": "1201..2400",
            "attempted_trial_ids": [],
            "completed_trial_ids": [],
            "in_progress_trial_id": None,
            "checkpoint_executed": True,
            "historical_trial_ids_rerun": False,
            "started_at_utc": _now(),
        })
        started = time.monotonic()
        expected_hashes = {
            int(trial_id): digest
            for trial_id, digest in inputs["target_reference_hashes"].items()
        }
        if sorted(expected_hashes) != list(range(1, 2401)):
            raise RuntimeError("APPROVED_TARGET_REFERENCE_HASH_COVERAGE_MISMATCH")
        mismatch_record = None
        completed_rows: list[dict[str, Any]] = []
        attempted_ids: list[int] = []
        completed_ids: list[int] = []
        with results_path.open("x", encoding="utf-8") as handle:
            for trial_id in range(TRIAL_START, TRIAL_END + 1):
                if time.monotonic() - started >= time_budget_seconds:
                    _atomic_json(progress_path, {
                        **json.loads(progress_path.read_text(encoding="utf-8")),
                        "status": "BLOCKED_TIME_BUDGET",
                        "attempted_trial_ids": attempted_ids,
                        "completed_trial_ids": completed_ids,
                        "in_progress_trial_id": None,
                        "next_not_started_trial_id": trial_id,
                        "elapsed_trial_generation_seconds": time.monotonic() - started,
                        "updated_at_utc": _now(),
                    })
                    report = {
                        **report_base,
                        "checkpoint_status": "BLOCKED_TIME_BUDGET",
                        "checkpoint_executed": True,
                        "completed_trial_count": len(completed_rows),
                        "completed_trial_ids": f"{TRIAL_START}..{completed_ids[-1]}" if completed_ids else None,
                        "attempted_trial_ids": attempted_ids,
                        "next_not_started_trial_id": trial_id,
                        "in_progress_trial_id": None,
                        "elapsed_trial_generation_seconds": time.monotonic() - started,
                        "exact_failure_literal": "INTERNAL_TIME_BUDGET_EXHAUSTED_BEFORE_NEXT_TRIAL",
                        "failure_classification": "BLOCKED",
                    }
                    _write_report(outdir, report)
                    return 1

                attempted_ids.append(trial_id)
                current_progress = json.loads(progress_path.read_text(encoding="utf-8"))
                current_progress.update({
                    "attempted_trial_ids": attempted_ids,
                    "completed_trial_ids": completed_ids,
                    "in_progress_trial_id": trial_id,
                    "updated_at_utc": _now(),
                })
                _atomic_json(progress_path, current_progress)

                trial_result, _daily_rows = monte_carlo.run_single_trial(
                    SCENARIO, trial_id=trial_id, master_seed=MASTER_SEED
                )
                del _daily_rows
                trial_dict = asdict(trial_result)
                actual_sha = stage10_trial_result_sha256(trial_dict)
                expected_sha = expected_hashes[trial_id]
                record = {
                    "scenario_id": SCENARIO,
                    "trial_id": trial_id,
                    "source_sha": SOURCE_SHA,
                    "source_commit": SOURCE_COMMIT,
                    "master_seed": MASTER_SEED,
                    "run_id": run_id,
                    "run_attempt": run_attempt,
                    "tested_head_sha": tested_head,
                    "origin": "pinned_source_candidate_checkpoint",
                    "result_sha256": actual_sha,
                    "approved_golden_sha256": expected_sha,
                    "exact_golden_match": actual_sha == expected_sha,
                    "trial_result": trial_dict,
                }
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str) + "\n")
                handle.flush()
                os.fsync(handle.fileno())
                completed_rows.append(record)
                completed_ids.append(trial_id)
                progress = json.loads(progress_path.read_text(encoding="utf-8"))
                progress.update({
                    "completed_trial_ids": completed_ids,
                    "completed_trial_count": len(completed_ids),
                    "in_progress_trial_id": None,
                    "last_completed_trial_id": trial_id,
                    "updated_at_utc": _now(),
                })
                if actual_sha != expected_sha:
                    progress["status"] = "FAIL_GATE_A_MISMATCH"
                    _atomic_json(progress_path, progress)
                    mismatch_record = {
                        "trial_id": trial_id,
                        "expected_golden_sha256": expected_sha,
                        "actual_sha256": actual_sha,
                    }
                    report = {
                        **report_base,
                        "checkpoint_status": "FAIL_GATE_A_MISMATCH",
                        "checkpoint_executed": True,
                        "gate_a": {"status": "FAIL", "checked": True, "mismatch": mismatch_record},
                        "completed_trial_count": len(completed_rows),
                        "attempted_trial_ids": attempted_ids,
                        "completed_trial_ids": completed_ids,
                        "remaining_trial_ids_not_started": list(range(trial_id + 1, TRIAL_END + 1)),
                        "in_progress_trial_id": None,
                        "failure_classification": "K_CODE_OR_SOURCE_IDENTITY_REQUIRES_INVESTIGATION",
                        "exact_failure_literal": f"EXACT_GOLDEN_HASH_MISMATCH:{SCENARIO}/{trial_id}",
                    }
                    _write_report(outdir, report)
                    return 1
                _atomic_json(progress_path, progress)

        generation_seconds = time.monotonic() - started
        if [int(row["trial_id"]) for row in completed_rows] != list(range(TRIAL_START, TRIAL_END + 1)):
            raise RuntimeError("GENERATED_EXTENSION_TRIAL_COVERAGE_NOT_EXACTLY_1201_TO_2400")

        extension_hashes = {int(row["trial_id"]): row["result_sha256"] for row in completed_rows}
        target_actual_hashes = {
            int(row["trial_id"]): stage10_trial_result_sha256(row["trial_result"])
            for row in inputs["base_results"]
        }
        target_actual_hashes.update(extension_hashes)
        target_expected_hashes = {
            int(trial_id): expected_hashes[int(trial_id)]
            for trial_id in range(1, TRIAL_END + 1)
        }
        target_map_actual = _target_map_sha256(target_actual_hashes)
        target_map_expected = _target_map_sha256(target_expected_hashes)
        gate_a = {
            "checked": True,
            "status": "PASS" if (
                target_actual_hashes == target_expected_hashes
                and target_map_actual == target_map_expected
                and target_map_actual == _target_map_sha256(expected_hashes)
            ) else "FAIL",
            "scenario": SCENARIO,
            "trial_count_compared": len(target_actual_hashes),
            "trial_id_coverage": "1..2400",
            "mismatch_count": sum(
                1 for trial_id in range(1, TRIAL_END + 1)
                if target_actual_hashes.get(trial_id) != target_expected_hashes.get(trial_id)
            ),
            "actual_target_map_sha256": target_map_actual,
            "approved_target_map_sha256": target_map_expected,
            "golden_reference_id": reference_id,
            "source_identity_matches": provider.verify_source_identity(SOURCE_SHA),
        }
        if gate_a["status"] != "PASS" or gate_a["source_identity_matches"] is not True:
            _atomic_json(progress_path, {
                **json.loads(progress_path.read_text(encoding="utf-8")),
                "status": "FAIL_GATE_A_FINAL_MAP",
                "completed_trial_ids": completed_ids,
                "in_progress_trial_id": None,
                "updated_at_utc": _now(),
            })
            report = {
                **report_base,
                "checkpoint_status": "FAIL_GATE_A_FINAL_MAP",
                "checkpoint_executed": True,
                "completed_trial_count": len(completed_rows),
                "generation_seconds": generation_seconds,
                "gate_a": gate_a,
                "failure_classification": "K_CODE_OR_REFERENCE_IDENTITY_REQUIRES_INVESTIGATION",
                "exact_failure_literal": "FINAL_GATE_A_MAP_OR_SOURCE_IDENTITY_MISMATCH",
            }
            _write_report(outdir, report)
            return 1

        all_results = base_results + [
            monte_carlo.TrialResult(**row["trial_result"])
            for row in completed_rows
        ]
        all_results.sort(key=lambda row: row.trial_id)
        if (
            len(all_results) != 2400
            or [int(row.trial_id) for row in all_results] != list(range(1, 2401))
            or any(
                row.scenario_id != SCENARIO
                for row in all_results
            )
        ):
            raise RuntimeError("FINAL_N2400_COHORT_NOT_EXACTLY_1_TO_2400")

        gate_b_1200 = _gate_b_metrics(all_results[:1200], np, candidate_constants, scipy_t)
        gate_b_2400 = _gate_b_metrics(all_results, np, candidate_constants, scipy_t)
        previous_reference_metrics = _reference_metrics(all_results[:1200], np, candidate_constants)
        current_reference_metrics = _reference_metrics(all_results, np, candidate_constants)
        reference_transition = _reference_transition(
            previous_reference_metrics, current_reference_metrics, candidate_constants
        )
        gates_pass = gate_a["status"] == "PASS" and gate_b_2400["stable"] is True and reference_transition["stable"] is True
        checkpoint_status = "PASS_AT_N2400_ONLY" if gates_pass else "FAIL_AT_N2400"
        report = {
            **report_base,
            "checkpoint_status": checkpoint_status,
            "checkpoint_executed": True,
            "statistical_checkpoint_executed": True,
            "completed_trial_count": len(completed_rows),
            "new_trial_ids": "1201..2400",
            "historical_trials_rerun": False,
            "dataset_or_parquet_modified": False,
            "source_sha_bumped": False,
            "main_modified": False,
            "release_created": False,
            "generation_seconds": generation_seconds,
            "new_trials_result_jsonl_sha256": hashlib.sha256(results_path.read_bytes()).hexdigest(),
            "gate_a": gate_a,
            "gate_b_at_n1200": gate_b_1200,
            "gate_b_at_n2400": gate_b_2400,
            "reference_section_2_5": {
                "decision_id": "D-2026-10-14-20",
                "indicators_expected": list(candidate_constants.REFERENCE_STABILITY_INDICATORS),
                "previous_n": 1200,
                "current_n": 2400,
                "previous_metrics": previous_reference_metrics,
                "current_metrics": current_reference_metrics,
                "transition": reference_transition,
            },
            "historical_n300_to_n600_failure_preserved": True,
            "historical_failure": report_base["historic_failure"],
            "overall_scenario_stability": "NOT_ESTABLISHED_BY_N2400_ALONE",
            "overall_reason": "A single N=1200 to N=2400 pass cannot erase the historic N=300 to N=600 §2.5 FAIL or satisfy the project-wide consecutive-checkpoint requirement.",
            "approved_artifact_provenance": {
                "n1200_source_run_id": BASE_RUN_ID,
                "n1200_source_artifact_id": BASE_ARTIFACT_ID,
                "n1200_source_artifact_sha256": BASE_ARTIFACT_SHA256,
                "reference_run_id": EXTENSION_RUN_ID,
                "reference_workflow_head_sha": EXTENSION_RUN_HEAD,
                "reference_artifact_id": EXTENSION_ARTIFACT_ID,
                "reference_artifact_sha256": EXTENSION_ARTIFACT_SHA256,
                "provider_validation_run_id": PROVIDER_VALIDATION_RUN_ID,
                "provider_validation_artifact_id": PROVIDER_VALIDATION_ARTIFACT_ID,
                "provider_validation_artifact_sha256": PROVIDER_VALIDATION_ARTIFACT_SHA256,
                "provider_combined_map_sha256": EXTENDED_FULL_MAP_SHA256,
            },
            "temporary_workflow_removed": False,
        }
        _atomic_json(progress_path, {
            **json.loads(progress_path.read_text(encoding="utf-8")),
            "status": "COMPLETE" if gates_pass else "FAIL_CHECKPOINT_GATE",
            "completed_trial_ids": completed_ids,
            "completed_trial_count": len(completed_ids),
            "in_progress_trial_id": None,
            "finished_at_utc": _now(),
            "elapsed_trial_generation_seconds": generation_seconds,
            "checkpoint_status": checkpoint_status,
            "updated_at_utc": _now(),
        })
        _write_report(outdir, report)
        return 0 if gates_pass else 1

    except Exception as exc:
        progress = None
        if progress_path.exists():
            try:
                progress = json.loads(progress_path.read_text(encoding="utf-8"))
                progress["status"] = "BLOCKED_OR_FAILED_EXCEPTION"
                progress["exact_failure_literal"] = f"{type(exc).__name__}: {exc}"
                progress["failure_classification"] = "PENDING_CLASSIFICATION"
                progress["updated_at_utc"] = _now()
                _atomic_json(progress_path, progress)
            except Exception:
                pass
        report = {
            **report_base,
            "checkpoint_status": "BLOCKED_OR_FAILED_EXCEPTION",
            "checkpoint_executed": bool(progress and progress.get("checkpoint_executed")),
            "failure_classification": "PENDING_CLASSIFICATION",
            "exact_failure_literal": f"{type(exc).__name__}: {exc}",
            "in_progress_trial_id": progress.get("in_progress_trial_id") if progress else None,
            "attempted_trial_ids": progress.get("attempted_trial_ids", []) if progress else [],
            "completed_trial_ids": progress.get("completed_trial_ids", []) if progress else [],
            "historical_n300_to_n600_failure_preserved": True,
        }
        _write_report(outdir, report)
        return 1

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--time-budget-seconds", type=int, default=2100)
    args = parser.parse_args()
    return _execute_checkpoint(
        source_root=args.source_root,
        outdir=args.output_dir,
        time_budget_seconds=args.time_budget_seconds,
    )

if __name__ == "__main__":
    raise SystemExit(main())
