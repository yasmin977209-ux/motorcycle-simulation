from __future__ import annotations
import argparse, hashlib, json, os, platform, subprocess, sys, time
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any
import pyarrow as pa
import pyarrow.parquet as pq
import constants, monte_carlo, rng, validation

EXPECTED_C100_GOLDEN_SHA256 = "39950d91c3b40b11bea0997b8504ac932a57bcc0ef8e0c51e12d031342a53327"
EXPECTED_C100_MANIFEST_SHA256 = "2097284d77ead6b00492bf75830d09aeef8dbde4aaa1c15dae6a877dc7e9ff04"
C100_GOLDEN_PATH = Path("docs/golden/v2.3/C100_GOLDEN_965281d52441cd0d4b744e211c9f68ee4cdc3753.json")
C100_MANIFEST_PATH = Path("docs/audits/S4_C100_GOLDEN_MANIFEST_965281d52441cd0d4b744e211c9f68ee4cdc3753.json")
COLLECTION_LEVELS = (85, 70, 50, 30)
RECOVERY_LEVELS = (100, 70, 50, 30, 0)
OPT1_ENABLED_COLLECTIONS = frozenset({85, 70})
SCHEMA_VERSION = "v2.3"

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def require_source_sha(value: str) -> None:
    if len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("S6_SOURCE_SHA_INVALID")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def current_git_commit(source_sha: str) -> str:
    commit = os.environ.get("GITHUB_SHA")
    if not commit:
        result = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
        commit = result.stdout.strip()
    require_source_sha(commit)
    return commit


def package_versions() -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for package in ("numpy", "scipy", "pyarrow", "pandas", "python-dateutil"):
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            versions[package] = None
    return versions


def command_argv() -> list[str]:
    return ["python", *sys.argv]

def verify_c100_reuse() -> dict[str, Any]:
    if not C100_GOLDEN_PATH.is_file() or sha256_file(C100_GOLDEN_PATH) != EXPECTED_C100_GOLDEN_SHA256:
        raise RuntimeError("S6_C100_GOLDEN_REUSE_SHA256_MISMATCH")
    if not C100_MANIFEST_PATH.is_file() or sha256_file(C100_MANIFEST_PATH) != EXPECTED_C100_MANIFEST_SHA256:
        raise RuntimeError("S6_C100_MANIFEST_REUSE_SHA256_MISMATCH")
    c100_manifest=json.loads(C100_MANIFEST_PATH.read_text(encoding="utf-8"))
    return {"status":"REUSED_READ_ONLY","run_id":int(c100_manifest["workflow_run_id"]),"rerun":False,
            "golden_path":str(C100_GOLDEN_PATH),"golden_sha256":EXPECTED_C100_GOLDEN_SHA256,
            "manifest_path":str(C100_MANIFEST_PATH),"manifest_sha256":EXPECTED_C100_MANIFEST_SHA256,
            "source_sha":c100_manifest["source_sha"],"cohort_id":c100_manifest["cohort_id"],
            "scenario_ids":list(c100_manifest["scenario_ids"]),
            "trial_count_per_scenario":int(c100_manifest["trial_ids_per_scenario"][1]),
            "n_unique_paths":int(c100_manifest["N_unique_paths"]),
            "degeneracy_status":c100_manifest["degeneracy_status"],"G_status":c100_manifest["G_status"]}

def result_record(result: monte_carlo.TrialResult, source_sha: str, cohort_id: str, derived_from: str | None) -> dict[str, Any]:
    row=asdict(result)
    row.pop("collection_probability",None)
    row["rng_checksum"]=str(row["rng_checksum"])
    row.update(source_sha=source_sha,cohort_id=cohort_id,schema_version=SCHEMA_VERSION,derived_from=derived_from)
    return row

def result_from_record(row: dict[str, Any]) -> monte_carlo.TrialResult:
    clean=dict(row)
    for key in ("source_sha","cohort_id","schema_version","derived_from"): clean.pop(key,None)
    clean["rng_checksum"]=int(clean["rng_checksum"])
    clean["collection_probability"]=monte_carlo.parse_scenario_id(str(clean["scenario_id"]))[0]
    return monte_carlo.TrialResult(**clean)

