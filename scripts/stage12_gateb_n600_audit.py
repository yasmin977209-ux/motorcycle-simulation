#!/usr/bin/env python3
"""Evidence-gated N=600 Gate B checkpoint. Historical inputs are read-only."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import zipfile
from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
from scipy.stats import t

REPO = "yasmin977209-ux/motorcycle-simulation"
PINNED_MAIN_SHA = "f9e7d06e4140612b1bd2ee2a8afd069f65a02d53"
SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
SOURCE_COMMIT = "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
MASTER_SEED = 20270101
STAGE7_RUN_ID = 37225915321
STAGE7_HEAD = "e0b2fab6710833774937d778097363d7a8ee8e59"
STAGE10_RUN_ID = 37709936740
STAGE10_HEAD = "ca73f2df37baacebbcad965fc5f433f129675820"
STAGE12_RUN_ID = 37964656154
STAGE12_HEAD = "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
N300_RUN_ID = 38162171123
N300_ARTIFACT_ID = 11711110209
EXPECTED_STAGE12_GLOBAL = "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44"
EXPECTED_STAGE9A_GLOBAL = "892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6"
SCENARIOS = [f"C{c:03d}_G{g:03d}" for c in (85, 70, 50, 30) for g in (100, 70, 50, 30, 0)]
BASE_BLOCKS = ((1, 300), (301, 350), (351, 400), (401, 450))
HISTORICAL_IDS = range(1, 551)
NEW_IDS = range(551, 601)
METRICS = {
    "Final_Net_Project_Equity": "final_net_project_equity",
    "Partner1_Final_Entitlement": "partner1_final_entitlement",
    "Partner2_Final_Entitlement": "partner2_final_entitlement",
}
IDENTITY_KEY = b"stage12.dataset_identity"
SCHEMA_VERSION = "stage12-daily-accounting-v1"
RNG_POLICY = "rng.py:SHA-256(seed key master_seed|scenario_id|trial_id|bike_id|date|event_type); draw=first_8_digest_bytes_big_endian/2^64; probability boundaries are deterministic"
HISTORICAL_SAMPLING_POLICY = "one-based contiguous trial IDs; C100 scenarios use 1..1; non-C100 scenarios use 1..550; one materialization per scenario/trial; no cross-run inputs or resume"
HISTORICAL_STABILITY_POLICY = "C100 uses one deterministic trial and no CI gate; non-C100 checkpoint N=300 then +50; 95% Student-t CI half-width <1% of absolute mean for Final_Net_Project_Equity, Partner1_Final_Entitlement, Partner2_Final_Entitlement; CI_ABSOLUTE_EPSILON=1; three consecutive successful checkpoints; accepted N=550 (checkpoints 450, 500, 550)"
TRIAL_ID_POLICY = "one-based contiguous trial IDs from 1 to scenario target; no duplicate IDs"
EPSILON = 1.0

COLUMN_TYPES = {
    "scenario_id": "string", "trial_id": "int64", "date": "string",
    "source_sha": "string", "master_seed": "int64",
    "Opening_Cash": "int64", "cash_inflows": "int64", "cash_outflows": "int64", "Closing_Cash": "int64",
    "Opening_AR": "int64", "ar_accruals": "int64", "ar_collections": "int64",
    "ar_transfers_to_guarantee": "int64", "Closing_AR": "int64",
    "Opening_Gross_Bike_Assets": "int64", "capitalized_purchases_and_customs": "int64",
    "gross_writeoffs_on_ownership": "int64", "Closing_Gross_Bike_Assets": "int64",
    "Opening_Accumulated_Depreciation": "int64", "depreciation_expense": "int64",
    "ad_removed_on_writeoff": "int64", "Closing_Accumulated_Depreciation": "int64",
    "Net_Bike_Assets": "int64", "Capital": "int64", "Retained_Earnings": "int64",
    "Opening_Equity": "int64", "Operating_Net_Profit": "int64", "Closing_Equity": "int64",
    "Guarantee_Claim_Receivable": "int64", "Total_Assets": "int64", "Liabilities": "int64",
    "Balance_Difference": "int64", "Final_Close_Date": "string", "Simulation_Stopped": "bool",
    "Active_Bikes": "int64", "Owned_Transferred_Bikes": "int64", "Pending_Claims": "int64",
    "result_sha256": "string",
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def row_sha(row: dict[str, Any]) -> str:
    raw = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return sha_bytes(raw)


def canonicalize(value: Any) -> Any:
    if isinstance(value, float):
        return value.hex()
    if isinstance(value, dict):
        return {str(k): canonicalize(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [canonicalize(item) for item in value]
    return value


def canonical_fingerprint(rows: list[dict[str, Any]]) -> str:
    ordered = sorted(rows, key=lambda item: int(item["trial_id"]))
    payload = "\n".join(json.dumps(canonicalize(row), ensure_ascii=False, sort_keys=True, separators=(",", ":")) for row in ordered)
    return sha_bytes(payload.encode("utf-8"))


def parse_json_bytes(raw: bytes, allow_known_stage10_suffix: bool = False) -> tuple[dict[str, Any], str]:
    literal_suffix = b"}\\n"
    if raw.endswith(literal_suffix):
        if not allow_known_stage10_suffix:
            fail("UNEXPECTED_LITERAL_BACKSLASH_N_JSON_SUFFIX")
        object_bytes = raw[:-2]
        if not object_bytes.endswith(b"}"):
            fail("STAGE10_SUFFIX_TRIM_DID_NOT_END_AT_JSON_OBJECT")
        value = json.loads(object_bytes.decode("utf-8"))
        if not isinstance(value, dict):
            fail("JSON_ROOT_NOT_OBJECT")
        return value, "known_stage10_literal_backslash_n_suffix_removed_in_memory"
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        fail("JSON_ROOT_NOT_OBJECT")
    return value, "standard_json"


def gh_json(endpoint: str) -> dict[str, Any]:
    result = subprocess.run(["gh", "api", endpoint], text=True, capture_output=True, check=False)
    if result.returncode:
        fail(f"GH_API_FAILED endpoint={endpoint} exit={result.returncode} stderr={result.stderr[-1200:]}")
    value = json.loads(result.stdout)
    if not isinstance(value, dict):
        fail(f"GH_API_RESPONSE_NOT_OBJECT endpoint={endpoint}")
    return value


def validate_live_run(run_id: int, expected_head: str, expected_conclusion: str) -> dict[str, Any]:
    data = gh_json(f"repos/{REPO}/actions/runs/{run_id}")
    if int(data.get("id", -1)) != run_id or data.get("head_sha") != expected_head:
        fail(f"RUN_IDENTITY_MISMATCH run={run_id} expected_head={expected_head} actual_head={data.get('head_sha')}")
    if data.get("status") != "completed" or data.get("conclusion") != expected_conclusion:
        fail(f"RUN_STATUS_MISMATCH run={run_id} expected={expected_conclusion} actual={data.get('status')}/{data.get('conclusion')}")
    return {key: data.get(key) for key in ("id", "head_sha", "head_branch", "status", "conclusion", "created_at", "html_url")}


def list_artifacts(run_id: int) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    response = gh_json(f"repos/{REPO}/actions/runs/{run_id}/artifacts?per_page=100")
    items = response.get("artifacts")
    if not isinstance(items, list) or int(response.get("total_count", -1)) != len(items):
        fail(f"ARTIFACT_LIST_INCOMPLETE run={run_id}")
    indexed = {}
    for artifact in items:
        if artifact.get("expired"):
            continue
        name = artifact.get("name")
        if not name:
            continue
        if name in indexed:
            fail(f"DUPLICATE_ARTIFACT_NAME run={run_id} name={name}")
        workflow_run = artifact.get("workflow_run") or {}
        if workflow_run and int(workflow_run.get("id", -1)) != run_id:
            fail(f"ARTIFACT_WRONG_RUN run={run_id} name={name}")
        indexed[name] = artifact
    return indexed, response


def download_artifact(artifact: dict[str, Any], path: Path) -> dict[str, Any]:
    artifact_id = int(artifact["id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as stream:
        result = subprocess.run(
            ["gh", "api", f"repos/{REPO}/actions/artifacts/{artifact_id}/zip"],
            stdout=stream, stderr=subprocess.PIPE, check=False,
        )
    if result.returncode or path.stat().st_size == 0 or not zipfile.is_zipfile(path):
        fail(f"ARTIFACT_DOWNLOAD_FAILED id={artifact_id} exit={result.returncode} stderr={result.stderr.decode('utf-8', errors='replace')[-1000:]}")
    actual = sha_file(path)
    expected = artifact.get("digest")
    if expected and actual != str(expected).removeprefix("sha256:"):
        fail(f"ARTIFACT_DIGEST_MISMATCH id={artifact_id} expected={expected} actual={actual}")
    return {"artifact_id": artifact_id, "artifact_name": artifact.get("name"), "archive_sha256": actual, "api_digest": expected}


def zip_member(zf: zipfile.ZipFile, name: str) -> bytes:
    matches = [item for item in zf.namelist() if item == name]
    if len(matches) != 1:
        fail(f"ZIP_MEMBER_COUNT name={name} count={len(matches)}")
    return zf.read(matches[0])


def zip_member_basename(zf: zipfile.ZipFile, name: str) -> bytes:
    matches = [item for item in zf.namelist() if Path(item).name == name]
    if len(matches) != 1:
        fail(f"ZIP_MEMBER_BASENAME_COUNT name={name} count={len(matches)}")
    if matches[0].startswith("/") or ".." in Path(matches[0]).parts:
        fail(f"ZIP_PATH_INVALID name={matches[0]}")
    return zf.read(matches[0])


def check_metric_row(row: dict[str, Any], scenario: str, trial_id: int) -> None:
    if row.get("scenario_id") != scenario or int(row.get("trial_id", -1)) != trial_id:
        fail(f"TRIAL_ROW_KEY_MISMATCH {scenario}/{trial_id}")
    if row.get("collection_probability") is None or row.get("recovery_rate_pct") is None:
        fail(f"TRIAL_ROW_SCENARIO_FIELDS_MISSING {scenario}/{trial_id}")
    for metric in METRICS.values():
        value = row.get(metric)
        if isinstance(value, bool) or not isinstance(value, int):
            fail(f"TRIAL_METRIC_NOT_INTEGER {scenario}/{trial_id}/{metric} value={value!r}")


def verify_source_block(
    scenario: str, start: int, end: int, metadata_raw: bytes, parquet_raw: bytes,
    run_id: int, expected_source_block_fingerprint: str | None,
    allow_stage10_suffix: bool = False,
) -> tuple[dict[int, dict[str, Any]], dict[str, Any]]:
    metadata, parse_mode = parse_json_bytes(metadata_raw, allow_known_stage10_suffix=allow_stage10_suffix)
    expected_count = end - start + 1
    checks = {
        "scenario": metadata.get("scenario") == scenario,
        "source_sha": metadata.get("source_sha") == SOURCE_SHA,
        "run_id": str(metadata.get("run_id")) == str(run_id),
        "trial_id_start": int(metadata.get("trial_id_start", -1)) == start,
        "trial_id_end": int(metadata.get("trial_id_end", -1)) == end,
        "trial_count": int(metadata.get("trial_count", -1)) == expected_count,
        "log_events_disabled": metadata.get("log_events") is False,
    }
    if not all(checks.values()):
        fail(f"SOURCE_BLOCK_METADATA_IDENTITY_MISMATCH {scenario}/{start}-{end} checks={checks}")
    stored_fingerprint = metadata.get("fingerprint_sha256")
    if not isinstance(stored_fingerprint, str) or re.fullmatch(r"[0-9a-f]{64}", stored_fingerprint) is None:
        fail(f"SOURCE_BLOCK_FINGERPRINT_INVALID {scenario}/{start}-{end}")
    if expected_source_block_fingerprint and stored_fingerprint != expected_source_block_fingerprint:
        fail(f"OFFICIAL_BLOCK_FINGERPRINT_MISMATCH {scenario}/{start}-{end} metadata={stored_fingerprint} official={expected_source_block_fingerprint}")
    stored_hashes = metadata.get("per_trial_sha256")
    if not isinstance(stored_hashes, list) or len(stored_hashes) != expected_count:
        fail(f"SOURCE_BLOCK_HASH_COUNT_MISMATCH {scenario}/{start}-{end}")
    rows = pq.read_table(BytesIO(parquet_raw)).to_pylist()
    if len(rows) != expected_count:
        fail(f"SOURCE_BLOCK_ROW_COUNT_MISMATCH {scenario}/{start}-{end} rows={len(rows)}")
    if canonical_fingerprint(rows) != stored_fingerprint:
        fail(f"SOURCE_BLOCK_FINGERPRINT_RECOMPUTE_MISMATCH {scenario}/{start}-{end}")
    indexed = {}
    for offset, row in enumerate(rows):
        trial_id = start + offset
        check_metric_row(row, scenario, trial_id)
        actual_hash = row_sha(row)
        if actual_hash != stored_hashes[offset]:
            fail(f"SOURCE_BLOCK_TRIAL_HASH_MISMATCH {scenario}/{trial_id} metadata={stored_hashes[offset]} parquet={actual_hash}")
        indexed[trial_id] = row
    evidence = {
        "run_id": run_id, "range": [start, end], "metadata_raw_sha256": sha_bytes(metadata_raw),
        "parquet_raw_sha256": sha_bytes(parquet_raw), "metadata_parse_mode": parse_mode,
        "block_fingerprint_sha256": stored_fingerprint, "trial_rows_rehashed": len(rows),
        "per_trial_metadata_matches_parquet": True,
    }
    return indexed, evidence


def expected_historical_identity(scenario: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION, "scenario": scenario, "source_sha": SOURCE_SHA,
        "master_seed": MASTER_SEED, "rng_policy": RNG_POLICY,
        "sampling_policy": HISTORICAL_SAMPLING_POLICY, "stability_policy": HISTORICAL_STABILITY_POLICY,
        "trial_id_policy": TRIAL_ID_POLICY,
    }


def local_json(path: str) -> dict[str, Any]:
    file_path = Path(path)
    if not file_path.is_file():
        fail(f"REQUIRED_LOCAL_IDENTITY_FILE_MISSING {path}")
    value = json.loads(file_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail(f"LOCAL_IDENTITY_ROOT_NOT_OBJECT {path}")
    return value


def verify_historical_scenario(scenario: str, temp_dir: Path) -> dict[str, Any]:
    report: dict[str, Any] = {
        "scenario_id": scenario, "status": "FAIL", "source_sha": SOURCE_SHA,
        "master_seed": MASTER_SEED, "historical_run_id": STAGE12_RUN_ID,
        "simulation_or_trial_executed": False, "historical_dataset_modified": False,
        "historical_artifacts_modified": False, "errors": [],
    }
    try:
        manifest = local_json("docs/stage9a/dataset_manifest.json")
        identity = local_json("docs/stage11/dataset_identity.json")
        roll = local_json("docs/stage12/roll_forward_validation.json")
        closure = local_json("docs/stage12/closure_settlement_validation.json")
        if manifest.get("global_manifest_sha256") != EXPECTED_STAGE9A_GLOBAL or manifest.get("source_sha") != SOURCE_SHA:
            fail("STAGE9A_MANIFEST_IDENTITY_MISMATCH")
        if int(identity.get("total_canonical_trials", -1)) != 11005 or int(identity.get("scenarios_count", -1)) != 25:
            fail("STAGE11_CANONICAL_IDENTITY_MISMATCH")
        if identity.get("sources", {}).get("stage7", {}).get("run_head_sha") != STAGE7_HEAD:
            fail("STAGE11_STAGE7_HEAD_MISMATCH")
        stage10_recorded_head = identity.get("sources", {}).get("stage10", {}).get("branch_head_sha")
        if str(identity.get("sources", {}).get("stage10", {}).get("run_id")) != str(STAGE10_RUN_ID):
            fail("STAGE11_STAGE10_RUN_ID_MISMATCH")
        if roll.get("source_sha") != SOURCE_SHA or str(roll.get("source_run_id")) != str(STAGE12_RUN_ID):
            fail("STAGE12_ROLLFORWARD_IDENTITY_MISMATCH")
        if roll.get("expected_global_sha256_from_cp12b") != EXPECTED_STAGE12_GLOBAL or roll.get("overall_result") != "PASS":
            fail("STAGE12_ROLLFORWARD_GATE_NOT_PASS")
        if closure.get("source_sha") != SOURCE_SHA or str(closure.get("cp12b_run_id")) != str(STAGE12_RUN_ID):
            fail("STAGE12_CLOSURE_IDENTITY_MISMATCH")
        if closure.get("expected_global_sha256") != EXPECTED_STAGE12_GLOBAL or closure.get("overall_result") != "PASS":
            fail("STAGE12_CLOSURE_GATE_NOT_PASS")

        live7 = validate_live_run(STAGE7_RUN_ID, STAGE7_HEAD, "success")
        live10 = validate_live_run(STAGE10_RUN_ID, STAGE10_HEAD, "failure")
        live12 = validate_live_run(STAGE12_RUN_ID, STAGE12_HEAD, "success")
        jobs7 = gh_json(f"repos/{REPO}/actions/runs/{STAGE7_RUN_ID}/jobs?per_page=100")
        jobs10 = gh_json(f"repos/{REPO}/actions/runs/{STAGE10_RUN_ID}/jobs?per_page=100")
        jobs12 = gh_json(f"repos/{REPO}/actions/runs/{STAGE12_RUN_ID}/jobs?per_page=100")
        for run_id, jobs in ((STAGE7_RUN_ID, jobs7), (STAGE10_RUN_ID, jobs10), (STAGE12_RUN_ID, jobs12)):
            if int(jobs.get("total_count", -1)) != len(jobs.get("jobs", [])):
                fail(f"SOURCE_JOB_LIST_INCOMPLETE run={run_id}")
        stage7_matches = [j for j in jobs7["jobs"] if j.get("name") == f"simulation-{scenario}"]
        stage10_matches = [j for j in jobs10["jobs"] if j.get("name") == f"bench-{scenario}-1"]
        stage12_matches = [j for j in jobs12["jobs"] if j.get("name") == f"materialize ({scenario})" or j.get("name") == f"materialize-{scenario}" or scenario in str(j.get("name", "")) and "materialize" in str(j.get("name", "")).lower()]
        if len(stage7_matches) != 1 or stage7_matches[0].get("conclusion") != "success":
            fail(f"STAGE7_SCENARIO_JOB_NOT_SUCCESS {scenario}")
        if len(stage10_matches) != 1 or stage10_matches[0].get("conclusion") != "success":
            fail(f"STAGE10_SCENARIO_JOB_NOT_SUCCESS {scenario}")
        if len(stage12_matches) != 1 or stage12_matches[0].get("conclusion") != "success":
            fail(f"STAGE12_SCENARIO_JOB_NOT_SUCCESS {scenario}")

        index7, _ = list_artifacts(STAGE7_RUN_ID)
        index10, _ = list_artifacts(STAGE10_RUN_ID)
        index12, _ = list_artifacts(STAGE12_RUN_ID)
        block_ids = manifest.get("artifact_manifest", {}).get("official_block_artifacts", {})
        expected_stage7_artifact_id = int(block_ids.get(scenario, -1))
        stage7_name = f"stage7-blocks-{scenario}-1"
        if stage7_name not in index7 or int(index7[stage7_name].get("id", -2)) != expected_stage7_artifact_id:
            fail(f"STAGE7_ARTIFACT_ID_MISMATCH {scenario}")
        stage10_name = f"stage10-bench-{scenario}-1"
        stage12_name = f"stage12-daily-{scenario}"
        if stage10_name not in index10:
            fail(f"STAGE10_ARTIFACT_MISSING {scenario}")
        if stage12_name not in index12:
            fail(f"STAGE12_ARTIFACT_MISSING {scenario}")

        stage7_zip = temp_dir / "stage7.zip"
        stage10_zip = temp_dir / "stage10.zip"
        stage12_zip = temp_dir / "stage12.zip"
        art7_evidence = download_artifact(index7[stage7_name], stage7_zip)
        art10_evidence = download_artifact(index10[stage10_name], stage10_zip)
        art12_evidence = download_artifact(index12[stage12_name], stage12_zip)

        source_rows: dict[int, dict[str, Any]] = {}
        base_raw: dict[str, tuple[bytes, bytes]] = {}
        block_evidence = []
        with zipfile.ZipFile(stage7_zip) as z7:
            for start, end in BASE_BLOCKS:
                stem = f"block_{start}_{end}"
                metadata_raw = zip_member(z7, stem + "_metadata.json")
                parquet_raw = zip_member(z7, stem + ".parquet")
                official_fp = manifest.get("block_fingerprints", {}).get(scenario, {}).get(f"{start}-{end}")
                if not isinstance(official_fp, str):
                    fail(f"OFFICIAL_STAGE7_BLOCK_FINGERPRINT_MISSING {scenario}/{start}-{end}")
                rows, block_ev = verify_source_block(scenario, start, end, metadata_raw, parquet_raw, STAGE7_RUN_ID, official_fp)
                if set(source_rows).intersection(rows):
                    fail(f"STAGE7_DUPLICATE_TRIAL_KEYS {scenario}/{start}-{end}")
                source_rows.update(rows)
                base_raw[stem] = (metadata_raw, parquet_raw)
                block_evidence.append(block_ev)
        if sorted(source_rows) != list(range(1, 451)):
            fail(f"STAGE7_COVERAGE_MISMATCH {scenario}")

        with zipfile.ZipFile(stage10_zip) as z10:
            for start, end in BASE_BLOCKS:
                stem = f"block_{start}_{end}"
                if zip_member(z10, stem + "_metadata.json") != base_raw[stem][0] or zip_member(z10, stem + ".parquet") != base_raw[stem][1]:
                    fail(f"STAGE10_BASE_1_450_NOT_BYTE_IDENTICAL_TO_STAGE7 {scenario}/{stem}")
            metadata_raw = zip_member(z10, "block_451_550_metadata.json")
            parquet_raw = zip_member(z10, "block_451_550.parquet")
            stage10_rows, ext_ev = verify_source_block(scenario, 451, 550, metadata_raw, parquet_raw, STAGE10_RUN_ID, None, allow_stage10_suffix=True)
            meta, suffix_mode = parse_json_bytes(metadata_raw, allow_known_stage10_suffix=True)
            baseline_fp = manifest.get("scenarios", {}).get(scenario, {}).get("scenario_fingerprint")
            combined_fp = identity.get("per_scenario", {}).get(scenario, {}).get("combined_dataset_fingerprint_sha256_stage10")
            if meta.get("baseline_fingerprint_sha256") != baseline_fp or meta.get("combined_fingerprint_sha256") != combined_fp:
                fail(f"STAGE10_BASELINE_OR_COMBINED_FINGERPRINT_MISMATCH {scenario}")
            metrics_raw = zip_member(z10, "metrics.json")
            resume_raw = zip_member(z10, "resume_descriptor.json")
            metrics, metrics_mode = parse_json_bytes(metrics_raw, allow_known_stage10_suffix=True)
            resume, resume_mode = parse_json_bytes(resume_raw, allow_known_stage10_suffix=True)
            known_mode = "known_stage10_literal_backslash_n_suffix_removed_in_memory"
            if suffix_mode != known_mode or metrics_mode != known_mode or resume_mode != known_mode:
                fail(f"STAGE10_KNOWN_SUFFIX_PATTERN_CHANGED {scenario}")
            metrics_ok = (
                metrics.get("scenario") == scenario and metrics.get("mode") == "canonical"
                and metrics.get("source_sha") == SOURCE_SHA and int(metrics.get("master_seed", -1)) == MASTER_SEED
                and str(metrics.get("expected_source_run_id")) == str(STAGE7_RUN_ID)
                and str(metrics.get("benchmark_run_id")) == str(STAGE10_RUN_ID)
                and metrics.get("canonical_trial_range") == [451, 550]
                and int(metrics.get("canonical_trials_added", -1)) == 100
                and int(metrics.get("executions_completed", -1)) == 100
                and int(metrics.get("executions_failed", -1)) == 0
                and metrics.get("errors") == [] and metrics.get("final_dataset_fingerprint_sha256") == combined_fp
            )
            resume_ok = (
                resume.get("schema_version") == "stage10-resume-v1" and resume.get("scenario") == scenario
                and resume.get("source_sha") == SOURCE_SHA and int(resume.get("master_seed", -1)) == MASTER_SEED
                and int(resume.get("baseline_trials", -1)) == 450
                and int(resume.get("canonical_trials_added", -1)) == 100
                and resume.get("new_trial_range") == [451, 550]
                and resume.get("baseline_fingerprint_sha256") == baseline_fp
                and resume.get("combined_dataset_fingerprint_sha256") == combined_fp
                and int(resume.get("next_trial_id", -1)) == 551
            )
            if not metrics_ok or not resume_ok:
                fail(f"STAGE10_METRICS_OR_RESUME_IDENTITY_INVALID {scenario} metrics={metrics_ok} resume={resume_ok}")
            combined = list(source_rows.values()) + list(stage10_rows.values())
            actual_combined = canonical_fingerprint(combined)
            if actual_combined != combined_fp:
                fail(f"STAGE10_COMBINED_FINGERPRINT_RECOMPUTE_MISMATCH {scenario}")
            block_evidence.append(ext_ev)
        if set(source_rows).intersection(stage10_rows):
            fail(f"HISTORICAL_SOURCE_TRIAL_OVERLAP {scenario}")
        source_rows.update(stage10_rows)
        if sorted(source_rows) != list(HISTORICAL_IDS):
            fail(f"HISTORICAL_SOURCE_COVERAGE_MISMATCH {scenario}")
        for trial_id, row in source_rows.items():
            check_metric_row(row, scenario, trial_id)

        roll_scenario = roll.get("scenarios", {}).get(scenario)
        closure_scenario = closure.get("scenarios", {}).get(scenario)
        if not isinstance(roll_scenario, dict) or not isinstance(closure_scenario, dict):
            fail(f"STAGE12_SCENARIO_REPORT_MISSING {scenario}")
        if roll_scenario.get("content_sha256") != closure_scenario.get("content_sha256"):
            fail(f"STAGE12_VALIDATION_REPORT_SHA_DISAGREEMENT {scenario}")
        if roll_scenario.get("content_sha256_matches_cp12b_manifest") is not True or closure_scenario.get("content_sha256_matches_cp12c_report") is not True:
            fail(f"STAGE12_REPORT_SOURCE_HASH_GATE_NOT_PASS {scenario}")
        if int(roll_scenario.get("trials", -1)) != 550 or int(closure_scenario.get("trial_count", -1)) != 550:
            fail(f"STAGE12_REPORTED_TRIAL_COUNT_MISMATCH {scenario}")

        with zipfile.ZipFile(stage12_zip) as z12:
            parquet_names = [n for n in z12.namelist() if n.endswith(".parquet")]
            if parquet_names != [f"{scenario}.parquet"]:
                fail(f"STAGE12_ARCHIVE_PARQUET_MEMBERS_INVALID {scenario} {parquet_names}")
            if any(n.startswith("/") or ".." in Path(n).parts for n in parquet_names):
                fail(f"STAGE12_ARCHIVE_PATH_INVALID {scenario}")
            daily_raw = zip_member(z12, parquet_names[0])
        daily_file_sha = sha_bytes(daily_raw)
        expected_daily_sha = roll_scenario.get("content_sha256")
        if daily_file_sha != expected_daily_sha or daily_file_sha != closure_scenario.get("content_sha256"):
            fail(f"STAGE12_PARQUET_FILE_SHA_MISMATCH {scenario}")
        parquet_file = pq.ParquetFile(BytesIO(daily_raw))
        schema = parquet_file.schema_arrow
        if {field.name: str(field.type) for field in schema} != COLUMN_TYPES:
            fail(f"STAGE12_SCHEMA_TYPE_MISMATCH {scenario}")
        if any(field.nullable != (field.name == "Final_Close_Date") for field in schema):
            fail(f"STAGE12_SCHEMA_NULLABILITY_MISMATCH {scenario}")
        identity_raw = (schema.metadata or {}).get(IDENTITY_KEY)
        if identity_raw is None or json.loads(identity_raw.decode("utf-8")) != expected_historical_identity(scenario):
            fail(f"STAGE12_DATASET_IDENTITY_MISMATCH {scenario}")
        expected_daily_rows = int(roll_scenario.get("daily_rows", -1))
        if expected_daily_rows < 1 or expected_daily_rows != int(closure_scenario.get("daily_rows", -2)):
            fail(f"STAGE12_DAILY_ROW_COUNT_REPORT_MISMATCH {scenario}")

        trial_checks = []
        current_id = None
        current_hash = None
        first_day = None
        last_day = None
        day_count = 0
        daily_rows = 0
        def close_daily_trial() -> None:
            nonlocal current_id, current_hash, first_day, last_day, day_count
            if current_id is None:
                return
            if first_day != date(2027, 1, 1):
                fail(f"STAGE12_FIRST_DATE_MISMATCH {scenario}/{current_id} date={first_day}")
            if last_day is None or day_count != (last_day - first_day).days + 1:
                fail(f"STAGE12_DAILY_GAP_OR_DUPLICATE {scenario}/{current_id}")
            row = source_rows.get(current_id)
            if row is None:
                fail(f"HISTORICAL_TRIAL_RESULT_MISSING {scenario}/{current_id}")
            golden_hash = row_sha(row)
            if current_hash != golden_hash:
                fail(f"STAGE12_TRIAL_FINGERPRINT_MISMATCH {scenario}/{current_id} daily={current_hash} result={golden_hash}")
            trial_checks.append({"trial_id": current_id, "result_sha256": current_hash, "daily_rows": day_count})
        for batch in parquet_file.iter_batches(batch_size=65536, columns=["scenario_id", "trial_id", "date", "source_sha", "master_seed", "result_sha256"]):
            for daily in batch.to_pylist():
                daily_rows += 1
                trial_id = int(daily["trial_id"])
                if daily["scenario_id"] != scenario or daily["source_sha"] != SOURCE_SHA or int(daily["master_seed"]) != MASTER_SEED:
                    fail(f"STAGE12_ROW_IDENTITY_MISMATCH {scenario}/{trial_id}")
                digest = daily["result_sha256"]
                if not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None:
                    fail(f"STAGE12_RESULT_HASH_INVALID {scenario}/{trial_id}")
                day = date.fromisoformat(daily["date"])
                if current_id is None or trial_id != current_id:
                    if current_id is not None:
                        close_daily_trial()
                    expected_id = len(trial_checks) + 1
                    if trial_id != expected_id:
                        fail(f"STAGE12_TRIAL_ID_SEQUENCE_MISMATCH {scenario} expected={expected_id} actual={trial_id}")
                    current_id = trial_id
                    current_hash = digest
                    first_day = day
                    last_day = day
                    day_count = 1
                else:
                    if day != last_day + timedelta(days=1):
                        fail(f"STAGE12_DAILY_DATE_GAP_OR_DUPLICATE {scenario}/{trial_id}/{day}")
                    if digest != current_hash:
                        fail(f"STAGE12_RESULT_HASH_DRIFT_WITHIN_TRIAL {scenario}/{trial_id}")
                    last_day = day
                    day_count += 1
        close_daily_trial()
        if len(trial_checks) != 550 or [r["trial_id"] for r in trial_checks] != list(HISTORICAL_IDS):
            fail(f"STAGE12_TRIAL_COVERAGE_MISMATCH {scenario}")
        if daily_rows != expected_daily_rows:
            fail(f"STAGE12_DAILY_ROW_COUNT_MISMATCH {scenario} actual={daily_rows} expected={expected_daily_rows}")

        history_rows = []
        for trial_id in sorted(source_rows):
            row = source_rows[trial_id]
            history_rows.append({
                "scenario_id": scenario, "trial_id": trial_id, "trial_result": row,
                "result_sha256": row_sha(row), "source_sha": SOURCE_SHA, "master_seed": MASTER_SEED,
                "origin": "historical_stage7" if trial_id <= 450 else "historical_stage10",
                "historical_provenance": {
                    "stage7_run_id": STAGE7_RUN_ID, "stage7_head_sha": STAGE7_HEAD,
                    "stage10_run_id": STAGE10_RUN_ID if trial_id > 450 else None,
                    "stage10_head_sha": STAGE10_HEAD if trial_id > 450 else None,
                    "stage12_run_id": STAGE12_RUN_ID, "stage12_head_sha": STAGE12_HEAD,
                    "schema_version": SCHEMA_VERSION, "stage12_parquet_sha256": daily_file_sha,
                    "stage12_result_sha256_match": True,
                },
            })
        report.update({
            "status": "PASS", "historical_trial_count": len(history_rows),
            "daily_rows_checked": daily_rows, "stage12_parquet_sha256": daily_file_sha,
            "stage7_artifact": art7_evidence, "stage10_artifact": art10_evidence,
            "stage12_artifact": art12_evidence, "source_blocks": block_evidence,
            "source_trial_rows_rehashed": 550, "stage12_exact_trial_hash_matches": 550,
            "stage10_run_conclusion": live10["conclusion"],
            "stage10_run_identity_deviation": {
                "classification": "K_CODE",
                "recorded_stage11_branch_head_sha": stage10_recorded_head,
                "live_run_api_head_sha": STAGE10_HEAD,
                "recorded_head_length": len(stage10_recorded_head) if isinstance(stage10_recorded_head, str) else None,
                "live_head_length": len(STAGE10_HEAD),
                "disposition": "Historical metadata was not edited; live run API head, per-scenario job, artifact digest, source identity and row hashes were checked."
            },
            "historical_rows": history_rows,
            "live_runs": {"stage7": live7, "stage10": live10, "stage12": live12},
        })
    except Exception as exc:
        report["status"] = "FAIL"
        report["errors"] = [str(exc)]
        report["error_type"] = type(exc).__name__
    return report


def verify_n300_checkpoint(temp_dir: Path) -> dict[str, Any]:
    validate_live_run(N300_RUN_ID, "4d979ff4de178ed07c81ef26a0707c14e1de15ee", "success")
    artifacts, _ = list_artifacts(N300_RUN_ID)
    found = [a for a in artifacts.values() if int(a.get("id", -1)) == N300_ARTIFACT_ID]
    if len(found) != 1 or found[0].get("name") != "gateb-historical-300-n300-report":
        fail("N300_CHECKPOINT_ARTIFACT_IDENTITY_MISMATCH")
    archive = temp_dir / "n300.zip"
    event = download_artifact(found[0], archive)
    with zipfile.ZipFile(archive) as zf:
        raw = zip_member_basename(zf, "gate_b_n300_report.json")
    report, _ = parse_json_bytes(raw)
    if report.get("status") != "PASS_AT_N300_ONLY" or report.get("overall_gate_b") != "NOT_ESTABLISHED_BY_N300_ALONE":
        fail("N300_CHECKPOINT_STATUS_INVALID")
    if int(report.get("scenario_count_verified", -1)) != 20 or int(report.get("historical_trial_inputs_verified", -1)) != 6000:
        fail("N300_CHECKPOINT_COVERAGE_INVALID")
    if int(report.get("metric_points_reported", -1)) != 60 or report.get("gate_b_pass") is not False:
        fail("N300_CHECKPOINT_METRIC_OR_FINAL_GATE_STATUS_INVALID")
    return {"run_id": N300_RUN_ID, "artifact_id": N300_ARTIFACT_ID, "status": report["status"], "metrics": report["metric_points_reported"], "inputs": report["historical_trial_inputs_verified"], **event}


def preflight() -> dict[str, Any]:
    main_ref = gh_json(f"repos/{REPO}/git/ref/heads/main")
    live_main = main_ref.get("object", {}).get("sha")
    if live_main != PINNED_MAIN_SHA:
        fail(f"MAIN_MOVED_SINCE_R4 expected={PINNED_MAIN_SHA} actual={live_main}")
    stage7 = validate_live_run(STAGE7_RUN_ID, STAGE7_HEAD, "success")
    stage10 = validate_live_run(STAGE10_RUN_ID, STAGE10_HEAD, "failure")
    stage12 = validate_live_run(STAGE12_RUN_ID, STAGE12_HEAD, "success")
    with tempfile.TemporaryDirectory(prefix="gateb-n600-preflight-") as tmp:
        checkpoint = verify_n300_checkpoint(Path(tmp))
    return {
        "status": "PASS", "main_sha": live_main, "source_sha": SOURCE_SHA,
        "master_seed": MASTER_SEED, "stage7": stage7, "stage10": stage10,
        "stage12": stage12, "n300_checkpoint": checkpoint,
        "scope": "N=600 only; historical IDs 1..550 analytic inputs; only IDs 551..600 may be newly materialized."
    }


def validate_trial_payload(payload: dict[str, Any], scenario: str, trial_id: int, expected_run_id: int | None = None) -> None:
    row = payload.get("trial_result")
    if not isinstance(row, dict):
        fail(f"NEW_TRIAL_ROW_MISSING {scenario}/{trial_id}")
    check_metric_row(row, scenario, trial_id)
    if payload.get("scenario_id") != scenario or int(payload.get("trial_id", -1)) != trial_id:
        fail(f"NEW_TRIAL_ENVELOPE_KEY_MISMATCH {scenario}/{trial_id}")
    if payload.get("source_sha") != SOURCE_SHA or int(payload.get("master_seed", -1)) != MASTER_SEED:
        fail(f"NEW_TRIAL_SOURCE_OR_SEED_MISMATCH {scenario}/{trial_id}")
    if payload.get("source_commit") != SOURCE_COMMIT or payload.get("log_events") is not False:
        fail(f"NEW_TRIAL_SOURCE_COMMIT_OR_LOG_POLICY_MISMATCH {scenario}/{trial_id}")
    if expected_run_id is not None and int(payload.get("run_id", -1)) != expected_run_id:
        fail(f"NEW_TRIAL_RUN_ID_MISMATCH {scenario}/{trial_id}")
    actual = row_sha(row)
    if payload.get("result_sha256") != actual:
        fail(f"NEW_TRIAL_RESULT_HASH_MISMATCH {scenario}/{trial_id}")
    for metric in METRICS.values():
        if metric not in row:
            fail(f"NEW_TRIAL_REQUIRED_METRIC_MISSING {scenario}/{trial_id}/{metric}")


def restore_previous_attempts(scenario: str, current_run_id: int, current_attempt: int, destination: Path) -> dict[int, dict[str, Any]]:
    artifacts, _ = list_artifacts(current_run_id)
    prefix = f"gateb-n600-new-{scenario}-attempt-"
    restored: dict[int, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix=f"gateb-n600-restore-{scenario}-") as tmp:
        for name, artifact in sorted(artifacts.items()):
            if not name.startswith(prefix):
                continue
            suffix = name[len(prefix):]
            if not suffix.isdigit() or int(suffix) >= current_attempt:
                continue
            archive = Path(tmp) / f"{name}.zip"
            download_artifact(artifact, archive)
            with zipfile.ZipFile(archive) as zf:
                for member in zf.namelist():
                    basename = Path(member).name
                    if not re.fullmatch(r"trial_[0-9]{5}\.json", basename):
                        continue
                    if member.startswith("/") or ".." in Path(member).parts:
                        fail(f"PRIOR_NEW_TRIAL_ARTIFACT_PATH_INVALID {name}/{member}")
                    payload = json.loads(zf.read(member).decode("utf-8"))
                    trial_id = int(payload.get("trial_id", -1))
                    if trial_id not in NEW_IDS:
                        fail(f"PRIOR_NEW_TRIAL_ID_OUT_OF_RANGE {scenario}/{trial_id}")
                    validate_trial_payload(payload, scenario, trial_id, current_run_id)
                    if trial_id in restored:
                        fail(f"DUPLICATE_COMPLETED_NEW_TRIAL_ID {scenario}/{trial_id}; refusing to rerun or silently deduplicate")
                    restored[trial_id] = payload
    for trial_id, payload in restored.items():
        _ = destination  # restored records remain in prior-attempt artifacts; they are not re-uploaded.
        print(f"RESTORED_ALREADY_COMPLETED_TRIAL={scenario}/{trial_id} hash={payload['result_sha256']}")
    return restored


def run_new_trials(scenario: str, source_root: Path, output_root: Path) -> dict[str, Any]:
    if scenario not in SCENARIOS:
        fail(f"UNSUPPORTED_SCENARIO {scenario}")
    source_root = source_root.resolve()
    git = subprocess.run(["git", "-C", str(source_root), "rev-parse", "HEAD"], text=True, capture_output=True, check=False)
    if git.returncode or git.stdout.strip() != SOURCE_COMMIT:
        fail(f"PINNED_SOURCE_CHECKOUT_MISMATCH expected={SOURCE_COMMIT} actual={git.stdout.strip()}")
    sys.path.insert(0, str(source_root))
    import constants
    import daily_engine
    import monte_carlo
    if int(constants.MASTER_SEED) != MASTER_SEED:
        fail("SOURCE_MASTER_SEED_CONSTANT_MISMATCH")
    if Path(daily_engine.__file__).resolve().parent != source_root:
        fail("DAILY_ENGINE_NOT_IMPORTED_FROM_PINNED_SOURCE_CHECKOUT")

    run_id = int(os.environ["GITHUB_RUN_ID"])
    attempt = int(os.environ["GITHUB_RUN_ATTEMPT"])
    output_dir = output_root / "trial_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    prior = restore_previous_attempts(scenario, run_id, attempt, output_dir)
    missing = [trial_id for trial_id in NEW_IDS if trial_id not in prior]
    collection_probability, recovery_rate_pct = monte_carlo.parse_scenario_id(scenario)
    completed_now = []
    for trial_id in missing:
        project = daily_engine.run_deterministic_trial(
            recovery_rate_pct=recovery_rate_pct, trial_id=trial_id, scenario_id=scenario,
            master_seed=MASTER_SEED, collection_probability=collection_probability, log_events=False,
        )
        result = monte_carlo._trial_result_from_project(
            project, scenario_id=scenario, collection_probability=collection_probability,
            recovery_rate_pct=recovery_rate_pct, trial_id=trial_id,
        )
        row = __import__("dataclasses").asdict(result)
        payload = {
            "scenario_id": scenario, "trial_id": trial_id, "trial_result": row,
            "result_sha256": row_sha(row), "source_sha": SOURCE_SHA, "master_seed": MASTER_SEED,
            "source_commit": SOURCE_COMMIT, "run_id": run_id, "run_attempt": attempt,
            "log_events": False, "origin": "new_stage12_gateb_n600",
        }
        validate_trial_payload(payload, scenario, trial_id, run_id)
        path = output_dir / f"trial_{trial_id:05d}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        temporary.replace(path)
        completed_now.append(trial_id)
        print(f"NEW_TRIAL_MATERIALIZED={scenario}/{trial_id} result_sha256={payload['result_sha256']} run_id={run_id} attempt={attempt}")
    return {
        "scenario_id": scenario, "run_id": run_id, "run_attempt": attempt,
        "source_sha": SOURCE_SHA, "source_commit": SOURCE_COMMIT, "master_seed": MASTER_SEED,
        "historical_ids_rerun": False, "completed_before_attempt": sorted(prior),
        "new_ids_materialized_this_attempt": completed_now,
        "remaining_ids": sorted(set(NEW_IDS) - set(prior) - set(completed_now)),
        "status": "PASS" if set(prior) | set(completed_now) == set(NEW_IDS) else "PARTIAL_PRESERVED_FOR_RETRY",
    }


def aggregate_historical(input_root: Path, output_file: Path) -> dict[str, Any]:
    report_files = list(input_root.rglob("*.json"))
    reports = {}
    for path in report_files:
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        scenario = item.get("scenario_id")
        if scenario in SCENARIOS:
            if scenario in reports:
                fail(f"DUPLICATE_HISTORICAL_SCENARIO_REPORT {scenario}")
            reports[scenario] = item
    missing = sorted(set(SCENARIOS) - set(reports))
    if missing:
        fail(f"HISTORICAL_SCENARIO_REPORTS_MISSING {missing}")
    scenario_rows: dict[str, list[dict[str, Any]]] = {}
    report_summary = {}
    for scenario in SCENARIOS:
        item = reports[scenario]
        if item.get("status") != "PASS" or item.get("simulation_or_trial_executed") is not False or item.get("historical_dataset_modified") is not False:
            fail(f"HISTORICAL_SCENARIO_GATE_NOT_PASS {scenario} status={item.get('status')} errors={item.get('errors')}")
        rows = item.get("historical_rows")
        if not isinstance(rows, list) or len(rows) != 550:
            fail(f"HISTORICAL_SCENARIO_COUNT_INVALID {scenario}")
        ids = []
        for record in rows:
            trial_id = int(record.get("trial_id", -1))
            if record.get("scenario_id") != scenario or trial_id not in HISTORICAL_IDS:
                fail(f"HISTORICAL_ROW_KEY_INVALID {scenario}/{trial_id}")
            validate_trial_payload({
                "scenario_id": scenario, "trial_id": trial_id,
                "trial_result": record.get("trial_result"), "result_sha256": record.get("result_sha256"),
                "source_sha": record.get("source_sha"), "master_seed": record.get("master_seed"),
                "source_commit": SOURCE_COMMIT, "log_events": False,
            }, scenario, trial_id)
            ids.append(trial_id)
        if ids != list(HISTORICAL_IDS):
            fail(f"HISTORICAL_TRIAL_ID_COVERAGE_OR_ORDER_INVALID {scenario}")
        scenario_rows[scenario] = rows
        report_summary[scenario] = {
            "status": item["status"], "historical_trials": len(rows),
            "stage12_parquet_sha256": item["stage12_parquet_sha256"],
            "stage12_exact_trial_hash_matches": item["stage12_exact_trial_hash_matches"],
            "stage7_archive_sha256": item["stage7_artifact"]["archive_sha256"],
            "stage10_archive_sha256": item["stage10_artifact"]["archive_sha256"],
        }
    fingerprint_entries = sorted(
        (scenario, int(row["trial_id"]), row["result_sha256"])
        for scenario, rows in scenario_rows.items() for row in rows
    )
    fingerprint_sha = sha_bytes("".join(f"{scenario}|{trial_id}|{digest}\n" for scenario, trial_id, digest in fingerprint_entries).encode("utf-8"))
    out = {
        "status": "PASS", "scope": "historical analytic inputs only; no trial executed; no dataset/metadata modified",
        "source_sha": SOURCE_SHA, "source_commit": SOURCE_COMMIT, "master_seed": MASTER_SEED,
        "stage12_run_id": STAGE12_RUN_ID, "scenario_count": len(SCENARIOS),
        "historical_trial_count": len(fingerprint_entries), "trial_id_range_per_scenario": [1, 550],
        "ordered_scenario_trial_hash_map_sha256": fingerprint_sha,
        "scenarios": scenario_rows, "scenario_evidence": report_summary,
    }
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"status": out["status"], "scenarios": out["scenario_count"], "historical_trials": out["historical_trial_count"], "ordered_scenario_trial_hash_map_sha256": fingerprint_sha}, indent=2))
    return out


def aggregate_n600(historical_file: Path, new_root: Path, output_file: Path) -> dict[str, Any]:
    historical = json.loads(historical_file.read_text(encoding="utf-8"))
    if historical.get("status") != "PASS" or int(historical.get("scenario_count", -1)) != 20 or int(historical.get("historical_trial_count", -1)) != 11000:
        fail("HISTORICAL_AGGREGATE_GATE_NOT_PASS")
    history_scenarios = historical.get("scenarios", {})
    if sorted(history_scenarios) != sorted(SCENARIOS):
        fail("HISTORICAL_AGGREGATE_SCENARIO_KEYS_INVALID")
    new_rows: dict[str, dict[int, dict[str, Any]]] = {s: {} for s in SCENARIOS}
    new_provenance: dict[str, list[dict[str, Any]]] = {s: [] for s in SCENARIOS}
    for path in sorted(new_root.rglob("trial_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        scenario = payload.get("scenario_id")
        if scenario not in SCENARIOS:
            continue
        trial_id = int(payload.get("trial_id", -1))
        if trial_id not in NEW_IDS:
            fail(f"NEW_TRIAL_ID_OUT_OF_RANGE {scenario}/{trial_id}")
        validate_trial_payload(payload, scenario, trial_id)
        if trial_id in new_rows[scenario]:
            fail(f"DUPLICATE_NEW_TRIAL_ID {scenario}/{trial_id}")
        new_rows[scenario][trial_id] = payload
        new_provenance[scenario].append({
            "trial_id": trial_id, "result_sha256": payload["result_sha256"],
            "run_id": payload.get("run_id"), "run_attempt": payload.get("run_attempt"),
            "source_commit": payload.get("source_commit"),
        })

    all_points = []
    scenario_summaries = []
    p50_final_equity = {}
    all_rows_fingerprint_entries = []
    undefined = []
    statistical_failures = []
    for scenario in SCENARIOS:
        hist_rows = history_scenarios[scenario]
        if len(hist_rows) != 550 or [int(r["trial_id"]) for r in hist_rows] != list(HISTORICAL_IDS):
            fail(f"HISTORICAL_TRIAL_SEQUENCE_INVALID_FOR_N600 {scenario}")
        additions = new_rows[scenario]
        if sorted(additions) != list(NEW_IDS):
            fail(f"NEW_TRIAL_COVERAGE_INVALID {scenario} missing={sorted(set(NEW_IDS)-set(additions))} extra={sorted(set(additions)-set(NEW_IDS))}")
        values_by_metric = {metric: [] for metric in METRICS.values()}
        for record in hist_rows:
            payload = record
            row = payload["trial_result"]
            validate_trial_payload({
                "scenario_id": scenario, "trial_id": record["trial_id"], "trial_result": row,
                "result_sha256": record["result_sha256"], "source_sha": SOURCE_SHA,
                "master_seed": MASTER_SEED, "source_commit": SOURCE_COMMIT, "log_events": False,
            }, scenario, int(record["trial_id"]))
            all_rows_fingerprint_entries.append((scenario, int(record["trial_id"]), record["result_sha256"]))
            for field in values_by_metric:
                values_by_metric[field].append(int(row[field]))
        for trial_id in sorted(additions):
            payload = additions[trial_id]
            row = payload["trial_result"]
            all_rows_fingerprint_entries.append((scenario, trial_id, payload["result_sha256"]))
            for field in values_by_metric:
                values_by_metric[field].append(int(row[field]))
        for field, values in values_by_metric.items():
            if len(values) != 600:
                fail(f"N600_METRIC_SAMPLE_COUNT_MISMATCH {scenario}/{field} n={len(values)}")
        final_values = np.asarray(values_by_metric["final_net_project_equity"], dtype=np.float64)
        p50 = float(np.quantile(final_values, 0.50, method="linear"))
        p50_final_equity[scenario] = p50
        metric_points = []
        for metric_label, field in METRICS.items():
            values = np.asarray(values_by_metric[field], dtype=np.float64)
            n = int(values.size)
            mean = float(values.mean())
            sample_std = float(values.std(ddof=1))
            t_critical = float(t.ppf(0.975, df=n - 1))
            half_width = float(t_critical * sample_std / math.sqrt(n))
            point_status = "UNDEFINED_BUSINESS_RULE" if abs(mean) <= EPSILON else ("PASS" if half_width < 0.01 * abs(mean) else "FAIL")
            point = {
                "scenario_id": scenario, "metric": metric_label, "field": field,
                "n": n, "df": n - 1, "confidence": 0.95, "distribution": "Student-t",
                "t_critical": t_critical, "mean": mean, "sample_std_ddof1": sample_std,
                "ci_half_width_95": half_width, "relative_half_width": None if mean == 0 else half_width / abs(mean),
                "ci_absolute_epsilon": EPSILON,
                "required_half_width": None if abs(mean) <= EPSILON else 0.01 * abs(mean),
                "inequality": "ci_half_width_95 < 0.01 * abs(mean)",
                "status": point_status,
            }
            metric_points.append(point)
            all_points.append(point)
            if point_status == "UNDEFINED_BUSINESS_RULE":
                undefined.append({"scenario_id": scenario, "metric": metric_label, "mean": mean, "ci_half_width_95": half_width, "classification": point_status})
            elif point_status == "FAIL":
                statistical_failures.append({"scenario_id": scenario, "metric": metric_label, "half_width": half_width, "required_half_width": point["required_half_width"]})
        scenario_summaries.append({
            "scenario_id": scenario, "historical_trial_count": 550, "new_trial_count": 50,
            "trial_count_at_checkpoint": 600, "p50_final_net_project_equity": p50,
            "metrics": metric_points,
            "new_trial_attempts": sorted(new_provenance[scenario], key=lambda item: item["trial_id"]),
        })

    if len(all_rows_fingerprint_entries) != 12000 or len({(s, i) for s, i, _ in all_rows_fingerprint_entries}) != 12000:
        fail("N600_GLOBAL_TRIAL_KEY_COVERAGE_INVALID")
    global_map_sha = sha_bytes("".join(f"{scenario}|{trial_id}|{digest}\n" for scenario, trial_id, digest in sorted(all_rows_fingerprint_entries)).encode("utf-8"))
    if undefined:
        checkpoint_status = "HOLD_UNDEFINED_BUSINESS_RULE"
    elif statistical_failures:
        checkpoint_status = "FAIL_AT_N600_ESCALATE_TO_N1200"
    else:
        checkpoint_status = "PASS_AT_N600_ONLY"
    out = {
        "status": "PASS" if checkpoint_status == "PASS_AT_N600_ONLY" else ("HOLD" if checkpoint_status == "HOLD_UNDEFINED_BUSINESS_RULE" else "CHECKPOINT_COMPLETE_ESCALATION_REQUIRED"),
        "checkpoint": "N=600", "checkpoint_status": checkpoint_status,
        "overall_gate_b": "NOT_ESTABLISHED_BY_N600_ALONE",
        "gate_a": "SEPARATE_GATE_NOT_PROMOTED_BY_THIS_CP",
        "statistical_policy_source": "D-2026-10-10-01; D-2026-10-11-02 authorizes historical analytical inputs 1..550 only",
        "source_sha": SOURCE_SHA, "source_commit_for_new_trials": SOURCE_COMMIT, "master_seed": MASTER_SEED,
        "historical_stage12_run_id": STAGE12_RUN_ID,
        "new_trial_run_id": int(os.environ.get("GITHUB_RUN_ID", "-1")),
        "new_trial_run_attempt": int(os.environ.get("GITHUB_RUN_ATTEMPT", "-1")),
        "scenario_count": 20, "historical_inputs_expected": 11000, "historical_inputs_verified": 11000,
        "new_trials_expected": 1000, "new_trials_verified": 1000,
        "trial_keys_expected": 12000, "trial_keys_verified": len(all_rows_fingerprint_entries),
        "ordered_scenario_trial_hash_map_sha256_n600": global_map_sha,
        "ci_points_expected": 60, "ci_points_reported": len(all_points),
        "passed_ci_points": sum(p["status"] == "PASS" for p in all_points),
        "failed_ci_points": sum(p["status"] == "FAIL" for p in all_points),
        "undefined_ci_points": sum(p["status"] == "UNDEFINED_BUSINESS_RULE" for p in all_points),
        "undefined_business_rules": undefined, "failed_ci_points_detail": statistical_failures,
        "p50_final_net_project_equity_by_scenario": p50_final_equity,
        "scenarios": scenario_summaries, "checkpoint_metrics": all_points,
        "no_historical_trial_rerun": True, "historical_dataset_modified": False,
        "historical_metadata_modified": False, "historical_identity_changed": False,
        "new_trials_run_once_per_missing_id_with_per_trial_result_hash": True,
        "limitations": [
            "This is the N=600 checkpoint only; Gate B requires three consecutive successful checkpoints and is not declared final here.",
            "Gate A remains a separate acceptance gate; this report does not merge or promote PR #30.",
            "D-2026-10-10-01 has a P50 >5% comparison condition after N=300/600/1200 but its exact percentage-change denominator/formula is not defined in the decision text. Do not invent it if that condition must be evaluated at N=1200.",
            "If abs(mean) <= CI_ABSOLUTE_EPSILON=1, the exact near-zero inequality remains UNDEFINED_BUSINESS_RULE and is held rather than guessed.",
        ],
    }
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(out, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "checkpoint_status": checkpoint_status, "overall_gate_b": out["overall_gate_b"],
        "scenarios": out["scenario_count"], "historical_trials": out["historical_inputs_verified"],
        "new_trials": out["new_trials_verified"], "ci_points": len(all_points),
        "passed_ci_points": out["passed_ci_points"], "failed_ci_points": out["failed_ci_points"],
        "undefined_ci_points": out["undefined_ci_points"], "global_sha256": global_map_sha,
        "report": str(output_file),
    }, indent=2))
    # A statistically failing checkpoint is a completed checkpoint, not an identity/workflow failure.
    if checkpoint_status == "HOLD_UNDEFINED_BUSINESS_RULE":
        return out
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--verify-historical", action="store_true")
    parser.add_argument("--aggregate-historical", action="store_true")
    parser.add_argument("--run-new-trials", action="store_true")
    parser.add_argument("--aggregate-n600", action="store_true")
    parser.add_argument("--scenario")
    parser.add_argument("--output-root", default="gateb_n600")
    parser.add_argument("--input-root")
    parser.add_argument("--historical-file")
    parser.add_argument("--new-root")
    parser.add_argument("--source-root")
    parser.add_argument("--output-file")
    args = parser.parse_args()

    if args.preflight:
        result = preflight()
        Path(args.output_file or "gateb_n600/preflight.json").parent.mkdir(parents=True, exist_ok=True)
        Path(args.output_file or "gateb_n600/preflight.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, indent=2))
        return 0
    if args.verify_historical:
        if args.scenario not in SCENARIOS:
            parser.error("--verify-historical requires one supported --scenario")
        outroot = Path(args.output_root)
        outroot.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=f"gateb-n600-historical-{args.scenario}-") as tmp:
            result = verify_historical_scenario(args.scenario, Path(tmp))
        outroot.joinpath(f"{args.scenario}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({k: result.get(k) for k in ("scenario_id", "status", "historical_trial_count", "daily_rows_checked", "errors")}, indent=2))
        return 0 if result.get("status") == "PASS" else 1
    if args.aggregate_historical:
        if not args.input_root or not args.output_file:
            parser.error("--aggregate-historical requires --input-root and --output-file")
        aggregate_historical(Path(args.input_root), Path(args.output_file))
        return 0
    if args.run_new_trials:
        if not args.scenario or not args.source_root:
            parser.error("--run-new-trials requires --scenario and --source-root")
        result = run_new_trials(args.scenario, Path(args.source_root), Path(args.output_root))
        print(json.dumps(result, indent=2))
        return 0
    if args.aggregate_n600:
        if not args.historical_file or not args.new_root or not args.output_file:
            parser.error("--aggregate-n600 requires --historical-file, --new-root and --output-file")
        aggregate_n600(Path(args.historical_file), Path(args.new_root), Path(args.output_file))
        return 0
    parser.error("choose exactly one operation")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
