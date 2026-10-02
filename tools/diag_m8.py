from __future__ import annotations

import json
import math
import os
import random
import statistics
import subprocess
import sys
import time
from datetime import date, timedelta
from pathlib import Path

RESULTS = Path("results_diag")
RESULTS.mkdir(parents=True, exist_ok=True)

STATUS = []


def write_json(path: str, payload: dict) -> None:
    (RESULTS / path).write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def run_pytest() -> None:
    out = RESULTS / "01_pytest_m8.txt"
    with out.open("w", encoding="utf-8") as fh:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/test_m8_settlement_api.py", "-v"],
            stdout=fh,
            stderr=subprocess.STDOUT,
            text=True,
        )
    (RESULTS / "01_pytest_m8_status.txt").write_text(
        f"EXIT_CODE={proc.returncode}\n", encoding="utf-8"
    )
    STATUS.append(("pytest_m8", proc.returncode))


def run_c100() -> None:
    from daily_engine import run_deterministic_trial

    started = time.perf_counter()
    p = run_deterministic_trial(
        recovery_rate_pct=100,
        trial_id=1,
        scenario_id="C100_G100",
        master_seed=20270101,
    )
    elapsed = time.perf_counter() - started
    max_abs = max(abs(row["Balance_Difference"]) for row in p.daily_balance_checks)

    payload = {
        "Final_Net_Project_Equity": p.final_net_project_equity,
        "P1": p.partner1_final_entitlement,
        "P2": p.partner2_final_entitlement,
        "days": len(p.daily_balance_checks),
        "final_close_date": p.final_close_date.isoformat() if p.final_close_date else None,
        "max_absolute_balance_difference": max_abs,
        "elapsed_seconds": elapsed,
        "cpu_count": os.cpu_count(),
    }
    write_json("02_c100_g100.json", payload)

    rc = 0
    try:
        assert payload["Final_Net_Project_Equity"] == 209671000
        assert payload["P1"] == 146769700
        assert payload["P2"] == 62901300
        assert payload["days"] == 2198
        assert payload["max_absolute_balance_difference"] == 0
    except AssertionError:
        rc = 1

    (RESULTS / "02_c100_g100_status.txt").write_text(
        f"EXIT_CODE={rc}\n", encoding="utf-8"
    )
    STATUS.append(("c100", rc))


def run_single_contract() -> None:
    import constants
    import dateutils
    from state_machine import derive_state_from_balance

    p = 0.30
    trials = 2000
    random_seed = 20270101
    start_date = date(2027, 1, 2)
    maturity_date = dateutils.primary_maturity_date(start_date)
    default_days = constants.PRIMARY_DEFAULT_AMOUNT // constants.PRIMARY_DAILY_RENT

    business_dates = []
    current = start_date
    while current <= maturity_date:
        if dateutils.is_business_day(current):
            business_dates.append(current)
        current += timedelta(days=1)

    rng = random.Random(random_seed)
    shared_draw_table = [
        [rng.random() for _ in business_dates]
        for _ in range(trials)
    ]

    maturity_count = 0
    termination_business_indices = []
    termination_calendar_offsets = []

    for trial_draws in shared_draw_table:
        outstanding = 0
        terminated = False

        for index, (current_date, draw) in enumerate(
            zip(business_dates, trial_draws), start=1
        ):
            outstanding += constants.PRIMARY_DAILY_RENT

            if draw < p:
                prior_arrears = max(
                    0,
                    outstanding - constants.PRIMARY_DAILY_RENT,
                )
                arrears_payment = min(
                    constants.PRIMARY_DAILY_RENT,
                    prior_arrears,
                )
                collected = min(
                    constants.PRIMARY_DAILY_RENT + arrears_payment,
                    outstanding,
                )
                outstanding -= collected

            if (
                derive_state_from_balance(
                    outstanding,
                    constants.PRIMARY_DAILY_RENT,
                    "PRIMARY",
                )
                is None
            ):
                terminated = True
                termination_business_indices.append(index)
                termination_calendar_offsets.append(
                    (current_date - start_date).days
                )
                break

        if not terminated:
            maturity_count += 1

    dp = [0.0] * default_days
    dp[0] = 1.0
    for _ in business_dates:
        nxt = [0.0] * default_days
        for state, mass in enumerate(dp):
            if mass == 0.0:
                continue
            if state + 1 < default_days:
                nxt[state + 1] += mass * (1.0 - p)
            nxt[max(0, state - 1)] += mass * p
        dp = nxt

    theoretical_maturity_probability = sum(dp)

    def percentile(values, q):
        ordered = sorted(values)
        if not ordered:
            return None
        position = (len(ordered) - 1) * q
        lo = math.floor(position)
        hi = math.ceil(position)
        if lo == hi:
            return ordered[lo]
        return ordered[lo] + (ordered[hi] - ordered[lo]) * (position - lo)

    payload = {
        "trials": trials,
        "p": p,
        "shared_draw_table_seed": random_seed,
        "shared_draw_table_rows": len(shared_draw_table),
        "shared_draw_table_columns": len(business_dates),
        "maturity_date": maturity_date.isoformat(),
        "business_days_to_maturity": len(business_dates),
        "default_threshold_days": default_days,
        "maturity_count": maturity_count,
        "maturity_fraction": maturity_count / trials,
        "maturity_percent": 100.0 * maturity_count / trials,
        "termination_count": len(termination_business_indices),
        "termination_business_day_mean": statistics.mean(termination_business_indices)
        if termination_business_indices
        else None,
        "termination_business_day_P10": percentile(
            termination_business_indices, 0.10
        ),
        "termination_business_day_P50": percentile(
            termination_business_indices, 0.50
        ),
        "termination_business_day_P90": percentile(
            termination_business_indices, 0.90
        ),
        "termination_calendar_offset_mean": statistics.mean(
            termination_calendar_offsets
        )
        if termination_calendar_offsets
        else None,
        "termination_calendar_offset_P10": percentile(
            termination_calendar_offsets, 0.10
        ),
        "termination_calendar_offset_P50": percentile(
            termination_calendar_offsets, 0.50
        ),
        "termination_calendar_offset_P90": percentile(
            termination_calendar_offsets, 0.90
        ),
        "theoretical_maturity_probability": theoretical_maturity_probability,
        "theoretical_maturity_probability_ratio_to_2_5e-22":
            theoretical_maturity_probability / 2.5e-22,
        "absolute_difference_from_2_5e-22":
            abs(theoretical_maturity_probability - 2.5e-22),
        "cpu_count": os.cpu_count(),
    }
    write_json("03_single_contract_2000.json", payload)
    (RESULTS / "03_single_contract_2000_status.txt").write_text(
        "EXIT_CODE=0\n", encoding="utf-8"
    )
    STATUS.append(("single_contract", 0))


