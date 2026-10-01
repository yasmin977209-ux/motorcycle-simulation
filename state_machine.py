"""Chapter 4 — the eleven-state bike lifecycle state machine.

The module is deterministic and structural only. It does not import dateutils
or rng and it does not execute M1-M17.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

from constants import (
    GRACE_PRIMARY_UPPER,
    NOTICE_PRIMARY_UPPER,
    PRIMARY_DAILY_RENT,
    PRIMARY_DEFAULT_AMOUNT,
    SECONDARY_DAILY_RENT,
    SECONDARY_DEFAULT_AMOUNT,
    WAITING_PRIMARY_UPPER,
)
from entities import BikeState, ContractType


STATE_COUNT = len(BikeState)

FORBIDDEN_STATE_NAMES = frozenset(
    {
        "TERMINATION_PENDING",
        "MINI_PREP",
        "PENDING_RECALL",
        "GUARANTEE_PENDING",
    }
)


def derive_state_from_balance(
    outstanding_amount: int,
    daily_rate: int,
    contract_type: str | ContractType,
) -> Optional[str]:
    """Classify the state from the current outstanding balance only.

    Threshold breaches return None. M11, not this function, performs the
    termination transition.
    """
    if outstanding_amount < 0:
        raise ValueError("outstanding_amount must not be negative")
    if daily_rate <= 0:
        raise ValueError("daily_rate must be positive")

    contract = ContractType(contract_type)

    if contract is ContractType.PRIMARY:
        if outstanding_amount == 0:
            return BikeState.ACTIVE_PRIMARY.value
        if outstanding_amount < 21 * daily_rate:
            return BikeState.WAITING_PRIMARY.value
        if outstanding_amount < 28 * daily_rate:
            return BikeState.NOTICE_PRIMARY.value
        if outstanding_amount < 30 * daily_rate:
            return BikeState.GRACE_PRIMARY.value
        return None

    if outstanding_amount == 0:
        return BikeState.ACTIVE_SECONDARY.value
    if outstanding_amount < 10 * daily_rate:
        return BikeState.NOTICE_SECONDARY.value
    return None


@dataclass(frozen=True)
class TransitionRule:
    from_states: tuple[str, ...]
    to_states: tuple[str, ...]
    condition: str
    phase: str


TRANSITION_TABLE: tuple[TransitionRule, ...] = (
    TransitionRule(
        ("PREP",),
        ("ACTIVE_PRIMARY",),
        "prep_paid and customs_paid and first working day on/after actual_ready_date",
        "M3",
    ),
    TransitionRule(
        ("ACTIVE_PRIMARY",),
        ("WAITING_PRIMARY",),
        f"0 < outstanding < {WAITING_PRIMARY_UPPER}",
        "M10",
    ),
    TransitionRule(
        ("WAITING_PRIMARY",),
        ("ACTIVE_PRIMARY",),
        "outstanding == 0",
        "M10",
    ),
    TransitionRule(
        ("WAITING_PRIMARY",),
        ("NOTICE_PRIMARY",),
        f"{WAITING_PRIMARY_UPPER} <= outstanding < {NOTICE_PRIMARY_UPPER}",
        "M10",
    ),
    TransitionRule(
        ("NOTICE_PRIMARY",),
        ("WAITING_PRIMARY", "ACTIVE_PRIMARY"),
        "new outstanding after payment is in the WAITING_PRIMARY or ACTIVE_PRIMARY band",
        "M10",
    ),
    TransitionRule(
        ("NOTICE_PRIMARY",),
        ("GRACE_PRIMARY",),
        f"{NOTICE_PRIMARY_UPPER} <= outstanding < {GRACE_PRIMARY_UPPER}",
        "M10",
    ),
    TransitionRule(
        ("GRACE_PRIMARY",),
        ("ACTIVE_PRIMARY", "WAITING_PRIMARY", "NOTICE_PRIMARY", "GRACE_PRIMARY"),
        "new outstanding after payment remains below the M11 default threshold",
        "M10",
    ),
    TransitionRule(
        ("GRACE_PRIMARY",),
        ("AVAILABLE_FOR_SECONDARY",),
        f"outstanding >= {GRACE_PRIMARY_UPPER}",
        "M11",
    ),
    TransitionRule(
        ("ACTIVE_PRIMARY", "WAITING_PRIMARY", "NOTICE_PRIMARY", "GRACE_PRIMARY"),
        ("OWNED_TRANSFERRED",),
        "current_date == maturity_date and total_due == total_paid after maturity-day collection",
        "M12",
    ),
    TransitionRule(
        ("ACTIVE_PRIMARY", "WAITING_PRIMARY", "NOTICE_PRIMARY", "GRACE_PRIMARY"),
        ("POST_MATURITY_SETTLEMENT",),
        "current_date == maturity_date and total_due > total_paid after maturity-day collection",
        "M12",
    ),
    TransitionRule(
        ("POST_MATURITY_SETTLEMENT",),
        ("OWNED_TRANSFERRED",),
        "settlement_legacy_debt_remaining == 0",
        "M13",
    ),
    TransitionRule(
        ("POST_MATURITY_SETTLEMENT",),
        ("AVAILABLE_FOR_SECONDARY",),
        "30 working days have elapsed from settlement_start_date without full payment",
        "M13",
    ),
    TransitionRule(
        ("AVAILABLE_FOR_SECONDARY",),
        ("ACTIVE_SECONDARY",),
        "first eligible working day",
        "M3",
    ),
    TransitionRule(
        ("ACTIVE_SECONDARY",),
        ("NOTICE_SECONDARY",),
        f"0 < outstanding < {SECONDARY_DEFAULT_AMOUNT}",
        "M10",
    ),
    TransitionRule(
        ("NOTICE_SECONDARY",),
        ("ACTIVE_SECONDARY",),
        "outstanding == 0",
        "M10",
    ),
    TransitionRule(
        ("NOTICE_SECONDARY",),
        ("AVAILABLE_FOR_SECONDARY",),
        f"outstanding >= {SECONDARY_DEFAULT_AMOUNT}",
        "M11",
    ),
    TransitionRule(
        ("ACTIVE_SECONDARY", "NOTICE_SECONDARY"),
        ("HELD_AS_ASSET",),
        "dynamic closure conditions satisfied",
        "M15",
    ),
    TransitionRule(
        (
            "PREP",
            "ACTIVE_PRIMARY",
            "WAITING_PRIMARY",
            "NOTICE_PRIMARY",
            "GRACE_PRIMARY",
            "POST_MATURITY_SETTLEMENT",
            "AVAILABLE_FOR_SECONDARY",
            "ACTIVE_SECONDARY",
            "NOTICE_SECONDARY",
        ),
        ("HELD_AS_ASSET",),
        "dynamic closure conditions satisfied",
        "M15",
    ),
)


def is_declared_transition(from_state: str, to_state: str) -> bool:
    """Return whether the 4.3 table declares the directed edge."""
    return any(
        from_state in rule.from_states and to_state in rule.to_states
        for rule in TRANSITION_TABLE
    )


def run_reference_path(path: Sequence[str]) -> tuple[str, ...]:
    """Validate one of the six Chapter 4.4 reference paths structurally."""
    if len(path) < 2:
        raise ValueError("A lifecycle path must contain at least two states")

    declared = {state.value for state in BikeState}
    if any(state not in declared for state in path):
        raise ValueError("Path contains an undeclared state")

    for current, target in zip(path, path[1:]):
        if not is_declared_transition(current, target):
            raise ValueError(f"Undeclared transition: {current} -> {target}")

    return tuple(path)


def legal_next_state(
    current_state: str,
    outstanding_amount: int,
    daily_rate: int,
    contract_type: str | ContractType,
) -> Optional[str]:
    """Apply the M10 classification without executing an M11 termination."""
    state = BikeState(current_state)
    derived = derive_state_from_balance(outstanding_amount, daily_rate, contract_type)

    if state in {
        BikeState.ACTIVE_PRIMARY,
        BikeState.WAITING_PRIMARY,
        BikeState.NOTICE_PRIMARY,
        BikeState.GRACE_PRIMARY,
        BikeState.ACTIVE_SECONDARY,
        BikeState.NOTICE_SECONDARY,
    }:
        return derived

    return state.value


# R4/R6 structural integrity checks. Threshold constants are referenced rather
# than duplicated numeric business values.
assert WAITING_PRIMARY_UPPER == 21 * PRIMARY_DAILY_RENT
assert NOTICE_PRIMARY_UPPER == 28 * PRIMARY_DAILY_RENT
assert GRACE_PRIMARY_UPPER == 30 * PRIMARY_DAILY_RENT
assert PRIMARY_DEFAULT_AMOUNT == GRACE_PRIMARY_UPPER
assert SECONDARY_DEFAULT_AMOUNT == 10 * SECONDARY_DAILY_RENT
assert STATE_COUNT == 11
assert len(TRANSITION_TABLE) == 18
assert not (set(BikeState.__members__) & FORBIDDEN_STATE_NAMES)
