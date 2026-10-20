from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
import traceback
import zipfile
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from scripts import stage13_gatea_fingerprint_bridge as gatea

REPO = "yasmin977209-ux/motorcycle-simulation"
STAGE7_RUN = 37225915321
STAGE7_HEAD = "e0b2fab6710833774937d778097363d7a8ee8e59"
STAGE10_RUN = 37709936740
STAGE10_HEAD = "ca73f2df37baacebbcad965fc5f433f129675820"
STAGE12_RUN = 37964656154
STAGE12_HEAD = "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
MASTER_SEED = 20270101
REFERENCE_SHA256 = "ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479"
SCENARIOS = [f"C{c:03d}_G{g:03d}" for c in (100, 85, 70, 50, 30) for g in (100, 70, 50, 30, 0)]
BASE_BLOCKS = ((1, 300), (301, 350), (351, 400), (401, 450))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: str) -> dict[str, Any]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise RuntimeError(f"JSON_ROOT_NOT_OBJECT: {path}")
    return value


def expected_collection_probability(scenario: str) -> float:
    return int(scenario[1:4]) / 100.0


def expected_recovery_rate(scenario: str) -> int:
    return int(scenario[6:9])


def rows_from_zip(scenario: str, archive_path: Path, manifest: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[int, str]]:
    rows: list[dict[str, Any]] = []
    block_evidence: list[dict[str, Any]] = []
    trial_hashes: dict[int, str] = {}
    with zipfile.ZipFile(archive_path, "r") as zf:
        if scenario.startswith("C100_"):
            meta_raw = gatea.member(zf, "block_1_1_metadata.json")
            parquet_raw = gatea.member(zf, "block_1_1.parquet")
            hashes, evidence = gatea.validate_block(
                scenario, 1, 1, meta_raw, parquet_raw, manifest, STAGE7_RUN
            )
            block_rows = pq.read_table(BytesIO(parquet_raw)).to_pylist()
            if list(hashes) != [1] or len(block_rows) != 1:
                raise RuntimeError(f"C100_TRIAL_COVERAGE_MISMATCH: {scenario}")
            rows.extend(block_rows)
            trial_hashes.update(hashes)
            block_evidence.append(evidence)
        else:
            expected_ids: list[int] = []
            for start, end in BASE_BLOCKS + ((451, 550),):
                name = f"block_{start}_{end}"
                meta_raw = gatea.member(zf, name + "_metadata.json")
                parquet_raw = gatea.member(zf, name + ".parquet")
                source_run = STAGE10_RUN if start == 451 else STAGE7_RUN
                hashes, evidence = gatea.validate_block(
                    scenario,
                    start,
                    end,
                    meta_raw,
                    parquet_raw,
                    manifest,
                    source_run,
                    allow_bad_suffix=(start == 451),
                )
                block_rows = pq.read_table(BytesIO(parquet_raw)).to_pylist()
                block_ids = [int(row.get("trial_id", -1)) for row in block_rows]
                wanted_ids = list(range(start, end + 1))
                if block_ids != wanted_ids or list(hashes) != wanted_ids:
                    raise RuntimeError(f"TRIAL_ID_SEQUENCE_MISMATCH: {scenario}/{name}")
                rows.extend(block_rows)
                trial_hashes.update(hashes)
                expected_ids.extend(wanted_ids)
                block_evidence.append(evidence)
            if [int(row.get("trial_id", -1)) for row in rows] != list(range(1, 551)):
                raise RuntimeError(f"CANONICAL_TRIAL_COVERAGE_MISMATCH: {scenario}")
    expected_count = 1 if scenario.startswith("C100_") else 550
    if len(rows) != expected_count:
        raise RuntimeError(f"TRIAL_COUNT_MISMATCH: {scenario}: {len(rows)} != {expected_count}")
    for row in rows:
        if row.get("scenario_id") != scenario:
            raise RuntimeError(f"SCENARIO_ID_MISMATCH: {scenario}/{row.get('trial_id')}")
        if row.get("collection_probability") != expected_collection_probability(scenario):
            raise RuntimeError(f"COLLECTION_PROBABILITY_MISMATCH: {scenario}/{row.get('trial_id')}")
        if row.get("recovery_rate_pct") != expected_recovery_rate(scenario):
            raise RuntimeError(f"RECOVERY_RATE_MISMATCH: {scenario}/{row.get('trial_id')}")
        if type(row.get("final_net_project_equity")) is not int:
            raise RuntimeError(f"FINAL_EQUITY_NOT_INTEGER: {scenario}/{row.get('trial_id')}")
    return rows, block_evidence, trial_hashes


