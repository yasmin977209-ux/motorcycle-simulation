from __future__ import annotations

import base64
import json
from datetime import datetime, timedelta, timezone
import re
from pathlib import Path

import pytest
import yaml

from scripts.stage7_state import (
    LeaseConflict,
    StateIntegrityError,
    StateRemoteNotFound,
    StateStore,
    build_artifact_identity,
    validate_trial_sequence,
)
from scripts.stage7_stability import (
    evaluate_gate_a,
    evaluate_gate_b,
    has_successful_adjacent_transition_window,
)

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


def test_requirements_include_pyyaml() -> None:
    requirements = (REPO_ROOT / "requirements.txt").read_text(encoding="utf-8")
    assert "pyyaml" in requirements.lower()

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

def test_stage7_internal_timeout_leaves_cleanup_margin() -> None:
    text = _workflow_text()
    assert 'JOB_TIMEOUT_MINUTES: "40"' in text
    assert _workflow()["jobs"]["matrix-simulation"]["timeout-minutes"] == 45


def test_stage7_workflow_does_not_contain_360_timeout() -> None:
    timeout_lines = [
        line
        for line in _workflow_text().splitlines()
        if "timeout" in line.lower() or "JOB_TIMEOUT_MINUTES" in line
    ]
    assert timeout_lines
    assert all(
        stale not in line
        for line in timeout_lines
        for stale in ("90", "360")
    )


def test_stage7_timeout_change_is_documented() -> None:
    text = _workflow_text()
    assert 'JOB_TIMEOUT_MINUTES: "40"' in text
    assert "Operational orchestration cap; model logic has no max_days limit." in text

def test_stage7_workflow_has_concurrency_guard() -> None:
    concurrency = _workflow()["concurrency"]
    assert concurrency == {
        "group": "stage7-full-run-${{ github.workflow }}-${{ github.ref }}",
        "cancel-in-progress": False,
        "queue": "max",
    }
def test_stage7_preflight_fails_closed_on_existing_active_stage7_runs() -> None:
    text = _workflow_text()
    preflight = text[text.index("  preflight-gates:"):text.index("  matrix-simulation:")]
    top_permissions = text[:text.index("jobs:")]
    assert "actions: read" in top_permissions
    assert "actions: write" not in top_permissions
    assert "GH_TOKEN: ${{ github.token }}" in preflight
    assert "gh api --paginate" in preflight
    assert "actions/runs?branch=tmp%2Fstage7-full-run-20261004" in preflight
    assert 'select(.status == "in_progress")' in preflight
    assert "select(.conclusion == null)" not in preflight
    assert "STAGE7_ACTIVE_RUN_CONFLICT=" in preflight
    assert "refusing to cancel another run" in preflight
    assert "actions/runs/${run_id}/cancel" not in preflight
    assert "CANCELLED_STALE_RUN=" not in preflight
    assert "for attempt in $(seq 1 90); do" not in preflight
def test_stage7_preflight_enumerates_state_branches_without_force_reset() -> None:
    text = _workflow_text()
    preflight = text[text.index("  preflight-gates:"):text.index("  matrix-simulation:")]
    assert "SCENARIOS=(" in preflight
    assert "C100_G100 C100_G070 C100_G050 C100_G030 C100_G000" in preflight
    assert "C085_G100 C085_G070 C085_G050 C085_G030 C085_G000" in preflight
    assert "C070_G100 C070_G070 C070_G050 C070_G030 C070_G000" in preflight
    assert "C050_G100 C050_G070 C050_G050 C050_G030 C050_G000" in preflight
    assert "C030_G100 C030_G070 C030_G050 C030_G030 C030_G000" in preflight
    assert "STAGE7_STATE_CONFLICT=" in preflight
    assert "STAGE7_STATE_ABSENT=" in preflight
    assert "git/ref/heads/${STATE_BRANCH}" in preflight
    assert "STAGE7_STATE_RESET=" not in preflight
    assert "gh api --method PATCH" not in preflight
    assert "-F force=true" not in preflight
