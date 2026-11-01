from fractions import Fraction

import pytest

from scripts.d3_registry_extension import build_sensitivity_entries


def test_sensitivity_entries_cover_both_dimensions_with_exact_ids():
    entries = []
    for collection in (30, 50, 70, 85, 100):
        for guarantee in (0, 30, 50, 70, 100):
            scenario = f"C{collection:03d}_G{guarantee:03d}"
            entries.append({
                "scenario_id": scenario,
                "metric_name": f"{scenario}.N2400.mean.Cumulative_Project_Profit",
                "number_id": "NR-" + f"{collection:02d}{guarantee:03d}".ljust(24, "0")[:24],
                "numerator": collection * 1000 + guarantee * 100,
                "denominator": 1,
            })
    rows = build_sensitivity_entries(entries)
    assert len(rows) == 40
    assert len({row["number_id"] for row in rows}) == 40
    assert {row["dimension"] for row in rows} == {"COLLECTION", "GUARANTEE"}
    assert all(row["source_number_ids"] == [row["from_number_id"], row["to_number_id"]] for row in rows)
    assert all(row["denominator"] == 1 for row in rows)


def test_sensitivity_entries_fail_closed_without_all_25_scenarios():
    with pytest.raises(ValueError, match="D3_SENSITIVITY_MEAN_PROFIT_COVERAGE_INVALID"):
        build_sensitivity_entries([])
