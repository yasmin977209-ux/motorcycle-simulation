from __future__ import annotations

from openpyxl import Workbook
import pytest

from scripts.stage13_maxcase_source_audit import (
    _cpf_artifact_maxcase_trial_id,
    _non_c100_daily_rows_from_cpf_artifact,
    _non_c100_daily_rows_from_enriched_role_artifact,
    _pending_maxcase_memo_rows,
    _read_representative_summary_daily,
    reconcile_enriched_c100_daily_rows,
)
from scripts import stage13_gatea_fingerprint_bridge as gatea

from scripts.stage13_assemble import (
    EXPECTED_SCENARIOS,
    _validate_representatives,
    representative_daily_value,
    write_representatives,
)


def _trial_row(scenario: str) -> dict:
    return {
        "scenario_id": scenario,
        "trial_id": 1,
        "collection_probability": int(scenario[1:4]) / 100.0,
        "recovery_rate_pct": int(scenario[6:9]),
        "final_net_project_equity": 100,
        "final_cash": 50,
        "cumulative_project_profit": 40,
        "operating_net_profit": 10,
        "final_close_date": "2027-01-01",
        "termination_count": 0,
        "secondary_cycle_count": 0,
        "owned_bikes": 1,
        "held_assets": 0,
        "total_operating_revenue": 100,
        "bad_debt": 0,
        "guarantee_recovered": 0,
    }


def _fixture_data() -> dict:
    rows_by_scenario = {}
    reps_by_scenario = {}
    for scenario in EXPECTED_SCENARIOS:
        row = _trial_row(scenario)
        rows_by_scenario[scenario] = [row]
        daily = {
            "trial_id": 1,
            "date": "2027-01-01",
            "Final_Close_Date": "2027-01-01",
            "Cash": 50,
            "Net_Equity": 100,
            "Cumulative_Project_Profit": 40,
            "Operating_Net_Profit": 10,
            "Active_Bikes": 1,
            "Owned_Transferred_Bikes": 0,
            "Pending_Claims": 0,
            "Partner1_Reinvestment_Balance": 25,
            "Partner2_Reinvestment_Balance": 15,
        }
        roles = {}
        for role in ("P10", "P50", "P90", "Loss"):
            roles[role] = {"summary": row.copy(), "daily": [daily.copy()]}
        max_daily = daily.copy()
        max_daily.pop("Partner1_Reinvestment_Balance")
        max_daily.pop("Partner2_Reinvestment_Balance")
        max_daily["Cumulative_Project_Profit"] = "PENDING_DATA_SOURCE"
        roles["Max Case"] = {"summary": row.copy(), "daily": [max_daily]}
        reps_by_scenario[scenario] = roles
    return {
        "trials_by_scenario": rows_by_scenario,
        "representative_trial_ids": {},
        "representatives_by_scenario": reps_by_scenario,
    }


def test_missing_maxcase_fields_are_explicitly_pending_not_zero_or_retained_earnings():
    assert representative_daily_value("Max Case", {}, "Partner1_Reinvestment_Balance") == "PENDING_DATA_SOURCE"
    assert representative_daily_value("Max Case", {}, "Partner2_Reinvestment_Balance") == "PENDING_DATA_SOURCE"
    assert representative_daily_value("Max Case", {}, "Cumulative_Project_Profit") == "PENDING_DATA_SOURCE"
    assert representative_daily_value("P50", {}, "Partner1_Reinvestment_Balance") is None
    assert representative_daily_value("Max Case", {"Cumulative_Project_Profit": 0}, "Cumulative_Project_Profit") == 0


def test_validator_accepts_explicit_pending_marker_only_for_maxcase_daily_cumulative_profit():
    data = _fixture_data()
    assert _validate_representatives(data, "canonical") is True

    data = _fixture_data()
    data["representatives_by_scenario"]["C100_G100"]["P50"]["daily"][0][
        "Cumulative_Project_Profit"
    ] = "PENDING_DATA_SOURCE"
    with pytest.raises(RuntimeError, match="REPRESENTATIVE_DAILY_TERMINAL_MISMATCH"):
        _validate_representatives(data, "canonical")


