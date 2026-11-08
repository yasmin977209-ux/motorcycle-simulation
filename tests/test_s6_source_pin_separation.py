import argparse
import subprocess

from scripts import s4_c100_golden as c100
from scripts import s6_first_checkpoint as s6


MODEL_SOURCE_SHA = "b" * 40
WORKFLOW_HEAD_SHA = "a" * 40
COHORT = "s6-v23-rebuild-20261105"


def test_s6_current_git_commit_prefers_checked_out_source_over_workflow_sha(monkeypatch):
    monkeypatch.setenv("GITHUB_SHA", WORKFLOW_HEAD_SHA)
    monkeypatch.setattr(
        s6.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, stdout=MODEL_SOURCE_SHA + "\n", stderr=""),
    )
    assert s6.current_git_commit() == MODEL_SOURCE_SHA


def test_s6_action_config_separates_model_source_sha_from_workflow_head(monkeypatch):
    config = {
        "checkpoint_mode": "FRESH",
        "active_target_trials": 300,
        "trial_start": 1,
        "trial_end": 300,
        "cohort_id": COHORT,
        "governing_decision_id": "D-2026-10-30-REFERENCE-V2.4.0",
        "reference_sha256": "225de838d35d6ed383886bf8d0dbe104a6f3d7c72baa6eac5d15e352f4652c0b",
    }
    monkeypatch.setattr(s6, "_s6_action_checkpoint_config", lambda: config)
    monkeypatch.setattr(s6, "current_git_commit", lambda: MODEL_SOURCE_SHA)
    monkeypatch.setenv("S6_SOURCE_SHA", MODEL_SOURCE_SHA)
    monkeypatch.setenv("GITHUB_SHA", WORKFLOW_HEAD_SHA)
    args = argparse.Namespace(
        source_sha=MODEL_SOURCE_SHA,
        cohort_id=COHORT,
        trials=300,
        mode="scenario",
        previous_dir=None,
    )
    assert s6.apply_action_checkpoint_config(args) == config
    assert args.trial_start == 1
    assert args.trial_end == 300


def test_c100_checked_out_source_sha_is_not_workflow_event_sha(monkeypatch):
    monkeypatch.setenv("GITHUB_SHA", WORKFLOW_HEAD_SHA)
    monkeypatch.setattr(
        c100.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 0, stdout=MODEL_SOURCE_SHA + "\n", stderr=""),
    )
    assert c100.checked_out_source_sha() == MODEL_SOURCE_SHA
