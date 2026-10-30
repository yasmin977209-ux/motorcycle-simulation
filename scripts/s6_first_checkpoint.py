from __future__ import annotations
import argparse, hashlib, json, os, platform, subprocess, sys, time
from datetime import date, datetime, timedelta, timezone
from fractions import Fraction
from importlib.metadata import PackageNotFoundError, version
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import tempfile, zipfile
import pyarrow as pa
import pyarrow.parquet as pq
import constants, monte_carlo, rng, validation, stats_integrity
from stats_integrity import resolve_n_unique_paths, validate_cumulative_trial_ids
from scripts.s6_daily_path_identity import DAILY_BALANCE_INTEGER_FIELDS, DAILY_BALANCE_SCHEMA_VERSION, SCENARIO_MANIFEST_SCHEMA_VERSION, build_daily_path_identity_evidence, require_daily_path_manifest_contract

EXPECTED_C100_GOLDEN_SHA256 = "39950d91c3b40b11bea0997b8504ac932a57bcc0ef8e0c51e12d031342a53327"
EXPECTED_C100_MANIFEST_SHA256 = "2097284d77ead6b00492bf75830d09aeef8dbde4aaa1c15dae6a877dc7e9ff04"
C100_GOLDEN_PATH = Path("docs/golden/v2.3/C100_GOLDEN_965281d52441cd0d4b744e211c9f68ee4cdc3753.json")
C100_MANIFEST_PATH = Path("docs/audits/S4_C100_GOLDEN_MANIFEST_965281d52441cd0d4b744e211c9f68ee4cdc3753.json")
COLLECTION_LEVELS = (85, 70, 50, 30)
RECOVERY_LEVELS = (100, 70, 50, 30, 0)
OPT1_ENABLED_COLLECTIONS = frozenset({85, 70})
SCHEMA_VERSION = "v2.3"
GOVERNING_DECISION_ID = "D-2026-10-30-REFERENCE-V2.4.0"
GOVERNING_REFERENCE_SHA256 = "225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b"
REQUIRED_SCENARIO_ARTIFACT_FILES = (
    "trials_summary.parquet",
    "daily_snapshots.parquet",
    "daily_distribution.parquet",
    "opt1_provenance.json",
)

def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def daily_path_fingerprints(rows: list[dict[str, Any]]) -> dict[int, str]:
    """Hash legacy daily trajectories only after rejecting duplicate or gapped keys."""
    grouped: dict[int, list[dict[str, Any]]] = {}
    seen: set[tuple[int, str]] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError("S6_LEGACY_DAILY_ROW_INVALID")
        trial_id = row.get("trial_id")
        if type(trial_id) is not int or trial_id < 1:
            raise RuntimeError("S6_LEGACY_DAILY_TRIAL_ID_INVALID")
        date_text = row.get("date")
        if not isinstance(date_text, str):
            raise RuntimeError("S6_LEGACY_DAILY_DATE_INVALID")
        try:
            parsed_date = date.fromisoformat(date_text)
        except ValueError as exc:
            raise RuntimeError("S6_LEGACY_DAILY_DATE_INVALID") from exc
        if parsed_date.isoformat() != date_text:
            raise RuntimeError("S6_LEGACY_DAILY_DATE_INVALID")
        key = (trial_id, date_text)
        if key in seen:
            raise RuntimeError(f"S6_LEGACY_DAILY_DUPLICATE_TRIAL_DATE:{trial_id}:{date_text}")
        seen.add(key)
        clean = {key: value for key, value in row.items()
                 if key not in {"trial_id", "scenario_id", "source_sha", "cohort_id", "schema_version"}}
        grouped.setdefault(trial_id, []).append(clean)
    if not grouped:
        raise RuntimeError("S6_LEGACY_DAILY_ROWS_MISSING")
    fingerprints: dict[int, str] = {}
    for trial_id, path_rows in grouped.items():
        path_rows.sort(key=lambda row: str(row["date"]))
        dates = [date.fromisoformat(str(row["date"])) for row in path_rows]
        expected = [dates[0] + timedelta(days=i) for i in range((dates[-1] - dates[0]).days + 1)]
        if dates != expected:
            raise RuntimeError(f"S6_LEGACY_DAILY_DATE_GAP:{trial_id}")
        payload = "\n".join(json.dumps(row, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), default=str) for row in path_rows)
        fingerprints[trial_id] = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return fingerprints


def validate_unique_trial_ids(rows: list[dict[str, Any]], expected_n: int, *, context: str) -> None:
    """Reject duplicate IDs before any dict comprehension can collapse them."""
    if type(expected_n) is not int or expected_n < 1:
        raise RuntimeError(f"S6_TRIAL_COUNT_INVALID:{context}")
    ids = [row.get("trial_id") for row in rows]
    if any(type(trial_id) is not int or trial_id < 1 for trial_id in ids):
        raise RuntimeError(f"S6_TRIAL_ID_INVALID:{context}")
    if len(ids) != len(set(ids)):
        raise RuntimeError(f"S6_DUPLICATE_TRIAL_ID:{context}")
    if sorted(ids) != list(range(1, expected_n + 1)):
        raise RuntimeError(f"S6_TRIAL_ID_COVERAGE_MISMATCH:{context}")


def validate_required_scenario_files(base_dir: Path, manifest: dict[str, Any]) -> None:
    """Require the complete, exact S6 scenario file inventory and verify every byte."""
    files = manifest.get("files")
    if not isinstance(files, dict) or set(files) != set(REQUIRED_SCENARIO_ARTIFACT_FILES):
        raise RuntimeError("S6_SCENARIO_REQUIRED_FILE_MANIFEST_INCOMPLETE")
    for name in REQUIRED_SCENARIO_ARTIFACT_FILES:
        entry = files.get(name)
        if not isinstance(entry, dict):
            raise RuntimeError(f"S6_SCENARIO_FILE_MANIFEST_ENTRY_INVALID:{name}")
        size = entry.get("size_bytes")
        digest = entry.get("sha256")
        if type(size) is not int or size < 0 or not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            raise RuntimeError(f"S6_SCENARIO_FILE_MANIFEST_ENTRY_INVALID:{name}")
        path = base_dir / name
        if not path.is_file() or path.stat().st_size != size or sha256_file(path) != digest:
            raise RuntimeError(f"S6_SCENARIO_FILE_HASH_MISMATCH:{name}")

def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

def require_source_sha(value: str) -> None:
    if len(value) != 40 or any(c not in "0123456789abcdef" for c in value):
        raise ValueError("S6_SOURCE_SHA_INVALID")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def reported_unique_path_evidence(manifest: dict[str, Any], computed_count: int,
                                  diagnostic_count: int, expected_source_sha: str,
                                  expected_cohort_id: str) -> tuple[int, str]:
    """Apply the owner-approved unique-daily-path contract only to the pinned cohort."""
    if manifest.get("source_sha") != expected_source_sha or manifest.get("cohort_id") != expected_cohort_id:
        raise RuntimeError("S6_N_UNIQUE_PATHS_SOURCE_OR_COHORT_MISMATCH")
    if "unique_daily_paths" in manifest and manifest.get("unique_daily_paths") != diagnostic_count:
        raise RuntimeError("S6_SCENARIO_UNIQUE_DAILY_PATHS_DIAGNOSTIC_MISMATCH")
    scenario = str(manifest.get("scenario_id", ""))
    if scenario.startswith("C100_"):
        if computed_count != 1 or diagnostic_count != 1:
            raise RuntimeError("S6_SCENARIO_N_UNIQUE_PATHS_MISMATCH")
        return 1, "DEGENERATE_DETERMINISTIC"
    if computed_count != diagnostic_count:
        raise RuntimeError("S6_N_UNIQUE_PATHS_DAILY_PATH_COUNT_MISMATCH")
    return computed_count, "OWNER_APPROVED_UNIQUE_DAILY_PATHS_CONTRACT"


def current_git_commit(source_sha: str | None = None) -> str | None:
    """Return an actual checked-out commit SHA; never substitute SOURCE_SHA."""
    commit = os.environ.get("GITHUB_SHA")
    if commit:
        require_source_sha(commit)
        return commit
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    commit = result.stdout.strip()
    if not commit:
        return None
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
    require_daily_path_manifest_contract(manifest, expected_source_sha=source_sha, expected_cohort_id=cohort_id, expected_scenario_id=f"C{collection_pct:03d}_G100", expected_master_seed=constants.MASTER_SEED, expected_trial_count=trial_count, model_schema_version=SCHEMA_VERSION)
    validate_required_scenario_files(base_dir, manifest)
    rows=pq.read_table(base_dir/"trials_summary.parquet").to_pylist()
    validate_unique_trial_ids(rows, trial_count, context="OPT1_BASE")
    results={row["trial_id"]:result_from_record(row) for row in rows}
    expected=set(range(1,trial_count+1))
    if set(results)!=expected: raise RuntimeError("S6_OPT1_BASE_TRIAL_ID_COVERAGE_MISMATCH")
    daily_rows=pq.read_table(base_dir/"daily_snapshots.parquet").to_pylist()
    base_evidence=build_daily_path_identity_evidence(daily_rows,source_sha=source_sha,cohort_id=cohort_id,master_seed=constants.MASTER_SEED,scenario_id=f"C{collection_pct:03d}_G100",expected_trial_ids=range(1,trial_count+1),expected_start_date=constants.PROJECT_START_DATE.isoformat(),model_schema_version=SCHEMA_VERSION)
    if base_evidence["summary"]!=manifest.get("daily_path_identity_contract"): raise RuntimeError("S6_OPT1_BASE_DAILY_PATH_IDENTITY_CONTRACT_MISMATCH")
    slices={}
    for row in daily_rows:
        tid=int(row["trial_id"])
        clean={k:v for k,v in row.items() if k not in {"scenario_id","source_sha","cohort_id","schema_version"}}
        slices.setdefault(tid,[]).append(clean)
    for tid in slices: slices[tid].sort(key=lambda x:str(x["date"]))
    if set(slices)!=expected: raise RuntimeError("S6_OPT1_BASE_DAILY_TRIAL_COVERAGE_MISMATCH")
    return results,slices

