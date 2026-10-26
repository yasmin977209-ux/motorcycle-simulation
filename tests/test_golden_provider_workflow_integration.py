from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

import run_batch
from scripts.golden_reference_provider import (
    APPROVED_SOURCE_SHA,
    GoldenReferenceProvider,
    golden_authority_status,
    statistical_execution_status,
    stage10_trial_result_sha256,
)


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


def test_coverage_guard_blocks_unsupported_checkpoint_before_execution() -> None:
    trials = _trials(300)
    provider = _provider_for(trials)
    assert run_batch._gate_a_target_is_covered(provider, "C070_G100", 300)
    assert not run_batch._gate_a_target_is_covered(provider, "C070_G100", 600)
    assert not run_batch._gate_a_target_is_covered(provider, "C070_G100", 2400)
    assert not run_batch._gate_a_target_is_covered(provider, "C000_G000", 300)


def test_stage7_coverage_guard_precedes_trial_runner() -> None:
    workflow = Path(".github/workflows/stage7-full-run.yml").read_text(encoding="utf-8")
    guard = workflow.index("GATE_A_GOLDEN_COVERAGE_EXHAUSTED=")
    trial_block = workflow.index('"--trial-id-start", str(trial_start)')
    assert guard < trial_block
    assert "_gate_a_target_is_covered(" in workflow
    assert '"trial_block_executed": False' in workflow


def test_provider_cache_rejects_wrong_schema_or_identity(tmp_path: Path) -> None:
    path = tmp_path / "golden.json"
    path.write_text(json.dumps({"schema_version": "wrong"}), encoding="utf-8")
    with pytest.raises(RuntimeError, match="GOLDEN_PROVIDER_CACHE_SCHEMA_INVALID"):
        GoldenReferenceProvider.from_verified_payload(path)


def test_current_governance_record_authorizes_only_the_explicit_bounded_golden_map() -> None:
    authority = golden_authority_status(Path("docs/governance/DECISIONS_LOG.md"))
    assert authority["authorized"] is True
    assert authority["status"] == "AUTHORIZED"
    decision = authority["required_decisions"]["D-2026-10-24-01"]
    assert decision["integrity"] == "PASS"
    assert decision["scope"] == "exact pinned Golden map only; statistical execution remains separately blocked"


def test_production_preflight_blocks_statistics_before_state_inspection() -> None:
    workflow = Path(".github/workflows/stage7-full-run.yml").read_text(encoding="utf-8")
    early_guard = workflow.index("Golden and statistical authority preflight")
    stage7_preflight = workflow.index("Stage 7-specific preflight")
    state_ref = workflow.index("STATE_REF=")
    golden_map_guard = workflow.index("GATE_A_GOVERNANCE_AUTHORITY_BLOCKED")
    statistical_guard = workflow.index("STATISTICAL_INFERENCE_BLOCKED")
    upload = workflow.index("Upload verified Gate A map for matrix workers")
    matrix = workflow.index("matrix-simulation:")
    assert early_guard < stage7_preflight < state_ref
    assert golden_map_guard < upload < matrix
    assert statistical_guard < upload < matrix


def test_read_only_verifier_reports_authority_separately_from_map_integrity() -> None:
    workflow = Path(".github/workflows/cp-gatea-provider-wire-verify-20261024.yml").read_text(encoding="utf-8")
    assert '"production_authority_status": authority["status"]' in workflow
    assert '"production_authority_blockers": authority["blockers"]' in workflow


