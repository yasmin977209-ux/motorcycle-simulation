from __future__ import annotations

from dataclasses import asdict

import daily_engine
import monte_carlo


def _trial_result(project, scenario_id: str, trial_id: int):
    collection_probability, recovery_rate_pct = monte_carlo.parse_scenario_id(
        scenario_id
    )
    return monte_carlo._trial_result_from_project(
        project,
        scenario_id=scenario_id,
        collection_probability=collection_probability,
        recovery_rate_pct=recovery_rate_pct,
        trial_id=trial_id,
    )


def test_log_events_preserves_trial_result_and_c100_golden():
    scenario_id = "C085_G100"
    trial_id = 1

    project_true = daily_engine.run_deterministic_trial(
        scenario_id=scenario_id,
        trial_id=trial_id,
        log_events=True,
    )
    project_false = daily_engine.run_deterministic_trial(
        scenario_id=scenario_id,
        trial_id=trial_id,
        log_events=False,
    )

    result_true = _trial_result(project_true, scenario_id, trial_id)
    result_false = _trial_result(project_false, scenario_id, trial_id)

    assert asdict(result_true) == asdict(result_false)
    assert len(project_true.event_log) > 0
    assert len(project_false.event_log) == 0

    golden = daily_engine.run_deterministic_trial(
        scenario_id="C100_G100",
        trial_id=1,
        log_events=False,
    )
    golden_result = _trial_result(golden, "C100_G100", 1)

    assert golden_result.final_net_project_equity == 209671000
    assert golden_result.final_cash == 209671000
    assert golden_result.partner1_final_entitlement == 146769700
    assert golden_result.partner2_final_entitlement == 62901300
    assert golden_result.final_close_date == "2033-01-06"
