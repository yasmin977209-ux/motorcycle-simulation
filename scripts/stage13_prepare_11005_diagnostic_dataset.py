from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import tempfile
import zipfile
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

from scripts import stage13_gatea_fingerprint_bridge as gatea
from scripts import stage13_maxcase_source_audit as maxcase_audit
from scripts.stage13_assemble import EXPECTED_SCENARIOS, select_representative_trial_ids

STAGE7_RUN = maxcase_audit.STAGE7_RUN
STAGE10_RUN = maxcase_audit.STAGE10_RUN
STAGE12_RUN = maxcase_audit.STAGE12_RUN
STAGE7_HEAD = maxcase_audit.STAGE7_HEAD
STAGE10_HEAD = maxcase_audit.STAGE10_HEAD
STAGE12_HEAD = maxcase_audit.STAGE12_HEAD
SOURCE_SHA = maxcase_audit.SOURCE_SHA
MASTER_SEED = maxcase_audit.MASTER_SEED
SOURCE_MANIFEST_BLOB = "c8591aac3d309fd94c4e67a547d33fb62ac5694d"
IDENTITY_BLOB = "72a481d509d39820fba78732724fde4fa9f25134"
COHORT_MANIFEST_BLOB = "b8947a60051a244784248875f5e0435b9996d95b"
GLOBAL_11005 = "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44"
EXPECTED_DAILY_ROWS = 22546465
METRICS = {
    "Cash": "Closing_Cash",
    "Net_Equity": "Closing_Equity",
    "Active_Bikes": "Active_Bikes",
    "Owned_Transferred_Bikes": "Owned_Transferred_Bikes",
    "Pending_Claims": "Pending_Claims",
}
QUANTILES = ((10, 0.10), (25, 0.25), (50, 0.50), (75, 0.75), (90, 0.90))
ROLE_FILES = (("P10", "P10"), ("P50", "P50"), ("P90", "P90"), ("Loss", "Loss"))


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, default=str) + "\n", encoding="utf-8")


def same_summary(candidate: Any, expected: dict[str, Any]) -> bool:
    return (
        isinstance(candidate, dict)
        and set(candidate) == set(expected)
        and all(type(candidate.get(key)) is type(value) and candidate.get(key) == value for key, value in expected.items())
    )


def validate_rng_audit_rows(scenario: str, rows: list[dict[str, Any]]) -> None:
    """Reject legacy rows without real RNG audit; never synthesize missing checksums."""
    expected_probability = maxcase_audit.expected_collection_probability(scenario)
    seen: dict[int, int] = {}
    for row in rows:
        trial_id = row.get("trial_id")
        if "rng_checksum" not in row or "rng_draw_count" not in row:
            raise RuntimeError(
                f"STAGE13_RNG_AUDIT_MISSING: {scenario}/{trial_id}; "
                "historical rows must be regenerated under an approved audited source"
            )
        checksum = row["rng_checksum"]
        draw_count = row["rng_draw_count"]
        if type(checksum) is not int or not 0 <= checksum < (1 << 64):
            raise RuntimeError(f"STAGE13_RNG_CHECKSUM_INVALID: {scenario}/{trial_id}")
        if type(draw_count) is not int or draw_count < 0:
            raise RuntimeError(f"STAGE13_RNG_DRAW_COUNT_INVALID: {scenario}/{trial_id}")
        if expected_probability in (0.0, 1.0):
            if checksum != 0 or draw_count != 0:
                raise RuntimeError(f"STAGE13_DETERMINISTIC_RNG_AUDIT_NOT_EMPTY: {scenario}/{trial_id}")
        elif draw_count == 0:
            raise RuntimeError(f"STAGE13_STOCHASTIC_RNG_AUDIT_EMPTY: {scenario}/{trial_id}")
        if draw_count == 0 and checksum != 0:
            raise RuntimeError(f"STAGE13_RNG_CHECKSUM_WITHOUT_DRAWS: {scenario}/{trial_id}")
        if checksum != 0:
            previous = seen.get(checksum)
            if previous is not None:
                raise RuntimeError(
                    f"DUPLICATE_SEED_DETECTED: {scenario}:{previous},{trial_id}:{checksum}"
                )
            seen[checksum] = int(trial_id)