def test_golden_authority_parser_accepts_complete_and_rejects_corrupt_records(tmp_path: Path) -> None:
    path = tmp_path / "DECISIONS_LOG.md"
    decision = """## D-2026-10-24-01 — Explicit Gate A Golden provider authorization and bounded use
**Status:** APPROVED — current explicit project-owner delegation dated 2026-10-24
20270101; f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b
25,205 trial fingerprints; 24,005 fingerprints; IDs 1..1200; C100
24,005-fingerprint base Gate A map SHA-256 is
166cae242d972c597f1a4466d184062f3d959649eb5e2440ad8de8b75663ff2c
25,205-fingerprint combined extended Gate A map SHA-256 is
0fbe3aa87a253f9527953c77b0a122871c9344f75ece6c8a49da99b2a85c1ce1
11,005-fingerprint Stage 12 canonical map SHA-256 is
7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44
dd537fe96c5a8736201441e9a620db148a0d16cadae518d2a777fbc723db395f
eaf1f8f3060aac6967b064d3199c082d2a9b47027c865628986f56cbb23c1fc3
C030_G030; 1201..2400; 38662076725; 11940485523
049af21733b59d753967f27f251cb88fec122b5e1ff4f99d77b9215114c9d3e3
0c7679edfbee54797d64fc66e17116f0db617d1e0fa5f7ee21395fe98a628c65
Preserve the previous C030_G030 N=300→600 failure record
STATISTICAL_INFERENCE_BLOCKED; No production Monte Carlo, Trial, checkpoint
does not reconstruct, replace, or claim recovery
"""
    path.write_text(decision, encoding="utf-8")
    assert golden_authority_status(path)["authorized"] is True

    path.write_text(decision.replace("25,205 trial fingerprints", "NaNNaN trial fingerprints"), encoding="utf-8")
    status = golden_authority_status(path)
    assert status["authorized"] is False
    assert any("D-2026-10-24-01" in item for item in status["blockers"])


def test_statistical_execution_contract_authorizes_work_branch_but_blocks_final_acceptance() -> None:
    status = statistical_execution_status(Path("docs/stage7/statistical_execution_gate.json"))
    assert status["authorized"] is True
    contract = json.loads(Path("docs/stage7/statistical_execution_gate.json").read_text(encoding="utf-8"))
    assert contract["status"] == "AUTHORIZED_FOR_V2.3_EXECUTION"
    authorization = contract["execution_authorization"]
    assert authorization["production_trial_checkpoint_monte_carlo_allowed"] is True
    assert authorization["scenario_stability_declaration_allowed"] is False
    assert authorization["final_delivery_acceptance_allowed"] is False
    assert contract["approved_policy"]["required_successful_adjacent_transitions"] == 3
    assert contract["approved_policy"]["checkpoint_schedule"] == [300, 600, 1200, 2400]


def test_statistical_gate_cannot_be_cleared_by_status_string_alone(tmp_path: Path) -> None:
    path = tmp_path / "statistical_execution_gate.json"
    contract = json.loads(Path("docs/stage7/statistical_execution_gate.json").read_text(encoding="utf-8"))
    contract["status"] = "ACCEPTED_FOR_PRODUCTION"
    contract["execution_authorization"] = {
        "production_trial_checkpoint_monte_carlo_allowed": True,
        "scenario_stability_declaration_allowed": True,
        "final_delivery_acceptance_allowed": True,
    }
    contract["component_status"] = {key: {"status": "PASS"} for key in contract["component_status"]}
    path.write_text(json.dumps(contract), encoding="utf-8")
    result = statistical_execution_status(path)
    assert result["authorized"] is False
    assert any("IMPLEMENTATION_APPROVAL_OR_EVIDENCE_MISSING" in item for item in result["blockers"])

def test_direct_run_batch_entrypoint_blocks_before_any_state_or_trial_side_effects(tmp_path, monkeypatch):
    calls = []
    output_dir = tmp_path / "blocked-output"

    def blocked_status(path):
        calls.append(("gate", Path(path)))
        return {
            "authorized": False,
            "status": "STATISTICAL_INFERENCE_BLOCKED",
            "blockers": ["K_SPEC_BLOCKED"],
        }

    monkeypatch.setattr(run_batch, "statistical_execution_status", blocked_status)
    monkeypatch.setattr(
        run_batch.monte_carlo,
        "parse_scenario_id",
        lambda scenario: calls.append(("parse_scenario", scenario)),
    )
    monkeypatch.setattr(
        run_batch.monte_carlo,
        "run_trials_sequentially",
        lambda *args, **kwargs: calls.append(("run_trials_sequentially", args)),
    )

    with pytest.raises(run_batch.StateIntegrityError, match="STATISTICAL_INFERENCE_BLOCKED"):
        run_batch.run_batch(
            scenario="C070_G100",
            trials=300,
            output_dir=output_dir,
        )

    assert len(calls) == 1
    assert calls[0][0] == "gate"
    assert calls[0][1] == Path(run_batch.__file__).resolve().parent / "docs" / "stage7" / "statistical_execution_gate.json"
    assert not output_dir.exists()


