from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from urllib.request import Request, urlopen

REPO = "yasmin977209-ux/motorcycle-simulation"


def api_json(url: str, token: str) -> dict:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "motorcycle-simulation-p16-final-register",
        },
    )
    with urlopen(request, timeout=45) as response:
        value = json.loads(response.read())
    if not isinstance(value, dict):
        raise RuntimeError("ACTIONS_ARTIFACTS_RESPONSE_INVALID")
    return value


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN")
    run_id = os.environ.get("GITHUB_RUN_ID")
    tested_sha = os.environ.get("GITHUB_SHA")
    branch = os.environ.get("GITHUB_REF_NAME")
    if not token or not run_id or not tested_sha or not branch:
        raise RuntimeError("FINAL_REGISTER_CONTEXT_MISSING")
    out_dir = Path("deliverables")
    manifest_path = out_dir / "output_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("status") != "PASS_SCOPED_PROVISIONAL_OUTPUTS_NOT_ACCEPTED":
        raise RuntimeError(f"DELIVERABLE_MANIFEST_NOT_PASS_SCOPED: {manifest.get('status')}")
    for filename, entry in manifest["seven_files"].items():
        path = out_dir / filename
        if not path.is_file():
            raise RuntimeError(f"DELIVERABLE_MISSING_AFTER_UPLOAD: {filename}")
        actual_sha = sha256_file(path)
        actual_size = path.stat().st_size
        if actual_sha != entry["sha256"] or actual_size != entry["bytes"]:
            raise RuntimeError(f"DELIVERABLE_READBACK_HASH_MISMATCH: {filename}")

    api = api_json(
        f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}/artifacts?per_page=100",
        token,
    )
    expected_name = f"p16-provisional-seven-deliverables-{run_id}"
    matches = [a for a in api.get("artifacts", []) if a.get("name") == expected_name]
    if len(matches) != 1:
        raise RuntimeError(f"DELIVERABLE_ARTIFACT_NOT_UNIQUE: {expected_name}: {len(matches)}")
    artifact = matches[0]
    if artifact.get("expired") is True:
        raise RuntimeError("DELIVERABLE_ARTIFACT_EXPIRED")
    workflow = artifact.get("workflow_run") or {}
    if workflow.get("id") != int(run_id) or workflow.get("head_sha") != tested_sha or workflow.get("head_branch") != branch:
        raise RuntimeError("DELIVERABLE_ARTIFACT_RUN_BRANCH_SHA_MISMATCH")

    manifest["deliverable_artifact_id"] = artifact["id"]
    manifest["deliverable_artifact_name"] = artifact["name"]
    manifest["deliverable_artifact_bytes"] = artifact["size_in_bytes"]
    manifest["deliverable_artifact_digest"] = artifact.get("digest")
    manifest["run_id"] = int(run_id)
    manifest["tested_sha"] = tested_sha
    manifest["branch"] = branch
    for entry in manifest["seven_files"].values():
        entry["run_id"] = int(run_id)
        entry["tested_sha"] = tested_sha
        entry["artifact_id"] = artifact["id"]
        entry["artifact_name"] = artifact["name"]
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    register = {
        "schema_version": "1.0",
        "status": "READ_BACK_VERIFIED_PASS_SCOPED_PROVISIONAL_OUTPUTS_NOT_ACCEPTED",
        "branch": branch,
        "tested_sha": tested_sha,
        "run_id": int(run_id),
        "artifact_id": artifact["id"],
        "artifact_name": artifact["name"],
        "artifact_bytes": artifact["size_in_bytes"],
        "artifact_digest": artifact.get("digest"),
        "source_sha": manifest["source_sha"],
        "reference_sha256": manifest["reference_sha256"],
        "delivery": "NOT_ACCEPTED",
        "release": "BLOCKED / NOT_AUTHORIZED",
        "files": manifest["seven_files"],
    }
    register_path = out_dir / "p16_final_provenance_register.json"
    register_path.write_text(json.dumps(register, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # Read back both records and the seven file digests after mutation.
    check = json.loads(manifest_path.read_text(encoding="utf-8"))
    if check.get("deliverable_artifact_id") != artifact["id"] or len(check.get("seven_files", {})) != 7:
        raise RuntimeError("FINAL_OUTPUT_MANIFEST_READBACK_FAILED")
    for filename, entry in check["seven_files"].items():
        target = out_dir / filename
        if sha256_file(target) != entry["sha256"] or target.stat().st_size != entry["bytes"]:
            raise RuntimeError(f"FINAL_OUTPUT_HASH_READBACK_FAILED: {filename}")
    print(json.dumps({
        "status": register["status"],
        "run_id": run_id,
        "tested_sha": tested_sha,
        "artifact_id": artifact["id"],
        "artifact_name": artifact["name"],
        "files": register["files"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
