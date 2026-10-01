"""Authoritative deterministic constants for the motorcycle simulation.

Construction basis: the approved reference only, plus the user's approved
execution overrides. No prior implementation is copied into this file.

R4: every required name/interface was compared against main tests, the
stage3b-preserved diagnostic interface, and the reference before writing.
R6: every constant is classified as primitive (1), expressive derivation (2),
collection/dict (3), or operational key/name (4).
R7: every type-2 value is calculated in its own assignment expression, with no
imports or function calls from other project modules.
"""

from __future__ import annotations

from datetime import date
from typing import Dict, Final, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Chapter 2.1 — temporal constants
# ─────────────────────────────────────────────────────────────────────────────

# [R6-1][Ref 2.1] Beginning of the simulation.
PROJECT_START_DATE: Final[date] = date(2027, 1, 1)

# [R6-1][Ref 2.1] Founding-fleet purchase date, before simulation start.
INITIAL_FLEET_PURCHASE_DATE: Final[date] = date(2026, 12, 26)

# [R6-1][Ref 2.1] Literal reference value; dateutils handles the calendar rule.
INITIAL_FLEET_READY_DATE: Final[date] = date(2027, 1, 1)

# [R6-1][Ref 2.1] Literal reference value; delivery-day logic belongs in dateutils.py.
INITIAL_FLEET_DELIVERY_DATE: Final[date] = date(2027, 1, 2)

# [R6-1][Ref 2.1] Calendar days added to purchase date for scheduled readiness.
BIKE_PREP_SCHEDULE_DAYS: Final[int] = 6

# [R6-1][Ref 2.1] Primary contract duration, calculated with relativedelta elsewhere.
PRIMARY_CONTRACT_MONTHS: Final[int] = 24

# [R6-1][Ref 2.1] User/reference meaning: secondary contract is open-ended.
SECONDARY_CONTRACT_DURATION: Final[Optional[int]] = None

# [R6-1][Ref 2.1] Last day on which a new expansion purchase may begin.
EXPANSION_CUTOFF_DATE: Final[date] = date(2030, 12, 31)

# [R6-1][Ref 2.1] Dynamic close marker; there is intentionally no fixed close date.
FINAL_CLOSE_DATE: Final[Optional[date]] = None


# ─────────────────────────────────────────────────────────────────────────────
# Chapter 2.2 — financial and opening constants
# ─────────────────────────────────────────────────────────────────────────────

# [R6-1][Ref 2.2] Total project capital.
TOTAL_CAPITAL: Final[int] = 3_700_000

# [R6-1][Ref 2.2] Base purchase price of one motorcycle.
BIKE_BASE_PURCHASE_COST: Final[int] = 350_000

# [R6-1][Ref 2.2] Customs charge per motorcycle.
CUSTOMS_COST: Final[int] = 5_000

# [R6-1][Ref 2.2] Registration/plate/card charge per motorcycle.
REGISTRATION_COST: Final[int] = 5_000

# [R6-2][Ref 2.2] Derived from customs plus registration, not hard-coded.
CUSTOMS_AND_REGISTRATION_COST: Final[int] = CUSTOMS_COST + REGISTRATION_COST

# [R6-2][Ref 2.2] Gross motorcycle asset cost = base purchase + customs/registration.
BIKE_GROSS_ASSET_COST: Final[int] = BIKE_BASE_PURCHASE_COST + CUSTOMS_AND_REGISTRATION_COST

# [R6-1][Ref 2.2] Preparation oil/fuel expense per expansion motorcycle.
PREP_OIL_COST: Final[int] = 2_000

# [R6-1][Ref 2.2] Preparation lubricant/oil expense per expansion motorcycle.
PREP_LUBE_COST: Final[int] = 2_000

# [R6-2][Ref 2.2] Preparation expense = oil + lubricant.
PREP_OPERATING_EXPENSE_PER_BIKE: Final[int] = PREP_OIL_COST + PREP_LUBE_COST

