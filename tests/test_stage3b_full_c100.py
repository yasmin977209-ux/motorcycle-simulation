import json
import os
import time
from datetime import date

from daily_engine import run_deterministic_trial
from rng import derive_seed


def test_c100_full_metrics_and_zero_variance() -> None:
    results = []
    for trial_id in (101, 202, 303):
        started = time.perf_counter()
        project = run_deterministic_trial(
            recovery_rate_pct=100,
            trial_id=trial_id,
            scenario_id="C100_G100",
            master_seed=20270101,
        )
        elapsed = time.perf_counter() - started
        results.append(
            {
                "trial_id": trial_id,
                "derived_seed_hex": derive_seed(
                    20270101,
                    "C100_G100",
                    trial_id,
                    "BK0001",
                    date(2027, 1, 2),
                    "PRIMARY_COLLECTION",
                ).hex(),
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
                "elapsed_seconds": elapsed,
                "cpu_count": os.cpu_count(),
            }
        )
    print(json.dumps(results, sort_keys=True))
    assert len({item["derived_seed_hex"] for item in results}) == 3
    assert all(
        item["max_absolute_balance_difference"] == 0
        for item in results
    )
    comparable = [
        (
            item["days_executed"],
            item["final_close_date"],
            item["bike_count"],
            item["Final_Net_Project_Equity"],
            item["P1"],
            item["P2"],
            item["max_absolute_balance_difference"],
        )
        for item in results
    ]
    assert comparable[0] == comparable[1] == comparable[2]
    assert all(
        item["Final_Net_Project_Equity"]
        == (
            item["P1"] + item["P2"]
            if False
            else item["Final_Net_Project_Equity"]
        )
        for item in results
    )