def snapshot_record(row: dict[str, Any], scenario_id: str, source_sha: str, cohort_id: str) -> dict[str, Any]:
    out=dict(row)
    out.update(scenario_id=scenario_id,source_sha=source_sha,cohort_id=cohort_id,schema_version=SCHEMA_VERSION)
    return out

def load_base_artifact(base_dir: Path, collection_pct: int, source_sha: str, cohort_id: str, trial_count: int):
    manifest_path=base_dir/"scenario_manifest.json"
    if not manifest_path.is_file(): raise RuntimeError(f"S6_OPT1_BASE_MANIFEST_MISSING:C{collection_pct:03d}")
    manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("scenario_id") != f"C{collection_pct:03d}_G100": raise RuntimeError("S6_OPT1_BASE_SCENARIO_MISMATCH")
    if manifest.get("source_sha") != source_sha or manifest.get("cohort_id") != cohort_id: raise RuntimeError("S6_OPT1_BASE_SOURCE_OR_COHORT_MISMATCH")
    for name,entry in manifest.get("files",{}).items():
        path=base_dir/name
        if not path.is_file() or path.stat().st_size != entry["size_bytes"] or sha256_file(path) != entry["sha256"]:
            raise RuntimeError(f"S6_OPT1_BASE_ARTIFACT_HASH_MISMATCH:{name}")
    rows=pq.read_table(base_dir/"trials_summary.parquet").to_pylist()
    results={int(row["trial_id"]):result_from_record(row) for row in rows}
    expected=set(range(1,trial_count+1))
    if set(results)!=expected: raise RuntimeError("S6_OPT1_BASE_TRIAL_ID_COVERAGE_MISMATCH")
    daily_rows=pq.read_table(base_dir/"daily_snapshots.parquet").to_pylist()
    slices={}
    for row in daily_rows:
        tid=int(row["trial_id"])
        clean={k:v for k,v in row.items() if k not in {"scenario_id","source_sha","cohort_id","schema_version"}}
        slices.setdefault(tid,[]).append(clean)
    for tid in slices: slices[tid].sort(key=lambda x:str(x["date"]))
    if set(slices)!=expected: raise RuntimeError("S6_OPT1_BASE_DAILY_TRIAL_COVERAGE_MISMATCH")
    return results,slices

def run_full_trials(scenario_id: str, trial_ids: list[int], source_sha: str, workers: int):
    if not trial_ids: return {},{}
    results,daily=monte_carlo.run_trials_parallel(scenario_id,trial_ids,workers,master_seed=constants.MASTER_SEED,source_sha=source_sha)
    validation.validate_rng_audit_records([asdict(x) for x in results],source_sha=source_sha,master_seed=constants.MASTER_SEED,require_audit_fingerprint=True)
    return {x.trial_id:x for x in results},daily

def previous_checkpoint_n(target_n: int) -> int:
    start = constants.STATISTICAL_CHECK_START_N
    if target_n < start:
        raise ValueError("S6_CHECKPOINT_N_BELOW_APPROVED_START")
    ratio = target_n // start
    if target_n % start or ratio & (ratio - 1):
        raise ValueError("S6_CHECKPOINT_N_NOT_APPROVED_DOUBLING_POINT")
    return 0 if target_n == start else target_n // 2

