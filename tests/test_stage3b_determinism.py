from datetime import date

from daily_engine import run_deterministic_trial
from rng import derive_seed


def test_c100_trial_seeds_are_distinct() -> None:
    seeds = {
        derive_seed(
            20270101,
            "C100_G100",
            trial_id,
            "BK0001",
            date(2027, 1, 2),
            "PRIMARY_COLLECTION",
        )
        for trial_id in (101, 202, 303)
    }
    assert len(seeds) == 3


def test_c100_three_full_repetitions_are_identical() -> None:
    results = []
    for trial_id in (101, 202, 303):
        project = run_deterministic_trial(
            recovery_rate_pct=100,
            trial_id=trial_id,
            scenario_id="C100_G100",
            master_seed=20270101,
        )
        results.append(
            {
                "days_executed": len(project.daily_balance_checks),
                "final_close_date": (
                    project.final_close_date.isoformat()
                    if project.final_close_date
                    else None
                ),
                "bike_count": len(project.bikes),
                "Final_Net_Project_Equity": project.final_net_project_equity,
                "P1": project.partner1_final_entitlement,
                "P2": project.partner2_final_entitlement,
                "max_absolute_balance_difference": max(
                    abs(item["Balance_Difference"])
                    for item in project.daily_balance_checks
                ),
            }
        )
    assert results[0] == results[1] == results[2]
    assert all(
        item["max_absolute_balance_difference"] == 0
        for item in results
    )
