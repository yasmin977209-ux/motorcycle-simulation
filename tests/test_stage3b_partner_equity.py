from constants import BIKE_BASE_PURCHASE_COST
from entities import Project
from partner_equity import (
    allocate_inflow,
    assert_memo_nonnegative,
    consume_partner1_for_expansion,
    final_entitlements,
    split_70_30,
)


def test_ch11_eligible_inflow_allocates_seventy_thirty() -> None:
    project = Project.opening()
    assert allocate_inflow(project, 10_000) == (7_000, 3_000)
    assert project.partner1_reinvestment_balance == 7_000
    assert project.partner2_reinvestment_balance == 3_000
    assert_memo_nonnegative(project)


def test_ch11_partner1_consumes_only_partner1_memo() -> None:
    project = Project.opening()
    allocate_inflow(project, 500_000)
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



def test_ch11_split_70_30_assigns_integer_remainder_to_partner2() -> None:
    assert split_70_30(1001) == (700, 301)


def test_ch11_allocate_inflow_is_the_only_memo_balance_allocator() -> None:
    project = Project.opening()
    assert allocate_inflow(project, 1001) == (700, 301)
    assert project.partner1_reinvestment_balance == 700
    assert project.partner2_reinvestment_balance == 301