def run_c030() -> None:
    from daily_engine import create_initial_project, run_day

    p = create_initial_project(recovery_rate_pct=0)
    current = date(2027, 1, 1)
    started = time.perf_counter()
    days = 0

    while not p.simulation_stopped:
        run_day(
            p,
            current,
            collection_probability=0.30,
            scenario_id="C030_G000",
            trial_id=1,
            recovery_rate_pct=0,
            master_seed=20270101,
        )
        days += 1
        current += timedelta(days=1)

    elapsed = time.perf_counter() - started
    max_abs = max(abs(row["Balance_Difference"]) for row in p.daily_balance_checks)

    payload = {
        "scenario_id": "C030_G000",
        "trial_id": 1,
        "days": days,
        "final_close_date":
            p.final_close_date.isoformat() if p.final_close_date else None,
        "Final_Net_Project_Equity": p.final_net_project_equity,
        "contracts": len(p.contracts),
        "claims": len(p.guarantee_claims),
        "max_absolute_balance_difference": max_abs,
        "daily_balance_check_count": len(p.daily_balance_checks),
        "elapsed_seconds": elapsed,
        "cpu_count": os.cpu_count(),
    }
    write_json("04_c030_g000.json", payload)
    (RESULTS / "04_c030_g000_status.txt").write_text(
        "EXIT_CODE=0\n", encoding="utf-8"
    )
    STATUS.append(("c030", 0))


def main() -> int:
    overall = 0
    try:
        run_pytest()
    except Exception as exc:
        (RESULTS / "01_pytest_m8_exception.txt").write_text(
            repr(exc) + "\n", encoding="utf-8"
        )
        STATUS.append(("pytest_m8_exception", 1))

    try:
        run_c100()
    except Exception as exc:
        (RESULTS / "02_c100_g100_exception.txt").write_text(
            repr(exc) + "\n", encoding="utf-8"
        )
        (RESULTS / "02_c100_g100_status.txt").write_text(
            "EXIT_CODE=1\n", encoding="utf-8"
        )
        STATUS.append(("c100_exception", 1))

    try:
        run_single_contract()
    except Exception as exc:
        (RESULTS / "03_single_contract_2000_exception.txt").write_text(
            repr(exc) + "\n", encoding="utf-8"
        )
        (RESULTS / "03_single_contract_2000_status.txt").write_text(
            "EXIT_CODE=1\n", encoding="utf-8"
        )
        STATUS.append(("single_contract_exception", 1))

    try:
        run_c030()
    except Exception as exc:
        (RESULTS / "04_c030_g000_exception.txt").write_text(
            repr(exc) + "\n", encoding="utf-8"
        )
        (RESULTS / "04_c030_g000_status.txt").write_text(
            "EXIT_CODE=1\n", encoding="utf-8"
        )
        STATUS.append(("c030_exception", 1))

    overall = 1 if any(rc != 0 for _, rc in STATUS) else 0
    write_json(
        "05_status.json",
        {
            "overall_exit_code": overall,
            "items": [
                {"name": name, "exit_code": rc}
                for name, rc in STATUS
            ],
        },
    )
    return overall


if __name__ == "__main__":
    raise SystemExit(main())
