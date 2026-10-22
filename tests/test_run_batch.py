from __future__ import annotations

import json
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


@pytest.mark.parametrize("terminal_status", ["blocked", "failed", "stable"])
def test_run_batch_refuses_resume_after_terminal_local_state(
    terminal_status: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    (tmp_path / run_batch.STATE_JSON).write_text(
        json.dumps(
            {
                "final_status": terminal_status,
                "reason_if_not_stable": "Gate A did not PASS",
            }
        ),
        encoding="utf-8",
    )

    def unexpected_checkpoint_load(**_kwargs):
        pytest.fail("checkpoint loading must not bypass the terminal local state")

    monkeypatch.setattr(run_batch, "load_stage7_checkpoint", unexpected_checkpoint_load)
    with pytest.raises(StateIntegrityError, match="operator review is required"):
        run_batch.run_batch(
            scenario="C070_G100",
            trials=300,
            output_dir=tmp_path,
            resume_from_checkpoint=True,
            source_sha=APPROVED_SOURCE_SHA,
        )


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"final_status": None},
        {"final_status": 17},
        {"final_status": "unknown"},
    ],
)
def test_run_batch_refuses_resume_after_invalid_local_state(
    payload: object,
    tmp_path: Path,
) -> None:
    (tmp_path / run_batch.STATE_JSON).write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    with pytest.raises(StateIntegrityError):
        run_batch._refuse_terminal_local_state_on_resume(
            tmp_path,
            resume_from_checkpoint=True,
        )


def test_run_batch_refuses_resume_when_local_state_is_missing(
    tmp_path: Path,
) -> None:
    with pytest.raises(StateIntegrityError, match="state is missing"):
        run_batch._refuse_terminal_local_state_on_resume(
            tmp_path,
            resume_from_checkpoint=True,
        )


def test_run_batch_refuses_resume_when_local_state_is_unreadable(
    tmp_path: Path,
) -> None:
    (tmp_path / run_batch.STATE_JSON).write_text("{not-json", encoding="utf-8")

    with pytest.raises(StateIntegrityError, match="unreadable"):
        run_batch._refuse_terminal_local_state_on_resume(
            tmp_path,
            resume_from_checkpoint=True,
        )


@pytest.mark.parametrize(
    "gate_a",
    [
        {"status": "PASS", "checked": False, "stable": True},
        {"status": "PASS", "checked": True, "stable": False},
        {"status": "PASS", "checked": 1, "stable": True},
        {"status": "PASS", "stable": True},
        {"status": "FAIL", "checked": True, "stable": False},
        None,
        [],
    ],
)
def test_prior_gate_a_requires_explicit_checked_stable_pass(gate_a: object) -> None:
    assert run_batch._has_explicit_gate_a_pass(gate_a) is False


def test_prior_gate_a_accepts_only_explicit_checked_stable_pass() -> None:
    assert run_batch._has_explicit_gate_a_pass(
        {"status": "PASS", "checked": True, "stable": True}
    ) is True


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
        "STATISTICAL_ESCALATION_POLICY_ID",
        "STATISTICAL_ESCALATION_MULTIPLIER",
        "constants.STATISTICAL_CHECK_START_N",
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

def test_run_batch_c100_checkpoint_skips_escalation_check() -> None:
    """C100 does not have an escalation step; next_check_n
    validation must be skipped."""
    checkpoint = {
        "stage": "7",
        "scenario": "C100_G100",
        "source_sha": "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b",
        "completed_trials": 1,
        "next_trial_id": 2,
        "next_check_n": 1,
        "final_fingerprint": "abc",
        "artifact_identity": {
            "scenario": "C100_G100",
            "source_sha": "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b",
            "trial_id_start": 1,
            "trial_id_end": 1,
            "fingerprint_sha256": "abc",
        },
    }
    # Must not raise
    run_batch._checkpoint_identity_is_valid(
        checkpoint,
        scenario="C100_G100",
        source_sha="f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b",
    )


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

    with pytest.raises(ValueError, match="N must be an integer"):
        filter_statistical_history([{"metrics": {}}])
    with pytest.raises(ValueError, match="duplicate stability-history N"):
        filter_statistical_history([{"n": 350}, {"n": 350}])
    with pytest.raises(ValueError, match="not ordered"):
        filter_statistical_history([{"n": 400}, {"n": 350}])