# [R6-2][Ref 2.2] Full cash flow cost = purchase + customs/registration + preparation.
BIKE_TOTAL_CASH_FLOW_COST: Final[int] = (
    BIKE_BASE_PURCHASE_COST + CUSTOMS_AND_REGISTRATION_COST + PREP_OPERATING_EXPENSE_PER_BIKE
)

# [R6-1][Ref 2.2] Expansion-purchase eligibility threshold is base purchase price only.
EXPANSION_PURCHASE_CASH_THRESHOLD: Final[int] = 350_000

# [R6-2][Ref 2.2] Additional cash required after purchase = prep + customs/registration.
FULL_PREP_CASH_REQUIREMENT: Final[int] = (
    PREP_OPERATING_EXPENSE_PER_BIKE + CUSTOMS_AND_REGISTRATION_COST
)

# [R6-1][Ref 2.2] Primary daily rent on eligible business days.
PRIMARY_DAILY_RENT: Final[int] = 1_500

# [R6-1][Ref 2.2] Secondary daily rent on eligible business days.
SECONDARY_DAILY_RENT: Final[int] = 1_000

# [R6-1][Ref 2.2] Deterministic settlement-period rent on eligible business days.
SETTLEMENT_DAILY_RENT: Final[int] = 1_500

# [R6-1][Ref 2.2] Deterministic eligible-Friday fee.
FRIDAY_FEE: Final[int] = 1_000

# [R6-1][Ref 2.2] Periodic Friday oil-service expense.
OIL_SERVICE_COST: Final[int] = 2_000

# [R6-1][Ref 2.2] Daily depreciation rate per actual possession/use day.
DEPRECIATION_RATE_PER_DAY: Final[int] = 50

# [R6-2][Ref 2.2] Maximum depreciation equals the full gross motorcycle asset cost.
MAX_DEPRECIATION: Final[int] = BIKE_GROSS_ASSET_COST

# [R6-1][Ref 2.2] Final entitlement percentage for partner 1.
PARTNER1_FINAL_SHARE_PCT: Final[int] = 70

# [R6-1][Ref 2.2] Final entitlement percentage for partner 2.
PARTNER2_FINAL_SHARE_PCT: Final[int] = 30

# [R6-1][Ref 2.2] Founding fleet size.
INITIAL_FLEET_SIZE: Final[int] = 10

# [R6-1][Ref 2.2] Opening project cash.
OPENING_CASH: Final[int] = 0

# [R6-1][Ref 2.2] One-time pre-simulation marketing expense.
OPENING_MARKETING_EXPENSE: Final[int] = 60_000

# [R6-2][Ref 2.2] Ten founding motorcycles x preparation expense per motorcycle.
OPENING_PREP_EXPENSE: Final[int] = INITIAL_FLEET_SIZE * PREP_OPERATING_EXPENSE_PER_BIKE

# [R6-2][Ref 2.2] Opening retained loss is the negative of the two opening expenses.
OPENING_RETAINED_LOSS: Final[int] = -(
    OPENING_MARKETING_EXPENSE + OPENING_PREP_EXPENSE
)

# [R6-2][Ref 2.2] Ten founding motorcycles x gross asset cost.
OPENING_BIKE_ASSETS: Final[int] = INITIAL_FLEET_SIZE * BIKE_GROSS_ASSET_COST

# [R6-1][Ref 2.2] Opening memo allocation balance for partner 1.
OPENING_PARTNER1_REINVESTMENT_BALANCE: Final[int] = 0

# [R6-1][Ref 2.2] Opening memo allocation balance for partner 2.
OPENING_PARTNER2_REINVESTMENT_BALANCE: Final[int] = 0


# ─────────────────────────────────────────────────────────────────────────────
# Chapter 2.3 — default thresholds and settlement period
# ─────────────────────────────────────────────────────────────────────────────

# [R6-2][Ref 2.3] Thirty primary daily rents.
PRIMARY_DEFAULT_AMOUNT: Final[int] = 30 * PRIMARY_DAILY_RENT

