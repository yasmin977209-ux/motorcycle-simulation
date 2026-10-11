#!/usr/bin/env python3
"""Evidence-gated N=1200 checkpoint; earlier trial IDs are analytic-only."""
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
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import t

REPO = "yasmin977209-ux/motorcycle-simulation"
PINNED_MAIN_SHA = "2325b6ae6e110d9e54e614aa9b1e255be5965375"
SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
SOURCE_COMMIT = "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
MASTER_SEED = 20270101
STAGE7_RUN_ID = 37225915321
STAGE10_RUN_ID = 37709936740
STAGE12_RUN_ID = 37964656154
STAGE7_HEAD = "e0b2fab6710833774937d778097363d7a8ee8e59"
STAGE10_HEAD = "ca73f2df37baacebbcad965fc5f433f129675820"
STAGE12_HEAD = "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
N300_RUN_ID = 38162171123
N300_HEAD = "4d979ff4de178ed07c81ef26a0707c14e1de15ee"
N300_ARTIFACT_ID = 11711110209
N600_RUN_ID = 38174743440
N600_HEAD = "61ae9e2354ff37b1d4d9d13849bd6b264cf9cfa3"
N600_HISTORY_ARTIFACT_ID = 11715099731
N600_REPORT_ARTIFACT_ID = 11715388165
N600_HISTORY_MAP_SHA = "a796c13a0e596916785e5c7af792550de28b13e4abb9a2ef2fc9255977c206b3"
N600_SAMPLE_MAP_SHA = "dd537fe96c5a8736201441e9a620db148a0d16cadae518d2a777fbc723db395f"
N600_HISTORY_ARTIFACT_DIGEST = "df47991b1e94f39c9064497df82989d60d86e88c5627405f03d428d9d9ea0ee0"
N600_REPORT_ARTIFACT_DIGEST = "67d5033a67eec27bd7a90b735c56f7f7ceff4181e32c88271dd07f39f3b8e8ae"
EXPECTED_STAGE12_GLOBAL = "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44"
EXPECTED_STAGE9A_GLOBAL = "892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6"
SCENARIOS = [f"C{c:03d}_G{g:03d}" for c in (85, 70, 50, 30) for g in (100, 70, 50, 30, 0)]
HISTORICAL_IDS = range(1, 551)
PREVIOUS_NEW_IDS = range(551, 601)
CUMULATIVE_IDS = range(1, 601)
NEW_IDS = range(601, 1201)
EXPECTED_N1200_KEYS = 24000
EXPECTED_N1200_NEW = 12000
EPSILON = 1.0
METRICS = {
    "Final_Net_Project_Equity": "final_net_project_equity",
    "Partner1_Final_Entitlement": "partner1_final_entitlement",
    "Partner2_Final_Entitlement": "partner2_final_entitlement",
}
N600_ARTIFACTS = {
    "C030_G000": (11715547143, "e84f5650af4821f5a0b30792de2d5e853a3e65cf3377c121666ef2bd89d1ccb1"),
    "C030_G030": (11715826349, "4b3482f6d5a1b67a93aaef1cc1d63aa62ff6c780917a36ae3d0b5625124f8b8e"),
    "C030_G050": (11715716652, "80348577c31b150fdfaf3b99faab6d62be7f6f81099eb555517fe3ce01efcf7a"),
    "C030_G070": (11715881097, "02741f13113b4ba631d64df679fe9f5223990fd19bb8703e7229ad1bea6f659d"),
    "C030_G100": (11714609330, "4122ab99de7e7581f76cf02f242925208ada6d11eca1ca0a9ed37bd2f11e10a0"),
    "C050_G000": (11715418067, "75ca662033458a94dee98fc07a8b9a99c5c60ce083fcafca76f274087fc77b95"),
    "C050_G030": (11714938895, "77b86fd44d7556df333e52e92a3852faabcbf40327855581c626fa1543fa2d18"),
    "C050_G050": (11715577196, "d62765b79a915292072309feef51f180ada9e03ce716c87154c2d1b79f0614f6"),
    "C050_G070": (11716135405, "4791bd2cf6c4f15907be5d5bc79933a01f25a72f69ed45057ed229ebb5416f5b"),
    "C050_G100": (11715816540, "786622e74c32e3fbcd0d341c45c28ed2ba40103e9524162027ca2e315983e3c5"),
    "C070_G000": (11714938587, "c54f120d07ebca68d1f1a7a92c78628258bc73365bd42a4dce96339e67803842"),
    "C070_G030": (11715970751, "cbf2901f032a456eee2bde74a6f0dfcdd57f1b5f3fb33c98fc3d5fe8856eb26a"),
    "C070_G050": (11716090495, "b49a0100da4dc0b3ed4caf6dbbc4e57a022fa510959c3d7d3c84dd56ecc29869"),
    "C070_G070": (11715018502, "0f0fca2e3e6ad1592ebe880e71a89373289f2410648ce5470c20e55d5d00406e"),
    "C070_G100": (11715905921, "88e57cd9c1ecb12cf90b6ace8d1d1bc596de91fcee30177625a9e8bd8ca2b89f"),
    "C085_G000": (11715133463, "e7df3451518a2952ca429b6ba0738e3c395cc017037c10c0f93080e33d50b88c"),
    "C085_G030": (11715845950, "5ed31fbb5ebbc2a50d9eb3584a2a15072d5e025964b117c20ed6b7758974bf05"),
    "C085_G050": (11714903754, "fc5485523fa75cee7fa2f79600449a6c4af6c0c4dbfbc4ce54e3668f385d2ad5"),
    "C085_G070": (11715810942, "a840ab8450f2bd0c6a7cc0216269f0d667d0767cc934ce2cc7b5e1cef3e5c52c"),
    "C085_G100": (11715636588, "d11d7342df8d4b3b659f3a25aee75a79f97e9391731bad0e15d90afa20082ad9"),
}