def test_stage7_preflight_preserves_same_run_and_blocks_other_run_state() -> None:
    text = _workflow_text()
    preflight = text[text.index("  preflight-gates:"):text.index("  matrix-simulation:")]
    identity_check = preflight.index('git diff --quiet "${SOURCE_SHA}" HEAD -- "${MODEL_FILES[@]}"')
    state_check = preflight.index('STATE_REF="repos/${GITHUB_REPOSITORY}/git/ref/heads/${STATE_BRANCH}"')
    assert "STATE_CONTENTS=\"repos/${GITHUB_REPOSITORY}/contents/state.json?ref=${STATE_BRANCH}\"" in preflight
    assert "jq -r '.run_id // empty'" in preflight
    assert 'if [ "${state_run_id}" = "${GITHUB_RUN_ID}" ]; then' in preflight
    assert "STAGE7_STATE_RESUME=" in preflight
    assert "STAGE7_STATE_CONFLICT=" in preflight
    assert "STAGE7_STATE_UNVERIFIABLE=" in preflight
    assert "STAGE7_STATE_RESET=" not in preflight
    assert "gh api --method PATCH" not in preflight
    assert identity_check < state_check
    assert "MODEL_SOURCE_DRIFT_DETECTED_IN_PREFLIGHT" in preflight
def test_stage7_restore_artifacts_is_scoped_to_current_workflow_run() -> None:
    text = _workflow_text()
    start = text.index("      - name: Restore previous scenario block artifacts when available")
    end = text.index("      - name: Adaptive scenario orchestration", start)
    restore = text[start:end]
    assert "actions/runs/${GITHUB_RUN_ID}/artifacts?per_page=100" in restore
    assert "actions/artifacts?per_page=100" not in restore
    assert "STAGE7_ARTIFACT_RESTORE=RUN_ID:" in restore
    assert "stage7-blocks-" in restore

def test_stage7_job_started_at_uses_epoch_not_workflow_start() -> None:
    text = _workflow_text()
    assert "JOB_STARTED_AT_EPOCH = time.time()" in text
    assert "return time.time() - JOB_STARTED_AT_EPOCH" in text
    assert 'os.environ["JOB_STARTED_AT"]' not in text
    assert "JOB_STARTED_AT:" not in text
    assert "github.run_started_at" not in text

def _matching_golden_kwargs() -> dict[str, str]:
    fingerprint = "a" * 64
    return {
        "expected_golden_fingerprint_sha256": fingerprint,
        "actual_fingerprint_sha256": fingerprint,
        "golden_reference_id": "test-approved-golden-v1",
        "expected_source_sha": APPROVED_SOURCE_SHA,
        "actual_source_sha": APPROVED_SOURCE_SHA,
    }


def test_gate_a_first_checkpoint_can_pass_only_with_exact_golden() -> None:
    current = _metrics((1000, 700, 300), stable=True)
    gate_a = evaluate_gate_a(
        previous_n=None, previous_metrics=None, current_n=300,
        current_metrics=current, escalation_multiplier=2,
        relative_epsilon=0.01, absolute_epsilon=1,
        **_matching_golden_kwargs(),
    )
    assert gate_a["checked"] is True
    assert gate_a["status"] == "PASS"
    assert gate_a["stable"] is True


def test_gate_a_missing_golden_is_blocked_even_when_metrics_are_close() -> None:
    previous = _metrics((1000, 700, 300), stable=True)
    current = _metrics((1001, 700.5, 300.2), stable=True)
    gate_a = evaluate_gate_a(
        previous_n=300, previous_metrics=previous, current_n=600,
        current_metrics=current, escalation_multiplier=2,
        relative_epsilon=0.01, absolute_epsilon=1,
    )
    gate_b = evaluate_gate_b(current)
    assert gate_a["checked"] is False
    assert gate_a["stable"] is False
    assert gate_a["status"] == "BLOCKED"
    assert gate_b["stable"] is True
    assert not (gate_a["stable"] and gate_b["stable"])


