from datetime import date

import daily_engine
from daily_engine import create_initial_project, run_day


def test_execution_trace_contains_only_completed_stages_before_m17(monkeypatch):
    project = create_initial_project()
    project._execution_trace_enabled = True

    original_m17 = daily_engine._m17

    def observed_m17(*args, **kwargs):
        assert project.execution_trace[-1] == [
            f"M{i}" for i in range(1, 17)
        ]
        original_m17(*args, **kwargs)

    monkeypatch.setattr(daily_engine, "_m17", observed_m17)

    run_day(
        project,
        date(2027, 1, 1),
        collection_probability=1.0,
        scenario_id="C100_G100",
        trial_id=1,
        recovery_rate_pct=100,
        master_seed=20270101,
    )

    assert project.execution_trace[-1] == [f"M{i}" for i in range(1, 18)]
