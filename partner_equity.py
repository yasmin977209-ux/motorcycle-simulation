"""Chapter 11 partner memo balances rebuilt from the authoritative reference."""

from __future__ import annotations

from constants import PARTNER1_FINAL_SHARE_PCT
from entities import Project


def split_70_30(amount: int) -> tuple[int, int]:
    if not isinstance(amount, int) or isinstance(amount, bool):
        raise TypeError("amount must be an int")
    if amount < 0:
        raise ValueError("amount must not be negative")
    partner1 = (amount * PARTNER1_FINAL_SHARE_PCT) // 100
    return partner1, amount - partner1


def allocate_inflow(project: Project, amount: int) -> tuple[int, int]:
    partner1, partner2 = split_70_30(amount)
    project.partner1_reinvestment_balance += partner1
    project.partner2_reinvestment_balance += partner2
    return partner1, partner2


def consume_partner1_for_expansion(project: Project, amount: int) -> None:
    if amount < 0:
        raise ValueError("partner-1 consumption must not be negative")
    if project.partner1_reinvestment_balance < amount:
        raise ValueError("Partner1_Reinvestment_Balance is insufficient")
    project.partner1_reinvestment_balance -= amount


def assert_memo_nonnegative(project: Project) -> None:
    if project.partner1_reinvestment_balance < 0:
        raise AssertionError("Partner1_Reinvestment_Balance became negative")
    if project.partner2_reinvestment_balance < 0:
        raise AssertionError("Partner2_Reinvestment_Balance became negative")


def final_entitlements(project: Project) -> tuple[int, int]:
    if project.final_net_project_equity is None:
        raise ValueError("final equity is not available")
    return split_70_30(project.final_net_project_equity)


__all__ = [
    "split_70_30",
    "allocate_inflow",
    "consume_partner1_for_expansion",
    "assert_memo_nonnegative",
    "final_entitlements",
]
