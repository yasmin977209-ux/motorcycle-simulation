"""Chapter 11 partner memo balances rebuilt from the authoritative reference."""

from __future__ import annotations

from constants import PARTNER1_FINAL_SHARE_PCT, PARTNER2_FINAL_SHARE_PCT
from entities import Project


def record_eligible_inflow(project: Project, amount: int) -> tuple[int, int]:
    if amount < 0:
        raise ValueError("eligible inflow must not be negative")
    p1 = (amount * PARTNER1_FINAL_SHARE_PCT) // 100
    p2 = (amount * PARTNER2_FINAL_SHARE_PCT) // 100
    project.partner1_reinvestment_balance += p1
    project.partner2_reinvestment_balance += p2
    return p1, p2


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
    p1 = (project.final_net_project_equity * PARTNER1_FINAL_SHARE_PCT) // 100
    p2 = project.final_net_project_equity - p1
    return p1, p2


__all__ = [
    "record_eligible_inflow",
    "consume_partner1_for_expansion",
    "assert_memo_nonnegative",
    "final_entitlements",
]
