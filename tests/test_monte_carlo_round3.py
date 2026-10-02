from __future__ import annotations

from datetime import date, timedelta

import monte_carlo


def _assert_no_daily_gaps(rows: list[dict[str, object]]) -> None:
    dates = sorted({str(row["date"]) for row in rows})
    start = date.fromisoformat(dates[0])
    end = date.fromisoformat(dates[-1])
    expected = [
        (start + timedelta(days=index)).isoformat()
        for index in range((end - start).days + 1)
    ]
    assert dates == expected


def test_c070_g100_20_trials_daily_distribution_has_no_gaps() -> None:
    trial_ids = tuple(range(1, 21))
    results, slices = monte_carlo.run_trials_sequentially(
        "C070_G100",
        trial_ids,
    )
    distribution = monte_carlo.build_daily_distribution(results, slices)
    assert distribution
    _assert_no_daily_gaps(distribution)
    assert {
        row["quantile_name"] for row in distribution
    } == {"P10", "P25", "P50", "P75", "P90"}
    assert all(
        row["active_trial_count"]
        == sum(
            result.final_close_date is None
            or result.final_close_date >= row["date"]
            for result in results
        )
        for row in distribution
    )
    assert max(
        len(rows) for rows in slices.values()
    ) == len({row["date"] for row in distribution})


def test_c100_g100_single_trial_daily_distribution() -> None:
    results, slices = monte_carlo.run_trials_sequentially(
        "C100_G100",
        (1,),
    )
    distribution = monte_carlo.build_daily_distribution(results, slices)
    assert distribution
    assert {row["active_trial_count"] for row in distribution} == {1}
    assert distribution[0]["date"] == "2027-01-01"
    assert distribution[-1]["date"] == "2033-01-06"
    assert {
        row["quantile_name"] for row in distribution
    } == {"P10", "P25", "P50", "P75", "P90"}
