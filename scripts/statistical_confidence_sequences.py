"""Candidate time-uniform confidence sequences for Stage 7 reference indicators.

The fixed-quantile order-statistic construction follows Howard & Ramdas,
"Sequential estimation of quantiles with applications to A/B-testing and
best-arm identification" (arXiv:1906.09712) and the beta-binomial mixture
bound implementation described by the ConfSeq project
(https://github.com/gostevehoward/confseq, MIT-licensed reference software).

This module intentionally does not mark the production statistical gate
accepted: financial-mean time-uniform inference and independent acceptance
of the full procedure remain unresolved.
"""
from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

import numpy as np
from scipy.special import betaln


METHOD_VERSION = "HOWARD_RAMDAS_FIXED_QUANTILE_BETA_BINOMIAL_CANDIDATE_V1"
BERNOULLI_METHOD_VERSION = "BETA_BINOMIAL_MIXTURE_BERNOULLI_CS_CANDIDATE_V1"

DEFAULT_ALPHA = 0.0025
DEFAULT_ALPHA_OPT = 0.05
DEFAULT_T_OPT = 300
LOSS_HALF_WIDTH_LIMIT = 0.005
LOSS_ADJACENT_CHANGE_LIMIT = 0.005

QUANTILE_INDICATORS = {
    "P10_Cumulative_Project_Profit": ("cumulative_project_profit", 0.10, 18_500.0),
    "P50_Cumulative_Project_Profit": ("cumulative_project_profit", 0.50, 18_500.0),
    "P90_Cumulative_Project_Profit": ("cumulative_project_profit", 0.90, 18_500.0),
    "P90_Final_Cash": ("final_cash", 0.90, 18_500.0),
    "P90_Termination_Count": ("termination_count", 0.90, 1.0),
    "P90_Held_Assets": ("held_assets", 0.90, 1.0),
}


def _check_alpha(alpha: float, name: str = "alpha") -> None:
    if not isinstance(alpha, (int, float)) or isinstance(alpha, bool) or not 0 < alpha < 1:
        raise ValueError(f"{name} must be in (0, 1)")


def _check_tuning(t_opt: int, alpha_opt: float) -> None:
    if type(t_opt) is not int or t_opt < 1:
        raise ValueError("t_opt must be a positive integer")
    _check_alpha(alpha_opt, "alpha_opt")


def _beta_binomial_log_mixture(
    s: float,
    v: float,
    *,
    v_opt: float,
    g: float,
    h: float,
    alpha_opt: float = DEFAULT_ALPHA_OPT,
) -> float:
    """Two-sided beta-binomial mixture log supermartingale from ConfSeq.

    The parameters follow the published/reference implementation, including
    its tuning rule; this avoids substituting an arbitrary prior or an
    asymptotic approximation for the reviewed candidate.
    """
    _check_alpha(alpha_opt, "alpha_opt")
    if not all(math.isfinite(x) for x in (s, v, v_opt, g, h)):
        raise ValueError("mixture inputs must be finite")
    if v < 0 or v_opt <= 0 or g <= 0 or h <= 0:
        raise ValueError("mixture variance must be non-negative and tuning parameters positive")
    total = g + h
    rho = v_opt / (
        2.0 * math.log(1.0 / alpha_opt)
        + math.log(1.0 + 2.0 * math.log(1.0 / alpha_opt))
    )
    r = max(rho - g * h, 1e-3 * g * h)
    normalizer = float(betaln(r / (g * total), r / (h * total)))
    a = (r + v - g * s) / (g * total)
    b = (r + v + h * s) / (h * total)
    if a <= 0 or b <= 0:
        raise ValueError("mixture beta shape became non-positive")
    return (
        v / (g * h) * math.log(total)
        - ((v + h * s) / (h * total)) * math.log(g)
        - ((v - g * s) / (g * total)) * math.log(h)
        + float(betaln(a, b))
        - normalizer
    )


