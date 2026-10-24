from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "docs" / "stage9a" / "dataset_manifest.json"


def load_manifest() -> dict:
    return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))


def test_c050_g000_enriched_artifact_matches_recorded_enrichment_run() -> None:
    manifest = load_manifest()

    assert manifest["artifact_manifest"]["enriched_artifacts"]["C050_G000"] == 11503510055
    assert manifest["artifact_manifest"]["enrichment_run_ids"]["C050_G000"] == 37662891608
    assert manifest["scenarios"]["C050_G000"]["enriched_artifact_id"] == 11503510055


def test_c050_g000_provenance_correction_preserves_data_identity() -> None:
    manifest = load_manifest()
    scenario = manifest["scenarios"]["C050_G000"]
    representative = manifest["representative_trials"]["C050_G000"]

    assert manifest["global_manifest_sha256"] == (
        "892da438955160bb59aff3046271402f57bdd61a4abb35f41db7188f61346ff6"
    )
    assert manifest["source_sha"] == "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
    assert manifest["master_seed"] == 20270101
    assert scenario["scenario_fingerprint"] == (
        "dc428780bd6603269c0816842c4f7ead8153ec14bde69bdbe820ab40ad99f3fc"
    )
    assert scenario["trial_count"] == 450
    assert {
        role: representative[role]
        for role in ("P10", "P50", "P90", "Loss")
    } == {"P10": 131, "P50": 29, "P90": 18, "Loss": 304}