def fail(message: str) -> None:
    raise RuntimeError(message)


def sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def row_sha(row: dict[str, Any]) -> str:
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return sha_bytes(payload)


def valid_sha(value: Any, context: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        fail(f"INVALID_SHA256 {context} value={value!r}")
    return value


def gh_json(endpoint: str) -> dict[str, Any]:
    response = subprocess.run(["gh", "api", endpoint], text=True, capture_output=True, check=False)
    if response.returncode:
        fail(f"GH_API_FAILED endpoint={endpoint} exit={response.returncode} stderr={response.stderr[-1200:]}")
    value = json.loads(response.stdout)
    if not isinstance(value, dict):
        fail(f"GH_API_RESPONSE_NOT_OBJECT endpoint={endpoint}")
    return value


def validate_run(run_id: int, head_sha: str, conclusion: str) -> dict[str, Any]:
    data = gh_json(f"repos/{REPO}/actions/runs/{run_id}")
    if int(data.get("id", -1)) != run_id or data.get("head_sha") != head_sha:
        fail(f"RUN_IDENTITY_MISMATCH run={run_id} expected={head_sha} actual={data.get('head_sha')}")
    if data.get("status") != "completed" or data.get("conclusion") != conclusion:
        fail(f"RUN_CONCLUSION_MISMATCH run={run_id} expected={conclusion} actual={data.get('status')}/{data.get('conclusion')}")
    return {key: data.get(key) for key in ("id", "head_sha", "head_branch", "status", "conclusion", "created_at", "html_url")}


def list_artifacts(run_id: int) -> dict[str, dict[str, Any]]:
    data = gh_json(f"repos/{REPO}/actions/runs/{run_id}/artifacts?per_page=100")
    items = data.get("artifacts")
    if not isinstance(items, list) or int(data.get("total_count", -1)) != len(items):
        fail(f"ARTIFACT_LIST_INCOMPLETE run={run_id}")
    result = {}
    for item in items:
        if item.get("expired"):
            fail(f"SOURCE_ARTIFACT_EXPIRED run={run_id} artifact={item.get('id')}")
        name = item.get("name")
        if not name:
            continue
        if name in result:
            fail(f"DUPLICATE_ARTIFACT_NAME run={run_id} name={name}")
        result[name] = item
    return result


def download_artifact(artifact: dict[str, Any], target: Path, expected_digest: str | None = None) -> dict[str, Any]:
    artifact_id = int(artifact["id"])
    with target.open("wb") as stream:
        response = subprocess.run(["gh", "api", f"repos/{REPO}/actions/artifacts/{artifact_id}/zip"], stdout=stream, stderr=subprocess.PIPE, check=False)
    if response.returncode or target.stat().st_size == 0 or not zipfile.is_zipfile(target):
        fail(f"ARTIFACT_DOWNLOAD_FAILED id={artifact_id} exit={response.returncode} stderr={response.stderr.decode('utf-8', errors='replace')[-1000:]}")
    actual = sha_bytes(target.read_bytes())
    api_digest = str(artifact.get("digest") or "").removeprefix("sha256:")
    expected = expected_digest or api_digest
    if not expected or actual != expected:
        fail(f"ARTIFACT_DIGEST_MISMATCH id={artifact_id} expected={expected} actual={actual}")
    if api_digest and actual != api_digest:
        fail(f"ARTIFACT_API_DIGEST_MISMATCH id={artifact_id} api={api_digest} actual={actual}")
    return {"artifact_id": artifact_id, "name": artifact.get("name"), "archive_sha256": actual, "api_digest": artifact.get("digest")}


def zip_member_basename(zf: zipfile.ZipFile, basename: str) -> bytes:
    found = [name for name in zf.namelist() if Path(name).name == basename]
    if len(found) != 1 or found[0].startswith("/") or ".." in Path(found[0]).parts:
        fail(f"ZIP_MEMBER_INVALID basename={basename} matches={found}")
    return zf.read(found[0])


def validate_result_row(row: dict[str, Any], scenario: str, trial_id: int) -> None:
    if row.get("scenario_id") != scenario or int(row.get("trial_id", -1)) != trial_id:
        fail(f"TRIAL_ROW_KEY_MISMATCH {scenario}/{trial_id}")
    for field in METRICS.values():
        value = row.get(field)
        if isinstance(value, bool) or not isinstance(value, int):
            fail(f"TRIAL_METRIC_NOT_INTEGER {scenario}/{trial_id}/{field} value={value!r}")


def validate_trial_payload(payload: dict[str, Any], scenario: str, trial_id: int, expected_run_id: int | None = None, expected_origin: str | None = None) -> None:
    row = payload.get("trial_result")
    if not isinstance(row, dict):
        fail(f"TRIAL_RESULT_MISSING {scenario}/{trial_id}")
    validate_result_row(row, scenario, trial_id)
    if payload.get("scenario_id") != scenario or int(payload.get("trial_id", -1)) != trial_id:
        fail(f"TRIAL_ENVELOPE_KEY_MISMATCH {scenario}/{trial_id}")
    if payload.get("source_sha") != SOURCE_SHA or int(payload.get("master_seed", -1)) != MASTER_SEED:
        fail(f"TRIAL_SOURCE_OR_SEED_MISMATCH {scenario}/{trial_id}")
    if payload.get("source_commit") != SOURCE_COMMIT or payload.get("log_events") is not False:
        fail(f"TRIAL_SOURCE_COMMIT_OR_LOG_POLICY_MISMATCH {scenario}/{trial_id}")
    if expected_run_id is not None and int(payload.get("run_id", -1)) != expected_run_id:
        fail(f"TRIAL_RUN_ID_MISMATCH {scenario}/{trial_id}")
    if expected_origin is not None and payload.get("origin") != expected_origin:
        fail(f"TRIAL_ORIGIN_MISMATCH {scenario}/{trial_id}")
    actual_sha = row_sha(row)
    if valid_sha(payload.get("result_sha256"), f"{scenario}/{trial_id}") != actual_sha:
        fail(f"TRIAL_RESULT_SHA_MISMATCH {scenario}/{trial_id}")
    if "final_close_date" not in row or "final_net_project_equity" not in row:
        fail(f"TRIAL_REQUIRED_FIELDS_MISSING {scenario}/{trial_id}")


def ordered_map_sha(rows: list[dict[str, Any]]) -> str:
    entries = sorted((str(r["scenario_id"]), int(r["trial_id"]), str(r["result_sha256"])) for r in rows)
    if len({(s, i) for s, i, _ in entries}) != len(entries):
        fail("DUPLICATE_SCENARIO_TRIAL_KEY_IN_HASH_MAP")
    return sha_bytes("".join(f"{s}|{i}|{digest}\n" for s, i, digest in entries).encode("utf-8"))


def preflight() -> dict[str, Any]:
    main = gh_json(f"repos/{REPO}/git/ref/heads/main")
    live_main = main.get("object", {}).get("sha")
    if live_main != PINNED_MAIN_SHA:
        fail(f"MAIN_MOVED_SINCE_R4 expected={PINNED_MAIN_SHA} actual={live_main}")
    run300 = validate_run(N300_RUN_ID, N300_HEAD, "success")
    run600 = validate_run(N600_RUN_ID, N600_HEAD, "success")
    stage7 = validate_run(STAGE7_RUN_ID, STAGE7_HEAD, "success")
    stage10 = validate_run(STAGE10_RUN_ID, STAGE10_HEAD, "failure")
    stage12 = validate_run(STAGE12_RUN_ID, STAGE12_HEAD, "success")
    artifacts300 = list_artifacts(N300_RUN_ID)
    hit300 = [a for a in artifacts300.values() if int(a.get("id", -1)) == N300_ARTIFACT_ID and a.get("name") == "gateb-historical-300-n300-report"]
    if len(hit300) != 1:
        fail("N300_CHECKPOINT_ARTIFACT_IDENTITY_MISMATCH")
    return {
        "status": "PASS", "main_sha": live_main, "source_sha": SOURCE_SHA,
        "source_commit": SOURCE_COMMIT, "master_seed": MASTER_SEED,
        "stage7": stage7, "stage10": stage10, "stage12": stage12,
        "n300_checkpoint": {"run": run300, "artifact_id": N300_ARTIFACT_ID, "artifact_api_digest": hit300[0].get("digest")},
        "n600_checkpoint": {"run": run600, "historical_aggregate_artifact_id": N600_HISTORY_ARTIFACT_ID, "n600_report_artifact_id": N600_REPORT_ARTIFACT_ID},
        "scope": "Use IDs 1..600 as verified analytical inputs; execute only IDs 601..1200 per non-C100 scenario.",
    }


def read_n600_inputs(output_file: Path) -> dict[str, Any]:
    run600 = validate_run(N600_RUN_ID, N600_HEAD, "success")
    jobs_response = gh_json(f"repos/{REPO}/actions/runs/{N600_RUN_ID}/jobs?per_page=100")
    jobs = jobs_response.get("jobs", [])
    if int(jobs_response.get("total_count", -1)) != len(jobs) or len(jobs) != 43 or any(job.get("conclusion") != "success" for job in jobs):
        fail(f"N600_JOB_SET_NOT_ALL_SUCCESS count={len(jobs)}")
    for scenario in SCENARIOS:
        matches = [j for j in jobs if j.get("name") == f"Run missing IDs 551–600 only — {scenario}"]
        if len(matches) != 1 or matches[0].get("conclusion") != "success":
            fail(f"N600_NEW_TRIAL_JOB_NOT_SUCCESS {scenario}")

    artifacts = list_artifacts(N600_RUN_ID)
    history_matches = [a for a in artifacts.values() if int(a.get("id", -1)) == N600_HISTORY_ARTIFACT_ID and a.get("name") == "gateb-historical-inputs-aggregate"]
    report_matches = [a for a in artifacts.values() if int(a.get("id", -1)) == N600_REPORT_ARTIFACT_ID and a.get("name") == "gateb-historical-and-new-n600-report"]
    if len(history_matches) != 1 or len(report_matches) != 1:
        fail("N600_AGGREGATE_ARTIFACT_IDENTITY_MISMATCH")
    expected_names = {f"gateb-n600-new-{s}-attempt-1" for s in SCENARIOS}
    found_names = {name for name in artifacts if name.startswith("gateb-n600-new-")}
    if found_names != expected_names:
        fail(f"N600_NEW_TRIAL_ARTIFACT_SET_MISMATCH missing={sorted(expected_names-found_names)} extra={sorted(found_names-expected_names)}")
    for scenario, (expected_id, expected_digest) in N600_ARTIFACTS.items():
        name = f"gateb-n600-new-{scenario}-attempt-1"
        artifact = artifacts.get(name)
        if artifact is None or int(artifact.get("id", -1)) != expected_id or str(artifact.get("digest", "")).removeprefix("sha256:") != expected_digest:
            fail(f"N600_NEW_TRIAL_ARTIFACT_ID_OR_DIGEST_MISMATCH {scenario}")

    with tempfile.TemporaryDirectory(prefix="gateb-n1200-previous-") as tmp:
        root = Path(tmp)
        history_zip = root / "n600-history.zip"
        report_zip = root / "n600-report.zip"
        history_event = download_artifact(history_matches[0], history_zip, N600_HISTORY_ARTIFACT_DIGEST)
        report_event = download_artifact(report_matches[0], report_zip, N600_REPORT_ARTIFACT_DIGEST)
        with zipfile.ZipFile(history_zip) as zf:
            history_raw = zip_member_basename(zf, "historical_inputs.json")
        history = json.loads(history_raw.decode("utf-8"))
        if history.get("status") != "PASS" or int(history.get("scenario_count", -1)) != 20 or int(history.get("historical_trial_count", -1)) != 11000:
            fail("N600_HISTORICAL_AGGREGATE_STATUS_OR_COUNT_INVALID")
        if history.get("source_sha") != SOURCE_SHA or history.get("source_commit") != SOURCE_COMMIT or int(history.get("master_seed", -1)) != MASTER_SEED:
            fail("N600_HISTORICAL_AGGREGATE_SOURCE_IDENTITY_INVALID")
        if history.get("ordered_scenario_trial_hash_map_sha256") != N600_HISTORY_MAP_SHA:
            fail("N600_HISTORICAL_AGGREGATE_HASH_MAP_SHA_INVALID")

        with zipfile.ZipFile(report_zip) as zf:
            report_raw = zip_member_basename(zf, "gate_b_n600_report.json")
        n600_report = json.loads(report_raw.decode("utf-8"))
        if n600_report.get("checkpoint_status") != "PASS_AT_N600_ONLY" or n600_report.get("overall_gate_b") != "NOT_ESTABLISHED_BY_N600_ALONE":
            fail("N600_REPORT_STATUS_INVALID")
        if int(n600_report.get("scenario_count", -1)) != 20 or int(n600_report.get("historical_inputs_verified", -1)) != 11000 or int(n600_report.get("new_trials_verified", -1)) != 1000:
            fail("N600_REPORT_SAMPLE_COVERAGE_INVALID")
        if int(n600_report.get("ci_points_expected", -1)) != 60 or int(n600_report.get("passed_ci_points", -1)) != 60 or int(n600_report.get("failed_ci_points", -1)) != 0 or int(n600_report.get("undefined_ci_points", -1)) != 0:
            fail("N600_REPORT_CI_GATE_INVALID")
        if n600_report.get("ordered_scenario_trial_hash_map_sha256_n600") != N600_SAMPLE_MAP_SHA:
            fail("N600_REPORT_SAMPLE_HASH_MAP_INVALID")

        cumulative: dict[str, list[dict[str, Any]]] = {}
        hash_rows: list[dict[str, Any]] = []
        for scenario in SCENARIOS:
            records = history.get("scenarios", {}).get(scenario)
            if not isinstance(records, list) or len(records) != 550:
                fail(f"N600_HISTORICAL_SCENARIO_COUNT_INVALID {scenario}")
            indexed = {}
            for record in records:
                trial_id = int(record.get("trial_id", -1))
                row = record.get("trial_result")
                if trial_id not in HISTORICAL_IDS or not isinstance(row, dict) or trial_id in indexed:
                    fail(f"N600_HISTORICAL_KEY_INVALID {scenario}/{trial_id}")
                if record.get("scenario_id") != scenario or record.get("source_sha") != SOURCE_SHA or int(record.get("master_seed", -1)) != MASTER_SEED:
                    fail(f"N600_HISTORICAL_ROW_IDENTITY_INVALID {scenario}/{trial_id}")
                validate_result_row(row, scenario, trial_id)
                digest = row_sha(row)
                if record.get("result_sha256") != digest:
                    fail(f"N600_HISTORICAL_RESULT_SHA_MISMATCH {scenario}/{trial_id}")
                prov = record.get("historical_provenance", {})
                if prov.get("stage12_run_id") != STAGE12_RUN_ID or prov.get("schema_version") != "stage12-daily-accounting-v1" or prov.get("stage12_result_sha256_match") is not True:
                    fail(f"N600_HISTORICAL_PROVENANCE_INVALID {scenario}/{trial_id}")
                if record.get("origin") != ("historical_stage7" if trial_id <= 450 else "historical_stage10"):
                    fail(f"N600_HISTORICAL_ORIGIN_INVALID {scenario}/{trial_id}")
                indexed[trial_id] = {
                    "scenario_id": scenario, "trial_id": trial_id, "trial_result": row,
                    "result_sha256": digest, "source_sha": SOURCE_SHA, "source_commit": SOURCE_COMMIT,
                    "master_seed": MASTER_SEED, "origin": record["origin"],
                    "run_id": prov.get("stage7_run_id") if trial_id <= 450 else prov.get("stage10_run_id"),
                    "historical_provenance": prov,
                }
            if sorted(indexed) != list(HISTORICAL_IDS):
                fail(f"N600_HISTORICAL_TRIAL_COVERAGE_INVALID {scenario}")
            cumulative[scenario] = [indexed[i] for i in HISTORICAL_IDS]

        prior_trial_files = 0
        for scenario in SCENARIOS:
            artifact = artifacts[f"gateb-n600-new-{scenario}-attempt-1"]
            archive = root / f"{scenario}-new.zip"
            download_event = download_artifact(artifact, archive, N600_ARTIFACTS[scenario][1])
            with zipfile.ZipFile(archive) as zf:
                records_by_id = {}
                for member in zf.namelist():
                    basename = Path(member).name
                    if not re.fullmatch(r"trial_[0-9]{5}\.json", basename):
                        continue
                    payload = json.loads(zf.read(member).decode("utf-8"))
                    trial_id = int(payload.get("trial_id", -1))
                    if trial_id not in PREVIOUS_NEW_IDS or trial_id in records_by_id:
                        fail(f"N600_TRIAL_ID_INVALID_OR_DUPLICATE {scenario}/{trial_id}")
                    validate_trial_payload(payload, scenario, trial_id, N600_RUN_ID, "new_stage12_gateb_n600")
                    if int(payload.get("run_attempt", -1)) != 1:
                        fail(f"N600_TRIAL_ATTEMPT_INVALID {scenario}/{trial_id}")
                    records_by_id[trial_id] = {
                        "scenario_id": scenario, "trial_id": trial_id, "trial_result": payload["trial_result"],
                        "result_sha256": payload["result_sha256"], "source_sha": SOURCE_SHA, "source_commit": SOURCE_COMMIT,
                        "master_seed": MASTER_SEED, "origin": "new_stage12_gateb_n600",
                        "run_id": N600_RUN_ID, "run_attempt": 1,
                        "historical_provenance": {"n600_run_id": N600_RUN_ID, "n600_run_head_sha": N600_HEAD, "artifact_id": N600_ARTIFACTS[scenario][0], "artifact_sha256": N600_ARTIFACTS[scenario][1]},
                    }
                if sorted(records_by_id) != list(PREVIOUS_NEW_IDS):
                    fail(f"N600_NEW_TRIAL_COVERAGE_INVALID {scenario}")
                cumulative[scenario].extend(records_by_id[i] for i in PREVIOUS_NEW_IDS)
                prior_trial_files += len(records_by_id)

        all_records = [r for scenario in SCENARIOS for r in cumulative[scenario]]
        if prior_trial_files != 1000 or len(all_records) != 12000:
            fail("N600_CUMULATIVE_RECORD_COUNT_INVALID")
        actual_n600_map = ordered_map_sha(all_records)
        if actual_n600_map != N600_SAMPLE_MAP_SHA:
            fail(f"N600_CUMULATIVE_MAP_RECOMPUTE_MISMATCH expected={N600_SAMPLE_MAP_SHA} actual={actual_n600_map}")
        result = {
            "status": "PASS", "source_sha": SOURCE_SHA, "source_commit": SOURCE_COMMIT, "master_seed": MASTER_SEED,
            "scenario_count": 20, "cumulative_sample_size_per_scenario": 600,
            "historical_trials_verified": 11000, "n600_run_trials_verified": 1000,
            "total_records_verified": len(all_records), "ordered_scenario_trial_hash_map_sha256_n600": actual_n600_map,
            "historical_aggregate_artifact": history_event, "n600_report_artifact": report_event,
            "n600_workflow_run": run600, "stage7_workflow_run": validate_run(STAGE7_RUN_ID, STAGE7_HEAD, "success"),
            "stage10_workflow_run": validate_run(STAGE10_RUN_ID, STAGE10_HEAD, "failure"),
            "stage12_workflow_run": validate_run(STAGE12_RUN_ID, STAGE12_HEAD, "success"),
            "n300_checkpoint_run": validate_run(N300_RUN_ID, N300_HEAD, "success"),
            "n600_report_status": n600_report["checkpoint_status"], "n600_ci_points_passed": 60,
            "historical_hash_map_sha256": N600_HISTORY_MAP_SHA,
            "new_trial_artifacts": {s: {"artifact_id": N600_ARTIFACTS[s][0], "archive_sha256": N600_ARTIFACTS[s][1], "trials": 50} for s in SCENARIOS},
            "scenarios": cumulative,
            "historical_trial_rerun": False, "historical_dataset_modified": False, "historical_metadata_modified": False,
        }
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": "PASS", "scenarios": 20, "historical_trial_inputs": 11000, "n600_additions": 1000,
            "cumulative_records": 12000, "ordered_scenario_trial_hash_map_sha256_n600": actual_n600_map,
            "report": str(output_file),
        }, indent=2))
        return result


