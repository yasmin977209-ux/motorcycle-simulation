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
    next_statistical_checkpoint,
)


TRIALS_PARQUET = "trials_summary.parquet"
TRIALS_JSONL_GZ = "trials_summary.jsonl.gz"
STATE_JSON = "state.json"
STATISTICS_JSON = "statistics.json"

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

    initial_trials = (
        constants.C100_STATISTICAL_START_TRIALS
        if args.scenario.startswith("C100_")
        else constants.NON_C100_STATISTICAL_START_TRIALS
    )
    if args.scenario.startswith("C100_") and args.trials != initial_trials:
        raise ValueError("C100 policy requires exactly one trial")

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
        if abs(mean) < constants.REFERENCE_EPSILON:
            limit = constants.CI_ABSOLUTE_EPSILON
        else:
            limit = constants.CI_RELATIVE_TOLERANCE * abs(mean)
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
    metric_payload = {}
    for field_name in STABILITY_FIELDS:
        raw_stable = current_metrics[field_name]["stable"]
        if type(raw_stable) is not bool:
            raise ValueError(
                f"Gate B stable field for {field_name!r} must be a Boolean"
            )
        metric_payload[field_name] = {"stable": raw_stable}
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

    if not scenario.startswith("C100_") and next_check_n <= completed_trials:
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


def _refuse_terminal_local_state_on_resume(
    output_dir: Path,
    *,
    resume_from_checkpoint: bool,
) -> None:
    if not resume_from_checkpoint:
        return

    state_path = output_dir / STATE_JSON
    if not state_path.exists():
        raise StateIntegrityError(
            "resume refused because the previous local batch state is missing"
        )

    try:
        previous_state = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StateIntegrityError(
            "resume refused because the previous local batch state is unreadable"
        ) from exc

    if not isinstance(previous_state, dict):
        raise StateIntegrityError(
            "resume refused because the previous local batch state must be a JSON object"
        )

    previous_status = previous_state.get("final_status")
    if previous_status not in {"running", "stable", "blocked", "failed"}:
        raise StateIntegrityError(
            "resume refused because the previous local batch state has a missing or invalid final_status"
        )
    if previous_status in {"blocked", "failed", "stable"}:
        raise StateIntegrityError(
            f"resume refused because the previous local batch state is {previous_status}; "
            "operator review is required before any additional trials"
        )


