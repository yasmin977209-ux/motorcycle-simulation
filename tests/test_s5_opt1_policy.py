from __future__ import annotations

from types import SimpleNamespace

import pytest

from monte_carlo import TrialResult
from scripts import s5_mini_verification as s5


def _result(
    *,
    scenario_id: str = "C085_G100",
    recovery_rate_pct: int = 100,
    claims_created: int = 0,
    final_cash: int = 10,
) -> TrialResult:
    return TrialResult(
        scenario_id=scenario_id,
        collection_probability=0.85,
        recovery_rate_pct=recovery_rate_pct,
        trial_id=1,
        final_close_date=None,
        final_net_project_equity=100,
        final_cash=final_cash,
        cumulative_project_profit=12,
        operating_net_profit=8,
        termination_count=0,
        secondary_cycle_count=0,
        owned_bikes=10,
        held_assets=0,
        total_operating_revenue=50,
        bad_debt=0,
        guarantee_recovered=0,
        partner1_final_entitlement=70,
        partner2_final_entitlement=30,
        claims_created=claims_created,
    )


def test_opt1_claim_free_g100_allows_only_bit_exact_tagged_candidate():
    base = _result()
    candidate = _result(scenario_id="C085_G070", recovery_rate_pct=70)
    daily = [{"date": "2027-01-01", "Cash": 10}]
    proof = s5.opt1_compare_candidate(
        base, candidate, daily, list(daily), 85, 1, "C085_G070"
    )
    assert proof["base_trial_fingerprint"] == proof["candidate_trial_fingerprint"]
    assert proof["daily_rows_bit_exact"] is True
    assert proof["eligible_for_derived_copy"] is True
    assert proof["derived_from_tag"] == "C085_G100"
    assert s5.opt1_should_derive(0) is True


def test_opt1_positive_claims_refuse_derivation_and_require_all_five_g_runs():
    base = _result(claims_created=1)
    candidate = _result(scenario_id="C085_G070", recovery_rate_pct=70, claims_created=1)
    daily = [{"date": "2027-01-01", "Cash": 10}]
    assert s5.opt1_should_derive(1) is False
    with pytest.raises(RuntimeError, match="OPT1_DERIVATION_FORBIDDEN_CLAIMS_PRESENT"):
        s5.opt1_compare_candidate(base, candidate, daily, list(daily), 85, 1, "C085_G070")
    assert s5.opt1_level_status(0, len(s5.SCENARIO_RECOVERY_RATES)) == "OPT1_INELIGIBLE_FULL_RUN_REQUIRED"
    with pytest.raises(RuntimeError, match="OPT1_FULL_G_RUNS_NOT_VERIFIED"):
        s5.opt1_level_status(0, len(s5.SCENARIO_RECOVERY_RATES) - 1)


def test_opt1_full_run_coverage_requires_all_g_levels_and_all_trial_ids():
    collection_pct = 85
    trial_ids = (1, 2)
    results_by_scenario = {}
    slices_by_scenario = {}
    completed = set()
    for recovery_pct in s5.SCENARIO_RECOVERY_RATES:
        scenario_id = f"C{collection_pct:03d}_G{recovery_pct:03d}"
        results_by_scenario[scenario_id] = [
            SimpleNamespace(trial_id=trial_id) for trial_id in trial_ids
        ]
        slices_by_scenario[scenario_id] = {trial_id: [{"date": "2027-01-01"}] for trial_id in trial_ids}
        completed.add(scenario_id)
    assert len(s5.verify_opt1_full_g_coverage(
        collection_pct, trial_ids, results_by_scenario, slices_by_scenario, completed
    )) == len(s5.SCENARIO_RECOVERY_RATES)
    completed.remove("C085_G000")
    with pytest.raises(RuntimeError, match="OPT1_FULL_RUN_EXECUTION_MISSING:C085_G000"):
        s5.verify_opt1_full_g_coverage(
            collection_pct, trial_ids, results_by_scenario, slices_by_scenario, completed
        )


def test_opt1_positive_claim_count_must_be_an_integer_not_a_boolean_or_float():
    with pytest.raises(ValueError, match="OPT1_CLAIMS_CREATED_MUST_BE_NONNEGATIVE_INT"):
        s5.opt1_should_derive(True)
    with pytest.raises(ValueError, match="OPT1_CLAIMS_CREATED_MUST_BE_NONNEGATIVE_INT"):
        s5.opt1_should_derive(1.0)
