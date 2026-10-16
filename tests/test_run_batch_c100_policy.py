from __future__ import annotations

from pathlib import Path

import pytest

import constants
import monte_carlo
import run_batch

SOURCE_SHA_SENTINEL = "c" * 40
SCENARIO = "C100_G100"


def _result(trial_id: int) -> monte_carlo.TrialResult:
    return monte_carlo.TrialResult(
        scenario_id=SCENARIO,
        collection_probability=1.0,
        recovery_rate_pct=100,
        trial_id=trial_id,
        final_close_date="2027-01-01",
        final_net_project_equity=1_000,
        final_cash=500,
        cumulative_project_profit=900,
        operating_net_profit=920,
        termination_count=0,
        secondary_cycle_count=0,
        owned_bikes=10,
        held_assets=0,
        total_operating_revenue=1_200,
        bad_debt=0,
        guarantee_recovered=0,
        partner1_final_entitlement=700,
        partner2_final_entitlement=300,
    )


def _daily(trial_id: int) -> list[dict[str, object]]:
    return [{
        "date": "2027-01-01",
        "trial_id": trial_id,
        "Cash": 500,
        "Capital": 1_000,
        "Retained_Earnings": 0,
        "Net_Equity": 1_000,
        "Active_Bikes": 10,
        "Owned_Transferred_Bikes": 0,
        "Pending_Claims": 0,
        "Final_Close_Date": "2027-01-01",
    }]


def _fake_batch_factory(calls: list[list[int]]):
    def fake_run_trials(
        scenario: str,
        trial_ids: tuple[int, ...] | list[int],
        *,
        master_seed: int,
    ) -> tuple[list[monte_carlo.TrialResult], dict[int, list[dict[str, object]]]]:
        ids = [int(value) for value in trial_ids]
        calls.append(ids)
        return ([_result(value) for value in ids], {value: _daily(value) for value in ids})
    return fake_run_trials


def test_c100_has_the_same_start_checkpoint_and_ci_policy() -> None:
    assert constants.C100_STATISTICAL_START_TRIALS == 300
    assert constants.NON_C100_STATISTICAL_START_TRIALS == 300
    assert constants.C100_CI_GATE_ENABLED is True
    assert constants.STATISTICAL_START_TRIALS_BY_COLLECTION[1.0] == 300
    assert constants.STATISTICAL_START_TRIALS_BY_COLLECTION[0.7] == 300

    args = run_batch.parse_args([
        "--scenario", SCENARIO,
        "--trials", "300",
        "--output-dir", "unused-output",
    ])
    assert args.trials == 300


def test_c100_runs_the_same_doubling_checkpoints_with_synthetic_rows_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[int]] = []
    monkeypatch.setattr(monte_carlo, "run_trials_sequentially", _fake_batch_factory(calls))

    def approved_gate_a(**kwargs):
        return {
            "status": "PASS",
            "checked": True,
            "stable": True,
            "previous_n": kwargs["previous_n"],
            "current_n": kwargs["current_n"],
            "reason": None,
        }

    monkeypatch.setattr(run_batch, "evaluate_gate_a", approved_gate_a)
    monkeypatch.setattr(
        monte_carlo,
        "run_single_trial",
        lambda *args, **kwargs: pytest.fail("legacy C100 extra verification was called"),
    )

    state = run_batch.run_batch(
        scenario=SCENARIO,
        trials=1200,
        output_dir=tmp_path / "batch",
        source_sha=SOURCE_SHA_SENTINEL,
    )

    assert [len(group) for group in calls] == [300, 300, 600]
    assert calls[0] == list(range(1, 301))
    assert calls[1] == list(range(301, 601))
    assert calls[2] == list(range(601, 1201))
    assert [point["n"] for point in state["stability_history"]] == [300, 600, 1200]
    assert state["final_status"] == "stable"
    assert state["stable_at_n"] == 1200
    assert state["included_in_final_stats"] is True
    assert not state.get("c100_independent_verification")
    assert state["source_sha"] == SOURCE_SHA_SENTINEL
    assert state["master_seed"] == constants.MASTER_SEED


def test_c100_stops_at_first_checkpoint_when_gate_a_has_no_approved_golden(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[int]] = []
    monkeypatch.setattr(monte_carlo, "run_trials_sequentially", _fake_batch_factory(calls))

    state = run_batch.run_batch(
        scenario=SCENARIO,
        trials=1200,
        output_dir=tmp_path / "batch-blocked",
        source_sha=SOURCE_SHA_SENTINEL,
    )

    assert len(calls) == 1
    assert calls[0] == list(range(1, 301))
    assert [point["n"] for point in state["stability_history"]] == [300]
    assert state["stability_history"][0]["gate_a"]["status"] == "BLOCKED"
    assert state["final_status"] == "blocked"
    assert state["included_in_final_stats"] is False
    assert state["next_check_n"] == 600