def load_previous_artifact(previous_dir: Path, scenario_id: str, source_sha: str,
                           cohort_id: str, expected_n: int):
    manifest_path = previous_dir / "scenario_manifest.json"
    if not manifest_path.is_file():
        raise RuntimeError("S6_PREVIOUS_CHECKPOINT_MANIFEST_MISSING")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("scenario_id") != scenario_id:
        raise RuntimeError("S6_PREVIOUS_CHECKPOINT_SCENARIO_MISMATCH")
    if manifest.get("source_sha") != source_sha or manifest.get("cohort_id") != cohort_id:
        raise RuntimeError("S6_PREVIOUS_CHECKPOINT_SOURCE_OR_COHORT_MISMATCH")
    if manifest.get("trial_count") != expected_n or manifest.get("trial_id_start") != 1 or manifest.get("trial_id_end") != expected_n:
        raise RuntimeError("S6_PREVIOUS_CHECKPOINT_RANGE_MISMATCH")
    for name, entry in manifest.get("files", {}).items():
        path = previous_dir / name
        if not path.is_file() or path.stat().st_size != entry["size_bytes"] or sha256_file(path) != entry["sha256"]:
            raise RuntimeError(f"S6_PREVIOUS_CHECKPOINT_FILE_HASH_MISMATCH:{name}")
    rows = pq.read_table(previous_dir / "trials_summary.parquet").to_pylist()
    ids = [int(row["trial_id"]) for row in rows]
    if ids != list(range(1, expected_n + 1)):
        raise RuntimeError("S6_PREVIOUS_CHECKPOINT_TRIAL_ID_COVERAGE_MISMATCH")
    results = {int(row["trial_id"]): result_from_record(row) for row in rows}
    derived = {int(row["trial_id"]): row.get("derived_from") for row in rows}
    daily_rows = pq.read_table(previous_dir / "daily_snapshots.parquet").to_pylist()
    slices = {}
    for row in daily_rows:
        tid = int(row["trial_id"])
        clean = {k:v for k,v in row.items() if k not in {"scenario_id","source_sha","cohort_id","schema_version"}}
        slices.setdefault(tid, []).append(clean)
    for tid in slices:
        slices[tid].sort(key=lambda x: str(x["date"]))
    if set(slices) != set(range(1, expected_n + 1)):
        raise RuntimeError("S6_PREVIOUS_CHECKPOINT_DAILY_COVERAGE_MISMATCH")
    return results, slices, derived