def validate_cumulative_rng_audit(records: list[dict[str, Any]], source_sha: str) -> int:
    """Validate RNG audit fingerprints and checksum uniqueness across the full cumulative cohort."""
    normalized = []
    for raw in records:
        row = dict(raw)
        for key in ("trial_id", "rng_checksum", "rng_draw_count"):
            row[key] = int(row[key])
        normalized.append(row)
    return validation.validate_rng_audit_records(
        normalized, source_sha=source_sha, master_seed=constants.MASTER_SEED,
        require_audit_fingerprint=True,
    )


def run_full_trials(scenario_id: str, trial_ids: list[int], source_sha: str, workers: int):
    if not trial_ids: return {},{}
    results,daily=monte_carlo.run_trials_parallel(scenario_id,trial_ids,workers,master_seed=constants.MASTER_SEED,source_sha=source_sha)
    validation.validate_rng_audit_records([asdict(x) for x in results],source_sha=source_sha,master_seed=constants.MASTER_SEED,require_audit_fingerprint=True)
    return {x.trial_id:x for x in results},daily

def previous_checkpoint_n(target_n: int) -> int:
    start = constants.STATISTICAL_CHECK_START_N
    if type(target_n) is not int or target_n < start:
        raise ValueError("S6_CHECKPOINT_N_BELOW_APPROVED_START")
    ratio = target_n // start
    if target_n % start or ratio & (ratio - 1):
        raise ValueError("S6_CHECKPOINT_N_NOT_APPROVED_DOUBLING_POINT")
    return 0 if target_n == start else target_n // 2


def statistical_checkpoint_schedule(max_n: int) -> list[int]:
    """Return every approved cumulative checkpoint up to max_n; no fixed upper cap."""
    previous_checkpoint_n(max_n)  # fail closed unless max_n is an approved doubling point
    schedule: list[int] = []
    n = constants.STATISTICAL_CHECK_START_N
    while n <= max_n:
        schedule.append(n)
        n *= constants.STATISTICAL_ESCALATION_MULTIPLIER
    if not schedule or schedule[-1] != max_n:
        raise RuntimeError("S6_STATISTICAL_CHECKPOINT_SCHEDULE_INCOMPLETE")
    return schedule


def validate_checkpoint_target_range(target: int, trial_start: int, trial_end: int) -> int:
    """Validate a resumable target without imposing a hard-coded maximum checkpoint."""
    if type(target) is not int or type(trial_start) is not int or type(trial_end) is not int:
        raise RuntimeError("S6_CHECKPOINT_CONFIG_RANGE_INVALID")
    if target < constants.STATISTICAL_CHECK_START_N * constants.STATISTICAL_ESCALATION_MULTIPLIER:
        raise RuntimeError("S6_CHECKPOINT_CONFIG_RANGE_INVALID")
    if trial_start != target // 2 + 1 or trial_end != target or target != 2 * (trial_start - 1):
        raise RuntimeError("S6_CHECKPOINT_CONFIG_RANGE_INVALID")
    try:
        previous_n = previous_checkpoint_n(target)
    except ValueError as exc:
        raise RuntimeError("S6_CHECKPOINT_CONFIG_RANGE_INVALID") from exc
    if previous_n != target // 2:
        raise RuntimeError("S6_CHECKPOINT_CONFIG_RANGE_INVALID")
    return previous_n


def _s6_action_checkpoint_config() -> dict[str, Any] | None:
    """Load owner-pinned resume config only on Actions, never under pytest."""
    if os.environ.get("GITHUB_ACTIONS", "").lower() != "true" or "PYTEST_CURRENT_TEST" in os.environ:
        return None
    path = Path("scripts/s6_checkpoint_config.json")
    if not path.is_file():
        raise RuntimeError("S6_CHECKPOINT_CONFIG_MISSING")
    config = json.loads(path.read_text(encoding="utf-8"))
    target, start, end = int(config["active_target_trials"]), int(config["trial_start"]), int(config["trial_end"])
    validate_checkpoint_target_range(target, start, end)
    require_source_sha(str(config["source_sha"]))
    if config.get("cohort_id") != f"s6-v23-{config['source_sha'][:8]}":
        raise RuntimeError("S6_CHECKPOINT_CONFIG_COHORT_INVALID")
    return config


def _safe_extract_zip(zip_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    with zipfile.ZipFile(zip_path) as archive:
        for member in archive.infolist():
            target = (destination / member.filename).resolve()
            if target != root and root not in target.parents:
                raise RuntimeError("S6_PREVIOUS_ARTIFACT_ZIP_PATH_TRAVERSAL")
        archive.extractall(destination)


def download_previous_scenario_artifact(run_id: int, scenario_id: str, destination: Path) -> Path:
    """Download one artifact by exact name from the pinned GitHub Actions run."""
    repo, token = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not repo or not token:
        raise RuntimeError("S6_PREVIOUS_ARTIFACT_DOWNLOAD_REQUIRES_GITHUB_REPOSITORY_AND_TOKEN")
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28"}
    api = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}/artifacts?per_page=100"
    try:
        with urlopen(Request(api, headers=headers), timeout=60) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise RuntimeError(f"S6_PREVIOUS_ARTIFACT_LIST_FAILED:HTTP_{exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"S6_PREVIOUS_ARTIFACT_LIST_FAILED:{type(exc).__name__}") from exc
    # Artifact labels in legacy workflows may retain the old N300 label even when
    # the manifest is a later cumulative checkpoint. Select by pinned run and scenario,
    # then validate the manifest's N and trial IDs before reuse.
    expected_scenario = scenario_id.replace("_", "-")
    matches = []
    for artifact in payload.get("artifacts", []):
        name = str(artifact.get("name", ""))
        if artifact.get("expired") or not name.startswith("s6-n") or not name.endswith(f"-{run_id}"):
            continue
        remainder = name[len("s6-n"):]
        checkpoint_label, separator, scenario_label = remainder.partition("-")
        if not separator or not checkpoint_label.isdigit():
            continue
        scenario_label = scenario_label[:-(len(str(run_id)) + 1)]
        if scenario_label.replace("_", "-") == expected_scenario:
            matches.append(artifact)
    if len(matches) != 1:
        raise RuntimeError(f"S6_PREVIOUS_ARTIFACT_NOT_UNIQUE:{scenario_id}:{len(matches)}")
    archive_url = f"https://api.github.com/repos/{repo}/actions/artifacts/{int(matches[0]['id'])}/zip"
    try:
        with urlopen(Request(archive_url, headers=headers), timeout=300) as response:
            data = response.read()
    except HTTPError as exc:
        raise RuntimeError(f"S6_PREVIOUS_ARTIFACT_DOWNLOAD_FAILED:{scenario_id}:HTTP_{exc.code}") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"S6_PREVIOUS_ARTIFACT_DOWNLOAD_FAILED:{scenario_id}:{type(exc).__name__}") from exc
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix="s6-prev-", suffix=".zip", delete=False) as tmp:
        tmp.write(data); archive_path = Path(tmp.name)
    try:
        _safe_extract_zip(archive_path, destination)
    finally:
        archive_path.unlink(missing_ok=True)
    manifests = list(destination.rglob("scenario_manifest.json"))
    if len(manifests) != 1:
        raise RuntimeError(f"S6_PREVIOUS_ARTIFACT_MANIFEST_CARDINALITY:{scenario_id}:{len(manifests)}")
    return manifests[0].parent


def require_latest_branch_commit() -> None:
    """Prevent queued pushes from launching duplicate Monte Carlo work."""
    if os.environ.get("GITHUB_ACTIONS", "").lower() != "true" or "PYTEST_CURRENT_TEST" in os.environ:
        return
    repo = os.environ.get("GITHUB_REPOSITORY")
    ref = os.environ.get("GITHUB_REF", "")
    current = os.environ.get("GITHUB_SHA", "")
    prefix = "refs/heads/"
    if not repo or not ref.startswith(prefix) or not current:
        raise RuntimeError("S6_LATEST_COMMIT_GUARD_CONTEXT_MISSING")
    branch = ref[len(prefix):]
    from urllib.parse import quote
    url = f"https://api.github.com/repos/{repo}/branches/{quote(branch, safe='')}"
    try:
        with urlopen(Request(url, headers={"Accept": "application/vnd.github+json"}), timeout=30) as response:
            latest = json.loads(response.read().decode("utf-8"))["commit"]["sha"]
    except Exception as exc:
        raise RuntimeError(f"S6_LATEST_COMMIT_LOOKUP_FAILED:{type(exc).__name__}") from exc
    if latest != current:
        raise RuntimeError("S6_STALE_WORKFLOW_COMMIT_NO_MONTE_CARLO")


