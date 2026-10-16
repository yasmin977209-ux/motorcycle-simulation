#!/usr/bin/env python3
"""Independent, read-only audit of the pinned CP-F representative source payloads."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any

from scripts.cp_daily_details_extension import (
    _audit_representative_balance_checks,
    _combine_representative_audit_statuses,
    stage10_trial_result_sha256,
)

SCENARIO = "C030_G030"
SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
MASTER_SEED = 20270101
SCHEMA_VERSION = "stage12-daily-accounting-v1"

SOURCE_RUN_ID = 38619859394
SOURCE_ARTIFACT_ID = 11922303249
SOURCE_ARTIFACT_SHA256 = "fff34ded9a85da5f0340cc98e089bd6d66cc9af2ecd28ce35f93f64293b0660"
SOURCE_MANIFEST_SHA256 = "5e1890e519e6853bb6f72f484517d4d5edb5ddcff88078af6c4a55eb2db2bbd3"
SOURCE_MANIFEST_BYTES = 65563

PRIOR_AUDIT_RUN_ID = 38838627191
PRIOR_AUDIT_ARTIFACT_ID = 12020867516
PRIOR_AUDIT_ARTIFACT_SHA256 = "e9656565101ddd1a8a4c7811bc879b04a57cd57e38b1e2f4e5053f770f1d3b88"
PRIOR_AUDIT_FILE_SHA256 = "4de463f14eceeaade14d468800d6eebfaeefd444a193a6208d1593308b7eaa39"
PRIOR_AUDIT_FILE_BYTES = 1923

ROLE_FILES = {
    "P10.json": {"role": "P10", "trial_id": 774, "bytes": 47477590,
                 "sha256": "d16fb40c4131448ad2b431226d206c3a166386abde30db0a5a08779b7bcdaa5e"},
    "P50.json": {"role": "P50", "trial_id": 748, "bytes": 49054525,
                 "sha256": "0e179c7e2a12ce12c50aece1d20187e94977512e8c6bd3ee0092a1daff098093"},
    "P90.json": {"role": "P90", "trial_id": 1193, "bytes": 51242475,
                 "sha256": "55f93bfcac87cc1515abe93e785bf6a65903b3147b3c395993ccafab547166bb"},
    "Loss.json": {"role": "LossCase", "trial_id": 981, "bytes": 45007176,
                  "sha256": "1fec3de0170f9d135475c32d6697c50f86f6d1bc5e52ea9f2889f537a43d015e"},
    "Max Case.json": {"role": "MaxCase", "trial_id": 233, "bytes": 56287776,
                      "sha256": "16b424a307c06d33568b9d4ff04f06aac132455c494ff22374b7aa2b516d9c5c"},
}


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _combine(states: list[str]) -> str:
    return _combine_representative_audit_statuses(states)


def _file_identity(path: Path, expected: dict[str, Any]) -> dict[str, Any]:
    if not path.is_file():
        return {"status": "NOT_VERIFIABLE", "reason_codes": ["REPRESENTATIVE_FILE_MISSING"]}
    raw = path.read_bytes()
    actual_sha = _sha256_bytes(raw)
    identity_failures = []
    if len(raw) != expected["bytes"]:
        identity_failures.append("REPRESENTATIVE_FILE_SIZE_MISMATCH")
    if actual_sha != expected["sha256"]:
        identity_failures.append("REPRESENTATIVE_FILE_SHA256_MISMATCH")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {
            "status": _combine(["FAIL" if identity_failures else "NOT_VERIFIABLE"]),
            "reason_codes": identity_failures + ["REPRESENTATIVE_JSON_INVALID"],
            "bytes": len(raw), "sha256": actual_sha, "payload": None,
        }
    if not isinstance(payload, dict):
        return {"status": "NOT_VERIFIABLE", "reason_codes": ["REPRESENTATIVE_PAYLOAD_NOT_OBJECT"],
                "bytes": len(raw), "sha256": actual_sha, "payload": None}
    return {
        "status": "FAIL" if identity_failures else "PASS",
        "reason_codes": identity_failures, "bytes": len(raw), "sha256": actual_sha,
        "payload": payload,
    }


def audit(input_dir: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = input_dir / "scenario_manifest.json"
    manifest = None
    manifest_state = "NOT_VERIFIABLE"
    manifest_reasons: list[str] = []
    manifest_raw: bytes | None = None
    if not manifest_path.is_file():
        manifest_reasons.append("SOURCE_MANIFEST_MISSING")
    else:
        manifest_raw = manifest_path.read_bytes()
        if len(manifest_raw) != SOURCE_MANIFEST_BYTES or _sha256_bytes(manifest_raw) != SOURCE_MANIFEST_SHA256:
            manifest_state = "FAIL"
            manifest_reasons.append("SOURCE_MANIFEST_PIN_MISMATCH")
        try:
            parsed = json.loads(manifest_raw.decode("utf-8"))
            if isinstance(parsed, dict):
                manifest = parsed
            else:
                manifest_reasons.append("SOURCE_MANIFEST_NOT_OBJECT")
        except (UnicodeDecodeError, json.JSONDecodeError):
            manifest_reasons.append("SOURCE_MANIFEST_INVALID_JSON")
        if manifest is not None:
            expected_fields = {
                "scenario": SCENARIO, "source_sha": SOURCE_SHA, "master_seed": MASTER_SEED,
                "schema_version": SCHEMA_VERSION,
            }
            bad_fields = [key for key, value in expected_fields.items() if manifest.get(key) != value]
            if bad_fields:
                manifest_state = "FAIL"
                manifest_reasons.append("SOURCE_MANIFEST_IDENTITY_MISMATCH:" + ",".join(bad_fields))
            elif manifest_state != "FAIL":
                manifest_state = "PASS"

    files: dict[str, Any] = {}
    file_states: list[str] = []
    roles_dir = input_dir / "representatives"
    expected_names = set(ROLE_FILES)
    found_names = {path.name for path in roles_dir.glob("*.json")} if roles_dir.is_dir() else set()
    unexpected_names = sorted(found_names - expected_names)
    if unexpected_names:
        file_states.append("NOT_VERIFIABLE")
    for filename, expected in ROLE_FILES.items():
        info = _file_identity(roles_dir / filename, expected)
        item: dict[str, Any] = {
            "role": expected["role"], "expected_trial_id": expected["trial_id"],
            "file_identity_status": info["status"],
            "bytes": info.get("bytes"), "sha256": info.get("sha256"),
            "file_identity_reason_codes": info.get("reason_codes", []),
            "balance_audit": {"status": "NOT_VERIFIABLE", "reason_codes": ["REPRESENTATIVE_PAYLOAD_UNAVAILABLE"]},
        }
        payload = info.get("payload")
        role_state = info["status"]
        if isinstance(payload, dict):
            summary = payload.get("summary")
            if not isinstance(summary, dict):
                item["summary_identity_status"] = "NOT_VERIFIABLE"
                item["summary_identity_reason_codes"] = ["SUMMARY_MISSING_OR_INVALID"]
                role_state = _combine([role_state, "NOT_VERIFIABLE"])
            else:
                summary_trial = summary.get("trial_id")
                summary_scenario = summary.get("scenario_id")
                manifest_selected = (manifest or {}).get("representative_trial_ids", {})
                selected_trial = manifest_selected.get(expected["role"]) if isinstance(manifest_selected, dict) else None
                summary_digest = stage10_trial_result_sha256(summary)
                manifest_hashes = (manifest or {}).get("trial_fingerprints", {})
                expected_fingerprint = manifest_hashes.get(str(expected["trial_id"])) if isinstance(manifest_hashes, dict) else None
                summary_reasons = []
                if summary_trial != expected["trial_id"] or summary_scenario != SCENARIO:
                    summary_reasons.append("REPRESENTATIVE_ROLE_IDENTITY_MISMATCH")
                if selected_trial != expected["trial_id"]:
                    summary_reasons.append("REPRESENTATIVE_TRIAL_ID_MISMATCH_WITH_MANIFEST")
                if not isinstance(expected_fingerprint, str):
                    summary_reasons.append("GOLDEN_FINGERPRINT_MISSING_FROM_MANIFEST")
                    fingerprint_status = "NOT_VERIFIABLE"
                elif summary_digest != expected_fingerprint:
                    summary_reasons.append("REPRESENTATIVE_FINGERPRINT_MISMATCH")
                    fingerprint_status = "FAIL"
                else:
                    fingerprint_status = "PASS"
                summary_status = "FAIL" if any(code.endswith("MISMATCH") for code in summary_reasons) else (
                    "NOT_VERIFIABLE" if summary_reasons else "PASS"
                )
                item.update({
                    "summary_trial_id": summary_trial, "summary_scenario": summary_scenario,
                    "summary_sha256": summary_digest, "manifest_golden_fingerprint": expected_fingerprint,
                    "fingerprint_check_status": fingerprint_status, "summary_identity_status": summary_status,
                    "summary_identity_reason_codes": summary_reasons,
                })
                role_state = _combine([role_state, summary_status, fingerprint_status])
            item["balance_audit"] = _audit_representative_balance_checks(payload)
            role_state = _combine([role_state, item["balance_audit"]["status"]])
        item["status"] = role_state
        files[filename] = item
        file_states.append(role_state)

    manifest_bytes_mismatch = manifest is not None and (
        len(manifest_raw or b"") != SOURCE_MANIFEST_BYTES or _sha256_bytes(manifest_raw or b"") != SOURCE_MANIFEST_SHA256
    )
    overall = _combine([manifest_state, *file_states])
    report = {
        "schema_version": "cp-representative-audit-v1",
        "status": overall,
        "scope": {
            "scenario": SCENARIO, "trial_generation": False, "monte_carlo_rerun": False,
            "statistical_checkpoint": False, "historical_data_mutated": False,
        },
        "execution": {
            "branch": os.environ.get("GITHUB_REF_NAME", "LOCAL_OR_UNSET"),
            "tested_sha": os.environ.get("GITHUB_SHA", "LOCAL_OR_UNSET"),
            "run_id": os.environ.get("GITHUB_RUN_ID", "LOCAL_OR_UNSET"),
            "run_attempt": os.environ.get("GITHUB_RUN_ATTEMPT", "LOCAL_OR_UNSET"),
        },
        "source": {
            "run_id": SOURCE_RUN_ID, "artifact_id": SOURCE_ARTIFACT_ID,
            "recorded_archive_sha256": SOURCE_ARTIFACT_SHA256,
            "scenario_manifest_bytes": len(manifest_raw) if manifest_raw is not None else None,
            "scenario_manifest_sha256": _sha256_bytes(manifest_raw) if manifest_raw is not None else None,
            "identity_status": manifest_state, "identity_reason_codes": manifest_reasons,
            "scenario_manifest_pin_mismatch": manifest_bytes_mismatch,
            "representative_files_found": sorted(found_names),
            "unexpected_representative_files": unexpected_names,
        },
        "previous_audit": {
            "run_id": PRIOR_AUDIT_RUN_ID, "artifact_id": PRIOR_AUDIT_ARTIFACT_ID,
            "artifact_sha256": PRIOR_AUDIT_ARTIFACT_SHA256,
            "representative_details_audit_sha256": PRIOR_AUDIT_FILE_SHA256,
            "representative_details_audit_bytes": PRIOR_AUDIT_FILE_BYTES,
            "reported_status": "PASS", "reported_balance_checks_per_role": 0,
        },
        "files": files,
        "status_semantics": {
            "PASS": "All five pinned role files have exact identity, full daily check coverage, numeric checks, and zero accounting imbalance.",
            "FAIL": "A pinned source identity/fingerprint mismatch or a proven accounting imbalance exists.",
            "NOT_VERIFIABLE": "Required input/check data is missing, empty, malformed, or insufficient to establish a complete daily audit.",
        },
    }
    if unexpected_names:
        report["status"] = _combine([report["status"], "NOT_VERIFIABLE"])
    report_path = output_dir / "representative_details_audit.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    if manifest_raw is not None:
        (output_dir / "source_scenario_manifest.json").write_bytes(manifest_raw)
    inventory_paths = [report_path]
    manifest_copy = output_dir / "source_scenario_manifest.json"
    if manifest_copy.is_file():
        inventory_paths.append(manifest_copy)
    inventory_items = []
    for path in sorted(inventory_paths):
        raw = path.read_bytes()
        inventory_items.append({"path": path.name, "size_bytes": len(raw), "sha256": _sha256_bytes(raw)})
    inventory = {
        "schema_version": "cp-representative-audit-inventory-v1",
        "status": report["status"], "files": inventory_items,
        "source_run_id": SOURCE_RUN_ID, "source_artifact_id": SOURCE_ARTIFACT_ID,
        "tested_sha": report["execution"]["tested_sha"], "run_id": report["execution"]["run_id"],
    }
    inventory_path = output_dir / "artifact_inventory.json"
    inventory_path.write_text(json.dumps(inventory, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    checksum_paths = sorted([*inventory_paths, inventory_path])
    checksum_text = "".join(f"{_sha256_bytes(path.read_bytes())}  {path.name}\n" for path in checksum_paths)
    (output_dir / "SHA256SUMS.txt").write_text(checksum_text, encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    report = audit(args.input_dir, args.output_dir)
    print(json.dumps({"status": report["status"], "source": report["source"], "files": {
        name: {"status": item["status"], "balance_status": item["balance_audit"]["status"],
               "daily_row_count": item["balance_audit"]["daily_row_count"],
               "balance_checks": item["balance_audit"]["balance_checks"],
               "verified_balance_checks": item["balance_audit"]["verified_balance_checks"]}
        for name, item in report["files"].items()
    }}, ensure_ascii=False, sort_keys=True))
    if report["status"] == "PASS":
        return 0
    if report["status"] == "FAIL":
        return 2
    return 1


if __name__ == "__main__":
    sys.exit(main())
