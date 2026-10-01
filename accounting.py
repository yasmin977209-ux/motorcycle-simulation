"""Chapter 10 — accrual accounting and daily balance-sheet controls."""
from __future__ import annotations
from entities import Project

LIABILITIES = 0

def initialize_accounting(project: Project | None = None) -> Project:
    """Initialize the Chapter 10 accounting state on a Project entity.

    The opening position is established before 2027-01-01:
    Cash=0, AR=0, Guarantee Claims=0, Gross Bike Assets=3,600,000,
    Accumulated Depreciation=0, Capital=3,700,000, and Retained Earnings=-100,000.
    Marketing expense is recorded once as an opening memorandum value.
    """
    if project is None:
        project = Project()
    from constants import OPENING_BIKE_ASSETS, OPENING_CASH, OPENING_MARKETING_EXPENSE, OPENING_RETAINED_LOSS, TOTAL_CAPITAL

    project.project_cash = OPENING_CASH
    project.accounts_receivable = 0
    project.guarantee_claim_receivable = 0
    project.gross_bike_assets = OPENING_BIKE_ASSETS
    project.accumulated_depreciation = 0
    project.capital = TOTAL_CAPITAL
    project.retained_earnings = OPENING_RETAINED_LOSS
    project.opening_loss = OPENING_RETAINED_LOSS
    project.expense_marketing = OPENING_MARKETING_EXPENSE
    return project

def accrue_rent(project: Project, contract, amount: int | None = None) -> int:
    """Accrue one ordinary rental amount under Chapter 10 accrual accounting."""
    rent = contract.daily_rate if amount is None else amount
    if rent < 0:
        raise ValueError("rent amount must be non-negative")
    contract.total_due += rent
    project.accounts_receivable += rent
    contract_type = getattr(contract.contract_type, "value", contract.contract_type)
    if contract_type == "PRIMARY":
        project.revenue_primary += rent
    elif contract_type == "SECONDARY":
        project.revenue_secondary += rent
    else:
        raise ValueError(f"unsupported contract type for ordinary rent accrual: {contract_type}")
    return rent

def collect_from_ar(project: Project, amount: int) -> int:
    """Collect an existing receivable without recognizing revenue a second time."""
    if amount < 0:
        raise ValueError("collection amount must be non-negative")
    collected = min(amount, project.accounts_receivable)
    project.accounts_receivable -= collected
    project.project_cash += collected
    return collected

def settle_guarantee_accounting(project: Project, claim_amount: int, recovered_amount: int, bad_debt_amount: int) -> None:
    """Account for settlement of a guarantee claim: recovery is cash only; unrecovered balance is bad debt."""
    if min(claim_amount, recovered_amount, bad_debt_amount) < 0:
        raise ValueError("guarantee amounts must be non-negative")
    if recovered_amount + bad_debt_amount != claim_amount:
        raise ValueError("recovered_amount + bad_debt_amount must equal claim_amount")
    if claim_amount > project.guarantee_claim_receivable:
        raise ValueError("claim amount exceeds guarantee claim receivable")
    project.guarantee_claim_receivable -= claim_amount
    project.project_cash += recovered_amount
    project.bad_debt_expense += bad_debt_amount
def operating_revenue(project: Project) -> int:
    return project.revenue_primary + project.revenue_secondary + project.revenue_settlement + project.revenue_friday_fee

def operating_expenses(project: Project) -> int:
    return project.expense_depreciation + project.expense_oil_service + project.expense_prep + project.bad_debt_expense + project.asset_writeoff_expense

def operating_net_profit(project: Project) -> int:
    return operating_revenue(project) - operating_expenses(project)

def refresh_profit(project: Project) -> int:
    project.retained_earnings = project.opening_loss + operating_net_profit(project)
    return project.retained_earnings

def net_bike_assets(project: Project) -> int:
    return project.gross_bike_assets - project.accumulated_depreciation

def balance_sheet_snapshot(project: Project) -> dict[str, int]:
    refresh_profit(project)
    net_assets = net_bike_assets(project)
    total_assets = project.project_cash + project.accounts_receivable + project.guarantee_claim_receivable + net_assets
    total_equity = project.capital + project.retained_earnings
    return {
        "Cash": project.project_cash,
        "Accounts_Receivable": project.accounts_receivable,
        "Guarantee_Claim_Receivable": project.guarantee_claim_receivable,
        "Gross_Bike_Assets": project.gross_bike_assets,
        "Accumulated_Depreciation": project.accumulated_depreciation,
        "Net_Bike_Assets": net_assets,
        "Capital": project.capital,
        "Retained_Earnings": project.retained_earnings,
        "Total_Assets": total_assets,
        "Total_Equity": total_equity,
        "Balance_Difference": total_assets - total_equity,
        "Liabilities": LIABILITIES,
    }

def assert_balance_sheet_balanced(project: Project, current_date=None) -> dict[str, int]:
    snapshot = balance_sheet_snapshot(project)
    if snapshot["Balance_Difference"] != 0:
        suffix = f" on {current_date}" if current_date is not None else ""
        raise AssertionError(f"Balance sheet out of balance{suffix}: {snapshot['Balance_Difference']}")
    return snapshot
