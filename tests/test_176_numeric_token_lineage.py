from __future__ import annotations

import json
from pathlib import Path


def test_176_every_numeric_token_has_a_registry_or_explicit_classification():
    path = Path("docs/stage_d/D4_NUMERIC_TOKEN_LINEAGE_2026-11-07.json")
    report = json.loads(path.read_text(encoding="utf-8"))

    assert report["acceptance"] == "PASS"
    assert report["unresolved_occurrences"] == 0
    assert report["identity_equation"] is True
    assert report["total_occurrences"] == (
        report["resolved_occurrences"] + report["explicitly_classified_occurrences"]
    )

    required = {
        "التقرير_الكامل_AR.docx",
        "Full_Report_EN.docx",
        "الملخص_AR.docx",
        "Summary_EN.docx",
        "دراسة_الجدوى_AR.docx",
    }
    observed = {Path(item["file"]).name for item in report["documents"]}
    assert observed == required
    assert all(item["xml_parts_scanned"] > 0 for item in report["documents"])
