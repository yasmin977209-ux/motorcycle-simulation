from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.audit_stage9a_artifact_run_provenance import (
    EXPECTED_C050_ARTIFACT_ID,
    EXPECTED_C050_RUN_ID,
    audit_manifest_artifact_pairs,
)

MANIFEST_PATH = Path("docs/stage9a/dataset_manifest.json")


def _manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def _fake_fetch_factory(manifest: dict):
    artifact_map = manifest["artifact_manifest"]["enriched_artifacts"]
    run_map = manifest["artifact_manifest"]["enrichment_run_ids"]

    def fake_fetch(endpoint: str, token: str) -> dict:
        assert token == "test-read-only-token"
        parts = endpoint.split("/")
        if len(parts) == 3 and parts[0] == "actions" and parts[1] == "runs":
            return {"id": int(parts[2]), "head_sha": "synthetic-run-head"}
        if len(parts) == 4 and parts[0] == "actions" and parts[1] == "runs" and parts[3].startswith("artifacts?"):
            run_id = int(parts[2])
            entries = []
            for scenario, artifact_id in artifact_map.items():
                if run_map[scenario] != run_id:
                    continue
                entries.append({
                    "id": artifact_id,
                    "name": f"stage9a06-enriched-{scenario}",
                    "size_in_bytes": 1000,
                    "digest": "sha256:" + ("a" * 64),
                    "expired": False,
                    "workflow_run": {"id": run_id},
                })
            return {"total_count": len(entries), "artifacts": entries}
        raise AssertionError(f"Unexpected fake GitHub API endpoint: {endpoint}")

    return fake_fetch


def test_candidate_manifest_records_all_25_artifacts_under_their_runs() -> None:
    manifest = _manifest()
    report = audit_manifest_artifact_pairs(
        manifest, fetch_json=_fake_fetch_factory(manifest), token="test-read-only-token"
    )

    assert report["audit_status"] == "PASS_SCOPED"
    assert report["scenario_count"] == 25
    assert report["verified_artifact_run_pairs"] == 25
    assert report["mismatches"] == 0
    assert report["manifest_c050_g000_artifact_id"] == EXPECTED_C050_ARTIFACT_ID
    assert report["manifest_c050_g000_run_id"] == EXPECTED_C050_RUN_ID


def test_old_c050_artifact_pointer_fails_closed() -> None:
    manifest = _manifest()
    manifest["artifact_manifest"]["enriched_artifacts"]["C050_G000"] = 11503191706

    with pytest.raises(RuntimeError, match="C050_G000_ARTIFACT_ID_NOT_RECONCILED"):
        audit_manifest_artifact_pairs(
            manifest, fetch_json=_fake_fetch_factory(manifest), token="test-read-only-token"
        )
