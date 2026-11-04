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
D3_ARTIFACT_ID = 13288779998
D3_ARTIFACT_RUN = 41754147172
D3_ARTIFACT_BYTES = 535567142
D3_ARTIFACT_SHA = "e49b206d8d80034b1dc0cb284bfee76d81f9e9759e2459b1608fad2f5c933ffe"
D3_ARTIFACT_EXPIRY = "2026-12-04T02:07:02Z"
REGISTRY_PATH = "results/number_registry.json"
REGISTRY_BYTES = 24137036
REGISTRY_SHA = "743ffcced8de09a766870f201c352aabcf5789c43c84bfeae654a939700e4f87"
PACKAGE_NAME = "Motorcycle_Simulation_D5_T2_INTERIM_2026-11-05.zip"
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
    "التقرير_الكامل_AR.docx": (42249, "332d7205d67ce19b12cbb196820f741cab34d99f5f11aa8780775446b1dec0bb"),
    "Full_Report_EN.docx": (41645, "945c11d9dbc71b185371cd21ff02d0db68e74d8770eec8f5e09cee00fad2a778"),
    "الملخص_AR.docx": (40435, "d1f5dcc7ac6ff67779d3a6a430645f65dad813c1ec8afa6130c9464a9109dc1d"),
    "Summary_EN.docx": (39967, "8310bbb52c0eb275ed3cbcca4d8cbb9227c438bf77db9b39454d0232d08e5699"),
    "دراسة_الجدوى_AR.docx": (40761, "1fe55fb3ece3dee3368c290551fd8461b0e47240e889fc2ceb384eb11155b3dc"),
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
        "Full_Results_EN.xlsx": (259442692, "8b14ec0b2555beae117d453722abc6c733b49ef941bfa8b3e15d299d7983d77d"),
        "النتائج_الكاملة_AR.xlsx": (259444534, "e6617de7799e9a1ee00533e9e5eb77da3ab7d32d3c9d6940fcb87dd04afcbc5d"),
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
    d3accept = load_json(root / "docs/stage_d/D3_ARTIFACT_FINAL_ACCEPTANCE_2026-11-05.json")
    d4audit = load_json(root / "docs/stage_d/D4_BUILD_AUDIT_2026-11-05.json")
    d4manifest = load_json(root / "docs/stage_d/D4_REPORT_MANIFEST_2026-11-05.json")
    if d3accept.get("owner_decision") != "ACCEPTED_BY_OWNER_2026-11-05" or d3accept.get("d3_18") != "PASS_SCOPED" or d3accept.get("d3_gate_status") != "PASS_SCOPED_WITH_LIMITATIONS":
        raise ValueError("D3_OWNER_ACCEPTANCE_OR_GATE_STATUS_INVALID")
    if d3accept.get("artifact", {}).get("id") != D3_ARTIFACT_ID or d3accept.get("artifact", {}).get("sha256") != D3_ARTIFACT_SHA:
        raise ValueError("D3_ACCEPTANCE_ARTIFACT_IDENTITY_MISMATCH")
    if d3accept.get("source_run_id") != D3_ARTIFACT_RUN or d3accept.get("artifact", {}).get("bytes") != D3_ARTIFACT_BYTES:
        raise ValueError("D3_ACCEPTANCE_LINEAGE_MISMATCH")
    if d4audit.get("status") != "PASS_SCOPED_WITH_LIMITATIONS" or int(d4audit.get("workflow_run_id", 0)) != 41916830283:
        raise ValueError("D4_BUILD_GATE_NOT_CLOSED")
    if d4audit.get("tested_sha") != d4manifest.get("tested_sha") or d4audit.get("manifest_sha256") != sha256_file(root / "docs/stage_d/D4_REPORT_MANIFEST_2026-11-05.json"):
        raise ValueError("D4_MANIFEST_LINEAGE_MISMATCH")
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
    return d3, d3audit, d3accept, d4audit, d4manifest

def build(args) -> None:
    root = Path(args.root).resolve()
    out = root / "deliverables"
    reference = Path(args.reference).resolve()
    d3, d3audit, d3accept, d4audit, d4manifest = validate_inputs(root, reference)
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
    d4_commit = d4audit.get("output_commit") or "df5bf4564fbbe2168a364190c64d9018a66211d1"
    manifest = {
        "schema_version": "motorcycle-simulation-d5-manifest-v1",
        "package_identity": "Motorcycle_Simulation_D5_T2_INTERIM_2026-11-05",
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
                "acceptance_run_id": d3accept["acceptance_run_id"],
                "owner_decision": d3accept["owner_decision"],
                "d3_18": d3accept["d3_18"],
                "d3_gate_status": d3accept["d3_gate_status"]
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
            {"stage": "D1-D2 source validation", "run_id": 41916830333, "tested_sha": "c5327554d45dc836b7d7f265b4a024dd9049e1f5", "result": "PASS"},
            {"stage": "D3 owner-approved Artifact acceptance", "run_id": 41914970361, "tested_sha": "b3dfd886ec57308c0bf68f5eec4cc8417faaa3e1", "result": "PASS_SCOPED", "artifact_id": D3_ARTIFACT_ID},
            {"stage": "D4 report build and final-head readback", "run_id": 41916830283, "tested_sha": "c5327554d45dc836b7d7f265b4a024dd9049e1f5", "final_output_commit_sha": "df5bf4564fbbe2168a364190c64d9018a66211d1", "result": "PASS_SCOPED_WITH_LIMITATIONS"}
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
            "D1_D2_source_validation": {"status": "PASS", "run_id": 41916830333, "tested_sha": "c5327554d45dc836b7d7f265b4a024dd9049e1f5"},
            "D3_artifact_acceptance": {"status": "PASS_SCOPED", "run_id": 41914970361, "tested_sha": "b3dfd886ec57308c0bf68f5eec4cc8417faaa3e1", "artifact_id": D3_ARTIFACT_ID},
            "D4_docx_build_and_tests": {"status": "PASS_SCOPED_WITH_LIMITATIONS", "run_id": 41916830283, "tested_sha": "c5327554d45dc836b7d7f265b4a024dd9049e1f5", "final_output_commit_sha": "df5bf4564fbbe2168a364190c64d9018a66211d1", "all_steps_passed": True},
            "D5_package_integrity": {"status": "PASS_BUILDER_REOPEN_AND_CHECKSUM_VALIDATION", "scope": "builder-generated ZIP, embedded manifest, 10-entry SHA256SUMS"}
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
        "status": "PACKAGE_BUILD_AND_REOPEN_PASS_PENDING_ARTIFACT_PUBLICATION",
        "repository": REPO, "branch": args.branch, "tested_sha": args.tested_sha,
        "workflow_run_id": int(args.run_id),
        "package": {"path": "deliverables/" + args.package_name, **file_record(package), "members": 8},
        "manifest": {"path": "deliverables/manifest.json", **file_record(manifest_path)},
        "sha256sums": {"path": "deliverables/SHA256SUMS.txt", **file_record(sums_path)},
        "publication": "PENDING_GITHUB_ACTIONS_ARTIFACT_UPLOAD_AND_REMOTE_READBACK",
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
    b.add_argument("--report", default="docs/stage_d/D5_PACKAGE_PREFLIGHT_2026-11-05.json")
    b.set_defaults(fn=build)
    v = sub.add_parser("verify")
    v.add_argument("--root", default=".")
    v.add_argument("--package-name", default=PACKAGE_NAME)
    v.set_defaults(fn=verify)
    args = p.parse_args()
    args.fn(args)

if __name__ == "__main__":
    main()
