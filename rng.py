"""Deterministic, integer-threshold RNG governed by reference 14.3."""

from __future__ import annotations

import hashlib
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Final, Union

import constants


HASH_ALGORITHM: Final[str] = "sha256"
SHA256_DIGEST_BYTES: Final[int] = 32
RNG_WORD_BYTES: Final[int] = 8
RNG_DENOMINATOR: Final[int] = 1 << 64


def scenario_id(collection_probability: float, recovery_rate_pct: int) -> str:
    """Return the canonical scenario identifier used by the simulation."""
    if not 0.0 <= collection_probability <= 1.0:
        raise ValueError("collection_probability must be in [0, 1]")
    if not isinstance(recovery_rate_pct, int) or isinstance(recovery_rate_pct, bool):
        raise TypeError("recovery_rate_pct must be an int")
    return f"C{int(collection_probability * 100):03d}_G{recovery_rate_pct:03d}"
def _normalize_collection_stream_id(scenario_or_stream_id: str) -> str:
    prefix = scenario_or_stream_id.split("_", 1)[0]
    if (
        len(prefix) != 4
        or prefix[0] != "C"
        or not prefix[1:].isdigit()
        or not 0 <= int(prefix[1:]) <= 100
    ):
        raise ValueError("expected a collection stream id Cxxx or scenario id Cxxx_Gyyy")
    if constants.SEED_SCOPE != "COLLECTION_LEVEL":
        raise ValueError("unsupported SEED_SCOPE")
    return prefix


def rng_stream_id(scenario_or_stream_id: str) -> str:
    """Normalize a scenario id to its COLLECTION_LEVEL stream id (Cxxx)."""
    return _normalize_collection_stream_id(scenario_or_stream_id)


def collection_pct_from_scenario_id(scenario_or_stream_id: str) -> int:
    """Read the exact integer collection percentage encoded by Cxxx."""
    return int(_normalize_collection_stream_id(scenario_or_stream_id)[1:])


def collection_pct_from_probability(collection_probability: object) -> int:
    """Normalize a compatibility probability argument to integer pct once."""
    try:
        scaled = Decimal(str(collection_probability)) * 100
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError("collection_probability must map exactly to an integer percentage") from exc
    if not scaled.is_finite() or scaled != scaled.to_integral_value():
        raise ValueError("collection_probability must map exactly to an integer percentage")
    pct = int(scaled)
    if not 0 <= pct <= 100:
        raise ValueError("collection_probability must be in [0, 1]")
    return pct


def derive_seed(
    master_seed: int,
    rng_stream_id: str,
    trial_id: Union[int, str],
    bike_id: str,
    day: date,
    event_type: str,
) -> bytes:
    stream_id = _normalize_collection_stream_id(rng_stream_id)
    key = (
        f"{master_seed}|{stream_id}|{trial_id}|{bike_id}|"
        f"{day.isoformat()}|{event_type}"
    )
    return hashlib.sha256(key.encode("utf-8")).digest()


def rng_draw(seed_bytes: bytes) -> float:
    if len(seed_bytes) != SHA256_DIGEST_BYTES:
        raise ValueError(
            f"seed_bytes must contain exactly {SHA256_DIGEST_BYTES} bytes"
        )
    value = int.from_bytes(seed_bytes[:RNG_WORD_BYTES], "big")
    return value / RNG_DENOMINATOR


def draw_success(seed_bytes: bytes, pct: int) -> bool:
    """Compare a 64-bit draw against an integer percentage, without float."""
    if len(seed_bytes) != SHA256_DIGEST_BYTES:
        raise ValueError(
            f"seed_bytes must contain exactly {SHA256_DIGEST_BYTES} bytes"
        )
    if not isinstance(pct, int) or isinstance(pct, bool):
        raise TypeError("pct must be an integer percentage")
    if not 0 <= pct <= 100:
        raise ValueError("pct must be in [0, 100]")
    u64 = int.from_bytes(seed_bytes[:RNG_WORD_BYTES], "big")
    return u64 * 100 < pct * RNG_DENOMINATOR


def deterministic_success(
    collection_probability: float, seed_bytes: bytes
) -> bool:
    """Compatibility helper for endpoint checks; active engine uses draw_success."""
    if collection_probability == 1.0:
        return draw_success(seed_bytes, 100)
    if collection_probability == 0.0:
        return draw_success(seed_bytes, 0)
    raise ValueError("use draw_success(seed_bytes, integer_pct) for active collection")


def seed_hex(
    master_seed: int,
    rng_stream_id: str,
    trial_id: Union[int, str],
    bike_id: str,
    day: date,
    event_type: str,
) -> str:
    return derive_seed(
        master_seed, rng_stream_id, trial_id, bike_id, day, event_type
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
