from __future__ import annotations
import hashlib, json, os, subprocess, time
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import constants, monte_carlo, validation
from scripts import s6_first_checkpoint as s6
from scripts.s5_mini_verification import build_exact_daily_distribution

SOURCE_SHA = "da1a9ea9b5cd789c944de3f07b08395bb67c49e7"
COHORT_ID = "s6-v23-da1a9ea9"
REFERENCE_SHA256 = "e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f"
TRIAL_COUNT = 2400
SCENARIOS = ("C100_G100", "C100_G070", "C100_G050", "C100_G030", "C100_G000")
MODEL_PATHS = ("constants.py", "dateutils.py", "daily_engine.py", "entities.py",
               "monte_carlo.py", "rng.py", "validation.py", "stats_integrity.py")

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()

def verify_source_lock() -> dict[str, str]:
    if constants.MASTER_SEED != 20270101:
        raise RuntimeError("C100_MASTER_SEED_MISMATCH")
    reference = Path("المرجع_النهائي_الموحد_v2.3-إعادة_صياغة.md")
    if not reference.is_file() or sha256_file(reference) != REFERENCE_SHA256:
        raise RuntimeError("C100_NORMATIVE_REFERENCE_SHA256_MISMATCH")
    tested_sha = git("rev-parse", "HEAD")
    if tested_sha != os.environ.get("GITHUB_SHA"):
        raise RuntimeError("C100_TESTED_SHA_CONTEXT_MISMATCH")
    if os.environ.get("GITHUB_REF") != "refs/heads/tmp/s6-c100-current-source-da1a-20261028":
        raise RuntimeError("C100_UNEXPECTED_BRANCH")
    remote = git("ls-remote", "origin", os.environ["GITHUB_REF"]).split()
    if not remote or remote[0] != tested_sha:
        raise RuntimeError("C100_STALE_WORKFLOW_COMMIT")
    source_lines = git("ls-tree", "-r", "--format=%(objectname) %(path)", SOURCE_SHA).splitlines()
    tested_lines = git("ls-tree", "-r", "--format=%(objectname) %(path)", "HEAD").splitlines()
    def as_map(lines: list[str]) -> dict[str, str]:
        out = {}
        for line in lines:
            blob, path = line.split(" ", 1)
            out[path] = blob
        return out
    source_map, tested_map = as_map(source_lines), as_map(tested_lines)
    mismatches = [p for p in MODEL_PATHS if source_map.get(p) != tested_map.get(p) or p not in source_map]
    if mismatches:
        raise RuntimeError(f"C100_MODEL_SOURCE_BLOB_LOCK_MISMATCH:{mismatches}")
    return {p: source_map[p] for p in MODEL_PATHS}

def canonical_fingerprint_map_sha256(scenario: str, values: dict[str, str]) -> str:
    payload = "".join(f"{scenario}|{tid}|{values[tid]}\n" for tid in sorted(values, key=int))
    return sha256_text(payload)

