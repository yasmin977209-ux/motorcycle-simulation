from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import monte_carlo
from scripts import s6_first_checkpoint as s6

SOURCE_RUN_ID = "40731224990"
SOURCE_RUN_HEAD_SHA = "a23ba71f48487f3ebead99bc30039b14ef9b7609"
AGGREGATE_RUN_ID = "40773412377"
AGGREGATE_TESTED_SHA = "4f2f2cc16d0cb5125262088704febccbae6f50ed"
AGGREGATE_ARTIFACT_SHA256 = "ec05a69ae8968585decf83cf0716d56c264f47f86187cfd3cf53b11f52ca2e54"
GOLDEN_RUN_ID = "40760465042"
GOLDEN_TESTED_SHA = "3a972c9a0b18b9bc170a289a6aaf8fe1b8797f10"
GOLDEN_ARTIFACT_SHA256 = "e6d94d715eb7e52ffc8ba61ae6dafb766b76914d956879190f1e87b87e311078"
SOURCE_SHA = "da1a9ea9b5cd789c944de3f07b08395bb67c49e7"
COHORT_ID = "s6-v23-da1a9ea9"
MASTER_SEED = 20270101
N = 2400
SCENARIOS = sorted(s6.stochastic_scenario_ids())
C100 = ["C100_G100", "C100_G070", "C100_G050", "C100_G030", "C100_G000"]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def canonical_row_hash_update(h, row: dict[str, Any]) -> None:
    h.update(json.dumps(row, ensure_ascii=False, sort_keys=True,
                        separators=(",", ":"), default=str).encode("utf-8"))
    h.update(b"\n")


def financial_map_sha256(scenario: str, fingerprints: dict[str, str]) -> str:
    lines = [f"{scenario}|{tid}|{fingerprints[tid]}"
             for tid in sorted(fingerprints, key=lambda value: int(value))]
    return hashlib.sha256(("\n".join(lines) + "\n").encode("utf-8")).hexdigest()