# [R6-2][Ref 2.3] Ten secondary daily rents.
SECONDARY_DEFAULT_AMOUNT: Final[int] = 10 * SECONDARY_DAILY_RENT

# [R6-2][Ref 2.3] Twenty-one primary daily rents.
WAITING_PRIMARY_UPPER: Final[int] = 21 * PRIMARY_DAILY_RENT

# [R6-2][Ref 2.3] Twenty-eight primary daily rents.
NOTICE_PRIMARY_UPPER: Final[int] = 28 * PRIMARY_DAILY_RENT

# [R6-2][Ref 2.3] Grace upper bound equals the primary default threshold.
GRACE_PRIMARY_UPPER: Final[int] = PRIMARY_DEFAULT_AMOUNT

# [R6-1][Ref 2.3] Thirty business days, excluding Friday.
SETTLEMENT_PERIOD_DAYS: Final[int] = 30


# ─────────────────────────────────────────────────────────────────────────────
# Chapter 2.4 — guarantee waiting periods
# ─────────────────────────────────────────────────────────────────────────────

# [R6-1][Ref 2.4] Calendar-day waiting period for primary early termination.
PRIMARY_EARLY_TERMINATION_WAIT_DAYS: Final[int] = 30

# [R6-1][Ref 2.4] Calendar-day waiting period for secondary early termination.
SECONDARY_EARLY_TERMINATION_WAIT_DAYS: Final[int] = 20

# [R6-1][Ref 2.4] Calendar-day waiting period for failed post-maturity settlement.
POST_MATURITY_SETTLEMENT_FAILURE_WAIT_DAYS: Final[int] = 60

# [R6-1][Ref 2.4] Immediate settlement at administrative closure.
ADMINISTRATIVE_CLOSURE_WAIT_DAYS: Final[int] = 0

# [R6-1][Ref 2.4] Immediate final-closure settlement.
FINAL_CLOSURE_WAIT_DAYS: Final[int] = 0

# [R6-4][Ref 2.4] Operational claim-source key matching the ClaimSource/Excel vocabulary.
CLAIM_SOURCE_PRIMARY_EARLY_TERMINATION: Final[str] = "PRIMARY_EARLY_TERMINATION"

# [R6-4][Ref 2.4] Operational claim-source key matching the ClaimSource/Excel vocabulary.
CLAIM_SOURCE_SECONDARY_EARLY_TERMINATION: Final[str] = "SECONDARY_EARLY_TERMINATION"

# [R6-4][Ref 2.4] Operational claim-source key matching the ClaimSource/Excel vocabulary.
CLAIM_SOURCE_POST_MATURITY_SETTLEMENT_FAILURE: Final[str] = "POST_MATURITY_SETTLEMENT_FAILURE"

# [R6-4][Ref 2.4] Operational claim-source key matching the ClaimSource/Excel vocabulary.
CLAIM_SOURCE_ADMINISTRATIVE_CLOSURE: Final[str] = "ADMINISTRATIVE_CLOSURE"

# [R6-4][Ref 2.4] Operational claim-source key matching the ClaimSource/Excel vocabulary.
CLAIM_SOURCE_FINAL_CLOSURE: Final[str] = "FINAL_CLOSURE"

# [R6-3][Ref 2.4] Single source for source->waiting-period mapping; values derive from the five primitives above.
CLAIM_WAITING_PERIODS_DAYS: Final[Dict[str, int]] = {
    CLAIM_SOURCE_PRIMARY_EARLY_TERMINATION: PRIMARY_EARLY_TERMINATION_WAIT_DAYS,
    CLAIM_SOURCE_SECONDARY_EARLY_TERMINATION: SECONDARY_EARLY_TERMINATION_WAIT_DAYS,
    CLAIM_SOURCE_POST_MATURITY_SETTLEMENT_FAILURE: POST_MATURITY_SETTLEMENT_FAILURE_WAIT_DAYS,
    CLAIM_SOURCE_ADMINISTRATIVE_CLOSURE: ADMINISTRATIVE_CLOSURE_WAIT_DAYS,
    CLAIM_SOURCE_FINAL_CLOSURE: FINAL_CLOSURE_WAIT_DAYS,
}


