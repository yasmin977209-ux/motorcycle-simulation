from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.stage13_maxcase_source_audit import (
    load_expected_p16_maxcase_map,
    select_maxcase,
)

EXPECTED_MAP_PATH = Path("docs/audits/p16_maxcase_expected_ids_20261021.json")


def _rows() -> list[dict]:
    rows = [
        {"trial_id": trial_id, "final_net_project_equity": 10_000 + trial_id}
        for trial_id in range(1, 551)
    ]
    # The highest result in the Stage 9A 450-trial cohort must be selected,
    # even though a larger result exists at trial 550 in the wider Stage 12 set.
    rows[415]["final_net_project_equity"] = 500_000
    rows[549]["final_net_project_equity"] = 600_000
    return rows


def test_p16_450_selection_cap_does_not_use_trials_451_to_550() -> None:
    rows = _rows()
    selected_p16 = select_maxcase(rows, max_trial_id=450)
    selected_stage12 = select_maxcase(rows, max_trial_id=550)
    selected_default = select_maxcase(rows)

    assert selected_p16 is not None
    assert selected_p16["trial_id"] == 416
    assert selected_p16["final_net_project_equity"] == 500_000
    assert selected_stage12 is not None
    assert selected_stage12["trial_id"] == 550
    assert selected_default == selected_stage12


def test_maxcase_selection_keeps_smallest_trial_id_for_ties_with_cap() -> None:
    rows = [
        {"trial_id": 8, "final_net_project_equity": 900},
        {"trial_id": 3, "final_net_project_equity": 900},
        {"trial_id": 12, "final_net_project_equity": 899},
    ]

    selected = select_maxcase(rows, max_trial_id=450)
    assert selected is not None
    assert selected["trial_id"] == 3


@pytest.mark.parametrize("invalid_cap", [449, 451, 5500, True, 450.0, "450", None])
def test_explicit_maxcase_cap_rejects_invalid_values(invalid_cap) -> None:
    if invalid_cap is None:
        # None is the documented default mode, and thus is intentionally valid.
        assert select_maxcase(_rows(), max_trial_id=invalid_cap) is not None
    else:
        with pytest.raises(ValueError, match="exactly 450 or 550"):
            select_maxcase(_rows(), max_trial_id=invalid_cap)


def test_p16_expected_selection_map_is_source_pinned_and_covers_25_scenarios() -> None:
    expected = load_expected_p16_maxcase_map(str(EXPECTED_MAP_PATH))

    assert expected["artifact_provenance"]["p16_primary_artifact_id"] == 12363135623
    assert expected["artifact_provenance"]["p16_artifact_zip_sha256"] == (
        "7e2e821e8c1f8e13b37189638e9a975ac8fc8862ee349abce928fea0cd048ada"
    )
    assert expected["artifact_provenance"]["embedded_output_manifest_sha256"] == (
        "c50488f27541e20ba15b99d259966c41b51a5a15f5e8805cb8dd57f55027a44c"
    )
    assert len(expected["maxcase_by_scenario"]) == 25
    assert expected["maxcase_by_scenario"]["C050_G050"] == {
        "trial_id": 416,
        "final_net_project_equity": 323662600,
    }
    assert expected["maxcase_by_scenario"]["C070_G050"] == {
        "trial_id": 214,
        "final_net_project_equity": 209293500,
    }
    assert expected["maxcase_by_scenario"]["C085_G070"] == {
        "trial_id": 285,
        "final_net_project_equity": 209886500,
    }


def test_p16_expected_selection_map_rejects_modified_provenance(tmp_path: Path) -> None:
    expected = load_expected_p16_maxcase_map(str(EXPECTED_MAP_PATH))
    expected["artifact_provenance"]["p16_artifact_zip_sha256"] = "0" * 64
    altered = tmp_path / "altered.json"
    altered.write_text(json.dumps(expected), encoding="utf-8")

    with pytest.raises(RuntimeError, match="P16_EXPECTED_MAXCASE_MAP_PROVENANCE_MISMATCH"):
        load_expected_p16_maxcase_map(str(altered))
