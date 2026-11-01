"""Source-verified D3 scoped completion pipeline.

Downloads only three already-existing pinned GitHub Actions artifacts.
Does not run simulations, trials, Monte Carlo, N expansion, backfill, or zero-fill.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import subprocess
import sys
from datetime import datetime, timezone

import requests
from openpyxl import load_workbook

REPO = os.environ["GITHUB_REPOSITORY"]
BRANCH = "tmp/d1-rebuild-20261101"
SOURCE_HEAD = os.environ["GITHUB_SHA"]
RUN_ID = os.environ["GITHUB_RUN_ID"]
TOKEN = os.environ["GH_TOKEN"]
API = f"https://api.github.com/repos/{REPO}"
RAW = f"https://raw.githubusercontent.com/{REPO}"
SESSION = requests.Session()
SESSION.headers.update({
    "Authorization": "Bearer " + TOKEN,
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
})
ARTIFACTS = {
    "aggregate": {
        "id": 12852969854, "run_id": 40773412377, "bytes": 9357996,
        "sha256": "ec05a69ae8968585decf83cf0716d56c264f47f86187cfd3cf53b11f52ca2e54",
        "head": "4f2f2cc16d0cb5125262088704febccbae6f50ed",
        "name": "s6-n2400-status-reconciled-aggregate-40773412377",
        "filename": "s6-n2400.zip",
    },
    "full_logging": {
        "id": 12998778418, "run_id": 41098699740, "bytes": 310827203,
        "sha256": "403371cc8eb12880dda05529b4c83dd675bfa609e8680c09d35efa729c5b5aeb",
        "head": "e3c2098df9fc5dbc126eb1e77ad35c493ff3ac70",
        "name": "s6-stage-c-representative-full-logging-41098699740",
        "filename": "full-logging.zip",
    },
    "c100": {
        "id": 12630457193, "run_id": 40263424595, "bytes": 361733,
        "sha256": "c977d1cbb5204919eadc72358533f77cdbbc239902bcd6f921bf1a915a716e79",
        "head": "24050f15bc7eb3097e20f76785a45c5d177643dd",
        "name": "s4-c100-v23-40263424595",
        "filename": "c100-reuse.zip",
    },
}
ACCOUNTING_FIELDS = [
    "Accounts_Receivable", "Accumulated_Depreciation", "Gross_Bike_Assets",
    "Guarantee_Claim_Receivable", "Total_Assets",
]
GLOBAL_SHEETS = [
    "README", "CONSTANTS", "SCENARIO_MATRIX", "HEATMAP", "SENSITIVITY",
    "VALIDATION_SUMMARY", "ERROR_LOG", "FINAL_CLOSURE_SUMMARY",
    "DAILY_DISTRIBUTION", "REPRESENTATIVE_CASES",
]
SCENARIOS = [
    f"C{c:03d}_G{g:03d}"
    for c in (30, 50, 70, 85, 100)
    for g in (0, 30, 50, 70, 100)
]
EXPECTED_SHEETS = GLOBAL_SHEETS + [
    f"{sid}_{suffix}"
    for sid in SCENARIOS
    for suffix in ("STATS", "DAILY", "ASSETS", "ACCTG", "PARTNER", "GUARANTEE", "CONTRACTS")
]


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + bytes([0]) + raw).hexdigest()


def run(command: list[str]) -> None:
    print("+", " ".join(command), flush=True)
    subprocess.run(command, check=True)


def verify_and_download_artifacts() -> dict:
    root = pathlib.Path("/tmp/d3-source-artifacts")
    root.mkdir(parents=True, exist_ok=True)
    verified = {}
    for key, spec in ARTIFACTS.items():
        response = SESSION.get(f"{API}/actions/artifacts/{spec['id']}", timeout=90)
        response.raise_for_status()
        meta = response.json()
        observed = (
            meta.get("id"), meta.get("name"), meta.get("size_in_bytes"), meta.get("digest"),
            meta.get("expired"), meta.get("workflow_run", {}).get("id"),
            meta.get("workflow_run", {}).get("head_sha"),
        )
        expected = (
            spec["id"], spec["name"], spec["bytes"], "sha256:" + spec["sha256"],
            False, spec["run_id"], spec["head"],
        )
        if observed != expected:
            raise RuntimeError(f"SOURCE_ARTIFACT_METADATA_MISMATCH:{key}:{observed!r}:{expected!r}")
        response = SESSION.get(meta["archive_download_url"], stream=True, timeout=(90, 900))
        response.raise_for_status()
        target = root / spec["filename"]
        hasher = hashlib.sha256()
        total = 0
        with target.open("wb") as stream:
            for chunk in response.iter_content(1024 * 1024):
                if chunk:
                    stream.write(chunk)
                    hasher.update(chunk)
                    total += len(chunk)
        actual_sha = hasher.hexdigest()
        if total != spec["bytes"] or actual_sha != spec["sha256"]:
            raise RuntimeError(f"SOURCE_ARTIFACT_RAW_HASH_MISMATCH:{key}:{total}:{actual_sha}")
        verified[key] = {
            "artifact_id": spec["id"], "run_id": spec["run_id"],
            "size_bytes": total, "sha256": actual_sha,
            "workflow_run_head_sha": spec["head"], "filename": spec["filename"],
            "evidence_status": "VERIFIED_LIVE",
        }
        print(
            f"VERIFIED_SOURCE_ARTIFACT name={key} id={spec['id']} run={spec['run_id']} "
            f"head={spec['head']} bytes={total} sha256={actual_sha} path={target}",
            flush=True,
        )
    return verified


def verify_governing_reference() -> bytes:
    url = (
        "https://gist.githubusercontent.com/yasmin977209-ux/"
        "c3e5362f5928da22ee079fc94817224e/raw/"
        "384c27810e76572e77e79e9829c5f92c1c4165d7/reference_v240.md"
    )
    response = requests.get(url, timeout=300)
    response.raise_for_status()
    raw = response.content
    expected = "225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b"
    if len(raw) != 401397 or digest(raw) != expected:
        raise RuntimeError("APPROVED_GOVERNING_REFERENCE_PIN_MISMATCH")
    pathlib.Path("/tmp/approved-v240.md").write_bytes(raw)
    repo_copy = pathlib.Path("docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md").read_bytes()
    if repo_copy != raw:
        raise RuntimeError("REPOSITORY_GOVERNING_REFERENCE_RAW_MISMATCH")
    print(f"VERIFIED_GOVERNING_REFERENCE bytes={len(raw)} sha256={digest(raw)} blob={git_blob(raw)}")
    return raw


def create_input_manifest(extension_audit: dict, reference_raw: bytes) -> str:
    registry_raw = pathlib.Path("results/number_registry.json").read_bytes()
    extension_raw = pathlib.Path("deliverables/D3_NUMBER_REGISTRY_EXTENSION.json.gz").read_bytes()
    manifest = {
        "schema_version": "d3-input-manifest-v1",
        "source_head": SOURCE_HEAD,
        "workflow_run_id": RUN_ID,
        "current_governing_reference": {
            "url": (
                "https://gist.githubusercontent.com/yasmin977209-ux/"
                "c3e5362f5928da22ee079fc94817224e/raw/"
                "384c27810e76572e77e79e9829c5f92c1c4165d7/reference_v240.md"
            ),
            "revision_commit": "384c27810e76572e77e79e9829c5f92c1c4165d7",
            "bytes": len(reference_raw), "sha256": digest(reference_raw),
            "git_blob_sha1": git_blob(reference_raw),
        },
        "historical_execution_reference_sha256": (
            "e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f"
        ),
        "base_number_registry": {
            "path": "results/number_registry.json", "bytes": len(registry_raw),
            "sha256": digest(registry_raw), "git_blob_sha1": git_blob(registry_raw),
        },
        "d3_extension": {
            "path": "deliverables/D3_NUMBER_REGISTRY_EXTENSION.json.gz",
            "bytes": len(extension_raw), "sha256": digest(extension_raw),
            "git_blob_sha1": git_blob(extension_raw),
            "extension_id": extension_audit["extension_id"],
            "actions_artifact_name": f"D3-Registry-Extension-{RUN_ID}",
        },
        "source_artifacts": extension_audit["source_artifacts"],
        "full_logging_validation": extension_audit["full_logging_validation"],
        "c100_validation": extension_audit["c100_validation"],
        "close_date_validation": extension_audit["close_date_validation"],
        "representative_accounting_fields": extension_audit["representative_accounting_fields"],
        "no_trials_or_simulation_executed": True,
    }
    raw = (json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode()
    pathlib.Path("deliverables/D3_INPUT_MANIFEST.json").write_bytes(raw)
    sha = digest(raw)
    print(f"D3_INPUT_MANIFEST bytes={len(raw)} sha256={sha} blob={git_blob(raw)}")
    return sha


def independent_workbook_validation(build_audit: dict, input_manifest_sha: str) -> dict:
    results = {}
    for filename in ("النتائج_الكاملة_AR.xlsx", "Full_Results_EN.xlsx"):
        path = pathlib.Path("deliverables") / filename
        wb = load_workbook(path, read_only=True, data_only=False)
        try:
            if wb.sheetnames != EXPECTED_SHEETS or len(wb.sheetnames) != 185:
                raise RuntimeError("D3_WORKSHEET_INVENTORY_MISMATCH:" + filename)
            representative = wb["REPRESENTATIVE_CASES"]
            counts = {"DAILY_RAW": 0, "TRIAL_SUMMARY": 0, "REGISTRY_METRIC": 0}
            trial_keys = set()
            roles = set()
            assignments = 0
            daily_rows = 0
            for row in representative.iter_rows(min_row=2, values_only=True):
                kind = row[0]
                if kind in counts:
                    counts[kind] += 1
                if kind == "DAILY_RAW":
                    daily_rows += 1
                if kind == "TRIAL_SUMMARY":
                    trial_keys.add((row[1], row[3]))
                    role_list = [x.strip() for x in (row[4] or "").split(",") if x.strip()]
                    roles.update(role_list)
                    assignments += len(role_list)
            if (
                len(trial_keys) != 105 or counts["TRIAL_SUMMARY"] != 105
                or assignments != 125
                or roles != {"P50", "P10", "P90", "LossCase", "MaxCase"}
                or daily_rows < 105 or counts["REGISTRY_METRIC"] == 0
            ):
                raise RuntimeError(
                    "D3_REPRESENTATIVE_CASE_COVERAGE_MISMATCH:"
                    + filename + ":" + repr((counts, len(trial_keys), assignments, roles, daily_rows))
                )
            closure_ws = wb["FINAL_CLOSURE_SUMMARY"]
            close_scenarios = set()
            close_total = 0
            for row in closure_ws.iter_rows(min_row=2, values_only=True):
                if row[0] in SCENARIOS:
                    close_scenarios.add(row[0])
                    if type(row[3]) is int:
                        close_total += row[3]
            if len(close_scenarios) != 25 or close_total != 49500:
                raise RuntimeError(
                    "D3_CLOSE_DATE_COVERAGE_MISMATCH:"
                    + filename + ":" + repr((len(close_scenarios), close_total))
                )
            required_data_sheets = [
                f"{sid}_{suffix}" for sid in SCENARIOS
                for suffix in ("STATS", "DAILY", "ASSETS", "ACCTG", "PARTNER", "GUARANTEE", "CONTRACTS")
            ]
            for sheet in required_data_sheets:
                if wb[sheet].max_row < 2:
                    raise RuntimeError("D3_REQUIRED_DETAIL_SHEET_EMPTY:" + filename + ":" + sheet)
            input_manifest_rows = list(wb["README"].iter_rows(min_row=1, values_only=True))
            manifest_values = {str(row[0]): row[1] for row in input_manifest_rows if len(row) > 1}
            if manifest_values.get("D3 input manifest SHA-256") != input_manifest_sha:
                raise RuntimeError("D3_README_INPUT_MANIFEST_FINGERPRINT_MISMATCH:" + filename)
            results[filename] = {
                "sheet_count": len(wb.sheetnames),
                "representative_daily_raw_rows": daily_rows,
                "representative_trial_summary_rows": counts["TRIAL_SUMMARY"],
                "representative_registry_metric_rows": counts["REGISTRY_METRIC"],
                "unique_representative_trial_keys": len(trial_keys),
                "role_assignments": assignments, "roles": sorted(roles),
                "final_close_date_scenarios": len(close_scenarios),
                "final_close_date_trial_count": close_total,
                "required_detail_sheets_nonempty": len(required_data_sheets),
                "input_manifest_sha256_in_readme": input_manifest_sha,
            }
        finally:
            wb.close()

    if (
        build_audit["arabic_workbook"]["formula_cell_count"] != 0
        or build_audit["arabic_workbook"]["excel_error_cell_count"] != 0
        or build_audit["english_workbook"]["formula_cell_count"] != 0
        or build_audit["english_workbook"]["excel_error_cell_count"] != 0
        or build_audit["arabic_workbook"]["sheet_direction_status"] != "PASS"
        or build_audit["english_workbook"]["sheet_direction_status"] != "PASS"
        or build_audit["bilingual_numeric_parity"]["numeric_mismatches"] != 0
        or build_audit["number_id_traceability"]["untraced_numeric_cells"] != 0
    ):
        raise RuntimeError("D3_WORKBOOK_SAFETY_PARITY_OR_TRACEABILITY_FAILED")

    result = {
        "status": "PASS_SCOPED_D3_INDEPENDENT_STRUCTURE",
        "workbooks": results,
        "bilingual_numeric_parity": build_audit["bilingual_numeric_parity"],
        "number_id_traceability": build_audit["number_id_traceability"],
        "arabic_formula_cells": build_audit["arabic_workbook"]["formula_cell_count"],
        "arabic_error_cells": build_audit["arabic_workbook"]["excel_error_cell_count"],
        "english_formula_cells": build_audit["english_workbook"]["formula_cell_count"],
        "english_error_cells": build_audit["english_workbook"]["excel_error_cell_count"],
        "arabic_direction": build_audit["arabic_workbook"]["sheet_direction_status"],
        "english_direction": build_audit["english_workbook"]["sheet_direction_status"],
        "no_trials_or_simulation_executed": True,
    }
    path = pathlib.Path("deliverables/D3_INDEPENDENT_VALIDATION.json")
    path.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return result


def append(path: str, text: str) -> None:
    target = pathlib.Path(path)
    old = target.read_text(encoding="utf-8")
    target.write_text(old + "\n\n" + text.strip() + "\n", encoding="utf-8")


def write_closure_docs(extension_audit: dict, build_audit: dict, manifest: dict, independent: dict) -> None:
    statuses = build_audit["requirement_statuses"]
    limitations = build_audit["limitations"]
    closure = {
        "schema_version": "d3-scoped-closure-v1",
        "disposition": "PASS_SCOPED_WITH_LIMITATIONS",
        "candidate_classification": build_audit["d3_candidate_status"],
        "source_head": SOURCE_HEAD, "workflow_run_id": RUN_ID,
        "current_governing_reference_sha256": build_audit["current_governing_reference"]["sha256"],
        "historical_execution_reference_sha256": build_audit["historical_execution_reference_sha256"],
        "requirement_statuses": statuses,
        "source_artifacts": extension_audit["source_artifacts"],
        "full_logging_validation": extension_audit["full_logging_validation"],
        "c100_validation": extension_audit["c100_validation"],
        "close_date_validation": extension_audit["close_date_validation"],
        "representative_accounting_fields": extension_audit["representative_accounting_fields"],
        "independent_validation": independent,
        "files": [],
        "preserved_gate_statuses": build_audit["gate_statuses_preserved"],
        "limitations": limitations,
        "no_trials_or_simulation_executed": True,
        "final_acceptance": "NOT_DECLARED",
        "d4": "NOT_STARTED / NOT_AUTHORIZED_BY_THIS_CLOSURE",
    }
    report_path = pathlib.Path("docs/stage_d/D3_SCOPED_CLOSURE_REPORT_2026-11-02.md")
    report = report_path.read_text(encoding="utf-8")
    report += (
        "\n\n## Independent source and workbook closure audit\n\n"
        f"- Source artifacts: aggregate {extension_audit['source_artifacts']['aggregate']['artifact_id']}; "
        f"Full Logging {extension_audit['source_artifacts']['full_logging']['artifact_id']}; "
        f"C100 {extension_audit['source_artifacts']['c100']['artifact_id']}.\n"
        f"- Full Logging: {extension_audit['full_logging_validation']['unique_trial_keys']} unique keys / "
        f"{extension_audit['full_logging_validation']['role_assignments']} role assignments; all 105 post-write audits passed.\n"
        f"- Independent workbook check: {independent['status']}; 105 raw representative trial keys; "
        "125 assignments across P50/P10/P90/LossCase/MaxCase.\n"
        f"- Final close dates: {extension_audit['close_date_validation']['total_trial_count']} trials across "
        f"{extension_audit['close_date_validation']['scenario_count']} scenarios.\n"
        f"- Bilingual numeric comparisons: {build_audit['bilingual_numeric_parity']['numeric_comparisons']}; "
        f"mismatches: {build_audit['bilingual_numeric_parity']['numeric_mismatches']}.\n"
        f"- Number-ID traced numeric cells: {build_audit['number_id_traceability']['numeric_cells_checked']}; "
        f"untraced: {build_audit['number_id_traceability']['untraced_numeric_cells']}.\n"
        "- Historical 48K accounting fields remain MISSING_EVIDENCE and are not inferred or zero-filled.\n"
        "- Full model acceptance suite remains NOT_RUN; this D3 workflow is not project final acceptance.\n"
        "- D4 remains NOT_STARTED and requires a separate owner instruction.\n"
    )
    report_path.write_text(report, encoding="utf-8")
    report_raw = report_path.read_bytes()

    tracked = [
        "deliverables/النتائج_الكاملة_AR.xlsx", "deliverables/Full_Results_EN.xlsx",
        "deliverables/D3_BUILD_AUDIT.json", "deliverables/D3_MANIFEST.json",
        "deliverables/D3_INPUT_MANIFEST.json", "deliverables/D3_EXTENSION_AUDIT.json",
        "deliverables/D3_INDEPENDENT_VALIDATION.json",
        "docs/stage_d/D3_SCOPED_CLOSURE_REPORT_2026-11-02.md",
    ]
    file_rows = []
    for name in tracked:
        raw = pathlib.Path(name).read_bytes()
        file_rows.append({
            "path": name, "bytes": len(raw), "sha256": digest(raw), "git_blob_sha1": git_blob(raw),
        })
    closure["files"] = file_rows
    pathlib.Path("docs/stage_d/D3_SCOPED_CLOSURE_2026-11-02.json").write_text(
        json.dumps(closure, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )

    matrix = """