def load_golden(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest_paths = list((root / "golden").rglob("independent_golden_manifest.json"))
    map_paths = list((root / "golden").rglob("independent_golden_fingerprints.json"))
    if len(manifest_paths) != 1 or len(map_paths) != 1:
        raise RuntimeError(f"GOLDEN_FILES_MISSING_OR_DUPLICATED:{len(manifest_paths)}:{len(map_paths)}")
    manifest_path, map_path = manifest_paths[0], map_paths[0]
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    gm = json.loads(map_path.read_text(encoding="utf-8"))
    map_hash = sha256_file(map_path)

    expected_manifest = {
        "schema_version": "s6-independent-golden-manifest-v1",
        "status": "INDEPENDENT_GOLDEN_CANDIDATE_NOT_APPROVED",
        "source_sha": SOURCE_SHA, "cohort_id": COHORT_ID, "master_seed": MASTER_SEED,
        "model_schema_version": "v2.3", "tested_sha": GOLDEN_TESTED_SHA,
        "run_id": GOLDEN_RUN_ID, "run_attempt": 1, "trial_count_per_scenario": N,
        "scenario_count": 20, "total_trial_fingerprints": 48000, "total_n_closed": 48000,
        "total_n_censored": 0, "independent_execution": True,
        "production_result_artifacts_read": False,
        "gate_a_approval": "NOT_EVALUATED_REQUIRES_SEPARATE_REVIEW",
        "map_file": map_path.name, "map_file_sha256": map_hash,
    }
    for key, expected in expected_manifest.items():
        if m.get(key) != expected:
            raise RuntimeError(f"GOLDEN_MANIFEST_IDENTITY_MISMATCH:{key}:{m.get(key)}")
    expected_map = {
        "schema_version": "s6-independent-golden-map-v1",
        "status": "INDEPENDENT_GOLDEN_CANDIDATE_NOT_APPROVED",
        "golden_type": "STOCHASTIC_FINANCIAL_TRIAL_FINGERPRINT_MAP",
        "source_sha": SOURCE_SHA, "cohort_id": COHORT_ID, "master_seed": MASTER_SEED,
        "model_schema_version": "v2.3", "tested_sha": GOLDEN_TESTED_SHA,
        "trial_id_start": 1, "trial_id_end": N, "trial_count_per_scenario": N,
        "scenario_count": 20, "total_trial_fingerprints": 48000,
        "independent_execution": True, "production_result_artifacts_read": False,
    }
    for key, expected in expected_map.items():
        if gm.get(key) != expected:
            raise RuntimeError(f"GOLDEN_MAP_IDENTITY_MISMATCH:{key}:{gm.get(key)}")

    scenario_maps = gm.get("scenarios", {})
    scenario_ids = m.get("scenario_ids", [])
    manifest_entries = {str(e.get("scenario_id")): e for e in m.get("scenario_manifest", [])}
    if set(scenario_maps) != set(SCENARIOS) or set(scenario_ids) != set(SCENARIOS):
        raise RuntimeError("GOLDEN_SCENARIO_SET_INVALID")
    if len(manifest_entries) != 20 or set(manifest_entries) != set(SCENARIOS):
        raise RuntimeError("GOLDEN_SCENARIO_MANIFEST_SET_INVALID")

    combined = hashlib.sha256()
    for scenario in scenario_ids:
        entry = scenario_maps[scenario]
        fps = entry.get("trial_fingerprints", {})
        if set(fps) != {str(t) for t in range(1, N + 1)}:
            raise RuntimeError(f"GOLDEN_TRIAL_ID_COVERAGE_INVALID:{scenario}")
        if entry.get("trial_id_start") != 1 or entry.get("trial_id_end") != N or entry.get("trial_count") != N:
            raise RuntimeError(f"GOLDEN_TRIAL_RANGE_INVALID:{scenario}")
        if financial_map_sha256(scenario, fps) != entry.get("financial_trial_fingerprint_map_sha256"):
            raise RuntimeError(f"GOLDEN_SCENARIO_MAP_HASH_INVALID:{scenario}")
        for tid in range(1, N + 1):
            combined.update(f"{scenario}|{tid}|{fps[str(tid)]}\n".encode("utf-8"))
    if m.get("combined_financial_trial_fingerprint_map_sha256") != combined.hexdigest():
        raise RuntimeError("GOLDEN_COMBINED_MAP_HASH_INVALID")

    individual_paths = list((root / "golden-scenarios").rglob("independent_golden_candidate.json"))
    if len(individual_paths) != 20:
        raise RuntimeError(f"GOLDEN_INDIVIDUAL_FILES_INVALID:{len(individual_paths)}")
    individual_seen = set()
    for path in individual_paths:
        doc = json.loads(path.read_text(encoding="utf-8"))
        scenario = str(doc.get("scenario_id", ""))
        if scenario not in SCENARIOS or scenario in individual_seen:
            raise RuntimeError(f"GOLDEN_INDIVIDUAL_SCENARIO_INVALID:{scenario}")
        individual_seen.add(scenario)
        me = manifest_entries[scenario]
        if sha256_file(path) != me.get("file_sha256"):
            raise RuntimeError(f"GOLDEN_INDIVIDUAL_FILE_HASH_MISMATCH:{scenario}")
        identity = {
            "schema_version": "s6-independent-golden-scenario-v1",
            "source_sha": SOURCE_SHA, "cohort_id": COHORT_ID, "master_seed": MASTER_SEED,
            "model_schema_version": "v2.3", "scenario_id": scenario,
            "tested_sha": GOLDEN_TESTED_SHA, "run_id": GOLDEN_RUN_ID, "run_attempt": 1,
            "trial_count": N, "trial_id_start": 1, "trial_id_end": N,
            "n_closed": N, "n_censored": 0, "independent_execution": True,
            "production_result_artifacts_read": False,
            "gate_a_approval": "NOT_EVALUATED_REQUIRES_SEPARATE_REVIEW",
        }
        for key, expected in identity.items():
            if doc.get(key) != expected:
                raise RuntimeError(f"GOLDEN_INDIVIDUAL_IDENTITY_MISMATCH:{scenario}:{key}")
        fps = doc.get("financial_trial_fingerprints", {})
        if set(fps) != {str(t) for t in range(1, N + 1)}:
            raise RuntimeError(f"GOLDEN_INDIVIDUAL_TRIAL_COVERAGE_INVALID:{scenario}")
        if financial_map_sha256(scenario, fps) != doc.get("financial_trial_fingerprint_map_sha256"):
            raise RuntimeError(f"GOLDEN_INDIVIDUAL_MAP_HASH_INVALID:{scenario}")
        if fps != scenario_maps[scenario].get("trial_fingerprints"):
            raise RuntimeError(f"GOLDEN_INDIVIDUAL_VS_COMBINED_MAP_MISMATCH:{scenario}")
        for key in ("financial_trial_fingerprint_map_sha256", "rng_audit_map_sha256",
                    "complete_trial_result_audit_sha256", "trial_count"):
            if doc.get(key) != me.get(key) or doc.get(key) != scenario_maps[scenario].get(key):
                raise RuntimeError(f"GOLDEN_INDIVIDUAL_MANIFEST_ENTRY_MISMATCH:{scenario}:{key}")

    evidence = {
        "status": "VERIFIED_CANDIDATE_COVERAGE_NOT_APPROVED",
        "run_id": int(GOLDEN_RUN_ID), "tested_sha": GOLDEN_TESTED_SHA,
        "artifact_sha256": GOLDEN_ARTIFACT_SHA256, "map_sha256": map_hash,
        "combined_financial_trial_fingerprint_map_sha256": combined.hexdigest(),
        "scenario_count": 20, "trial_fingerprints": 48000,
        "individual_scenario_files_verified": len(individual_paths),
        "approval": "NOT_EVALUATED_REQUIRES_SEPARATE_REVIEW",
    }
    return scenario_maps, evidence


def capture_source_run_provenance(root: Path) -> dict[str, Any]:
    api = root / "source-api"
    paths = {"run": api / "source_run.json", "jobs": api / "source_jobs.json",
             "artifacts": api / "source_artifacts.json"}
    if not all(p.is_file() for p in paths.values()):
        return {"status": "MISSING_EVIDENCE_API_CAPTURE_NOT_AVAILABLE"}
    run = json.loads(paths["run"].read_text(encoding="utf-8"))
    jobs = json.loads(paths["jobs"].read_text(encoding="utf-8")).get("jobs", [])
    artifacts = json.loads(paths["artifacts"].read_text(encoding="utf-8")).get("artifacts", [])
    expected_run = {
        "id": int(SOURCE_RUN_ID), "run_attempt": 1, "status": "completed",
        "head_sha": SOURCE_RUN_HEAD_SHA,
        "head_branch": "tmp/s6-aggregate-contract-fix-20261027",
        "path": ".github/workflows/s6-n600-checkpoint.yml",
    }
    for key, expected in expected_run.items():
        if run.get(key) != expected:
            raise RuntimeError(f"SOURCE_RUN_API_IDENTITY_MISMATCH:{key}:{run.get(key)}")
    expected_names = {f"s6-n2400-{s.replace('_G100','-G100')}-{SOURCE_RUN_ID}" for s in SCENARIOS}
    by_name = {str(a.get("name")): a for a in artifacts}
    if len(artifacts) != 20 or set(by_name) != expected_names:
        raise RuntimeError("SOURCE_RUN_ARTIFACT_API_COVERAGE_INVALID")
    for name, art in by_name.items():
        if art.get("expired") is True or not art.get("digest") or int(art.get("size_in_bytes", 0)) <= 0:
            raise RuntimeError(f"SOURCE_RUN_ARTIFACT_API_METADATA_INVALID:{name}")
    job_by_name = {str(j.get("name")): j for j in jobs}
    scenario_jobs = {}
    for scenario in SCENARIOS:
        collection, recovery = scenario.split("_")
        job_name = f"S6 N2400 G100 base — {collection}" if recovery == "G100" else f"S6 N2400 {scenario}"
        job = job_by_name.get(job_name)
        if not job or job.get("status") != "completed" or job.get("conclusion") != "success":
            raise RuntimeError(f"SOURCE_SCENARIO_JOB_NOT_SUCCESS:{scenario}")
        scenario_jobs[scenario] = {"job_id": int(job["id"]), "name": job_name,
                                   "conclusion": job.get("conclusion")}
    return {
        "status": "VERIFIED_SCENARIO_JOBS_AND_ARTIFACTS_PARENT_RUN_FAILED",
        "source_run_id": int(SOURCE_RUN_ID), "run_attempt": 1,
        "source_run_head_sha": SOURCE_RUN_HEAD_SHA, "source_sha": SOURCE_SHA,
        "cohort_id": COHORT_ID, "master_seed": MASTER_SEED,
        "parent_run_status": run.get("status"), "parent_run_conclusion": run.get("conclusion"),
        "created_at": run.get("created_at"), "run_started_at": run.get("run_started_at"),
        "updated_at": run.get("updated_at"), "scenario_job_count": len(scenario_jobs),
        "scenario_jobs": scenario_jobs, "scenario_artifact_count": len(by_name),
        "scenario_artifacts": {name: {"artifact_id": int(a["id"]),
                                      "size_bytes": int(a["size_in_bytes"]),
                                      "digest": a["digest"], "expired": a.get("expired")}
                               for name, a in sorted(by_name.items())},
        "api_capture_sha256": {key: sha256_file(path) for key, path in paths.items()},
        "interpretation": "20 scenario jobs and artifacts are individually successful; the parent workflow failed at its final aggregate job. The original null source_run_metadata.sha256 remains unfilled.",
    }


def reject_floats(value: Any, path: str = "$") -> None:
    if isinstance(value, float):
        raise RuntimeError(f"FLOAT_IN_EXACT_NUMBER_REGISTRY:{path}")
    if isinstance(value, dict):
        for key, item in value.items():
            reject_floats(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            reject_floats(item, f"{path}[{index}]")


def main() -> int:
    root = Path(os.environ.get("AUDIT_INPUT_ROOT", "audit-input"))
    aggregate_manifests = list((root / "aggregate").rglob("manifest.json"))
    source_manifests = sorted((root / "scenarios").rglob("scenario_manifest.json"),
                              key=lambda p: str(json.loads(p.read_text(encoding="utf-8")).get("scenario_id", "")))
    if len(aggregate_manifests) != 1 or len(source_manifests) != 20:
        raise RuntimeError(f"AUDIT_INPUT_COVERAGE_INVALID:{len(aggregate_manifests)}:{len(source_manifests)}")
    aggregate_dir = aggregate_manifests[0].parent
    manifest = json.loads(aggregate_manifests[0].read_text(encoding="utf-8"))
    identity = {
        "schema_version": "s6-cumulative-aggregate-v2", "status": "EXECUTED",
        "exit_code": 0, "run_id": AGGREGATE_RUN_ID, "git_commit": AGGREGATE_TESTED_SHA,
        "source_run_id": SOURCE_RUN_ID, "source_run_attempt": 1,
        "source_sha": SOURCE_SHA, "cohort_id": COHORT_ID, "master_seed": MASTER_SEED,
        "checkpoint_n": N, "scenario_count": 20, "total_scenario_combinations": 25,
        "c100_reused_scenario_count": 5,
    }
    for key, expected in identity.items():
        if manifest.get(key) != expected:
            raise RuntimeError(f"AGGREGATE_IDENTITY_MISMATCH:{key}:{manifest.get(key)}")
    aggregate_files = {}
    for name, expected in manifest.get("files", {}).items():
        path = aggregate_dir / name
        if not path.is_file():
            raise RuntimeError(f"AGGREGATE_MEMBER_MISSING:{name}")
        digest, size = sha256_file(path), path.stat().st_size
        if digest != expected.get("sha256") or size != expected.get("size_bytes"):
            raise RuntimeError(f"AGGREGATE_MEMBER_HASH_OR_SIZE_MISMATCH:{name}")
        aggregate_files[name] = {"sha256": digest, "size_bytes": size}
    if aggregate_files.get("trials_summary.parquet", {}).get("sha256") != "66c8c4530073dba14e4082eb13ab492d304fa6841e3db08ae6c38509de66d522":
        raise RuntimeError("LATEST_AGGREGATE_TRIALS_HASH_NOT_EXPECTED")
    if aggregate_files.get("daily_distribution.parquet", {}).get("sha256") != "9619fc94e371da073a622f8f0fcd28786caf79fac47697cca2bfadbb469e4903":
        raise RuntimeError("LATEST_AGGREGATE_DAILY_HASH_NOT_EXPECTED")

    c100 = json.loads((aggregate_dir / "c100_reuse.json").read_text(encoding="utf-8"))
    expected_c100 = {
        "status": "REUSED_READ_ONLY", "run_id": 40263424595, "rerun": False,
        "source_sha": "965281d52441cd0d4b744e211c9f68ee4cdc3753",
        "cohort_id": "c100-v23-s4-20261026-965281d5",
        "golden_sha256": "39950d91c3b40b11bea0997b8504ac932a57bcc0ef8e0c51e12d031342a53327",
        "manifest_sha256": "2097284d77ead6b00492bf75830d09aeef8dbde4aaa1c15dae6a877dc7e9ff04",
        "trial_count_per_scenario": 300, "n_unique_paths": 1,
        "degeneracy_status": "DEGENERATE_DETERMINISTIC", "G_status": "G_INERT",
        "scenario_ids": C100,
    }
    for key, expected in expected_c100.items():
        if c100.get(key) != expected:
            raise RuntimeError(f"C100_REUSE_IDENTITY_MISMATCH:{key}")
    original_source_metadata_sha = manifest.get("source_run_metadata", {}).get("sha256")

    golden_maps, golden_evidence = load_golden(root)
    source_provenance = capture_source_run_provenance(root)
    comparison = {"status": "PENDING", "compared_fingerprints": 0, "exact_matches": 0,
                  "mismatch_count": 0, "first_mismatches": [],
                  "gate_a_approval": "NOT_GRANTED_CANDIDATE_REQUIRES_SEPARATE_REVIEW"}
    source_trial_digest = hashlib.sha256()
    source_daily_digest = hashlib.sha256()
    scenario_data = {}
    accounting = {
        "rows_seen": 0, "rows_recomputed": 0, "missing_component_rows": 0,
        "invalid_integer_rows": 0, "assets_neq_equity_count": 0,
        "stored_total_assets_mismatch_count": 0,
        "stored_balance_difference_mismatch_count": 0, "first_mismatches": [],
    }
    component_keys = ("Cash", "Accounts_Receivable", "Guarantee_Claim_Receivable",
                      "Gross_Bike_Assets", "Accumulated_Depreciation")

    for scenario_manifest_path in source_manifests:
        sm = json.loads(scenario_manifest_path.read_text(encoding="utf-8"))
        scenario = str(sm.get("scenario_id", ""))
        if scenario not in SCENARIOS or scenario in scenario_data:
            raise RuntimeError(f"SOURCE_SCENARIO_DUPLICATE_OR_UNKNOWN:{scenario}")
        expected_identity = {
            "source_sha": SOURCE_SHA, "cohort_id": COHORT_ID, "master_seed": MASTER_SEED,
            "run_id": SOURCE_RUN_ID, "run_attempt": 1, "trial_count": N,
            "trial_id_start": 1, "trial_id_end": N,
            "schema_version": "s6-first-checkpoint-v1", "git_commit": SOURCE_RUN_HEAD_SHA,
        }
        for key, expected in expected_identity.items():
            if sm.get(key) != expected:
                raise RuntimeError(f"SOURCE_SCENARIO_MANIFEST_IDENTITY_MISMATCH:{scenario}:{key}")
        folder = scenario_manifest_path.parent
        file_checks = {}
        for name, expected in sm.get("files", {}).items():
            path = folder / name
            if not path.is_file():
                raise RuntimeError(f"SOURCE_SCENARIO_MEMBER_MISSING:{scenario}:{name}")
            digest, size = sha256_file(path), path.stat().st_size
            if digest != expected.get("sha256") or size != expected.get("size_bytes"):
                raise RuntimeError(f"SOURCE_SCENARIO_MEMBER_HASH_OR_SIZE_MISMATCH:{scenario}:{name}")
            file_checks[name] = {"sha256": digest, "size_bytes": size}

        rows = pq.read_table(folder / "trials_summary.parquet").to_pylist()
        ids = [int(row["trial_id"]) for row in rows]
        if ids != list(range(1, N + 1)):
            raise RuntimeError(f"SOURCE_TRIAL_IDS_NOT_EXACT_1_TO_2400:{scenario}")
        if any(str(row.get("scenario_id")) != scenario or row.get("source_sha") != SOURCE_SHA
               or row.get("cohort_id") != COHORT_ID or row.get("schema_version") != "v2.3" for row in rows):
            raise RuntimeError(f"SOURCE_TRIAL_ROW_IDENTITY_MISMATCH:{scenario}")
        s6.validate_cumulative_rng_audit(rows, SOURCE_SHA)
        golden_fps = golden_maps[scenario]["trial_fingerprints"]
        for row in rows:
            tid = int(row["trial_id"])
            prod_fp = str(row.get("trial_fingerprint", ""))
            golden_fp = golden_fps.get(str(tid))
            comparison["compared_fingerprints"] += 1
            if prod_fp == golden_fp:
                comparison["exact_matches"] += 1
            else:
                comparison["mismatch_count"] += 1
                if len(comparison["first_mismatches"]) < 25:
                    comparison["first_mismatches"].append({"scenario_id": scenario, "trial_id": tid,
                                                            "production": prod_fp, "golden": golden_fp})
            calculated = monte_carlo.trial_fingerprint(s6.result_from_record(row))
            if prod_fp != calculated:
                raise RuntimeError(f"PRODUCTION_FINANCIAL_FINGERPRINT_RECOMPUTE_MISMATCH:{scenario}:{tid}")
            canonical_row_hash_update(source_trial_digest, row)

        daily_rows = 0
        for batch in pq.ParquetFile(folder / "daily_distribution.parquet").iter_batches(batch_size=8192):
            for row in batch.to_pylist():
                canonical_row_hash_update(source_daily_digest, row)
                daily_rows += 1

        snapshots_path = folder / "daily_snapshots.parquet"
        pf = pq.ParquetFile(snapshots_path)
        columns = set(pf.schema_arrow.names)
        seen_ids, previous_id = set(), None
        snapshot_rows = 0
        for batch in pf.iter_batches(batch_size=8192):
            for row in batch.to_pylist():
                snapshot_rows += 1
                if row.get("schema_version") != "v2.3" or row.get("source_sha") != SOURCE_SHA or row.get("cohort_id") != COHORT_ID or str(row.get("scenario_id")) != scenario:
                    raise RuntimeError(f"DAILY_SNAPSHOT_IDENTITY_MISMATCH:{scenario}")
                tid = int(row["trial_id"])
                if previous_id is not None and tid < previous_id:
                    raise RuntimeError(f"DAILY_SNAPSHOT_ORDER_INVALID:{scenario}")
                previous_id = tid
                if not 1 <= tid <= N:
                    raise RuntimeError(f"DAILY_SNAPSHOT_TRIAL_ID_OUT_OF_RANGE:{scenario}:{tid}")
                seen_ids.add(tid)
                accounting["rows_seen"] += 1
                if not all(k in row and row[k] is not None for k in component_keys):
                    accounting["missing_component_rows"] += 1
                    if len(accounting["first_mismatches"]) < 25:
                        accounting["first_mismatches"].append({"scenario_id": scenario, "trial_id": tid,
                                                                "date": str(row.get("date")), "reason": "MISSING_ASSET_COMPONENTS"})
                    continue
                vals = [row[k] for k in component_keys]
                equity = row.get("Total_Equity")
                if equity is None and row.get("Capital") is not None and row.get("Retained_Earnings") is not None:
                    equity = row["Capital"] + row["Retained_Earnings"]
                if type(equity) is not int or any(type(v) is not int for v in vals):
                    accounting["invalid_integer_rows"] += 1
                    if len(accounting["first_mismatches"]) < 25:
                        accounting["first_mismatches"].append({"scenario_id": scenario, "trial_id": tid,
                                                                "date": str(row.get("date")), "reason": "MISSING_OR_NONINTEGER_EQUITY"})
                    continue
                cash, ar, guar_ar, gross, depreciation = vals
                assets = cash + ar + guar_ar + gross - depreciation
                difference = assets - equity
                accounting["rows_recomputed"] += 1
                mismatch = difference != 0
                if mismatch:
                    accounting["assets_neq_equity_count"] += 1
                reported_assets = row.get("Total_Assets")
                if reported_assets is not None and (type(reported_assets) is not int or reported_assets != assets):
                    accounting["stored_total_assets_mismatch_count"] += 1
                    mismatch = True
                stored_diff = row.get("Balance_Difference")
                if stored_diff is not None and (type(stored_diff) is not int or stored_diff != difference):
                    accounting["stored_balance_difference_mismatch_count"] += 1
                    mismatch = True
                if mismatch and len(accounting["first_mismatches"]) < 25:
                    accounting["first_mismatches"].append({"scenario_id": scenario, "trial_id": tid,
                        "date": str(row.get("date")), "reason": "ASSETS_EQUITY_OR_STORED_TOTAL_MISMATCH",
                        "assets": assets, "equity": equity, "difference": difference,
                        "reported_total_assets": reported_assets, "stored_difference": stored_diff})
        if seen_ids != set(range(1, N + 1)):
            raise RuntimeError(f"DAILY_SNAPSHOT_TRIAL_COVERAGE_INVALID:{scenario}")
        scenario_data[scenario] = {
            "trial_rows": len(rows), "daily_distribution_rows": daily_rows,
            "daily_snapshot_rows": snapshot_rows, "daily_snapshot_columns": sorted(columns),
            "assets_field_present": "Total_Assets" in columns, "equity_field_present": "Total_Equity" in columns,
            "asset_components_present": set(component_keys).issubset(columns),
            "scenario_manifest_sha256": sha256_file(scenario_manifest_path), "files": file_checks,
        }

    if set(scenario_data) != set(SCENARIOS) or comparison["compared_fingerprints"] != 48000:
        raise RuntimeError("EXACT_SCENARIO_OR_GOLDEN_COMPARISON_COVERAGE_INVALID")
    comparison["status"] = "PASS_EXACT_MATCH" if comparison["mismatch_count"] == 0 and comparison["exact_matches"] == 48000 else "FAIL_EXACT_MATCH"

    # Compare source trial rows and daily-distribution rows against the immutable aggregate in canonical row order.
    aggregate_trial_hash = hashlib.sha256()
    aggregate_trial_count = 0
    for batch in pq.ParquetFile(aggregate_dir / "trials_summary.parquet").iter_batches(batch_size=8192):
        for row in batch.to_pylist():
            canonical_row_hash_update(aggregate_trial_hash, row)
            aggregate_trial_count += 1
    aggregate_daily_hash = hashlib.sha256()
    aggregate_daily_count = 0
    for batch in pq.ParquetFile(aggregate_dir / "daily_distribution.parquet").iter_batches(batch_size=8192):
        for row in batch.to_pylist():
            canonical_row_hash_update(aggregate_daily_hash, row)
            aggregate_daily_count += 1
    if aggregate_trial_count != 48000 or aggregate_trial_hash.hexdigest() != source_trial_digest.hexdigest():
        raise RuntimeError("AGGREGATE_TRIAL_ROWS_DIFFER_FROM_IMMUTABLE_SOURCE")
    if aggregate_daily_count != sum(x["daily_distribution_rows"] for x in scenario_data.values()) or aggregate_daily_hash.hexdigest() != source_daily_digest.hexdigest():
        raise RuntimeError("AGGREGATE_DAILY_ROWS_DIFFER_FROM_IMMUTABLE_SOURCE")

    registry = json.loads((aggregate_dir / "number_registry.json").read_text(encoding="utf-8"))
    reject_floats(registry)
    entries = registry.get("entries", [])
    if len(entries) != 960:
        raise RuntimeError(f"NUMBER_REGISTRY_COUNT_INVALID:{len(entries)}")
    for item in entries:
        if type(item.get("exact_numerator")) is not int or type(item.get("exact_denominator")) is not int or int(item["exact_denominator"]) <= 0:
            raise RuntimeError("NUMBER_REGISTRY_FRACTION_INVALID")
        if not str(item.get("source", "")).startswith(f"{SOURCE_SHA}/{COHORT_ID}/"):
            raise RuntimeError("NUMBER_REGISTRY_SOURCE_IDENTITY_INVALID")

    stats = json.loads((aggregate_dir / "statistical_evaluation.json").read_text(encoding="utf-8"))
    counts = stats.get("checkpoint_gate_b_counts", {})
    if set(counts) != {"300", "600", "1200", "2400"} or any(sum(c.values()) != 20 for c in counts.values()):
        raise RuntimeError("STATISTICAL_CHECKPOINT_COVERAGE_INVALID")
    if stats.get("transition_count") != 60 or stats.get("successful_transition_count") != 0:
        raise RuntimeError("STATISTICAL_TRANSITION_COUNTS_INVALID")
    if stats.get("gate_a_final") != "NOT_EVALUATED_NO_SAME_SOURCE_PRODUCTION_GOLDEN" or stats.get("scenario_stability_final") != "NOT_CONVERGED":
        raise RuntimeError("STATISTICAL_FAIL_CLOSED_STATUS_INVALID")
    acc_status = "FAIL_ACCOUNTING_BALANCE" if (accounting["assets_neq_equity_count"] or accounting["stored_total_assets_mismatch_count"] or accounting["stored_balance_difference_mismatch_count"]) else (
        "PASS_INDEPENDENT_RECHECK" if accounting["rows_seen"] > 0 and accounting["rows_recomputed"] == accounting["rows_seen"] and accounting["missing_component_rows"] == 0 and accounting["invalid_integer_rows"] == 0 else "MISSING_EVIDENCE_FOR_INDEPENDENT_RECHECK"
    )
    accounting.update({
        "status": acc_status, "scenario_count": 20,
        "assets_field_present_all_scenarios": all(v["assets_field_present"] for v in scenario_data.values()),
        "equity_field_present_all_scenarios": all(v["equity_field_present"] for v in scenario_data.values()),
        "asset_components_present_all_scenarios": all(v["asset_components_present"] for v in scenario_data.values()),
        "formula": "Assets = Cash + Accounts_Receivable + Guarantee_Claim_Receivable + Gross_Bike_Assets - Accumulated_Depreciation; compare to Total_Equity (or Capital + Retained_Earnings when present).",
    })
    provenance = capture_source_run_provenance(root)
    out = Path("audit-output")
    out.mkdir(parents=True, exist_ok=True)
    provenance_path = out / "source_run_provenance_reconciliation.json"
    provenance_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    provenance_sha = sha256_file(provenance_path)
    audit = {
        "schema_version": "s6-n2400-golden-accounting-independent-audit-v1",
        "status": "EXECUTED_SCOPED_RECONCILIATION",
        "source_run_id": SOURCE_RUN_ID, "source_run_head_sha": SOURCE_RUN_HEAD_SHA,
        "aggregate_run_id": AGGREGATE_RUN_ID, "aggregate_tested_sha": AGGREGATE_TESTED_SHA,
        "aggregate_artifact_sha256": AGGREGATE_ARTIFACT_SHA256,
        "golden_run_id": GOLDEN_RUN_ID, "golden_tested_sha": GOLDEN_TESTED_SHA,
        "golden_artifact_sha256": GOLDEN_ARTIFACT_SHA256,
        "source_sha": SOURCE_SHA, "cohort_id": COHORT_ID, "master_seed": MASTER_SEED, "checkpoint_n": N,
        "scenario_count": 20, "total_scenario_combinations": 25, "c100_reused_scenario_count": 5,
        "trial_rows": aggregate_trial_count, "daily_distribution_rows": aggregate_daily_count,
        "aggregate_trial_rows_equal_source_rows": True, "aggregate_daily_rows_equal_source_rows": True,
        "aggregate_member_hashes": aggregate_files, "scenario_evidence": scenario_data,
        "golden_candidate": golden_evidence, "golden_candidate_comparison": comparison,
        "daily_balance_reconciliation": accounting,
        "statistical_evaluation": {"checkpoint_gate_b_counts": counts, "gate_a": stats.get("gate_a_final"),
            "gate_b": stats.get("gate_b_final"), "stability": stats.get("scenario_stability_final"),
            "transitions": stats.get("transition_count"), "successful_transitions": stats.get("successful_transition_count")},
        "source_run_provenance_reconciliation": provenance,
        "source_run_provenance_reconciliation_sha256": provenance_sha,
        "original_source_run_metadata_sha256": original_source_metadata_sha,
        "original_source_run_metadata_status": "PRESERVED_NULL_MISSING_ORIGINAL_FILE" if original_source_metadata_sha is None else "PRESENT",
        "gate_a_approval": "NOT_GRANTED_CANDIDATE_REQUIRES_SEPARATE_REVIEW",
        "acceptance": "NOT_GRANTED",
    }
    (out / "S6_N2400_GOLDEN_ACCOUNTING_AUDIT.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# S6 N2400 Exact Golden and Daily Accounting Audit", "",
        f"- Audit execution: {audit['status']}",
        f"- Source run conclusion: {provenance.get('parent_run_conclusion')}",
        f"- Source SHA / cohort / seed: {SOURCE_SHA} / {COHORT_ID} / {MASTER_SEED}",
        f"- N2400 aggregate run and ZIP digest: {AGGREGATE_RUN_ID} / {AGGREGATE_ARTIFACT_SHA256}",
        f"- Golden candidate run and ZIP digest: {GOLDEN_RUN_ID} / {GOLDEN_ARTIFACT_SHA256}",
        f"- Exact production-vs-Golden comparison: {comparison['status']}; compared {comparison['compared_fingerprints']}; exact matches {comparison['exact_matches']}; mismatches {comparison['mismatch_count']}.",
        "- Golden candidate remains unapproved; exact match alone does not grant Gate A.",
        f"- Independent daily accounting recheck: {acc_status}; rows seen {accounting['rows_seen']}; recomputed {accounting['rows_recomputed']}; balance mismatches {accounting['assets_neq_equity_count']}.",
        f"- Original source_run_metadata.sha256: {original_source_metadata_sha!r}; separate provenance reconciliation SHA-256: {provenance_sha}.",
        f"- Gate A: {stats.get('gate_a_final')}; Gate B: {stats.get('gate_b_final')}; stability: {stats.get('scenario_stability_final')}.",
        f"- Transitions: {stats.get('transition_count')}; successful: {stats.get('successful_transition_count')}.",
        "", "Scoped audit evidence only; no Gate A/B PASS, CONVERGED, or FINAL_ACCEPTED is granted.",
    ]
    (out / "S6_N2400_GOLDEN_ACCOUNTING_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": audit["status"], "golden_comparison": comparison,
        "daily_balance_reconciliation": acc_status, "rows_seen": accounting["rows_seen"],
        "rows_recomputed": accounting["rows_recomputed"], "balance_mismatches": accounting["assets_neq_equity_count"],
        "source_run_status": provenance.get("status"), "source_run_provenance_sha256": provenance_sha,
        "gate_a": stats.get("gate_a_final"), "gate_b": stats.get("gate_b_final"),
        "stability": stats.get("scenario_stability_final")}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