def assert_artifact_run(artifact: dict[str, Any], run_id: int, head_sha: str, scenario: str) -> None:
    run = artifact.get("workflow_run") or {}
    if not run or int(run.get("id", -1)) != run_id or run.get("head_sha") != head_sha:
        raise RuntimeError(
            f"SOURCE_ARTIFACT_RUN_HEAD_MISMATCH: {scenario}/{artifact.get('name')} "
            f"expected={run_id}/{head_sha} actual={run.get('id')}/{run.get('head_sha')}"
        )


def download_single_parquet(artifact: dict[str, Any], name: str, root: Path) -> tuple[Path, dict[str, Any]]:
    zip_path = root / f"{int(artifact['id'])}.zip"
    evidence = gatea.download_artifact(artifact, zip_path)
    with zipfile.ZipFile(zip_path, "r") as archive:
        members = archive.namelist()
        if members != [name]:
            raise RuntimeError(f"STAGE12_ARTIFACT_MEMBERS_MISMATCH: expected={[name]} actual={members}")
        payload = archive.read(name)
    path = root / name
    path.write_bytes(payload)
    return path, {
        **evidence, "artifact_id": int(artifact["id"]),
        "artifact_name": artifact.get("name"),
        "parquet_sha256": hashlib.sha256(payload).hexdigest(),
    }


def build_daily_distribution(matrices: dict[str, np.ndarray], last_day: int) -> list[dict[str, Any]]:
    output = []
    first_date = date(2027, 1, 1)
    for day_index in range(last_day + 1):
        active = np.isfinite(matrices["Cash"][:, day_index])
        active_count = int(active.sum())
        if active_count == 0:
            continue
        row: dict[str, Any] = {
            "date": (first_date + timedelta(days=day_index)).isoformat(),
            "active_trial_count": active_count,
        }
        for metric, matrix in matrices.items():
            values = matrix[active, day_index]
            quantiles = np.quantile(values, [q for _, q in QUANTILES], method="linear")
            for (percent, _), value in zip(QUANTILES, quantiles):
                row[f"P{percent}_{metric}"] = float(value)
        output.append(row)
    return output


