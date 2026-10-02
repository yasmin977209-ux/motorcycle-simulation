from __future__ import annotations

import dataclasses

import numpy as np

import monte_carlo


def test_c100_zero_variance_across_trial_ids() -> None:
    results = [
        monte_carlo.run_single_trial(
            "C100_G100",
            trial_id,
            master_seed=20270101,
        )[0]
        for trial_id in (1, 100, 9999)
    ]
    assert results[0] == results[1] == results[2]


def test_c100_representative_selection_has_four_equal_keys() -> None:
    results = [
        monte_carlo.run_single_trial(
            "C100_G100",
            trial_id,
            master_seed=20270101,
        )[0]
        for trial_id in (1, 100, 9999)
    ]
    selected = monte_carlo.select_representative_trials(results)
    assert set(selected) == {
        "p50_trial_id",
        "p10_trial_id",
        "p90_trial_id",
        "loss_case_trial_id",
    }
    assert len(set(selected.values())) == 1


def test_c070_selection_depends_only_on_final_project_equity() -> None:
    results, _ = monte_carlo.run_trials_sequentially(
        "C070_G100",
        tuple(range(1, 21)),
    )
    equities = [result.final_net_project_equity for result in results]

    def expected_nearest(q: float) -> int:
        target = np.quantile(equities, q, method="linear")
        return min(
            results,
            key=lambda result: (
                abs(result.final_net_project_equity - target),
                result.trial_id,
            ),
        ).trial_id

    expected = {
        "p50_trial_id": expected_nearest(0.50),
        "p10_trial_id": expected_nearest(0.10),
        "p90_trial_id": expected_nearest(0.90),
        "loss_case_trial_id": min(
            results,
            key=lambda result: (
                result.final_net_project_equity,
                result.trial_id,
            ),
        ).trial_id,
    }

    perturbed = [
        dataclasses.replace(
            result,
            final_cash=-result.final_cash,
            partner1_final_entitlement=-result.partner1_final_entitlement,
            partner2_final_entitlement=-result.partner2_final_entitlement,
        )
        for result in results
    ]

    assert monte_carlo.select_representative_trials(perturbed) == expected
