from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.stage7_golden_reference import (
    GoldenReferenceError,
    compare_known_golden_trials,
    evaluate_gate_a_for_results,
    load_golden_manifest,
    ordered_trial_map_sha256,
    trial_result_sha256,
    validate_model_source,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO_ROOT / "scripts" / "data" / "stage12_golden_fingerprints_v1.json"
SOURCE_SHA = "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
GLOBAL_SHA = "7a5de15c78b862749bc3ff6e689fe44909827d903ba7cbc4b469ca126ff25d44"


def _row(trial_id: int, *, scenario: str = "C030_G000", final_cash: int | None = None) -> dict:
    return {
        "scenario_id": scenario,
        "trial_id": trial_id,
        "final_cash": trial_id if final_cash is None else final_cash,
    }


def _unit_manifest(rows: list[dict], *, scenario: str = "C030_G000") -> dict:
    hashes = {str(row["trial_id"]): trial_result_sha256(row) for row in rows}
    ordered = [(scenario, int(row["trial_id"]), hashes[str(row["trial_id"])]) for row in rows]
    return {
        "canonical_reference_id": "UNIT_TEST_GOLDEN_V1",
        "scenarios": {
            scenario: {
                "trial_hashes": hashes,
                "historical_trial_result_fingerprint_sha256": ordered_trial_map_sha256(ordered),
            }
        },
    }


def test_canonical_manifest_has_11005_exact_historical_hashes() -> None:
    manifest = load_golden_manifest(
        MANIFEST_PATH, source_sha=SOURCE_SHA, master_seed=20270101
    )
    assert len(manifest["scenarios"]) == 25
    assert sum(len(item["trial_hashes"]) for item in manifest["scenarios"].values()) == 11005
    assert manifest["global_ordered_trial_hash_map_sha256"] == GLOBAL_SHA
    assert manifest["hash_map_sha256_recomputed"] == GLOBAL_SHA
    assert all(
        item["historical_trial_result_fingerprint_sha256"]
        for item in manifest["scenarios"].values()
    )


def test_manifest_rejects_wrong_source_and_seed() -> None:
    with pytest.raises(GoldenReferenceError, match="SOURCE_SHA_MISMATCH"):
        load_golden_manifest(MANIFEST_PATH, source_sha="0" * 40, master_seed=20270101)
    with pytest.raises(GoldenReferenceError, match="MASTER_SEED_MISMATCH"):
        load_golden_manifest(MANIFEST_PATH, source_sha=SOURCE_SHA, master_seed=7)


def test_manifest_rejects_missing_file() -> None:
    with pytest.raises(GoldenReferenceError, match="GOLDEN_MANIFEST_MISSING"):
        load_golden_manifest(REPO_ROOT / "missing-golden.json", source_sha=SOURCE_SHA, master_seed=20270101)


def test_exact_golden_trial_map_passes_for_matching_rows() -> None:
    rows = [_row(i) for i in range(1, 301)]
    manifest = _unit_manifest(rows)
    evidence = compare_known_golden_trials(
        scenario="C030_G000", results=rows, current_n=300, manifest=manifest
    )
    assert evidence["historical_mismatch_count"] == 0
    assert evidence["expected_golden_fingerprint_sha256"] == evidence["actual_fingerprint_sha256"]
    assert evidence["golden_coverage_count"] == 300
    assert evidence["current_n_without_historical_goldens"] == 0


def test_exact_golden_trial_map_fails_on_one_changed_trial() -> None:
    golden_rows = [_row(i) for i in range(1, 301)]
    actual_rows = [_row(i, final_cash=999999 if i == 17 else None) for i in range(1, 301)]
    manifest = _unit_manifest(golden_rows)
    evidence = compare_known_golden_trials(
        scenario="C030_G000", results=actual_rows, current_n=300, manifest=manifest
    )
    assert evidence["historical_mismatch_count"] == 1
    assert evidence["historical_mismatches"][0]["trial_id"] == 17
    assert evidence["expected_golden_fingerprint_sha256"] != evidence["actual_fingerprint_sha256"]


def test_checkpoint_600_compares_only_550_verified_historical_ids() -> None:
    golden_rows = [_row(i) for i in range(1, 551)]
    current_rows = [_row(i) for i in range(1, 601)]
    manifest = _unit_manifest(golden_rows)
    evidence = compare_known_golden_trials(
        scenario="C030_G000", results=current_rows, current_n=600, manifest=manifest
    )
    assert evidence["historical_mismatch_count"] == 0
    assert evidence["golden_coverage_count"] == 550
    assert evidence["golden_coverage_current_n"] == 600
    assert evidence["current_n_without_historical_goldens"] == 50
    assert evidence["expected_golden_fingerprint_sha256"] == evidence["actual_fingerprint_sha256"]


def test_gate_a_blocks_checkpoint_when_exact_golden_coverage_is_incomplete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import scripts.stage7_golden_reference as provider

    rows = [_row(i) for i in range(1, 551)]
    manifest = _unit_manifest(rows)
    monkeypatch.setattr(provider, "load_golden_manifest", lambda *args, **kwargs: manifest)
    monkeypatch.setattr(provider, "validate_model_source", lambda *args, **kwargs: SOURCE_SHA)

    gate = provider.evaluate_gate_a_for_results(
        previous_n=300,
        previous_metrics={},
        current_n=600,
        current_metrics={},
        escalation_multiplier=2,
        relative_epsilon=0.01,
        absolute_epsilon=1,
        results=[*_row_results_for_test(rows), *[_row(i) for i in range(551, 601)]],
        scenario="C030_G000",
        source_sha=SOURCE_SHA,
        master_seed=20270101,
        model_source_root=tmp_path,
        manifest_path=MANIFEST_PATH,
        loaded_modules=None,
    )
    assert gate["checked"] is False
    assert gate["stable"] is False
    assert gate["status"] == "BLOCKED"
    assert gate["golden_coverage_count"] == 550
    assert gate["current_n_without_historical_goldens"] == 50
    assert "full checkpoint" in gate["reason"]


def _row_results_for_test(rows: list[dict]):
    from types import SimpleNamespace

    return [SimpleNamespace(**row) for row in rows]


def test_gate_a_cannot_pass_without_a_pinned_source_root() -> None:
    rows = [_row(i) for i in range(1, 301)]
    manifest = _unit_manifest(rows)
    gate = evaluate_gate_a_for_results(
        previous_n=None,
        previous_metrics=None,
        current_n=300,
        current_metrics={},
        escalation_multiplier=2,
        relative_epsilon=0.01,
        absolute_epsilon=1,
        results=rows,
        scenario="C030_G000",
        source_sha=SOURCE_SHA,
        master_seed=20270101,
        model_source_root=None,
        manifest_path=MANIFEST_PATH,
    )
    assert gate["checked"] is False
    assert gate["stable"] is False
    assert gate["status"] == "BLOCKED"


def test_unverified_model_directory_cannot_be_accepted_as_pinned_source(tmp_path: Path) -> None:
    (tmp_path / "daily_engine.py").write_text("# not the source", encoding="utf-8")
    with pytest.raises(GoldenReferenceError, match="GIT_IDENTITY_UNAVAILABLE"):
        validate_model_source(tmp_path, expected_source_sha=SOURCE_SHA)


def test_ordered_fingerprint_preserves_scenario_trial_and_hash_tuple_identity() -> None:
    rows = [
        ("C030_G000", 2, "b" * 64),
        ("C030_G000", 1, "a" * 64),
    ]
    same_sorted = [
        ("C030_G000", 1, "a" * 64),
        ("C030_G000", 2, "b" * 64),
    ]
    assert ordered_trial_map_sha256(rows) == ordered_trial_map_sha256(same_sorted)
    assert ordered_trial_map_sha256(rows) != ordered_trial_map_sha256(
        [("C030_G000", 1, "a" * 64), ("C030_G001", 2, "b" * 64)]
    )
