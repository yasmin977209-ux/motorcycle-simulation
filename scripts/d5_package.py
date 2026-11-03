from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

from openpyxl import load_workbook
from docx import Document

REPO = "yasmin977209-ux/motorcycle-simulation"
BRANCH = "tmp/d1-rebuild-20261101"
GOVERNING_SHA = "225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b"
GOVERNING_BYTES = 401397
GOVERNING_URL = "https://gist.githubusercontent.com/yasmin977209-ux/c3e5362f5928da22ee079fc94817224e/raw/384c27810e76572e77e79e9829c5f92c1c4165d7/reference_v240.md"
HISTORICAL_SHA = "e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f"
D3_ARTIFACT_ID = 13160434943
D3_ARTIFACT_RUN = 41480650491
D3_ARTIFACT_BYTES = 535358202
D3_ARTIFACT_SHA = "513f2a2edab7083c4f36d0e655de6b8a939403f67b51cf0d0d65d4e51f437b04"
D3_ARTIFACT_EXPIRY = "2026-12-02T16:56:31Z"
REGISTRY_PATH = "results/number_registry.json"
REGISTRY_BYTES = 24137036
REGISTRY_SHA = "743ffcced8de09a766870f201c352aabcf5789c43c84bfeae654a939700e4f87"
PACKAGE_NAME = "Motorcycle_Simulation_D5_T2_INTERIM_2026-11-03.zip"
MEMBERS = (
    "Full_Results_EN.xlsx",
    "النتائج_الكاملة_AR.xlsx",
    "التقرير_الكامل_AR.docx",
    "Full_Report_EN.docx",
    "الملخص_AR.docx",
    "Summary_EN.docx",
    "دراسة_الجدوى_AR.docx",
)
DOCX_EXPECTED = {
    "التقرير_الكامل_AR.docx": (42248, "e0e0d9ef504aa4d799b16a94597f228471e1f94ef4d5747b55690e5c43d11dc4"),
    "Full_Report_EN.docx": (41645, "927eae4fd072f765ee6d595e8da6aa4052d770b0ac23d8254154a5fe7436a064"),
    "الملخص_AR.docx": (40435, "874c3a87dfa9f2b6648c59ef0bd51ba85779a991f744e08ab9da73e934115681"),
    "Summary_EN.docx": (39968, "e0b589769b749d0429c0fb0cece03f68af8aabd87544ca0a2e5e791f0b04ced2"),
    "دراسة_الجدوى_AR.docx": (40761, "08dd8602cd7666db1f7a48b146498d882cdfb07cb292f44759ddb8f2509f3ec3"),
}
S6_SOURCE = "da1a9ea9b5cd789c944de3f07b08395bb67c49e7"
S6_COHORT = "s6-v23-da1a9ea9"
C100_SOURCE = "965281d52441cd0d4b744e211c9f68ee4cdc3753"
C100_COHORT = "c100-v23-s4-20261026-965281d5"
MASTER_SEED = 20270101

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def git_blob_sha1(path: Path) -> str:
    raw_size = path.stat().st_size
    h = hashlib.sha1()
    h.update(f"blob {raw_size}\0".encode())
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def safe_member(name: str) -> bool:
    if not name or "\\" in name or name.startswith("/"):
        return False
    p = PurePosixPath(name)
    if p.is_absolute() or (len(name) >= 2 and name[1] == ":"):
        return False
    return all(part not in ("", ".", "..") for part in name.rstrip("/").split("/"))

def verify_zip_safety(path: Path, expected_names: set[str] | None = None) -> list[str]:
    with zipfile.ZipFile(path, "r") as zf:
        infos = zf.infolist()
        names = [i.filename for i in infos]
        if len(names) != len(set(names)):
            raise ValueError("ZIP_DUPLICATE_MEMBER")
        for info in infos:
            if not safe_member(info.filename):
                raise ValueError("ZIP_UNSAFE_PATH:" + info.filename)
            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise ValueError("ZIP_SYMLINK:" + info.filename)
        bad = zf.testzip()
        if bad:
            raise ValueError("ZIP_CRC_FAILURE:" + bad)
        if expected_names is not None and set(names) != expected_names:
            raise ValueError("ZIP_MEMBER_SET_MISMATCH:" + repr(sorted(names)))
        return names

