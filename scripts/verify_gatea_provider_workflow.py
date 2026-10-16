#!/usr/bin/env python3
"""Validate that this CP's temporary workflow cannot run Stage 7 or Monte Carlo."""
from __future__ import annotations

from pathlib import Path
import yaml

EXPECTED_BRANCH = "tmp/cp-gatea-provider-bind-20261016"
TEMP_WORKFLOW = Path(".github/workflows/tmp-cp-gatea-provider-bind-verify.yml")
STAGE7_WORKFLOW = Path(".github/workflows/stage7-full-run.yml")


def main() -> None:
    temporary = yaml.safe_load(TEMP_WORKFLOW.read_text(encoding="utf-8"))
    triggers = temporary.get("on") or temporary.get(True) or {}
    assert triggers.get("push", {}).get("branches") == [EXPECTED_BRANCH]
    assert "workflow_dispatch" not in triggers
    assert set(temporary["permissions"].keys()) == {"contents", "actions"}
    assert temporary["permissions"]["contents"] == "read"
    assert temporary["permissions"]["actions"] == "read"
    assert len(temporary["jobs"]) == 1
    job = next(iter(temporary["jobs"].values()))
    assert job["timeout-minutes"] == 15
    steps = job["steps"]
    joined = "\n".join(str(step.get("run", "")) for step in steps)
    assert "scripts/verify_stage7_gate_a_provider.py" in joined
    assert "scripts/verify_source_identity_exception.py" in joined
    assert "pytest" in joined
    forbidden = (
        "scripts.stage7_run_trial_block",
        "python -m scripts.stage7_run_trial_block",
        "gh workflow run",
        "workflow_dispatch",
    )
    assert all(term not in joined for term in forbidden)
    stage7 = yaml.safe_load(STAGE7_WORKFLOW.read_text(encoding="utf-8"))
    stage7_triggers = stage7.get("on") or stage7.get(True) or {}
    assert stage7_triggers.get("push", {}).get("branches") == ["tmp/stage7-full-run-20261004"]
    print("CP_GATEA_PROVIDER_WORKFLOW_STATIC_VALIDATION=PASS")


if __name__ == "__main__":
    main()
