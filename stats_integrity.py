"""Exact report-statistics helpers from owner-approved v2.3 Appendix E."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
from math import ceil, floor, log, sqrt
from typing import Iterable, Any

from scipy.stats import norm, t

import constants


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
    """Report whether the owner-approved Appendix E procedure is enabled."""
    approved = constants.TIME_UNIFORM_METHOD_APPROVED is True
    return {
        "approved": approved,
        "method_id": constants.TIME_UNIFORM_METHOD_ID,
        "status": "APPROVED" if approved else "K_SPEC / BLOCKED",
        "reason": None if approved else "No approved time-uniform inference method",
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





def mean_confidence_summary_at_n_and_half(
    values: Iterable[int],
    *,
    k: int,
    relative_tolerance: Fraction | None = None,
    absolute_tolerance: int | None = None,
) -> dict[str, Any]:
    """Require the sequential interval precision test at N and N/2."""
    items = list(values)
    if len(items) < 4:
        summary = mean_confidence_summary(
            items, k=k,
            relative_tolerance=relative_tolerance,
            absolute_tolerance=absolute_tolerance,
        )
        summary["half_n"] = None
        summary["stable_at_n"] = summary["stable"]
        summary["stable_at_half_n"] = None
        return summary
    full = mean_confidence_summary(
        items, k=k,
        relative_tolerance=relative_tolerance,
        absolute_tolerance=absolute_tolerance,
    )
    half_k = max(1, k - 1)
    half = mean_confidence_summary(
        items[: len(items) // 2],
        k=half_k,
        relative_tolerance=relative_tolerance,
        absolute_tolerance=absolute_tolerance,
    )
    full["half_n"] = {
        "n": half["n"],
        "spending_index": half["spending_index"],
        "alpha_s_k_numerator": half["alpha_s_k_numerator"],
        "alpha_s_k_denominator": half["alpha_s_k_denominator"],
        "mean": half["mean"],
        "mean_display": half["mean_display"],
        "mean_exact_numerator": half["mean_exact_numerator"],
        "mean_exact_denominator": half["mean_exact_denominator"],
        "half_ci_sequential": half["half_ci_sequential"],
        "limit": half["limit"],
        "stable": half["stable"],
    }
    full["stable_at_n"] = full["stable"]
    full["stable_at_half_n"] = half["stable"]
    full["stable"] = bool(full["stable"] and half["stable"])
    return full


def p50_relative_change_exceeds_guard(previous: Fraction, current: Fraction) -> bool:
    """Apply strict >5% exactly; fail closed when a nonzero change has zero denominator."""
    if not isinstance(previous, Fraction) or not isinstance(current, Fraction):
        raise TypeError("P50_GUARD_VALUES_MUST_BE_FRACTION")
    difference = abs(current - previous)
    if previous == 0:
        if current == 0:
            return False
        raise RuntimeError(
            "UNDEFINED_BUSINESS_RULE: P50_CHANGE_FROM_ZERO; clauses=2.5,14.11"
        )
    # Cross-multiplication encodes the strict >5% inequality without float division.
    return (
        difference * constants.STAT_P50_CHANGE_GUARD_DENOMINATOR
        > abs(previous) * constants.STAT_P50_CHANGE_GUARD_NUMERATOR
    )


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
    """Compute the owner-approved Appendix E indicator intervals at N and N/2."""
    items = sorted(list(results), key=lambda item: item.trial_id)
    if len(items) < 2:
        raise ValueError("STAT_SAMPLE_TOO_SMALL")
    statistical_checkpoint_index(len(items))  # fail closed unless N follows approved doubling.
    half_items = items[: len(items) // 2]
    half_index = max(1, k - 1)
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
        full = _rank_interval(
            (getattr(item, field) for item in items),
            q=quantile, k=k, metric_kind=kind,
        )
        half = (
            _rank_interval(
                (getattr(item, field) for item in half_items),
                q=quantile, k=half_index, metric_kind=kind,
            )
            if len(half_items) >= 2
            else None
        )
        indicators[name] = {
            "current_n": full,
            "half_n": half,
            "stable": bool(full["stable"] and (half is None or half["stable"])),
        }
    loss_full = _loss_probability_interval(
        (item.cumulative_project_profit < 0 for item in items), k=k
    )
    loss_half = (
        _loss_probability_interval(
            (item.cumulative_project_profit < 0 for item in half_items), k=half_index
        )
        if half_items
        else None
    )
    indicators["Probability_of_Accounting_Loss"] = {
        "current_n": loss_full,
        "half_n": loss_half,
        "stable": bool(loss_full["stable"] and (loss_half is None or loss_half["stable"])),
    }
    return {
        "method_id": constants.TIME_UNIFORM_METHOD_ID,
        "status": "APPROVED" if constants.TIME_UNIFORM_METHOD_APPROVED else "K_SPEC / BLOCKED",
        "interpretation": "APPROVED_VALID_TIME_INTERVALS" if constants.TIME_UNIFORM_METHOD_APPROVED else "CANDIDATE_DIAGNOSTIC_ONLY",
        "formal_acceptance_allowed": constants.TIME_UNIFORM_METHOD_APPROVED is True,
        "n": len(items),
        "spending_index": k,
        "alpha_s_k_numerator": sequential_alpha_fraction(k).numerator,
        "alpha_s_k_denominator": sequential_alpha_fraction(k).denominator,
        "indicators": indicators,
        "stable": constants.TIME_UNIFORM_METHOD_APPROVED is True
            and all(item["stable"] for item in indicators.values()),
    }