def extract_d3(args) -> None:
    artifact = Path(args.artifact_zip)
    if artifact.stat().st_size != D3_ARTIFACT_BYTES:
        raise ValueError("D3_ARTIFACT_SIZE_MISMATCH")
    actual = sha256_file(artifact)
    if actual != D3_ARTIFACT_SHA:
        raise ValueError("D3_ARTIFACT_SHA256_MISMATCH:" + actual)
    verify_zip_safety(artifact)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    wanted = {"Full_Results_EN.xlsx", "النتائج_الكاملة_AR.xlsx"}
    found = {}
    with zipfile.ZipFile(artifact, "r") as zf:
        for info in zf.infolist():
            if Path(info.filename).name in wanted:
                base = Path(info.filename).name
                if base in found:
                    raise ValueError("D3_WORKBOOK_DUPLICATE:" + base)
                found[base] = info.filename
        if set(found) != wanted:
            raise ValueError("D3_WORKBOOK_MEMBERS_MISSING:" + repr(sorted(wanted-set(found))))
        for base, member in found.items():
            target = out / base
            with zf.open(member) as src, target.open("wb") as dst:
                for chunk in iter(lambda: src.read(1024 * 1024), b""):
                    dst.write(chunk)
    print(f"D3_ARTIFACT_VERIFIED bytes={artifact.stat().st_size} sha256={actual} artifact_id={D3_ARTIFACT_ID}")
    for name, expected in {
        "Full_Results_EN.xlsx": (259441523, "849090a6cd03cf023f8d203345c7aca0141b326d308972b6963a746e84225bd5"),
        "النتائج_الكاملة_AR.xlsx": (259443380, "bcaeac7be2733a745d2f7608476d696fe613644a32244c26b4a3a5c45c598eb2"),
    }.items():
        p = out / name
        if (p.stat().st_size, sha256_file(p)) != expected:
            raise ValueError("D3_WORKBOOK_FINGERPRINT_MISMATCH:" + name)
        print(f"D3_WORKBOOK_VERIFIED {name} bytes={p.stat().st_size} sha256={expected[1]}")

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def file_record(path: Path) -> dict:
    return {
        "bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "git_blob_sha1": git_blob_sha1(path) if path.exists() else None,
    }

def validate_inputs(root: Path, reference: Path) -> tuple[dict, dict, dict, dict]:
    d3 = load_json(root / "deliverables/D3_MANIFEST.json")
    d3audit = load_json(root / "deliverables/D3_BUILD_AUDIT.json")
    d3accept = load_json(root / "docs/stage_d/D3_ARTIFACT_FINAL_ACCEPTANCE_2026-11-03.json")
    d4audit = load_json(root / "docs/stage_d/D4_BUILD_AUDIT_2026-11-03.json")
    d4manifest = load_json(root / "docs/stage_d/D4_REPORT_MANIFEST_2026-11-03.json")
    if d3["current_governing_reference"]["sha256"] != GOVERNING_SHA:
        raise ValueError("D3_GOVERNING_REFERENCE_IDENTITY_MISMATCH")
    if d3["historical_execution_reference_sha256"] != HISTORICAL_SHA:
        raise ValueError("D3_HISTORICAL_REFERENCE_IDENTITY_MISMATCH")
    if d3accept["artifact"]["id"] != D3_ARTIFACT_ID or d3accept["artifact"]["sha256"] != D3_ARTIFACT_SHA:
        raise ValueError("D3_ACCEPTANCE_ARTIFACT_IDENTITY_MISMATCH")
    if d3accept["artifact"]["expired"] is not False:
        raise ValueError("D3_ARTIFACT_EXPIRED")
    if (reference.stat().st_size, sha256_file(reference)) != (GOVERNING_BYTES, GOVERNING_SHA):
        raise ValueError("GOVERNING_REFERENCE_RAW_FINGERPRINT_MISMATCH")
    registry = root / REGISTRY_PATH
    if (registry.stat().st_size, sha256_file(registry)) != (REGISTRY_BYTES, REGISTRY_SHA):
        raise ValueError("NUMBER_REGISTRY_FINGERPRINT_MISMATCH")
    for name, expected in DOCX_EXPECTED.items():
        p = root / "deliverables" / name
        if (p.stat().st_size, sha256_file(p)) != expected:
            raise ValueError("D4_DOCX_FINGERPRINT_MISMATCH:" + name)
        verify_zip_safety(p)
        Document(str(p))
    return d3, d3audit, d4audit, d4manifest

