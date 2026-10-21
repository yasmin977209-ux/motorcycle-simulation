from __future__ import annotations

import hashlib
import json
import os
import re
import urllib.request
from pathlib import Path
from typing import Any

REPOSITORY = "yasmin977209-ux/motorcycle-simulation"
MANIFEST_PATH = Path("docs/stage9a/dataset_manifest.json")
EXPECTED_SCENARIOS = 25
EXPECTED_TOTAL_TRIALS = 9005
EXPECTED_SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
EXPECTED_MASTER_SEED = 20270101
EXPECTED_GLOBAL_MANIFEST_SHA256 = "892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6"
EXPECTED_C050_ARTIFACT_ID = 11503510055
EXPECTED_C050_RUN_ID = 37662891608
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")


def _fail(condition: bool, code: str) -> None:
    if not condition:
        raise RuntimeError(code)


def _get_json(endpoint: str, token: str) -> dict[str, Any]:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{REPOSITORY}/{endpoint}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "motorcycle-simulation-manifest-provenance-audit",
        },
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        _fail(response.status == 200, f"GITHUB_API_STATUS_{response.status}:{endpoint}")
        value = json.loads(response.read().decode("utf-8"))
        _fail(isinstance(value, dict), f"GITHUB_API_RESPONSE_NOT_OBJECT:{endpoint}")
        return value


def audit_manifest_artifact_pairs(
    manifest: dict[str, Any],
    fetch_json=_get_json,
    token: str | None = None,
) -> dict[str, Any]:
    _fail(manifest.get("source_sha") == EXPECTED_SOURCE_SHA, "MANIFEST_SOURCE_SHA_MISMATCH")
    _fail(manifest.get("master_seed") == EXPECTED_MASTER_SEED, "MANIFEST_MASTER_SEED_MISMATCH")
    _fail(manifest.get("total_trials") == EXPECTED_TOTAL_TRIALS, "MANIFEST_TRIAL_COUNT_MISMATCH")
    _fail(
        manifest.get("global_manifest_sha256") == EXPECTED_GLOBAL_MANIFEST_SHA256,
        "MANIFEST_GLOBAL_FINGERPRINT_MISMATCH",
    )

    artifact_map = manifest.get("artifact_manifest", {}).get("enriched_artifacts")
    run_map = manifest.get("artifact_manifest", {}).get("enrichment_run_ids")
    _fail(isinstance(artifact_map, dict), "MANIFEST_ARTIFACT_MAP_MISSING")
    _fail(isinstance(run_map, dict), "MANIFEST_RUN_MAP_MISSING")
    _fail(len(artifact_map) == EXPECTED_SCENARIOS, "MANIFEST_SCENARIO_COUNT_MISMATCH")
    _fail(set(artifact_map) == set(run_map), "MANIFEST_ARTIFACT_RUN_SCENARIO_KEYS_MISMATCH")
    _fail(
        artifact_map.get("C050_G000") == EXPECTED_C050_ARTIFACT_ID,
        "C050_G000_ARTIFACT_ID_NOT_RECONCILED",
    )
    _fail(
        run_map.get("C050_G000") == EXPECTED_C050_RUN_ID,
        "C050_G000_RECORDED_RUN_ID_CHANGED",
    )

    api_token = token or os.environ.get("GH_TOKEN")
    _fail(bool(api_token), "GH_TOKEN_MISSING")

    api_cache: dict[int, dict[int, dict[str, Any]]] = {}
    report_pairs: list[dict[str, Any]] = []
    all_ids: set[int] = set()
    for scenario in sorted(artifact_map):
        artifact_id = artifact_map[scenario]
        run_id = run_map[scenario]
        _fail(
            type(artifact_id) is int and artifact_id > 0,
            f"INVALID_ARTIFACT_ID:{scenario}",
        )
        _fail(type(run_id) is int and run_id > 0, f"INVALID_RUN_ID:{scenario}")
        _fail(artifact_id not in all_ids, f"DUPLICATE_ARTIFACT_ID:{scenario}")
        all_ids.add(artifact_id)

        if run_id not in api_cache:
            run = fetch_json(f"actions/runs/{run_id}", api_token)
            _fail(run.get("id") == run_id, f"RUN_IDENTITY_MISMATCH:{scenario}")
            run_artifacts = fetch_json(
                f"actions/runs/{run_id}/artifacts?per_page=100", api_token
            )
            _fail(run_artifacts.get("total_count", 0) <= 100, f"ARTIFACT_PAGE_INCOMPLETE:{run_id}")
            items = run_artifacts.get("artifacts")
            _fail(isinstance(items, list), f"ARTIFACT_LIST_MISSING:{run_id}")
            index: dict[int, dict[str, Any]] = {}
            for item in items:
                if not isinstance(item, dict) or type(item.get("id")) is not int:
                    raise RuntimeError(f"INVALID_ARTIFACT_RECORD:{run_id}")
                if item["id"] in index:
                    raise RuntimeError(f"DUPLICATE_ARTIFACT_API_ID:{item['id']}")
                index[item["id"]] = item
            api_cache[run_id] = index

        item = api_cache[run_id].get(artifact_id)
        _fail(item is not None, f"ARTIFACT_NOT_IN_RECORDED_RUN:{scenario}:{artifact_id}:{run_id}")
        expected_name = f"stage9a06-enriched-{scenario}"
        _fail(item.get("name") == expected_name, f"ARTIFACT_NAME_MISMATCH:{scenario}")
        _fail(item.get("workflow_run", {}).get("id") == run_id, f"ARTIFACT_PARENT_RUN_MISMATCH:{scenario}")
        _fail(item.get("expired") is False, f"ARTIFACT_EXPIRED:{scenario}")
        digest = item.get("digest")
        _fail(isinstance(digest, str) and SHA256_RE.fullmatch(digest), f"ARTIFACT_DIGEST_MISSING_OR_INVALID:{scenario}")
        size = item.get("size_in_bytes")
        _fail(type(size) is int and size > 0, f"ARTIFACT_SIZE_INVALID:{scenario}")

        report_pairs.append({
            "scenario": scenario,
            "artifact_id": artifact_id,
            "run_id": run_id,
            "artifact_name": item["name"],
            "artifact_size_bytes": size,
            "artifact_digest": digest,
            "artifact_expired": item["expired"],
            "artifact_run_match": True,
        })

    _fail(len(report_pairs) == EXPECTED_SCENARIOS, "ARTIFACT_PAIR_VERIFICATION_COUNT_MISMATCH")
    return {
        "audit_status": "PASS_SCOPED",
        "audit_scope": "all 25 Stage 9A artifact/run pairs; read-only Actions API metadata",
        "scenario_count": len(report_pairs),
        "verified_artifact_run_pairs": sum(1 for pair in report_pairs if pair["artifact_run_match"]),
        "mismatches": 0,
        "source_sha": EXPECTED_SOURCE_SHA,
        "master_seed": EXPECTED_MASTER_SEED,
        "total_trials": EXPECTED_TOTAL_TRIALS,
        "global_manifest_sha256": EXPECTED_GLOBAL_MANIFEST_SHA256,
        "manifest_c050_g000_artifact_id": artifact_map["C050_G000"],
        "manifest_c050_g000_run_id": run_map["C050_G000"],
        "unique_run_ids_checked": sorted(api_cache),
        "pairs": report_pairs,
        "historical_data_modified": False,
        "simulation_or_trials_executed": False,
        "production_workbook_built": False,
    }


def main() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    report = audit_manifest_artifact_pairs(manifest)
    output_dir = Path("stage9a_provenance_audit")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "artifact_run_pair_report.json"
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