## D3 scoped closure assessment — 2026-11-02 (append-only)

- D3-01 through D3-04: PASS_SCOPED.
- D3-05: PASS_SCOPED_WITH_LIMITATIONS — complete S6 daily distributions plus source-backed C100 deterministic daily reuse; cohort separation preserved.
- D3-06: PASS_SCOPED_WITH_LIMITATIONS — 105 unique representative raw daily keys and 125 role assignments; not 48,000 full-trial logging.
- D3-07 through D3-13: PASS_SCOPED — representative P50 daily, ASSETS, ACCTG, PARTNER, GUARANTEE, CONTRACTS and all-trial close-date records are source-backed by pinned artifacts.
- D3-14 through D3-16: PASS_SCOPED — separate formula/error audit, RTL/LTR, bilingual numeric parity, Number-ID traceability and exact-ratio/no-float controls.
- D3-17: PASS_SCOPED_WITH_LIMITATIONS — all statistical, production and historical accounting limitations preserved.
- D3-18: PASS_SCOPED — exact final HEAD and GitHub Raw byte triples verified by the final completion workflow.
- Overall D3: PASS_SCOPED_WITH_LIMITATIONS. This is not final project acceptance and does not authorize D4.
"""
    append("docs/stage_d/D3_REQUIREMENTS_MATRIX_2026-11-01.md", matrix)
    append(
        "docs/stage_d/D3_CORRECTION_LEDGER_2026-11-02.md",
        """
