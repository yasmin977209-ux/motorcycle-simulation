from __future__ import annotations

from types import SimpleNamespace

from scripts import p16_produce_deliverables_v4 as producer


def test_write_reports_uses_the_actual_candidate_branch_name(tmp_path, monkeypatch) -> None:
    # Keep the scope synthetic: no Parquet, workbook, artifact or production input is read.
    monkeypatch.setattr(
        producer.pq,
        "read_table",
        lambda _path: SimpleNamespace(to_pylist=lambda: []),
    )

    scenarios = producer.excel_builder.EXPECTED_SCENARIOS
    summaries = {
        scenario: {
            "trial_count": 450,
            "p10_profit": 100,
            "p50_profit": 200,
            "p90_profit": 300,
            "p50_cash": 400,
            "p90_cash": 500,
            "loss_probability": 0.1,
        }
        for scenario in scenarios
    }
    assignments = {
        scenario: {"MaxCase": 1}
        for scenario in scenarios
    }
    input_artifacts = {
        scenario: {
            "artifact_id": 123,
            "artifact_run_id": 456,
            "producer_sha": "a" * 40,
            "artifact_sha256": "b" * 64,
        }
        for scenario in scenarios
    }
    actual_branch = "tmp/p16-report-provenance-test-current-branch"

    producer.write_reports(
        output_dir=tmp_path,
        dataset_root=tmp_path / "synthetic-input-only",
        manifest={},
        input_artifacts=input_artifacts,
        summaries=summaries,
        assignments=assignments,
        total_trials=9005,
        tested_sha="c" * 40,
        run_id="123456789",
        branch=actual_branch,
    )

    for filename in ("Full_Report_EN", "التقرير_الكامل_AR"):
        report = (tmp_path / filename).read_text(encoding="utf-8")
        assert f"branch: {actual_branch}" in report
        assert "tmp/p16-provisional-outputs-20261021" not in report
        assert "PENDING_DATA_SOURCE" in report
        assert "Delivery = NOT_ACCEPTED" in report