def process_stage12_daily(
    scenario: str,
    parquet_path: Path,
    trial_count: int,
    selected: dict[str, int],
    scenario_dir: Path,
    trial_hashes: dict[int, str],
) -> tuple[dict[int, list[dict[str, Any]]], dict[str, Any]]:
    required = {
        "scenario_id", "trial_id", "date", "source_sha", "master_seed", "result_sha256",
        "Closing_Cash", "Closing_Equity", "Retained_Earnings", "Final_Close_Date",
        "Active_Bikes", "Owned_Transferred_Bikes", "Pending_Claims",
    }
    parquet = pq.ParquetFile(parquet_path)
    missing = sorted(required - set(parquet.schema_arrow.names))
    if missing:
        raise RuntimeError(f"STAGE12_REQUIRED_FIELDS_MISSING: {scenario}: {missing}")
    matrices = {name: np.full((trial_count, 2500), np.nan, dtype=np.float64) for name in METRICS}
    selected_ids = set(selected.values())
    selected_daily = {trial_id: [] for trial_id in selected_ids}
    first_date = date(2027, 1, 1)
    last_by_trial: dict[int, date] = {}
    rows_seen = 0
    last_day_index = -1

    for batch in parquet.iter_batches(batch_size=65536, columns=sorted(required)):
        for item in batch.to_pylist():
            rows_seen += 1
            trial_id = int(item["trial_id"])
            if (
                item["scenario_id"] != scenario
                or item["source_sha"] != SOURCE_SHA
                or int(item["master_seed"]) != MASTER_SEED
            ):
                raise RuntimeError(f"STAGE12_DAILY_IDENTITY_MISMATCH: {scenario}/{trial_id}")
            if not (1 <= trial_id <= trial_count):
                raise RuntimeError(f"STAGE12_DAILY_TRIAL_ID_OUT_OF_RANGE: {scenario}/{trial_id}")
            current_date = date.fromisoformat(str(item["date"]))
            previous_date = last_by_trial.get(trial_id)
            if previous_date is None:
                if current_date != first_date:
                    raise RuntimeError(f"STAGE12_FIRST_DATE_MISMATCH: {scenario}/{trial_id}")
            elif current_date != previous_date + timedelta(days=1):
                raise RuntimeError(f"STAGE12_DATE_GAP: {scenario}/{trial_id}/{current_date}")
            last_by_trial[trial_id] = current_date
            if item["result_sha256"] != trial_hashes[trial_id]:
                raise RuntimeError(f"STAGE12_RESULT_SHA_MISMATCH: {scenario}/{trial_id}")
            day_index = (current_date - first_date).days
            last_day_index = max(last_day_index, day_index)
            if day_index >= matrices["Cash"].shape[1]:
                new_width = max(day_index + 1, matrices["Cash"].shape[1] + 500)
                for metric, old in list(matrices.items()):
                    grown = np.full((trial_count, new_width), np.nan, dtype=np.float64)
                    grown[:, :old.shape[1]] = old
                    matrices[metric] = grown
            for metric, source_field in METRICS.items():
                value = item[source_field]
                if type(value) is bool or not isinstance(value, (int, float)):
                    raise RuntimeError(f"STAGE12_METRIC_NOT_NUMERIC: {scenario}/{trial_id}/{source_field}")
                matrices[metric][trial_id - 1, day_index] = float(value)
            if trial_id in selected_daily:
                selected_daily[trial_id].append({
                    "trial_id": trial_id,
                    "date": str(item["date"]),
                    "Final_Close_Date": item.get("Final_Close_Date"),
                    "Cash": int(item["Closing_Cash"]),
                    "Net_Equity": int(item["Closing_Equity"]),
                    "Cumulative_Project_Profit": int(item["Retained_Earnings"]),
                    "Retained_Earnings": int(item["Retained_Earnings"]),
                    "Active_Bikes": int(item["Active_Bikes"]),
                    "Owned_Transferred_Bikes": int(item["Owned_Transferred_Bikes"]),
                    "Pending_Claims": int(item["Pending_Claims"]),
                    "source_sha": item["source_sha"],
                    "master_seed": int(item["master_seed"]),
                    "result_sha256": item["result_sha256"],
                })

    if sorted(last_by_trial) != list(range(1, trial_count + 1)):
        raise RuntimeError(f"STAGE12_DAILY_TRIAL_COVERAGE_MISMATCH: {scenario}")
    for trial_id, daily_rows in selected_daily.items():
        if not daily_rows:
            raise RuntimeError(f"STAGE12_SELECTED_TRIAL_DAILY_MISSING: {scenario}/{trial_id}")
    distribution = build_daily_distribution(matrices, last_day_index)
    scenario_dir.mkdir(parents=True, exist_ok=True)
    distribution_path = scenario_dir / "daily_distribution.parquet"
    pq.write_table(pa.Table.from_pylist(distribution), distribution_path, compression="zstd")
    return selected_daily, {
        "daily_rows_read": rows_seen,
        "trial_count": len(last_by_trial),
        "selected_role_trial_count": len(selected_daily),
        "last_day_index": last_day_index,
        "daily_distribution_rows": len(distribution),
        "daily_distribution_sha256": hashlib.sha256(distribution_path.read_bytes()).hexdigest(),
        "stage12_parquet_sha256": hashlib.sha256(parquet_path.read_bytes()).hexdigest(),
    }


