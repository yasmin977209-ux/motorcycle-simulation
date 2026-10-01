from constants import BIKE_BASE_PURCHASE_COST
from entities import Project
from partner_equity import (
    assert_memo_nonnegative,
    consume_partner1_for_expansion,
    final_entitlements,
    record_eligible_inflow,
)


def test_ch11_eligible_inflow_allocates_seventy_thirty() -> None:
    project = Project.opening()
    assert record_eligible_inflow(project, 10_000) == (7_000, 3_000)
    assert project.partner1_reinvestment_balance == 7_000
    assert project.partner2_reinvestment_balance == 3_000
    assert_memo_nonnegative(project)


def test_ch11_partner1_consumes_only_partner1_memo() -> None:
    project = Project.opening()
    record_eligible_inflow(project, 500_000)
    consume_partner1_for_expansion(project, BIKE_BASE_PURCHASE_COST)
    assert project.partner1_reinvestment_balance == 0
    assert project.partner2_reinvestment_balance == 150_000
    assert_memo_nonnegative(project)


def test_ch11_final_entitlements_are_not_memo_balances() -> None:
    project = Project.opening()
    project.final_net_project_equity = 12_345
    assert final_entitlements(project) == (8_641, 3_704)
    assert project.partner1_reinvestment_balance == 0
    assert project.partner2_reinvestment_balance == 0