def run_scenario(args: argparse.Namespace) -> dict[str, Any]:
    started_at_utc = utc_now()
    started = time.monotonic()
    require_source_sha(args.source_sha)
    previous_n = previous_checkpoint_n(args.trials)
    if args.workers<1: raise ValueError("S6_WORKERS_MUST_BE_POSITIVE")
    if previous_n and not args.previous_dir:
        raise ValueError("S6_PREVIOUS_CHECKPOINT_DIR_REQUIRED")
    if not previous_n and args.previous_dir:
        raise ValueError("S6_PREVIOUS_CHECKPOINT_DIR_FORBIDDEN_AT_N300")
    trial_start = args.trial_start if args.trial_start is not None else (previous_n + 1 if previous_n else 1)
    trial_end = args.trial_end if args.trial_end is not None else args.trials
    if trial_start != (previous_n + 1 if previous_n else 1) or trial_end != args.trials:
        raise ValueError("S6_INCREMENTAL_RANGE_MUST_EXTEND_PREVIOUS_CHECKPOINT_TO_TARGET_N")
    if trial_start < 1 or trial_end < trial_start:
        raise ValueError("S6_INCREMENTAL_TRIAL_RANGE_INVALID")
    c100_reuse=verify_c100_reuse()
    # Parse canonical scenario percentages as integers; parse_scenario_id returns a float probability.
    monte_carlo.parse_scenario_id(args.scenario)  # validates canonical scenario syntax and supported values
    collection_part, recovery_part = args.scenario.split("_", 1)
    collection_pct = int(collection_part[1:])
    recovery_pct = int(recovery_part[1:])
    if collection_pct not in COLLECTION_LEVELS or recovery_pct not in RECOVERY_LEVELS: raise ValueError("S6_SCENARIO_OUTSIDE_FIRST_STOCHASTIC_FAMILY")
    cohort_id=f"s6-v23-{args.source_sha[:8]}"
    trial_ids=list(range(1,args.trials+1))
    new_trial_ids=list(range(trial_start,trial_end+1))
    out_dir=Path(args.output_dir); out_dir.mkdir(parents=True,exist_ok=True)
    if previous_n:
        results, slices, derived = load_previous_artifact(Path(args.previous_dir), args.scenario, args.source_sha, cohort_id, previous_n)
    else:
        results, slices, derived = {}, {}, {}
    base_scenario=f"C{collection_pct:03d}_G100"
    if recovery_pct==100:
        new_results,new_slices=run_full_trials(args.scenario,new_trial_ids,args.source_sha,args.workers)
        results.update(new_results); slices.update(new_slices)
        policy="G100_BASE_FULL_RUN_INCREMENTAL_RANGE"
    elif collection_pct in OPT1_ENABLED_COLLECTIONS:
        if not args.base_dir: raise ValueError("S6_OPT1_BASE_DIR_REQUIRED_FOR_C085_C070_LOWER_G")
        base_results,base_slices=load_base_artifact(Path(args.base_dir),collection_pct,args.source_sha,cohort_id,args.trials)
        eligible=[tid for tid in new_trial_ids if base_results[tid].claims_created==0]
        full_ids=[tid for tid in new_trial_ids if base_results[tid].claims_created>0]
        full_results,full_slices=run_full_trials(args.scenario,full_ids,args.source_sha,args.workers)
        results.update(full_results); slices.update(full_slices)
        for tid in eligible:
            base=base_results[tid]
            candidate=replace(base,scenario_id=args.scenario,recovery_rate_pct=recovery_pct,
                rng_checksum_fingerprint_sha256=rng.rng_audit_fingerprint(source_sha=args.source_sha,
                    master_seed=constants.MASTER_SEED,scenario_id=args.scenario,trial_id=tid,
                    rng_checksum=base.rng_checksum,rng_draw_count=base.rng_draw_count),trial_fingerprint="")
            candidate=replace(candidate,trial_fingerprint=monte_carlo.trial_fingerprint(candidate))
            if monte_carlo.trial_fingerprint(candidate)!=monte_carlo.trial_fingerprint(base):
                raise RuntimeError(f"S6_OPT1_FINANCIAL_FINGERPRINT_MISMATCH:{args.scenario}:{tid}")
            results[tid]=candidate; slices[tid]=[dict(row) for row in base_slices[tid]]
            derived[tid]=f"DERIVED_FROM={base_scenario}"
        policy=("OPT1_ENABLED_DERIVED_ZERO_CLAIM_TRIALS_FULL_RUN_POSITIVE_CLAIM_TRIALS_INCREMENTAL_RANGE"
                if eligible else "OPT1_ENABLED_NO_ZERO_CLAIM_TRIALS_IN_INCREMENTAL_RANGE_FULL_RUN")
    else:
        new_results,new_slices=run_full_trials(args.scenario,new_trial_ids,args.source_sha,args.workers)
        results.update(new_results); slices.update(new_slices)
        policy="OPT1_INELIGIBLE_FULL_RUN_INCREMENTAL_RANGE"
    expected=set(trial_ids)
    if set(results)!=expected or set(slices)!=expected: raise RuntimeError(f"S6_SCENARIO_TRIAL_COVERAGE_MISMATCH:{args.scenario}")
    ordered=[results[tid] for tid in trial_ids]
    if any(x.scenario_id!=args.scenario for x in ordered): raise RuntimeError("S6_SCENARIO_IDENTITY_MISMATCH")
    trial_rows=[result_record(results[tid],args.source_sha,cohort_id,derived.get(tid)) for tid in trial_ids]
    daily_rows=[snapshot_record(row,args.scenario,args.source_sha,cohort_id) for tid in trial_ids for row in sorted(slices[tid],key=lambda x:str(x["date"]))]
    os.environ["S5_TRIAL_COUNT"]=str(args.trials)
    from scripts.s5_mini_verification import build_exact_daily_distribution
    distribution=build_exact_daily_distribution(ordered,slices,args.scenario,cohort_id,args.source_sha)
    targets={
        "trials_summary.parquet":trial_rows,
        "daily_snapshots.parquet":daily_rows,
        "daily_distribution.parquet":distribution,
    }
    for name,rows in targets.items(): pq.write_table(pa.Table.from_pylist(rows),out_dir/name,compression="zstd")
    provenance={
        "scenario_id":args.scenario,"collection_level":collection_pct,"recovery_level":recovery_pct,
        "policy":policy,"sample_trial_count":args.trials,
        "eligible_zero_claim_trials":sum(1 for x in ordered if x.claims_created==0),
        "derived_trial_count":sum(1 for v in derived.values() if v is not None),
        "full_run_trial_ids":[tid for tid in trial_ids if derived.get(tid) is None],
        "derived_trials":[{"trial_id":tid,"derived_from":derived.get(tid),"trial_fingerprint":results[tid].trial_fingerprint} for tid in trial_ids if derived.get(tid) is not None],
        "status":"EXECUTED"}
    write_json(out_dir/"opt1_provenance.json",provenance)
    names=[*targets.keys(),"opt1_provenance.json"]
    files={name:{"sha256":sha256_file(out_dir/name),"size_bytes":(out_dir/name).stat().st_size} for name in names}
    manifest={
        "schema_version":"s6-first-checkpoint-v1","status":"EXECUTED","scenario_id":args.scenario,
        "collection_level":collection_pct,"recovery_level":recovery_pct,"source_sha":args.source_sha,
        "cohort_id":cohort_id,"master_seed":constants.MASTER_SEED,"rng_scope":"COLLECTION_LEVEL",
        "schema_version_model":SCHEMA_VERSION,"trial_id_start":1,"trial_id_end":args.trials,
        "trial_count":len(ordered),"n_unique_paths":len({monte_carlo.trial_fingerprint(x) for x in ordered}),
        "git_commit":current_git_commit(args.source_sha),"run_id":args.run_id,"run_attempt":args.run_attempt,
        "started_at_utc":started_at_utc,"finished_at_utc":utc_now(),"command_argv":command_argv(),"exit_code":0,
        "python_version":platform.python_version(),"package_versions":package_versions(),
        "elapsed_seconds":time.monotonic()-started,"workers":args.workers,
        "opt1_policy":policy,"c100_reuse":c100_reuse,
        "gate_a_status":"NOT_EVALUATED_NO_SAME_SOURCE_PRODUCTION_GOLDEN",
        "gate_b_status":"NOT_EVALUATED_FIRST_CHECKPOINT_ONLY",
        "stability_status":"NOT_CONVERGED_CHECKPOINT_N300_BASELINE","files":files}
    write_json(out_dir/"scenario_manifest.json",manifest)
    print(json.dumps({"status":"S6_SCENARIO_CHECKPOINT_EXECUTED","scenario":args.scenario,
        "trial_count":len(ordered),"source_sha":args.source_sha,"cohort_id":cohort_id,"opt1_policy":policy,
        "eligible_zero_claim_trials":provenance["eligible_zero_claim_trials"],
        "derived_trial_count":provenance["derived_trial_count"],"elapsed_seconds":manifest["elapsed_seconds"],"files":files},
        ensure_ascii=False,sort_keys=True))
    return manifest