def _bisect_root(function, left: float, right: float, *, iterations: int = 80) -> float:
    if not (math.isfinite(left) and math.isfinite(right) and left < right):
        raise ValueError("invalid root interval")
    f_left = function(left)
    f_right = function(right)
    if f_left == 0:
        return left
    if f_right == 0:
        return right
    if not math.isfinite(f_left) or not math.isfinite(f_right) or f_left * f_right > 0:
        raise RuntimeError(
            f"confidence-sequence root not bracketed: f(left)={f_left}, f(right)={f_right}"
        )
    for _ in range(iterations):
        mid = (left + right) / 2.0
        f_mid = function(mid)
        if not math.isfinite(f_mid):
            raise RuntimeError("non-finite confidence-sequence root function")
        if f_mid == 0:
            return mid
        if (f_left < 0) == (f_mid < 0):
            left, f_left = mid, f_mid
        else:
            right, f_right = mid, f_mid
    return (left + right) / 2.0


def _beta_binomial_mixture_boundary(
    v: float,
    alpha: float,
    *,
    v_opt: float,
    g: float,
    h: float,
    alpha_opt: float = DEFAULT_ALPHA_OPT,
) -> float:
    """Find the nonnegative mixture boundary s at crossing threshold 1/alpha."""
    _check_alpha(alpha)
    if v <= 0:
        raise ValueError("v must be positive for a quantile boundary")
    upper = v / g
    threshold = math.log(1.0 / alpha)

    def objective(s: float) -> float:
        return _beta_binomial_log_mixture(
            s, v, v_opt=v_opt, g=g, h=h, alpha_opt=alpha_opt
        ) - threshold

    f0 = objective(0.0)
    f_upper = objective(upper)
    if f0 >= 0:
        # The conservative response is to avoid a narrow, unsupported interval.
        raise RuntimeError("quantile mixture boundary is already crossed at s=0")
    if f_upper < 0:
        return upper
    return _bisect_root(objective, 0.0, upper)


def fixed_quantile_confidence_sequence(
    values: Sequence[float],
    p: float,
    *,
    alpha: float = DEFAULT_ALPHA,
    t_opt: int = DEFAULT_T_OPT,
    alpha_opt: float = DEFAULT_ALPHA_OPT,
) -> dict[str, Any]:
    """Return an order-statistic CS for one fixed population quantile.

    The point estimate remains NumPy's linear sample quantile. The CS itself
    is rank/order-statistic based and handles discrete ties without interpolation.
    """
    _check_alpha(alpha)
    _check_tuning(t_opt, alpha_opt)
    if not isinstance(p, (int, float)) or isinstance(p, bool) or not 0 < p < 1:
        raise ValueError("p must be in (0, 1)")
    arr = np.asarray(values, dtype=np.float64)
    if arr.ndim != 1 or arr.size == 0 or not np.isfinite(arr).all():
        raise ValueError("values must be a non-empty one-dimensional finite sample")
    n = int(arr.size)
    sorted_values = np.sort(arr)
    point = float(np.quantile(arr, float(p), method="linear"))
    v = p * (1.0 - p) * n
    v_opt = p * (1.0 - p) * t_opt
    lower_boundary = _beta_binomial_mixture_boundary(
        v, alpha, v_opt=v_opt, g=1.0 - p, h=p, alpha_opt=alpha_opt
    )
    upper_boundary = _beta_binomial_mixture_boundary(
        v, alpha, v_opt=v_opt, g=p, h=1.0 - p, alpha_opt=alpha_opt
    )
    lower_radius = lower_boundary / n
    upper_radius = upper_boundary / n

    lower_index = math.floor(n * (p - lower_radius) + 1.0)
    upper_index = math.ceil(n * (p + upper_radius))
    if lower_index < 1:
        lower = -math.inf
    elif lower_index > n:
        lower = -math.inf
    else:
        lower = float(sorted_values[lower_index - 1])
    if upper_index < 1:
        upper = math.inf
    elif upper_index > n:
        upper = math.inf
    else:
        upper = float(sorted_values[upper_index - 1])

    return {
        "method": METHOD_VERSION,
        "n": n,
        "p": float(p),
        "alpha": float(alpha),
        "t_opt": t_opt,
        "point_estimate": point,
        "lower": lower,
        "upper": upper,
        "lower_probability_radius": float(lower_radius),
        "upper_probability_radius": float(upper_radius),
        "margin": None,
    }


