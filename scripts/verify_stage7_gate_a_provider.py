#!/usr/bin/env python3
"""Read-only live verification of the exact Gate A golden reference provider."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from scripts.golden_reference_provider import GoldenReferenceProvider
from scripts.stage7_gate_a_provider import validate_provider_full_coverage


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    source_sha = os.environ.get("SOURCE_SHA", "")
    try:
        master_seed = int(os.environ["MASTER_SEED"])
    except (KeyError, ValueError):
        master_seed = -1
    provider = GoldenReferenceProvider()
    report = validate_provider_full_coverage(provider, source_sha=source_sha, master_seed=master_seed)
    report["run_mode"] = "read_only_provider_validation"
    report["workflow_or_monte_carlo_executed"] = False
    report["report_file"] = str(args.output)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