def inventory_identity_mismatches(
    manifest: dict[str, Any], inventory: dict[str, Any]
) -> list[dict[str, Any]]:
    artifact_map = manifest.get("artifact_manifest", {}).get("enriched_artifacts", {})
    run_map = manifest.get("artifact_manifest", {}).get("enrichment_run_ids", {})
    mismatches: list[dict[str, Any]] = []
    for item in inventory.get("artifacts", []):
        scenario = item.get("scenario")
        manifest_artifact_id = artifact_map.get(scenario)
        manifest_run_id = run_map.get(scenario)
        if manifest_artifact_id != item.get("artifact_id") or manifest_run_id != item.get("run_id"):
            mismatches.append({
                "scenario": scenario,
                "manifest_artifact_id": manifest_artifact_id,
                "inventory_artifact_id": item.get("artifact_id"),
                "manifest_run_id": manifest_run_id,
                "inventory_run_id": item.get("run_id"),
            })
    return mismatches


def select_maxcase(rows: list[dict[str, Any]]) -> dict[str, Any] | None:
    positive = [
        row for row in rows
        if type(row.get("final_net_project_equity")) is int
        and row["final_net_project_equity"] > 0
    ]
    if not positive:
        return None
    highest = max(row["final_net_project_equity"] for row in positive)
    return min(
        (row for row in positive if row["final_net_project_equity"] == highest),
        key=lambda row: int(row["trial_id"]),
    )


