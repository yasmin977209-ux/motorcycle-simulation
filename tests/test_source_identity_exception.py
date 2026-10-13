from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path

import daily_engine
import monte_carlo


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "docs" / "stage9a" / "dataset_manifest.json"


def _stage10_result_sha(result: monte_carlo.TrialResult) -> str:
    """Use the source-proven Stage 10 per-trial fingerprint convention."""
    payload = json.dumps(
        dataclasses.asdict(result),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def test_compatibility_adapter_and_target_exist() -> None:
    assert callable(getattr(daily_engine, "_create_contract", None))
    assert callable(getattr(daily_engine, "_new_contract", None))

    import ast
    import inspect

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


def test_miniature_replay_matches_historical_manifest_using_source_algorithm() -> None:
    scenario = "C030_G000"
    trial_ids = (100, 200, 300)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["source_sha"] == "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
    assert manifest["master_seed"] == 20270101

    results, _daily = monte_carlo.run_trials_sequentially(
        scenario, trial_ids, master_seed=20270101
    )
    for result in results:
        historical = manifest["trial_fingerprints"][scenario][result.trial_id - 1]
        compatible_sha = _stage10_result_sha(result)
        assert compatible_sha == historical
        # Distinguish this per-trial hash from monte_carlo's dataset-fingerprint encoding.
        assert compatible_sha != monte_carlo.fingerprint_trial_results([result])