def test_gate_a_exact_fingerprint_pass_gate_b_fail_is_not_stable() -> None:
    previous = _metrics((1000, 700, 300), stable=False)
    current = _metrics((1001, 700.5, 300.2), stable=False)
    gate_a = evaluate_gate_a(
        previous_n=300, previous_metrics=previous, current_n=600,
        current_metrics=current, escalation_multiplier=2,
        relative_epsilon=0.01, absolute_epsilon=1,
        **_matching_golden_kwargs(),
    )
    gate_b = evaluate_gate_b(current)
    assert gate_a["status"] == "PASS"
    assert gate_a["stable"] is True
    assert gate_b["stable"] is False
    assert not (gate_a["stable"] and gate_b["stable"])


def test_gate_a_fingerprint_mismatch_gate_b_pass_is_not_stable() -> None:
    previous = _metrics((1000, 700, 300), stable=True)
    current = _metrics((1105, 770, 330), stable=True)
    wrong_actual = {
        **_matching_golden_kwargs(),
        "actual_fingerprint_sha256": "b" * 64,
    }
    gate_a = evaluate_gate_a(
        previous_n=300, previous_metrics=previous, current_n=600,
        current_metrics=current, escalation_multiplier=2,
        relative_epsilon=0.01, absolute_epsilon=1,
        **wrong_actual,
    )
    gate_b = evaluate_gate_b(current)
    assert gate_a["checked"] is True
    assert gate_a["status"] == "FAIL"
    assert gate_a["stable"] is False
    assert gate_b["stable"] is True
    assert not (gate_a["stable"] and gate_b["stable"])


def test_gate_a_fingerprint_mismatch_gate_b_fail_is_not_stable() -> None:
    previous = _metrics((1000, 700, 300), stable=False)
    current = _metrics((1105, 770, 330), stable=False)
    wrong_actual = {
        **_matching_golden_kwargs(),
        "actual_fingerprint_sha256": "b" * 64,
    }
    gate_a = evaluate_gate_a(
        previous_n=300, previous_metrics=previous, current_n=600,
        current_metrics=current, escalation_multiplier=2,
        relative_epsilon=0.01, absolute_epsilon=1,
        **wrong_actual,
    )
    gate_b = evaluate_gate_b(current)
    assert gate_a["status"] == "FAIL"
    assert gate_a["stable"] is False
    assert gate_b["stable"] is False
    assert not (gate_a["stable"] and gate_b["stable"])


def test_gate_a_exact_golden_and_gate_b_pass_requires_three_consecutive_points() -> None:
    previous = _metrics((1000, 700, 300), stable=True)
    p600 = _metrics((1001, 700.5, 300.2), stable=True)
    p1200 = _metrics((1002, 701.0, 300.4), stable=True)
    p2400 = _metrics((1003, 701.5, 300.6), stable=True)
    pairs = (
        (300, previous, 600, p600),
        (600, p600, 1200, p1200),
        (1200, p1200, 2400, p2400),
    )
    checks = []
    for previous_n, previous_metrics, current_n, current_metrics in pairs:
        gate_a = evaluate_gate_a(
            previous_n=previous_n, previous_metrics=previous_metrics,
            current_n=current_n, current_metrics=current_metrics,
            escalation_multiplier=2, relative_epsilon=0.01,
            absolute_epsilon=1, **_matching_golden_kwargs(),
        )
        gate_b = evaluate_gate_b(current_metrics)
        checks.append(gate_a["stable"] and gate_b["stable"])
    assert checks == [True, True, True]



def _checkpoint_history(ns: list[int]) -> list[dict]:
    history = []
    previous_n = None
    for n in ns:
        history.append({
            "n": n,
            "gate_a": {
                "previous_n": previous_n,
                "current_n": n,
                "status": "PASS",
                "checked": True,
                "stable": True,
            },
            "gate_b": {"checked": True, "stable": True},
        })
        previous_n = n
    return history


def test_stability_requires_four_cumulative_points_for_three_adjacent_transitions() -> None:
    history = _checkpoint_history([300, 600, 1200, 2400])
    assert has_successful_adjacent_transition_window(
        history, required_transitions=3, required_points=4
    )


def test_stability_does_not_stop_after_only_three_points() -> None:
    history = _checkpoint_history([300, 600, 1200])
    assert not has_successful_adjacent_transition_window(
        history, required_transitions=3, required_points=4
    )


