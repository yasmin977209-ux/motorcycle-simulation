"""Chapter 10 accounting layer rebuilt from the authoritative reference."""

from __future__ import annotations

from datetime import date

from entities import Contract, Project


ROLLFORWARD_FIELDS = {
    "cash": (
        "Opening_Cash",
        "Inflows",
        "Outflows",
        "Closing_Cash",
    ),
    "ar": (
        "Opening_AR",
        "Accruals",
        "Collections",
        "TransfersToGuarantee",
        "Closing_AR",
    ),
    "asset": (
        "Opening_Gross_Bike_Assets",
        "Capitalized_Purchases_And_Customs",
        "Gross_Writeoffs_On_Ownership",
        "Closing_Gross_Bike_Assets",
        "Opening_Accumulated_Depreciation",
        "Depreciation_Expense",
        "AD_Removed_On_Writeoff",
        "Closing_Accumulated_Depreciation",
    ),
    "equity": (
        "Opening_Equity",
        "Operating_Net_Profit",
        "Closing_Equity",
    ),
}


def initialize_accounting(project: Project | None = None) -> Project:
    return Project.opening() if project is None else project


def accrue_rent(project: Project, contract: Contract, amount: int | None = None) -> int:
    rent = contract.daily_rate if amount is None else amount
    if rent < 0:
        raise ValueError("rent amount must not be negative")
    contract.total_due += rent
    if contract.contract_type.value == "PRIMARY":
        project.revenue_primary += rent
    else:
        project.revenue_secondary += rent
    project.accounts_receivable += rent
    return rent


def collect_from_ar(project: Project, amount: int) -> int:
    if amount < 0 or amount > project.accounts_receivable:
        raise ValueError("collection amount is outside Accounts_Receivable")
    project.project_cash += amount
    project.accounts_receivable -= amount
    return amount


def settle_guarantee_accounting(
    project: Project,
    claim_amount: int,
    recovered_amount: int,
    bad_debt_amount: int,
) -> None:
    if min(claim_amount, recovered_amount, bad_debt_amount) < 0:
        raise ValueError("guarantee accounting amounts must not be negative")
    if recovered_amount + bad_debt_amount != claim_amount:
        raise ValueError("recovered + bad debt must equal claim amount")
    if project.guarantee_claim_receivable < claim_amount:
        raise ValueError("claim exceeds Guarantee_Claim_Receivable")
    project.project_cash += recovered_amount
    project.guarantee_claim_receivable -= claim_amount
    project.bad_debt_expense += bad_debt_amount


def operating_revenue(project: Project) -> int:
    return (
        project.revenue_primary
        + project.revenue_secondary
        + project.revenue_settlement
        + project.revenue_friday_fee
    )


def operating_expenses(project: Project) -> int:
    return (
        project.expense_depreciation
        + project.expense_oil_service
        + project.expense_prep
        + project.bad_debt_expense
        + project.asset_writeoff_expense
    )


def operating_net_profit(project: Project) -> int:
    return operating_revenue(project) - operating_expenses(project)


def refresh_profit(project: Project) -> int:
    project.operating_revenue = operating_revenue(project)
    project.operating_expenses = operating_expenses(project)
    project.operating_net_profit = operating_net_profit(project)
    project.cumulative_project_profit = (
        project.opening_loss + project.operating_net_profit
    )
    project.retained_earnings = project.cumulative_project_profit
    return project.operating_net_profit


def net_bike_assets(project: Project) -> int:
    return project.gross_bike_assets - project.accumulated_depreciation


def balance_sheet_snapshot(project: Project) -> dict[str, int]:
    net_assets = net_bike_assets(project)
    total_assets = (
        project.project_cash
        + project.accounts_receivable
        + project.guarantee_claim_receivable
        + net_assets
    )
    total_equity = project.capital + project.retained_earnings
    return {
        "Cash": project.project_cash,
        "Accounts_Receivable": project.accounts_receivable,
        "Guarantee_Claim_Receivable": project.guarantee_claim_receivable,
        "Gross_Bike_Assets": project.gross_bike_assets,
        "Accumulated_Depreciation": project.accumulated_depreciation,
        "Net_Bike_Assets": net_assets,
        "Total_Assets": total_assets,
        "Total_Equity": total_equity,
        "Liabilities": 0,
        "Balance_Difference": total_assets - total_equity,
    }


def assert_balance_sheet_balanced(
    project: Project,
    current_date: date | None = None,
) -> dict[str, int]:
    snapshot = balance_sheet_snapshot(project)
    if snapshot["Balance_Difference"] != 0:
        raise AssertionError(
            f"balance sheet mismatch on {current_date}: "
            f"{snapshot['Balance_Difference']}"
        )
    return snapshot


def _fixed_record(kind: str, values: dict[str, int]) -> dict[str, int]:
    fields = ROLLFORWARD_FIELDS[kind]
    if set(values) != set(fields):
        raise ValueError(f"invalid {kind} roll-forward fields")
    return {field: values[field] for field in fields}


def record_daily_rollforwards(
    project: Project,
    current_date: date,
    opening: dict[str, int],
    metrics: dict[str, int],
) -> None:
    closing_equity = project.capital + project.retained_earnings
    daily_operating_profit = closing_equity - opening["Opening_Equity"]

    project.cash_rollforward.append(
        _fixed_record(
            "cash",
            {
                "Opening_Cash": opening["Opening_Cash"],
                "Inflows": metrics["cash_inflows"],
                "Outflows": metrics["cash_outflows"],
                "Closing_Cash": project.project_cash,
            },
        )
    )
    project.ar_rollforward.append(
        _fixed_record(
            "ar",
            {
                "Opening_AR": opening["Opening_AR"],
                "Accruals": metrics["ar_accruals"],
                "Collections": metrics["ar_collections"],
                "TransfersToGuarantee": metrics["ar_transfers_to_guarantee"],
                "Closing_AR": project.accounts_receivable,
            },
        )
    )
    project.asset_rollforward.append(
        _fixed_record(
            "asset",
            {
                "Opening_Gross_Bike_Assets": opening["Opening_Gross_Bike_Assets"],
                "Capitalized_Purchases_And_Customs": metrics[
                    "capitalized_purchases_and_customs"
                ],
                "Gross_Writeoffs_On_Ownership": metrics[
                    "gross_writeoffs_on_ownership"
                ],
                "Closing_Gross_Bike_Assets": project.gross_bike_assets,
                "Opening_Accumulated_Depreciation": opening[
                    "Opening_Accumulated_Depreciation"
                ],
                "Depreciation_Expense": metrics["depreciation_expense"],
                "AD_Removed_On_Writeoff": metrics["ad_removed_on_writeoff"],
                "Closing_Accumulated_Depreciation": (
                    project.accumulated_depreciation
                ),
            },
        )
    )
    project.equity_rollforward.append(
        _fixed_record(
            "equity",
            {
                "Opening_Equity": opening["Opening_Equity"],
                "Operating_Net_Profit": daily_operating_profit,
                "Closing_Equity": closing_equity,
            },
        )
    )
    project.daily_snapshots.append(
        {
            "date": current_date,
            **balance_sheet_snapshot(project),
        }
    )


__all__ = [
    "ROLLFORWARD_FIELDS",
    "initialize_accounting",
    "accrue_rent",
    "collect_from_ar",
    "settle_guarantee_accounting",
    "operating_revenue",
    "operating_expenses",
    "operating_net_profit",
    "refresh_profit",
    "net_bike_assets",
    "balance_sheet_snapshot",
    "assert_balance_sheet_balanced",
    "record_daily_rollforwards",
]
