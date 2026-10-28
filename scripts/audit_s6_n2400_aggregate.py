from __future__ import annotations
import hashlib, json, os
from pathlib import Path
from typing import Any
import pyarrow.parquet as pq
import monte_carlo
from scripts import s6_first_checkpoint as s6

SOURCE_RUN_ID = "40731224990"
SOURCE_RUN_HEAD_SHA = "a23ba71f48487f3ebead99bc30039b14ef9b7609"
AGGREGATE_RUN_ID = "40753615920"
AGGREGATE_TESTED_SHA = "66cb1eb8bced40657642b6d234596c2e5b4efdd1"
SOURCE_SHA = "da1a9ea9b5cd789c944de3f07b08395bb67c49e7"
COHORT_ID = "s6-v23-da1a9ea9"
MASTER_SEED = 20270101
CHECKPOINT_N = 2400
EXPECTED_SCENARIOS = sorted(s6.stochastic_scenario_ids())

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()

def row_digest(path: Path) -> tuple[int, str]:
    pf = pq.ParquetFile(path)
    h = hashlib.sha256()
    for batch in pf.iter_batches(batch_size=8192):
        for row in batch.to_pylist():
            h.update(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode())
            h.update(b"\n")
    return int(pf.metadata.num_rows), h.hexdigest()

def reject_floats(value: Any, path: str = "$") -> None:
    if isinstance(value, float):
        raise RuntimeError(f"FLOAT_FOUND_IN_EXACT_NUMBER_REGISTRY:{path}")
    if isinstance(value, dict):
        for k, v in value.items(): reject_floats(v, f"{path}.{k}")
    elif isinstance(value, list):
        for i, v in enumerate(value): reject_floats(v, f"{path}[{i}]")

def stream_daily_path_fingerprints(path: Path, scenario: str) -> tuple[int, dict[int, str], list[str]]:
    """Recompute full daily-path hashes with bounded memory, preserving canonical row semantics."""
    parquet = pq.ParquetFile(path)
    columns = parquet.schema_arrow.names
    fingerprints: dict[int, str] = {}
    current_trial_id: int | None = None
    current_rows: list[dict[str, Any]] = []
    previous_trial_id: int | None = None

    def finish_path(trial_id: int, rows: list[dict[str, Any]]) -> None:
        rows.sort(key=lambda row: str(row["date"]))
        payload = chr(10).join(json.dumps(row, ensure_ascii=False, sort_keys=True,
                            separators=(",", ":"), default=str) for row in rows)
        fingerprints[trial_id] = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    for batch in parquet.iter_batches(batch_size=8192):
        for row in batch.to_pylist():
            if row.get("schema_version") != "v2.3" or row.get("source_sha") != SOURCE_SHA or row.get("cohort_id") != COHORT_ID:
                raise RuntimeError(f"SOURCE_DAILY_SNAPSHOT_SCHEMA_OR_IDENTITY_MISMATCH:{scenario}")
            if str(row.get("scenario_id")) != scenario:
                raise RuntimeError(f"SOURCE_DAILY_SNAPSHOT_SCENARIO_MISMATCH:{scenario}")
            trial_id = int(row["trial_id"])
            if previous_trial_id is not None and trial_id < previous_trial_id:
                raise RuntimeError(f"DAILY_SNAPSHOT_ROWS_NOT_ORDERED_BY_TRIAL_ID:{scenario}")
            if current_trial_id is None:
                current_trial_id = trial_id
            elif trial_id != current_trial_id:
                finish_path(current_trial_id, current_rows)
                current_trial_id = trial_id
                current_rows = []
            clean = {key: value for key, value in row.items()
                     if key not in {"trial_id", "scenario_id", "source_sha", "cohort_id", "schema_version"}}
            current_rows.append(clean)
            previous_trial_id = trial_id
    if current_trial_id is not None:
        finish_path(current_trial_id, current_rows)
    return int(parquet.metadata.num_rows), fingerprints, columns


