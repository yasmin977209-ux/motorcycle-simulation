import argparse
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

import daily_engine
import monte_carlo
from entities import BikeState, ClaimStatus

SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
MASTER_SEED = 20270101


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scenario", required=True)
    p.add_argument("--start", type=int, required=True)
    p.add_argument("--end", type=int, required=True)
    a = p.parse_args()
    cp, rr = monte_carlo.parse_scenario_id(a.scenario)
    if a.end < a.start or a.end - a.start + 1 > 150 or (
        a.scenario.startswith("C100_") and a.start != a.end
    ):
        raise SystemExit("invalid chunk range")

    rows = []
    for tid in range(a.start, a.end + 1):
        daily_meta = []

        def capture(prj, d):
            daily_meta.append({
                "date": d.isoformat(),
                "Capital": prj.capital,
                "Retained_Earnings": prj.retained_earnings,
                "Simulation_Stopped": prj.simulation_stopped,
                "Active_Bikes": sum(b.current_state in daily_engine.POSSESSION_STATES for b in prj.bikes),
                "Owned_Transferred_Bikes": sum(b.current_state is BikeState.OWNED_TRANSFERRED for b in prj.bikes),
                "Pending_Claims": sum(c.status is ClaimStatus.PENDING for c in prj.guarantee_claims),
            })

        project = daily_engine.run_deterministic_trial(
            recovery_rate_pct=rr, trial_id=tid, scenario_id=a.scenario,
            master_seed=MASTER_SEED, collection_probability=cp,
            on_day_end=capture, log_events=False,
        )
        result = monte_carlo._trial_result_from_project(
            project, scenario_id=a.scenario, collection_probability=cp,
            recovery_rate_pct=rr, trial_id=tid
        )
        trial_sha = monte_carlo.fingerprint_trial_results([result])
        series = (
            project.daily_snapshots, project.cash_rollforward, project.ar_rollforward,
            project.asset_rollforward, project.equity_rollforward, daily_meta
        )
        if len({len(x) for x in series}) != 1:
            raise SystemExit(f"daily accounting length mismatch trial {tid}")

        for snap, cash, ar, asset, equity, meta in zip(*series):
            rows.append({
                "scenario_id": a.scenario, "trial_id": tid, "date": snap["date"].isoformat(),
                "source_sha": SOURCE_SHA, "master_seed": MASTER_SEED,
                "Opening_Cash": cash["Opening_Cash"], "cash_inflows": cash["Inflows"],
                "cash_outflows": cash["Outflows"], "Closing_Cash": cash["Closing_Cash"],
                "Opening_AR": ar["Opening_AR"], "ar_accruals": ar["Accruals"],
                "ar_collections": ar["Collections"], "ar_transfers_to_guarantee": ar["TransfersToGuarantee"],
                "Closing_AR": ar["Closing_AR"],
                "Opening_Gross_Bike_Assets": asset["Opening_Gross_Bike_Assets"],
                "capitalized_purchases_and_customs": asset["Capitalized_Purchases_And_Customs"],
                "gross_writeoffs_on_ownership": asset["Gross_Writeoffs_On_Ownership"],
                "Closing_Gross_Bike_Assets": asset["Closing_Gross_Bike_Assets"],
                "Opening_Accumulated_Depreciation": asset["Opening_Accumulated_Depreciation"],
                "depreciation_expense": asset["Depreciation_Expense"],
                "ad_removed_on_writeoff": asset["AD_Removed_On_Writeoff"],
                "Closing_Accumulated_Depreciation": asset["Closing_Accumulated_Depreciation"],
                "Net_Bike_Assets": snap["Net_Bike_Assets"], "Capital": meta["Capital"],
                "Retained_Earnings": meta["Retained_Earnings"], "Opening_Equity": equity["Opening_Equity"],
                "Operating_Net_Profit": equity["Operating_Net_Profit"], "Closing_Equity": equity["Closing_Equity"],
                "Guarantee_Claim_Receivable": snap["Guarantee_Claim_Receivable"],
                "Total_Assets": snap["Total_Assets"], "Liabilities": snap["Liabilities"],
                "Balance_Difference": snap["Balance_Difference"],
                "Final_Close_Date": project.final_close_date.isoformat() if project.final_close_date else None,
                "Simulation_Stopped": meta["Simulation_Stopped"], "Active_Bikes": meta["Active_Bikes"],
                "Owned_Transferred_Bikes": meta["Owned_Transferred_Bikes"], "Pending_Claims": meta["Pending_Claims"],
                "result_sha256": trial_sha,
            })

    out = Path("docs/stage12/daily_accounting")
    out.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), out / f"{a.scenario}_{a.start}_{a.end}.parquet")


if __name__ == "__main__":
    main()