def build(args) -> None:
    root = Path(args.root).resolve()
    out = root / "deliverables"
    reference = Path(args.reference).resolve()
    d3, d3audit, d4audit, d4manifest = validate_inputs(root, reference)
    registry = root / REGISTRY_PATH
    for name, expected_sha in [
        ("Full_Results_EN.xlsx", d3["files"]["Full_Results_EN.xlsx"]["sha256"]),
        ("النتائج_الكاملة_AR.xlsx", d3["files"]["النتائج_الكاملة_AR.xlsx"]["sha256"]),
    ]:
        p = out / name
        if not p.is_file() or sha256_file(p) != expected_sha:
            raise ValueError("D3_WORKBOOK_NOT_PRESENT_OR_INVALID:" + name)
        verify_zip_safety(p)
        wb = load_workbook(p, read_only=True, data_only=False)
        try:
            if len(wb.sheetnames) != 185:
                raise ValueError("D3_WORKBOOK_SHEET_COUNT_INVALID:" + name)
        finally:
            wb.close()
    d4_commit = d4audit.get("output_commit") or "c0bfcbadac8d90932d52eb4ecaec2e72e6b4b909"
    manifest = {
        "schema_version": "motorcycle-simulation-d5-manifest-v1",
        "package_identity": "Motorcycle_Simulation_D5_T2_INTERIM_2026-11-03",
        "package_status": "T2_INTERIM / NOT_FINAL_BLOCKED",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "repository": REPO,
        "branch": args.branch,
        "tested_build_commit_sha": args.tested_sha,
        "build_workflow_run_id": int(args.run_id),
        "spec_version": "2.4.0",
        "current_governing_reference_sha256": GOVERNING_SHA,
        "current_governing_reference": {
            "url": GOVERNING_URL,
            "bytes": GOVERNING_BYTES,
            "sha256": GOVERNING_SHA,
            "gist_revision_commit": "384c27810e76572e77e79e9829c5f92c1c4165d7"
        },
        "historical_execution_reference_sha256": HISTORICAL_SHA,
        "source_identities": {
            "S6": {"SOURCE_SHA": S6_SOURCE, "cohort_id": S6_COHORT, "MASTER_SEED": MASTER_SEED},
            "C100": {"SOURCE_SHA": C100_SOURCE, "cohort_id": C100_COHORT, "classification": "CROSS_COHORT_DETERMINISTIC_REUSE"}
        },
        "rng_policy": {
            "status": "CARRIED_FORWARD_NOT_EXECUTED",
            "note": "D5 performs packaging and integrity checks only; no RNG draws, Trial, Simulation, Monte Carlo, or N expansion are executed."
        },
        "trial_inventory": {
            "S6_source_trial_count_reported": 48000,
            "C100_source_trial_count_reported": 1500,
            "trial_completed_count": "NOT_DECLARED_BY_D3_ACCEPTANCE_EVIDENCE",
            "trial_incomplete_count": "NOT_DECLARED_BY_D3_ACCEPTANCE_EVIDENCE"
        },
        "inputs": {
            "D3_artifact": {
                "artifact_id": D3_ARTIFACT_ID, "source_run_id": D3_ARTIFACT_RUN,
                "bytes": D3_ARTIFACT_BYTES, "sha256": D3_ARTIFACT_SHA,
                "expires_at": D3_ARTIFACT_EXPIRY,
                "acceptance_run_id": d3accept["acceptance_run_id"]
            },
            "D3_output_manifest": {"path": "deliverables/D3_MANIFEST.json", **file_record(root / "deliverables/D3_MANIFEST.json")},
            "D3_build_audit": {"path": "deliverables/D3_BUILD_AUDIT.json", **file_record(root / "deliverables/D3_BUILD_AUDIT.json")},
            "D4_source_run_id": int(d4audit["workflow_run_id"]),
            "D4_tested_sha": d4audit["tested_sha"],
            "D4_output_commit_sha": d4_commit,
            "D4_report_manifest_sha256": d4audit["manifest_sha256"],
            "Number_Registry": {"path": REGISTRY_PATH, **file_record(registry)},
            "D4_reports": {name: {"path": "deliverables/" + name, **file_record(root / "deliverables" / name)} for name in DOCX_EXPECTED}
        },
        "package_members": {name: file_record(out / name) for name in MEMBERS},
        "package_member_count": 8,
        "number_registry_external": {"path": REGISTRY_PATH, **file_record(registry)},
        "runtime": {
            "python": os.sys.version.split()[0],
            "openpyxl": __import__("openpyxl").__version__,
            "python_docx": __import__("docx").__version__
        },
        "validation_runs": [
            {"stage": "D1-D2", "run_id": 41694461194, "tested_sha": "17696ec48557a33f2c231634ba25f26cf831800e", "result": "PASS", "tests_passed": 34},
            {"stage": "D3 artifact acceptance", "run_id": 41682389098, "tested_sha": "a05d71adb3d45140ebc07f523dad2569e560c7c4", "result": "PASS_SCOPED", "artifact_id": D3_ARTIFACT_ID},
            {"stage": "D3 exact-head", "run_id": 41694461171, "tested_sha": "17696ec48557a33f2c231634ba25f26cf831800e", "result": "PASS", "tests_passed": 36},
            {"stage": "D4 report build", "run_id": 41694460895, "tested_sha": "17696ec48557a33f2c231634ba25f26cf831800e", "result": "PASS_SCOPED_WITH_LIMITATIONS", "tests_passed": 5},
            {"stage": "D0-D4 final exact-head", "run_id": 41697223043, "tested_sha": "00dfa15934780271a9be98d55d4cdd83f10e3740", "result": "PASS"}
        ],
        "gate_statuses": {
            "financial_gate_a": "PASS_SCOPED",
            "production_gate_a": "NOT_DECLARED / MISSING_EVIDENCE_HISTORICAL_48K_BALANCE_FIELDS",
            "gate_b_n2400": "FAIL_SCOPED (10/10)",
            "stability": "NOT_CONVERGED (0/60)",
            "n4800": "NOT_EXECUTED",
            "full_logging": "105 representative keys only; NOT_VERIFIED_105_OF_105",
            "c100_golden": "NOT_RUN"
        },
        "missing_accounting_fields": [
            "Accounts_Receivable", "Accumulated_Depreciation", "Gross_Bike_Assets",
            "Guarantee_Claim_Receivable", "Total_Assets"
        ],
        "open_blockers": [
            "Historical 48K accounting fields remain MISSING_EVIDENCE.",
            "Production Gate A is NOT_DECLARED.",
            "Gate B N=2400 remains FAIL_SCOPED (10/10).",
            "Stability remains NOT_CONVERGED (0/60); N=4800 remains NOT_EXECUTED.",
            "Full Logging is representative-only (105 keys / 125 role assignments), not 48,000-trial full daily logging.",
            "C100 Golden revalidation remains NOT_RUN.",
            "D4 reports render 16 Number Registry IDs only."
        ],
        "test_statuses": {
            "full_177_unique_acceptance_suite": {
                "status": "NOT_RUN",
                "reason": "The D0-D4 scoped validation runs are not the complete 177-unique-test acceptance suite."
            },
            "D1_D2_source_validation": {"status": "PASS", "run_id": 41694461194, "tested_sha": "17696ec48557a33f2c231634ba25f26cf831800e", "tests_passed": 34},
            "D3_artifact_acceptance": {"status": "PASS_SCOPED", "run_id": 41682389098, "tested_sha": "a05d71adb3d45140ebc07f523dad2569e560c7c4"},
            "D3_exact_head_validation": {"status": "PASS", "run_id": 41694461171, "tested_sha": "17696ec48557a33f2c231634ba25f26cf831800e", "tests_passed": 36},
            "D4_docx_tests": {"status": "PASS", "run_id": 41694460895, "tested_sha": "17696ec48557a33f2c231634ba25f26cf831800e", "tests_passed": 5},
            "D0_D4_final_exact_head": {"status": "PASS", "run_id": 41697223043, "tested_sha": "00dfa15934780271a9be98d55d4cdd83f10e3740"},
            "D5_package_integrity": {"status": "PENDING_LOCAL_VALIDATION"}
        },
        "limitations": d3.get("limitations", []),
        "final_acceptance": "NOT_DECLARED",
        "release_authorized": False
    }
    manifest_path = out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    package = out / args.package_name
    tmp = package.with_suffix(package.suffix + ".tmp")
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as zf:
        for name in MEMBERS:
            zf.write(out / name, arcname=name)
        zf.write(manifest_path, arcname="manifest.json")
    os.replace(tmp, package)
    sums = [
        (package, args.package_name),
        (manifest_path, "manifest.json"),
        *[(out / name, name) for name in MEMBERS],
        (registry, REGISTRY_PATH),
    ]
    sums_path = out / "SHA256SUMS.txt"
    sums_path.write_text("".join(f"{sha256_file(p)}  {label}\n" for p, label in sums), encoding="utf-8")
    verify(args)
    report = {
        "schema_version": "d5-package-preflight-v1",
        "status": "PREFLIGHT_PASS_PENDING_OWNER_APPROVAL_FOR_NEW_ARTIFACT_PUBLICATION",
        "repository": REPO, "branch": args.branch, "tested_sha": args.tested_sha,
        "workflow_run_id": int(args.run_id),
        "package": {"path": "deliverables/" + args.package_name, **file_record(package), "members": 8},
        "manifest": {"path": "deliverables/manifest.json", **file_record(manifest_path)},
        "sha256sums": {"path": "deliverables/SHA256SUMS.txt", **file_record(sums_path)},
        "publication": "NOT_PUBLISHED_OWNER_APPROVAL_REQUIRED_FOR_NEW_D5_ARTIFACT",
        "main_modified": False, "d6_started": False
    }
    Path(args.report).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("D5_PACKAGE_PREFLIGHT_PASS")
    print(json.dumps(report, ensure_ascii=False, indent=2))