def restore_previous_attempts(scenario: str, run_id: int, current_attempt: int) -> dict[int, dict[str, Any]]:
    artifacts = list_artifacts(run_id)
    prefix = f"gateb-n1200-new-{scenario}-attempt-"
    restored = {}
    with tempfile.TemporaryDirectory(prefix=f"gateb-n1200-restore-{scenario}-") as tmp:
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
                    if not re.fullmatch(r"trial_[0-9]{5}\.json", Path(member).name):
                        continue
                    if member.startswith("/") or ".." in Path(member).parts:
                        fail(f"PREVIOUS_ATTEMPT_ARTIFACT_PATH_INVALID {name}/{member}")
                    payload = json.loads(zf.read(member).decode("utf-8"))
                    trial_id = int(payload.get("trial_id", -1))
                    if trial_id not in NEW_IDS:
                        fail(f"PRIOR_N1200_TRIAL_ID_OUT_OF_RANGE {scenario}/{trial_id}")
                    validate_trial_payload(payload, scenario, trial_id, run_id, "new_stage12_gateb_n1200")
                    if int(payload.get("run_attempt", -1)) != int(suffix):
                        fail(f"PRIOR_N1200_TRIAL_ATTEMPT_IDENTITY_MISMATCH {scenario}/{trial_id}")
                    if trial_id in restored:
                        fail(f"DUPLICATE_COMPLETED_N1200_TRIAL {scenario}/{trial_id}; refusing to rerun or deduplicate")
                    restored[trial_id] = payload
    return restored


