"""Deterministic RNG from Chapter 14.

Every logical random event is independently keyed by:
master_seed | rng_stream_id | trial_id | bike_id | date | event_type

For canonical Cxxx_Gxxx scenarios, rng_stream_id is Cxxx. This couples
guarantee-recovery scenarios that share a collection probability, as required
by the collection-level RNG scope. Python built-in hash() is never used.
"""

from __future__ import annotations

import hashlib
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from datetime import date
from typing import Final, Iterator, Union


HASH_ALGORITHM: Final[str] = "sha256"
SHA256_DIGEST_BYTES: Final[int] = 32
RNG_WORD_BYTES: Final[int] = 8
RNG_DENOMINATOR: Final[int] = 1 << 64
RNG_FLOAT_DENOMINATOR: Final[int] = 1 << 53
RNG_CHECKSUM_MODULUS: Final[int] = 1 << 64
RNG_CHECKSUM_SCHEMA: Final[str] = "rng-checksum-high53-mod2^64-v1"


@dataclass
class RngChecksum:
    """Per-trial RNG audit: sum of drawn high-53-bit values modulo 2**64."""

    checksum: int = 0
    draw_count: int = 0

    def record(self, value: int) -> None:
        if type(value) is not int or not 0 <= value < (1 << 53):
            raise ValueError("RNG checksum draw must be an unsigned 53-bit integer")
        self.checksum = (self.checksum + value) % RNG_CHECKSUM_MODULUS
        self.draw_count += 1


_ACTIVE_RNG_CHECKSUM: ContextVar[RngChecksum | None] = ContextVar(
    "motorcycle_simulation_rng_checksum", default=None
)


@contextmanager
def capture_rng_checksum() -> Iterator[RngChecksum]:
    """Capture random draws in the current logical trial, isolated by context."""
    audit = RngChecksum()
    token = _ACTIVE_RNG_CHECKSUM.set(audit)
    try:
        yield audit
    finally:
        _ACTIVE_RNG_CHECKSUM.reset(token)


def scenario_id(collection_probability: float, recovery_rate_pct: int) -> str:
    """Return the canonical scenario identifier used by the simulation."""
    if not 0.0 <= collection_probability <= 1.0:
        raise ValueError("collection_probability must be in [0, 1]")
    if not isinstance(recovery_rate_pct, int) or isinstance(recovery_rate_pct, bool):
        raise TypeError("recovery_rate_pct must be an int")
    return f"C{int(collection_probability * 100):03d}_G{recovery_rate_pct:03d}"
def _rng_stream_id(scenario_id: str) -> str:
    """Return the RNG stream ID required by the canonical scenario contract.

    Recovery-rate variants share their collection-level stream. Preserve the
    original identifier for noncanonical strings; canonical scenario
    validation remains the responsibility of the scenario parser.
    """
    collection_part, separator, recovery_part = scenario_id.partition("_G")
    is_canonical_shape = (
        separator == "_G"
        and len(collection_part) == 4
        and collection_part.startswith("C")
        and collection_part[1:].isdigit()
        and len(recovery_part) == 3
        and recovery_part.isdigit()
    )
    return collection_part if is_canonical_shape else scenario_id


def derive_seed(
    master_seed: int,
    scenario_id: str,
    trial_id: Union[int, str],
    bike_id: str,
    day: date,
    event_type: str,
) -> bytes:
    rng_stream_id = _rng_stream_id(scenario_id)
    key = (
        f"{master_seed}|{rng_stream_id}|{trial_id}|{bike_id}|{day}|{event_type}"
    )
    return hashlib.sha256(key.encode("utf-8")).digest()


def rng_draw(seed_bytes: bytes) -> float:
    """Return a floating-point view for diagnostics only, never for decisions."""
    if len(seed_bytes) != SHA256_DIGEST_BYTES:
        raise ValueError(
            f"seed_bytes must contain exactly {SHA256_DIGEST_BYTES} bytes"
        )
    value = int.from_bytes(seed_bytes[:RNG_WORD_BYTES], "big")
    return (value >> 11) / RNG_FLOAT_DENOMINATOR


def draw_success(seed_bytes: bytes, pct: int) -> bool:
    """Compare the first 64 SHA-256 bits using exact integer arithmetic.

    This implements reference §14.3 literally: u * 100 < pct * 2**64.
    No float conversion is used in the probabilistic decision path.
    """
    if len(seed_bytes) != SHA256_DIGEST_BYTES:
        raise ValueError(
            f"seed_bytes must contain exactly {SHA256_DIGEST_BYTES} bytes"
        )
    if type(pct) is not int:
        raise TypeError("pct must be an integer percentage")
    if not 0 <= pct <= 100:
        raise ValueError("pct must be in [0, 100]")
    # Deterministic endpoints are permitted to skip draws entirely.
    if pct == 0:
        return False
    if pct == 100:
        return True
    value = int.from_bytes(seed_bytes[:RNG_WORD_BYTES], "big")
    audit = _ACTIVE_RNG_CHECKSUM.get()
    if audit is not None:
        audit.record(value >> 11)
    return value * 100 < pct * RNG_DENOMINATOR


def deterministic_success(
    collection_probability: float, seed_bytes: bytes
) -> bool:
    """Apply a canonical integer-percent collection probability exactly."""
    if isinstance(collection_probability, bool) or not isinstance(
        collection_probability, (int, float)
    ):
        raise TypeError("collection_probability must be a numeric probability")
    if not 0.0 <= collection_probability <= 1.0:
        raise ValueError("collection_probability must be in [0, 1]")
    pct = round(float(collection_probability) * 100)
    if float(collection_probability) != pct / 100.0:
        raise ValueError(
            "collection_probability must correspond to a whole integer percentage"
        )
    return draw_success(seed_bytes, pct)


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
