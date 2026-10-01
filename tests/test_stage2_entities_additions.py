"""Additional Stage 2 entity/index contract tests."""

from __future__ import annotations

from datetime import date

import constants
from entities import (
    Bike,
    BikeSource,
    Contract,
    ContractIndex,
    ContractType,
    Project,
)


def _contract(contract_id: str) -> Contract:
    return Contract(
        contract_id=contract_id,
        bike_id="BK0001",
        tenant_id="TN0001",
        guarantor_id="GR0001",
        contract_type=ContractType.PRIMARY,
        daily_rate=constants.PRIMARY_DAILY_RENT,
        start_date=date(2027, 1, 2),
    )


def test_bike_approved_defaults_and_source_of_truth_fields() -> None:
    bike = Bike(
        bike_id="BK0001",
        source=BikeSource.INITIAL,
        purchase_date=date(2026, 12, 26),
        scheduled_ready_date=date(2027, 1, 1),
    )

    assert bike.pending_writeoff_today is False
    assert bike.active_settlement_receivable_id is None
    assert not hasattr(bike, "total_due")
    assert not hasattr(bike, "total_paid")
    assert not hasattr(bike, "friday_counter")


def test_contract_index_is_dict_backed_and_supports_large_key_lookup() -> None:
    index = ContractIndex()

    for number in range(100_000):
        contract_id = f"CT{number:08d}"
        index[contract_id] = _contract(contract_id)

    target_id = "CT099999"
    target = index[target_id]

    assert isinstance(index, dict)
    assert target.contract_id == target_id
    assert index[target_id] is target

    # The key lookup must not depend on value iteration / a linear scan.
    original_iter = ContractIndex.__iter__

    def fail_if_iterated(self):
        raise AssertionError("key lookup must not iterate over the contract index")

    ContractIndex.__iter__ = fail_if_iterated
    try:
        assert index[target_id] is target
    finally:
        ContractIndex.__iter__ = original_iter


def test_contract_index_repeated_contract_id_replaces_existing_value() -> None:
    index = ContractIndex()
    first = _contract("CT00000001")
    second = _contract("CT00000001")

    index.append(first)
    index.append(second)

    assert len(index) == 1
    assert index["CT00000001"] is second
    assert list(index) == [second]


def test_project_rollforward_names_and_reference_record_shapes() -> None:
    project = Project()

    expected_fields = {
        "cash_rollforward": {
            "Opening_Cash",
            "Inflows",
            "Outflows",
            "Closing_Cash",
        },
        "ar_rollforward": {
            "Opening_AR",
            "Accruals",
            "Collections",
            "TransfersToGuarantee",
            "Closing_AR",
        },
        "asset_rollforward": {
            "Opening_Gross_Bike_Assets",
            "Capitalized_Purchases_And_Customs",
            "Gross_Writeoffs_On_Ownership",
            "Closing_Gross_Bike_Assets",
            "Opening_Accumulated_Depreciation",
            "Depreciation_Expense",
            "AD_Removed_On_Writeoff",
            "Closing_Accumulated_Depreciation",
        },
        "equity_rollforward": {
            "Opening_Equity",
            "Operating_Net_Profit",
            "Closing_Equity",
        },
    }

    for attribute_name, fields in expected_fields.items():
        records = getattr(project, attribute_name)
        assert isinstance(records, list)
        for record in records:
            assert set(record) == fields

    assert "Net_Bike_Assets" not in expected_fields["asset_rollforward"]
    assert not hasattr(project, "net_bike_assets")