# ─────────────────────────────────────────────────────────────────────────────
# Chapter 2.5 / 14 — RNG and scenario constants
# ─────────────────────────────────────────────────────────────────────────────

# [R6-1][Ref 2.5] Main deterministic RNG seed.
MASTER_SEED: Final[int] = 20270101

# [R6-3][Ref 2.5] Five collection-probability levels; this is a source collection for derived scenario structures.
COLLECTION_PROBABILITIES: Final[Tuple[float, ...]] = (1.00, 0.85, 0.70, 0.50, 0.30)

# [R6-3][Ref 2.5] Five integer guarantee-recovery percentages.
GUARANTEE_RECOVERY_RATES: Final[Tuple[int, ...]] = (100, 70, 50, 30, 0)

# [R6-2][Ref 2.5/14.1] Number of combinations is derived from the two source collections: 5 x 5.
MONTE_CARLO_SCENARIO_COUNT: Final[int] = len(COLLECTION_PROBABILITIES) * len(GUARANTEE_RECOVERY_RATES)

# [R6-1][Ref 2.5] One-riyal absolute stability tolerance for the near-zero branch.
ABSOLUTE_EPSILON: Final[int] = 1

# [R6-1][Ref 2.5] Small reference epsilon for near-zero relative comparisons.
REFERENCE_EPSILON: Final[float] = 1e-6

# [R6-1][Ref 2.5] Original reference Gate-(A) relative tolerance: <1% change.
REFERENCE_STABILITY_RELATIVE_TOLERANCE: Final[float] = 0.01

# [R6-1][User deviation from Ref 2.5/14.2] C100 starts at one trial; not the original 200.
C100_STATISTICAL_START_TRIALS: Final[int] = 1

# [R6-1][User deviation from Ref 2.5/14.2] All non-C100 collection levels start at 300 trials.
NON_C100_STATISTICAL_START_TRIALS: Final[int] = 300

# [R6-1][User deviation from Ref 2.5/14.2] Escalation is +50, not doubling.
ITERATION_ESCALATION_STEP: Final[int] = 50

# [R6-1][User decision] First CI checkpoint for non-C100 collections.
STATISTICAL_CHECK_START_N: Final[int] = 300

# [R6-1][User decision] CI checkpoints advance in increments of 50.
STATISTICAL_CHECK_STEP_N: Final[int] = 50

# [R6-1][User decision] Non-C100 cannot stop before completing n=400.
MINIMUM_STOP_N_FOR_NON_C100: Final[int] = 400

# [R6-1][User decision] Three consecutive checkpoints must satisfy stability gates.
STABILITY_CONSECUTIVE_CHECKS_REQUIRED: Final[int] = 3

# [R6-1][User decision] One initial smoke trial per scenario.
INITIAL_SMOKE_TRIALS_PER_SCENARIO: Final[int] = 1

# [R6-1][User decision] C100 has no confidence-interval gate at n=1.
C100_CI_GATE_ENABLED: Final[bool] = False

# [R6-1][User decision] One-riyal absolute epsilon for the CI near-zero protection.
CI_ABSOLUTE_EPSILON: Final[int] = 1

# [R6-1][User decision] Confidence level for the t-distribution CI gate.
CI_CONFIDENCE_LEVEL: Final[float] = 0.95

# [R6-1][User decision] Relative CI half-width threshold: <1% of |mean| when mean is not near zero.
CI_RELATIVE_TOLERANCE: Final[float] = 0.01

# [R6-4][User decision] Exact TrialResult/Excel field name for final project equity.
STABILITY_INDICATOR_FINAL_NET_EQUITY: Final[str] = "Final_Net_Project_Equity"

# [R6-4][User decision] Exact TrialResult/Excel field name for partner-1 final entitlement.
STABILITY_INDICATOR_P1: Final[str] = "Partner1_Final_Entitlement"

