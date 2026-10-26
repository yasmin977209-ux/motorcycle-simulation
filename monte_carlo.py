from __future__ import annotations

from datetime import date, timedelta
from dataclasses import asdict, dataclass, replace
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
from fractions import Fraction
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
    trial_fingerprint: str = ""
    rng_checksum: int = 0
    rng_draw_count: int = 0
    rng_checksum_fingerprint_sha256: str | None = None


def _daily_snapshot(
    project: Project,
    current_date,
    trial_id: int,
) -> dict[str, object]:
    return {
        "date": current_date.isoformat(),
        "trial_id": trial_id,
        "Cash": project.project_cash,
        "Partner1_Reinvestment_Balance": project.partner1_reinvestment_balance,
        "Partner2_Reinvestment_Balance": project.partner2_reinvestment_balance,
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
    master_seed: int = constants.MASTER_SEED,
    source_sha: str | None = None,
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

    result = TrialResult(
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
        rng_checksum=project.rng_checksum,
        rng_draw_count=project.rng_draw_count,
        rng_checksum_fingerprint_sha256=(
            rng.rng_audit_fingerprint(
                source_sha=source_sha,
                master_seed=master_seed,
                scenario_id=scenario_id,
                trial_id=trial_id,
                rng_checksum=project.rng_checksum,
                rng_draw_count=project.rng_draw_count,
            )
            if source_sha is not None
            else None
        ),
    )
    return replace(result, trial_fingerprint=trial_fingerprint(result))


def run_single_trial(
    scenario_id: str,
    trial_id: int,
    *,
    master_seed: int = constants.MASTER_SEED,
    source_sha: str | None = None,
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
        master_seed=master_seed,
        source_sha=source_sha,
    )

    return result, daily_rows


def run_trials_sequentially(
    scenario_id: str,
    trial_ids: tuple[int, ...] | list[int],
    *,
    master_seed: int = constants.MASTER_SEED,
    source_sha: str | None = None,
) -> tuple[list[TrialResult], dict[int, list[dict[str, object]]]]:
    results: list[TrialResult] = []
    daily_rows_by_trial: dict[int, list[dict[str, object]]] = {}

    for trial_id in trial_ids:
        result, daily_rows = run_single_trial(
            scenario_id,
            trial_id,
            master_seed=master_seed,
            source_sha=source_sha,
        )
        results.append(result)
        daily_rows_by_trial[trial_id] = daily_rows

    return results, daily_rows_by_trial



def _run_single_trial_worker(
    scenario_id: str,
    trial_id: int,
    master_seed: int,
    source_sha: str | None = None,
) -> tuple[TrialResult, list[dict[str, object]]]:
    return run_single_trial(
        scenario_id,
        trial_id,
        master_seed=master_seed,
        source_sha=source_sha,
    )


def run_trials_parallel(
    scenario_id: str,
    trial_ids: tuple[int, ...] | list[int],
    n_workers: int,
    *,
    master_seed: int = constants.MASTER_SEED,
    source_sha: str | None = None,
) -> tuple[list[TrialResult], dict[int, list[dict[str, object]]]]:
    if n_workers < 1:
        raise ValueError("n_workers must be >= 1")
    jobs = [(scenario_id, int(trial_id), master_seed, source_sha) for trial_id in trial_ids]
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


def _financial_trial_record(
    result: TrialResult, *, include_trial_id: bool
) -> dict[str, object]:
    record = asdict(result)
    for field_name in (
        "trial_fingerprint",
        "rng_checksum",
        "rng_draw_count",
        "rng_checksum_fingerprint_sha256",
    ):
        record.pop(field_name, None)
    if not include_trial_id:
        record.pop("trial_id", None)
    return record


_FINANCIAL_RESULT_FIELDS = (
    "final_close_date",
    "final_net_project_equity",
    "final_cash",
    "cumulative_project_profit",
    "operating_net_profit",
    "termination_count",
    "secondary_cycle_count",
    "owned_bikes",
    "held_assets",
    "total_operating_revenue",
    "bad_debt",
    "guarantee_recovered",
    "partner1_final_entitlement",
    "partner2_final_entitlement",
)


def _financial_outcome_record(result: TrialResult) -> dict[str, object]:
    """Select outcome fields only, excluding scenario/trial identity and RNG audit."""
    return {
        field_name: getattr(result, field_name)
        for field_name in _FINANCIAL_RESULT_FIELDS
    }


def trial_fingerprint(result: TrialResult) -> str:
    """SHA-256 of financial outcomes only; not trial/scenario identity or RNG audit."""
    return _fingerprint_json_lines([_financial_outcome_record(result)])


def financial_path_fingerprint(result: TrialResult) -> str:
    """Compatibility name for the exact same financial-outcome identity."""
    return trial_fingerprint(result)


def fingerprint_trial_results(results: list[TrialResult]) -> str:
    records = [
        _financial_trial_record(result, include_trial_id=True)
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



def _daily_fraction_display(value: Fraction) -> str:
    """Return the normative display string; exact numerator/denominator stay alongside it."""
    if value.denominator == 1:
        return str(value.numerator)
    with localcontext() as context:
        context.prec = constants.REPORT_DECIMAL_PRECISION
        decimal_value = Decimal(value.numerator) / Decimal(value.denominator)
        places = Decimal(1).scaleb(-constants.REPORT_DECIMAL_PLACES)
        return str(decimal_value.quantize(places, rounding=ROUND_HALF_EVEN))


def _linear_quantile_fraction(values: list[int], q: Fraction) -> Fraction:
    """Exact linear/type-7 percentile over integer observations."""
    if not values:
        raise ValueError("DAILY_DISTRIBUTION_SAMPLE_EMPTY")
    if any(type(value) is not int for value in values):
        raise TypeError("DAILY_DISTRIBUTION_REQUIRES_INTEGER_VALUES")
    ordered = sorted(values)
    position = Fraction(len(ordered) - 1) * q
    lower_index = position.numerator // position.denominator
    remainder = position - lower_index
    upper_index = min(lower_index + 1, len(ordered) - 1)
    return (
        Fraction(ordered[lower_index]) * (1 - remainder)
        + Fraction(ordered[upper_index]) * remainder
    )


def build_daily_distribution(
    results_list: list[TrialResult],
    slices_by_trial: dict[int, list[dict[str, object]]],
    *,
    population_mode: str = "ACTIVE_ONLY",
) -> list[dict[str, object]]:
    """Build daily percentile rows with exact Fractions and an explicit population rule.

    ACTIVE_ONLY excludes trials after their recorded close date. The
    ALL_TRIALS_CARRY_FORWARD population retains all trials and carries the last
    recorded daily state forward after each trial closes.
    """
    if population_mode not in constants.DAILY_DISTRIBUTION_POPULATION_MODES:
        raise ValueError("DAILY_DISTRIBUTION_POPULATION_MODE_INVALID")
    metric_names = (
        "Cash",
        "Net_Equity",
        "Active_Bikes",
        "Owned_Transferred_Bikes",
        "Pending_Claims",
    )
    trial_by_id = {result.trial_id: result for result in results_list}
    if not trial_by_id or set(trial_by_id) != set(slices_by_trial):
        raise ValueError("results_list and slices_by_trial trial_ids differ")

    rows_by_trial_date = {
        trial_id: {str(row["date"]): row for row in rows}
        for trial_id, rows in slices_by_trial.items()
    }
    last_row_by_trial = {}
    for trial_id, rows in rows_by_trial_date.items():
        if not rows:
            raise ValueError("DAILY_DISTRIBUTION_TRIAL_HAS_NO_DAILY_ROWS")
        last_date = max(rows)
        last_row_by_trial[trial_id] = (last_date, rows[last_date])

    all_dates = sorted({
        str(row["date"])
        for rows in slices_by_trial.values()
        for row in rows
    })
    if not all_dates:
        return []

    start_date = date.fromisoformat(all_dates[0])
    end_date = date.fromisoformat(all_dates[-1])
    expected_dates = [
        (start_date + timedelta(days=index)).isoformat()
        for index in range((end_date - start_date).days + 1)
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
        selected_trial_ids = (
            active_trial_ids
            if population_mode == "ACTIVE_ONLY"
            else sorted(trial_by_id)
        )
        if not selected_trial_ids:
            raise AssertionError("DAILY_DISTRIBUTION has no active trials")

        day_rows = []
        for trial_id in sorted(selected_trial_ids):
            row = rows_by_trial_date[trial_id].get(current_date)
            if row is None and population_mode == "ALL_TRIALS_CARRY_FORWARD":
                result = trial_by_id[trial_id]
                last_date, last_row = last_row_by_trial[trial_id]
                if (
                    result.final_close_date is not None
                    and result.final_close_date < current_date
                    and last_date < current_date
                ):
                    row = last_row
            if row is None:
                raise AssertionError(
                    f"missing daily slice: trial_id={trial_id} date={current_date} "
                    f"population_mode={population_mode}"
                )
            day_rows.append(row)

        for quantile_name, quantile_pct in constants.DAILY_DISTRIBUTION_PERCENTILES:
            quantile = Fraction(quantile_pct, constants.REPORT_PERCENT_DENOMINATOR)
            record: dict[str, object] = {
                "scenario_id": next(iter(trial_by_id.values())).scenario_id,
                "date": current_date,
                "quantile_name": quantile_name,
                "population_mode": population_mode,
                "population_count": len(day_rows),
                "active_trial_count": len(active_trial_ids),
            }
            for metric in metric_names:
                exact_value = _linear_quantile_fraction(
                    [row[metric] for row in day_rows], quantile
                )
                # String display plus integer numerator/denominator columns makes
                # Parquet schema stable without converting fractional statistics to float.
                record[metric] = _daily_fraction_display(exact_value)
                record[f"{metric}_exact_numerator"] = exact_value.numerator
                record[f"{metric}_exact_denominator"] = exact_value.denominator
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

    @property
    def max_case_trial_id(self) -> int:
        return self["max_case_trial_id"]


def select_representative_trials(
    results: list[TrialResult],
    quantiles: tuple[float, ...] = (0.10, 0.50, 0.90),
) -> RepresentativeSelection:
    if not results:
        raise ValueError("results must not be empty")
    if tuple(quantiles) != (0.10, 0.50, 0.90):
        raise ValueError("quantiles must be exactly (0.10, 0.50, 0.90)")

    equities = sorted(result.final_net_project_equity for result in results)

    def nearest_trial(q: Fraction) -> int:
        position = (len(equities) - 1) * q
        lower_index = position.numerator // position.denominator
        remainder = position - lower_index
        upper_index = min(lower_index + 1, len(equities) - 1)
        target = Fraction(equities[lower_index]) * (1 - remainder) + Fraction(equities[upper_index]) * remainder
        return min(
            results,
            key=lambda result: (
                abs(Fraction(result.final_net_project_equity) - target),
                result.trial_id,
            ),
        ).trial_id

    return RepresentativeSelection(
        p50_trial_id=nearest_trial(Fraction(1, 2)),
        p10_trial_id=nearest_trial(Fraction(1, 10)),
        p90_trial_id=nearest_trial(Fraction(9, 10)),
        loss_case_trial_id=min(
            results,
            key=lambda result: (result.final_net_project_equity, result.trial_id),
        ).trial_id,
        max_case_trial_id=min(
            results,
            key=lambda result: (-result.final_net_project_equity, result.trial_id),
        ).trial_id,
    )


__all__ = [
    "TrialResult",
    "parse_scenario_id",
    "run_single_trial",
    "run_trials_sequentially",
    "run_trials_parallel",
    "fingerprint_trial_results",
    "trial_fingerprint",
    "financial_path_fingerprint",
    "fingerprint_daily_distribution",
    "fingerprint_per_trial_slices",
    "build_daily_distribution",
    "RepresentativeSelection",
    "select_representative_trials",
]
