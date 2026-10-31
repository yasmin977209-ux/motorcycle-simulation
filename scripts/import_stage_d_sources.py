#!/usr/bin/env python3
"""One-time, fail-closed import of the extracted S6 D1/D2 source files to the authorized GitHub branch.

Run from a local clone after downloading the 50 KB source container once:
  python scripts/import_stage_d_sources.py --source-zip /path/to/D1_D2_S6_BUILDER_SOURCE_BUNDLE.zip --apply

This script never uploads files to ChatGPT. It extracts only the six source modules and two
test modules, applies the verified current continuity pins, commits those individual files,
and pushes only the authorized Stage D branch. The GitHub Actions workflow then downloads
the three immutable pinned input artifacts itself and builds the large JSON outputs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

REPOSITORY = "yasmin977209-ux/motorcycle-simulation"
BRANCH = "tmp/cp-v240-stage-d-s6-deliverables-20261030"
SOURCE_BUNDLE_SHA256 = "caa5d6d72cdc8588de104f24aa23499e85912921bce9a509e27e10e909d74dc6"
CONTINUITY_SHA256 = "7458723582ba50454ff80bacb4132afacf76035de9db0907da0145d86ed20f74"
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
ARCHIVE_MEMBERS = IMPORT_PATHS | {
    "docs/stage_d/D0_REPOSITORY_CLOSURE.md",
    "docs/stage_d/D1_BUILDER_DESIGN.md",
    "docs/stage_d/D1_BUILDER_AUDIT.json",
    "docs/stage_d/D1_REPOSITORY_CLOSURE.md",
    "docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.md",
    "docs/stage_d/D2_NUMBER_REGISTRY_AUDIT.json",
    ".github/workflows/stage-d-deliverables-validation.yml",
}


def run(*args: str, cwd: Path) -> str:
    p = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.returncode:
        raise RuntimeError(f"COMMAND_FAILED:{args!r}\n{p.stdout}")
    return p.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-zip", required=True, type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--apply", action="store_true", help="required to write, commit and push")
    args = parser.parse_args()

    root = args.repo_root.resolve()
    archive = args.source_zip.expanduser().resolve()
    if not args.apply:
        raise SystemExit("NO_WRITE_PERFORMED: pass --apply after reviewing this script")
    if not archive.is_file():
        raise SystemExit(f"SOURCE_BUNDLE_NOT_FOUND:{archive}")
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    if digest != SOURCE_BUNDLE_SHA256:
        raise SystemExit(f"SOURCE_BUNDLE_SHA256_MISMATCH:{digest}")

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

    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
        if len(names) != len(set(names)):
            raise SystemExit("DUPLICATE_ZIP_MEMBERS")
        if set(names) != ARCHIVE_MEMBERS:
            raise SystemExit(f"SOURCE_ARCHIVE_MEMBER_SET_MISMATCH:{sorted(set(names)^ARCHIVE_MEMBERS)}")
        if zf.testzip() is not None:
            raise SystemExit("SOURCE_ARCHIVE_CRC_FAILURE")
        for info in zf.infolist():
            if (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise SystemExit(f"SYMLINK_ARCHIVE_MEMBER:{info.filename}")
        for name in names:
            p = PurePosixPath(name)
            if p.is_absolute() or ".." in p.parts or "\\" in name:
                raise SystemExit(f"UNSAFE_ARCHIVE_PATH:{name}")
        for name in sorted(IMPORT_PATHS):
            target = root.joinpath(*PurePosixPath(name).parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            raw = zf.read(name)
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

    for path in sorted(IMPORT_PATHS):
        run("git", "add", path, cwd=root)
    changed = run("git", "diff", "--cached", "--name-only", cwd=root).splitlines()
    if set(changed) != IMPORT_PATHS:
        raise SystemExit(f"STAGED_PATH_SET_MISMATCH:{sorted(set(changed)^IMPORT_PATHS)}")

    name = subprocess.run(["git", "config", "user.name"], cwd=root, text=True, stdout=subprocess.PIPE).stdout.strip()
    email = subprocess.run(["git", "config", "user.email"], cwd=root, text=True, stdout=subprocess.PIPE).stdout.strip()
    if not name:
        run("git", "config", "user.name", "Stage D source importer", cwd=root)
    if not email:
        run("git", "config", "user.email", "stage-d-import@users.noreply.github.com", cwd=root)
    run("git", "commit", "-m", "feat(stage-d): publish independent S6 D1-D2 source and tests", cwd=root)
    commit = run("git", "rev-parse", "HEAD", cwd=root)
    run("git", "push", "origin", f"HEAD:refs/heads/{BRANCH}", cwd=root)
    remote = run("git", "ls-remote", "origin", f"refs/heads/{BRANCH}", cwd=root).split()[0]
    if remote != commit:
        raise SystemExit(f"REMOTE_PUSH_HEAD_MISMATCH:{remote}:{commit}")

    print(json.dumps({
        "status": "SOURCE_FILES_PUSHED_AWAITING_GITHUB_WORKFLOW",
        "repository": REPOSITORY,
        "branch": BRANCH,
        "commit_sha": commit,
        "source_bundle_sha256": digest,
        "files_committed": sorted(IMPORT_PATHS),
        "workflow": f"https://github.com/{REPOSITORY}/actions",
        "main_modified": False,
        "pr_merge_release": "NOT_CREATED",
        "simulation_trial_monte_carlo_n4800": "NOT_RUN",
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
