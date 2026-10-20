from __future__ import annotations

import hashlib
import json
import os
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
    existing = {item["scenario"]: item for item in payload_inventory["artifacts"]}
    if set(existing) != set(SCENARIOS):
        raise RuntimeError("REPRESENTATIVE_INVENTORY_SCENARIO_SET_MISMATCH")
    if manifest.get("source_sha") != SOURCE_SHA or manifest.get("master_seed") != MASTER_SEED:
        raise RuntimeError("STAGE9A_MANIFEST_IDENTITY_MISMATCH")

    stage7_run = gatea.validate_run(STAGE7_RUN, STAGE7_HEAD, "success")
    stage10_run = gatea.validate_run(STAGE10_RUN, STAGE10_HEAD, None)
    stage7_artifacts, _ = gatea.artifact_index(STAGE7_RUN)
    stage10_artifacts, _ = gatea.artifact_index(STAGE10_RUN)

    contract_text = json.dumps(accounting_contract, ensure_ascii=False, sort_keys=True)
    workbook_daily_fields = [
        "Cash", "Net_Equity", "Active_Bikes", "Owned_Transferred_Bikes",
        "Pending_Claims", "Partner1_Reinvestment_Balance",
        "Partner2_Reinvestment_Balance",
    ]
    stage12_contract_has = {
        field: (f'"{field}"' in contract_text) for field in workbook_daily_fields
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
        "scope": "READ_ONLY_EXISTING_STAGE7_STAGE10_TRIALRESULTS; NO_SIMULATION; NO_STAGE12_ARTIFACT_MUTATION; NO_WORKBOOK",
        "source_identity": {
            "source_sha": SOURCE_SHA,
            "master_seed": MASTER_SEED,
            "reference_sha256": REFERENCE_SHA256,
            "stage9a_manifest_git_blob": __import__("subprocess").check_output(
                ["git", "hash-object", "docs/stage9a/dataset_manifest.json"], text=True
            ).strip(),
            "stage9a_global_manifest_sha256": manifest.get("global_manifest_sha256"),
        },
        "runs": {"stage7": stage7_run, "stage10": stage10_run},
        "daily_contract": {
            "contract_version": accounting_contract.get("contract_version"),
            "schema_version": accounting_contract.get("daily_ledger_schema", {}).get("schema_version"),
            "workbook_daily_fields_checked": stage12_contract_has,
            "fields_absent_from_stage12_contract": missing_from_stage12_contract,
        },
        "scenarios": [],
        "integrity_status": "NOT_STARTED",
        "payload_status": "NOT_STARTED",
        "historical_artifacts_modified": False,
        "historical_dataset_modified": False,
        "simulation_or_trial_executed": False,
        "workbook_built": False,
    }

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
            roles = existing[scenario]["roles"]
            role_matches: list[str] = []
            if selected is not None:
                role_matches = [
                    role for role, value in roles.items()
                    if int(value["trial_id"]) == int(selected["trial_id"])
                ]
            if selected is None:
                selection_status = "UNDEFINED_BUSINESS_RULE"
                payload_reuse = False
            else:
                selection_status = "PASS"
                payload_reuse = bool(role_matches)
            report["scenarios"].append({
                "scenario": scenario,
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
                "block_evidence": blocks,
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
                    role: int(value["trial_id"]) for role, value in roles.items()
                },
                "matched_existing_roles": role_matches,
                "existing_payload_reusable_exactly": payload_reuse,
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
        "new_payload_scenarios_missing_partner_memo_source": [
            x["scenario"] for x in payload_missing
            if not x["partner_memo_fields_available_in_stage12_contract"]
        ],
    }
    if (
        report["summary"]["scenario_count"] == 25
        and report["summary"]["actual_trial_rows"] == 11005
        and report["summary"]["trial_rows_rehashed"] == 11005
        and all(x["source_artifact"]["artifact_zip_sha256"] == x["source_artifact"]["api_digest"].removeprefix("sha256:")
                for x in report["scenarios"])
    ):
        report["integrity_status"] = "PASS_SCOPED"
    else:
        report["integrity_status"] = "FAIL"
    if undefined:
        report["payload_status"] = "UNDEFINED_BUSINESS_RULE"
    elif payload_missing:
        report["payload_status"] = "MISSING_EVIDENCE"
    else:
        report["payload_status"] = "EXISTING_PAYLOADS_REUSABLE"
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