def bernoulli_mean_confidence_sequence(
    successes: int,
    n: int,
    *,
    alpha: float = DEFAULT_ALPHA,
    t_opt: int = DEFAULT_T_OPT,
    alpha_opt: float = DEFAULT_ALPHA_OPT,
) -> dict[str, Any]:
    """Time-uniform CS for a Bernoulli mean via the reviewed beta-mixture test.

    This is a martingale/e-process inversion for Bernoulli outcomes, not a
    Clopper-Pearson or pointwise-Wilson interval. It is applicable here only
    because the loss indicator is binary and its definition is fixed.
    """
    _check_alpha(alpha)
    _check_tuning(t_opt, alpha_opt)
    if type(n) is not int or n < 1:
        raise ValueError("n must be a positive integer")
    if type(successes) is not int or not 0 <= successes <= n:
        raise ValueError("successes must be an integer between 0 and n")
    empirical = successes / n
    threshold = math.log(1.0 / alpha)

    def objective(p: float, zero_value: float, one_value: float) -> float:
        if p <= 0:
            return zero_value
        if p >= 1:
            return one_value
        v = p * (1.0 - p) * n
        v_opt = p * (1.0 - p) * t_opt
        s = (empirical - p) * n
        return _beta_binomial_log_mixture(
            s, v, v_opt=v_opt, g=p, h=1.0 - p, alpha_opt=alpha_opt
        ) - threshold

    if empirical > 0:
        lower = _bisect_root(
            lambda p: objective(p, 1.0, -1.0), 0.0, empirical
        )
    else:
        lower = 0.0
    if empirical < 1:
        upper = _bisect_root(
            lambda p: objective(p, -1.0, 1.0), empirical, 1.0
        )
    else:
        upper = 1.0

    lower = max(0.0, min(float(lower), empirical))
    upper = min(1.0, max(float(upper), empirical))
    half_width = max(empirical - lower, upper - empirical)
    return {
        "method": BERNOULLI_METHOD_VERSION,
        "n": n,
        "successes": successes,
        "alpha": float(alpha),
        "t_opt": t_opt,
        "point_estimate": float(empirical),
        "lower": float(lower),
        "upper": float(upper),
        "half_width": float(half_width),
        "precision_limit": LOSS_HALF_WIDTH_LIMIT,
        "precision_pass": bool(half_width < LOSS_HALF_WIDTH_LIMIT),
    }