## D3 source-verified closure correction — 2026-11-02 (append-only)

The prior MISSING_EVIDENCE disposition for C100 daily reuse, representative raw daily logs, detailed P50 ledgers and close-date distribution is superseded for the scoped D3 deliverables only. These records were extracted and verified from the three existing pinned GitHub Actions artifacts; no new Trial or simulation was run. The five historical accounting fields remain MISSING_EVIDENCE for the full 48K cohort and are not inferred or zero-filled. Full Logging remains 105 unique keys / 125 role assignments only. C100 Golden full revalidation remains NOT_RUN. D3 disposition is PASS_SCOPED_WITH_LIMITATIONS, not final project acceptance.
""",
    )
    append(
        "docs/stage_d/D3_REPAIR_AND_PUBLICATION_ADDENDUM_2026-11-02.md",
        """
## D3 complete scoped repair — 2026-11-02 (append-only)

The three pinned source artifacts were downloaded from GitHub. Their live metadata, source run-head identities, byte sizes and SHA-256 digests were verified before parsing. The extension validates ZIP CRC/path integrity, source manifests, all 105 representative sidecars/member hashes and post-write audits, C100 identities/determinism, and the representative C100 daily path correspondence. Two 185-sheet bilingual workbooks now include 25 P50 detail ledgers and raw daily logs for all 105 unique representative keys / 125 role assignments. No new Trial, Simulation, Monte Carlo, N expansion, backfill or zero-fill was performed. D3 closes PASS_SCOPED_WITH_LIMITATIONS; limitations are recorded in the scoped closure report.
""",
    )
    append(
        "docs/stage_d/D3_LIVE_REVIEW_AUDIT_2026-11-02.md",
        """
