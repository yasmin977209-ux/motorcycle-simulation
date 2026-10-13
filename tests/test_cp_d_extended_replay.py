from __future__ import annotations

from scripts.cp_d_extended_replay import (
    ALL_TARGETS,
    BENCHMARK_BLOB_SHA,
    C100_GOLDEN,
    HISTORICAL,
    TARGETS,
    classify_fingerprints,
)


def test_cp_d_replay_has_exactly_the_approved_ten_new_trials() -> None:
    assert TARGETS == [
        ("C030_G000", 551),
        ("C030_G000", 600),
        ("C030_G000", 700),
        ("C030_G000", 1200),
        ("C050_G050", 600),
        ("C050_G050", 1200),
        ("C070_G070", 600),
        ("C070_G070", 1200),
        ("C085_G100", 600),
        ("C085_G100", 1200),
    ]
    assert sum(trial_id <= 600 for _, trial_id in TARGETS) == 5
    assert sum(trial_id > 600 for _, trial_id in TARGETS) == 5


def test_c100_trial_one_is_a_separate_deterministic_replay() -> None:
    assert ALL_TARGETS[-1] == ("C100_G100", 1)
    assert C100_GOLDEN == "4e58d9f5f5a11ff8a3f1f9c80e90ac5594660ae99d4f52170ec775bbd5a63417"


def test_cp_d_history_contains_each_approved_non_c100_key() -> None:
    assert set(HISTORICAL) == set(TARGETS)
    assert all(len(item["sha256"]) == 64 for item in HISTORICAL.values())
    assert all(item["manifest_run_id"] == 38174743440 for key, item in HISTORICAL.items() if key[1] <= 600)
    assert all(item["manifest_run_id"] == 38179919488 for key, item in HISTORICAL.items() if key[1] > 600)


def test_cp_d_uses_the_pinned_stage10_per_trial_hash_implementation() -> None:
    assert BENCHMARK_BLOB_SHA == "d54602982b6422939955ca841a251ecd250b4139"


def test_exact_three_way_match_is_pass() -> None:
    digest = "a" * 64
    assert classify_fingerprints(digest, digest, digest) == "PASS"


def test_a_versus_b_disagreement_is_classified_as_drift() -> None:
    assert classify_fingerprints("a" * 64, "b" * 64, "a" * 64) == "FAIL_DRIFT"


def test_equal_replays_with_historical_disagreement_fail() -> None:
    assert classify_fingerprints("a" * 64, "a" * 64, "b" * 64) == "FAIL_HISTORICAL_MISMATCH"


def test_missing_fingerprint_cannot_pass() -> None:
    assert classify_fingerprints(None, "a" * 64, "a" * 64) == "BLOCKED_MISSING_FINGERPRINT"