def test_stability_rejects_non_doubling_or_misbound_transition() -> None:
    history = _checkpoint_history([300, 600, 1000, 2400])
    assert not has_successful_adjacent_transition_window(
        history, required_transitions=3, required_points=4
    )
    history = _checkpoint_history([300, 600, 1200, 2400])
    history[-1]["gate_a"]["previous_n"] = 600
    assert not has_successful_adjacent_transition_window(
        history, required_transitions=3, required_points=4
    )


def test_stability_rejects_a_failed_gate_in_any_checkpoint() -> None:
    history = _checkpoint_history([300, 600, 1200, 2400])
    history[1]["gate_b"]["stable"] = False
    assert not has_successful_adjacent_transition_window(
        history, required_transitions=3, required_points=4
    )


def test_gate_a_rejects_source_identity_mismatch() -> None:
    previous = _metrics((1000, 700, 300), stable=True)
    current = _metrics((1001, 700.5, 300.2), stable=True)
    fields = {
        **_matching_golden_kwargs(),
        "actual_source_sha": "e" * 40,
    }
    gate_a = evaluate_gate_a(
        previous_n=300, previous_metrics=previous, current_n=600,
        current_metrics=current, escalation_multiplier=2,
        relative_epsilon=0.01, absolute_epsilon=1, **fields,
    )
    assert gate_a["checked"] is True
    assert gate_a["stable"] is False
    assert gate_a["status"] == "FAIL"
    assert gate_a["reason"] == "golden and actual source identities differ"


def test_gate_a_rejects_malformed_fingerprint() -> None:
    previous = _metrics((1000, 700, 300), stable=True)
    current = _metrics((1001, 700.5, 300.2), stable=True)
    fields = {
        **_matching_golden_kwargs(),
        "actual_fingerprint_sha256": "not-a-sha256",
    }
    gate_a = evaluate_gate_a(
        previous_n=300, previous_metrics=previous, current_n=600,
        current_metrics=current, escalation_multiplier=2,
        relative_epsilon=0.01, absolute_epsilon=1, **fields,
    )
    assert gate_a["checked"] is True
    assert gate_a["stable"] is False
    assert gate_a["status"] == "FAIL"


def test_stage7_fails_closed_on_unverified_resume_and_stable_state() -> None:
    text = _workflow_text()
    assert 'if not SCENARIO.startswith("C100_") and completed >= INITIAL_NON_C100:' in text
    assert 'latest_status = latest_gate_a.get("status")' in text
    assert 'state.get("final_status") == "stable"' in text
    assert 'item.get("gate_a", {}).get("status") == "PASS"' in text
    assert 'GATE_A_PREFLIGHT_BLOCKED=' in text


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

def test_c100_verification_excludes_trial_id_from_comparison() -> None:
    text = _workflow_text()
    assert 'primary_dict = asdict(primary)' in text
    assert 'verification_dict = asdict(verification)' in text
    assert 'primary_trial_id = primary_dict.pop("trial_id")' in text
    assert 'verification_trial_id = verification_dict.pop("trial_id")' in text
    assert 'if primary_trial_id == verification_trial_id:' in text
    assert 'raise AssertionError(' in text
    assert "C100 independence requires distinct trial_id" in text
    assert 'equality = primary_dict == verification_dict' in text
    assert 'equality = asdict(primary) == asdict(verification)' not in text


def test_c100_stability_is_after_independent_equality_proof() -> None:
    text = _workflow_text()
    equality_pos = text.index("equality = primary_dict == verification_dict")
    stable_pos = text.index('state["final_status"] = "stable"')
    assert equality_pos < stable_pos

def test_gate_a_requires_exact_doubling_checkpoint() -> None:
    previous = _metrics((1000, 700, 300), stable=True)
    current = _metrics((1001, 700.5, 300.2), stable=True)
    gate_a = evaluate_gate_a(
        previous_n=300, previous_metrics=previous, current_n=601,
        current_metrics=current, escalation_multiplier=2,
        relative_epsilon=0.01, absolute_epsilon=1,
        **_matching_golden_kwargs(),
    )
    assert gate_a["checked"] is False
    assert gate_a["status"] == "BLOCKED"


