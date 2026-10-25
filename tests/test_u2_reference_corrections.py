from datetime import date

import daily_engine
from entities import ContractType


def test_168_first_eligible_friday_is_stored_per_secondary_contract() -> None:
    project = daily_engine.create_initial_project()
    bike = project.bikes[0]

    saturday = daily_engine._new_contract(
        project, bike, ContractType.SECONDARY, date(2027, 1, 2)
    )
    tuesday = daily_engine._new_contract(
        project, bike, ContractType.SECONDARY, date(2027, 1, 5)
    )

    assert saturday.first_eligible_friday_date == date(2027, 1, 8)
    assert tuesday.first_eligible_friday_date == date(2027, 1, 15)
    assert saturday.friday_counter == 0
    assert tuesday.friday_counter == 0

import dateutils
from datetime import timedelta
from entities import BikeState, ContractStatus


def _m12_settlement_fixture(maturity_date: date):
    project = daily_engine.create_initial_project()
    bike = project.bikes[0]
    contract = daily_engine._new_contract(
        project, bike, ContractType.PRIMARY, date(2029, 1, 2)
    )
    contract.maturity_date = maturity_date
    contract.total_due = 1
    contract.total_paid = 0
    bike.current_contract_id = contract.contract_id
    bike.current_tenant_id = contract.tenant_id
    bike.current_state = BikeState.ACTIVE_PRIMARY
    daily_engine._m12(project, maturity_date)
    return project, bike, contract


def test_165_settlement_start_date_is_set_in_m12_for_maturity_weekdays() -> None:
    for maturity_date in (
        date(2031, 1, 2),  # Thursday -> Saturday
        date(2031, 1, 3),  # Friday -> Saturday
        date(2031, 1, 4),  # Saturday -> Sunday
        date(2031, 1, 6),  # Monday -> Tuesday
    ):
        project, bike, contract = _m12_settlement_fixture(maturity_date)
        assert bike.current_state is BikeState.POST_MATURITY_SETTLEMENT
        assert bike.settlement_start_date == dateutils.next_business_day(maturity_date)
        assert bike.settlement_start_date > maturity_date
        assert contract.status is ContractStatus.MATURED


def test_164_settlement_failure_occurs_on_business_day_30() -> None:
    project, bike, contract = _m12_settlement_fixture(date(2031, 1, 2))
    start = bike.settlement_start_date
    assert start is not None
    receivable = daily_engine._receivable_of(project, bike)
    assert receivable is not None

    day30 = start
    count = 0
    while count < daily_engine.constants.SETTLEMENT_PERIOD_DAYS:
        if dateutils.is_business_day(day30):
            count += 1
        if count < daily_engine.constants.SETTLEMENT_PERIOD_DAYS:
            day30 += timedelta(days=1)

    bike.settlement_business_days_elapsed = daily_engine.constants.SETTLEMENT_PERIOD_DAYS - 1
    bike.settlement_legacy_debt_remaining = 1
    project.accounts_receivable = 1
    receivable.remaining_amount = 1
    daily_engine._ensure_day_metrics(project)
    daily_engine._m13(project, day30, recovery_rate_pct=100)

    assert bike.current_state is BikeState.AVAILABLE_FOR_SECONDARY
    assert project.guarantee_claims[-1].claim_source == "POST_MATURITY_SETTLEMENT_FAILURE"
    assert project.guarantee_claims[-1].created_date == day30
    assert bike.active_settlement_receivable_id is None
    assert bike.settlement_business_days_elapsed == daily_engine.constants.SETTLEMENT_PERIOD_DAYS

from constants import EXPANSION_PURCHASE_CASH_THRESHOLD, BIKE_BASE_PURCHASE_COST


def test_166_m2_purchases_at_most_one_expansion_bike_per_day() -> None:
    project = daily_engine.create_initial_project()
    starting_count = len(project.bikes)
    starting_cash = EXPANSION_PURCHASE_CASH_THRESHOLD * 2
    project.project_cash = starting_cash
    project.partner1_reinvestment_balance = starting_cash

    daily_engine._m2(project, date(2027, 1, 2))

    assert len(project.bikes) == starting_count + 1
    assert project.project_cash == starting_cash - BIKE_BASE_PURCHASE_COST
    assert project.partner1_reinvestment_balance == (
        starting_cash - BIKE_BASE_PURCHASE_COST
    )

def test_167_customs_are_in_investing_cash_outflows_and_cash_rollforward() -> None:
    project = daily_engine.run_deterministic_trial(
        recovery_rate_pct=100,
        trial_id=1,
        scenario_id="C100_G100",
        master_seed=daily_engine.constants.MASTER_SEED,
    )

    investing_outflows = sum(
        row["Investing_Cash_Outflows"] for row in project.cash_rollforward
    )
    capitalized_purchases_and_customs = sum(
        row["Capitalized_Purchases_And_Customs"]
        for row in project.asset_rollforward
    )

    assert investing_outflows > 0
    assert investing_outflows == capitalized_purchases_and_customs
    for cash in project.cash_rollforward:
        assert cash["Outflows"] == (
            cash["Operating_Cash_Outflows"] + cash["Investing_Cash_Outflows"]
        )
        assert cash["Opening_Cash"] + cash["Inflows"] - cash["Outflows"] == cash["Closing_Cash"]



def test_partner_split_has_one_algorithm_and_inflows_use_allocator() -> None:
    from partner_equity import split_70_30, allocate_inflow
    project = daily_engine.create_initial_project()
    assert split_70_30(1001) == (700, 301)
    before1 = project.partner1_reinvestment_balance
    before2 = project.partner2_reinvestment_balance
    allocate_inflow(project, 1001)
    assert project.partner1_reinvestment_balance - before1 == 700
    assert project.partner2_reinvestment_balance - before2 == 301


def test_177_no_integer_magic_numbers_outside_constants_py() -> None:
    import ast
    from acceptance_helpers import APP_FILES

    forbidden_values = {
        1500, 1000, 4000, 10000, 350000, 360000,
        45000, 31500, 42000, 2000, 50,
    }
    findings = []
    for path in APP_FILES:
        if path.name == "constants.py":
            continue
        syntax_tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(syntax_tree):
            if (
                isinstance(node, ast.Constant)
                and type(node.value) is int
                and node.value in forbidden_values
            ):
                findings.append(f"{path.name}:{node.lineno}={node.value}")
    assert not findings, "Magic integer constants outside constants.py: " + ", ".join(findings)


def test_178_unified_names_only_in_engine_and_active_output_builder() -> None:
    from acceptance_helpers import APP_FILES, ROOT
    from entities import BikeState
    import re

    banned_names = (
        "Gross_Bike_Assets_" + "Project",
        "Bike_Assets_Gross_" + "Project",
        "Accumulated_Depreciation_" + "Project",
        "Depreciation_" + "Expense",
        "Oil_Service_" + "Expense",
        "Oil_Service_" + "Expenses",
        "Prep_" + "Expense",
        "Prep_" + "Expenses",
        "Marketing_" + "Expense",
        "Bad_Debt_" + "Expense",
        "Asset_Writeoff_" + "Expense",
        "Final_Net_" + "Equity",
        "Final_Net_Equity_" + "at_point",
        "Probability_of_" + "Loss",
        "notice_start_" + "date",
        "grace_start_" + "date",
        "legacy_debt_" + "amount",
        "mini_prep_" + "date",
        "TERMINATION_" + "PENDING",
        "MINI_" + "PREP",
        "PENDING_" + "RECALL",
        "GUARANTEE_" + "PENDING",
        "is_" + "stable",
        "PRACTICAL_MAX_" + "DAYS",
        "PROJECT_END_" + "DATE",
    )
    source_files = list(APP_FILES) + [ROOT / "scripts" / "stage13_assemble.py"]
    findings = []
    for path in source_files:
        source = path.read_text(encoding="utf-8")
        for name in banned_names:
            if name in source:
                findings.append(f"{path.relative_to(ROOT)}:{name}")
    assert not findings, "Forbidden aliases in engine/output source: " + ", ".join(findings)

    forbidden_states = {
        "TERMINATION_" + "PENDING",
        "MINI_" + "PREP",
        "PENDING_" + "RECALL",
        "GUARANTEE_" + "PENDING",
    }
    assert not forbidden_states.intersection(BikeState.__members__)
    assert not re.search(r"\*\s*70\s*\)\s*//\s*100", "\n".join(p.read_text(encoding="utf-8") for p in APP_FILES))


def test_171_rng_stream_pairing_and_integer_success_threshold() -> None:
    import constants
    import rng
    from monte_carlo import run_single_trial

    assert constants.SEED_SCOPE == "COLLECTION_LEVEL"
    same_g_100 = rng.derive_seed(
        constants.MASTER_SEED, "C085_G100", 1, "BK0001",
        date(2027, 1, 2), "PRIMARY_COLLECTION"
    )
    same_g_000 = rng.derive_seed(
        constants.MASTER_SEED, "C085_G000", 1, "BK0001",
        date(2027, 1, 2), "PRIMARY_COLLECTION"
    )
    other_collection = rng.derive_seed(
        constants.MASTER_SEED, "C070_G100", 1, "BK0001",
        date(2027, 1, 2), "PRIMARY_COLLECTION"
    )
    assert rng.rng_stream_id("C085_G100") == "C085"
    assert same_g_100 == same_g_000
    assert same_g_100 != other_collection

    zero_draw = bytes(32)
    half_minus_one = ((1 << 63) - 1).to_bytes(8, "big") + bytes(24)
    half = (1 << 63).to_bytes(8, "big") + bytes(24)
    max_draw = ((1 << 64) - 1).to_bytes(8, "big") + bytes(24)
    assert rng.draw_success(zero_draw, 0) is False
    assert rng.draw_success(zero_draw, 100) is True
    assert rng.draw_success(half_minus_one, 50) is True
    assert rng.draw_success(half, 50) is False
    assert rng.draw_success(max_draw, 99) is False
    assert rng.draw_success(max_draw, 100) is True

    paired = [
        run_single_trial(f"C085_G{g:03d}", 1, master_seed=constants.MASTER_SEED)
        for g in (100, 70, 50, 30, 0)
    ]
    baseline_result, baseline_rows = paired[0]
    assert baseline_result.bad_debt == 0
    assert baseline_result.guarantee_recovered == 0
    for result, rows in paired[1:]:
        assert result.final_close_date == baseline_result.final_close_date
        assert result.final_net_project_equity == baseline_result.final_net_project_equity
        assert result.final_cash == baseline_result.final_cash
        assert result.cumulative_project_profit == baseline_result.cumulative_project_profit
        assert result.partner1_final_entitlement == baseline_result.partner1_final_entitlement
        assert result.partner2_final_entitlement == baseline_result.partner2_final_entitlement
        assert result.bad_debt == 0 and result.guarantee_recovered == 0
        assert rows == baseline_rows


def test_pending_writeoff_today_is_consumed_by_m16() -> None:
    project = daily_engine.create_initial_project()
    bike = project.bikes[0]
    for other in project.bikes[1:]:
        other.current_state = BikeState.HELD_AS_ASSET
    contract = daily_engine._new_contract(
        project, bike, ContractType.PRIMARY, date(2029, 1, 2)
    )
    contract.maturity_date = date(2031, 1, 2)
    contract.total_due = 0
    contract.total_paid = 0
    bike.current_state = BikeState.ACTIVE_PRIMARY
    bike.current_contract_id = contract.contract_id
    bike.current_tenant_id = contract.tenant_id

    daily_engine._m12(project, contract.maturity_date)
    assert bike.current_state is BikeState.OWNED_TRANSFERRED
    assert bike.pending_writeoff_today is True

    daily_engine._ensure_day_metrics(project, reset=True)
    daily_engine._m16(project, contract.maturity_date)
    assert bike.pending_writeoff_today is False
    assert bike.net_book_value == 0
    assert project.gross_bike_assets == (
        daily_engine.constants.OPENING_BIKE_ASSETS - bike.gross_cost
    )


def test_m13_failure_claim_uses_recovery_rate_pct_in_daily_sequence() -> None:
    import constants
    import dateutils

    project = daily_engine.create_initial_project()
    bike = project.bikes[0]
    for other in project.bikes[1:]:
        other.current_state = BikeState.HELD_AS_ASSET
        other.current_contract_id = None
        other.current_tenant_id = None

    contract = daily_engine._new_contract(
        project, bike, ContractType.PRIMARY, date(2029, 1, 2)
    )
    contract.status = ContractStatus.MATURED
    contract.maturity_date = date(2028, 1, 2)
    amount = constants.SETTLEMENT_DAILY_RENT
    contract.total_due = amount
    contract.total_paid = 0
    bike.current_state = BikeState.POST_MATURITY_SETTLEMENT
    bike.current_contract_id = contract.contract_id
    bike.current_tenant_id = contract.tenant_id
    bike.settlement_legacy_debt_original = amount
    bike.settlement_legacy_debt_remaining = amount
    bike.settlement_business_days_elapsed = constants.SETTLEMENT_PERIOD_DAYS - 1

    day30 = constants.EXPANSION_CUTOFF_DATE
    assert dateutils.is_business_day(day30)
    start = day30
    prior_business_days = constants.SETTLEMENT_PERIOD_DAYS - 1
    while prior_business_days:
        start -= timedelta(days=1)
        if dateutils.is_business_day(start):
            prior_business_days -= 1
    bike.settlement_start_date = start

    receivable = daily_engine._new_receivable(project, bike, contract, amount)
    receivable.created_date = start
    project.accounts_receivable = amount
    project.revenue_primary = amount

    daily_engine.run_day(
        project,
        day30,
        collection_probability=0.0,
        scenario_id="C000_TEST",
        trial_id=1,
        recovery_rate_pct=30,
    )

    claim = project.guarantee_claims[-1]
    assert claim.recovery_rate_pct == 30
    assert claim.claim_amount == amount
    assert bike.current_state is BikeState.AVAILABLE_FOR_SECONDARY
    assert bike.active_settlement_receivable_id is None
    assert project.simulation_stopped is False


def test_m15_3_final_closure_receivable_uses_scenario_recovery_rate() -> None:
    import constants

    project = daily_engine.create_initial_project()
    for bike in project.bikes:
        bike.current_state = BikeState.HELD_AS_ASSET
        bike.current_contract_id = None
        bike.current_tenant_id = None
    bike = project.bikes[0]
    contract = daily_engine._new_contract(
        project, bike, ContractType.PRIMARY, date(2029, 1, 2)
    )
    amount = constants.SETTLEMENT_DAILY_RENT
    project.accounts_receivable = amount
    project.revenue_primary = amount
    receivable = daily_engine._new_receivable(project, bike, contract, amount)
    receivable.created_date = date(2030, 12, 31)
    daily_engine._ensure_day_metrics(project, reset=True)

    daily_engine._m15(project, date(2031, 1, 1), recovery_rate_pct=70)

    claim = project.guarantee_claims[-1]
    assert claim.claim_source == constants.CLAIM_SOURCE_FINAL_CLOSURE
    assert claim.recovery_rate_pct == 70
    assert claim.recovered_amount == (amount * 70) // 100
    assert claim.bad_debt_amount == amount - claim.recovered_amount
    assert claim.status.value == "SETTLED"
    assert project.accounts_receivable == 0
    assert project.guarantee_claim_receivable == 0
    assert project.project_cash == claim.recovered_amount
    assert project.partner1_reinvestment_balance > 0
    assert project.simulation_stopped is True


def test_173_stall_detector_requires_all_reference_conditions() -> None:
    import constants
    import pytest
    from closure import SimulationStall, raise_if_stalled, stall_detected
    from entities import BikeState
    from guarantee import create_guarantee_claim

    def deadlocked_project():
        project = daily_engine.create_initial_project()
        for bike in project.bikes:
            bike.current_state = BikeState.HELD_AS_ASSET
            bike.current_contract_id = None
            bike.current_tenant_id = None
        bike = project.bikes[0]
        bike.current_state = BikeState.PREP
        bike.prep_paid = False
        bike.customs_paid = False
        bike.actual_ready_date = None
        project.project_cash = 0
        project.partner1_reinvestment_balance = 0
        return project

    deadlocked = deadlocked_project()
    assert stall_detected(deadlocked) is True
    with pytest.raises(SimulationStall, match="STALL_DETECTED"):
        raise_if_stalled(deadlocked, date(2031, 1, 1))
    assert deadlocked.error_log[-1]["error_code"] == "STALL_DETECTED"
    assert "state_summary" in deadlocked.error_log[-1]

    sufficiently_funded = deadlocked_project()
    required = (
        constants.PREP_OPERATING_EXPENSE_PER_BIKE
        + constants.CUSTOMS_AND_REGISTRATION_COST
    )
    sufficiently_funded.project_cash = required
    sufficiently_funded.partner1_reinvestment_balance = required
    assert stall_detected(sufficiently_funded) is False

    revenue_path_exists = deadlocked_project()
    revenue_path_exists.bikes[1].current_state = BikeState.AVAILABLE_FOR_SECONDARY
    assert stall_detected(revenue_path_exists) is False

    future_cash_exists = deadlocked_project()
    future_cash_exists.guarantee_claims.append(
        create_guarantee_claim(
            "CL00000001",
            "BK0001",
            "CT00000001",
            "TN00000001",
            "GR00000001",
            constants.CLAIM_SOURCE_FINAL_CLOSURE,
            constants.SETTLEMENT_DAILY_RENT,
            date(2031, 1, 1),
            100,
        )
    )
    assert stall_detected(future_cash_exists) is False