def build_derived_manifest(
    source_manifest: dict[str, Any],
    identity: dict[str, Any],
    cohort_manifest: dict[str, Any],
    rows_by_scenario: dict[str, list[dict[str, Any]]],
    selected_by_scenario: dict[str, dict[str, int]],
    hashes_by_scenario: dict[str, dict[int, str]],
    source_evidence: dict[str, Any],
) -> dict[str, Any]:
    derived = copy.deepcopy(source_manifest)
    derived["manifest_version"] = "stage13-diagnostic-11005-v1"
    derived["manifest_status"] = "DERIVED_DIAGNOSTIC_ONLY_NOT_FINAL"
    derived["dataset_status"] = "DIAGNOSTIC_ONLY_NOT_FINAL"
    derived["validation_status"] = "SOURCE_IDENTITY_VERIFIED_DIAGNOSTIC_NOT_FINAL"
    derived["diagnostic_only"] = True
    derived["cohort_id"] = "STAGE13_DIAGNOSTIC_CANONICAL_11005_V1"
    derived["total_trials"] = sum(len(rows) for rows in rows_by_scenario.values())
    derived["global_manifest_sha256"] = cohort_manifest["global_aggregate_sha256"]
    derived["stage11_global_manifest_git_blob_sha"] = COHORT_MANIFEST_BLOB
    derived["source_manifest_git_blob_sha"] = SOURCE_MANIFEST_BLOB
    derived["dataset_identity_git_blob_sha"] = IDENTITY_BLOB
    derived["production_or_final_acceptance"] = False
    derived["historical_stage9a_total_trials"] = 9005
    derived["historical_stage9a_artifact_manifest"] = derived.pop("artifact_manifest", {})
    derived["historical_stage9a_block_fingerprints"] = derived.pop("block_fingerprints", {})
    derived["artifact_manifest"] = {
        "stage7_run_id": STAGE7_RUN,
        "stage10_run_id": STAGE10_RUN,
        "stage12_run_id": STAGE12_RUN,
        "scenario_sources": source_evidence,
    }
    derived["trial_fingerprints"] = {
        scenario: {str(trial_id): sha for trial_id, sha in hashes_by_scenario[scenario].items()}
        for scenario in EXPECTED_SCENARIOS
    }
    derived["representative_trials"] = {}
    for scenario in EXPECTED_SCENARIOS:
        rows = rows_by_scenario[scenario]
        selected = selected_by_scenario[scenario]
        rows_by_id = {int(row["trial_id"]): row for row in rows}
        scenario_identity = identity["per_scenario"][scenario]
        fingerprint = (
            scenario_identity["scenario_fingerprint_stage9a"]
            if scenario.startswith("C100_")
            else scenario_identity["combined_dataset_fingerprint_sha256_stage10"]
        )
        role_meta: dict[str, Any] = {
            "trial_count": len(rows),
            "is_deterministic": scenario.startswith("C100_"),
        }
        for role, trial_id in selected.items():
            role_meta[role] = int(trial_id)
            role_meta[f"{role}_value"] = int(rows_by_id[trial_id]["final_net_project_equity"])
        item = derived["scenarios"][scenario]
        item["trial_count"] = len(rows)
        item["scenario_fingerprint"] = fingerprint
        item["representative_trials"] = role_meta
        item["selected_role_ids"] = dict(selected)
        item["historical_stage9a_trial_count"] = int(source_manifest["scenarios"][scenario]["trial_count"])
        item["final_status"] = "DIAGNOSTIC_ONLY_NOT_FINAL"
        item["stable_at_n"] = None
        derived["representative_trials"][scenario] = dict(role_meta)
    derived["total_representatives"] = len(EXPECTED_SCENARIOS) * 5
    derived["source_artifacts"] = source_evidence
    derived["status_note"] = (
        "Derived diagnostic cohort from pinned Stage7/Stage10 TrialResult blocks and Stage12 daily data, "
        "rehashed against the Stage12 per-trial result_sha256 values. This temporary 11005 cohort is not "
        "the Stage9A 9005 baseline and is not final delivery or statistical acceptance."
    )
    return derived