def test_statistical_history_rejects_non_integer_checkpoint_n() -> None:
    from scripts.stage7_stability import filter_statistical_history

    for invalid_n in (300.9, 300.0, "300", True, None):
        with pytest.raises(ValueError, match="N must be an integer"):
            filter_statistical_history([{"n": invalid_n}])

    with pytest.raises(ValueError, match="N must be an integer"):
        filter_statistical_history([{"metrics": {}}])


def test_gate_b_requires_actual_boolean_stability_evidence() -> None:
    valid = {
        field_name: {"mean": 10.0, "stable": True}
        for field_name in run_batch.STABILITY_FIELDS
    }
    assert run_batch.evaluate_gate_b(valid)["stable"] is True

    false_metrics = {
        field_name: {"mean": 10.0, "stable": False}
        for field_name in run_batch.STABILITY_FIELDS
    }
    assert run_batch.evaluate_gate_b(false_metrics)["stable"] is False

    for invalid_value in ("False", "True", 0, 1, 1.0, None, [], {}):
        for field_name in run_batch.STABILITY_FIELDS:
            malformed = {
                name: dict(metric)
                for name, metric in valid.items()
            }
            malformed[field_name]["stable"] = invalid_value
            with pytest.raises(ValueError, match="must be a Boolean"):
                run_batch.evaluate_gate_b(malformed)


