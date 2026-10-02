from __future__ import annotations

from dataclasses import dataclass

import constants
import daily_engine
import rng
from entities import BikeState, ClaimStatus, Project


def parse_scenario_id(scenario_id: str) -> tuple[float, int]:
    try:
        collection_part, recovery_part = scenario_id.split("_", 1)
        if not collection_part.startswith("C"):
            raise ValueError
        if not recovery_part.startswith("G"):
            raise ValueError
        collection_percent = int(collection_part[1:])
        recovery_rate_pct = int(recovery_part[1:])
    except (AttributeError, TypeError, ValueError):
        raise ValueError(
            f"Unsupported scenario_id: {scenario_id!r}"
        ) from None

    collection_probability = collection_percent / 100.0

    if collection_probability not in constants.COLLECTION_PROBABILITIES:
        raise ValueError(
            f"Unsupported collection probability in scenario_id: {scenario_id!r}"
        )

    if recovery_rate_pct not in constants.GUARANTEE_RECOVERY_RATES:
        raise ValueError(
            f"Unsupported recovery rate in scenario_id: {scenario_id!r}"
        )

    if rng.scenario_id(collection_probability, recovery_rate_pct) != scenario_id:
        raise ValueError(
            f"Non-canonical scenario_id: {scenario_id!r}"
        )

    return collection_probability, recovery_rate_pct


@dataclass(frozen=True)
class TrialResult:
    scenario_id: str
    collection_probability: float
    recovery_rate_pct: int
    trial_id: int
    final_close_date: str | None
    final_net_project_equity: int
    final_cash: int
    cumulative_project_profit: int
    operating_net_profit: int
    termination_count: int
    secondary_cycle_count: int
    owned_bikes: int
    held_assets: int
    total_operating_revenue: int
    bad_debt: int
    guarantee_recovered: int
    partner1_final_entitlement: int
    partner2_final_entitlement: int


def _daily_snapshot(
    project: Project,
    current_date,
    trial_id: int,
) -> dict[str, object]:
    return {
        "date": current_date.isoformat(),
        "trial_id": trial_id,
        "Cash": project.project_cash,
        "Capital": project.capital,
        "Retained_Earnings": project.retained_earnings,
        "Net_Equity": project.capital + project.retained_earnings,
        "Active_Bikes": sum(
            1
            for bike in project.bikes
            if bike.current_state in daily_engine.POSSESSION_STATES
        ),
        "Owned_Transferred_Bikes": sum(
            1
            for bike in project.bikes
            if bike.current_state is BikeState.OWNED_TRANSFERRED
        ),
        "Pending_Claims": sum(
            1
            for claim in project.guarantee_claims
            if claim.status is ClaimStatus.PENDING
        ),
        "Final_Close_Date": (
            project.final_close_date.isoformat()
            if project.final_close_date is not None
            else None
        ),
    }


def _trial_result_from_project(
    project: Project,
    *,
    scenario_id: str,
    collection_probability: float,
    recovery_rate_pct: int,
    trial_id: int,
) -> TrialResult:
    if project.final_net_project_equity is None:
        raise AssertionError(
            "simulation finished without final_net_project_equity"
        )
    if project.partner1_final_entitlement is None:
        raise AssertionError(
            "simulation finished without partner1_final_entitlement"
        )
    if project.partner2_final_entitlement is None:
        raise AssertionError(
            "simulation finished without partner2_final_entitlement"
        )

    return TrialResult(
        scenario_id=scenario_id,
        collection_probability=collection_probability,
        recovery_rate_pct=recovery_rate_pct,
        trial_id=trial_id,
        final_close_date=(
            project.final_close_date.isoformat()
            if project.final_close_date is not None
            else None
        ),
        final_net_project_equity=project.final_net_project_equity,
        final_cash=project.project_cash,
        cumulative_project_profit=project.cumulative_project_profit,
        operating_net_profit=project.operating_net_profit,
        termination_count=sum(
            bike.termination_count for bike in project.bikes
        ),
        secondary_cycle_count=sum(
            bike.secondary_cycle_count for bike in project.bikes
        ),
        owned_bikes=sum(
            1
            for bike in project.bikes
            if bike.current_state is BikeState.OWNED_TRANSFERRED
        ),
        held_assets=sum(
            1
            for bike in project.bikes
            if bike.current_state is BikeState.HELD_AS_ASSET
        ),
        total_operating_revenue=project.operating_revenue,
        bad_debt=project.bad_debt_expense,
        guarantee_recovered=sum(
            claim.recovered_amount or 0
            for claim in project.guarantee_claims
        ),
        partner1_final_entitlement=project.partner1_final_entitlement,
        partner2_final_entitlement=project.partner2_final_entitlement,
    )


def run_single_trial(
    scenario_id: str,
    trial_id: int,
    *,
    master_seed: int = constants.MASTER_SEED,
) -> tuple[TrialResult, list[dict[str, object]]]:
    collection_probability, recovery_rate_pct = parse_scenario_id(
        scenario_id
    )

    daily_rows: list[dict[str, object]] = []

    def capture_day(project: Project, current_date) -> None:
        daily_rows.append(
            _daily_snapshot(project, current_date, trial_id)
        )

    project = daily_engine.run_deterministic_trial(
        recovery_rate_pct=recovery_rate_pct,
        trial_id=trial_id,
        scenario_id=scenario_id,
        master_seed=master_seed,
        collection_probability=collection_probability,
        on_day_end=capture_day,
    )

    result = _trial_result_from_project(
        project,
        scenario_id=scenario_id,
        collection_probability=collection_probability,
        recovery_rate_pct=recovery_rate_pct,
        trial_id=trial_id,
    )

    return result, daily_rows


def run_trials_sequentially(
    scenario_id: str,
    trial_ids: tuple[int, ...] | list[int],
    *,
    master_seed: int = constants.MASTER_SEED,
) -> tuple[list[TrialResult], dict[int, list[dict[str, object]]]]:
    results: list[TrialResult] = []
    daily_rows_by_trial: dict[int, list[dict[str, object]]] = {}

    for trial_id in trial_ids:
        result, daily_rows = run_single_trial(
            scenario_id,
            trial_id,
            master_seed=master_seed,
        )
        results.append(result)
        daily_rows_by_trial[trial_id] = daily_rows

    return results, daily_rows_by_trial


__all__ = [
    "TrialResult",
    "parse_scenario_id",
    "run_single_trial",
    "run_trials_sequentially",
]
