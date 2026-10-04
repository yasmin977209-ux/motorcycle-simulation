from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path

import pyarrow.parquet as pq

import constants
import daily_engine
import monte_carlo


EXPECTED_CP2_AGGREGATE_SHA256 = (
    "c09d39cd3f79e9460d16df4fc2a6a47b6b029983e2f596de4af4009bc169a14a"
)

SAMPLE_TRIAL_IDS = (
    1,
    500,
    1000,
    2000,
    3000,
    4000,
    5000,
    5500,
    5900,
    6000,
)


def _result_sha256(
    result: monte_carlo.TrialResult,
) -> str:
    payload = json.dumps(
        asdict(result),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main() -> None:
    parquet_path = (
        Path("results_stage6_5")
        / "trials_summary_6000.parquet"
    )
    output_path = (
        Path("results_stage6_5")
        / "cp3_verification.json"
    )

    rows = pq.read_table(parquet_path).to_pylist()
    stored_results = [
        monte_carlo.TrialResult(**row)
        for row in rows
    ]
    stored_results.sort(
        key=lambda result: result.trial_id
    )

    if len(stored_results) != 6000:
        raise AssertionError(
            f"expected 6000 TrialResult rows, got {len(stored_results)}"
        )

    expected_trial_ids = list(range(1, 6001))
    actual_trial_ids = [
        result.trial_id
        for result in stored_results
    ]
    if actual_trial_ids != expected_trial_ids:
        raise AssertionError(
            "stored TrialResult trial_ids must be exactly 1..6000"
        )

    stored_by_id = {
        result.trial_id: result
        for result in stored_results
    }

    reference = stored_results[0]
    scenario_id = reference.scenario_id
    collection_probability = (
        reference.collection_probability
    )
    recovery_rate_pct = reference.recovery_rate_pct

    for result in stored_results:
        if result.scenario_id != scenario_id:
            raise AssertionError(
                "stored TrialResult scenario_id values differ"
            )
        if (
            result.collection_probability
            != collection_probability
        ):
            raise AssertionError(
                "stored TrialResult collection_probability values differ"
            )
        if (
            result.recovery_rate_pct
            != recovery_rate_pct
        ):
            raise AssertionError(
                "stored TrialResult recovery_rate_pct values differ"
            )

    rerun_results: list[
        monte_carlo.TrialResult
    ] = []
    per_trial_match: dict[str, bool] = {}

    for trial_id in SAMPLE_TRIAL_IDS:
        project = daily_engine.run_deterministic_trial(
            recovery_rate_pct=recovery_rate_pct,
            trial_id=trial_id,
            scenario_id=scenario_id,
            master_seed=constants.MASTER_SEED,
            collection_probability=collection_probability,
            log_events=False,
        )

        rerun_result = (
            monte_carlo._trial_result_from_project(
                project,
                scenario_id=scenario_id,
                collection_probability=collection_probability,
                recovery_rate_pct=recovery_rate_pct,
                trial_id=trial_id,
            )
        )

        stored_result = stored_by_id[trial_id]
        rerun_results.append(rerun_result)
        per_trial_match[str(trial_id)] = (
            asdict(rerun_result)
            == asdict(stored_result)
        )

    stored_sample_results = [
        stored_by_id[trial_id]
        for trial_id in SAMPLE_TRIAL_IDS
    ]

    stored_sample_fingerprint = (
        monte_carlo.fingerprint_trial_results(
            stored_sample_results
        )
    )
    rerun_sample_fingerprint = (
        monte_carlo.fingerprint_trial_results(
            rerun_results
        )
    )

    aggregate_fingerprint = (
        monte_carlo.fingerprint_trial_results(
            stored_results
        )
    )

    aggregate_fingerprint_match = (
        aggregate_fingerprint
        == EXPECTED_CP2_AGGREGATE_SHA256
    )
    per_trial_fingerprint_match = (
        rerun_sample_fingerprint
        == stored_sample_fingerprint
    )
    all_match = (
        all(per_trial_match.values())
        and aggregate_fingerprint_match
        and per_trial_fingerprint_match
    )

    payload = {
        "sample_trial_ids": list(SAMPLE_TRIAL_IDS),
        "per_trial_match": per_trial_match,
        "aggregate_fingerprint": aggregate_fingerprint,
        "expected_cp2_aggregate_sha256": (
            EXPECTED_CP2_AGGREGATE_SHA256
        ),
        "aggregate_fingerprint_match": (
            aggregate_fingerprint_match
        ),
        "stored_sample_fingerprint": (
            stored_sample_fingerprint
        ),
        "rerun_sample_fingerprint": (
            rerun_sample_fingerprint
        ),
        "per_trial_fingerprint_match": (
            per_trial_fingerprint_match
        ),
        "all_match": all_match,
    }

    output_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
        )
        + "
",
        encoding="utf-8",
    )

    print(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
        )
    )

    if not all_match:
        raise AssertionError(
            "CP3 verification mismatch"
        )


if __name__ == "__main__":
    main()