def prepare_dataset(output_dataset: Path, manifest_out: Path, provenance_out: Path) -> dict[str, Any]:
    source_manifest_path = Path("docs/stage9a/dataset_manifest.json")
    identity_path = Path("docs/stage11/dataset_identity.json")
    cohort_manifest_path = Path("docs/stage11/global_manifest_11005_reconciled.json")
    roll_path = Path("docs/stage12/roll_forward_validation.json")
    closure_path = Path("docs/stage12/closure_settlement_validation.json")
    source_manifest = json.loads(source_manifest_path.read_text(encoding="utf-8"))
    identity = json.loads(identity_path.read_text(encoding="utf-8"))
    cohort_manifest = json.loads(cohort_manifest_path.read_text(encoding="utf-8"))
    roll = json.loads(roll_path.read_text(encoding="utf-8"))
    closure = json.loads(closure_path.read_text(encoding="utf-8"))

    source_blob = git_blob_sha(source_manifest_path.read_bytes())
    identity_blob = git_blob_sha(identity_path.read_bytes())
    cohort_blob = git_blob_sha(cohort_manifest_path.read_bytes())
    if source_blob != SOURCE_MANIFEST_BLOB:
        raise RuntimeError(f"STAGE9A_SOURCE_MANIFEST_BLOB_MISMATCH: {source_blob}")
    if identity_blob != IDENTITY_BLOB or cohort_blob != COHORT_MANIFEST_BLOB:
        raise RuntimeError("STAGE11_COHORT_IDENTITY_BLOB_MISMATCH")
    if source_manifest.get("total_trials") != 9005:
        raise RuntimeError("STAGE9A_SOURCE_MANIFEST_NOT_9005")
    if (
        cohort_manifest.get("total_trials_expected") != 11005
        or cohort_manifest.get("total_trials_evidenced") != 11005
        or identity.get("total_canonical_trials") != 11005
        or identity.get("scenarios_count") != 25
    ):
        raise RuntimeError("STAGE11_COHORT_NOT_11005")
    if cohort_manifest.get("global_aggregate_sha256") != GLOBAL_11005:
        raise RuntimeError("STAGE11_GLOBAL_AGGREGATE_MISMATCH")
    if source_manifest.get("source_sha") != SOURCE_SHA or source_manifest.get("master_seed") != MASTER_SEED:
        raise RuntimeError("STAGE9A_SOURCE_IDENTITY_MISMATCH")

    if output_dataset.exists():
        shutil.rmtree(output_dataset)
    output_dataset.mkdir(parents=True, exist_ok=True)
    sources: dict[str, Any] = {
        "stage7_run_id": STAGE7_RUN, "stage7_head_sha": STAGE7_HEAD,
        "stage10_run_id": STAGE10_RUN, "stage10_head_sha": STAGE10_HEAD,
        "stage12_run_id": STAGE12_RUN, "stage12_head_sha": STAGE12_HEAD,
        "stage9a_source_manifest_git_blob_sha": source_blob,
        "stage11_manifest_git_blob_sha": cohort_blob,
        "dataset_identity_git_blob_sha": identity_blob,
        "scenario_sources": {},
        "simulation_trials_or_checkpoints_run": False,
        "historical_dataset_modified": False,
    }
    artifacts7, api7 = gatea.artifact_index(STAGE7_RUN)
    artifacts10, api10 = gatea.artifact_index(STAGE10_RUN)
    artifacts12, api12 = gatea.artifact_index(STAGE12_RUN)
    sources["stage7_artifact_count"] = api7.get("total_count")
    sources["stage10_artifact_count"] = api10.get("total_count")
    sources["stage12_artifact_count"] = api12.get("total_count")

    rows_by_scenario: dict[str, list[dict[str, Any]]] = {}
    selected_by_scenario: dict[str, dict[str, int]] = {}
    hashes_by_scenario: dict[str, dict[int, str]] = {}
    total_daily_rows = 0
    with tempfile.TemporaryDirectory(prefix="stage13-11005-source-") as temporary:
        root = Path(temporary)
        for scenario in EXPECTED_SCENARIOS:
            count = 1 if scenario.startswith("C100_") else 550
            if scenario.startswith("C100_"):
                run_id, head_sha, index = STAGE7_RUN, STAGE7_HEAD, artifacts7
                artifact_name = f"stage7-blocks-{scenario}-1"
            else:
                run_id, head_sha, index = STAGE10_RUN, STAGE10_HEAD, artifacts10
                artifact_name = f"stage10-bench-{scenario}-1"
            trial_artifact = gatea.find_artifact(index, artifact_name, run_id)
            assert_artifact_run(trial_artifact, run_id, head_sha, scenario)
            trial_zip = root / f"{scenario}-trials.zip"
            trial_artifact_evidence = gatea.download_artifact(trial_artifact, trial_zip)
            rows, block_evidence, trial_hashes = maxcase_audit.rows_from_zip(
                scenario, trial_zip, source_manifest,
            )
            validate_rng_audit_rows(scenario, rows)
            if len(rows) != count or sorted(trial_hashes) != list(range(1, count + 1)):
                raise RuntimeError(f"PINNED_TRIAL_SOURCE_COVERAGE_MISMATCH: {scenario}")
            for row in rows:
                trial_id = int(row["trial_id"])
                if gatea.row_sha(row) != trial_hashes[trial_id]:
                    raise RuntimeError(f"TRIAL_ROW_SHA_RECONCILIATION_MISMATCH: {scenario}/{trial_id}")
            selected = select_representative_trial_ids(rows, scenario)
            if set(selected) != {"P10", "P50", "P90", "Loss", "Max Case"}:
                raise RuntimeError(f"REPRESENTATIVE_ROLE_COVERAGE_MISMATCH: {scenario}")
            for role, trial_id in selected.items():
                if type(trial_id) is not int or trial_id not in trial_hashes:
                    raise RuntimeError(f"REPRESENTATIVE_ROLE_TRIAL_ID_INVALID: {scenario}/{role}")
            rows_by_scenario[scenario] = rows
            selected_by_scenario[scenario] = selected
            hashes_by_scenario[scenario] = trial_hashes
            scenario_dir = output_dataset / scenario
            scenario_dir.mkdir(parents=True, exist_ok=True)
            pq.write_table(pa.Table.from_pylist(rows), scenario_dir / "trial_results.parquet", compression="zstd")

            stage12_artifact = gatea.find_artifact(artifacts12, f"stage12-daily-{scenario}", STAGE12_RUN)
            assert_artifact_run(stage12_artifact, STAGE12_RUN, STAGE12_HEAD, scenario)
            stage12_parquet, stage12_artifact_evidence = download_single_parquet(
                stage12_artifact, f"{scenario}.parquet", root,
            )
            comparisons, validation = gatea.validate_stage12(
                scenario, stage12_parquet, roll, closure, trial_hashes,
            )
            if (
                len(comparisons) != count
                or validation.get("mismatch_count") != 0
                or any(not item["exact_match"] for item in comparisons)
            ):
                raise RuntimeError(f"STAGE12_SOURCE_GOLDEN_MISMATCH: {scenario}")
            selected_daily, daily_report = process_stage12_daily(
                scenario, stage12_parquet, count, selected, scenario_dir, trial_hashes,
            )
            for role, filename in ROLE_FILES:
                trial_id = selected[role]
                summary = next(row for row in rows if int(row["trial_id"]) == trial_id)
                write_json(scenario_dir / "representatives" / f"{filename}.json", {
                    "summary": dict(summary),
                    "daily": selected_daily[trial_id],
                })
            total_daily_rows += int(validation["daily_rows"])
            sources["scenario_sources"][scenario] = {
                "trial_artifact_id": int(trial_artifact["id"]),
                "trial_artifact_name": artifact_name,
                "trial_artifact_run_id": run_id,
                "trial_artifact_head_sha": head_sha,
                "trial_artifact_zip_sha256": trial_artifact_evidence["artifact_zip_sha256"],
                "trial_count": count,
                "source_blocks": block_evidence,
                "trial_result_sha256_map": {str(k): v for k, v in trial_hashes.items()},
                "stage12_artifact_id": int(stage12_artifact["id"]),
                "stage12_artifact_zip_sha256": stage12_artifact_evidence["artifact_zip_sha256"],
                "stage12_validation": validation,
                "derived_daily_distribution": daily_report,
            }

    if sum(len(rows) for rows in rows_by_scenario.values()) != 11005 or total_daily_rows != EXPECTED_DAILY_ROWS:
        raise RuntimeError(
            f"CANONICAL_11005_SOURCE_TOTAL_MISMATCH: trials={sum(len(v) for v in rows_by_scenario.values())} "
            f"daily_rows={total_daily_rows}"
        )
    derived_manifest = build_derived_manifest(
        source_manifest, identity, cohort_manifest,
        rows_by_scenario, selected_by_scenario, hashes_by_scenario, sources,
    )
    write_json(manifest_out, derived_manifest)
    write_json(output_dataset / "representative_trial_ids.json", {
        "schema_version": "stage13-diagnostic-representative-trial-ids-v2",
        "source_manifest_git_blob_sha": source_blob,
        "cohort_manifest_git_blob_sha": cohort_blob,
        "scenario_count": len(rows_by_scenario),
        "total_trials": sum(len(v) for v in rows_by_scenario.values()),
        "scenarios": selected_by_scenario,
        "diagnostic_only": True,
        "production_or_release_acceptance": False,
    })
    report = {
        "schema_version": "stage13-diagnostic-11005-cohort-preparation-v1",
        "source_manifest_git_blob_sha": source_blob,
        "dataset_identity_git_blob_sha": identity_blob,
        "cohort_manifest_git_blob_sha": cohort_blob,
        "derived_manifest_sha256": hashlib.sha256(manifest_out.read_bytes()).hexdigest(),
        "dataset_path": str(output_dataset),
        "scenario_count": len(rows_by_scenario),
        "trial_count": sum(len(v) for v in rows_by_scenario.values()),
        "trial_counts_by_scenario": {s: len(v) for s, v in rows_by_scenario.items()},
        "stage12_daily_rows_validated": total_daily_rows,
        "all_stage12_trial_hashes_match_source_golden": True,
        "all_five_role_ids_computed_from_11005_cohort": True,
        "source_artifacts": sources,
        "simulation_trials_or_checkpoints_run": False,
        "historical_source_artifacts_modified": False,
        "historical_dataset_modified": False,
        "production_or_release_acceptance": False,
    }
    write_json(provenance_out, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dataset", required=True)
    parser.add_argument("--manifest-out", required=True)
    parser.add_argument("--provenance-out", required=True)
    args = parser.parse_args()
    result = prepare_dataset(Path(args.output_dataset), Path(args.manifest_out), Path(args.provenance_out))
    print(json.dumps({
        "scenario_count": result["scenario_count"],
        "trial_count": result["trial_count"],
        "stage12_daily_rows_validated": result["stage12_daily_rows_validated"],
        "all_stage12_trial_hashes_match_source_golden": True,
        "simulation_trials_or_checkpoints_run": False,
        "production_or_release_acceptance": False,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
