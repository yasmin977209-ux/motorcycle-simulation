from __future__ import annotations

from pathlib import Path

import pytest

import constants
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
        "initial_trials = constants.STATISTICAL_CHECK_START_N",
        "STATISTICAL_ESCALATION_POLICY_ID",
        "STATISTICAL_ESCALATION_MULTIPLIER",
        "constants.STATISTICAL_CHECK_START_N",
        "constants.STABILITY_STOP_ON_FIRST_PASS",
        "summarize_reference_stability_metrics",
        "evaluate_reference_stability_transition",
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
            "n": 300,
            "metrics": {
                "final_net_project_equity": {"mean": 1000.0, "stable": True},
                "partner1_final_entitlement": {"mean": 700.0, "stable": True},
                "partner2_final_entitlement": {"mean": 300.0, "stable": True},
            },
            "gate_a": {"stable": True},
            "gate_b": {"stable": True},
        }
    ]
    checkpoint["next_check_n"] = 600

    previous_metrics = checkpoint["stability_history"][-1]["metrics"]
    previous_n = 300
    current_metrics = {
        "final_net_project_equity": {"mean": 1001.0, "stable": True},
        "partner1_final_entitlement": {"mean": 700.5, "stable": True},
        "partner2_final_entitlement": {"mean": 300.2, "stable": True},
    }

    gate_a = run_batch.evaluate_gate_a(
        previous_metrics=previous_metrics,
        previous_n=previous_n,
        current_metrics=current_metrics,
        current_n=600,
    )

    # Metric deltas alone are not Gate A evidence.
    assert gate_a["checked"] is False
    assert gate_a["stable"] is False
    assert gate_a["status"] == "BLOCKED"
    assert gate_a["previous_n"] == 300
    assert gate_a["current_n"] == 600


def test_run_batch_gate_a_requires_exact_golden_fingerprint() -> None:
    previous_metrics = {
        "final_net_project_equity": {"mean": 1000.0},
        "partner1_final_entitlement": {"mean": 700.0},
        "partner2_final_entitlement": {"mean": 300.0},
    }
    current_metrics = {
        "final_net_project_equity": {"mean": 9000.0},
        "partner1_final_entitlement": {"mean": 7000.0},
        "partner2_final_entitlement": {"mean": 3000.0},
    }
    golden_sha = "a" * 64
    gate_a = run_batch.evaluate_gate_a(
        previous_metrics=previous_metrics,
        previous_n=300,
        current_metrics=current_metrics,
        current_n=600,
        expected_golden_fingerprint_sha256=golden_sha,
        actual_fingerprint_sha256=golden_sha,
        golden_reference_id="test-golden-v1",
        expected_source_sha="f" * 40,
        actual_source_sha="f" * 40,
    )
    assert gate_a["checked"] is True
    assert gate_a["stable"] is True
    assert gate_a["status"] == "PASS"

def test_stage8_source_sha_is_literal_in_workflow() -> None:
    text = (REPO_ROOT / ".github" / "workflows" /
            "stage8-authoring-verify.yml").read_text(encoding="utf-8")
    assert (
        'SOURCE_SHA="f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"'
        in text
    )
    assert "${{ env.SOURCE_SHA }}" not in text

def test_run_batch_c100_uses_approved_checkpoint_schedule() -> None:
    """C100 now shares the same doubling schedule as every other scenario."""
    checkpoint = {
        "stage": "7",
        "scenario": "C100_G100",
        "source_sha": APPROVED_SOURCE_SHA,
        "completed_trials": 300,
        "next_trial_id": 301,
        "next_check_n": 600,
        "final_fingerprint": "abc",
        "artifact_identity": {
            "scenario": "C100_G100",
            "source_sha": APPROVED_SOURCE_SHA,
            "trial_id_start": 1,
            "trial_id_end": 300,
            "fingerprint_sha256": "abc",
        },
    }
    run_batch._checkpoint_identity_is_valid(
        checkpoint,
        scenario="C100_G100",
        source_sha=APPROVED_SOURCE_SHA,
    )
    invalid = {**checkpoint, "next_check_n": 300}
    with pytest.raises(StateIntegrityError, match="next_check_n"):
        run_batch._checkpoint_identity_is_valid(
            invalid,
            scenario="C100_G100",
            source_sha=APPROVED_SOURCE_SHA,
        )


def test_run_batch_accepts_the_mandatory_300_trial_c100_cohort() -> None:
    args = run_batch.parse_args([
        "--scenario", "C100_G100", "--trials", "300",
        "--output-dir", "/tmp/stage8-c100-policy-test",
    ])
    assert args.trials == 300
    source = (REPO_ROOT / "run_batch.py").read_text(encoding="utf-8")
    assert "initial_target = constants.STATISTICAL_CHECK_START_N" in source
    assert "constants.C100_STATISTICAL_START_TRIALS" not in source


def test_statistical_escalation_uses_only_approved_doubling_points() -> None:
    from scripts.stage7_stability import (
        filter_statistical_history,
        is_statistical_checkpoint,
        next_statistical_checkpoint,
    )

    assert [next_statistical_checkpoint(n) for n in (0, 300, 350, 599, 600, 1200)] == [
        300, 600, 600, 600, 1200, 2400
    ]
    assert all(is_statistical_checkpoint(n) for n in (300, 600, 1200, 2400))
    assert not any(is_statistical_checkpoint(n) for n in (350, 400, 450, 500, 550))

    original = [{"n": n} for n in (300, 350, 400, 450, 500, 550)]
    accepted, discarded = filter_statistical_history(original)
    assert [item["n"] for item in accepted] == [300]
    assert discarded == [350, 400, 450, 500, 550]
    assert [item["n"] for item in original] == [300, 350, 400, 450, 500, 550]


def test_statistical_history_migration_fails_closed_on_malformed_or_duplicate_entries() -> None:
    import pytest
    from scripts.stage7_stability import filter_statistical_history

    with pytest.raises(ValueError, match="missing or invalid N"):
        filter_statistical_history([{"metrics": {}}])
    with pytest.raises(ValueError, match="duplicate stability-history N"):
        filter_statistical_history([{"n": 350}, {"n": 350}])
    with pytest.raises(ValueError, match="not ordered"):
        filter_statistical_history([{"n": 400}, {"n": 350}])