def test_gate_a_does_not_substitute_metric_deltas_for_golden_equality() -> None:
    previous = _metrics((1000, 700, 300), stable=True)
    current = _metrics((1001, 900, 300.2), stable=True)
    gate_a = evaluate_gate_a(
        previous_n=300, previous_metrics=previous, current_n=600,
        current_metrics=current, escalation_multiplier=2,
        relative_epsilon=0.01, absolute_epsilon=1,
        **_matching_golden_kwargs(),
    )
    assert gate_a["status"] == "PASS"
    assert gate_a["stable"] is True


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

def test_stage7_state_module_has_distinct_remote_404_exception() -> None:
    assert issubclass(StateRemoteNotFound, RuntimeError)
    assert "404" in Path(
        REPO_ROOT / "scripts" / "stage7_state.py"
    ).read_text(encoding="utf-8")


def test_stage7_state_module_has_retry_backoff_contract() -> None:
    text = Path(
        REPO_ROOT / "scripts" / "stage7_state.py"
    ).read_text(encoding="utf-8")
    assert "MAX_ATTEMPTS = 4" in text
    assert "RETRYABLE_HTTP_STATUS" in text
    assert "time.sleep" in text
    assert "2**attempt" in text


def test_stage7_state_module_has_concurrency_lease_contract() -> None:
    text = Path(
        REPO_ROOT / "scripts" / "stage7_state.py"
    ).read_text(encoding="utf-8")
    assert "LeaseConflict" in text
    assert "lease_owner" in text
    assert "expires_at" in text
    assert "StateConflict" in text


def test_stage7_state_module_persists_initial_state_remotely() -> None:
    text = Path(
        REPO_ROOT / "scripts" / "stage7_state.py"
    ).read_text(encoding="utf-8")
    assert "self._put_state(state, None)" in text
    assert '"completed_trials": 0' in text
    assert '"next_trial_id": 1' in text


def test_stage7_state_module_has_local_remote_sync_verification() -> None:
    text = Path(
        REPO_ROOT / "scripts" / "stage7_state.py"
    ).read_text(encoding="utf-8")
    assert "_verify_remote_equals" in text
    assert "_write_local" in text


def test_stage7_workflow_uses_transactional_state_store() -> None:
    text = _workflow_text()
    assert "StateStore(" in text
    assert "state, blob_sha = store.acquire()" in text
    assert "store.save_state(state, blob_sha)" in text
    assert "atexit.register(store.release)" in text


def test_stage7_workflow_does_not_keep_the_old_nonpersistent_initializer() -> None:
    text = _workflow_text()
    assert "Initialize or restore scenario state" not in text
    assert "StateStore(" in text


def test_stage7_pause_resume_uses_persisted_next_trial_id() -> None:
    text = _workflow_text()
    assert 'run_attempt=os.environ["RUN_ATTEMPT"]' in text
    assert "next_trial_id = int(" in text
    assert "validate_trial_sequence(" in text


def test_stage7_artifact_identity_contains_exact_required_identity_fields() -> None:
    identity = build_artifact_identity(
        scenario="C070_G100",
        source_sha=APPROVED_SOURCE_SHA,
        trial_id_start=1,
        trial_id_end=300,
        fingerprint_sha256="abc123",
        master_seed=20270101,
        rng_checksum_fingerprint_sha256="c" * 64,
    )
    assert identity == {
        "scenario": "C070_G100",
        "source_sha": APPROVED_SOURCE_SHA,
        "master_seed": 20270101,
        "rng_audit_schema": "rng-checksum-high53-mod2^64-v1",
        "trial_id_start": 1,
        "trial_id_end": 300,
        "fingerprint_sha256": "abc123",
        "rng_checksum_fingerprint_sha256": "c" * 64,
    }


def test_stage7_trial_sequence_rejects_gap_and_duplicate() -> None:
    with pytest.raises(StateIntegrityError):
        validate_trial_sequence(
            trial_ids=[1, 2, 4],
            completed_trials=3,
            next_trial_id=4,
        )
    with pytest.raises(StateIntegrityError):
        validate_trial_sequence(
            trial_ids=[1, 2, 2],
            completed_trials=3,
            next_trial_id=4,
        )


