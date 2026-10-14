#!/usr/bin/env python3
"""CP-F verifies the highest reached N=1200 delivery cohort and fails closed
if required full daily/representative detail sources are absent.
This script does not run Monte Carlo, replay trials, or create deliverables.
"""
from __future__ import annotations
import ast, hashlib, io, json, os, sys, tarfile, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import numpy as np
import pyarrow.parquet as pq
def read_expected_scenarios() -> list[str]:
    source = Path("scripts/stage13_assemble.py").read_text(encoding="utf-8")
    tree = ast.parse(source, filename="scripts/stage13_assemble.py")
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "EXPECTED_SCENARIOS"
            for target in node.targets
        ):
            values = ast.literal_eval(node.value)
            if isinstance(values, list) and all(isinstance(value, str) for value in values):
                return values
    raise RuntimeError("ASSEMBLER_EXPECTED_SCENARIOS_DEFINITION_MISSING")

EXPECTED_SCENARIOS = read_expected_scenarios()

REPO = "yasmin977209-ux/motorcycle-simulation"
STAGE9A_RUN = 37671448546
N1200_RUN = 38179919488
SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
SOURCE_COMMIT = "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
MASTER_SEED = 20270101
SCHEMA_VERSION = "stage12-daily-accounting-v1"
N1200_GLOBAL_SHA256 = "eaf1f8f3060aac6967b064d3199c082d2a9b47027c865628986f56cbb23c1fc3"
N600_GLOBAL_SHA256 = "dd537fe96c5a8736201441e9a620db148a0d16cadae518d2a777fbc723db395f"
N1200_TRIALS_PER_NON_C100 = 1200
N600_ARTIFACT_NAME = "gateb-n1200-cumulative-600"
N1200_REPORT_ARTIFACT_NAME = "gateb-n1200-checkpoint-report"
C100_SCENARIOS = {s for s in EXPECTED_SCENARIOS if s.startswith("C100_")}
NON_C100_SCENARIOS = sorted(set(EXPECTED_SCENARIOS) - C100_SCENARIOS)

class _NoFollowRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def api_json(url: str, token: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "motorcycle-simulation-cp-f",
    })
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))

def get_zip(artifact_id: int, token: str) -> bytes:
    """Download an artifact without forwarding API credentials to its storage host."""
    url = f"https://api.github.com/repos/{REPO}/actions/artifacts/{artifact_id}/zip"
    request = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "motorcycle-simulation-cp-f",
    })
    opener = urllib.request.build_opener(_NoFollowRedirect())
    try:
        with opener.open(request, timeout=180) as response:
            raw = response.read()
    except Exception as response:
        code = getattr(response, "code", None)
        if code not in (301, 302, 303, 307, 308):
            raise
        location = getattr(response, "headers", {}).get("Location")
        if not location:
            raise RuntimeError(f"ARTIFACT_REDIRECT_LOCATION_MISSING: {artifact_id}")
        storage_request = urllib.request.Request(location, headers={"User-Agent": "motorcycle-simulation-cp-f"})
        with urllib.request.urlopen(storage_request, timeout=180) as storage_response:
            raw = storage_response.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        damaged = archive.testzip()
        if damaged:
            raise RuntimeError(f"ARTIFACT_ZIP_CORRUPT: {artifact_id}:{damaged}")
    return raw

def artifacts_for_run(run_id: int, token: str) -> list[dict[str, Any]]:
    return api_json(
        f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}/artifacts?per_page=100",
        token,
    ).get("artifacts", [])

def unique_artifact(items: list[dict[str, Any]], name: str) -> dict[str, Any]:
    matches = [item for item in items if item.get("name") == name and not item.get("expired")]
    if len(matches) != 1:
        raise RuntimeError(f"ARTIFACT_LOOKUP_NOT_UNIQUE: {name}; count={len(matches)}")
    return matches[0]

def verify_archive_digest(raw: bytes, record: dict[str, Any]) -> str:
    actual = hashlib.sha256(raw).hexdigest()
    declared = str(record.get("digest") or "").removeprefix("sha256:")
    if declared and declared != actual:
        raise RuntimeError(
            f"ARTIFACT_ARCHIVE_SHA256_MISMATCH: id={record.get('id')}; expected={declared}; actual={actual}"
        )
    return actual

def zip_member(raw_zip: bytes, suffix: str) -> bytes:
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as archive:
        matches = [name for name in archive.namelist() if name == suffix or name.endswith("/" + suffix)]
        if len(matches) != 1:
            raise RuntimeError(f"ZIP_MEMBER_LOOKUP_NOT_UNIQUE: {suffix}; matches={matches[:5]}")
        return archive.read(matches[0])