## D3 source-verified closure review — 2026-11-02 (append-only)

The formerly missing D3 scoped source categories were recovered from pinned existing artifacts, not generated by new trials. Independent workbook checks verify 185 sheets per language, 105 unique representative trial keys, 125 role assignments across P50/P10/P90/LossCase/MaxCase, raw daily rows, all 25 close-date scenarios and 49,500 total close-date trial records. The build audit separately verifies formula cells, Excel error cells, RTL/LTR, bilingual numeric parity and Number-ID traceability. All 18 D3 requirements have scoped dispositions; D3 overall is PASS_SCOPED_WITH_LIMITATIONS. Full 48K historical accounting remains MISSING_EVIDENCE, C100 Golden full revalidation NOT_RUN, and production/statistical gates remain unchanged. D4 remains NOT_STARTED.
""",
    )
    append(
        "docs/PROJECT_CONTINUITY.md",
        """
## D3 scoped closure — 2026-11-02

- D3 was rebuilt from three existing pinned, non-expired GitHub Actions artifacts; no new Trial/Simulation/Monte Carlo or N expansion was executed.
- The D3 Number Registry extension adds C100 daily reuse, 49,500 all-trial close-date records, 25 source-backed P50 detail ledgers, and raw daily logs for 105 unique representative keys / 125 role assignments.
- Both bilingual workbooks have 185 sheets; workbook audit and independent representative coverage, numeric parity, formula/error, direction and Number-ID checks are recorded in the D3 scoped closure evidence.
- D3 disposition: PASS_SCOPED_WITH_LIMITATIONS. Five full-48K historical accounting fields remain MISSING_EVIDENCE; Full Logging remains 105 representative keys only; C100 Golden full revalidation NOT_RUN; Production Gate A NOT_DECLARED; Gate B FAIL_SCOPED (10/10); Stability NOT_CONVERGED (0/60); N=4800 NOT_EXECUTED.
- D4 remains NOT_STARTED and is not initiated by this D3 closure. No main update, merge, PR, Release or final acceptance.
""",
    )
    append(
        "docs/PROJECT_HANDOFF.md",
        """
