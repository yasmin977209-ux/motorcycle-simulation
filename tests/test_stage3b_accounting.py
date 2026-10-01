from datetime import date

from accounting import (
    accrue_rent,
    assert_balance_sheet_balanced,
    balance_sheet_snapshot,
    collect_from_ar,
    refresh_profit,
    settle_guarantee_accounting,
)
from constants import (
    BIKE_GROSS_ASSET_COST,
    CLAIM_SOURCE_PRIMARY_EARLY_TERMINATION,
)
from entities import Contract, ContractType, Project
from guarantee import create_guarantee_claim


def _project_contract() -> tuple[Project, Contract]:
    project = Project.opening()
    contract = Contract(
        contract_id="CT00000001",
        bike_id="BK0001",
        tenant_id="TN0001",
        guarantor_id="GR0001",
        contract_type=ContractType.PRIMARY,
        daily_rate=1_500,
        start_date=date(2027, 1, 2),
        maturity_date=date(2029, 1, 2),
    )
    project.contracts[contract.contract_id] = contract
    return project, contract


def test_ch10_opening_balance_sheet_is_exact() -> None:
    project = Project.opening()
    snapshot = assert_balance_sheet_balanced(
        project,
        date(2027, 1, 1),
    )
    assert snapshot["Cash"] == 0
    assert snapshot["Net_Bike_Assets"] == BIKE_GROSS_ASSET_COST * 10
    assert snapshot["Total_Equity"] == 3_600_000


def test_ch10_reference_numeric_bridge() -> None:
    project, contract = _project_contract()
    accrue_rent(project, contract, 20_000)
    collect_from_ar(project, 5_000)

    claim = create_guarantee_claim(
        "CL00000001",
        contract.bike_id,
        contract.contract_id,
        contract.tenant_id,
        contract.guarantor_id,
        CLAIM_SOURCE_PRIMARY_EARLY_TERMINATION,
        15_000,
        date(2027, 2, 1),
        50,
    )
    project.guarantee_claims.append(claim)
    project.accounts_receivable -= 15_000
    project.guarantee_claim_receivable += 15_000
    settle_guarantee_accounting(project, 15_000, 7_500, 7_500)
    refresh_profit(project)

    assert project.revenue_primary == 20_000
    assert project.bad_debt_expense == 7_500
    assert project.operating_net_profit == 12_500
    assert project.cumulative_project_profit == -87_500
    assert project.project_cash == 12_500
    snapshot = balance_sheet_snapshot(project)
    assert snapshot["Balance_Difference"] == 0
    assert snapshot["Total_Equity"] == 3_612_500