def apply_action_checkpoint_config(args: argparse.Namespace) -> dict[str, Any] | None:
    """Apply active checkpoint config only to scenario runs; aggregate uses manifest evidence."""
    config = _s6_action_checkpoint_config()
    if config is None:
        return None
    args._s6_checkpoint_config = config
    if str(args.source_sha) != str(config["source_sha"]):
        raise RuntimeError("S6_CHECKPOINT_CONFIG_SOURCE_SHA_MISMATCH")
    if args.mode != "scenario":
        return config

    target = int(config["active_target_trials"])
    args.trials = target
    args.trial_start = int(config["trial_start"])
    args.trial_end = int(config["trial_end"])
    scenario = str(args.scenario)
    prior_run_id = int(config["previous_run_id"])
    candidates: list[Path] = []
    if args.previous_dir:
        supplied = Path(args.previous_dir)
        if (supplied / "scenario_manifest.json").is_file():
            candidates.append(supplied)
        elif supplied.is_dir():
            manifests = list(supplied.rglob("scenario_manifest.json"))
            if len(manifests) == 1:
                candidates.append(manifests[0].parent)
    cache_dir = Path("/tmp/s6_prev_n600") / scenario
    if cache_dir.is_dir() and (cache_dir / "scenario_manifest.json").is_file():
        candidates.append(cache_dir)

    previous_dir: Path | None = None
    for candidate in candidates:
        manifest = json.loads((candidate / "scenario_manifest.json").read_text(encoding="utf-8"))
        if (
            manifest.get("scenario_id") != scenario
            or manifest.get("source_sha") != config["source_sha"]
            or manifest.get("cohort_id") != config["cohort_id"]
            or int(manifest.get("trial_count", -1)) != target // 2
            or str(manifest.get("run_id")) != str(prior_run_id)
            or int(manifest.get("run_attempt", -1)) != 1
            or manifest.get("trial_id_start") != 1
            or manifest.get("trial_id_end") != target // 2
        ):
            raise RuntimeError(f"S6_PREVIOUS_CHECKPOINT_SOURCE_COHORT_RUN_OR_RANGE_MISMATCH:{scenario}")
        previous_dir = candidate
        break
    if previous_dir is None:
        previous_dir = download_previous_scenario_artifact(prior_run_id, scenario, cache_dir)
        manifest = json.loads((previous_dir / "scenario_manifest.json").read_text(encoding="utf-8"))
        if (
            manifest.get("scenario_id") != scenario
            or manifest.get("source_sha") != config["source_sha"]
            or manifest.get("cohort_id") != config["cohort_id"]
            or int(manifest.get("trial_count", -1)) != target // 2
            or str(manifest.get("run_id")) != str(prior_run_id)
            or int(manifest.get("run_attempt", -1)) != 1
            or manifest.get("trial_id_start") != 1
            or manifest.get("trial_id_end") != target // 2
        ):
            raise RuntimeError(f"S6_PREVIOUS_CHECKPOINT_SOURCE_COHORT_RUN_OR_RANGE_MISMATCH:{scenario}")
    args.previous_dir = str(previous_dir)
    return config


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
    require_daily_path_manifest_contract(manifest, expected_source_sha=source_sha, expected_cohort_id=cohort_id, expected_scenario_id=scenario_id, expected_master_seed=constants.MASTER_SEED, expected_trial_count=expected_n, model_schema_version=SCHEMA_VERSION)
    for name, entry in manifest.get("files", {}).items():
        path = previous_dir / name
        if not path.is_file() or path.stat().st_size != entry["size_bytes"] or sha256_file(path) != entry["sha256"]:
            raise RuntimeError(f"S6_PREVIOUS_CHECKPOINT_FILE_HASH_MISMATCH:{name}")
    rows = pq.read_table(previous_dir / "trials_summary.parquet").to_pylist()
    ids = [int(row["trial_id"]) for row in rows]
    validate_cumulative_trial_ids(ids, expected_n, scenario_id=scenario_id)
    results = {int(row["trial_id"]): result_from_record(row) for row in rows}
    derived = {int(row["trial_id"]): row.get("derived_from") for row in rows}
    daily_rows = pq.read_table(previous_dir / "daily_snapshots.parquet").to_pylist()
    previous_evidence=build_daily_path_identity_evidence(daily_rows,source_sha=source_sha,cohort_id=cohort_id,master_seed=constants.MASTER_SEED,scenario_id=scenario_id,expected_trial_ids=range(1,expected_n+1),expected_start_date=constants.PROJECT_START_DATE.isoformat(),model_schema_version=SCHEMA_VERSION)
    if previous_evidence["summary"]!=manifest.get("daily_path_identity_contract"): raise RuntimeError("S6_PREVIOUS_CHECKPOINT_DAILY_PATH_IDENTITY_MISMATCH")
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
    rng_audit_records_verified = validate_cumulative_rng_audit([asdict(x) for x in ordered], args.source_sha)
    trial_rows=[result_record(results[tid],args.source_sha,cohort_id,derived.get(tid)) for tid in trial_ids]
    daily_rows=[snapshot_record(row,args.scenario,args.source_sha,cohort_id) for tid in trial_ids for row in sorted(slices[tid],key=lambda x:str(x["date"]))]
    path_evidence=build_daily_path_identity_evidence(daily_rows,source_sha=args.source_sha,cohort_id=cohort_id,master_seed=constants.MASTER_SEED,scenario_id=args.scenario,expected_trial_ids=trial_ids,expected_start_date=constants.PROJECT_START_DATE.isoformat(),model_schema_version=SCHEMA_VERSION)
    path_contract=path_evidence["summary"]
    n_unique_daily_paths=int(path_contract["unique_daily_path_count"])
    n_unique_financial_outcomes=len({monte_carlo.trial_fingerprint(x) for x in ordered})
    os.environ["S5_TRIAL_COUNT"]=str(args.trials)
    from scripts.s5_mini_verification import build_exact_daily_distribution
    distribution=build_exact_daily_distribution(ordered,slices,args.scenario,cohort_id,args.source_sha)
    targets={
        "trials_summary.parquet":trial_rows,
        "daily_snapshots.parquet":daily_rows,
        "daily_distribution.parquet":distribution,
    }
    for name,rows in targets.items(): pq.write_table(pa.Table.from_pylist(rows),out_dir/name,compression="zstd")
    persisted_daily=pq.read_table(out_dir/"daily_snapshots.parquet").to_pylist()
    readback=build_daily_path_identity_evidence(persisted_daily,source_sha=args.source_sha,cohort_id=cohort_id,master_seed=constants.MASTER_SEED,scenario_id=args.scenario,expected_trial_ids=trial_ids,expected_start_date=constants.PROJECT_START_DATE.isoformat(),model_schema_version=SCHEMA_VERSION)
    if readback["summary"]!=path_contract: raise RuntimeError("S6_POST_WRITE_DAILY_PATH_IDENTITY_MISMATCH")
    path_contract=readback["summary"]
    n_unique_daily_paths=int(path_contract["unique_daily_path_count"])
    n_unique_paths=resolve_n_unique_paths(args.scenario,[int(getattr(x,"rng_draw_count",0)) for x in ordered],n_unique_daily_paths)
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
        "schema_version":SCENARIO_MANIFEST_SCHEMA_VERSION,"status":"EXECUTED","scenario_id":args.scenario,
        "collection_level":collection_pct,"recovery_level":recovery_pct,"source_sha":args.source_sha,
        "cohort_id":cohort_id,"master_seed":constants.MASTER_SEED,"rng_scope":"COLLECTION_LEVEL",
        "schema_version_model":SCHEMA_VERSION,"trial_id_start":1,"trial_id_end":args.trials,
        "trial_count":len(ordered),
        "daily_balance_contract":{"schema_version":DAILY_BALANCE_SCHEMA_VERSION,"status":"PASS_SCOPED_POST_WRITE_BALANCE_CHECK","source_sha":args.source_sha,"cohort_id":cohort_id,"master_seed":constants.MASTER_SEED,"model_schema_version":SCHEMA_VERSION,"rows_checked":path_contract["balance_rows_checked"],"balance_mismatch_count":path_contract["balance_mismatch_count"],"required_integer_fields":list(DAILY_BALANCE_INTEGER_FIELDS)},
        "daily_path_identity_contract":path_contract,
        "n_unique_paths":n_unique_paths,
        "rng_audit_validation":{"status":"PASS","records_verified":rng_audit_records_verified,"scope":"cumulative scenario trial IDs 1..N"},
        "n_unique_paths_status":"DEGENERATE_DETERMINISTIC" if args.scenario.startswith("C100_") else "OWNER_APPROVED_UNIQUE_DAILY_PATHS_CONTRACT",
        "unique_daily_paths":n_unique_daily_paths,
        "unique_terminal_fingerprints":n_unique_financial_outcomes,
        "n_unique_financial_outcomes":n_unique_financial_outcomes,
        "n_unique_daily_paths_diagnostic":n_unique_daily_paths,
        "git_commit":current_git_commit(args.source_sha),
        "governing_decision_id":GOVERNING_DECISION_ID,
        "governing_reference_sha256":GOVERNING_REFERENCE_SHA256,
        "source_run_metadata_declared_sha256":source_metadata.get("sha256") if source_metadata_path else None,
        "source_run_metadata_file_sha256":sha256_file(Path(source_metadata_path)) if source_metadata_path else None,
        "run_id":args.run_id,"run_attempt":args.run_attempt,
        "started_at_utc":started_at_utc,"finished_at_utc":utc_now(),"command_argv":command_argv(),"exit_code":0,
        "python_version":platform.python_version(),"package_versions":package_versions(),
        "elapsed_seconds":time.monotonic()-started,"workers":args.workers,
        "opt1_policy":policy,"c100_reuse":c100_reuse,
        "gate_a_status":"NOT_EVALUATED_NO_SAME_SOURCE_PRODUCTION_GOLDEN",
        "gate_b_status":"NOT_EVALUATED_FIRST_CHECKPOINT_ONLY" if args.trials==constants.STATISTICAL_CHECK_START_N else "NOT_EVALUATED_INTERMEDIATE_CHECKPOINT",
        "stability_status":"NOT_CONVERGED_CHECKPOINT_N300_BASELINE" if args.trials==constants.STATISTICAL_CHECK_START_N else "NOT_EVALUATED_INTERMEDIATE_CHECKPOINT",
        "files":files}
    write_json(out_dir/"scenario_manifest.json",manifest)
    from scripts.audit_s6_daily_balance_artifact import audit_scenario_artifacts
    audit_report=audit_scenario_artifacts(out_dir)
    if audit_report["status"]!="PASS_SCOPED_DAILY_BALANCE_AND_PATH_IDENTITY": raise RuntimeError("S6_POST_WRITE_DAILY_BALANCE_AUDIT_NOT_PASS")
    write_json(out_dir/"daily_balance_path_audit.json",audit_report)
    print(json.dumps({"status":"S6_SCENARIO_CHECKPOINT_EXECUTED","scenario":args.scenario,"trial_count":len(ordered),"source_sha":args.source_sha,"cohort_id":cohort_id,"opt1_policy":policy,"eligible_zero_claim_trials":provenance["eligible_zero_claim_trials"],"derived_trial_count":provenance["derived_trial_count"],"elapsed_seconds":manifest["elapsed_seconds"],"daily_balance_audit_status":audit_report["status"],"daily_balance_path_audit_sha256":sha256_file(out_dir/"daily_balance_path_audit.json"),"files":files},ensure_ascii=False,sort_keys=True))
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


