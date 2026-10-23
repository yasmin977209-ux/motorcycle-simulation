from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

import run_batch
from scripts.golden_reference_provider import APPROVED_SOURCE_SHA, GoldenReferenceProvider, stage10_trial_result_sha256


@dataclass(frozen=True)
class Trial:
    scenario_id: str
    collection_probability: float
    recovery_rate_pct: int
    trial_id: int
    final_close_date: str | None
    final_net_project_equity: int
    final_cash: int
    cumulative_project_profit: int
    operating_net_profit: int
    termination_count: int
    secondary_cycle_count: int
    owned_bikes: int
    held_assets: int
    total_operating_revenue: int
    bad_debt: int
    guarantee_recovered: int
    partner1_final_entitlement: int
    partner2_final_entitlement: int


def _trials(count: int = 300) -> list[Trial]:
    return [
        Trial("C070_G100", 0.70, 100, i, None, 10000+i, 5000+i, 1000+i, 800+i,
              i % 4, i % 3, 3, i % 2, 20000+i, i % 11, i % 5, 6000+i, 4000+i)
        for i in range(1, count + 1)
    ]


def _provider_for(trials: list[Trial]) -> GoldenReferenceProvider:
    return GoldenReferenceProvider._from_test_map({
        "C070_G100": {item.trial_id: stage10_trial_result_sha256(item) for item in trials}
    })


def test_gate_a_exact_provider_match_passes_only_with_full_coverage() -> None:
    trials = _trials()
    result = run_batch._evaluate_gate_a_with_provider(
        provider=_provider_for(trials), scenario_id="C070_G100", trial_results=trials,
        source_sha=APPROVED_SOURCE_SHA, master_seed=20270101, previous_metrics=None,
        previous_n=None, current_metrics={}, current_n=300,
    )
    assert result["status"] == "PASS"
    assert result["golden_provider_status"] == "VERIFIED"
    assert result["golden_trials_compared"] == 300
    assert result["golden_trial_mismatch_count"] == 0


def test_gate_a_provider_missing_checkpoint_coverage_blocks() -> None:
    trials = _trials()
    result = run_batch._evaluate_gate_a_with_provider(
        provider=_provider_for(trials[:299]), scenario_id="C070_G100", trial_results=trials,
        source_sha=APPROVED_SOURCE_SHA, master_seed=20270101, previous_metrics=None,
        previous_n=None, current_metrics={}, current_n=300,
    )
    assert result["status"] == "BLOCKED"
    assert result["golden_provider_status"] == "BLOCKED_INCOMPLETE_COVERAGE"


def test_gate_a_provider_exact_hash_mismatch_fails() -> None:
    trials = _trials()
    original = _provider_for(trials)
    altered = {scenario: dict(values) for scenario, values in original._fingerprints.items()}
    altered["C070_G100"][27] = "0" * 64
    provider = GoldenReferenceProvider._from_test_map(altered)
    result = run_batch._evaluate_gate_a_with_provider(
        provider=provider, scenario_id="C070_G100", trial_results=trials,
        source_sha=APPROVED_SOURCE_SHA, master_seed=20270101, previous_metrics=None,
        previous_n=None, current_metrics={}, current_n=300,
    )
    assert result["status"] == "FAIL"
    assert result["golden_trial_mismatch_count"] == 1


def test_gate_a_provider_source_mismatch_fails_closed() -> None:
    trials = _trials()
    result = run_batch._evaluate_gate_a_with_provider(
        provider=_provider_for(trials), scenario_id="C070_G100", trial_results=trials,
        source_sha="0" * 40, master_seed=20270101, previous_metrics=None,
        previous_n=None, current_metrics={}, current_n=300,
    )
    assert result["status"] == "FAIL"
    assert result["golden_source_identity_matches"] is False


def test_stage7_workflow_consumes_verified_provider_cache_and_fails_closed() -> None:
    text = Path(".github/workflows/stage7-full-run.yml").read_text(encoding="utf-8")
    assert "Validate and package exact Gate A golden map" in text
    assert "Download verified Gate A provider map" in text
    assert "GoldenReferenceProvider.from_verified_payload" in text
    assert "_evaluate_gate_a_with_provider(" in text
    assert "GATE_A_EXACT_GOLDEN_BLOCKED_OR_FAILED=" in text


def test_provider_cache_rejects_wrong_schema_or_identity(tmp_path: Path) -> None:
    path = tmp_path / "golden.json"
    path.write_text(json.dumps({"schema_version": "wrong"}), encoding="utf-8")
    with pytest.raises(RuntimeError, match="GOLDEN_PROVIDER_CACHE_SCHEMA_INVALID"):
        GoldenReferenceProvider.from_verified_payload(path)