def test_stage7_trial_sequence_accepts_exact_resume_boundary() -> None:
    validate_trial_sequence(
        trial_ids=list(range(1, 6)),
        completed_trials=5,
        next_trial_id=6,
    )


def test_stage7_workflow_binds_artifact_identity_to_state_and_final_artifact() -> None:
    text = _workflow_text()
    assert 'state["artifact_identity"] = build_artifact_identity(' in text
    assert '"artifact_identity": state["artifact_identity"]' in text


def test_stage7_cp3_pending_is_not_encoded_as_false() -> None:
    text = _workflow_text()
    report = text[text.index("  final-report:"):]
    assert "cp3_match = None" in report
    assert "cp3_match = False" not in report

def test_cp3_cross_reference_compares_only_overlapping_range() -> None:
    text = _workflow_text()
    start = text.index('if SCENARIO == CP3_SCENARIO:')
    end = text.index('write_json(', start)
    cross_reference = text[start:end]

    assert "cp3_overlap = min(" in cross_reference
    assert "len(results)" in cross_reference
    assert "len(cp3_results)" in cross_reference
    assert "1 <= result.trial_id <= cp3_overlap" in cross_reference
    assert "fingerprint_trial_results(stage7_prefix)" in cross_reference
    assert "fingerprint_trial_results(cp3_prefix)" in cross_reference
    assert "trial_id <= 6000" not in cross_reference
    assert "CP3_AGGREGATE_SHA256" not in cross_reference


def test_same_run_id_different_attempt_is_allowed_by_lease() -> None:
    store = StateStore(
        repo="example/repo",
        token="token",
        scenario="C070_G100",
        source_sha=APPROVED_SOURCE_SHA,
        run_id="100",
        run_attempt="2",
        local_path=REPO_ROOT / "state.json",
    )
    now = datetime.now(timezone.utc)
    lease = {
        "owner": "100",
        "run_id": "100",
        "run_attempt": 1,
        "acquired_at": (
            now - timedelta(minutes=1)
        ).isoformat().replace("+00:00", "Z"),
        "expires_at": (
            now + timedelta(minutes=10)
        ).isoformat().replace("+00:00", "Z"),
    }
    assert store._lease_is_active_for_other_owner(lease) is False


def test_different_run_id_is_rejected_while_lease_is_active() -> None:
    store = StateStore(
        repo="example/repo",
        token="token",
        scenario="C070_G100",
        source_sha=APPROVED_SOURCE_SHA,
        run_id="200",
        run_attempt="1",
        local_path=REPO_ROOT / "state.json",
    )
    now = datetime.now(timezone.utc)
    lease = {
        "owner": "100",
        "run_id": "100",
        "run_attempt": 1,
        "acquired_at": (
            now - timedelta(minutes=1)
        ).isoformat().replace("+00:00", "Z"),
        "expires_at": (
            now + timedelta(minutes=10)
        ).isoformat().replace("+00:00", "Z"),
    }
    assert store._lease_is_active_for_other_owner(lease) is True


def test_expired_lease_is_available_to_a_new_run_id() -> None:
    store = StateStore(
        repo="example/repo",
        token="token",
        scenario="C070_G100",
        source_sha=APPROVED_SOURCE_SHA,
        run_id="200",
        run_attempt="1",
        local_path=REPO_ROOT / "state.json",
    )
    now = datetime.now(timezone.utc)
    lease = {
        "owner": "100",
        "run_id": "100",
        "run_attempt": 1,
        "acquired_at": (
            now - timedelta(minutes=20)
        ).isoformat().replace("+00:00", "Z"),
        "expires_at": (
            now - timedelta(minutes=10)
        ).isoformat().replace("+00:00", "Z"),
    }
    assert store._lease_is_active_for_other_owner(lease) is False


def test_stage7_state_module_documents_same_run_id_re_run_policy() -> None:
    text = Path(
        REPO_ROOT / "scripts" / "stage7_state.py"
    ).read_text(encoding="utf-8")
    assert "Same run_id across GitHub re-runs is one logical lease owner." in text
    assert "run_attempt is retained in the record for auditability only." in text