def run_new_trials(scenario: str, source_root: Path, input_file: Path, output_root: Path) -> dict[str, Any]:
    if scenario not in SCENARIOS:
        fail(f"UNSUPPORTED_SCENARIO {scenario}")
    cumulative = json.loads(input_file.read_text(encoding="utf-8"))
    if cumulative.get("status") != "PASS" or cumulative.get("ordered_scenario_trial_hash_map_sha256_n600") != N600_SAMPLE_MAP_SHA:
        fail("CUMULATIVE_N600_PROOF_INVALID")
    if len(cumulative.get("scenarios", {}).get(scenario, [])) != 600:
        fail(f"CUMULATIVE_N600_SCENARIO_COVERAGE_INVALID {scenario}")

    git = subprocess.run(["git", "-C", str(source_root), "rev-parse", "HEAD"], text=True, capture_output=True, check=False)
    if git.returncode or git.stdout.strip() != SOURCE_COMMIT:
        fail(f"PINNED_SOURCE_CHECKOUT_MISMATCH expected={SOURCE_COMMIT} actual={git.stdout.strip()}")
    sys.path.insert(0, str(source_root))
    import constants
    import daily_engine
    import monte_carlo
    if int(constants.MASTER_SEED) != MASTER_SEED or Path(daily_engine.__file__).resolve().parent != source_root:
        fail("PINNED_ENGINE_IMPORT_OR_MASTER_SEED_MISMATCH")

    run_id = int(os.environ["GITHUB_RUN_ID"])
    attempt = int(os.environ["GITHUB_RUN_ATTEMPT"])
    output_dir = output_root / "trial_outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    prior = restore_previous_attempts(scenario, run_id, attempt)
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
            "log_events": False, "origin": "new_stage12_gateb_n1200",
        }
        validate_trial_payload(payload, scenario, trial_id, run_id, "new_stage12_gateb_n1200")
        path = output_dir / f"trial_{trial_id:05d}.json"
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        temporary.replace(path)
        completed_now.append(trial_id)
        if len(completed_now) % 50 == 0:
            print(f"N1200_TRIAL_PROGRESS={scenario} completed_this_attempt={len(completed_now)} last_trial_id={trial_id}")
    total = set(prior) | set(completed_now)
    if total != set(NEW_IDS):
        fail(f"N1200_NEW_TRIAL_BLOCK_INCOMPLETE {scenario} completed={len(total)}")
    return {
        "scenario_id": scenario, "run_id": run_id, "run_attempt": attempt,
        "source_sha": SOURCE_SHA, "source_commit": SOURCE_COMMIT, "master_seed": MASTER_SEED,
        "historical_ids_rerun": False, "completed_before_attempt": sorted(prior),
        "new_ids_materialized_this_attempt": completed_now,
        "trial_count_at_n1200": len(total), "remaining_ids": sorted(set(NEW_IDS) - total),
        "status": "PASS",
    }


