#!/usr/bin/env python3
"""CP-F fail-closed source readiness audit; it never runs Monte Carlo."""
from __future__ import annotations
import hashlib, io, json, os, sys, tarfile, urllib.request, zipfile
from urllib.error import HTTPError
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import pyarrow.parquet as pq

REPO = "yasmin977209-ux/motorcycle-simulation"
STAGE9A_FINAL_RUN = 37671448546
STAGE10_RUN = 37709936740
STAGE12_RUN = 37964656154
SCENARIO = "C070_G100"
SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
GLOBAL_SHA = "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44"

def api_json(url: str, token: str) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "motorcycle-simulation-cp-f",
    })
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.loads(response.read().decode("utf-8"))

class _NoFollowRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def get_zip(artifact_id: int, token: str) -> bytes:
    url = f"https://api.github.com/repos/{REPO}/actions/artifacts/{artifact_id}/zip"
    request = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "motorcycle-simulation-cp-f",
    })
    # GitHub returns a short-lived signed storage URL. Do not forward the API
    # Authorization header to that different host.
    opener = urllib.request.build_opener(_NoFollowRedirect())
    try:
        with opener.open(request, timeout=180) as response:
            raw = response.read()
    except HTTPError as response:
        if response.code not in (301, 302, 303, 307, 308):
            raise
        location = response.headers.get("Location")
        if not location:
            raise RuntimeError(f"ARTIFACT_REDIRECT_LOCATION_MISSING: {artifact_id}")
        remote_request = urllib.request.Request(
            location, headers={"User-Agent": "motorcycle-simulation-cp-f"}
        )
        with urllib.request.urlopen(remote_request, timeout=180) as response:
            raw = response.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        damaged = archive.testzip()
        if damaged:
            raise RuntimeError(f"ARTIFACT_ZIP_CORRUPT: {damaged}")
    return raw
def artifacts(run_id: int, token: str) -> list[dict[str, Any]]:
    return api_json(
        f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}/artifacts?per_page=100",
        token,
    ).get("artifacts", [])

def one(items: list[dict[str, Any]], name: str) -> dict[str, Any]:
    matches = [x for x in items if x.get("name") == name and not x.get("expired")]
    if len(matches) != 1:
        raise RuntimeError(f"ARTIFACT_LOOKUP_NOT_UNIQUE: {name}; count={len(matches)}")
    return matches[0]

