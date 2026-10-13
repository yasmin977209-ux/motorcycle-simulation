from __future__ import annotations

import io
import json
import os
import subprocess
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

import pyarrow.parquet as pq
import monte_carlo
from scripts.stage7_golden_reference import (
    GoldenReferenceError,
    load_golden_manifest,
    sha256_bytes,
    trial_result_sha256,
    validate_model_source,
)

STAGE7_RUN_ID = 37225915321
STAGE7_HEAD_SHA = "e0b2fab6710833774937d778097363d7a8ee8e59"
STAGE10_RUN_ID = 37709936740
STAGE10_HEAD_SHA = "ca73f2df37baacebbcad965fc5f433f129675820"
STAGE12_RUN_ID = 37964656154
STAGE12_HEAD_SHA = "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"


def _api_request(token: str, url: str) -> bytes:
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read()
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
        raise GoldenReferenceError(f"GITHUB_ARTIFACT_API_REQUEST_FAILED url={url}: {exc}") from exc


def _api_json(token: str, repo: str, endpoint: str) -> dict[str, Any]:
    raw = _api_request(token, f"https://api.github.com/repos/{repo}/{endpoint}")
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GoldenReferenceError(f"GITHUB_API_JSON_INVALID endpoint={endpoint}") from exc
    if not isinstance(data, dict):
        raise GoldenReferenceError(f"GITHUB_API_RESPONSE_INVALID endpoint={endpoint}")
    return data


def _run_identity(token: str, repo: str, run_id: int, expected_head: str) -> dict[str, Any]:
    run = _api_json(token, repo, f"actions/runs/{run_id}")
    if int(run.get("id", -1)) != run_id or run.get("head_sha") != expected_head:
        raise GoldenReferenceError(f"HISTORICAL_RUN_IDENTITY_MISMATCH run_id={run_id}")
    if run.get("status") != "completed":
        raise GoldenReferenceError(f"HISTORICAL_RUN_NOT_COMPLETED run_id={run_id}")
    return run


