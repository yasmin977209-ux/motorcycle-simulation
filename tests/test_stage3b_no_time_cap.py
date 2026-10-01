from datetime import date, timedelta

import closure
from daily_engine import create_initial_project, run_day


def test_daily_engine_continues_for_more_than_two_thousand_days(
    monkeypatch,
) -> None:
    project = create_initial_project()
    monkeypatch.setattr(
        closure,
        "execute_dynamic_closure",
        lambda *args, **kwargs: False,
    )
    for offset in range(2_001):
        run_day(
            project,
            date(2027, 1, 1) + timedelta(days=offset),
            0.0,
            "C000_TEST",
            1,
            100,
            20270101,
        )
    assert project.simulation_stopped is False
    assert len(project.daily_balance_checks) == 2_001
