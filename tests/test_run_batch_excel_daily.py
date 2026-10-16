from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest
import pyarrow.parquet as pq

import constants
import monte_carlo
import run_batch
from scripts import excel_builder
from scripts.stage7_state import StateIntegrityError


TEST_SOURCE_SHA = "0000000000000000000000000000000000000000"
SCENARIO = "C070_G100"


def _trial(trial_id: int, equity: int) -> monte_carlo.TrialResult:
    return monte_carlo.TrialResult(
        scenario_id=SCENARIO,
        collection_probability=0.7,
        recovery_rate_pct=100,
        trial_id=trial_id,
        final_close_date="2027-01-02",
        final_net_project_equity=equity,
        final_cash=equity // 2,
        cumulative_project_profit=equity - 100,
        operating_net_profit=equity - 80,
        termination_count=0,
        secondary_cycle_count=0,
        owned_bikes=1,
        held_assets=0,
        total_operating_revenue=equity + 50,
        bad_debt=0,
        guarantee_recovered=0,
        partner1_final_entitlement=equity * 70 // 100,
        partner2_final_entitlement=equity * 30 // 100,
    )


def _daily_rows(trial_id: int, cash: int, equity: int) -> list[dict[str, object]]:
    common = {
        "trial_id": trial_id,
        "Capital": 100,
        "Retained_Earnings": equity - 100,
        "Active_Bikes": 10 - trial_id,
        "Owned_Transferred_Bikes": 0,
        "Pending_Claims": 0,
        "Final_Close_Date": "2027-01-02",
    }
    return [
        {
            **common,
            "date": "2027-01-01",
            "Cash": cash,
            "Net_Equity": equity,
        },
        {
            **common,
            "date": "2027-01-02",
            "Cash": cash + 5,
            "Net_Equity": equity + 5,
            "Final_Close_Date": "2027-01-02",
        },
    ]


def test_cli_exposes_excel_dataset_root_with_uniform_c100_policy(tmp_path: Path) -> None:
    args = run_batch.parse_args(
        [
            "--scenario", SCENARIO,
            "--trials", "2",
            "--output-dir", str(tmp_path / "batch"),
            "--excel-dataset-root", str(tmp_path / "excel"),
        ]
    )
    assert args.scenario == SCENARIO
    assert args.trials == 2
    assert args.excel_dataset_root == str(tmp_path / "excel")

    c100 = run_batch.parse_args(
        [
            "--scenario", "C100_G100",
            "--trials", "300",
            "--output-dir", str(tmp_path / "c100"),
        ]
    )
    assert c100.trials == constants.C100_STATISTICAL_START_TRIALS == 300
    assert c100.trials == constants.NON_C100_STATISTICAL_START_TRIALS

    # C100 now accepts ordinary batch sizes exactly as other scenarios do.
    c100_partial = run_batch.parse_args(
        [
            "--scenario", "C100_G100",
            "--trials", "2",
            "--output-dir", str(tmp_path / "c100-partial"),
        ]
    )
    assert c100_partial.trials == 2