## D3 scoped closure handoff — 2026-11-02

D3 is PASS_SCOPED_WITH_LIMITATIONS on the source-backed bilingual workbook outputs. Review D3_SCOPED_CLOSURE_REPORT_2026-11-02.md/.json, the D3 input/output manifests, extension audit, independent validation, remote evidence ledger and exact-final-head workflow. D4 is NOT_STARTED; wait for explicit owner instruction. All preserved gate and historical data limitations remain in force.
""",
    )
    append(
        "docs/stage_d/STAGE_D_SESSION_STATUS_2026-11-01.md",
        """
## D3 closure status — 2026-11-02

D3: PASS_SCOPED_WITH_LIMITATIONS. D0/D1/D2 remain PASS_SCOPED_WITH_LIMITATIONS. D4: NOT_STARTED. No Trial, Simulation, Monte Carlo, N expansion, backfill, zero-fill, main update, merge, PR or Release.
""",
    )
    append(
        "docs/stage_d/STAGE_D_CONTINUITY_HANDOFF_2026-11-01.md",
        """
## D3 closure handoff — 2026-11-02

D3 scoped gate is PASS_SCOPED_WITH_LIMITATIONS, with source artifacts and exact final HEAD verified in the D3 completion workflow. D4 has not started. Preserve all five missing historical accounting fields and all statistical/production gate statuses.
""",
    )
    append(
        "docs/stage_d/PROJECT_PROMPT_LIBRARY_AR_2026-11-01_REV2.md",
        """