def _has_explicit_gate_a_pass(gate_a: Any) -> bool:
    """Require an explicit, checked Gate A PASS before continuing a batch."""
    return (
        isinstance(gate_a, dict)
        and gate_a.get("status") == "PASS"
        and gate_a.get("checked") is True
        and gate_a.get("stable") is True
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
) -> dict[str, Any]:
    if source_sha is None:
        source_sha = os.environ.get("SOURCE_SHA", "")
    if not source_sha:
        raise ValueError("SOURCE_SHA must be supplied by environment")

    monte_carlo.parse_scenario_id(scenario)

    _refuse_terminal_local_state_on_resume(
        output_dir,
        resume_from_checkpoint=resume_from_checkpoint,
    )

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

    if (
        scenario.startswith("C100_")
        and (
            resolved_start != constants.C100_STATISTICAL_START_TRIALS
            or trials != constants.C100_STATISTICAL_START_TRIALS
        )
    ):
        raise StateIntegrityError(
            "C100 policy permits exactly one trial"
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

    if resume_from_checkpoint:
        _validate_resume_dataset(results, checkpoint)

    initial_target = (
        constants.C100_STATISTICAL_START_TRIALS
        if scenario.startswith("C100_")
        else constants.NON_C100_STATISTICAL_START_TRIALS
    )

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
            history = original_history
            state["stability_history"] = history
            previous_metrics, previous_n = _latest_stability_point(history)
            state["next_check_n"] = int(
                checkpoint.get("next_check_n", initial_target)
            )
        elif not policy_is_current and (results or original_history):
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
        state["next_check_n"] = (
            None
            if scenario.startswith("C100_")
            else initial_target
        )

    gate_a_preflight_stop = False
    if (
        not scenario.startswith("C100_")
        and len(results) >= constants.STATISTICAL_CHECK_START_N
    ):
        prior_history = state.get("stability_history", [])
        prior_checkpoint = (
            prior_history[-1]
            if isinstance(prior_history, list) and prior_history
            else {}
        )
        prior_gate_a = (
            prior_checkpoint.get("gate_a", {})
            if isinstance(prior_checkpoint, dict)
            else {}
        )
        prior_gate_a_status = (
            prior_gate_a.get("status")
            if isinstance(prior_gate_a, dict)
            else None
        )
        if not _has_explicit_gate_a_pass(prior_gate_a):
            is_failure = (
                isinstance(prior_gate_a, dict)
                and prior_gate_a.get("status") == "FAIL"
                and prior_gate_a.get("checked") is True
                and prior_gate_a.get("stable") is False
            )
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
        if scenario.startswith("C100_"):
            trial_end = 1
        else:
            if (
                resolved_next_check is not None
                and len(results) < resolved_next_check
            ):
                target = resolved_next_check
            else:
                target = next_statistical_checkpoint(len(results))
            trial_end = min(batch_end, target)

        trial_ids = list(range(resolved_start, trial_end + 1))
        new_results, _ = monte_carlo.run_trials_sequentially(
            scenario,
            trial_ids,
            master_seed=master_seed,
        )
        results.extend(new_results)
        results.sort(key=lambda item: item.trial_id)

        _validate_trial_sequence(results)
        _write_dataset(results, output_dir)
        _update_state_identity(
            state,
            scenario=scenario,
            source_sha=source_sha,
            results=results,
        )

        if scenario.startswith("C100_"):
            primary = results[0]
            verification, _ = monte_carlo.run_single_trial(
                scenario,
                trial_id=2,
                master_seed=master_seed,
            )
            primary_dict = asdict(primary)
            verification_dict = asdict(verification)
            primary_dict.pop("trial_id")
            verification_dict.pop("trial_id")

            exact_equality = primary_dict == verification_dict
            state["c100_independent_verification"] = {
                "primary_trial_id": 1,
                "verification_trial_id": 2,
                "different_trial_id": True,
                "different_derived_seed": True,
                "exact_result_equality": exact_equality,
                "stable": exact_equality,
            }
            state["final_status"] = (
                "stable" if exact_equality else "failed"
            )
            state["reason_if_not_stable"] = (
                None
                if exact_equality
                else "C100 independent result mismatch"
            )
            _atomic_write_json(output_dir / STATE_JSON, state)
            break

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
                }
            )

            gate_a_status = gate_a.get("status")
            if (
                gate_a_status != "PASS"
                or gate_a.get("checked") is not True
                or gate_a.get("stable") is not True
            ):
                state["final_status"] = (
                    "failed" if gate_a_status == "FAIL" else "blocked"
                )
                state["stable_at_n"] = None
                state["included_in_final_stats"] = False
                state["reason_if_not_stable"] = (
                    f"Gate A {gate_a_status or 'UNVERIFIED'}: exact-golden evidence "
                    "is missing or Gate A did not PASS; refusing to execute additional trials"
                )
                state["next_check_n"] = next_statistical_checkpoint(len(results))
                _atomic_write_json(output_dir / STATE_JSON, state)
                break

            recent = state["stability_history"][
                -constants.STABILITY_CONSECUTIVE_CHECKS_REQUIRED:
            ]
            stable_now = (
                len(recent)
                == constants.STABILITY_CONSECUTIVE_CHECKS_REQUIRED
                and all(
                    item["gate_a"]["stable"]
                    and item["gate_b"]["stable"]
                    for item in recent
                )
            )
            state["final_status"] = (
                "stable" if stable_now else "running"
            )
            state["reason_if_not_stable"] = (
                None
                if stable_now
                else "dual stability gates not yet satisfied"
            )

            previous_metrics = metrics
            previous_n = len(results)
            resolved_next_check = next_statistical_checkpoint(len(results))
            state["next_check_n"] = resolved_next_check

            _atomic_write_json(output_dir / STATE_JSON, state)

            if stable_now:
                break
        else:
            if (
                scenario.startswith("C100_")
                or len(results) < constants.STATISTICAL_CHECK_START_N
            ):
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
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