def test_batch_daily_outputs_round_trip_through_excel_builder_loaders(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_dir = tmp_path / "batch"
    excel_root = tmp_path / "excel-dataset"
    fake_results = [_trial(1, 120), _trial(2, 140)]
    fake_slices = {1: _daily_rows(1, 10, 120), 2: _daily_rows(2, 20, 140)}

    def no_simulation(
        scenario: str,
        trial_ids: tuple[int, ...] | list[int],
        *,
        master_seed: int,
    ) -> tuple[list[monte_carlo.TrialResult], dict[int, list[dict[str, object]]]]:
        selected_ids = [int(x) for x in trial_ids]
        return (
            [result for result in fake_results if result.trial_id in selected_ids],
            {trial_id: fake_slices[trial_id] for trial_id in selected_ids},
        )

    monkeypatch.setattr(monte_carlo, "run_trials_sequentially", no_simulation)
    state = run_batch.run_batch(
        scenario=SCENARIO,
        trials=2,
        output_dir=output_dir,
        master_seed=constants.MASTER_SEED,
        source_sha=TEST_SOURCE_SHA,
        excel_dataset_root=excel_root,
    )

    scenario_root = excel_root / SCENARIO
    trial_path = scenario_root / "trial_results.parquet"
    distribution_path = scenario_root / "daily_distribution.parquet"
    raw_daily_path = scenario_root / "daily_trial_slices.parquet"
    manifest_path = scenario_root / "daily_export_manifest.json"

    assert trial_path.is_file()
    assert distribution_path.is_file()
    assert raw_daily_path.is_file()
    assert manifest_path.is_file()
    assert (output_dir / "daily_slices.parquet").is_file()

    loaded_trials = excel_builder.load_scenario_trials(excel_root, SCENARIO)
    loaded_distribution = excel_builder.load_scenario_daily_distribution(
        excel_root, SCENARIO
    )
    assert [row["trial_id"] for row in loaded_trials] == [1, 2]
    assert len(loaded_distribution) == 10
    assert {row["date"] for row in loaded_distribution} == {
        "2027-01-01", "2027-01-02"
    }
    assert all(row["active_trial_count"] == 2 for row in loaded_distribution)
    assert {
        "Cash", "Net_Equity", "Active_Bikes",
        "Owned_Transferred_Bikes", "Pending_Claims",
    } <= set(loaded_distribution[0])

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["source_sha"] == TEST_SOURCE_SHA
    assert manifest["master_seed"] == constants.MASTER_SEED
    assert manifest["trial_count"] == 2
    assert manifest["daily_distribution_rows"] == 10
    assert manifest["gate_a_status"] == "NOT_REACHED"
    assert manifest["full_excel_delivery"] == "NOT_ASSERTED_BY_THIS_EXPORT"
    assert state["final_status"] != "stable" or state["included_in_final_stats"]

    raw_records = pq.read_table(raw_daily_path).to_pylist()
    assert len(raw_records) == 4
    assert {row["trial_id"] for row in raw_records} == {1, 2}

    evidence_dir = os.environ.get("CP_RUNTIME_EVIDENCE_DIR")
    if evidence_dir:
        evidence_root = Path(evidence_dir)
        evidence_root.mkdir(parents=True, exist_ok=True)
        shutil.copytree(output_dir, evidence_root / "batch-output", dirs_exist_ok=True)
        shutil.copytree(excel_root, evidence_root / "excel-dataset", dirs_exist_ok=True)
        report = {
            "status": "PASS_DAILY_DATASET_EXCEL_LOADER_ROUND_TRIP",
            "simulator_invocations": 0,
            "trial_rows": len(loaded_trials),
            "daily_slice_rows": len(raw_records),
            "daily_distribution_rows": len(loaded_distribution),
            "excel_builder_loaders": [
                "load_scenario_trials",
                "load_scenario_daily_distribution",
            ],
            "test_source_sha_sentinel": TEST_SOURCE_SHA,
            "production_source_sha_unchanged": "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b",
            "master_seed": constants.MASTER_SEED,
            "scenario": SCENARIO,
            "final_status": state["final_status"],
            "full_excel_delivery": "NOT_ASSERTED_BY_THIS_EXPORT",
        }
        (evidence_root / "round-trip-report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def test_resume_fails_closed_when_completed_trials_have_no_daily_rows(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    output_dir = tmp_path / "old-batch"
    output_dir.mkdir()
    results = [_trial(1, 120), _trial(2, 140)]
    run_batch._write_dataset(results, output_dir)
    fingerprint = monte_carlo.fingerprint_trial_results(results)
    checkpoint = {
        "stage": "7",
        "scenario": SCENARIO,
        "source_sha": TEST_SOURCE_SHA,
        "completed_trials": 2,
        "next_trial_id": 3,
        "next_check_n": 300,
        "final_fingerprint": fingerprint,
        "artifact_identity": {
            "scenario": SCENARIO,
            "source_sha": TEST_SOURCE_SHA,
            "trial_id_start": 1,
            "trial_id_end": 2,
            "fingerprint_sha256": fingerprint,
        },
        "stability_history": [],
    }
    monkeypatch.setattr(run_batch, "load_stage7_checkpoint", lambda **_: checkpoint)
    with pytest.raises(StateIntegrityError, match="refusing to replay completed trial IDs"):
        run_batch.run_batch(
            scenario=SCENARIO,
            trials=1,
            output_dir=output_dir,
            resume_from_checkpoint=True,
            source_sha=TEST_SOURCE_SHA,
        )
