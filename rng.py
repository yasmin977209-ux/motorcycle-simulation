"""Deterministic RNG from Chapter 14.

Every logical random event is independently keyed by:
master_seed | scenario_id | trial_id | bike_id | date | event_type

Python built-in hash() is never used for seed derivation.
"""

from __future__ import annotations

import hashlib
from datetime import date
from typing import Final, Union


HASH_ALGORITHM: Final[str] = "sha256"
SHA256_DIGEST_BYTES: Final[int] = 32
RNG_WORD_BYTES: Final[int] = 8
RNG_DENOMINATOR: Final[int] = 1 << 64


def derive_seed(
    master_seed: int,
    scenario_id: str,
    trial_id: Union[int, str],
    bike_id: str,
    day: date,
    event_type: str,
) -> bytes:
    key = (
        f"{master_seed}|{scenario_id}|{trial_id}|{bike_id}|{day}|{event_type}"
    )
    return hashlib.sha256(key.encode("utf-8")).digest()


def rng_draw(seed_bytes: bytes) -> float:
    if len(seed_bytes) != SHA256_DIGEST_BYTES:
        raise ValueError(
            f"seed_bytes must contain exactly {SHA256_DIGEST_BYTES} bytes"
        )
    value = int.from_bytes(seed_bytes[:RNG_WORD_BYTES], "big")
    return value / RNG_DENOMINATOR


def deterministic_success(
    collection_probability: float, seed_bytes: bytes
) -> bool:
    if collection_probability == 1.0:
        return True
    if collection_probability == 0.0:
        return False
    if not 0.0 < collection_probability < 1.0:
        raise ValueError("collection_probability must be in [0, 1]")
    return rng_draw(seed_bytes) < collection_probability


def seed_hex(
    master_seed: int,
    scenario_id: str,
    trial_id: Union[int, str],
    bike_id: str,
    day: date,
    event_type: str,
) -> str:
    return derive_seed(
        master_seed, scenario_id, trial_id, bike_id, day, event_type
    ).hex()


# Structural checks only.
_seed = derive_seed(
    20270101, "C085_G070", 1, "BK0001", date(2027, 1, 2), "PRIMARY_COLLECTION"
)
assert len(_seed) == SHA256_DIGEST_BYTES
assert 0.0 <= rng_draw(_seed) < 1.0
assert derive_seed(
    20270101, "C085_G070", 1, "BK0001", date(2027, 1, 2), "PRIMARY_COLLECTION"
) == _seed
