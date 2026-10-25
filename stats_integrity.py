"""Exact report-statistics helpers from owner-approved v2.3 Appendix E."""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
from typing import Iterable, Any

import constants


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
