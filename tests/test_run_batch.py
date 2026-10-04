from __future__ import annotations

from pathlib import Path

import pytest

import run_batch
from scripts.stage7_state import StateIntegrityError


REPO_ROOT = Path(__file__).resolve().parents[1]
APPROVED_SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"


def _base_checkpoint() -> dict:
    return {
        "stage": "7",
        "scenario": "C070_G100",
        "source_sha": APPROVED_SOURCE_SHA,
        "completed_trials": 450,
        "next_trial_id": 451,
        "final_fingerprint": "abc123",
        "artifact_identity": {
            "scenario": "C070_G100",
            "source_sha": APPROVED_SOURCE_SHA,
            "trial_id_start": 1,
            "trial_id_end": 450,
            "fingerprint_sha256": "abc123",
        },
        "stability_history": [],
        "next_check_n": 500,
    }


def test_run_batch_starts_from_trial_1_by_default() -> None:
    args = run_batch.parse_args(
        [
            "--scenario",
            "C070_G100",
            "--trials",
            "300",
            "--output-dir",
            "/tmp/stage8-test",
        ]
    )

    assert args.start_trial_id == 1
    assert args.resume_from_checkpoint is False

    assert (
        run_batch.resolve_start_trial_id(
            requested_start_trial_id=args.start_trial_id,
            resume_from_checkpoint=args.resume_from_checkpoint,
            checkpoint=None,
        )
        == 1
    )


def test_run_batch_resume_from_checkpoint_uses_next_trial_id() -> None:
    checkpoint = _base_checkpoint()

    resolved = run_batch.resolve_start_trial_id(
        requested_start_trial_id=1,
        resume_from_checkpoint=True,
        checkpoint=checkpoint,
    )

    assert resolved == 451


def test_run_batch_rejects_checkpoint_with_different_source_sha() -> None:
    checkpoint = _base_checkpoint()
    checkpoint["source_sha"] = "different-source-sha"

    with pytest.raises(StateIntegrityError, match="source SHA mismatch"):
        run_batch._checkpoint_identity_is_valid(
            checkpoint,
            scenario="C070_G100",
            source_sha=APPROVED_SOURCE_SHA,
        )


def test_run_batch_rejects_checkpoint_with_different_artifact_identity() -> None:
    checkpoint = _base_checkpoint()
    checkpoint["artifact_identity"]["fingerprint_sha256"] = "different"

    with pytest.raises(
        StateIntegrityError,
        match="final_fingerprint differs from artifact_identity",
    ):
        run_batch._checkpoint_identity_is_valid(
            checkpoint,
            scenario="C070_G100",
            source_sha=APPROVED_SOURCE_SHA,
        )


def test_run_batch_uses_user_approved_policy_not_reference_defaults() -> None:
    source = (
        REPO_ROOT / "run_batch.py"
    ).read_text(encoding="utf-8")

    required_constants = (
        "constants.C100_STATISTICAL_START_TRIALS",
        "constants.NON_C100_STATISTICAL_START_TRIALS",
        "constants.ITERATION_ESCALATION_STEP",
        "constants.STATISTICAL_CHECK_START_N",
        "constants.STATISTICAL_CHECK_STEP_N",
        "constants.STABILITY_CONSECUTIVE_CHECKS_REQUIRED",
        "constants.CI_CONFIDENCE_LEVEL",
        "constants.CI_RELATIVE_TOLERANCE",
        "constants.CI_ABSOLUTE_EPSILON",
    )

    for name in required_constants:
        assert name in source

    for legacy_value in ("5000", "8000", "15000", "20000"):
        assert legacy_value not in source


def test_run_batch_resume_after_stable_rechecks_stability() -> None:
    """Resume after stable must re-evaluate stability for new range."""
    checkpoint = _base_checkpoint()
    checkpoint["stability_history"] = [
        {
            "n": 450,
            "metrics": {
                "final_net_project_equity": {"mean": 1000.0, "stable": True},
                "partner1_final_entitlement": {"mean": 700.0, "stable": True},
                "partner2_final_entitlement": {"mean": 300.0, "stable": True},
            },
            "gate_a": {"stable": True},
            "gate_b": {"stable": True},
        }
    ]
    checkpoint["next_check_n"] = 500

    previous_metrics = checkpoint["stability_history"][-1]["metrics"]
    previous_n = 450
    current_metrics = {
        "final_net_project_equity": {"mean": 1001.0, "stable": True},
        "partner1_final_entitlement": {"mean": 700.5, "stable": True},
        "partner2_final_entitlement": {"mean": 300.2, "stable": True},
    }

    gate_a = run_batch.evaluate_gate_a(
        previous_metrics=previous_metrics,
        previous_n=previous_n,
        current_metrics=current_metrics,
        current_n=500,
    )

    assert gate_a["checked"] is True
    assert gate_a["stable"] is True
    assert gate_a["previous_n"] == 450
    assert gate_a["current_n"] == 500

def test_stage8_source_sha_is_literal_in_workflow() -> None:
    text = (REPO_ROOT / ".github" / "workflows" /
            "stage8-authoring-verify.yml").read_text(encoding="utf-8")
    assert (
        'SOURCE_SHA="f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"'
        in text
    )
    assert "${{ env.SOURCE_SHA }}" not in text