def main() -> int:
    root = Path(os.environ.get("AUDIT_INPUT_ROOT", "audit-input"))
    aggregate_manifests = list(root.joinpath("aggregate").rglob("manifest.json"))
    scenario_manifests = sorted(root.joinpath("scenarios").rglob("scenario_manifest.json"), key=lambda path: str(json.loads(path.read_text(encoding="utf-8")).get("scenario_id", "")))
    if len(aggregate_manifests) != 1: raise RuntimeError(f"AGGREGATE_MANIFEST_COUNT_INVALID:{len(aggregate_manifests)}")
    if len(scenario_manifests) != 20: raise RuntimeError(f"SOURCE_SCENARIO_MANIFEST_COUNT_INVALID:{len(scenario_manifests)}")
    agg_dir = aggregate_manifests[0].parent
    m = json.loads(aggregate_manifests[0].read_text(encoding="utf-8"))
    identity = {
        "schema_version": "s6-cumulative-aggregate-v2", "status": "EXECUTED", "exit_code": 0,
        "source_sha": SOURCE_SHA, "cohort_id": COHORT_ID, "master_seed": MASTER_SEED,
        "checkpoint_n": CHECKPOINT_N, "source_run_id": SOURCE_RUN_ID, "source_run_attempt": 1,
        "run_id": AGGREGATE_RUN_ID, "git_commit": AGGREGATE_TESTED_SHA, "scenario_count": 20,
        "total_scenario_combinations": 25, "c100_reused_scenario_count": 5,
    }
    for key, expected in identity.items():
        if m.get(key) != expected: raise RuntimeError(f"AGGREGATE_IDENTITY_MISMATCH:{key}:{m.get(key)}")
    aggregate_file_checks = {}
    for name, expected in m.get("files", {}).items():
        p = agg_dir / name
        if not p.is_file(): raise RuntimeError(f"AGGREGATE_FILE_MISSING:{name}")
        sha, size = sha256_file(p), p.stat().st_size
        if sha != expected.get("sha256") or size != expected.get("size_bytes"):
            raise RuntimeError(f"AGGREGATE_FILE_HASH_OR_SIZE_MISMATCH:{name}")
        aggregate_file_checks[name] = {"sha256": sha, "size_bytes": size}

    # These five deterministic C100 scenarios are a different accepted cohort and must be reused read-only.
    c100 = json.loads((agg_dir / "c100_reuse.json").read_text(encoding="utf-8"))
    expected_c100 = ["C100_G100", "C100_G070", "C100_G050", "C100_G030", "C100_G000"]
    c100_identity = {
        "status": "REUSED_READ_ONLY",
        "run_id": 40263424595,
        "rerun": False,
        "source_sha": "965281d52441cd0d4b744e211c9f68ee4cdc3753",
        "cohort_id": "c100-v23-s4-20261026-965281d5",
        "golden_sha256": "39950d91c3b40b11bea0997b8504ac932a57bcc0ef8e0c51e12d031342a53327",
        "manifest_sha256": "2097284d77ead6b00492bf75830d09aeef8dbde4aaa1c15dae6a877dc7e9ff04",
        "trial_count_per_scenario": 300,
        "n_unique_paths": 1,
        "degeneracy_status": "DEGENERATE_DETERMINISTIC",
        "G_status": "G_INERT",
    }
    for key, expected in c100_identity.items():
        if c100.get(key) != expected:
            raise RuntimeError(f"C100_READ_ONLY_REUSE_IDENTITY_MISMATCH:{key}:{c100.get(key)}")
    if c100.get("scenario_ids") != expected_c100:
        raise RuntimeError(f"C100_SCENARIO_COVERAGE_INVALID:{c100.get('scenario_ids')}")
    if m.get("scenario_count") != 20 or m.get("c100_reused_scenario_count") != 5 or m.get("total_scenario_combinations") != 25:
        raise RuntimeError("COMPLETE_25_SCENARIO_COVERAGE_INVALID")

    scenarios = {};
    digest_trials = hashlib.sha256()
    digest_daily = hashlib.sha256()
    # Match aggregate writer order: sorted scenario, source Parquet rows in stored order.
    ordered_dirs = {}
    for mp in scenario_manifests:
        sm = json.loads(mp.read_text(encoding="utf-8"))
        scenario = str(sm.get("scenario_id", ""))
        if scenario not in EXPECTED_SCENARIOS or scenario in scenarios:
            raise RuntimeError(f"SOURCE_SCENARIO_IDENTITY_OR_DUPLICATE_INVALID:{scenario}")
        checks = {
            "source_sha": SOURCE_SHA, "cohort_id": COHORT_ID, "master_seed": MASTER_SEED,
            "run_id": SOURCE_RUN_ID, "run_attempt": 1, "trial_count": CHECKPOINT_N,
            "trial_id_start": 1, "trial_id_end": CHECKPOINT_N,
            "schema_version": "s6-first-checkpoint-v1", "git_commit": SOURCE_RUN_HEAD_SHA,
        }
        for key, expected in checks.items():
            if sm.get(key) != expected: raise RuntimeError(f"SOURCE_MANIFEST_IDENTITY_MISMATCH:{scenario}:{key}")
        folder = mp.parent
        file_checks = {}
        for name, expected in sm.get("files", {}).items():
            p = folder / name
            if not p.is_file(): raise RuntimeError(f"SOURCE_FILE_MISSING:{scenario}:{name}")
            sha, size = sha256_file(p), p.stat().st_size
            if sha != expected.get("sha256") or size != expected.get("size_bytes"):
                raise RuntimeError(f"SOURCE_FILE_HASH_OR_SIZE_MISMATCH:{scenario}:{name}")
            file_checks[name] = {"sha256": sha, "size_bytes": size}
        trial_path, daily_path = folder / "trials_summary.parquet", folder / "daily_distribution.parquet"
        snapshots_path = folder / "daily_snapshots.parquet"
        if pq.ParquetFile(trial_path).metadata.num_rows != CHECKPOINT_N:
            raise RuntimeError(f"SOURCE_TRIAL_ROW_COUNT_MISMATCH:{scenario}")
        rows = pq.read_table(trial_path).to_pylist()
        ids = [int(row["trial_id"]) for row in rows]
        s6.validate_cumulative_trial_ids(ids, CHECKPOINT_N, scenario_id=scenario)
        if any(str(row.get("scenario_id")) != scenario for row in rows):
            raise RuntimeError(f"SOURCE_TRIAL_SCENARIO_COLUMN_MISMATCH:{scenario}")
        if any(row.get("schema_version") != "v2.3" or row.get("source_sha") != SOURCE_SHA or row.get("cohort_id") != COHORT_ID for row in rows):
            raise RuntimeError(f"SOURCE_TRIAL_ROW_SCHEMA_OR_IDENTITY_MISMATCH:{scenario}")
        for row in rows:
            fp = monte_carlo.trial_fingerprint(s6.result_from_record(row))
            if row.get("trial_fingerprint") != fp:
                raise RuntimeError(f"FINANCIAL_FINGERPRINT_RECOMPUTE_MISMATCH:{scenario}:{row['trial_id']}")
        s6.validate_cumulative_rng_audit(rows, SOURCE_SHA)
        snapshot_rows, daily_paths, snapshot_columns = stream_daily_path_fingerprints(snapshots_path, scenario)
        if set(daily_paths) != set(range(1, CHECKPOINT_N + 1)):
            raise RuntimeError(f"DAILY_PATH_TRIAL_COVERAGE_MISMATCH:{scenario}")
        unique_paths = len(set(daily_paths.values()))
        if sm.get("unique_daily_paths", unique_paths) != unique_paths or sm.get("n_unique_paths", unique_paths) != unique_paths:
            raise RuntimeError(f"UNIQUE_DAILY_PATH_COUNT_MISMATCH:{scenario}")
        trial_rows, trial_sha = row_digest(trial_path)
        daily_rows, daily_sha = row_digest(daily_path)
        for parquet_path, digest in ((trial_path, digest_trials), (daily_path, digest_daily)):
            for batch in pq.ParquetFile(parquet_path).iter_batches(batch_size=8192):
                for row in batch.to_pylist():
                    digest.update(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str).encode())
                    digest.update(bytes([10]))
        scenarios[scenario] = {
            "trial_rows": trial_rows, "trial_row_sha256": trial_sha,
            "daily_distribution_rows": daily_rows, "daily_row_sha256": daily_sha,
            "daily_snapshots_rows": snapshot_rows,
            "daily_path_coverage": len(daily_paths), "unique_daily_paths": unique_paths,
            "rng_records_verified": len(rows), "scenario_manifest_sha256": sha256_file(mp),
            "files": file_checks,
            "daily_balance_columns_available": {"Total_Assets","Total_Equity"}.issubset(snapshot_columns),
        }
        ordered_dirs[scenario] = folder

    if set(scenarios) != set(EXPECTED_SCENARIOS): raise RuntimeError("SOURCE_SCENARIO_SET_NOT_EXACT")
    if sum(int(x["n_total"]) for x in m["scenario_summaries"]) != 48_000: raise RuntimeError("AGGREGATE_TRIAL_ROW_SUM_INVALID")
    trial_rows, trial_sha = row_digest(agg_dir / "trials_summary.parquet")
    daily_rows, daily_sha = row_digest(agg_dir / "daily_distribution.parquet")
    if trial_rows != 48_000 or digest_trials.hexdigest() != trial_sha:
        raise RuntimeError("AGGREGATE_TRIAL_ROWS_DIFFER_FROM_SOURCE_ROWS")
    if sum(x["daily_distribution_rows"] for x in scenarios.values()) != daily_rows or digest_daily.hexdigest() != daily_sha:
        raise RuntimeError("AGGREGATE_DAILY_ROWS_DIFFER_FROM_SOURCE_ROWS")

    registry = json.loads((agg_dir / "number_registry.json").read_text(encoding="utf-8"))
    reject_floats(registry)
    entries = registry.get("entries", [])
    if len(entries) != 960: raise RuntimeError(f"NUMBER_REGISTRY_COUNT_INVALID:{len(entries)}")
    for item in entries:
        if type(item.get("exact_numerator")) is not int or type(item.get("exact_denominator")) is not int or int(item["exact_denominator"]) <= 0:
            raise RuntimeError("NUMBER_REGISTRY_EXACT_FRACTION_INVALID")
        if not str(item.get("source", "")).startswith(f"{SOURCE_SHA}/{COHORT_ID}/"):
            raise RuntimeError("NUMBER_REGISTRY_SOURCE_IDENTITY_INVALID")
    stats = json.loads((agg_dir / "statistical_evaluation.json").read_text(encoding="utf-8"))
    checkpoints = [300, 600, 1200, 2400]
    counts = stats.get("checkpoint_gate_b_counts", {})
    if set(counts) != {str(x) for x in checkpoints} or any(sum(c.values()) != 20 for c in counts.values()):
        raise RuntimeError("STATISTICAL_CHECKPOINT_COVERAGE_INVALID")
    if stats.get("transition_count") != 60 or stats.get("successful_transition_count") != 0:
        raise RuntimeError("STATISTICAL_TRANSITION_AUDIT_INVALID")
    if stats.get("gate_a_final") != "NOT_EVALUATED_NO_SAME_SOURCE_PRODUCTION_GOLDEN" or stats.get("scenario_stability_final") != "NOT_CONVERGED":
        raise RuntimeError("FAIL_CLOSED_GATE_STATUS_INVALID")
    balance_columns = all(x["daily_balance_columns_available"] for x in scenarios.values())
    audit = {
        "schema_version": "s6-n2400-independent-artifact-audit-v1", "status": "PASS_SCOPED",
        "source_run_id": SOURCE_RUN_ID, "source_run_head_sha": SOURCE_RUN_HEAD_SHA,
        "aggregate_run_id": AGGREGATE_RUN_ID, "aggregate_tested_sha": AGGREGATE_TESTED_SHA,
        "aggregate_artifact_sha256": "b9ff1bb14fcaf57a60cbd645ce6ef3aa9b9843061852c6798a89708c64c32580",
        "source_sha": SOURCE_SHA, "cohort_id": COHORT_ID, "model_schema_version": "v2.3",
        "master_seed": MASTER_SEED, "checkpoint_n": CHECKPOINT_N, "scenario_count": len(scenarios),
        "stochastic_scenario_ids": sorted(scenarios),
        "deterministic_c100_scenario_ids_read_only": c100["scenario_ids"],
        "total_scenario_combinations": len(scenarios) + len(c100["scenario_ids"]),
        "c100_reuse_verified_read_only": True,
        "trial_rows": trial_rows, "daily_distribution_rows": daily_rows,
        "scenario_artifacts": scenarios, "aggregate_files": aggregate_file_checks,
        "row_by_row_canonical_digest_match": True, "financial_trial_fingerprints_recomputed": True,
        "rng_audit_records_verified": 48_000, "number_registry_entries": len(entries),
        "number_registry_exact_fraction_and_no_float_check": "PASS",
        "gate_a": stats["gate_a_final"], "gate_b_point_counts": counts,
        "gate_b_final": m["acceptance_status"]["gate_b"], "stability": stats["scenario_stability_final"],
        "successful_transitions": stats["successful_transition_count"],
        "daily_balance_independent_recheck": "READY_FOR_RECHECK" if balance_columns else "MISSING_EVIDENCE_FOR_INDEPENDENT_RECHECK",
        "source_run_metadata_sha256": m.get("source_run_metadata", {}).get("sha256"),
        "source_run_metadata_gap": "NONE" if m.get("source_run_metadata", {}).get("sha256") else "MISSING_EVIDENCE_SOURCE_RUN_METADATA_FILE_NOT_PINNED",
    }
    out = Path("audit-output")
    out.mkdir(parents=True, exist_ok=True)
    (out / "S6_N2400_INDEPENDENT_AUDIT.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# S6 N=2400 Independent Artifact Audit", "",
        f"- Status: {audit['status']}",
        f"- Source run / tested SHA: {SOURCE_RUN_ID} / {SOURCE_RUN_HEAD_SHA}",
        f"- Aggregate run / tested SHA: {AGGREGATE_RUN_ID} / {AGGREGATE_TESTED_SHA}",
        f"- SOURCE_SHA / cohort / seed: {SOURCE_SHA} / {COHORT_ID} / {MASTER_SEED}",
        f"- Coverage: {len(scenarios)} stochastic + {len(c100[\"scenario_ids\"])} C100 read-only = {len(scenarios) + len(c100[\"scenario_ids\"])} combinations.",
        f"- Trial rows: {trial_rows:,}; daily distribution rows: {daily_rows:,}",
        "- Canonical digest of all source scenario trial rows equals the aggregate table.",
        "- Canonical digest of all source scenario daily-distribution rows equals the aggregate table.",
        "- Recomputed each persisted financial trial fingerprint and validated RNG audit records.",
        "- Checked file hashes, Parquet footer counts, exact number registry fractions, and absence of float values.",
        f"- Gate A: {audit['gate_a']}; Gate B: {audit['gate_b_final']}; stability: {audit['stability']}.",
        f"- Daily Assets==Equity independent post-write recheck: {audit['daily_balance_independent_recheck']}.",
        f"- Source run metadata SHA pin: {audit['source_run_metadata_gap']}.",
        "", "Scoped integrity evidence only; this report does not grant Gate A/B acceptance or CONVERGED status."
    ]
    (out / "S6_N2400_INDEPENDENT_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k:audit[k] for k in ("status","trial_rows","daily_distribution_rows","row_by_row_canonical_digest_match","financial_trial_fingerprints_recomputed","number_registry_entries","gate_a","gate_b_final","stability","daily_balance_independent_recheck","source_run_metadata_gap")}, ensure_ascii=False, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
