"""Candidate time-uniform statistical procedures for Stage 7 acceptance.

This module is intentionally not wired into run_batch.py. Quantile intervals are
valid at the approved deterministic checkpoint grid using an explicit alpha
spending sequence. Bernoulli intervals invert a beta-binomial mixture
likelihood-ratio martingale and are time-uniform at every sample size. Production
acceptance still requires independent source-identity/completeness validation
and reviewed integration into the decision path.
"""
from __future__ import annotations

import math
from typing import Any, Sequence

import numpy as np
from scipy.optimize import brentq
from scipy.special import betaln
from scipy.stats import binom

import constants


QUANTILE_METHOD_ID = "ORDER_STATISTIC_ALPHA_SPENDING_GRID_V1"
BERNOULLI_METHOD_ID = "BETA_BINOMIAL_MIXTURE_CS_V1"


def _require_alpha(alpha: float) -> float:
    if isinstance(alpha, bool) or not isinstance(alpha, (int, float)):
        raise ValueError("alpha must be a finite number strictly between 0 and 1")
    alpha = float(alpha)
    if not math.isfinite(alpha) or not (0.0 < alpha < 1.0):
        raise ValueError("alpha must be a finite number strictly between 0 and 1")
    return alpha


def checkpoint_look_number(n: int) -> int:
    """Return 1-based look number on the approved 300, 600, 1200, ... grid."""
    if type(n) is not int or n < constants.STATISTICAL_CHECK_START_N:
        raise ValueError("N must be an integer on the approved statistical checkpoint grid")
    target = constants.STATISTICAL_CHECK_START_N
    multiplier = constants.STATISTICAL_ESCALATION_MULTIPLIER
    look = 1
    while target < n:
        target *= multiplier
        look += 1
    if target != n:
        raise ValueError("N must be an integer on the approved statistical checkpoint grid")
    return look


def checkpoint_alpha_spend(alpha: float, n: int) -> float:
    """Spend alpha_j = alpha / (j(j+1)); total spend over all looks is <= alpha."""
    alpha = _require_alpha(alpha)
    look = checkpoint_look_number(n)
    return alpha / (look * (look + 1))


def order_statistic_quantile_interval(
    values: Sequence[float],
    q: float,
    *,
    checkpoint_n: int,
    alpha: float,
) -> dict[str, Any]:
    """Distribution-free fixed-quantile interval at an approved checkpoint.

    The interval is simultaneous over the approved checkpoint sequence because
    each look uses alpha_j = alpha/(j(j+1)). It assumes values are the complete,
    identity-verified prefix of independent trial outcomes for this scenario.
    Lower/upper None means a finite order-statistic endpoint is unavailable and
    precision must fail closed.
    """
    alpha = _require_alpha(alpha)
    if isinstance(q, bool) or not isinstance(q, (int, float)):
        raise ValueError("q must be strictly between 0 and 1")
    q = float(q)
    if not math.isfinite(q) or not (0.0 < q < 1.0):
        raise ValueError("q must be strictly between 0 and 1")
    if type(checkpoint_n) is not int:
        raise ValueError("checkpoint_n must be an integer")
    look = checkpoint_look_number(checkpoint_n)
    arr = np.asarray(values, dtype=np.float64)
    if arr.ndim != 1 or arr.size != checkpoint_n:
        raise ValueError("values must be the complete prefix with size equal to checkpoint_n")
    if not np.isfinite(arr).all():
        raise ValueError("values must contain only finite numeric observations")

    per_look_alpha = alpha / (look * (look + 1))
    tail_alpha = per_look_alpha / 2.0
    ordered = np.sort(arr)
    lower_rank = int(binom.ppf(tail_alpha, checkpoint_n, q))
    upper_rank = int(binom.ppf(1.0 - tail_alpha, checkpoint_n, q)) + 1
    lower = float(ordered[lower_rank - 1]) if 1 <= lower_rank <= checkpoint_n else None
    upper = float(ordered[upper_rank - 1]) if 1 <= upper_rank <= checkpoint_n else None
    estimate = float(np.quantile(arr, q, method="linear"))
    return {
        "method": QUANTILE_METHOD_ID,
        "n": checkpoint_n,
        "look_number": look,
        "alpha_total": alpha,
        "alpha_at_look": per_look_alpha,
        "quantile": q,
        "estimate": estimate,
        "lower": lower,
        "upper": upper,
        "finite_interval": lower is not None and upper is not None,
    }


def quantile_precision_pass(interval: dict[str, Any], margin: float) -> bool:
    """Fail closed unless this is a complete finite interval from the candidate method."""
    if isinstance(margin, bool) or not isinstance(margin, (int, float)):
        raise ValueError("margin must be a finite positive number")
    margin = float(margin)
    if not math.isfinite(margin) or margin <= 0:
        raise ValueError("margin must be a finite positive number")
    if (
        interval.get("method") != QUANTILE_METHOD_ID
        or interval.get("finite_interval") is not True
    ):
        return False
    raw = (interval.get("estimate"), interval.get("lower"), interval.get("upper"))
    if any(
        value is None or isinstance(value, bool) or not isinstance(value, (int, float))
        for value in raw
    ):
        return False
    estimate, lower, upper = (float(value) for value in raw)
    if not all(math.isfinite(value) for value in (estimate, lower, upper)):
        return False
    if lower > estimate or estimate > upper:
        return False
    return max(estimate - lower, upper - estimate) < margin


