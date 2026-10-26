from __future__ import annotations
import json
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace
import pytest
import stats_integrity as si
from scripts.test192_coverage import run_coverage_simulation

REPO_ROOT = Path(__file__).resolve().parents[1]
PROOF_PATH = REPO_ROOT / "docs" / "stage7" / "test192_coverage_proof.json"


def _trial_rows(n: int):
    return [
        SimpleNamespace(trial_id=i, cumulative_project_profit=100, final_cash=200,
                        termination_count=1, held_assets=2)
        for i in range(1, n + 1)
    ]


def test_172_sequential_alpha_and_cumulative_checkpoint_index_are_exact():
    assert [si.statistical_checkpoint_index(n) for n in (300, 600, 1200, 2400)] == [1, 2, 3, 4]
    assert [si.sequential_alpha_fraction(k) for k in range(1, 5)] == [
        Fraction(1, 800), Fraction(1, 2400), Fraction(1, 4800), Fraction(1, 8000)
    ]
    assert si.cumulative_alpha_fraction(4) == Fraction(1, 500)


def test_172_p50_guard_uses_cross_multiplication_and_zero_baseline():
    assert si.p50_relative_change_exceeds_guard(Fraction(0), Fraction(0)) is False
    assert si.p50_relative_change_exceeds_guard(Fraction(0), Fraction(9, 10)) is True
    assert si.p50_relative_change_exceeds_guard(Fraction(100), Fraction(105)) is False
    assert si.p50_relative_change_exceeds_guard(Fraction(100), Fraction(106)) is True


def test_172_fixed_n_three_over_n_is_descriptive_not_adaptive_acceptance():
    result = si._loss_probability_interval([False] * 300, k=1)
    assert result["descriptive_3_over_n"] == "1/100"
    assert result["stable"] is False


def test_172_all_seven_indicators_use_current_checkpoint_and_iut_gate_b():
    n = 2400
    means = {
        "Final_Net_Project_Equity": [100] * n,
        "Partner1_Final_Entitlement": [70] * n,
        "Partner2_Final_Entitlement": [30] * n,
    }
    decision = si.evaluate_gate_b_statistical(means, _trial_rows(n), k=4)
    expected = {
        "P10_Cumulative_Project_Profit", "P50_Cumulative_Project_Profit",
        "P90_Cumulative_Project_Profit", "P90_Final_Cash",
        "Probability_of_Accounting_Loss", "P90_Termination_Count", "P90_Held_Assets",
    }
    assert set(decision["indicators"]["indicators"]) == expected
    assert decision["decision_framework"] == "IUT"
    assert decision["n"] == n and decision["spending_index"] == 4
    assert decision["stable"] is True


def test_172_wrong_checkpoint_index_fails_closed():
    with pytest.raises(ValueError, match="STATISTICAL_CHECKPOINT_INDEX_MISMATCH"):
        si.time_uniform_indicator_summary(_trial_rows(600), k=1)


def test_172_legacy_n_and_half_n_gate_is_removed():
    source = (REPO_ROOT / "stats_integrity.py").read_text(encoding="utf-8")
    assert "mean_confidence_summary_at_n_and_half" not in source
    assert '"half_n"' not in source
    assert "stable_at_half_n" not in source


def test_192_coverage_proof_is_deterministic_and_familywise_bounded():
    proof = run_coverage_simulation()
    assert proof["master_seed"] == 20270101
    assert proof["replications"] == 10_000
    assert proof["scenario_count"] == 20
    assert proof["checkpoint_schedule"] == [300, 600, 1200, 2400]
    assert proof["pass"] is True
    assert float(proof["observed_fwer"]) <= 0.05
    assert proof["familywise_fwer_numerator"] <= proof["familywise_fwer_denominator"] // 20
    assert PROOF_PATH.exists(), "workflow must materialize docs/stage7/test192_coverage_proof.json"
    assert json.loads(PROOF_PATH.read_text(encoding="utf-8")) == proof
