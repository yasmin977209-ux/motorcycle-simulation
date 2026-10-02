from __future__ import annotations

from datetime import date, timedelta
from dataclasses import asdict, dataclass
import numpy as np
import hashlib
import json
import multiprocessing

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



def _run_single_trial_worker(
    scenario_id: str,
    trial_id: int,
    master_seed: int,
) -> tuple[TrialResult, list[dict[str, object]]]:
    return run_single_trial(
        scenario_id,
        trial_id,
        master_seed=master_seed,
    )


def run_trials_parallel(
    scenario_id: str,
    trial_ids: tuple[int, ...] | list[int],
    n_workers: int,
    *,
    master_seed: int = constants.MASTER_SEED,
) -> tuple[list[TrialResult], dict[int, list[dict[str, object]]]]:
    if n_workers < 1:
        raise ValueError("n_workers must be >= 1")
    jobs = [(scenario_id, int(trial_id), master_seed) for trial_id in trial_ids]
    ctx = multiprocessing.get_context("spawn")
    with ctx.Pool(processes=n_workers) as pool:
        outputs = pool.starmap(_run_single_trial_worker, jobs)
    outputs.sort(key=lambda item: item[0].trial_id)
    results = [item[0] for item in outputs]
    daily_rows_by_trial = {
        result.trial_id: daily_rows
        for result, daily_rows in outputs
    }
    return results, daily_rows_by_trial


def _canonical_jsonable(value: object) -> object:
    if isinstance(value, float):
        return value.hex()
    if isinstance(value, dict):
        return {
            str(key): _canonical_jsonable(value[key])
            for key in sorted(value, key=str)
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_jsonable(item) for item in value]
    return value


def _fingerprint_json_lines(records: list[object]) -> str:
    payload = "\n".join(
        json.dumps(
            _canonical_jsonable(record),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        for record in records
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def fingerprint_trial_results(results: list[TrialResult]) -> str:
    records = [
        asdict(result)
        for result in sorted(results, key=lambda item: item.trial_id)
    ]
    return _fingerprint_json_lines(records)


def fingerprint_daily_distribution(
    distribution: list[dict[str, object]],
) -> str:
    ordered = sorted(
        distribution,
        key=lambda row: (str(row["date"]), str(row["quantile_name"])),
    )
    return _fingerprint_json_lines(ordered)


def fingerprint_per_trial_slices(
    slices: dict[int, list[dict[str, object]]],
) -> str:
    ordered: list[dict[str, object]] = []
    for trial_id in sorted(slices):
        for row in sorted(
            slices[trial_id],
            key=lambda item: str(item["date"]),
        ):
            ordered.append(
                {"trial_id": trial_id, **row}
            )
    return _fingerprint_json_lines(ordered)



def build_daily_distribution(
    results_list: list[TrialResult],
    slices_by_trial: dict[int, list[dict[str, object]]],
) -> list[dict[str, object]]:
    quantile_names = ("P10", "P25", "P50", "P75", "P90")
    quantiles = (0.10, 0.25, 0.50, 0.75, 0.90)
    metric_names = (
        "Cash",
        "Net_Equity",
        "Active_Bikes",
        "Owned_Transferred_Bikes",
        "Pending_Claims",
    )
    trial_by_id = {result.trial_id: result for result in results_list}
    if set(trial_by_id) != set(slices_by_trial):
        raise ValueError("results_list and slices_by_trial trial_ids differ")

    rows_by_trial_date = {
        trial_id: {row["date"]: row for row in rows}
        for trial_id, rows in slices_by_trial.items()
    }
    all_dates = sorted(
        {
            row["date"]
            for rows in slices_by_trial.values()
            for row in rows
        }
    )
    if not all_dates:
        return []

    start = date.fromisoformat(all_dates[0])
    end = date.fromisoformat(all_dates[-1])
    expected_dates = [
        (start + timedelta(days=index)).isoformat()
        for index in range((end - start).days + 1)
    ]
    if all_dates != expected_dates:
        raise AssertionError("DAILY_DISTRIBUTION contains date gaps")

    distribution: list[dict[str, object]] = []
    for current_date in expected_dates:
        active_trial_ids = [
            trial_id
            for trial_id, result in trial_by_id.items()
            if result.final_close_date is None
            or result.final_close_date >= current_date
        ]
        day_rows = []
        for trial_id in active_trial_ids:
            row = rows_by_trial_date[trial_id].get(current_date)
            if row is None:
                raise AssertionError(
                    f"missing active daily slice: trial_id={trial_id} date={current_date}"
                )
            day_rows.append(row)

        if not day_rows:
            raise AssertionError(f"no active trials on {current_date}")

        payloads = {
            metric: np.asarray([row[metric] for row in day_rows])
            for metric in metric_names
        }
        active_trial_count = len(day_rows)
        for quantile_name, quantile in zip(quantile_names, quantiles):
            record = {
                "date": current_date,
                "quantile_name": quantile_name,
                "active_trial_count": active_trial_count,
            }
            record.update(
                {
                    metric: np.quantile(
                        values,
                        quantile,
                        method="linear",
                    ).item()
                    for metric, values in payloads.items()
                }
            )
            distribution.append(record)

    return distribution



class RepresentativeSelection(dict[str, int]):
    @property
    def p50_trial_id(self) -> int:
        return self["p50_trial_id"]

    @property
    def p10_trial_id(self) -> int:
        return self["p10_trial_id"]

    @property
    def p90_trial_id(self) -> int:
        return self["p90_trial_id"]

    @property
    def loss_case_trial_id(self) -> int:
        return self["loss_case_trial_id"]


def select_representative_trials(
    results: list[TrialResult],
    quantiles: tuple[float, ...] = (0.10, 0.50, 0.90),
) -> RepresentativeSelection:
    if not results:
        raise ValueError("results must not be empty")
    if tuple(quantiles) != (0.10, 0.50, 0.90):
        raise ValueError("quantiles must be exactly (0.10, 0.50, 0.90)")

    equities = np.asarray(
        [result.final_net_project_equity for result in results],
        dtype=np.float64,
    )

    def nearest_trial(target_quantile: float) -> int:
        target = np.quantile(
            equities,
            target_quantile,
            method="linear",
        )
        return min(
            results,
            key=lambda result: (
                abs(result.final_net_project_equity - target),
                result.trial_id,
            ),
        ).trial_id

    return RepresentativeSelection(
        p50_trial_id=nearest_trial(0.50),
        p10_trial_id=nearest_trial(0.10),
        p90_trial_id=nearest_trial(0.90),
        loss_case_trial_id=min(
            results,
            key=lambda result: (
                result.final_net_project_equity,
                result.trial_id,
            ),
        ).trial_id,
    )


__all__ = [
    "TrialResult",
    "parse_scenario_id",
    "run_single_trial",
    "run_trials_sequentially",
    "run_trials_parallel",
    "fingerprint_trial_results",
    "fingerprint_daily_distribution",
    "fingerprint_per_trial_slices",
    "build_daily_distribution",
    "RepresentativeSelection",
    "select_representative_trials",
]
