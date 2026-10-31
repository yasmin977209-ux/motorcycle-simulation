#!/usr/bin/env python3
"""One-time fail-closed import of all S6 D1/D2 source files and governance text archives.

Run from a clean local clone of the authorized Stage D branch:
  python scripts/import_stage_d_sources.py \
    --source-zip /path/to/D1_D2_S6_BUILDER_SOURCE_BUNDLE.zip \
    --governing-reference-zip /path/to/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0_CANDIDATE_2026-10-30.zip \
    --historical-source-pack-zip /path/to/MOTORCYCLE_SIMULATION_SOURCE_PACK.zip \
    --local-evidence-zip /path/to/STAGE_D_LOCAL_TEXT_EVIDENCE_2026-10-31.zip --apply

The ZIP files are containers only. This script does not commit the ZIPs or binary artifact ZIPs.
It extracts individual source modules, tests and text/JSON/CSV governance files, preserves
historical and quarantined lineages, commits every extracted file to the authorized branch,
and pushes once. The GitHub Actions workflow then downloads the three large pinned artifacts
directly from GitHub and builds the shared model and Number Registry.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import zipfile
from pathlib import Path, PurePosixPath

REPOSITORY = "yasmin977209-ux/motorcycle-simulation"
BRANCH = "tmp/cp-v240-stage-d-s6-deliverables-20261030"

SOURCE_BUNDLE_SHA256 = "caa5d6d72cdc8588de104f24aa23499e85912921bce9a509e27e10e909d74dc6"
GOVERNING_ZIP_SHA256 = "efb6a663a2fc63ac5c1f052048b3dfc945e233df9810d4fe0b21b892c533e52c"
HISTORICAL_SOURCE_PACK_SHA256 = "4facbc9ed00cbbbaede83bfc65b8cdc8f0b335eabe13579f185b95a12a46ce5a"
LOCAL_D0_EVIDENCE_SHA256 = "b155d74bca7d16970dea06f77b876b2a97bcf6d240d21028234da07109a36fd2"
GOVERNING_REFERENCE_SHA256 = "225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b"
HISTORICAL_V23_SHA256 = "e5efaf0874384e8248c339ca10e248ea9e17e9f0882153b4ef88bc955b91d53f"
CLOSED_V231_SHA256 = "724a22aae9bb3caf55bf9de1f27c2edba79b453585bb863b72fe7c5e04c44db0"

CONTINUITY_SHA256 = "d9ade8e347b1b0bec7a9a60e35ca05ae2a8374c51a7ba5f7da494bd5b66c7d78"
CONTINUITY_GIT_BLOB_SHA1 = "b956ebee141e3e9d625114973a0693506454b117"

IMPORT_PATHS = {
    "scripts/s6_deliverables_builder.py",
    "scripts/s6_deliverables_model.py",
    "scripts/s6_artifact_reader.py",
    "scripts/s6_manifest_resolver.py",
    "scripts/s6_number_registry.py",
    "scripts/s6_validate_representatives.py",
    "tests/test_s6_deliverables_builder.py",
    "tests/test_s6_number_registry.py",
}
SOURCE_ARCHIVE_DOCS = {
    "docs/stage_d/D0_REPOSITORY_CLOSURE.md": "docs/stage_d/archive/source_bundle/D0_REPOSITORY_CLOSURE.md",
    "docs/stage_d/D1_BUILDER_DESIGN.md": "docs/stage_d/archive/source_bundle/D1_BUILDER_DESIGN.md",
    "docs/stage_d/D1_BUILDER_AUDIT.json": "docs/stage_d/archive/source_bundle/D1_BUILDER_AUDIT.json",
    "docs/stage_d/D1_REPOSITORY_CLOSURE.md": "docs/stage_d/archive/source_bundle/D1_REPOSITORY_CLOSURE.md",
    "docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.md": "docs/stage_d/archive/source_bundle/D2_NUMBER_REGISTRY_AUDIT.md",
    "docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.json": "docs/stage_d/archive/source_bundle/D2_NUMBER_REGISTRY_AUDIT.json",
    ".github/workflows/stage-d-deliverables-validation.yml": "docs/stage_d/archive/source_bundle/workflows/stage-d-deliverables-validation.yml",
}
SOURCE_ARCHIVE_MEMBERS = IMPORT_PATHS | set(SOURCE_ARCHIVE_DOCS)
TEXT_EXTENSIONS = {".md", ".txt", ".json", ".csv", ".yaml", ".yml", ".py", ".toml", ".xml", ".ini"}
TEXT_ROOT = "docs/governance/imported"


def run(*args: str, cwd: Path) -> str:
    p = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.returncode:
        raise RuntimeError(f"COMMAND_FAILED:{args!r}\n{p.stdout}")
    return p.stdout.strip()


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def decoded_member_name(info: zipfile.ZipInfo) -> str:
    name = info.filename
    if not (info.flag_bits & 0x800):
        try:
            repaired = name.encode("cp437").decode("utf-8")
            if repaired and "\ufffd" not in repaired:
                name = repaired
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    return name


def safe_name(name: str) -> PurePosixPath:
    p = PurePosixPath(name.replace("\\", "/"))
    if p.is_absolute() or ".." in p.parts or "\\" in name:
        raise SystemExit(f"UNSAFE_ARCHIVE_PATH:{name}")
    return p


def write_text_member(root: Path, prefix: str, name: str, raw: bytes, source_archive: str,
                      lineage: str, files: list[dict]) -> None:
    rel = safe_name(name)
    if rel.suffix.lower() not in TEXT_EXTENSIONS or b"\x00" in raw:
        return
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        raise SystemExit(f"TEXT_MEMBER_NOT_UTF8:{source_archive}:{name}")
    destination = PurePosixPath(prefix) / rel
    target = root.joinpath(*destination.parts)
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.read_bytes() != raw:
        raise SystemExit(f'GOVERNANCE_FILE_COLLISION:{destination.as_posix()}')
    target.write_bytes(raw)
    files.append({
        "repository_path": destination.as_posix(),
        "source_archive": source_archive,
        "source_member": name,
        "source_lineage": lineage,
        "size_bytes": len(raw),
        "sha256_local_source_bytes": digest(raw),
        "remote_readback_status": "PENDING",
    })


def process_nested_archive(raw_zip: bytes, prefix: str, source_archive: str, lineage: str,
                           root: Path, files: list[dict], skipped: list[dict],
                           recurse_sources: bool = True, depth: int = 0) -> None:
    if depth > 8:
        raise SystemExit(f"NESTED_ARCHIVE_DEPTH_LIMIT:{source_archive}")
    with zipfile.ZipFile(io.BytesIO(raw_zip)) as zf:
        names = [decoded_member_name(i) for i in zf.infolist()]
        if len(names) != len(set(names)):
            raise SystemExit(f"DUPLICATE_NESTED_ZIP_MEMBERS:{source_archive}")
        if zf.testzip() is not None:
            raise SystemExit(f"NESTED_ZIP_CRC_FAILURE:{source_archive}")
        for info, name in zip(zf.infolist(), names):
            rel = safe_name(name)
            if info.is_dir():
                continue
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise SystemExit(f"SYMLINK_NESTED_ZIP_MEMBER:{source_archive}:{name}")
            member = zf.read(info)
            lower = name.lower()
            if rel.suffix.lower() == ".zip":
                if not recurse_sources:
                    skipped.append({
                        "source_archive": source_archive, "source_member": name,
                        "size_bytes": len(member), "sha256": digest(member),
                        "reason": "NESTED_ARCHIVE_RECURSION_DISABLED",
                    })
                    continue
                stem = rel.stem.replace(" ", "_")
                archive_id = digest(member)[:12]
                if "v2.3.1" in lower or "quarantine" in lower:
                    next_lineage = "QUARANTINED_NOT_AUTHORITATIVE_V2.3.1"
                    next_prefix = f"{prefix}/QUARANTINE_V2.3.1/{stem}_{archive_id}"
                elif "source_pack" in lower:
                    next_lineage = "HISTORICAL_SOURCE_PACK"
                    next_prefix = f"{prefix}/SOURCE_PACK_ORIGINAL/{stem}_{archive_id}"
                else:
                    next_lineage = f"{lineage}/NESTED_ARCHIVE_TEXT_ONLY"
                    next_prefix = f"{prefix}/NESTED_ARCHIVES/{stem}_{archive_id}"
                process_nested_archive(member, next_prefix, f"{source_archive}!/{name}",
                                       next_lineage, root, files, skipped,
                                       recurse_sources=True, depth=depth + 1)
                continue
            write_text_member(root, prefix, name, member, source_archive, lineage, files)

def import_governance_archives(root: Path, governing_zip: Path, historical_zip: Path) -> list[str]:
    files: list[dict] = []
    skipped: list[dict] = []
    input_archives = []

    for path, expected, label in [
        (governing_zip, GOVERNING_ZIP_SHA256, "governing_reference_v2.4.0"),
        (historical_zip, HISTORICAL_SOURCE_PACK_SHA256, "historical_source_pack_v2.3"),
    ]:
        if not path.is_file():
            raise SystemExit(f"ARCHIVE_NOT_FOUND:{path}")
        raw = path.read_bytes()
        actual = digest(raw)
        if actual != expected:
            raise SystemExit(f"ARCHIVE_SHA256_MISMATCH:{label}:{actual}")
        input_archives.append({"label": label, "size_bytes": len(raw), "sha256": actual})

    with zipfile.ZipFile(governing_zip) as zf:
        if zf.testzip() is not None:
            raise SystemExit("GOVERNING_ZIP_CRC_FAILURE")
        for info in zf.infolist():
            name = decoded_member_name(info)
            if info.is_dir():
                continue
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise SystemExit(f"GOVERNING_ZIP_SYMLINK:{name}")
            member = zf.read(info)
            if name.lower().endswith(".zip"):
                if "OWNER_STARTER_PACK_VERIFIED" in name:
                    process_nested_archive(member, f"{TEXT_ROOT}/owner_starter_pack",
                                           "governing_reference_zip", "HISTORICAL_EVIDENCE_ARCHIVE",
                                           root, files, skipped)
                else:
                    skipped.append({"source_archive":"governing_reference_zip","source_member":name,
                                    "size_bytes":len(member),"sha256":digest(member),
                                    "reason":"BINARY_ARCHIVE_NOT_EXPANDED"})
                continue
            write_text_member(root, f"{TEXT_ROOT}/v2.4.0", name, member,
                              "governing_reference_zip", "V2.4.0_GOVERNING_OR_ARCHIVED_SOURCE", files)

    with zipfile.ZipFile(historical_zip) as zf:
        if zf.testzip() is not None:
            raise SystemExit("HISTORICAL_SOURCE_PACK_CRC_FAILURE")
        for info in zf.infolist():
            name = decoded_member_name(info)
            if info.is_dir():
                continue
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise SystemExit(f"SOURCE_PACK_SYMLINK:{name}")
            member = zf.read(info)
            if name.lower().endswith(".zip"):
                stem = PurePosixPath(name).stem.replace(" ", "_")
                archive_id = digest(member)[:12]
                if "v2.3.1" in name.lower() or "quarantine" in name.lower():
                    next_prefix = f"{TEXT_ROOT}/source_pack/QUARANTINE_V2.3.1/{stem}_{archive_id}"
                    next_lineage = "QUARANTINED_NOT_AUTHORITATIVE_V2.3.1"
                else:
                    next_prefix = f"{TEXT_ROOT}/source_pack/NESTED_ARCHIVES/{stem}_{archive_id}"
                    next_lineage = "HISTORICAL_SOURCE_PACK_NESTED_ARCHIVE"
                process_nested_archive(member, next_prefix, f"historical_source_pack_zip!/{name}",
                                       next_lineage, root, files, skipped)
                continue
            write_text_member(root, f"{TEXT_ROOT}/source_pack", name, member,
                              "historical_source_pack_zip", "HISTORICAL_V2.3_SOURCE_PACK", files)

    # Canonical, stable paths for the current governing reference and its owner approval source.
    with zipfile.ZipFile(governing_zip) as zf:
        reference_member = next(n for n in zf.namelist() if "/01_REFERENCE/" in n and n.endswith(".md"))
        approval_member = next(n for n in zf.namelist() if "/04_APPROVAL/" in n and n.endswith(".md"))
        v23_member = next(n for n in zf.namelist() if "/05_SOURCE_ARCHIVE/" in n and "v2.3_" in n and n.endswith(".md"))
        v231_member = next(n for n in zf.namelist() if "/05_SOURCE_ARCHIVE/" in n and "v2.3.1" in n and n.endswith(".md"))
        canonical = [
            ("docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md", zf.read(reference_member), GOVERNING_REFERENCE_SHA256, "CURRENT_GOVERNING_REFERENCE_V2.4.0"),
            ("docs/governance/V2.4.0_OWNER_APPROVAL_SOURCE.md", zf.read(approval_member), None, "OWNER_APPROVAL_SOURCE"),
            ("docs/governance/archive/MOTORCYCLE_SIMULATION_REFERENCE_V2.3_HISTORICAL.md", zf.read(v23_member), HISTORICAL_V23_SHA256, "HISTORICAL_EXECUTION_REFERENCE_S6"),
            ("docs/governance/archive/QUARANTINED_V2.3.1_CANDIDATE_NOT_AUTHORITATIVE.md", zf.read(v231_member), CLOSED_V231_SHA256, "QUARANTINED_NOT_AUTHORITATIVE_V2.3.1"),
        ]
        for rel, raw, expected, lineage in canonical:
            if expected and digest(raw) != expected:
                raise SystemExit(f"CANONICAL_REFERENCE_HASH_MISMATCH:{rel}:{digest(raw)}")
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and target.read_bytes() != raw:
                raise SystemExit(f'CANONICAL_FILE_COLLISION:{rel}')
            target.write_bytes(raw)
            files.append({"repository_path":rel,"source_archive":"governing_reference_zip",
                          "source_member":rel,"source_lineage":lineage,"size_bytes":len(raw),
                          "sha256_local_source_bytes":digest(raw),"remote_readback_status":"PENDING"})

    manifest = {
        "schema_version": "1.0",
        "status": "LOCAL_ARCHIVE_EXTRACTION_COMPLETE_REMOTE_READBACK_PENDING",
        "classification": "T2_INTERIM / NOT_FINAL_BLOCKED",
        "repository": REPOSITORY,
        "branch": BRANCH,
        "archive_inputs": input_archives,
        "governing_reference_sha256_expected": GOVERNING_REFERENCE_SHA256,
        "historical_v23_reference_sha256_expected": HISTORICAL_V23_SHA256,
        "closed_v231_candidate_sha256_expected": CLOSED_V231_SHA256,
        "files": sorted(files, key=lambda x: x["repository_path"]),
        "skipped_binary_archives": skipped,
    }
    manifest_path = root / "docs/governance/ARCHIVE_IMPORT_MANIFEST.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return [x["repository_path"] for x in files] + ["docs/governance/ARCHIVE_IMPORT_MANIFEST.json"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", required=True, type=Path)
    parser.add_argument("--governing-reference-zip", required=True, type=Path)
    parser.add_argument("--historical-source-pack-zip", required=True, type=Path)
    parser.add_argument("--local-evidence-zip", required=True, type=Path, help="small archive containing the D0 reconciliation CSV and executive continuity report")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--apply", action="store_true", help="required to write, commit and push")
    args = parser.parse_args()

    root = args.repo_root.resolve()
    archives = [args.source_zip.expanduser().resolve(), args.governing_reference_zip.expanduser().resolve(),
                args.historical_source_pack_zip.expanduser().resolve(), args.local_evidence_zip.expanduser().resolve()]
    if not args.apply:
        raise SystemExit("NO_WRITE_PERFORMED: pass --apply after reviewing this script")
    if not archives[0].is_file():
        raise SystemExit(f"SOURCE_BUNDLE_NOT_FOUND:{archives[0]}")
    digest_source = digest(archives[0].read_bytes())
    if digest_source != SOURCE_BUNDLE_SHA256:
        raise SystemExit(f"SOURCE_BUNDLE_SHA256_MISMATCH:{digest_source}")

    branch = run("git", "branch", "--show-current", cwd=root)
    if branch != BRANCH:
        raise SystemExit(f"WRONG_BRANCH:{branch}; expected {BRANCH}")
    if run("git", "status", "--porcelain", cwd=root):
        raise SystemExit("WORKTREE_NOT_CLEAN")
    origin = run("git", "remote", "get-url", "origin", cwd=root)
    if REPOSITORY not in origin:
        raise SystemExit(f"WRONG_ORIGIN:{origin}")
    run("git", "fetch", "origin", BRANCH, cwd=root)
    run("git", "pull", "--ff-only", "origin", BRANCH, cwd=root)
    if run("git", "rev-parse", "HEAD", cwd=root) != run("git", "rev-parse", f"origin/{BRANCH}", cwd=root):
        raise SystemExit("LOCAL_BRANCH_NOT_AT_REMOTE_HEAD")

    with zipfile.ZipFile(archives[0]) as zf:
        names = zf.namelist()
        if len(names) != len(set(names)) or set(names) != SOURCE_ARCHIVE_MEMBERS:
            raise SystemExit(f"SOURCE_ARCHIVE_MEMBER_SET_MISMATCH:{sorted(set(names)^SOURCE_ARCHIVE_MEMBERS)}")
        if zf.testzip() is not None:
            raise SystemExit("SOURCE_ARCHIVE_CRC_FAILURE")
        for info in zf.infolist():
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise SystemExit(f"SYMLINK_SOURCE_MEMBER:{info.filename}")
            p = safe_name(info.filename)
            if p.is_absolute():
                raise SystemExit(f"UNSAFE_SOURCE_PATH:{info.filename}")
        preexisting_conflict_paths = []
        for name in sorted(IMPORT_PATHS):
            target = root.joinpath(*PurePosixPath(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            raw = zf.read(name)
            if target.exists() and target.read_bytes() != raw:
                backup_rel = f"docs/stage_d/archive/pre_import_conflicts/{name}"
                backup = root / backup_rel
                backup.parent.mkdir(parents=True, exist_ok=True)
                previous = target.read_bytes()
                if backup.exists() and backup.read_bytes() != previous:
                    raise SystemExit(f"PRE_IMPORT_BACKUP_COLLISION:{backup_rel}")
                backup.write_bytes(previous)
                preexisting_conflict_paths.append(backup_rel)
            if name.endswith(".py"):
                text = raw.decode("utf-8")
                text = text.replace(
                    "bf6f157c26a2072ccb5c5df4b73e1e03332e4c51439772a7c53f00a9e7747caf",
                    CONTINUITY_SHA256,
                ).replace(
                    "3f05f706cca1d14ae9326cf5519f4271b050e5e3",
                    CONTINUITY_GIT_BLOB_SHA1,
                )
                raw = text.encode("utf-8")
            target.write_bytes(raw)

    source_archive_paths = []
    with zipfile.ZipFile(archives[0]) as zf:
        for source_name, destination in sorted(SOURCE_ARCHIVE_DOCS.items()):
            raw = zf.read(source_name)
            raw.decode("utf-8")
            target = root / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and target.read_bytes() != raw:
                raise SystemExit(f"SOURCE_ARCHIVE_DOCUMENT_COLLISION:{destination}")
            target.write_bytes(raw)
            source_archive_paths.append(destination)

    governance_paths = import_governance_archives(root, archives[1], archives[2])
    local_evidence_paths = []
    if not archives[3].is_file():
        raise SystemExit(f'LOCAL_EVIDENCE_ARCHIVE_NOT_FOUND:{archives[3]}')
    local_evidence_raw = archives[3].read_bytes()
    if digest(local_evidence_raw) != LOCAL_D0_EVIDENCE_SHA256:
        raise SystemExit(f'LOCAL_EVIDENCE_ARCHIVE_SHA256_MISMATCH:{digest(local_evidence_raw)}')
    local_targets = {
        'D0_trial_manifest_reconciliation_105.csv': 'docs/stage_d/archive/D0_trial_manifest_reconciliation_105.csv',
        '01_EXECUTIVE_AND_CONTINUITY_REPORT_AR-1.md': 'docs/stage_d/archive/01_EXECUTIVE_AND_CONTINUITY_REPORT_AR-1.md',
    }
    with zipfile.ZipFile(archives[3]) as zf:
        if zf.testzip() is not None or set(zf.namelist()) != set(local_targets):
            raise SystemExit('LOCAL_EVIDENCE_ARCHIVE_MEMBER_OR_CRC_MISMATCH')
        for member, rel in local_targets.items():
            raw = zf.read(member)
            raw.decode('utf-8')
            target = root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and target.read_bytes() != raw:
                raise SystemExit(f'LOCAL_EVIDENCE_FILE_COLLISION:{rel}')
            target.write_bytes(raw)
            local_evidence_paths.append(rel)
    manifest_path = root / 'docs/governance/ARCHIVE_IMPORT_MANIFEST.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['archive_inputs'].append({'label':'d1d2_source_bundle','size_bytes':archives[0].stat().st_size,'sha256':digest_source})
    manifest['archive_inputs'].append({'label':'d0_local_text_evidence','size_bytes':archives[3].stat().st_size,'sha256':LOCAL_D0_EVIDENCE_SHA256})
    for imported_path in sorted(IMPORT_PATHS):
        raw = (root / imported_path).read_bytes()
        manifest['files'].append({'repository_path':imported_path,'source_archive':'d1d2_source_bundle',
                                  'source_member':imported_path,'source_lineage':'S6_D1_D2_IMPLEMENTATION',
                                  'size_bytes':len(raw),'sha256_local_source_bytes':digest(raw),
                                  'remote_readback_status':'PENDING'})
    for imported_path in sorted(preexisting_conflict_paths):
        raw = (root / imported_path).read_bytes()
        manifest['files'].append({'repository_path':imported_path,'source_archive':'pre_import_remote_branch',
                                  'source_member':imported_path.replace('docs/stage_d/archive/pre_import_conflicts/','',1),
                                  'source_lineage':'PRE_IMPORT_CONFLICTED_CONTENT_PRESERVED',
                                  'size_bytes':len(raw),'sha256_local_source_bytes':digest(raw),
                                  'remote_readback_status':'PENDING'})
    for imported_path in sorted(source_archive_paths):
        raw = (root / imported_path).read_bytes()
        manifest['files'].append({'repository_path':imported_path,'source_archive':'d1d2_source_bundle',
                                  'source_member':next(k for k,v in SOURCE_ARCHIVE_DOCS.items() if v==imported_path),
                                  'source_lineage':'SOURCE_BUNDLE_DOCUMENT_ARCHIVE',
                                  'size_bytes':len(raw),'sha256_local_source_bytes':digest(raw),
                                  'remote_readback_status':'PENDING'})
    manifest['files'] = sorted(manifest['files'], key=lambda x:x['repository_path'])
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    for imported_path in sorted(local_evidence_paths):
        raw = (root / imported_path).read_bytes()
        manifest['files'].append({'repository_path':imported_path,'source_archive':'d0_local_text_evidence',
                                  'source_member':Path(imported_path).name,'source_lineage':'D0_LOCAL_DERIVED_AUDIT_REPORTED_ONLY',
                                  'size_bytes':len(raw),'sha256_local_source_bytes':digest(raw),
                                  'remote_readback_status':'PENDING'})
    manifest['files'] = sorted(manifest['files'], key=lambda x:x['repository_path'])
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    all_paths = IMPORT_PATHS | set(governance_paths) | set(local_evidence_paths) | set(source_archive_paths) | set(preexisting_conflict_paths)
    for path in sorted(all_paths):
        run("git", "add", path, cwd=root)
    changed = set(run("git", "diff", "--cached", "--name-only", cwd=root).splitlines())
    if not set(changed).issubset(all_paths):
        raise SystemExit(f"UNEXPECTED_STAGED_PATHS:{sorted(set(changed)-all_paths)}")
    if not changed:
        print(json.dumps({'status':'NO_CHANGES_ALREADY_IMPORTED','branch':BRANCH,'files_expected':len(all_paths)},indent=2))
        return 0

    name = subprocess.run(["git", "config", "user.name"], cwd=root, text=True, stdout=subprocess.PIPE).stdout.strip()
    email = subprocess.run(["git", "config", "user.email"], cwd=root, text=True, stdout=subprocess.PIPE).stdout.strip()
    if not name:
        run("git", "config", "user.name", "Stage D source importer", cwd=root)
    if not email:
        run("git", "config", "user.email", "stage-d-import@users.noreply.github.com", cwd=root)
    run("git", "commit", "-m", "feat(stage-d): import S6 sources and governing text archives", cwd=root)
    commit = run("git", "rev-parse", "HEAD", cwd=root)
    run("git", "push", "origin", f"HEAD:refs/heads/{BRANCH}", cwd=root)
    remote = run("git", "ls-remote", "origin", f"refs/heads/{BRANCH}", cwd=root).split()[0]
    if remote != commit:
        raise SystemExit(f"REMOTE_PUSH_HEAD_MISMATCH:{remote}:{commit}")

    print(json.dumps({
        "status": "SOURCE_AND_GOVERNANCE_TEXT_PUSHED_AWAITING_GITHUB_WORKFLOW",
        "repository": REPOSITORY,
        "branch": BRANCH,
        "commit_sha": commit,
        "source_bundle_sha256": digest_source,
        "governing_reference_zip_sha256": digest(archives[1].read_bytes()),
        "historical_source_pack_zip_sha256": digest(archives[2].read_bytes()),
        "local_d0_evidence_zip_sha256": LOCAL_D0_EVIDENCE_SHA256,
        "files_committed": len(changed),
        "governance_text_files": len(json.loads((root / 'docs/governance/ARCHIVE_IMPORT_MANIFEST.json').read_text(encoding='utf-8')).get('files',[])),
        "canonical_governing_reference": "docs/governance/MOTORCYCLE_SIMULATION_GOVERNING_REFERENCE_V2.4.0.md",
        "workflow": f"https://github.com/{REPOSITORY}/actions",
        "main_modified": False,
        "pr_merge_release": "NOT_CREATED",
        "simulation_trial_monte_carlo_n4800": "NOT_RUN",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