def _artifact_archive(token: str, repo: str, run_id: int, name: str, expected_head: str) -> tuple[bytes, dict[str, Any]]:
    data = _api_json(token, repo, f"actions/runs/{run_id}/artifacts?per_page=100")
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list):
        raise GoldenReferenceError(f"HISTORICAL_ARTIFACT_LIST_INVALID run_id={run_id}")
    matches = [a for a in artifacts if a.get("name") == name]
    if len(matches) != 1:
        raise GoldenReferenceError(
            f"HISTORICAL_ARTIFACT_COUNT_MISMATCH run_id={run_id} name={name} count={len(matches)}"
        )
    artifact = matches[0]
    if artifact.get("expired") is not False:
        raise GoldenReferenceError(f"HISTORICAL_ARTIFACT_EXPIRED name={name}")
    digest = artifact.get("digest")
    if not isinstance(digest, str) or not digest.startswith("sha256:"):
        raise GoldenReferenceError(f"HISTORICAL_ARTIFACT_DIGEST_MISSING name={name}")
    env = os.environ.copy()
    env["GH_TOKEN"] = token
    download = subprocess.run(
        ["gh", "api", f"repos/{repo}/actions/artifacts/{int(artifact['id'])}/zip"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=env,
        timeout=120,
    )
    if download.returncode != 0:
        raise GoldenReferenceError(
            f"HISTORICAL_ARTIFACT_DOWNLOAD_FAILED name={name} "
            f"exit={download.returncode} "
            f"stderr={download.stderr.decode('utf-8', errors='replace')[-1000:]}"
        )
    archive = download.stdout
    actual = sha256_bytes(archive)
    if actual != digest.removeprefix("sha256:"):
        raise GoldenReferenceError(
            f"HISTORICAL_ARTIFACT_DIGEST_MISMATCH name={name} expected={digest} actual={actual}"
        )
    return archive, {
        "artifact_id": int(artifact["id"]),
        "artifact_name": name,
        "archive_sha256": actual,
        "archive_size_bytes": len(archive),
        "run_id": run_id,
        "run_head_sha": expected_head,
    }


def _parse_metadata(raw: bytes, *, allow_known_stage10_suffix: bool) -> tuple[dict[str, Any], str]:
    if allow_known_stage10_suffix and raw.endswith(b"}\\n"):
        raw = raw[:-2]
        mode = "known_stage10_literal_backslash_n_suffix_removed_in_memory"
    else:
        mode = "standard_json"
    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GoldenReferenceError(f"HISTORICAL_BLOCK_METADATA_INVALID mode={mode}: {exc}") from exc
    if not isinstance(result, dict):
        raise GoldenReferenceError("HISTORICAL_BLOCK_METADATA_ROOT_INVALID")
    return result, mode


def restore_historical_results(
    *,
    repo: str,
    token: str,
    scenario: str,
    source_sha: str,
    master_seed: int,
    model_source_root: str | Path,
    loaded_modules: Mapping[str, Any],
    manifest_path: str | Path,
    blocks_dir: str | Path,
) -> dict[str, Any]:
    """Restore verified existing trial rows from immutable artifacts; never execute trials."""
    if repo != "yasmin977209-ux/motorcycle-simulation":
        raise GoldenReferenceError(f"UNEXPECTED_GITHUB_REPOSITORY repo={repo}")
    if source_sha != "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b" or master_seed != 20270101:
        raise GoldenReferenceError("HISTORICAL_DATASET_IDENTITY_MISMATCH")
    model_head = validate_model_source(
        model_source_root, expected_source_sha=source_sha, loaded_modules=loaded_modules
    )
    if model_head != source_sha:
        raise GoldenReferenceError(f"PINNED_MODEL_SOURCE_SHA_MISMATCH expected={source_sha} actual={model_head}")
    manifest = load_golden_manifest(manifest_path, source_sha=source_sha, master_seed=master_seed)
    if scenario not in manifest["scenarios"]:
        raise GoldenReferenceError(f"GOLDEN_SCENARIO_MISSING scenario={scenario}")
    directory = Path(blocks_dir)
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()):
        raise GoldenReferenceError(f"HISTORICAL_RESTORE_REFUSES_NONEMPTY_BLOCK_DIRECTORY path={directory}")

    run7 = _run_identity(token, repo, STAGE7_RUN_ID, STAGE7_HEAD_SHA)
    run10 = _run_identity(token, repo, STAGE10_RUN_ID, STAGE10_HEAD_SHA)
    run12 = _run_identity(token, repo, STAGE12_RUN_ID, STAGE12_HEAD_SHA)
    if run7.get("conclusion") != "success" or run12.get("conclusion") != "success":
        raise GoldenReferenceError("OFFICIAL_STAGE7_OR_STAGE12_RUN_NOT_SUCCESS")
    # The exact, known Stage 10 run is marked failure because of a documented metadata
    # serialization defect. All selected outputs are revalidated against the official goldens.
    if run10.get("conclusion") != "failure":
        raise GoldenReferenceError(f"STAGE10_KNOWN_HISTORICAL_CONCLUSION_CHANGED actual={run10.get('conclusion')}")

    if scenario.startswith("C100_"):
        run_id, head_sha = STAGE7_RUN_ID, STAGE7_HEAD_SHA
        artifact_name = f"stage7-blocks-{scenario}-1"
        ranges = [(1, 1)]
    else:
        run_id, head_sha = STAGE10_RUN_ID, STAGE10_HEAD_SHA
        artifact_name = f"stage10-bench-{scenario}-1"
        ranges = [(1, 300), (301, 350), (351, 400), (401, 450), (451, 550)]
    archive, artifact_identity = _artifact_archive(token, repo, run_id, artifact_name, head_sha)
    golden_hashes = manifest["scenarios"][scenario]["trial_hashes"]
    restored = []
    block_evidence = []
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        names = zf.namelist()
        if len(names) != len(set(names)):
            raise GoldenReferenceError(f"HISTORICAL_ARTIFACT_DUPLICATE_MEMBERS name={artifact_name}")
        unsafe = [name for name in names if PurePosixPath(name).is_absolute() or ".." in PurePosixPath(name).parts]
        if unsafe:
            raise GoldenReferenceError(f"HISTORICAL_ARTIFACT_UNSAFE_PATHS paths={unsafe[:5]}")
        for start, end in ranges:
            parquet_name = f"block_{start}_{end}.parquet"
            metadata_name = f"block_{start}_{end}_metadata.json"
            if names.count(parquet_name) != 1 or names.count(metadata_name) != 1:
                raise GoldenReferenceError(
                    f"HISTORICAL_ARTIFACT_BLOCK_MEMBER_MISSING scenario={scenario} range={start}-{end}"
                )
            raw_meta = zf.read(metadata_name)
            stage10_extension = not scenario.startswith("C100_") and (start, end) == (451, 550)
            metadata, parse_mode = _parse_metadata(raw_meta, allow_known_stage10_suffix=stage10_extension)
            expected_run_id = STAGE7_RUN_ID if end <= 450 else STAGE10_RUN_ID
            expected_fields = {
                "scenario": scenario,
                "source_sha": source_sha,
                "trial_id_start": start,
                "trial_id_end": end,
                "trial_count": end - start + 1,
                "log_events": False,
            }
            for key, expected in expected_fields.items():
                if metadata.get(key) != expected:
                    raise GoldenReferenceError(
                        f"HISTORICAL_BLOCK_METADATA_MISMATCH scenario={scenario} range={start}-{end} field={key}"
                    )
            if str(metadata.get("run_id")) != str(expected_run_id):
                raise GoldenReferenceError(f"HISTORICAL_BLOCK_RUN_MISMATCH scenario={scenario} range={start}-{end}")
            raw_parquet = zf.read(parquet_name)
            try:
                rows = pq.read_table(io.BytesIO(raw_parquet)).to_pylist()
            except Exception as exc:
                raise GoldenReferenceError(f"HISTORICAL_PARQUET_INVALID scenario={scenario} range={start}-{end}: {exc}") from exc
            if len(rows) != end - start + 1:
                raise GoldenReferenceError(f"HISTORICAL_ROW_COUNT_MISMATCH scenario={scenario} range={start}-{end}")
            metadata_hashes = metadata.get("per_trial_sha256")
            if not isinstance(metadata_hashes, list) or len(metadata_hashes) != len(rows):
                raise GoldenReferenceError(f"HISTORICAL_METADATA_HASH_COUNT_MISMATCH scenario={scenario} range={start}-{end}")
            block_results = []
            for offset, row in enumerate(rows):
                trial_id = start + offset
                if int(row.get("trial_id", -1)) != trial_id or row.get("scenario_id") != scenario:
                    raise GoldenReferenceError(f"HISTORICAL_ROW_KEY_MISMATCH scenario={scenario} trial_id={trial_id}")
                actual_hash = trial_result_sha256(row)
                if metadata_hashes[offset] != actual_hash or golden_hashes.get(str(trial_id)) != actual_hash:
                    raise GoldenReferenceError(f"HISTORICAL_GOLDEN_HASH_MISMATCH scenario={scenario} trial_id={trial_id}")
                block_results.append(monte_carlo.TrialResult(**row))
            actual_block_fingerprint = monte_carlo.fingerprint_trial_results(block_results)
            if metadata.get("fingerprint_sha256") != actual_block_fingerprint:
                raise GoldenReferenceError(f"HISTORICAL_BLOCK_FINGERPRINT_MISMATCH scenario={scenario} range={start}-{end}")
            restored.extend(block_results)
            # Preserve the source Parquet and metadata byte-for-byte.
            (directory / parquet_name).write_bytes(raw_parquet)
            (directory / metadata_name).write_bytes(raw_meta)
            block_evidence.append({
                "range": f"{start}-{end}",
                "run_id": expected_run_id,
                "parquet_sha256": sha256_bytes(raw_parquet),
                "metadata_sha256": sha256_bytes(raw_meta),
                "fingerprint_sha256": actual_block_fingerprint,
                "trial_hashes_verified": len(rows),
                "metadata_parse_mode": parse_mode,
            })

    restored.sort(key=lambda result: result.trial_id)
    expected_count = 1 if scenario.startswith("C100_") else 550
    if [result.trial_id for result in restored] != list(range(1, expected_count + 1)):
        raise GoldenReferenceError(f"HISTORICAL_TRIAL_SEQUENCE_MISMATCH scenario={scenario}")
    actual_dataset_fp = monte_carlo.fingerprint_trial_results(restored)
    expected_dataset_fp = manifest["scenarios"][scenario]["historical_trial_result_fingerprint_sha256"]
    if actual_dataset_fp != expected_dataset_fp:
        raise GoldenReferenceError(f"HISTORICAL_DATASET_FINGERPRINT_MISMATCH scenario={scenario}")

    legacy_points = []
    if not scenario.startswith("C100_"):
        with zipfile.ZipFile(io.BytesIO(archive)) as zf:
            if zf.namelist().count("resume_descriptor.json") != 1:
                raise GoldenReferenceError("HISTORICAL_RESUME_DESCRIPTOR_MISSING")
            descriptor, _ = _parse_metadata(zf.read("resume_descriptor.json"), allow_known_stage10_suffix=True)
            legacy_points = sorted({
                int(item["n"]) for item in descriptor.get("baseline_stability_history", [])
                if isinstance(item, dict) and item.get("n") is not None
            })
    return {
        "status": "PASS",
        "restoration_only": True,
        "simulation_or_trial_executed": False,
        "historical_trials_rerun": False,
        "historical_dataset_modified": False,
        "historical_artifacts_modified": False,
        "scenario": scenario,
        "source_sha": source_sha,
        "master_seed": master_seed,
        "restored_trial_count": len(restored),
        "historical_trial_result_fingerprint_sha256": actual_dataset_fp,
        "canonical_reference_id": manifest["canonical_reference_id"],
        "global_golden_trial_map_sha256": manifest["global_ordered_trial_hash_map_sha256"],
        "stage7_run_id": STAGE7_RUN_ID,
        "stage7_run_head_sha": STAGE7_HEAD_SHA,
        "stage7_run_conclusion": run7.get("conclusion"),
        "stage10_run_id": STAGE10_RUN_ID if not scenario.startswith("C100_") else None,
        "stage10_run_head_sha": STAGE10_HEAD_SHA if not scenario.startswith("C100_") else None,
        "stage10_run_conclusion": run10.get("conclusion") if not scenario.startswith("C100_") else None,
        "stage12_run_id": STAGE12_RUN_ID,
        "stage12_run_head_sha": STAGE12_HEAD_SHA,
        "source_artifact": artifact_identity,
        "blocks": block_evidence,
        "legacy_linear_checkpoint_n_discarded_from_current_policy": legacy_points,
    }


__all__ = ["restore_historical_results"]
