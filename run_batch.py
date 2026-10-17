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
import rng
from scripts.stage7_state import StateIntegrityError, StateStore
from scripts.stage7_stability import (
    STATISTICAL_ESCALATION_POLICY_ID,
    STATISTICAL_ESCALATION_MULTIPLIER,
    evaluate_gate_a as evaluate_stage7_gate_a,
    evaluate_p50_transition,
    evaluate_reference_stability_transition,
    is_statistical_checkpoint,
    p50_requires_n2400,
    summarize_reference_stability_metrics,
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

    if next_check_n <= completed_trials:
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

    if resume_from_checkpoint:
        _validate_resume_dataset(results, checkpoint)

    initial_target = constants.STATISTICAL_CHECK_START_N

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
        "stop_rule": "FIRST_PASSING_ELIGIBLE_TRANSITION",
        "reference_stability_metrics": list(constants.REFERENCE_STABILITY_INDICATORS),
        "n300_role": "MANDATORY_COVERAGE_ONLY",
        "first_stability_transition": "300->600",
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

        # Do not repeat the old standalone C100 trial-2 diagnostic. The legacy
        # state may hold only an equality proof, not the complete TrialResult row.
        if scenario.startswith("C100_") and len(results) < 300:
            old_proof = checkpoint.get("c100_independent_verification") or {}
            if (
                int(old_proof.get("verification_trial_id", 0) or 0) == 2
                and all(result.trial_id != 2 for result in results)
            ):
                raise StateIntegrityError(
                    "legacy C100 trial_id=2 was previously executed but its full "
                    "TrialResult row is absent; restore the identity-verified row-2 "
                    "artifact before migration; refusing to rerun or synthesize it"
                )

        try:
            _, noncompliant_history_n = filter_statistical_history(original_history)
        except ValueError as exc:
            raise StateIntegrityError(str(exc)) from exc

        # Preserve the whole historical log, including failed/legacy transitions.
        # Reassess approved cumulative checkpoints from the already verified rows;
        # do not delete or relabel earlier status values.
        history = [dict(item) for item in original_history]
        state["stability_history"] = history
        state["policy_migration"] = {
            "from_policy_id": saved_policy.get(
                "statistical_policy_id", "LEGACY_UNVERSIONED"
            ),
            "to_policy_id": STATISTICAL_ESCALATION_POLICY_ID,
            "preserved_historical_checkpoint_n": [
                item.get("n") for item in original_history
            ],
            "noncompliant_historical_checkpoint_n_preserved": noncompliant_history_n,
            "completed_trials_reused": len(results),
            "historical_trials_rerun": False,
            "source_sha": source_sha,
            "master_seed": master_seed,
            "historical_statuses_rewritten": False,
        }

        # N=300 is the required coverage baseline, never a stability PASS.
        eligible_ns = {
            int(item["n"])
            for item in history
            if item.get("n") is not None
            and is_statistical_checkpoint(int(item["n"]))
            and int(item["n"]) <= len(results)
        }
        if len(results) >= constants.STATISTICAL_CHECK_START_N and 300 not in eligible_ns:
            baseline_rows = results[:300]
            baseline_ci = _metric_summary(baseline_rows)
            baseline_reference = summarize_reference_stability_metrics(baseline_rows)
            baseline_gate_a = evaluate_gate_a(
                previous_metrics=None,
                previous_n=None,
                current_metrics=baseline_ci,
                current_n=300,
            )
            baseline_gate_b = evaluate_gate_b(baseline_ci)
            baseline = {
                "n": 300,
                "gate_a": baseline_gate_a,
                "gate_b": baseline_gate_b,
                "metrics": baseline_ci,
                "reference_metrics": baseline_reference,
                "reference_stability_gate": evaluate_reference_stability_transition(
                    previous_n=None,
                    previous_metrics=None,
                    current_n=300,
                    current_metrics=baseline_reference,
                ),
                "p50_final_net_project_equity": float(np.quantile(
                    [row.final_net_project_equity for row in baseline_rows],
                    0.50,
                    method="linear",
                )),
                "p50_transition": {
                    "previous_n": None,
                    "current_n": 300,
                    "checked": False,
                    "stable": True,
                    "requires_n2400": False,
                    "status": "BASELINE",
                    "reason": "N=300 is mandatory coverage only",
                },
                "reconstructed_from_identity_verified_rows": True,
                "historical_gate_status_preserved": True,
            }
            at = next(
                (i for i, item in enumerate(history) if int(item.get("n", -1)) > 300),
                len(history),
            )
            history.insert(at, baseline)
            state["stability_history"] = history
            eligible_ns.add(300)

        # Attach fresh §2.5/P50 calculations to eligible legacy points without
        # overwriting their historical Gate A/Gate B outcomes or their failures.
        for item in history:
            try:
                n = int(item.get("n", -1))
            except (TypeError, ValueError):
                continue
            if not is_statistical_checkpoint(n) or n > len(results):
                continue
            sample = results[:n]
            if "reference_metrics" not in item:
                item["reference_metrics"] = summarize_reference_stability_metrics(sample)
            if "reference_stability_gate" not in item:
                if n == 300:
                    item["reference_stability_gate"] = evaluate_reference_stability_transition(
                        previous_n=None,
                        previous_metrics=None,
                        current_n=300,
                        current_metrics=item["reference_metrics"],
                    )
                else:
                    prior_n = n // 2
                    prior_metrics = summarize_reference_stability_metrics(results[:prior_n])
                    item["reference_stability_gate"] = evaluate_reference_stability_transition(
                        previous_n=prior_n,
                        previous_metrics=prior_metrics,
                        current_n=n,
                        current_metrics=item["reference_metrics"],
                    )
                item["policy_reassessment_added"] = True
            if n == 300:
                item.setdefault("p50_final_net_project_equity", float(np.quantile(
                    [row.final_net_project_equity for row in sample],
                    0.50,
                    method="linear",
                )))
                item.setdefault("p50_transition", {
                    "previous_n": None,
                    "current_n": 300,
                    "checked": False,
                    "stable": True,
                    "requires_n2400": False,
                    "status": "BASELINE",
                    "reason": "N=300 is mandatory coverage only",
                })
            elif n in (600, 1200) and "p50_transition" not in item:
                previous_n = n // 2
                previous_p50 = float(np.quantile(
                    [row.final_net_project_equity for row in results[:previous_n]],
                    0.50,
                    method="linear",
                ))
                current_p50 = float(np.quantile(
                    [row.final_net_project_equity for row in sample],
                    0.50,
                    method="linear",
                ))
                item["p50_final_net_project_equity"] = current_p50
                item["p50_transition"] = evaluate_p50_transition(
                    previous_n=previous_n,
                    previous_p50=previous_p50,
                    current_n=n,
                    current_p50=current_p50,
                )
                item["policy_reassessment_added"] = True

        official_history = sorted(
            (
                item for item in history
                if item.get("n") is not None
                and is_statistical_checkpoint(int(item["n"]))
                and int(item["n"]) <= len(results)
            ),
            key=lambda item: int(item["n"]),
        )
        previous_metrics, previous_n = _latest_stability_point(official_history)
        state["next_check_n"] = next_statistical_checkpoint(len(results))
        state["final_status"] = "running" if results else "running"
        state["stable_at_n"] = None
        state["included_in_final_stats"] = False
        if not policy_is_current:
            state["reason_if_not_stable"] = (
                "checkpoint resumed under the approved first-passing §2.5 transition policy; "
                "historical transition statuses preserved"
            )
    else:
        previous_metrics = None
        previous_n = None
        state["stability_history"] = []
        state["next_check_n"] = initial_target

    gate_a_preflight_stop = False
    if len(results) >= constants.STATISTICAL_CHECK_START_N:
        prior_history = state.get("stability_history", [])
        eligible_prior = [
            item for item in prior_history
            if item.get("n") is not None
            and is_statistical_checkpoint(int(item["n"]))
            and int(item["n"]) <= len(results)
        ]
        latest_eligible = max(
            eligible_prior,
            key=lambda item: int(item["n"]),
            default=None,
        )
        prior_gate_a = (
            latest_eligible.get("gate_a", {})
            if latest_eligible is not None
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

    # A new or pre-checkpoint dataset must not start a statistical sample when
    # the exact approved-Golden provider is absent. Fail before generating any IDs.
    if len(results) < constants.STATISTICAL_CHECK_START_N:
        eligible_history = [
            item for item in state.get("stability_history", [])
            if item.get("n") is not None
            and is_statistical_checkpoint(int(item["n"]))
            and int(item["n"]) <= len(results)
        ]
        latest_eligible = max(
            eligible_history,
            key=lambda item: int(item["n"]),
            default=None,
        )
        if latest_eligible is None or latest_eligible.get("gate_a", {}).get("status") != "PASS":
            preflight = evaluate_gate_a(
                previous_metrics=None,
                previous_n=None,
                current_metrics={},
                current_n=constants.STATISTICAL_CHECK_START_N,
            )
            raise StateIntegrityError(
                "Gate A production preflight is blocked before trial execution: "
                + str(preflight.get("reason") or preflight.get("status"))
            )

    batch_end = resolved_start + trials - 1
    resolved_next_check = state["next_check_n"]
    stop_for_gate = False

    while resolved_start <= batch_end and not gate_a_preflight_stop:
        target = (
            resolved_next_check
            if resolved_next_check is not None and len(results) < resolved_next_check
            else next_statistical_checkpoint(len(results))
        )
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

        if (
            trial_end >= constants.STATISTICAL_CHECK_START_N
            and trial_end == resolved_next_check
            and is_statistical_checkpoint(trial_end)
        ):
            current_n = len(results)
            metrics = _metric_summary(results)
            reference_metrics = summarize_reference_stability_metrics(results)

            if current_n == 300:
                previous_ci_metrics = None
                reference_gate = evaluate_reference_stability_transition(
                    previous_n=None,
                    previous_metrics=None,
                    current_n=300,
                    current_metrics=reference_metrics,
                )
                p50_value = float(np.quantile(
                    [row.final_net_project_equity for row in results],
                    0.50,
                    method="linear",
                ))
                p50_transition = {
                    "metric": "final_net_project_equity",
                    "previous_n": None,
                    "current_n": 300,
                    "checked": False,
                    "stable": True,
                    "requires_n2400": False,
                    "change_percent": None,
                    "absolute_change": None,
                    "status": "BASELINE",
                    "reason": "N=300 is mandatory coverage only",
                }
            else:
                previous_n = current_n // STATISTICAL_ESCALATION_MULTIPLIER
                previous_rows = results[:previous_n]
                previous_reference_metrics = summarize_reference_stability_metrics(
                    previous_rows
                )
                previous_ci_metrics = _metric_summary(previous_rows)
                reference_gate = evaluate_reference_stability_transition(
                    previous_n=previous_n,
                    previous_metrics=previous_reference_metrics,
                    current_n=current_n,
                    current_metrics=reference_metrics,
                )
                previous_p50 = float(np.quantile(
                    [row.final_net_project_equity for row in previous_rows],
                    0.50,
                    method="linear",
                ))
                p50_value = float(np.quantile(
                    [row.final_net_project_equity for row in results],
                    0.50,
                    method="linear",
                ))
                p50_transition = (
                    {
                        "previous_n": previous_n,
                        "current_n": current_n,
                        "checked": False,
                        "stable": True,
                        "requires_n2400": False,
                        "status": "NOT_APPLICABLE",
                        "reason": "D-2026-10-12-01 excludes C100 from the P50 continuation trigger",
                    }
                    if scenario.startswith("C100_")
                    else evaluate_p50_transition(
                        previous_n=previous_n,
                        previous_p50=previous_p50,
                        current_n=current_n,
                        current_p50=p50_value,
                    )
                )

            gate_a = evaluate_gate_a(
                previous_metrics=previous_ci_metrics,
                previous_n=None if current_n == 300 else current_n // 2,
                current_metrics=metrics,
                current_n=current_n,
            )
            computed_gate_b = evaluate_gate_b(metrics)
            gate_b = (
                computed_gate_b
                if not scenario.startswith("C100_") or constants.C100_CI_GATE_ENABLED
                else {
                    "checked": False,
                    "stable": True,
                    "status": "NOT_APPLICABLE",
                    "reason": "C100 CI applicability remains unchanged by the approved start/§2.5 policy",
                    "metrics": computed_gate_b["metrics"],
                }
            )
            entry = {
                "n": current_n,
                "gate_a": gate_a,
                "gate_b": gate_b,
                "metrics": metrics,
                "reference_metrics": reference_metrics,
                "reference_stability_gate": reference_gate,
                "p50_final_net_project_equity": p50_value,
                "p50_transition": p50_transition,
            }

            if scenario.startswith("C100_") and current_n >= 2:
                primary_dict = asdict(results[0])
                verification_dict = asdict(results[1])
                primary_dict.pop("trial_id")
                verification_dict.pop("trial_id")
                primary_seed = rng.seed_hex(
                    master_seed,
                    scenario,
                    1,
                    "BK0001",
                    constants.INITIAL_FLEET_DELIVERY_DATE,
                    "PRIMARY_COLLECTION",
                )
                verification_seed = rng.seed_hex(
                    master_seed,
                    scenario,
                    2,
                    "BK0001",
                    constants.INITIAL_FLEET_DELIVERY_DATE,
                    "PRIMARY_COLLECTION",
                )
                exact_equality = primary_dict == verification_dict
                entry["c100_independent_verification"] = {
                    "primary_trial_id": 1,
                    "verification_trial_id": 2,
                    "primary_seed_hex": primary_seed,
                    "verification_seed_hex": verification_seed,
                    "different_trial_id": True,
                    "different_derived_seed": primary_seed != verification_seed,
                    "exact_result_equality": exact_equality,
                    "stable": exact_equality,
                }
                state["c100_independent_verification"] = entry[
                    "c100_independent_verification"
                ]

            state["stability_history"].append(entry)
            current_gate_a_status = gate_a.get("status", "BLOCKED")
            required_gate_b_pass = (
                not scenario.startswith("C100_") or constants.C100_CI_GATE_ENABLED
            )
            gate_b_ok = (not required_gate_b_pass) or gate_b.get("stable") is True
            c100_ok = (
                not scenario.startswith("C100_")
                or (
                    current_n >= 300
                    and (state.get("c100_independent_verification") or {}).get("stable") is True
                )
            )
            p50_blocked = p50_transition.get("status") == "BLOCKED"
            p50_continuation = (
                p50_requires_n2400(state["stability_history"])
                and current_n < 2400
            )
            reference_pass = reference_gate.get("status") == "PASS"

            if current_gate_a_status != "PASS":
                state["final_status"] = (
                    "failed" if current_gate_a_status == "FAIL" else "blocked"
                )
                state["stable_at_n"] = None
                state["reason_if_not_stable"] = (
                    f"Gate A {current_gate_a_status}: approved exact-golden fingerprint "
                    "and source-identity evidence are required; stopping before further trials"
                )
                stop_for_gate = True
            elif p50_blocked:
                state["final_status"] = "blocked"
                state["stable_at_n"] = None
                state["reason_if_not_stable"] = (
                    "P50 continuation trigger lacks complete adjacent-checkpoint evidence"
                )
                stop_for_gate = True
            elif current_n == 300:
                state["final_status"] = "running"
                state["stable_at_n"] = None
                state["reason_if_not_stable"] = (
                    "N=300 is mandatory coverage only; first §2.5 stability comparison is 300->600"
                )
            elif (
                reference_pass
                and gate_b_ok
                and c100_ok
                and not p50_continuation
                and gate_a.get("stable") is True
            ):
                state["final_status"] = "stable"
                state["stable_at_n"] = current_n
                state["reason_if_not_stable"] = None
            else:
                state["final_status"] = "running"
                state["stable_at_n"] = None
                reasons = []
                if not reference_pass:
                    reasons.append(f"§2.5 transition {reference_gate.get('status')}")
                if not gate_b_ok:
                    reasons.append("Gate B confidence-interval gate not stable")
                if not c100_ok:
                    reasons.append("C100 deterministic equality proof not established")
                if p50_continuation:
                    reasons.append("approved P50 rule requires continuing through N=2400")
                if gate_a.get("stable") is not True:
                    reasons.append("Gate A exact-golden identity condition not passed")
                state["reason_if_not_stable"] = "; ".join(reasons) or (
                    "current eligible transition has not met all applicable gates"
                )

            # Preserve all prior checkpoint records, including failed transitions.
            state["next_check_n"] = next_statistical_checkpoint(current_n)
            resolved_next_check = state["next_check_n"]
            _atomic_write_json(output_dir / STATE_JSON, state)

            if stop_for_gate or state["final_status"] == "stable":
                break
        else:
            _atomic_write_json(output_dir / STATE_JSON, state)

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