def test_representative_sheet_writes_pending_data_source_markers():
    workbook = Workbook()
    write_representatives(workbook, _fixture_data()["representatives_by_scenario"])
    sheet = workbook["REPRESENTATIVE_CASES"]

    # C100_G100 rows: P10 (2-3), P50 (4-5), P90 (6-7), Loss (8-9), Max Case (10-11).
    assert sheet["L11"].value == "PENDING_DATA_SOURCE"
    assert sheet["M11"].value == "PENDING_DATA_SOURCE"
    assert sheet["P11"].value == "PENDING_DATA_SOURCE"
    assert sheet["P5"].value == 40


def test_c100_p50_payload_reader_selects_top_level_daily_and_summary_without_full_load():
    import io
    import json

    expected = {
        "accounting": {"not_the_daily_ledger": [{"x": 1}]},
        "daily": [
            {
                "date": "2027-01-01",
                "trial_id": 1,
                "Partner1_Reinvestment_Balance": 0,
                "Partner2_Reinvestment_Balance": 0,
            }
        ],
        "event_log": [{"type": "unrelated"}],
        "summary": {"scenario_id": "C100_G000", "trial_id": 1},
    }
    stream = io.BytesIO(json.dumps(expected, ensure_ascii=False, indent=2).encode("utf-8"))
    summary, daily = _read_representative_summary_daily(stream)
    assert summary == expected["summary"]
    assert daily == expected["daily"]


def _c100_pair():
    final_date = "2027-01-02"
    enriched = [
        {
            "date": "2027-01-01", "Final_Close_Date": final_date, "trial_id": 1,
            "Cash": 10, "Net_Equity": 100, "Cumulative_Project_Profit": -90,
            "Active_Bikes": 3, "Owned_Transferred_Bikes": 0, "Pending_Claims": 0,
            "Partner1_Reinvestment_Balance": 0, "Partner2_Reinvestment_Balance": 0,
        },
        {
            "date": "2027-01-02", "Final_Close_Date": final_date, "trial_id": 1,
            "Cash": 20, "Net_Equity": 110, "Cumulative_Project_Profit": -80,
            "Active_Bikes": 0, "Owned_Transferred_Bikes": 0, "Pending_Claims": 0,
            "Partner1_Reinvestment_Balance": 7, "Partner2_Reinvestment_Balance": 13,
        },
    ]
    stage12 = [
        {
            "date": "2027-01-01", "Final_Close_Date": final_date, "trial_id": 1,
            "Closing_Cash": 10, "Closing_Equity": 100, "Retained_Earnings": -90,
            "Active_Bikes": 3, "Owned_Transferred_Bikes": 0, "Pending_Claims": 0,
        },
        {
            "date": "2027-01-02", "Final_Close_Date": final_date, "trial_id": 1,
            "Closing_Cash": 20, "Closing_Equity": 110, "Retained_Earnings": -80,
            "Active_Bikes": 0, "Owned_Transferred_Bikes": 0, "Pending_Claims": 0,
        },
    ]
    return enriched, stage12


def test_c100_partner_memo_daily_rows_are_reused_only_after_stage12_reconciliation():
    enriched, stage12 = _c100_pair()
    result = reconcile_enriched_c100_daily_rows(
        "C100_G000", enriched, stage12, trial_id=1,
        expected_trial_sha256="a" * 64,
        source_sha="f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b",
        master_seed=20270101, final_close_date="2027-01-02",
        final_cash=20, final_equity=110, cumulative_project_profit=-80,
    )
    assert len(result) == 2
    assert result[-1]["Partner1_Reinvestment_Balance"] == 7
    assert result[-1]["Partner2_Reinvestment_Balance"] == 13
    assert result[-1]["result_sha256"] == "a" * 64


def test_c100_partner_memo_reuse_fails_if_daily_ledger_does_not_match_stage12():
    enriched, stage12 = _c100_pair()
    enriched[0]["Net_Equity"] = 999
    with pytest.raises(RuntimeError, match="C100_ENRICHED_STAGE12_LEDGER_MISMATCH"):
        reconcile_enriched_c100_daily_rows(
            "C100_G000", enriched, stage12, trial_id=1,
            expected_trial_sha256="a" * 64,
            source_sha="f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b",
            master_seed=20270101, final_close_date="2027-01-02",
            final_cash=20, final_equity=110, cumulative_project_profit=-80,
        )


