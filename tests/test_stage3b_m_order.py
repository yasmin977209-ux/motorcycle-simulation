from datetime import date

from daily_engine import create_initial_project, run_day


def test_ch12_m1_to_m17_order_is_recorded_only_when_test_enables_trace() -> None:
    project = create_initial_project()
    project._execution_trace_enabled = True
    run_day(
        project,
        date(2027, 1, 1),
        collection_probability=1.0,
        trial_id=1,
        scenario_id="C100_G100",
    )
    assert project.execution_trace[-1] == [f"M{i}" for i in range(1, 18)]


def test_ch12_trace_is_empty_by_default() -> None:
    project = create_initial_project()
    run_day(project, date(2027, 1, 1))
    assert project.execution_trace == []


def test_ch12_daily_engine_processes_calendar_days() -> None:
    project = create_initial_project()
    run_day(project, date(2027, 1, 1))
    run_day(project, date(2027, 1, 2))
    assert len(project.daily_balance_checks) == 2
