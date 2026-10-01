"""Chapter 10 — accrual accounting and daily balance-sheet controls."""
from __future__ import annotations
from entities import Project

LIABILITIES = 0

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
