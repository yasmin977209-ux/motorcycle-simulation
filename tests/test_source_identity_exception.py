from __future__ import annotations

import ast
import inspect

import daily_engine
import monte_carlo


def test_compatibility_adapter_and_target_exist() -> None:
    assert callable(getattr(daily_engine, "_create_contract", None))
    assert callable(getattr(daily_engine, "_new_contract", None))

    module = ast.parse(inspect.getsource(daily_engine._create_contract))
    function = next(
        node for node in module.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_create_contract"
    )
    returns = [
        node for node in ast.walk(function)
        if isinstance(node, ast.Return)
    ]
    assert len(returns) == 1
    call = returns[0].value
    assert isinstance(call, ast.Call)
    assert isinstance(call.func, ast.Name)
    assert call.func.id == "_new_contract"
    assert len(call.args) == 4
    assert not call.keywords


def test_miniature_deterministic_replay_is_stable_for_three_trials() -> None:
    scenario = "C030_G000"
    trial_ids = (100, 200, 300)
    first_results, first_slices = monte_carlo.run_trials_sequentially(
        scenario, trial_ids, master_seed=20270101
    )
    second_results, second_slices = monte_carlo.run_trials_sequentially(
        scenario, trial_ids, master_seed=20270101
    )

    assert monte_carlo.fingerprint_trial_results(first_results) == (
        monte_carlo.fingerprint_trial_results(second_results)
    )
    assert monte_carlo.fingerprint_per_trial_slices(first_slices) == (
        monte_carlo.fingerprint_per_trial_slices(second_slices)
    )
