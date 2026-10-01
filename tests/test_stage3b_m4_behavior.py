from datetime import date

from daily_engine import create_initial_project, run_day
from entities import BikeState


def test_m4_delivery_day_counts_as_one_usage_day_and_depreciates_50():
    project = create_initial_project()
    delivery_day = date(2027, 1, 2)

    run_day(
        project,
        delivery_day,
        collection_probability=1.0,
        scenario_id="C100_G100",
        trial_id=1,
        recovery_rate_pct=100,
        master_seed=20270101,
    )

    target = project.bikes[0]

    assert target.delivery_date == delivery_day
    assert target.current_state is BikeState.ACTIVE_PRIMARY
    assert target.usage_days == 1
    assert target.accumulated_depreciation == 50
