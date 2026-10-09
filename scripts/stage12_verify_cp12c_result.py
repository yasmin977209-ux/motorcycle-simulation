from __future__ import annotations

import argparse
import json
from pathlib import Path

EXPECTED_RUN_ID = 37971902520
EXPECTED_RUN_SHA = "d4b335926d25d4bc2c6440effc7568260ef5aeb8"
EXPECTED_BRANCH = "tmp/stage12-c-rollforward-20261009"
EXPECTED_SOURCE_RUN_ID = "37964656154"
EXPECTED_SOURCE_RUN_SHA = "0156c5f4272eb0ca7e32442657d0df9eaf4973d3"
EXPECTED_SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
EXPECTED_MASTER_SEED = 20270101
EXPECTED_ROWS = 22546465
EXPECTED_TRIALS = 11005
EXPECTED_GLOBAL_SHA = "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44"


def main() -> int:
    parser = argparse.ArgumentParser(description="Gate CP-12-D on the exact successful CP-12-C evidence.")
    parser.add_argument("--run-json", required=True)
    parser.add_argument("--audit-json", required=True)
    args = parser.parse_args()

    run = json.loads(Path(args.run_json).read_text(encoding="utf-8"))
    audit = json.loads(Path(args.audit_json).read_text(encoding="utf-8"))

    assert run.get("id") == EXPECTED_RUN_ID, f"unexpected CP-12-C run id: {run.get('id')}"
    assert run.get("status") == "completed" and run.get("conclusion") == "success", "CP-12-C Actions run is not successful"
    assert run.get("head_sha") == EXPECTED_RUN_SHA, f"unexpected CP-12-C SHA: {run.get('head_sha')}"
    assert run.get("head_branch") == EXPECTED_BRANCH, f"unexpected CP-12-C branch: {run.get('head_branch')}"

    assert audit.get("overall_result") == "PASS", f"CP-12-C audit result is {audit.get('overall_result')}"
    assert audit.get("source_run_id") == EXPECTED_SOURCE_RUN_ID
    assert audit.get("source_run_head_sha") == EXPECTED_SOURCE_RUN_SHA
    assert audit.get("source_sha") == EXPECTED_SOURCE_SHA
    assert audit.get("master_seed") == EXPECTED_MASTER_SEED
    assert audit.get("expected_global_sha256_from_cp12b") == EXPECTED_GLOBAL_SHA
    assert audit.get("expected_daily_rows_from_cp12b") == EXPECTED_ROWS
    assert audit.get("total_daily_rows") == EXPECTED_ROWS
    assert audit.get("total_trials") == EXPECTED_TRIALS
    assert audit.get("scenario_count") == 25
    scenarios = audit.get("scenarios", {})
    assert len(scenarios) == 25
    assert all(item.get("content_sha256_matches_cp12b_manifest") is True for item in scenarios.values())
    checks = audit.get("checks", {})
    assert checks, "CP-12-C audit contains no explicit checks"
    assert all(item.get("violations") == 0 for item in checks.values()), "CP-12-C has accounting or identity violations"

    print(json.dumps({
        "gate": "CP-12-C PASS",
        "run_id": run["id"],
        "run_sha": run["head_sha"],
        "source_run_id": audit["source_run_id"],
        "scenarios": audit["scenario_count"],
        "trials": audit["total_trials"],
        "daily_rows": audit["total_daily_rows"],
        "explicit_checks": len(checks),
        "violations": sum(item["violations"] for item in checks.values()),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
