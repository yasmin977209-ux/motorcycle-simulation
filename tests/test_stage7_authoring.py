from __future__ import annotations

import re
from pathlib import Path

import yaml

from scripts.stage7_stability import evaluate_gate_a, evaluate_gate_b

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

def _metrics(means: tuple[float, float, float], stable: bool = True) -> dict[str, dict[str, float | bool]]:
    keys = ("final_net_project_equity", "partner1_final_entitlement", "partner2_final_entitlement")
    return {key: {"mean": value, "stable": stable} for key, value in zip(keys, means)}

def test_stage7_workflow_pins_approved_source_sha() -> None:
    assert _workflow()["env"]["SOURCE_SHA"] == APPROVED_SOURCE_SHA

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
    steps = _workflow()["jobs"]["matrix-simulation"]["steps"]
    env_blocks = [step.get("env", {}) for step in steps if isinstance(step, dict)]
    assert any(block.get("SOURCE_SHA") == "${{ env.SOURCE_SHA }}" for block in env_blocks)

def test_stage7_still_declares_exactly_25_scenarios() -> None:
    scenarios = _workflow()["jobs"]["matrix-simulation"]["strategy"]["matrix"]["scenario"]
    assert len(scenarios) == 25
    assert len(set(scenarios)) == 25

def test_stage7_authoring_verify_runs_contract_tests() -> None:
    assert "tests/test_stage7_authoring.py" in AUTHORING_VERIFY.read_text(encoding="utf-8")

def test_stage7_trial_block_records_source_sha_in_metadata() -> None:
    assert '"source_sha": source_sha' in TRIAL_BLOCK.read_text(encoding="utf-8")

def test_stage7_timeout_contract_is_not_changed_in_commit_B() -> None:
    assert re.search(r'JOB_TIMEOUT_MINUTES:\s*"360"', _workflow_text())

def test_gate_a_pass_gate_b_fail_is_not_stable() -> None:
    previous = _metrics((1000, 700, 300), stable=False)
    current = _metrics((1001, 700.5, 300.2), stable=False)
    gate_a = evaluate_gate_a(previous_n=300, previous_metrics=previous, current_n=350, current_metrics=current, escalation_step=50, relative_epsilon=0.01, absolute_epsilon=1)
    gate_b = evaluate_gate_b(current)
    assert gate_a["stable"] is True
    assert gate_b["stable"] is False
    assert not (gate_a["stable"] and gate_b["stable"])

def test_gate_a_fail_gate_b_pass_is_not_stable() -> None:
    previous = _metrics((1000, 700, 300), stable=True)
    current = _metrics((1105, 770, 330), stable=True)
    gate_a = evaluate_gate_a(previous_n=300, previous_metrics=previous, current_n=350, current_metrics=current, escalation_step=50, relative_epsilon=0.01, absolute_epsilon=1)
    gate_b = evaluate_gate_b(current)
    assert gate_a["stable"] is False
    assert gate_b["stable"] is True
    assert not (gate_a["stable"] and gate_b["stable"])

def test_gate_a_fail_gate_b_fail_is_not_stable() -> None:
    previous = _metrics((1000, 700, 300), stable=False)
    current = _metrics((1105, 770, 330), stable=False)
    gate_a = evaluate_gate_a(previous_n=300, previous_metrics=previous, current_n=350, current_metrics=current, escalation_step=50, relative_epsilon=0.01, absolute_epsilon=1)
    gate_b = evaluate_gate_b(current)
    assert gate_a["stable"] is False
    assert gate_b["stable"] is False
    assert not (gate_a["stable"] and gate_b["stable"])

def test_gate_a_pass_gate_b_pass_requires_three_consecutive_points() -> None:
    previous = _metrics((1000, 700, 300), stable=True)
    p350 = _metrics((1001, 700.5, 300.2), stable=True)
    p400 = _metrics((1002, 701.0, 300.4), stable=True)
    p450 = _metrics((1003, 701.5, 300.6), stable=True)
    pairs = ((300, previous, 350, p350), (350, p350, 400, p400), (400, p400, 450, p450))
    checks = []
    for previous_n, previous_metrics, current_n, current_metrics in pairs:
        gate_a = evaluate_gate_a(previous_n=previous_n, previous_metrics=previous_metrics, current_n=current_n, current_metrics=current_metrics, escalation_step=50, relative_epsilon=0.01, absolute_epsilon=1)
        gate_b = evaluate_gate_b(current_metrics)
        checks.append(gate_a["stable"] and gate_b["stable"])
    assert checks == [True, True, True]

def test_c100_n1_without_rerun_is_not_allowed_to_be_stable() -> None:
    text = _workflow_text()
    assert "C100 primary sample must remain n=1" in text
    assert '"verification_trial_id": 2' in text

def test_c100_independent_rerun_uses_different_trial_id_and_derived_seed() -> None:
    text = _workflow_text()
    assert "trial_id=2" in text
    assert "different_trial_id" in text
    assert "different_derived_seed" in text
    assert "exact_result_equality" in text

def test_c100_mismatch_cannot_be_declared_stable() -> None:
    text = _workflow_text()
    assert 'state["final_status"] = None' in text
    assert "independent C100 trial result mismatch" in text

def test_c100_stability_is_after_independent_equality_proof() -> None:
    text = _workflow_text()
    equality_pos = text.index("equality = asdict(primary) == asdict(verification)")
    stable_pos = text.index('state["final_status"] = "stable"')
    assert equality_pos < stable_pos

def test_gate_a_requires_exact_n_plus_escalation_step() -> None:
    previous = _metrics((1000, 700, 300), stable=True)
    current = _metrics((1001, 700.5, 300.2), stable=True)
    gate_a = evaluate_gate_a(previous_n=300, previous_metrics=previous, current_n=351, current_metrics=current, escalation_step=50, relative_epsilon=0.01, absolute_epsilon=1)
    assert gate_a["checked"] is False

def test_joint_gate_requires_all_three_metrics() -> None:
    previous = _metrics((1000, 700, 300), stable=True)
    current = _metrics((1001, 900, 300.2), stable=True)
    gate_a = evaluate_gate_a(previous_n=300, previous_metrics=previous, current_n=350, current_metrics=current, escalation_step=50, relative_epsilon=0.01, absolute_epsilon=1)
    assert gate_a["stable"] is False


def test_stage7_preflight_does_not_rerun_passed_stages() -> None:
    text = _workflow_text()
    preflight = text[text.index("  preflight-gates:"):text.index("  matrix-simulation:")]
    forbidden = (
        "tests/test_stage1.py",
        "tests/test_stage2.py",
        "tests/test_stage3a.py",
        "tests/test_stage3b_accounting.py",
        "tests/test_stage3b_partner_equity.py",
        "tests/test_stage3b_m_order.py",
        "tests/test_stage3b_closure.py",
        "tests/test_stage3b_path1.py",
        "tests/test_stage3b_paths.py",
        "tests/test_stage3b_no_time_cap.py",
        "tests/test_stage3b_determinism.py",
        "tests/test_acceptance_16_v2.py",
        "tests/test_monte_carlo_round1.py",
        "tests/test_monte_carlo_round2.py",
        "tests/test_monte_carlo_round3.py",
        "tests/test_monte_carlo_round4.py",
    )
    for marker in forbidden:
        assert marker not in preflight


def test_stage7_preflight_is_stage7_specific() -> None:
    text = _workflow_text()
    preflight = text[text.index("  preflight-gates:"):text.index("  matrix-simulation:")]
    assert "STAGE7_PREFLIGHT_OK" in preflight
    assert "SOURCE_SHA" in preflight
