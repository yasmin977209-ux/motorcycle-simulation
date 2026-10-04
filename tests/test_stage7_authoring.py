from __future__ import annotations

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = REPO_ROOT / ".github" / "workflows" / "stage7-full-run.yml"
AUTHORING_VERIFY = REPO_ROOT / ".github" / "workflows" / "stage7-authoring-verify.yml"
TRIAL_BLOCK = REPO_ROOT / "scripts" / "stage7_run_trial_block.py"

APPROVED_SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
MODEL_FILES = (
    "constants.py",
    "dateutils.py",
    "rng.py",
    "entities.py",
    "state_machine.py",
    "daily_engine.py",
    "accounting.py",
    "collection.py",
    "guarantee.py",
    "friday.py",
    "settlement.py",
    "closure.py",
    "partner_equity.py",
    "monte_carlo.py",
)

def _workflow_text() -> str:
    return WORKFLOW.read_text(encoding="utf-8")

def _workflow() -> dict:
    return yaml.safe_load(_workflow_text())

def test_stage7_workflow_pins_approved_source_sha() -> None:
    spec = _workflow()
    assert spec["env"]["SOURCE_SHA"] == APPROVED_SOURCE_SHA

def test_stage7_workflow_has_no_dynamic_origin_main_source_resolution() -> None:
    text = _workflow_text()
    assert "git rev-parse origin/main" not in text
    assert "Determine stable source SHA from main" not in text
    assert "steps.source.outputs.source_sha" not in text

def test_stage7_workflow_declares_model_source_boundary() -> None:
    text = _workflow_text()
    for path in MODEL_FILES:
        assert path in text

def test_stage7_workflow_verifies_pinned_commit_and_model_integrity() -> None:
    text = _workflow_text()
    assert 'git cat-file -e "${SOURCE_SHA}^{commit}"' in text
    assert "MODEL_SOURCE_DRIFT_DETECTED" in text
    assert "MODEL_SOURCE_BOUNDARY_OK" in text

def test_stage7_source_sha_is_passed_to_matrix_state_and_orchestrator() -> None:
    spec = _workflow()
    matrix_steps = spec["jobs"]["matrix-simulation"]["steps"]
    env_blocks = [step.get("env", {}) for step in matrix_steps if isinstance(step, dict)]
    assert any(block.get("SOURCE_SHA") == "${{ env.SOURCE_SHA }}" for block in env_blocks)

def test_stage7_still_declares_exactly_25_scenarios() -> None:
    spec = _workflow()
    scenarios = spec["jobs"]["matrix-simulation"]["strategy"]["matrix"]["scenario"]
    assert len(scenarios) == 25
    assert len(set(scenarios)) == 25

def test_stage7_authoring_verify_runs_contract_tests() -> None:
    text = AUTHORING_VERIFY.read_text(encoding="utf-8")
    assert "tests/test_stage7_authoring.py" in text

def test_stage7_trial_block_records_source_sha_in_metadata() -> None:
    text = TRIAL_BLOCK.read_text(encoding="utf-8")
    assert '"source_sha": source_sha' in text

def test_stage7_timeout_contract_is_not_changed_in_commit_A() -> None:
    text = _workflow_text()
    assert re.search(r'JOB_TIMEOUT_MINUTES:\s*"360"', text)

