from __future__ import annotations

import argparse
import gzip
import json
import math
import os
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from scipy.stats import t

import constants
import monte_carlo
from scripts.stage7_state import StateIntegrityError, StateStore
from scripts.stage7_stability import (
    STATISTICAL_ESCALATION_POLICY_ID,
    STATISTICAL_ESCALATION_MULTIPLIER,
    evaluate_gate_a as evaluate_stage7_gate_a,
    filter_statistical_history,
    hydrate_p50_history,
    next_statistical_checkpoint,
    p50_history_ready,
    p50_requires_n2400,
)


TRIALS_PARQUET = "trials_summary.parquet"
TRIALS_JSONL_GZ = "trials_summary.jsonl.gz"
STATE_JSON = "state.json"
STATISTICS_JSON = "statistics.json"
DAILY_SLICES_PARQUET = "daily_slices.parquet"

STABILITY_FIELDS = (
    "final_net_project_equity",
    "partner1_final_entitlement",
    "partner2_final_entitlement",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Stage 8 batch runner with optional Stage 7 checkpoint resume."
    )
    parser.add_argument(
        "--start-trial-id",
        type=int,
        default=1,
        help="First trial id for a new dataset; resume mode overrides this with checkpoint next_trial_id.",
    )
    parser.add_argument(
        "--resume-from-checkpoint",
        action="store_true",
        default=False,
        help="Resume explicitly from stage7-state/<scenario>.",
    )
    parser.add_argument(
        "--scenario",
        required=True,
    )
    parser.add_argument(
        "--trials",
        type=int,
        required=True,
        help="Number of ADDITIONAL trials to run starting from start-trial-id",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Working directory for batch outputs and resumable state.",
    )
    parser.add_argument(
        "--excel-dataset-root",
        default=None,
        help=(
            "Optional dataset root consumed by scripts/excel_builder.py. "
            "Writes <root>/<scenario>/trial_results.parquet and "
            "daily_distribution.parquet, plus raw daily slices and an identity manifest."
        ),
    )
    parser.add_argument(
        "--master-seed",
        type=int,
        default=constants.MASTER_SEED,
    )
    return parser


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    args = build_parser().parse_args(argv)

    if args.start_trial_id < 1:
        raise ValueError("--start-trial-id must be >= 1")
    if args.trials < 1:
        raise ValueError("--trials must be >= 1")

    monte_carlo.parse_scenario_id(args.scenario)

    return args


def _atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except Exception:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass
        raise


