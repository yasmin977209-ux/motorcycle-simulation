"""Additional Stage 2 entity/index contract tests."""

from __future__ import annotations

from datetime import date

import constants
from entities import (
    Bike,
    BikeSource,
    Contract,
    ContractType,
    Project,
    add_contract,
    contract_of,
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


def test_project_contracts_is_plain_dict_and_supports_large_key_lookup() -> None:
    project = Project()

    for number in range(100_000):
        contract = _contract(f"CT{number:08d}")
        project.contracts[contract.contract_id] = contract

    target_id = "CT00099999"
    target = project.contracts[target_id]

    assert type(project.contracts) is dict
    assert target.contract_id == target_id
    assert project.contracts[target_id] is target


def test_add_contract_raises_value_error_on_duplicate_contract_id() -> None:
    project = Project()
    first = _contract("CT00000001")
    second = _contract("CT00000001")

    add_contract(project, first)

    try:
        add_contract(project, second)
    except ValueError:
        pass
    else:
        raise AssertionError("duplicate contract_id must raise ValueError")

    assert project.contracts["CT00000001"] is first
    assert len(project.contracts) == 1


def test_contract_of_returns_current_contract_by_key_or_none() -> None:
    project = Project()
    bike = Bike(
        bike_id="BK0001",
        source=BikeSource.INITIAL,
        purchase_date=date(2026, 12, 26),
        scheduled_ready_date=date(2027, 1, 1),
    )

    assert contract_of(project, bike) is None

    contract = _contract("CT00000001")
    add_contract(project, contract)
    bike.current_contract_id = contract.contract_id

    assert contract_of(project, bike) is contract

    bike.current_contract_id = "CT_NOT_PRESENT"
    assert contract_of(project, bike) is None


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
