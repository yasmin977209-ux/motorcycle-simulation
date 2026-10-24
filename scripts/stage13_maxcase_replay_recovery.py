#!/usr/bin/env python3
"""Recover missing Stage 13 MaxCase memo balances by exact, source-pinned Trial replay.

Only the ten already-selected historical Trial IDs are replayed. No new Trial IDs,
seed/RNG changes, canonical Stage 12 writes, or workbook builds are performed.
A replay is accepted only when its TrialResult SHA-256 and every daily accounting
field available in the immutable Stage 12 payload match exactly.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict
from datetime import date, timedelta, datetime, timezone
from pathlib import Path
from typing import Any

import constants
import daily_engine
import monte_carlo
from entities import BikeState, ClaimStatus

REPOSITORY = "yasmin977209-ux/motorcycle-simulation"
SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
MASTER_SEED = 20270101
SOURCE_AUDIT_ARTIFACT_ID = 12544311885
SOURCE_AUDIT_RUN_ID = 40053300044
SOURCE_AUDIT_ZIP_SHA256 = "93b150e5d3360c8d160f3facad85c28dc676819466ed3fded3167bcb703c3f32"
SOURCE_AUDIT_JSON_SHA256 = "f599e59d5e8fa66e42a4bff7f42849bf7a627f79c88a48fd44bf519632bdb468"
SOURCE_PAYLOADS_JSON_SHA256 = "c2c0e2b9541534c59901bbcd369f4d9cf6e630f35c0f7b18b8ce542e3ca52e9d"
REFERENCE_SHA256 = "ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479"
STAGE9A_GLOBAL_SHA256 = "892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6"
STAGE9A_MANIFEST_GIT_BLOB = "c8591aac3d309fd94c4e67a547d33fb62ac5694d"
STAGE12_GLOBAL_SHA256 = "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44"
AUDIT_TESTED_HEAD = "73934c2062e8dc7e1062b9a784cf07b6a16cce28"
PARTNER_FIELDS = ("Partner1_Reinvestment_Balance", "Partner2_Reinvestment_Balance")
DAILY_COMMON_FIELDS = (
    "date", "trial_id", "Cash", "Net_Equity", "Cumulative_Project_Profit",
    "Active_Bikes", "Owned_Transferred_Bikes", "Pending_Claims",
    "Final_Close_Date", "source_sha", "master_seed", "result_sha256",
)
EXPECTED_SOURCE_IDENTITY = {
    "master_seed": MASTER_SEED,
    "reference_sha256": REFERENCE_SHA256,
    "source_sha": SOURCE_SHA,
    "stage9a_global_manifest_sha256": STAGE9A_GLOBAL_SHA256,
    "stage9a_manifest_git_blob": STAGE9A_MANIFEST_GIT_BLOB,
}
# Exact selected IDs and per-Trial hashes from the pinned Stage 12 / MaxCase audit.
RECOVERY_PLAN = {
    "C085_G030": {"trial_id": 53, "trial_result_sha256": "0261e6cac29254da77b97d5eb23153a1f893fcdc0fa41e9a2758ce9b251ec1d8", "daily_rows": 2198},
    "C070_G100": {"trial_id": 106, "trial_result_sha256": "9ebab5b0c761acd8344908d18aa83d97924732705fac79bfa0a537e2b94d3f3e", "daily_rows": 2202},
    "C070_G050": {"trial_id": 544, "trial_result_sha256": "20e34e66c37c56b2394de7a70331b423141ea895d325b6268c5c2e12f736eff0", "daily_rows": 2200},
    "C070_G030": {"trial_id": 429, "trial_result_sha256": "37b9e148f2f27ee899a2f7b44bd137d5488e7c27312b583bb8c524118b8af6ba", "daily_rows": 2200},
    "C070_G000": {"trial_id": 165, "trial_result_sha256": "13375cf2422a44b13683a32249c633e63a424d294deebc5134d7f6de2b266077", "daily_rows": 2202},
    "C050_G100": {"trial_id": 172, "trial_result_sha256": "5cd0f174d868004c96c5058f04c256e8b16312f70309b70d7f3cd272206764a4", "daily_rows": 2233},
    "C050_G070": {"trial_id": 7, "trial_result_sha256": "e4ff429687e9af845082252a066ad1b67c7d111f1f192057d2e62fc2486cd8b4", "daily_rows": 2222},
    "C050_G050": {"trial_id": 543, "trial_result_sha256": "16f01fb5a27bb6302480bc31f6e665d1a61990d8754af14671bf2f1f329792d5", "daily_rows": 2232},
    "C050_G030": {"trial_id": 122, "trial_result_sha256": "9467b01b5a897fcacf619c3524fe4f1a45d3386ecf01486409e4a8f19b0c466a", "daily_rows": 2231},
    "C030_G000": {"trial_id": 199, "trial_result_sha256": "ceda99eca77b00d117aa42574c088d9a98cea1ca5f88c804056b727d45c87a16", "daily_rows": 1655},
}
# Canonical Git blob SHA-1 identities at SOURCE_SHA for the deterministic engine.
EXPECTED_ENGINE_BLOBS = {
    "accounting.py": "8bbbfacbefa4290dd3efbdee2aee3cc7661a42b4",
    "closure.py": "3307e1759f84badd37686d3c44c78e87092cb1e0",
    "collection.py": "54a5d1c3be41d49841bed887c7bab393a2d83dc6",
    "constants.py": "88b3e7b5a509f8486597ac08dfc5acaf80d4d39b",
    "daily_engine.py": "6c4496c3e9a9b41668c3d93063ad31d96df5f878",
    "dateutils.py": "30a55ac360f2d5befc28a58b7ff224ba3b0bb39a",
    "depreciation.py": "d3f0999ad3edc0141501827dd1b8985130023779",
    "entities.py": "028c4c6e93ec80c4c1291cf69147372da66d0271",
    "guarantee.py": "d493a49855d8badd714e1f4633b64d695fbd53b5",
    "monte_carlo.py": "a8c3603487f92d3e15c3d754ce3faee3580a5f46",
    "partner_equity.py": "887a9401b7e0a6abeec49033d38f80e70cfaf51a",
    "rng.py": "e50d0410729aeeb657d4b187c0bc32f9527442d1",
}


def _sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def _read_pinned_json(path: Path, expected_sha256: str, error_code: str) -> dict[str, Any]:
    raw = path.read_bytes()
    actual = _sha256_bytes(raw)
    if actual != expected_sha256:
        raise RuntimeError(f"{error_code}_SHA256_MISMATCH: expected={expected_sha256} actual={actual}")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"{error_code}_JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise RuntimeError(f"{error_code}_ROOT_INVALID")
    return value


def verify_engine_identity() -> dict[str, str]:
    actual = {}
    for filename, expected in EXPECTED_ENGINE_BLOBS.items():
        path = Path(filename)
        if not path.is_file():
            raise RuntimeError(f"PINNED_ENGINE_FILE_MISSING: {filename}")
        digest = _git_blob_sha(path.read_bytes())
        actual[filename] = digest
        if digest != expected:
            raise RuntimeError(f"PINNED_ENGINE_BLOB_MISMATCH: {filename} expected={expected} actual={digest}")
    return actual


def _strict_equal(actual: Any, expected: Any) -> bool:
    return type(actual) is type(expected) and actual == expected


def _load_and_validate_inputs(audit_path: Path, payloads_path: Path) -> tuple[dict, dict, dict, dict]:
    audit = _read_pinned_json(audit_path, SOURCE_AUDIT_JSON_SHA256, "SOURCE_AUDIT")
    payloads = _read_pinned_json(payloads_path, SOURCE_PAYLOADS_JSON_SHA256, "SOURCE_PAYLOADS")
    if audit.get("schema_version") != "stage13-maxcase-source-audit-v1":
        raise RuntimeError("SOURCE_AUDIT_SCHEMA_MISMATCH")
    if payloads.get("schema_version") != "stage13-maxcase-daily-payloads-v1":
        raise RuntimeError("SOURCE_PAYLOADS_SCHEMA_MISMATCH")
    if (
        audit.get("repository") != REPOSITORY
        or payloads.get("repository") != REPOSITORY
        or audit.get("tested_head_sha") != AUDIT_TESTED_HEAD
        or payloads.get("tested_head_sha") != AUDIT_TESTED_HEAD
        or audit.get("created_at_utc") != payloads.get("created_at_utc")
        or audit.get("source_identity") != EXPECTED_SOURCE_IDENTITY
        or payloads.get("source_identity") != EXPECTED_SOURCE_IDENTITY
        or payloads.get("stage12_global_sha256") != STAGE12_GLOBAL_SHA256
    ):
        raise RuntimeError("SOURCE_AUDIT_PAIR_OR_CANONICAL_IDENTITY_MISMATCH")
    if (
        audit.get("integrity_status") != "PASS_SCOPED"
        or audit.get("payload_status") != "MISSING_EVIDENCE"
        or audit.get("historical_dataset_modified") is not False
        or audit.get("historical_artifacts_modified") is not False
        or audit.get("workbook_built") is not False
        or audit.get("simulation_or_trial_executed") is not False
    ):
        raise RuntimeError("SOURCE_AUDIT_DISPOSITION_NOT_AS_EXPECTED")
    summary = audit.get("summary")
    stage12 = audit.get("stage12_daily_validation")
    if not isinstance(summary, dict) or not isinstance(stage12, dict):
        raise RuntimeError("SOURCE_AUDIT_SUMMARY_MISSING")
    if (
        summary.get("scenario_count") != 25
        or summary.get("expected_trial_rows") != 11005
        or summary.get("actual_trial_rows") != 11005
        or summary.get("trial_rows_rehashed") != 11005
        or stage12.get("scenarios_validated") != 25
        or stage12.get("daily_rows_validated") != 22546465
        or stage12.get("trial_result_fingerprint_mismatches") != 0
    ):
        raise RuntimeError("SOURCE_AUDIT_INTEGRITY_COVERAGE_MISMATCH")
    audit_scenarios = audit.get("scenarios")
    payload_scenarios = payloads.get("scenarios")
    if not isinstance(audit_scenarios, list) or not isinstance(payload_scenarios, list):
        raise RuntimeError("SOURCE_AUDIT_SCENARIO_LIST_MISSING")
    audit_by_scenario = {}
    payload_by_scenario = {}
    for item in audit_scenarios:
        if not isinstance(item, dict) or not isinstance(item.get("scenario"), str):
            raise RuntimeError("SOURCE_AUDIT_SCENARIO_INVALID")
        if item["scenario"] in audit_by_scenario:
            raise RuntimeError(f"SOURCE_AUDIT_DUPLICATE_SCENARIO: {item['scenario']}")
        audit_by_scenario[item["scenario"]] = item
    for item in payload_scenarios:
        if not isinstance(item, dict) or not isinstance(item.get("scenario"), str):
            raise RuntimeError("SOURCE_PAYLOAD_SCENARIO_INVALID")
        if item["scenario"] in payload_by_scenario:
            raise RuntimeError(f"SOURCE_PAYLOAD_DUPLICATE_SCENARIO: {item['scenario']}")
        payload_by_scenario[item["scenario"]] = item
    if len(audit_by_scenario) != 25 or set(payload_by_scenario) != set(audit_by_scenario):
        raise RuntimeError("SOURCE_AUDIT_SCENARIO_COVERAGE_MISMATCH")
    if set(summary.get("non_c100_maxcase_payloads_missing_partner_memo_source", [])) != set(RECOVERY_PLAN):
        raise RuntimeError("SOURCE_MISSING_SCENARIO_SET_MISMATCH")
    if payloads.get("scenario_count") != 25:
        raise RuntimeError("SOURCE_PAYLOAD_SCENARIO_COUNT_MISMATCH")
    for scenario, plan in RECOVERY_PLAN.items():
        audit_item = audit_by_scenario.get(scenario)
        payload_item = payload_by_scenario.get(scenario)
        if not isinstance(audit_item, dict) or not isinstance(payload_item, dict):
            raise RuntimeError(f"SOURCE_SCENARIO_REQUIRED: {scenario}")
        trial_id = plan["trial_id"]
        trial_hash = plan["trial_result_sha256"]
        source_days = payload_item.get("daily_rows")
        if (
            audit_item.get("maxcase_selection_status") != "PASS"
            or audit_item.get("maxcase_trial_id") != trial_id
            or audit_item.get("maxcase_trial_result_sha256") != trial_hash
            or not isinstance(audit_item.get("trial_result_hashes"), dict)
            or audit_item["trial_result_hashes"].get(str(trial_id)) != trial_hash
            or payload_item.get("trial_id") != trial_id
            or payload_item.get("partner_memo_fields_status") != "MISSING_EVIDENCE"
            or not isinstance(source_days, list)
            or len(source_days) != plan["daily_rows"]
            or payload_item.get("case") != "Max Case"
        ):
            raise RuntimeError(f"SOURCE_SELECTED_TRIAL_IDENTITY_MISMATCH: {scenario}")
        for row in source_days:
            if not isinstance(row, dict):
                raise RuntimeError(f"SOURCE_DAILY_ROW_INVALID: {scenario}")
            if (
                row.get("trial_id") != trial_id
                or row.get("source_sha") != SOURCE_SHA
                or row.get("master_seed") != MASTER_SEED
                or row.get("result_sha256") != trial_hash
                or row.get("Partner1_Reinvestment_Balance") != "PENDING_DATA_SOURCE"
                or row.get("Partner2_Reinvestment_Balance") != "PENDING_DATA_SOURCE"
            ):
                raise RuntimeError(f"SOURCE_DAILY_ROW_IDENTITY_OR_PENDING_MARKER_INVALID: {scenario}")
    return audit, payloads, audit_by_scenario, payload_by_scenario


def _daily_snapshot(project, current_date: date, trial_id: int) -> dict[str, Any]:
    return {
        "date": current_date.isoformat(),
        "trial_id": trial_id,
        "Cash": project.project_cash,
        "Net_Equity": project.capital + project.retained_earnings,
        # Reference §10.10 defines the representative ledger's cumulative profit as retained earnings.
        "Cumulative_Project_Profit": project.retained_earnings,
        "Active_Bikes": sum(1 for bike in project.bikes if bike.current_state in daily_engine.POSSESSION_STATES),
        "Owned_Transferred_Bikes": sum(1 for bike in project.bikes if bike.current_state is BikeState.OWNED_TRANSFERRED),
        "Pending_Claims": sum(1 for claim in project.guarantee_claims if claim.status is ClaimStatus.PENDING),
        "Partner1_Reinvestment_Balance": project.partner1_reinvestment_balance,
        "Partner2_Reinvestment_Balance": project.partner2_reinvestment_balance,
    }


def _trial_result_sha256(result) -> str:
    raw = json.dumps(
        asdict(result), ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str
    ).encode("utf-8")
    return _sha256_bytes(raw)


def _replay_one(scenario: str, plan: dict, audit_item: dict, payload_item: dict) -> dict:
    trial_id = plan["trial_id"]
    probability, recovery_rate = monte_carlo.parse_scenario_id(scenario)
    replay_rows: list[dict[str, Any]] = []
    project = daily_engine.run_deterministic_trial(
        recovery_rate_pct=recovery_rate,
        trial_id=trial_id,
        scenario_id=scenario,
        master_seed=MASTER_SEED,
        collection_probability=probability,
        on_day_end=lambda p, d: replay_rows.append(_daily_snapshot(p, d, trial_id)),
        log_events=False,
    )
    result = monte_carlo._trial_result_from_project(
        project, scenario_id=scenario, collection_probability=probability,
        recovery_rate_pct=recovery_rate, trial_id=trial_id,
    )
    actual_hash = _trial_result_sha256(result)
    expected_hash = plan["trial_result_sha256"]
    if actual_hash != expected_hash:
        raise RuntimeError(f"TRIAL_RESULT_SHA256_MISMATCH: {scenario}/{trial_id} expected={expected_hash} actual={actual_hash}")
    expected_summary = audit_item.get("maxcase_summary")
    if not isinstance(expected_summary, dict):
        raise RuntimeError(f"SOURCE_MAXCASE_SUMMARY_MISSING: {scenario}")
    for key, actual in asdict(result).items():
        expected = expected_summary.get(key)
        if not _strict_equal(actual, expected):
            raise RuntimeError(f"TRIAL_RESULT_SUMMARY_MISMATCH: {scenario}/{trial_id}:{key} expected={expected!r} actual={actual!r}")
    if len(replay_rows) != plan["daily_rows"]:
        raise RuntimeError(f"DAILY_ROW_COUNT_MISMATCH: {scenario}/{trial_id} expected={plan['daily_rows']} actual={len(replay_rows)}")
    final_close = result.final_close_date
    if not isinstance(final_close, str) or not final_close:
        raise RuntimeError(f"TRIAL_FINAL_CLOSE_DATE_MISSING: {scenario}/{trial_id}")
    for row in replay_rows:
        row["Final_Close_Date"] = final_close
        row["source_sha"] = SOURCE_SHA
        row["master_seed"] = MASTER_SEED
        row["result_sha256"] = actual_hash

    source_rows = payload_item["daily_rows"]
    if len(source_rows) != len(replay_rows):
        raise RuntimeError(f"STAGE12_DAILY_ROW_COUNT_MISMATCH: {scenario}")
    prior_day = None
    final_close_day = date.fromisoformat(final_close)
    for index, (actual, expected) in enumerate(zip(replay_rows, source_rows)):
        for field in DAILY_COMMON_FIELDS:
            if not _strict_equal(actual.get(field), expected.get(field)):
                raise RuntimeError(f"STAGE12_DAILY_FIELD_MISMATCH: {scenario}/{trial_id}/row={index}/{field} expected={expected.get(field)!r} actual={actual.get(field)!r}")
        actual_day = date.fromisoformat(actual["date"])
        if prior_day is not None and actual_day != prior_day + timedelta(days=1):
            raise RuntimeError(f"REPLAY_DAILY_DATE_GAP: {scenario}/{trial_id}/{index}")
        prior_day = actual_day
        for field in PARTNER_FIELDS:
            value = actual.get(field)
            if type(value) is not int or value < 0:
                raise RuntimeError(f"REPLAY_PARTNER_MEMO_BALANCE_INVALID: {scenario}/{trial_id}/{index}/{field}")
    if not replay_rows or prior_day != final_close_day or replay_rows[-1]["Final_Close_Date"] != replay_rows[-1]["date"]:
        raise RuntimeError(f"REPLAY_DAILY_TERMINAL_DATE_MISMATCH: {scenario}/{trial_id}")
    return {
        "scenario": scenario,
        "trial_id": trial_id,
        "trial_result_sha256": actual_hash,
        "status": "PASS_EXACT_REPLAY_AND_STAGE12_COMMON_FIELDS",
        "daily_row_count": len(replay_rows),
        "first_date": replay_rows[0]["date"],
        "final_close_date": final_close,
        "summary": asdict(result),
        "comparison_contract": {
            "compared_common_daily_fields": list(DAILY_COMMON_FIELDS),
            "replay_only_recovered_fields": list(PARTNER_FIELDS),
            "stage12_trial_result_hash_equal": True,
            "all_daily_common_fields_equal": True,
            "dates_consecutive": True,
            "memo_balances_integer_nonnegative": True,
        },
        "daily_rows": replay_rows,
    }


def run_recovery(audit_path: Path, payloads_path: Path, output_path: Path) -> tuple[dict, int]:
    engine_blobs = verify_engine_identity()
    audit, payloads, audit_by_scenario, payload_by_scenario = _load_and_validate_inputs(audit_path, payloads_path)
    results, errors = [], []
    for scenario, plan in RECOVERY_PLAN.items():
        try:
            results.append(_replay_one(scenario, plan, audit_by_scenario[scenario], payload_by_scenario[scenario]))
        except Exception as exc:
            errors.append({"scenario": scenario, "trial_id": plan["trial_id"], "error_type": type(exc).__name__, "error": str(exc)})
    passed = [item for item in results if item.get("status") == "PASS_EXACT_REPLAY_AND_STAGE12_COMMON_FIELDS"]
    report = {
        "schema_version": "stage13-maxcase-replay-recovery-v1",
        "repository": REPOSITORY,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if len(passed) == len(RECOVERY_PLAN) and not errors else "FAIL",
        "scope": "EXACT_REPLAY_OF_TEN_ALREADY_SELECTED_CANONICAL_TRIALS_ONLY; NO_NEW_TRIAL_IDS; NO_STAGE12_OR_HISTORICAL_MUTATION; NO_WORKBOOK_BUILD",
        "owner_authorization": "EXPLICIT_USER_DELEGATION_2026-10-24_FOR_BOUNDED_EXACT_TRIAL_REPLAY",
        "source_identity": EXPECTED_SOURCE_IDENTITY,
        "pinned_source_commit": SOURCE_SHA,
        "pinned_engine_git_blobs": engine_blobs,
        "input_artifacts": {
            "audit_artifact_id": SOURCE_AUDIT_ARTIFACT_ID,
            "audit_run_id": SOURCE_AUDIT_RUN_ID,
            "audit_artifact_zip_sha256": SOURCE_AUDIT_ZIP_SHA256,
            "audit_json_sha256": _sha256_bytes(audit_path.read_bytes()),
            "payloads_json_sha256": _sha256_bytes(payloads_path.read_bytes()),
            "stage12_global_sha256": STAGE12_GLOBAL_SHA256,
            "stage12_daily_rows_validated_before_replay": 22546465,
            "stage12_trial_fingerprint_mismatches_before_replay": 0,
            "source_audit_tested_head_sha": AUDIT_TESTED_HEAD,
            "source_audit_integrity_status": audit.get("integrity_status"),
            "source_audit_payload_status_before_replay": audit.get("payload_status"),
        },
        "execution": {
            "selected_trials_expected": len(RECOVERY_PLAN),
            "selected_trials_replayed": len(RECOVERY_PLAN),
            "successful_trials": len(passed),
            "new_trial_ids_created": False,
            "canonical_stage12_files_modified": False,
            "source_artifacts_modified": False,
            "random_seed_or_rng_changed": False,
            "production_workbook_built": False,
            "monte_carlo_expansion_run": False,
            "checkpoint_run": False,
        },
        "summary": {
            "expected_scenarios": len(RECOVERY_PLAN),
            "passed_scenarios": [item["scenario"] for item in passed],
            "failed_scenarios": [item["scenario"] for item in errors],
            "recovered_daily_rows": sum(item["daily_row_count"] for item in passed),
            "source_trial_hash_mismatches": sum("TRIAL_RESULT_SHA256_MISMATCH" in item["error"] for item in errors),
            "stage12_common_field_mismatches": sum("STAGE12_DAILY_FIELD_MISMATCH" in item["error"] for item in errors),
        },
        "scenarios": results,
        "errors": errors,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    raw = (json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    output_path.write_bytes(raw)
    print(json.dumps({
        "status": report["status"],
        "pinned_source_commit": SOURCE_SHA,
        "replayed": report["execution"]["selected_trials_replayed"],
        "successful": report["execution"]["successful_trials"],
        "failed_scenarios": report["summary"]["failed_scenarios"],
        "recovered_daily_rows": report["summary"]["recovered_daily_rows"],
        "output_path": str(output_path),
        "output_sha256": _sha256_bytes(raw),
        "historical_mutation": False,
    }, ensure_ascii=False, sort_keys=True))
    return report, 0 if report["status"] == "PASS" else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", required=True, type=Path)
    parser.add_argument("--payloads", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        _, code = run_recovery(args.audit, args.payloads, args.output)
        return code
    except Exception as exc:
        failure = {
            "schema_version": "stage13-maxcase-replay-recovery-v1",
            "repository": REPOSITORY,
            "status": "FAIL",
            "scope": "EXACT_REPLAY_OF_TEN_ALREADY_SELECTED_CANONICAL_TRIALS_ONLY",
            "pinned_source_commit": SOURCE_SHA,
            "error_type": type(exc).__name__,
            "error": str(exc),
            "canonical_stage12_files_modified": False,
            "source_artifacts_modified": False,
            "production_workbook_built": False,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(failure, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(failure, ensure_ascii=False, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