def stochastic_scenario_ids() -> set[str]:
    """Return only the 20 scenarios executed under the current stochastic SOURCE_SHA."""
    return {f"C{collection:03d}_G{recovery:03d}"
            for collection in COLLECTION_LEVELS for recovery in RECOVERY_LEVELS}


def reconstructed_scenario_command(scenario: str, source_sha: str, run_id: str,
                                   run_attempt: int, checkpoint_n: int, workers: int) -> list[str]:
    command = ["python", "scripts/s6_first_checkpoint.py", "--mode", "scenario",
        "--scenario", scenario, "--source-sha", source_sha, "--run-id", str(run_id),
        "--run-attempt", str(run_attempt), "--trials", str(checkpoint_n),
        "--workers", str(workers), "--output-dir", f"results_stage7_s6/{scenario}"]
    collection = int(scenario.split("_", 1)[0][1:])
    recovery = int(scenario.split("_", 1)[1][1:])
    if collection in OPT1_ENABLED_COLLECTIONS and recovery != 100:
        command.extend(["--base-dir", "results_stage7_s6/base"])
    return command


def aggregate(args: argparse.Namespace) -> dict[str, Any]:
    started_at_utc = utc_now()
    started = time.monotonic()
    require_source_sha(args.source_sha); c100_reuse=verify_c100_reuse()
    source_run_id = str(getattr(args,"source_run_id",None) or args.run_id)
    source_run_attempt = int(getattr(args,"source_run_attempt",None) or args.run_attempt)
    checkpoint_n = args.trials
    previous_checkpoint_n(checkpoint_n)
    root=Path(args.input_root); manifests=sorted(root.rglob("scenario_manifest.json")); by_scenario={}
    for mp in manifests:
        m=json.loads(mp.read_text(encoding="utf-8")); scenario=str(m.get("scenario_id",""))
        if scenario in by_scenario: raise RuntimeError(f"S6_DUPLICATE_SCENARIO_ARTIFACT:{scenario}")
        if m.get("source_sha")!=args.source_sha: raise RuntimeError(f"S6_SOURCE_SHA_MISMATCH:{scenario}")
        if str(m.get("run_id"))!=source_run_id or int(m.get("run_attempt",-1))!=source_run_attempt:
            raise RuntimeError(f"S6_RUN_IDENTITY_MISMATCH:{scenario}")
        if m.get("cohort_id")!=f"s6-v23-{args.source_sha[:8]}":
            raise RuntimeError(f"S6_COHORT_ID_MISMATCH:{scenario}")
        if m.get("trial_count")!=checkpoint_n or m.get("trial_id_start")!=1 or m.get("trial_id_end")!=checkpoint_n: raise RuntimeError(f"S6_TRIAL_COUNT_MISMATCH:{scenario}")
        base=mp.parent
        for name,e in m.get("files",{}).items():
            p=base/name
            if not p.is_file() or p.stat().st_size!=e["size_bytes"] or sha256_file(p)!=e["sha256"]:
                raise RuntimeError(f"S6_SCENARIO_FILE_HASH_MISMATCH:{scenario}:{name}")
        by_scenario[scenario]=(base,m)
    # C100 is a separate, immutable S4 cohort. It is verified and referenced above,
    # never merged into the new stochastic SOURCE_SHA/cohort or counted as independent samples.
    expected=stochastic_scenario_ids()
    if set(by_scenario)!=expected:
        raise RuntimeError(f"S6_SCENARIO_COVERAGE_MISMATCH:missing={sorted(expected-set(by_scenario))}:extra={sorted(set(by_scenario)-expected)}")
    all_trials=[]; all_daily=[]; summaries=[]
    for scenario in sorted(expected):
        base,m=by_scenario[scenario]
        rows=pq.read_table(base/"trials_summary.parquet").to_pylist()
        ids=[int(row["trial_id"]) for row in rows]
        if ids!=list(range(1,checkpoint_n+1)): raise RuntimeError(f"S6_TRIAL_ID_SEQUENCE_MISMATCH:{scenario}")
        daily=pq.read_table(base/"daily_distribution.parquet").to_pylist()
        if not daily: raise RuntimeError(f"S6_DAILY_DISTRIBUTION_EMPTY:{scenario}")
        all_trials.extend(rows); all_daily.extend(daily)
        summaries.append({"scenario_id":scenario,"status":m.get("status"),
            "n_total":len(rows),"n_closed":sum(1 for row in rows if row.get("final_close_date") is not None),
            "n_unique_paths":m["n_unique_paths"],"opt1_policy":m["opt1_policy"],
            "source_sha":m["source_sha"],"cohort_id":m["cohort_id"],
            "git_commit":m.get("git_commit",m["source_sha"]),
            "execution_metadata_source":"scenario_manifest" if m.get("git_commit") else "pinned_workflow_and_source_sha",
            "run_id":m.get("run_id"),"run_attempt":m.get("run_attempt"),
            "started_at_utc":m.get("started_at_utc"),"finished_at_utc":m.get("finished_at_utc"),
            "command_argv":m.get("command_argv") or reconstructed_scenario_command(
                scenario,args.source_sha,source_run_id,source_run_attempt,checkpoint_n,int(m.get("workers",2))),
            "exit_code":m.get("exit_code",0),"python_version":m.get("python_version"),
            "package_versions":m.get("package_versions"),"elapsed_seconds":m.get("elapsed_seconds"),
            "files":m.get("files",{}),"artifact_files_verified":True,
            "trial_fingerprint_map_sha256":hashlib.sha256("".join(f'{row["trial_id"]}|{row["trial_fingerprint"]}\n' for row in rows).encode()).hexdigest(),
            "scenario_manifest_sha256":sha256_file(base/"scenario_manifest.json")})
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    for name,rows in (("trials_summary.parquet",all_trials),("daily_distribution.parquet",all_daily)):
        pq.write_table(pa.Table.from_pylist(rows),out/name,compression="zstd")
    write_json(out/"c100_reuse.json",c100_reuse)
    files={p.name:{"sha256":sha256_file(p),"size_bytes":p.stat().st_size} for p in [out/"trials_summary.parquet",out/"daily_distribution.parquet",out/"c100_reuse.json"]}
    manifest={"schema_version":"s6-cumulative-aggregate-v2","status":"EXECUTED","source_sha":args.source_sha,
        "git_commit":current_git_commit(args.source_sha),"cohort_id":f"s6-v23-{args.source_sha[:8]}",
        "run_id":args.run_id,"run_attempt":args.run_attempt,
        "source_run_id":source_run_id,"source_run_attempt":source_run_attempt,
        "started_at_utc":started_at_utc,"finished_at_utc":utc_now(),
        "command_argv":command_argv(),"exit_code":0,
        "python_version":platform.python_version(),"package_versions":package_versions(),
        "elapsed_seconds":time.monotonic()-started,
        "master_seed":constants.MASTER_SEED,"rng_scope":"COLLECTION_LEVEL","checkpoint_n":checkpoint_n,
        "scenario_count":len(expected),"stochastic_scenario_count":len(expected),
        "total_scenario_combinations":len(expected)+len(c100_reuse["scenario_ids"]),
        "c100_reused_scenario_count":len(c100_reuse["scenario_ids"]),
        "scenario_summaries":summaries,"c100_reuse":c100_reuse,
        "test192_reuse":{"run_ids":[40531095239,40546712685],"proof_sha256":"f6add77e9e7ff8256b36b661df337897de10cd96d7e00b0d9dfa660dea0e927b","rerun":False},
        "acceptance_status":{"gate_a":"NOT_EVALUATED_NO_SAME_SOURCE_PRODUCTION_GOLDEN","gate_b":"NOT_EVALUATED_FIRST_CHECKPOINT_ONLY","stability":"NOT_CONVERGED_CHECKPOINT_N300_BASELINE"},
        "files":files}
    write_json(out/"manifest.json",manifest)
    print(json.dumps({"status":"S6_CUMULATIVE_CHECKPOINT_EXECUTED","source_sha":args.source_sha,
        "cohort_id":manifest["cohort_id"],"checkpoint_n":checkpoint_n,"scenario_count":len(expected),"trial_rows":len(all_trials),
        "daily_distribution_rows":len(all_daily),"stochastic_scenario_count":len(expected),
        "total_scenario_combinations":manifest["total_scenario_combinations"],
        "c100_reused_scenario_count":manifest["c100_reused_scenario_count"],
        "gate_a":manifest["acceptance_status"]["gate_a"],
        "gate_b":manifest["acceptance_status"]["gate_b"],"files":files},ensure_ascii=False,sort_keys=True))
    return manifest

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("scenario","aggregate"),required=True)
    p.add_argument("--scenario")
    p.add_argument("--source-sha",required=True)
    p.add_argument("--run-id",required=True)
    p.add_argument("--run-attempt",type=int,required=True)
    p.add_argument("--source-run-id")
    p.add_argument("--source-run-attempt",type=int)
    p.add_argument("--trials",type=int,default=constants.STATISTICAL_CHECK_START_N, help="Cumulative checkpoint N: 300, 600, 1200, 2400, ...")
    p.add_argument("--trial-start",type=int,default=None,help="First incremental trial ID; defaults to previous checkpoint N + 1 (or 1 at N=300)")
    p.add_argument("--trial-end",type=int,default=None,help="Last incremental trial ID; defaults to --trials")
    p.add_argument("--workers",type=int,default=2)
    p.add_argument("--output-dir",default="results_stage7_s6/scenario")
    p.add_argument("--base-dir")
    p.add_argument("--previous-dir", help="Verified artifact for the immediately preceding cumulative checkpoint")
    p.add_argument("--input-root",default="results_stage7_s6/artifacts")
    args=p.parse_args()
    if args.mode=="scenario":
        if not args.scenario: p.error("--scenario is required in scenario mode")
        run_scenario(args)
    else: aggregate(args)
    return 0

if __name__=="__main__": raise SystemExit(main())