def test_run_batch_stops_after_gate_a_is_blocked(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from types import SimpleNamespace

    trial_blocks: list[list[int]] = []

    def fake_run_trials(scenario, trial_ids, *, master_seed):
        ids = list(trial_ids)
        trial_blocks.append(ids)
        return [SimpleNamespace(trial_id=trial_id) for trial_id in ids], None

    metrics = {
        field_name: {"mean": 1.0, "stable": False}
        for field_name in run_batch.STABILITY_FIELDS
    }
    monkeypatch.setattr(run_batch, "_ensure_output_contract", lambda *a, **k: None)
    monkeypatch.setattr(run_batch, "_write_dataset", lambda *a, **k: None)
    monkeypatch.setattr(run_batch, "_update_state_identity", lambda *a, **k: None)
    monkeypatch.setattr(run_batch, "_atomic_write_json", lambda *a, **k: None)
    monkeypatch.setattr(run_batch, "_metric_summary", lambda _results: metrics)
    monkeypatch.setattr(
        run_batch,
        "evaluate_gate_a",
        lambda **_kwargs: {
            "checked": False,
            "stable": False,
            "status": "BLOCKED",
            "reason": "golden provider missing",
        },
    )
    monkeypatch.setattr(
        run_batch,
        "evaluate_gate_b",
        lambda _metrics: {"checked": True, "stable": False, "metrics": {}},
    )
    monkeypatch.setattr(
        run_batch.monte_carlo,
        "run_trials_sequentially",
        fake_run_trials,
    )

    state = run_batch.run_batch(
        scenario="C070_G100",
        trials=600,
        output_dir=tmp_path,
        source_sha=APPROVED_SOURCE_SHA,
    )

    assert len(trial_blocks) == 1
    assert trial_blocks[0] == list(range(1, 301))
    assert state["final_status"] == "blocked"
    assert state["stability_history"][-1]["gate_a"]["status"] == "BLOCKED"
    assert state["included_in_final_stats"] is False
    assert state["stable_at_n"] is None
    assert "refusing to execute additional trials" in state["reason_if_not_stable"]
    assert state["final_status"] != "stable"


def _metric_summary_rows(values: tuple[float, float]) -> list[object]:
    from types import SimpleNamespace

    return [
        SimpleNamespace(
            final_net_project_equity=value,
            partner1_final_entitlement=value,
            partner2_final_entitlement=value,
        )
        for value in values
    ]


def test_metric_summary_uses_absolute_limit_only_inside_near_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(run_batch.t, "ppf", lambda *_args, **_kwargs: 1.0)
    epsilon = run_batch.constants.REFERENCE_EPSILON

    positive_near_zero = run_batch._metric_summary(
        _metric_summary_rows((0.0, epsilon * 1.8))
    )
    for metric in run_batch.STABILITY_FIELDS:
        assert positive_near_zero[metric]["mean"] == pytest.approx(epsilon * 0.9)
        assert positive_near_zero[metric]["limit"] == run_batch.constants.CI_ABSOLUTE_EPSILON

    negative_near_zero = run_batch._metric_summary(
        _metric_summary_rows((-epsilon * 1.8, 0.0))
    )
    for metric in run_batch.STABILITY_FIELDS:
        assert negative_near_zero[metric]["mean"] == pytest.approx(-epsilon * 0.9)
        assert negative_near_zero[metric]["limit"] == run_batch.constants.CI_ABSOLUTE_EPSILON

    boundary = run_batch._metric_summary(
        _metric_summary_rows((0.0, epsilon * 2.0))
    )
    for metric in run_batch.STABILITY_FIELDS:
        assert boundary[metric]["mean"] == pytest.approx(epsilon)
        assert boundary[metric]["limit"] == pytest.approx(
            run_batch.constants.CI_RELATIVE_TOLERANCE * epsilon
        )

    above_boundary = run_batch._metric_summary(
        _metric_summary_rows((0.0, epsilon * 2.2))
    )
    for metric in run_batch.STABILITY_FIELDS:
        assert above_boundary[metric]["mean"] == pytest.approx(epsilon * 1.1)
        assert above_boundary[metric]["limit"] == pytest.approx(
            run_batch.constants.CI_RELATIVE_TOLERANCE * epsilon * 1.1
        )


def test_metric_summary_does_not_apply_absolute_epsilon_to_regular_means(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(run_batch.t, "ppf", lambda *_args, **_kwargs: 1.0)
    summary = run_batch._metric_summary(_metric_summary_rows((9.8, 10.2)))

    for metric in run_batch.STABILITY_FIELDS:
        point = summary[metric]
        assert point["mean"] == pytest.approx(10.0)
        assert point["limit"] == pytest.approx(
            run_batch.constants.CI_RELATIVE_TOLERANCE * 10.0
        )
        assert point["half_ci_95"] > point["limit"]
        assert point["half_ci_95"] < run_batch.constants.CI_ABSOLUTE_EPSILON
        assert point["stable"] is False


def test_stage7_lease_rejects_malformed_records_fail_closed(tmp_path: Path) -> None:
    store = run_batch.StateStore(
        repo="yasmin977209-ux/motorcycle-simulation",
        token="test-token",
        scenario="C070_G100",
        source_sha=APPROVED_SOURCE_SHA,
        run_id="run-current",
        run_attempt="1",
        local_path=tmp_path / "state.json",
    )

    assert store._lease_is_active_for_other_owner(None) is False
    malformed_records = (
        {},
        {"expires_at": "2099-01-01T00:00:00Z"},
        {"owner": "run-other"},
        {"owner": "run-other", "expires_at": "not-a-date"},
        {"owner": "run-other", "expires_at": "2099-01-01T00:00:00"},
        [],
        "run-other",
    )
    for lease in malformed_records:
        with pytest.raises(StateIntegrityError):
            store._lease_is_active_for_other_owner(lease)


def test_stage7_lease_detects_active_other_owner_and_accepts_current_owner(
    tmp_path: Path,
) -> None:
    store = run_batch.StateStore(
        repo="yasmin977209-ux/motorcycle-simulation",
        token="test-token",
        scenario="C070_G100",
        source_sha=APPROVED_SOURCE_SHA,
        run_id="run-current",
        run_attempt="1",
        local_path=tmp_path / "state.json",
    )
    expiry = "2099-01-01T00:00:00Z"

    assert store._lease_is_active_for_other_owner(
        {"owner": "run-other", "expires_at": expiry}
    ) is True
    assert store._lease_is_active_for_other_owner(
        {"owner": "run-current", "expires_at": expiry}
    ) is False
