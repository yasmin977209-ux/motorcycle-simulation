from __future__ import annotations

import argparse
import hashlib
import json
import tarfile
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

from scripts.stage13_assemble import (
    DATE_FMT,
    FINANCE_FMT,
    EXPECTED_SCENARIOS,
    assemble_workbook,
    build_scenario_summary,
    collect_excel_errors,
    ensure_date,
    load_json,
    metric_stats,
    numeric_metrics,
    patch_xlsx_numeric_values,
    py_value,
    save_workbook_preserving_stats_precision,
    select_representative_trial_ids,
    sha256_file,
    style_sheet,
    write_acctg_sheet,
    write_assets_sheet,
    write_constants,
    write_daily_sheet,
    write_errors,
    write_final_closure,
    write_generic,
    write_heatmap,
    write_partner_sheet,
    write_readme,
    write_scenario_detail,
    write_scenario_matrix,
    write_stats_sheet,
    write_table,
    write_validation,
    write_sensitivity_sheet as write_sensitivity,
    write_daily_distribution as _write_daily_distribution,
    write_representatives as _write_representatives,
)


MAXCASE_AUDIT_SCHEMA = "stage13-maxcase-source-audit-v1"
MAXCASE_PAYLOAD_SCHEMA = "stage13-maxcase-daily-payloads-v1"
MAXCASE_EXPECTED_SOURCE_IDENTITY = {
    "master_seed": 20270101,
    "reference_sha256": "ee277aea4f68ffa2e801e100ebb8eee939c44b2c6150494aea0a6c4d1a6b7479",
    "source_sha": "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b",
    "stage9a_global_manifest_sha256": "892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6",
    "stage9a_manifest_git_blob": "c8591aac3d309fd94c4e67a547d33fb62ac5694d",
}
MAXCASE_REPLAY_EXPECTED_SOURCE_IDENTITY = {
    **MAXCASE_EXPECTED_SOURCE_IDENTITY,
    "stage9a_manifest_git_blob": "e796fa2443493b607f1f9c60b58eb63607959c26",
}
MAXCASE_EXPECTED_C050_ARTIFACT_ID = 11503510055
MAXCASE_EXPECTED_C050_ENRICHMENT_RUN_ID = 37662891608
MAXCASE_EXPECTED_C050_POINTER_PREVIOUS_ARTIFACT_ID = 11503191706
MAXCASE_EXPECTED_C050_POINTER_PREVIOUS_RUN_ID = 37660610243
MAXCASE_EXPECTED_STAGE12_GLOBAL_SHA256 = (
    "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44"
)
MAXCASE_REQUIRED_MEMO_FIELDS = (
    "Partner1_Reinvestment_Balance",
    "Partner2_Reinvestment_Balance",
)

