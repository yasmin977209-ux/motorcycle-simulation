from __future__ import annotations

from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

import daily_engine
from constants import BIKE_GROSS_ASSET_COST
from accounting import accrue_rent
from entities import Bike, Contract, ContractType, Project, BikeSource, BikeState
from closure import execute_dynamic_closure


ROOT = Path(__file__).resolve().parents[1]
APP_FILES = [
    p for p in ROOT.glob("*.py")
    if p.name not in {"test_acceptance_16_full.py", "test_acceptance_16_v2.py"}
]


def _new_project() -> Project:
    return daily_engine.create_initial_project(recovery_rate_pct=100)


def _add_active_contract(
    project: Project,
    *,
    contract_type: str = "PRIMARY",
    start: date = date(2029, 1, 2),
    state: str | None = None,
    maturity: date | None = None,
    due: int = 0,
    paid: int = 0,
) -> tuple[Bike, Contract]:
    bike = Bike(
        bike_id=f"T{len(project.bikes)+1:06d}",
        source=BikeSource.INITIAL,
        purchase_date=date(2026, 12, 26),
        scheduled_ready_date=start,
        funding_completion_date=date(2026, 12, 26),
        actual_ready_date=start,
        prep_paid=True,
        customs_paid=True,
        gross_cost=BIKE_GROSS_ASSET_COST,
        accumulated_depreciation=0,
        net_book_value=BIKE_GROSS_ASSET_COST,
        current_state=BikeState.PREP,
    )
    project.bikes.append(bike)
    contract = daily_engine._new_contract(
        project, bike, ContractType(contract_type), start
    )
    if due:
        accrue_rent(project, contract, amount=due)
    if paid:
        contract.total_paid = paid
        project.project_cash += paid
        project.accounts_receivable -= paid
    if maturity is not None:
        contract.maturity_date = maturity
    bike.current_state = BikeState(
        state
        or ("ACTIVE_PRIMARY" if contract_type == "PRIMARY" else "ACTIVE_SECONDARY")
    )
    bike.delivery_date = start
    bike.current_contract_id = contract.contract_id
    bike.current_tenant_id = contract.tenant_id
    return bike, contract


def _mark_all_initial_owned(project: Project) -> None:
    for bike in project.bikes:
        bike.current_state = BikeState.OWNED_TRANSFERRED
        bike.current_contract_id = None
        bike.current_tenant_id = None
        old_accumulated = bike.accumulated_depreciation
        project.accumulated_depreciation -= old_accumulated
        writeoff_amount = bike.gross_cost - old_accumulated
        project.asset_writeoff_expense += writeoff_amount
        project.gross_bike_assets -= bike.gross_cost
        bike.net_book_value = 0
        bike.accumulated_depreciation = bike.gross_cost


def _run_days(
    project: Project,
    start: date,
    end: date,
    *,
    p: float = 1.0,
    scenario: str = "C100_G100",
    trial_id: int = 1,
) -> Project:
    current = start
    while current <= end and not project.simulation_stopped:
        daily_engine.run_day(
            project,
            current,
            collection_probability=p,
            scenario_id=scenario,
            trial_id=trial_id,
        )
        current += timedelta(days=1)
    return project


@lru_cache(maxsize=1)
def _deterministic_trial_cached() -> Project:
    return daily_engine.run_deterministic_trial(
        recovery_rate_pct=100,
        trial_id=1,
        scenario_id="C100_G100",
    )


def _source_text(paths=None) -> str:
    selected = paths or APP_FILES
    return "\n".join(path.read_text(encoding="utf-8") for path in selected)


def _event_types(project: Project):
    return [event.event_type for event in project.event_log]


def invoke_closure_and_get_state(
    project: Project,
    current_date: date,
    recovery_rate_pct: int,
) -> dict[str, object]:
    execute_dynamic_closure(project, current_date, recovery_rate_pct)
    return {
        "final_close_date": project.final_close_date,
        "final_net_project_equity": project.final_net_project_equity,
        "partner1_final_entitlement": project.partner1_final_entitlement,
        "partner2_final_entitlement": project.partner2_final_entitlement,
    }