def beta_binomial_mixture_confidence_sequence(
    successes: int,
    n: int,
    *,
    alpha: float,
    mixture_a: float = 1.0,
    mixture_b: float = 1.0,
) -> dict[str, Any]:
    """Invert a Beta-mixture likelihood-ratio martingale for a Bernoulli p.

    For each fixed p, M_n(p) is the beta-binomial marginal likelihood divided
    by the likelihood under p; Ville's inequality yields simultaneous coverage
    over all n at confidence level 1-alpha. The Beta(a,b) distribution defines
    the test-martingale mixture, not a modelling assumption about the unknown p.
    """
    alpha = _require_alpha(alpha)
    if type(n) is not int or n < 1:
        raise ValueError("n must be a positive integer")
    if type(successes) is not int or not (0 <= successes <= n):
        raise ValueError("successes must be an integer between 0 and n")
    for name, value in (("mixture_a", mixture_a), ("mixture_b", mixture_b)):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be finite and positive")
        if not math.isfinite(float(value)) or float(value) <= 0:
            raise ValueError(f"{name} must be finite and positive")
    a, b = float(mixture_a), float(mixture_b)
    s = successes
    log_marginal = float(betaln(s + a, n - s + b) - betaln(a, b))
    threshold = log_marginal + math.log(alpha)

    def log_likelihood(p: float) -> float:
        if p <= 0.0:
            return 0.0 if s == 0 else -math.inf
        if p >= 1.0:
            return 0.0 if s == n else -math.inf
        return s * math.log(p) + (n - s) * math.log1p(-p)

    mle = s / n
    maximum_log_likelihood = log_likelihood(mle)
    if maximum_log_likelihood < threshold:
        return {
            "method": BERNOULLI_METHOD_ID,
            "n": n,
            "successes": s,
            "estimate": mle,
            "lower": None,
            "upper": None,
            "alpha": alpha,
            "mixture_a": a,
            "mixture_b": b,
            "empty_confidence_set": True,
            "half_width": None,
        }

    if s == 0:
        lower, upper = 0.0, min(1.0, max(0.0, -math.expm1(threshold / n)))
    elif s == n:
        lower, upper = min(1.0, max(0.0, math.exp(threshold / n))), 1.0
    else:
        def root_function(p: float) -> float:
            return log_likelihood(p) - threshold

        lower_edge = float(np.finfo(np.float64).tiny)
        upper_edge = float(np.nextafter(1.0, 0.0))
        if root_function(lower_edge) >= 0.0:
            lower = 0.0
        else:
            lower = float(brentq(root_function, lower_edge, mle, xtol=1e-14, rtol=1e-14))
        if root_function(upper_edge) >= 0.0:
            upper = 1.0
        else:
            upper = float(brentq(root_function, mle, upper_edge, xtol=1e-14, rtol=1e-14))

    return {
        "method": BERNOULLI_METHOD_ID,
        "n": n,
        "successes": s,
        "estimate": mle,
        "lower": float(lower),
        "upper": float(upper),
        "alpha": alpha,
        "mixture_a": a,
        "mixture_b": b,
        "empty_confidence_set": False,
        "half_width": float((upper - lower) / 2.0),
    }


def bernoulli_precision_pass(interval: dict[str, Any], maximum_half_width: float) -> bool:
    """Fail closed unless bounds, estimate, method identity and reported width agree."""
    if isinstance(maximum_half_width, bool) or not isinstance(maximum_half_width, (int, float)):
        raise ValueError("maximum_half_width must be finite and positive")
    threshold = float(maximum_half_width)
    if not math.isfinite(threshold) or threshold <= 0:
        raise ValueError("maximum_half_width must be finite and positive")
    if (
        interval.get("method") != BERNOULLI_METHOD_ID
        or interval.get("empty_confidence_set") is not False
    ):
        return False
    n = interval.get("n")
    successes = interval.get("successes")
    if type(n) is not int or n < 1 or type(successes) is not int or not (0 <= successes <= n):
        return False
    raw = (
        interval.get("estimate"),
        interval.get("lower"),
        interval.get("upper"),
        interval.get("half_width"),
    )
    if any(
        value is None or isinstance(value, bool) or not isinstance(value, (int, float))
        for value in raw
    ):
        return False
    estimate, lower, upper, reported_half_width = (float(value) for value in raw)
    if not all(math.isfinite(value) for value in raw):
        return False
    if not (0.0 <= lower <= estimate <= upper <= 1.0):
        return False
    if not math.isclose(estimate, successes / n, rel_tol=1e-12, abs_tol=1e-15):
        return False
    computed_half_width = (upper - lower) / 2.0
    if not math.isclose(reported_half_width, computed_half_width, rel_tol=1e-10, abs_tol=1e-12):
        return False
    return computed_half_width < threshold


def adjacent_probability_change_pass(
    previous_estimate: float,
    current_estimate: float,
    maximum_absolute_change: float,
) -> bool:
    """Strictly enforce the adjacent checkpoint probability-change threshold."""
    values = (previous_estimate, current_estimate, maximum_absolute_change)
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
        raise ValueError("probability estimates and threshold must be finite numbers")
    previous, current, threshold = (float(value) for value in values)
    if not all(math.isfinite(value) for value in (previous, current, threshold)):
        raise ValueError("probability estimates and threshold must be finite numbers")
    if not (0.0 <= previous <= 1.0 and 0.0 <= current <= 1.0):
        raise ValueError("probability estimates must be between 0 and 1")
    if threshold <= 0:
        raise ValueError("maximum_absolute_change must be positive")
    return abs(current - previous) < threshold