def ci_point(scenario: str, label: str, field: str, values: list[int]) -> dict[str, Any]:
    numbers = np.asarray(values, dtype=np.float64)
    n = int(numbers.size)
    if n != 1200:
        fail(f"N1200_METRIC_SAMPLE_COUNT_INVALID {scenario}/{field} n={n}")
    mean = float(numbers.mean())
    sample_std = float(numbers.std(ddof=1))
    critical = float(t.ppf(0.975, df=n - 1))
    half_width = float(critical * sample_std / math.sqrt(n))
    if abs(mean) <= EPSILON:
        status = "UNDEFINED_BUSINESS_RULE"
        limit = None
    else:
        limit = 0.01 * abs(mean)
        status = "PASS" if half_width < limit else "FAIL"
    return {
        "scenario_id": scenario, "metric": label, "field": field, "n": n, "df": n - 1,
        "confidence": 0.95, "distribution": "Student-t", "t_critical": critical,
        "mean": mean, "sample_std_ddof1": sample_std, "ci_half_width_95": half_width,
        "relative_half_width": None if mean == 0 else half_width / abs(mean),
        "ci_absolute_epsilon": EPSILON, "required_half_width": limit,
        "inequality": "ci_half_width_95 < 0.01 * abs(mean)", "status": status,
    }