def test_c100_partner_memo_reuse_rejects_boolean_balances():
    enriched, stage12 = _c100_pair()
    enriched[0]["Partner1_Reinvestment_Balance"] = True
    with pytest.raises(RuntimeError, match="C100_ENRICHED_MEMO_BALANCE_NOT_INTEGER"):
        reconcile_enriched_c100_daily_rows(
            "C100_G000", enriched, stage12, trial_id=1,
            expected_trial_sha256="a" * 64,
            source_sha="f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b",
            master_seed=20270101, final_close_date="2027-01-02",
            final_cash=20, final_equity=110, cumulative_project_profit=-80,
        )


def test_representative_payload_reader_handles_compact_json_and_nested_duplicate_keys():
    import io
    import json

    expected_summary = {"scenario_id": "C050_G000", "trial_id": 60, "nested": {"summary": "ignore"}}
    expected_daily = [{"date": "2027-01-01", "trial_id": 60, "Partner1_Reinvestment_Balance": 4,
                       "Partner2_Reinvestment_Balance": 6}]
    compact = json.dumps({
        "preceding": {"summary": {"bad": True}, "daily": [{"bad": True}]},
        "summary": expected_summary,
        "daily": expected_daily,
        "tail": "compact-json",
    }, separators=(",", ":"), ensure_ascii=False)
    summary, daily = _read_representative_summary_daily(io.BytesIO(compact.encode("utf-8")))
    assert summary == expected_summary
    assert daily == expected_daily


def _synthetic_cpf_role_fixture(tmp_path, fingerprint="a" * 64):
    import json
    import zipfile

    scenario = "C050_G000"
    summary = {
        "scenario_id": scenario, "collection_probability": 0.5, "recovery_rate_pct": 0,
        "trial_id": 60, "final_close_date": "2027-01-02",
        "final_net_project_equity": 110, "final_cash": 20,
        "cumulative_project_profit": -80, "operating_net_profit": -80,
        "termination_count": 1, "secondary_cycle_count": 0, "owned_bikes": 0,
        "held_assets": 0, "total_operating_revenue": 50, "bad_debt": 0,
        "guarantee_recovered": 0, "partner1_final_entitlement": 70,
        "partner2_final_entitlement": 30,
    }
    daily = [
        {
            "date": "2027-01-01", "Final_Close_Date": "2027-01-02", "trial_id": 60,
            "Cash": 10, "Net_Equity": 100, "Cumulative_Project_Profit": -90,
            "Retained_Earnings": -90, "Active_Bikes": 3, "Owned_Transferred_Bikes": 0,
            "Pending_Claims": 0, "Partner1_Reinvestment_Balance": 0,
            "Partner2_Reinvestment_Balance": 0, "Accounts_Receivable": 1,
            "Gross_Bike_Assets": 100, "Accumulated_Depreciation": 0,
            "Capital": 100, "Guarantee_Claim_Receivable": 0, "Operating_Net_Profit": 10,
        },
        {
            "date": "2027-01-02", "Final_Close_Date": "2027-01-02", "trial_id": 60,
            "Cash": 20, "Net_Equity": 110, "Cumulative_Project_Profit": -80,
            "Retained_Earnings": -80, "Active_Bikes": 0, "Owned_Transferred_Bikes": 0,
            "Pending_Claims": 0, "Partner1_Reinvestment_Balance": 7,
            "Partner2_Reinvestment_Balance": 13, "Accounts_Receivable": 0,
            "Gross_Bike_Assets": 110, "Accumulated_Depreciation": 0,
            "Capital": 100, "Guarantee_Claim_Receivable": 0, "Operating_Net_Profit": -80,
        },
    ]
    manifest = {
        "scenario": scenario, "status": "PASS",
        "source_sha": "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b",
        "master_seed": 20270101, "schema_version": "stage12-daily-accounting-v1",
        "historical_daily_trials": 550, "extension_trial_count": 650,
        "extension_trial_ids": list(range(551, 1201)),
        "non_c100_gate_a_fingerprints_verified": True,
        "production_monte_carlo_run": False, "historical_dataset_modified": False,
        "historical_parquet_modified": False, "main_modified": False,
        "release_created": False, "source_sha_bumped": False,
        "detail_replay_trial_ids": [60, 175, 304, 534, 709],
        "representative_payload_trial_ids": [60, 175, 304, 534, 709],
        "representative_trial_ids": {"LossCase": 304, "MaxCase": 60, "P10": 709, "P50": 175, "P90": 534},
        "trial_fingerprints": {"60": fingerprint},
    }
    path = tmp_path / "cp-f-replay-C050_G000.zip"
    payload = {
        "daily_accounting_extension.parquet": b"fixture", "daily_distribution.parquet": b"fixture",
        "representatives/Loss.json": b"{}", "representatives/P10.json": b"{}",
        "representatives/P50.json": b"{}", "representatives/P90.json": b"{}",
        "scenario_manifest.json": json.dumps(manifest, separators=(",", ":")).encode("utf-8"),
        "representatives/Max Case.json": json.dumps(
            {"summary": summary, "daily": daily}, separators=(",", ":")
        ).encode("utf-8"),
    }
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, value in payload.items():
            archive.writestr(name, value)
    stage12 = [
        {
            "date": "2027-01-01", "Final_Close_Date": "2027-01-02",
            "Closing_Cash": 10, "Closing_Equity": 100, "Retained_Earnings": -90,
            "Active_Bikes": 3, "Owned_Transferred_Bikes": 0, "Pending_Claims": 0,
            "Closing_AR": 1, "Closing_Gross_Bike_Assets": 100,
            "Closing_Accumulated_Depreciation": 0, "Capital": 100,
            "Guarantee_Claim_Receivable": 0, "Operating_Net_Profit": 10,
        },
        {
            "date": "2027-01-02", "Final_Close_Date": "2027-01-02",
            "Closing_Cash": 20, "Closing_Equity": 110, "Retained_Earnings": -80,
            "Active_Bikes": 0, "Owned_Transferred_Bikes": 0, "Pending_Claims": 0,
            "Closing_AR": 0, "Closing_Gross_Bike_Assets": 110,
            "Closing_Accumulated_Depreciation": 0, "Capital": 100,
            "Guarantee_Claim_Receivable": 0, "Operating_Net_Profit": -80,
        },
    ]
    selected = summary.copy()
    artifact = {"id": 999, "name": "cp-f-replay-C050_G000", "digest": None}
    return path, artifact, selected, stage12