def run_audit() -> dict[str, Any]:
    manifest = read_json("docs/stage9a/dataset_manifest.json")
    payload_inventory = read_json("docs/audits/stage9a_payload_inventory_20261020.json")
    accounting_contract = read_json("docs/stage12/accounting_data_contract.json")
    roll_forward = read_json("docs/stage12/roll_forward_validation.json")
    closure_report = read_json("docs/stage12/closure_settlement_validation.json")
    existing = {item["scenario"]: item for item in payload_inventory["artifacts"]}
    if set(existing) != set(SCENARIOS):
        raise RuntimeError("REPRESENTATIVE_INVENTORY_SCENARIO_SET_MISMATCH")
    inventory_mismatches = inventory_identity_mismatches(manifest, payload_inventory)
    inventory_mismatch_scenarios = {item["scenario"] for item in inventory_mismatches}
    if manifest.get("source_sha") != SOURCE_SHA or manifest.get("master_seed") != MASTER_SEED:
        raise RuntimeError("STAGE9A_MANIFEST_IDENTITY_MISMATCH")

    stage7_run = gatea.validate_run(STAGE7_RUN, STAGE7_HEAD, "success")
    stage10_run = gatea.validate_run(STAGE10_RUN, STAGE10_HEAD, None)
    stage12_run = gatea.validate_run(STAGE12_RUN, STAGE12_HEAD, "success")
    stage7_artifacts, _ = gatea.artifact_index(STAGE7_RUN)
    stage10_artifacts, _ = gatea.artifact_index(STAGE10_RUN)
    stage12_artifacts, _ = gatea.artifact_index(STAGE12_RUN)
    stage10_jobs_response = gatea.gh_json(
        f"repos/{REPO}/actions/runs/{STAGE10_RUN}/jobs?per_page=100"
    )
    stage10_jobs = stage10_jobs_response.get("jobs", [])
    if int(stage10_jobs_response.get("total_count", -1)) != len(stage10_jobs):
        raise RuntimeError("STAGE10_JOB_LIST_INCOMPLETE")
    successful_stage10_benchmark_jobs = sum(
        1 for job in stage10_jobs
        if str(job.get("name", "")).startswith("bench-") and job.get("conclusion") == "success"
    )

    workbook_daily_fields = [
        "Closing_Cash", "Closing_Equity", "Retained_Earnings",
        "Active_Bikes", "Owned_Transferred_Bikes", "Pending_Claims",
        "Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance",
    ]
    stage12_required_fields = set(accounting_contract.get("schema", {}).get("required_fields", []))
    stage12_contract_has = {
        field: field in stage12_required_fields for field in workbook_daily_fields
    }
    missing_from_stage12_contract = [
        field for field, present in stage12_contract_has.items() if not present
    ]

    report: dict[str, Any] = {
        "schema_version": "stage13-maxcase-source-audit-v1",
        "stage10_run_level_disposition": (
            {
                "status": "FAIL",
                "classification": "WORKFLOW_DEFECT",
                "run_conclusion": stage10_run.get("conclusion"),
                "failed_job_id": 113098100249,
                "exact_error": "SyntaxError: unterminated string literal at scripts/stage10_aggregate.py line 59",
                "disposition": "Do not call the Stage 10 run successful; validate each existing artifact and row fingerprint independently.",
            }
            if stage10_run.get("conclusion") != "success"
            else {"status": "PASS", "run_conclusion": "success"}
        ),
        "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "repository": REPO,
        "tested_head_sha": os.environ.get("GITHUB_SHA"),
        "tested_branch": os.environ.get("GITHUB_REF_NAME"),
        "scope": "READ_ONLY_STAGE7_STAGE10_TRIALRESULTS_AND_STAGE12_DAILY_PARQUET_EXTRACTION; NO_SIMULATION; NO_HISTORICAL_ARTIFACT_MUTATION; NO_WORKBOOK",
        "source_identity": {
            "source_sha": SOURCE_SHA,
            "master_seed": MASTER_SEED,
            "reference_sha256": REFERENCE_SHA256,
            "stage9a_manifest_git_blob": __import__("subprocess").check_output(
                ["git", "hash-object", "docs/stage9a/dataset_manifest.json"], text=True
            ).strip(),
            "stage9a_global_manifest_sha256": manifest.get("global_manifest_sha256"),
        },
        "runs": {
            "stage7": stage7_run,
            "stage10": stage10_run,
            "stage12": stage12_run,
            "stage10_successful_benchmark_job_count": successful_stage10_benchmark_jobs,
            "stage10_aggregate_job_conclusion": next(
                (job.get("conclusion") for job in stage10_jobs if job.get("name") == "aggregate-stage10"),
                None,
            ),
        },
        "representative_inventory_provenance": {
            "status": "CONFLICTED" if inventory_mismatches else "PASS_SCOPED",
            "mismatch_count": len(inventory_mismatches),
            "mismatches": inventory_mismatches,
            "reuse_allowed_only_for_identity_matched_scenarios": True,
        },
        "daily_contract": {
            "contract_version": accounting_contract.get("contract_version"),
            "schema_version": accounting_contract.get("schema", {}).get("schema_version"),
            "workbook_daily_fields_checked": stage12_contract_has,
            "fields_absent_from_stage12_contract": missing_from_stage12_contract,
        },
        "scenarios": [],
        "stage12_daily_validation": {"scenarios_validated": 0, "daily_rows_validated": 0, "trial_result_fingerprint_mismatches": 0},
        "integrity_status": "NOT_STARTED",
        "payload_status": "NOT_STARTED",
        "historical_artifacts_modified": False,
        "historical_dataset_modified": False,
        "simulation_or_trial_executed": False,
        "workbook_built": False,
    }

    extracted_payloads: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="stage13-maxcase-source-") as tmp:
        root = Path(tmp)
        for scenario in SCENARIOS:
            is_c100 = scenario.startswith("C100_")
            run_id = STAGE7_RUN if is_c100 else STAGE10_RUN
            index = stage7_artifacts if is_c100 else stage10_artifacts
            artifact_name = (
                f"stage7-blocks-{scenario}-1" if is_c100
                else f"stage10-bench-{scenario}-1"
            )
            artifact = gatea.find_artifact(index, artifact_name, run_id)
            stage10_scenario_job = None
            if not is_c100:
                matching_jobs = [
                    job for job in stage10_jobs
                    if job.get("name") == f"bench-{scenario}-1"
                ]
                if len(matching_jobs) != 1 or matching_jobs[0].get("conclusion") != "success":
                    raise RuntimeError(
                        f"STAGE10_SCENARIO_JOB_NOT_SUCCESS: {scenario}: "
                        f"{[(job.get('name'), job.get('conclusion')) for job in matching_jobs]}"
                    )
                stage10_scenario_job = {
                    "job_id": int(matching_jobs[0]["id"]),
                    "name": matching_jobs[0]["name"],
                    "conclusion": matching_jobs[0]["conclusion"],
                }
            expected_head = STAGE7_HEAD if is_c100 else STAGE10_HEAD
            artifact_run = artifact.get("workflow_run") or {}
            if artifact_run and (
                int(artifact_run.get("id", -1)) != run_id
                or artifact_run.get("head_sha") != expected_head
            ):
                raise RuntimeError(f"ARTIFACT_RUN_HEAD_MISMATCH: {scenario}/{artifact_name}")
            zip_path = root / f"{scenario}.zip"
            download_evidence = gatea.download_artifact(artifact, zip_path)
            rows, blocks, trial_hashes = rows_from_zip(scenario, zip_path, manifest)
            selected = select_maxcase(rows)
            canonical_roles = manifest["representative_trials"][scenario]
            role_matches: list[str] = []
            inventory_identity_matches = scenario not in inventory_mismatch_scenarios
            if selected is not None and inventory_identity_matches:
                role_matches = [
                    role for role in ("P10", "P50", "P90", "Loss")
                    if int(canonical_roles[role]) == int(selected["trial_id"])
                ]
            if selected is None:
                selection_status = "UNDEFINED_BUSINESS_RULE"
                payload_reuse = False
            else:
                selection_status = "PASS"
                payload_reuse = bool(role_matches)
            stage12_name = f"stage12-daily-{scenario}"
            stage12_artifact = gatea.find_artifact(stage12_artifacts, stage12_name, STAGE12_RUN)
            stage12_artifact_run = stage12_artifact.get("workflow_run") or {}
            if (
                int(stage12_artifact_run.get("id", -1)) != STAGE12_RUN
                or stage12_artifact_run.get("head_sha") != STAGE12_HEAD
            ):
                raise RuntimeError(f"STAGE12_ARTIFACT_RUN_HEAD_MISMATCH: {scenario}/{stage12_name}")
            stage12_zip = root / f"{scenario}-stage12.zip"
            stage12_download = gatea.download_artifact(stage12_artifact, stage12_zip)
            if stage12_zip.stat().st_size != int(stage12_artifact["size_in_bytes"]):
                raise RuntimeError(f"STAGE12_ARTIFACT_SIZE_MISMATCH: {scenario}")
            parquet_path = root / f"{scenario}.parquet"
            with zipfile.ZipFile(stage12_zip, "r") as zf:
                expected_member = f"{scenario}.parquet"
                if zf.namelist() != [expected_member]:
                    raise RuntimeError(f"STAGE12_ZIP_MEMBER_MISMATCH: {scenario}: {zf.namelist()}")
                with zf.open(expected_member, "r") as source_stream, parquet_path.open("wb") as target_stream:
                    shutil.copyfileobj(source_stream, target_stream)
            trial_checks, stage12_daily_evidence = gatea.validate_stage12(
                scenario, parquet_path, roll_forward, closure_report, trial_hashes
            )
            if any(not item["exact_match"] for item in trial_checks):
                raise RuntimeError(f"STAGE12_TRIAL_RESULT_FINGERPRINT_MISMATCH: {scenario}")
            selected_check = next(
                (item for item in trial_checks if int(item["trial_id"]) == int(selected["trial_id"])),
                None,
            ) if selected is not None else None
            selected_daily_payload = None
            if selected is not None:
                if selected_check is None or not selected_check["exact_match"]:
                    raise RuntimeError(f"STAGE12_MAXCASE_TRIAL_NOT_VERIFIED: {scenario}/{selected['trial_id']}")
                daily_rows = pq.read_table(
                    parquet_path, filters=[("trial_id", "=", int(selected["trial_id"]))]
                ).to_pylist()
                daily_rows.sort(key=lambda row: row["date"])
                if len(daily_rows) != int(selected_check["daily_rows"]) or not daily_rows:
                    raise RuntimeError(f"STAGE12_MAXCASE_DAILY_ROW_COUNT_MISMATCH: {scenario}/{selected['trial_id']}")
                expected_hash = trial_hashes[int(selected["trial_id"])]
                if any(row.get("result_sha256") != expected_hash for row in daily_rows):
                    raise RuntimeError(f"STAGE12_MAXCASE_RESULT_SHA_MISMATCH: {scenario}/{selected['trial_id']}")
                if any(
                    row.get("scenario_id") != scenario
                    or int(row.get("trial_id", -1)) != int(selected["trial_id"])
                    or row.get("source_sha") != SOURCE_SHA
                    or int(row.get("master_seed", -1)) != MASTER_SEED
                    or row.get("Final_Close_Date") != selected.get("final_close_date")
                    for row in daily_rows
                ):
                    raise RuntimeError(f"STAGE12_MAXCASE_DAILY_IDENTITY_OR_CLOSE_DATE_MISMATCH: {scenario}/{selected['trial_id']}")
                final_daily = daily_rows[-1]
                if (
                    int(final_daily["Closing_Cash"]) != int(selected["final_cash"])
                    or int(final_daily["Closing_Equity"]) != int(selected["final_net_project_equity"])
                    or int(final_daily["Retained_Earnings"]) != int(selected["cumulative_project_profit"])
                ):
                    raise RuntimeError(f"STAGE12_MAXCASE_FINAL_VALUE_MISMATCH: {scenario}/{selected['trial_id']}")
                selected_daily_payload = [
                    {
                        "date": row["date"],
                        "Final_Close_Date": row["Final_Close_Date"],
                        "Cash": int(row["Closing_Cash"]),
                        "Net_Equity": int(row["Closing_Equity"]),
                        "Active_Bikes": int(row["Active_Bikes"]),
                        "Owned_Transferred_Bikes": int(row["Owned_Transferred_Bikes"]),
                        "Pending_Claims": int(row["Pending_Claims"]),
                        "Cumulative_Project_Profit": int(row["Retained_Earnings"]),
                        "trial_id": int(row["trial_id"]),
                        "source_sha": row["source_sha"],
                        "master_seed": int(row["master_seed"]),
                        "result_sha256": row["result_sha256"],
                    }
                    for row in daily_rows
                ]
                extracted_payloads.append({
                    "scenario": scenario,
                    "case": "Max Case",
                    "trial_id": int(selected["trial_id"]),
                    "final_net_project_equity": int(selected["final_net_project_equity"]),
                    "final_cash": int(selected["final_cash"]),
                    "cumulative_project_profit": int(selected["cumulative_project_profit"]),
                    "partner_memo_fields_status": "MISSING_EVIDENCE",
                    "partner_memo_fields": [
                        "Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance"
                    ],
                    "source_artifact": {
                        "run_id": STAGE12_RUN,
                        "run_head_sha": STAGE12_HEAD,
                        "artifact_id": int(stage12_artifact["id"]),
                        "artifact_name": stage12_name,
                        "artifact_size_bytes": int(stage12_artifact["size_in_bytes"]),
                        "artifact_api_digest": stage12_artifact.get("digest"),
                        **stage12_download,
                        **stage12_daily_evidence,
                    },
                    "daily_rows": selected_daily_payload,
                })
                report["stage12_daily_validation"]["scenarios_validated"] += 1
                report["stage12_daily_validation"]["daily_rows_validated"] += int(stage12_daily_evidence["daily_rows"])
                report["stage12_daily_validation"]["trial_result_fingerprint_mismatches"] += int(stage12_daily_evidence["mismatch_count"])
            else:
                report["stage12_daily_validation"]["scenarios_validated"] += 1
                report["stage12_daily_validation"]["daily_rows_validated"] += int(stage12_daily_evidence["daily_rows"])
            report["scenarios"].append({
                "scenario": scenario,
                "stage10_scenario_job": stage10_scenario_job,
                "source_artifact": {
                    "run_id": run_id,
                    "run_head_sha": expected_head,
                    "artifact_id": int(artifact["id"]),
                    "artifact_name": artifact_name,
                    "artifact_size_bytes": int(artifact["size_in_bytes"]),
                    "artifact_api_digest": artifact.get("digest"),
                    **download_evidence,
                },
                "trial_count": len(rows),
                "source_trial_rows_rehashed": sum(
                    int(item["trial_hashes_recomputed_from_parquet"]) for item in blocks
                ),
                "trial_result_hashes": {
                    str(trial_id): digest for trial_id, digest in sorted(trial_hashes.items())
                },
                "block_evidence": blocks,
                "stage12_daily_evidence": stage12_daily_evidence,
                "maxcase_daily_rows_extracted": len(selected_daily_payload) if selected_daily_payload is not None else 0,
                "maxcase_selection_status": selection_status,
                "maxcase_trial_id": int(selected["trial_id"]) if selected is not None else None,
                "maxcase_final_net_project_equity": (
                    selected["final_net_project_equity"] if selected is not None else None
                ),
                "maxcase_summary": selected,
                "maxcase_trial_result_sha256": (
                    trial_hashes.get(int(selected["trial_id"])) if selected is not None else None
                ),
                "existing_role_trial_ids": {
                    role: int(canonical_roles[role]) for role in ("P10", "P50", "P90", "Loss")
                },
                "representative_inventory_identity_matches_manifest": inventory_identity_matches,
                "matched_existing_roles": role_matches,
                "existing_payload_reusable_exactly": payload_reuse and inventory_identity_matches,
                "new_daily_payload_required": selected is not None and not payload_reuse,
                "partner_memo_fields_available_in_stage12_contract": (
                    stage12_contract_has["Partner1_Reinvestment_Balance"]
                    and stage12_contract_has["Partner2_Reinvestment_Balance"]
                ),
            })

    selected = [x for x in report["scenarios"] if x["maxcase_selection_status"] == "PASS"]
    undefined = [x for x in report["scenarios"] if x["maxcase_selection_status"] != "PASS"]
    payload_reuse = [x for x in selected if x["existing_payload_reusable_exactly"]]
    payload_missing = [x for x in selected if x["new_daily_payload_required"]]
    report["summary"] = {
        "scenario_count": len(report["scenarios"]),
        "expected_trial_rows": sum(1 if s.startswith("C100_") else 550 for s in SCENARIOS),
        "actual_trial_rows": sum(x["trial_count"] for x in report["scenarios"]),
        "trial_rows_rehashed": sum(x["source_trial_rows_rehashed"] for x in report["scenarios"]),
        "maxcase_positive_selected": len(selected),
        "undefined_business_rule_scenarios": [x["scenario"] for x in undefined],
        "maxcase_payload_can_reuse_existing_role": len(payload_reuse),
        "maxcase_payload_needs_new_daily_payload": len(payload_missing),
        "stage12_daily_scenarios_validated": report["stage12_daily_validation"]["scenarios_validated"],
        "stage12_daily_rows_validated": report["stage12_daily_validation"]["daily_rows_validated"],
        "maxcase_daily_rows_extracted": sum(len(x["daily_rows"]) for x in extracted_payloads),
        "representative_inventory_provenance_mismatch_count": len(inventory_mismatches),
        "representative_inventory_provenance_mismatch_scenarios": sorted(inventory_mismatch_scenarios),
        "new_payload_scenarios_missing_partner_memo_source": [
            x["scenario"] for x in payload_missing
            if not x["partner_memo_fields_available_in_stage12_contract"]
        ],
    }
    if (
        report["summary"]["scenario_count"] == 25
        and report["summary"]["actual_trial_rows"] == 11005
        and report["summary"]["trial_rows_rehashed"] == 11005
        and report["stage12_daily_validation"]["scenarios_validated"] == 25
        and report["stage12_daily_validation"]["daily_rows_validated"] == 22546465
        and report["stage12_daily_validation"]["trial_result_fingerprint_mismatches"] == 0
        and len(extracted_payloads) == 25
        and all(x["daily_rows"] for x in extracted_payloads)
        and all(x["source_artifact"]["artifact_zip_sha256"] == x["source_artifact"]["api_digest"].removeprefix("sha256:")
                for x in report["scenarios"])
        and all(x["source_artifact"]["artifact_zip_sha256"] == x["source_artifact"]["api_digest"].removeprefix("sha256:")
                for x in extracted_payloads)
    ):
        report["integrity_status"] = "PASS_SCOPED"
    else:
        report["integrity_status"] = "FAIL"
    if undefined:
        report["payload_status"] = "UNDEFINED_BUSINESS_RULE"
    elif (
        payload_missing
        or inventory_mismatches
        or not stage12_contract_has["Partner1_Reinvestment_Balance"]
        or not stage12_contract_has["Partner2_Reinvestment_Balance"]
    ):
        report["payload_status"] = "MISSING_EVIDENCE"
    else:
        report["payload_status"] = "EXISTING_PAYLOADS_REUSABLE"
    daily_payload_document = {
        "schema_version": "stage13-maxcase-daily-payloads-v1",
        "created_at_utc": report["created_at_utc"],
        "repository": REPO,
        "tested_head_sha": report["tested_head_sha"],
        "scope": "READ_ONLY_EXTRACTION_FROM_VERIFIED_STAGE12_PARQUET; NO_SIMULATION; NO_HISTORICAL_MUTATION; NOT_A_FINAL_WORKBOOK",
        "source_identity": report["source_identity"],
        "stage12_run": stage12_run,
        "stage12_global_sha256": roll_forward.get("expected_global_sha256_from_cp12b"),
        "scenario_count": len(extracted_payloads),
        "maxcase_daily_rows": sum(len(x["daily_rows"]) for x in extracted_payloads),
        "missing_fields": ["Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance"],
        "missing_fields_status": "MISSING_EVIDENCE",
        "scenarios": extracted_payloads,
    }
    Path("stage13_maxcase_daily_payloads.json").write_text(
        json.dumps(daily_payload_document, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return report


def main() -> None:
    out_path = Path("stage13_maxcase_source_audit.json")
    try:
        report = run_audit()
        out_path.write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({
            "integrity_status": report["integrity_status"],
            "payload_status": report["payload_status"],
            "summary": report.get("summary"),
            "output": str(out_path),
        }, ensure_ascii=False, sort_keys=True))
        if report["integrity_status"] != "PASS_SCOPED":
            raise SystemExit(1)
    except Exception as exc:
        failure = {
            "integrity_status": "FAIL",
            "payload_status": "MISSING_EVIDENCE",
            "error": str(exc),
            "traceback": traceback.format_exc()[-8000:],
            "tested_head_sha": os.environ.get("GITHUB_SHA"),
            "tested_branch": os.environ.get("GITHUB_REF_NAME"),
            "simulation_or_trial_executed": False,
            "historical_artifacts_modified": False,
        }
        out_path.write_text(
            json.dumps(failure, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(json.dumps(failure, ensure_ascii=False, sort_keys=True))
        raise


if __name__ == "__main__":
    main()