def aggregate_n1200(cumulative_file: Path, new_root: Path, output_file: Path) -> dict[str, Any]:
    cumulative = json.loads(cumulative_file.read_text(encoding="utf-8"))
    if cumulative.get("status") != "PASS" or cumulative.get("ordered_scenario_trial_hash_map_sha256_n600") != N600_SAMPLE_MAP_SHA:
        fail("N600_CUMULATIVE_INPUT_ARTIFACT_INVALID")
    rows_by_scenario = cumulative.get("scenarios", {})
    if sorted(rows_by_scenario) != sorted(SCENARIOS):
        fail("N600_CUMULATIVE_SCENARIO_SET_INVALID")
    cumulative_rows = []
    for scenario in SCENARIOS:
        records = rows_by_scenario[scenario]
        if len(records) != 600:
            fail(f"N600_CUMULATIVE_COUNT_INVALID {scenario}")
        ids = []
        for record in records:
            tid = int(record.get("trial_id", -1))
            if record.get("scenario_id") != scenario or tid not in CUMULATIVE_IDS:
                fail(f"N600_CUMULATIVE_ROW_KEY_INVALID {scenario}/{tid}")
            row = record.get("trial_result")
            validate_result_row(row, scenario, tid)
            if row_sha(row) != record.get("result_sha256"):
                fail(f"N600_CUMULATIVE_ROW_SHA_INVALID {scenario}/{tid}")
            ids.append(tid)
            cumulative_rows.append(record)
        if ids != list(CUMULATIVE_IDS):
            fail(f"N600_CUMULATIVE_IDS_INVALID {scenario}")
    if ordered_map_sha(cumulative_rows) != N600_SAMPLE_MAP_SHA or len(cumulative_rows) != 12000:
        fail("N600_CUMULATIVE_MAP_OR_COUNT_INVALID")

    new_by_scenario: dict[str, dict[int, dict[str, Any]]] = {s: {} for s in SCENARIOS}
    for path in sorted(new_root.rglob("trial_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        scenario = payload.get("scenario_id")
        if scenario not in SCENARIOS:
            continue
        tid = int(payload.get("trial_id", -1))
        if tid not in NEW_IDS:
            fail(f"N1200_TRIAL_ID_OUT_OF_RANGE {scenario}/{tid}")
        validate_trial_payload(payload, scenario, tid, expected_origin="new_stage12_gateb_n1200")
        if tid in new_by_scenario[scenario]:
            fail(f"DUPLICATE_N1200_TRIAL_ID {scenario}/{tid}")
        new_by_scenario[scenario][tid] = payload

    points = []
    scenario_reports = []
    all_rows = list(cumulative_rows)
    p50s = {}
    failed = []
    undefined = []
    for scenario in SCENARIOS:
        new_ids = new_by_scenario[scenario]
        if sorted(new_ids) != list(NEW_IDS):
            fail(f"N1200_NEW_TRIAL_COVERAGE_INVALID {scenario} missing={sorted(set(NEW_IDS)-set(new_ids))[:10]} extra={sorted(set(new_ids)-set(NEW_IDS))[:10]}")
        combined = {int(r["trial_id"]): r for r in rows_by_scenario[scenario]}
        for tid, payload in new_ids.items():
            combined[tid] = {
                "scenario_id": scenario, "trial_id": tid, "trial_result": payload["trial_result"],
                "result_sha256": payload["result_sha256"], "source_sha": SOURCE_SHA,
                "source_commit": SOURCE_COMMIT, "master_seed": MASTER_SEED,
                "origin": payload["origin"], "run_id": payload["run_id"], "run_attempt": payload["run_attempt"],
            }
            all_rows.append(combined[tid])
        if sorted(combined) != list(range(1, 1201)) or len(combined) != 1200:
            fail(f"N1200_FULL_SAMPLE_KEYS_INVALID {scenario}")

        values_by_metric = {field: [int(combined[tid]["trial_result"][field]) for tid in range(1, 1201)] for field in METRICS.values()}
        metric_points = []
        for label, field in METRICS.items():
            point = ci_point(scenario, label, field, values_by_metric[field])
            metric_points.append(point)
            points.append(point)
            if point["status"] == "FAIL":
                failed.append({"scenario_id": scenario, "metric": label, "half_width": point["ci_half_width_95"], "required_half_width": point["required_half_width"]})
            elif point["status"] == "UNDEFINED_BUSINESS_RULE":
                undefined.append({"scenario_id": scenario, "metric": label, "mean": point["mean"], "half_width": point["ci_half_width_95"]})

        equity = np.asarray(values_by_metric["final_net_project_equity"], dtype=np.float64)
        p50s[scenario] = {
            "N300": float(np.quantile(equity[:300], 0.50, method="linear")),
            "N600": float(np.quantile(equity[:600], 0.50, method="linear")),
            "N1200": float(np.quantile(equity, 0.50, method="linear")),
            "change_percent_decision": "UNDEFINED_BUSINESS_RULE: exact percentage-change formula/denominator not stated in D-2026-10-10-01",
        }
        scenario_reports.append({
            "scenario_id": scenario, "historical_and_prior_trials": 600,
            "new_trial_count": 600, "trial_count_at_checkpoint": 1200,
            "new_trial_ids": [601, 1200], "metrics": metric_points,
            "new_trial_artifacts": {str(tid): {"result_sha256": new_ids[tid]["result_sha256"], "run_id": new_ids[tid].get("run_id"), "run_attempt": new_ids[tid].get("run_attempt")} for tid in sorted(new_ids)},
        })

    if len(all_rows) != EXPECTED_N1200_KEYS or len({(r["scenario_id"], int(r["trial_id"])) for r in all_rows}) != EXPECTED_N1200_KEYS:
        fail("N1200_GLOBAL_KEY_COVERAGE_INVALID")
    global_map = ordered_map_sha(all_rows)
    checkpoint_status = "HOLD_UNDEFINED_BUSINESS_RULE" if undefined else ("FAIL_AT_N1200_ESCALATE_TO_N2400" if failed else "PASS_AT_N1200_ONLY")
    result = {
        "status": checkpoint_status, "checkpoint": "N=1200", "checkpoint_status": checkpoint_status,
        "overall_gate_b": "NOT_ESTABLISHED_BY_N1200_ALONE",
        "gate_a": "SEPARATE_GATE_NOT_PROMOTED_BY_THIS_CP",
        "source_sha": SOURCE_SHA, "source_commit_for_new_trials": SOURCE_COMMIT, "master_seed": MASTER_SEED,
        "n300_run_id": N300_RUN_ID, "n600_run_id": N600_RUN_ID, "new_trial_run_id": int(os.environ.get("GITHUB_RUN_ID", "-1")),
        "new_trial_run_attempt": int(os.environ.get("GITHUB_RUN_ATTEMPT", "-1")),
        "scenario_count": 20, "historical_and_prior_inputs_verified": 12000,
        "new_trials_expected": EXPECTED_N1200_NEW, "new_trials_verified": sum(len(v) for v in new_by_scenario.values()),
        "trial_keys_expected": EXPECTED_N1200_KEYS, "trial_keys_verified": len(all_rows),
        "ordered_scenario_trial_hash_map_sha256_n1200": global_map,
        "ci_points_expected": 60, "ci_points_reported": len(points),
        "passed_ci_points": sum(p["status"] == "PASS" for p in points),
        "failed_ci_points": sum(p["status"] == "FAIL" for p in points),
        "undefined_ci_points": sum(p["status"] == "UNDEFINED_BUSINESS_RULE" for p in points),
        "failed_ci_points_detail": failed, "undefined_business_rules": undefined,
        "p50_final_net_project_equity_by_scenario": p50s,
        "scenarios": scenario_reports, "checkpoint_metrics": points,
        "historical_trials_rerun": False, "historical_dataset_modified": False,
        "historical_metadata_modified": False, "historical_identity_changed": False,
        "p50_change_formula": "UNDEFINED_BUSINESS_RULE; P50 medians are reported at N=300/600/1200 without making the >5% branch decision",
        "limitations": [
            "N=1200 is one checkpoint; overall Gate B requires three consecutive successful checkpoints and all applicable decision conditions.",
            "If any metric has abs(mean) <= CI_ABSOLUTE_EPSILON=1, its status is held as UNDEFINED_BUSINESS_RULE.",
            "D-2026-10-10-01 does not specify the exact percentage-change formula/denominator for the P50 >5% condition. No formula is inferred.",
            "Gate A and Stage 9C/CP-D are independent gates and are not established by this report.",
        ],
    }
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "checkpoint_status": checkpoint_status, "overall_gate_b": result["overall_gate_b"],
        "scenarios": 20, "cumulative_inputs": 12000, "new_trials": result["new_trials_verified"],
        "ci_points": len(points), "passed_ci_points": result["passed_ci_points"],
        "failed_ci_points": result["failed_ci_points"], "undefined_ci_points": result["undefined_ci_points"],
        "ordered_scenario_trial_hash_map_sha256_n1200": global_map, "report": str(output_file),
    }, indent=2))
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--prepare-cumulative-600", action="store_true")
    parser.add_argument("--run-new-trials", action="store_true")
    parser.add_argument("--aggregate-n1200", action="store_true")
    parser.add_argument("--scenario")
    parser.add_argument("--source-root")
    parser.add_argument("--cumulative-file")
    parser.add_argument("--input-file")
    parser.add_argument("--output-root", default="gateb_n1200")
    parser.add_argument("--new-root")
    parser.add_argument("--output-file")
    args = parser.parse_args()
    if args.preflight:
        report = preflight()
        output = Path(args.output_file or "results_gateb/preflight.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 0
    if args.prepare_cumulative_600:
        read_n600_inputs(Path(args.output_file or "results_gateb/cumulative_600.json"))
        return 0
    if args.run_new_trials:
        if not args.scenario or not args.source_root or not args.input_file:
            parser.error("--run-new-trials requires --scenario, --source-root, --input-file")
        result = run_new_trials(args.scenario, Path(args.source_root), Path(args.input_file), Path(args.output_root))
        print(json.dumps(result, indent=2))
        return 0
    if args.aggregate_n1200:
        if not args.cumulative_file or not args.new_root or not args.output_file:
            parser.error("--aggregate-n1200 requires --cumulative-file, --new-root and --output-file")
        aggregate_n1200(Path(args.cumulative_file), Path(args.new_root), Path(args.output_file))
        return 0
    parser.error("choose exactly one operation")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