def run_scenario(scenario: str, output_root: Path, workers: int = 2) -> dict[str, Any]:
    started = time.monotonic()
    source_blobs = verify_source_lock()
    if scenario not in SCENARIOS:
        raise RuntimeError(f"C100_UNEXPECTED_SCENARIO:{scenario}")
    trial_ids = list(range(1, TRIAL_COUNT + 1))
    results, daily_by_trial = s6.run_full_trials(scenario, trial_ids, SOURCE_SHA, workers)
    if set(results) != set(trial_ids) or set(daily_by_trial) != set(trial_ids):
        raise RuntimeError(f"C100_TRIAL_OR_DAILY_COVERAGE_MISMATCH:{scenario}")
    ordered = [results[tid] for tid in trial_ids]
    if [r.trial_id for r in ordered] != trial_ids:
        raise RuntimeError(f"C100_TRIAL_ID_SEQUENCE_MISMATCH:{scenario}")
    if any(r.scenario_id != scenario for r in ordered):
        raise RuntimeError(f"C100_SCENARIO_IDENTITY_MISMATCH:{scenario}")
    validation.validate_rng_audit_records(
        [asdict(r) for r in ordered], source_sha=SOURCE_SHA, master_seed=20270101,
        require_audit_fingerprint=True,
    )
    if any(int(r.rng_draw_count) != 0 or int(r.rng_checksum) != 0 for r in ordered):
        raise RuntimeError(f"C100_UNEXPECTED_RNG_DRAWS:{scenario}")
    output = output_root / scenario
    output.mkdir(parents=True, exist_ok=True)
    trial_rows = [s6.result_record(results[tid], SOURCE_SHA, COHORT_ID, None) for tid in trial_ids]
    snapshot_rows = [
        s6.snapshot_record(row, scenario, SOURCE_SHA, COHORT_ID)
        for tid in trial_ids
        for row in sorted(daily_by_trial[tid], key=lambda item: str(item["date"]))
    ]
    paths = s6.daily_path_fingerprints(snapshot_rows)
    if set(paths) != set(trial_ids):
        raise RuntimeError(f"C100_DAILY_PATH_COVERAGE_MISMATCH:{scenario}")
    financial = {str(tid): monte_carlo.trial_fingerprint(results[tid]) for tid in trial_ids}
    daily_path_map = {str(tid): paths[tid] for tid in trial_ids}
    if len(set(financial.values())) != 1 or len(set(daily_path_map.values())) != 1:
        raise RuntimeError(f"C100_NOT_DETERMINISTIC:{scenario}")
    if len(set(paths.values())) != 1:
        raise RuntimeError(f"C100_N_UNIQUE_PATHS_NOT_ONE:{scenario}")

    os.environ["S5_TRIAL_COUNT"] = str(TRIAL_COUNT)
    distribution = build_exact_daily_distribution(ordered, daily_by_trial, scenario, COHORT_ID, SOURCE_SHA)
    parquet = {
        "trials_summary.parquet": trial_rows,
        "daily_snapshots.parquet": snapshot_rows,
        "daily_distribution.parquet": distribution,
    }
    for name, rows in parquet.items():
        pq.write_table(pa.Table.from_pylist(rows), output / name, compression="zstd")
    s6.write_json(output / "financial_trial_fingerprints.json", {
        "schema_version": "s6-c100-fingerprint-map-v1", "source_sha": SOURCE_SHA,
        "cohort_id": COHORT_ID, "scenario_id": scenario, "trial_id_start": 1,
        "trial_id_end": TRIAL_COUNT, "trial_count": TRIAL_COUNT,
        "trial_fingerprints": financial,
        "map_sha256": canonical_fingerprint_map_sha256(scenario, financial),
    })
    s6.write_json(output / "daily_path_fingerprints.json", {
        "schema_version": "s6-c100-daily-path-map-v1", "source_sha": SOURCE_SHA,
        "cohort_id": COHORT_ID, "scenario_id": scenario, "trial_id_start": 1,
        "trial_id_end": TRIAL_COUNT, "trial_count": TRIAL_COUNT,
        "path_fingerprints": daily_path_map,
        "map_sha256": canonical_fingerprint_map_sha256(scenario, daily_path_map),
        "unique_daily_paths": len(set(daily_path_map.values())),
    })
    names = (*parquet.keys(), "financial_trial_fingerprints.json", "daily_path_fingerprints.json")
    files = {name: {"sha256": sha256_file(output / name), "size_bytes": (output / name).stat().st_size}
             for name in names}
    n_closed = sum(r.final_close_date is not None for r in ordered)
    manifest = {
        "schema_version": "s6-first-checkpoint-v1",
        "status": "EXECUTED_DETERMINISTIC_REPRODUCIBILITY_NOT_GATE_A_APPROVAL",
        "scenario_id": scenario, "source_sha": SOURCE_SHA, "cohort_id": COHORT_ID,
        "master_seed": 20270101, "schema_version_model": "v2.3",
        "git_commit": SOURCE_SHA, "tested_sha": os.environ.get("GITHUB_SHA"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": int(os.environ.get("GITHUB_RUN_ATTEMPT", "1")),
        "trial_id_start": 1, "trial_id_end": TRIAL_COUNT, "trial_count": TRIAL_COUNT,
        "n_total": TRIAL_COUNT, "n_closed": n_closed, "n_censored": TRIAL_COUNT - n_closed,
        "rng_draw_count_zero_rows": TRIAL_COUNT, "rng_checksum_zero_rows": TRIAL_COUNT,
        "rng_audit_validation": {"status": "PASS", "records_verified": TRIAL_COUNT},
        "n_unique_paths": 1, "unique_daily_paths": 1, "unique_financial_fingerprints": 1,
        "opt1_policy": "C100_DETERMINISTIC_REPRODUCIBILITY_FULL_RUN",
        "workers": workers, "elapsed_seconds": time.monotonic() - started,
        "reference_sha256": REFERENCE_SHA256, "source_model_blobs": source_blobs,
        "production_result_artifacts_read": False, "files": files,
    }
    s6.write_json(output / "scenario_manifest.json", manifest)
    return {"scenario_id": scenario, "trial_count": TRIAL_COUNT, "n_unique_paths": 1,
            "n_unique_financial_fingerprints": 1, "files": files,
            "manifest_sha256": sha256_file(output / "scenario_manifest.json")}

def aggregate(input_root: Path, output_root: Path) -> dict[str, Any]:
    verify_source_lock()
    manifests = sorted(input_root.rglob("scenario_manifest.json"))
    if len(manifests) != len(SCENARIOS):
        raise RuntimeError(f"C100_SCENARIO_MANIFEST_COUNT_INVALID:{len(manifests)}")
    by_scenario = {}
    for mp in manifests:
        m = json.loads(mp.read_text(encoding="utf-8"))
        scenario = m.get("scenario_id")
        if scenario not in SCENARIOS or scenario in by_scenario:
            raise RuntimeError(f"C100_SCENARIO_DUPLICATE_OR_UNEXPECTED:{scenario}")
        expected = {
            "schema_version": "s6-first-checkpoint-v1", "status": "EXECUTED_DETERMINISTIC_REPRODUCIBILITY_NOT_GATE_A_APPROVAL",
            "source_sha": SOURCE_SHA, "cohort_id": COHORT_ID, "master_seed": 20270101,
            "schema_version_model": "v2.3", "trial_id_start": 1, "trial_id_end": TRIAL_COUNT,
            "trial_count": TRIAL_COUNT, "n_total": TRIAL_COUNT, "n_unique_paths": 1,
            "unique_daily_paths": 1, "unique_financial_fingerprints": 1,
            "run_id": os.environ.get("GITHUB_RUN_ID"),
        }
        for key, value in expected.items():
            if m.get(key) != value:
                raise RuntimeError(f"C100_MANIFEST_IDENTITY_OR_PATH_COUNT_MISMATCH:{scenario}:{key}")
        folder = mp.parent
        for name, entry in m.get("files", {}).items():
            p = folder / name
            if not p.is_file() or p.stat().st_size != entry.get("size_bytes") or sha256_file(p) != entry.get("sha256"):
                raise RuntimeError(f"C100_FILE_HASH_OR_SIZE_MISMATCH:{scenario}:{name}")
        trial_path = folder / "trials_summary.parquet"
        if pq.ParquetFile(trial_path).metadata.num_rows != TRIAL_COUNT:
            raise RuntimeError(f"C100_PARQUET_ROW_COUNT_MISMATCH:{scenario}")
        ids = [int(x["trial_id"]) for x in pq.read_table(trial_path, columns=["trial_id"]).to_pylist()]
        s6.validate_cumulative_trial_ids(ids, TRIAL_COUNT, scenario_id=scenario)
        fm = json.loads((folder / "financial_trial_fingerprints.json").read_text(encoding="utf-8"))
        pm = json.loads((folder / "daily_path_fingerprints.json").read_text(encoding="utf-8"))
        if set(fm.get("trial_fingerprints", {})) != {str(i) for i in range(1, TRIAL_COUNT + 1)}:
            raise RuntimeError(f"C100_FINANCIAL_MAP_COVERAGE_INVALID:{scenario}")
        if set(pm.get("path_fingerprints", {})) != {str(i) for i in range(1, TRIAL_COUNT + 1)}:
            raise RuntimeError(f"C100_DAILY_PATH_MAP_COVERAGE_INVALID:{scenario}")
        by_scenario[scenario] = (folder, m, fm, pm)
    if set(by_scenario) != set(SCENARIOS):
        raise RuntimeError("C100_SCENARIO_SET_NOT_EXACT")
    base_f = by_scenario["C100_G100"][2]["trial_fingerprints"]
    base_p = by_scenario["C100_G100"][3]["path_fingerprints"]
    for scenario in SCENARIOS:
        f_map = by_scenario[scenario][2]["trial_fingerprints"]
        p_map = by_scenario[scenario][3]["path_fingerprints"]
        if f_map != base_f or p_map != base_p:
            raise RuntimeError(f"C100_G_LEVEL_CHANGED_FINANCIAL_OR_DAILY_PATH_MAP:{scenario}")
    output_root.mkdir(parents=True, exist_ok=True)
    scenario_summary = []
    combined = {"schema_version": "s6-c100-current-source-combined-map-v1",
                "source_sha": SOURCE_SHA, "cohort_id": COHORT_ID, "master_seed": 20270101,
                "trial_count": TRIAL_COUNT, "scenario_count": 5, "scenarios": {}}
    for scenario in SCENARIOS:
        folder, manifest, fm, pm = by_scenario[scenario]
        scenario_summary.append({
            "scenario_id": scenario, "run_id": manifest["run_id"], "run_attempt": manifest["run_attempt"],
            "trial_count": TRIAL_COUNT, "n_unique_paths": 1,
            "scenario_manifest_sha256": sha256_file(folder / "scenario_manifest.json"),
            "files": manifest["files"],
        })
        combined["scenarios"][scenario] = {
            "financial_trial_fingerprints": fm["trial_fingerprints"],
            "daily_path_fingerprints": pm["path_fingerprints"],
        }
    s6.write_json(output_root / "c100_current_source_combined_maps.json", combined)
    s6.write_json(output_root / "c100_current_source_manifest.json", {
        "schema_version": "s6-c100-current-source-aggregate-v1",
        "status": "EXECUTED_DETERMINISTIC_REPRODUCIBILITY_NOT_GATE_A_APPROVAL",
        "source_sha": SOURCE_SHA, "cohort_id": COHORT_ID, "master_seed": 20270101,
        "model_schema_version": "v2.3", "tested_sha": os.environ.get("GITHUB_SHA"),
        "run_id": os.environ.get("GITHUB_RUN_ID"),
        "run_attempt": int(os.environ.get("GITHUB_RUN_ATTEMPT", "1")),
        "scenario_count": 5, "scenario_ids": list(SCENARIOS),
        "trial_count_per_scenario": TRIAL_COUNT, "total_trial_rows": 5 * TRIAL_COUNT,
        "n_unique_paths_per_scenario": 1, "all_trial_ids_contiguous": True,
        "all_rng_draw_counts_zero": True, "all_rng_checksums_zero": True,
        "financial_fingerprint_maps_equal_across_g": True,
        "daily_path_fingerprint_maps_equal_across_g": True,
        "production_artifacts_read": False, "historical_c100_artifacts_modified": False,
        "reference_sha256": REFERENCE_SHA256, "scenarios": scenario_summary,
    })
    files = {name: {"sha256": sha256_file(output_root / name), "size_bytes": (output_root / name).stat().st_size}
             for name in ("c100_current_source_manifest.json", "c100_current_source_combined_maps.json")}
    summary = {"status": "EXECUTED_DETERMINISTIC_REPRODUCIBILITY_NOT_GATE_A_APPROVAL",
               "run_id": os.environ.get("GITHUB_RUN_ID"), "scenario_count": 5,
               "total_trial_rows": 12000, "files": files}
    print(json.dumps(summary, sort_keys=True))
    return summary

def main() -> int:
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("scenario", "aggregate"), required=True)
    p.add_argument("--scenario")
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--input-root", default="c100-input")
    p.add_argument("--output-root", default="c100-output")
    args = p.parse_args()
    if args.mode == "scenario":
        if not args.scenario:
            p.error("--scenario is required in scenario mode")
        print(json.dumps(run_scenario(args.scenario, Path(args.output_root), args.workers), sort_keys=True))
    else:
        aggregate(Path(args.input_root), Path(args.output_root))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