MAXCASE_REPLAY_SCHEMA = "stage13-maxcase-replay-recovery-v1"
MAXCASE_REPLAY_EXPECTED_JSON_SHA256 = (
    "c477e390a5b0b9c8c35a3d5474e5b359056e59d1f2254395e589af4621982006"
)
MAXCASE_REPLAY_EXPECTED_ARTIFACT = {
    "artifact_id": 12542814312,
    "artifact_run_id": 40050459020,
    "artifact_zip_sha256": "85e0d747044910d8d9837085b3a221a7459feb418eb78776ae3b4f1a31f5db68",
    "recovery_json_sha256": MAXCASE_REPLAY_EXPECTED_JSON_SHA256,
    "recovery_script_git_blob_sha": "fbfe660b6847f42f89bb40c7eea474eca61e0a2c",
    "tested_head_sha": "d80b91579bdfda6277f630ece764777261df2059",
}
MAXCASE_REPLAY_EXPECTED_ENGINE_BLOBS = {
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
MAXCASE_REPLAY_PLAN = {
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
MAXCASE_REPLAY_COMMON_DAILY_FIELDS = (
    "date", "trial_id", "Cash", "Net_Equity", "Cumulative_Project_Profit",
    "Active_Bikes", "Owned_Transferred_Bikes", "Pending_Claims",
    "Final_Close_Date", "source_sha", "master_seed", "result_sha256",
)
MAXCASE_REPLAY_RECOVERED_ROWS = 21575
MAXCASE_REPLAY_SOURCE_AUDIT_JSON_SHA256 = (
    "b9ba0ff23b3dfd42abd7436b7935017f15ba8cbaf5198d8e31093a56441fb951"
)
MAXCASE_REPLAY_SOURCE_PAYLOADS_JSON_SHA256 = (
    "096a85448ff5c7ece0648739fdc4ccad499763f1862467751983e0152f8e8c7d"
)
MAXCASE_REPLAY_SOURCE_AUDIT_ZIP_SHA256 = (
    "88abdc9e0ce4097df044280b517f08b1595642476c8d596ac13fc128b88092b3"
)


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(
        char in "0123456789abcdef" for char in value
    )


def _git_blob_sha(raw: bytes) -> str:
    """Return Git's canonical SHA-1 blob identity for exact source bytes."""
    header = b"blob " + str(len(raw)).encode("ascii") + b"\0"
    return hashlib.sha1(header + raw).hexdigest()


def _validate_active_stage9a_manifest(
    manifest: dict[str, Any], *, manifest_git_blob_sha: str,
) -> None:
    """Require the one current Stage 9A manifest pointer approved on main."""
    if manifest_git_blob_sha != MAXCASE_EXPECTED_SOURCE_IDENTITY["stage9a_manifest_git_blob"]:
        raise RuntimeError("MAXCASE_ACTIVE_MANIFEST_GIT_BLOB_MISMATCH")
    artifact_manifest = manifest.get("artifact_manifest")
    enriched = artifact_manifest.get("enriched_artifacts") if isinstance(artifact_manifest, dict) else None
    enrichment_runs = artifact_manifest.get("enrichment_run_ids") if isinstance(artifact_manifest, dict) else None
    if (
        manifest.get("source_sha") != MAXCASE_EXPECTED_SOURCE_IDENTITY["source_sha"]
        or manifest.get("master_seed") != MAXCASE_EXPECTED_SOURCE_IDENTITY["master_seed"]
        or manifest.get("reference_sha256") != MAXCASE_EXPECTED_SOURCE_IDENTITY["reference_sha256"]
        or manifest.get("global_manifest_sha256") != MAXCASE_EXPECTED_SOURCE_IDENTITY["stage9a_global_manifest_sha256"]
        or not isinstance(enriched, dict)
        or not isinstance(enrichment_runs, dict)
        or enriched.get("C050_G000") != MAXCASE_EXPECTED_C050_ARTIFACT_ID
        or enrichment_runs.get("C050_G000") != MAXCASE_EXPECTED_C050_ENRICHMENT_RUN_ID
    ):
        raise RuntimeError("MAXCASE_ACTIVE_MANIFEST_IDENTITY_OR_C050_POINTER_MISMATCH")


def _read_maxcase_audit_bundle(
    audit_path: str | Path,
    payloads_path: str | Path,
    *,
    audit_sha256: str | None,
    payloads_sha256: str | None,
    manifest: dict[str, Any],
    manifest_git_blob_sha: str,
) -> dict[str, Any]:
    """Load a paired, digest-pinned MaxCase audit and daily-payload export.

    This source audit supports diagnostic assembly only. The Stage 13 assembler is
    not the project release gate and must never infer final acceptance from a build.
    """
    _validate_active_stage9a_manifest(
        manifest, manifest_git_blob_sha=manifest_git_blob_sha,
    )
    if not _is_sha256(audit_sha256) or not _is_sha256(payloads_sha256):
        raise RuntimeError("MAXCASE_AUDIT_SHA256_REQUIRED")
    audit_raw = Path(audit_path).read_bytes()
    payloads_raw = Path(payloads_path).read_bytes()
    actual_audit_sha = hashlib.sha256(audit_raw).hexdigest()
    actual_payloads_sha = hashlib.sha256(payloads_raw).hexdigest()
    if actual_audit_sha != audit_sha256:
        raise RuntimeError(
            f"MAXCASE_AUDIT_DIGEST_MISMATCH: expected={audit_sha256} actual={actual_audit_sha}"
        )
    if actual_payloads_sha != payloads_sha256:
        raise RuntimeError(
            f"MAXCASE_PAYLOADS_DIGEST_MISMATCH: expected={payloads_sha256} actual={actual_payloads_sha}"
        )
    try:
        audit = json.loads(audit_raw.decode("utf-8"))
        payload_document = json.loads(payloads_raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("MAXCASE_AUDIT_JSON_INVALID") from exc
    if not isinstance(audit, dict) or not isinstance(payload_document, dict):
        raise RuntimeError("MAXCASE_AUDIT_ROOT_INVALID")
    if audit.get("schema_version") != MAXCASE_AUDIT_SCHEMA:
        raise RuntimeError("MAXCASE_AUDIT_SCHEMA_MISMATCH")
    if payload_document.get("schema_version") != MAXCASE_PAYLOAD_SCHEMA:
        raise RuntimeError("MAXCASE_PAYLOADS_SCHEMA_MISMATCH")
    # Pin the source-audit execution head: this report's source reader/selector code
    # is itself part of the provenance chain, not interchangeable by schema alone.
    if audit.get("tested_head_sha") != "73934c2062e8dc7e1062b9a784cf07b6a16cce28":
        raise RuntimeError("MAXCASE_AUDIT_EXECUTION_HEAD_NOT_APPROVED")
    run_records = audit.get("runs")
    if not isinstance(run_records, dict):
        raise RuntimeError("MAXCASE_AUDIT_RUN_RECORDS_MISSING")
    expected_runs = {
        "stage7": (37225915321, "e0b2fab6710833774937d778097363d7a8ee8e59", "success"),
        "stage10": (37709936740, "ca73f2df37baacebbcad965fc5f433f129675820", "failure"),
        "stage12": (37964656154, "0156c5f4272eb0ca7e32442657d0df9eaf4973d3", "success"),
        "cp_f_delivery_detail_replay": (38619859394, "f7096bcc9f910df54a60d5a4329a7ebbcd2a43ae", "success"),
    }
    for run_key, (expected_id, expected_head, expected_conclusion) in expected_runs.items():
        record = run_records.get(run_key)
        if (
            not isinstance(record, dict)
            or record.get("id") != expected_id
            or record.get("head_sha") != expected_head
            or record.get("conclusion") != expected_conclusion
            or record.get("status") != "completed"
        ):
            raise RuntimeError(f"MAXCASE_AUDIT_SOURCE_RUN_IDENTITY_MISMATCH: {run_key}")
    if run_records.get("stage10_aggregate_job_conclusion") != "failure":
        raise RuntimeError("MAXCASE_AUDIT_STAGE10_DISPOSITION_MISMATCH")
    if run_records.get("stage10_successful_benchmark_job_count") != 45:
        raise RuntimeError("MAXCASE_AUDIT_STAGE10_BENCHMARK_COVERAGE_MISMATCH")
    if (
        audit.get("repository") != "yasmin977209-ux/motorcycle-simulation"
        or payload_document.get("repository") != audit.get("repository")
        or audit.get("created_at_utc") != payload_document.get("created_at_utc")
        or audit.get("tested_head_sha") != payload_document.get("tested_head_sha")
        or audit.get("source_identity") != payload_document.get("source_identity")
    ):
        raise RuntimeError("MAXCASE_AUDIT_PAIR_IDENTITY_MISMATCH")
    stage12_run = payload_document.get("stage12_run")
    audit_stage12 = run_records.get("stage12")
    if (
        not isinstance(stage12_run, dict)
        or not isinstance(audit_stage12, dict)
        or stage12_run.get("id") != 37964656154
        or stage12_run.get("head_sha") != "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
        or stage12_run.get("conclusion") != "success"
        or stage12_run != audit_stage12
    ):
        raise RuntimeError("MAXCASE_AUDIT_STAGE12_SOURCE_IDENTITY_MISMATCH")
    if audit.get("source_identity") != MAXCASE_EXPECTED_SOURCE_IDENTITY:
        raise RuntimeError("MAXCASE_AUDIT_SOURCE_IDENTITY_MISMATCH")
    if payload_document.get("stage12_global_sha256") != MAXCASE_EXPECTED_STAGE12_GLOBAL_SHA256:
        raise RuntimeError("MAXCASE_STAGE12_GLOBAL_IDENTITY_MISMATCH")
    if manifest_git_blob_sha != MAXCASE_EXPECTED_SOURCE_IDENTITY["stage9a_manifest_git_blob"]:
        raise RuntimeError("MAXCASE_AUDIT_DATASET_IDENTITY_MISMATCH")
    if (
        audit.get("integrity_status") != "PASS_SCOPED"
        or audit.get("simulation_or_trial_executed") is not False
        or audit.get("historical_dataset_modified") is not False
        or audit.get("historical_artifacts_modified") is not False
        or audit.get("workbook_built") is not False
    ):
        raise RuntimeError("MAXCASE_AUDIT_SCOPE_OR_INTEGRITY_NOT_ACCEPTED")
    summary = audit.get("summary")
    stage12_validation = audit.get("stage12_daily_validation")
    if not isinstance(summary, dict) or not isinstance(stage12_validation, dict):
        raise RuntimeError("MAXCASE_AUDIT_SUMMARY_MISSING")
    if (
        summary.get("scenario_count") != len(EXPECTED_SCENARIOS)
        or summary.get("expected_trial_rows") != 11005
        or summary.get("actual_trial_rows") != 11005
        or summary.get("trial_rows_rehashed") != 11005
        or summary.get("maxcase_positive_selected") != len(EXPECTED_SCENARIOS)
        or summary.get("undefined_business_rule_scenarios") != []
        or stage12_validation.get("scenarios_validated") != len(EXPECTED_SCENARIOS)
        or stage12_validation.get("daily_rows_validated") != 22546465
        or stage12_validation.get("trial_result_fingerprint_mismatches") != 0
    ):
        raise RuntimeError("MAXCASE_AUDIT_COVERAGE_OR_RECONCILIATION_FAILURE")

    payload_scenarios = payload_document.get("scenarios")
    audit_scenarios = audit.get("scenarios")
    if not isinstance(payload_scenarios, list) or not isinstance(audit_scenarios, list):
        raise RuntimeError("MAXCASE_AUDIT_SCENARIO_LIST_INVALID")
    payload_by_scenario = {}
    audit_by_scenario = {}
    for item in payload_scenarios:
        if not isinstance(item, dict) or not isinstance(item.get("scenario"), str):
            raise RuntimeError("MAXCASE_PAYLOAD_SCENARIO_INVALID")
        scenario = item["scenario"]
        if scenario in payload_by_scenario:
            raise RuntimeError(f"MAXCASE_PAYLOAD_SCENARIO_DUPLICATE: {scenario}")
        payload_by_scenario[scenario] = item
    for item in audit_scenarios:
        if not isinstance(item, dict) or not isinstance(item.get("scenario"), str):
            raise RuntimeError("MAXCASE_AUDIT_SCENARIO_INVALID")
        scenario = item["scenario"]
        if scenario in audit_by_scenario:
            raise RuntimeError(f"MAXCASE_AUDIT_SCENARIO_DUPLICATE: {scenario}")
        audit_by_scenario[scenario] = item
    expected_scenarios = set(EXPECTED_SCENARIOS)
    if (
        set(payload_by_scenario) != expected_scenarios
        or set(audit_by_scenario) != expected_scenarios
        or payload_document.get("scenario_count") != len(EXPECTED_SCENARIOS)
    ):
        raise RuntimeError("MAXCASE_AUDIT_SCENARIO_COVERAGE_MISMATCH")

    total_daily_rows = 0
    for scenario in EXPECTED_SCENARIOS:
        payload_item = payload_by_scenario[scenario]
        audit_item = audit_by_scenario[scenario]
        trial_id = payload_item.get("trial_id")
        trial_sha = audit_item.get("maxcase_trial_result_sha256")
        daily_rows = payload_item.get("daily_rows")
        report_summary = audit_item.get("maxcase_summary")
        if (
            payload_item.get("case") != "Max Case"
            or type(trial_id) is not int
            or audit_item.get("maxcase_selection_status") != "PASS"
            or audit_item.get("maxcase_trial_id") != trial_id
            or not _is_sha256(trial_sha)
            or not isinstance(report_summary, dict)
            or not isinstance(daily_rows, list)
            or not daily_rows
        ):
            raise RuntimeError(f"MAXCASE_AUDIT_SCENARIO_IDENTITY_INVALID: {scenario}")
        audit_hash_rows = audit_item.get("trial_result_hashes")
        if not isinstance(audit_hash_rows, dict) or audit_hash_rows.get(str(trial_id)) != trial_sha:
            raise RuntimeError(f"MAXCASE_AUDIT_TRIAL_HASH_MAP_MISMATCH: {scenario}")
        for field in ("final_cash", "final_net_project_equity", "cumulative_project_profit"):
            if payload_item.get(field) != report_summary.get(field):
                raise RuntimeError(f"MAXCASE_AUDIT_SUMMARY_MISMATCH: {scenario}:{field}")
        source_status = payload_item.get("partner_memo_fields_status")
        if source_status == "VERIFIED_REUSED_SOURCE_ARTIFACT":
            selected_source = payload_item.get("selected_daily_payload_artifact")
            api_digest = selected_source.get("api_digest") if isinstance(selected_source, dict) else None
            artifact_api_digest = selected_source.get("artifact_api_digest") if isinstance(selected_source, dict) else None
            zip_digest = selected_source.get("artifact_zip_sha256") if isinstance(selected_source, dict) else None
            artifact_name = selected_source.get("artifact_name") if isinstance(selected_source, dict) else None
            if not isinstance(selected_source, dict):
                raise RuntimeError(f"MAXCASE_AUDIT_SOURCE_PROVENANCE_MISMATCH: {scenario}")
            common_source_valid = (
                type(selected_source.get("artifact_id")) is int
                and type(selected_source.get("run_id")) is int
                and isinstance(selected_source.get("run_head_sha"), str)
                and len(selected_source.get("run_head_sha")) == 40
                and selected_source.get("trial_id") == trial_id
                and selected_source.get("trial_result_sha256") == trial_sha
                and selected_source.get("daily_row_count") == len(daily_rows)
                and isinstance(api_digest, str)
                and api_digest.startswith("sha256:")
                and artifact_api_digest == api_digest
                and zip_digest == api_digest.removeprefix("sha256:")
            )
            if isinstance(artifact_name, str) and artifact_name.startswith("stage9a06-enriched-"):
                source_specific_valid = (
                    artifact_name == f"stage9a06-enriched-{scenario}"
                    and selected_source.get("manifest_authorized_source") is True
                    and selected_source.get("run_id") == 37655041728
                    and selected_source.get("run_head_sha") == "b4a88a117fa7d7fcdc7718d6a475699e3e8ac47e"
                    and selected_source.get("run_conclusion") == (
                        "failure (artifact validated individually; run-level success is not claimed)"
                    )
                    and _is_sha256(selected_source.get("metadata_sha256"))
                    and _is_sha256(selected_source.get("trial_fingerprints_sha256"))
                    and selected_source.get("partner_memo_fields_status") is None
                )
            elif isinstance(artifact_name, str) and artifact_name.startswith("cp-f-replay-"):
                source_specific_valid = (
                    artifact_name == f"cp-f-replay-{scenario}"
                    and selected_source.get("manifest_non_c100_gate_a_fingerprints_verified") is True
                    and selected_source.get("day_by_day_stage12_reconciliation") is True
                    and selected_source.get("historical_dataset_modified") is False
                    and selected_source.get("historical_parquet_modified") is False
                    and selected_source.get("production_monte_carlo_run") is False
                    and selected_source.get("partner_memo_fields_status") == "VERIFIED_REUSED_SOURCE_ARTIFACT"
                    and selected_source.get("run_conclusion") == "success"
                    and selected_source.get("run_id") == 38619859394
                    and selected_source.get("run_head_sha") == "f7096bcc9f910df54a60d5a4329a7ebbcd2a43ae"
                    and selected_source.get("run_branch") == "tmp/cp-f-delivery-20261014"
                    and _is_sha256(selected_source.get("scenario_manifest_sha256"))
                    and isinstance(selected_source.get("representative_payload_member"), str)
                    and selected_source.get("representative_payload_member") == "representatives/Max Case.json"
                    and type(selected_source.get("representative_payload_member_size_bytes")) is int
                    and selected_source.get("representative_payload_member_size_bytes") > 0
                )
            else:
                source_specific_valid = False
            if (
                audit_item.get("selected_daily_payload_source_verified") is not True
                or audit_item.get("existing_payload_reusable_exactly") is not True
                or not common_source_valid
                or not source_specific_valid
            ):
                raise RuntimeError(f"MAXCASE_AUDIT_SOURCE_PROVENANCE_MISMATCH: {scenario}")
        elif source_status == "MISSING_EVIDENCE":
            if audit_item.get("selected_daily_payload_source_verified") is True:
                raise RuntimeError(f"MAXCASE_AUDIT_PENDING_STATUS_CONFLICT: {scenario}")
        else:
            raise RuntimeError(f"MAXCASE_AUDIT_SOURCE_STATUS_INVALID: {scenario}")

        dates = []
        observed_hashes = set()
        for row in daily_rows:
            if (
                not isinstance(row, dict)
                or type(row.get("trial_id")) is not int
                or row.get("trial_id") != trial_id
                or row.get("source_sha") != MAXCASE_EXPECTED_SOURCE_IDENTITY["source_sha"]
                or type(row.get("master_seed")) is not int
                or row.get("master_seed") != MAXCASE_EXPECTED_SOURCE_IDENTITY["master_seed"]
                or not _is_sha256(row.get("result_sha256"))
                or row.get("result_sha256") != trial_sha
            ):
                raise RuntimeError(f"MAXCASE_DAILY_ROW_IDENTITY_MISMATCH: {scenario}")
            try:
                dates.append(date.fromisoformat(row["date"]))
            except (KeyError, TypeError, ValueError) as exc:
                raise RuntimeError(f"MAXCASE_DAILY_DATE_INVALID: {scenario}") from exc
            observed_hashes.add(row["result_sha256"])
            for field in ("Cash", "Net_Equity", "Cumulative_Project_Profit", "Active_Bikes", "Owned_Transferred_Bikes", "Pending_Claims"):
                if type(row.get(field)) is not int:
                    raise RuntimeError(f"MAXCASE_DAILY_REQUIRED_FIELD_INVALID: {scenario}:{field}")
            memo_values = [row.get(field) for field in MAXCASE_REQUIRED_MEMO_FIELDS]
            if source_status == "VERIFIED_REUSED_SOURCE_ARTIFACT":
                if any(type(value) is not int for value in memo_values):
                    raise RuntimeError(f"MAXCASE_VERIFIED_MEMO_FIELD_INVALID: {scenario}")
            elif memo_values != ["PENDING_DATA_SOURCE", "PENDING_DATA_SOURCE"]:
                raise RuntimeError(f"MAXCASE_PENDING_MEMO_FIELD_NOT_EXPLICIT: {scenario}")
        if (
            len(observed_hashes) != 1
            or not dates
            or any(current != previous + timedelta(days=1) for previous, current in zip(dates, dates[1:]))
            or dates[-1].isoformat() != report_summary.get("final_close_date")
        ):
            raise RuntimeError(f"MAXCASE_DAILY_SEQUENCE_OR_TERMINAL_MISMATCH: {scenario}")
        total_daily_rows += len(daily_rows)

    if (
        total_daily_rows != payload_document.get("maxcase_daily_rows")
        or total_daily_rows != summary.get("maxcase_daily_rows_extracted")
    ):
        raise RuntimeError("MAXCASE_AUDIT_DAILY_ROW_COUNT_MISMATCH")
    provenance = audit.get("representative_inventory_provenance")
    mismatch_rows = provenance.get("mismatches") if isinstance(provenance, dict) else None
    summary_mismatch_scenarios = summary.get("representative_inventory_provenance_mismatch_scenarios")
    if (
        not isinstance(provenance, dict)
        or type(provenance.get("mismatch_count")) is not int
        or not isinstance(mismatch_rows, list)
        or provenance.get("mismatch_count") != len(mismatch_rows)
        or provenance.get("mismatch_count") != summary.get("representative_inventory_provenance_mismatch_count")
        or not isinstance(summary_mismatch_scenarios, list)
        or [item.get("scenario") for item in mismatch_rows if isinstance(item, dict)] != summary_mismatch_scenarios
        or len([item for item in mismatch_rows if isinstance(item, dict)]) != len(mismatch_rows)
        or provenance.get("status") not in {"PASS", "CONFLICTED"}
    ):
        raise RuntimeError("MAXCASE_AUDIT_PROVENANCE_STATUS_MISSING")
    return {
        "payloads_by_scenario": payload_by_scenario,
        "audit_by_scenario": audit_by_scenario,
        "metadata": {
            "audit_sha256": actual_audit_sha,
            "payloads_sha256": actual_payloads_sha,
            "tested_head_sha": audit.get("tested_head_sha"),
            "integrity_status": audit.get("integrity_status"),
            "payload_status": audit.get("payload_status"),
            "representative_inventory_mismatch_count": provenance["mismatch_count"],
            "representative_inventory_mismatch_scenarios": summary.get("representative_inventory_provenance_mismatch_scenarios", []),
            "missing_memo_scenarios": summary.get("non_c100_maxcase_payloads_missing_partner_memo_source", []),
            "source_identity": audit.get("source_identity"),
        },
    }




def _strict_type_equal(actual: Any, expected: Any) -> bool:
    return type(actual) is type(expected) and actual == expected


def _read_maxcase_replay_bundle(
    replay_path: str | Path,
    *,
    replay_sha256: str | None,
    manifest: dict[str, Any],
    manifest_git_blob_sha: str,
    audit_bundle: dict[str, Any] | None,
) -> dict[str, Any]:
    """Read the pinned R4 replay artifact, bound to the paired original audit.

    This is a distinct provenance type from a Stage 9A/CP-F role archive. It can
    replace only the ten audited PENDING_DATA_SOURCE memo-balance rows. It never
    establishes final-delivery acceptance.
    """
    if audit_bundle is None:
        raise RuntimeError("MAXCASE_REPLAY_REQUIRES_PINNED_SOURCE_AUDIT_BUNDLE")
    _validate_active_stage9a_manifest(
        manifest, manifest_git_blob_sha=manifest_git_blob_sha,
    )
    if audit_bundle.get("metadata", {}).get("source_identity") != MAXCASE_EXPECTED_SOURCE_IDENTITY:
        raise RuntimeError("MAXCASE_REPLAY_CURRENT_AUDIT_IDENTITY_MISMATCH")
    if not _is_sha256(replay_sha256):
        raise RuntimeError("MAXCASE_REPLAY_SHA256_REQUIRED")
    raw = Path(replay_path).read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != replay_sha256:
        raise RuntimeError(
            f"MAXCASE_REPLAY_DIGEST_MISMATCH: expected={replay_sha256} actual={actual_sha}"
        )
    if actual_sha != MAXCASE_REPLAY_EXPECTED_JSON_SHA256:
        raise RuntimeError("MAXCASE_REPLAY_JSON_NOT_THE_APPROVED_EXACT_ARTIFACT")
    try:
        recovery = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("MAXCASE_REPLAY_JSON_INVALID") from exc
    if not isinstance(recovery, dict):
        raise RuntimeError("MAXCASE_REPLAY_ROOT_INVALID")
    if (
        recovery.get("schema_version") != MAXCASE_REPLAY_SCHEMA
        or recovery.get("status") != "PASS"
        or recovery.get("repository") != "yasmin977209-ux/motorcycle-simulation"
        or recovery.get("pinned_source_commit") != MAXCASE_EXPECTED_SOURCE_IDENTITY["source_sha"]
        or recovery.get("source_identity") != MAXCASE_REPLAY_EXPECTED_SOURCE_IDENTITY
        or recovery.get("owner_authorization") != "EXPLICIT_USER_DELEGATION_2026-10-24_FOR_BOUNDED_EXACT_TRIAL_REPLAY"
    ):
        raise RuntimeError("MAXCASE_REPLAY_SCHEMA_OR_SOURCE_IDENTITY_MISMATCH")
    if recovery.get("pinned_engine_git_blobs") != MAXCASE_REPLAY_EXPECTED_ENGINE_BLOBS:
        raise RuntimeError("MAXCASE_REPLAY_ENGINE_BLOBS_MISMATCH")
    expected_inputs = {
        "audit_artifact_id": 12537818827,
        "audit_run_id": 40038112945,
        "audit_artifact_zip_sha256": MAXCASE_REPLAY_SOURCE_AUDIT_ZIP_SHA256,
        "audit_json_sha256": MAXCASE_REPLAY_SOURCE_AUDIT_JSON_SHA256,
        "payloads_json_sha256": MAXCASE_REPLAY_SOURCE_PAYLOADS_JSON_SHA256,
        "stage12_global_sha256": MAXCASE_EXPECTED_STAGE12_GLOBAL_SHA256,
        "stage12_daily_rows_validated_before_replay": 22546465,
        "stage12_trial_fingerprint_mismatches_before_replay": 0,
        "source_audit_tested_head_sha": "c00b48912e10cc0334dfb0d7bb3c3741eb002315",
        "source_audit_integrity_status": "PASS_SCOPED",
        "source_audit_payload_status_before_replay": "MISSING_EVIDENCE",
    }
    if recovery.get("input_artifacts") != expected_inputs:
        raise RuntimeError("MAXCASE_REPLAY_SOURCE_AUDIT_PROVENANCE_MISMATCH")
    expected_execution = {
        "selected_trials_expected": len(MAXCASE_REPLAY_PLAN),
        "selected_trials_replayed": len(MAXCASE_REPLAY_PLAN),
        "successful_trials": len(MAXCASE_REPLAY_PLAN),
        "new_trial_ids_created": False,
        "canonical_stage12_files_modified": False,
        "source_artifacts_modified": False,
        "random_seed_or_rng_changed": False,
        "production_workbook_built": False,
        "monte_carlo_expansion_run": False,
        "checkpoint_run": False,
    }
    if recovery.get("execution") != expected_execution:
        raise RuntimeError("MAXCASE_REPLAY_EXECUTION_DISPOSITION_MISMATCH")
    replay_source_identity = recovery.get("source_identity")
    active_source_identity = audit_bundle.get("metadata", {}).get("source_identity")
    common_identity_fields = set(MAXCASE_EXPECTED_SOURCE_IDENTITY) - {"stage9a_manifest_git_blob"}
    if (
        replay_source_identity != MAXCASE_REPLAY_EXPECTED_SOURCE_IDENTITY
        or not isinstance(active_source_identity, dict)
        or active_source_identity != MAXCASE_EXPECTED_SOURCE_IDENTITY
        or any(replay_source_identity.get(key) != active_source_identity.get(key) for key in common_identity_fields)
        or replay_source_identity.get("stage9a_manifest_git_blob") != "e796fa2443493b607f1f9c60b58eb63607959c26"
        or active_source_identity.get("stage9a_manifest_git_blob") != manifest_git_blob_sha
        or manifest_git_blob_sha != MAXCASE_EXPECTED_SOURCE_IDENTITY["stage9a_manifest_git_blob"]
    ):
        raise RuntimeError("MAXCASE_REPLAY_DATASET_IDENTITY_MISMATCH")
    summary = recovery.get("summary")
    results = recovery.get("scenarios")
    if not isinstance(summary, dict) or not isinstance(results, list):
        raise RuntimeError("MAXCASE_REPLAY_SUMMARY_OR_SCENARIOS_MISSING")
    expected_names = set(MAXCASE_REPLAY_PLAN)
    if (
        summary.get("expected_scenarios") != len(MAXCASE_REPLAY_PLAN)
        or set(summary.get("passed_scenarios", [])) != expected_names
        or summary.get("failed_scenarios") != []
        or summary.get("recovered_daily_rows") != MAXCASE_REPLAY_RECOVERED_ROWS
        or summary.get("source_trial_hash_mismatches") != 0
        or summary.get("stage12_common_field_mismatches") != 0
        or len(results) != len(MAXCASE_REPLAY_PLAN)
    ):
        raise RuntimeError("MAXCASE_REPLAY_COVERAGE_OR_RESULT_STATUS_MISMATCH")
    replay_by_scenario = {}
    for item in results:
        if not isinstance(item, dict) or not isinstance(item.get("scenario"), str):
            raise RuntimeError("MAXCASE_REPLAY_SCENARIO_INVALID")
        scenario = item["scenario"]
        if scenario in replay_by_scenario:
            raise RuntimeError(f"MAXCASE_REPLAY_DUPLICATE_SCENARIO: {scenario}")
        replay_by_scenario[scenario] = item
    if set(replay_by_scenario) != expected_names:
        raise RuntimeError("MAXCASE_REPLAY_SCENARIO_COVERAGE_MISMATCH")

    source_meta = audit_bundle.get("metadata", {})
    source_audit_by_scenario = audit_bundle.get("audit_by_scenario", {})
    source_payloads_by_scenario = audit_bundle.get("payloads_by_scenario", {})
    if set(source_meta.get("missing_memo_scenarios", [])) != expected_names:
        raise RuntimeError("MAXCASE_REPLAY_DOES_NOT_MATCH_SOURCE_AUDIT_MISSING_SCENARIOS")
    replay_by_scenario_validated = {}
    total_rows = 0
    for scenario, plan in MAXCASE_REPLAY_PLAN.items():
        item = replay_by_scenario[scenario]
        audit_item = source_audit_by_scenario.get(scenario)
        source_payload = source_payloads_by_scenario.get(scenario)
        if not isinstance(audit_item, dict) or not isinstance(source_payload, dict):
            raise RuntimeError(f"MAXCASE_REPLAY_SOURCE_SCENARIO_MISSING: {scenario}")
        trial_id = plan["trial_id"]
        trial_sha = plan["trial_result_sha256"]
        rows = item.get("daily_rows")
        if (
            item.get("status") != "PASS_EXACT_REPLAY_AND_STAGE12_COMMON_FIELDS"
            or item.get("trial_id") != trial_id
            or item.get("trial_result_sha256") != trial_sha
            or item.get("daily_row_count") != plan["daily_rows"]
            or not isinstance(rows, list)
            or len(rows) != plan["daily_rows"]
            or item.get("comparison_contract", {}).get("stage12_trial_result_hash_equal") is not True
            or item.get("comparison_contract", {}).get("all_daily_common_fields_equal") is not True
            or item.get("comparison_contract", {}).get("dates_consecutive") is not True
            or item.get("comparison_contract", {}).get("memo_balances_integer_nonnegative") is not True
        ):
            raise RuntimeError(f"MAXCASE_REPLAY_SCENARIO_CONTRACT_MISMATCH: {scenario}")
        audit_hashes = audit_item.get("trial_result_hashes")
        if (
            audit_item.get("maxcase_selection_status") != "PASS"
            or audit_item.get("maxcase_trial_id") != trial_id
            or audit_item.get("maxcase_trial_result_sha256") != trial_sha
            or not isinstance(audit_hashes, dict)
            or audit_hashes.get(str(trial_id)) != trial_sha
            or source_payload.get("trial_id") != trial_id
            or source_payload.get("partner_memo_fields_status") != "MISSING_EVIDENCE"
            or not isinstance(source_payload.get("daily_rows"), list)
            or len(source_payload["daily_rows"]) != len(rows)
        ):
            raise RuntimeError(f"MAXCASE_REPLAY_SELECTED_TRIAL_PROVENANCE_MISMATCH: {scenario}")
        audited_summary = audit_item.get("maxcase_summary")
        recovered_summary = item.get("summary")
        if not isinstance(audited_summary, dict) or not isinstance(recovered_summary, dict):
            raise RuntimeError(f"MAXCASE_REPLAY_SUMMARY_MISSING: {scenario}")
        for field, value in recovered_summary.items():
            if not _strict_type_equal(value, audited_summary.get(field)):
                raise RuntimeError(f"MAXCASE_REPLAY_TRIAL_SUMMARY_MISMATCH: {scenario}:{field}")

        dates = []
        source_rows = source_payload["daily_rows"]
        for index, (row, source_row) in enumerate(zip(rows, source_rows)):
            if not isinstance(row, dict) or not isinstance(source_row, dict):
                raise RuntimeError(f"MAXCASE_REPLAY_DAILY_ROW_INVALID: {scenario}:{index}")
            if (
                type(row.get("trial_id")) is not int
                or row.get("trial_id") != trial_id
                or row.get("source_sha") != MAXCASE_EXPECTED_SOURCE_IDENTITY["source_sha"]
                or type(row.get("master_seed")) is not int
                or row.get("master_seed") != MAXCASE_EXPECTED_SOURCE_IDENTITY["master_seed"]
                or row.get("result_sha256") != trial_sha
            ):
                raise RuntimeError(f"MAXCASE_REPLAY_DAILY_ROW_IDENTITY_MISMATCH: {scenario}:{index}")
            for field in MAXCASE_REPLAY_COMMON_DAILY_FIELDS:
                if not _strict_type_equal(row.get(field), source_row.get(field)):
                    raise RuntimeError(f"MAXCASE_REPLAY_STAGE12_COMMON_FIELD_MISMATCH: {scenario}:{index}:{field}")
            if (
                source_row.get("Partner1_Reinvestment_Balance") != "PENDING_DATA_SOURCE"
                or source_row.get("Partner2_Reinvestment_Balance") != "PENDING_DATA_SOURCE"
                or type(row.get("Partner1_Reinvestment_Balance")) is not int
                or row.get("Partner1_Reinvestment_Balance") < 0
                or type(row.get("Partner2_Reinvestment_Balance")) is not int
                or row.get("Partner2_Reinvestment_Balance") < 0
            ):
                raise RuntimeError(f"MAXCASE_REPLAY_MEMO_FIELD_INVALID: {scenario}:{index}")
            try:
                dates.append(date.fromisoformat(row["date"]))
            except (KeyError, TypeError, ValueError) as exc:
                raise RuntimeError(f"MAXCASE_REPLAY_DATE_INVALID: {scenario}:{index}") from exc
        if (
            not dates
            or any(current != previous + timedelta(days=1) for previous, current in zip(dates, dates[1:]))
            or dates[0].isoformat() != item.get("first_date")
            or dates[-1].isoformat() != item.get("final_close_date")
            or dates[-1].isoformat() != recovered_summary.get("final_close_date")
            or any(row.get("Final_Close_Date") != dates[-1].isoformat() for row in rows)
        ):
            raise RuntimeError(f"MAXCASE_REPLAY_DATE_OR_TERMINAL_MISMATCH: {scenario}")
        replay_by_scenario_validated[scenario] = item
        total_rows += len(rows)
    if total_rows != MAXCASE_REPLAY_RECOVERED_ROWS:
        raise RuntimeError("MAXCASE_REPLAY_TOTAL_DAILY_ROW_COUNT_MISMATCH")
    return {
        "payloads_by_scenario": replay_by_scenario_validated,
        "metadata": {
            "replay_recovery_status": "PASS_EXACT_REPLAY",
            "replay_json_sha256": actual_sha,
            "replay_artifact_id": MAXCASE_REPLAY_EXPECTED_ARTIFACT["artifact_id"],
            "replay_artifact_run_id": MAXCASE_REPLAY_EXPECTED_ARTIFACT["artifact_run_id"],
            "replay_artifact_zip_sha256": MAXCASE_REPLAY_EXPECTED_ARTIFACT["artifact_zip_sha256"],
            "replay_run_head_sha": MAXCASE_REPLAY_EXPECTED_ARTIFACT["tested_head_sha"],
            "replay_engine_identity_matches_source_sha": True,
            "replay_recovered_scenarios": list(MAXCASE_REPLAY_PLAN),
            "replay_recovered_daily_rows": total_rows,
            "replay_covers_all_missing_memo_scenarios": True,
            "replay_selected_trial_sha256_mismatches": 0,
            "replay_stage12_common_field_mismatches": 0,
        },
    }


def _maxcase_role_from_replay(scenario, trial_rows, replay_item, audit_item):
    """Translate an exact-Trial replay record into the Stage 13 representative contract."""
    trial_id = replay_item["trial_id"]
    selected = select_representative_trial_ids(trial_rows, scenario)["Max Case"]
    if selected != trial_id:
        raise RuntimeError(
            f"MAXCASE_REPLAY_SELECTED_TRIAL_MISMATCH: {scenario} expected={selected} replay={trial_id}"
        )
    rows_by_id = {}
    for row in trial_rows:
        raw_trial_id = row.get("trial_id")
        if type(raw_trial_id) is not int:
            raise RuntimeError(f"MAXCASE_REPLAY_SOURCE_TRIAL_ID_INVALID: {scenario}")
        rows_by_id[raw_trial_id] = row
    summary = rows_by_id.get(trial_id)
    if summary is None:
        raise RuntimeError(f"MAXCASE_REPLAY_SELECTED_TRIAL_MISSING: {scenario}:{trial_id}")
    replay_summary = replay_item.get("summary")
    if not isinstance(replay_summary, dict):
        raise RuntimeError(f"MAXCASE_REPLAY_TRIAL_SUMMARY_MISSING: {scenario}")
    for field, expected_value in summary.items():
        if not _strict_type_equal(replay_summary.get(field), expected_value):
            raise RuntimeError(f"MAXCASE_REPLAY_TRIAL_RESULT_MISMATCH: {scenario}:{field}")
    if (
        audit_item.get("maxcase_trial_id") != trial_id
        or audit_item.get("maxcase_trial_result_sha256") != replay_item.get("trial_result_sha256")
    ):
        raise RuntimeError(f"MAXCASE_REPLAY_AUDIT_BINDING_MISMATCH: {scenario}")
    return {
        "summary": dict(summary),
        "daily": [dict(row) for row in replay_item["daily_rows"]],
    }




def _maxcase_role_from_audit(scenario, trial_rows, payload_item, audit_item):
    """Translate one verified audit selection into the Stage 13 representative contract."""
    trial_id = payload_item["trial_id"]
    selected = select_representative_trial_ids(trial_rows, scenario)["Max Case"]
    if selected != trial_id:
        raise RuntimeError(
            f"MAXCASE_SELECTED_TRIAL_MISMATCH: {scenario} expected={selected} audit={trial_id}"
        )
    rows_by_id = {int(row["trial_id"]): row for row in trial_rows}
    summary = rows_by_id.get(trial_id)
    if summary is None:
        raise RuntimeError(f"MAXCASE_SELECTED_TRIAL_MISSING: {scenario}:{trial_id}")
    report_summary = audit_item.get("maxcase_summary", {})
    for field in ("final_cash", "final_net_project_equity", "cumulative_project_profit", "final_close_date"):
        if summary.get(field) != report_summary.get(field):
            raise RuntimeError(f"MAXCASE_SUMMARY_IDENTITY_MISMATCH: {scenario}:{field}")
    return {
        "summary": dict(summary),
        "daily": [dict(row) for row in payload_item["daily_rows"]],
    }



def load_rep_payload(dataset_root: Path, scenario: str, label: str) -> dict[str, Any]:
    """Read a named representative JSON, including from the scenario archive."""
    direct = dataset_root / scenario / "representatives" / f"{label}.json"
    if direct.is_file():
        return load_json(direct)
    tar_path = dataset_root / scenario / f"{scenario}.tar.gz"
    if not tar_path.is_file():
        raise FileNotFoundError(f"MISSING_REPRESENTATIVE_PAYLOAD: {scenario}/{label}")
    target = f"representatives/{label}.json"
    with tarfile.open(tar_path, "r:gz") as archive:
        member = next(
            (item for item in archive.getmembers() if item.name.lstrip("./") == target),
            None,
        )
        if member is None:
            raise FileNotFoundError(f"MISSING_REPRESENTATIVE_PAYLOAD: {scenario}/{label}")
        stream = archive.extractfile(member)
        if stream is None:
            raise RuntimeError(f"UNREADABLE_REPRESENTATIVE_PAYLOAD: {scenario}/{label}")
        return json.load(stream)


def load_scenario_trials(dataset_root: Path, scenario: str):
    """Legacy loader retained for callers that expect lists of Parquet rows."""
    path = Path(dataset_root) / scenario / "trial_results.parquet"
    if not path.is_file():
        raise FileNotFoundError(path)
    return pq.read_table(path).to_pylist()


def load_scenario_daily_distribution(dataset_root: Path, scenario: str):
    """Legacy daily-distribution loader retained for existing callers."""
    path = Path(dataset_root) / scenario / "daily_distribution.parquet"
    if not path.is_file():
        raise FileNotFoundError(path)
    return pq.read_table(path).to_pylist()


def representative_rows(rep_path: Path, scenario: str):
    """Legacy representative trial-id reader retained for external scripts."""
    rep = load_json(Path(rep_path))["scenarios"][scenario]
    return {
        label: int(trial_id)
        for label, trial_id in rep.items()
        if label in {"P10", "P50", "P90", "Loss"}
    }


def _root_layout(
    dataset_path: str | Path,
    manifest_path: str | Path | None = None,
):
    given = Path(dataset_path)
    if not given.exists() or not given.is_dir():
        raise FileNotFoundError(f"DATASET_PATH_NOT_FOUND: {given}")
    if manifest_path is not None:
        manifest_file = Path(manifest_path)
        artifact_root, dataset_root = manifest_file.parent, given
    elif (given / "dataset").is_dir() and (given / "manifest.json").is_file():
        artifact_root, dataset_root = given, given / "dataset"
        manifest_file = given / "manifest.json"
    else:
        artifact_root = dataset_root = given
        manifest_file = given / "manifest.json"
    if not manifest_file.is_file():
        raise FileNotFoundError(f"DATASET_MANIFEST_MISSING: {manifest_file}")
    return artifact_root, dataset_root, manifest_file


def load_dataset(
    dataset_path: str | Path,
    mode: str = "canonical",
    *,
    manifest_path: str | Path | None = None,
    representatives_path: str | Path | None = None,
    maxcase_audit_path: str | Path | None = None,
    maxcase_payloads_path: str | Path | None = None,
    maxcase_audit_sha256: str | None = None,
    maxcase_payloads_sha256: str | None = None,
    maxcase_replay_path: str | Path | None = None,
    maxcase_replay_sha256: str | None = None,
) -> dict[str, Any]:
    """Load immutable Parquet/JSON data; worksheet writing is delegated to Stage 13."""
    artifact_root, dataset_root, manifest_file = _root_layout(dataset_path, manifest_path)
    manifest = load_json(manifest_file)
    manifest_git_blob_sha = _git_blob_sha(Path(manifest_file).read_bytes())
    audit_args = (
        maxcase_audit_path, maxcase_payloads_path,
        maxcase_audit_sha256, maxcase_payloads_sha256,
    )
    if any(value is not None for value in audit_args) and not all(value is not None for value in audit_args):
        raise RuntimeError(
            "MAXCASE_AUDIT_INPUTS_REQUIRE_BOTH_FILES_AND_BOTH_SHA256_DIGESTS"
        )
    maxcase_audit_bundle = (
        _read_maxcase_audit_bundle(
            maxcase_audit_path, maxcase_payloads_path,
            audit_sha256=maxcase_audit_sha256,
            payloads_sha256=maxcase_payloads_sha256,
            manifest=manifest,
            manifest_git_blob_sha=manifest_git_blob_sha,
        )
        if maxcase_audit_path is not None
        else None
    )

    if (maxcase_replay_path is not None and maxcase_replay_sha256 is None) or (
        maxcase_replay_path is None and maxcase_replay_sha256 is not None
    ):
        raise RuntimeError("MAXCASE_REPLAY_INPUT_REQUIRES_PATH_AND_SHA256")
    maxcase_replay_bundle = (
        _read_maxcase_replay_bundle(
            maxcase_replay_path,
            replay_sha256=maxcase_replay_sha256,
            manifest=manifest,
            manifest_git_blob_sha=manifest_git_blob_sha,
            audit_bundle=maxcase_audit_bundle,
        )
        if maxcase_replay_path is not None
        else None
    )

    if representatives_path is not None:
        reps_file = Path(representatives_path)
    else:
        reps_file = next(
            (
                p for p in (
                    artifact_root / "representative_trial_ids.json",
                    dataset_root / "representative_trial_ids.json",
                )
                if p.is_file()
            ),
            None,
        )
    assignments = load_json(reps_file).get("scenarios", {}) if reps_file else {}
    validation_file = next(
        (
            p for p in (
                artifact_root / "validation_163.json",
                dataset_root / "validation_163.json",
            )
            if p.is_file()
        ),
        None,
    )
    validation = (
        load_json(validation_file)
        if validation_file
        else {"status": "not-provided", "tests": []}
    )
    error_file = dataset_root / "error_log.json"
    errors = load_json(error_file) if error_file.is_file() else []

    trials, distributions, representatives = {}, {}, {}
    replay_scenarios_used = []
    for scenario in EXPECTED_SCENARIOS:
        folder = dataset_root / scenario
        trial_file = folder / "trial_results.parquet"
        daily_file = folder / "daily_distribution.parquet"

        if trial_file.is_file():
            trials[scenario] = pq.read_table(trial_file).to_pylist()
        elif mode == "demo":
            trials[scenario] = []
        else:
            raise FileNotFoundError(f"SCENARIO_TRIAL_RESULTS_MISSING: {scenario}")

        if daily_file.is_file():
            distributions[scenario] = pq.read_table(daily_file).to_pylist()
        elif mode == "demo":
            distributions[scenario] = []
        else:
            raise FileNotFoundError(f"SCENARIO_DAILY_DISTRIBUTION_MISSING: {scenario}")

        reps = {}
        for filename, key in (
            ("P10", "P10"),
            ("P50", "P50"),
            ("P90", "P90"),
            ("Loss", "Loss"),
            ("Max Case", "Max Case"),
        ):
            try:
                reps[key] = load_rep_payload(dataset_root, scenario, filename)
            except FileNotFoundError:
                if (
                    key == "Max Case"
                    and maxcase_replay_bundle is not None
                    and scenario in maxcase_replay_bundle["payloads_by_scenario"]
                    and trials[scenario]
                ):
                    audit_item = maxcase_audit_bundle["audit_by_scenario"][scenario]
                    reps[key] = _maxcase_role_from_replay(
                        scenario, trials[scenario],
                        maxcase_replay_bundle["payloads_by_scenario"][scenario],
                        audit_item,
                    )
                    replay_scenarios_used.append(scenario)
                elif key == "Max Case" and maxcase_audit_bundle is not None and trials[scenario]:
                    payload_item = maxcase_audit_bundle["payloads_by_scenario"][scenario]
                    audit_item = maxcase_audit_bundle["audit_by_scenario"][scenario]
                    reps[key] = _maxcase_role_from_audit(
                        scenario, trials[scenario], payload_item, audit_item
                    )
                elif mode != "demo" and trials[scenario]:
                    raise
        # The replay artifact is the explicit source of record for its ten scenarios,
        # replacing any stale/incomplete role payload under the same selected Trial ID.
        if (
            "Max Case" in reps
            and maxcase_replay_bundle is not None
            and scenario in maxcase_replay_bundle["payloads_by_scenario"]
            and trials[scenario]
            and scenario not in replay_scenarios_used
        ):
            audit_item = maxcase_audit_bundle["audit_by_scenario"][scenario]
            reps["Max Case"] = _maxcase_role_from_replay(
                scenario, trials[scenario],
                maxcase_replay_bundle["payloads_by_scenario"][scenario],
                audit_item,
            )
            replay_scenarios_used.append(scenario)
        representatives[scenario] = reps
        if scenario not in assignments and reps:
            assignments[scenario] = {
                key: int(reps[key]["summary"]["trial_id"])
                for key in ("P10", "P50", "P90", "Loss", "Max Case")
                if key in reps
            }
        elif scenario in assignments and "Max Case" in reps:
            current = assignments[scenario]
            current_id = current.get("Max Case", current.get("MaxCase"))
            audit_id = int(reps["Max Case"]["summary"]["trial_id"])
            if current_id is not None and current_id != audit_id:
                raise RuntimeError(f"MAXCASE_ASSIGNMENT_TRIAL_MISMATCH: {scenario}")
            current["Max Case"] = audit_id

    return {
        "manifest": manifest,
        "trials_by_scenario": trials,
        "daily_distributions_by_scenario": distributions,
        "representatives_by_scenario": representatives,
        "representative_trial_ids": assignments,
        "validation": validation,
        "errors": errors,
        "dataset_root": str(dataset_root),
        "maxcase_audit_status": (
            {
                **maxcase_audit_bundle["metadata"],
                **(maxcase_replay_bundle["metadata"] if maxcase_replay_bundle else {}),
                "replay_scenarios_used_by_loader": list(replay_scenarios_used),
            }
            if maxcase_audit_bundle else None
        ),
    }


def build_excel(dataset_path, output_path, mode="canonical"):
    """Legacy public API for the approved orchestrator/assembler split."""
    data = load_dataset(dataset_path, mode=mode)
    return assemble_workbook(data, output_path, mode=mode)


def build_excel_with_maxcase_audit(
    dataset_path, output_path, mode="canonical", *,
    maxcase_audit_path=None, maxcase_payloads_path=None,
    maxcase_audit_sha256=None, maxcase_payloads_sha256=None,
    maxcase_replay_path=None, maxcase_replay_sha256=None,
):
    """Build a diagnostic artifact using digest-pinned audit and exact-replay inputs."""
    data = load_dataset(
        dataset_path, mode=mode,
        maxcase_audit_path=maxcase_audit_path,
        maxcase_payloads_path=maxcase_payloads_path,
        maxcase_audit_sha256=maxcase_audit_sha256,
        maxcase_payloads_sha256=maxcase_payloads_sha256,
        maxcase_replay_path=maxcase_replay_path,
        maxcase_replay_sha256=maxcase_replay_sha256,
    )
    return assemble_workbook(data, output_path, mode=mode)


def resolve_build_mode(manifest, mode=None):
    """Resolve a declared cohort explicitly; an unknown cohort never becomes demo."""
    supported = {"canonical", "sample", "demo", "adaptive"}
    if mode is not None:
        if mode not in supported:
            raise ValueError(f"UNSUPPORTED_EXCEL_MODE: {mode}")
        return mode
    if manifest.get("cohort_id") == "STAGE13_ADAPTIVE_STABLE_PER_SCENARIO_V1":
        return "adaptive"
    count = manifest.get("total_trials")
    if count == 11005:
        return "canonical"
    if count == 625:
        return "sample"
    raise ValueError(
        "UNRECOGNIZED_COHORT_MODE: specify mode='demo' for fixtures or provide an approved cohort contract"
    )


def _build_workbook_core(
    dataset_root,
    output_path,
    manifest_path,
    representatives_path,
    mode=None,
    *,
    maxcase_audit_path=None,
    maxcase_payloads_path=None,
    maxcase_audit_sha256=None,
    maxcase_payloads_sha256=None,
    maxcase_replay_path=None,
    maxcase_replay_sha256=None,
):
    """Shared implementation for legacy and digest-pinned MaxCase entrypoints."""
    manifest = load_json(Path(manifest_path))
    resolved_mode = resolve_build_mode(manifest, mode)
    data = load_dataset(
        dataset_root,
        mode=resolved_mode,
        manifest_path=manifest_path,
        representatives_path=representatives_path,
        maxcase_audit_path=maxcase_audit_path,
        maxcase_payloads_path=maxcase_payloads_path,
        maxcase_audit_sha256=maxcase_audit_sha256,
        maxcase_payloads_sha256=maxcase_payloads_sha256,
        maxcase_replay_path=maxcase_replay_path,
        maxcase_replay_sha256=maxcase_replay_sha256,
    )
    return assemble_workbook(data, output_path, mode=resolved_mode)


def build_workbook(dataset_root, output_path, manifest_path, representatives_path, mode=None):
    """Legacy signature retained for existing callers."""
    return _build_workbook_core(
        dataset_root, output_path, manifest_path, representatives_path, mode=mode,
    )


def build_workbook_with_maxcase_audit(
    dataset_root, output_path, manifest_path, representatives_path, mode=None, *,
    maxcase_audit_path=None, maxcase_payloads_path=None,
    maxcase_audit_sha256=None, maxcase_payloads_sha256=None,
    maxcase_replay_path=None, maxcase_replay_sha256=None,
):
    """Use verified audit/replay inputs without changing the legacy signature."""
    return _build_workbook_core(
        dataset_root, output_path, manifest_path, representatives_path, mode=mode,
        maxcase_audit_path=maxcase_audit_path,
        maxcase_payloads_path=maxcase_payloads_path,
        maxcase_audit_sha256=maxcase_audit_sha256,
        maxcase_payloads_sha256=maxcase_payloads_sha256,
        maxcase_replay_path=maxcase_replay_path,
        maxcase_replay_sha256=maxcase_replay_sha256,
    )


def write_daily_distribution(wb, dataset_root):
    """Legacy worksheet helper signature; delegate its data to the Stage 13 writer."""
    daily_by_scenario = {}
    for scenario in EXPECTED_SCENARIOS:
        try:
            daily_by_scenario[scenario] = load_scenario_daily_distribution(
                Path(dataset_root), scenario
            )
        except FileNotFoundError:
            daily_by_scenario[scenario] = []
    return _write_daily_distribution(wb, daily_by_scenario)


def write_representatives(wb, manifest, rep_path):
    """Legacy worksheet helper signature; read named payloads then delegate assembly."""
    dataset_root = Path(manifest.get("_dataset_root", Path(rep_path).parent))
    representatives_by_scenario = {}
    role_files = (
        ("P10", "P10"),
        ("P50", "P50"),
        ("P90", "P90"),
        ("Loss", "Loss"),
        ("Max Case", "Max Case"),
    )
    for scenario in EXPECTED_SCENARIOS:
        reps = {}
        for role, filename in role_files:
            try:
                reps[role] = load_rep_payload(dataset_root, scenario, filename)
            except FileNotFoundError:
                continue
        representatives_by_scenario[scenario] = reps
    return _write_representatives(wb, representatives_by_scenario)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-path")
    parser.add_argument("--dataset-root")
    parser.add_argument("--output-path", required=True)
    parser.add_argument(
        "--mode",
        choices=("canonical", "sample", "demo", "adaptive"),
        default=None,
    )
    parser.add_argument("--manifest")
    parser.add_argument("--representatives")
    parser.add_argument("--maxcase-audit")
    parser.add_argument("--maxcase-payloads")
    parser.add_argument("--maxcase-audit-sha256")
    parser.add_argument("--maxcase-payloads-sha256")
    parser.add_argument("--maxcase-replay")
    parser.add_argument("--maxcase-replay-sha256")
    parser.add_argument("--require-final-acceptance", action="store_true")
    args = parser.parse_args()
    dataset = args.dataset_path or args.dataset_root
    if not dataset:
        parser.error("--dataset-path is required (or use legacy --dataset-root)")
    has_maxcase_audit = any((
        args.maxcase_audit, args.maxcase_payloads,
        args.maxcase_audit_sha256, args.maxcase_payloads_sha256,
        args.maxcase_replay, args.maxcase_replay_sha256,
    ))
    if args.manifest or args.representatives or args.dataset_root:
        build_fn = build_workbook_with_maxcase_audit if has_maxcase_audit else build_workbook
        build_kwargs = {}
        if has_maxcase_audit:
            build_kwargs = {
                "maxcase_audit_path": args.maxcase_audit,
                "maxcase_payloads_path": args.maxcase_payloads,
                "maxcase_audit_sha256": args.maxcase_audit_sha256,
                "maxcase_payloads_sha256": args.maxcase_payloads_sha256,
                "maxcase_replay_path": args.maxcase_replay,
                "maxcase_replay_sha256": args.maxcase_replay_sha256,
            }
        result = build_fn(
            dataset,
            args.output_path,
            args.manifest or str(Path(dataset) / "manifest.json"),
            args.representatives or str(Path(dataset) / "representative_trial_ids.json"),
            mode=args.mode,
            **build_kwargs,
        )
    else:
        if has_maxcase_audit:
            result = build_excel_with_maxcase_audit(
                dataset, args.output_path, mode=args.mode or "canonical",
                maxcase_audit_path=args.maxcase_audit,
                maxcase_payloads_path=args.maxcase_payloads,
                maxcase_audit_sha256=args.maxcase_audit_sha256,
                maxcase_payloads_sha256=args.maxcase_payloads_sha256,
                maxcase_replay_path=args.maxcase_replay,
                maxcase_replay_sha256=args.maxcase_replay_sha256,
            )
        else:
            result = build_excel(dataset, args.output_path, mode=args.mode or "canonical")
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    final_accepted = result.get("final_acceptance_status") == "FINAL_ACCEPTED"
    build_ok = bool(result.get("success"))
    raise SystemExit(0 if build_ok and (not args.require_final_acceptance or final_accepted) else 1)


if __name__ == "__main__":
    main()
