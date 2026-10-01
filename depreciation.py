"""Chapter 8 depreciation and ownership write-off rules."""

from __future__ import annotations

from dataclasses import dataclass

from constants import DEPRECIATION_RATE_PER_DAY, MAX_DEPRECIATION


@dataclass(frozen=True)
class DepreciationResult:
    depreciation_recorded: int
    accumulated_depreciation_after: int
    usage_days_after: int
    net_book_value_after: int
    project_accumulated_depreciation_delta: int
    depreciation_expense: int


@dataclass(frozen=True)
class OwnershipWriteoffResult:
    old_accumulated_depreciation: int
    writeoff_amount: int
    project_accumulated_depreciation_delta: int
    project_gross_asset_delta: int
    expense_asset_writeoff: int
    bike_accumulated_depreciation_after: int
    bike_net_book_value_after: int


def apply_daily_depreciation(
    gross_cost: int,
    accumulated_depreciation: int,
    in_tenant_possession: bool,
) -> DepreciationResult:
    """Apply one day of use-based depreciation, including Friday."""
    if gross_cost < 0:
        raise ValueError("gross_cost must not be negative")
    if accumulated_depreciation < 0 or accumulated_depreciation > gross_cost:
        raise ValueError("accumulated_depreciation is outside gross_cost bounds")

    depreciation_cap = min(gross_cost, MAX_DEPRECIATION)
    current_accumulated = min(accumulated_depreciation, depreciation_cap)
    current_net = max(0, gross_cost - current_accumulated)

    if not in_tenant_possession or current_net == 0:
        return DepreciationResult(
            depreciation_recorded=0,
            accumulated_depreciation_after=current_accumulated,
            usage_days_after=0,
            net_book_value_after=current_net,
            project_accumulated_depreciation_delta=0,
            depreciation_expense=0,
        )

    depreciation = min(
        DEPRECIATION_RATE_PER_DAY,
        depreciation_cap - current_accumulated,
    )
    accumulated_after = current_accumulated + depreciation
    return DepreciationResult(
        depreciation_recorded=depreciation,
        accumulated_depreciation_after=accumulated_after,
        usage_days_after=1 if depreciation > 0 else 0,
        net_book_value_after=max(0, gross_cost - accumulated_after),
        project_accumulated_depreciation_delta=depreciation,
        depreciation_expense=depreciation,
    )


def apply_ownership_writeoff(
    gross_cost: int,
    accumulated_depreciation: int,
) -> OwnershipWriteoffResult:
    """Write off the gross asset and release the old accumulated depreciation."""
    if gross_cost < 0:
        raise ValueError("gross_cost must not be negative")
    if accumulated_depreciation < 0 or accumulated_depreciation > gross_cost:
        raise ValueError("accumulated_depreciation is outside gross_cost bounds")

    old_accumulated = accumulated_depreciation
    writeoff_amount = gross_cost - old_accumulated
    return OwnershipWriteoffResult(
        old_accumulated_depreciation=old_accumulated,
        writeoff_amount=writeoff_amount,
        project_accumulated_depreciation_delta=-old_accumulated,
        project_gross_asset_delta=-gross_cost,
        expense_asset_writeoff=writeoff_amount,
        bike_accumulated_depreciation_after=gross_cost,
        bike_net_book_value_after=0,
    )


__all__ = [
    "DepreciationResult",
    "OwnershipWriteoffResult",
    "apply_daily_depreciation",
    "apply_ownership_writeoff",
]