## D3 status correction — 2026-11-02 (append-only)

D3 was source-verified and closed PASS_SCOPED_WITH_LIMITATIONS using existing pinned S6 aggregate, Full Logging and C100 artifacts. The prior D3 BLOCKED status is superseded for the scoped deliverables only. Read D3_SCOPED_CLOSURE_REPORT_2026-11-02.md and its evidence ledger before any subsequent work. D4 remains NOT_STARTED and requires a separate owner instruction; this entry does not authorize D4. All historical accounting and statistical gate limitations remain unchanged.
""",
    )


def remote_readback(paths: list[str], commit: str) -> list[tuple[str, int, str, str]]:
    rows = []
    for path in paths:
        local = pathlib.Path(path).read_bytes()
        url = f"{RAW}/{commit}/{path}"
        response = requests.get(url, timeout=300)
        response.raise_for_status()
        raw = response.content
        if raw != local:
            raise RuntimeError("D3_RAW_READBACK_MISMATCH:" + path)
        row = (path, len(raw), digest(raw), git_blob(raw))
        rows.append(row)
        print(
            f"VERIFIED_LIVE url={url} bytes={row[1]} sha256={row[2]} "
            f"blob={row[3]} commit={commit}",
            flush=True,
        )
    return rows


def main() -> None:
    if os.environ.get("GITHUB_REF_NAME") != BRANCH:
        raise RuntimeError("D3_WRONG_BRANCH")
    if subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip() != SOURCE_HEAD:
        raise RuntimeError("D3_START_HEAD_MISMATCH")

    source_artifacts = verify_and_download_artifacts()
    reference_raw = verify_governing_reference()

    run([
        sys.executable, "-m", "compileall", "-q",
        "scripts/d3_registry_extension.py", "scripts/d3_excel_export_complete.py",
        "tests/test_d3_registry_extension.py", "tests/test_d3_sensitivity_entries.py",
        "tests/test_s6_excel_export.py",
    ])
    run([
        sys.executable, "-m", "pytest", "-q", "-rs",
        "tests/test_d3_registry_extension.py", "tests/test_d3_sensitivity_entries.py",
        "tests/test_s6_excel_export.py",
    ])

    pathlib.Path("deliverables").mkdir(exist_ok=True)
    run([
        sys.executable, "-m", "scripts.d3_registry_extension", "build",
        "--aggregate", "/tmp/d3-source-artifacts/s6-n2400.zip",
        "--full-logging", "/tmp/d3-source-artifacts/full-logging.zip",
        "--c100", "/tmp/d3-source-artifacts/c100-reuse.zip",
        "--base-registry", "results/number_registry.json",
        "--output", "deliverables/D3_NUMBER_REGISTRY_EXTENSION.json.gz",
        "--audit", "deliverables/D3_EXTENSION_AUDIT.json",
    ])
    extension_audit = json.loads(
        pathlib.Path("deliverables/D3_EXTENSION_AUDIT.json").read_text(encoding="utf-8")
    )
    if extension_audit.get("status") != "PASS_SCOPED_D3_REGISTRY_EXTENSION":
        raise RuntimeError("D3_EXTENSION_AUDIT_NOT_PASS")
    if (
        extension_audit["full_logging_validation"]["unique_trial_keys"] != 105
        or extension_audit["full_logging_validation"]["role_assignments"] != 125
        or extension_audit["c100_validation"]["daily_reuse_status"] != "PASS_SCOPED_C100_DAILY_REUSE"
        or extension_audit["close_date_validation"]["total_trial_count"] != 49500
    ):
        raise RuntimeError("D3_EXTENSION_COVERAGE_ASSERTION_FAILED")
    if extension_audit["source_artifacts"] != source_artifacts:
        raise RuntimeError("D3_EXTENSION_SOURCE_ARTIFACT_IDENTITY_MISMATCH")

    input_manifest_sha = create_input_manifest(extension_audit, reference_raw)
    run([
        sys.executable, "-m", "scripts.d3_excel_export_complete", "build",
        "--registry", "results/number_registry.json",
        "--extension", "deliverables/D3_NUMBER_REGISTRY_EXTENSION.json.gz",
        "--reference", "/tmp/approved-v240.md",
        "--output-dir", "deliverables",
        "--source-head", SOURCE_HEAD,
        "--run-id", RUN_ID,
        "--input-manifest-sha256", input_manifest_sha,
    ])
    build_audit = json.loads(
        pathlib.Path("deliverables/D3_BUILD_AUDIT.json").read_text(encoding="utf-8")
    )
    if build_audit.get("d3_gate_status") != "PASS_SCOPED_WITH_LIMITATIONS":
        raise RuntimeError("D3_BUILD_GATE_NOT_SCOPED_PASS")
    independent = independent_workbook_validation(build_audit, input_manifest_sha)

    audit_path = pathlib.Path("deliverables/D3_BUILD_AUDIT.json")
    manifest_path = pathlib.Path("deliverables/D3_MANIFEST.json")
    build_audit["independent_validation"] = independent
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["independent_validation"] = independent
    manifest["extension_artifact_name"] = manifest["registry_extension"]["actions_artifact_name"]
    audit_path.write_text(json.dumps(build_audit, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    write_closure_docs(extension_audit, build_audit, manifest, independent)

    output_paths = [
        "deliverables/النتائج_الكاملة_AR.xlsx", "deliverables/Full_Results_EN.xlsx",
        "deliverables/D3_BUILD_AUDIT.json", "deliverables/D3_MANIFEST.json",
        "deliverables/D3_INPUT_MANIFEST.json", "deliverables/D3_EXTENSION_AUDIT.json",
        "deliverables/D3_INDEPENDENT_VALIDATION.json",
        "docs/stage_d/D3_SCOPED_CLOSURE_REPORT_2026-11-02.md",
        "docs/stage_d/D3_SCOPED_CLOSURE_2026-11-02.json",
        "docs/stage_d/D3_REQUIREMENTS_MATRIX_2026-11-01.md",
        "docs/stage_d/D3_CORRECTION_LEDGER_2026-11-02.md",
        "docs/stage_d/D3_REPAIR_AND_PUBLICATION_ADDENDUM_2026-11-02.md",
        "docs/stage_d/D3_LIVE_REVIEW_AUDIT_2026-11-02.md",
        "docs/PROJECT_CONTINUITY.md", "docs/PROJECT_HANDOFF.md",
        "docs/stage_d/STAGE_D_SESSION_STATUS_2026-11-01.md",
        "docs/stage_d/STAGE_D_CONTINUITY_HANDOFF_2026-11-01.md",
        "docs/stage_d/PROJECT_PROMPT_LIBRARY_AR_2026-11-01_REV2.md",
    ]
    for path in output_paths:
        if not pathlib.Path(path).is_file():
            raise RuntimeError("D3_OUTPUT_MISSING:" + path)

    run(["git", "config", "user.name", "github-actions[bot]"])
    run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"])
    run([
        "git", "add", "-f", "--",
        "deliverables/النتائج_الكاملة_AR.xlsx", "deliverables/Full_Results_EN.xlsx",
    ])
    run([
        "git", "add", "--",
        "deliverables/D3_BUILD_AUDIT.json", "deliverables/D3_MANIFEST.json",
        "deliverables/D3_INPUT_MANIFEST.json", "deliverables/D3_EXTENSION_AUDIT.json",
        "deliverables/D3_INDEPENDENT_VALIDATION.json",
        "docs/stage_d/D3_SCOPED_CLOSURE_REPORT_2026-11-02.md",
        "docs/stage_d/D3_SCOPED_CLOSURE_2026-11-02.json",
        "docs/stage_d/D3_REQUIREMENTS_MATRIX_2026-11-01.md",
        "docs/stage_d/D3_CORRECTION_LEDGER_2026-11-02.md",
        "docs/stage_d/D3_REPAIR_AND_PUBLICATION_ADDENDUM_2026-11-02.md",
        "docs/stage_d/D3_LIVE_REVIEW_AUDIT_2026-11-02.md",
        "docs/PROJECT_CONTINUITY.md", "docs/PROJECT_HANDOFF.md",
        "docs/stage_d/STAGE_D_SESSION_STATUS_2026-11-01.md",
        "docs/stage_d/STAGE_D_CONTINUITY_HANDOFF_2026-11-01.md",
        "docs/stage_d/PROJECT_PROMPT_LIBRARY_AR_2026-11-01_REV2.md",
    ])
    run(["git", "commit", "-m", "feat(d3): close scoped bilingual deliverables from pinned source artifacts"])
    run(["git", "push", "origin", f"HEAD:{BRANCH}"])
    output_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
    print("D3_OUTPUT_COMMIT=" + output_commit, flush=True)

    rows = remote_readback(output_paths, output_commit)
    table = "\n".join(
        f"| {path} | {size} | {sha} | {blob} | {output_commit} |"
        for path, size, sha, blob in rows
    )
    ledger_path = pathlib.Path("docs/stage_d/D3_REMOTE_EVIDENCE_LEDGER_2026-11-01.md")
    ledger_path.write_text(
        ledger_path.read_text(encoding="utf-8")
        + "\n\n## D3 exact output commit fingerprints — 2026-11-02\n\n"
        + f"- Output commit: {output_commit}\n"
        + "- Each file below was fetched from GitHub Raw at this exact commit and byte-compared with the workflow workspace.\n\n"
        + "| Path | Bytes | SHA-256 | Git blob SHA-1 | Containing commit |\n"
        + "|---|---:|---|---|---|\n"
        + table + "\n",
        encoding="utf-8",
    )
    run(["git", "add", "docs/stage_d/D3_REMOTE_EVIDENCE_LEDGER_2026-11-01.md"])
    run(["git", "commit", "-m", "docs(d3): append exact output commit fingerprints"])
    run(["git", "push", "origin", f"HEAD:{BRANCH}"])
    final_head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()

    ref_response = SESSION.get(f"{API}/git/ref/heads/{BRANCH}", timeout=90)
    ref_response.raise_for_status()
    if ref_response.json()["object"]["sha"] != final_head:
        raise RuntimeError("D3_EXACT_FINAL_HEAD_MISMATCH")

    final_paths = output_paths + [
        "docs/stage_d/D3_REMOTE_EVIDENCE_LEDGER_2026-11-01.md",
        "docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md",
    ]
    final_rows = remote_readback(final_paths, final_head)
    print("D3_EXACT_FINAL_HEAD_PASS " + final_head, flush=True)
    print("D3_FINAL_READBACK_FILE_SELF_FINGERPRINT", flush=True)
    ledger_raw = pathlib.Path("docs/stage_d/D3_REMOTE_EVIDENCE_LEDGER_2026-11-01.md").read_bytes()
    print(
        "FINAL_LEDGER bytes=" + str(len(ledger_raw))
        + " sha256=" + digest(ledger_raw)
        + " blob=" + git_blob(ledger_raw)
        + " commit=" + final_head,
        flush=True,
    )
    status = subprocess.check_output(["git", "status", "--porcelain"], text=True)
    if status.strip():
        raise RuntimeError("D3_WORKTREE_NOT_CLEAN_AFTER_FINAL_COMMIT")
    print(
        "D3_SCOPED_CLOSURE_PASS_SCOPED_WITH_LIMITATIONS "
        + json.dumps({
            "source_head": SOURCE_HEAD, "output_commit": output_commit,
            "final_head": final_head, "workflow_run_id": RUN_ID,
            "verified_raw_files": len(final_rows),
            "no_trials_or_simulation_executed": True,
            "d4": "NOT_STARTED",
        }, sort_keys=True),
        flush=True,
    )


if __name__ == "__main__":
    main()