def test_cpf_maxcase_role_payload_reuse_requires_manifest_trial_hash_and_day_by_day_reconciliation(tmp_path):
    path, artifact, selected, stage12 = _synthetic_cpf_role_fixture(tmp_path)
    payload, evidence = _non_c100_daily_rows_from_cpf_artifact(
        "C050_G000", artifact, path, "a" * 64, selected, stage12
    )
    assert len(payload) == 2
    assert payload[-1]["Partner1_Reinvestment_Balance"] == 7
    assert payload[-1]["Partner2_Reinvestment_Balance"] == 13
    assert payload[-1]["source_sha"] == "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
    assert payload[-1]["result_sha256"] == "a" * 64
    assert evidence["partner_memo_fields_status"] == "VERIFIED_REUSED_SOURCE_ARTIFACT"


def test_cpf_maxcase_role_payload_fails_closed_on_trial_fingerprint_mismatch(tmp_path):
    path, artifact, selected, stage12 = _synthetic_cpf_role_fixture(tmp_path)
    with pytest.raises(RuntimeError, match="CP_F_TRIAL_FINGERPRINT_MISMATCH"):
        _non_c100_daily_rows_from_cpf_artifact(
            "C050_G000", artifact, path, "b" * 64, selected, stage12
        )


def test_cpf_maxcase_role_payload_fails_closed_on_stage12_daily_mismatch(tmp_path):
    path, artifact, selected, stage12 = _synthetic_cpf_role_fixture(tmp_path)
    stage12[0]["Closing_Equity"] = 999
    with pytest.raises(RuntimeError, match="CP_F_MAXCASE_STAGE12_LEDGER_MISMATCH"):
        _non_c100_daily_rows_from_cpf_artifact(
            "C050_G000", artifact, path, "a" * 64, selected, stage12
        )