def evaluate_reference_indicators(
    results: Sequence[Any],
    *,
    alpha: float = DEFAULT_ALPHA,
    t_opt: int = DEFAULT_T_OPT,
    alpha_opt: float = DEFAULT_ALPHA_OPT,
    previous: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate all seven §2.5 indicator CIs without asserting final acceptance."""
    if not results:
        raise ValueError("at least one TrialResult is required")
    _check_alpha(alpha)
    _check_tuning(t_opt, alpha_opt)
    n = len(results)
    indicators: dict[str, dict[str, Any]] = {}
    for name, (attribute, p, margin) in QUANTILE_INDICATORS.items():
        sample = [getattr(result, attribute) for result in results]
        ci = fixed_quantile_confidence_sequence(
            sample, p, alpha=alpha, t_opt=t_opt, alpha_opt=alpha_opt
        )
        point = ci["point_estimate"]
        precision_pass = bool(
            ci["lower"] >= point - margin and ci["upper"] <= point + margin
        )
        indicators[name] = {
            **ci,
            "margin": margin,
            "precision_pass": precision_pass,
            "status": "CANDIDATE_PASS" if precision_pass else "CANDIDATE_FAIL",
        }

    losses = sum(int(getattr(result, "cumulative_project_profit") < 0) for result in results)
    loss_cs = bernoulli_mean_confidence_sequence(
        losses, n, alpha=alpha, t_opt=t_opt, alpha_opt=alpha_opt
    )
    previous_loss_estimate = None
    adjacent_change = None
    adjacent_change_pass = None
    if previous is not None:
        prior_indicators = previous.get("indicators")
        prior_loss = (
            prior_indicators.get("Probability_of_Accounting_Loss")
            if isinstance(prior_indicators, Mapping) else None
        )
        if isinstance(prior_loss, Mapping) and isinstance(prior_loss.get("point_estimate"), (int, float)):
            previous_loss_estimate = float(prior_loss["point_estimate"])
            adjacent_change = abs(loss_cs["point_estimate"] - previous_loss_estimate)
            adjacent_change_pass = bool(adjacent_change < LOSS_ADJACENT_CHANGE_LIMIT)

    loss_cs.update({
        "margin": LOSS_HALF_WIDTH_LIMIT,
        "adjacent_change_limit": LOSS_ADJACENT_CHANGE_LIMIT,
        "previous_point_estimate": previous_loss_estimate,
        "adjacent_absolute_change": adjacent_change,
        "adjacent_change_pass": adjacent_change_pass,
        "status": (
            "CANDIDATE_PASS" if loss_cs["precision_pass"] else "CANDIDATE_FAIL"
        ),
    })
    indicators["Probability_of_Accounting_Loss"] = loss_cs

    all_precision = all(item.get("precision_pass") is True for item in indicators.values())
    return {
        "schema_version": "stage7-reference-indicator-cs-v1",
        "method": METHOD_VERSION,
        "n": n,
        "alpha_per_scenario": float(alpha),
        "quantile_alpha_opt": float(alpha_opt),
        "t_opt": t_opt,
        "indicators": indicators,
        "point_precision_pass": bool(all_precision),
        "acceptance_status": "CANDIDATE_ONLY_NOT_ACCEPTED",
        "blockers": [
            "FINANCIAL_MEAN_TIME_UNIFORM_CS_NOT_IMPLEMENTED_OR_ACCEPTED",
            "GATE_A_PRODUCTION_GOLDEN_PROVIDER_NOT_CONNECTED_TO_THIS_SOURCE_HEAD",
            "CANDIDATE_METHODS_REQUIRE_INDEPENDENT_ACCEPTANCE",
        ],
    }


def _point_components_accepted(point: Mapping[str, Any]) -> bool:
    inference = point.get("statistical_inference")
    gate_a = point.get("gate_a")
    gate_b = point.get("gate_b")
    indicators = point.get("reference_indicators")
    return bool(
        isinstance(inference, Mapping)
        and inference.get("status") == "ACCEPTED"
        and isinstance(gate_a, Mapping)
        and gate_a.get("status") == "PASS"
        and isinstance(gate_b, Mapping)
        and gate_b.get("status") == "ACCEPTED_TIME_UNIFORM_CS"
        and gate_b.get("stable") is True
        and isinstance(indicators, Mapping)
        and indicators.get("acceptance_status") == "ACCEPTED"
        and indicators.get("point_precision_pass") is True
    )


def evaluate_adjacent_transition(
    previous: Mapping[str, Any] | None,
    current: Mapping[str, Any],
) -> dict[str, Any]:
    """Record one adjacent checkpoint transition; no pointwise shortcut to PASS."""
    current_n = current.get("n")
    previous_n = previous.get("n") if isinstance(previous, Mapping) else None
    base = {
        "previous_n": previous_n,
        "current_n": current_n,
        "status": "BLOCKED",
        "p50_continuation_trigger": False,
        "minimum_required_n": 400,
        "blockers": [],
    }
    if not isinstance(previous, Mapping):
        return {**base, "status": "NOT_APPLICABLE", "blockers": ["NO_PREVIOUS_CHECKPOINT"]}
    if type(previous_n) is not int or type(current_n) is not int or current_n != previous_n * 2:
        return {**base, "blockers": ["CHECKPOINTS_NOT_ADJACENT_UNDER_DOUBLING_POLICY"]}

    prev_refs = previous.get("reference_indicators")
    curr_refs = current.get("reference_indicators")
    try:
        old_p50 = float(prev_refs["indicators"]["P50_Cumulative_Project_Profit"]["point_estimate"])
        new_p50 = float(curr_refs["indicators"]["P50_Cumulative_Project_Profit"]["point_estimate"])
    except (TypeError, KeyError, ValueError):
        old_p50 = new_p50 = math.nan
    p50_trigger = False
    p50_relative_change = None
    if current_n in (600, 1200) and math.isfinite(old_p50) and math.isfinite(new_p50):
        if abs(old_p50) < 1e-6:
            p50_relative_change = 0.0 if new_p50 == old_p50 else math.inf
        else:
            p50_relative_change = abs(new_p50 - old_p50) / abs(old_p50)
        p50_trigger = bool(p50_relative_change > 0.05)
        if p50_trigger:
            base["minimum_required_n"] = 2400
    base.update({
        "p50_relative_change": p50_relative_change,
        "p50_continuation_trigger": p50_trigger,
    })

    blockers = []
    if not _point_components_accepted(previous):
        blockers.append("PREVIOUS_CHECKPOINT_COMPONENTS_NOT_ACCEPTED")
    if not _point_components_accepted(current):
        blockers.append("CURRENT_CHECKPOINT_COMPONENTS_NOT_ACCEPTED")
    loss = (curr_refs or {}).get("indicators", {}).get("Probability_of_Accounting_Loss", {}) if isinstance(curr_refs, Mapping) else {}
    if loss.get("adjacent_change_pass") is not True:
        blockers.append("ACCOUNTING_LOSS_ADJACENT_CHANGE_NOT_PASS")
    reference = curr_refs if isinstance(curr_refs, Mapping) else {}
    if reference.get("acceptance_status") != "ACCEPTED":
        blockers.append("REFERENCE_INDICATOR_METHODS_NOT_INDEPENDENTLY_ACCEPTED")
    return {
        **base,
        "status": "PASS" if not blockers else "BLOCKED",
        "blockers": blockers,
    }


def evaluate_stopping_window(
    history: Sequence[Mapping[str, Any]],
    *,
    required_points: int = 4,
    required_transitions: int = 3,
    minimum_stop_n: int = 400,
) -> dict[str, Any]:
    """Fail-closed final stopping rule: 4 cumulative points / 3 adjacent transitions."""
    if required_points != required_transitions + 1:
        raise ValueError("stopping window must contain one more point than transitions")
    if len(history) < required_points:
        return {
            "status": "BLOCKED",
            "stable": False,
            "points_required": required_points,
            "transitions_required": required_transitions,
            "points_seen": len(history),
            "transitions_seen": max(0, len(history) - 1),
            "blockers": ["INSUFFICIENT_CUMULATIVE_CHECKPOINT_POINTS"],
        }
    recent = list(history[-required_points:])
    ns = [item.get("n") for item in recent]
    if any(type(n) is not int for n in ns) or any(b != a * 2 for a, b in zip(ns, ns[1:])):
        return {
            "status": "BLOCKED",
            "stable": False,
            "points_required": required_points,
            "transitions_required": required_transitions,
            "points_seen": len(recent),
            "transitions_seen": max(0, len(recent) - 1),
            "blockers": ["FOUR_POINTS_DO_NOT_FORM_THREE_ADJACENT_DOUBLING_TRANSITIONS"],
        }
    blockers: list[str] = []
    if ns[-1] < minimum_stop_n:
        blockers.append("MINIMUM_STOP_N_NOT_REACHED")
    if any(not _point_components_accepted(item) for item in recent):
        blockers.append("ONE_OR_MORE_CHECKPOINT_COMPONENTS_NOT_ACCEPTED")
    transitions = [item.get("transition") for item in recent[1:]]
    if len(transitions) != required_transitions or any(
        not isinstance(item, Mapping) or item.get("status") != "PASS" for item in transitions
    ):
        blockers.append("THREE_SUCCESSFUL_ADJACENT_TRANSITIONS_NOT_ESTABLISHED")
    any_p50_trigger = any(
        bool((item.get("transition") or {}).get("p50_continuation_trigger"))
        for item in history if isinstance(item, Mapping) and isinstance(item.get("transition"), Mapping)
    )
    required_n = 2400 if any_p50_trigger else minimum_stop_n
    if ns[-1] < required_n:
        blockers.append("P50_TRIGGER_REQUIRES_CONTINUATION_TO_N2400")
    return {
        "status": "PASS" if not blockers else "BLOCKED",
        "stable": not blockers,
        "points_required": required_points,
        "transitions_required": required_transitions,
        "points_seen": len(recent),
        "transitions_seen": len(transitions),
        "window_n": ns,
        "p50_trigger_seen": any_p50_trigger,
        "minimum_required_n": required_n,
        "blockers": blockers,
    }