def member(raw_zip: bytes, suffix: str) -> bytes:
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as archive:
        matches = [n for n in archive.namelist() if n == suffix or n.endswith("/" + suffix)]
        if len(matches) != 1:
            raise RuntimeError(f"ZIP_MEMBER_LOOKUP_NOT_UNIQUE: {suffix}; matches={matches[:5]}")
        return archive.read(matches[0])

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def read_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def main() -> int:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN_MISSING")
    evidence_dir = Path("cp-f-evidence")
    evidence_dir.mkdir(parents=True, exist_ok=True)

    state = read_json("state.json")
    roll = read_json("docs/stage12/roll_forward_validation.json")
    closure = read_json("docs/stage12/closure_settlement_validation.json")
    global_manifest = read_json("docs/stage11/global_manifest_11005_reconciled.json")
    assembler = Path("scripts/stage13_assemble.py").read_text(encoding="utf-8")
    identity = {
        "state_source_sha": state.get("source_sha"),
        "stage12_source_sha": roll.get("source_sha"),
        "master_seed": roll.get("master_seed"),
        "schema_version": roll.get("schema_version"),
        "canonical_trials": roll.get("total_trials"),
        "canonical_daily_rows": roll.get("total_daily_rows"),
        "global_sha256": global_manifest.get("global_aggregate_sha256"),
        "global_manifest_status": global_manifest.get("manifest_status"),
        "stage12_roll_forward_result": roll.get("overall_result"),
        "stage12_closure_result": closure.get("overall_result"),
    }
    checks = [
        identity["state_source_sha"] == SOURCE_SHA,
        identity["stage12_source_sha"] == SOURCE_SHA,
        identity["canonical_trials"] == 11005,
        identity["canonical_daily_rows"] == 22546465,
        identity["global_sha256"] == GLOBAL_SHA,
        identity["global_manifest_status"] == "PASS",
        identity["stage12_roll_forward_result"] == "PASS",
        identity["stage12_closure_result"] == "PASS",
    ]
    if not all(checks):
        raise RuntimeError(f"CANONICAL_IDENTITY_ASSERTION_FAILED: {identity}")

    final_item = one(artifacts(STAGE9A_FINAL_RUN, token), "stage9a-final-output")
    final_zip = get_zip(int(final_item["id"]), token)
    s9_manifest = json.loads(member(final_zip, "manifest_final.json"))
    s9_report = json.loads(member(final_zip, "Stage9A_Report.json"))
    if s9_manifest.get("source_sha") != SOURCE_SHA or s9_manifest.get("total_trials") != 9005:
        raise RuntimeError("STAGE9A_SOURCE_OR_COHORT_MISMATCH")
    scenarios = sorted(global_manifest.get("scenario_counts", {}).keys())
    rep_manifest = s9_manifest.get("representative_trials", {})
    if len(scenarios) != 25 or set(rep_manifest) != set(scenarios):
        raise RuntimeError("STAGE9A_SCENARIO_COVERAGE_MISMATCH")
    missing_max_scenarios = [
        sc for sc in scenarios
        if "MaxCase" not in rep_manifest[sc] and "Max Case" not in rep_manifest[sc]
    ]

    enriched_id = int(s9_manifest["artifact_manifest"]["enriched_artifacts"][SCENARIO])
    enriched_zip = get_zip(enriched_id, token)
    scenario_tar = member(enriched_zip, f"{SCENARIO}.tar.gz")
    with tarfile.open(fileobj=io.BytesIO(scenario_tar), mode="r:gz") as tar:
        names = sorted(x.lstrip("./") for x in tar.getnames())
        rep_files = [
            x.removeprefix("representatives/").removesuffix(".json")
            for x in names if x.startswith("representatives/") and x.endswith(".json")
        ]
        parquet_member = next(x for x in tar.getmembers() if x.name.lstrip("./") == "trial_results.parquet")
        stream = tar.extractfile(parquet_member)
        if stream is None:
            raise RuntimeError("STAGE9A_TRIAL_RESULTS_UNREADABLE")
        s9_parquet = pq.ParquetFile(io.BytesIO(stream.read()))
        s9_rows = s9_parquet.metadata.num_rows
        s9_cols = s9_parquet.schema_arrow.names

    stage10_item = one(artifacts(STAGE10_RUN, token), f"stage10-bench-{SCENARIO}-1")
    stage10_zip = get_zip(int(stage10_item["id"]), token)
    with zipfile.ZipFile(io.BytesIO(stage10_zip)) as archive:
        s10_names = sorted(archive.namelist())
        block_name = next((x for x in s10_names if x.endswith("block_451_550.parquet")), None)
        if block_name is None:
            raise RuntimeError("STAGE10_451_550_BLOCK_MISSING")
        block_bytes = archive.read(block_name)
        block = pq.ParquetFile(io.BytesIO(block_bytes))
        block_rows = block.metadata.num_rows
        block_cols = block.schema_arrow.names
        detail_files = [x for x in s10_names if "representatives/" in x or "MaxCase.json" in x or "Max Case.json" in x]

    stage12_item = one(artifacts(STAGE12_RUN, token), f"stage12-daily-{SCENARIO}")
    stage12_zip = get_zip(int(stage12_item["id"]), token)
    ledger_bytes = member(stage12_zip, f"{SCENARIO}.parquet")
    expected_ledger_sha = roll["scenarios"][SCENARIO]["content_sha256"]
    observed_ledger_sha = sha(ledger_bytes)
    if expected_ledger_sha != observed_ledger_sha:
        raise RuntimeError("STAGE12_SAMPLE_PARQUET_SHA256_MISMATCH")
    ledger = pq.ParquetFile(io.BytesIO(ledger_bytes))
    ledger_cols = ledger.schema_arrow.names
    ledger_rows = ledger.metadata.num_rows

    decision_log_text = Path("docs/governance/DECISIONS_LOG.md").read_text(encoding="utf-8")
    decision_start = decision_log_text.find("## D-2026-10-10-03")
    if decision_start < 0:
        raise RuntimeError("APPROVED_REPRESENTATIVE_DECISION_MISSING")
    decision_end = decision_log_text.find("\n## ", decision_start + 4)
    decision_block = decision_log_text[decision_start:] if decision_end < 0 else decision_log_text[decision_start:decision_end]
    decision_approved = "**Status:** APPROVED — NORMATIVE" in decision_block
    decision_roles_exact = "P50/P10/P90/LossCase/MaxCase." in decision_block
    roles = ["P50", "P10", "P90", "LossCase", "MaxCase"] if decision_approved and decision_roles_exact else []
    assembler_requires_max = (
        '"Max Case"' in assembler
        and '("P10", "P50", "P90", "Loss", "Max Case")' in assembler
    )
    stage9a_missing_max = len(missing_max_scenarios) == 25 and not any(
        x in rep_files for x in ("MaxCase", "Max Case")
    )
    stage10_lacks_detail = not detail_files and block_rows == 100
    blocked = roles == ["P50", "P10", "P90", "LossCase", "MaxCase"] and assembler_requires_max and stage9a_missing_max and stage10_lacks_detail

    audit = {
        "audit_version": "cp-f-source-readiness-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "repository": REPO,
        "branch": os.environ.get("GITHUB_REF_NAME"),
        "head_sha": os.environ.get("GITHUB_SHA"),
        "status": "BLOCKED_MISSING_REPRESENTATIVE_PAYLOAD" if blocked else "REQUIRES_REVIEW",
        "classification": "MISSING_ARTIFACT" if blocked else "PENDING",
        "delivery_files_created": False,
        "monte_carlo_rerun": False,
        "main_modified": False,
        "release_created": False,
        "identity_evidence": identity,
        "source_evidence": {
            "stage9a_run_id": STAGE9A_FINAL_RUN,
            "stage9a_final_artifact_id": final_item["id"],
            "stage9a_final_artifact_name": final_item["name"],
            "stage9a_zip_sha256": sha(final_zip),
            "stage9a_trial_count": s9_manifest.get("total_trials"),
            "stage9a_global_sha256": s9_manifest.get("global_manifest_sha256"),
            "stage9a_report": s9_report,
            "stage9a_scenario_count": len(scenarios),
            "stage9a_missing_max_case_scenarios": missing_max_scenarios,
            "stage9a_sample_enriched_artifact_id": enriched_id,
            "stage9a_sample_tarball_sha256": sha(scenario_tar),
            "stage9a_sample_rep_files": rep_files,
            "stage9a_sample_trial_rows": s9_rows,
            "stage9a_sample_trial_columns": s9_cols,
            "stage10_run_id": STAGE10_RUN,
            "stage10_sample_artifact_id": stage10_item["id"],
            "stage10_sample_artifact_name": stage10_item["name"],
            "stage10_zip_sha256": sha(stage10_zip),
            "stage10_sample_entries": s10_names,
            "stage10_extension_rows": block_rows,
            "stage10_extension_columns": block_cols,
            "stage10_detail_payload_files": detail_files,
            "stage12_run_id": STAGE12_RUN,
            "stage12_sample_artifact_id": stage12_item["id"],
            "stage12_sample_artifact_name": stage12_item["name"],
            "stage12_sample_sha256_expected": expected_ledger_sha,
            "stage12_sample_sha256_observed": observed_ledger_sha,
            "stage12_sample_parquet_rows": ledger_rows,
            "stage12_sample_ledger_columns": ledger_cols,
            "stage12_ledger_lacks_detail_columns": [
                x for x in ("assets", "contracts", "guarantee_claims", "event_log") if x not in ledger_cols
            ],
        },
        "decision_evidence": {
            "decision_id": "D-2026-10-10-03",
            "decision_cases": roles,
            "decision_log_block_sha256": sha(decision_block.encode("utf-8")),
            "decision_status_approved_normative": decision_approved,
            "decision_log_has_five_roles": decision_roles_exact,
            "assembler_requires_five_roles_including_max_case": assembler_requires_max,
            "sample_stage9a_rep_files": rep_files,
            "sample_stage10_detail_payload_files": detail_files,
            "scope_note": "Only the named Stage 12 scenario artifact was downloaded and hash-checked in this probe; all 25 Stage 12 Parquet files were not re-verified here.",
        },
        "gates": {
            "G_SOURCE_IDENTITY_METADATA": "PASS" if all(checks) else "FAIL",
            "G_STAGE12_SAMPLE_ARTIFACT_SHA256": "PASS" if observed_ledger_sha == expected_ledger_sha else "FAIL",
            "G_STAGE9A_COHORT_EQUALS_11005": "FAIL",
            "G_REPRESENTATIVE_ROLE_COVERAGE": "FAIL" if blocked else "PENDING",
            "G_COMPLETE_SEVEN_FILE_SET": "BLOCKED",
        },
        "blocker": (
            "The approved representative-case decision and current assembler require five detailed roles, including MaxCase. "
            "The Stage 9A manifest covers 9,005 trials and records no MaxCase payload for all 25 scenarios; the inspected "
            "enriched tarball has only P10/P50/P90/Loss detail JSON. The inspected Stage 10 extension archive contains the "
            "451..550 summary Parquet block and metadata, not detailed MaxCase payload JSON. The official Stage 12 accounting "
            "artifact verifies as a daily ledger, but is not a substitute for missing representative assets/contracts/guarantee "
            "payloads. Re-labelling the old 9,005 workbook, mixing cohorts, omitting MaxCase, inventing payloads, or rerunning "
            "completed trials is not permitted."
        ) if blocked else "The inspected inputs do not establish readiness; review the attached evidence.",
    }
    json_path = Path("cp-f-evidence/CP_F_SOURCE_READINESS.json")
    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = f"""# CP-F Source Readiness Audit

Status: {audit['status']}
Classification: {audit['classification']}
Branch: {audit['branch']}
Run HEAD: {audit['head_sha']}

## Official identity
- Source SHA: {SOURCE_SHA}
- Master seed: {identity['master_seed']}
- Schema version: {identity['schema_version']}
- Canonical trials: {identity['canonical_trials']}
- Daily rows: {identity['canonical_daily_rows']}
- Global aggregate SHA-256: {GLOBAL_SHA}

## Source evidence
- Stage 9A run: {STAGE9A_FINAL_RUN}; output artifact: {final_item['id']}; cohort: {s9_manifest.get('total_trials')}.
- Stage 9A scenarios missing MaxCase payload in manifest: {len(missing_max_scenarios)} of 25.
- Stage 9A sample artifact: {enriched_id}; payload roles physically present: {', '.join(rep_files)}.
- Stage 10 run: {STAGE10_RUN}; sample artifact: {stage10_item['id']}; extension rows: {block_rows}; detailed role JSON files: {len(detail_files)}.
- Stage 12 run: {STAGE12_RUN}; sample artifact: {stage12_item['id']}; SHA-256 expected: {expected_ledger_sha}; observed: {observed_ledger_sha}; row count: {ledger_rows}.
- Caveat: only the named Stage 12 scenario artifact was re-hashed during this diagnostic; this is not a new verification of every Stage 12 file.

## Gate results
| Gate | Result |
|---|---|
| Source identity metadata | {audit['gates']['G_SOURCE_IDENTITY_METADATA']} |
| Sample Stage 12 Parquet exact SHA-256 | {audit['gates']['G_STAGE12_SAMPLE_ARTIFACT_SHA256']} |
| Stage 9A cohort matches canonical 11,005 | FAIL |
| Required representative role payload coverage | {audit['gates']['G_REPRESENTATIVE_ROLE_COVERAGE']} |
| Complete seven-file delivery set | BLOCKED |

## Blocking finding
{audit['blocker']}

## Disposition
No final Excel/report/summary/feasibility deliverables were created. No Monte Carlo was run, no engine or source identity was changed, main was not modified, and no Release was created.
"""
    md_path = Path("cp-f-evidence/CP_F_SOURCE_READINESS.md")
    md_path.write_text(report, encoding="utf-8")
    print(json.dumps({
        "status": audit["status"],
        "classification": audit["classification"],
        "stage9a_trials": s9_manifest.get("total_trials"),
        "canonical_trials": 11005,
        "scenarios_missing_max_case_payload": len(missing_max_scenarios),
        "stage9a_sample_roles": rep_files,
        "stage10_extension_rows": block_rows,
        "stage10_detail_payloads": detail_files,
        "stage12_sample_hash_matches": observed_ledger_sha == expected_ledger_sha,
        "evidence_json": str(json_path),
        "evidence_markdown": str(md_path),
    }, ensure_ascii=False, sort_keys=True))
    return 2 if blocked else 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"CP_F_AUDIT_EXECUTION_ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise
