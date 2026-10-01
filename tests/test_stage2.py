"""Executable Stage 2 tests for Chapters 3 and 4 and reference lifecycle paths."""

from __future__ import annotations

from datetime import date

import constants
from entities import (
    Bike,
    BikeSource,
    ClaimSource,
    Contract,
    ContractType,
    EventLogEntry,
    EventType,
    GuaranteeClaim,
    Guarantor,
    Project,
    ReceivableEntry,
    ReceivableSource,
    ReceivableStatus,
    Tenant,
    TenantType,
)
from state_machine import (
    BikeState,
    FORBIDDEN_STATE_NAMES,
    run_reference_path,
    STATE_COUNT,
    TRANSITION_TABLE,
    derive_state_from_balance,
    legal_next_state,
)


def test_entities_enums_and_event_catalog_are_exact() -> None:
    assert {x.value for x in BikeSource} == {"INITIAL", "EXPANSION"}
    assert {x.value for x in ContractType} == {"PRIMARY", "SECONDARY"}
    assert {x.value for x in TenantType} == {"ORIGINAL", "SECONDARY"}
    assert {x.value for x in ClaimSource} == {
        "PRIMARY_EARLY_TERMINATION",
        "SECONDARY_EARLY_TERMINATION",
        "POST_MATURITY_SETTLEMENT_FAILURE",
        "ADMINISTRATIVE_CLOSURE",
        "FINAL_CLOSURE",
    }
    assert {x.value for x in EventType} == {
        "BIKE_PURCHASED",
        "PREP_STARTED",
        "PREP_COMPLETED",
        "PRIMARY_CONTRACT_STARTED",
        "PRIMARY_CONTRACT_MATURED",
        "WAITING_STARTED",
        "NOTICE_STARTED",
        "GRACE_STARTED",
        "PRIMARY_TERMINATED",
        "SETTLEMENT_STARTED",
        "SETTLEMENT_COMPLETED",
        "SETTLEMENT_FAILED",
        "SECONDARY_CONTRACT_STARTED",
        "SECONDARY_TERMINATED",
        "ADMINISTRATIVE_CLOSURE",
        "GUARANTEE_CLAIM_CREATED",
        "GUARANTEE_RECOVERED",
        "GUARANTEE_WRITTEN_OFF",
        "OWNERSHIP_TRANSFERRED",
        "FINAL_ASSET_HELD",
        "EXPANSION_PURCHASE",
        "FRIDAY_FEE_COLLECTED",
        "OIL_SERVICE_PERFORMED",
        "DEPRECIATION_RECORDED",
    }
    assert len(EventType) == 24
    assert FORBIDDEN_STATE_NAMES == {
        "TERMINATION_PENDING",
        "MINI_PREP",
        "PENDING_RECALL",
        "GUARANTEE_PENDING",
    }


def test_entity_defaults_and_source_of_truth_fields() -> None:
    project = Project()
    assert project.project_cash == 0
    assert project.partner1_reinvestment_balance == 0
    assert project.partner2_reinvestment_balance == 0

    bike = Bike(
        bike_id="BK0001",
        source=BikeSource.INITIAL,
        purchase_date=date(2026, 12, 26),
        scheduled_ready_date=date(2027, 1, 1),
        gross_cost=constants.BIKE_GROSS_ASSET_COST,
        net_book_value=constants.BIKE_GROSS_ASSET_COST,
    )
    assert bike.current_state == "PREP"
    assert bike.termination_count == 0
    assert bike.secondary_cycle_count == 0
    assert bike.usage_days == 0
    assert not hasattr(bike, "total_due")
    assert not hasattr(bike, "total_paid")
    assert not hasattr(bike, "friday_counter")

    contract = Contract(
        contract_id="CT0001",
        bike_id="BK0001",
        tenant_id="TN0001",
        guarantor_id="GR0001",
        contract_type=ContractType.PRIMARY,
        daily_rate=constants.PRIMARY_DAILY_RENT,
        start_date=date(2027, 1, 2),
        maturity_date=date(2029, 1, 2),
    )
    assert contract.total_due == 0
    assert contract.total_paid == 0
    assert contract.friday_counter == 0

    tenant = Tenant(
        tenant_id="TN0001",
        tenant_type=TenantType.ORIGINAL,
        contract_id="CT0001",
        guarantor_id="GR0001",
        start_date=date(2027, 1, 2),
    )
    guarantor = Guarantor("GR0001", "CT0001", "TN0001")
    assert tenant.tenant_type is TenantType.ORIGINAL
    assert guarantor.related_contract_id == "CT0001"

    claim = GuaranteeClaim(
        "CL0001",
        "BK0001",
        "CT0001",
        "TN0001",
        "GR0001",
        ClaimSource.PRIMARY_EARLY_TERMINATION,
        45000,
        date(2027, 2, 1),
        30,
        date(2027, 3, 4),
        70,
    )
    assert claim.status.value == "PENDING"

    receivable = ReceivableEntry(
        "RC0001",
        "BK0001",
        "CT0001",
        "TN0001",
        ReceivableSource.SETTLEMENT_LEGACY_DEBT,
        10000,
        0,
        10000,
        ReceivableStatus.OUTSTANDING,
        date(2027, 1, 1),
    )
    assert receivable.remaining_amount == receivable.original_amount

    event = EventLogEntry(
        "EV0001",
        date(2027, 1, 2),
        "BK0001",
        EventType.PRIMARY_CONTRACT_STARTED,
        previous_state="PREP",
        new_state="ACTIVE_PRIMARY",
    )
    assert event.previous_state == "PREP"
    assert event.new_state == "ACTIVE_PRIMARY"


def test_exactly_eleven_exclusive_states() -> None:
    assert len(BikeState) == STATE_COUNT == 11
    assert {s.value for s in BikeState} == {
        "PREP",
        "ACTIVE_PRIMARY",
        "WAITING_PRIMARY",
        "NOTICE_PRIMARY",
        "GRACE_PRIMARY",
        "POST_MATURITY_SETTLEMENT",
        "AVAILABLE_FOR_SECONDARY",
        "ACTIVE_SECONDARY",
        "NOTICE_SECONDARY",
        "OWNED_TRANSFERRED",
        "HELD_AS_ASSET",
    }
    assert not any(s in FORBIDDEN_STATE_NAMES for s in BikeState.__members__)


def test_derive_state_from_balance_primary_boundaries() -> None:
    r = constants.PRIMARY_DAILY_RENT
    assert derive_state_from_balance(0, r, "PRIMARY") == "ACTIVE_PRIMARY"
    assert derive_state_from_balance(1, r, "PRIMARY") == "WAITING_PRIMARY"
    assert derive_state_from_balance(21 * r - 1, r, "PRIMARY") == "WAITING_PRIMARY"
    assert derive_state_from_balance(21 * r, r, "PRIMARY") == "NOTICE_PRIMARY"
    assert derive_state_from_balance(28 * r - 1, r, "PRIMARY") == "NOTICE_PRIMARY"
    assert derive_state_from_balance(28 * r, r, "PRIMARY") == "GRACE_PRIMARY"
    assert derive_state_from_balance(30 * r - 1, r, "PRIMARY") == "GRACE_PRIMARY"
    assert derive_state_from_balance(30 * r, r, "PRIMARY") is None


def test_derive_state_from_balance_secondary_boundaries() -> None:
    r = constants.SECONDARY_DAILY_RENT
    assert derive_state_from_balance(0, r, "SECONDARY") == "ACTIVE_SECONDARY"
    assert derive_state_from_balance(1, r, "SECONDARY") == "NOTICE_SECONDARY"
    assert derive_state_from_balance(10 * r - 1, r, "SECONDARY") == "NOTICE_SECONDARY"
    assert derive_state_from_balance(10 * r, r, "SECONDARY") is None


def test_threshold_breach_does_not_self_terminate_in_m10() -> None:
    assert legal_next_state(
        "GRACE_PRIMARY", 30 * constants.PRIMARY_DAILY_RENT, constants.PRIMARY_DAILY_RENT, "PRIMARY"
    ) is None
    assert legal_next_state(
        "NOTICE_SECONDARY", 10 * constants.SECONDARY_DAILY_RENT, constants.SECONDARY_DAILY_RENT, "SECONDARY"
    ) is None


def test_transition_table_contains_reference_rules() -> None:
    assert len(TRANSITION_TABLE) == 19
    pairs = {(rule.from_states, rule.to_state, rule.phase) for rule in TRANSITION_TABLE}
    assert (("PREP",), "ACTIVE_PRIMARY", "M3") in pairs
    assert (
        ("GRACE_PRIMARY",),
        "AVAILABLE_FOR_SECONDARY",
        "M11",
    ) in pairs
    assert (
        ("POST_MATURITY_SETTLEMENT",),
        "OWNED_TRANSFERRED",
        "M13",
    ) in pairs
    assert (
        ("POST_MATURITY_SETTLEMENT",),
        "AVAILABLE_FOR_SECONDARY",
        "M13",
    ) in pairs
    assert (
        ("AVAILABLE_FOR_SECONDARY",),
        "ACTIVE_SECONDARY",
        "M3",
    ) in pairs
    assert (
        ("NOTICE_SECONDARY",),
        "AVAILABLE_FOR_SECONDARY",
        "M11",
    ) in pairs
    assert (
        ("ACTIVE_SECONDARY", "NOTICE_SECONDARY"),
        "HELD_AS_ASSET",
        "M15",
    ) in pairs
    assert (
        (
            "PREP",
            "ACTIVE_PRIMARY",
            "WAITING_PRIMARY",
            "NOTICE_PRIMARY",
            "GRACE_PRIMARY",
            "POST_MATURITY_SETTLEMENT",
            "AVAILABLE_FOR_SECONDARY",
            "ACTIVE_SECONDARY",
            "NOTICE_SECONDARY",
        ),
        "HELD_AS_ASSET",
        "M15",
    ) in pairs


def test_reference_path_1_natural() -> None:
    path = [
        "PREP",
        "ACTIVE_PRIMARY",
        "OWNED_TRANSFERRED",
    ]
    assert run_reference_path(path) == tuple(path)
    assert BikeState.OWNED_TRANSFERRED.value == path[-1]


def test_reference_path_2_primary_early_default() -> None:
    path = [
        "PREP",
        "ACTIVE_PRIMARY",
        "WAITING_PRIMARY",
        "NOTICE_PRIMARY",
        "GRACE_PRIMARY",
        "AVAILABLE_FOR_SECONDARY",
        "ACTIVE_SECONDARY",
    ]
    assert run_reference_path(path) == tuple(path)


def test_reference_path_3_maturity_debt_settled() -> None:
    path = [
        "ACTIVE_PRIMARY",
        "POST_MATURITY_SETTLEMENT",
        "OWNED_TRANSFERRED",
    ]
    assert run_reference_path(path) == tuple(path)


def test_reference_path_4_maturity_debt_failed() -> None:
    path = [
        "ACTIVE_PRIMARY",
        "POST_MATURITY_SETTLEMENT",
        "AVAILABLE_FOR_SECONDARY",
    ]
    assert run_reference_path(path) == tuple(path)


def test_reference_path_5_secondary_repeated_cycle() -> None:
    path = [
        "ACTIVE_SECONDARY",
        "NOTICE_SECONDARY",
        "AVAILABLE_FOR_SECONDARY",
        "ACTIVE_SECONDARY",
    ]
    assert run_reference_path(path) == tuple(path)
    assert "ACTIVE_SECONDARY" == path[-1]


def test_reference_path_6_dynamic_closure() -> None:
    active_states = {
        "PREP",
        "ACTIVE_PRIMARY",
        "WAITING_PRIMARY",
        "NOTICE_PRIMARY",
        "GRACE_PRIMARY",
        "POST_MATURITY_SETTLEMENT",
        "AVAILABLE_FOR_SECONDARY",
        "ACTIVE_SECONDARY",
        "NOTICE_SECONDARY",
    }
    assert active_states
    for state in active_states:
        assert run_reference_path([state, "HELD_AS_ASSET"]) == (state, "HELD_AS_ASSET")
    closure_targets = {
        rule.to_state
        for rule in TRANSITION_TABLE
        if rule.phase == "M15" and rule.to_state == "HELD_AS_ASSET"
    }
    assert closure_targets == {"HELD_AS_ASSET"}


def test_paths_are_composed_of_declared_states_only() -> None:
    path_sets = [
        ["PREP", "ACTIVE_PRIMARY", "OWNED_TRANSFERRED"],
        ["PREP", "ACTIVE_PRIMARY", "WAITING_PRIMARY", "NOTICE_PRIMARY", "GRACE_PRIMARY", "AVAILABLE_FOR_SECONDARY", "ACTIVE_SECONDARY"],
        ["ACTIVE_PRIMARY", "POST_MATURITY_SETTLEMENT", "OWNED_TRANSFERRED"],
        ["ACTIVE_PRIMARY", "POST_MATURITY_SETTLEMENT", "AVAILABLE_FOR_SECONDARY"],
        ["ACTIVE_SECONDARY", "NOTICE_SECONDARY", "AVAILABLE_FOR_SECONDARY", "ACTIVE_SECONDARY"],
        ["ACTIVE_PRIMARY", "HELD_AS_ASSET"],
    ]
    declared = {s.value for s in BikeState}
    for path in path_sets:
        assert set(path) <= declared