def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def trial_result_sha256(trial_result: dict[str, Any]) -> str:
    canonical = json.dumps(
        trial_result, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return sha256_bytes(canonical)

def global_trial_hash_map(rows_by_scenario: dict[str, dict[int, dict[str, Any]]]) -> str:
    digest = hashlib.sha256()
    for scenario in sorted(rows_by_scenario):
        for trial_id in sorted(rows_by_scenario[scenario]):
            row = rows_by_scenario[scenario][trial_id]
            digest.update(f"{scenario}|{trial_id}|{row['result_sha256']}\n".encode("utf-8"))
    return digest.hexdigest()

def verify_trial_row(row: dict[str, Any], scenario: str, trial_id: int) -> None:
    if row.get("scenario_id") != scenario or int(row.get("trial_id", -1)) != trial_id:
        raise RuntimeError(f"TRIAL_KEY_MISMATCH: expected={scenario}/{trial_id}")
    if row.get("source_sha") != SOURCE_SHA:
        raise RuntimeError(f"TRIAL_SOURCE_SHA_MISMATCH: {scenario}/{trial_id}")
    if int(row.get("master_seed", -1)) != MASTER_SEED:
        raise RuntimeError(f"TRIAL_MASTER_SEED_MISMATCH: {scenario}/{trial_id}")
    result = row.get("trial_result")
    if not isinstance(result, dict):
        raise RuntimeError(f"TRIAL_RESULT_MISSING: {scenario}/{trial_id}")
    if result.get("scenario_id") != scenario or int(result.get("trial_id", -1)) != trial_id:
        raise RuntimeError(f"INNER_TRIAL_KEY_MISMATCH: {scenario}/{trial_id}")
    actual_hash = trial_result_sha256(result)
    if actual_hash != row.get("result_sha256"):
        raise RuntimeError(f"TRIAL_RESULT_SHA256_MISMATCH: {scenario}/{trial_id}")

def get_trial_file_records(raw_zip: bytes) -> list[dict[str, Any]]:
    rows = []
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as archive:
        for name in archive.namelist():
            if name.startswith("trial_") and name.endswith(".json"):
                rows.append(json.loads(archive.read(name)))
    return rows

def load_c100_trial(artifact_id: int, scenario: str, token: str) -> tuple[dict[str, Any], str, int]:
    raw = get_zip(artifact_id, token)
    scenario_tar = zip_member(raw, f"{scenario}.tar.gz")
    with tarfile.open(fileobj=io.BytesIO(scenario_tar), mode="r:gz") as tar:
        members = [m for m in tar.getmembers() if m.name.lstrip("./") == "trial_results.parquet"]
        if len(members) != 1:
            raise RuntimeError(f"C100_TRIAL_PARQUET_NOT_UNIQUE: {scenario}")
        stream = tar.extractfile(members[0])
        if stream is None:
            raise RuntimeError(f"C100_TRIAL_PARQUET_UNREADABLE: {scenario}")
        rows = pq.read_table(io.BytesIO(stream.read())).to_pylist()
        if len(rows) != 1:
            raise RuntimeError(f"C100_TRIAL_COUNT_MISMATCH: {scenario}; rows={len(rows)}")
        trial_result = rows[0]
    if trial_result.get("scenario_id") != scenario or int(trial_result.get("trial_id", -1)) != 1:
        raise RuntimeError(f"C100_TRIAL_IDENTITY_MISMATCH: {scenario}")
    return {
        "scenario_id": scenario, "trial_id": 1, "source_sha": SOURCE_SHA,
        "master_seed": MASTER_SEED, "result_sha256": trial_result_sha256(trial_result),
        "trial_result": trial_result, "origin": "stage9a_official_deterministic_c100",
        "log_events": True,
    }, sha256_bytes(raw), len(trial_result)

def select_roles(rows_by_id: dict[int, dict[str, Any]], scenario: str) -> dict[str, int]:
    rows = [rows_by_id[k]["trial_result"] for k in sorted(rows_by_id)]
    values = np.asarray([float(row["final_net_project_equity"]) for row in rows], dtype=float)
    selected = {}
    for role, q in (("P10", 0.10), ("P50", 0.50), ("P90", 0.90)):
        target = float(np.quantile(values, q, method="linear"))
        selected[role] = int(min(
            rows, key=lambda row: (abs(float(row["final_net_project_equity"]) - target), int(row["trial_id"]))
        )["trial_id"])
    selected["LossCase"] = int(min(
        rows, key=lambda row: (abs(float(row["final_net_project_equity"])), int(row["trial_id"]))
    )["trial_id"])
    positive = [row for row in rows if float(row["final_net_project_equity"]) > 0]
    if not positive:
        raise RuntimeError(f"UNDEFINED_BUSINESS_RULE: MaxCase has no positive equity in {scenario}")
    max_equity = max(float(row["final_net_project_equity"]) for row in positive)
    selected["MaxCase"] = min(
        int(row["trial_id"]) for row in positive
        if float(row["final_net_project_equity"]) == max_equity
    )
    return selected

def main() -> int:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN_MISSING")
    outdir = Path("cp-f-evidence")
    outdir.mkdir(parents=True, exist_ok=True)

    state = json.loads(Path("state.json").read_text(encoding="utf-8"))
    roll = json.loads(Path("docs/stage12/roll_forward_validation.json").read_text(encoding="utf-8"))
    global_manifest = json.loads(Path("docs/stage11/global_manifest_11005_reconciled.json").read_text(encoding="utf-8"))
    decision_log = Path("docs/governance/DECISIONS_LOG.md").read_text(encoding="utf-8")
    dstart = decision_log.find("## D-2026-10-10-03")
    dend = decision_log.find("\n## ", dstart + 4) if dstart >= 0 else -1
    decision_block = decision_log[dstart:] if dend < 0 else decision_log[dstart:dend]
    if "**Status:** APPROVED — NORMATIVE" not in decision_block or "P50/P10/P90/LossCase/MaxCase." not in decision_block:
        raise RuntimeError("REPRESENTATIVE_ROLE_DECISION_NOT_APPROVED")

    # The user explicitly selected the highest reached N=1200 cohort.
    run_artifacts = artifacts_for_run(N1200_RUN, token)
    report_art = unique_artifact(run_artifacts, N1200_REPORT_ARTIFACT_NAME)
    cumulative_art = unique_artifact(run_artifacts, N600_ARTIFACT_NAME)
    report_zip = get_zip(int(report_art["id"]), token)
    cumulative_zip = get_zip(int(cumulative_art["id"]), token)
    report_sha = verify_archive_digest(report_zip, report_art)
    cumulative_sha = verify_archive_digest(cumulative_zip, cumulative_art)
    report = json.loads(zip_member(report_zip, "gate_b_n1200_report.json"))
    cumulative = json.loads(zip_member(cumulative_zip, "cumulative_600.json"))

    n1200_source_checks = {
        "checkpoint": report.get("checkpoint"),
        "checkpoint_status": report.get("checkpoint_status"),
        "overall_gate_b": report.get("overall_gate_b"),
        "source_sha": report.get("source_sha"),
        "source_commit_for_new_trials": report.get("source_commit_for_new_trials"),
        "master_seed": report.get("master_seed"),
        "scenario_count_non_c100": report.get("scenario_count"),
        "trial_keys_expected": report.get("trial_keys_expected"),
        "trial_keys_verified": report.get("trial_keys_verified"),
        "new_trials_expected": report.get("new_trials_expected"),
        "new_trials_verified": report.get("new_trials_verified"),
        "historical_and_prior_inputs_verified": report.get("historical_and_prior_inputs_verified"),
        "historical_trials_rerun": report.get("historical_trials_rerun"),
        "historical_dataset_modified": report.get("historical_dataset_modified"),
        "historical_metadata_modified": report.get("historical_metadata_modified"),
        "ordered_scenario_trial_hash_map_sha256_n1200": report.get("ordered_scenario_trial_hash_map_sha256_n1200"),
        "n1200_report_artifact_id": report_art["id"],
        "n1200_report_zip_sha256": report_sha,
        "cumulative_600_artifact_id": cumulative_art["id"],
        "cumulative_600_zip_sha256": cumulative_sha,
    }
    assertions_pass = (
        report.get("checkpoint") == "N=1200"
        and report.get("checkpoint_status") == "PASS_AT_N1200_ONLY"
        and report.get("overall_gate_b") == "NOT_ESTABLISHED_BY_N1200_ALONE"
        and report.get("source_sha") == SOURCE_SHA
        and report.get("source_commit_for_new_trials") == SOURCE_COMMIT
        and report.get("master_seed") == MASTER_SEED
        and report.get("scenario_count") == 20
        and report.get("trial_keys_expected") == 24000
        and report.get("trial_keys_verified") == 24000
        and report.get("new_trials_expected") == 12000
        and report.get("new_trials_verified") == 12000
        and report.get("historical_and_prior_inputs_verified") == 12000
        and report.get("historical_trials_rerun") is False
        and report.get("historical_dataset_modified") is False
        and report.get("historical_metadata_modified") is False
        and cumulative.get("source_sha") == SOURCE_SHA
        and cumulative.get("master_seed") == MASTER_SEED
        and cumulative.get("scenario_count") == 20
        and cumulative.get("cumulative_sample_size_per_scenario") == 600
        and cumulative.get("total_records_verified") == 12000
        and cumulative.get("historical_trial_rerun") is False
    )
    if not assertions_pass:
        raise RuntimeError(f"N1200_SOURCE_IDENTITY_ASSERTION_FAILED: {n1200_source_checks}")

    # Verify all 12,000 rows in the cumulative N=600 source and recompute its ordered map.
    non_c100_rows: dict[str, dict[int, dict[str, Any]]] = {}
    c600_scenarios = cumulative.get("scenarios", {})
    if set(c600_scenarios) != set(NON_C100_SCENARIOS):
        raise RuntimeError("N600_SCENARIO_COVERAGE_MISMATCH")
    for scenario in NON_C100_SCENARIOS:
        records = c600_scenarios[scenario]
        if len(records) != 600:
            raise RuntimeError(f"N600_SCENARIO_TRIAL_COUNT_MISMATCH: {scenario}; count={len(records)}")
        by_id = {}
        for row in records:
            trial_id = int(row["trial_id"])
            if trial_id in by_id:
                raise RuntimeError(f"N600_DUPLICATE_TRIAL_ID: {scenario}/{trial_id}")
            verify_trial_row(row, scenario, trial_id)
            by_id[trial_id] = row
        if sorted(by_id) != list(range(1, 601)):
            raise RuntimeError(f"N600_TRIAL_COVERAGE_MISMATCH: {scenario}")
        non_c100_rows[scenario] = by_id
    n600_map = global_trial_hash_map(non_c100_rows)
    if n600_map != cumulative.get("ordered_scenario_trial_hash_map_sha256_n600") or n600_map != N600_GLOBAL_SHA256:
        raise RuntimeError(f"N600_ORDERED_HASH_MAP_MISMATCH: observed={n600_map}")

    # Independently verify the 20 official increment archives for IDs 551..600.
    n600_artifact_checks = {}
    for scenario in NON_C100_SCENARIOS:
        info = cumulative.get("new_trial_artifacts", {}).get(scenario)
        if not isinstance(info, dict):
            raise RuntimeError(f"N600_NEW_ARTIFACT_RECORD_MISSING: {scenario}")
        artifact_id = int(info["artifact_id"])
        raw = get_zip(artifact_id, token)
        raw_sha = sha256_bytes(raw)
        if raw_sha != info.get("archive_sha256"):
            raise RuntimeError(f"N600_INCREMENT_ARCHIVE_SHA256_MISMATCH: {scenario}")
        if int(info.get("trials", -1)) != 50:
            raise RuntimeError(f"N600_INCREMENT_COUNT_MISMATCH: {scenario}")
        records = get_trial_file_records(raw)
        if len(records) != 50:
            raise RuntimeError(f"N600_INCREMENT_ARCHIVE_RECORD_COUNT_MISMATCH: {scenario}")
        ids = set()
        for row in records:
            trial_id = int(row["trial_id"])
            if trial_id not in range(551, 601):
                raise RuntimeError(f"N600_INCREMENT_TRIAL_ID_OUT_OF_RANGE: {scenario}/{trial_id}")
            verify_trial_row(row, scenario, trial_id)
            if non_c100_rows[scenario][trial_id]["result_sha256"] != row["result_sha256"]:
                raise RuntimeError(f"N600_INCREMENT_HASH_DISAGREEMENT: {scenario}/{trial_id}")
            if trial_id in ids:
                raise RuntimeError(f"N600_INCREMENT_DUPLICATE_TRIAL_ID: {scenario}/{trial_id}")
            ids.add(trial_id)
        if ids != set(range(551, 601)):
            raise RuntimeError(f"N600_INCREMENT_RANGE_INCOMPLETE: {scenario}")
        n600_artifact_checks[scenario] = {
            "artifact_id": artifact_id, "archive_sha256": raw_sha,
            "records": 50, "trial_id_range": "551..600",
        }

    # Match each N=1200 trial to the accepted report's exact result hash, run ID and attempt.
    report_scenarios = {row["scenario_id"]: row for row in report.get("scenarios", [])}
    if set(report_scenarios) != set(NON_C100_SCENARIOS):
        raise RuntimeError("N1200_REPORT_SCENARIO_COVERAGE_MISMATCH")
    incr_artifacts = [
        a for a in run_artifacts
        if a.get("name", "").startswith("gateb-n1200-new-") and not a.get("expired")
    ]
    n1200_artifact_checks = {}
    for scenario in NON_C100_SCENARIOS:
        expected = report_scenarios[scenario].get("new_trial_artifacts", {})
        if set(expected) != {str(n) for n in range(601, 1201)}:
            raise RuntimeError(f"N1200_EXPECTED_TRIAL_HASH_COVERAGE_MISMATCH: {scenario}")
        prefix = f"gateb-n1200-new-{scenario}-attempt-"
        candidates = [a for a in incr_artifacts if a.get("name", "").startswith(prefix)]
        if not candidates:
            raise RuntimeError(f"N1200_INCREMENT_ARCHIVE_MISSING: {scenario}")
        accepted = {}
        archive_shas = []
        for artifact in candidates:
            raw = get_zip(int(artifact["id"]), token)
            archive_shas.append({
                "id": artifact["id"], "name": artifact["name"],
                "archive_sha256": verify_archive_digest(raw, artifact),
            })
            for row in get_trial_file_records(raw):
                trial_id = int(row.get("trial_id", -1))
                expected_row = expected.get(str(trial_id))
                if expected_row is None or trial_id not in range(601, 1201):
                    continue
                if row.get("result_sha256") != expected_row.get("result_sha256"):
                    continue
                if int(row.get("run_id", -1)) != int(expected_row.get("run_id", -2)):
                    continue
                if int(row.get("run_attempt", -1)) != int(expected_row.get("run_attempt", -2)):
                    continue
                verify_trial_row(row, scenario, trial_id)
                previous = accepted.get(trial_id)
                if previous is not None and previous.get("result_sha256") != row.get("result_sha256"):
                    raise RuntimeError(f"N1200_ACCEPTED_TRIAL_CONFLICT: {scenario}/{trial_id}")
                accepted[trial_id] = row
        if set(accepted) != set(range(601, 1201)):
            missing = sorted(set(range(601, 1201)) - set(accepted))
            raise RuntimeError(f"N1200_INCREMENT_COVERAGE_MISMATCH: {scenario}; missing={missing[:10]}")
        non_c100_rows[scenario].update(accepted)
        if sorted(non_c100_rows[scenario]) != list(range(1, 1201)):
            raise RuntimeError(f"N1200_CUMULATIVE_TRIAL_COVERAGE_MISMATCH: {scenario}")
        n1200_artifact_checks[scenario] = {
            "artifact_count": len(archive_shas), "archives": archive_shas,
            "accepted_trials": len(accepted), "trial_id_range": "601..1200",
        }
    n1200_map = global_trial_hash_map(non_c100_rows)
    if n1200_map != report.get("ordered_scenario_trial_hash_map_sha256_n1200"):
        raise RuntimeError(f"N1200_ORDERED_HASH_MAP_MISMATCH: observed={n1200_map}")

    # Obtain the five canonical C100 trial outcomes from official Stage 9A enriched Parquet.
    stage9a_items = artifacts_for_run(STAGE9A_RUN, token)
    stage9a_art = unique_artifact(stage9a_items, "stage9a-final-output")
    stage9a_zip = get_zip(int(stage9a_art["id"]), token)
    stage9a_manifest = json.loads(zip_member(stage9a_zip, "manifest_final.json"))
    stage9a_report = json.loads(zip_member(stage9a_zip, "Stage9A_Report.json"))
    if stage9a_manifest.get("source_sha") != SOURCE_SHA or stage9a_manifest.get("master_seed") != MASTER_SEED:
        raise RuntimeError("STAGE9A_C100_SOURCE_IDENTITY_MISMATCH")
    enriched_ids = stage9a_manifest.get("artifact_manifest", {}).get("enriched_artifacts", {})
    if not C100_SCENARIOS.issubset(set(enriched_ids)):
        raise RuntimeError("C100_ENRICHED_ARTIFACT_MAP_INCOMPLETE")
    c100_evidence = {}
    all_rows: dict[str, dict[int, dict[str, Any]]] = {
        scenario: dict(non_c100_rows[scenario]) for scenario in NON_C100_SCENARIOS
    }
    for scenario in sorted(C100_SCENARIOS):
        row, archive_sha, field_count = load_c100_trial(int(enriched_ids[scenario]), scenario, token)
        fingerprints = stage9a_manifest.get("trial_fingerprints", {}).get(scenario, [])
        if fingerprints and row["result_sha256"] != fingerprints[0]:
            raise RuntimeError(f"C100_TRIAL_SHA256_MISMATCH: {scenario}")
        all_rows[scenario] = {1: row}
        c100_evidence[scenario] = {
            "artifact_id": int(enriched_ids[scenario]), "archive_sha256": archive_sha,
            "trial_count": 1, "trial_id": 1, "trial_result_sha256": row["result_sha256"],
            "trial_result_field_count": field_count,
        }

    total_rows = sum(len(rows) for rows in all_rows.values())
    counts = {scenario: len(rows) for scenario, rows in all_rows.items()}
    if total_rows != 24005:
        raise RuntimeError(f"DELIVERY_SOURCE_TOTAL_NOT_24005: {total_rows}")
    if set(counts) != set(EXPECTED_SCENARIOS):
        raise RuntimeError("DELIVERY_SOURCE_SCENARIO_COVERAGE_MISMATCH")
    if any(counts[s] != 1 for s in C100_SCENARIOS) or any(counts[s] != 1200 for s in NON_C100_SCENARIOS):
        raise RuntimeError("DELIVERY_SOURCE_PER_SCENARIO_COUNT_MISMATCH")
    if global_trial_hash_map(non_c100_rows) != N1200_GLOBAL_SHA256:
        raise RuntimeError("N1200_GLOBAL_HASH_CONSTANT_MISMATCH")

    # Select all five roles from the actual highest reached cohort.
    representative_trials = stage9a_manifest.get("representative_trials", {})
    if set(representative_trials) != set(EXPECTED_SCENARIOS):
        raise RuntimeError("STAGE9A_REPRESENTATIVE_ASSIGNMENT_COVERAGE_MISMATCH")
    role_inventory = {}
    missing_role_payloads = []
    stage9a_roles_by_scenario = {}
    for scenario in sorted(all_rows):
        selected = select_roles(all_rows[scenario], scenario)
        old_assignment = representative_trials[scenario]
        old_detail_ids = {
            int(old_assignment[key])
            for key in ("P10", "P50", "P90", "Loss")
            if key in old_assignment
        }
        role_checks = {}
        for role, trial_id in selected.items():
            available = trial_id in old_detail_ids
            role_checks[role] = {"selected_trial_id": trial_id, "full_detail_payload_available": available}
            if not available:
                missing_role_payloads.append({
                    "scenario": scenario, "role": role, "selected_trial_id": trial_id,
                    "available_stage9a_detail_ids": sorted(old_detail_ids),
                })
        role_inventory[scenario] = {
            "source_trial_count": counts[scenario],
            "source_trial_id_range": f"1..{counts[scenario]}",
            "selected_roles": selected,
            "prior_stage9a_representative_trial_ids": old_assignment,
            "role_checks": role_checks,
        }
        stage9a_roles_by_scenario[scenario] = sorted(
            k for k in ("P10", "P50", "P90", "Loss", "LossCase", "MaxCase", "Max Case")
            if k in old_assignment
        )
    detail_total = int(stage9a_manifest.get("total_representatives", 0))
    missing_max_scenarios = [
        scenario for scenario, roles in stage9a_roles_by_scenario.items()
        if "MaxCase" not in roles and "Max Case" not in roles
    ]

    stage12_trials = int(roll.get("total_trials", -1))
    stage12_daily_rows = int(roll.get("total_daily_rows", -1))
    missing_daily_trial_count = len(NON_C100_SCENARIOS) * (N1200_TRIALS_PER_NON_C100 - 550)
    blocker_codes = []
    if report.get("overall_gate_b") != "PASS":
        blocker_codes.append("GATEB_NOT_ESTABLISHED_AT_N1200")
    if stage12_trials != total_rows:
        blocker_codes.append("MISSING_DAILY_LEDGER_FOR_N1200_COHORT")
    if missing_daily_trial_count > 0:
        blocker_codes.append("MISSING_DAILY_AND_ENTITY_DETAIL_FOR_TRIALS_551_1200")
    if missing_role_payloads or missing_max_scenarios or detail_total != 125:
        blocker_codes.append("MISSING_FIVE_ROLE_REPRESENTATIVE_PAYLOADS")

    decision_sha = sha256_bytes(decision_block.encode("utf-8"))
    audit = {
        "audit_version": "cp-f-n1200-source-readiness-v2",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository": REPO, "branch": os.environ.get("GITHUB_REF_NAME"),
        "head_sha": os.environ.get("GITHUB_SHA"),
        "user_directed_delivery_source": "highest reached escalation N=1200; total trial outcomes=24005",
        "status": "SOURCE_IDENTITY_VERIFIED_BUT_DELIVERY_BLOCKED" if blocker_codes else "READY_FOR_CANDIDATE_ASSEMBLY",
        "classification": "MISSING_ARTIFACT" if blocker_codes else "PENDING_FINAL_GATES",
        "monte_carlo_rerun": False, "historical_trials_rerun": False,
        "main_modified": False, "release_created": False, "delivery_files_created": False,
        "dataset": {
            "source_sha": SOURCE_SHA, "source_commit_for_new_trials": SOURCE_COMMIT,
            "master_seed": MASTER_SEED, "schema_version": SCHEMA_VERSION,
            "scenario_count": 25, "non_c100_scenarios": 20,
            "trials_each_non_c100": 1200, "c100_scenarios": 5,
            "trials_each_c100": 1, "total_trial_outcomes": total_rows,
            "n1200_ordered_trial_hash_map_sha256": n1200_map,
            "n600_ordered_trial_hash_map_sha256": n600_map,
        },
        "n1200_checkpoint": n1200_source_checks,
        "stage12_historical_daily_cohort": {
            "run_id": roll.get("source_run_id"), "schema_version": roll.get("schema_version"),
            "source_sha": roll.get("source_sha"), "master_seed": roll.get("master_seed"),
            "trial_count": stage12_trials, "daily_rows": stage12_daily_rows,
            "global_sha256": global_manifest.get("global_aggregate_sha256"),
            "status": roll.get("overall_result"),
            "detail_gap_for_n1200": {
                "non_c100_scenarios": 20, "full_daily_history_available_through_trial_id": 550,
                "highest_statistical_trial_id": 1200, "missing_trial_histories": missing_daily_trial_count,
                "n600_n1200_log_events": False,
            },
        },
        "verified_archives": {
            "n600_trial_archives": n600_artifact_checks,
            "n1200_trial_archives": n1200_artifact_checks,
            "c100_trial_archives": c100_evidence,
            "stage9a_final_output_artifact_id": stage9a_art["id"],
            "stage9a_final_output_zip_sha256": sha256_bytes(stage9a_zip),
            "stage9a_historical_trial_count": stage9a_manifest.get("total_trials"),
            "stage9a_total_representatives": detail_total,
            "stage9a_roles_per_scenario": stage9a_roles_by_scenario,
            "stage9a_missing_maxcase_payload_scenarios": missing_max_scenarios,
        },
        "representative_roles": {
            "decision_id": "D-2026-10-10-03", "decision_log_sha256": decision_sha,
            "five_roles": ["P50", "P10", "P90", "LossCase", "MaxCase"],
            "selection_by_n1200_source": role_inventory,
            "selected_role_payloads_missing": missing_role_payloads,
            "missing_role_payload_count": len(missing_role_payloads),
        },
        "gates": {
            "G_N600_12000_RECORDS_AND_HASH_MAP": "PASS" if n600_map == N600_GLOBAL_SHA256 else "FAIL",
            "G_N1200_24000_RECORDS_AND_HASH_MAP": "PASS" if n1200_map == report.get("ordered_scenario_trial_hash_map_sha256_n1200") else "FAIL",
            "G_PLUS_FIVE_C100_RECORDS": "PASS" if total_rows == 24005 else "FAIL",
            "G_SOURCE_DAILY_DETAIL_FOR_ALL_24005": "FAIL" if missing_daily_trial_count else "PASS",
            "G_FIVE_REPRESENTATIVE_DETAIL_PAYLOADS": "FAIL" if (missing_role_payloads or missing_max_scenarios or detail_total != 125) else "PASS",
            "G_GATE_B_FINAL_STABILITY": "PENDING" if report.get("overall_gate_b") == "NOT_ESTABLISHED_BY_N1200_ALONE" else report.get("overall_gate_b"),
            "G_ALL_SEVEN_DELIVERY_FILES": "BLOCKED" if blocker_codes else "PENDING",
        },
        "blocker_codes": blocker_codes,
        "source_evidence": {
            "stage9a_report": stage9a_report,
            "cumulative_600_status": cumulative.get("status"),
            "cumulative_600_total_records_verified": cumulative.get("total_records_verified"),
            "cumulative_600_trial_rerun": cumulative.get("historical_trial_rerun"),
            "n1200_checkpoint_status": report.get("checkpoint_status"),
            "n1200_overall_gate_b": report.get("overall_gate_b"),
            "n1200_trial_keys_verified": report.get("trial_keys_verified"),
            "n1200_new_trials_verified": report.get("new_trials_verified"),
            "n1200_historical_trials_rerun": report.get("historical_trials_rerun"),
            "n1200_gate_a": report.get("gate_a"),
        },
    }
    json_path = outdir / "CP_F_N1200_SOURCE_READINESS.json"
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_text = f"""# CP-F — N=1200 Delivery Source Readiness

- Status: {audit['status']}
- Classification: {audit['classification']}
- Run HEAD: {audit['head_sha']}
- Source selection: highest reached N=1200; 24,005 total trial outcomes
- SOURCE_SHA: {SOURCE_SHA}
- MASTER_SEED: {MASTER_SEED}
- N=1200 checkpoint run: https://github.com/{REPO}/actions/runs/{N1200_RUN}
- Stage 9A C100 source run: https://github.com/{REPO}/actions/runs/{STAGE9A_RUN}

## Source cohort and identity checks

| Item | Evidence/result |
|---|---|
| Non-C100 scenario count | {len(NON_C100_SCENARIOS)} |
| N=1200 trial results per non-C100 scenario | {N1200_TRIALS_PER_NON_C100} |
| C100 scenarios, one deterministic trial each | {len(C100_SCENARIOS)} |
| Total assembled metric trial outcomes | {total_rows} |
| Cumulative N=600 ordered hash map | {n600_map} |
| N=1200 ordered hash map | {n1200_map} |
| N=1200 checkpoint status | {report.get('checkpoint_status')} |
| N=1200 overall Gate B | {report.get('overall_gate_b')} |
| Stage 12 daily cohort | {stage12_trials} trials / {stage12_daily_rows} daily rows |

## Daily detail and representative payload findings

The N=1200 statistical source contains metrics and result fingerprints, not detailed daily/entity histories for the later trials. The official Stage 12 daily source ends at trial ID 550 for each non-C100 scenario; therefore {missing_daily_trial_count} trial histories (IDs 551–1200 across 20 non-C100 scenarios) are missing from the selected delivery cohort.

The five approved representative roles are P50, P10, P90, LossCase, and MaxCase. The archived Stage 9A enrichment has {detail_total} full representative payloads, corresponding to four roles per scenario. The audit selected the five role IDs from all {total_rows} source trial outcomes. It does not invent details for roles whose selected trial has no full payload.

## Gate results

| Gate | Result |
|---|---|
| N=600 cumulative 12,000 rows and exact map | {audit['gates']['G_N600_12000_RECORDS_AND_HASH_MAP']} |
| N=1200 24,000 rows and exact map | {audit['gates']['G_N1200_24000_RECORDS_AND_HASH_MAP']} |
| Five C100 canonical trial rows | {audit['gates']['G_PLUS_FIVE_C100_RECORDS']} |
| Full daily detail for all 24,005 outcomes | {audit['gates']['G_SOURCE_DAILY_DETAIL_FOR_ALL_24005']} |
| Five representative roles have required details | {audit['gates']['G_FIVE_REPRESENTATIVE_DETAIL_PAYLOADS']} |
| Final Gate B/stability | {audit['gates']['G_GATE_B_FINAL_STABILITY']} |
| Seven-file delivery set | {audit['gates']['G_ALL_SEVEN_DELIVERY_FILES']} |

## Blocking evidence

{chr(10).join('- ' + code for code in blocker_codes)}

- GATEB_NOT_ESTABLISHED_AT_N1200: Run {N1200_RUN} explicitly records NOT_ESTABLISHED_BY_N1200_ALONE.
- MISSING_DAILY_AND_ENTITY_DETAIL_FOR_TRIALS_551_1200: the selected source has no detailed daily events for IDs 551–1200. The reference requires a full daily distribution and detailed P50 scenario tabs.
- MISSING_FIVE_ROLE_REPRESENTATIVE_PAYLOADS: the current official detailed representative package records four roles per scenario, while the approved decision requires five, including MaxCase.

## Disposition

BLOCKED: no final Excel, report, summary or feasibility file was produced. No Monte Carlo was run, no completed trial was replayed, no source/data identity was changed, main was not modified, and no Release was created.
"""
    md_path = outdir / "CP_F_N1200_SOURCE_READINESS.md"
    md_path.write_text(report_text, encoding="utf-8")
    print(json.dumps({
        "status": audit["status"], "classification": audit["classification"],
        "total_trial_outcomes": total_rows, "non_c100_count": len(NON_C100_SCENARIOS),
        "n600_hash_map_matches": n600_map == N600_GLOBAL_SHA256,
        "n1200_hash_map_matches": n1200_map == report.get("ordered_scenario_trial_hash_map_sha256_n1200"),
        "n1200_overall_gate_b": report.get("overall_gate_b"),
        "missing_daily_trial_histories": missing_daily_trial_count,
        "stage9a_representative_payload_count": detail_total,
        "missing_role_payload_count": len(missing_role_payloads),
        "blocker_codes": blocker_codes,
        "evidence_json": str(json_path), "evidence_markdown": str(md_path),
    }, ensure_ascii=False, sort_keys=True))
    return 2 if blocker_codes else 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"CP_F_AUDIT_EXECUTION_ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
