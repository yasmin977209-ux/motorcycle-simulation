from __future__ import annotations

import inspect
from datetime import date, timedelta

import constants
import daily_engine
import dateutils
from closure import closure_preconditions_met
from entities import Bike, BikeSource, BikeState, Project


def _underfunded_prep_project() -> tuple[Project, Bike]:
    project = Project(
        project_cash=0,
        partner1_reinvestment_balance=0,
    )
    bike = Bike(
        bike_id="BK_AUDIT_PREP",
        source=BikeSource.EXPANSION,
        purchase_date=date(2030, 12, 31),
        scheduled_ready_date=date(2031, 1, 6),
        current_state=BikeState.PREP,
        prep_paid=False,
        customs_paid=False,
    )
    project.bikes.append(bike)
    return project, bike


def test_unfunded_prep_has_no_local_progress_or_closure_without_funding() -> None:
    project, bike = _underfunded_prep_project()
    probe_days = [date(2031, 1, 1) + timedelta(days=i) for i in range(20)]
    assert any(dateutils.is_business_day(day) for day in probe_days)

    for current_date in probe_days:
        daily_engine._m2(project, current_date)
        assert bike.current_state is BikeState.PREP
        assert bike.prep_paid is False
        assert bike.customs_paid is False
        assert bike.actual_ready_date is None
        assert closure_preconditions_met(project, current_date) is False
        assert project.simulation_stopped is False

    # This establishes the conditional behavior of the synthetic state only.
    # It does not establish reachability from create_initial_project().
    assert daily_engine._has_prep_underfunded(project) is True


def test_current_runner_has_no_hard_day_cap_or_fixed_close_date() -> None:
    source = inspect.getsource(daily_engine.run_deterministic_trial)
    signature = inspect.signature(daily_engine.run_deterministic_trial)

    assert "while not project.simulation_stopped" in source
    assert "max_days" not in signature.parameters
    assert constants.FINAL_CLOSE_DATE is None
    assert constants.EXPANSION_CUTOFF_DATE == date(2030, 12, 31)


def test_closure_explicitly_requires_zero_prep_bikes_after_cutoff() -> None:
    project, _bike = _underfunded_prep_project()
    assert date(2031, 1, 1) > constants.EXPANSION_CUTOFF_DATE
    assert closure_preconditions_met(project, date(2031, 1, 1)) is False
