#!/usr/bin/env python3
"""Prove model import provenance against the exact approved Git source commit."""
from __future__ import annotations

import argparse
import ast
import importlib
import json
import subprocess
import sys
from pathlib import Path

SOURCE_COMMIT = "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
MASTER_SEED = 20270101
ROOT_MODULES = ("daily_engine", "monte_carlo")


def _run(args: list[str], root: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def _module_path(root: Path, name: str) -> Path | None:
    parts = name.split(".")
    module_file = root.joinpath(*parts).with_suffix(".py")
    package_file = root.joinpath(*parts, "__init__.py")
    if module_file.is_file():
        return module_file
    if package_file.is_file():
        return package_file
    return None


def _local_import_names(root: Path, file_path: Path) -> set[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                for end in range(len(parts), 0, -1):
                    candidate = ".".join(parts[:end])
                    if _module_path(root, candidate) is not None:
                        names.add(candidate)
                        break
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                package_parts = file_path.relative_to(root).parent.parts
                cut = max(0, len(package_parts) - node.level + 1)
                base_parts = list(package_parts[:cut])
                if base:
                    base_parts.extend(base.split("."))
                base = ".".join(base_parts)
            if base and _module_path(root, base) is not None:
                names.add(base)
            for alias in node.names:
                if alias.name == "*":
                    continue
                candidate = f"{base}.{alias.name}" if base else alias.name
                if _module_path(root, candidate) is not None:
                    names.add(candidate)
    return names


def verify(source_root: Path) -> dict:
    root = source_root.resolve(strict=True)
    head = _run(["rev-parse", "HEAD"], root)
    if head != SOURCE_COMMIT:
        raise RuntimeError(f"PINNED_SOURCE_COMMIT_MISMATCH:{head}")
    dirty = _run(["status", "--porcelain", "--untracked-files=all"], root)
    if dirty:
        raise RuntimeError("PINNED_SOURCE_WORKTREE_NOT_CLEAN")
    resolved: set[str] = set()
    pending = list(ROOT_MODULES)
    while pending:
        name = pending.pop()
        if name in resolved:
            continue
        path = _module_path(root, name)
        if path is None:
            raise RuntimeError(f"PINNED_SOURCE_MODULE_FILE_MISSING:{name}")
        resolved.add(name)
        pending.extend(sorted(_local_import_names(root, path) - resolved))

    for name in resolved:
        sys.modules.pop(name, None)
    sys.path[:] = [str(root)] + [
        item for item in sys.path
        if not item or Path(item).resolve() != root
    ]
    for name in ROOT_MODULES:
        importlib.import_module(name)
    modules = []
    for name in sorted(resolved):
        module = importlib.import_module(name)
        origin_value = getattr(module, "__file__", None)
        if not origin_value:
            raise RuntimeError(f"PINNED_SOURCE_MODULE_ORIGIN_MISSING:{name}")
        origin = Path(origin_value).resolve(strict=True)
        expected = _module_path(root, name).resolve(strict=True)
        if origin != expected or not origin.is_relative_to(root):
            raise RuntimeError(
                f"PINNED_SOURCE_MODULE_ORIGIN_MISMATCH:{name}:"
                f"expected={expected}:actual={origin}"
            )
        relative = origin.relative_to(root).as_posix()
        blob_sha = _run(["rev-parse", f"{SOURCE_COMMIT}:{relative}"], root)
        modules.append({
            "module": name,
            "relative_path": relative,
            "git_blob_sha": blob_sha,
            "imported_file": str(origin),
            "origin_matches_pinned_source": True,
        })
    return {
        "status": "PASS",
        "source_sha": SOURCE_SHA,
        "master_seed": MASTER_SEED,
        "source_commit": SOURCE_COMMIT,
        "checked_roots": list(ROOT_MODULES),
        "module_count": len(modules),
        "modules": modules,
        "source_worktree_clean": True,
        "trial_generation_executed": False,
        "dataset_or_parquet_modified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--output-file", default="results_gatea/source_identity.json")
    args = parser.parse_args()
    report = verify(args.source_root)
    output = Path(args.output_file)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
