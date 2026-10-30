"""Exact report-statistics helpers implementing v2.3 §§2.5, 14.11.4, 14.12, and 21.3."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from functools import lru_cache
from fractions import Fraction
from math import ceil, floor, log, sqrt
from typing import Iterable, Any

from scipy.stats import norm, t
from dateutil.relativedelta import relativedelta

import constants



def resolve_n_unique_paths(scenario_id: str, rng_draw_counts: Iterable[int], unique_daily_paths: int) -> int:
    """Resolve N_unique_paths from the owner-approved daily-path contract.

    For the current S6 v2.3 cohort, N_unique_paths is the number of distinct
    complete daily paths persisted in the scenario artifact. The caller must
    verify SOURCE_SHA/cohort identity and the daily snapshot file digests before
    relying on this value. C100 remains a separate deterministic cohort.
    """
    counts = list(rng_draw_counts)
    if not scenario_id or not counts:
        raise ValueError("N_UNIQUE_PATHS_AUDIT_INPUT_EMPTY")
    if isinstance(unique_daily_paths, bool) or not isinstance(unique_daily_paths, int) or unique_daily_paths < 1:
        raise ValueError("N_UNIQUE_DAILY_PATHS_INVALID")
    if any(isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in counts):
        raise TypeError("RNG_DRAW_COUNT_MUST_BE_NONNEGATIVE_INTEGER")
    if scenario_id.startswith("C100_"):
        if any(value != 0 for value in counts) or unique_daily_paths != 1:
            raise RuntimeError("C100_DETERMINISTIC_PATH_CONTRACT_VIOLATION")
        return 1
    if unique_daily_paths > len(counts):
        raise RuntimeError("N_UNIQUE_DAILY_PATHS_EXCEEDS_TRIAL_COUNT")
    # Zero RNG draws are legal; checksum=0 and the uniqueness exemption are enforced
    # independently by validation.validate_rng_audit_records.
    # Under the owner-approved contract, N_unique_paths is counted from persisted
    # complete daily paths after the caller verifies source/cohort and file integrity.
    return unique_daily_paths


def validate_cumulative_trial_ids(trial_ids: Iterable[int], expected_n: int, *, scenario_id: str) -> list[int]:
    """Require the complete, duplicate-free cumulative trial sequence 1..N."""
    if isinstance(expected_n, bool) or not isinstance(expected_n, int) or expected_n < 1:
        raise ValueError("S6_EXPECTED_TRIAL_COUNT_INVALID")
    ids = list(trial_ids)
    if any(isinstance(value, bool) or not isinstance(value, int) for value in ids):
        raise TypeError(f"S6_TRIAL_ID_MUST_BE_INTEGER:{scenario_id}")
    if len(ids) != expected_n:
        raise RuntimeError(f"S6_TRIAL_ID_COUNT_MISMATCH:{scenario_id}:{len(ids)}:{expected_n}")
    if len(set(ids)) != len(ids):
        raise RuntimeError(f"S6_DUPLICATE_TRIAL_ID:{scenario_id}")
    if sorted(ids) != list(range(1, expected_n + 1)):
        raise RuntimeError(f"S6_TRIAL_ID_COVERAGE_MISMATCH:{scenario_id}")
    return sorted(ids)


def statistical_checkpoint_index(n: int) -> int:
    """Map approved N=300*2**(k-1) checkpoints to their 1-based spending index."""
    if not isinstance(n, int) or isinstance(n, bool) or n < 300 or n % 300:
        raise ValueError("STATISTICAL_CHECKPOINT_N_INVALID")
    ratio = n // 300
    if ratio & (ratio - 1):
        raise ValueError("STATISTICAL_CHECKPOINT_N_INVALID")
    return ratio.bit_length()


def sequential_alpha_fraction(k: int) -> Fraction:
    """alpha_s,k = 0.0025 / (k*(k+1)), represented exactly."""
    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise ValueError("SEQUENTIAL_ALPHA_INDEX_INVALID")
    return Fraction(
        constants.STAT_ALPHA_PER_SCENARIO_NUMERATOR,
        constants.STAT_ALPHA_PER_SCENARIO_DENOMINATOR * k * (k + 1),
    )


def cumulative_alpha_fraction(k: int) -> Fraction:
    """Exact sum of the first k telescoping alpha-spending allocations."""
    if not isinstance(k, int) or isinstance(k, bool) or k < 1:
        raise ValueError("SEQUENTIAL_ALPHA_INDEX_INVALID")
    return Fraction(k, k + 1) * Fraction(
        constants.STAT_ALPHA_PER_SCENARIO_NUMERATOR,
        constants.STAT_ALPHA_PER_SCENARIO_DENOMINATOR,
    )



@lru_cache(maxsize=1)
def compute_deterministic_support_bounds() -> dict[str, Any]:
    """Return a finite, conservative support envelope derived from v2.3 model constants.

    Expansion purchases are bounded by the one-purchase-per-day rule and the
    inclusive EXPANSION_CUTOFF_DATE. Contract length is bounded by the longest
    calendar duration of PRIMARY_CONTRACT_MONTHS over eligible purchase dates.
    The envelope reserves one bounded lifecycle slot per possible fleet member,
    plus a closure lifecycle, and uses worst-case per-bike daily flows. It is a
    conservative inference support envelope, not a simulation result.
    """
    start = constants.PROJECT_START_DATE
    cutoff = constants.EXPANSION_CUTOFF_DATE
    purchase_date_count = max(0, (cutoff - start).days + 1)
    max_fleet_size = constants.INITIAL_FLEET_SIZE + purchase_date_count

    longest_primary_contract_days = 0
    candidate = start
    while candidate <= cutoff:
        contract_end = candidate + relativedelta(
            months=constants.PRIMARY_CONTRACT_MONTHS
        )
        longest_primary_contract_days = max(
            longest_primary_contract_days, (contract_end - candidate).days
        )
        candidate += timedelta(days=1)

    maximum_claim_wait_days = max(
        constants.CLAIM_WAITING_PERIODS_DAYS.values(), default=0
    )
    settlement_calendar_days = constants.SETTLEMENT_PERIOD_DAYS * 2
    lifecycle_days = (
        constants.BIKE_PREP_SCHEDULE_DAYS
        + longest_primary_contract_days
        + maximum_claim_wait_days
        + settlement_calendar_days
    )
    bounded_lifecycle_slots = max_fleet_size + 1
    maximum_duration_days = lifecycle_days * bounded_lifecycle_slots
    maximum_close_date = cutoff + timedelta(days=maximum_duration_days)
    maximum_simulation_days = (maximum_close_date - start).days + 1

    maximum_daily_rent = max(
        constants.PRIMARY_DAILY_RENT,
        constants.SECONDARY_DAILY_RENT,
        constants.SETTLEMENT_DAILY_RENT,
    )
    maximum_daily_inflow = max_fleet_size * (
        maximum_daily_rent + constants.FRIDAY_FEE
    )
    # The second inflow factor conservatively reserves for recovery of
    # previously unpaid receivables without treating it as a new contract.
    maximum_cumulative_inflow = (
        maximum_simulation_days * maximum_daily_inflow * 2
    )
    maximum_acquisition_and_prep_cost = (
        max_fleet_size * constants.BIKE_TOTAL_CASH_FLOW_COST
    )
    maximum_daily_operating_cost = (
        constants.OIL_SERVICE_COST
        + constants.PREP_OPERATING_EXPENSE_PER_BIKE
    )
    maximum_operating_cost = (
        maximum_simulation_days
        * max_fleet_size
        * maximum_daily_operating_cost
    )
    maximum_gross_assets = max_fleet_size * constants.BIKE_GROSS_ASSET_COST
    maximum_abs_financial_value = (
        abs(constants.TOTAL_CAPITAL)
        + maximum_cumulative_inflow
        + maximum_acquisition_and_prep_cost
        + maximum_operating_cost
        + maximum_gross_assets
        + constants.OPENING_MARKETING_EXPENSE
        + constants.OPENING_PREP_EXPENSE
    )
    maximum_final_cash = constants.OPENING_CASH + maximum_cumulative_inflow
    maximum_event_count = max_fleet_size * maximum_simulation_days

    metric_bounds: dict[str, dict[str, int]] = {
        "final_net_project_equity": {
            "lower": -maximum_abs_financial_value,
            "upper": maximum_abs_financial_value,
        },
        "partner1_final_entitlement": {
            "lower": -maximum_abs_financial_value,
            "upper": maximum_abs_financial_value,
        },
        "partner2_final_entitlement": {
            "lower": -maximum_abs_financial_value,
            "upper": maximum_abs_financial_value,
        },
        "cumulative_project_profit": {
            "lower": -maximum_abs_financial_value,
            "upper": maximum_abs_financial_value,
        },
        "operating_net_profit": {
            "lower": -maximum_abs_financial_value,
            "upper": maximum_abs_financial_value,
        },
        "final_cash": {"lower": 0, "upper": maximum_final_cash},
        "termination_count": {"lower": 0, "upper": maximum_event_count},
        "secondary_cycle_count": {"lower": 0, "upper": maximum_event_count},
        "held_assets": {"lower": 0, "upper": max_fleet_size},
    }
    return {
        "bound_id": "V2.3_DETERMINISTIC_SUPPORT_ENVELOPE_V1",
        "finite": True,
        "purchase_date_count_upper_bound": purchase_date_count,
        "maximum_fleet_size": max_fleet_size,
        "longest_primary_contract_days": longest_primary_contract_days,
        "maximum_claim_wait_days": maximum_claim_wait_days,
        "settlement_calendar_days_upper_bound": settlement_calendar_days,
        "bounded_lifecycle_slots": bounded_lifecycle_slots,
        "maximum_duration_days": maximum_duration_days,
        "maximum_close_date": maximum_close_date.isoformat(),
        "maximum_simulation_days": maximum_simulation_days,
        "maximum_cumulative_inflow": maximum_cumulative_inflow,
        "maximum_abs_financial_value": maximum_abs_financial_value,
        "maximum_final_cash": maximum_final_cash,
        "maximum_event_count": maximum_event_count,
        "metric_bounds": metric_bounds,
        "note": (
            "Finite conservative envelope derived from the v2.3 constants and "
            "one-primary-lifecycle-per-bike execution contract; it is not an "
            "observed maximum and does not by itself certify scenario stability."
        ),
    }


def validate_values_within_deterministic_support(
    values: Iterable[int],
    metric_name: str,
) -> int:
    """Fail closed when integer observations exceed the approved finite envelope."""
    items = list(values)
    bounds = compute_deterministic_support_bounds()["metric_bounds"].get(metric_name)
    if bounds is None:
        raise ValueError(f"DETERMINISTIC_SUPPORT_METRIC_UNKNOWN:{metric_name}")
    for value in items:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("DETERMINISTIC_SUPPORT_REQUIRES_INTEGER_VALUES")
        if value < bounds["lower"] or value > bounds["upper"]:
            raise RuntimeError(
                f"STAT_OBSERVATION_OUTSIDE_DETERMINISTIC_SUPPORT:{metric_name}:{value}"
            )
    return len(items)


def mean_fraction(values: Iterable[int]) -> Fraction:
    items = list(values)
    if not items:
        raise ValueError("STAT_SAMPLE_EMPTY")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in items):
        raise TypeError("FINANCIAL_STATISTIC_REQUIRES_INTEGER_VALUES")
    return Fraction(sum(items), len(items))


def linear_quantile_fraction(values: Iterable[int], q: Fraction) -> Fraction:
    """Exact type-7/NumPy-linear quantile over integers, without float conversion."""
    items = sorted(values)
    if not items:
        raise ValueError("STAT_SAMPLE_EMPTY")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in items):
        raise TypeError("FINANCIAL_STATISTIC_REQUIRES_INTEGER_VALUES")
    if not isinstance(q, Fraction) or q < 0 or q > 1:
        raise ValueError("QUANTILE_MUST_BE_FRACTION_IN_0_1")
    position = (len(items) - 1) * q
    lower = position.numerator // position.denominator
    remainder = position - lower
    upper = min(lower + 1, len(items) - 1)
    return Fraction(items[lower]) * (1 - remainder) + Fraction(items[upper]) * remainder


def fraction_to_report_value(value: Fraction) -> int | Decimal:
    """Keep exact integers; round only nonintegers to 2 places, HALF_EVEN."""
    if not isinstance(value, Fraction):
        raise TypeError("FINANCIAL_STATISTIC_MUST_BE_FRACTION")
    if value.denominator == 1:
        return value.numerator
    with localcontext() as context:
        context.prec = constants.REPORT_DECIMAL_PRECISION
        decimal_value = Decimal(value.numerator) / Decimal(value.denominator)
        places = Decimal(1).scaleb(-constants.REPORT_DECIMAL_PLACES)
        return decimal_value.quantize(places, rounding=ROUND_HALF_EVEN)


def number_registry_entry(
    name: str,
    value: Fraction,
    *,
    source: str,
) -> dict[str, Any]:
    if not isinstance(value, Fraction):
        raise TypeError("NUMBER_REGISTRY_VALUE_MUST_BE_FRACTION")
    if not source:
        raise ValueError("NUMBER_REGISTRY_SOURCE_MISSING")
    display = fraction_to_report_value(value)
    return {
        "name": name,
        "exact_numerator": value.numerator,
        "exact_denominator": value.denominator,
        "display_value": str(display),
        "source": source,
        "rounding": "ROUND_HALF_EVEN" if value.denominator != 1 else "EXACT_INTEGER",
    }



def _fraction_to_decimal(value: Fraction) -> Decimal:
    with localcontext() as context:
        context.prec = constants.REPORT_DECIMAL_PRECISION
        return Decimal(value.numerator) / Decimal(value.denominator)


def time_uniform_inference_status() -> dict[str, Any]:
    """Report whether the v2.3 §14.11.4 alpha-spending procedure is enabled."""
    approved = constants.TIME_UNIFORM_METHOD_APPROVED is True
    support = compute_deterministic_support_bounds()
    return {
        "approved": approved,
        "method_id": constants.TIME_UNIFORM_METHOD_ID,
        "status": "APPROVED" if approved else "NOT_AUTHORIZED",
        "reason": None if approved else "No approved time-uniform inference method",
        "support_bounds_id": support["bound_id"],
        "finite_support_bounds": support["finite"],
        "maximum_close_date": support["maximum_close_date"],
    }


def mean_confidence_summary(
    values: Iterable[int],
    *,
    k: int,
    relative_tolerance: Fraction | None = None,
    absolute_tolerance: int | None = None,
) -> dict[str, Any]:
    """Exact mean and Decimal Student-t widths at alpha_s,k and descriptive 95%."""
    items = list(values)
    if len(items) < 2:
        raise ValueError("STAT_SAMPLE_TOO_SMALL")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in items):
        raise TypeError("FINANCIAL_STATISTIC_REQUIRES_INTEGER_VALUES")
    support = compute_deterministic_support_bounds()
    max_abs_support = support["maximum_abs_financial_value"]
    if any(abs(value) > max_abs_support for value in items):
        raise RuntimeError("STAT_OBSERVATION_OUTSIDE_DETERMINISTIC_SUPPORT:financial_mean")
    alpha_sk = sequential_alpha_fraction(k)
    mean = mean_fraction(items)
    variance = Fraction(
        sum((Fraction(value) - mean) ** 2 for value in items),
        len(items) - 1,
    )
    with localcontext() as context:
        context.prec = constants.REPORT_DECIMAL_PRECISION
        std = _fraction_to_decimal(variance).sqrt()
        n_decimal = Decimal(len(items)).sqrt()
        t_sequential = Decimal(str(t.isf(float(alpha_sk) / 2.0, len(items) - 1)))
        t_descriptive = Decimal(str(t.isf((1.0 - constants.CI_CONFIDENCE_LEVEL) / 2.0, len(items) - 1)))
        half_width_sequential = t_sequential * std / n_decimal
        half_width_95 = t_descriptive * std / n_decimal
        rel = relative_tolerance if relative_tolerance is not None else Fraction(
            constants.STAT_REL_TOL_NUMERATOR, constants.STAT_REL_TOL_DENOMINATOR
        )
        abs_tol = absolute_tolerance if absolute_tolerance is not None else constants.CI_ABSOLUTE_EPSILON
        limit_fraction = max(abs(mean) * rel, Fraction(abs_tol))
        limit = _fraction_to_decimal(limit_fraction)
        displayed = fraction_to_report_value(mean)
        return {
            "n": len(items),
            "spending_index": k,
            "alpha_s_k_numerator": alpha_sk.numerator,
            "alpha_s_k_denominator": alpha_sk.denominator,
            "mean": displayed if isinstance(displayed, int) else str(displayed),
            "mean_display": str(displayed),
            "mean_exact_numerator": mean.numerator,
            "mean_exact_denominator": mean.denominator,
            "sample_std": str(std),
            "t_critical_sequential": str(t_sequential),
            "half_ci_sequential": str(half_width_sequential),
            "half_ci_95_descriptive": str(half_width_95),
            "limit": str(limit),
            "stable": half_width_sequential < limit,
        }





def p50_relative_change_exceeds_guard(previous: Fraction, current: Fraction) -> bool:
    """Apply the owner's strict >5% P50 guard by exact cross-multiplication.

    The zero baseline is defined by the same inequality: 0 -> 0 is False;
    0 -> nonzero is True. No division or special undefined branch is needed.
    """
    if not isinstance(previous, Fraction) or not isinstance(current, Fraction):
        raise TypeError("P50_GUARD_VALUES_MUST_BE_FRACTION")
    difference = abs(current - previous)
    return (
        difference * constants.STAT_P50_CHANGE_GUARD_DENOMINATOR
        > abs(previous) * constants.STAT_P50_CHANGE_GUARD_NUMERATOR
    )


def evaluate_statistical_transition(
    previous_point: dict[str, Any],
    current_point: dict[str, Any],
) -> dict[str, Any]:
    """Fail-closed adjacent doubling evaluator with exact P50/loss-probability guards."""
    previous_n, current_n = previous_point.get("n"), current_point.get("n")
    if type(previous_n) is not int or type(current_n) is not int:
        raise TypeError("STATISTICAL_TRANSITION_N_MUST_BE_INTEGER")
    try:
        previous_k = statistical_checkpoint_index(previous_n)
        current_k = statistical_checkpoint_index(current_n)
    except ValueError as exc:
        raise ValueError("STATISTICAL_TRANSITION_N_NOT_APPROVED_CHECKPOINT") from exc
    if current_n != previous_n * constants.STATISTICAL_ESCALATION_MULTIPLIER:
        raise ValueError("STATISTICAL_TRANSITION_NOT_ADJACENT_DOUBLING")

    def exact_fraction(point: dict[str, Any], field: str) -> Fraction:
        value = point.get(field)
        if not isinstance(value, dict):
            raise ValueError(f"STATISTICAL_TRANSITION_EXACT_VALUE_MISSING:{field}")
        numerator, denominator = value.get("numerator"), value.get("denominator")
        if type(numerator) is not int or type(denominator) is not int or denominator <= 0:
            raise ValueError(f"STATISTICAL_TRANSITION_EXACT_VALUE_INVALID:{field}")
        return Fraction(numerator, denominator)

    def gate_pass(point: dict[str, Any], name: str) -> bool:
        gate = point.get(name)
        return isinstance(gate, dict) and gate.get("status") == "PASS" and gate.get("stable") is True

    ga_prev, ga_curr = gate_pass(previous_point, "gate_a"), gate_pass(current_point, "gate_a")
    gb_prev, gb_curr = gate_pass(previous_point, "gate_b"), gate_pass(current_point, "gate_b")
    p50_prev = exact_fraction(previous_point, "p50_cumulative_project_profit")
    p50_curr = exact_fraction(current_point, "p50_cumulative_project_profit")
    loss_prev = exact_fraction(previous_point, "probability_accounting_loss")
    loss_curr = exact_fraction(current_point, "probability_accounting_loss")
    p50_exceeded = p50_relative_change_exceeds_guard(p50_prev, p50_curr)
    loss_delta = abs(loss_curr - loss_prev)
    loss_tolerance = Fraction(constants.STAT_PROB_ABS_TOL_NUMERATOR, constants.STAT_PROB_ABS_TOL_DENOMINATOR)
    loss_pass = loss_delta < loss_tolerance

    if not (ga_prev and ga_curr):
        status = "BLOCKED_GATE_A"
    elif not (gb_prev and gb_curr):
        status = "FAIL_GATE_B"
    elif p50_exceeded:
        status = "CONTINUE_P50_GUARD"
    elif not loss_pass:
        status = "CONTINUE_LOSS_PROBABILITY_CHANGE"
    else:
        status = "PASS"
    return {
        "previous_n": previous_n, "current_n": current_n, "status": status,
        "passed": status == "PASS",
        "gate_a_previous_pass": ga_prev, "gate_a_current_pass": ga_curr,
        "gate_b_previous_pass": gb_prev, "gate_b_current_pass": gb_curr,
        "previous_p50_numerator": p50_prev.numerator, "previous_p50_denominator": p50_prev.denominator,
        "current_p50_numerator": p50_curr.numerator, "current_p50_denominator": p50_curr.denominator,
        "p50_relative_change_exceeds_guard": p50_exceeded,
        "loss_probability_abs_change_numerator": loss_delta.numerator,
        "loss_probability_abs_change_denominator": loss_delta.denominator,
        "loss_probability_change_tolerance_numerator": loss_tolerance.numerator,
        "loss_probability_change_tolerance_denominator": loss_tolerance.denominator,
        "loss_probability_change_pass": loss_pass,
    }


def _rank_interval(
    values: Iterable[int],
    *,
    q: Fraction,
    k: int,
    metric_kind: str,
) -> dict[str, Any]:
    items = sorted(values)
    if not items:
        raise ValueError("STAT_SAMPLE_EMPTY")
    if any(isinstance(value, bool) or not isinstance(value, int) for value in items):
        raise TypeError("FINANCIAL_STATISTIC_REQUIRES_INTEGER_VALUES")
    alpha_sk = sequential_alpha_fraction(k)
    n = len(items)
    z = float(norm.isf(float(alpha_sk) / 2.0))
    q_float = float(q)
    radius = z * sqrt(n * q_float * (1.0 - q_float))
    low_rank = max(1, min(n, floor(n * q_float - radius)))
    high_rank = max(1, min(n, ceil(n * q_float + radius)))
    estimate = linear_quantile_fraction(items, q)
    lower_value = items[low_rank - 1]
    upper_value = items[high_rank - 1]
    half_width = max(estimate - lower_value, Fraction(upper_value) - estimate)
    if metric_kind == "count":
        stable = upper_value - lower_value <= constants.STAT_COUNT_TOL
        tolerance = Fraction(constants.STAT_COUNT_TOL)
    else:
        tolerance = max(
            abs(estimate) * Fraction(
                constants.STAT_REL_TOL_NUMERATOR,
                constants.STAT_REL_TOL_DENOMINATOR,
            ),
            Fraction(constants.CI_ABSOLUTE_EPSILON),
        )
        stable = half_width < tolerance
    shown_estimate = fraction_to_report_value(estimate)
    return {
        "n": n,
        "spending_index": k,
        "alpha_s_k_numerator": alpha_sk.numerator,
        "alpha_s_k_denominator": alpha_sk.denominator,
        "estimate_display": str(shown_estimate),
        "estimate_exact_numerator": estimate.numerator,
        "estimate_exact_denominator": estimate.denominator,
        "lower_rank": low_rank,
        "upper_rank": high_rank,
        "lower_value": lower_value,
        "upper_value": upper_value,
        "half_width_numerator": half_width.numerator,
        "half_width_denominator": half_width.denominator,
        "half_width_display": str(fraction_to_report_value(half_width)),
        "tolerance_numerator": tolerance.numerator,
        "tolerance_denominator": tolerance.denominator,
        "stable": stable,
    }


def _loss_probability_interval(losses: Iterable[bool], *, k: int) -> dict[str, Any]:
    flags = list(losses)
    if not flags:
        raise ValueError("STAT_SAMPLE_EMPTY")
    if any(type(value) is not bool for value in flags):
        raise TypeError("LOSS_INDICATOR_MUST_BE_BOOLEAN")
    n = len(flags)
    loss_count = sum(flags)
    alpha_sk = sequential_alpha_fraction(k)
    alpha = float(alpha_sk)
    estimate = Fraction(loss_count, n)
    if loss_count == 0:
        lower = 0.0
        upper = min(1.0, -log(alpha) / n)
    else:
        z = float(norm.isf(alpha / 2.0))
        p_hat = loss_count / n
        z2 = z * z
        denominator = 1.0 + z2 / n
        center = (p_hat + z2 / (2.0 * n)) / denominator
        radius = z * sqrt(p_hat * (1.0 - p_hat) / n + z2 / (4.0 * n * n)) / denominator
        lower = max(0.0, center - radius)
        upper = min(1.0, center + radius)
    half_width = (upper - lower) / 2.0
    tolerance = constants.STAT_PROB_ABS_TOL_NUMERATOR / constants.STAT_PROB_ABS_TOL_DENOMINATOR
    return {
        "n": n,
        "spending_index": k,
        "alpha_s_k_numerator": alpha_sk.numerator,
        "alpha_s_k_denominator": alpha_sk.denominator,
        "loss_count": loss_count,
        "estimate_exact_numerator": estimate.numerator,
        "estimate_exact_denominator": estimate.denominator,
        "estimate_display": str(fraction_to_report_value(estimate)),
        "lower_bound": lower,
        "upper_bound": upper,
        "half_width": half_width,
        "descriptive_3_over_n": str(Fraction(3, n)),
        "stable": half_width < tolerance,
    }


def time_uniform_indicator_summary(results: Iterable[Any], *, k: int) -> dict[str, Any]:
    """Evaluate all seven §2.5 indicators at the current cumulative N_k only."""
    items = sorted(list(results), key=lambda item: item.trial_id)
    if len(items) < 2:
        raise ValueError("STAT_SAMPLE_TOO_SMALL")
    actual_k = statistical_checkpoint_index(len(items))
    if k != actual_k:
        raise ValueError("STATISTICAL_CHECKPOINT_INDEX_MISMATCH")
    indicators: dict[str, Any] = {}
    definitions = (
        ("P10_Cumulative_Project_Profit", "cumulative_project_profit", Fraction(1, 10), "money"),
        ("P50_Cumulative_Project_Profit", "cumulative_project_profit", Fraction(1, 2), "money"),
        ("P90_Cumulative_Project_Profit", "cumulative_project_profit", Fraction(9, 10), "money"),
        ("P90_Final_Cash", "final_cash", Fraction(9, 10), "money"),
        ("P90_Termination_Count", "termination_count", Fraction(9, 10), "count"),
        ("P90_Held_Assets", "held_assets", Fraction(9, 10), "count"),
    )
    for name, field, quantile, kind in definitions:
        summary = _rank_interval(
            (getattr(item, field) for item in items),
            q=quantile, k=k, metric_kind=kind,
        )
        indicators[name] = {**summary, "stable": bool(summary["stable"])}
    loss = _loss_probability_interval(
        (item.cumulative_project_profit < 0 for item in items), k=k
    )
    indicators["Probability_of_Accounting_Loss"] = {**loss, "stable": bool(loss["stable"])}
    alpha_sk = sequential_alpha_fraction(k)
    return {
        "method_id": constants.TIME_UNIFORM_METHOD_ID,
        "status": "APPROVED" if constants.TIME_UNIFORM_METHOD_APPROVED else "K_SPEC / BLOCKED",
        "interpretation": "APPROVED_VALID_TIME_INTERVALS" if constants.TIME_UNIFORM_METHOD_APPROVED else "CANDIDATE_DIAGNOSTIC_ONLY",
        "formal_acceptance_allowed": constants.TIME_UNIFORM_METHOD_APPROVED is True,
        "n": len(items),
        "spending_index": k,
        "alpha_s_k_numerator": alpha_sk.numerator,
        "alpha_s_k_denominator": alpha_sk.denominator,
        "indicators": indicators,
        "stable": constants.TIME_UNIFORM_METHOD_APPROVED is True
            and all(item["stable"] for item in indicators.values()),
    }


def evaluate_gate_b_statistical(
    mean_samples: dict[str, Iterable[int]],
    results: Iterable[Any],
    *,
    k: int,
) -> dict[str, Any]:
    """Intersection-union Gate B: all three financial means and seven indicators pass at N_k."""
    required_means = (
        "Final_Net_Project_Equity",
        "Partner1_Final_Entitlement",
        "Partner2_Final_Entitlement",
    )
    if set(mean_samples) != set(required_means):
        raise ValueError("GATE_B_MEAN_COMPONENT_SET_INVALID")
    summaries = {
        name: mean_confidence_summary(mean_samples[name], k=k)
        for name in required_means
    }
    n_values = {summary["n"] for summary in summaries.values()}
    if len(n_values) != 1:
        raise ValueError("GATE_B_MEAN_SAMPLE_SIZE_MISMATCH")
    n = next(iter(n_values))
    if statistical_checkpoint_index(n) != k:
        raise ValueError("STATISTICAL_CHECKPOINT_INDEX_MISMATCH")
    indicators = time_uniform_indicator_summary(results, k=k)
    all_components = (
        all(bool(item["stable"]) for item in summaries.values())
        and bool(indicators["stable"])
    )
    return {
        "status": "PASS" if all_components else "FAIL",
        "stable": all_components,
        "decision_framework": "IUT",
        "n": n,
        "spending_index": k,
        "alpha_s_k_numerator": sequential_alpha_fraction(k).numerator,
        "alpha_s_k_denominator": sequential_alpha_fraction(k).denominator,
        "financial_means": summaries,
        "indicators": indicators,
    }



def validate_daily_distribution_rows(
    rows: list[dict[str, Any]],
    *,
    scenario_id: str,
    source_sha: str,
    cohort_id: str,
    expected_dates: Iterable[str],
    expected_trial_count: int,
) -> dict[str, Any]:
    """Validate exact daily-distribution key coverage, identities, counts and rational values."""
    dates = list(expected_dates)
    if type(expected_trial_count) is not int or expected_trial_count < 1:
        raise RuntimeError("S6_DAILY_DISTRIBUTION_EXPECTED_TRIAL_COUNT_INVALID")
    if not dates or dates != sorted(set(dates)):
        raise RuntimeError("S6_DAILY_DISTRIBUTION_EXPECTED_DATES_INVALID")
    try:
        parsed = [date.fromisoformat(value) for value in dates]
    except (TypeError, ValueError) as exc:
        raise RuntimeError("S6_DAILY_DISTRIBUTION_EXPECTED_DATES_INVALID") from exc
    if any(value.isoformat() != text for value, text in zip(parsed, dates)):
        raise RuntimeError("S6_DAILY_DISTRIBUTION_EXPECTED_DATES_INVALID")
    if parsed != [parsed[0] + timedelta(days=i) for i in range((parsed[-1] - parsed[0]).days + 1)]:
        raise RuntimeError("S6_DAILY_DISTRIBUTION_DATE_GAP")
    modes = ("ACTIVE_ONLY", "ALL_TRIALS_CARRY_FORWARD")
    metrics = ("Cash", "Net_Equity", "Active_Bikes", "Owned_Transferred_Bikes", "Pending_Claims")
    quantiles = ("P10", "P25", "P50", "P75", "P90")
    expected_keys = {
        (day, mode, metric, quantile)
        for day in dates for mode in modes for metric in metrics for quantile in quantiles
    }
    seen: set[tuple[str, str, str, str]] = set()
    active_counts: dict[str, int] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise RuntimeError("S6_DAILY_DISTRIBUTION_ROW_INVALID")
        key = (row.get("date"), row.get("mode"), row.get("metric_name"), row.get("quantile_name"))
        if key in seen:
            raise RuntimeError(f"S6_DAILY_DISTRIBUTION_DUPLICATE_KEY:{key}")
        seen.add(key)
        if key not in expected_keys:
            raise RuntimeError(f"S6_DAILY_DISTRIBUTION_UNEXPECTED_KEY:{key}")
        if row.get("source_sha") != source_sha or row.get("cohort_id") != cohort_id or row.get("scenario_id") != scenario_id:
            raise RuntimeError("S6_DAILY_DISTRIBUTION_IDENTITY_MISMATCH")
        active = row.get("active_trial_count")
        sample = row.get("sample_trial_count")
        numerator = row.get("exact_numerator")
        denominator = row.get("exact_denominator")
        if type(active) is not int or not 0 <= active <= expected_trial_count:
            raise RuntimeError("S6_DAILY_DISTRIBUTION_ACTIVE_COUNT_INVALID")
        if row["date"] in active_counts and active_counts[row["date"]] != active:
            raise RuntimeError("S6_DAILY_DISTRIBUTION_ACTIVE_COUNT_INCONSISTENT")
        active_counts[row["date"]] = active
        if type(sample) is not int or sample < 1:
            raise RuntimeError("S6_DAILY_DISTRIBUTION_SAMPLE_COUNT_INVALID")
        expected_sample = active if row["mode"] == "ACTIVE_ONLY" else expected_trial_count
        if expected_sample < 1 or sample != expected_sample:
            raise RuntimeError("S6_DAILY_DISTRIBUTION_SAMPLE_COVERAGE_INVALID")
        if type(numerator) is not int or type(denominator) is not int or denominator < 1:
            raise RuntimeError("S6_DAILY_DISTRIBUTION_EXACT_VALUE_INVALID")
        exact = Fraction(numerator, denominator)
        if exact.numerator != numerator or exact.denominator != denominator:
            raise RuntimeError("S6_DAILY_DISTRIBUTION_EXACT_VALUE_NOT_REDUCED")
        if row.get("display_value") != str(fraction_to_report_value(exact)):
            raise RuntimeError("S6_DAILY_DISTRIBUTION_DISPLAY_VALUE_MISMATCH")
    if seen != expected_keys:
        missing = sorted(expected_keys - seen)
        raise RuntimeError(f"S6_DAILY_DISTRIBUTION_KEY_COVERAGE_MISMATCH:{len(missing)}")
    return {
        "status": "PASS_SCOPED_DAILY_DISTRIBUTION_SCHEMA_AND_COVERAGE",
        "date_count": len(dates),
        "rows_checked": len(rows),
        "expected_rows": len(expected_keys),
        "scenario_id": scenario_id,
        "source_sha": source_sha,
        "cohort_id": cohort_id,
    }