def resolve_aggregate_checkpoint_n(
    requested_n: int, manifest_trial_counts: list[int], config: dict[str, Any] | None = None,
) -> int:
    """Resolve the cumulative N from verified input manifests, and reject mixed checkpoints."""
    if not manifest_trial_counts:
        raise RuntimeError("S6_AGGREGATE_SCENARIO_MANIFESTS_MISSING")
    if any(type(value) is not int for value in manifest_trial_counts):
        raise RuntimeError("S6_AGGREGATE_MANIFEST_TRIAL_COUNT_INVALID")
    observed = set(manifest_trial_counts)
    if len(observed) != 1:
        raise RuntimeError(f"S6_AGGREGATE_MIXED_CHECKPOINT_N:{sorted(observed)}")
    actual_n = next(iter(observed))
    if actual_n == requested_n:
        previous_checkpoint_n(actual_n)
        return actual_n
    if config is not None:
        target = int(config["active_target_trials"])
        if actual_n == target and requested_n == target // 2:
            previous_checkpoint_n(actual_n)
            return actual_n
    raise RuntimeError(f"S6_AGGREGATE_REQUESTED_N_MISMATCH:requested={requested_n}:artifacts={actual_n}")



def ordered_stochastic_scenario_ids() -> list[str]:
    return [f"C{collection:03d}_G{recovery:03d}"
            for collection in COLLECTION_LEVELS for recovery in RECOVERY_LEVELS]


def financial_fingerprint_map_sha256(scenario: str, fingerprints: dict[str, str]) -> str:
    lines = [f"{scenario}|{trial_id}|{fingerprints[trial_id]}"
             for trial_id in sorted(fingerprints, key=lambda value: int(value))]
    return hashlib.sha256(("\n".join(lines) + "\n").encode("utf-8")).hexdigest()


def validate_golden_approval_combined_map_pin(approval:dict[str,Any],manifest:dict[str,Any],combined_sha:str)->None:
    if (
        manifest.get("combined_financial_trial_fingerprint_map_sha256")!=combined_sha
        or approval.get("combined_financial_trial_fingerprint_map_sha256")!=combined_sha
    ):
        raise RuntimeError("S6_GATE_A_GOLDEN_APPROVAL_COMBINED_MAP_PIN_MISMATCH")


def load_approved_gate_a_golden(
    golden_map_path: str | None,
    golden_manifest_path: str | None,
    golden_approval_path: str | None,
    *,
    expected_source_sha: str,
    expected_cohort_id: str,
) -> dict[str, Any] | None:
    """Load a separately reviewed, hash-pinned, independent Golden map; never self-generate it."""
    supplied = (golden_map_path, golden_manifest_path, golden_approval_path)
    if not any(supplied):
        return None
    if not all(supplied):
        raise RuntimeError("S6_GATE_A_GOLDEN_INPUT_SET_INCOMPLETE")

    map_path, manifest_path, approval_path = (Path(value) for value in supplied if value)
    for path in (map_path, manifest_path, approval_path):
        if not path.is_file():
            raise RuntimeError(f"S6_GATE_A_GOLDEN_INPUT_MISSING:{path.name}")
    map_sha = sha256_file(map_path)
    manifest_sha = sha256_file(manifest_path)
    approval_sha = sha256_file(approval_path)
    golden_map = json.loads(map_path.read_text(encoding="utf-8"))
    golden_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    approval = json.loads(approval_path.read_text(encoding="utf-8"))

    expected_scenarios = ordered_stochastic_scenario_ids()
    if golden_map.get("schema_version") != "s6-independent-golden-map-v1":
        raise RuntimeError("S6_GATE_A_GOLDEN_MAP_SCHEMA_INVALID")
    if golden_map.get("status") != "INDEPENDENT_GOLDEN_CANDIDATE_NOT_APPROVED":
        raise RuntimeError("S6_GATE_A_GOLDEN_MAP_STATUS_INVALID")
    if golden_manifest.get("schema_version") != "s6-independent-golden-manifest-v1":
        raise RuntimeError("S6_GATE_A_GOLDEN_MANIFEST_SCHEMA_INVALID")
    if golden_manifest.get("status") != "INDEPENDENT_GOLDEN_CANDIDATE_NOT_APPROVED":
        raise RuntimeError("S6_GATE_A_GOLDEN_MANIFEST_STATUS_INVALID")
    if (
        golden_map.get("source_sha") != expected_source_sha
        or golden_manifest.get("source_sha") != expected_source_sha
        or golden_map.get("cohort_id") != expected_cohort_id
        or golden_manifest.get("cohort_id") != expected_cohort_id
        or golden_map.get("master_seed") != constants.MASTER_SEED
        or golden_manifest.get("master_seed") != constants.MASTER_SEED
        or golden_map.get("model_schema_version") != SCHEMA_VERSION
        or golden_manifest.get("model_schema_version") != SCHEMA_VERSION
    ):
        raise RuntimeError("S6_GATE_A_GOLDEN_SOURCE_COHORT_SEED_OR_SCHEMA_MISMATCH")

    golden_n = golden_map.get("trial_count_per_scenario")
    if (
        type(golden_n) is not int
        or golden_n < constants.STATISTICAL_CHECK_START_N
        or golden_map.get("trial_id_start") != 1
        or golden_map.get("trial_id_end") != golden_n
        or golden_manifest.get("trial_count_per_scenario") != golden_n
        or golden_manifest.get("total_trial_fingerprints") != 20 * golden_n
        or golden_map.get("scenario_count") != len(expected_scenarios)
        or golden_manifest.get("scenario_count") != len(expected_scenarios)
        or golden_map.get("total_trial_fingerprints") != len(expected_scenarios) * golden_n
        or golden_map.get("independent_execution") is not True
        or golden_manifest.get("independent_execution") is not True
        or golden_map.get("production_result_artifacts_read") is not False
        or golden_manifest.get("production_result_artifacts_read") is not False
        or golden_manifest.get("map_file") != map_path.name
        or golden_manifest.get("map_file_sha256") != map_sha
    ):
        raise RuntimeError("S6_GATE_A_GOLDEN_COVERAGE_OR_INDEPENDENCE_INVALID")
    previous_checkpoint_n(golden_n)

    scenario_maps = golden_map.get("scenarios", {})
    if not isinstance(scenario_maps, dict) or set(scenario_maps) != set(expected_scenarios):
        raise RuntimeError("S6_GATE_A_GOLDEN_SCENARIO_SET_INVALID")
    scenario_manifest = golden_manifest.get("scenario_manifest", [])
    if not isinstance(scenario_manifest, list) or len(scenario_manifest) != len(expected_scenarios):
        raise RuntimeError("S6_GATE_A_GOLDEN_SCENARIO_MANIFEST_INVALID")
    scenario_manifest_by_id = {str(item.get("scenario_id", "")): item for item in scenario_manifest}
    if set(scenario_manifest_by_id) != set(expected_scenarios):
        raise RuntimeError("S6_GATE_A_GOLDEN_SCENARIO_MANIFEST_SET_INVALID")

    combined_lines: list[str] = []
    for scenario in expected_scenarios:
        entry = scenario_maps[scenario]
        fingerprints = entry.get("trial_fingerprints", {})
        expected_ids = {str(trial_id) for trial_id in range(1, golden_n + 1)}
        if set(fingerprints) != expected_ids:
            raise RuntimeError(f"S6_GATE_A_GOLDEN_TRIAL_COVERAGE_INVALID:{scenario}")
        if any(
            not isinstance(value, str) or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
            for value in fingerprints.values()
        ):
            raise RuntimeError(f"S6_GATE_A_GOLDEN_FINANCIAL_FINGERPRINT_INVALID:{scenario}")
        recomputed_map_sha = financial_fingerprint_map_sha256(scenario, fingerprints)
        if entry.get("financial_trial_fingerprint_map_sha256") != recomputed_map_sha:
            raise RuntimeError(f"S6_GATE_A_GOLDEN_SCENARIO_MAP_HASH_MISMATCH:{scenario}")
        manifest_entry = scenario_manifest_by_id[scenario]
        if (
            manifest_entry.get("trial_count") != golden_n
            or manifest_entry.get("financial_trial_fingerprint_map_sha256") != recomputed_map_sha
            or not manifest_entry.get("file_sha256")
        ):
            raise RuntimeError(f"S6_GATE_A_GOLDEN_SCENARIO_MANIFEST_HASH_MISMATCH:{scenario}")
        for trial_id in range(1, golden_n + 1):
            combined_lines.append(f"{scenario}|{trial_id}|{fingerprints[str(trial_id)]}")
    combined_sha = hashlib.sha256(("\n".join(combined_lines) + "\n").encode("utf-8")).hexdigest()
    if golden_manifest.get("combined_financial_trial_fingerprint_map_sha256") != combined_sha:
        raise RuntimeError("S6_GATE_A_GOLDEN_COMBINED_MAP_HASH_MISMATCH")
    validate_golden_approval_combined_map_pin(approval, golden_manifest, combined_sha)

    required_review_checks = (
        "source_lock_pass",
        "source_cohort_seed_schema_match",
        "full_scenario_coverage",
        "contiguous_trial_ids",
        "map_hashes_verified",
        "scenario_artifact_hashes_verified",
        "no_production_artifact_input",
        "tested_sha_verified_from_actions",
    )
    review_checks = approval.get("review_checks", {})
    if (
        approval.get("schema_version") != "s6-gate-a-golden-approval-v1"
        or approval.get("status") != "APPROVED_FOR_GATE_A"
        or approval.get("review_status") != "APPROVED"
        or approval.get("source_sha") != expected_source_sha
        or approval.get("cohort_id") != expected_cohort_id
        or approval.get("master_seed") != constants.MASTER_SEED
        or approval.get("model_schema_version") != SCHEMA_VERSION
        or approval.get("golden_map_sha256") != map_sha
        or approval.get("golden_manifest_sha256") != manifest_sha
        or str(approval.get("golden_run_id")) != str(golden_manifest.get("run_id"))
        or approval.get("golden_run_attempt") != golden_manifest.get("run_attempt")
        or approval.get("tested_sha") != golden_map.get("tested_sha")
        or approval.get("tested_sha") != golden_manifest.get("tested_sha")
        or approval.get("trial_id_start") != 1
        or approval.get("trial_id_end") != golden_n
        or approval.get("trial_count_per_scenario") != golden_n
        or approval.get("scenario_count") != len(expected_scenarios)
        or approval.get("independent_execution") is not True
        or approval.get("production_result_artifacts_read") is not False
        or not __import__("re").fullmatch(r"sha256:[0-9a-f]{64}", str(approval.get("golden_artifact_digest", "")))
        or not isinstance(review_checks, dict)
        or any(review_checks.get(key) is not True for key in required_review_checks)
    ):
        raise RuntimeError("S6_GATE_A_GOLDEN_APPROVAL_INVALID_OR_NOT_HASH_PINNED")
    approved_scenario_hashes = approval.get("scenario_artifact_file_sha256_by_scenario", {})
    if set(approved_scenario_hashes) != set(expected_scenarios) or any(
        approved_scenario_hashes[scenario] != scenario_manifest_by_id[scenario].get("file_sha256")
        for scenario in expected_scenarios
    ):
        raise RuntimeError("S6_GATE_A_GOLDEN_SCENARIO_ARTIFACT_APPROVAL_MISMATCH")

    return {
        "status": "APPROVED_FOR_GATE_A",
        "golden_map": golden_map,
        "golden_manifest": golden_manifest,
        "approval": approval,
        "golden_map_path": str(map_path),
        "golden_manifest_path": str(manifest_path),
        "golden_approval_path": str(approval_path),
        "golden_map_sha256": map_sha,
        "golden_manifest_sha256": manifest_sha,
        "golden_approval_sha256": approval_sha,
        "golden_run_id": str(golden_manifest.get("run_id")),
        "golden_run_attempt": golden_manifest.get("run_attempt"),
        "golden_tested_sha": golden_manifest.get("tested_sha"),
        "golden_trial_count_per_scenario": golden_n,
        "golden_artifact_digest": approval.get("golden_artifact_digest"),
    }