def test_pending_maxcase_memo_rows_preserve_ledger_and_never_default_missing_balances_to_zero():
    source = [
        {
            "date": "2027-01-01",
            "Cash": 123,
            "Net_Equity": 456,
            "Cumulative_Project_Profit": -7,
        }
    ]
    result = _pending_maxcase_memo_rows(source)
    assert result[0]["Cash"] == 123
    assert result[0]["Net_Equity"] == 456
    assert result[0]["Cumulative_Project_Profit"] == -7
    assert result[0]["Partner1_Reinvestment_Balance"] == "PENDING_DATA_SOURCE"
    assert result[0]["Partner2_Reinvestment_Balance"] == "PENDING_DATA_SOURCE"
    assert result[0]["Partner1_Reinvestment_Balance"] != 0
    assert result[0]["Partner2_Reinvestment_Balance"] != 0


def test_cpf_artifact_role_id_is_not_mistaken_for_selected_maxcase(tmp_path):
    path, artifact, selected, stage12 = _synthetic_cpf_role_fixture(tmp_path)
    assert _cpf_artifact_maxcase_trial_id(path, "C050_G000") == 60
    selected["trial_id"] = 53
    assert _cpf_artifact_maxcase_trial_id(path, "C050_G000") != selected["trial_id"]
    pending = _pending_maxcase_memo_rows([
        {"date": "2027-01-01", "Cash": 1, "trial_id": 53}
    ])
    assert pending[0]["trial_id"] == 53
    assert pending[0]["Partner1_Reinvestment_Balance"] == "PENDING_DATA_SOURCE"
    assert pending[0]["Partner2_Reinvestment_Balance"] == "PENDING_DATA_SOURCE"


def _synthetic_stage9a_role_artifact(tmp_path):
    import io
    import json
    import tarfile
    import zipfile
    import hashlib
    import pyarrow as pa
    import pyarrow.parquet as pq
    from scripts.stage13_maxcase_source_audit import SOURCE_SHA, MASTER_SEED, STAGE7_RUN, C100_ENRICHMENT_RUN

    scenario = "C050_G000"
    trial_id = 60
    summary = {
        "scenario_id": scenario, "collection_probability": 0.5, "recovery_rate_pct": 0,
        "trial_id": trial_id, "final_close_date": "2027-01-02",
        "final_net_project_equity": 110, "final_cash": 20,
        "cumulative_project_profit": -80, "operating_net_profit": -80,
        "termination_count": 1, "secondary_cycle_count": 0, "owned_bikes": 0,
        "held_assets": 0, "total_operating_revenue": 50, "bad_debt": 0,
        "guarantee_recovered": 0, "partner1_final_entitlement": 70,
        "partner2_final_entitlement": 30,
    }
    daily = [
        {
            "date": "2027-01-01", "Final_Close_Date": "2027-01-02", "trial_id": trial_id,
            "Cash": 10, "Net_Equity": 100, "Cumulative_Project_Profit": -90,
            "Retained_Earnings": -90, "Active_Bikes": 3, "Owned_Transferred_Bikes": 0,
            "Pending_Claims": 0, "Partner1_Reinvestment_Balance": 0,
            "Partner2_Reinvestment_Balance": 0,
        },
        {
            "date": "2027-01-02", "Final_Close_Date": "2027-01-02", "trial_id": trial_id,
            "Cash": 20, "Net_Equity": 110, "Cumulative_Project_Profit": -80,
            "Retained_Earnings": -80, "Active_Bikes": 0, "Owned_Transferred_Bikes": 0,
            "Pending_Claims": 0, "Partner1_Reinvestment_Balance": 7,
            "Partner2_Reinvestment_Balance": 13,
        },
    ]
    trial_rows = []
    for tid in range(1, 451):
        row = {**summary, "trial_id": tid}
        trial_rows.append(row)
    selected_row = next(row for row in trial_rows if row["trial_id"] == trial_id)
    fingerprint = gatea.row_sha(selected_row)
    metadata = {
        "scenario": scenario, "source_sha": SOURCE_SHA, "master_seed": MASTER_SEED,
        "run_id": STAGE7_RUN, "trial_count": 450, "recovery_rate_pct": 0,
        "collection_probability": 0.5,
    }
    fingerprints = {
        "scenario": scenario, "source_sha": SOURCE_SHA, "run_id": STAGE7_RUN,
        "trial_count": 450, "fingerprints": {str(trial_id): fingerprint},
    }
    parquet_buffer = io.BytesIO()
    pq.write_table(pa.Table.from_pylist(trial_rows), parquet_buffer)
    members = {
        "scenario_metadata.json": json.dumps(metadata, separators=(",", ":")).encode(),
        "trial_fingerprints.json": json.dumps(fingerprints, separators=(",", ":")).encode(),
        "trial_results.parquet": parquet_buffer.getvalue(),
        "representatives/P50.json": json.dumps(
            {"summary": summary, "daily": daily}, separators=(",", ":")
        ).encode(),
    }
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w:gz") as tar:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    archive_path = tmp_path / "stage9a-enriched.zip"
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as outer:
        outer.writestr("scenario.tar.gz", tar_buffer.getvalue())
    archive_sha = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    artifact = {
        "id": 999, "name": f"stage9a06-enriched-{scenario}",
        "digest": f"sha256:{archive_sha}",
    }
    manifest = {
        "representative_trials": {scenario: {"P10": 15, "P50": trial_id, "P90": 10, "Loss": 136}},
        "artifact_manifest": {
            "enriched_artifacts": {scenario: 999},
            "enrichment_run_ids": {scenario: C100_ENRICHMENT_RUN},
        },
    }
    inventory = {
        "scenario": scenario, "artifact_id": 999, "run_id": C100_ENRICHMENT_RUN,
        "zip_sha256": archive_sha,
        "roles": {"P50": {"trial_id": trial_id, "daily_rows": 2}},
    }
    stage12 = [
        {
            "date": "2027-01-01", "Final_Close_Date": "2027-01-02",
            "Closing_Cash": 10, "Closing_Equity": 100, "Retained_Earnings": -90,
            "Active_Bikes": 3, "Owned_Transferred_Bikes": 0, "Pending_Claims": 0,
        },
        {
            "date": "2027-01-02", "Final_Close_Date": "2027-01-02",
            "Closing_Cash": 20, "Closing_Equity": 110, "Retained_Earnings": -80,
            "Active_Bikes": 0, "Owned_Transferred_Bikes": 0, "Pending_Claims": 0,
        },
    ]
    return archive_path, artifact, summary, stage12, manifest, inventory, fingerprint