# [R6-4][User decision] Exact TrialResult/Excel field name for partner-2 final entitlement.
STABILITY_INDICATOR_P2: Final[str] = "Partner2_Final_Entitlement"

# [R6-3][Ref 2.5/Gate-(A)] Reference stability indicator names; includes Probability_of_Accounting_Loss exactly.
REFERENCE_STABILITY_INDICATORS: Final[Tuple[str, ...]] = (
    "P10_Cumulative_Project_Profit",
    "P50_Cumulative_Project_Profit",
    "P90_Cumulative_Project_Profit",
    "P90_Final_Cash",
    "Probability_of_Accounting_Loss",
    "P90_Termination_Count",
    "P90_Held_Assets",
)

# [R6-3][Ref 2.5/14.1] Derived immutable scenario IDs in the exact canonical naming format.
SCENARIO_IDS: Final[Tuple[str, ...]] = tuple(
    f"C{int(probability * 100):03d}_G{recovery_rate:03d}"
    for probability in COLLECTION_PROBABILITIES
    for recovery_rate in GUARANTEE_RECOVERY_RATES
)

# [R6-3][User decision] Execution start trials keyed only by the probability values from COLLECTION_PROBABILITIES.
# The keys must be looked up exclusively through COLLECTION_PROBABILITIES, and any external conversion
# (str/int) is required to pass through those probability values first.
STATISTICAL_START_TRIALS_BY_COLLECTION: Final[Dict[float, int]] = {
    1.00: C100_STATISTICAL_START_TRIALS,
    0.85: NON_C100_STATISTICAL_START_TRIALS,
    0.70: NON_C100_STATISTICAL_START_TRIALS,
    0.50: NON_C100_STATISTICAL_START_TRIALS,
    0.30: NON_C100_STATISTICAL_START_TRIALS,
}


# ─────────────────────────────────────────────────────────────────────────────
# Deterministic structural integrity checks for the constants layer only.
# These do not run the simulation.
# ─────────────────────────────────────────────────────────────────────────────

assert MONTE_CARLO_SCENARIO_COUNT == len(SCENARIO_IDS)
assert PARTNER1_FINAL_SHARE_PCT + PARTNER2_FINAL_SHARE_PCT == 100
assert BIKE_GROSS_ASSET_COST == BIKE_BASE_PURCHASE_COST + CUSTOMS_AND_REGISTRATION_COST
assert PREP_OPERATING_EXPENSE_PER_BIKE == PREP_OIL_COST + PREP_LUBE_COST
assert BIKE_TOTAL_CASH_FLOW_COST == (
    BIKE_BASE_PURCHASE_COST + CUSTOMS_AND_REGISTRATION_COST + PREP_OPERATING_EXPENSE_PER_BIKE
)
assert FULL_PREP_CASH_REQUIREMENT == PREP_OPERATING_EXPENSE_PER_BIKE + CUSTOMS_AND_REGISTRATION_COST
assert PRIMARY_DEFAULT_AMOUNT == 30 * PRIMARY_DAILY_RENT
assert SECONDARY_DEFAULT_AMOUNT == 10 * SECONDARY_DAILY_RENT
assert WAITING_PRIMARY_UPPER == 21 * PRIMARY_DAILY_RENT
assert NOTICE_PRIMARY_UPPER == 28 * PRIMARY_DAILY_RENT
assert GRACE_PRIMARY_UPPER == PRIMARY_DEFAULT_AMOUNT
assert MAX_DEPRECIATION == BIKE_GROSS_ASSET_COST
assert OPENING_PREP_EXPENSE == INITIAL_FLEET_SIZE * PREP_OPERATING_EXPENSE_PER_BIKE
assert OPENING_RETAINED_LOSS == -(OPENING_MARKETING_EXPENSE + OPENING_PREP_EXPENSE)
assert OPENING_BIKE_ASSETS == INITIAL_FLEET_SIZE * BIKE_GROSS_ASSET_COST
assert TOTAL_CAPITAL - OPENING_BIKE_ASSETS + OPENING_RETAINED_LOSS == OPENING_CASH