def evaluate_gate_a_checkpoint(
    scenario: str,
    n: int,
    production_rows: dict[int, dict[str, Any]],
    golden_evidence: dict[str, Any] | None,
    *,
    source_sha: str,
    cohort_id: str,
) -> dict[str, Any]:
    if golden_evidence is None:
        return {
            "status": "NOT_EVALUATED_NO_SAME_SOURCE_PRODUCTION_GOLDEN",
            "checked": False,
            "stable": False,
            "source_sha": source_sha,
            "cohort_id": cohort_id,
        }
    coverage_n = int(golden_evidence["golden_trial_count_per_scenario"])
    evidence = {
        "source_sha": source_sha,
        "cohort_id": cohort_id,
        "golden_run_id": golden_evidence["golden_run_id"],
        "golden_map_sha256": golden_evidence["golden_map_sha256"],
        "golden_trial_count_per_scenario": coverage_n,
    }
    if n > coverage_n:
        return {
            "status": "NOT_EVALUATED_GOLDEN_COVERAGE_INSUFFICIENT",
            "checked": False,
            "stable": False,
            "required_trial_count": n,
            "trial_count_checked": 0,
            **evidence,
        }
    fingerprints = golden_evidence["golden_map"]["scenarios"][scenario]["trial_fingerprints"]
    mismatch_ids: list[int] = []
    for trial_id in range(1, n + 1):
        row = production_rows.get(trial_id)
        actual = str(row.get("trial_fingerprint", "")) if row is not None else ""
        expected = fingerprints.get(str(trial_id))
        if not actual or actual != expected:
            mismatch_ids.append(trial_id)
    passed = not mismatch_ids
    return {
        "status": "PASS" if passed else "FAIL_FINANCIAL_TRIAL_FINGERPRINT_MISMATCH",
        "checked": True,
        "stable": passed,
        "required_trial_count": n,
        "trial_count_checked": n,
        "mismatch_count": len(mismatch_ids),
        "mismatch_trial_ids_sample": mismatch_ids[:20],
        **evidence,
    }