def test_stage9a_role_reuse_requires_exact_trial_fingerprint_and_day_by_day_reconciliation(tmp_path):
    from scripts.stage13_maxcase_source_audit import _non_c100_daily_rows_from_enriched_role_artifact
    from scripts.stage13_maxcase_source_audit import SOURCE_SHA

    path, artifact, selected, stage12, manifest, inventory, fingerprint = _synthetic_stage9a_role_artifact(tmp_path)
    with_role, evidence = _non_c100_daily_rows_from_enriched_role_artifact(
        "C050_G000", "P50", artifact, path, fingerprint, selected, stage12, manifest, inventory
    )
    assert len(with_role) == 2
    assert with_role[-1]["Partner1_Reinvestment_Balance"] == 7
    assert with_role[-1]["Partner2_Reinvestment_Balance"] == 13
    assert with_role[-1]["source_sha"] == SOURCE_SHA
    assert evidence["partner_memo_fields_status"] == "VERIFIED_REUSED_SOURCE_ARTIFACT"
    assert evidence["day_by_day_stage12_reconciliation"] is True


def test_stage9a_role_reuse_rejects_a_different_selected_trial(tmp_path):
    from scripts.stage13_maxcase_source_audit import _non_c100_daily_rows_from_enriched_role_artifact

    path, artifact, selected, stage12, manifest, inventory, fingerprint = _synthetic_stage9a_role_artifact(tmp_path)
    selected = {**selected, "trial_id": 61}
    with pytest.raises(RuntimeError, match="STAGE9A_ROLE_TRIAL_ID_MISMATCH"):
        _non_c100_daily_rows_from_enriched_role_artifact(
            "C050_G000", "P50", artifact, path, fingerprint, selected, stage12, manifest, inventory
        )