def verify(args) -> None:
    root = Path(args.root).resolve()
    out = root / "deliverables"
    package = out / args.package_name
    manifest_path = out / "manifest.json"
    sums_path = out / "SHA256SUMS.txt"
    expected = set(MEMBERS) | {"manifest.json"}
    names = verify_zip_safety(package, expected)
    if len(names) != 8:
        raise ValueError("D5_PACKAGE_MEMBER_COUNT_INVALID")
    with zipfile.ZipFile(package, "r") as zf:
        if zf.read("manifest.json") != manifest_path.read_bytes():
            raise ValueError("D5_EMBEDDED_MANIFEST_MISMATCH")
        for name in MEMBERS:
            if zf.read(name) != (out / name).read_bytes():
                raise ValueError("D5_PACKAGE_MEMBER_BYTES_MISMATCH:" + name)
    rows = {}
    for line in sums_path.read_text(encoding="utf-8").splitlines():
        m = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not m or m.group(2) in rows:
            raise ValueError("D5_SHA256SUMS_FORMAT_OR_DUPLICATE")
        rows[m.group(2)] = m.group(1)
    required = {args.package_name, "manifest.json", *MEMBERS, REGISTRY_PATH}
    if set(rows) != required:
        raise ValueError("D5_SHA256SUMS_COVERAGE_MISMATCH")
    for path, label in [(package, args.package_name), (manifest_path, "manifest.json"), *[(out / n, n) for n in MEMBERS], (root / REGISTRY_PATH, REGISTRY_PATH)]:
        if rows[label] != sha256_file(path):
            raise ValueError("D5_SHA256SUMS_DIGEST_MISMATCH:" + label)
    manifest = load_json(manifest_path)
    if manifest.get("package_member_count") != 8 or manifest.get("package_status") != "T2_INTERIM / NOT_FINAL_BLOCKED":
        raise ValueError("D5_MANIFEST_STATUS_OR_COUNT_INVALID")
    print(f"D5_ZIP_VALID members=8 bytes={package.stat().st_size} sha256={sha256_file(package)}")
    print(f"D5_MANIFEST_VALID bytes={manifest_path.stat().st_size} sha256={sha256_file(manifest_path)}")
    print(f"D5_SHA256SUMS_VALID lines={len(rows)} bytes={sums_path.stat().st_size} sha256={sha256_file(sums_path)}")

def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="command", required=True)
    e = sub.add_parser("extract")
    e.add_argument("--artifact-zip", required=True)
    e.add_argument("--output-dir", required=True)
    e.set_defaults(fn=extract_d3)
    b = sub.add_parser("build")
    b.add_argument("--root", default=".")
    b.add_argument("--reference", required=True)
    b.add_argument("--tested-sha", required=True)
    b.add_argument("--run-id", required=True)
    b.add_argument("--branch", default=BRANCH)
    b.add_argument("--package-name", default=PACKAGE_NAME)
    b.add_argument("--report", default="docs/stage_d/D5_PACKAGE_PREFLIGHT_2026-11-03.json")
    b.set_defaults(fn=build)
    v = sub.add_parser("verify")
    v.add_argument("--root", default=".")
    v.add_argument("--package-name", default=PACKAGE_NAME)
    v.set_defaults(fn=verify)
    args = p.parse_args()
    args.fn(args)

if __name__ == "__main__":
    main()