def evaluate_s6_aggregate_statistics(
    rows_by_scenario: dict[str, dict[int, dict[str, Any]]],
    *, source_sha: str, cohort_id: str, run_id: str,
    golden_evidence: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    """Evaluate Gate B/IUT at all completed cumulative points; never promote to final acceptance."""
    evaluations: dict[str, Any] = {}
    registry: list[dict[str, Any]] = []
    checkpoint_counts: dict[str, dict[str, int]] = {}
    max_n = max((len(rows) for rows in rows_by_scenario.values()), default=0)
    checkpoint_schedule = statistical_checkpoint_schedule(max_n)
    stability_history: dict[str, Any] = {
        "schema_version": "s6-stability-history-v1",
        "source_sha": source_sha,
        "cohort_id": cohort_id,
        "aggregation_run_id": str(run_id),
        "checkpoint_schedule": checkpoint_schedule,
        "historical_cohorts_imported": False,
        "convergence_authorized": False,
        "per_scenario": {},
    }
    for scenario in sorted(rows_by_scenario):
        point_records: list[dict[str, Any]] = []
        try:
            records = rows_by_scenario[scenario]
            ordered_rows = [records[tid] for tid in sorted(records)]
            results = [result_from_record(row) for row in ordered_rows]
            validate_cumulative_trial_ids([item.trial_id for item in results], len(results), scenario_id=scenario)
            points: list[dict[str, Any]] = []
            for n in checkpoint_schedule:
                if n > len(results):
                    continue
                sample = results[:n]
                if [item.trial_id for item in sample] != list(range(1, n + 1)):
                    raise RuntimeError(f"S6_STATISTICAL_CHECKPOINT_TRIAL_COVERAGE_INVALID:{scenario}:N{n}")
                k = stats_integrity.statistical_checkpoint_index(n)
                mean_samples = {
                    "Final_Net_Project_Equity": [int(item.final_net_project_equity) for item in sample],
                    "Partner1_Final_Entitlement": [int(item.partner1_final_entitlement) for item in sample],
                    "Partner2_Final_Entitlement": [int(item.partner2_final_entitlement) for item in sample],
                }
                try:
                    gate_b = stats_integrity.evaluate_gate_b_statistical(mean_samples, sample, k=k)
                except Exception as exc:
                    gate_b = {"status": "EVALUATION_ERROR", "stable": False, "n": n,
                              "spending_index": k, "error_type": type(exc).__name__, "error": str(exc)}
                p50 = stats_integrity.linear_quantile_fraction(
                    [int(item.cumulative_project_profit) for item in sample], Fraction(1, 2),
                )
                loss_probability = Fraction(
                    sum(1 for item in sample if int(item.cumulative_project_profit) < 0), n,
                )
                point = {
                    "n": n,
                    "spending_index": k,
                    "alpha_s_k_numerator": stats_integrity.sequential_alpha_fraction(k).numerator,
                    "alpha_s_k_denominator": stats_integrity.sequential_alpha_fraction(k).denominator,
                    "gate_a": evaluate_gate_a_checkpoint(
                        scenario, n, records, golden_evidence,
                        source_sha=source_sha, cohort_id=cohort_id,
                    ),
                    "gate_b": gate_b,
                    "p50_cumulative_project_profit": {"numerator": p50.numerator, "denominator": p50.denominator},
                    "probability_accounting_loss": {"numerator": loss_probability.numerator,
                                                     "denominator": loss_probability.denominator},
                }
                points.append(point)
                registry.append(stats_integrity.number_registry_entry(
                    f"{scenario}.N{n}.P50_Cumulative_Project_Profit", p50,
                    source=f"{source_sha}/{cohort_id}/{scenario}/N{n}/P50_Cumulative_Project_Profit",
                ))
                registry.append(stats_integrity.number_registry_entry(
                    f"{scenario}.N{n}.Probability_of_Accounting_Loss", loss_probability,
                    source=f"{source_sha}/{cohort_id}/{scenario}/N{n}/Probability_of_Accounting_Loss",
                ))
                if gate_b.get("status") not in {"EVALUATION_ERROR", "K_SPEC / BLOCKED"}:
                    for name, summary in gate_b.get("financial_means", {}).items():
                        registry.append(stats_integrity.number_registry_entry(
                            f"{scenario}.N{n}.mean.{name}",
                            Fraction(int(summary["mean_exact_numerator"]), int(summary["mean_exact_denominator"])),
                            source=f"{source_sha}/{cohort_id}/{scenario}/N{n}/GateB/{name}",
                        ))
                    for name, summary in gate_b.get("indicators", {}).get("indicators", {}).items():
                        registry.append(stats_integrity.number_registry_entry(
                            f"{scenario}.N{n}.indicator.{name}",
                            Fraction(int(summary["estimate_exact_numerator"]), int(summary["estimate_exact_denominator"])),
                            source=f"{source_sha}/{cohort_id}/{scenario}/N{n}/GateB/{name}",
                        ))
                point_records.append(point)
            transitions = [
                stats_integrity.evaluate_statistical_transition(previous, current)
                for previous, current in zip(point_records, point_records[1:])
            ]
            consecutive = 0
            for transition in transitions:
                consecutive = consecutive + 1 if transition["passed"] else 0
            evaluation = {
                "scenario_id": scenario,
                "source_sha": source_sha,
                "cohort_id": cohort_id,
                "status": "EXECUTED_POINTWISE_STATISTICS_NOT_FINAL_ACCEPTANCE",
                "checkpoint_points": point_records,
                "transitions": transitions,
                "consecutive_successful_transitions": consecutive,
                "scenario_stability": "CONVERGED" if consecutive >= constants.STABILITY_CONSECUTIVE_CHECKS_REQUIRED else "NOT_CONVERGED",
            }
        except Exception as exc:
            evaluation = {
                "scenario_id": scenario,
                "source_sha": source_sha,
                "cohort_id": cohort_id,
                "status": "EVALUATION_ERROR",
                "error_type": type(exc).__name__,
                "error": str(exc),
                "checkpoint_points": point_records,
                "transitions": [],
                "consecutive_successful_transitions": 0,
                "scenario_stability": "NOT_CONVERGED",
            }
        evaluations[scenario] = evaluation
        stability_history["per_scenario"][scenario] = {
            "checkpoint_points": evaluation["checkpoint_points"],
            "transitions": evaluation["transitions"],
            "consecutive_successful_transitions": evaluation["consecutive_successful_transitions"],
            "status": evaluation["scenario_stability"],
        }
        for point in evaluation["checkpoint_points"]:
            counts = checkpoint_counts.setdefault(str(point["n"]), {"PASS": 0, "FAIL": 0, "EVALUATION_ERROR": 0, "BLOCKED": 0})
            status = str(point["gate_b"].get("status", "EVALUATION_ERROR"))
            counts[status if status in counts else "BLOCKED"] += 1

    latest_n = max((int(point["n"]) for item in evaluations.values() for point in item.get("checkpoint_points", [])), default=0)
    transition_count = sum(len(item.get("transitions", [])) for item in evaluations.values())
    passed_transitions = sum(
        1 for item in evaluations.values() for transition in item.get("transitions", [])
        if transition.get("passed") is True
    )
    latest_gate_a_statuses = [
        item["checkpoint_points"][-1]["gate_a"]["status"]
        for item in evaluations.values() if item.get("checkpoint_points")
    ]
    latest_gate_b_statuses = [
        item["checkpoint_points"][-1]["gate_b"].get("status", "EVALUATION_ERROR")
        for item in evaluations.values() if item.get("checkpoint_points")
    ]
    if not golden_evidence:
        gate_a_final = "NOT_EVALUATED_NO_SAME_SOURCE_PRODUCTION_GOLDEN"
    elif any(status.startswith("FAIL_") for status in latest_gate_a_statuses):
        gate_a_final = "FAIL"
    elif len(latest_gate_a_statuses) == len(rows_by_scenario) and all(status == "PASS" for status in latest_gate_a_statuses):
        gate_a_final = "PASS"
    elif "NOT_EVALUATED_GOLDEN_COVERAGE_INSUFFICIENT" in latest_gate_a_statuses:
        gate_a_final = "NOT_EVALUATED_GOLDEN_COVERAGE_INSUFFICIENT"
    else:
        gate_a_final = "NOT_EVALUATED_INCOMPLETE_GATE_A_COVERAGE"

    if any(status == "FAIL" for status in latest_gate_b_statuses):
        gate_b_final = "FAIL_SCOPED"
    elif len(latest_gate_b_statuses) == len(rows_by_scenario) and all(status == "PASS" for status in latest_gate_b_statuses):
        gate_b_final = "PASS_SCOPED"
    elif any(status in {"EVALUATION_ERROR", "K_SPEC / BLOCKED"} for status in latest_gate_b_statuses):
        gate_b_final = "BLOCKED_EVALUATION_ERROR"
    else:
        gate_b_final = "NOT_EVALUATED"

    all_scenarios_converged = (
        len(evaluations) == len(rows_by_scenario)
        and all(item.get("scenario_stability") == "CONVERGED" for item in evaluations.values())
    )
    scenario_stability_final = (
        "CONVERGED"
        if all_scenarios_converged and gate_a_final == "PASS" and gate_b_final == "PASS_SCOPED"
        else "NOT_CONVERGED"
    )
    evaluation_summary = {
        "schema_version": "s6-v23-statistical-evaluation-v1",
        "status": "EXECUTED_POINTWISE_STATISTICS_NOT_FINAL_ACCEPTANCE",
        "run_id": str(run_id), "source_sha": source_sha, "cohort_id": cohort_id,
        "latest_checkpoint_n": latest_n, "scenario_count": len(evaluations),
        "checkpoint_gate_b_counts": checkpoint_counts,
        "transition_count": transition_count, "successful_transition_count": passed_transitions,
        "gate_a_final": gate_a_final,
        "gate_b_final": gate_b_final,
        "scenario_stability_final": scenario_stability_final,
        "gate_a_golden_evidence": {
            "status": golden_evidence["status"] if golden_evidence else "NOT_PROVIDED",
            "golden_map_sha256": golden_evidence.get("golden_map_sha256") if golden_evidence else None,
            "golden_manifest_sha256": golden_evidence.get("golden_manifest_sha256") if golden_evidence else None,
            "golden_approval_sha256": golden_evidence.get("golden_approval_sha256") if golden_evidence else None,
            "golden_run_id": golden_evidence.get("golden_run_id") if golden_evidence else None,
            "golden_trial_count_per_scenario": golden_evidence.get("golden_trial_count_per_scenario") if golden_evidence else None,
            "golden_artifact_digest": golden_evidence.get("golden_artifact_digest") if golden_evidence else None,
        },
        "test192_reuse": {
            "run_ids": [40531095239, 40546712685],
            "proof_sha256": "f6add77e9e7ff8256b36b661df337897de10cd96d7e00b0d9dfa660dea0e927b",
            "rerun": False,
        },
        "scenarios": evaluations,
    }

    stability_history["final_gate_a_status"] = evaluation_summary["gate_a_final"]
    stability_history["final_gate_b_status"] = evaluation_summary["gate_b_final"]
    stability_history["gate_a_golden_evidence"] = evaluation_summary["gate_a_golden_evidence"]
    number_registry = {
        "schema_version": "number-registry-v1",
        "rounding": "Decimal.quantize(Decimal('0.01'), ROUND_HALF_EVEN); exact numerator/denominator retained",
        "entries": registry,
    }
    return evaluation_summary, stability_history, number_registry


def aggregate(args: argparse.Namespace) -> dict[str, Any]:
    started_at_utc = utc_now()
    started = time.monotonic()
    require_source_sha(args.source_sha); c100_reuse=verify_c100_reuse()
    source_run_id = str(getattr(args,"source_run_id",None) or args.run_id)
    source_run_attempt = int(getattr(args,"source_run_attempt",None) or args.run_attempt)
    requested_n = args.trials
    source_metadata_path=getattr(args,"source_run_metadata_json",None)
    source_metadata={}
    if source_metadata_path:
        source_metadata=json.loads(Path(source_metadata_path).read_text(encoding="utf-8"))
        if str(source_metadata.get("source_run_id"))!=source_run_id or int(source_metadata.get("source_run_attempt",-1))!=source_run_attempt:
            raise RuntimeError("S6_SOURCE_RUN_METADATA_IDENTITY_MISMATCH")
        if source_metadata.get("source_sha")!=args.source_sha:
            raise RuntimeError("S6_SOURCE_RUN_METADATA_SOURCE_SHA_MISMATCH")
    root=Path(args.input_root); manifests=sorted(root.rglob("scenario_manifest.json")); by_scenario={}
    manifest_pairs=[(mp,json.loads(mp.read_text(encoding="utf-8"))) for mp in manifests]
    checkpoint_n=resolve_aggregate_checkpoint_n(
        requested_n,[manifest.get("trial_count") for _,manifest in manifest_pairs],
        getattr(args,"_s6_checkpoint_config",None),
    )
    previous_checkpoint_n(checkpoint_n)
    for mp,m in manifest_pairs:
        scenario=str(m.get("scenario_id",""))
        if scenario in by_scenario: raise RuntimeError(f"S6_DUPLICATE_SCENARIO_ARTIFACT:{scenario}")
        if m.get("source_sha")!=args.source_sha: raise RuntimeError(f"S6_SOURCE_SHA_MISMATCH:{scenario}")
        if str(m.get("run_id"))!=source_run_id or int(m.get("run_attempt",-1))!=source_run_attempt:
            raise RuntimeError(f"S6_RUN_IDENTITY_MISMATCH:{scenario}")
        if m.get("cohort_id")!=f"s6-v23-{args.source_sha[:8]}":
            raise RuntimeError(f"S6_COHORT_ID_MISMATCH:{scenario}")
        if m.get("trial_count")!=checkpoint_n or m.get("trial_id_start")!=1 or m.get("trial_id_end")!=checkpoint_n: raise RuntimeError(f"S6_TRIAL_COUNT_MISMATCH:{scenario}")
        base=mp.parent
        validate_required_scenario_files(base, m)
        by_scenario[scenario]=(base,m)
    # C100 is a separate, immutable S4 cohort. It is verified and referenced above,
    # never merged into the new stochastic SOURCE_SHA/cohort or counted as independent samples.
    expected=stochastic_scenario_ids()
    if source_metadata_path:
        if set(source_metadata.get("scenarios",{}))!=expected:
            raise RuntimeError("S6_SOURCE_RUN_METADATA_SCENARIO_COVERAGE_MISMATCH")
        for scenario,metadata in source_metadata["scenarios"].items():
            if metadata.get("conclusion")!="success" or metadata.get("exit_code")!=0:
                raise RuntimeError(f"S6_SOURCE_RUN_METADATA_JOB_NOT_SUCCESS:{scenario}")
            if not metadata.get("started_at_utc") or not metadata.get("finished_at_utc") or not metadata.get("package_versions") or not metadata.get("python_version"):
                raise RuntimeError(f"S6_SOURCE_RUN_METADATA_INCOMPLETE:{scenario}")
    if set(by_scenario)!=expected:
        raise RuntimeError(f"S6_SCENARIO_COVERAGE_MISMATCH:missing={sorted(expected-set(by_scenario))}:extra={sorted(set(by_scenario)-expected)}")
    manifest_versions={str(item[1].get("schema_version","LEGACY_SCHEMA_UNKNOWN")) for item in by_scenario.values()}
    if len(manifest_versions)!=1: raise RuntimeError(f"S6_AGGREGATE_DAILY_SCHEMA_MIXED:{sorted(manifest_versions)}")
    all_have_path_contract=manifest_versions=={SCENARIO_MANIFEST_SCHEMA_VERSION}
    all_trials=[]; all_daily=[]; summaries=[]
    scenario_rows_by_id={}; scenario_path_fingerprints={}; scenario_provenance={}
    for scenario in sorted(expected):
        base,m=by_scenario[scenario]
        rows=pq.read_table(base/"trials_summary.parquet").to_pylist()
        validate_unique_trial_ids(rows, checkpoint_n, context=scenario)
        ids=[row["trial_id"] for row in rows]
        validate_cumulative_trial_ids(ids, checkpoint_n, scenario_id=scenario)
        for row in rows:
            calculated = monte_carlo.trial_fingerprint(result_from_record(row))
            if row.get("trial_fingerprint") != calculated:
                raise RuntimeError(f"S6_FINANCIAL_TRIAL_FINGERPRINT_RECOMPUTE_MISMATCH:{scenario}:{row.get('trial_id')}")
        daily=pq.read_table(base/"daily_distribution.parquet").to_pylist()
        if not daily: raise RuntimeError(f"S6_DAILY_DISTRIBUTION_EMPTY:{scenario}")
        snapshots=pq.read_table(base/"daily_snapshots.parquet").to_pylist()
        stats_integrity.validate_daily_distribution_rows(
            daily, scenario_id=scenario, source_sha=args.source_sha,
            cohort_id=f"s6-v23-{args.source_sha[:8]}",
            expected_dates=sorted({str(row["date"]) for row in snapshots}),
            expected_trial_count=checkpoint_n,
        )
        if all_have_path_contract:
            require_daily_path_manifest_contract(m,expected_source_sha=args.source_sha,expected_cohort_id=f"s6-v23-{args.source_sha[:8]}",expected_scenario_id=scenario,expected_master_seed=constants.MASTER_SEED,expected_trial_count=checkpoint_n,model_schema_version=SCHEMA_VERSION)
            path_evidence=build_daily_path_identity_evidence(snapshots,source_sha=args.source_sha,cohort_id=f"s6-v23-{args.source_sha[:8]}",master_seed=constants.MASTER_SEED,scenario_id=scenario,expected_trial_ids=range(1,checkpoint_n+1),expected_start_date=constants.PROJECT_START_DATE.isoformat(),model_schema_version=SCHEMA_VERSION)
            if path_evidence["summary"]!=m.get("daily_path_identity_contract"): raise RuntimeError(f"S6_DAILY_PATH_IDENTITY_MANIFEST_MISMATCH:{scenario}")
            path_fingerprints=path_evidence["path_content_fingerprint_by_trial"];n_unique_daily_paths=int(path_evidence["summary"]["unique_daily_path_count"])
            daily_balance_schema_status="PASS_SCOPED_POST_WRITE_BALANCE_CHECK";daily_path_identity_status="PASS_SCOPED_DAILY_BALANCE_PATH_CONTRACT"
            n_unique_paths=resolve_n_unique_paths(scenario,[int(row.get("rng_draw_count",0)) for row in rows],n_unique_daily_paths)
            reported_n_unique_paths,reported_n_unique_paths_status=reported_unique_path_evidence(m,n_unique_paths,n_unique_daily_paths,args.source_sha,f"s6-v23-{args.source_sha[:8]}")
        else:
            path_fingerprints=daily_path_fingerprints(snapshots)
            if set(path_fingerprints)!=set(range(1,checkpoint_n+1)):raise RuntimeError(f"S6_DAILY_PATH_TRIAL_COVERAGE_MISMATCH:{scenario}")
            n_unique_daily_paths=len(set(path_fingerprints.values()))
            n_unique_paths=resolve_n_unique_paths(scenario,[int(row.get("rng_draw_count",0)) for row in rows],n_unique_daily_paths)
            reported_n_unique_paths,reported_n_unique_paths_status=reported_unique_path_evidence(m,n_unique_paths,n_unique_daily_paths,args.source_sha,f"s6-v23-{args.source_sha[:8]}")
            daily_balance_schema_status="MISSING_EVIDENCE";daily_path_identity_status="MISSING_EVIDENCE_IDENTITY_BOUND_PATH_MAP"
        n_unique_financial_outcomes=len({str(row["trial_fingerprint"]) for row in rows})
        rng_audit_records_verified=validate_cumulative_rng_audit(rows,args.source_sha)
        if m.get("unique_terminal_fingerprints", n_unique_financial_outcomes) != n_unique_financial_outcomes:
            raise RuntimeError(f"S6_SCENARIO_UNIQUE_TERMINAL_FINGERPRINTS_MISMATCH:{scenario}")
        provenance_path=base/"opt1_provenance.json"
        if not provenance_path.is_file():
            raise RuntimeError(f"S6_OPT1_PROVENANCE_MISSING:{scenario}")
        provenance=json.loads(provenance_path.read_text(encoding="utf-8"))
        scenario_rows_by_id[scenario]={int(row["trial_id"]):row for row in rows}
        scenario_path_fingerprints[scenario]=path_fingerprints
        scenario_provenance[scenario]=provenance
        all_trials.extend(rows); all_daily.extend(daily)
        n_closed=sum(1 for row in rows if row.get("final_close_date") is not None)
        n_censored=len(rows)-n_closed
        if n_closed+n_censored!=len(rows): raise RuntimeError(f"S6_CENSORING_COUNT_MISMATCH:{scenario}")
        srcmeta=source_metadata.get("scenarios",{}).get(scenario,{})
        summaries.append({"scenario_id":scenario,"status":m.get("status"),
            "n_total":len(rows),"n_closed":n_closed,"n_censored":n_censored,
            "n_unique_paths":reported_n_unique_paths,"n_unique_paths_status":reported_n_unique_paths_status,
            "daily_balance_schema_status":daily_balance_schema_status,"daily_path_identity_status":daily_path_identity_status,
            "unique_daily_paths":n_unique_daily_paths,
            "unique_terminal_fingerprints":n_unique_financial_outcomes,
            "n_unique_financial_outcomes":n_unique_financial_outcomes,
            "rng_audit_validation_status":"PASS","rng_audit_records_verified":rng_audit_records_verified,
            "n_unique_daily_paths_diagnostic":n_unique_daily_paths,
            "opt1_policy":m["opt1_policy"],
            "source_sha":m["source_sha"],"cohort_id":m["cohort_id"],
            "git_commit":m.get("git_commit") or srcmeta.get("git_commit"),
            "governing_decision_id":m.get("governing_decision_id"),
            "governing_reference_sha256":m.get("governing_reference_sha256"),
            "execution_metadata_source":"scenario_manifest" if all(m.get(k) for k in ("git_commit","started_at_utc","finished_at_utc","python_version","package_versions")) else ("source_run_job_api_and_logs" if srcmeta else "pinned_workflow_and_source_sha"),
            "run_id":m.get("run_id"),"run_attempt":m.get("run_attempt"),
            "source_job_id":srcmeta.get("job_id"),"source_job_name":srcmeta.get("job_name"),
            "source_job_log_sha256":srcmeta.get("job_log_sha256"),
            "started_at_utc":m.get("started_at_utc") or srcmeta.get("started_at_utc"),
            "finished_at_utc":m.get("finished_at_utc") or srcmeta.get("finished_at_utc"),
            "command_argv":m.get("command_argv") or srcmeta.get("command_argv") or reconstructed_scenario_command(
                scenario,args.source_sha,source_run_id,source_run_attempt,checkpoint_n,int(m.get("workers",2))),
            "exit_code":m.get("exit_code",srcmeta.get("exit_code",0)),
            "python_version":m.get("python_version") or srcmeta.get("python_version"),
            "package_versions":m.get("package_versions") or srcmeta.get("package_versions"),
            "elapsed_seconds":m.get("elapsed_seconds") or srcmeta.get("elapsed_seconds"),
            "files":m.get("files",{}),"artifact_files_verified":True,
            "trial_fingerprint_map_sha256":hashlib.sha256("".join(f'{row["trial_id"]}|{row["trial_fingerprint"]}\n' for row in rows).encode()).hexdigest(),
            "scenario_manifest_sha256":sha256_file(base/"scenario_manifest.json")})
    opt1_derived_trial_rows=0
    for scenario in sorted(expected):
        collection=int(scenario.split("_",1)[0][1:])
        recovery=int(scenario.split("_",1)[1][1:])
        rows=scenario_rows_by_id[scenario]
        provenance=scenario_provenance[scenario]
        manifest=by_scenario[scenario][1]
        expected_ids=set(range(1,checkpoint_n+1))
        base_scenario=f"C{collection:03d}_G100"
        if recovery==100:
            expected_derived=set()
            expected_full=expected_ids
            expected_policy="G100_BASE_FULL_RUN_INCREMENTAL_RANGE"
        elif collection in OPT1_ENABLED_COLLECTIONS:
            base_rows=scenario_rows_by_id[base_scenario]
            expected_derived={tid for tid,row in base_rows.items() if int(row.get("claims_created",0))==0}
            expected_full=expected_ids-expected_derived
            expected_policy=("OPT1_ENABLED_DERIVED_ZERO_CLAIM_TRIALS_FULL_RUN_POSITIVE_CLAIM_TRIALS_INCREMENTAL_RANGE"
                if expected_derived else "OPT1_ENABLED_NO_ZERO_CLAIM_TRIALS_IN_INCREMENTAL_RANGE_FULL_RUN")
            for tid in expected_derived:
                row=rows[tid]; base_row=base_rows[tid]
                if row.get("derived_from")!=f"DERIVED_FROM={base_scenario}":
                    raise RuntimeError(f"S6_OPT1_DERIVED_FROM_MISMATCH:{scenario}:{tid}")
                if int(row.get("claims_created",-1))!=0 or row.get("trial_fingerprint")!=base_row.get("trial_fingerprint"):
                    raise RuntimeError(f"S6_OPT1_FINANCIAL_EQUIVALENCE_MISMATCH:{scenario}:{tid}")
                if scenario_path_fingerprints[scenario][tid]!=scenario_path_fingerprints[base_scenario][tid]:
                    raise RuntimeError(f"S6_OPT1_DAILY_PATH_MISMATCH:{scenario}:{tid}")
            for tid in expected_full:
                if rows[tid].get("derived_from") is not None or int(rows[tid].get("claims_created",0))<=0:
                    raise RuntimeError(f"S6_OPT1_POSITIVE_CLAIM_FULL_RUN_MISMATCH:{scenario}:{tid}")
        else:
            expected_derived=set()
            expected_full=expected_ids
            expected_policy="OPT1_INELIGIBLE_FULL_RUN_INCREMENTAL_RANGE"
        actual_derived={tid for tid,row in rows.items() if row.get("derived_from") is not None}
        if actual_derived!=expected_derived:
            raise RuntimeError(f"S6_OPT1_DERIVED_TRIAL_SET_MISMATCH:{scenario}")
        if manifest.get("opt1_policy")!=expected_policy or provenance.get("policy")!=expected_policy:
            raise RuntimeError(f"S6_OPT1_POLICY_MISMATCH:{scenario}")
        if provenance.get("scenario_id")!=scenario or int(provenance.get("sample_trial_count",-1))!=checkpoint_n:
            raise RuntimeError(f"S6_OPT1_PROVENANCE_IDENTITY_MISMATCH:{scenario}")
        if int(provenance.get("eligible_zero_claim_trials",-1))!=sum(1 for row in rows.values() if int(row.get("claims_created",0))==0):
            raise RuntimeError(f"S6_OPT1_ZERO_CLAIM_COUNT_MISMATCH:{scenario}")
        if int(provenance.get("derived_trial_count",-1))!=len(expected_derived):
            raise RuntimeError(f"S6_OPT1_DERIVED_COUNT_MISMATCH:{scenario}")
        if sorted(int(tid) for tid in provenance.get("full_run_trial_ids",[]))!=sorted(expected_full):
            raise RuntimeError(f"S6_OPT1_FULL_RUN_ID_SET_MISMATCH:{scenario}")
        actual_derived_records={int(item["trial_id"]):(item.get("derived_from"),item.get("trial_fingerprint"))
            for item in provenance.get("derived_trials",[])}
        expected_derived_records={tid:(rows[tid].get("derived_from"),rows[tid].get("trial_fingerprint")) for tid in expected_derived}
        if actual_derived_records!=expected_derived_records:
            raise RuntimeError(f"S6_OPT1_DERIVED_PROVENANCE_MISMATCH:{scenario}")
        opt1_derived_trial_rows+=len(expected_derived)
    golden_evidence = load_approved_gate_a_golden(
        getattr(args, "golden_map", None),
        getattr(args, "golden_manifest", None),
        getattr(args, "golden_approval", None),
        expected_source_sha=args.source_sha,
        expected_cohort_id=f"s6-v23-{args.source_sha[:8]}",
    )
    out=Path(args.output_dir); out.mkdir(parents=True,exist_ok=True)
    gate_a_evidence_output_paths: list[Path] = []
    if golden_evidence is not None:
        for source_key, target_name in (
            ("golden_map_path", "gate_a_golden_fingerprints.json"),
            ("golden_manifest_path", "gate_a_golden_manifest.json"),
            ("golden_approval_path", "gate_a_golden_approval.json"),
        ):
            target_path = out / target_name
            target_path.write_bytes(Path(golden_evidence[source_key]).read_bytes())
            gate_a_evidence_output_paths.append(target_path)
    statistical_evaluation, stability_history, number_registry = evaluate_s6_aggregate_statistics(
        scenario_rows_by_id, source_sha=args.source_sha,
        cohort_id=f"s6-v23-{args.source_sha[:8]}", run_id=args.run_id,
        golden_evidence=golden_evidence,
    )
    for name,rows in (("trials_summary.parquet",all_trials),("daily_distribution.parquet",all_daily)):
        pq.write_table(pa.Table.from_pylist(rows),out/name,compression="zstd")
    write_json(out/"c100_reuse.json",c100_reuse)
    write_json(out/"statistical_evaluation.json",statistical_evaluation)
    write_json(out/"stability_history.json",stability_history)
    write_json(out/"number_registry.json",number_registry)
    output_paths=[
        out/"trials_summary.parquet",out/"daily_distribution.parquet",out/"c100_reuse.json",
        out/"statistical_evaluation.json",out/"stability_history.json",out/"number_registry.json",
        *gate_a_evidence_output_paths,
    ]
    source_metadata_sha256=None
    if source_metadata_path:
        source_metadata_bytes=Path(source_metadata_path).read_bytes()
        (out/"source_run_metadata.json").write_bytes(source_metadata_bytes)
        source_metadata_sha256=hashlib.sha256(source_metadata_bytes).hexdigest()
        output_paths.append(out/"source_run_metadata.json")
    files={p.name:{"sha256":sha256_file(p),"size_bytes":p.stat().st_size} for p in output_paths}
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
        "rng_audit_validation":{"status":"PASS","records_verified":sum(x["rng_audit_records_verified"] for x in summaries),"scope":"all cumulative trial IDs per scenario; checksum uniqueness only where rng_draw_count > 0"},
        "total_scenario_combinations":len(expected)+len(c100_reuse["scenario_ids"]),
        "c100_reused_scenario_count":len(c100_reuse["scenario_ids"]),
        "scenario_summaries":summaries,"c100_reuse":c100_reuse,
        "daily_balance_schema_status":"PASS_SCOPED_POST_WRITE_BALANCE_CHECK" if all_have_path_contract else "MISSING_EVIDENCE",
        "daily_path_identity_status":"PASS_SCOPED_DAILY_BALANCE_PATH_CONTRACT" if all_have_path_contract else "MISSING_EVIDENCE_IDENTITY_BOUND_PATH_MAP",
        "opt1_audit":{"status":"PASS","scenario_count":len(expected),
            "derived_trial_rows":opt1_derived_trial_rows,"full_run_scenario_rows":len(expected)*checkpoint_n-opt1_derived_trial_rows},
        "source_run_metadata":{"status":"VERIFIED_FROM_GITHUB_ACTIONS_JOB_LOGS" if source_metadata_path else ("SOURCE_SCENARIO_MANIFESTS_COMPLETE" if all(all(row.get(k) for k in ("git_commit","started_at_utc","finished_at_utc","python_version","package_versions","command_argv")) for row in summaries) else "NOT_PROVIDED"),
            "sha256":source_metadata_sha256,"scenario_count":len(source_metadata.get("scenarios",{})) if source_metadata_path else (len(expected) if all(all(row.get(k) for k in ("git_commit","started_at_utc","finished_at_utc","python_version","package_versions","command_argv")) for row in summaries) else 0)},
        "statistical_evaluation":{
            "status":statistical_evaluation["status"],
            "latest_checkpoint_n":statistical_evaluation["latest_checkpoint_n"],
            "scenario_count":statistical_evaluation["scenario_count"],
            "checkpoint_gate_b_counts":statistical_evaluation["checkpoint_gate_b_counts"],
            "transition_count":statistical_evaluation["transition_count"],
            "successful_transition_count":statistical_evaluation["successful_transition_count"],
            "gate_a_final":statistical_evaluation["gate_a_final"],
            "gate_b_final":statistical_evaluation["gate_b_final"],
            "scenario_stability_final":statistical_evaluation["scenario_stability_final"],
        },
        "test192_reuse":{"run_ids":[40531095239,40546712685],"proof_sha256":"f6add77e9e7ff8256b36b661df337897de10cd96d7e00b0d9dfa660dea0e927b","rerun":False},
        "gate_a_golden_evidence":statistical_evaluation["gate_a_golden_evidence"],
        "acceptance_status":{"gate_a":statistical_evaluation["gate_a_final"],
            "gate_b":statistical_evaluation["gate_b_final"],
            "stability":statistical_evaluation["scenario_stability_final"],
            "n_unique_paths":"COMPUTED_FROM_UNIQUE_DAILY_PATHS" if all(row["n_unique_paths"] is not None for row in summaries) else "UNDEFINED_BUSINESS_RULE"},
        "files":files}
    write_json(out/"manifest.json",manifest)
    print(json.dumps({
        "status": "S6_STATISTICAL_EVALUATION_SUMMARY",
        "checkpoint_n": statistical_evaluation["latest_checkpoint_n"],
        "checkpoint_gate_b_counts": statistical_evaluation["checkpoint_gate_b_counts"],
        "transition_count": statistical_evaluation["transition_count"],
        "successful_transition_count": statistical_evaluation["successful_transition_count"],
        "gate_a_final": statistical_evaluation["gate_a_final"],
        "gate_b_final": statistical_evaluation["gate_b_final"],
        "stability_final": statistical_evaluation["scenario_stability_final"],
    }, ensure_ascii=False, sort_keys=True))
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
    p.add_argument("--source-run-metadata-json")
    p.add_argument("--trials",type=int,default=constants.STATISTICAL_CHECK_START_N, help="Cumulative checkpoint N: 300, 600, 1200, 2400, ...")
    p.add_argument("--trial-start",type=int,default=None,help="First incremental trial ID; defaults to previous checkpoint N + 1 (or 1 at N=300)")
    p.add_argument("--trial-end",type=int,default=None,help="Last incremental trial ID; defaults to --trials")
    p.add_argument("--workers",type=int,default=2)
    p.add_argument("--output-dir",default="results_stage7_s6/scenario")
    p.add_argument("--base-dir")
    p.add_argument("--previous-dir", help="Verified artifact for the immediately preceding cumulative checkpoint")
    p.add_argument("--input-root",default="results_stage7_s6/artifacts")
    p.add_argument("--golden-map", help="Reviewed independent stochastic Golden fingerprint map JSON")
    p.add_argument("--golden-manifest", help="Reviewed independent stochastic Golden manifest JSON")
    p.add_argument("--golden-approval", help="Hash-pinned approval record for Gate A")
    args=p.parse_args()
    require_latest_branch_commit()
    apply_action_checkpoint_config(args)
    if args.mode=="scenario":
        if not args.scenario: p.error("--scenario is required in scenario mode")
        run_scenario(args)
    else: aggregate(args)
    return 0

if __name__=="__main__": raise SystemExit(main())
