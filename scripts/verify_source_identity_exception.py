#!/usr/bin/env python3
"""Verify the one owner-approved additive source adapter without running simulation."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

APPROVED_SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
REPLAY_RUN_ID = 38461464864
REPLAY_TESTED_SHA = "6da81aadbf451131304024d919f6a89be772b717"
MODEL_FILES = (
    "constants.py", "dateutils.py", "rng.py", "entities.py",
    "state_machine.py", "daily_engine.py", "accounting.py", "collection.py",
    "guarantee.py", "friday.py", "settlement.py", "closure.py",
    "partner_equity.py", "monte_carlo.py",
)
ALLOWED_ADAPTER_TEXT = '''# Adapter للتوافق التاريخي فقط؛ لا يضيف منطقاً لإنشاء العقد.
def _create_contract(
    project: Project,
    bike: Bike,
    contract_type: ContractType,
    current_date: date,
) -> Contract:
    """واجهة توافق تاريخية — تُفوّض إلى _new_contract."""
    return _new_contract(project, bike, contract_type, current_date)


'''
ALLOWED_ADAPTER_BYTES = ALLOWED_ADAPTER_TEXT.encode("utf-8")


class SourceIdentityExceptionError(RuntimeError):
    pass


def strip_allowlisted_adapter(candidate_bytes: bytes) -> bytes:
    """Remove exactly one byte-identical approved adapter; no fuzzy matching."""
    occurrences = candidate_bytes.count(ALLOWED_ADAPTER_BYTES)
    if occurrences != 1:
        raise SourceIdentityExceptionError(f"ALLOWLISTED_ADAPTER_OCCURRENCE_MISMATCH:{occurrences}")
    return candidate_bytes.replace(ALLOWED_ADAPTER_BYTES, b"", 1)


def _git_show(source_sha: str, path: str) -> bytes:
    result = subprocess.run(["git", "show", f"{source_sha}:{path}"], capture_output=True, check=False)
    if result.returncode != 0:
        raise SourceIdentityExceptionError(
            f"PINNED_SOURCE_FILE_UNAVAILABLE:{path}:"
            + result.stderr.decode("utf-8", errors="replace")[-500:]
        )
    return result.stdout


def verify_source_tree(source_sha: str, root: Path = Path(".")) -> dict[str, Any]:
    if source_sha != APPROVED_SOURCE_SHA:
        raise SourceIdentityExceptionError(f"SOURCE_SHA_NOT_APPROVED:{source_sha}")
    differences = []
    for path in MODEL_FILES:
        pinned, candidate = _git_show(source_sha, path), (root / path).read_bytes()
        if path == "daily_engine.py":
            recovered = strip_allowlisted_adapter(candidate)
            if recovered != pinned:
                differences.append({
                    "path": path,
                    "classification": "UNALLOWLISTED_SOURCE_DIFF",
                    "pinned_sha256": hashlib.sha256(pinned).hexdigest(),
                    "candidate_without_adapter_sha256": hashlib.sha256(recovered).hexdigest(),
                })
        elif candidate != pinned:
            differences.append({
                "path": path,
                "classification": "UNALLOWLISTED_SOURCE_DIFF",
                "pinned_sha256": hashlib.sha256(pinned).hexdigest(),
                "candidate_sha256": hashlib.sha256(candidate).hexdigest(),
            })
    if differences:
        raise SourceIdentityExceptionError("UNALLOWLISTED_SOURCE_DIFF:" + json.dumps(differences, sort_keys=True))
    pinned_engine, candidate_engine = _git_show(source_sha, "daily_engine.py"), (root / "daily_engine.py").read_bytes()
    return {
        "status": "PASS",
        "classification": "additive_compatibility_adapter",
        "source_sha": source_sha,
        "changed_model_files": ["daily_engine.py"],
        "allowlisted_adapter_occurrences": candidate_engine.count(ALLOWED_ADAPTER_BYTES),
        "pinned_daily_engine_sha256": hashlib.sha256(pinned_engine).hexdigest(),
        "candidate_daily_engine_sha256": hashlib.sha256(candidate_engine).hexdigest(),
        "candidate_without_adapter_sha256": hashlib.sha256(strip_allowlisted_adapter(candidate_engine)).hexdigest(),
        "replay_evidence": {
            "run_id": REPLAY_RUN_ID,
            "tested_sha": REPLAY_TESTED_SHA,
            "matching_trial_fingerprints": "10/10",
            "drift_count": 0,
            "dataset_modified": False,
            "parquet_modified": False,
            "full_pytest_conclusion": "FAIL — 3 failed, 384 passed, 1 skipped",
        },
        "source_sha_bumped": False,
        "trial_generation_executed": False,
        "historical_dataset_modified": False,
        "parquet_modified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--output", default="")
    args = parser.parse_args()
    try:
        report, code = verify_source_tree(args.source_sha), 0
    except Exception as exc:
        report, code = {
            "status": "FAIL",
            "classification": "K_CODE",
            "reason": str(exc),
            "source_sha": args.source_sha,
            "source_sha_bumped": False,
            "trial_generation_executed": False,
            "historical_dataset_modified": False,
            "parquet_modified": False,
        }, 1
    raw = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(raw, encoding="utf-8")
    print(raw, end="")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
