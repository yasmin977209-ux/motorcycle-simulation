"""C100 determinism: same full trial, different trial IDs and derived event seeds."""

from datetime import date
import json

from daily_engine import run_deterministic_trial, run_day, create_initial_project
from rng import derive_seed


def test_c100_three_full_repetitions_are_identical():
    trial_ids = (101, 202, 303)
    results = []

    for trial_id in trial_ids:
        project = run_deterministic_trial(
            recovery_rate_pct=100,
            trial_id=trial_id,
            scenario_id="C100_G100",
        )
        event_seed = derive_seed(
            20270101,
            "C100_G100",
            trial_id,
            "BK0001",
            date(2027, 1, 2),
            "PRIMARY_COLLECTION",
        )
        row = {
            "trial_id": trial_id,
            "derived_seed_hex": event_seed.hex(),
            "Cash": project.project_cash,
            "Final_Net_Project_Equity": project.final_net_project_equity,
            "Partner1_Final_Entitlement": project.partner1_final_entitlement,
            "Partner2_Final_Entitlement": project.partner2_final_entitlement,
            "final_close_date": project.final_close_date.isoformat(),
        }
        results.append(row)

    print(json.dumps(results, ensure_ascii=False, sort_keys=True))

    assert len({r["derived_seed_hex"] for r in results}) == 3

    fields = (
        "Cash",
        "Final_Net_Project_Equity",
        "Partner1_Final_Entitlement",
        "Partner2_Final_Entitlement",
        "final_close_date",
    )
    baseline = results[0]
    for row in results[1:]:
        for field in fields:
            assert row[field] == baseline[field]
