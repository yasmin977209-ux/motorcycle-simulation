"""Pytest coverage for Stage 1 (Chapters 0, 1, and 2).

All assertions are executable: any missing constant, value mismatch,
calendar mismatch, RNG mismatch, or cross-process reproducibility failure
causes pytest to fail.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import constants
import dateutils
import rng


# Directly named identifiers appearing as constants in the Chapter 2 tables:
# 2.1 (9) + 2.2 (28) + 2.3 (6) + 2.5 (3) = 46.
REFERENCE_CHAPTER_2_CONSTANTS = {
    # 2.1 temporal
    "PROJECT_START_DATE": date(2027, 1, 1),
    "INITIAL_FLEET_PURCHASE_DATE": date(2026, 12, 26),
    "INITIAL_FLEET_READY_DATE": date(2027, 1, 1),
    "INITIAL_FLEET_DELIVERY_DATE": date(2027, 1, 2),
    "BIKE_PREP_SCHEDULE_DAYS": 6,
    "PRIMARY_CONTRACT_MONTHS": 24,
    "SECONDARY_CONTRACT_DURATION": None,
    "EXPANSION_CUTOFF_DATE": date(2030, 12, 31),
    "FINAL_CLOSE_DATE": None,
    # 2.2 financial/opening
    "TOTAL_CAPITAL": 3_700_000,
    "BIKE_BASE_PURCHASE_COST": 350_000,
    "CUSTOMS_COST": 5_000,
    "REGISTRATION_COST": 5_000,
    "CUSTOMS_AND_REGISTRATION_COST": 10_000,
    "BIKE_GROSS_ASSET_COST": 360_000,
    "PREP_OIL_COST": 2_000,
    "PREP_LUBE_COST": 2_000,
    "PREP_OPERATING_EXPENSE_PER_BIKE": 4_000,
    "EXPANSION_PURCHASE_CASH_THRESHOLD": 350_000,
    "FULL_PREP_CASH_REQUIREMENT": 14_000,
    "PRIMARY_DAILY_RENT": 1_500,
    "SECONDARY_DAILY_RENT": 1_000,
    "SETTLEMENT_DAILY_RENT": 1_500,
    "FRIDAY_FEE": 1_000,
    "OIL_SERVICE_COST": 2_000,
    "DEPRECIATION_RATE_PER_DAY": 50,
    "MAX_DEPRECIATION": 360_000,
    "PARTNER1_FINAL_SHARE_PCT": 70,
    "PARTNER2_FINAL_SHARE_PCT": 30,
    "OPENING_CASH": 0,
    "OPENING_MARKETING_EXPENSE": 60_000,
    "OPENING_PREP_EXPENSE": 40_000,
    "OPENING_RETAINED_LOSS": -100_000,
    "OPENING_BIKE_ASSETS": 3_600_000,
    "INITIAL_FLEET_SIZE": 10,
    "OPENING_PARTNER1_REINVESTMENT_BALANCE": 0,
    "OPENING_PARTNER2_REINVESTMENT_BALANCE": 0,
    # 2.3 default/state thresholds
    "PRIMARY_DEFAULT_AMOUNT": 45_000,
    "SECONDARY_DEFAULT_AMOUNT": 10_000,
    "WAITING_PRIMARY_UPPER": 31_500,
    "NOTICE_PRIMARY_UPPER": 42_000,
    "GRACE_PRIMARY_UPPER": 45_000,
    "SETTLEMENT_PERIOD_DAYS": 30,
    # 2.5 Monte Carlo
    "MASTER_SEED": 20270101,
    "COLLECTION_PROBABILITIES": (1.00, 0.85, 0.70, 0.50, 0.30),
    "GUARANTEE_RECOVERY_RATES": (100, 70, 50, 30, 0),
}

# Chapter 2.4 has five claim-source rows with numeric waiting periods.
# These are represented in constants.py by explicit duration names + a
# claim-source -> duration mapping.
REFERENCE_CLAIM_WAITING_PERIODS = {
    "PRIMARY_EARLY_TERMINATION": 30,
    "SECONDARY_EARLY_TERMINATION": 20,
    "POST_MATURITY_SETTLEMENT_FAILURE": 60,
    "ADMINISTRATIVE_CLOSURE": 0,
    "FINAL_CLOSURE": 0,
}

# User-approved execution overrides that supersede Chapter 2.5's older
# illustrative starting/escalation table.
USER_APPROVED_EXECUTION_OVERRIDES = {
    "C100_STATISTICAL_START_TRIALS": 1,
    "NON_C100_STATISTICAL_START_TRIALS": 300,
    "ITERATION_ESCALATION_STEP": 50,
    "STATISTICAL_CHECK_START_N": 300,
    "STATISTICAL_CHECK_STEP_N": 50,
    "MINIMUM_STOP_N_FOR_NON_C100": 400,
    "STABILITY_CONSECUTIVE_CHECKS_REQUIRED": 3,
    "INITIAL_SMOKE_TRIALS_PER_SCENARIO": 1,
    "C100_CI_GATE_ENABLED": False,
    "CI_ABSOLUTE_EPSILON": 1,
}


def test_reference_chapter_2_constants_are_exact() -> None:
    actual = {
        name: getattr(constants, name)
        for name in REFERENCE_CHAPTER_2_CONSTANTS
        if hasattr(constants, name)
    }
    assert set(actual) == set(REFERENCE_CHAPTER_2_CONSTANTS)
    for name, expected in REFERENCE_CHAPTER_2_CONSTANTS.items():
        assert actual[name] == expected, name


def test_chapter_2_4_claim_waiting_periods_are_exact() -> None:
    actual = {
        constants.CLAIM_SOURCE_PRIMARY_EARLY_TERMINATION:
            constants.PRIMARY_EARLY_TERMINATION_WAIT_DAYS,
        constants.CLAIM_SOURCE_SECONDARY_EARLY_TERMINATION:
            constants.SECONDARY_EARLY_TERMINATION_WAIT_DAYS,
        constants.CLAIM_SOURCE_POST_MATURITY_SETTLEMENT_FAILURE:
            constants.POST_MATURITY_SETTLEMENT_FAILURE_WAIT_DAYS,
        constants.CLAIM_SOURCE_ADMINISTRATIVE_CLOSURE:
            constants.ADMINISTRATIVE_CLOSURE_WAIT_DAYS,
        constants.CLAIM_SOURCE_FINAL_CLOSURE:
            constants.FINAL_CLOSURE_WAIT_DAYS,
    }
    assert actual == REFERENCE_CLAIM_WAITING_PERIODS
    assert constants.CLAIM_WAITING_PERIODS_DAYS == REFERENCE_CLAIM_WAITING_PERIODS


def test_user_approved_execution_overrides_are_exact() -> None:
    for name, expected in USER_APPROVED_EXECUTION_OVERRIDES.items():
        assert getattr(constants, name) == expected, name
    assert constants.STATISTICAL_START_TRIALS_BY_COLLECTION == {
        1.00: 1,
        0.85: 300,
        0.70: 300,
        0.50: 300,
        0.30: 300,
    }


def test_date_calendar_and_reference_examples() -> None:
    assert date(2027, 1, 1).weekday() == 4
    assert dateutils.is_friday(date(2027, 1, 1))
    assert not dateutils.is_business_day(date(2027, 1, 1))
    assert dateutils.is_business_day(date(2027, 1, 2))
    assert dateutils.is_business_day(date(2027, 1, 3))
    assert dateutils.scheduled_ready_date(date(2026, 12, 26)) == date(2027, 1, 1)
    assert dateutils.next_business_day_on_or_after(date(2027, 1, 1)) == date(2027, 1, 2)
    assert dateutils.primary_maturity_date(date(2027, 1, 2)) == date(2029, 1, 2)

    expected_fridays = {
        date(2027, 1, 2): date(2027, 1, 8),
        date(2027, 1, 3): date(2027, 1, 8),
        date(2027, 1, 4): date(2027, 1, 8),
        date(2027, 1, 5): date(2027, 1, 15),
        date(2027, 1, 6): date(2027, 1, 15),
        date(2027, 1, 7): date(2027, 1, 15),
    }
    for delivery, expected in expected_fridays.items():
        assert dateutils.first_eligible_friday(delivery) == expected
        assert dateutils.is_eligible_friday(delivery, expected)
        assert dateutils.eligible_friday_number(delivery, expected) == 1

    assert dateutils.settlement_due_date(date(2027, 1, 15), 20) == date(2027, 2, 5)
    assert dateutils.settlement_due_date(date(2027, 1, 15), 30) == date(2027, 2, 15)
    assert dateutils.settlement_due_date(date(2027, 1, 15), 60) == date(2027, 3, 17)
    assert dateutils.settlement_due_date(date(2027, 1, 15), 0) == date(2027, 1, 15)
    assert dateutils.claim_waiting_period_days(
        constants.CLAIM_SOURCE_PRIMARY_EARLY_TERMINATION
    ) == 30


def test_rng_is_sha256_and_logically_independent() -> None:
    key = "20270101|C085_G070|1|BK0001|2027-01-02|PRIMARY_COLLECTION"
    expected_digest = hashlib.sha256(key.encode("utf-8")).digest()
    actual_digest = rng.derive_seed(
        constants.MASTER_SEED,
        "C085_G070",
        1,
        "BK0001",
        date(2027, 1, 2),
        "PRIMARY_COLLECTION",
    )
    assert rng.HASH_ALGORITHM == "sha256"
    assert actual_digest == expected_digest
    assert rng.seed_hex(
        constants.MASTER_SEED,
        "C085_G070",
        1,
        "BK0001",
        date(2027, 1, 2),
        "PRIMARY_COLLECTION",
    ) == expected_digest.hex()

    logical_events = {
        actual_digest,
        rng.derive_seed(constants.MASTER_SEED, "C085_G071", 1, "BK0001", date(2027, 1, 2), "PRIMARY_COLLECTION"),
        rng.derive_seed(constants.MASTER_SEED, "C085_G070", 2, "BK0001", date(2027, 1, 2), "PRIMARY_COLLECTION"),
        rng.derive_seed(constants.MASTER_SEED, "C085_G070", 1, "BK0002", date(2027, 1, 2), "PRIMARY_COLLECTION"),
        rng.derive_seed(constants.MASTER_SEED, "C085_G070", 1, "BK0001", date(2027, 1, 3), "PRIMARY_COLLECTION"),
        rng.derive_seed(constants.MASTER_SEED, "C085_G070", 1, "BK0001", date(2027, 1, 2), "SECONDARY_COLLECTION"),
        rng.derive_seed(constants.MASTER_SEED, "C085_G070", 1, "BK0001", date(2027, 1, 2), "LEGACY_DEBT_COLLECTION"),
    }
    assert len(logical_events) == 7
    assert rng.deterministic_success(1.0, actual_digest) is True
    assert rng.deterministic_success(0.0, actual_digest) is False


def test_rng_reproducible_across_pythonhashseed_processes() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = """
from datetime import date
import hashlib
import rng
key = "20270101|C085_G070|1|BK0001|2027-01-02|PRIMARY_COLLECTION"
digest = rng.derive_seed(20270101, "C085_G070", 1, "BK0001", date(2027, 1, 2), "PRIMARY_COLLECTION")
print(hash("motorcycle-simulation"))
print(digest.hex())
print(hashlib.sha256(key.encode("utf-8")).hexdigest())
"""
    results = []
    for hash_seed in ("1", "987654"):
        env = os.environ.copy()
        env["PYTHONHASHSEED"] = hash_seed
        env["PYTHONPATH"] = os.pathsep.join(
            [str(repo_root), env.get("PYTHONPATH", "")]
        ).rstrip(os.pathsep)
        completed = subprocess.run(
            [sys.executable, "-c", script],
            cwd=repo_root,
            env=env,
            check=True,
            capture_output=True,
            text=True,
        )
        lines = completed.stdout.strip().splitlines()
        assert len(lines) == 3
        results.append(lines)

    # The interpreter's randomized string hash differs, proving the two
    # processes really used different PYTHONHASHSEED settings.
    assert results[0][0] != results[1][0]
    # The project seed is independent of Python's hash randomization.
    assert results[0][1] == results[1][1] == results[0][2]
    assert results[0][1] == "a3f7d0599bc3deee189973f3e84a008efdeb6363bf317fc82ab174a2267399b5"