def test_stage7_operational_timeout_is_45_minutes() -> None:
    text = _workflow_text()
    assert 'JOB_TIMEOUT_MINUTES: "40"' in text
    matrix = _workflow()["jobs"]["matrix-simulation"]
    assert matrix["timeout-minutes"] == 45


def test_stage7_workflow_no_longer_exports_unused_log_events_setting() -> None:
    text = _workflow_text()
    assert 'LOG_EVENTS:' not in text
    assert 'os.environ["LOG_EVENTS"]' not in text


def test_stage7_timeout_state_is_excluded_from_final_statistics() -> None:
    text = _workflow_text()
    assert 'state["included_in_final_stats"] = False' in text
    assert '"final_stats_included": False' in text


def test_stage7_final_report_distinguishes_404_from_other_state_errors() -> None:
    text = _workflow_text()
    assert "STATE_NOT_FOUND_404" in text
    assert "STATE_REMOTE_HTTP_ERROR_" in text
    assert "STATE_REMOTE_TRANSPORT_ERROR" in text


def test_stage7_final_report_excludes_timeout_partial_counts() -> None:
    text = _workflow_text()
    assert 'is_timeout = state.get("final_status") == "timeout"' in text
    assert '"final_trial_count": None if is_timeout else' in text
    assert '"final_fingerprint": None if is_timeout else' in text


def test_stage7_final_report_uses_actual_uploaded_state_path() -> None:
    text = _workflow_text()
    assert '**/stage7-final-{scenario}-*/state.json' in text


def test_stage7_final_report_reports_state_path_and_error_count() -> None:
    text = _workflow_text()
    assert '"state_path": f"stage7-state/{scenario}/state.json"' in text
    assert '"error_count": error_count' in text


def test_stage7_state_initial_stats_inclusion_is_false() -> None:
    text = Path(
        REPO_ROOT / "scripts" / "stage7_state.py"
    ).read_text(encoding="utf-8")
    assert '"included_in_final_stats": False' in text


def test_stage7_authoring_verify_parses_all_stage7_helpers() -> None:
    text = AUTHORING_VERIFY.read_text(encoding="utf-8")
    assert "scripts/stage7_run_trial_block.py" in text
    assert "scripts/stage7_state.py" in text
    assert "scripts/stage7_stability.py" in text


def test_stage7_state_store_rejects_stage_6_5_schema() -> None:
    store = StateStore(
        repo="example/repo",
        token="token",
        scenario="C070_G100",
        source_sha=APPROVED_SOURCE_SHA,
        run_id="100",
        run_attempt="1",
        local_path=REPO_ROOT / "state.json",
    )
    state = {
        "stage": "6.5",
        "cp_completed": "CP5",
        "sha": "15b5c6e2c54ade5c1ddce07aecdc53d86a60ad95",
        "next": "stage7",
        "blockers": [],
    }
    with pytest.raises(StateIntegrityError):
        store._validate_identity(state)


def test_stage7_state_store_accepts_only_stage_7_schema() -> None:
    store = StateStore(
        repo="example/repo",
        token="token",
        scenario="C070_G100",
        source_sha=APPROVED_SOURCE_SHA,
        run_id="100",
        run_attempt="1",
        local_path=REPO_ROOT / "state.json",
    )
    state = {
        "stage": "7",
        "scenario": "C070_G100",
        "source_sha": APPROVED_SOURCE_SHA,
        "completed_trials": 0,
        "next_trial_id": 1,
        "stability_history": [],
    }
    store._validate_identity(state)


