"""Chapter 2 — authoritative deterministic constants.

Built from the final reference only.
No execution logic belongs in this module.
"""
from __future__ import annotations

from datetime import date
from typing import Final


# 2.1 Time constants
PROJECT_START_DATE: Final[date] = date(2027, 1, 1)
INITIAL_FLEET_PURCHASE_DATE: Final[date] = date(2026, 12, 26)
INITIAL_FLEET_READY_DATE: Final[date] = date(2027, 1, 1)
INITIAL_FLEET_DELIVERY_DATE: Final[date] = date(2027, 1, 2)
BIKE_PREP_SCHEDULE_DAYS: Final[int] = 6
PRIMARY_CONTRACT_MONTHS: Final[int] = 24
SECONDARY_CONTRACT_DURATION = None  # Open-ended; no fixed duration.
EXPANSION_CUTOFF_DATE: Final[date] = date(2030, 12, 31)


# 2.2 Financial/opening constants (Yemeni riyals)
TOTAL_CAPITAL: Final[int] = 3_700_000
BIKE_BASE_PURCHASE_COST: Final[int] = 350_000
CUSTOMS_COST: Final[int] = 5_000
REGISTRATION_COST: Final[int] = 5_000
CUSTOMS_AND_REGISTRATION_COST: Final[int] = 10_000
BIKE_GROSS_ASSET_COST: Final[int] = 360_000
PREP_OIL_COST: Final[int] = 2_000
PREP_LUBE_COST: Final[int] = 2_000
PREP_OPERATING_EXPENSE_PER_BIKE: Final[int] = 4_000
BIKE_FULL_CASH_FLOW_COST: Final[int] = 364_000
EXPANSION_PURCHASE_CASH_THRESHOLD: Final[int] = 350_000
FULL_PREP_CASH_REQUIREMENT: Final[int] = 14_000
PRIMARY_DAILY_RENT: Final[int] = 1_500
SECONDARY_DAILY_RENT: Final[int] = 1_000
SETTLEMENT_DAILY_RENT: Final[int] = 1_500
FRIDAY_FEE: Final[int] = 1_000
OIL_SERVICE_COST: Final[int] = 2_000
DEPRECIATION_RATE_PER_DAY: Final[int] = 50
MAX_DEPRECIATION: Final[int] = 360_000
PARTNER1_FINAL_SHARE_PCT: Final[int] = 70
PARTNER2_FINAL_SHARE_PCT: Final[int] = 30
OPENING_CASH: Final[int] = 0
OPENING_MARKETING_EXPENSE: Final[int] = 60_000
INITIAL_FLEET_SIZE: Final[int] = 10
OPENING_PREP_EXPENSE: Final[int] = 40_000
OPENING_RETAINED_LOSS: Final[int] = -100_000
OPENING_BIKE_ASSETS: Final[int] = 3_600_000
OPENING_PARTNER1_REINVESTMENT_BALANCE: Final[int] = 0
OPENING_PARTNER2_REINVESTMENT_BALANCE: Final[int] = 0


# 2.3 Default/termination/state-classification constants
PRIMARY_DEFAULT_AMOUNT: Final[int] = 45_000
SECONDARY_DEFAULT_AMOUNT: Final[int] = 10_000
WAITING_PRIMARY_UPPER: Final[int] = 31_500
NOTICE_PRIMARY_UPPER: Final[int] = 42_000
GRACE_PRIMARY_UPPER: Final[int] = 45_000
SETTLEMENT_PERIOD_DAYS: Final[int] = 30


# 2.4 Guarantee waiting periods — calendar days
CLAIM_WAITING_PERIODS_DAYS: Final[dict[str, int]] = {
    "PRIMARY_EARLY_TERMINATION": 30,
    "SECONDARY_EARLY_TERMINATION": 20,
    "POST_MATURITY_SETTLEMENT_FAILURE": 60,
    "ADMINISTRATIVE_CLOSURE": 0,
    "FINAL_CLOSURE": 0,
}


# 2.5 Monte Carlo/RNG constants
MASTER_SEED: Final[int] = 20_270_101
COLLECTION_PROBABILITIES: Final[tuple[float, ...]] = (1.00, 0.85, 0.70, 0.50, 0.30)
GUARANTEE_RECOVERY_RATES: Final[tuple[int, ...]] = (100, 70, 50, 30, 0)
SCENARIO_COUNT: Final[int] = 25

# The reference defines these as mathematical configuration for later Monte Carlo
# stages. They are constants only; no trial loop is implemented here.
ABSOLUTE_EPSILON: Final[float] = 1.0
REFERENCE_EPSILON: Final[float] = 1e-6


# Structural invariants stated explicitly by the reference.
assert CUSTOMS_COST + REGISTRATION_COST == CUSTOMS_AND_REGISTRATION_COST
assert BIKE_BASE_PURCHASE_COST + CUSTOMS_AND_REGISTRATION_COST == BIKE_GROSS_ASSET_COST
assert BIKE_GROSS_ASSET_COST + PREP_OPERATING_EXPENSE_PER_BIKE == BIKE_FULL_CASH_FLOW_COST
assert PREP_OIL_COST + PREP_LUBE_COST == PREP_OPERATING_EXPENSE_PER_BIKE
assert (
    OPENING_BIKE_ASSETS
    == INITIAL_FLEET_SIZE * BIKE_GROSS_ASSET_COST
)
assert TOTAL_CAPITAL + OPENING_RETAINED_LOSS == OPENING_BIKE_ASSETS
assert PARTNER1_FINAL_SHARE_PCT + PARTNER2_FINAL_SHARE_PCT == 100
assert all(rate in (100, 70, 50, 30, 0) for rate in GUARANTEE_RECOVERY_RATES)
assert all(0.0 <= p <= 1.0 for p in COLLECTION_PROBABILITIES)
assert len(COLLECTION_PROBABILITIES) * len(GUARANTEE_RECOVERY_RATES) == SCENARIO_COUNT
