from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _state() -> dict:
    return json.loads((ROOT / "state.json").read_text(encoding="utf-8"))


def test_head_and_main_audit_snapshot_are_explicit() -> None:
    state = _state()
    head_sha = state.get("head_sha")
    assert isinstance(head_sha, str)
    assert len(head_sha) == 40
    assert all(char in "0123456789abcdef" for char in head_sha)
    assert head_sha.lower() != "dynamic"
    assert state.get("main_head_at_audit") == (
        "647c19826b90d8224ce73ef9b90c306a45e03fb0"
    )


def test_governance_decision_exists_and_gate_a_is_not_duplicated() -> None:
    state = _state()
    assert "D-2026-10-12-01" in state["governance_decisions"]
    assert state["cp_completed"].count("CP-GATEA-FAIL-CLOSED-20261013") == 1


def test_stage11_is_closed_by_scope_not_marked_complete() -> None:
    state = _state()
    assert state["stage11"]["status"] == "CLOSED_BY_APPROVED_SCOPE_DECISION"
    assert state["stage11"]["status"] != "COMPLETE"
    assert state["stage11"]["stage10_metadata_discrepancy"]["status"] == "REMAINS_OPEN"