def test_stage7_new_branch_does_not_inherit_root_state() -> None:
    root_state = {
        "stage": "6.5",
        "cp_completed": "CP5",
        "sha": "15b5c6e2c54ade5c1ddce07aecdc53d86a60ad95",
        "next": "stage7",
        "blockers": [],
    }

    class FakeSourceBackedStateStore(StateStore):
        def __init__(self) -> None:
            super().__init__(
                repo="example/repo",
                token="token",
                scenario="C070_G100",
                source_sha=APPROVED_SOURCE_SHA,
                run_id="100",
                run_attempt="1",
                local_path=REPO_ROOT / "state.json",
            )
            self.branch_sha = APPROVED_SOURCE_SHA
            self.state = dict(root_state)
            self.state_blob_sha = "root-state-blob"
            self.put_payloads = []

        def _request(self, method, path, payload=None):
            if method == "GET" and path == self._branch_ref_path():
                return {"object": {"sha": self.branch_sha}}
            if method == "GET" and path == self._state_contents_path():
                raw = json.dumps(self.state).encode("utf-8")
                return {
                    "sha": self.state_blob_sha,
                    "content": base64.b64encode(raw).decode("ascii"),
                }
            if method == "PUT" and path == "contents/state.json":
                self.put_payloads.append(dict(payload))
                raw = base64.b64decode(payload["content"]).decode("utf-8")
                self.state = json.loads(raw)
                self.state_blob_sha = "stage7-state-blob"
                self.branch_sha = "stage7-checkpoint-commit"
                return {"content": {"sha": self.state_blob_sha}}
            raise AssertionError(f"unexpected request: {method} {path}")

    store = FakeSourceBackedStateStore()
    state, _ = store.acquire()

    assert store.branch_sha != APPROVED_SOURCE_SHA
    assert store.put_payloads[0]["sha"] == "root-state-blob"
    assert state["stage"] == "7"
    assert state["scenario"] == "C070_G100"
    assert state["source_sha"] == APPROVED_SOURCE_SHA
    assert state["completed_trials"] == 0
    assert state["next_trial_id"] == 1
    assert state["stability_history"] == []
    assert store.state["stage"] == "7"

def test_stage7_statistical_policy_is_the_approved_doubling_policy() -> None:
    from scripts.stage7_stability import is_statistical_checkpoint, next_statistical_checkpoint
    import constants

    assert constants.STATISTICAL_ESCALATION_MULTIPLIER == 2
    assert _workflow()["env"]["ESCALATION_MULTIPLIER"] == str(constants.STATISTICAL_ESCALATION_MULTIPLIER)
    assert _workflow()["env"]["INITIAL_NON_C100_TRIALS"] == "300"
    assert [next_statistical_checkpoint(n) for n in (0, 300, 350, 600, 1200)] == [
        300, 600, 600, 1200, 2400
    ]
    assert all(is_statistical_checkpoint(n) for n in (300, 600, 1200, 2400))
    assert not any(is_statistical_checkpoint(n) for n in (350, 400, 450, 500, 550))



def test_stage7_gate_b_requires_actual_boolean_stability_evidence() -> None:
    valid = _metrics((1000.0, 700.0, 300.0), stable=True)
    result = evaluate_gate_b(valid)
    assert result["checked"] is True
    assert result["stable"] is True

    explicit_false = _metrics((1000.0, 700.0, 300.0), stable=False)
    assert evaluate_gate_b(explicit_false)["stable"] is False

    invalid_values = ("False", "true", 0, 1, None, [], {}, float("nan"))
    for field_name in ("final_net_project_equity", "partner1_final_entitlement", "partner2_final_entitlement"):
        for invalid in invalid_values:
            malformed = _metrics((1000.0, 700.0, 300.0), stable=True)
            malformed[field_name]["stable"] = invalid
            with pytest.raises(ValueError, match="must be a Boolean"):
                evaluate_gate_b(malformed)

    missing_stability = _metrics((1000.0, 700.0, 300.0), stable=True)
    missing_stability["final_net_project_equity"].pop("stable")
    with pytest.raises(ValueError, match="must be a Boolean"):
        evaluate_gate_b(missing_stability)

    missing_metric = _metrics((1000.0, 700.0, 300.0), stable=True)
    missing_metric.pop("partner2_final_entitlement")
    with pytest.raises(ValueError, match="must be a mapping"):
        evaluate_gate_b(missing_metric)

    for malformed_top_level in (None, [], "not-a-mapping"):
        with pytest.raises(ValueError, match="current metrics must be a mapping"):
            evaluate_gate_b(malformed_top_level)  # type: ignore[arg-type]
