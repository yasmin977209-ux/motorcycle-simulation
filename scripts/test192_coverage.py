#!/usr/bin/env python3
"""Deterministic, vectorized Test 192 coverage experiment for v2.3."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import numpy as np
from scipy.stats import t

MASTER_SEED = 20270101
REPLICATIONS = 10_000
SCENARIO_COUNT = 20
CHECKPOINTS = (300, 600, 1200, 2400)
BATCH_SIZE = 250
ALPHA_PER_SCENARIO = 0.0025
FAMILYWISE_TARGET = 0.05


def run_coverage_simulation() -> dict:
    """Nested-look coverage simulation using 20 known, right-skewed lognormal laws."""
    rng = np.random.default_rng(MASTER_SEED)
    mu = np.linspace(-0.2, 0.7, SCENARIO_COUNT, dtype=np.float64)
    sigma = np.linspace(0.1, 0.55, SCENARIO_COUNT, dtype=np.float64)
    truth = np.exp(mu + (sigma * sigma) / 2.0)
    missed = np.zeros((REPLICATIONS, SCENARIO_COUNT, len(CHECKPOINTS)), dtype=np.bool_)
    for first in range(0, REPLICATIONS, BATCH_SIZE):
        size = min(BATCH_SIZE, REPLICATIONS - first)
        cumulative_sum = np.zeros((size, SCENARIO_COUNT), dtype=np.float64)
        cumulative_sum_squares = np.zeros((size, SCENARIO_COUNT), dtype=np.float64)
        previous_n = 0
        for k, n in enumerate(CHECKPOINTS, start=1):
            new_n = n - previous_n
            sample = rng.lognormal(
                mean=mu[None, :, None], sigma=sigma[None, :, None],
                size=(size, SCENARIO_COUNT, new_n),
            )
            cumulative_sum += sample.sum(axis=2)
            cumulative_sum_squares += np.square(sample).sum(axis=2)
            mean = cumulative_sum / n
            variance = np.maximum(
                (cumulative_sum_squares - cumulative_sum * cumulative_sum / n) / (n - 1), 0.0
            )
            standard_error = np.sqrt(variance / n)
            alpha_sk = ALPHA_PER_SCENARIO / (k * (k + 1))
            critical = float(t.isf(alpha_sk / 2.0, n - 1))
            lower, upper = mean - critical * standard_error, mean + critical * standard_error
            missed[first:first + size, :, k - 1] = (
                (truth[None, :] < lower) | (truth[None, :] > upper)
            )
            previous_n = n
    familywise_failures = int(np.any(missed, axis=(1, 2)).sum())
    familywise_fwer = familywise_failures / REPLICATIONS
    proof = {
        "schema_version": "test192-coverage-proof-v1",
        "test_id": 192,
        "master_seed": MASTER_SEED,
        "replications": REPLICATIONS,
        "scenario_count": SCENARIO_COUNT,
        "checkpoint_schedule": list(CHECKPOINTS),
        "alpha_spending": {
            "per_scenario": "0.0025",
            "formula": "0.0025 / (k * (k + 1))",
            "values": [
                {"k": k, "n": n, "alpha_numerator": 1, "alpha_denominator": 400 * k * (k + 1)}
                for k, n in enumerate(CHECKPOINTS, start=1)
            ],
        },
        "synthetic_distribution": {
            "family": "lognormal",
            "parameterization": "known mu and sigma; mean = exp(mu + sigma^2 / 2)",
            "mu_range": ["-0.2", "0.7"],
            "sigma_range": ["0.1", "0.55"],
            "skewed": True,
            "finite_moments": True,
            "nested_checkpoints": True,
        },
        "coverage_method": "two-sided Student-t mean interval at each N_k using alpha_s,k; familywise event is any miss over 20 scenarios and all four looks",
        "familywise_failures": familywise_failures,
        "familywise_fwer_numerator": familywise_failures,
        "familywise_fwer_denominator": REPLICATIONS,
        "observed_fwer": f"{familywise_fwer:.4f}",
        "familywise_target": "0.05",
        "per_checkpoint_miss_counts": [
            int(missed[:, :, index].sum()) for index in range(len(CHECKPOINTS))
        ],
        "pass": familywise_fwer <= FAMILYWISE_TARGET,
    }
    assert REPLICATIONS >= 10_000
    assert familywise_fwer <= FAMILYWISE_TARGET, (
        f"TEST192_FWER_EXCEEDED: observed={familywise_fwer:.6f}, target={FAMILYWISE_TARGET:.6f}"
    )
    return proof


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    proof = run_coverage_simulation()
    text = json.dumps(proof, indent=2, sort_keys=True) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
