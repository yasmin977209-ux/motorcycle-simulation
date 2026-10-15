#!/usr/bin/env python3
"""Read-only live verification of the decision-approved Gate A provider extension."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from scripts.golden_reference_provider import (
    APPROVED_SOURCE_COMMIT,
    APPROVED_SOURCE_SHA,
    BASE_TRIAL_COUNT,
    DECISION_ID,
    EXTENDED_TRIAL_COUNT,
    EXTENSION_ARTIFACT_ID,
    EXTENSION_ARTIFACT_SHA256,
    EXTENSION_DECISION_ID,
    EXTENSION_RUN_HEAD,
    EXTENSION_RUN_ID,
    EXTENSION_SCENARIO,
    EXTENSION_TRIAL_ID_END,
    EXTENSION_TRIAL_ID_START,
    MASTER_SEED,
    SCENARIOS,
    GoldenReferenceProvider,
)


def verify_provider() -> dict:
    provider = GoldenReferenceProvider()
    if provider.load_error:
        raise RuntimeError(f"GOLDEN_PROVIDER_LOAD_FAILED:{provider.load_error}")
    if not provider.verify_source_identity(APPROVED_SOURCE_SHA):
        raise RuntimeError("GOLDEN_PROVIDER_SOURCE_SHA_IDENTITY_FAIL")
    if provider.source_commit != APPROVED_SOURCE_COMMIT:
        raise RuntimeError("GOLDEN_PROVIDER_SOURCE_COMMIT_IDENTITY_FAIL")
    if provider.master_seed != MASTER_SEED:
        raise RuntimeError("GOLDEN_PROVIDER_MASTER_SEED_IDENTITY_FAIL")
    if provider.base_trial_count != BASE_TRIAL_COUNT:
        raise RuntimeError("GOLDEN_PROVIDER_BASE_COUNT_FAIL")
    if provider.trial_count != EXTENDED_TRIAL_COUNT:
        raise RuntimeError("GOLDEN_PROVIDER_EXTENDED_COUNT_FAIL")
    if provider.scenario_count != 25:
        raise RuntimeError("GOLDEN_PROVIDER_SCENARIO_COUNT_FAIL")
    if provider.extension_decision_id != EXTENSION_DECISION_ID:
        raise RuntimeError("GOLDEN_PROVIDER_EXTENSION_DECISION_FAIL")
    if provider.extension_run_id != EXTENSION_RUN_ID or provider.extension_run_head_sha != EXTENSION_RUN_HEAD:
        raise RuntimeError("GOLDEN_PROVIDER_EXTENSION_RUN_IDENTITY_FAIL")
    if provider.extension_artifact_id != EXTENSION_ARTIFACT_ID:
        raise RuntimeError("GOLDEN_PROVIDER_EXTENSION_ARTIFACT_ID_FAIL")
    if provider.extension_artifact_sha256 != EXTENSION_ARTIFACT_SHA256:
        raise RuntimeError("GOLDEN_PROVIDER_EXTENSION_ARTIFACT_DIGEST_FAIL")
    if provider.base_source_map_sha256 != "166cae242d972c597f1a4466d184062f3d959649eb5e2440ad8de8b75663ff2c":
        raise RuntimeError("GOLDEN_PROVIDER_BASE_MAP_IDENTITY_FAIL")
    if provider.source_map_sha256 != provider.get_golden_reference_id().rsplit(":", 1)[-1]:
        raise RuntimeError("GOLDEN_PROVIDER_COMBINED_MAP_IDENTITY_FAIL")
    coverage = {scenario: sorted(provider.get_coverage(scenario)) for scenario in SCENARIOS}
    for scenario in SCENARIOS:
        expected = (
            [1] if scenario.startswith("C100_")
            else list(range(1, EXTENSION_TRIAL_ID_END + 1))
            if scenario == EXTENSION_SCENARIO
            else list(range(1, 1201))
        )
        if coverage[scenario] != expected:
            raise RuntimeError(f"GOLDEN_PROVIDER_COVERAGE_MISMATCH:{scenario}")
        for trial_id in expected:
            if provider.get_fingerprint(scenario, trial_id) is None:
                raise RuntimeError(f"GOLDEN_PROVIDER_FINGERPRINT_MISSING:{scenario}/{trial_id}")
    total = sum(len(ids) for ids in coverage.values())
    if total != EXTENDED_TRIAL_COUNT or total != 25205:
        raise RuntimeError(f"GOLDEN_PROVIDER_TOTAL_COVERAGE_FAIL:{total}")
    return {
        "status": "PASS",
        "source_sha": provider.source_sha,
        "source_commit": provider.source_commit,
        "master_seed": provider.master_seed,
        "base_decision_id": DECISION_ID,
        "extension_decision_id": provider.extension_decision_id,
        "base_trial_count": provider.base_trial_count,
        "trial_count": provider.trial_count,
        "scenario_count": provider.scenario_count,
        "base_source_map_sha256": provider.base_source_map_sha256,
        "extension_map_sha256": provider.extension_map_sha256,
        "combined_map_sha256": provider.source_map_sha256,
        "golden_reference_id": provider.get_golden_reference_id(),
        "extension_run_id": provider.extension_run_id,
        "extension_workflow_head_sha": provider.extension_run_head_sha,
        "extension_artifact_id": provider.extension_artifact_id,
        "extension_artifact_sha256": provider.extension_artifact_sha256,
        "scenario_coverage": {
            scenario: {
                "first_trial_id": ids[0],
                "last_trial_id": ids[-1],
                "count": len(ids),
            }
            for scenario, ids in coverage.items()
        },
        "prior_failure_preserved": {
            "metric": "C030_G030/P90_Final_Cash",
            "transition": "N300->N600",
            "relative_change_percent": 1.5715059334983579,
            "strict_limit_percent": 1,
            "status": "FAIL",
        },
        "checkpoint_run_id": None,
        "checkpoint_status": "NOT_STARTED",
        "statistical_checkpoint_executed": False,
        "source_sha_bumped": False,
        "dataset_or_parquet_modified": False,
        "main_modified": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-file", default="results_gatea/provider_extension_validation.json")
    args = parser.parse_args()
    report = verify_provider()
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
