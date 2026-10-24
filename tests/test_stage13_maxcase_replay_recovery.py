from __future__ import annotations

import hashlib

from scripts.stage13_maxcase_replay_recovery import (
    EXPECTED_ENGINE_BLOBS,
    RECOVERY_PLAN,
    SOURCE_SHA,
    _git_blob_sha,
)


def test_recovery_is_limited_to_the_ten_preselected_trial_ids():
    assert len(RECOVERY_PLAN) == 10
    assert RECOVERY_PLAN == {
        "C085_G030": {"trial_id": 53, "trial_result_sha256": "0261e6cac29254da77b97d5eb23153a1f893fcdc0fa41e9a2758ce9b251ec1d8", "daily_rows": 2198},
        "C070_G100": {"trial_id": 106, "trial_result_sha256": "9ebab5b0c761acd8344908d18aa83d97924732705fac79bfa0a537e2b94d3f3e", "daily_rows": 2202},
        "C070_G050": {"trial_id": 544, "trial_result_sha256": "20e34e66c37c56b2394de7a70331b423141ea895d325b6268c5c2e12f736eff0", "daily_rows": 2200},
        "C070_G030": {"trial_id": 429, "trial_result_sha256": "37b9e148f2f27ee899a2f7b44bd137d5488e7c27312b583bb8c524118b8af6ba", "daily_rows": 2200},
        "C070_G000": {"trial_id": 165, "trial_result_sha256": "13375cf2422a44b13683a32249c633e63a424d294deebc5134d7f6de2b266077", "daily_rows": 2202},
        "C050_G100": {"trial_id": 172, "trial_result_sha256": "5cd0f174d868004c96c5058f04c256e8b16312f70309b70d7f3cd272206764a4", "daily_rows": 2233},
        "C050_G070": {"trial_id": 7, "trial_result_sha256": "e4ff429687e9af845082252a066ad1b67c7d111f1f192057d2e62fc2486cd8b4", "daily_rows": 2222},
        "C050_G050": {"trial_id": 543, "trial_result_sha256": "16f01fb5a27bb6302480bc31f6e665d1a61990d8754af14671bf2f1f329792d5", "daily_rows": 2232},
        "C050_G030": {"trial_id": 122, "trial_result_sha256": "9467b01b5a897fcacf619c3524fe4f1a45d3386ecf01486409e4a8f19b0c466a", "daily_rows": 2231},
        "C030_G000": {"trial_id": 199, "trial_result_sha256": "ceda99eca77b00d117aa42574c088d9a98cea1ca5f88c804056b727d45c87a16", "daily_rows": 1655},
    }
    assert all(not scenario.startswith("C100_") for scenario in RECOVERY_PLAN)


def test_source_identity_and_git_blob_algorithm_are_fixed():
    assert SOURCE_SHA == "f3af4f06fded8b7a4e8c7730b5f2d19201a0a84b"
    assert len(EXPECTED_ENGINE_BLOBS) == 12
    assert _git_blob_sha(b"test") == hashlib.sha1(b"blob 4\0test").hexdigest()