def _atomic_write_json(path: Path, value: object) -> None:
    payload = (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")
    _atomic_write_bytes(path, payload)


def _write_dataset(
    results: list[monte_carlo.TrialResult],
    output_dir: Path,
) -> None:
    ordered = sorted(results, key=lambda item: item.trial_id)
    records = [asdict(result) for result in ordered]

    parquet_target = output_dir / TRIALS_PARQUET
    parquet_tmp = output_dir / f".{TRIALS_PARQUET}.tmp"
    table = pa.Table.from_pylist(records)
    pq.write_table(table, parquet_tmp)
    os.replace(parquet_tmp, parquet_target)

    jsonl_payload = "\n".join(
        json.dumps(
            record,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        for record in records
    )
    if jsonl_payload:
        jsonl_payload += "\n"

    with tempfile.NamedTemporaryFile(
        mode="wb",
        prefix=f".{TRIALS_JSONL_GZ}.",
        suffix=".tmp",
        dir=output_dir,
        delete=False,
    ) as temporary:
        temporary_path = Path(temporary.name)

    try:
        with gzip.open(temporary_path, "wb") as handle:
            handle.write(jsonl_payload.encode("utf-8"))
        os.replace(temporary_path, output_dir / TRIALS_JSONL_GZ)
    except Exception:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass
        raise


def _load_dataset(output_dir: Path) -> list[monte_carlo.TrialResult]:
    path = output_dir / TRIALS_PARQUET
    if not path.exists():
        return []

    results = [
        monte_carlo.TrialResult(**row)
        for row in pq.read_table(path).to_pylist()
    ]
    return sorted(results, key=lambda item: item.trial_id)



def _load_daily_slices(output_dir: Path) -> dict[int, list[dict[str, object]]]:
    """Load persisted raw daily rows for completed trials without replaying them."""
    path = output_dir / DAILY_SLICES_PARQUET
    if not path.exists():
        return {}

    slices: dict[int, list[dict[str, object]]] = {}
    for record in pq.read_table(path).to_pylist():
        record = dict(record)
        try:
            trial_id = int(record.pop("trial_id"))
        except (KeyError, TypeError, ValueError) as exc:
            raise StateIntegrityError(
                "daily_slices.parquet contains a missing or invalid trial_id"
            ) from exc
        slices.setdefault(trial_id, []).append(record)

    for rows in slices.values():
        rows.sort(key=lambda row: str(row.get("date", "")))
    return slices


def _validate_daily_slices(
    results: list[monte_carlo.TrialResult],
    slices_by_trial: dict[int, list[dict[str, object]]],
) -> None:
    expected_ids = {int(result.trial_id) for result in results}
    if expected_ids != set(slices_by_trial):
        raise StateIntegrityError(
            "daily slice trial IDs differ from completed trial dataset; refusing to replay completed trials"
        )

    required_fields = {
        "date", "Cash", "Net_Equity", "Active_Bikes",
        "Owned_Transferred_Bikes", "Pending_Claims", "Final_Close_Date",
    }
    from datetime import date

    for trial_id, rows in slices_by_trial.items():
        if not rows:
            raise StateIntegrityError(
                f"daily slices are empty for completed trial_id={trial_id}"
            )
        dates: list[str] = []
        for row in rows:
            missing = required_fields.difference(row)
            if missing:
                raise StateIntegrityError(
                    f"daily slice is missing Excel fields for trial_id={trial_id}: {sorted(missing)}"
                )
            current_trial_id = row.get("trial_id", trial_id)
            if int(current_trial_id) != trial_id:
                raise StateIntegrityError(
                    f"daily slice trial_id mismatch: expected={trial_id}, actual={current_trial_id}"
                )
            current_date = row.get("date")
            if not isinstance(current_date, str):
                raise StateIntegrityError(
                    f"daily slice date must be ISO text for trial_id={trial_id}"
                )
            try:
                parsed_date = date.fromisoformat(current_date)
            except ValueError as exc:
                raise StateIntegrityError(
                    f"daily slice date is not ISO format for trial_id={trial_id}: {current_date!r}"
                ) from exc
            if parsed_date.isoformat() != current_date:
                raise StateIntegrityError(
                    f"daily slice date is not canonical ISO format for trial_id={trial_id}: {current_date!r}"
                )
            dates.append(current_date)

        if dates != sorted(dates) or len(dates) != len(set(dates)):
            raise StateIntegrityError(
                f"daily slice dates are unordered or duplicated for trial_id={trial_id}"
            )


def _write_daily_slices(
    slices_by_trial: dict[int, list[dict[str, object]]],
    output_dir: Path,
) -> None:
    records = [
        {"trial_id": trial_id, **row}
        for trial_id in sorted(slices_by_trial)
        for row in sorted(slices_by_trial[trial_id], key=lambda item: str(item["date"]))
    ]
    if not records:
        raise StateIntegrityError("cannot persist an empty daily detail dataset")

    path = output_dir / DAILY_SLICES_PARQUET
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    os.close(fd)
    temporary_path = Path(temporary_name)
    try:
        pq.write_table(pa.Table.from_pylist(records), temporary_path)
        os.replace(temporary_path, path)
    except Exception:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass
        raise


def _atomic_write_parquet(path: Path, records: list[dict[str, object]]) -> None:
    if not records:
        raise StateIntegrityError(f"refusing to write an empty Parquet dataset: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    os.close(fd)
    temporary_path = Path(temporary_name)
    try:
        pq.write_table(pa.Table.from_pylist(records), temporary_path)
        os.replace(temporary_path, path)
    except Exception:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass
        raise


def _write_excel_daily_datasets(
    *,
    dataset_root: Path,
    scenario: str,
    results: list[monte_carlo.TrialResult],
    slices_by_trial: dict[int, list[dict[str, object]]],
    state: dict[str, Any],
) -> dict[str, object]:
    """Write the exact per-scenario trial and daily-distribution inputs read by ExcelBuilder.

    This is a daily-data export, not a claim that representative-case, accounting,
    assets, partner, guarantee, contracts, or the full Stage 13 workbook is present.
    """
    _validate_daily_slices(results, slices_by_trial)
    distribution = monte_carlo.build_daily_distribution(results, slices_by_trial)
    if not distribution:
        raise StateIntegrityError("daily distribution is empty")

    scenario_root = dataset_root / scenario
    trial_records = [
        asdict(result) for result in sorted(results, key=lambda item: item.trial_id)
    ]
    daily_slice_records = [
        {"trial_id": trial_id, **row}
        for trial_id in sorted(slices_by_trial)
        for row in sorted(slices_by_trial[trial_id], key=lambda item: str(item["date"]))
    ]
    trial_path = scenario_root / "trial_results.parquet"
    distribution_path = scenario_root / "daily_distribution.parquet"
    raw_daily_path = scenario_root / "daily_trial_slices.parquet"
    _atomic_write_parquet(trial_path, trial_records)
    _atomic_write_parquet(distribution_path, distribution)
    _atomic_write_parquet(raw_daily_path, daily_slice_records)

    history = state.get("stability_history") or []
    last_gate_a = (
        (history[-1].get("gate_a") or {}).get("status", "UNRECORDED")
        if history else "NOT_REACHED"
    )
    manifest: dict[str, object] = {
        "format_version": "1.0",
        "contract": "scripts/excel_builder.py per-scenario trial and daily-distribution inputs",
        "scenario": scenario,
        "source_sha": state.get("source_sha"),
        "master_seed": state.get("master_seed"),
        "trial_count": len(trial_records),
        "trial_id_start": int(trial_records[0]["trial_id"]),
        "trial_id_end": int(trial_records[-1]["trial_id"]),
        "daily_slice_rows": len(daily_slice_records),
        "daily_distribution_rows": len(distribution),
        "trial_results_fingerprint_sha256": monte_carlo.fingerprint_trial_results(results),
        "daily_slices_fingerprint_sha256": monte_carlo.fingerprint_per_trial_slices(slices_by_trial),
        "daily_distribution_fingerprint_sha256": monte_carlo.fingerprint_daily_distribution(distribution),
        "final_status": state.get("final_status"),
        "included_in_final_stats": state.get("included_in_final_stats", False),
        "gate_a_status": last_gate_a,
        "full_excel_delivery": "NOT_ASSERTED_BY_THIS_EXPORT",
    }
    _atomic_write_json(scenario_root / "daily_export_manifest.json", manifest)
    return {
        "trial_results_path": str(trial_path),
        "daily_distribution_path": str(distribution_path),
        "daily_trial_slices_path": str(raw_daily_path),
        "manifest_path": str(scenario_root / "daily_export_manifest.json"),
        "trial_rows": len(trial_records),
        "daily_slice_rows": len(daily_slice_records),
        "daily_distribution_rows": len(distribution),
    }


def _p50_values_by_checkpoint(
    results: list[monte_carlo.TrialResult],
) -> dict[int, float]:
    values: dict[int, float] = {}
    for checkpoint_n in (300, 600, 1200):
        if len(results) < checkpoint_n:
            continue
        sample = np.asarray(
            [item.final_net_project_equity for item in results[:checkpoint_n]],
            dtype=np.float64,
        )
        values[checkpoint_n] = float(
            np.quantile(sample, 0.50, method="linear")
        )
    return values


def _validate_trial_sequence(
    results: list[monte_carlo.TrialResult],
) -> None:
    trial_ids = [result.trial_id for result in results]
    if not trial_ids:
        return
    if trial_ids[0] != 1:
        raise StateIntegrityError(
            f"trial sequence must start at 1, got {trial_ids[0]}"
        )
    expected = list(range(1, trial_ids[-1] + 1))
    if trial_ids != expected:
        raise StateIntegrityError("run_batch trial sequence mismatch")


def _metric_summary(
    results: list[monte_carlo.TrialResult],
) -> dict[str, dict[str, float | int | bool]]:
    if len(results) < 2:
        raise ValueError("At least two observations are required for CI evaluation")

    n = len(results)
    tail_probability = (1.0 - constants.CI_CONFIDENCE_LEVEL) / 2.0
    t_critical = float(t.ppf(1.0 - tail_probability, n - 1))

    summary: dict[str, dict[str, float | int | bool]] = {}
    for field_name in STABILITY_FIELDS:
        sample = np.asarray(
            [getattr(result, field_name) for result in results],
            dtype=np.float64,
        )
        mean = float(sample.mean())
        sample_std = float(sample.std(ddof=1))
        half_ci = float(t_critical * sample_std / math.sqrt(n))
        limit = max(
            constants.CI_ABSOLUTE_EPSILON,
            constants.CI_RELATIVE_TOLERANCE * abs(mean),
        )
        summary[field_name] = {
            "n": n,
            "mean": mean,
            "sample_std": sample_std,
            "t_critical": t_critical,
            "half_ci_95": half_ci,
            "limit": limit,
            "stable": half_ci < limit,
        }

    return summary


def evaluate_gate_a(
    *,
    previous_metrics: dict[str, dict[str, Any]] | None,
    previous_n: int | None,
    current_metrics: dict[str, dict[str, Any]],
    current_n: int,
    expected_golden_fingerprint_sha256: str | None = None,
    actual_fingerprint_sha256: str | None = None,
    golden_reference_id: str | None = None,
    expected_source_sha: str | None = None,
    actual_source_sha: str | None = None,
) -> dict[str, Any]:
    """Apply Gate A's exact-golden contract; missing evidence fails closed."""
    return evaluate_stage7_gate_a(
        previous_n=previous_n,
        previous_metrics=previous_metrics,
        current_n=current_n,
        current_metrics=current_metrics,
        escalation_multiplier=STATISTICAL_ESCALATION_MULTIPLIER,
        relative_epsilon=constants.CI_RELATIVE_TOLERANCE,
        absolute_epsilon=constants.CI_ABSOLUTE_EPSILON,
        expected_golden_fingerprint_sha256=expected_golden_fingerprint_sha256,
        actual_fingerprint_sha256=actual_fingerprint_sha256,
        golden_reference_id=golden_reference_id,
        expected_source_sha=expected_source_sha,
        actual_source_sha=actual_source_sha,
    )

def evaluate_gate_b(
    current_metrics: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    metric_payload = {
        field_name: {
            "stable": bool(current_metrics[field_name]["stable"])
        }
        for field_name in STABILITY_FIELDS
    }
    return {
        "checked": True,
        "stable": all(
            item["stable"] for item in metric_payload.values()
        ),
        "metrics": metric_payload,
    }


def _checkpoint_identity_is_valid(
    checkpoint: dict[str, Any],
    *,
    scenario: str,
    source_sha: str,
) -> None:
    if checkpoint.get("stage") != "7":
        raise StateIntegrityError("checkpoint stage must be 7")
    if checkpoint.get("scenario") != scenario:
        raise StateIntegrityError("checkpoint scenario mismatch")
    if checkpoint.get("source_sha") != source_sha:
        raise StateIntegrityError("checkpoint source SHA mismatch")

    identity = checkpoint.get("artifact_identity")
    if not isinstance(identity, dict):
        raise StateIntegrityError("checkpoint artifact_identity is missing")

    if identity.get("scenario") != scenario:
        raise StateIntegrityError(
            "checkpoint artifact_identity scenario mismatch"
        )
    if identity.get("source_sha") != source_sha:
        raise StateIntegrityError(
            "checkpoint artifact_identity source SHA mismatch"
        )

    completed_trials = int(checkpoint.get("completed_trials", 0))
    next_trial_id = int(checkpoint.get("next_trial_id", 0))
    next_check_n = int(checkpoint.get("next_check_n", 0))

    legacy_c100_single_trial_checkpoint = (
        scenario.startswith("C100_")
        and completed_trials == 1
        and next_trial_id == 2
        and next_check_n == 1
    )
    if next_check_n <= completed_trials and not legacy_c100_single_trial_checkpoint:
        raise StateIntegrityError(
            "checkpoint next_check_n must be greater than completed_trials"
        )

    trial_id_start = int(identity.get("trial_id_start", 0))
    trial_id_end = int(identity.get("trial_id_end", 0))
    fingerprint = identity.get("fingerprint_sha256")

    if trial_id_start != 1:
        raise StateIntegrityError(
            "checkpoint artifact_identity trial_id_start must be 1"
        )
    if trial_id_end != completed_trials:
        raise StateIntegrityError(
            "checkpoint artifact_identity trial_id_end mismatch"
        )
    if next_trial_id != completed_trials + 1:
        raise StateIntegrityError("checkpoint next_trial_id mismatch")
    if checkpoint.get("final_fingerprint") != fingerprint:
        raise StateIntegrityError(
            "checkpoint final_fingerprint differs from artifact_identity"
        )


def load_stage7_checkpoint(
    *,
    scenario: str,
    source_sha: str,
) -> dict[str, Any]:
    repo = os.environ.get("GITHUB_REPOSITORY")
    token = os.environ.get("GH_TOKEN")
    if not repo or not token:
        raise RuntimeError(
            "resume requires GITHUB_REPOSITORY and GH_TOKEN"
        )

    store = StateStore(
        repo=repo,
        token=token,
        scenario=scenario,
        source_sha=source_sha,
        run_id=f"stage8-read-{os.getpid()}",
        run_attempt="1",
        local_path=(
            Path(tempfile.gettempdir())
            / f"stage8-read-{scenario}-state.json"
        ),
    )
    checkpoint, _ = store.load_state()
    _checkpoint_identity_is_valid(
        checkpoint,
        scenario=scenario,
        source_sha=source_sha,
    )
    return checkpoint


def resolve_start_trial_id(
    *,
    requested_start_trial_id: int,
    resume_from_checkpoint: bool,
    checkpoint: dict[str, Any] | None,
) -> int:
    if not resume_from_checkpoint:
        return requested_start_trial_id
    if checkpoint is None:
        raise StateIntegrityError(
            "resume requested without a checkpoint"
        )
    return int(checkpoint["next_trial_id"])


def _new_state(
    *,
    scenario: str,
    source_sha: str,
    master_seed: int,
    start_trial_id: int,
    requested_trials: int,
    resume_from_checkpoint: bool,
    checkpoint: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "stage": "8",
        "schema_version": 1,
        "scenario": scenario,
        "source_sha": source_sha,
        "master_seed": master_seed,
        "dataset_kind": (
            "checkpoint_resume"
            if resume_from_checkpoint
            else "new"
        ),
        "start_trial_id": start_trial_id,
        "requested_trials": requested_trials,
        "completed_trial_count": 0,
        "next_trial_id": start_trial_id,
        "stability_history": [],
        "artifact_identity": None,
        "final_fingerprint": None,
        "final_status": "running",
        "reason_if_not_stable": None,
        "input_checkpoint": (
            {
                "scenario": checkpoint["scenario"],
                "source_sha": checkpoint["source_sha"],
                "completed_trials": checkpoint["completed_trials"],
                "next_trial_id": checkpoint["next_trial_id"],
                "artifact_identity": checkpoint["artifact_identity"],
            }
            if checkpoint is not None
            else None
        ),
    }


def _validate_resume_dataset(
    results: list[monte_carlo.TrialResult],
    checkpoint: dict[str, Any],
) -> None:
    _validate_trial_sequence(results)

    expected_end = int(
        checkpoint["artifact_identity"]["trial_id_end"]
    )
    if not results:
        raise StateIntegrityError(
            "resume requires the checkpoint dataset in output-dir"
        )
    if results[0].trial_id != 1 or results[-1].trial_id != expected_end:
        raise StateIntegrityError(
            "resume dataset trial range differs from checkpoint"
        )

    actual_fingerprint = monte_carlo.fingerprint_trial_results(results)
    expected_fingerprint = checkpoint["artifact_identity"][
        "fingerprint_sha256"
    ]
    if actual_fingerprint != expected_fingerprint:
        raise StateIntegrityError(
            "resume dataset fingerprint differs from checkpoint"
        )


def _ensure_output_contract(
    output_dir: Path,
    *,
    resume_from_checkpoint: bool,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    existing = list(output_dir.iterdir())

    if not resume_from_checkpoint and existing:
        raise FileExistsError(
            "default mode requires an empty output directory"
        )

    if resume_from_checkpoint and not (
        output_dir / TRIALS_PARQUET
    ).exists():
        raise StateIntegrityError(
            "resume requires existing trial dataset in output-dir"
        )


def _build_artifact_identity(
    *,
    scenario: str,
    source_sha: str,
    results: list[monte_carlo.TrialResult],
) -> dict[str, Any] | None:
    if not results:
        return None
    return {
        "scenario": scenario,
        "source_sha": source_sha,
        "trial_id_start": results[0].trial_id,
        "trial_id_end": results[-1].trial_id,
        "fingerprint_sha256": (
            monte_carlo.fingerprint_trial_results(results)
        ),
    }


def _update_state_identity(
    state: dict[str, Any],
    *,
    scenario: str,
    source_sha: str,
    results: list[monte_carlo.TrialResult],
) -> None:
    state["completed_trial_count"] = len(results)
    state["next_trial_id"] = (
        results[-1].trial_id + 1
        if results
        else state["start_trial_id"]
    )
    state["final_fingerprint"] = (
        monte_carlo.fingerprint_trial_results(results)
        if results
        else None
    )
    state["artifact_identity"] = _build_artifact_identity(
        scenario=scenario,
        source_sha=source_sha,
        results=results,
    )


def _latest_stability_point(
    history: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, int | None]:
    if not history:
        return None, None
    latest = history[-1]
    return latest.get("metrics"), (
        int(latest["n"]) if latest.get("n") is not None else None
    )


def run_batch(
    *,
    scenario: str,
    trials: int,
    output_dir: Path,
    start_trial_id: int = 1,
    resume_from_checkpoint: bool = False,
    master_seed: int = constants.MASTER_SEED,
    source_sha: str | None = None,
    excel_dataset_root: Path | None = None,
) -> dict[str, Any]:
    if source_sha is None:
        source_sha = os.environ.get("SOURCE_SHA", "")
    if not source_sha:
        raise ValueError("SOURCE_SHA must be supplied by environment")

    monte_carlo.parse_scenario_id(scenario)

    checkpoint = None
    if resume_from_checkpoint:
        checkpoint = load_stage7_checkpoint(
            scenario=scenario,
            source_sha=source_sha,
        )

    resolved_start = resolve_start_trial_id(
        requested_start_trial_id=start_trial_id,
        resume_from_checkpoint=resume_from_checkpoint,
        checkpoint=checkpoint,
    )

    _ensure_output_contract(
        output_dir,
        resume_from_checkpoint=resume_from_checkpoint,
    )

    results = (
        _load_dataset(output_dir)
        if resume_from_checkpoint
        else []
    )

    daily_slices_path = output_dir / DAILY_SLICES_PARQUET
    if resume_from_checkpoint:
        _validate_resume_dataset(results, checkpoint)
        if results and not daily_slices_path.exists():
            raise StateIntegrityError(
                "resume requires daily_slices.parquet for the completed dataset; "
                "refusing to replay completed trial IDs to reconstruct missing daily data"
            )
        daily_slices = _load_daily_slices(output_dir)
        if results:
            _validate_daily_slices(results, daily_slices)
    else:
        daily_slices = {}

    initial_target = constants.NON_C100_STATISTICAL_START_TRIALS

    state = _new_state(
        scenario=scenario,
        source_sha=source_sha,
        master_seed=master_seed,
        start_trial_id=resolved_start,
        requested_trials=trials,
        resume_from_checkpoint=resume_from_checkpoint,
        checkpoint=checkpoint,
    )
    state["statistical_policy_id"] = STATISTICAL_ESCALATION_POLICY_ID
    state["policy"] = {
        "statistical_policy_id": STATISTICAL_ESCALATION_POLICY_ID,
        "c100_start_trials": constants.C100_STATISTICAL_START_TRIALS,
        "non_c100_start_trials": constants.NON_C100_STATISTICAL_START_TRIALS,
        "escalation_multiplier": STATISTICAL_ESCALATION_MULTIPLIER,
        "check_start_n": constants.STATISTICAL_CHECK_START_N,
        "consecutive_checks": constants.STABILITY_CONSECUTIVE_CHECKS_REQUIRED,
        "ci_confidence_level": constants.CI_CONFIDENCE_LEVEL,
        "ci_relative_tolerance": constants.CI_RELATIVE_TOLERANCE,
        "ci_absolute_epsilon": constants.CI_ABSOLUTE_EPSILON,
    }

    if checkpoint is not None:
        original_history = list(checkpoint.get("stability_history", []))
        saved_policy = checkpoint.get("policy") or {}
        policy_is_current = (
            saved_policy.get("statistical_policy_id")
            == STATISTICAL_ESCALATION_POLICY_ID
        )

        if scenario.startswith("C100_"):
            policy_is_current = (
                policy_is_current
                and int(saved_policy.get("c100_start_trials", 0))
                == constants.C100_STATISTICAL_START_TRIALS
            )

        if not policy_is_current and (results or original_history):
            if len(results) > 550:
                raise StateIntegrityError(
                    "legacy linear-schedule checkpoint exceeds the authorized "
                    "historical analytical range 1..550; cannot migrate safely"
                )
            try:
                history, discarded_points = filter_statistical_history(
                    original_history
                )
            except ValueError as exc:
                raise StateIntegrityError(str(exc)) from exc

            reconstructed_n300 = False
            if len(results) >= constants.STATISTICAL_CHECK_START_N and not any(
                int(item.get("n", -1)) == constants.STATISTICAL_CHECK_START_N
                for item in history
            ):
                baseline_results = results[:constants.STATISTICAL_CHECK_START_N]
                baseline_metrics = _metric_summary(baseline_results)
                history.insert(
                    0,
                    {
                        "n": constants.STATISTICAL_CHECK_START_N,
                        "gate_a": evaluate_gate_a(
                            previous_metrics=None,
                            previous_n=None,
                            current_metrics=baseline_metrics,
                            current_n=constants.STATISTICAL_CHECK_START_N,
                        ),
                        "gate_b": evaluate_gate_b(baseline_metrics),
                        "metrics": baseline_metrics,
                        "reconstructed_from_identity_verified_rows": True,
                    },
                )
                reconstructed_n300 = True

            state["policy_migration"] = {
                "from_policy_id": saved_policy.get(
                    "statistical_policy_id", "LEGACY_UNVERSIONED"
                ),
                "legacy_escalation_step": saved_policy.get("escalation_step"),
                "to_policy_id": STATISTICAL_ESCALATION_POLICY_ID,
                "preserved_checkpoint_n": [int(item["n"]) for item in history],
                "discarded_noncompliant_checkpoint_n": discarded_points,
                "n300_reconstructed_from_existing_verified_rows": reconstructed_n300,
                "completed_trials_reused": len(results),
                "historical_trials_rerun": False,
                "source_sha": source_sha,
                "master_seed": master_seed,
            }
            if results:
                state["final_status"] = "running"
                state["reason_if_not_stable"] = (
                    "legacy linear checkpoints excluded; resumed under approved doubling policy"
                )
                state["stable_at_n"] = None
                state["included_in_final_stats"] = False

            state["stability_history"] = history
            previous_metrics, previous_n = _latest_stability_point(history)
            state["next_check_n"] = next_statistical_checkpoint(len(results))
        else:
            try:
                history, discarded_points = filter_statistical_history(
                    original_history
                )
            except ValueError as exc:
                raise StateIntegrityError(str(exc)) from exc
            if discarded_points:
                raise StateIntegrityError(
                    "current-policy checkpoint contains non-doubling history points"
                )
            expected_next = next_statistical_checkpoint(len(results))
            saved_next = checkpoint.get("next_check_n")
            if saved_next is not None and int(saved_next) != expected_next:
                raise StateIntegrityError(
                    "checkpoint next_check_n does not match the approved doubling policy"
                )
            state["stability_history"] = history
            previous_metrics, previous_n = _latest_stability_point(history)
            state["next_check_n"] = expected_next
    else:
        previous_metrics = None
        previous_n = None
        state["next_check_n"] = initial_target

    state["stability_history"] = hydrate_p50_history(
        state.get("stability_history", []),
        _p50_values_by_checkpoint(results),
    )
    gate_a_preflight_stop = False
    if (
        len(results) >= constants.STATISTICAL_CHECK_START_N
        and not p50_history_ready(state["stability_history"], len(results))
    ):
        state["final_status"] = "blocked"
        state["stable_at_n"] = None
        state["included_in_final_stats"] = False
        state["reason_if_not_stable"] = (
            "P50 >5% policy evidence is incomplete or invalid; refusing to execute additional trials"
        )
        _atomic_write_json(output_dir / STATE_JSON, state)
        gate_a_preflight_stop = True

    if (
        len(results) >= constants.STATISTICAL_CHECK_START_N
        and state.get("final_status") == "stable"
        and p50_requires_n2400(state["stability_history"])
        and len(results) < 2400
    ):
        state["final_status"] = "PRELIMINARY_STABLE"
        state["stable_at_n"] = None
        state["included_in_final_stats"] = False
        state["reason_if_not_stable"] = (
            "P50 >5% continuation rule requires checkpoint N=2400"
        )
        _atomic_write_json(output_dir / STATE_JSON, state)

    if len(results) >= constants.STATISTICAL_CHECK_START_N:
        prior_history = state.get("stability_history", [])
        prior_gate_a = (
            prior_history[-1].get("gate_a", {})
            if prior_history
            else {}
        )
        prior_gate_a_status = prior_gate_a.get("status")
        if prior_gate_a_status != "PASS":
            is_failure = prior_gate_a_status == "FAIL"
            state["final_status"] = "failed" if is_failure else "blocked"
            state["stable_at_n"] = None
            state["included_in_final_stats"] = False
            state["reason_if_not_stable"] = (
                f"Gate A {prior_gate_a_status or 'UNVERIFIED'}: "
                "the latest completed checkpoint lacks an explicit exact-golden PASS; "
                "refusing to execute additional trials"
            )
            state["next_check_n"] = next_statistical_checkpoint(len(results))
            _atomic_write_json(output_dir / STATE_JSON, state)
            gate_a_preflight_stop = True

    batch_end = resolved_start + trials - 1
    resolved_next_check = state["next_check_n"]

    while resolved_start <= batch_end and not gate_a_preflight_stop:
        if (
            resolved_next_check is not None
            and len(results) < resolved_next_check
        ):
            target = resolved_next_check
        else:
            target = next_statistical_checkpoint(len(results))
        trial_end = min(batch_end, target)

        trial_ids = list(range(resolved_start, trial_end + 1))
        new_results, new_daily_rows = monte_carlo.run_trials_sequentially(
            scenario,
            trial_ids,
            master_seed=master_seed,
        )
        new_result_ids = {int(result.trial_id) for result in new_results}
        if new_result_ids != {int(trial_id) for trial_id in new_daily_rows}:
            raise StateIntegrityError(
                "new daily slice trial IDs differ from newly completed trials"
            )
        for trial_id, rows in new_daily_rows.items():
            canonical_trial_id = int(trial_id)
            if canonical_trial_id in daily_slices:
                raise StateIntegrityError(
                    f"daily slices already exist for completed trial_id={canonical_trial_id}; refusing duplicate/replay"
                )
            daily_slices[canonical_trial_id] = sorted(
                [dict(row) for row in rows],
                key=lambda row: str(row.get("date", "")),
            )

        results.extend(new_results)
        results.sort(key=lambda item: item.trial_id)

        _validate_trial_sequence(results)
        _validate_daily_slices(results, daily_slices)
        _write_dataset(results, output_dir)
        _write_daily_slices(daily_slices, output_dir)
        _update_state_identity(
            state,
            scenario=scenario,
            source_sha=source_sha,
            results=results,
        )

        if (
            trial_end >= constants.STATISTICAL_CHECK_START_N
            and trial_end == resolved_next_check
        ):
            metrics = _metric_summary(results)
            gate_a = evaluate_gate_a(
                previous_metrics=previous_metrics,
                previous_n=previous_n,
                current_metrics=metrics,
                current_n=len(results),
            )
            gate_b = evaluate_gate_b(metrics)

            state["stability_history"].append(
                {
                    "n": len(results),
                    "gate_a": gate_a,
                    "gate_b": gate_b,
                    "metrics": metrics,
                    "p50_final_net_project_equity": _p50_values_by_checkpoint(results).get(len(results)),
                }
            )
            state["stability_history"] = hydrate_p50_history(
                state["stability_history"],
                _p50_values_by_checkpoint(results),
            )

            gate_a_status = gate_a.get("status", "BLOCKED")
            p50_ready = p50_history_ready(
                state["stability_history"], len(results)
            )
            p50_waiting_for_n2400 = (
                p50_requires_n2400(state["stability_history"])
                and len(results) < 2400
            )
            stable_gates_now = False
            stable_now = False
            if gate_a_status != "PASS":
                state["final_status"] = (
                    "failed" if gate_a_status == "FAIL" else "blocked"
                )
                state["stable_at_n"] = None
                state["included_in_final_stats"] = False
                state["reason_if_not_stable"] = (
                    f"Gate A {gate_a_status}: {gate_a.get('reason')}; "
                    "execution stopped before the next trial block"
                )
            elif not p50_ready:
                state["final_status"] = "blocked"
                state["stable_at_n"] = None
                state["included_in_final_stats"] = False
                state["reason_if_not_stable"] = (
                    "P50 >5% policy evidence is incomplete or invalid; "
                    "execution stopped before the next trial block"
                )
            else:
                recent = state["stability_history"][
                    -constants.STABILITY_CONSECUTIVE_CHECKS_REQUIRED:
                ]
                stable_gates_now = (
                    len(recent)
                    == constants.STABILITY_CONSECUTIVE_CHECKS_REQUIRED
                    and all(
                        item.get("gate_a", {}).get("status") == "PASS"
                        and item.get("gate_a", {}).get("checked") is True
                        and item.get("gate_a", {}).get("stable") is True
                        and item["gate_b"]["stable"]
                        for item in recent
                    )
                )
                stable_now = stable_gates_now and not p50_waiting_for_n2400
                state["final_status"] = (
                    "stable" if stable_now
                    else "PRELIMINARY_STABLE" if stable_gates_now and p50_waiting_for_n2400
                    else "running"
                )
                state["stable_at_n"] = len(results) if stable_now else None
                state["included_in_final_stats"] = stable_now
                state["reason_if_not_stable"] = (
                    None
                    if stable_now
                    else "P50 >5% continuation rule requires checkpoint N=2400"
                    if stable_gates_now and p50_waiting_for_n2400
                    else "dual stability gates not yet satisfied"
                )

            previous_metrics = metrics
            previous_n = len(results)
            resolved_next_check = next_statistical_checkpoint(len(results))
            state["next_check_n"] = resolved_next_check
            _atomic_write_json(output_dir / STATE_JSON, state)

            if gate_a_status != "PASS" or not p50_ready:
                gate_a_preflight_stop = True
                break
            if stable_now:
                break
        else:
            if len(results) < constants.STATISTICAL_CHECK_START_N:
                _atomic_write_json(output_dir / STATE_JSON, state)

        if state["final_status"] == "stable":
            break

        resolved_start = trial_end + 1

    _update_state_identity(
        state,
        scenario=scenario,
        source_sha=source_sha,
        results=results,
    )
    if state["final_status"] == "running":
        state["reason_if_not_stable"] = (
            "requested additional trial range completed"
        )

    _atomic_write_json(
        output_dir / STATISTICS_JSON,
        {
            "scenario": scenario,
            "trial_count": len(results),
            "final_fingerprint": state["final_fingerprint"],
            "artifact_identity": state["artifact_identity"],
            "stability_history": state["stability_history"],
        },
    )
    _atomic_write_json(output_dir / STATE_JSON, state)
    if excel_dataset_root is not None:
        _write_excel_daily_datasets(
            dataset_root=Path(excel_dataset_root),
            scenario=scenario,
            results=results,
            slices_by_trial=daily_slices,
            state=state,
        )
    return state


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    run_batch(
        scenario=args.scenario,
        trials=args.trials,
        output_dir=Path(args.output_dir),
        start_trial_id=args.start_trial_id,
        resume_from_checkpoint=args.resume_from_checkpoint,
        master_seed=args.master_seed,
        source_sha=os.environ.get("SOURCE_SHA"),
        excel_dataset_root=(
            Path(args.excel_dataset_root)
            if args.excel_dataset_root is not None
            else None
        ),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
